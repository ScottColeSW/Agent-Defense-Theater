# Roadmap

The order follows the gaps that matter most for agent containment. Each step has an exit criterion so it can be called done.

| Step | Work | Exit criterion |
| --- | --- | --- |
| 1 | `common/` harness, results schema, decision log | One scripted example run writes a valid result record and a verifiable log entry |
| 2 | ASI03 Identity and Privilege Abuse | Preregistration committed; scoped-credential prototype blocks the scripted confused-deputy case with utility reported |
| 3 | ASI02 Tool Misuse and Exploitation | Policy gate in front of the RealEstateTools MCP server; block and pass rates reported |
| 4 | ASI05 Unexpected Code Execution | Sandbox tier runs the crew's generated code with no network; escape attempts logged |
| 5 | ASI01 Goal Hijack on a tool-using crew | Plan-diff gate measured against the three attack tiers |
| 6 | ASI04 Supply Chain | Pinned manifest check catches a tampered tool; false-block rate reported |
| 7 | ASI07, ASI08 on the crew | Signed messages and circuit breaker measured |
| 8 | ASI09, ASI10 with Theater tiers | Tier transitions measured over a long run; reviewer-presentation test designed |
| 9 | Adaptive tier for every measured item | An attacker who knows the defense has tried and the result is reported |

Items 8 and 9 depend on resources noted in [`LIMITS-AND-ANSWERS.md`](LIMITS-AND-ANSWERS.md).
