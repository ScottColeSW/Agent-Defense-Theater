import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from adt import harness, models, scorer
from adt.loader import experiments, load_scenario


def test_listed_and_same_cases_as_the_probe():
    assert "duplicate-probe-replicate" in experiments("asi03")
    a, b = load_scenario("asi03", "duplicate-probe").cases(), load_scenario("asi03", "duplicate-probe-replicate").cases()
    assert [(c.attack, c.task, c.data["ticket"], c.data["injection"]) for c in a] == [(c.attack, c.task, c.data["ticket"], c.data["injection"]) for c in b] and len(b) == 18


def test_pass_bar_reads_a_scripted_run_and_says_where_it_differs_from_the_live_probe(tmp_path):
    sc = load_scenario("asi03", "duplicate-probe-replicate")
    meta = harness.run(sc, [models.ScriptedRunner()], tmp_path, mode="scripted", progress=None)
    recs = scorer.load_records([tmp_path / f"{meta['run_id']}.jsonl"], live_only=False)
    bar = sc.pass_bar(scorer.summarize(recs), {"records": recs})
    assert [c["id"] for c in bar] == [1, 2, 3, 4]
    assert bar[0]["status"] == "missed"          # one scripted victim gives 18 cases a condition, not 54
    assert bar[1]["status"] == "met" and bar[2]["status"] == "met" and bar[3]["status"] == "met"


def test_prediction_interval_is_thirty_to_thirty_four_of_fifty_four():
    sc = load_scenario("asi03", "duplicate-probe-replicate")
    assert round(sc.predictions["none"]["lo"] * 54) == 30 and round(sc.predictions["none"]["hi"] * 54) == 34
