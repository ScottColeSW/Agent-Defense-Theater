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
