# ASI03: Identity and Privilege Abuse

| | |
| --- | --- |
| Status | Stub |
| OWASP LLM Top 10 2025 | LLM06 Excessive Agency |
| MITRE ATLAS | To be mapped |
| Existing work | New work |

The mapping to the LLM Top 10 and ATLAS is the author's proposal. See [`../crosswalk/README.md`](../crosswalk/README.md).

## Threat

Agents inherit or cache credentials and delegate authority in ways that let one compromised agent act with more privilege than its task needs.

**Example scenario.** A low-trust agent reuses a high-privilege agent's token it found in shared context.

## Attack tiers

Every item is tested at three tiers, written down before the run (see `PREREGISTRATION.md`).

| Tier | Planned attack |
| --- | --- |
| Loud | Asking a peer agent to act on the attacker's behalf. |
| Quiet | Confused-deputy requests that look like normal delegation. |
| Adaptive | Replay and relay of short-lived credentials within their lifetime. |

## Defense layers

| Layer | Planned defense |
| --- | --- |
| Prevent | Per-agent scoped credentials, short lifetimes, and no credentials in shared context. |
| Detect | Record the delegation chain for every action and check it against policy. |
| Contain | Revocation that takes effect mid-task; privilege ceilings per trust tier. |

## Measurement

Unauthorized-action block rate; credential exposure in context; time to revoke.

Results use the shared schema in [`../common/RESULTS-SCHEMA.md`](../common/RESULTS-SCHEMA.md) and only saved runs appear in `results/`.

## What exists today

Agent Theater's trust tiers define the privilege ceilings but no credential layer exists yet.

## Limits and what it would take

Needs a real identity provider (for example Entra ID or Okta) and workload identity. A local simulation shows the logic, not production behavior.

## Folder map

- `attacks/`: attack payloads and generators, one file per tier.
- `defenses/`: defense implementations, one file per layer.
- `eval/`: test cases and pass criteria.
- `results/`: saved runs only.
- `PREREGISTRATION.md`: the prediction, committed before the first run.
