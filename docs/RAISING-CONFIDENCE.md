# Raising confidence

The [Risk vs Confidence](../site/risk.html) page reports confidence as a measured number: how well the strongest
defense contained our attack suite, with a 95% Wilson floor and the sample size, never a bare 100%. This page says
what that number is bounded by, and the concrete ways to raise the floor. The short version is on the chart itself:
push a point down with stronger controls, push it right with harder, independent testing. This is the "right".

## What the floor is bounded by

A high containment floor is an upper bound on confidence, not a guarantee, for two separate reasons.

1. **The attacker is the author.** The same work that built the defenses wrote the attacks that test them. An attack
   suite written by the defender's own hand cannot show what an independent adversary would find. This is the single
   largest open gap, tracked in [issue 33](https://github.com/ScottColeSW/Agent-Defense-Theater/issues/33).

2. **Small models can flatter the defense.** The agents under attack are local models up to 8B on one workstation. A
   weaker agent sometimes simply fails to write the bypass it was nudged toward, so the measured attack-success rate
   drops, and that reads as containment when it is really model incapacity. The preregistrations already note this as
   "the live rate is a model-compliance rate." Nothing here shows how a more capable agent behaves.

So the floor is conservative twice over: it assumes our attacks, and it assumes an agent no smarter than an 8B. Both
assumptions can only make the real residual risk larger than the page shows, never smaller.

## The levers, in order

Each lever moves points to the right on the chart (more confidence) or down (less residual), and the order is roughly
by how much it closes the gaps above.

1. **An independent attacker.** A human red team, or a model with no knowledge of the defenses, writing and refining
   attacks. This is the only thing that answers the attacker-is-author limit directly. The range already takes a step
   here (blind and informed model-written attacks in later ASI03 rounds), but no independent human has tried it. See
   [issue 33](https://github.com/ScottColeSW/Agent-Defense-Theater/issues/33) and [`OPEN-WORK.md`](OPEN-WORK.md).

2. **A more capable agent.** Run the agents under attack, not just the attackers, on larger hosted models. A smarter
   agent is a harder test: it is more likely to actually execute the bypass, so a floor that holds against it means
   much more than one that holds against an 8B. This is the direct answer to the small-model limit. Hosted models come
   in through `keys.ini` the same way the attacker models do (see the README's "Using models together").

3. **More replicates, wider distribution.** Confidence is a distribution, not a point. More runs and a wider spread of
   attack phrasings tighten the Wilson interval, which narrows the gap between the point estimate and the floor, which
   moves the point right without changing the defense at all. The replicate runs already recorded for ASI03, ASI05 and
   ASI07 are the start of this.

4. **Live-deployment telemetry.** The confidence and containment KPIs marked *Framework* on the
   [Purple Team](../site/purpleteam.html) page (semantic drift, rolling live windows, p95 latency under real load,
   OpenTelemetry trace correlation) are a running deployment's to measure. They validate the bench's findings under
   real traffic rather than a fixed suite.

## The run pattern

Confidence is only honest as a number you keep. The pattern that keeps it:

1. **Commit the prediction first.** Every run's pass bar is committed before it runs; the harness refuses a live run
   otherwise. Nothing below changes that.
2. **Re-run on every defense change.** When a control changes, re-run its item on the preregistered model set, rebuild
   the site (`python tools/build_data.py`, now deterministic so it only changes when the data does), and read the new
   floor. A control that was strengthened should not move the floor down.
3. **Track the floor over time.** A regression shows up as the containment floor dropping between runs, the same way
   the Purple Team page's "continuous regression" describes. Keep each run's `risk.json`; compare floors, not point
   estimates.
4. **Re-test after a model swap.** A silent provider update or a new local model is a new agent, so a floor measured
   against the old one no longer stands. Re-run before trusting it.

## Where this already lives

This page ties the forward path to the confidence axis; it does not replace the backlog. The gaps themselves are in
[`OPEN-WORK.md`](OPEN-WORK.md) (every known gap as an unclaimed stub), the honest answers in
[`LIMITS-AND-ANSWERS.md`](LIMITS-AND-ANSWERS.md), the red/blue/shared capabilities in
[`PURPLE-TEAM-MAP.md`](PURPLE-TEAM-MAP.md), and the roadmap in [`ROADMAP.md`](ROADMAP.md).
