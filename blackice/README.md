# Black ICE: defensive counter-intrusion

Status: Designed. Nothing in this folder runs yet. The first piece it will reuse already exists: the loose-key toolkit in [`../common/adt/loosekeys.py`](../common/adt/loosekeys.py) ([`../docs/LOOSE-KEYS.md`](../docs/LOOSE-KEYS.md)).

The name comes from fiction: ICE (intrusion countermeasures electronics) that pushes back against whoever breaks in. Here it means one thing. Defenses that **push back inside your own walls**: detect, contain, deceive, record and report. It never reaches out to the attacker's systems.

This is a separate track from the OWASP Top 10 for Agentic Applications. The ten items stay clean in [`../crosswalk/coverage.csv`](../crosswalk/coverage.csv). Black ICE is a layer that several of them lean on, and [`crosswalk.csv`](crosswalk.csv) shows which.

## Why it belongs in this project

The range measures defenses by the attacks they stop and the legitimate work they still allow. Active defenses are where that pairing matters most. A tarpit, a quarantine or a decoy can hurt real users as easily as a bot, and an automated defender is a new agent with its own credentials that an attacker can try to hijack, impersonate or feed false evidence. A crew of defensive agents that nobody tested the way the range tests everything else would be a liability.

## The red line

What is on the table, all on systems you own and operate:

1. **Observe only what reaches you.** Record addresses, timing, tools, and which bait token was presented. Bait that phones home from the attacker's machine runs code on their system. That is the same line as hacking back, so it stays out.
2. **Contain honeypots.** No outbound traffic from a decoy. Otherwise you built a pivot point that can hurt a third party.
3. **Intel is data, not orders.** Attackers can feed junk or spoof sources. Nothing blocks, quarantines or reports on the strength of one unverified signal.
4. **Keep decoys away from real use.** Bait and fake data live where only scavengers go, and the false-alarm rate is measured.
5. **Handle personal data carefully.** An address can be personal data under some laws. Keep what is needed, for a stated purpose and a limited time.
6. **Never name or shame publicly.** Attribution is weak, and the address may belong to a victim.

What is off the table, and why, is in [`MYTHS-VS-REALITY.md`](MYTHS-VS-REALITY.md). This page is orientation, not legal advice. Have counsel read the retention and reporting parts before anything ships.

## The ladder

| Rung | What it does | Example | Main risk |
| --- | --- | --- | --- |
| 1. Detect | Find what is exposed and notice use | Loose-token scan, grant audit, canary alarm (built) | Noise, missed formats |
| 2. Contain | Shrink what a thief can do the moment there is a signal | Quarantine a token, bind it to its network, trip a circuit breaker | A spoofed signal makes you quarantine your own users |
| 3. Deceive | Waste an intruder's time and learn their method | Honeypot gateway with fake data, tarpit, per-location bait | Real users reach the decoy |
| 4. Record and report | Preserve evidence and tell the people who can act | Hash-chained log, report to the token's issuer, host and CERT, human sign-off | Leaked personal data, wrong target |
| Out of scope | Retaliate against the attacker's systems | None | Illegal in most places, wrong target, forgeable, escalates |

## The crew

A small team of defensive agents, each with a narrow job and a Theater trust tier ([`../theater/README.md`](../theater/README.md)). A new agent starts on probation, and a harmful outcome costs more trust than a good one earns.

| Agent | Rung | Does | Ceiling |
| --- | --- | --- | --- |
| Scout | Detect | Scans for loose tokens, audits grants, watches canaries and logs | Read only |
| Warden | Contain | Quarantines, binds, trips the circuit breaker | May suspend, may not delete or revoke without sign-off |
| Illusionist | Deceive | Runs the honeypot gateway, tarpit and fake data | Lives in a sealed enclave with no outbound path |
| Scribe | Record and report | Writes the evidence log and drafts reports | Drafts only; a person sends |
| Marshal | Supervise | Cross-checks the others and escalates to a person | Human oversight at three speeds sets what it may decide |

Each is a rule-based component first. A model-based version is added only where a model might do something a rule cannot, and then tested against the rule, since the range has already found that a model reviewer is not automatically a check (see the ASI08 and reviewer-calibration results in the main README).

## The crew is a target

Every threat the range tests applies to the defenders, so they are tested the same way:

- **Hijacked defender (ASI01).** Planted text in a log line or a decoy response tries to change what the Warden is doing.
- **Impersonated defender (ASI03).** A forged message claims to come from the Marshal and orders a quarantine.
- **Poisoned evidence (ASI06, ASI08).** Spoofed alarms and false intel feed a decision, and a bad figure cascades into a real containment.
- **Weaponized containment.** The cheapest attack on an automatic defense is to trigger it against the owner. A bot that gets the Warden to quarantine the payroll service has won.

## How it is measured

Same method as every item: a prediction committed first, harm read from what happened, valid work run in every condition, and the misses reported. Scripted and synthetic comparisons, like the loose-key demo, are labeled and never count as results. What is new:

| Measure | Why |
| --- | --- |
| Bot successes against legitimate work interrupted | The pairing every item uses |
| False containment rate | How often the defense hits the owner |
| Time to contain | From first signal to the token being unusable |
| Decoy contact by real users | How clean the separation is |
| Intel quality | How often a report would have named the wrong target |
| Evidence integrity | Whether the log still verifies (`python adt.py verify`) |

The first planned test is in [`FIRST-RUNG.md`](FIRST-RUNG.md).

## Planned files

| File | Purpose |
| --- | --- |
| [`MYTHS-VS-REALITY.md`](MYTHS-VS-REALITY.md) | What popular culture and some vendors imply versus what the law and the evidence say |
| [`FIRST-RUNG.md`](FIRST-RUNG.md) | The first measured test: containment under spoofed alarms |
| [`crosswalk.csv`](crosswalk.csv) | Which OWASP items each rung supports |
| `CREW.md` | Roles, tiers and the escalation path in full |
| `ENCLAVE.md` | How a decoy is sealed: egress, data, logging |
| `REPORTING.md` | Who gets a report, what it contains, the human sign-off |
| [`rungs/bi01-contain/scripted.py`](rungs/bi01-contain/scripted.py) | The first rung's scripted run: containment under spoofed alarms (synthetic, never a result) |
| `rungs/` code | Live scenarios, added when the harness has one |

## Limits

- Designed, not built or measured. Every statement about effect is a hypothesis until a preregistered run supports it.
- The legal summary is general and not specific to your country.
- A defense that works against the author's bot may not work against an adaptive one. Each rung needs an informed attacker before any claim about it holds.
- The crew would run on local models of 8B parameters or smaller at first. Nothing here says how larger models behave.
