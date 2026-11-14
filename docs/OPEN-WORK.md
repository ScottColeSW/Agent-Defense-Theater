# Open work

Every item below is a stub: a gap the project knows about and has not closed. Each one is taken from [`LIMITS-AND-ANSWERS.md`](LIMITS-AND-ANSWERS.md) or the [crosswalk](../crosswalk/README.md), so nothing here is a new claim. Status for all of them is **Stub, unclaimed**.

To take one: say so in an issue, copy [`PREREGISTRATION-TEMPLATE.md`](PREREGISTRATION-TEMPLATE.md) into the item folder, commit the prediction, then run. See [`../CONTRIBUTING.md`](../CONTRIBUTING.md).

## Cuts across every item

| Gap | What it would take |
| --- | --- |
| Attacks are written by the author | An independent red team, or a public challenge, with attackers who know the defenses |
| Local models are capped near 8B parameters | Larger or frontier models, or a GPU server, for a comparison across sizes |
| Small samples, one scenario per item | More runs per cell, more scenarios, published raw results |
| Simulated crews in one process | Agents on separate hosts with real network paths and key management |
| No production telemetry | Integration with a real logging and detection stack |

## By item

| Item | Stub | What it would take |
| --- | --- | --- |
| ASI01 | Tool-using planner, adaptive red team | A tool-using agent crew, an attacker who is not the author, goal checks across several models |
| ASI02 | Larger tool catalog | Realistic argument variety, an enterprise policy engine, a multi-step agent |
| ASI03 | Vague and partial requests; attacks on request binding | Operator requests that are not stated plainly, adaptive attacks on the binding, reviewers other than two 7 to 8B models |
| ASI03 | Credential lifetimes, mid-task revocation, delegation-chain check | A real identity provider and workload identity, a multi-step agent |
| ASI04 | Time-delayed tampering, real packages | An organizational registry, software bill of materials tooling, a way to hash a remote server |
| ASI05 | Production isolation | A micro-VM or user-space kernel, a security review of the sandbox, a non-author attacker |
| ASI06 | Slow drift, many agreeing forgeries, poisoned verified corpus | Larger models, an attacker who knows the gate, a production-size corpus |
| ASI07 | Network-level attacks | Agents on separate hosts or runtimes, a real key management service |
| ASI08 | Agent-produced failures | Production-scale topologies with many agents, failures that agents cause rather than injected faults |
| ASI09 | Replication of the people study | A shorter, clearer card, read independently, with more participants and real queue pressure |
| ASI10 | Long-horizon drift | Runs longer than four check-ins, pressures other than market commentary (a forged identity or a compromised channel) |
| Black ICE | Later rungs | The rungs beyond containment under spoofed alarms are designed and do not run yet. See [`../blackice/README.md`](../blackice/README.md) |

## Purple team tooling stubs

From the capability map in [`PURPLE-TEAM-MAP.md`](PURPLE-TEAM-MAP.md). Each is a stub.

