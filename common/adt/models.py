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


def ollama_models(host: str = HOST) -> list:
    """Installed models as (name, parameter_size). Raises OSError if the server is not reachable."""
    with urllib.request.urlopen(host + "/api/tags", timeout=5) as r:
        return [(m["name"], m.get("details", {}).get("parameter_size", "?")) for m in json.load(r)["models"]]


class OllamaRunner:
    """Temperature 0 and a fixed seed. JSON output mode, because the agents here answer with a tool plan."""

    def __init__(self, model: str, host: str = HOST, num_ctx: int = 4096, seed: int = 0):
        self.model, self.host, self.num_ctx, self.seed = model, host, num_ctx, seed
        self.name = model

    def generate(self, system: str, user: str, hint=None) -> Reply:
        gpucooler.before_call()          # waits here while the GPU is over its limit, if a cooler is installed
        body = json.dumps({
            "model": self.model, "stream": False, "format": "json", "keep_alive": "10m",
            "options": {"temperature": 0, "seed": self.seed, "num_ctx": self.num_ctx},
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        }).encode()
        req = urllib.request.Request(self.host + "/api/chat", data=body, headers={"Content-Type": "application/json"})
        for attempt in (1, 2):
            t0 = time.perf_counter()
            try:
                with urllib.request.urlopen(req, timeout=300) as r:
                    d = json.load(r)
                return Reply(d["message"]["content"], d.get("prompt_eval_count", 0), d.get("eval_count", 0),
                             round((time.perf_counter() - t0) * 1000))
            except urllib.error.HTTPError as e:
                err = f"HTTP {e.code}"
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

    def generate(self, system: str, user: str, hint=None) -> Reply:
        k = hashlib.sha256((system + "\x00" + user).encode()).hexdigest()
        if k in self._c:
            self.hits += 1
            r = self._c[k]
            if isinstance(r, Exception):             # a failed call fails the same way for every defense
                raise r
            return Reply(r.text, r.tokens_in, r.tokens_out, r.latency_ms, cached=True)
        try:
            self._c[k] = self.inner.generate(system, user, hint)
        except ModelError as e:
            self._c[k] = e
            raise
        return self._c[k]


class ScriptedRunner:
    """A human-written reply for each case, passed in as `hint`. Never counted as a result."""

    name = "scripted"

    def generate(self, system: str, user: str, hint=None) -> Reply:
        return Reply(hint or "{}", 0, 0, 0)
