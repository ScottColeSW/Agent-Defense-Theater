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

## 5. Status labels

Stub, Designed, Built, Measured, Adversarially tested. An item moves up only when its evidence is in the repository or linked from it.

## 6. Small samples are stated

Report the number of answers per cell and the resulting step size. Ranges are wide on small runs and the report says so.

## 7. Failures stay in

Ideas that did not work are written up with the same care as ideas that did.
