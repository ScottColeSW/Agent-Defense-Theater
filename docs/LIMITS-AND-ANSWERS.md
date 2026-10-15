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

Status: Measured (first preregistered live run), with sibling evidence in Aegis Vector.

One agent on one simulated desk, author-written attacks, and three small models. The goal check is one small model on one prompt, and the plan lock assumes a trusted, complete request. Needs: a tool-using agent crew, an adaptive red team that is not the author, goal checks across several models, and models above the 8B size this hardware allows. Spotlighting made hijacks more likely here, replicated on new deals, and a follow-up showed it was the presence of a security rule and not its wording. Why is still open: the leading reading, that a rule primes the model to follow procedures it meets afterward, is untested.

### ASI02: Tool Misuse and Exploitation

Status: Measured (first preregistered live run).

Two small MCP servers (the author's RealEstateTools calculators and a purpose-built SQLite Deal Desk) show the pattern, not the coverage. Needs a larger real tool catalog with realistic argument variety, an enterprise policy engine, a multi-step agent, and an attacker who is not the author.

### ASI03: Identity and Privilege Abuse

Status: Measured (first preregistered run, simulated desk).

One simulated agent step, author-written attacks and an author-written credential gate, three models up to 8B. Zero escapes from a deterministic gate is close to true by construction. Untested: credential lifetimes, mid-task revocation, the delegation-chain check, credentials in shared context, an escalation path for legitimate above-tier work (0 of 9 such tasks completed under scoped credentials). Needs: a real identity provider (for example Entra ID or Okta) and workload identity, a multi-step agent, and an attacker who is not the author. A local simulation shows the logic, not production behavior.

The escalation experiment adds its own limits. The approver is one small local model, not a person, so it shows what a request card lets a careful reader catch and where a model reviewer is swayed or contradicts itself, not how people behave, tire or rubber-stamp. There is no queue, no timeout and no approval fatigue. The card's checks are author-written over the operator's own words. The agent's output format moved attack-following by up to 80 points per model, so a defense measured on one prompt may not hold on another. Needs: human reviewers (a study with real approvers), stronger reviewer models, and agents that are not tuned to one prompt.

The third round adds: every operator request in it states its amount and destination plainly and is compared by simple text matching, so request binding and the bottom-line card look better than they would against vague requests. The rule, the card and the binding share one comparison, so the round tests whether models follow it and what the design costs, not whether the comparison is right. One reviewer model followed the card and another did not, which means a reviewer's result does not transfer between models. No attack was written against the binding or the bottom line. Needs: vague and partial requests, adaptive attacks on the binding, reviewer calibration sets, and reviewers other than two 7 to 8B local models.

### ASI04: Agentic Supply Chain Vulnerabilities

Status: Measured (first preregistered live run).

The tampered tools are a proxy in front of one reviewed server, not real compromised packages, and there is no time-delayed tampering. Needs an organizational registry, software bill of materials tooling, real package ecosystems, and a way to hash a remote server, which the code pin cannot do. A toy registry cannot show scale or incentive effects.

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

Status: Measured (first preregistered live run).

The fault is injected at the first of three stages, and the reviewer and decider are the same model. This shows whether a bad figure crosses two hops, not the amplification factor. Needs production-scale topologies with many agents and real dependencies, and a crew whose failures are produced by agents and not injected.

### ASI09: Human-Agent Trust Exploitation

Status: AI reviewers measured (the ASI03 calibration run), a people study built and waiting for participants.

Needs a human-subject study with real reviewers, which the study page now makes possible, and enough of them: at least five finishing before anything is reported. A pilot of self-selected colleagues with nothing at stake cannot show how people fail under real queue pressure.

### ASI10: Rogue Agents

Status: Designed elsewhere.

Needs long-horizon runs and real deployments to see slow drift. Short simulations underrepresent it.
