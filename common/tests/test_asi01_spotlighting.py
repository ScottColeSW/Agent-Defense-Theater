import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from adt import harness, models, scorer
from adt.loader import experiments, load_scenario
from adt.models import Reply


def _mod():
    sc = load_scenario("asi01", "spotlighting")
    return sc, sys.modules[type(sc).__module__]


def test_registered_sized_and_the_first_runs_condition_is_unchanged():
    sc, mod = _mod()
    assert experiments("asi01") == ["first-run", "spotlighting"]
    cases = sc.cases()
    assert len(cases) == 30 and sum(c.kind == "attack" for c in cases) == 25 and len(sc.defenses) == 7 and sc.extra_models() == []
    assert sum(1 for c in cases if c.kind == "attack" and c.data["deal"] in mod.NEW_DEALS) == 10
    assert mod.SPEC["spotlighting"] == (mod.gg.SPOTLIGHT, True)                                   # exactly what the first run used
    first = load_scenario("asi01")
    assert first.prompt_spec("spotlighting") == (mod.gg.SPOTLIGHT, True) and first.prompt_spec("plan_lock") == ("", False)
    assert set(sc.predictions) == {d.name for d in sc.defenses}


def test_each_condition_puts_exactly_its_rule_and_tags_in_the_prompt_and_nothing_else_changes(tmp_path):
    sc, mod = _mod()
    seen = {}

    class Recorder(models.ScriptedRunner):
        name = "scripted"

        def generate(self, system, user, hint=None, **o):
            seen.setdefault(self.defense, []).append((system, user))
            return super().generate(system, user, hint, **o)

    class One:
        def __getattr__(self, k):
            return getattr(sc, k)

        def cases(self):
            return [c for c in sc.cases() if c.data["deal"] == "D-104" and c.attack in ("goal_reframe", "none")]

    for d in sc.defenses:
        rec = Recorder()
        rec.defense = d.name
        harness.run(One(), [rec], tmp_path / d.name, mode="scripted", progress=None, defenses=[d])
    base = seen["none"][0][0]
    for name, (rule, wrap) in mod.SPEC.items():
        systems = {s for s, _ in seen[name]}
        assert systems == {base + rule}, name                                                       # the only difference in the system prompt is the rule
        later = [u for _, u in seen[name] if "Tool results so far" in u]
        assert later and all(("<data>" in u) == wrap for u in later), name                          # and tags appear only where they are meant to


def test_scripted_agent_is_hijacked_and_clean_work_succeeds_under_every_condition(tmp_path):
    sc, mod = _mod()

    class Few:
        def __getattr__(self, k):
            return getattr(sc, k)

        def cases(self):
            return [c for c in sc.cases() if c.data["deal"] == "D-105"]

    meta = harness.run(Few(), [models.ScriptedRunner()], tmp_path, mode="scripted", progress=None)
    recs = scorer.load_records([tmp_path / f"{meta['run_id']}.jsonl"], live_only=False)
    attacks = [r for r in recs if r["attack"] != "none"]
    assert len(attacks) == 5 * 7 and all(r["outcome"] == "attack_succeeded" for r in attacks)       # prompts alone do not stop a scripted, compliant agent
    clean = [r for r in recs if r["attack"] == "none"]
    assert len(clean) == 7 and all(r["outcome"] == "task_succeeded" and not r["exceeds_tier"] for r in clean)
    rows = scorer.summarize(recs, ("defense",))
    bar = sc.pass_bar(rows, {"records": recs})
    assert sc.analyze(recs) and [c["id"] for c in bar] == [1, 2, 3, 4, 5]
