# Limits and what it would take

Every item, including the measured ones, has limits. This page collects them with the specific resource that would close each one. It is the answer to "why isn't this finished" and is part of the demo.

## Limits that apply to everything

| Limit | What it would take |
| --- | --- |
| Local models are capped by one workstation (up to roughly 8B parameters) | Access to larger or frontier models, or a GPU server, so results can be compared across sizes |
| Attacks are written by the author | An independent red team, or a public challenge, with attackers who know the defenses |
| Small samples, one scenario per item | More runs per cell, more scenarios, and published raw results |
| Simulated crews in one process | Agents on separate hosts with real network paths and key management |
| No real users. Only a five-person pilot of the oversight and trust item, read aloud in a group | A larger human-subject study, read independently with a clearer card |
| No production telemetry | Integration with a real logging and detection stack |

## By item

### ASI01: Agent Goal Hijack

Status: Measured (first preregistered live run), with sibling evidence in Aegis Vector.

One agent on one simulated desk, author-written attacks, and three small models. The goal check is one small model on one prompt, and the plan lock assumes a trusted, complete request. Needs: a tool-using agent crew, an adaptive red team that is not the author, goal checks across several models, and models above the 8B size this hardware allows. Spotlighting made hijacks more likely here, replicated on new deals, and a follow-up showed it was the presence of a security rule and not its wording. Why is still open: a second follow-up ruled out rule-following (an unrelated rule did not raise it) and showed plain background text about the desk raised hijacks as much as the security rule. A third follow-up crossed topic and length: 47 words of facts about an office building raised soft hijacks as much as the desk text (70% against 40%), while 46 words of style rules and 23 words about the desk did not, so neither topic nor length alone explains it and the answer is mixed. Replies at temperature 0 repeated 72 of 75 outcomes, not all.

### ASI02: Tool Misuse and Exploitation

Status: Measured (first preregistered live run).

