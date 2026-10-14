"""Keeping a long run from taking the machine down: free memory and disk are checked before a run and watched during it.

A run that cannot continue safely stops with a clear message and keeps what it has written. That is better than a frozen system, a
reboot, and a run with nothing saved. The thresholds are for a 16 GB workstation with an 8 GB GPU and are plain module values so a
test or a bigger machine can change them.
"""
import shutil
import time
from pathlib import Path

from . import modelmgr

MIN_RAM_START_MB = 3000          # refuse to start below this much free RAM
PAUSE_RAM_MB = 1500              # pause model calls below this
MAX_WAIT_S = 180                 # stop the run if memory has not recovered by then
MIN_DISK_START_MB = 3000
MIN_DISK_STOP_MB = 500
CHECK_EVERY_S = 5


class ResourceError(RuntimeError):
    """The machine is too short of memory or disk for the run to continue safely. The run stops, and what it wrote is kept."""


def ram_free_mb():
    r = modelmgr.ram()
    return None if r is None else int(r["free"] / 1024 / 1024)


def disk_free_mb(path) -> int:
    p = Path(path)
    while not p.exists() and p != p.parent:
        p = p.parent
    return int(shutil.disk_usage(p).free / 1024 / 1024)


def preflight(paths: list) -> list:
    """Problems that should stop a run before it starts. An empty list means go."""
    problems, free = [], ram_free_mb()
    if free is not None and free < MIN_RAM_START_MB:
        problems.append(f"only {free} MB of RAM is free (need {MIN_RAM_START_MB} MB). Close other programs, or unload models: python adt.py models")
    seen = set()
    for p in paths:
        drive = Path(p).resolve().anchor
        if drive in seen:
            continue
        seen.add(drive)
        d = disk_free_mb(p)
        if d < MIN_DISK_START_MB:
            problems.append(f"only {d} MB is free on {drive} (need {MIN_DISK_START_MB} MB)")
    return problems


_last = 0.0
waited_s = 0.0


def before_call(sleep=time.sleep, now=time.monotonic):
    """Called ahead of every model call. Cheap when memory is fine; waits when it is low; raises ResourceError if it stays low."""
    global _last, waited_s
    t = now()
    if t - _last < CHECK_EVERY_S:
        return
    _last = t
    start = t
    while True:
        free = ram_free_mb()
        if free is None or free >= PAUSE_RAM_MB:
            waited_s += now() - start
            _last = now()
            return
        if now() - start > MAX_WAIT_S:
            raise ResourceError(f"free RAM stayed under {PAUSE_RAM_MB} MB for {MAX_WAIT_S} s ({free} MB free). Stopped to keep the machine usable; the records written so far are kept")
        sleep(CHECK_EVERY_S)


def check_disk(paths: list):
    for p in paths:
        d = disk_free_mb(p)
        if d < MIN_DISK_STOP_MB:
            raise ResourceError(f"only {d} MB is free on {Path(p).resolve().anchor}. Stopped before the disk filled")
