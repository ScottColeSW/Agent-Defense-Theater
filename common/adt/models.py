"""Model runners. Local first: Ollama over HTTP with fixed settings so runs repeat."""
import hashlib
import json
import time
import urllib.request
from dataclasses import dataclass

from . import gpucooler

HOST = "http://localhost:11434"


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
        t0 = time.perf_counter()
        with urllib.request.urlopen(req, timeout=300) as r:
            d = json.load(r)
        return Reply(d["message"]["content"], d.get("prompt_eval_count", 0), d.get("eval_count", 0),
                     round((time.perf_counter() - t0) * 1000))


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
            return Reply(r.text, r.tokens_in, r.tokens_out, r.latency_ms, cached=True)
        self._c[k] = self.inner.generate(system, user, hint)
        return self._c[k]


class ScriptedRunner:
    """A human-written reply for each case, passed in as `hint`. Never counted as a result."""

    name = "scripted"

    def generate(self, system: str, user: str, hint=None) -> Reply:
        return Reply(hint or "{}", 0, 0, 0)
