import sys
import urllib.error
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from adt import keys, models, remote
from adt.models import ModelError

INI = """[anthropic]
api_key = sk-ant-SECRET1
[openai]
api_key = sk-oai-SECRET2
[google]
api_key = g-SECRET3
[myhost]
api_key = my-SECRET4
base_url = https://example.test/v1
[limits]
max_output_tokens = 100
max_calls = 0
"""


@pytest.fixture
def ini(tmp_path, monkeypatch):
    f = tmp_path / "keys.ini"
    f.write_text(INI, encoding="utf-8")
    monkeypatch.setenv("ADT_KEYS_FILE", str(f))
    for v in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY", "OPENROUTER_API_KEY"):
        monkeypatch.delenv(v, raising=False)
    monkeypatch.setattr(remote.time, "sleep", lambda s: None)
    monkeypatch.setattr(remote, "_calls", 0)
    return f


def test_names_route_by_prefix(ini):
    assert keys.split("anthropic:claude-x") == ("anthropic", "claude-x")
    assert keys.split("myhost:some/model:7b") == ("myhost", "some/model:7b")
    assert keys.split("llama3.1:8b") is None and not keys.is_remote("qwen2.5:7b")
    assert isinstance(models.make_runner("llama3.1:8b"), models.OllamaRunner)
    assert isinstance(models.make_runner("openai:gpt-x"), remote.RemoteRunner)


def test_missing_key_fails_before_any_call_and_names_no_key(ini):
    with pytest.raises(KeyError) as e:
        models.make_runner("groq:llama")
    assert "GROQ_API_KEY" in str(e.value)


def test_environment_fills_an_empty_key(ini, monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "env-SECRET5")
    assert keys.provider_config("groq")["api_key"] == "env-SECRET5"
    assert ("groq", "set", "environment, openai format") in keys.status()


def test_status_never_contains_a_key(ini):
    assert "SECRET" not in repr(keys.status())


def test_anthropic_wire_format(ini, monkeypatch):
    seen = {}
    def post(url, headers, body, timeout=180):
        seen.update(url=url, headers=headers, body=body)
        return {"model": "claude-x-2026", "content": [{"type": "text", "text": '{"ok": 1}'}], "usage": {"input_tokens": 7, "output_tokens": 3}}
    monkeypatch.setattr(remote, "_post", post)
    r = models.make_runner("anthropic:claude-x").generate("sys", "usr")
    assert (r.text, r.tokens_in, r.tokens_out) == ('{"ok": 1}', 7, 3)
    assert seen["url"].endswith("/v1/messages") and seen["headers"]["x-api-key"] == "sk-ant-SECRET1"
    assert seen["body"]["system"] == "sys" and seen["body"]["max_tokens"] == 100 and seen["body"]["temperature"] == 0.0


def test_google_key_goes_in_a_header_not_the_url(ini, monkeypatch):
    seen = {}
    def post(url, headers, body, timeout=180):
        seen.update(url=url, headers=headers, body=body)
        return {"candidates": [{"content": {"parts": [{"text": "hi"}]}}], "usageMetadata": {"promptTokenCount": 4, "candidatesTokenCount": 2, "thoughtsTokenCount": 5}}
    monkeypatch.setattr(remote, "_post", post)
    r = models.make_runner("google:gemini-x").generate("s", "u")
    assert "SECRET" not in seen["url"] and seen["headers"]["x-goog-api-key"] == "g-SECRET3"
    assert (r.text, r.tokens_in, r.tokens_out) == ("hi", 4, 7)


