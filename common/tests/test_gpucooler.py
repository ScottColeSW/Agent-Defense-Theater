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
    c, msgs = _cooler([75, 74, 71, 69, 67], max_c=72)           # resume at 68, so 69 is not cool enough yet
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
