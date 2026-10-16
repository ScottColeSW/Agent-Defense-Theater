import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from adt import decisionlog, harness, models, modelmgr, scorer
from adt.loader import experiments, load_scenario


def _cal():
    sc = load_scenario("asi03", "reviewer-calibration")
    return sc, sys.modules["asi03_cred"], sys.modules["asi03_desk"], sys.modules["asi03_esc"]


def test_experiments_are_registered_in_order():
    assert experiments("asi03") == ["first-run", "escalation", "bottom-line", "thinking-agents", "reviewer-calibration", "blind", "informed", "duplicate-probe", "duplicate-probe-replicate"]


def test_every_card_has_the_answer_the_system_comparison_gives():
    sc, cred, desk, _ = _cal()
    fams = sys.modules["asi03_scn_reviewer_calibration"].FAMILIES if "asi03_scn_reviewer_calibration" in sys.modules else None
    for case in sc.cases():
        d = case.data
        f = sc_family(sc, d["family"])
        call = desk.Call(f["tool"], f["args"](d["ticket"]), f["why"])
        match, _ = cred.explain_request(call, d["ticket"], desk.TICKETS, f["op"].format(t=d["ticket"]))
        assert match == (d["truth"] == "approve"), (d["family"], d["ticket"])


def sc_family(sc, name):
    return sys.modules[type(sc).__module__].FAMILIES[name]


def test_scripted_run_is_all_correct_and_log_verifies(tmp_path):
    sc, *_ = _cal()
    assert len(sc.cases()) == 22 and len(sc.defenses) == 6
    meta = harness.run(sc, [models.ScriptedRunner()], tmp_path, mode="scripted", progress=None)
    assert decisionlog.verify(tmp_path / f"{meta['run_id']}.decisions.jsonl").ok
    recs = scorer.load_records([tmp_path / f"{meta['run_id']}.jsonl"], live_only=False)
    assert all(r["outcome"] in ("blocked", "task_succeeded") for r in recs) and len(recs) == 132
    assert sc.analyze(recs) and sc.pass_bar([], {"records": recs})


def test_cards_differ_by_style():
    sc, *_ = _cal()
    mod = sys.modules[type(sc).__module__]
    cards = {s: mod.build_card(s, "n_wrong_account", "T-1001") for s in ("agent_card", "effect_card", "bottomline")}
    assert len(set(cards.values())) == 3 and "Finance on-call" not in cards["bottomline"]


def test_parse_verdict():
    esc = _cal()[3]
    assert esc.parse_verdict('{"decision": "approve", "reason": "ok"}') == (True, "ok", True)
    assert esc.parse_verdict("nonsense")[0] is False and esc.parse_verdict("nonsense")[2] is False
    assert esc.parse_verdict('{"decision": "deny"}')[0] is False


def test_make_runners_sets_think_only_for_thinking_models(monkeypatch):
    sc, *_ = _cal()
    monkeypatch.setattr(modelmgr, "describe", lambda n, *a, **k: {"capabilities": ["completion", "thinking"] if "qwen3" in n else ["completion"]})
    r = sc.make_runners(["qwen3:4b", "qwen2.5:7b"])
    assert [x.name for x in r] == ["qwen3:4b [thinking off]", "qwen3:4b [thinking on]", "qwen2.5:7b"]
    assert [x.think for x in r] == [False, True, None]
    t = load_scenario("asi03", "thinking-agents").make_runners(["qwen3:4b"])
    assert [x.think for x in t] == [False, True]


def test_thinking_scripted_run_and_sidecar(tmp_path):
    sc = load_scenario("asi03", "thinking-agents")
    assert [d.name for d in sc.defenses] == ["none", "scoped_credentials", "task_binding", "hold+bottomline"]

    class Thinker(models.ScriptedRunner):
        name = "t [thinking on]"

        def generate(self, system, user, hint=None, **o):
            r = super().generate(system, user, hint, **o)
            r.thinking = "let me think"
            r.tokens_out = 50
            return r

    meta = harness.run(sc, [Thinker()], tmp_path, mode="scripted", progress=None)
    side = tmp_path / f"{meta['run_id']}.thinking.jsonl"
    assert side.exists() and "let me think" in side.read_text(encoding="utf-8")
    recs = scorer.load_records([tmp_path / f"{meta['run_id']}.jsonl"], live_only=False)
    assert all(r.get("thinking_chars") == 12 for r in recs)
