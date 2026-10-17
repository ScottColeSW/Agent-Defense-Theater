# An AI agent security checklist, from what we measured

Eleven things worth checking against your own agents. Most teams will already do several. Each item says what we saw, in numbers, and where the evidence is thin, so you can weigh it against your own setup.

**Scope, stated once.** Everything below comes from simulated targets (a support desk, a deal pipeline, a three-agent crew), local models of 8B parameters or smaller, and attacks written either by the author or by two Google models. It is evidence, not an audit, and not a compliance claim. Results are in `items/*/results/`, and each round's prediction was committed before its run.

---

**1. Which of your agents carry one key that opens every door, and what does each one read that someone else wrote?**
*What we saw:* with a shared admin token, 62 of 120 planted instructions were carried out. Scoping the credential to the task and ticket cut that to 12 of 120.
*Caveat:* one simulated desk, one agent step. Credential lifetimes and mid-task changes were not tested.

**2. Does a control compare each privileged action with what the requester actually asked for, using data the agent did not write?**
*What we saw:* request binding let 0 of 120 through against the author's attacks and 0 of 675 against attacks written by models that were never told about the defenses, with no loss of valid work in either.
*Caveat:* our operator requests state amounts and destinations plainly and are matched as text. Vaguer requests will be harder. See item 5 for a way it failed.

**3. What does your approver see, and who wrote it?**
*What we saw:* showing a reviewer the agent's own stated reason let 40% of non-matching requests through, against 6% when the system's comparison with the operator's words came first.
*Caveat:* the reviewers were small models on 22 cards. People were not studied (a study is built and waiting for participants).

**4. Have you tested your reviewer against cases with known answers?**
*What we saw:* on the same card, reviewers differed by 27 points, and one model reviewer alone approved 12 refunds nobody asked for. In a three-agent crew, a reviewer agreed with 78% of bad reports and 67% of honest ones, so its agreement carried almost no information.
*Caveat:* two small simulated settings, a handful of reviewer models.

**5. Can an approval path reopen something a hard limit had already refused?**
*What we saw:* the $50 refund budget alone stopped a duplicate of a requested $30 refund (0 of 54). Add a hold path and the denial became a review: the card said MATCH, because $30 was the amount the operator named, and the reviewer approved 32 of 32. This held under request binding as well. A rerun under tighter generation limits reproduced it exactly (32 of 54, and 32 of 32 holds approved).
*Caveat:* six author-written texts, one mechanism, three agents and one reviewer model. A rule such as one refund per ticket, or a reviewer shown the refund history, was not tested.

**6. Are you counting on "be careful" prompts?**
*What we saw:* telling the model the text was untrusted made hijacks go up, 33 of 45 against 22 with no defense. A follow-up found it was not the wording of the rule.
*Caveat:* five goal-hijack attacks, three models.

**7. What does each control cost in work that no longer gets done?**
*What we saw:* the one control that stopped every tampered tool also refused all 18 legitimate updates. Scoped credentials alone blocked all above-tier work (0 of 27). Request binding with holds still completed 61 of 63 valid tasks.
*Caveat:* the valid tasks are the author's. Real workloads are messier.

**8. Do you test with attackers who did not write the controls, and with attackers who know them?**
*What we saw:* given only a description of the setting, two models wrote 45 attacks and found the one gap that leaks (refunds inside the credential's limit) in 2 of 39 unprompted. Shown the rules, the pro model aimed 4 of its first 6 straight at it. The 6 attacks that fit the gap produced all 76 leaks under scoped credentials. A local 8B model, shown the same defenses and the outcomes so far, wrote 10 usable attacks over three rounds, only 2 of which fit the gap, and its results did not improve with feedback.
*Caveat:* both hosted writers are Google models. The informed attacker managed one round of four (see item 9). Request binding held against the local attacker too (0 of 180), but an attacker that never found the gap is weak evidence that nothing else is there.

**9. Are you assuming an attacker will be refused?**
*What we saw:* one hosted model wrote attacks on request, then declined to refine them from results ("I cannot generate functional prompt injection payloads"). Nothing about that stops an attacker with other models: a local 8B model wrote attacks from the same prompt in all three rounds without declining.
*Caveat:* one refusal, one hosted model, one prompt. We did not try to get around it. The local model wrote few attacks and weak ones, so not declining is not the same as being a capable attacker.

**10. Did you write down the prediction before you measured, and can the log be checked?**
*What we saw:* every preregistered live run here refuses to start unless its prediction is committed and unedited, misses are reported (we missed the no-defense rate in the blind round, 75% against a predicted 52%), and each decision goes into a hash-chained log you can verify.
*Caveat:* this is method, not a guarantee. A prediction can still be wrong in a way that hides a hole.

**11. Is every model call bounded, in size, time, retries and spend?**
*What we saw:* two runaway generations held a GPU at 77 C for about ten minutes each, under a 64 C limit, because the cooler can only act between calls. An output cap, a timeout and no retry on timeouts now bound a call: a rerun of the same probe took 5.4 minutes instead of 25.6, with the longest call at 16.8 seconds. Hosted calls for all the attack generation so far cost $0.27 in total (the author's figure from the provider's billing page), under a cap of 4 attacker calls per run.
*Caveat:* this is about availability and cost. It is a smaller risk than the others on this list, and it was a surprise to us.
