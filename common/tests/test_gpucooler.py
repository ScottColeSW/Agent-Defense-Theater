import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from adt import gpucooler
from adt.gpucooler import GpuCooler


def _cooler(temps, **kw):
    """A cooler fed a fixed series of temperatures, with a fake clock that advances only when it sleeps."""
    seq, t = list(temps), {"now": 0.0}
    msgs = []

    def read():
        return seq.pop(0) if len(seq) > 1 else seq[0]

    def sleep(s):
        t["now"] += s

    return GpuCooler(read=read, sleep=sleep, clock=lambda: t["now"], say=msgs.append, **kw), msgs


def test_below_limit_does_not_pause():
    c, msgs = _cooler([60, 71, 72])
    assert [c.wait(), c.wait(), c.wait()] == [60, 71, 72]       # exactly at the limit is allowed
    assert c.pauses == 0 and c.stats()["peak_c"] == 72 and not msgs


def test_pauses_over_the_limit_until_it_has_cooled_past_the_margin():
    c, msgs = _cooler([75, 74, 71, 69, 67], max_c=72, resume_c=68)   # resume at 68, so 69 is not cool enough yet
    assert c.wait() == 67
    assert c.pauses == 1 and c.paused_s == pytest.approx(12.0)  # four polls of three seconds
    assert c.stats()["peak_c"] == 75
    assert any("Pausing" in m for m in msgs) and any("resumed at 67C" in m for m in msgs)


def test_wait_time_is_stamped_once():
    c, _ = _cooler([80, 60])
    c.wait()
    assert c.take_wait_ms() == 3000 and c.take_wait_ms() == 0


def test_no_temperature_reading_means_no_limiting_and_one_notice():
    c, msgs = _cooler([None])
    assert c.wait() is None and c.wait() is None
    assert len([m for m in msgs if "cannot read" in m]) == 1 and c.stats()["available"] is False


def test_gives_up_instead_of_waiting_forever():
    c, _ = _cooler([90], give_up_s=30)
    with pytest.raises(RuntimeError, match="still 90C"):
        c.wait()


def test_sensor_lost_while_paused_releases_the_run():
    c, _ = _cooler([80, None], max_c=72)
    c.wait()                                                    # first read 80, next read None: stop holding
    assert c.pauses == 1


def test_resume_above_max_is_rejected():
    with pytest.raises(ValueError):
        GpuCooler(max_c=72, resume_c=75)


def test_record_snapshot_and_hook(monkeypatch):
    c, _ = _cooler([70, 70])
    gpucooler.install(c, sampler=False)
    try:
        assert gpucooler.before_call() == 70
        assert gpucooler.snapshot() == {"gpu_temp_c": 70, "thermal_wait_ms": 0}
    finally:
        gpucooler.uninstall()
    assert gpucooler.before_call() is None and gpucooler.snapshot() == {}


def test_default_resume_is_60_and_the_card_eases_off_before_the_limit():
    c, msgs = _cooler([55, 67, 70, 72])
    assert c.resume_c == 60 and c.soft_c == 66 and c.max_c == 72
    assert [c.wait(), c.wait(), c.wait(), c.wait()] == [55, 67, 70, 72]
    assert c.eased == 3 and c.eased_s == pytest.approx(6.0) and c.pauses == 0 and not msgs      # warm calls rest, nothing stops, nothing is printed
    assert c.busy_s == pytest.approx(6.0)                                                      # and the rest is kept out of latency


def test_a_pause_now_lasts_until_60():
    c, _ = _cooler([75, 70, 66, 62, 60], max_c=72)
    assert c.wait() == 60 and c.paused_s == pytest.approx(12.0)


def test_settle_waits_for_a_cool_card_and_never_raises():
    c, msgs = _cooler([68, 64, 61, 59])
    assert c.settle() == 59 and c.settled_s == pytest.approx(9.0) and any("Settling" in m for m in msgs)
    c2, msgs2 = _cooler([90], give_up_s=30)
    assert c2.settle(max_wait_s=10) == 90 and any("Going on" in m for m in msgs2)            # gives up quietly, the per-call limit still holds
    c3, _ = _cooler([None])
    assert c3.settle() is None
    gpucooler.uninstall()
    assert gpucooler.settle() is None


def test_settle_can_cool_below_the_resume_point_and_gives_up_after_its_cap():
    c, msgs = _cooler([62, 58, 55, 52, 49], settle_c=50)
    assert c.settle() == 49 and c.settled_s == pytest.approx(12.0) and any("Settling to 50C" in m for m in msgs)
    c2, msgs2 = _cooler([53] * 40, settle_c=50, settle_max_s=15)                             # a card that idles above the target
    assert c2.settle() == 53 and any("Going on" in m for m in msgs2) and c2.settled_s < 25
    c3, _ = _cooler([55])
    assert c3.settle_c == c3.resume_c and c3.settle() == 55 or c3.settle_c == c3.resume_c    # unset: it is the resume point, as before