Two small MCP servers (the author's RealEstateTools calculators and a purpose-built SQLite Deal Desk) show the pattern, not the coverage. Needs a larger real tool catalog with realistic argument variety, an enterprise policy engine, a multi-step agent, and an attacker who is not the author.

### ASI03: Identity and Privilege Abuse

Status: Measured (first preregistered run, simulated desk).

One simulated agent step, author-written attacks and an author-written credential gate, three models up to 8B. Zero escapes from a deterministic gate is close to true by construction. Untested: credential lifetimes, mid-task revocation, the delegation-chain check, credentials in shared context, an escalation path for legitimate above-tier work (0 of 9 such tasks completed under scoped credentials). Needs: a real identity provider (for example Entra ID or Okta) and workload identity, a multi-step agent, and an attacker who is not the author. A local simulation shows the logic, not production behavior.

The escalation experiment adds its own limits. The approver is one small local model, not a person, so it shows what a request card lets a careful reader catch and where a model reviewer is swayed or contradicts itself, not how people behave, tire or rubber-stamp. There is no queue, no timeout and no approval fatigue. The card's checks are author-written over the operator's own words. The agent's output format moved attack-following by up to 80 points per model, so a defense measured on one prompt may not hold on another. Needs: human reviewers (a study with real approvers), stronger reviewer models, and agents that are not tuned to one prompt.

The third round adds: every operator request in it states its amount and destination plainly and is compared by simple text matching, so request binding and the bottom-line card look better than they would against vague requests. The rule, the card and the binding share one comparison, so the round tests whether models follow it and what the design costs, not whether the comparison is right. One reviewer model followed the card and another did not, which means a reviewer's result does not transfer between models. No attack was written against the binding or the bottom line. Needs: vague and partial requests, adaptive attacks on the binding, reviewer calibration sets, and reviewers other than two 7 to 8B local models.

The KTP capacity gate run closes the duplicate-refund hole on the six texts that found it (0 of 54 against 32 of 54) and leaves valid work unchanged. Its own limits: the texts were not written against the gate, the gate's contributor maintains the rule it implements, the declared capacity is a fixed number the agent never sees, and a simpler rule such as an idempotency key or one refund per ticket was not compared. The gate's result for its lease bound is close to true by construction. A defense review after the run found gaps this item has not closed: a refund amount of `NaN` or `-Infinity` defeats the scoped credential's budget and the independent scorer together when request binding is off, request binding reads "do not refund $200" as a request for it, the reviewer card can be told a destination is inside the company domain when it is not, and the verdict reader accepts any reply that starts with "approve". Each was shown by calling the code, not by a live model, and each has an open issue.

### ASI04: Agentic Supply Chain Vulnerabilities

Status: Measured (first preregistered live run).

The tampered tools are a proxy in front of one reviewed server, not real compromised packages, and there is no time-delayed tampering. Needs an organizational registry, software bill of materials tooling, real package ecosystems, and a way to hash a remote server, which the code pin cannot do. A toy registry cannot show scale or incentive effects.

### ASI05: Unexpected Code Execution

Status: Measured (first preregistered live run, 2026-11-08).

A data agent's generated code runs in a disposable Docker container, with three models up to 8B and author-written attacks. The audit hook stopped every attempt on the first run and the wall-clock cap alone stopped none. The container is relied on for one narrow thing and is not a micro-VM. Needs production isolation (a micro-VM or user-space kernel), a security review of the sandbox itself, and an attacker who is not the author. A container on a workstation is a demonstration, not a boundary to trust.

The second run (os-boundary, 2026-11-13) corrects a claim the first run's wording overstated: the audit hook and the alarm cap live in the agent's own interpreter, so its code switches them off. An `os.execv` read, which the hook never gated, leaked 4 of 9 under the strongest in-process condition, and cancelling the alarm ran code 6 of 9 cases well past the cap. An OS boundary (the secret root-only in a tmpfs the code cannot reach, the code run as an unprivileged user, the cap a supervisor process the code cannot signal) stopped every exfiltration (0 of 27) and killed every long run from outside, at no cost relative to no defense. Its own limits: the same review wrote the attacks and the boundary, so the attacker is not independent; it is a container on a workstation, not a micro-VM, and a kernel or runtime escape is out of scope; two of three models wrote the legitimate output poorly, so the utility reading (4 of 9) is low and bounds the comparison; and the run exposed an imprecise pass-bar criterion (a runtime threshold set below the cap flagged two sub-cap finishes), fixed for future runs.

### ASI06: Memory and Context Poisoning

Status: Measured elsewhere (retrieval) and measured here (write path, first preregistered live run).

Registered facts only; an unregistered fact is admitted. The write-path run closes part of what was untested. Still untested: slow drift, many agreeing forgeries, a poisoned verified corpus. Needs: larger models, an adaptive attacker who knows the gate, and a production-size corpus.

### ASI07: Insecure Inter-Agent Communication

Status: Measured (two preregistered live runs, 2026-11-08 and 2026-11-12).

A real shared-secret HMAC between agents in a single process, on the real deal desk. Needs agents on separate hosts or runtimes and a real key management service. A single-process crew cannot show network-level attacks.

The first run's deal check stops only a replay that leaves the message untouched. The deal id it compares is outside the signature, so a replay with that field rewritten, or a genuine message delivered twice, passed it 18 of 18 times in the second run. A signature over the deal with a nonce memory refused all 27 replays. That check and those replays have one author, so the result shows the specific gap closed, not that the new check holds against an attacker who is trying. Untested: a stolen shared key, a decider that restarts and loses its memory, several deciders, and a message delayed and delivered once.

### ASI08: Cascading Failures

Status: Measured (first preregistered live run).

The fault is injected at the first of three stages, and the reviewer and decider are the same model. This shows whether a bad figure crosses two hops, not the amplification factor. Needs production-scale topologies with many agents and real dependencies, and a crew whose failures are produced by agents and not injected.

### ASI09: Human-Agent Trust Exploitation

Status: AI reviewers measured (the ASI03 calibration run), and a first round of five people finished on 2026-11-08.

The five took the study together with the cards read aloud, a disclosed deviation from the protocol, so the timing data is uninformative and the result is a pilot. One pass-bar criterion was met, two missed and one was uninformative. Every error rate came in far above the prediction, which points at the cards being hard for people to read. Needs a replication with a clearer, shorter card, read independently, and more participants. A pilot of self-selected colleagues with nothing at stake cannot show how people fail under real queue pressure.

### ASI10: Rogue Agents

Status: Measured (first preregistered live run, 2026-11-08).

Four check-ins, one scenario, one kind of pressure (market commentary, never a forged identity or a compromised channel). Needs long-horizon runs and real deployments to see slow drift. Short simulations underrepresent it.
