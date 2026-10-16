import io
import json
import sys
import urllib.error
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from adt import harness, models
from adt.loader import load_scenario
from adt.models import CachedRunner, ModelError, OllamaRunner, Reply


class Resp:
    def __init__(self, body):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def ok(content="{}", done_reason="stop"):
    return {"message": {"content": content}, "prompt_eval_count": 3, "eval_count": 2, "done_reason": done_reason}


def patch_urlopen(monkeypatch, fn):
    monkeypatch.setattr(models.urllib.request, "urlopen", fn)
    monkeypatch.setattr(models.json, "load", lambda r: r.body)
    monkeypatch.setattr(models.time, "sleep", lambda s: None)


def test_default_cap_and_timeout_apply_to_a_non_thinking_call_and_are_recorded(monkeypatch):
    seen = {}

    def fake(req, timeout):
        seen.update(body=json.loads(req.data), timeout=timeout)
        return Resp(ok())
    patch_urlopen(monkeypatch, fake)
    OllamaRunner("m").generate("s", "u")
    assert seen["body"]["options"]["num_predict"] == models.DEFAULT_NUM_PREDICT == 1024 and seen["timeout"] == models.TIMEOUT_S == 120


def test_a_thinking_call_keeps_its_larger_budget_and_longer_timeout(monkeypatch):
    seen = {}
    patch_urlopen(monkeypatch, lambda req, timeout: seen.update(body=json.loads(req.data), timeout=timeout) or Resp(ok()))
    OllamaRunner("m", think=True).generate("s", "u")
    assert seen["body"]["options"]["num_predict"] == 4096 and seen["timeout"] == models.THINK_TIMEOUT_S == 300


def test_an_explicit_cap_still_wins(monkeypatch):
    seen = {}
    patch_urlopen(monkeypatch, lambda req, timeout: seen.update(body=json.loads(req.data)) or Resp(ok()))
    OllamaRunner("m", num_predict=200).generate("s", "u")
    assert seen["body"]["options"]["num_predict"] == 200


def test_a_reply_cut_at_the_cap_is_marked_truncated(monkeypatch):
    patch_urlopen(monkeypatch, lambda req, timeout: Resp(ok('{"calls": [{"tool"', "length")))
    assert OllamaRunner("m").generate("s", "u").truncated is True
    patch_urlopen(monkeypatch, lambda req, timeout: Resp(ok()))
    assert OllamaRunner("m").generate("s", "u").truncated is False


def test_a_timeout_is_not_retried_and_says_why(monkeypatch):
    n = []
    patch_urlopen(monkeypatch, lambda req, timeout: n.append(1) or (_ for _ in ()).throw(TimeoutError()))
    with pytest.raises(ModelError, match="not retried") as e:
        OllamaRunner("m").generate("s", "u")
    assert len(n) == 1 and e.value.kind == "timeout" and "120 s" in str(e.value)


def test_a_repetition_loop_abort_is_not_retried_either(monkeypatch):
    n = []
    body = b'{"error":"prediction aborted, token repeat limit reached"}'
    patch_urlopen(monkeypatch, lambda req, timeout: n.append(1) or (_ for _ in ()).throw(urllib.error.HTTPError("http://x", 500, "err", {}, io.BytesIO(body))))
    with pytest.raises(ModelError) as e:
        OllamaRunner("m").generate("s", "u")
    assert len(n) == 1 and e.value.kind == "repeat_limit"


def test_an_ordinary_server_error_is_still_retried_once(monkeypatch):
    n = []
    patch_urlopen(monkeypatch, lambda req, timeout: n.append(1) or (_ for _ in ()).throw(urllib.error.HTTPError("http://x", 500, "err", {}, io.BytesIO(b"oom"))))
    with pytest.raises(ModelError) as e:
        OllamaRunner("m").generate("s", "u")
    assert len(n) == 2 and e.value.kind == ""


def test_cache_keeps_the_truncated_flag_and_counts_it():
    class R:
        name, model = "r", "r"

        def generate(self, system, user, hint=None, **o):
            return Reply("{", 1, 1, 5, truncated=True)
    c = CachedRunner(R())
    assert c.generate("s", "u").truncated and c.generate("s", "u").truncated            # the second is a cache hit
    assert c.truncations == 2


class Runaway:
    name = "runaway"
    model = "runaway"

    def __init__(self, mode):
        self.mode = mode

    def generate(self, system, user, hint=None, **o):
        if self.mode == "timeout":
            raise ModelError("runaway: timed out after 120 s", kind="timeout")
        return Reply('{"calls": [', 1, 1, 5, truncated=True)


def test_records_flag_runaway_and_truncated_cases(tmp_path):
    sc = load_scenario("asi03")
    only = [sc.defenses[0]]
    m1 = harness.run(sc, [Runaway("timeout")], tmp_path, mode="live", exploratory=True, progress=None, defenses=only)
    recs = [json.loads(l) for l in (tmp_path / f"{m1['run_id']}.jsonl").read_text(encoding="utf-8").splitlines()]
    assert recs and all(r["runaway"] is True and r["model_error_kind"] == "timeout" for r in recs)
    m2 = harness.run(sc, [Runaway("cut")], tmp_path, mode="live", exploratory=True, progress=None, defenses=only)
    recs = [json.loads(l) for l in (tmp_path / f"{m2['run_id']}.jsonl").read_text(encoding="utf-8").splitlines()]
    assert recs and all(r.get("truncated") is True for r in recs) and not any(r.get("runaway") for r in recs)
