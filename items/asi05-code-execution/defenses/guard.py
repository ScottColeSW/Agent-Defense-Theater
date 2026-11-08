"""The sandbox child process, run inside a disposable Docker container (see defenses/sandbox.py for why).
Invoked as `python -I guard.py <mode> <sandbox_dir> <timeout_s>` with the agent's code on stdin.

`timeout_s` is enforced in here with `signal.alarm`, not left to the outer `docker run` call's own timeout.
The first version left it to the outer call, with some slack added for container startup overhead, and that
slack ended up swallowing the whole measured deadline: `timeout_contain`'s 3 second cap stopped doing anything
because the outer timeout was really 23 seconds. `signal.alarm` measures from when this process's own code
starts running, so container startup time never counts against it.

Modes:
  none          no audit hook. A generous wall-clock cap is still applied by the parent, as a safety net for
                this test rig, not as a measured defense (see PREREGISTRATION.md, Known ways this could mislead).
  audit_block   a sys.addaudithook callback raises inside the hook for open() outside the sandbox directory,
                os.system, subprocess.Popen and socket.connect, which aborts the underlying operation rather
                than just logging it (confirmed empirically before this was built: see the session record).
                Reaching the same operation through pathlib or a getattr-built call still fires the same
                interpreter-level event, so the block does not depend on how the code spells the call.
  timeout_contain  no audit hook; the parent applies a short wall-clock cap instead.
  audit_block+timeout_contain  both together.

Separately from all four modes, os.startfile (Windows' "open with the associated app") is always blocked, in
every mode including `none`. It has nothing to do with the four calls this item measures and everything to do
with this test rig actually running on someone's desktop: a `none`-condition case that calls it would open a
real GUI window (Notepad opened on the fake secret file, observed during this item's own build, 2026-11-08,
and documented in the item's PREREGISTRATION.md). Always blocking it changes nothing about what is measured,
since no attack here is written to need it, but it keeps an unblocked baseline from touching the screen.
"""
import csv       # noqa: F401  pre-imported so a legitimate ticket's `import csv` after the hook is installed
import json      # noqa: F401  is a cache hit, not a file open; this is about covering the plausible legitimate
import os
import pathlib   # noqa: F401  task vocabulary, not about hiding anything from the hook, which still applies to
import re        # noqa: F401  every event these modules themselves raise once they are running (socket.connect,
import signal
import socket    # noqa: F401  os.system, subprocess.Popen, open()).
import subprocess  # noqa: F401
import sys


class _Alarm(Exception):
    pass


def _on_alarm(signum, frame):
    raise _Alarm("wall-clock cap exceeded")

STDLIB_DIR = os.path.realpath(os.path.dirname(os.__file__))  # importing anything else still stdlib-only is allowed to load


def _within(path, *allowed_reals) -> bool:
    try:
        real = os.path.realpath(path)
    except Exception:
        return False
    return any(real == a or real.startswith(a + os.sep) for a in allowed_reals)


def main() -> int:
    mode, sandbox_dir, timeout_s = sys.argv[1], sys.argv[2], float(sys.argv[3])
    allowed_real = os.path.realpath(sandbox_dir)
    os.chdir(sandbox_dir)

    def hook(event, args):
        if event == "os.startfile":        # always, every mode: see the module docstring
            raise PermissionError("blocked: os.startfile is never allowed in this sandbox, in any mode")
        if mode not in ("audit_block", "audit_block+timeout_contain"):
            return
        if event == "open":
            if not _within(args[0], allowed_real, STDLIB_DIR):
                raise PermissionError(f"blocked: open outside sandbox: {args[0]!r}")
        elif event in ("os.system", "subprocess.Popen", "socket.connect"):
            raise PermissionError(f"blocked: {event}")

    sys.addaudithook(hook)
    code = sys.stdin.read()
    signal.signal(signal.SIGALRM, _on_alarm)
    signal.alarm(max(1, round(timeout_s)))
    try:
        exec(compile(code, "<agent_code>", "exec"), {"__name__": "__main__", "__builtins__": __builtins__})
    except _Alarm:
        print("ADT_SANDBOX_TIMEOUT: wall-clock cap exceeded", file=sys.stderr)
        return 3
    except PermissionError as e:
        print(f"ADT_SANDBOX_BLOCKED: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"ADT_SANDBOX_ERROR: {type(e).__name__}: {e}", file=sys.stderr)
        return 1
    finally:
        signal.alarm(0)
    return 0


if __name__ == "__main__":
    sys.exit(main())
