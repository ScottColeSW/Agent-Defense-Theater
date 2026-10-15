import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from adt import governance, report
from adt.loader import experiments


def test_links_point_at_real_rows_and_real_tests():
    rows, links = governance.load()
    ids = {r["id"] for r in rows}
    assert len(ids) == len(rows) == 10
    assert set(links["always"]) <= ids
    for key, mine in links["tests"].items():
        item, exp = key.split("/")
        assert exp in experiments(item), key
        assert set(mine) <= ids, key


def test_view_shows_criteria_with_their_results_and_nothing_without_a_pass_bar():
    pb = [{"id": i, "text": f"c{i}", "status": "met" if i % 2 else "missed", "result": f"r{i}"} for i in range(1, 9)]
    v = governance.view("ASI02", "first-run", pb)
    sec = next(r for r in v["rows"] if r["id"] == "security")
    assert [c["id"] for c in sec["criteria"]] == [1, 2, 4] and sec["criteria"][1]["status"] == "missed"
    assert next(r for r in v["rows"] if r["id"] == "log")["where"] and v["gaps"]
    assert governance.view("ASI02", "first-run", None) is None
    assert governance.view("ASI99", "nope", pb)["rows"][0]["where"]               # unknown test: only the rows every run supports


def test_a_saved_result_report_carries_the_governance_view():
    run = next(p.stem.replace(".decisions", "") for p in (Path(__file__).resolve().parents[2] / "items" / "asi03-identity-privilege" / "results").glob("asi03-bottom-line-*-prereg.jsonl"))
    out = report.build_report(run, records=False)
    assert out["governance"] and any(r["criteria"] for r in out["governance"]["rows"])


def test_tempo_and_surfaces_are_computed_from_records():
    from adt import tempo
    base = {"model_ms": 2000, "review_ms": 0, "gate_ms": 0, "tool_ms": 0, "holds": 0}
    recs = [
        dict(base, defense="none", attack="override_export", outcome="attack_succeeded", model_ms=1500),
        dict(base, defense="none", attack="audit_export", outcome="blocked"),
        dict(base, defense="none", attack="none", outcome="task_succeeded"),
        dict(base, defense="hold", attack="in_scope_refund", outcome="attack_succeeded", model_ms=2500, review_ms=500, holds=1),
        dict(base, defense="hold", attack="made_up_attack", outcome="blocked"),
    ]
    t = tempo.tempo(recs)
    assert t["to_unsafe_call"]["n"] == 2 and t["to_unsafe_call"]["median_ms"] == 2250 and t["to_unsafe_call"]["fastest_ms"] == 1500
    hold = next(r for r in t["rows"] if r["defense"] == "hold")
    assert hold["reviewer_ms"] == 250 and hold["decide_share"] == round(250 / (2250 + 250), 4) and t["holds"] == 1 and "People are not modeled" not in t["human"]
    s = tempo.surfaces(recs)
    by = {r["id"]: r for r in s["rows"]}
    assert by["injection"]["cells"]["none"] == {"k": 1, "n": 1} and by["authority"]["cells"]["none"] == {"k": 0, "n": 1}
    assert by["agency"]["cells"]["hold"] == {"k": 1, "n": 1} and s["unclassified"] == ["made_up_attack"]
    assert tempo.tempo([dict(base, defense="d", attack="none", outcome="task_succeeded")])["to_unsafe_call"]["median_ms"] is None


def test_every_classified_attack_in_the_saved_results_has_a_surface():
    import json
    from adt.loader import ROOT
    data = json.loads((ROOT / "crosswalk" / "threat-surfaces.json").read_text(encoding="utf-8"))
    assert set(data["attacks"].values()) <= set(data["surfaces"]) and set(data["why"]) <= set(data["attacks"])
    names = set()
    for f in (ROOT / "items").glob("*/results/*-prereg.jsonl"):
        for line in f.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            if r["attack"] != "none" and not r["attack"].startswith("n_"):
                names.add(r["attack"])
    assert names <= set(data["attacks"]), sorted(names - set(data["attacks"]))


def _row(name, k, n, vk, vn):
    return {"defense": name, "success": {"k": k, "n": n, "rate": k / n}, "valid": {"k": vk, "n": vn, "rate": vk / vn}}


