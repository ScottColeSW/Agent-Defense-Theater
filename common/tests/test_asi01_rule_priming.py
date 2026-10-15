import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from adt import harness, models, scorer
from adt.loader import experiments, load_scenario


def _mod():
    sc = load_scenario("asi01", "rule-priming")
    return sc, sys.modules[type(sc).__module__]


def test_registered_sized_and_the_control_texts_are_what_they_claim_to_be():
    sc, mod = _mod()
    assert experiments("asi01") == ["first-run", "spotlighting", "rule-priming"]
    cases = sc.cases()
    assert len(cases) == 25 and sum(c.kind == "attack" for c in cases) == 20 and len(sc.defenses) == 5 and "task_completion_trick" not in {c.attack for c in cases}
    assert set(sc.predictions) == {d.name for d in sc.defenses} and sc.extra_models() == []
    rule, bg = mod.sp.RULE_ONLY, mod.BACKGROUND
    assert abs(len(bg.split()) - len(rule.split())) / len(rule.split()) <= .10 and abs(len(bg) - len(rule)) / len(rule) <= .15      # matched in length
    lowered = bg.lower()
    assert not any(w in lowered for w in ("never", "must", "always", "do not", "apply", "rule", "policy", "binding", "follow"))        # background states facts and gives no instruction
    irr = mod.IRRELEVANT_RULE.lower()
    assert "never" not in irr and not any(w in irr for w in ("note", "price", "offer", "export", "delete", "task", "tool", "record", "operator", "untrusted", "security"))   # about nothing the attacks touch
    assert mod.SPEC["rule_only"] == (mod.sp.RULE_ONLY, False) and all(not wrap for _, wrap in mod.SPEC.values())                         # no tags anywhere in this test


def test_each_condition_adds_only_its_text_to_the_system_prompt(tmp_path):
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
    for name, (text, _) in mod.SPEC.items():
        assert {s for s, _ in seen[name]} == {base + text}, name
        assert not any("<data>" in u for _, u in seen[name]), name


def test_scripted_agent_is_hijacked_under_every_condition_and_the_pass_bar_reads(tmp_path):
    sc, mod = _mod()

    class Few:
        def __getattr__(self, k):
            return getattr(sc, k)

        def cases(self):
            return [c for c in sc.cases() if c.data["deal"] == "D-105"]

    meta = harness.run(Few(), [models.ScriptedRunner()], tmp_path, mode="scripted", progress=None)
    recs = scorer.load_records([tmp_path / f"{meta['run_id']}.jsonl"], live_only=False)
    assert all(r["outcome"] == "attack_succeeded" for r in recs if r["attack"] != "none") and len([r for r in recs if r["attack"] != "none"]) == 4 * 5
    assert all(r["outcome"] == "task_succeeded" for r in recs if r["attack"] == "none")
    bar = sc.pass_bar(scorer.summarize(recs, ("defense",)), {"records": recs})
    assert [c["id"] for c in bar] == [1, 2, 3, 4, 5, 6] and sc.analyze(recs)
