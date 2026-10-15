# ASI09: Human-Agent Trust Exploitation

| | |
| --- | --- |
| Status | Partly measured: AI reviewers measured, a people study built and waiting for participants |
| OWASP LLM Top 10 2025 | LLM09 Misinformation (partial) |
| MITRE ATLAS | To be mapped |
| Existing work | Agent Theater Framework |

The mapping to the LLM Top 10 and ATLAS is the author's proposal. See [`../../crosswalk/README.md`](../../crosswalk/README.md).

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

Results use the shared schema in [`../../common/RESULTS-SCHEMA.md`](../../common/RESULTS-SCHEMA.md) and only saved runs appear in `results/`.

## What exists today

- **AI reviewers, measured.** The [ASI03 reviewer-calibration run](../asi03-identity-privilege/PREREGISTRATION-reviewer-calibration.md) put 22 request cards to seven models in three presentation styles. Shown the agent's own account, reviewers approved 40% of the requests that did not match what the operator asked, against 6% when the system's comparison came first.
- **A study of people, built.** [`site/study.html`](../../site/study.html) (start the runner with `python adt.py serve --open`, then open `/study.html`) puts the same cards to a person and records each decision and the time taken, anonymously. `python adt.py study` and `study.html?view=summary` show the results beside the models'. The [protocol](STUDY-PROTOCOL.md), with the prediction and pass bar, is committed before the first participant.
- **No participants yet.** Nothing is reported as a result until at least five people have finished.

## Limits and what it would take

Needs a human-subject study with real reviewers. Simulated reviewers cannot show how people actually fail.

## Folder map

- `attacks/`: attack payloads and generators, one file per tier.
- `defenses/`: defense implementations, one file per layer.
- `eval/`: test cases and pass criteria.
- `results/`: saved runs only.
- `PREREGISTRATION.md`: the prediction, committed before the first run.
