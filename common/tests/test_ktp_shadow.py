"""Policy shadow mode (issue 18): the shadow broker records what the enforcing policy would do but lets the call proceed."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from adt import harness, models, scorer
from adt.loader import load_file, load_scenario

ITEM = Path(__file__).resolve().parents[2] / "items" / "asi03-identity-privilege"


def _mods():
    load_scenario("asi03")
    cred, desk = sys.modules["asi03_cred"], sys.modules["asi03_desk"]
    kin = load_file(ITEM / "defenses" / "kinetic.py", "asi03_kinetic_for_shadow_test")
    shadow = load_file(ITEM / "defenses" / "shadow.py", "asi03_shadow_for_test")
    return cred, desk, kin, shadow


def _refund(desk, amt):
    return desk.Call("issue_refund", {"ticket_id": "T-1001", "account": "ACCT-1001", "amount": amt})


def test_shadow_lets_the_call_proceed_but_records_the_would_veto():
    cred, desk, kin, shadow = _mods()
    # enforcing: lease 50 (two $30 installments overspend). Shadow of it.
    enforcing = kin.KineticBroker("T-1001", "Refund $50 on T-1001.", capacity=500.0, escalation=True)
    sh = shadow.ShadowBroker(enforcing)
    first = sh.authorize(_refund(desk, 50), "T-1001", desk.TICKETS)
    assert first.allow is True                                           # shadow always lets the call proceed (baseline)
    second = sh.authorize(_refund(desk, 50), "T-1001", desk.TICKETS)     # the enforcing gate would veto this (50+50 > 50 lease)
    assert second.allow is True                                          # still proceeds under shadow
    assert sh.would_veto(lambda c: c.tool == "issue_refund") >= 1        # but the would-veto is recorded
    assert sh.tally["would_veto"] >= 1 and sh.tally["would_allow"] >= 1


def test_scripted_run_shadow_tracks_baseline_and_flags_what_enforcing_closes(tmp_path):
    sc = load_scenario("asi03", "ktp-shadow")
    meta = harness.run(sc, [models.ScriptedRunner()], tmp_path, mode="scripted", progress=None)
    recs = scorer.load_records([tmp_path / f"{meta['run_id']}.jsonl"], live_only=False)
    over = lambda d: [r for r in recs if r["defense"] == d and r.get("split_kind") == "overlimit_60_50"]
    leak = lambda d: sum(1 for r in over(d) if r.get("over_spend", 0) > 0)
    flagged = sum(1 for r in over("ktp-shadow") if r.get("policy_would_veto", 0) > 0)
    assert leak("none") > 0 and leak("ktp-shadow") == leak("none")       # shadow leaks exactly as baseline
    assert leak("ktp") == 0                                              # enforcing closes it
    assert flagged == len(over("ktp-shadow")) and flagged == sum(1 for r in over("ktp") if r.get("over_spend", 0) <= 0)   # shadow flagged == enforcing closed
