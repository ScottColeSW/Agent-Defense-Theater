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
