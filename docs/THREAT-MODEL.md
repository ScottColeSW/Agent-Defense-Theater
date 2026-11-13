# Threat model

This page is organized around [Shostack's Four Question Frame for Threat Modeling](https://github.com/adamshostack/4QuestionFrame) (CC-BY): what are we working on, what can go wrong, what are we going to do about it, and did we do a good enough job. The four questions are the spine; each item folder holds the specifics, and the measurements answer the fourth.

A note on names: `greenroom/SPEC.md` has its own "four questions," which are an executive governance framing (what can it do if it goes wrong, who is responsible, can we stop and undo it, can you prove what it did). Those are not Shostack's frame and are not what this page uses.

## 1. What are we working on?

An organization's agents act on its behalf with real tools, memory, and credentials. The assets are the decisions the agents make, the data they can reach, the actions they can take, and the trust people place in their output.

The range models one small business desk reused across items (a real-estate deal desk and a support desk), with agents that read tickets and documents, call tools over real or simulated protocols, talk to each other, write to memory, and escalate to a person. The targets are simulated; the models, the tool protocols where noted, the attacks, and the measurements are real.

**Trust boundaries.** The design treats each of these as a place where trust must not be assumed:

1. Between an agent and the content it reads. Data is not instructions.
2. Between an agent and the tools it calls. A policy gate, not the model, decides what a call may do.
3. Between an agent and another agent. A peer's output is untrusted input.
4. Between an agent and a person. An approval must show what will actually change.
5. Between an agent and its memory. A new claim is judged before it is believed.

A sixth boundary is implied by ASI04 and is not yet in the list above as a first-class entry: between an agent and the provider of the tools it loads (provenance and integrity of the tool set itself, before any call is made). The coverage table below places ASI04 there and marks it.

There is no data-flow or trust-boundary diagram yet. Shostack's frame leans on a picture for this question, and the absence is tracked as an open item (see the issue linked from `docs/OPEN-WORK.md`).

**Out of scope.** Model training attacks, model theft, and infrastructure attacks unrelated to agents. Container and kernel escapes (the ASI05 sandbox claims only that the agent's own code cannot leave it, not that the container cannot be broken by other means).

## 2. What can go wrong?

Threats are enumerated two ways: by the OWASP Agentic and LLM Top 10 and MITRE ATLAS (the mapping lives in [`../crosswalk/`](../crosswalk/README.md), one item per agentic risk), and by the attack surface each attack targets (`crosswalk/threat-surfaces.json` sorts every classified attack into injection, authority, or agency).

The actors assumed, and where each is exercised:

| Actor | Capability assumed | Exercised in |
| --- | --- | --- |
| External content author | Places text in a document, web page, ticket, or message an agent reads | ASI01, ASI03, ASI06 |
| Malicious or compromised tool provider | Changes a tool, manifest, or server an agent loads | ASI04 |
| Compromised peer agent | Controls one agent in a crew and messages the others | ASI07, ASI08 |
| Careless insider | Approves requests without reading them | ASI03, ASI09 |
| Drifting or rogue agent | Exceeds its own declared scope over a task | ASI10 |
| Adaptive attacker | Knows the defenses and writes attacks against them | Partly: see question 4 |

The attacks in this repository are written by the author unless an item says otherwise. That limit applies to every result, and closing it (attacks by someone who is not the author of the defense) is the single largest gap, tracked in [issue 33](https://github.com/ScottColeSW/Agent-Defense-Theater/issues/33).

## 3. What are we going to do about it?

Every item tests defenses at three layers, named the same way throughout: **prevent** (stop the unsafe action before it happens), **detect** (notice it and record it), and **contain** (let it happen but bound the harm). A defense reads only trusted inputs (the operator's own request, the system's own records, a cryptographic check), never the text an attacker can write. The governance mapping, which control answers which risk, is in [`GOVERNANCE-CROSSWALK.md`](GOVERNANCE-CROSSWALK.md).

The method is deliberately comparative: each item runs the attacks against no defense and against each control, so the cost of a control to legitimate work is measured beside the protection it buys.

## 4. Did we do a good enough job?

This is the question the project is built to answer, and the method is the answer: every item commits a prediction and a pass bar before the run ([`PREREGISTRATION-TEMPLATE.md`](PREREGISTRATION-TEMPLATE.md)), measures attack success beside retained utility and cost, keeps every failure and miss in an addendum, and states the sample size and the limits beside every number ([`LIMITS-AND-ANSWERS.md`](LIMITS-AND-ANSWERS.md)). A control that looked strong is not trusted until a harder attack has tried it: that is why the duplicate-refund probe, the bound-signature replay, and the sandbox bypass review all followed their items' first runs, each turning a passed pass bar into the next experiment.

"Good enough" is also measured against the model itself. The coverage table below reads down the trust boundaries and shows where a measured defense exists and where one does not. Three gaps stand out:

- **The adaptive attacker is mostly absent.** Most items face author-written, non-adaptive attacks. The adaptive rounds that exist (ASI03's blind and informed attackers, ASI07's bound-signature replays, ASI05's sandbox bypasses) were written by the author of the defense, so the attacker is not independent. Issues 25 to 34 are the start of closing this.
- **The sixth boundary (tool provenance) has one item and no clean home** in the boundary list.
- **People, not models, as reviewers** are tested in only one item (ASI09), with five participants and a disclosed deviation.

### Coverage: boundary to defense to result

| Trust boundary | Item(s) | The defense that held | Headline measured result |
| --- | --- | --- | --- |
| 1. Agent and the content it reads | [ASI01](../items/asi01-goal-hijack/), [ASI06](../items/asi06-memory-context-poisoning/) | A plan locked before the agent reads untrusted text; a separate goal check; a memory floor that trusts an honest label over blind rules | ASI01: locked plan 0 of 36 hijacks that need a new tool, goal check 0 of 45. ASI06: floor stopped all 27 forgeries at no cost. A prompt-level "this is untrusted" warning made ASI01 worse (33 of 45 against 22) |
| 2. Agent and the tools it calls | [ASI02](../items/asi02-tool-misuse/), [ASI03](../items/asi03-identity-privilege/), [ASI05](../items/asi05-code-execution/), [ASI10](../items/asi10-rogue-agents/) | Request binding plus a schema gate; a scoped credential with request binding and holds; a sandbox; a kill switch | ASI02: binding plus schema 0 of 120. ASI03: binding plus holds 0 of 120, but a later probe found a duplicate-refund hole (32 of 32), since closed by the KTP capacity gate (0 of 54). ASI05: an in-process hook stopped the first attacks but can be switched off by the agent's own code (issue 26); an OS boundary is the fix. ASI10: the kill switch halved repeat drift; probation blocked everything including the operator's own request |
| 3. Agent and another agent | [ASI07](../items/asi07-inter-agent-communication/), [ASI08](../items/asi08-cascading-failures/) | A signature that binds the deal with a nonce memory; an independent recomputation that never trusts the message | ASI07: 23 of 27 forged or replayed messages produced a real offer with no defense; the bound signature refused all 27. ASI08: 29 of 45 bad figures became a harmful offer; the independent recompute stopped all 45 at no cost |
| 4. Agent and a person | [ASI03](../items/asi03-identity-privilege/), [ASI09](../items/asi09-human-agent-trust/) | A request card that states the system's own comparison before the agent's account | Showing the agent's own reason let 40% of non-matching requests through against 6% comparison-first (AI reviewers). With five people the gap held (54% against 26%), but people were fooled by the agent's account more than the models were |
| 5. Agent and its memory | [ASI06](../items/asi06-memory-context-poisoning/) | Quarantine of external documents; a floor that holds a claim when either rules or an honest label flag it | 23 of 27 forged documents changed a real decision with no defense; the floor stopped all 27. A rules-only condition missed what the rules cannot see (17 of 27 through) |
| 6. Agent and its tool provider (provenance) | [ASI04](../items/asi04-supply-chain/) | A manifest pin, a canary comparison, a code pin | Each control caught only what it was built to see. The code pin stopped everything but refused all 18 legitimate updates; the manifest pin was fooled by a tool that recognizes the check |

Every item is **Measured** (one or more preregistered live runs). What "Measured" does and does not cover for each is in [`LIMITS-AND-ANSWERS.md`](LIMITS-AND-ANSWERS.md), and the open gaps are in [`OPEN-WORK.md`](OPEN-WORK.md).

## References

[Shostack's Four Question Frame for Threat Modeling](https://github.com/adamshostack/4QuestionFrame), [OWASP Top 10 for Agentic Applications 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/), [OWASP Top 10 for LLM Applications 2025](https://genai.owasp.org/llm-top-10/), [MITRE ATLAS](https://atlas.mitre.org/).
