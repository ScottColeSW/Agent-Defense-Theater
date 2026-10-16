# Preregistration: <ASI id and name>

Commit this file before the first run. Do not edit the prediction afterward; add an addendum instead.

- **Date committed:**
- **Commit hash of the harness used:**

## Question

One sentence: what is being tested?

## Attacks

| Tier | Attack | Count |
| --- | --- | --- |
| Loud | | |
| Quiet | | |
| Adaptive | | |

## Defenses under test

List each defense and its layer (prevent, detect, contain).

## Models and agents

Model names, sizes, and the agent crew. State the hardware limit that capped model size, if any.

Generation settings: the output cap, the per-call timeout and the retry rule (defaults and reasons are in `docs/METHODOLOGY.md`, section 9). Say if this run changes any of them.

## Sample size

Runs per cell, and the step size that implies.

## Prediction

For each defense: expected attack success, expected retained utility, and a one-line reason.

## Pass bar

The number that would count as a win, written before the run.

## Known ways this could mislead

Author-written attacks, small samples, one scenario, and anything else that limits the claim.

## Addendum (after the run)

Actual results, which predictions missed, and what changed in the plan.
