"""Black ICE rung 2, scripted: the headline relations of blackice/rungs/01-contain/scripted.py. Scripted and synthetic, never a result."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("contain_scripted", ROOT / "blackice" / "rungs" / "01-contain" / "scripted.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

TABLE = mod.compare()
by = lambda attack: {r["condition"]: r for r in TABLE[attack]}
NONE, SINGLE, TWO, SIGNED = "no containment", "one signal quarantines", "two signals required", "two signals, gateway-signed"


def test_no_containment_is_the_baseline_and_the_spoofer_cannot_change_it():
    for attack in mod.ATTACKS:
        r = by(attack)[NONE]
        assert r["legit_interrupted"] == 0 and r["bot_successes"] == by("none")[NONE]["bot_successes"]


def test_signed_events_make_the_spoofer_irrelevant():
    base = by("none")[SIGNED]
    for attack in ("loud", "quiet", "adaptive"):
        r = by(attack)[SIGNED]
        assert r["forged_ignored"] == r["spoofed_events"] > 0
        assert (r["bot_successes"], r["false_quarantines"], r["legit_interrupted"]) == (base["bot_successes"], base["false_quarantines"], base["legit_interrupted"])
    assert base["bot_successes"] < by("none")[NONE]["bot_successes"]


def test_a_single_signal_is_a_lever_for_the_spoofer():
    assert by("loud")[SINGLE]["legit_interrupted"] > 1.3 * by("none")[SINGLE]["legit_interrupted"]
    assert by("loud")[SINGLE]["legit_interrupted"] > 5 * by("loud")[TWO]["legit_interrupted"]


def test_two_signals_hold_against_a_loud_spoofer_and_fall_to_an_adaptive_one():
    assert by("loud")[TWO]["false_quarantines"] < 2.5 * by("none")[TWO]["false_quarantines"]
    assert by("adaptive")[TWO]["false_quarantines"] > 5 * by("none")[TWO]["false_quarantines"]


def test_corroboration_costs_time_to_contain():
    assert by("none")[TWO]["avg_days_to_contain"] > by("none")[SINGLE]["avg_days_to_contain"] + 3
    assert by("none")[TWO]["bot_successes"] > by("none")[SINGLE]["bot_successes"]
