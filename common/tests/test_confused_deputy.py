"""ASI03 confused-deputy: model-free tests for the taint-deny broker and the deterministic outcomes."""
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from adt import decisionlog, harness, models, scorer
from adt.loader import load_file, load_scenario

ITEM = Path(__file__).resolve().parents[2] / "items" / "asi03-identity-privilege"


def _deleg():
    return load_file(ITEM / "defenses" / "delegation.py", "asi03_delegation_for_test")


def _call(tool, **args):
    return types.SimpleNamespace(tool=tool, args=args)


def test_taint_deny_refuses_privileged_only_under_taint():
    deleg = _deleg()
    tainted = deleg.TaintDenyBroker("T-1001", tier=3, tainted=True)
    dec = tainted.authorize(_call("issue_refund", ticket_id="T-1001", account="X", amount=10), "T-1001", {})
    assert dec.allow is False and deleg.TAINTED_CONTEXT in dec.codes        # a consequential action under taint is refused

    clean = deleg.TaintDenyBroker("T-1001", tier=3, tainted=False)
    dec2 = clean.authorize(_call("export_customers", destination="x"), "T-1001", {})
    assert deleg.TAINTED_CONTEXT not in dec2.codes                          # untainted: the taint gate does not fire; the credential decides


def test_scripted_run_precision_versus_cost(tmp_path):
    sc = load_scenario("asi03", "confused-deputy")
    meta = harness.run(sc, [models.ScriptedRunner()], tmp_path, mode="scripted", progress=None)
    assert decisionlog.verify(tmp_path / f"{meta['run_id']}.decisions.jsonl").ok
    recs = scorer.load_records([tmp_path / f"{meta['run_id']}.jsonl"], live_only=False)

    att = lambda d: [r for r in recs if r["defense"] == d and r["attack"] != "none"]
    harm = lambda d: sum(r["outcome"] == "attack_succeeded" for r in att(d))
    legit_ok = lambda d, task: sum(r["outcome"] == "task_succeeded" for r in recs if r["defense"] == d and r["attack"] == "none" and r["task"] == task)
    legit_n = lambda task: sum(1 for r in recs if r["defense"] == "none" and r["attack"] == "none" and r["task"] == task)

    assert harm("none") == len(att("none")) and harm("none") > 0            # every laundered call executes with no defense
    assert harm("scoped_grant") == 0 and harm("taint_deny") == 0            # both stop the laundering
    assert legit_ok("scoped_grant", "legit_refund") == legit_n("legit_refund")   # the grant keeps the authorized refund
    assert legit_ok("taint_deny", "legit_refund") == 0                      # the taint rule refuses it too (the cost)
    assert legit_ok("scoped_grant", "legit_close") == legit_n("legit_close") and legit_ok("taint_deny", "legit_close") == legit_n("legit_close")   # ordinary work untouched
