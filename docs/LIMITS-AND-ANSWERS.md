# Limits and what it would take

Every item, including the measured ones, has limits. This page collects them with the specific resource that would close each one. It is the answer to "why isn't this finished" and is part of the demo.

## Limits that apply to everything

| Limit | What it would take |
| --- | --- |
| Local models are capped by one workstation (up to roughly 8B parameters) | Access to larger or frontier models, or a GPU server, so results can be compared across sizes |
| Attacks are written by the author | An independent red team, or a public challenge, with attackers who know the defenses |
| Small samples, one scenario per item | More runs per cell, more scenarios, and published raw results |
| Simulated crews in one process | Agents on separate hosts with real network paths and key management |
| No real users | A human-subject study for the oversight and trust items |
| No production telemetry | Integration with a real logging and detection stack |

## By item

### ASI01: Agent Goal Hijack

Status: Partial evidence elsewhere.

Agent stack: only a single retrieval-and-answer loop has been tested, not a tool-using planner. Needs: a tool-using agent crew in Greenroom, an adaptive red team that is not the author, and models above the 8B size this hardware allows.

### ASI02: Tool Misuse and Exploitation

Status: Stub.

Needs a real tool catalog with realistic argument variety and an enterprise policy engine to test at scale. A single small MCP server proves the pattern, not the coverage.

### ASI03: Identity and Privilege Abuse

Status: Measured (first preregistered run, simulated desk).

One simulated agent step, author-written attacks and an author-written credential gate, three models up to 8B. Zero escapes from a deterministic gate is close to true by construction. Untested: credential lifetimes, mid-task revocation, the delegation-chain check, credentials in shared context, an escalation path for legitimate above-tier work (0 of 9 such tasks completed under scoped credentials). Needs: a real identity provider (for example Entra ID or Okta) and workload identity, a multi-step agent, and an attacker who is not the author. A local simulation shows the logic, not production behavior.

The escalation experiment adds its own limits. The approver is one small local model, not a person, so it shows what a request card lets a careful reader catch and where a model reviewer is swayed or contradicts itself, not how people behave, tire or rubber-stamp. There is no queue, no timeout and no approval fatigue. The card's checks are author-written over the operator's own words. The agent's output format moved attack-following by up to 80 points per model, so a defense measured on one prompt may not hold on another. Needs: human reviewers (a study with real approvers), stronger reviewer models, and agents that are not tuned to one prompt.

### ASI04: Agentic Supply Chain Vulnerabilities

Status: Stub.

Needs an organizational registry, software bill of materials tooling, and real package ecosystems. A toy registry cannot show scale or incentive effects.

### ASI05: Unexpected Code Execution

Status: Stub.

Needs production isolation (a micro-VM or user-space kernel) and a security review of the sandbox itself. A container on a workstation is a demonstration, not a boundary to trust.

### ASI06: Memory and Context Poisoning

Status: Measured elsewhere.

Registered facts only; an unregistered fact is admitted. Untested: the memory write path, slow drift, many agreeing forgeries, a poisoned verified corpus. Needs: larger models, an adaptive attacker who knows the gate, and a production-size corpus.

### ASI07: Insecure Inter-Agent Communication

Status: Stub.

Needs agents on separate hosts or runtimes and a real key management service. A single-process crew cannot show network-level attacks.

### ASI08: Cascading Failures

Status: Stub.

Needs production-scale topologies with many agents and real dependencies. A five-agent crew shows the mechanism, not the amplification factor.

### ASI09: Human-Agent Trust Exploitation

Status: Designed elsewhere.

Needs a human-subject study with real reviewers. Simulated reviewers cannot show how people actually fail.

### ASI10: Rogue Agents

Status: Designed elsewhere.

Needs long-horizon runs and real deployments to see slow drift. Short simulations underrepresent it.
