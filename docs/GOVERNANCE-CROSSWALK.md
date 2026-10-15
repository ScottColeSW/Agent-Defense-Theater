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

## What the project does not show

These are the places where a reader looking for assurance would find nothing yet.

| Gap | Requirement it touches | Why it matters |
| --- | --- | --- |
| No independent assessor. All attacks, gates and harm definitions are written by the author. | NIST MEASURE 1.3: internal experts or independent assessors who did not build the system are involved | A defense tested only by its builder is tested against what the builder thought of |
| No study of real human reviewers. The "reviewer" is a model or a rule. | EU Art. 14: oversight that works for the people doing it | A model reviewer's accuracy is not a person's, and fatigue, queues and pressure are not modeled |
| No monitoring after deployment, no incident response procedure. | NIST MANAGE 2.3 and 4.1 | These experiments end when the run ends |
| No impact assessment for affected people. | ISO/IEC 42001 A.5 | The desks are fictional, so there are no affected people to assess |
| Small local models up to 8B parameters, one workstation. | NIST MEASURE 2.5: valid and reliable for the conditions of use | Results say nothing about larger models or other conditions |
| Scripted runs and exploratory runs are shown but never counted. | NIST MEASURE 2.1 | This is a strength, noted so it is not mistaken for coverage |

## Where this goes in the product

The report page will carry a Governance view for each test: the rows above that the test supplies evidence for, with the result and the limits beside it, so a reader can go from a framework requirement to the run that bears on it. The same table is in [`crosswalk/governance.csv`](../crosswalk/governance.csv).
