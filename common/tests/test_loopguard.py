"""Unit tests for the live runtime duplicate tool-loop detector (issue #12)."""
from adt.decisionlog import DecisionLog, verify
from adt.loopguard import RuntimeLoopDetector


def test_detects_contiguous_duplicate_allow(tmp_path):
    log_path = tmp_path / "run.decisions.jsonl"
    detector = RuntimeLoopDetector()
    log = DecisionLog(log_path, observers=[detector.observe])

    log.append(
        actor="support-agent",
        tier="quiet",
        delegation=["user", "support-agent"],
        action="issue_refund",
        saw={"args": {"ticket_id": "T-1003", "account": "ACCT-1003", "amount": 30}},
        verdict="allow",
        reason="shared service token svc-desk holds every scope",
    )
    assert len(detector.alerts) == 0

    log.append(
        actor="support-agent",
        tier="quiet",
        delegation=["user", "support-agent"],
        action="issue_refund",
        saw={"args": {"amount": 30, "account": "ACCT-1003", "ticket_id": "T-1003"}},
        verdict="allow",
        reason="shared service token svc-desk holds every scope",
    )
    assert len(detector.alerts) == 1
    alert = detector.alerts[0]
    assert alert.seq == 2
    assert alert.prev_seq == 1
    assert alert.actor == "support-agent"
    assert alert.action == "issue_refund"
    assert alert.streak == 2

    v = verify(log_path)
    assert v.ok is True
    assert v.entries == 2


def test_ignores_failure_recovery_and_harness_retries(tmp_path):
    log_path = tmp_path / "control.decisions.jsonl"
    detector = RuntimeLoopDetector()
    log = DecisionLog(log_path, observers=[detector.observe])

    log.append(
        actor="support-agent",
        tier="quiet",
        delegation=["user", "support-agent"],
        action="issue_refund",
        saw={"args": {"ticket_id": "T-1002", "amount": 25}},
        verdict="deny",
        reason="temporary validation failure",
    )
    log.append(
        actor="support-agent",
        tier="quiet",
        delegation=["user", "support-agent"],
        action="issue_refund",
        saw={"args": {"ticket_id": "T-1002", "amount": 25}},
        verdict="allow",
        reason="retry succeeded",
    )
    assert len(detector.alerts) == 0

    for _ in range(2):
        log.append(
            actor="harness",
            tier="quiet",
            delegation=[],
            action="model call",
            saw={},
            verdict="error",
            reason="llama3.1:8b: timed out (after one retry)",
        )
    assert len(detector.alerts) == 0

    log.append(
        actor="support-agent",
        tier="quiet",
        delegation=["user", "support-agent"],
        action="issue_refund",
        saw={"args": {"ticket_id": "T-1005", "amount": 15}},
        verdict="allow",
        reason="valid distinct ticket",
    )
    assert len(detector.alerts) == 0
