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

## Addendum (after the first five participants)

Five participants finished all 22 cards, 110 answers, 2026-11-08 (`python adt.py study`; raw: `results/study/answers.jsonl`, `participants.jsonl`).

**A deviation from the committed protocol, disclosed rather than absorbed into the numbers:** these five took the study together at a gathering, with someone reading each card aloud rather than each participant reading independently and silently, as "What a participant does" above describes. Four of the five decided in well under two seconds on every single one of their 22 cards (session medians 0.9 to 1.0 s, no card over 5.9 s); the fifth took a median of 11.5 s and up to three minutes on one card. The recorded "time taken" therefore does not measure what the protocol predicted it would (reading plus deciding time) for four of the five, and criterion 3 is reported as **uninformative** for that reason, not as met or missed. The decisions themselves are still each participant's own choice, made out loud in response to a card read to them, not fabricated or skipped; they are kept.

### Prediction against result

| Presentation | Approved what was not asked (predicted) | Observed | Denied what was asked (predicted) | Observed |
| --- | --- | --- | --- | --- |
| The agent's own account | 25% (10 to 45) | **54% (13/24), far above its range** | 10% | **38% (5/13), far above its range** |
| System-computed checks | 12% (3 to 25) | **39% (9/23), far above its range** | 12% | **50% (7/14), far above its range** |
| The system's comparison first | 5% (0 to 15) | **26% (6/23), far above its range** | 5% | **62% (8/13), far above its range** |

Every number in both columns came in far above its predicted range, in the same direction, for all three presentation styles. The miss is uniform rather than style-specific, which points at a shared cause the prediction did not anticipate strongly enough even though it is named in this file's own known-limitations list below ("cards written for models... a person may read them differently"): the cards were, in this administration, hard enough to parse, read aloud, in a social setting, that both kinds of error went up together for every style, not just the one the prediction expected to be weakest.

### Pass bar: one met, two missed, one uninformative

| # | Criterion | Result |
| --- | --- | --- |
| 1 | Approvals of what was not asked are at least 10 points higher under the agent's own account than under the comparison-first card | Met. 54% against 26%, a 28-point gap |
| 2 | People do not rubber-stamp the comparison-first card: deny what was asked no more than 15% of the time under it | **Missed.** 62% (8/13) — far from rubber-stamping, the comparison-first card was wrongly denied more often than either other style |
| 3 | The comparison-first card is the fastest to decide | **Uninformative.** All three medians (0.9, 1.0, 0.9 s) sit at the floor of how fast a read-aloud decision can be recorded; the administration deviation above means this run cannot distinguish them |
| 4 | People are fooled by the agent's own account less often than the AI reviewers pooled (40%) | **Missed.** 54% against 40% — people were fooled *more* often than the small local models were, not less |

Exploratory fatigue observation: approvals ran 48% in the first third of each participant's cards, 43% in the second, 40% in the last — a mild downward drift, the opposite of fatigue (people got more cautious, not less, as the exercise went on).

### What this run shows

- **A real presentation-style gap survived even a confusing, read-aloud administration** (criterion 1, met by a wide margin): people approved what was not asked almost twice as often when shown the agent's own account as when shown the system's comparison first.
- **People were fooled more often than the AI reviewers this study was built to compare against**, not less — the opposite of what was predicted, and by a wide margin (54% against 40%).
- **The comparison-first card, which states plainly whether the request matches, was wrongly denied more than any other style (62%)** — the sharpest sign that the cards themselves, not just the agent's framing, were hard to act on correctly. This is consistent with what one participant said afterward (the questions were long and it was hard to tell what information mattered), not just a number that happened to come out high.

### What this run does not show

- **Whether a person reading independently and silently, as the protocol describes, would show the same pattern.** This administration (read aloud, in a group, at a social gathering) is disclosed above as a real deviation; the timing data in particular cannot be read as if it had not happened.
- **Whether the gap between styles would survive a clearer card.** The uniform miss across all three styles is the strongest signal in this run that the cards' own difficulty, not the presentation manipulation, may be driving a large share of both error rates; a revised, shorter card is needed before concluding more than criterion 1's gap.
- **Five people, one pass each, who knew this was a security exercise and took it together.** Not a sample of approvers in a real queue.
- This result stands as five of the five participants this protocol's own pass bar requires before anything is reported; a second round, with a clearer instrument, would be a replication, not a do-over of a broken one.
