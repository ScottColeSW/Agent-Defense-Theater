# ASI01: Agent Goal Hijack

| | |
| --- | --- |
| Status | Measured (first preregistered live run, with an addendum) |
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
- **One preregistered live run** (three models, 480 records, with an addendum that reports the misses). A plan written before the agent reads anything untrusted stopped every goal change that needed a new tool (0 of 36) and a goal check by a separate reviewer model stopped all 45 hijacks, at some cost in valid work. Spotlighting, the defense expected to help, made hijacks more likely (73% against 49% with no defense) and the run does not explain why. See [`PREREGISTRATION.md`](PREREGISTRATION.md).
- **A follow-up on the spotlighting result** ([`PREREGISTRATION-spotlighting.md`](PREREGISTRATION-spotlighting.md), 630 records). The effect replicated on deals the first run did not use (80% against 43%) and lives in the soft attacks. It was not the rule's wording: a plain two-sentence rule raised hijacks too (61%), and a rule that names the forbidden actions did not cut them (53% against 47%). Any security rule added to the prompt raised the rate here. A second follow-up ([`PREREGISTRATION-rule-priming.md`](PREREGISTRATION-rule-priming.md), 375 records) found it was not rule-following either: an unrelated rule did not raise it, and about 48 words of plain background about the desk raised it as much as the security rule (soft hijacks 77% against 40%). Whether the topic or the length of the added text matters is open, and the unrelated rule in that test was half the length of the others, so it cannot say.

## Limits and what it would take

Agent stack: only a single retrieval-and-answer loop has been tested, not a tool-using planner. Needs: a tool-using agent crew in Greenroom, an adaptive red team that is not the author, and models above the 8B size this hardware allows.

## Folder map

- `attacks/`: attack payloads and generators, one file per tier.
- `defenses/`: defense implementations, one file per layer.
- `eval/`: test cases and pass criteria.
- `results/`: saved runs only.
- `PREREGISTRATION.md`: the prediction, committed before the first run.
