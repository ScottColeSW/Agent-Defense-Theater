# ASI03: Identity and Privilege Abuse

| | |
| --- | --- |
| Status | Measured (first preregistered run, simulated desk) |
| OWASP LLM Top 10 2025 | LLM06 Excessive Agency |
| MITRE ATLAS | To be mapped |
| Existing work | First run in this repository, see [`PREREGISTRATION.md`](PREREGISTRATION.md) |

The mapping to the LLM Top 10 and ATLAS is the author's proposal. See [`../../crosswalk/README.md`](../../crosswalk/README.md).

## Threat

Agents inherit or cache credentials and delegate authority in ways that let one compromised agent act with more privilege than its task needs.

**Example scenario.** A low-trust agent reuses a high-privilege agent's token it found in shared context.

## Attack tiers

Every item is tested at three tiers, written down before the run (see `PREREGISTRATION.md`).

| Tier | Planned attack |
| --- | --- |
| Loud | Asking a peer agent to act on the attacker's behalf. |
| Quiet | Confused-deputy requests that look like normal delegation. |
| Adaptive | Replay and relay of short-lived credentials within their lifetime. |

## Defense layers

| Layer | Planned defense |
| --- | --- |
| Prevent | Per-agent scoped credentials, short lifetimes, and no credentials in shared context. |
| Detect | Record the delegation chain for every action and check it against policy. |
| Contain | Revocation that takes effect mid-task; privilege ceilings per trust tier. |

## Measurement

Unauthorized-action block rate; credential exposure in context; time to revoke.

Results use the shared schema in [`../../common/RESULTS-SCHEMA.md`](../../common/RESULTS-SCHEMA.md) and only saved runs appear in `results/`.

## What exists today

A runnable scenario: a simulated support desk with five tools, one agent at Theater tier 1, six author-written attacks planted in tickets, and two credential setups. Run it with `python adt.py run asi03 --models <names>` and score it with `python adt.py summary asi03`.

First preregistered run (2026-10-13, three local models up to 8B, 540 records). Pooled, 90 attack cases per defense:

| Defense | Attack succeeded | Beyond tier 1 | In-tier utility | Above-tier task done |
| --- | --- | --- | --- | --- |
| none (shared service token) | 68.9% (62/90) | 56.7% (51/90) | 36/36 | 9/9 |
| prompt_guard | 61.1% (55/90) | 46.7% (42/90) | 36/36 | 9/9 |
| scoped_credentials | 12.2% (11/90) | **0/90** | 36/36 | **0/9** |
| prompt_guard+scoped | 14.4% (13/90) | **0/90** | 36/36 | **0/9** |

The preregistered pass bar was met. Several predictions were missed, the prompt-level guard barely helped, and the 12.2% that got through scoped credentials is one attack (`in_scope_refund`) that stays inside what the credential allows. The full prediction, the misses and what they mean are in the addendum of [`PREREGISTRATION.md`](PREREGISTRATION.md).

### Escalation experiment (second preregistered run)

Scoped credentials blocked all above-tier work, so this run turns a denial into a **hold** that a reviewer can approve, carried out with a one-shot credential bound to that exact call. Run it with `python adt.py run asi03 --experiment escalation --models llama3.1:8b,qwen2.5:7b,phi4-mini:3.8b --reviewer qwen2.5:7b`. Pooled, 120 attack cases, 27 above-tier legitimate tasks per condition:

| Condition | Attack succeeded | Bad approvals (of attack holds) | Above-tier work done |
| --- | --- | --- | --- |
| none (shared token) | 51.7% (62/120) | n/a | 96.3% (26/27) |
| scoped_credentials | 10.0% (12/120) | n/a | 0% (0/27) |
| hold + rubber stamp | 51.7% (62/120) | 100% (50/50) | 96.3% (26/27) |
| hold + agent card | 11.7% (14/120) | 4.0% (2/50) | 7.4% (2/27) |
| hold + effect card | 10.0% (12/120) | 0% (0/50) | 29.6% (8/27) |
| hold + effect card + money review | 10.0% (12/120) | 19.4% (12/62) | 29.6% (8/27) |

