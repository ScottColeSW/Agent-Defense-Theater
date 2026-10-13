"""Model runners. Local first: Ollama over HTTP with fixed settings so runs repeat."""
import hashlib
import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

from . import gpucooler

HOST = "http://localhost:11434"


class ModelError(RuntimeError):
    """One model call failed after a retry (a server error or a timeout). The harness records the case as failed and carries on.
    A model server that is not running at all is not this: that stops the run, since every case would fail the same way."""


@dataclass
class Reply:
    text: str
    tokens_in: int = 0
    tokens_out: int = 0
    latency_ms: int = 0
    cached: bool = False
    thinking: str = ""            # a thinking model's reasoning, kept apart from its answer (tokens_out counts both)


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
        self.num_predict = num_predict if num_predict is not None else (4096 if think else None)
        self.name = model + label

    def describe(self) -> dict:
        """Ollama's own description of this model (capabilities, size, quantization, context, digest), for the run record."""
        from . import modelmgr
        digest = next((m.get("digest") for m in modelmgr._get("/api/tags", self.host).get("models", []) if m.get("name") == self.model), None)
        return {**modelmgr.describe(self.model, digest, self.host), "think": self.think, "temperature": self.temperature, "seed": self.seed}

    def generate(self, system: str, user: str, hint=None, **opts) -> Reply:
        """opts may override temperature and seed for this call (used to measure how stable a verdict is)."""
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
                with urllib.request.urlopen(req, timeout=300) as r:
                    d = json.load(r)
                return Reply(d["message"]["content"], d.get("prompt_eval_count", 0), d.get("eval_count", 0),
                             round((time.perf_counter() - t0) * 1000), thinking=d["message"].get("thinking") or "")
            except urllib.error.HTTPError as e:
                try:
                    msg = e.read().decode("utf-8", "replace").strip()[:200]        # Ollama says why in the body
                except Exception:
                    msg = ""
                err = f"HTTP {e.code}" + (f": {msg}" if msg else "") + (" (Ollama sends 500 on memory exhaustion or a model crash)" if e.code == 500 else "")
            except urllib.error.URLError as e:
                if isinstance(e.reason, ConnectionRefusedError):
                    raise RuntimeError(f"Ollama is not reachable at {self.host}. Start it and run again.") from e
                err = str(e.reason)
            except TimeoutError:
                err = "timed out"
            if attempt == 1:
                time.sleep(2)
        raise ModelError(f"{self.model}: {err} (after one retry)")


class CachedRunner:
    """Reuse a reply when the exact prompt repeats. At temperature 0 the model would answer the same,
    and defenses that act after the model (a credential gate) then see identical model output, which
    makes the comparison paired. Cached replies keep the original cost so cost stays comparable."""

    def __init__(self, inner):
        self.inner, self.name, self._c, self.hits = inner, inner.name, {}, 0

    def __getattr__(self, attr):                     # describe(), model and the rest come from the runner underneath
        return getattr(self.inner, attr)

    def generate(self, system: str, user: str, hint=None, **opts) -> Reply:
        k = hashlib.sha256((system + "\x00" + user + "\x00" + json.dumps(opts, sort_keys=True)).encode()).hexdigest()
        if k in self._c:
            self.hits += 1
            r = self._c[k]
            if isinstance(r, Exception):             # a failed call fails the same way for every defense
                raise r
            return Reply(r.text, r.tokens_in, r.tokens_out, r.latency_ms, cached=True, thinking=r.thinking)
        try:
            self._c[k] = self.inner.generate(system, user, hint, **opts)
        except ModelError as e:
            self._c[k] = e
            raise
        return self._c[k]


class ScriptedRunner:
    """A human-written reply for each case, passed in as `hint`. Never counted as a result."""

    name = "scripted"

    def generate(self, system: str, user: str, hint=None, **opts) -> Reply:
        return Reply(hint or "{}", 0, 0, 0)
