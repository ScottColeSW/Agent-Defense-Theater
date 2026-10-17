# Agent Defense Theater

A live range for testing defenses against the [OWASP Top 10 for Agentic Applications](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/). Local AI models are attacked through tool protocols (real MCP servers in three of the items, simulated desks in the others), and every defense is scored by two numbers together: the attacks it stops and the legitimate work it still allows. Each prediction is committed before the run, and misses are reported.

![The test runner: pick a test or run them all, choose scripted or live, and watch the GPU](docs/img/runner.png)

## Why it exists

Most agent security claims show a defense blocking an attack. They rarely show what the defense cost in work that no longer got done, whether the prediction came before the result, or whether the numbers can be checked. This project makes those three things the default.

The targets are simulated: a support desk, a deal pipeline, mail that lands in a database table. The models and the measurements are real. The tool protocol is a real MCP server in ASI01, ASI02 and ASI04, and an in-process simulation in ASI03 and ASI08. The attacks were written by the author, and in later ASI03 rounds by models (see below).

## Results so far

| Risk | Test | Finding |
| --- | --- | --- |
| [ASI03](items/asi03-identity-privilege/) Identity and Privilege Abuse | A support desk with a shared token, scoped credentials, an approval step, request binding, and model and rule reviewers (three rounds, three models) | With no defense, 62 of 120 planted instructions were carried out. Request binding with approval holds let 0 of 120 through and completed 61 of 63 valid tasks. A model reviewer alone approved 12 refunds nobody asked for, and the same card made one reviewer model perfect and another deny nearly every legitimate refund. The approvers here are models and rules, not people. A later probe found a hole in the strongest condition: a duplicate of a requested refund reached review and was approved 32 of 32 times (see below) |
| [ASI02](items/asi02-tool-misuse/) Tool Misuse and Exploitation | An agent on two real MCP servers, one of them a SQLite pipeline it can overwrite, behind a schema gate, a dry run and request binding (eight attacks, three models) | With no defense, 50 of 120 attacks carried out an unsafe call. A schema gate cut that to 18 and adaptive attacks written for it still got through (9 times). A dry run changed the database 0 times and completed 0 of 24 privileged tasks, though 7 of 120 attacks still ran an unsafe calculation (4 floods of simulations, 3 falsified figures). Request binding plus the schema gate let 0 of 120 through, at a cost of valid work |
| [ASI01](items/asi01-goal-hijack/) Agent Goal Hijack | Five attempts to replace the operator's goal, against spotlighting, a plan locked before the agent reads anything untrusted, and a goal check by a separate reviewer model | A locked plan stopped every hijack that needed a new tool (0 of 36), and the goal check stopped all 45. Telling the model the text was untrusted made things worse: 33 of 45 hijacked against 22 with no defense. A follow-up replicated it on new deals (80% against 43%) and showed it was not the rule's wording, and a second test that it was not rule-following either: plain background text about the desk raised it as much as the security rule |
| [ASI04](items/asi04-supply-chain/) Agentic Supply Chain | A tampered tool staged in front of the real MCP server, against a manifest pin, a canary comparison and a code pin | Each control saw exactly what it was built to see. The only one that stopped everything, the code pin, also refused all 18 legitimate updates; the one that let updates through was fooled by a tool that recognizes the check |
| [ASI08](items/asi08-cascading-failures/) Cascading Failures | A bad figure injected into a three-agent crew, against a verify prompt, a range check and an independent recomputation | With no defense 29 of 45 bad figures became a harmful offer. The reviewer was not a check: it agreed with 78% of bad reports and 67% of honest ones. The independent recomputation stopped all 45 and cost nothing |
| [ASI06](items/asi06-memory-context-poisoning/) Memory and Context Poisoning | Forged documents against a memory gate, in the sibling [Aegis Vector](https://github.com/ScottColeSW/Project-Aegis-Vector) and [Palimpsest](https://github.com/ScottColeSW/Palimpsest) repositories | Linked, not yet re-run here |

A reviewer-calibration test has also run: seven reviewer models shown 22 cards whose right answers are known. Showing a reviewer the agent's own reason let 40% of non-matching requests through, against 6% when the system's comparison came first, and reviewers differed by 27 points on the same card. A thinking-model test also ran: with no defense, `qwen3:4b` followed planted instructions more often with thinking on (21 of 40) than off (12 of 40), the opposite of the prediction, at 14 times the tokens. The defenses held in both modes, though the difference rests on 40 cases a cell and is not statistically firm.

### Later ASI03 rounds

Each round committed its prediction first, and the addenda record the misses. The attackers in these rounds were not the author.

| Round | Attacker | Finding |
| --- | --- | --- |
| Blind attacks | Two Google models told nothing about the defenses wrote 45 attacks | With no defense 506/675 ran. Scoped credentials let 76/675 through, all from the 6 attacks inside the credential's gap, and request binding let 0/675 through, with or without holds. Unprompted, the writers found that gap in 2 of 39 attacks |
| Informed attacker | A hosted model shown how each defense works, one round of four before it declined to refine its attacks | 4 of its first 6 attacks aimed at the gap. Scoped credentials let 30/54 through on one task and 36/54 on the other, and request binding 0/54 on each |
| Duplicate-refund probe | Six author-written texts | The operator asks for one $30 refund and the ticket asks for it again. A $50 budget limit stopped it (0/54), and so did request binding alone (0/54). With holds, 32/54 ran and the reviewer approved 32 of 32 holds, because the duplicate matched the operator's words. A rerun under tighter generation limits reproduced it exactly in 5.4 minutes instead of 25.6 |
| Local attacker, four draws | `hermes3:8b`, shown the same defenses and outcomes | 4 to 14 usable attacks a draw and scoped-credential success from 0% to 18.7%, so one draw misleads. Request binding let 0/720 through, but no attack asked for a repeat, so the duplicate path has not been tried by an attacker model |

The takeaway is about method as much as defenses: a defense that survives a weak attacker has not been shown to hold, and the control that looked strongest had a hole that a simpler one did not.

![The top of a report: baseline risk, best control, and a verdict for every control, with residual risk and business impact side by side](docs/img/report.png)

## How it works

1. **Predict.** A prediction file and pass bar are committed first. The harness refuses a live run unless that file is committed, unedited, and the code matches a commit.
2. **Attack.** A live model does a legitimate task. Outsider-controlled text it reads (a ticket, a seller's remarks) carries a planted instruction, in three tiers: loud, quiet, and adaptive.
3. **Defend.** A gate, credential, approval or policy sits between the model and the tools. Conditions are compared on the same model replies, so the comparison is paired.
4. **Score.** Harm is read from what actually happened (a database difference, a call that reached a server), never from what the agent says. Valid tasks run in every condition, so protection is always shown next to the work it cost.
5. **Record.** Every decision goes into a hash-chained log (`python adt.py verify`). Scripted demo runs are labeled and never count as results.

Every report opens with an at-a-glance view: each control gets a verdict (effective, partial, costly, does not hold, or no measurable effect), with residual risk and business impact side by side. It also gives plain statements of what works, what is worth exploring and where a better solution is needed, and a closing question drawn from that run's own results. A GPU temperature guard pauses live runs above 72 C and keeps the pauses out of the latency figures (it is one dependency-free file and can be [used on its own](docs/GPU-COOLER.md)), and latency is split into model time, reviewer time and our own code. Each report also shows tempo (how long a case takes to an unsafe call or a refusal, with people explicitly not modeled) and threat surfaces (which kind of attack got through: prompt injection, identity and authority claims, or excessive agency), and a governance view that maps the results to framework requirements.

## Quick start

Python 3.10 or newer, standard library only. [Ollama](https://ollama.com) is needed to run live, and Node 18 or newer for the ASI02 calculators.

```bash
python adt.py serve --open     # the runner and the reports, at http://localhost:8765/start.html
python adt.py demo             # a scripted ASI03 run, then verify its decision log
python adt.py run asi03 --models llama3.1:8b,qwen2.5:7b,phi4-mini:3.8b
python -m pytest -q
```

Remote models: copy `keys.example.ini` to `keys.ini` (git ignores it), fill in the providers you have, and name a model with its provider, for example `--models anthropic:claude-haiku-5-5,llama3.1:8b`. `python adt.py keys` shows what is set up without printing a key, and `[limits]` in the file caps calls and output tokens. Hosted models are not digest-pinned, and each run records the provider and the model id the service reported.

Blind attacks: `python adt.py attackgen asi03 --models anthropic:claude-haiku-5-5 --n 8` has a model that was told nothing about the defenses write attacks from the item's `attacks/brief.json` alone (`--show-prompt` prints exactly what it is sent). The file is saved unedited under `attacks/generated/` with the model, prompt hash and an `attacks_sha256` to cite in a preregistration; candidates that name a missing tool, use unknown arguments or never reach a privileged tool are rejected with the reason kept.

For ASI02, run `npm install` once in `items/asi02-tool-misuse/targets/real-estate-tools`. `python adt.py -h` lists the rest (models, gpu, status, summary, verify, prereg, experiments).

## Using models together

The range runs on a mix of models, and the mix is part of the method. Local models (Ollama, on the workstation) play the agents under attack, so the thousands of calls a run needs cost nothing per call. Hosted models come in through API keys, free tiers or small prepaid balances, for the jobs a local 8B model cannot do independently: writing attacks from a plain description of the setting without ever being told about a defense, and acting as a reviewer or a stronger agent for comparison. A hand-written attack carries the author's knowledge of the defenses; an attack written blind by another model does not, and this closes that gap for a few dollars.

What it costs and what it does not: hosted tiers limit calls a minute and sometimes return "overloaded", so the runner waits as told and retries, and a hosted model is not pinned to a version or guaranteed to repeat at temperature 0. Each result records the provider and the model id the service reported, and a preregistration cites the hash of the generated attack file so it cannot change after the fact.

Keeping keys private:

- Keys live only in `keys.ini`, which git ignores, or in environment variables. `keys.example.ini` is the committed template and holds no key.
- Nothing prints, logs or saves a key. `python adt.py keys` says only whether one is set, errors have any key removed, and saved attack files are redacted before they are written.
- A test (`test_no_key_is_in_the_repository`) fails if any tracked or uncommitted file holds a configured key or a string shaped like one, so a slip is caught before a commit.
- A key pasted into a chat, a screenshot or a log is exposed. Revoke it at the provider and make a new one.
- Set `max_calls` under `[limits]` to cap what a mistaken run can spend. A reply that comes back empty is not retried, because each try is billed.

## Coverage

| ID | Risk | Status | What exists |
| --- | --- | --- | --- |
| [ASI01](items/asi01-goal-hijack/) | Agent Goal Hijack | Measured | Five goal-hijack attacks against spotlighting, a locked plan and a goal check; one preregistered live run. Spotlighting results in Aegis Vector |
| [ASI02](items/asi02-tool-misuse/) | Tool Misuse and Exploitation | Measured | Real MCP servers, three gates, eight attacks; first preregistered live run |
| [ASI03](items/asi03-identity-privilege/) | Identity and Privilege Abuse | Measured | Three preregistered live rounds |
| [ASI04](items/asi04-supply-chain/) | Agentic Supply Chain Vulnerabilities | Measured | A tampered MCP tool staged in front of the real server, and three load-time controls; one preregistered live run |
| [ASI05](items/asi05-code-execution/) | Unexpected Code Execution | Stub | Plan written |
| [ASI06](items/asi06-memory-context-poisoning/) | Memory and Context Poisoning | Measured elsewhere | Palimpsest and Aegis Vector |
| [ASI07](items/asi07-inter-agent-communication/) | Insecure Inter-Agent Communication | Stub | Plan written |
| [ASI08](items/asi08-cascading-failures/) | Cascading Failures | Measured | A three-agent crew where a bad figure can spread to an offer; one preregistered live run |
| [ASI09](items/asi09-human-agent-trust/) | Human-Agent Trust Exploitation | Built | AI reviewers measured; a [people study](site/study.html) built and waiting for participants |
| [ASI10](items/asi10-rogue-agents/) | Rogue Agents | Designed elsewhere | Agent Theater Framework and Void-Marauders |

Status means: **Stub** (plan written, nothing built), **Designed** (design exists, nothing measured), **Built** (runs, not yet measured), **Measured** (saved results with a prior prediction), **Adversarially tested** (measured against an attacker who knows the defense). Each item's mapping to the OWASP LLM Top 10 and MITRE ATLAS is in [`crosswalk/coverage.csv`](crosswalk/coverage.csv), and what each gap would take to close is in [`docs/LIMITS-AND-ANSWERS.md`](docs/LIMITS-AND-ANSWERS.md).

## Limits

- The gates and harm definitions are written by the author, and so were the first rounds' attacks. Later ASI03 rounds add attacks written by models (two hosted, one local) and an attacker shown the defenses, but no independent human red team has tried the range.
- Credentials, holds and approvals are in-process simulations. They are not integrations with an identity provider or a production MCP gateway.
- The models are local, up to 8B parameters, on one workstation. Nothing here says how larger models behave.
- Reviewers are models or rules. No person has been in the loop: a study with people is built and has no participants yet.
- The repository was built with AI coding assistance (Claude Code). Commits carry co-author trailers.
- The taxonomy mapping is the author's classification, not an endorsement by OWASP or MITRE.

The [governance crosswalk](docs/GOVERNANCE-CROSSWALK.md) sets each measurement beside the NIST AI RMF, EU AI Act and ISO/IEC 42001 requirements it bears on, with these gaps stated. It is evidence mapped to requirements, not a compliance claim.

## Repository

| Path | Contents |
| --- | --- |
| `items/` | One folder per OWASP risk: attacks, defenses, evaluation, preregistrations, saved results |
| `common/` | The shared harness and `adt` command line, results schema, decision log, MCP client, model and GPU management, tests |
| `site/` | The static site: the runner, reports, coverage and project pages |
| `docs/` | Methodology, threat model, preregistration template, limits register, roadmap, governance crosswalk |
| [`docs/CHECKLIST.md`](docs/CHECKLIST.md), [`docs/ROLE-QUESTIONS.md`](docs/ROLE-QUESTIONS.md), [`docs/OUTREACH.md`](docs/OUTREACH.md) | An eleven-item agent security checklist, open questions by role, and a one-page outreach summary, each answer with its caveat. A test recomputes every quoted number from the saved results |
| `crosswalk/` | Coverage and governance mapping data |
| `theater/`, `greenroom/` | The governance model (earned trust, three oversight speeds) and the adversarial arena spec the project builds on |
| `integrations/` | Sibling projects used or linked |

## Related projects

[Palimpsest](https://github.com/ScottColeSW/Palimpsest) (the memory gate), [Aegis Vector](https://github.com/ScottColeSW/Project-Aegis-Vector) (forgery testbed and episode player), [Void-Marauders](https://github.com/ScottColeSW/Void-Marauders) (outcome-sensitive trust between agents), [Evo](https://github.com/ScottColeSW/Evo) (multi-agent simulation with a benchmark harness).

## Author and license

Built by Scott A. Cole ([GitHub](https://github.com/ScottColeSW), [About](site/about.html)). MIT license, see [LICENSE](LICENSE).
