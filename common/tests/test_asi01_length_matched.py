import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from adt import harness, models, scorer
from adt.loader import experiments, load_scenario


def _mod():
    sc = load_scenario("asi01", "length-matched")
    return sc, sys.modules[type(sc).__module__]


def test_registered_sized_and_the_texts_are_the_lengths_they_claim():
    sc, mod = _mod()
    assert experiments("asi01") == ["first-run", "spotlighting", "rule-priming", "length-matched"]
    cases = sc.cases()
    assert len(cases) == 25 and sum(c.kind == "attack" for c in cases) == 20 and len(sc.defenses) == 5
    assert set(sc.predictions) == {d.name for d in sc.defenses} and sc.extra_models() == []
    n = lambda t: len(t.split())
    assert n(mod.SHORT_BACKGROUND) == 23
    assert abs(n(mod.LONG_UNRELATED_RULE) - n(mod.sp.RULE_ONLY)) <= 2 and abs(n(mod.LONG_UNRELATED_FACTS) - n(mod.sp.RULE_ONLY)) <= 2
    assert mod.SPEC["long_background"][0] == mod.rp.BACKGROUND and mod.SPEC["none"] == ("", False)
    assert mod.LONG_UNRELATED_RULE.startswith(mod.rp.IRRELEVANT_RULE.rstrip(".")) or mod.rp.IRRELEVANT_RULE.strip()[:60] in mod.LONG_UNRELATED_RULE
    unrelated = (mod.LONG_UNRELATED_RULE + mod.LONG_UNRELATED_FACTS).lower()
    assert not any(w in unrelated for w in ("note", "price", "offer", "export", "delete", "task", "tool", "record", "operator", "untrusted", "security", "deal"))
    facts = (mod.SHORT_BACKGROUND + mod.LONG_UNRELATED_FACTS).lower()
    assert not any(w in facts for w in ("never", "must", "always", "do not", "apply", "rule", "policy", "binding", "follow"))      # facts, no instruction


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


def test_scripted_agent_is_hijacked_everywhere_and_the_pass_bar_reads(tmp_path):
    sc, mod = _mod()

    class Few:
        def __getattr__(self, k):
            return getattr(sc, k)

        def cases(self):
            return [c for c in sc.cases() if c.data["deal"] == "D-105"]

    meta = harness.run(Few(), [models.ScriptedRunner()], tmp_path, mode="scripted", progress=None)
    recs = scorer.load_records([tmp_path / f"{meta['run_id']}.jsonl"], live_only=False)
    assert all(r["outcome"] == "attack_succeeded" for r in recs if r["attack"] != "none")
    bar = sc.pass_bar(scorer.summarize(recs, ("defense",)), {"records": recs})
    assert [c["id"] for c in bar] == [1, 2, 3, 4, 5, 6] and sc.analyze(recs)
