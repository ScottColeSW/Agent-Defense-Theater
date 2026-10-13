# ASI03 results

Only saved runs live here.

| File | Contents |
| --- | --- |
| `asi03-<time>-prereg.jsonl` | One record per answer, in [`common/RESULTS-SCHEMA.md`](../../../common/RESULTS-SCHEMA.md), plus `attempted`, `exceeds_tier`, `blast_usd`, `calls`, `denied`, `invalid_calls`, `task_done`, `tier_ok` |
| `asi03-<time>-prereg.decisions.jsonl` | The hash-chained decision log: every tool call, allowed or denied, with tier, delegation chain and reason |
| `asi03-<experiment>-<time>-prereg.gpu.json` | The GPU temperature timeline and the cooler's pause events for that run (runs from 2026-10-13 on) |
| `asi03-<time>-prereg.meta.json` | Models, counts, the preregistration commit, the harness commit, and the decision-log head hash |
| (not here) | Exploratory runs and scripted demos are throwaway test output. They go under the system temp folder (`<temp>/adt/asi03-identity-privilege/`), which follows `TMP`/`TEMP`, not into the repository |

`-prereg` in a file name means the harness checked that the prediction was committed and the code matched a commit before it started.

```bash
python adt.py summary asi03                        # by defense
python adt.py summary asi03 --by defense,tier
python adt.py summary asi03 --by attack,defense
python adt.py summary asi03 --by defense,model
python adt.py verify                               # check every decision-log hash chain
```

## Reading these results

- Attacks and the credential gate were written by the same author. No attacker saw a run before writing.
- Replies are reused across defenses that act after the model, so `none` and `scoped_credentials` see identical model output. The comparison is paired, and the samples are not independent.
- Thirty attack cases per defense and model (six attacks across five tickets), 90 pooled. Intervals are Wilson 95%.
- A simulated desk, one agent step, three models up to 8B. See [`../README.md`](../README.md) and the addendum in [`../PREREGISTRATION.md`](../PREREGISTRATION.md).
