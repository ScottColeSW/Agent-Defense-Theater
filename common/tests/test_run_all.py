"""adt run-all: the experiment-selection logic (which experiments run, which are skipped and why)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from adt.cli import _plan_run_all

TESTS = [
    {"id": "asi03/first-run", "item": "ASI03", "experiment": "first-run", "needs_orchestrator": False, "prereg": {"ready": True}},
    {"id": "asi03/informed", "item": "ASI03", "experiment": "informed", "needs_orchestrator": True, "prereg": {"ready": True}},
    {"id": "asi05/os-boundary", "item": "ASI05", "experiment": "os-boundary", "needs_orchestrator": False, "prereg": {"ready": False, "message": "prediction not committed"}},
]


def test_live_skips_orchestrator_and_unready_prereg():
    run, skips = _plan_run_all(TESTS, None, live=True)
    assert [t["id"] for t in run] == ["asi03/first-run"]
    assert dict(skips) == {"asi03/informed": "runs in rounds; use `adt informed`", "asi05/os-boundary": "prediction not committed"}


def test_scripted_ignores_prereg_readiness_but_still_skips_orchestrator():
    run, skips = _plan_run_all(TESTS, None, live=False)
    assert {t["id"] for t in run} == {"asi03/first-run", "asi05/os-boundary"}
    assert [tid for tid, _ in skips] == ["asi03/informed"]


def test_item_filter():
    run, skips = _plan_run_all(TESTS, "asi05", live=False)
    assert [t["id"] for t in run] == ["asi05/os-boundary"] and skips == []
