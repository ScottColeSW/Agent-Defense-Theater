"""API keys for remote models, read from a local keys.ini that git ignores (see keys.example.ini).

Never print, log or store a key: `describe()` and `status()` report only whether one is set. An environment variable fills in
a key the file leaves empty, so a CI job or a shell session can supply one without a file."""
import configparser
import os
from pathlib import Path

from .loader import ROOT

# provider -> (wire format, default base url, environment variables tried when the file has no key)
PROVIDERS = {
    "anthropic":  ("anthropic", "https://api.anthropic.com", ("ANTHROPIC_API_KEY",)),
    "openai":     ("openai", "https://api.openai.com/v1", ("OPENAI_API_KEY",)),
    "google":     ("google", "https://generativelanguage.googleapis.com/v1beta", ("GEMINI_API_KEY", "GOOGLE_API_KEY")),
    "openrouter": ("openai", "https://openrouter.ai/api/v1", ("OPENROUTER_API_KEY",)),
    "groq":       ("openai", "https://api.groq.com/openai/v1", ("GROQ_API_KEY",)),
    "together":   ("openai", "https://api.together.xyz/v1", ("TOGETHER_API_KEY",)),
    "mistral":    ("openai", "https://api.mistral.ai/v1", ("MISTRAL_API_KEY",)),
    "xai":        ("openai", "https://api.x.ai/v1", ("XAI_API_KEY",)),
    "deepseek":   ("openai", "https://api.deepseek.com/v1", ("DEEPSEEK_API_KEY",)),
}
RESERVED = {"limits"}
DEFAULT_MAX_OUTPUT = 2048


def keys_path() -> Path:
    return Path(os.environ.get("ADT_KEYS_FILE") or ROOT / "keys.ini")


def _parser() -> configparser.ConfigParser:
    cp = configparser.ConfigParser(interpolation=None)         # keys may contain %
    p = keys_path()
    if p.exists():
        cp.read(p, encoding="utf-8")
    return cp


def provider_names() -> list:
    """Providers a model name may start with: the built-in ones and any extra section of keys.ini that names a base_url."""
    cp = _parser()
    extra = [s for s in cp.sections() if s not in RESERVED and s not in PROVIDERS and cp.get(s, "base_url", fallback="").strip()]
    return list(PROVIDERS) + extra


def split(model: str):
    """'anthropic:claude-haiku-5-5' -> ('anthropic', 'claude-haiku-5-5'). A name with no known provider prefix is a local
    Ollama model (llama3.1:8b has a colon too), so None means local."""
    if ":" in model:
        head, rest = model.split(":", 1)
        if head in provider_names() and rest:
            return head, rest
    return None


def is_remote(model: str) -> bool:
    return split(model) is not None


def provider_config(provider: str) -> dict:
    """{'format', 'base_url', 'api_key'} for a provider. Raises KeyError (with no key in the message) if no key is set."""
    cp = _parser()
    fmt, base, envs = PROVIDERS.get(provider, ("openai", "", ()))
    sect = cp[provider] if cp.has_section(provider) else {}
    key = (sect.get("api_key") or "").strip()
    for e in envs:
        key = key or os.environ.get(e, "").strip()
    if not key:
        raise KeyError(f"No API key for '{provider}'. Put it in {keys_path().name} (copy keys.example.ini) or set {envs[0] if envs else 'a key'}.")
    url = (sect.get("base_url") or base).strip().rstrip("/")
    if not url:
        raise KeyError(f"'{provider}' in {keys_path().name} needs a base_url.")
    return {"format": (sect.get("format") or fmt).strip(), "base_url": url, "api_key": key}


def limits() -> dict:
    """Spending guards from [limits]: max_output_tokens (per call) and max_calls (per process, 0 = no cap)."""
    cp = _parser()
    g = lambda k, d: cp.getint("limits", k, fallback=d) if cp.has_section("limits") else d
    return {"max_output_tokens": g("max_output_tokens", DEFAULT_MAX_OUTPUT), "max_calls": g("max_calls", 0)}


def status() -> list:
    """[(provider, 'set' | 'not set', where)] for every known provider. Never includes the key."""
    out = []
    for p in provider_names():
        try:
            c = provider_config(p)
            cp = _parser()
            src = "keys.ini" if (cp.has_section(p) and (cp.get(p, "api_key", fallback="") or "").strip()) else "environment"
            out.append((p, "set", f"{src}, {c['format']} format"))
        except KeyError:
            out.append((p, "not set", ""))
    return out


def redact(text: str) -> str:
    """Remove every configured key from a string before it is shown or kept."""
    for p in provider_names():
        try:
            k = provider_config(p)["api_key"]
        except KeyError:
            continue
        text = text.replace(k, "[key]")
    return text
