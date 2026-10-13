# ASI10: Rogue Agents

| | |
| --- | --- |
| Status | Designed elsewhere |
| OWASP LLM Top 10 2025 | LLM06 Excessive Agency |
| MITRE ATLAS | To be mapped |
| Existing work | Agent Theater Framework and Void-Marauders |

The mapping to the LLM Top 10 and ATLAS is the author's proposal. See [`../../crosswalk/README.md`](../../crosswalk/README.md).

## Threat

An agent drifts from its intended scope or acts deceptively, whether through compromise or misalignment.

**Example scenario.** A trusted agent starts taking actions outside its task and reports them as routine.

## Attack tiers

Every item is tested at three tiers, written down before the run (see `PREREGISTRATION.md`).

| Tier | Planned attack |
| --- | --- |
| Loud | An agent that openly ignores its instructions. |
| Quiet | Gradual scope creep that stays under each individual threshold. |
| Adaptive | An agent that behaves well while it believes it is observed. |

## Defense layers

| Layer | Planned defense |
| --- | --- |
| Prevent | Earned trust: new agents start on probation with the lowest privilege tier. |
| Detect | Classify agents as performing, miscast, or bad from outcome history. |
| Contain | Demotion and quarantine; kill switch owned by a person. |

## Measurement

Time to detect a rogue agent; false demotion rate; harm before containment.

Results use the shared schema in [`../../common/RESULTS-SCHEMA.md`](../../common/RESULTS-SCHEMA.md) and only saved runs appear in `results/`.

## What exists today

Agent Theater's three-tier taxonomy and Void-Marauders' outcome-sensitive loyalty and mutiny model.

## Limits and what it would take

Needs long-horizon runs and real deployments to see slow drift. Short simulations underrepresent it.

## Folder map

- `attacks/`: attack payloads and generators, one file per tier.
- `defenses/`: defense implementations, one file per layer.
- `eval/`: test cases and pass criteria.
- `results/`: saved runs only.
- `PREREGISTRATION.md`: the prediction, committed before the first run.
