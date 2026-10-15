# ASI04: Agentic Supply Chain Vulnerabilities

| | |
| --- | --- |
| Status | Measured (first preregistered live run, with an addendum) |
| OWASP LLM Top 10 2025 | LLM03 Supply Chain |
| MITRE ATLAS | To be mapped |
| Existing work | New work |

The mapping to the LLM Top 10 and ATLAS is the author's proposal. See [`../../crosswalk/README.md`](../../crosswalk/README.md).

## Threat

Tools, MCP servers, models, prompts, or plugins that an agent loads at runtime are compromised or swapped.

**Example scenario.** A tool manifest is changed after review so that a trusted tool name now exfiltrates data.

## Attack tiers

Every item is tested at three tiers, written down before the run (see `PREREGISTRATION.md`).

| Tier | Planned attack |
| --- | --- |
| Loud | An obviously malicious tool added to the registry. |
| Quiet | A look-alike tool name or a version bump that changes behavior. |
| Adaptive | A tool that behaves correctly until it detects it is not under test. |

## Defense layers

| Layer | Planned defense |
| --- | --- |
| Prevent | Pinned and signed tool manifests; an allowlist of frameworks and model hashes. |
| Detect | Re-verify manifests at load time and diff behavior against the reviewed version. |
| Contain | Run unreviewed tools in the sandbox tier with no network. |

## Measurement

Tampered-tool detection rate; false-block rate on legitimate updates; review time per tool.

Results use the shared schema in [`../../common/RESULTS-SCHEMA.md`](../../common/RESULTS-SCHEMA.md) and only saved runs appear in `results/`.

## What exists today

- **A live arena:** the ASI02 deal-desk agent with the RealEstateTools calculator server as the reviewed tool, tampered stand-ins staged by a proxy ([`targets/mutating_proxy.py`](targets/mutating_proxy.py)), and three load-time controls (a manifest pin, a canary comparison, a code pin) with a legitimate update to show their cost.
- **One preregistered live run** (three models, 450 records, with an addendum). Each load-time control saw exactly what it was built to see: the manifest pin stopped every poisoned description and look-alike, the canary comparison stopped a plain change in answers and was fooled by a tool that recognizes the check, and the code pin stopped everything and refused every legitimate update. See [`PREREGISTRATION.md`](PREREGISTRATION.md).

## Limits and what it would take

Needs an organizational registry, software bill of materials tooling, and real package ecosystems. A toy registry cannot show scale or incentive effects.

## Folder map

- `attacks/`: attack payloads and generators, one file per tier.
- `defenses/`: defense implementations, one file per layer.
- `eval/`: test cases and pass criteria.
- `results/`: saved runs only.
- `PREREGISTRATION.md`: the prediction, committed before the first run.
