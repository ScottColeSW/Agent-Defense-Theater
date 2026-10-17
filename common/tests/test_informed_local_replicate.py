import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from adt import cli, informed, models
from adt.loader import experiments, load_scenario


def test_listed_and_runs_as_a_scripted_continuation(tmp_path):
    assert "informed-local-replicate" in experiments("asi03")
    first = informed.run("asi03", cli._ScriptedAttacker(), [models.ScriptedRunner()], mode="scripted", out_dir=tmp_path, rounds=1, progress=None)
    hist = informed.history_from_session(first["file"])
    nxt = cli._ScriptedAttacker()
    nxt.n = 1
    s = informed.run("asi03", nxt, [models.ScriptedRunner()], mode="scripted", out_dir=tmp_path, rounds=3, progress=None, scenario_name="informed-local-replicate",
                     start_round=2, history=hist, resumed_from=first["file"])
    assert s["complete"] and s["scenario"] == "informed-local-replicate"
    sess, recs = informed.merged_records(s["file"])
    mod = sys.modules[load_scenario("asi03", "informed-local-replicate").__class__.__module__]
    bar = {c["id"]: c for c in mod.evaluate(recs, {"session": s, "spend": s["spend"]})}
    assert sorted(bar) == list(range(1, 8))
    assert bar[1]["status"] == "missed" and "have a reading" in bar[1]["result"]           # a scripted run has no cooler, so no GPU readings
    assert bar[2]["status"] == "met" and bar[7]["status"] == "met" and bar[6]["status"] == "met"


def test_the_cooler_criterion_passes_when_readings_are_present_and_cool():
    mod = sys.modules[load_scenario("asi03", "informed-local-replicate").__class__.__module__]
    rec = lambda t, d="none": dict(attack="a", defense=d, round=2, task_label="A", outcome="blocked", gpu_temp_c=t)
    assert mod.evaluate([rec(60), rec(69)], {})[0]["status"] == "met"
    assert mod.evaluate([rec(60), rec(71)], {})[0]["status"] == "missed"
    assert mod.evaluate([rec(60), dict(rec(60), gpu_temp_c=None)], {})[0]["status"] == "missed"
