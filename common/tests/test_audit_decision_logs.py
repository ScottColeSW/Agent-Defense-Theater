import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import audit_decision_logs as adl


def test_detect_contiguous_loops_flags_consecutive_identical_calls():
    entries = [
        {"seq": 1, "actor": "support-agent", "action": "issue_refund", "verdict": "allow",
         "reason": "ok", "saw": {"defense": "none", "case": "c1", "args": {"amount": 30}}},
        {"seq": 2, "actor": "support-agent", "action": "issue_refund", "verdict": "allow",
         "reason": "ok", "saw": {"defense": "none", "case": "c1", "args": {"amount": 30}}},
        {"seq": 3, "actor": "support-agent", "action": "get_ticket", "verdict": "allow",
         "reason": "ok", "saw": {"defense": "none", "case": "c1", "args": {"id": "T-1"}}},
        # Non-contiguous identical call in a different case must not merge
        {"seq": 4, "actor": "support-agent", "action": "issue_refund", "verdict": "allow",
         "reason": "ok", "saw": {"defense": "none", "case": "c2", "args": {"amount": 30}}},
    ]
    streaks = adl.detect_contiguous_loops(entries, min_streak=2)
    assert len(streaks) == 1
    assert streaks[0]["seq_start"] == 1
    assert streaks[0]["seq_end"] == 2
    assert streaks[0]["streak_length"] == 2
    assert streaks[0]["allowed"] == 2


def test_analyze_log_on_saved_duplicate_probe():
    logs = adl.iter_decision_logs("asi03-duplicate-probe")
    assert logs, "expected saved duplicate probe decision logs"
    summary = adl.analyze_log(logs[0])
    assert summary["entries"] > 0
    assert summary["contiguous_loop_count"] > 0
    assert summary["repeat_allow_loops"] > 0
    assert summary["empty_reasons"] == 0
