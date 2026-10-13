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
