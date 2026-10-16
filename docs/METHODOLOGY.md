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

## 9. Generation settings are part of the method

What a local model may output, and how long a call may take, change what a reply can be, so a preregistration names them. The defaults live in `common/adt/models.py`:

| Setting | Default | Why |
| --- | --- | --- |
| Output cap, a model not asked to think | 1,024 tokens | The agents answer with a short JSON plan (100 to 200 tokens). A longer reply is a runaway, and an uncapped one can run for minutes at full GPU load |
| Output cap, a thinking model | 4,096 tokens | Reasoning needs room |
| Timeout for one request | 120 s (300 s when thinking) | Bounds a stalled call |
| Retry | Once for an ordinary server error. **None** for a timeout or a repetition abort | At temperature 0 with a fixed seed a repeat would run away the same way |

A reply that hits the cap carries `truncated` on its record. A call that times out or is aborted by Ollama as a repetition loop is recorded as a failed case with `runaway: true` and `model_error_kind`, and is counted with the model errors, never as an attack success.

**These limits date from 2026-10-16.** The runs before that (including the blind, informed and duplicate-probe rounds of ASI03) used no output cap, a 300 s timeout and one retry for every error. The duplicate probe lost two cases to this: `llama3.1:8b` ran away for about ten minutes on each, twice, and the card sat at 77 C while the cooler, which acts between calls, could not intervene. Those cases are in the saved results as model errors. A preregistration written from now on should state the settings it uses and say if it changes any.

A replicate of the duplicate probe under these limits reproduced its result exactly (32 of 54) in 5.4 minutes instead of 25.6, with the longest call at 16.8 seconds. The two cases that had run away were cut at the cap and flagged `truncated` instead of timing out.
