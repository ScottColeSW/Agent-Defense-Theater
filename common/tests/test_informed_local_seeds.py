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
