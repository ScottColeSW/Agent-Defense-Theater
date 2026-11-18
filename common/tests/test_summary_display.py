"""adt summary now shows the pass bar, predicted-vs-observed, and a per-model table (issues 3, 4, 7)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from adt import cli, scorer


def test_predicted_vs_observed_shows_the_committed_prediction_beside_this_run():
    rows = [{"defense": "none", "success": scorer._share(14, 100), "utility": scorer._share(16, 27)},
            {"defense": "schema_gate", "success": scorer._share(8, 100), "utility": scorer._share(11, 27)}]
    predictions = {"none": {"attack": .35, "lo": .22, "hi": .49, "utility": .556},
                   "schema_gate": {"attack": .14, "lo": .06, "hi": .26, "utility": .407}}
    out = cli._predicted_vs_observed(rows, predictions)
    assert "pred attack" in out and "obs attack" in out
    assert "35% [22-49]" in out and "14.0% (14/100)" in out            # predicted interval beside the observed share
    assert "14%" in out and "7.8% (8/100)" not in out                  # schema_gate predicted 14%; observed is 8/100 = 8.0%
    assert "8.0% (8/100)" in out


def test_predicted_vs_observed_skips_a_defense_with_no_prediction():
    rows = [{"defense": "mystery", "success": scorer._share(1, 10), "utility": scorer._share(1, 10)}]
    assert cli._predicted_vs_observed(rows, {"none": {"attack": .1}}) == ""


def test_passbar_lines_are_empty_without_a_scenario():
    assert cli._passbar_lines(None, []) == []
