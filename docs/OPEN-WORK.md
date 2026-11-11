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

## Mapping stubs

| Gap | Where | Starting point |
| --- | --- | --- |
| MITRE ATLAS IDs are "To be mapped" for most rows | `crosswalk/coverage.csv` | Candidates from the OWASP LLM Top 10 are listed in [`../crosswalk/README.md`](../crosswalk/README.md). Verify each against the current ATLAS release before filling it in |
| No item maps to LLM02 Sensitive Information Disclosure or LLM07 System Prompt Leakage | `crosswalk/coverage.csv` | ASI05's secret-exfiltration attacks overlap LLM02. Decide whether to add a partial match |
| ASI07 has no direct LLM Top 10 match | `crosswalk/coverage.csv` | Confirm that is still true against the OWASP Agentic Top 10 text |
