# Roadmap

The order follows the gaps that matter most for agent containment. Each step has an exit criterion so it can be called done.

| Step | Work | Exit criterion |
| --- | --- | --- |
| 1 | `common/` harness, results schema, decision log | One scripted example run writes a valid result record and a verifiable log entry |
| 2 | ASI03 Identity and Privilege Abuse | Preregistration committed; scoped-credential prototype blocks the scripted confused-deputy case with utility reported |
| 3 | ASI02 Tool Misuse and Exploitation | Policy gates in front of two real MCP servers (RealEstateTools calculators and a SQLite Deal Desk); unsafe-call and valid-work rates reported |
| 4 | ASI05 Unexpected Code Execution | Sandbox tier runs the crew's generated code with no network; escape attempts logged |
| 5 | ASI01 Goal Hijack on a tool-using crew | Plan-diff gate measured against the three attack tiers |
| 6 | ASI04 Supply Chain | Pinned manifest check catches a tampered tool; false-block rate reported |
| 7 | ASI07, ASI08 on the crew | Signed messages and circuit breaker measured |
| 8 | ASI09, ASI10 with Theater tiers | Tier transitions measured over a long run; reviewer-presentation test designed |
| 9 | Adaptive tier for every measured item | An attacker who knows the defense has tried and the result is reported |

Items 8 and 9 depend on resources noted in [`LIMITS-AND-ANSWERS.md`](LIMITS-AND-ANSWERS.md).

## Progress

- **Step 1 done (2026-10-13).** `python adt.py demo` writes valid result records and a log entry that verifies.
- **Step 2 follow-up, escalation (2026-10-13).** An approval step with a one-shot credential was added and measured. Integrity held (no beyond-tier action without an approval) but a small model reviewer recovered only 30% of legitimate above-tier work and did not stop in-scope abuse. Next: a system-computed bottom line on the card, a stronger reviewer, and a per-task budget. Details in the ASI03 escalation addendum.
- **Step 2, third round (2026-10-13).** A system-stated bottom line fixed one reviewer model and not another; request binding plus holds gave 0 of 120 attacks with all valid work kept (61 of 63). Next: reviewer calibration on known cards, vague requests (where a model could beat a rule), adaptive attacks on the binding, thinking models, a human study. Details in the ASI03 bottom-line addendum.
- **Step 2 done (2026-10-13).** Preregistration committed, scoped-credential prototype blocked every call beyond tier 1 (0 of 90) with utility reported. The sensitivity of the utility check is limited, and in-scope abuse still gets through. Details in the ASI03 addendum.
