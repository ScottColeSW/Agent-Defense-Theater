"""A -prereg run must use the models the preregistration names; others need --exploratory (issue 36)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from adt import harness


class Scn:
    prereg_models = ["llama3.1:8b", "qwen2.5:7b", "phi4-mini:3.8b"]
    prereg_reviewer = "qwen2.5:7b"
    reviewer_model = "qwen2.5:7b"


def test_a_run_on_the_declared_models_is_accepted_and_recorded():
    ok, msg, info = harness.check_prereg_models(Scn(), ["llama3.1:8b", "qwen2.5:7b", "phi4-mini:3.8b"])
    assert ok and info["models_match"] is True
    assert info["prereg_models"] == Scn.prereg_models and info["prereg_reviewer"] == "qwen2.5:7b"


def test_a_run_on_a_model_outside_the_declared_set_is_refused():
    ok, msg, info = harness.check_prereg_models(Scn(), ["llama3.2:latest", "hermes3:3b", "mistral-local:7b"])
    assert not ok and info["models_match"] is False
    assert "exploratory" in msg and "llama3.2:latest" in msg and "llama3.1:8b" in msg   # names the extras and the missing


def test_a_reviewer_outside_the_declared_set_is_refused():
    s = Scn()
    s.reviewer_model = "llama3.2:latest"
    ok, msg, info = harness.check_prereg_models(s, ["llama3.1:8b", "qwen2.5:7b", "phi4-mini:3.8b"])
    assert not ok and "reviewer" in msg and info["models_match"] is False


def test_a_scenario_without_a_declared_set_is_unchanged():
    class Bare:
        pass
    assert harness.check_prereg_models(Bare(), ["anything:latest"]) == (True, "ok", {})