def test_glance_verdicts_follow_the_stated_rules_and_group_identical_controls():
    from adt import glance
    rows = [_row("none", 60, 120, 60, 60), _row("gate", 0, 120, 58, 60), _row("costly", 0, 120, 30, 60), _row("half", 20, 120, 58, 60),
            _row("twin", 20, 120, 58, 60), _row("weak", 50, 120, 50, 60), _row("same", 59, 120, 60, 60), _row("hurts", 20, 120, 20, 60), _row("third", 40, 120, 58, 60)]
    g = glance.view(rows, None, None)
    v = {r["defense"]: r["verdict"] for r in g["rows"]}
    assert v == {"none": "baseline", "gate": "effective", "costly": "effective_costly", "half": "partial", "twin": "partial",
                 "weak": "ineffective", "same": "no_effect", "hurts": "costly_incomplete", "third": "ineffective"}
    assert g["best"]["defense"] == "gate" and g["baseline"]["residual"]["k"] == 60
    assert any("half, twin" in line and "remove" in line for line in g["explore"])        # identical controls are one sentence
    assert g["works"] and "gate" in g["works"][0] and g["gaps"] == []
    assert glance.view(rows[:1], None, None) is None
    nobase = glance.view([_row("a", 40, 100, 50, 60), _row("b", 5, 100, 50, 60)], None, None, "reviewer-calibration")
    assert nobase["baseline"]["explicit"] is False and nobase["baseline"]["defense"] == "a" and nobase["noun"] == "false approvals"
    weak_base = glance.view([_row("none", 0, 100, 50, 60), _row("x", 0, 100, 50, 60)], None, None)
    assert {r["verdict"] for r in weak_base["rows"]} == {"baseline", "not_testable"}


def test_a_gap_is_stated_when_no_control_closes_a_surface_or_keeps_the_work():
    from adt import glance
    rows = [_row("none", 60, 120, 60, 60), _row("only", 0, 120, 20, 60)]
    surf = {"rows": [{"id": "agency", "label": "Excessive agency", "cells": {"none": {"k": 20, "n": 30}, "only": {"k": 3, "n": 30}}}]}
    g = glance.view(rows, surf, {"holds": 4})
    text = " ".join(g["gaps"])
    assert "excessive agency" in text and "still lets 3 of 30" in text and "Human review time is not modeled" in text and "stop 67 points" in text


def test_the_closing_question_is_asked_only_when_the_results_support_it():
    from adt import glance
    rows = [_row("none", 60, 120, 60, 60), _row("hold+rule", 12, 120, 58, 60), _row("hold+bottomline", 12, 120, 58, 60), _row("hold+bottomline+money", 0, 120, 58, 60)]
    q = glance.view(rows, None, None, "bottom-line", "ASI03")["question"]
    assert "plain rule" in q["ask"] and "12 of 120" in q["because"]
    worse = [_row("none", 60, 120, 60, 60), _row("hold+rule", 30, 120, 58, 60), _row("hold+bottomline", 12, 120, 58, 60)]
    assert "plain rule" not in glance.view(worse, None, None, "bottom-line", "ASI03")["question"]["ask"]       # the rule lost, so the question is not asked
    q2 = glance.view([_row("none", 60, 120, 60, 60), _row("x", 0, 120, 58, 60)], None, None, "unknown", "ASI99")["question"]
    assert q2["ask"].startswith("What does your agent read that someone else wrote") and "0 of 120" in q2["because"]
    q3 = glance.view([_row("none", 60, 120, 60, 60), _row("x", 0, 120, 20, 60)], None, None, "unknown", "ASI99")["question"]
    assert "switched off" in q3["ask"] and "67 points" in q3["because"]
    recs = [{"model": f"m [thinking {m}]", "defense": "none", "attack": "a", "outcome": o} for m, o in [("off", "blocked")] * 5 + [("on", "attack_succeeded")] * 5]
    q4 = glance.view([_row("none", 5, 10, 5, 5), _row("x", 0, 10, 5, 5)], None, None, "thinking-agents", "ASI03", recs)["question"]
    assert "time to think" in q4["ask"] and "5 of 5" in q4["because"] and "0 of 5" in q4["because"]
