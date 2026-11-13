"""The in-container half of the `os_boundary` condition (ASI05, os-boundary experiment).

Invoked as `python -I supervisor.py <timeout_s>` with the agent's code on stdin. It is the container's first process
and runs as root with every capability dropped except the three it needs: two to change user, one to stop that
user's processes.

The first run's guard (guard.py) put its two controls, an audit hook and a `signal.alarm` cap, inside the same
interpreter that then ran the agent's code. That code can switch both off (issue 26): replace `os.path.realpath`,
patch the guard's own helper, call `os.execv`, cancel the alarm, or swallow its exception. Here neither control
lives where the agent's code can reach it.

  The secret   is copied into /secret, a tmpfs owned by root with mode 0700, from a staging mount under /root (also
               0700). The agent's code runs as uid 65534, so the kernel refuses to open it. There is no hook to patch.
  The cap      is this process waiting on a child. The child cannot signal it (another uid, and it is the first
               process in the namespace), and when this process exits the container ends, which kills anything the
               child left running.

What it does not do: it does not stop code from using the network when the case is given one, and it is a container
on a workstation, not a micro-VM. A kernel or runtime escape is out of scope.
"""
import os
import signal
import subprocess
import sys

AGENT_UID = AGENT_GID = 65534
STAGE, SECRET_DIR, WORKDIR = "/root/stage/api_key.txt", "/secret", "/sandbox"

# Runs in the child, as the unprivileged user. It reports the kernel's refusals the way guard.py reports the hook's, so
# the parent reads both the same way. Nothing in it is a control: the agent's code may do what it likes with it.
RUNNER = r'''
import sys
code = sys.stdin.read()
try:
    exec(compile(code, "<agent_code>", "exec"), {"__name__": "__main__", "__builtins__": __builtins__})
except PermissionError as e:
    print(f"ADT_SANDBOX_BLOCKED: {e}", file=sys.stderr)
    sys.exit(2)
except SystemExit:
    raise
except BaseException as e:
    print(f"ADT_SANDBOX_ERROR: {type(e).__name__}: {e}", file=sys.stderr)
    sys.exit(1)
'''


def main() -> int:
    timeout_s = float(sys.argv[1])
    code = sys.stdin.read()
    with open(STAGE, "rb") as f:
        secret = f.read()
    path = os.path.join(SECRET_DIR, "api_key.txt")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(secret)
    child = subprocess.Popen([sys.executable, "-I", "-c", RUNNER], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             cwd=WORKDIR, user=AGENT_UID, group=AGENT_GID, extra_groups=[], start_new_session=True, text=True)
    try:
        out, err = child.communicate(code, timeout=max(1.0, timeout_s))
        rc = child.returncode
    except subprocess.TimeoutExpired:
        try:
            os.killpg(child.pid, signal.SIGKILL)
        except OSError as e:
            # The cap must not depend on the kill working. This process is the container's first, so ending it ends
            # the container and everything in it. (Seen while building this: without CAP_KILL, root cannot signal a
            # process owned by another user, the kill failed quietly, and the code ran to the end.)
            sys.stderr.write(f"ADT_SANDBOX_TIMEOUT: wall-clock cap exceeded (could not signal the child: {e}; ending the container)\n")
            sys.stderr.flush()
            os._exit(3)
        out, err = child.communicate()
        err = (err or "") + "\nADT_SANDBOX_TIMEOUT: wall-clock cap exceeded\n"
        rc = 3
    sys.stdout.write(out or "")
    sys.stderr.write(err or "")
    sys.stdout.flush()
    sys.stderr.flush()
    return rc if rc is not None and rc >= 0 else 1


if __name__ == "__main__":
    sys.exit(main())