def test_openai_and_compatible_formats(ini, monkeypatch):
    seen = []
    def post(url, headers, body, timeout=180):
        seen.append((url, headers, body))
        return {"choices": [{"message": {"content": "yo"}}], "usage": {"prompt_tokens": 1, "completion_tokens": 1}}
    monkeypatch.setattr(remote, "_post", post)
    models.make_runner("openai:gpt-x").generate("s", "u")
    models.make_runner("myhost:m").generate("s", "u")
    (u1, h1, b1), (u2, h2, b2) = seen
    assert u1 == "https://api.openai.com/v1/chat/completions" and "max_completion_tokens" in b1 and h1["Authorization"] == "Bearer sk-oai-SECRET2"
    assert u2 == "https://example.test/v1/chat/completions" and "max_tokens" in b2


def http_error(code, body=b"", headers=None):
    import io
    return urllib.error.HTTPError("u", code, "x", headers or {}, io.BytesIO(body))


def test_bad_key_stops_the_run(ini, monkeypatch):
    monkeypatch.setattr(remote, "_post", lambda *a, **k: (_ for _ in ()).throw(http_error(401)))
    with pytest.raises(remote.AuthError) as e:
        models.make_runner("openai:gpt-x").generate("s", "u")
    assert "SECRET" not in str(e.value)


def test_a_server_error_is_retried_then_a_model_error_with_the_key_redacted(ini, monkeypatch):
    n = []
    def post(*a, **k):
        n.append(1)
        raise http_error(500, b"boom sk-oai-SECRET2 echoed")
    monkeypatch.setattr(remote, "_post", post)
    with pytest.raises(ModelError) as e:
        models.make_runner("openai:gpt-x").generate("s", "u")
    assert len(n) == 3 and "SECRET" not in str(e.value) and "[key]" in str(e.value)


def test_a_model_that_refuses_temperature_is_retried_without_it(ini, monkeypatch):
    bodies = []
    def post(url, headers, body, timeout=180):
        bodies.append(dict(body))
        if "temperature" in body:
            raise http_error(400, b"Unsupported value: 'temperature' does not support 0")
        return {"choices": [{"message": {"content": "ok"}}], "usage": {}}
    monkeypatch.setattr(remote, "_post", post)
    r = models.make_runner("openai:o-x")
    assert r.generate("s", "u").text == "ok" and "temperature" not in bodies[-1]
    assert r.describe()["temperature"] is None


def test_empty_reply_is_an_error_not_a_blank_answer(ini, monkeypatch):
    monkeypatch.setattr(remote, "_post", lambda *a, **k: {"choices": [{"message": {"content": ""}}], "usage": {}})
    with pytest.raises(ModelError):
        models.make_runner("openai:gpt-x").generate("s", "u")


def test_call_cap_stops_the_run(ini, monkeypatch):
    ini.write_text(INI.replace("max_calls = 0", "max_calls = 2"), encoding="utf-8")
    monkeypatch.setattr(remote, "_post", lambda *a, **k: {"choices": [{"message": {"content": "ok"}}], "usage": {}})
    r = models.make_runner("openai:gpt-x")
    r.generate("s", "u"); r.generate("s", "u")
    with pytest.raises(remote.SpendLimit):
        r.generate("s", "u")


def test_describe_marks_the_run_remote(ini, monkeypatch):
    monkeypatch.setattr(remote, "_post", lambda *a, **k: {"model": "gpt-x-2026-01-01", "choices": [{"message": {"content": "ok"}}], "usage": {}})
    r = models.make_runner("openai:gpt-x")
    r.generate("s", "u")
    d = r.describe()
    assert d["remote"] and d["provider"] == "openai" and d["reported_model"] == "gpt-x-2026-01-01" and "SECRET" not in repr(d)


def test_an_account_with_no_credit_stops_at_once_without_retrying(ini, monkeypatch):
    n = []
    def post(*a, **k):
        n.append(1)
        raise http_error(429, b'{"error": {"code": "insufficient_quota"}}')
    monkeypatch.setattr(remote, "_post", post)
    with pytest.raises(remote.AuthError, match="no usable credit"):
        models.make_runner("openai:gpt-x").generate("s", "u")
    assert len(n) == 1
