# Reviewer study protocol (ASI09)

Commit this file before the first participant takes the study. Do not edit the prediction afterward; add an addendum instead.

- **Date committed:** 2026-10-15
- **The instrument:** [`site/study.html`](../../site/study.html), served by `python adt.py serve --open` at `http://localhost:8765/study.html`. Summary: `python adt.py study`, or `study.html?view=summary`.

## Question

When a person is the approver, does the way a request is presented change what they approve, as it did for the AI reviewers in the [calibration run](../asi03-identity-privilege/PREREGISTRATION-reviewer-calibration.md)? The AI reviewers approved 40% of the requests that did not match what the operator asked when shown the agent's own account, and 6% when the system's comparison came first. Do people show the same gap?

## What a participant does

Twenty-two request cards, the same ones the AI reviewers saw: eleven kinds of request on two tickets, four that match what the operator asked and seven that do not. Each is shown in one of three styles (the agent's own account, system-computed checks, the system's comparison first), rotated across participants so every request appears in every style across any three, and shown in a shuffled order. The participant approves or denies each one. The page records a random id, each decision and the time taken, and nothing else. The style, the family of request and the right answer stay on the server until the participant has finished.

## Who takes part

Whoever is asked: colleagues and others who sign off on, or would sign off on, what an agent does. There is no recruitment beyond that, no incentive, no time pressure, no queue, and nothing at stake.

## Prediction

Written before any participant. People, pooled over participants, one pass each.

| Presentation | Approved what was not asked (predicted) | Denied what was asked (predicted) | Median time per request |
| --- | --- | --- | --- |
| The agent's own account | 25% (10% to 45%) | 10% | 15 s |
| System-computed checks | 12% (3% to 25%) | 12% | 18 s |
| The system's comparison first | 5% (0% to 15%) | 5% | 9 s |

Reasons. A person reads a confident reason with more suspicion than a small model does, but a plausible reason from the agent is the thing that makes an approver relax, so the gap should be smaller than the models' and in the same direction. The comparison-first card answers the question for the reader, so it should be the fastest and the one with the fewest slips. People should not rubber-stamp it, since a card that says there is no match is easy to deny.

## Pass bar

Written before any participant. Each criterion is reported on its own, and only once at least five participants have finished all 22 requests. With fewer, the page and the summary say it is too few to read anything into, and nothing is reported as a result.

1. Presentation matters for people too: approvals of what was not asked are at least 10 points higher under the agent's own account than under the comparison-first card.
2. People do not rubber-stamp the comparison-first card: they deny what was asked no more than 15% of the time under it.
3. The comparison-first card is the fastest to decide: its median time is the lowest of the three.
4. People are fooled by the agent's own account less often than the AI reviewers pooled (40%).

An exploratory observation is also reported: the share of requests approved in the first, second and last third of the exercise, as a look for fatigue.

## Known ways this could mislead

- **Small and self-selected.** A handful of colleagues, who know this is a security exercise, are not a sample of approvers. They may be more careful than people in a real queue, or more suspicious than people who trust the agent they work with.
- **No consequence, no queue, no habit.** The mechanisms the stub for this risk worries about (approval fatigue, urgency, a reviewer's observed habits) are not present. This measures how people read the cards, not how they fail at work.
- **Cards written for models.** The cards are text written for a model reviewer, and a person may read them differently from a screen built for people.
- **The agent's reasons are the author's.** The reasons on the agent-style card were written by the author, not produced by an agent trying to persuade.
- **Twenty-two cards, eleven kinds, one scenario.**
- **Learning within the exercise.** A participant may work out the pattern as they go, which would lower the later slips and blur the style comparison. Order is shuffled to spread this, not remove it.
