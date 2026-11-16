"""Risk vs Confidence engine (common/adt/risk.py).

Two things must stay true for the view to be honest: the measured half (containment and its interval) is ordered the
way a confidence interval must be, and the assumption half (the dollar model) is exactly exposure x (1 - containment) x
impact, scaling linearly with its inputs and never collapsing to a bare $0 at finite n. Both are checked here without a
model and without Docker, against whatever preregistered runs are committed, by asserting invariants rather than fixed
dollar amounts (so the test does not break every time a run is added)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from adt import risk


def _all():
    rows = risk.all_item_risks()
    assert rows, "expected at least one item with a preregistered first-run"
    return rows


def test_containment_interval_is_ordered_and_bounded():
    for r in _all():
        assert 0.0 <= r["containment_floor"] <= r["containment_rate"] <= r["containment_ceiling"] <= 1.0, r["item"]


def test_residual_is_the_assumption_model_applied_to_the_measurement():
    a = risk.ASSUMPTIONS
    exposure, impact = a["exposure_attempts_per_year"], a["breach_impact_usd"]
    for r in _all():
        success_point = 1 - r["containment_rate"]
        assert r["residual_point_usd"] == pytest.approx(exposure * success_point * impact)
        # the headline residual is taken at the 95% floor (success upper edge), so it is the conservative figure
        success_upper = 1 - r["containment_floor"]
        assert r["residual_floor_usd"] == pytest.approx(exposure * success_upper * impact)
        assert r["residual_floor_usd"] >= r["residual_point_usd"] >= 0


def test_a_zero_failure_run_still_carries_a_nonzero_floor_residual():
    perfect = [r for r in _all() if r["containment_rate"] == 1.0]
    assert perfect, "expected at least one item whose best defense saw zero successes"
    for r in perfect:
        assert r["residual_point_usd"] == 0.0            # the point estimate is honest about what was seen
        assert r["residual_floor_usd"] > 0.0             # but the sample size cannot rule out the rest: never a bare $0


def test_avoided_is_a_central_estimate_point_minus_point():
    for r in _all():
        assert r["risk_reduced_usd"] == pytest.approx(r["residual_baseline_usd"] - r["residual_point_usd"])
        # avoided never goes negative: the baseline is the undefended (or worst) condition, the best is the min-success
        assert r["risk_reduced_usd"] >= -1e-6, r["item"]


def test_dollar_figures_scale_linearly_with_the_assumptions():
    base = risk.item_risk("asi05", "first-run")
    assert base is not None
    doubled = risk.item_risk("asi05", "first-run",
                             {"exposure_attempts_per_year": risk.ASSUMPTIONS["exposure_attempts_per_year"] * 2,
                              "breach_impact_usd": risk.ASSUMPTIONS["breach_impact_usd"]})
    assert doubled["residual_floor_usd"] == pytest.approx(base["residual_floor_usd"] * 2)
    assert doubled["residual_baseline_usd"] == pytest.approx(base["residual_baseline_usd"] * 2)
    # containment is measured, so changing the assumptions must not move it
    assert doubled["containment_rate"] == base["containment_rate"]
    assert doubled["containment_floor"] == base["containment_floor"]


def test_missing_item_or_experiment_returns_none():
    assert risk.item_risk("asi03", "no-such-experiment") is None
    assert risk.item_risk("zz99", "first-run") is None
