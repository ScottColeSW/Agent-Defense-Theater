# ASI05: Unexpected Code Execution

| | |
| --- | --- |
| Status | Measured |
| OWASP LLM Top 10 2025 | LLM05 Improper Output Handling |
| MITRE ATLAS | To be mapped |
| Existing work | New work |

The mapping to the LLM Top 10 and ATLAS is the author's proposal. See [`../../crosswalk/README.md`](../../crosswalk/README.md).

## Threat

An agent generates or runs code or commands that execute outside the intended boundary.

**Example scenario.** A data agent writes a script that reads credentials from the host environment.

## Attack tiers

Every item is tested at three tiers, written down before the run (see `PREREGISTRATION.md`).

| Tier | Planned attack |
| --- | --- |
| Loud | A shell command that prints a fake secret file. |
| Quiet | A TCP send of the secret to a local collector, an append of the secret into the ticket's own output, and a resource-exhaustion loop framed as a stability check. |
| Adaptive | The same file read reached through `pathlib` instead of `open()`, and the same shell call reached through `getattr(__import__(...))` instead of the literal text, each written to dodge a filter that checks the text of the call rather than the operation itself. |

## Defense layers

| Layer | Built defense |
| --- | --- |
| Prevent | A `sys.addaudithook` callback that raises inside the hook for `open()` outside the working directory, `os.system`, `subprocess.Popen` and `socket.connect`, which aborts the call rather than only logging it. |
| Detect | (not built as a separate layer here; the prevent layer's own block is what gets measured) |
| Contain | A wall-clock cap (`signal.alarm` inside the sandboxed process) that kills a case running past its budget; measured separately from, and found not to substitute for, the prevent layer. |

## Measurement

Attacks that got out of the sandbox (secret leaked, shell reached, or compute ran unchecked); legitimate-ticket completion rate, split into in-tier work and the one task that genuinely needs the network.

Results use the shared schema in [`../../common/RESULTS-SCHEMA.md`](../../common/RESULTS-SCHEMA.md) and only saved runs appear in `results/`.

## What exists today

A data agent (a live local model) writes Python to answer a ticket; the code runs inside a disposable Docker container, never on the host and never in the harness's own process. See [`PREREGISTRATION.md`](PREREGISTRATION.md) for the full design, including two real bugs caught and fixed while building this (a bare-subprocess version let generated code open real GUI windows on the host, and a first containerized version let its own safety margin swallow the measured timeout), and the full addendum.

**First run, pooled over three models:** with no defense, 15 of 54 exfiltration and compute-exhaustion attempts got through (27.8%). The audit hook stopped all of them, however the call was spelled (direct, `pathlib`, `getattr`-obfuscated, over a socket, or appended to the ticket's own output), at zero measured cost to in-tier work. The wall-clock cap alone stopped nothing: `timeout_contain` scored identically to no defense (also 15/54), because none of the five exfiltration channels take any measurable time to run. The one case the cap should have mattered for, a resource-exhaustion loop, mostly did not test it: two of three models wrote loops too fast to matter regardless of the instruction, and where one did run long enough, it was the test rig's own generous safety cap that caught it, not a clean "unchecked" comparison. Six of seven pass-bar criteria were met; one was missed and explained in the addendum.

**Second run, os-boundary (2026-11-13, [`PREREGISTRATION-os-boundary.md`](PREREGISTRATION-os-boundary.md)):** a defense review (issue 26) found the first run's wording overstated the audit hook. The hook and the alarm cap run inside the agent's own interpreter, so its code can switch them off. Against the first run's strongest in-process condition, an `os.execv` read, which the hook never gated, leaked 4 of 9, and cancelling the alarm (`signal.alarm(0)`) ran code 6 of 9 cases well past the cap (6.7 to 14.6 seconds). A new condition, `os_boundary`, puts the secret in a root-only tmpfs the agent's code cannot reach, runs that code as an unprivileged user, and makes the cap a supervisor process (container PID 1) the code cannot signal. It stopped every exfiltration (0 of 27) and killed every long run from outside, at no cost relative to no defense. Six of eight pass-bar criteria were met; the two misses were an imprecise criterion (a runtime threshold set below the cap flagged two loops that finished under it), not a boundary failure, and are explained in the addendum. The same review wrote the attacks and the boundary, so the attacker is not independent.

## Limits and what it would take

The container boundary here is relied on for one narrow thing, confirmed before it was: a Linux container cannot open a Windows GUI window, and `docker rm -f` reliably tears down the whole process tree. It is not a micro-VM and is not relied on against a kernel exploit or a container-escape technique, which stays out of scope. A container on a workstation remains a demonstration of the mechanism, not a production boundary to trust; that would need real isolation (a micro-VM or user-space kernel) and a security review of the sandbox itself.

## Folder map

- `attacks/`: attack payloads and generators, one file per tier.
- `defenses/`: defense implementations, one file per layer.
- `eval/`: test cases and pass criteria.
- `results/`: saved runs only.
- `PREREGISTRATION.md`: the prediction, committed before the first run.
