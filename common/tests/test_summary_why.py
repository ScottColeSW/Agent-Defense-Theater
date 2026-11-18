"""adt summary --why lists in-tier valid work that did not complete, with why (issue 5)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from adt import cli


def _rec(**kw):
    base = dict(attack="none", tier_ok=True, outcome="task_succeeded", defense="none", model="m",
                task="refund_30", ticket="T-1001", calls=1, denied=0, holds=0, model_error=None, attempted=True)
    base.update(kw)
    return base


def test_why_lists_a_broker_veto_with_its_reason(tmp_path, capsys):
    jsonl = tmp_path / "run.jsonl"
    (tmp_path / "run.decisions.jsonl").write_text(
        json.dumps({"actor": "support-agent", "verdict": "deny", "reason": "nope",
                    "saw": {"defense": "ktp+E30", "case": "none/refund_30/T-1001", "codes": ["KINETIC_CAPACITY_EXCEEDED"]}}) + "\n",
        encoding="utf-8")
    recs = [_rec(defense="ktp+E30", model="llama3.1:8b", outcome="blocked", denied=1)]
    cli._why([jsonl], recs)
    out = capsys.readouterr().out
    assert "refund_30" in out and "broker vetoed" in out and "KINETIC_CAPACITY_EXCEEDED" in out


def test_why_labels_a_model_that_made_no_call(tmp_path, capsys):
    cli._why([tmp_path / "run.jsonl"], [_rec(outcome="task_failed", calls=0, attempted=False)])
    assert "made no tool call" in capsys.readouterr().out


def test_why_is_empty_when_all_in_tier_work_completed(tmp_path, capsys):
    cli._why([tmp_path / "run.jsonl"], [_rec(outcome="task_succeeded")])
    assert "No in-tier valid work failed to complete" in capsys.readouterr().out


def test_why_filters_by_defense_and_skips_above_tier(tmp_path, capsys):
    recs = [_rec(defense="ktp", outcome="blocked", denied=1),
            _rec(defense="other", outcome="blocked", denied=1),
            _rec(defense="ktp", tier_ok=False, outcome="blocked", task="refund_200")]   # above-tier, not listed
    cli._why([tmp_path / "run.jsonl"], recs, defense_filter="ktp")
    out = capsys.readouterr().out
    assert "ktp" in out and "other" not in out and "refund_200" not in out
