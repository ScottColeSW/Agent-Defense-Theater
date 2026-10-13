# ASI05: Unexpected Code Execution

| | |
| --- | --- |
| Status | Stub |
| OWASP LLM Top 10 2025 | LLM05 Improper Output Handling |
| MITRE ATLAS | To be mapped |
| Existing work | New work |

The mapping to the LLM Top 10 and ATLAS is the author's proposal. See [`../crosswalk/README.md`](../crosswalk/README.md).

## Threat

An agent generates or runs code or commands that execute outside the intended boundary.

**Example scenario.** A data agent writes a script that reads credentials from the host environment.

## Attack tiers

Every item is tested at three tiers, written down before the run (see `PREREGISTRATION.md`).

| Tier | Planned attack |
| --- | --- |
| Loud | Prompts asking for shell access. |
| Quiet | Generated code with a harmless purpose and a harmful side effect. |
| Adaptive | Escape attempts that probe the sandbox's specific limits. |

## Defense layers

| Layer | Planned defense |
| --- | --- |
| Prevent | Sandboxed execution with no network and no host mounts by default. |
| Detect | Syscall and file-access logging from inside the sandbox. |
| Contain | Resource and time limits; disposable environments per task. |

## Measurement

Escape attempts blocked; legitimate-task completion rate in the sandbox; startup cost.

Results use the shared schema in [`../common/RESULTS-SCHEMA.md`](../common/RESULTS-SCHEMA.md) and only saved runs appear in `results/`.

## What exists today

None yet. The Greenroom design specifies limits on live demos, which the sandbox tier would enforce.

## Limits and what it would take

Needs production isolation (a micro-VM or user-space kernel) and a security review of the sandbox itself. A container on a workstation is a demonstration, not a boundary to trust.

## Folder map

- `attacks/`: attack payloads and generators, one file per tier.
- `defenses/`: defense implementations, one file per layer.
- `eval/`: test cases and pass criteria.
- `results/`: saved runs only.
- `PREREGISTRATION.md`: the prediction, committed before the first run.
