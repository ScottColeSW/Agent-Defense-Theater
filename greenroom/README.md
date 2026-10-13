# Greenroom: the adversarial arena

Status: Designed. The Greenroom design exists as a specification (draft 0.3) that has not been built. Add the spec to this folder as `SPEC.md` when ready.

## Purpose

Run a crew of agents under Theater's governance and attack it on purpose, then show what held and what did not.

## Format

The Black Hat vs White Hat episode format from [Aegis Vector](https://github.com/ScottColeSW/Project-Aegis-Vector):

1. Black Hat plants an attack.
2. White Hat answers with a defense.
3. A real model answers a real task, and the verdict is the measured rate.
4. The loser's next move counters what just beat them, up a ladder of defenses.

Each episode names the OWASP agentic item it exercises.

## Design rules carried over

- An automatic-versus-human decision switch, so a person can take over any step.
- Limits on live demos, so an audience can see a run without an unbounded cost or risk.
- Scripted episodes are labeled scripted and are never counted as results.

## Planned files

| File | Purpose |
| --- | --- |
| `SPEC.md` | The Greenroom design specification |
| `CREW.md` | The agents in the demonstration crew and their roles |
| `EPISODES.md` | The episode list, one per OWASP item, with the attack ladder |
| `SWITCH.md` | How the automatic-versus-human switch behaves |

## Relationship to the items

Each `asiNN-*` folder holds the attacks and defenses. Greenroom schedules them as episodes and shows the results.
