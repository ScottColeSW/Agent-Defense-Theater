import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from adt.loader import experiments, load_scenario


def test_listed_and_judged_by_the_replicate_pass_bar():
    assert "informed-local-seeds" in experiments("asi03")
    sc = load_scenario("asi03", "informed-local-seeds")
    assert sc.experiment == "informed-local-seeds" and sc.prereg_path.name == "PREREGISTRATION-informed-local-seeds.md" and sc.needs_orchestrator
    mod = sys.modules[sc.__class__.__module__.replace("seeds", "replicate")] if False else sys.modules[load_scenario("asi03", "informed-local-replicate").__class__.__module__]
    assert [c["id"] for c in sc.pass_bar([], {})] == list(range(1, 8))


def test_summary_works_for_every_informed_experiment_including_ones_that_inherit_their_pass_bar(tmp_path):
    from adt import cli, informed, models
    first = informed.run("asi03", cli._ScriptedAttacker(), [models.ScriptedRunner()], mode="scripted", out_dir=tmp_path, rounds=1, progress=None)
    hist = informed.history_from_session(first["file"])
    for name in ("informed-local", "informed-local-replicate", "informed-local-seeds"):
        nxt = cli._ScriptedAttacker()
        nxt.n = 1
        s = informed.run("asi03", nxt, [models.ScriptedRunner()], mode="scripted", out_dir=tmp_path, rounds=2, progress=None, scenario_name=name,
                         start_round=2, history=hist, resumed_from=first["file"])
        assert "Pass bar:" in informed.summarize(s["file"]), name


def test_a_failed_model_call_has_no_round_and_does_not_break_the_summary(tmp_path):
    import json
    from adt import cli, informed, models
    first = informed.run("asi03", cli._ScriptedAttacker(), [models.ScriptedRunner()], mode="scripted", out_dir=tmp_path, rounds=1, progress=None)
    s = json.loads(Path(first["file"]).read_text(encoding="utf-8"))
    path = tmp_path / f"{s['rounds'][0]['run_id']}.jsonl"
    lines = path.read_text(encoding="utf-8").splitlines()
    rec = json.loads(next(l for l in lines if '"attack": "none"' not in l))
    rec.pop("round", None)
    rec["model_error"] = "timed out"
    path.write_text("\n".join(lines + [json.dumps(rec)]) + "\n", encoding="utf-8")
    assert "Pass bar:" in informed.summarize(first["file"])


def test_a_session_that_resumes_itself_is_refused_not_recursed(tmp_path):
    import json
    import pytest
    from adt import cli, informed, models
    first = informed.run("asi03", cli._ScriptedAttacker(), [models.ScriptedRunner()], mode="scripted", out_dir=tmp_path, rounds=1, progress=None)
    s = json.loads(Path(first["file"]).read_text(encoding="utf-8"))
    s["resumed_from"] = first["file"]
    Path(first["file"]).write_text(json.dumps(s), encoding="utf-8")
    with pytest.raises(ValueError, match="continues itself"):
        informed.merged_records(first["file"])


def test_two_sessions_in_the_same_second_get_different_files(tmp_path):
    from adt import cli, informed, models
    a = informed.run("asi03", cli._ScriptedAttacker(), [models.ScriptedRunner()], mode="scripted", out_dir=tmp_path, rounds=1, progress=None)
    b = informed.run("asi03", cli._ScriptedAttacker(), [models.ScriptedRunner()], mode="scripted", out_dir=tmp_path, rounds=1, progress=None)
    assert a["file"] != b["file"] and Path(a["file"]).exists() and Path(b["file"]).exists()
