# Questions by role

Two open questions for each role that owns part of the AI agent risk, each with one short answer from our measurements and the caveat that goes with it. The questions are meant to be asked of your own environment first. The answers are what we saw in ours.

**Scope, stated once.** Simulated targets, local models of 8B parameters or smaller, attacks written by the author or by two Google models. Evidence, not an audit, and not a compliance claim. Detail and caveats for every number are in [`CHECKLIST.md`](CHECKLIST.md) and the preregistrations under `items/`.

---

## CISO

**Which of your agents still carry one key that opens every door?**
With a shared admin token, 62 of 120 planted instructions were carried out. A credential scoped to the task and ticket cut that to 12 of 120.
*Caveat:* one simulated desk, one agent step.

**If an attacker already knows your controls, which one still holds?**
Request binding let 0 of 675 through against attacks written by models that were never told about the defenses. Scoped credentials let 76 through, all from the six attacks that fit one gap.
*Caveat:* the attack writers were two Google models, and the informed attacker finished one round of four.

## CEO / COO

**What does your agent read that someone else wrote, and what is it allowed to do about it?**
With no control, planted text became actions in 62 of 120 cases. The best control left 0 of 120 and still completed 61 of 63 valid tasks.
*Caveat:* the valid tasks are the author's and tidier than real work.

**Where is a person in the loop, and what do they actually see?**
A reviewer shown the agent's own reason let 40% of non-matching requests through. Shown the system's comparison with the operator's words first, 6%.
*Caveat:* the reviewers were small models. A study with people is built and waiting for participants.

## CFO

**What does a control cost in work that no longer gets done?**
The one control that stopped every tampered tool also refused all 18 legitimate updates. Request binding with approval holds kept 61 of 63 valid tasks.
*Caveat:* two simulated settings.

**What does it cost to test this?**
All the attack generation so far, hosted models included, cost $0.27 (the author's figure from the provider's billing page), under hard caps on calls and tokens.
*Caveat:* small models and small samples. Larger models cost more and may behave differently.

## CTO

**Where does an approval path reopen something a hard limit had refused?**
A $50 refund budget stopped a duplicate of a requested $30 refund (0 of 54). With a hold path the same duplicate was approved 32 of 32 times, because it matched the operator's words.
It reproduced exactly on a rerun.
No attacker model has tried this shape yet (none of 40 local attack texts asks for a repeat).
*Caveat:* six author-written texts, one mechanism, one reviewer model.

**Which defenses did you adopt because they sound right?**
Telling the model the text was untrusted raised hijacks from 22 of 45 to 33 of 45.
*Caveat:* five attacks, three models.

## Head of AppSec

**Who has tried to break your control without having written it?**
Models given only a description of the setting wrote 45 attacks and found the one leaking gap in 2 of 39 on their own. Shown the rules, the strongest model aimed 4 of its first 6 at it, while a local 8B attacker shown the same history aimed 2 of 10 and did not improve with feedback. Across four draws of that local attacker, scoped-credential success ranged from 0% to 18.7%, so one draw misleads.
*Caveat:* one vendor for the hosted writers and one small local model. Request binding held in all four draws (0 of 720). Attackers of different strength all matter, and none replaces an outside red team.

**Who checks the checker?**
On the same card, reviewer models differed by 27 points. One alone approved 12 refunds nobody asked for. In a three-agent crew a reviewer agreed with 78% of bad reports and 67% of honest ones.
*Caveat:* a handful of small models.

## Compliance and Audit

**Can you show a prediction was made before the result, and that the log was not edited?**
Each preregistered live run refuses to start unless its prediction is committed and unedited. Each decision goes into a hash-chained log that can be verified. Misses are reported: the no-defense rate in the blind round came in at 75% against a predicted 52%.
*Caveat:* method, not a guarantee. The governance crosswalk lists the gaps against NIST AI RMF, EU AI Act and ISO/IEC 42001.

**What could not be tested, and what would close it?**
Independent red teams, larger models, real tool catalogs, production telemetry and people reviewing approvals. Each is listed with what it would take in `LIMITS-AND-ANSWERS.md`.
*Caveat:* the list is the author's own.

## Board

**If attackers are not refused and know our controls, what is our worst case?**
Our worst finding was the approval path that approved a duplicate refund 32 of 32 times. The control that looked strongest, request binding with holds, had a hole that a simpler control (a final budget denial) did not.
*Caveat:* one simulated setting. It shows a kind of failure to look for, not how often it happens elsewhere.

**Is a refusal from an AI provider part of our defense?**
One hosted model wrote attacks on request, then declined to refine them from results. A local model wrote attacks from the same prompt without declining, though few and weak ones.
*Caveat:* one refusal from one hosted model on one prompt, and one small local model.
