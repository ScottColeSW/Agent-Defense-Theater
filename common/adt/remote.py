"""Remote model runners (Anthropic, Google, and any OpenAI-compatible service) behind the same interface as OllamaRunner.

Differences from a local run that a result must not hide: a hosted model is not pinned to a digest and is not guaranteed to repeat at
temperature 0, so `describe()` records the provider, the model id the service reported, and that the run was remote. These runners
do not wait on the GPU cooler or the RAM guard, because nothing here uses either."""
import contextlib
import json
import re
import time
import urllib.error
import urllib.request

from . import keys
from .models import ModelError, Reply

ANTHROPIC_VERSION = "2023-06-01"
MAX_WAIT = 70                               # longest single wait on a rate limit, seconds
ATTEMPTS = 5
BACKOFF = (3, 8, 20, 45, 0)                  # seconds waited after each failed try; overloaded hosted models often clear in under a minute
_calls = 0                                  # remote calls made by this process, for the max_calls guard


_cap_override = None                        # set by limit_requests(): an absolute value of _calls the process may not pass


@contextlib.contextmanager
def limit_requests(n: int):
    """No more than n provider requests (retries included) inside this block, whatever keys.ini says."""
    global _cap_override
    prev, _cap_override = _cap_override, _calls + n
    try:
        yield
    finally:
        _cap_override = prev


class SpendLimit(RuntimeError):
    """max_calls in keys.ini was reached. Stops the run, like an unreachable server: every later case would hit the same limit."""


class AuthError(RuntimeError):
    """The service refused the key. Stops the run: every case would fail the same way."""


def _post(url: str, headers: dict, body: dict, timeout: int = 180) -> dict:
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def _error_text(e: urllib.error.HTTPError) -> str:
    try:
        return keys.redact(e.read().decode("utf-8", "replace").strip())[:300]
    except Exception:
        return ""


