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


def test_a_raising_observer_never_breaks_the_run_or_the_log(tmp_path):
    log_path = tmp_path / "noisy.decisions.jsonl"

    def boom(entry):
        raise RuntimeError("buggy observer")

    log = DecisionLog(log_path, observers=[boom])
    entry = log.append(
        actor="support-agent", tier="quiet", delegation=["user", "support-agent"],
        action="issue_refund", saw={"args": {"ticket_id": "T-1001", "amount": 10}},
        verdict="allow", reason="telemetry observer must not crash the run",
    )
    assert entry["seq"] == 1                      # append returned normally despite the raising observer
    v = verify(log_path)
    assert v.ok is True and v.entries == 1        # the entry was written and the hash chain stayed intact


def test_harness_loop_detect_opt_in_and_per_case_reset(tmp_path):
    import json
    from dataclasses import dataclass
    from types import SimpleNamespace
    from adt import harness
    from adt.models import Reply

    @dataclass
    class _Case:
        tier: str
        attack: str
        task: str
        data: dict

    class _Scenario:
        item = "ASI03"
        experiment = "loop-phase2a-test"
        crew = "test-crew"
        defenses = [SimpleNamespace(name="none", layer="none")]

        def cases(self):
            return [
                _Case("blind", "dup", "t1", {}),
                _Case("blind", "dup", "t2", {}),
            ]

        def run_case(self, case, defense, runner, log):
            # Case t1 emits two identical allowed calls (1 alert).
            # Case t2 starts with one identical allowed call (must NOT fire across case boundary).
            calls = 2 if case.task == "t1" else 1
            for _ in range(calls):
                log.append(
                    actor="agent",
                    tier="1",
                    delegation=[],
                    action="issue_refund",
                    verdict="allow",
                    reason="ok",
                    saw={"args": {"ticket_id": "T-1", "amount": 30}},
                )
            return harness.CaseResult(
                "attack_succeeded",
                Reply("done", 10, 5, 1),
                {"attempted": True, "exceeds_tier": False, "calls": calls, "denied": 0, "tier_ok": True},
            )

    runner = SimpleNamespace(name="scripted")

    # 1. Default (loop_detect=False): no sidecar, no loop keys in meta
    meta_off = harness.run(_Scenario(), [runner], tmp_path / "off", mode="scripted")
    assert "loop_detect" not in meta_off
    assert not (tmp_path / "off" / f"{meta_off['run_id']}.loops.jsonl").exists()

    # 2. Opt-in (loop_detect=True): sidecar written, per-case reset isolates t1 from t2, hash chain intact
    out_on = tmp_path / "on"
    meta_on = harness.run(_Scenario(), [runner], out_on, mode="scripted", loop_detect=True)
    assert meta_on["loop_detect"] is True
    assert meta_on["loop_alerts"] == 1

    loops_path = out_on / f"{meta_on['run_id']}.loops.jsonl"
    assert loops_path.exists()
    alerts = [json.loads(line) for line in loops_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(alerts) == 1
    assert alerts[0]["action"] == "issue_refund"
    assert alerts[0]["streak"] == 2
    assert alerts[0]["context"]["task"] == "t1"

    from adt import decisionlog
    v = decisionlog.verify(out_on / f"{meta_on['run_id']}.decisions.jsonl")
    assert v.ok, v.reason


def test_cli_summary_reports_loop_sidecar(tmp_path, monkeypatch, capsys):
    import json
    from adt import cli

    run_id = "asi03-test-20261122T000000-prereg"
    rec_path = tmp_path / f"{run_id}.jsonl"
    meta_path = tmp_path / f"{run_id}.meta.json"
    loops_path = tmp_path / f"{run_id}.loops.jsonl"

    rec_path.write_text(
        json.dumps({
            "run_id": run_id,
            "item": "ASI03",
            "tier": "blind",
            "attack": "dup",
            "defense": "none",
            "layer": "none",
            "model": "test-model",
            "crew": "crew",
            "outcome": "attack_succeeded",
            "tokens_in": 10,
            "tokens_out": 5,
            "latency_ms": 1,
            "mode": "live",
            "prereg": "p.md",
            "hardware_note": "cpu",
            "timestamp": "2026-11-22T00:00:00Z",
            "task": "t1",
            "model_ms": 1,
            "review_ms": 0,
            "gate_ms": 0,
            "attempted": True,
            "exceeds_tier": False,
            "calls": 2,
            "denied": 0,
            "tier_ok": True,
        }) + "\n",
        encoding="utf-8",
    )
    meta_path.write_text(json.dumps({"run_id": run_id, "loop_detect": True, "loop_alerts": 1}), encoding="utf-8")
    loops_path.write_text(json.dumps({"seq": 2, "action": "issue_refund", "streak": 2}) + "\n", encoding="utf-8")

    monkeypatch.setattr(cli, "_record_files", lambda item, include, exp: [rec_path])
    monkeypatch.setattr(cli, "experiments", lambda item: [])
    cli.main(["summary", "asi03"])
    out = capsys.readouterr().out
    assert "Loop detection: 1 LoopAlert(s) across 1 run(s)" in out
