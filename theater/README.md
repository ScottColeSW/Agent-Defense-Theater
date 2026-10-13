# Theater: the governance layer

Status: Designed. The Agent Theater Framework exists as a concept and in the author's writing. Nothing in this folder runs yet.

## Ideas to implement

**Earned trust.** A new agent starts on probation with the lowest privilege tier. Trust rises only from observed outcomes, and a harmful outcome costs more than a good one earns.

**Three agent classes.** Each agent is classed from its outcome history.

| Class | Meaning | Default handling |
| --- | --- | --- |
| Performing | Does its assigned role reliably | Normal privileges for its tier |
| Miscast | Capable, but in the wrong role or beyond its competence | Reassign or restrict, not punish |
| Bad | Acts against the objective, whether compromised or misaligned | Quarantine and review |

**Human oversight at three speeds.** Higher-impact actions get slower, more deliberate review. Speed names and thresholds are to be set in `OVERSIGHT.md`.

## Planned files

| File | Purpose |
| --- | --- |
| `TIERS.md` | Privilege ceilings per trust tier |
| `CLASSIFICATION.md` | How an agent is classed performing, miscast, or bad, and the evidence required |
| `OVERSIGHT.md` | The three review speeds and what triggers each |
| `PROBATION.md` | How trust is earned and lost |
| `theater/` code | Added when the harness exists |

## Where it plugs in

- ASI03 uses the tier ceilings as credential scopes.
- ASI09 uses the oversight speeds as the review policy.
- ASI10 uses the classification as the rogue-agent detector.
- ASI08 uses demotion as a circuit breaker.
