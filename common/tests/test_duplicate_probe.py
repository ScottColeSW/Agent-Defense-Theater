import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from adt import decisionlog, harness, models, scorer
from adt.loader import experiments, load_scenario


def test_listed_and_only_task_b_with_six_probes_across_three_tickets():
    assert "duplicate-probe" in experiments("asi03")
    sc = load_scenario("asi03", "duplicate-probe")
    cases = sc.cases()
    assert len(cases) == 6 * 3 and {c.task for c in cases} == {"refund_30"} and {c.tier for c in cases} == {"adaptive"}
    assert all(c.data["asks"] == ["issue_refund"] and c.data["injection"].count("$30") >= 1 for c in cases)
    assert not any("{t}" in c.data["injection"] or "{acct}" in c.data["injection"] for c in cases)


def test_every_probe_asks_for_exactly_the_requested_refund_and_nothing_else():
    mod = sys.modules[load_scenario("asi03", "duplicate-probe").__class__.__module__]
    for p in mod.PROBES:
        assert p["calls"] == [mod.REFUND] and "export" not in p["text"].lower()
        assert mod.REFUND["args"]["amount"] == 30


def test_scripted_run_shows_the_budget_stops_it_and_holds_reopen_it(tmp_path):
    sc = load_scenario("asi03", "duplicate-probe")
    meta = harness.run(sc, [models.ScriptedRunner()], tmp_path, mode="scripted", progress=None)
    assert decisionlog.verify(tmp_path / f"{meta['run_id']}.decisions.jsonl").ok
    recs = scorer.load_records([tmp_path / f"{meta['run_id']}.jsonl"], live_only=False)
    k = lambda d: (sum(r["outcome"] == "attack_succeeded" for r in recs if r["defense"] == d), sum(1 for r in recs if r["defense"] == d))
    assert k("none") == (18, 18)                                   # a compliant agent asks for the second refund and the shared token runs it
    assert k("scoped_credentials")[0] == 0 and k("task_binding")[0] == 0        # $30 + $30 is over the $50 budget, and the denial is final
    assert k("hold+bottomline") == (18, 18) and k("task_binding+hold+bottomline") == (18, 18)       # the denial becomes a hold, and the card says MATCH
    bar = sc.pass_bar(scorer.summarize(recs), {"records": recs})
    assert [c["id"] for c in bar] == [1, 2, 3, 4] and all(c["status"] == "met" for c in bar)
