# ASI06: Memory and Context Poisoning

| | |
| --- | --- |
| Status | Measured elsewhere |
| OWASP LLM Top 10 2025 | LLM04 Data and Model Poisoning; LLM08 Vector and Embedding Weaknesses |
| MITRE ATLAS | AML.T0070 RAG Poisoning |
| Existing work | Palimpsest and Aegis Vector |

The mapping to the LLM Top 10 and ATLAS is the author's proposal. See [`../../crosswalk/README.md`](../../crosswalk/README.md).

## Threat

Forged or manipulated content enters an agent's memory or retrieval store and shapes later decisions.

**Example scenario.** A forged policy document states a wrong spending limit and the assistant repeats it.

## Attack tiers

Every item is tested at three tiers, written down before the run (see `PREREGISTRATION.md`).

| Tier | Planned attack |
| --- | --- |
| Loud | Shouted override documents. |
| Quiet | Plausible memos written to be retrieved, borrowed real figures, and forgeries that state no number. |
| Adaptive | The inside job: a forgery built against the light defenses and sent through a trusted channel. |

## Defense layers

| Layer | Planned defense |
| --- | --- |
| Prevent | Memory gate that judges each new claim against held claims before retrieval can serve it. |
| Detect | Quarantine queue for a person to review; raise-only adjudicator. |
| Contain | External claims can never supersede held claims. |

## Measurement

Forged-answer adoption against retained utility, with cost per query. Already reported for twelve defenses.

Results use the shared schema in [`../../common/RESULTS-SCHEMA.md`](../../common/RESULTS-SCHEMA.md) and only saved runs appear in `results/`.

## What exists today

Palimpsest (memory gate) and Aegis Vector (forgery testbed). Both are linked from integrations/ and are not copied here. The Aegis Vector defenses battery is imported as schema-format records in [`results/`](results/) so it can be plotted on the [site](../../site/README.md).

## Limits and what it would take

Registered facts only; an unregistered fact is admitted. Untested: the memory write path, slow drift, many agreeing forgeries, a poisoned verified corpus. Needs: larger models, an adaptive attacker who knows the gate, and a production-size corpus.

## Folder map

- `attacks/`: attack payloads and generators, one file per tier.
- `defenses/`: defense implementations, one file per layer.
- `eval/`: test cases and pass criteria.
- `results/`: saved runs only.
- `PREREGISTRATION.md`: the prediction, committed before the first run.
