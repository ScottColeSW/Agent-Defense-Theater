# Outreach one-pager

Copy to adapt, not to send as is. Every figure is recomputed from the saved results by `common/tests/test_claims.py`, and the scope line should travel with any of it.

## In one paragraph

Agent Defense Theater is a live range for testing defenses against the OWASP Top 10 for Agentic Applications. Local models are attacked through real tool protocols, and each defense is scored by two numbers together: the attacks it stops and the legitimate work it still allows. Predictions are committed before each run, and misses are reported.

## Three findings

1. **An approval path reopened what a hard limit had refused.** A $50 refund budget stopped a duplicate of a requested $30 refund (0 of 54). With a hold path the same duplicate was approved 32 of 32 times, because it matched the operator's own words. A rerun reproduced it exactly.
2. **Test results depend on the attacker.** Models told nothing about the defenses wrote 45 attacks, and request binding let 0 of 675 through. A hosted model shown the rules aimed 4 of its first 6 attacks at the one gap that leaks, while a local 8B attacker aimed 2 of 10 and did not improve with feedback.
3. **The hard parts are the checks, not the prompts.** Telling the model the text was untrusted raised hijacks from 22 of 45 to 33 of 45. The controls that held compared each action with something the agent did not write.

## Three questions, by audience

- **Security leadership:** Which of your agents carry one key that opens every door?
- **Engineering:** Where does an approval path reopen something a hard limit had refused?
- **Risk and audit:** Who has tried to break your control without having written it?

The full set is in [`ROLE-QUESTIONS.md`](ROLE-QUESTIONS.md), and an eleven-item checklist is in [`CHECKLIST.md`](CHECKLIST.md).

## Two short versions

**Email opener (about 70 words).** Built a range that attacks AI agents through real tool protocols and scores each defense on the attacks it stops and the work it still allows. One finding: an approval step approved a duplicate refund 32 of 32 times, and a plain budget limit stopped it. The questions it raised for security, engineering and audit leads are short, and each comes with a measured answer and its caveat. Happy to share them.

**One line.** A small range for testing agent defenses with predictions committed first: an approval step let a duplicate refund through 32 of 32 times, and a plain budget limit stopped it.

## State with it

Simulated targets, local models of 8B parameters or smaller, and attacks written by the author or by models. Evidence, not an audit, and not a compliance claim. Hosted-model calls for all attack generation cost $0.27 in total (the author's figure from the provider's billing page).

## Where to look

The repository is `github.com/ScottColeSW/Agent-Defense-Theater`. Results are under `items/*/results/`, and each round's preregistration, with its addendum of misses, sits beside them.
