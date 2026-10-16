"""Model runners. Local first: Ollama over HTTP with fixed settings so runs repeat."""
import hashlib
import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

from . import gpucooler, resources

HOST = "http://localhost:11434"

# Generation settings that a preregistration should name, because they change what a reply can be (see docs/METHODOLOGY.md).
DEFAULT_NUM_PREDICT = 1024     # output cap for a model that is not asked to think. The agents here answer with a short JSON plan (100 to 200 tokens);
#                                a reply that needs more than this is a runaway, and without a cap one can run for minutes at full GPU load.
TIMEOUT_S = 120                # one request; a thinking model gets THINK_TIMEOUT_S
THINK_TIMEOUT_S = 300
NO_RETRY = ("timeout", "repeat_limit")     # at temperature 0 with a fixed seed a repeat would run away the same way, so these are not retried


class ModelError(RuntimeError):
    """One model call failed (a server error or a timeout). The harness records the case as failed and carries on.
    `kind` says why, so a record can flag a runaway: "timeout", "repeat_limit" (Ollama stopped a repetition loop), or "" for anything else.
    A model server that is not running at all is not this: that stops the run, since every case would fail the same way."""

    def __init__(self, message: str = "", kind: str = ""):
        super().__init__(message)
        self.kind = kind


@dataclass
class Reply:
    text: str
    tokens_in: int = 0
    tokens_out: int = 0
    latency_ms: int = 0
    cached: bool = False
    thinking: str = ""            # a thinking model's reasoning, kept apart from its answer (tokens_out counts both)
    truncated: bool = False       # the reply hit the output cap (Ollama's done_reason "length"), so it may be cut off mid-answer


def ollama_models(host: str = HOST) -> list:
    """Installed models as (name, parameter_size). Raises OSError if the server is not reachable."""
    with urllib.request.urlopen(host + "/api/tags", timeout=5) as r:
        return [(m["name"], m.get("details", {}).get("parameter_size", "?")) for m in json.load(r)["models"]]


