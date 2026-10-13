# ASI02: Tool Misuse and Exploitation

| | |
| --- | --- |
| Status | Stub |
| OWASP LLM Top 10 2025 | LLM06 Excessive Agency |
| MITRE ATLAS | AML.T0053 AI Agent Tool Invocation |
| Existing work | New work |

The mapping to the LLM Top 10 and ATLAS is the author's proposal. See [`../../crosswalk/README.md`](../../crosswalk/README.md).

## Threat

An agent uses a legitimate, authorized tool in an unsafe way because of manipulated input, ambiguous instructions, or over-broad tool permissions.

**Example scenario.** An analysis agent with a file tool is steered into overwriting a source record instead of reading it.

## Attack tiers

Every item is tested at three tiers, written down before the run (see `PREREGISTRATION.md`).

| Tier | Planned attack |
| --- | --- |
| Loud | Direct requests for destructive tool arguments. |
| Quiet | Benign-looking arguments that chain into harm across calls. |
| Adaptive | Argument shapes crafted to pass the policy gate's own rules. |

## Defense layers

| Layer | Planned defense |
| --- | --- |
| Prevent | Policy gate in front of every tool call with per-tool argument schemas and allowlists. |
| Detect | Log every call and argument; alert on out-of-pattern sequences. |
| Contain | Rate limits, dry-run mode, and reversible operations by default. |

## Measurement

Unsafe-call block rate against legitimate-call pass rate; latency added per call.

Results use the shared schema in [`../../common/RESULTS-SCHEMA.md`](../../common/RESULTS-SCHEMA.md) and only saved runs appear in `results/`.

## What exists today

None yet. RealEstateTools (an MCP server) is the planned target.

## Limits and what it would take

Needs a real tool catalog with realistic argument variety and an enterprise policy engine to test at scale. A single small MCP server proves the pattern, not the coverage.

## Folder map

- `attacks/`: attack payloads and generators, one file per tier.
- `defenses/`: defense implementations, one file per layer.
- `eval/`: test cases and pass criteria.
- `results/`: saved runs only.
- `PREREGISTRATION.md`: the prediction, committed before the first run.