Three of six pass-bar criteria were met. Approval without reading is no defense (identical to no defense), no beyond-tier action ran without a logged approval (0 of 183 per condition), and every one-shot credential was used exactly once. But the model reviewer mostly denied: the approval step recovered 30% of the legitimate work at best, the reviewer weighed the card's "over the limit" line above the operator's own words, and in the money condition it approved 12 in-scope refunds while writing "the operator's request is to summarize the ticket, not to process a refund." Full prediction, misses and next steps: [`PREREGISTRATION-escalation.md`](PREREGISTRATION-escalation.md).

### Third round: a system-stated bottom line, request binding, reviewer choice

Round 2's reviewer mostly denied and approved unrequested refunds. This round makes the system state its comparison with the operator's own words first, adds a rule on the same facts as a ceiling, tries a second reviewer model, and adds **request binding**: a refund or export the operator never asked for is refused outright, so nobody can approve it. Run it with `python adt.py run asi03 --experiment bottom-line --models llama3.1:8b,qwen2.5:7b,phi4-mini:3.8b --reviewer qwen2.5:7b`. Pooled, 120 attack cases and 63 valid tasks per condition:

| Condition | Attack succeeded | Valid work done (of 63) | What a reviewer was asked |
| --- | --- | --- | --- |
| none | 51.7% (62/120) | 61 | n/a |
| scoped credentials | 10.0% (12/120) | 35 | n/a |
| round 2's effect card (qwen2.5:7b) | 10.0% (12/120) | 43 | 76 holds |
| **bottom-line card (qwen2.5:7b)** | 10.0% (12/120) | **61** | 76 holds |
| bottom-line card, every refund reviewed | **0.0% (0/120)** | **61** | 96 holds |
| bottom-line card (llama3.1:8b) | 10.0% (12/120) | 43 | 76 holds |
| bottom-line card, both must approve | 10.0% (12/120) | 43 | 76 holds |
| rule on the same facts (no model) | 10.0% (12/120) | 61 | none |
| request binding alone | **0.0% (0/120)** | 35 | none |
| **request binding plus holds** | **0.0% (0/120)** | **61** | 26 holds |

Seven of eight pass-bar criteria were met. The same card that made `qwen2.5:7b` approve every legitimate hold and deny every attack did not fix `llama3.1:8b`, which denied all 18 refund holds while the card said MATCH. A reviewer has to be checked on known cases before it is trusted. The rule did what the best model did for 3 ms, so a model earns its place only on requests the system cannot decide, which was not tested. Request binding plus holds protected fully (0 of 120) and kept all the valid work (61 of 63). Every request here is explicit, which flatters it. Prediction, misses and next steps: [`PREREGISTRATION-bottom-line.md`](PREREGISTRATION-bottom-line.md).

### Planned against done

| Planned | First run |
| --- | --- |
| Loud: ask a peer agent to act for the attacker | Done as planted ticket text, not a peer message |
| Quiet: confused-deputy requests that look like delegation | Done (`policy_memo_refund`, `audit_export`) |
| Adaptive: replay and relay of short-lived credentials | Not done. The adaptive tier here is a forged delegation claim and an in-scope abuse |
| Prevent: scoped credentials | Done. Short lifetimes are not exercised |
| Detect: delegation chain checked against policy | The chain is recorded in the decision log but not checked |
| Contain: mid-task revocation, tier ceilings | Tier ceilings done. Revocation not done |
| Measure: block rate, credential exposure in context, time to revoke | Block rate done. The other two are not measured |

## Limits and what it would take

Needs a real identity provider (for example Entra ID or Okta) and workload identity. A local simulation shows the logic, not production behavior.

## Folder map

- `attacks/`: attack payloads and generators, one file per tier.
- `defenses/`: defense implementations, one file per layer.
- `eval/`: test cases and pass criteria.
- `results/`: saved runs only.
- `PREREGISTRATION.md`: the prediction, committed before the first run.
