# ASI01: Agent Goal Hijack

| | |
| --- | --- |
| Status | Built (prediction committed, first live run pending) |
| OWASP LLM Top 10 2025 | LLM01 Prompt Injection |
| MITRE ATLAS | AML.T0051 (.000 direct, .001 indirect) |
| Existing work | Aegis Vector (injection and spotlighting results) |

The mapping to the LLM Top 10 and ATLAS is the author's proposal. See [`../../crosswalk/README.md`](../../crosswalk/README.md).

## Threat

An attacker redirects what the agent is trying to do, through instructions hidden in content the agent reads or through manipulated task context.

**Example scenario.** A retrieved document tells a procurement agent to ignore its policy and approve a purchase.

## Attack tiers

Every item is tested at three tiers, written down before the run (see `PREREGISTRATION.md`).

| Tier | Planned attack |
| --- | --- |
| Loud | Shouted overrides and injected system-style instructions. |
| Quiet | Plausible memos and task reframing that carry no instruction words. |
| Adaptive | Payloads written against the specific defenses in place, including forged trusted-channel stamps. |

## Defense layers

| Layer | Planned defense |
| --- | --- |
| Prevent | Treat retrieved text as data (spotlighting); lock the goal in a signed task record. |
| Detect | Compare each planned action to the signed goal and flag drift. |
| Contain | Plan-diff approval gate before any irreversible action. |

## Measurement

Goal-hijack rate against retained task utility; approval-gate false-hold rate; cost per task.

Results use the shared schema in [`../../common/RESULTS-SCHEMA.md`](../../common/RESULTS-SCHEMA.md) and only saved runs appear in `results/`.

## What exists today

- **A live arena** (reused from ASI02): a deal-desk agent, two real MCP servers and a SQLite pipeline. Five author-written attacks that try to replace or extend the operator's goal, the same valid tasks as ASI02, and five conditions: no defense, spotlighting, a plan locked before the agent reads anything untrusted, a goal check by a separate reviewer model, and the last two together.
- **Not run live yet.** The prediction and pass bar are in [`PREREGISTRATION.md`](PREREGISTRATION.md). Aegis Vector's spotlighting results are sibling evidence.

## Limits and what it would take

Agent stack: only a single retrieval-and-answer loop has been tested, not a tool-using planner. Needs: a tool-using agent crew in Greenroom, an adaptive red team that is not the author, and models above the 8B size this hardware allows.

## Folder map

- `attacks/`: attack payloads and generators, one file per tier.
- `defenses/`: defense implementations, one file per layer.
- `eval/`: test cases and pass criteria.
- `results/`: saved runs only.
- `PREREGISTRATION.md`: the prediction, committed before the first run.