class RemoteRunner:
    def __init__(self, model: str, temperature: float = 0.0, label: str = "", max_out: int = None):
        parts = keys.split(model)
        if not parts:
            raise ValueError(f"{model} does not start with a known provider. Known: {', '.join(keys.provider_names())}")
        self.provider, self.model_id = parts
        self.cfg = keys.provider_config(self.provider)        # KeyError here, before any run starts, if the key is missing
        self.model, self.temperature, self.name = model, temperature, model + label
        self.max_out = max_out or keys.limits()["max_output_tokens"]
        self._send_temperature = True
        self.reported_model = ""

    def describe(self) -> dict:
        return {"remote": True, "provider": self.provider, "model": self.model_id, "reported_model": self.reported_model or None,
                "format": self.cfg["format"], "temperature": self.temperature if self._send_temperature else None,
                "note": "hosted model: not digest-pinned, and not guaranteed to repeat at temperature 0"}

    # ---- wire formats: each returns (url, headers, body) and a parser for the reply ----
    def _request(self, system: str, user: str):
        c, fmt = self.cfg, self.cfg["format"]
        if fmt == "anthropic":
            body = {"model": self.model_id, "max_tokens": self.max_out, "system": system, "messages": [{"role": "user", "content": user}]}
            if self._send_temperature:
                body["temperature"] = self.temperature
            return c["base_url"] + "/v1/messages", {"x-api-key": c["api_key"], "anthropic-version": ANTHROPIC_VERSION}, body
        if fmt == "google":
            gen = {"maxOutputTokens": self.max_out, "responseMimeType": "application/json"}
            if self._send_temperature:
                gen["temperature"] = self.temperature
            body = {"systemInstruction": {"parts": [{"text": system}]}, "contents": [{"role": "user", "parts": [{"text": user}]}], "generationConfig": gen}
            return f"{c['base_url']}/models/{self.model_id}:generateContent", {"x-goog-api-key": c["api_key"]}, body
        body = {"model": self.model_id, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
        body["max_completion_tokens" if self.provider == "openai" else "max_tokens"] = self.max_out
        if self._send_temperature:
            body["temperature"] = self.temperature
        return c["base_url"] + "/chat/completions", {"Authorization": "Bearer " + c["api_key"]}, body

    def _parse(self, d: dict):
        fmt = self.cfg["format"]
        self.reported_model = d.get("model") or d.get("modelVersion") or self.reported_model
        if fmt == "anthropic":
            u = d.get("usage", {})
            text = "".join(b.get("text", "") for b in d.get("content", []) if b.get("type") == "text")
            return text, u.get("input_tokens", 0), u.get("output_tokens", 0)
        if fmt == "google":
            u = d.get("usageMetadata", {})
            cand = (d.get("candidates") or [{}])[0]
            text = "".join(p.get("text", "") for p in cand.get("content", {}).get("parts", []) if not p.get("thought"))
            return text, u.get("promptTokenCount", 0), u.get("candidatesTokenCount", 0) + u.get("thoughtsTokenCount", 0)
        u = d.get("usage", {})
        text = ((d.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
        return text, u.get("prompt_tokens", 0), u.get("completion_tokens", 0)

    def generate(self, system: str, user: str, hint=None, **opts) -> Reply:
        global _calls
        cap = keys.limits()["max_calls"]
        if "temperature" in opts:
            self.temperature = opts["temperature"]
        err = "unknown error"
        for attempt in range(1, ATTEMPTS + 1):
            if _cap_override is not None and _calls >= _cap_override:
                raise SpendLimit("the request cap for this run was reached.")
            if cap and _calls >= cap:
                raise SpendLimit(f"max_calls = {cap} in {keys.keys_path().name} reached. Raise it to continue.")
            _calls += 1
            url, headers, body = self._request(system, user)
            t0 = time.perf_counter()
            wait = BACKOFF[attempt - 1]
            try:
                d = _post(url, headers, body)
                text, tin, tout = self._parse(d)
                block = (d.get("promptFeedback") or {}).get("blockReason")
                if block:
                    raise ModelError(f"{self.model}: the provider refused the prompt (blockReason {block}). Nothing was generated or billed. Retrying will not help; use another generator model.")
                if not text.strip():
                    raise ModelError(f"{self.model}: empty reply after {tout} output tokens. A reasoning model may have spent its whole budget thinking: "
                                     f"raise max_output_tokens in {keys.keys_path().name}. Not retried, since each try is billed.")
                else:
                    return Reply(text, tin, tout, round((time.perf_counter() - t0) * 1000))
            except urllib.error.HTTPError as e:
                msg = _error_text(e)
                if e.code in (401, 403):
                    raise AuthError(f"{self.provider} refused the key (HTTP {e.code}). Check {keys.keys_path().name}.") from e
                if e.code in (402, 429) and any(w in msg.lower() for w in ("insufficient_quota", "credit_balance")):
                    raise AuthError(f"{self.provider} accepted the key but the account has no usable credit (HTTP {e.code}). Add credit or a payment method, then try again.") from e
                if e.code == 400 and self._send_temperature and "temperature" in msg.lower():
                    self._send_temperature = False             # some models fix their own temperature; retry without it
                    continue
                if e.code == 429:
                    m = re.search(r"retry in ([\d.]+)\s*s", msg)            # Google names the wait; a free tier allows only a few calls a minute
                    try:
                        wait = min(float(m.group(1)) + 1 if m else float(e.headers.get("retry-after", wait)), MAX_WAIT)
                    except (TypeError, ValueError):
                        pass
                err = f"HTTP {e.code}" + (f": {msg}" if msg else "")
                if e.code in (400, 404, 422):                  # a bad request will not improve on retry
                    break
            except urllib.error.URLError as e:
                err = keys.redact(str(e.reason))
            except TimeoutError:
                err = "timed out"
            if attempt < ATTEMPTS:
                time.sleep(wait)
        raise ModelError(f"{self.model}: {err} (after retries)")
