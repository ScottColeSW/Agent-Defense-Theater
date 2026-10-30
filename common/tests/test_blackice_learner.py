"""Black ICE learner comparison (blackice/rungs/bi01-contain/learner.py). Scripted and synthetic, never a result."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("bi01_learner", ROOT / "blackice" / "rungs" / "bi01-contain" / "learner.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
TABLE = mod.compare()
row = lambda bot, det, mode: next(r for r in TABLE[bot] if r["detector"] == det and r["mode"] == mode)


def test_every_detector_sees_a_burst():
    for det in ("fixed_cap", "learned_naive", "learned_capped", "learned_verified"):
        assert row("burst", det, "advisor")["detected_pct"] == 100


def test_the_slow_ramp_poisons_an_unbounded_learner_and_not_a_bounded_one():
    naive, capped, fixed = row("slow_ramp", "learned_naive", "authority"), row("slow_ramp", "learned_capped", "authority"), row("slow_ramp", "fixed_cap", "authority")
    assert naive["detected_pct"] < 15 and capped["detected_pct"] >= 90 and fixed["detected_pct"] >= 90
    assert naive["baseline_vs_truth"] > 5 and capped["baseline_vs_truth"] < 2          # the unbounded baseline became the bot
    assert naive["bot_calls"] > 20 * capped["bot_calls"]


def test_learning_is_quieter_than_a_fixed_cap_and_the_safeguards_cost_quiet():
    quiet = {d: row("none", d, "advisor")["false_alerts_per_1000_token_days"] for d in ("fixed_cap", "learned_naive", "learned_capped", "learned_verified")}
    assert quiet["learned_naive"] < 0.2 * quiet["fixed_cap"]       # it adapts to honest changes
    assert quiet["learned_naive"] < quiet["learned_capped"] < quiet["fixed_cap"]
    assert quiet["learned_verified"] > quiet["fixed_cap"]           # never learning from an alarm day leaves it alarming after any honest change


def test_a_learner_catches_a_little_of_low_and_slow_and_nothing_catches_a_mimic():
    assert row("low_and_slow", "fixed_cap", "advisor")["detected_pct"] == 0 and row("low_and_slow", "learned_capped", "advisor")["detected_pct"] >= 15
    for det in ("fixed_cap", "learned_naive", "learned_capped", "learned_verified"):
        assert row("mimic", det, "advisor")["detected_pct"] == 0


def test_authority_interrupts_the_owner_and_an_advisor_does_not():
    assert row("none", "fixed_cap", "authority")["owner_interruptions"] > 5 * row("none", "learned_naive", "authority")["owner_interruptions"]
    assert row("none", "fixed_cap", "advisor")["owner_interruptions"] is None
