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
    assert streaks[0]["args_recorded"] is True


def test_a_streak_without_recorded_arguments_is_marked_as_such():
    """ASI10 logs a call's check-in but not its arguments, so two offers in one case look identical."""
    entries = [
        {"seq": 1, "actor": "agent", "action": "send_offer", "verdict": "allow", "reason": "ok", "saw": {"defense": "none", "case": "c1", "tick": 1}},
        {"seq": 2, "actor": "agent", "action": "send_offer", "verdict": "allow", "reason": "ok", "saw": {"defense": "none", "case": "c1", "tick": 4}},
    ]
    streaks = adl.detect_contiguous_loops(entries)
    assert len(streaks) == 1 and streaks[0]["args_recorded"] is False


def test_the_saved_logs_give_the_counts_the_docs_quote():
    """The duplicate-refund probe's 32 repeated refunds are found exactly, and ASI10's streaks are all without arguments."""
    path = adl.iter_decision_logs("asi03-duplicate-probe-20261016T174452")[0]
    assert adl.analyze_log(path)["repeat_allow_loops"] == 32
    repeats = [s for s in adl.detect_contiguous_loops(adl.read_entries(path)) if s["allowed"] >= 2]
    assert all(s["args_recorded"] and s["action"] == "issue_refund" for s in repeats)      # the harness's own error entries carry no arguments and are not among them
    rogue = adl.analyze_log(adl.iter_decision_logs("asi10-first-run-20261108T215243")[0])
    assert rogue["contiguous_loop_count"] == 40 and rogue["loops_args_unknown"] == 40


def test_analyze_log_on_saved_duplicate_probe():
    logs = adl.iter_decision_logs("asi03-duplicate-probe")
    assert logs, "expected saved duplicate probe decision logs"
    summary = adl.analyze_log(logs[0])
    assert summary["entries"] > 0
    assert summary["contiguous_loop_count"] > 0
    assert summary["repeat_allow_loops"] > 0
    assert summary["empty_reasons"] == 0
