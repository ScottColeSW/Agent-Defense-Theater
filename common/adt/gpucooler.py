"""GPU cooler: pause model calls while the GPU is too hot, so a hot card does not skew timing or throttle the run.

Before every model call the cooler reads the GPU temperature (nvidia-smi). Above `max_c` it waits, polling every few
seconds, until the card is at or below `resume_c`, a few degrees lower so it does not flap on and off at the limit.
It records the peak temperature, the number of pauses and the seconds spent paused, and the harness stamps each
result record with the temperature and any wait, so latency can be read with the waits taken out.

Limits, stated plainly:
- The check happens between calls. A single long generation can still push the card past the limit before the next check.
  A background sampler tracks the true peak so the report is honest about it.
- It reads temperature only. It does not set fan curves, clocks or power limits.
- With no NVIDIA GPU or no nvidia-smi it does nothing and says so once.
"""
import shutil
import subprocess
import threading
import time

DEFAULT_MAX_C = 72
DEFAULT_MARGIN_C = 4


def read_temp_c():
    """Hottest GPU in degrees C, or None if it cannot be read."""
    exe = shutil.which("nvidia-smi")
    if not exe:
        return None
    try:
        out = subprocess.run([exe, "--query-gpu=temperature.gpu", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=10).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    temps = [int(x) for x in out.split() if x.strip().isdigit()]
    return max(temps) if temps else None


class GpuCooler:
    def __init__(self, max_c=DEFAULT_MAX_C, resume_c=None, poll_s=3.0, give_up_s=1800,
                 read=read_temp_c, sleep=time.sleep, clock=time.monotonic, say=print):
        self.max_c = max_c
        self.resume_c = resume_c if resume_c is not None else max_c - DEFAULT_MARGIN_C
        if self.resume_c > self.max_c:
            raise ValueError("resume_c must not be above max_c")
        self.poll_s, self.give_up_s = poll_s, give_up_s
        self._read, self._sleep, self._clock, self._say = read, sleep, clock, say
        self.available = None
        self.last = self.peak = None
        self.pauses, self.paused_s, self._taken_s, self.busy_s = 0, 0.0, 0.0, 0.0
        self.t0 = clock()
        self.samples, self.pause_events = [], []     # [seconds since start, C], and one dict per pause
        self._stop = threading.Event()
        self._lock = threading.Lock()

    def _see(self, t):
        with self._lock:
            self.last = t
            self.peak = t if self.peak is None else max(self.peak, t)
            self.samples.append([round(self._clock() - self.t0, 1), t])
            if len(self.samples) > 20000:
                del self.samples[::2]                  # thin evenly rather than grow without bound

    def wait(self):
        """Block while the GPU is above the limit. Returns the temperature that allowed the call, or None if unreadable.
        All the time spent in here (reading the sensor and any pause) is added to busy_s so callers can take it out of
        their own timings."""
        t_in = self._clock()
        try:
            return self._wait()
        finally:
            self.busy_s += self._clock() - t_in

    def _wait(self):
        t = self._read()
        if t is None:
            if self.available is not False:
                self._say("GPU cooler: cannot read a GPU temperature (no nvidia-smi), so it is not limiting this run.")
            self.available = False
            return None
        self.available = True
        self._see(t)
        if t <= self.max_c:
            return t
        self.pauses += 1
        first = t
        start = self._clock()
        self._say(f"GPU cooler: {t}C is over {self.max_c}C. Pausing until {self.resume_c}C or lower.")
        while t > self.resume_c:
            if self._clock() - start > self.give_up_s:
                raise RuntimeError(f"GPU cooler: still {t}C after {self.give_up_s}s of waiting (target {self.resume_c}C). "
                                   "Check cooling or raise the limit. Stopping rather than waiting forever.")
            self._sleep(self.poll_s)
            nt = self._read()
            if nt is None:
                break                                   # sensor lost: stop holding the run
            t = nt
            self._see(t)
        waited = self._clock() - start
        self.paused_s += waited
        self.pause_events.append({"start_s": round(start - self.t0, 1), "seconds": round(waited, 1), "from_c": first, "to_c": t})
        self._say(f"GPU cooler: resumed at {t}C after {waited:.0f}s.")
        return t

    def take_wait_ms(self) -> int:
        """Milliseconds paused since the last call, for stamping one result record."""
        d, self._taken_s = self.paused_s - self._taken_s, self.paused_s
        return round(d * 1000)

    def stats(self) -> dict:
        return {"max_c": self.max_c, "resume_c": self.resume_c, "peak_c": self.peak, "pauses": self.pauses,
                "paused_s": round(self.paused_s, 1), "available": bool(self.available)}

    def timeline(self) -> dict:
        """Everything the UI needs to draw the cooldown: temperature samples, the pauses, and the two limits."""
        return {**self.stats(), "samples": list(self.samples), "pause_events": list(self.pause_events)}

    def start_sampler(self, every_s: float = 5.0):
        """Track the true peak between calls. Daemon thread, stops with the process or stop_sampler()."""
        def loop():
            while not self._stop.wait(every_s):
                t = self._read()
                if t is not None:
                    self._see(t)
        threading.Thread(target=loop, daemon=True, name="gpu-cooler-sampler").start()

    def stop_sampler(self):
        self._stop.set()


active = None      # the cooler in force for this process, if any


def install(cooler: GpuCooler, sampler: bool = True) -> GpuCooler:
    global active
    active = cooler
    if sampler:
        cooler.start_sampler()
    return cooler


def uninstall():
    global active
    if active:
        active.stop_sampler()
    active = None


def busy_ms() -> int:
    """Total time the cooler has spent checking and pausing so far. Subtract the change across a section to keep it out of that section's timing."""
    return round(active.busy_s * 1000) if active else 0


def before_call():
    """Called by the model runner ahead of each generation."""
    return active.wait() if active else None


def snapshot() -> dict:
    """Fields to stamp on a result record: the last reading and any time spent paused since the previous record."""
    if not active or active.last is None:
        return {}
    return {"gpu_temp_c": active.last, "thermal_wait_ms": active.take_wait_ms()}
