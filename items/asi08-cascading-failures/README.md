# ASI08: Cascading Failures

| | |
| --- | --- |
| Status | Measured (first preregistered live run, with an addendum) |
| OWASP LLM Top 10 2025 | LLM10 Unbounded Consumption (partial) |
| MITRE ATLAS | To be mapped |
| Existing work | New work |

The mapping to the LLM Top 10 and ATLAS is the author's proposal. See [`../../crosswalk/README.md`](../../crosswalk/README.md).

## Threat

One agent's fault, poisoned output, or runaway loop spreads through a crew and amplifies.

**Example scenario.** A bad figure from one agent is accepted by three downstream agents and acted on.

## Attack tiers

Every item is tested at three tiers, written down before the run (see `PREREGISTRATION.md`).

| Tier | Planned attack |
| --- | --- |
| Loud | A runaway loop that exhausts the crew's budget. |
| Quiet | A small error that each agent trusts and compounds. |
| Adaptive | An injected output tuned to be accepted by every downstream checker. |

## Defense layers

| Layer | Planned defense |
| --- | --- |
| Prevent | Blast-radius limits and per-agent budgets. |
| Detect | Cross-check outputs against an independent source before they fan out. |
| Contain | Circuit breakers that stop a crew and hand control to a person. |

## Measurement

Failure propagation depth; time to circuit break; cost of the runaway case.

Results use the shared schema in [`../../common/RESULTS-SCHEMA.md`](../../common/RESULTS-SCHEMA.md) and only saved runs appear in `results/`.

## What exists today

- **A live arena:** a three-agent crew (analyst fault injected, reviewer and decider live) on the ASI02 deal-desk arena, three faults, and four conditions: no defense, a verify prompt, a range check and an independent cross-check, with honest reports to show what each costs.
- **One preregistered live run** (three models, 300 records, with an addendum). With no defense 29 of 45 bad figures became a harmful offer, because the reviewer was not a check: it agreed with 78% of bad reports and 67% of honest ones. An independent recomputation stopped all 45 and cost nothing. See [`PREREGISTRATION.md`](PREREGISTRATION.md).

## Limits and what it would take

Needs production-scale topologies with many agents and real dependencies. A five-agent crew shows the mechanism, not the amplification factor.

## Folder map

- `attacks/`: attack payloads and generators, one file per tier.
- `defenses/`: defense implementations, one file per layer.
- `eval/`: test cases and pass criteria.
- `results/`: saved runs only.
- `PREREGISTRATION.md`: the prediction, committed before the first run.
