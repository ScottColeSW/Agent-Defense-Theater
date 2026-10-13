# ASI09: Human-Agent Trust Exploitation

| | |
| --- | --- |
| Status | Designed elsewhere |
| OWASP LLM Top 10 2025 | LLM09 Misinformation (partial) |
| MITRE ATLAS | To be mapped |
| Existing work | Agent Theater Framework |

The mapping to the LLM Top 10 and ATLAS is the author's proposal. See [`../crosswalk/README.md`](../crosswalk/README.md).

## Threat

An agent persuades or misleads the person reviewing it into approving a harmful action.

**Example scenario.** An agent presents a confident, well-formatted summary that hides the risky step.

## Attack tiers

Every item is tested at three tiers, written down before the run (see `PREREGISTRATION.md`).

| Tier | Planned attack |
| --- | --- |
| Loud | Urgency and authority claims. |
| Quiet | Selective summaries and routine-looking approvals that bury the change. |
| Adaptive | Approval requests timed and worded to the reviewer's observed habits. |

## Defense layers

| Layer | Planned defense |
| --- | --- |
| Prevent | Structured approval screens that show the diff, not a narrative. |
| Detect | Track reviewer approval speed and rubber-stamp patterns. |
| Contain | Oversight at three speeds, with slower review for higher-impact actions. |

## Measurement

Harmful-approval rate by presentation style; reviewer time; override rate.

Results use the shared schema in [`../common/RESULTS-SCHEMA.md`](../common/RESULTS-SCHEMA.md) and only saved runs appear in `results/`.

## What exists today

Agent Theater defines human-in-the-loop oversight at three speeds. No measurement exists yet.

## Limits and what it would take

Needs a human-subject study with real reviewers. Simulated reviewers cannot show how people actually fail.

## Folder map

- `attacks/`: attack payloads and generators, one file per tier.
- `defenses/`: defense implementations, one file per layer.
- `eval/`: test cases and pass criteria.
- `results/`: saved runs only.
- `PREREGISTRATION.md`: the prediction, committed before the first run.
