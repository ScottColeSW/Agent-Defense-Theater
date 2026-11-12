# Purple team capability map

This repository is a purple-team range for AI agents: attacks and defenses are tested together, and each result feeds the next defense. This page sets it beside the capability list in the OWASP GenAI Security Project's red teaming solutions guide taxonomy (version 1.0, CC BY-SA 4.0), so a reader used to that vocabulary can see what the range has and what it lacks.

**How to read it.** The mapping is the author's. It says where this repository has something relevant, not that it is a commercial-grade solution or that OWASP endorses it. The capability names are the taxonomy's. Status means:

- **Have**: saved evidence in the repository.
- **Partial**: something relevant exists, with a stated gap.
- **Stub**: not built. Each stub is also listed in [`OPEN-WORK.md`](OPEN-WORK.md).
- **Not planned**: the capability does not fit a range like this one, with the reason beside it.

## Purple teaming capabilities

| Capability (taxonomy) | Status | Where in this repository |
| --- | --- | --- |
| Map red scenarios to blue controls | Have | Every item pairs attack tiers with defense layers, and [`crosswalk/coverage.csv`](../crosswalk/coverage.csv) shows the coverage |
| Import red scenarios | Partial | `python adt.py attackgen` and `informed` bring in attacks written by other models, saved with a hash. No import from an outside scenario library |
| Interactive sandbox | Partial | The local range and the ASI05 container. A workstation range, not a shared environment |
| Defender signal analysis | Partial | ASI10's flag-only detector and the decision log record what a detector saw. No signal-quality analysis |
| Reasoning-trace capture | Partial | The thinking model's reasoning is saved in the reviewer-calibration run. Other runs keep replies, not reasoning |
| One-click purple runs | Partial | `python adt.py run` and the runner page score attack and defense together. One command per item, not one for everything |
| Metrics exporting (blue KPIs) | Partial | The results schema and reports. No export to a metrics system |
| Success-threshold analysis | Have | Every preregistration writes a pass bar before the run, and each criterion is reported on its own |
| Protocol spoofing (MCP / A2A) | Partial | ASI07 tests forged and replayed messages between agents, and ASI02 uses real MCP servers. Both are in one process |
| Cost-impact tracking | Have | Every report splits latency and tokens by defense, and hosted spend is capped and recorded |
| Continuous Integration hooks | Stub | No CI workflow in the repository |
| Auto-ticketing for failed tests | Stub | Failures are written up in addenda by hand |
| Hallucination vs misalignment labeling | Stub | Outcomes are scored as attack succeeded, blocked or valid work done. Causes are not classified |
| Closed-loop purple coaching, rule tuning, auto guardrail patching | Stub | Defenses are changed by the author between rounds, with each round preregistered. Nothing tunes them automatically |
| Agent behavior baselining | Stub | Black ICE lists a learned-baseline test against a slow-drift bot as a next step |
| Red/blue alert correlation, purple SIEM lens, merged telemetry | Stub | The decision log is a record, not a SIEM integration |
| Time-series scoring, model-drift vs threat-drift analysis | Stub | Runs are single rounds. No trend over time |
| Residual risk analysis cycles | Partial | Each addendum lists what was not shown. No scheduled cycle |
| Real-time policy shadow mode | Stub | Not built. A defense is either in a run or not, so there is no observe-only comparison. See [issue 18](https://github.com/ScottColeSW/Agent-Defense-Theater/issues/18) |
| Corpus diffing | Stub | Not built. ASI06 corpora are compared by reading. See [issue 19](https://github.com/ScottColeSW/Agent-Defense-Theater/issues/19) |
| Rollback script generation | Not planned | There is no release pipeline to roll back. The range runs experiments, not deployments |
| Risk simulators | Not planned | Forward-looking risk modeling would be speculation, which the preregistration rules are written to avoid. Revisit if a measured basis appears |

## Red teaming capabilities this range exercises

| Capability (taxonomy) | Status | Where |
| --- | --- | --- |
| Prompt-chaining and multi-turn attacks | Partial | ASI10 uses four check-ins. ASI01 is a single retrieval loop |
| Protocol attacks (A2A, MCP) | Partial | ASI07 and ASI02, as above |
| RAG-poison scenario runners, memory poisoning | Have | ASI06, with Palimpsest and Aegis Vector |
| Supply-chain attack simulation | Partial | ASI04 uses a tampered proxy, not real packages |
| Tool-chain and plug-in misuse simulation | Have | ASI02 |
| Agent privilege-escalation emulation | Have | ASI03 |
| Synthetic user and rogue-agent generation | Partial | ASI10 simulates a drifting agent. No generator of varied rogue agents |
| Autonomous red bots | Partial | Hosted and local models write attacks and learn from outcomes (`informed`). Not continuous |
| Audit-grade attack-path replay | Have | Preregistration, raw records and a hash-chained decision log that `python adt.py verify` checks |
| Cross-tenant data exposure testing | Stub | Not modeled |
| Continuous prompt fuzzing | Stub | Not built |

## Shared capabilities

| Capability (taxonomy) | Status | Where |
| --- | --- | --- |
| Framework mapping | Have | [`crosswalk/`](../crosswalk/README.md) and [`GOVERNANCE-CROSSWALK.md`](GOVERNANCE-CROSSWALK.md) |
| Signed artifact stores | Partial | The decision log is tamper-evident, and it detects tampering without preventing it. See [`common/decision-log/VERIFY.md`](../common/decision-log/VERIFY.md) |
| Export of tests as stories | Partial | The role questions and checklist put each result in plain language beside its caveat |
| Risk taxonomy import and export | Partial | The coverage CSV and JSON. No standard interchange format |
| AI-BOM / SBOM diffing | Stub | Run metadata records model digests, settings and commits, but nothing compares two runs. See [issue 20](https://github.com/ScottColeSW/Agent-Defense-Theater/issues/20) |
| Executive reporting | Stub | The role questions and checklist are plain-language, but there is no one-page summary of a run's pass bar and caveats |

Source: OWASP GenAI Security Project, Gen AI and Agentic Red Teaming Solutions Guide taxonomy, version 1.0, CC BY-SA 4.0. Capability names are quoted for mapping only, and the descriptions are the author's.
