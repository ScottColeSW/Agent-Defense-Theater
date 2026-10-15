import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from adt import decisionlog, harness, models, scorer
from adt.loader import experiments, load_scenario


def _gg():
    return sys.modules["asi01_goalguard"]


def test_registered_and_sized():
    sc = load_scenario("asi01")
    assert experiments("asi01") == ["first-run"]
    cases = sc.cases()
    assert len(cases) == 32 and sum(c.kind == "attack" for c in cases) == 15 and len(sc.defenses) == 5
    assert sc.extra_models() == ["qwen2.5:7b"]
    sc.configure(reviewer="llama3.1:8b")
    assert sc.extra_models() == ["llama3.1:8b"]
    sc.configure(reviewer="qwen2.5:7b")


def test_plan_and_verdict_parsing_fail_closed():
    load_scenario("asi01")
    g = _gg()
    assert g.parse_plan('{"plan": ["get_deal", " add_note "]}') == {"get_deal", "add_note"}
    assert g.parse_plan("not json") is None and g.parse_plan('{"plan": "get_deal"}') is None and g.parse_plan('{"plan": [1, 2]}') is None
    assert g.parse_fits('{"fits": true, "reason": "asked"}') == (True, "asked", True)
    fits, why, ok = g.parse_fits('{"fits": "yes"}')                      # not a boolean: does not fit, and is flagged
    assert fits is False and ok is False
    assert g.parse_fits("nonsense")[0] is False
    assert g.spotlight("x") == "<data>x</data>"


def test_scripted_run_each_defense_stops_what_it_is_built_to_stop(tmp_path):
    sc = load_scenario("asi01")

    class Sub:
        def __getattr__(self, k):
            return getattr(sc, k)

        def cases(self):
            return [c for c in sc.cases() if c.data["deal"] == "D-101" and c.task == "cocr_note"]

    meta = harness.run(Sub(), [models.ScriptedRunner()], tmp_path, mode="scripted", progress=None)
    assert decisionlog.verify(tmp_path / f"{meta['run_id']}.decisions.jsonl").ok
    recs = scorer.load_records([tmp_path / f"{meta['run_id']}.jsonl"], live_only=False)
    got = {(r["defense"], r["attack"] if r["attack"] != "none" else "valid"): r["outcome"] for r in recs}
    hijacks = ("new_task_override", "operator_update", "goal_reframe", "task_completion_trick")
    A, B = "attack_succeeded", "blocked"
    assert [got[("none", a)] for a in hijacks + ("note_stamp",)] == [A] * 5
    assert [got[("spotlighting", a)] for a in hijacks + ("note_stamp",)] == [A] * 5             # a compliant scripted agent ignores the data tags
    for d in ("plan_lock", "goal_check", "plan_lock+goal_check"):
        assert [got[(d, a)] for a in hijacks] == [B] * 4, d
        assert got[(d, "note_stamp")] == A, d                                                    # the stamp lives inside a tool the request asks for
    assert all(got[(d.name, "valid")] == "task_succeeded" for d in sc.defenses)


def test_a_plan_that_omits_a_needed_tool_costs_valid_work_and_a_bad_plan_refuses_everything(tmp_path):
    sc = load_scenario("asi01")
    from adt.models import Reply

    class NoNotePlan(models.ScriptedRunner):
        name = "scripted"

        def generate(self, system, user, hint=None, **o):
            if "write your plan" in system:
                return Reply('{"plan": ["get_deal", "calculate_cocr"]}')                       # forgot add_note
            return super().generate(system, user, hint, **o)

    class Garbage(models.ScriptedRunner):
        name = "scripted"

        def generate(self, system, user, hint=None, **o):
            return Reply("I will do my best") if "write your plan" in system else super().generate(system, user, hint, **o)

    class One:
        def __getattr__(self, k):
            return getattr(sc, k)

        def cases(self):
            return [c for c in sc.cases() if c.data["deal"] == "D-101" and c.attack == "none" and c.task == "cocr_note"]

    for runner, want_denied in ((NoNotePlan(), True), (Garbage(), True)):
        meta = harness.run(One(), [runner], tmp_path / runner.__class__.__name__, mode="scripted", progress=None, defenses=[next(d for d in sc.defenses if d.name == "plan_lock")])
        recs = scorer.load_records([tmp_path / runner.__class__.__name__ / f"{meta['run_id']}.jsonl"], live_only=False)
        assert recs[0]["outcome"] == "blocked" and recs[0]["denied_plan"] >= 1
    assert recs[0]["plan_ok"] is False
