# Methodology

The rules that make a result in this repository worth reading.

## 1. Predict first

Each item has a `PREREGISTRATION.md`. The prediction, the attack set, the defenses, the sample size, and the pass bar are committed before the first run. A run without a committed prediction is exploratory and is labeled that way. Misses are reported, not removed.

## 2. Measure three things together

| Measure | Question |
| --- | --- |
| Attack success | How often did the attack achieve its goal? |
| Retained utility | How often did legitimate work still succeed with the defense on? |
| Cost | Tokens, time, and added latency per task |

A defense that blocks everything by refusing everything scores zero utility and is reported as such.

## 3. Three attack tiers

Loud (obvious), quiet (plausible and low-signal), adaptive (written against the defense in place). A result is labeled by the highest tier it faced.

## 4. Scripted versus live

- **Live:** a real model produced the output in a saved run.
- **Scripted:** a human-written sequence that illustrates a mechanism. It is shown in the demo and never counted as a result.

## 5. Tempo and threat surfaces

Every report shows two more views, computed from the saved records.

- **Tempo.** How long a case takes from the agent being given the task, with the planted instruction already in what it reads, to an unsafe call being carried out or refused, and how long each defense takes to decide against the agent's own time. It is the machine side of the clock only. People are not modeled: every hold in these tests is decided by a model or a rule in about a second or less, while a real hold waits for a person. For tests with several rounds the figure is the whole case, an upper bound on the time to the unsafe call.
- **Threat surfaces.** The planted attacks grouped by the author's classification of their primary mechanism: prompt injection, identity and authority claims, and excessive agency. The grouping is in [`crosswalk/threat-surfaces.json`](../crosswalk/threat-surfaces.json), with a reason for each placement that is not obvious. An attack can touch more than one surface and is placed by the one it leans on most, so the grouping is a reading aid and not a measurement.

These tests are not about critical infrastructure and make no claim about it. The stakes in every scenario are fictional.

## 6. Status labels

Stub, Designed, Built, Measured, Adversarially tested. An item moves up only when its evidence is in the repository or linked from it.

## 7. Small samples are stated

Report the number of answers per cell and the resulting step size. Ranges are wide on small runs and the report says so.

## 8. Failures stay in

Ideas that did not work are written up with the same care as ideas that did.
