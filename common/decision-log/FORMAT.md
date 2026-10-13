# Decision log format

One JSON object per line. Implemented in [`../adt/decisionlog.py`](../adt/decisionlog.py).

| Field | Meaning |
| --- | --- |
| `seq` | 1, 2, 3 ... with no gaps |
| `ts` | UTC time of the decision |
| `actor` | The agent that asked |
| `tier` | The actor's Theater trust tier at the time |
| `delegation` | The chain of authority, for example `["operator:alice", "support-agent"]` |
| `action` | What was asked (the tool name) |
| `saw` | What the decider looked at: arguments, the credential in use, the defense, the case |
| `verdict` | `allow` or `deny` |
| `reason` | Why, in words a reviewer can read |
| `prev` | The `hash` of the entry before it (64 zeros for the first) |
| `hash` | SHA-256 of this entry with `hash` removed, serialized with sorted keys and no spaces |

Every entry in a run is written, allowed or denied. An allowed call under the ambient token is logged with the reason "shared service token holds every scope", which is the point: the log shows that nothing was deciding.
