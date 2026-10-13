# Results schema

Every saved run writes one record per answer. Fields below are the contract the item folders depend on.

| Field | Type | Meaning |
| --- | --- | --- |
| `run_id` | string | Unique id for the run |
| `item` | string | OWASP agentic id, for example `ASI03` |
| `tier` | string | `loud`, `quiet`, or `adaptive` |
| `attack` | string | Attack name |
| `defense` | string | Defense name, or `none` |
| `layer` | string | `prevent`, `detect`, `contain`, or `none` |
| `model` | string | Model name and size |
| `crew` | string | Agent crew or scenario id |
| `outcome` | string | `attack_succeeded`, `blocked`, `task_succeeded`, `task_failed`, or `flagged` |
| `tokens_in`, `tokens_out` | integer | Cost |
| `latency_ms` | integer | Added time for the task |
| `mode` | string | `live` or `scripted` (scripted is never a result) |
| `prereg` | string | Path to the preregistration committed before the run |
| `hardware_note` | string | What capped the model size or sample count |
| `timestamp` | string | UTC time |

Summary tables report attack success, retained utility, and cost per cell with the number of answers, so step size is visible.
