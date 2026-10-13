import sys
import urllib.error
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from adt import decisionlog, harness, models, scorer
from adt.loader import load_scenario
from adt.models import CachedRunner, ModelError, OllamaRunner, Reply


class Failing:
    name = "failing"
    calls = 0

    def generate(self, system, user, hint=None):
        Failing.calls += 1
        raise ModelError("failing: HTTP 500 (after one retry)")


def test_a_failing_model_does_not_stop_the_run_and_is_counted(tmp_path):
    sc = load_scenario("asi03")
    Failing.calls = 0
    meta = harness.run(sc, [Failing()], tmp_path, mode="live", exploratory=True, progress=None, defenses=[sc.defenses[0], sc.defenses[2]])   # none and scoped share one prompt
    recs = scorer.load_records([tmp_path / f"{meta['run_id']}.jsonl"])
    assert len(recs) == len(sc.cases()) * 2 and all(r["outcome"] == "task_failed" and r["model_error"] for r in recs)
    assert decisionlog.verify(tmp_path / f"{meta['run_id']}.decisions.jsonl").ok
    assert Failing.calls == len(sc.cases())                       # the second defense reuses the failure, it does not call again
    rows = scorer.summarize(recs)
    assert all(r["errors"] == len(sc.cases()) for r in rows) and "model errors" in scorer.format_table(rows)
    assert all(r["success"]["k"] == 0 for r in rows)              # an errored case is never an attack success


def test_reviewer_error_fails_closed():
    sc = load_scenario("asi03", "escalation")
    esc = sys.modules["asi03_esc"]
    v = esc.LlmReviewer(Failing()).decide("card", {})
    assert v.approve is False and "denied" in v.reason


def _http(code):
    return urllib.error.HTTPError("http://x", code, "err", {}, None)


def test_server_error_is_retried_once_then_raised(monkeypatch):
    seen = []
    monkeypatch.setattr(models.time, "sleep", lambda s: None)
    monkeypatch.setattr(models.urllib.request, "urlopen", lambda req, timeout: seen.append(1) or (_ for _ in ()).throw(_http(500)))
    with pytest.raises(ModelError, match="HTTP 500"):
        OllamaRunner("m").generate("s", "u")
    assert len(seen) == 2


def test_server_not_running_stops_the_run_instead_of_recording_errors(monkeypatch):
    monkeypatch.setattr(models.urllib.request, "urlopen",
                        lambda req, timeout: (_ for _ in ()).throw(urllib.error.URLError(ConnectionRefusedError())))
    with pytest.raises(RuntimeError, match="not reachable"):
        OllamaRunner("m").generate("s", "u")


def test_a_transient_failure_recovers_on_the_retry(monkeypatch):
    class Resp:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self, *a): return b'{"message": {"content": "{}"}, "prompt_eval_count": 3, "eval_count": 2}'

    n = {"i": 0}

    def flaky(req, timeout):
        n["i"] += 1
        if n["i"] == 1:
            raise _http(500)
        return Resp()

    monkeypatch.setattr(models.time, "sleep", lambda s: None)
    monkeypatch.setattr(models.urllib.request, "urlopen", flaky)
    monkeypatch.setattr(models.json, "load", lambda r: {"message": {"content": "{}"}, "prompt_eval_count": 3, "eval_count": 2})
    r = OllamaRunner("m").generate("s", "u")
    assert r.text == "{}" and r.tokens_in == 3 and n["i"] == 2
