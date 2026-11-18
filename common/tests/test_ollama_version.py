"""The Ollama server version is recorded in run metadata, null when it cannot be read (issue 11)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from adt import models


class _Resp:
    def __init__(self, body):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self):
        return self.body


def test_reads_the_server_version(monkeypatch):
    monkeypatch.setattr(models.urllib.request, "urlopen", lambda url, timeout: _Resp(b'{"version": "0.40.16"}'))
    assert models.ollama_version("http://x:11434") == "0.40.16"


def test_null_when_the_server_is_unreachable(monkeypatch):
    def boom(url, timeout):
        raise OSError("connection refused")
    monkeypatch.setattr(models.urllib.request, "urlopen", boom)
    assert models.ollama_version("http://x:11434") is None


def test_null_when_the_reply_has_no_version(monkeypatch):
    monkeypatch.setattr(models.urllib.request, "urlopen", lambda url, timeout: _Resp(b"{}"))
    assert models.ollama_version("http://x:11434") is None
