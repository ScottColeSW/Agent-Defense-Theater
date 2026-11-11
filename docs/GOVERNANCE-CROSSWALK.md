# Governance crosswalk

What this project measures, set beside the places three governance frameworks ask for the same thing: the [NIST AI Risk Management Framework](https://airc.nist.gov/AI_RMF_Knowledge_Base/Playbook), the [EU AI Act](https://artificialintelligenceact.eu/) (Regulation (EU) 2024/1689), and [ISO/IEC 42001:2023](https://www.iso.org/standard/81230.html).

## How to read it

- **This is the author's mapping.** A row says "this measurement is evidence that bears on that requirement". It does not say a system is compliant. Compliance is a judgment about a whole organization and a whole system, and nothing here is that.
- **The experiments are not products.** They are tests of defenses on simulated desks and small local models. The EU AI Act's obligations fall on providers and deployers of real high-risk systems, so those columns show where a measurement would be useful to such a team, not that the Act applies to these tests.
- **Reference depth differs on purpose.** NIST subcategory IDs and wording were checked against the [AIRC Playbook](https://airc.nist.gov/AI_RMF_Knowledge_Base/Playbook) pages (the Playbook says it will be revised, so recheck before relying on it). EU article numbers were checked against [artificialintelligenceact.eu](https://artificialintelligenceact.eu/); the Commission's [AI Act Explorer](https://ai-act-service-desk.ec.europa.eu/en/ai-act-explorer) and EUR-Lex hold the authoritative text, and application dates may change. ISO/IEC 42001 is paywalled and the free summaries disagree on sub-control numbers, so only the Annex A objective is given (A.5 impact assessment, A.6 AI system life cycle, A.7 data, A.8 information for interested parties, A.9 use, A.10 third parties). Check the sub-controls against the standard before using any row in an audit.

## The crosswalk

| What the project does or measures | Evidence in this repository | NIST AI RMF | EU AI Act | ISO/IEC 42001 |
| --- | --- | --- | --- | --- |
| **Security of the agent against manipulation** by text it reads (planted instructions, forged documents) | ASI03 and ASI02 attack tiers; Aegis Vector (linked) | MEASURE 2.7: security and resilience are evaluated and documented | Art. 15: accuracy, robustness and cybersecurity, including resistance to attempts by third parties to alter use or outputs | A.6 life cycle |
| **Limits on what an agent may do**: scoped and one-shot credentials, request binding, schema gates, dry runs | ASI03 rounds 1 to 3 (0 of 120 attacks under request binding plus holds); ASI02 first run | MANAGE 1.3: responses to high-priority risks are developed, planned and documented | Art. 9: a risk management system, including measures to reduce identified risks | A.6, A.9 use |
| **Human approval of consequential actions**, and how well a reviewer follows what it is shown | ASI03 escalation round; reviewer-calibration test (preregistered live run with an addendum) | GOVERN 3.2: roles for human-AI configurations and oversight are defined; MANAGE 2.4: responsibilities to supersede or disengage a system | Art. 14: human oversight, so a system can be effectively overseen by people while in use | A.9 use |
| **Tamper-evident record of every decision** | Hash-chained decision log, `python adt.py verify` | MEASURE 2.8: transparency and accountability risks are examined and documented | Art. 12: automatic recording of events over the system's life, for traceability | A.6 life cycle |
| **Predictions written down before the run**, pass bars, misses and aborted runs reported | Preregistration files; harness refusal of uncommitted predictions | MEASURE 1.1: approaches and metrics are selected; MEASURE 2.1: test sets, metrics and tools are documented; MEASURE 2.3: performance is demonstrated for stated conditions | Art. 9: testing as part of the risk management system | A.6 life cycle |
| **Valid use measured next to protection** (what a defense costs in work not done) | Every run reports attacks that got through beside valid tasks completed | MANAGE 1.1: whether the system achieves its intended purpose; MANAGE 2.2: mechanisms to sustain the value of deployed systems | Art. 15: appropriate accuracy for the intended purpose | A.9 use |
| **Cost of each defense** in model time, review time, our own code and tokens | Latency split in every report | MANAGE 1.2: treatment of risks is prioritized by impact, likelihood or available resources | Art. 9: risk management measures | A.6 life cycle |
| **Memory and context integrity** (forged or poisoned records) | ASI06, in the Palimpsest and Aegis Vector repositories (linked, not re-run here) | MEASURE 2.7; MAP 4.1: legal and technical risks of components, including third-party data | Art. 10: data and data governance; Art. 15: resilience to data poisoning | A.7 data for AI systems |
| **Third-party tools and servers** treated as part of the attack surface | ASI02 targets (the calculators, which accept unbounded inputs, and the deal desk) | GOVERN 6.1: policies for risks from third-party entities; MAP 4.1 | Art. 15: cybersecurity | A.10 third parties |
| **Testing as a standing practice, with failures reported** | Aborted-run notes, addenda that name misses | GOVERN 4.3: practices that enable AI testing, incident identification and information sharing | Art. 9: ongoing risk management, with testing | A.6 life cycle |

## AIUC-1 and the OWASP Agentic Top 10

The OWASP Agentic Security Initiative published a crosswalk between the Agentic Top 10 and AIUC-1, a security, safety and reliability standard for AI agents (version 1.0, May 2026, CC BY-SA 4.0). Its "observed gaps" section lists control surfaces that it says AIUC-1 does not yet require. Several of them are things this project has measured, so they are set beside the evidence here. As above, this is the author's reading: a measurement bears on a control, it does not show a standard is met.

| Control surface the crosswalk names | Item | Evidence in this repository | Caveat |
| --- | --- | --- | --- |
| Inter-agent message integrity and replay protection | ASI07 | An HMAC check stopped fabricated signatures, and binding the message to its deal stopped replays that a signature-only check passed | Shared-secret HMAC in one process, not separate hosts or a key service |
| Kill switches and runtime containment | ASI10 | A kill switch halved restricted calls (18 against 36) without the cost of blanket probation | Four check-ins, one scenario, and the first drift still got through |
| Circuit breakers and independent policy enforcement between planning and execution | ASI08 | An independent recomputation stopped every bad figure, where a reviewer in the crew did not | Fault injected at the first stage, reviewer and decider the same model |
| Runtime monitoring and containment of code execution | ASI05 | An audit hook stopped all 15 of 54 attempts that got through with no defense, and a wall-clock cap alone stopped none | Container on a workstation, author-written attacks, and the runaway-loop case barely tested the cap |
| Authorization of agent tool calls and tool identity | ASI02, ASI03 | Schema gates, scoped credentials and request binding, with the valid work lost reported | Simulated desks, small local models |
| Signed manifests and content-hash pinning for tools | ASI04 | A manifest pin stopped every poisoned description and look-alike, and a code pin stopped everything but refused every legitimate update | A tampered proxy in front of one reviewed server, not real packages |

Source: OWASP Top 10 for Agentic Applications, AIUC-1 Crosswalk, version 1.0, May 2026, OWASP GenAI Security Project, CC BY-SA 4.0. Gap descriptions are paraphrased.

## Field context: State of Agentic AI Security and Governance v2.01

The OWASP Agentic Security Initiative's State of Agentic AI Security and Governance report (version 2.01, June 2026, CC BY-SA 4.0) surveys incidents, regulation and maturity a year after the Agentic Top 10. It is field context, not a test, so it is set beside this project's results to show where they agree, where they differ, and where the field has evidence this range lacks. Statements from the report are paraphrased.

| What the report says | What this repository found | How they sit together |
| --- | --- | --- |
| Plan-divergence detection, comparing an agent's actions with its declared intent, is an emerging core control | ASI01: a locked plan stopped every hijack that needed a new tool (0 of 36), and a goal check by a separate reviewer stopped all 45 | Agrees. One simulated desk, author-written attacks, so it shows the mechanism and not field effectiveness |
| Hooks that intercept actions work more reliably as an early warning layer than as a hard boundary | ASI05: an audit hook stopped all 15 attempts that got through with no defense. ASI10: a flag-only detector changed nothing about the first drift | Mixed. The hook held here, but against author-written attacks in a container on a workstation. The flag-only result matches the report's point that detection warns and does not stop |
| Approval prompts at volume bring decision fatigue, and reviewers blanket-approve | ASI09 pilot: approvals fell across the exercise (48%, 43%, 40%), the opposite of fatigue | Does not contradict it. The pilot had no queue, no volume and nothing at stake, so it could not test fatigue. This is the main thing a real-conditions study would add |
| Human oversight cannot cover a high-throughput agent (the report's example is 50 reviews against 10,000 actions an hour) | ASI03: request binding with approval holds let 0 of 120 attacks through and kept 61 of 63 valid tasks | Consistent with the report's direction toward risk-tiered review. Binding narrows what reaches a person, but nothing here tests throughput |
| Inter-agent communication risk is more common in research than in production, and confirmed ASI09 incidents are limited | ASI07 and ASI09 each have one first run | These are the two items where the field has least confirmed incident evidence, so this project's results are also the least validated against real cases |
| Lower adoption tiers should focus on ASI01, ASI05 and ASI06, and higher tiers on the full list with ASI04, ASI07 and ASI08 | All ten items have a preregistered first run | Coverage matches the report's priorities. Depth does not: see [`OPEN-WORK.md`](OPEN-WORK.md) |

Where the report names a surface this range does not touch: coding agents running inside CI pipelines as a distinct, attacker-facing surface, shadow AI discovered through delegated OAuth access, and delegation chains through spawned sub-agents. They are listed as stubs in [`OPEN-WORK.md`](OPEN-WORK.md).

Source: OWASP GenAI Security Project, Agentic Security Initiative, State of Agentic AI Security and Governance, version 2.01, June 2026, CC BY-SA 4.0.

## Builder guidance: Securing Agentic Applications V2

The OWASP GenAI Security Project's builder and defender guide (Securing Agentic Applications V2, version 2.0, October 2026, CC BY-SA 4.0) gives lifecycle controls, and a chapter on assuring that the controls hold. Its testing advice matches how this project works in several places. Statements are paraphrased, and as above this is the author's reading, not a compliance claim.

| What the guide says | What this repository found or does | How they sit together |
| --- | --- | --- |
| Behavioral testing must count over-restriction and miscalibrated controls, since an agent that refuses legitimate work has failed as surely as one that oversteps | Every run reports valid work kept beside attacks stopped. One control stopped every tampered tool and refused all 18 legitimate updates, and one reviewer denied nearly every legitimate refund | Agrees, and this is the project's central method. Cases are the author's, tidier than real requests |
| The deployed application is the joint product of the model and its harness, and a change to any behavior-defining element invalidates earlier test results | The agent's output format moved attack-following by up to 80 points per model, and a reviewer's result did not transfer between models | Agrees. Revalidation here is manual, and a change that shifts results is not blocked automatically (stub in [`OPEN-WORK.md`](OPEN-WORK.md)) |
| Detection with no automated response is expensive logging, and kill switches should work in graduated tiers (warn, limit, suspend, kill) | ASI10: a flag-only detector changed no outcome, and a one-step kill switch halved restricted calls but the first drift still ran | Agrees on detection. Only a single-step kill switch was tested, so graduated tiers are a stub |
| An integrity hash detects modification of a record, but an intact record can still be malicious | The decision-log hash chain shows tampering after the fact and does not prevent it. In the ASI06 write-path run, two of the three forgeries were structurally invisible to the fixed rules | Agrees. The same limit is stated in [`common/decision-log/VERIFY.md`](../common/decision-log/VERIFY.md) |
| Keyword or pattern filtering is a detection signal, and schema enforcement and isolation should come first | ASI02: a schema gate left 18 of 120 attacks running, 9 of them adaptive, while request binding with the schema gate let 0 of 120 through. ASI05's adaptive attacks were written to dodge a filter that checks the text of a call | Agrees. Small local models, author-written attacks |
| Human approval should be risk-based, logged and rate limited | ASI03 holds and the ASI09 pilot log each human decision. No rate limit was tested | Partial. See the approval-load stub |
| An agent should not combine private data, untrusted input and external communication (the guide's "Rule of Two") | No item tests a capability composition as a design gate | Gap. Listed as a stub |

Source: OWASP GenAI Security Project, Securing Agentic Applications V2, version 2.0, October 2026, CC BY-SA 4.0.

## Benchmark reliability: LLM Exploit Generation Phase 2

The OWASP GenAI Security Project's Cyber Threat Intelligence team compared agent-driven and human-guided offensive testing against live targets (LLM Exploit Generation, Phase 2, version 1.0, October 2026, CC BY-SA 4.0). Its section on benchmark reliability is about how to read capability numbers, and it applies to this project's own results. Only that methodology is used here.

| What the report says | What this repository does or found | How they sit together |
| --- | --- | --- |
| The harness around a model can move results more than the choice of model (one study it cites found harness variance about 7.8 times model variance), so scores need the harness, trial count and budget disclosed | Preregistrations state models, sample sizes, generation settings and hardware, and results carry the provider and model id. Hosted models are not version pinned, and the docs say so | Mostly agrees. Pinning hosted models is not possible, which limits repeats |
| Treat guardrails as a variable and not a control | Marking text as untrusted raised ASI01 hijacks from 22 of 45 to 33 of 45, and plain background text about the desk raised soft hijacks as much as the security rule did | Agrees, and the project found it independently on small models. Why is still open |
| Weaker attackers give false comfort: the report found local models lacked the capability that hosted ones had | In the Black ICE series a local 8B attacker won 1 of 108 incidents against a design where a hosted attacker's instructions worked in 27 of 45. The docs say a defense that survives a weak attacker is not shown to hold | Agrees |
| Weight end-to-end and defended-environment results above discrete-skill results, and note that benchmarks omit active defenders | Every item is one simulated step or a short run with no active defender | Gap, stated in [`LIMITS-AND-ANSWERS.md`](LIMITS-AND-ANSWERS.md) |
| Ask for the rate of unintended routes to a passing score, because scores are inflated by unintended solutions | Outcomes are scored as attack succeeded, blocked or valid work done. A success or a block is not checked for an unintended route | Gap. Listed as a stub |

Source: OWASP GenAI Security Project, Cyber Threat Intelligence Layer, LLM Exploit Generation Phase 2, version 1.0, October 2026, CC BY-SA 4.0.

## What the project does not show

These are the places where a reader looking for assurance would find nothing yet.

| Gap | Requirement it touches | Why it matters |
| --- | --- | --- |
| No independent assessor. All attacks, gates and harm definitions are written by the author. | NIST MEASURE 1.3: internal experts or independent assessors who did not build the system are involved | A defense tested only by its builder is tested against what the builder thought of |
| Only a five-person pilot of human reviewers (read aloud in a group). Elsewhere the "reviewer" is a model or a rule. | EU Art. 14: oversight that works for the people doing it | A model reviewer's accuracy is not a person's, and fatigue, queues and pressure are not modeled |
| No monitoring after deployment, no incident response procedure. | NIST MANAGE 2.3 and 4.1 | These experiments end when the run ends |
| No impact assessment for affected people. | ISO/IEC 42001 A.5 | The desks are fictional, so there are no affected people to assess |
| Small local models up to 8B parameters, one workstation. | NIST MEASURE 2.5: valid and reliable for the conditions of use | Results say nothing about larger models or other conditions |
| Scripted runs and exploratory runs are shown but never counted. | NIST MEASURE 2.1 | This is a strength, noted so it is not mistaken for coverage |

## Where this goes in the product

The report page will carry a Governance view for each test: the rows above that the test supplies evidence for, with the result and the limits beside it, so a reader can go from a framework requirement to the run that bears on it. The same table is in [`crosswalk/governance.csv`](../crosswalk/governance.csv).
