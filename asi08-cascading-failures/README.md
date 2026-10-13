# ASI08: Cascading Failures

| | |
| --- | --- |
| Status | Stub |
| OWASP LLM Top 10 2025 | LLM10 Unbounded Consumption (partial) |
| MITRE ATLAS | To be mapped |
| Existing work | New work |

The mapping to the LLM Top 10 and ATLAS is the author's proposal. See [`../crosswalk/README.md`](../crosswalk/README.md).

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

Results use the shared schema in [`../common/RESULTS-SCHEMA.md`](../common/RESULTS-SCHEMA.md) and only saved runs appear in `results/`.

## What exists today

Void-Marauders shows outcome-sensitive trust between agents, which informs the breaker rules.

## Limits and what it would take

Needs production-scale topologies with many agents and real dependencies. A five-agent crew shows the mechanism, not the amplification factor.

## Folder map

- `attacks/`: attack payloads and generators, one file per tier.
- `defenses/`: defense implementations, one file per layer.
- `eval/`: test cases and pass criteria.
- `results/`: saved runs only.
- `PREREGISTRATION.md`: the prediction, committed before the first run.