| Stub | Starting point |
| --- | --- |
| A continuous integration workflow that runs the tests on every pull request | The `pytest` suite already runs from `common/tests`. Needs a workflow file and a decision about which tests need a live model |
| Auto-created issues for failed pass-bar criteria | The pass-bar scoring lives in `common/adt/passbar.py`, so a failed criterion can be detected in code |
| Classify failures as error or misalignment | Outcomes are scored without causes. Start with the ASI10 records |
| Learned behavior baseline against slow drift | Listed as a next step in the Black ICE roadmap |
| Trend scoring across repeated rounds | Needs the same experiment run on a schedule |
| Cross-tenant exposure test | Not modeled in any item |
| Continuous prompt fuzzing | Not built. `attackgen` is the nearest starting point |
| Real-time policy shadow mode | Wrap a broker so it records what it would have decided without enforcing it. The KTP broker already returns structured decisions. [Issue 18](https://github.com/ScottColeSW/Agent-Defense-Theater/issues/18) |
| Corpus diffing | A read-only diff of two ASI06 corpus versions. [Issue 19](https://github.com/ScottColeSW/Agent-Defense-Theater/issues/19) |
| AI-BOM / SBOM diffing | A read-only diff of the behavior-defining elements in two runs' metadata. [Issue 20](https://github.com/ScottColeSW/Agent-Defense-Theater/issues/20) |
| Executive reporting | A one-page plain-language summary of a run's pass bar and caveats. Start from the pass-bar console issue ([issue 3](https://github.com/ScottColeSW/Agent-Defense-Theater/issues/3)) |

## Field-context stubs

Surfaces named in the State of Agentic AI Security and Governance report (v2.01, June 2026) that no item here tests. See [`GOVERNANCE-CROSSWALK.md`](GOVERNANCE-CROSSWALK.md). Each is a stub.

| Stub | Why it matters | Starting point |
| --- | --- | --- |
| Coding agent inside a CI pipeline | It ingests input from outside contributors by design, so controls built for a trusted developer may not transfer | The ASI01 and ASI05 scenarios, with the attacker as the untrusted contributor |
| Approval load and fatigue | The report names decision fatigue with hundreds of prompts. The ASI09 pilot had no volume | A study with a real queue and a time limit, after the clearer card exists |
| Delegation through spawned sub-agents | Credentials inherited from a parent agent and revocation through a chain | The untested delegation-chain check in ASI03 |
| Shadow AI discovered through delegated OAuth access | Broad delegated scopes granted to third-party AI tools | The loose-keys toolkit in [`LOOSE-KEYS.md`](LOOSE-KEYS.md) already audits a grant inventory |
| Trajectory-level logging | The report calls it a primary runtime control. The decision log records each defense decision, not the full agent trajectory | Extend the decision log entry format in `common/decision-log/FORMAT.md` |
| Capability composition as a design gate (the "Rule of Two") | The Securing Agentic Applications guide says an agent should not combine private data, untrusted input and external communication. No item tests it | A scenario where an agent holds all three and one leg is then removed |
| Graduated kill switch (warn, limit, suspend, kill) | ASI10 tested a one-step kill switch only | Extend the ASI10 defenses with tiers and measure restricted calls per tier |
| Block a release when behavior-defining elements change results | The guide asks for revalidation when the model, prompt or tool set changes. Here it is manual | Re-run a fixed set of preregistered cases when `common/` or an item's prompt changes, which also needs the CI stub above |
| Check recorded successes and blocks for unintended routes | The exploit-generation report finds scores inflated by unintended solutions. Outcomes here are not checked that way | Partly done. `tools/audit_decision_logs.py` (by miaoyang-data) flags repeated allowed calls, shared-token allows and missing reasons in the saved logs. It does not read how an outcome was reached. Sampled route traces across all streak classes are documented in [`LOG-AUDIT-FINDINGS.md`](LOG-AUDIT-FINDINGS.md) ([issue 13](https://github.com/ScottColeSW/Agent-Defense-Theater/issues/13)). Broader sampling of non-loop trajectories remains open |
| Repetitive tool-loop detection | The report notes high-frequency, low-diversity tool calls as a candidate signal for model-driven activity | Measured, no detector yet. `tools/audit_decision_logs.py` (by miaoyang-data) finds consecutive identical calls in the saved logs. It recovers the 32 repeated refunds in each run that uses the duplicate-refund texts, and finds no repeated allowed call in any other ASI03 run. Where a log does not record arguments (ASI10) it can only show a repeated tool. The findings note comparing duplicate-refund probes against valid tasks and `probe_failed_first` controls across 39 runs is now in [`LOG-AUDIT-FINDINGS.md`](LOG-AUDIT-FINDINGS.md) ([issue 12](https://github.com/ScottColeSW/Agent-Defense-Theater/issues/12)); a live runtime detector remains open |

## Mapping stubs

| Gap | Where | Starting point |
| --- | --- | --- |
| MITRE ATLAS IDs are "To be mapped" for most rows | `crosswalk/coverage.csv` | Candidates from the OWASP LLM Top 10 are listed in [`../crosswalk/README.md`](../crosswalk/README.md). Verify each against the current ATLAS release before filling it in |
| No item maps to LLM02 Sensitive Information Disclosure or LLM07 System Prompt Leakage | `crosswalk/coverage.csv` | ASI05's secret-exfiltration attacks overlap LLM02. Decide whether to add a partial match |
| ASI07 has no direct LLM Top 10 match | `crosswalk/coverage.csv` | Confirm that is still true against the OWASP Agentic Top 10 text |