class OllamaRunner:
    """Temperature 0 and a fixed seed unless a call asks otherwise. JSON output mode, because the agents here answer with a tool plan.

    think: None leaves it to Ollama, which turns thinking ON for a thinking model and does not behave like an explicit True (it
    used about 40% more tokens in a probe), so a run that wants to repeat should always say True or False for such a model.
    A model that cannot think refuses think=True or False with HTTP 400, so only pass it for thinking-capable models."""

    def __init__(self, model: str, host: str = HOST, num_ctx: int = 4096, seed: int = 0, keep_alive: str = "10m",
                 think=None, temperature: float = 0.0, num_predict: int = None, label: str = ""):
        self.model, self.host, self.seed, self.keep_alive, self.think, self.temperature = model, host, seed, keep_alive, think, temperature
        self.num_ctx = max(num_ctx, 8192) if think else num_ctx                     # reasoning needs room
        self.num_predict = num_predict if num_predict is not None else (4096 if think else DEFAULT_NUM_PREDICT)
        self.timeout = THINK_TIMEOUT_S if think else TIMEOUT_S
        self.name = model + label

    def describe(self) -> dict:
        """Ollama's own description of this model (capabilities, size, quantization, context, digest), for the run record."""
        from . import modelmgr
        digest = next((m.get("digest") for m in modelmgr._get("/api/tags", self.host).get("models", []) if m.get("name") == self.model), None)
        return {**modelmgr.describe(self.model, digest, self.host), "think": self.think, "temperature": self.temperature, "seed": self.seed,
                "num_predict": self.num_predict, "timeout_s": self.timeout}

    def generate(self, system: str, user: str, hint=None, **opts) -> Reply:
        """opts may override temperature and seed for this call (used to measure how stable a verdict is)."""
        resources.before_call()          # waits while system RAM is low, and stops the run if it stays low
        gpucooler.before_call()          # waits here while the GPU is over its limit, if a cooler is installed
        options = {"temperature": opts.get("temperature", self.temperature), "seed": opts.get("seed", self.seed), "num_ctx": self.num_ctx}
        if self.num_predict:
            options["num_predict"] = self.num_predict
        payload = {"model": self.model, "stream": False, "format": "json", "keep_alive": self.keep_alive, "options": options,
                   "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
        if self.think is not None:
            payload["think"] = self.think
        body = json.dumps(payload).encode()
        req = urllib.request.Request(self.host + "/api/chat", data=body, headers={"Content-Type": "application/json"})
        for attempt in (1, 2):
            t0 = time.perf_counter()
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as r:
                    d = json.load(r)
                return Reply(d["message"]["content"], d.get("prompt_eval_count", 0), d.get("eval_count", 0),
                             round((time.perf_counter() - t0) * 1000), thinking=d["message"].get("thinking") or "",
                             truncated=d.get("done_reason") == "length")
            except urllib.error.HTTPError as e:
                try:
                    msg = e.read().decode("utf-8", "replace").strip()[:200]        # Ollama says why in the body
                except Exception:
                    msg = ""
                err = f"HTTP {e.code}" + (f": {msg}" if msg else "") + (" (Ollama sends 500 on memory exhaustion or a model crash)" if e.code == 500 else "")
                if e.code == 500 and "token repeat limit" in msg:
                    raise ModelError(f"{self.model}: {err} (a repetition loop; not retried, a repeat would loop the same way)", kind="repeat_limit") from e
            except urllib.error.URLError as e:
                if isinstance(e.reason, ConnectionRefusedError):
                    raise RuntimeError(f"Ollama is not reachable at {self.host}. Start it and run again.") from e
                err = str(e.reason)
            except TimeoutError:
                raise ModelError(f"{self.model}: timed out after {self.timeout} s (not retried: at temperature 0 a repeat would run away the same way)", kind="timeout")
            if attempt == 1:
                time.sleep(2)
        raise ModelError(f"{self.model}: {err} (after one retry)")


def make_runner(name: str, **kw):
    """A runner for a model name. 'anthropic:claude-haiku-5-5' goes to that provider (keys in keys.ini); anything else is a local Ollama model."""
    from . import keys
    if keys.is_remote(name):
        from .remote import RemoteRunner
        return RemoteRunner(name, **{k: v for k, v in kw.items() if k in ("temperature", "label", "max_out")})
    return OllamaRunner(name, **kw)


class CachedRunner:
    """Reuse a reply when the exact prompt repeats. At temperature 0 the model would answer the same,
    and defenses that act after the model (a credential gate) then see identical model output, which
    makes the comparison paired. Cached replies keep the original cost so cost stays comparable."""

    def __init__(self, inner):
        self.inner, self.name, self._c, self.hits = inner, inner.name, {}, 0
        self.truncations = 0                         # replies handed out that hit the output cap, cached or not; the harness reads it per case

    def __getattr__(self, attr):                     # describe(), model and the rest come from the runner underneath
        return getattr(self.inner, attr)

    def generate(self, system: str, user: str, hint=None, **opts) -> Reply:
        k = hashlib.sha256((system + "\x00" + user + "\x00" + json.dumps(opts, sort_keys=True)).encode()).hexdigest()
        if k in self._c:
            self.hits += 1
            r = self._c[k]
            if isinstance(r, Exception):             # a failed call fails the same way for every defense
                raise r
            self.truncations += r.truncated
            return Reply(r.text, r.tokens_in, r.tokens_out, r.latency_ms, cached=True, thinking=r.thinking, truncated=r.truncated)
        try:
            self._c[k] = self.inner.generate(system, user, hint, **opts)
        except ModelError as e:
            self._c[k] = e
            raise
        self.truncations += self._c[k].truncated
        return self._c[k]


class ScriptedRunner:
    """A human-written reply for each case, passed in as `hint`. Never counted as a result."""

    name = "scripted"

    def generate(self, system: str, user: str, hint=None, **opts) -> Reply:
        return Reply(hint or "{}", 0, 0, 0)
