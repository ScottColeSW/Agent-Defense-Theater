"""Loose-key detection and countermeasures (common/adt/loosekeys.py)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from adt import decisionlog, loosekeys as lk

GH = "ghp_" + "a1B2" * 10
REFRESH = "1//" + "Zq9_" * 10
NOW = "2026-10-30T00:00:00Z"


def test_scan_reports_fingerprints_and_never_the_token(tmp_path):
    (tmp_path / ".env").write_text(f"GITHUB_TOKEN={GH}\nrefresh_token: \"{REFRESH}\"\nnothing here\n", encoding="utf-8")
    (tmp_path / "app.log").write_text(f"Authorization: Bearer {'x' * 30}\n", encoding="utf-8")
    (tmp_path / ".git").mkdir(); (tmp_path / ".git" / "config").write_text(f"token={GH}\n", encoding="utf-8")
    found = lk.scan_paths([tmp_path])
    kinds = sorted((f.kind, f.exposure) for f in found)
    assert ("github", "config") in kinds and ("google_refresh", "config") in kinds and ("bearer", "log") in kinds
    assert len(found) == 3                       # the .git folder is skipped and one token is reported once, not once per shape
    dump = json.dumps([f.to_dict() for f in found])
    assert GH not in dump and REFRESH not in dump and "x" * 30 not in dump


def test_scan_env_names_the_variable_and_hides_the_value():
    found = lk.scan_env({"HOME": "/home/me", "GH_TOKEN": GH})
    assert [f.where for f in found] == ["env:GH_TOKEN"] and found[0].exposure == "env" and GH not in json.dumps(found[0].to_dict())


def test_audit_flags_and_actions():
    grants = [
        dict(id="never", app="a", kind="refresh", scopes=["read"], created="2026-08-01T00:00:00Z", last_used=None, expires=None),
        dict(id="idle", app="b", kind="access", scopes=["read"], created="2026-01-01T00:00:00Z", last_used="2026-08-01T00:00:00Z", expires="2026-12-01T00:00:00Z"),
        dict(id="wide", app="c", kind="access", scopes=["repo:*", "read"], created="2026-10-01T00:00:00Z", last_used="2026-10-29T00:00:00Z", expires="2026-11-01T00:00:00Z", scopes_used=["read"]),
        dict(id="fine", app="d", kind="access", scopes=["read"], created="2026-10-01T00:00:00Z", last_used="2026-10-29T00:00:00Z", expires="2026-11-15T00:00:00Z"),
        dict(id="new", app="e", kind="access", scopes=["read"], created="2026-10-28T00:00:00Z", last_used=None, expires="2026-11-28T00:00:00Z"),
        dict(id="dead", app="f", kind="access", scopes=["read"], created="2026-06-01T00:00:00Z", last_used="2026-10-20T00:00:00Z", expires="2026-09-01T00:00:00Z", active=True),
    ]
    got = {r["id"]: r for r in lk.audit_grants(grants, now=NOW)}
    assert "NEVER_USED" in got["never"]["flags"] and got["never"]["action"] == "revoke"
    assert "IDLE" in got["idle"]["flags"] and got["idle"]["action"] == "quarantine"
    assert {"WIDE_SCOPE", "UNUSED_SCOPES"} <= set(got["wide"]["flags"]) and got["wide"]["action"] == "narrow_scopes" and got["wide"]["narrow_to"] == ["read"]
    assert got["fine"]["flags"] == [] and got["fine"]["action"] == "keep"
    assert got["new"]["flags"] == []                                   # a brand new grant may be unused
    assert "EXPIRED_STILL_ACTIVE" in got["dead"]["flags"] and got["dead"]["action"] == "revoke"
    plan = lk.plan_countermeasures(list(got.values()))
    assert set(plan["revoke"]) == {"never", "dead"} and plan["quarantine"] == ["idle"]


def test_canary_is_alarmed_and_the_decision_log_verifies(tmp_path):
    reg = lk.CanaryRegistry(tmp_path / "canaries.json")
    canary = reg.plant("github", ".env of the build host", "bait")
    assert canary.startswith("ghp_") and canary not in (tmp_path / "canaries.json").read_text(encoding="utf-8")
    log = decisionlog.DecisionLog(tmp_path / "gate.decisions.jsonl")
    good = "real-token-aaaaaaaaaaaaaaaa"
    gate = lk.TokenGate({lk.fingerprint(good): {"sources": {"build-net"}, "suspended": False}}, reg.fingerprints, bind_source=True, log=log)
    assert gate.present(good, "build-net").verdict == "allow"
    assert gate.present(good, "elsewhere").verdict == "alarm"           # first use from a source it has never come from
    assert gate.present(canary, "elsewhere").verdict == "alarm"
    assert gate.present("not-a-token-we-issued", "elsewhere").verdict == "refuse"
    assert decisionlog.verify(log.path).ok and log.seq == 3       # the gate logs what it refuses or alarms on, not every allowed call
    hits = lk.check_events([f"GET /x 200 10.1.2.3 Bearer {canary}", "GET /y 200 ok"], reg.fingerprints)
    assert hits == [{"line": 1, "fingerprint": lk.fingerprint(canary), "from": "10.1.2.3"}]


def test_a_quarantined_token_refuses_until_the_owner_restores_it():
    tok = "quarantined-token-bbbbbbbbbbbb"
    gate = lk.TokenGate({lk.fingerprint(tok): {"sources": {"o"}, "suspended": True}}, set())
    assert gate.present(tok, "o").verdict == "refuse"


def test_scripted_comparison_keeps_its_headline_relations():
    by = lambda inside: {r["policy"]: r for r in lk.compare(inside=inside)}
    none, idle30, idle7, combo = "no countermeasure", "revoke idle at 30 days", "revoke idle at 7 days", "quarantine at 30 + bind to source + canary"
    easy, hard = by(0.0), by(0.25)
    # the thief's own use resets the idle clock, so idle revocation barely changes how many tokens it takes over
    assert easy[idle30]["tokens_taken_over"] >= 0.95 * easy[none]["tokens_taken_over"]
    # a short idle limit does stop the bot, and breaks most legitimate use to do it
    assert easy[idle7]["bot_successes"] < 0.5 * easy[none]["bot_successes"] and easy[idle7]["legit_broken_for_good"] > 10 * max(1, easy[idle30]["legit_broken_for_good"])
    # binding to a source plus canaries stops a bot from a new network, and only slows one with a foothold inside
    assert easy[combo]["bot_successes"] == 0 and easy[combo]["legit_broken_for_good"] == 0
    assert 0 < hard[combo]["bot_successes"] < hard[none]["bot_successes"]
    assert easy[none]["bot_successes"] == hard[none]["bot_successes"]
