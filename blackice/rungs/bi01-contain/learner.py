"""Black ICE: does a learned baseline earn a place as an advisor? A scripted, synthetic comparison.

Scripted and synthetic. The tokens, the owner's habits and the bot are written by the author, so this shows trade-offs under those
assumptions. It is not a measurement of any real system and never counts as a result. Nothing here is a live model.

The setting is the case source binding cannot handle: a bot with a foothold inside the owner's network uses leaked tokens from the
owner's own addresses, so "new source" never fires. What is left is how much each token is used. Four detectors watch that:

  none           nothing
  fixed_cap      alarm above three times the token's day-zero volume; a person set it and it never changes
  learned_naive  a running average of each token's volume, alarm four deviations above it, learning from every day
  learned_capped the same, but its baseline may rise at most 3% a day and is clamped to between half and four times the day-zero
                 volume, and its spread is bounded too (the bounds a person sets)
  learned_verified  the capped learner, and it learns only from days without an alarm (an alarm day is not trusted as data)

Bots, from a foothold: a burst (ten times normal at once), a slow ramp (the "boiling frog": volume rises 8% a day to ten times),
low and slow (1.5 times normal for good) and a mimic (takes a share of the owner's normal volume, so total volume never changes).

The owner is not static either. A seasonal burst (four times normal for four days) and a permanent migration (three times normal from
some day on) are honest changes a detector should survive. A fixed cap alarms on every honest change forever. A learner adapts, and
that adaptation is also what a bot's slow ramp exploits.

Two modes per run. As an advisor a detector only raises alerts, and what a person does with them is not modeled. With authority an alert
rotates the token: the bot's copy dies and the owner is interrupted once, whether the alert was right or not.

Usage
  python blackice/rungs/bi01-contain/learner.py
"""
import math
import random
import sys
from pathlib import Path

DETECTORS = ["none", "fixed_cap", "learned_naive", "learned_capped", "learned_verified"]
BOTS = ["none", "burst", "slow_ramp", "low_and_slow", "mimic"]
SEEDS = range(7, 12)
TOKENS, DAYS, WARMUP = 60, 120, 30
ALPHA, K_SD, GROW, LO, HI = 0.10, 4.0, 1.03, 0.5, 4.0
FIXED_X = 3.0


def _noisy(rng, mu):
    return max(0, round(rng.gauss(mu, math.sqrt(max(mu, 1.0)))))


def _bot_extra(kind, k, mu, owner):
    """Calls the bot adds on its k-th day holding the token, and the share of the owner's own volume it takes."""
    if kind == "burst":
        return 9.0 * mu, 0.0
    if kind == "slow_ramp":
        return mu * (min(10.0, 1.08 ** k) - 1.0), 0.0
    if kind == "low_and_slow":
        return 0.5 * mu, 0.0
    if kind == "mimic":
        return 0.0, 0.30
    return 0.0, 0.0


def run(detector: str, bot: str, seed: int, act: bool) -> dict:
    rng = random.Random(seed)
    mus = [max(8.0, rng.lognormvariate(math.log(40), 0.6)) for _ in range(TOKENS)]
    held = {i for i in range(TOKENS) if bot != "none" and rng.random() < 0.20}
    burst_day = {i: rng.randrange(35, 100) for i in range(TOKENS) if rng.random() < 0.15}
    migrate_day = {i: rng.randrange(40, 80) for i in range(TOKENS) if rng.random() < 0.15}
    mean, var = list(mus), [m for m in mus]                                # learned state, started from the day-zero calibration
    bot_start = WARMUP
    alive = set(held)
    first_alert = {}
    false_alerts = interruptions = bot_calls = alerts_total = 0
    token_days = 0
    for day in range(DAYS):
        for i in range(TOKENS):
            mu = mus[i]
            f = 1.0
            if i in burst_day and burst_day[i] <= day < burst_day[i] + 4:
                f = 4.0
            if i in migrate_day and day >= migrate_day[i]:
                f = max(f, 3.0)
            owner = _noisy(rng, mu * f)
            extra = take = 0.0
            on_bot = i in alive and day >= bot_start
            if on_bot:
                extra, take = _bot_extra(bot, day - bot_start, mu, owner)
            total = max(0, round(owner + extra + 0.0))
            seen = total                                                    # a taken share leaves the total unchanged
            bcalls = round(extra + take * owner)
            if on_bot:
                bot_calls += bcalls
            token_days += 1
            alert = False
            if detector == "fixed_cap":
                alert = seen > FIXED_X * mus[i]
            elif detector in ("learned_naive", "learned_capped", "learned_verified"):
                sd = max(math.sqrt(var[i]), math.sqrt(max(mean[i], 1.0)))
                alert = seen > mean[i] + K_SD * sd
                if detector != "learned_verified" or not alert:
                    new_mean = (1 - ALPHA) * mean[i] + ALPHA * seen
                    if detector != "learned_naive":
                        new_mean = min(new_mean, mean[i] * GROW)
                        new_mean = min(max(new_mean, LO * mus[i]), HI * mus[i])
                    var[i] = (1 - ALPHA) * var[i] + ALPHA * (seen - mean[i]) ** 2
                    if detector != "learned_naive":
                        var[i] = min(max(var[i], mus[i]), 4 * mus[i])            # the spread is poisoned too: bound it, or the alarm line runs away
                    mean[i] = new_mean
            if alert:
                alerts_total += 1
                if on_bot and f == 1.0:                                      # the bot is working and the owner has not changed: a true alert
                    first_alert.setdefault(i, day - bot_start)
                else:
                    false_alerts += 1
                if act:
                    interruptions += 1                                       # a rotation interrupts the owner, right or wrong
                    alive.discard(i)
    ratio = [mean[i] / mus[i] for i in held] if held and detector.startswith("learned") else []
    return {"bot_tokens": len(held), "detected": len(first_alert), "days_to_alert_sum": sum(first_alert.values()), "false_alerts": false_alerts,
            "interruptions": interruptions, "bot_calls": bot_calls, "token_days": token_days, "baseline_ratio_sum": sum(ratio), "baseline_ratio_n": len(ratio)}


def compare(seeds=SEEDS) -> dict:
    out = {}
    for bot in BOTS:
        rows = []
        for det in DETECTORS:
            for act in (False, True):
                if det == "none" and act:
                    continue
                agg = {}
                for s in seeds:
                    for k, v in run(det, bot, s, act).items():
                        agg[k] = agg.get(k, 0) + v
                rows.append({"detector": det, "mode": "authority" if act else "advisor",
                             "detected_pct": round(100 * agg["detected"] / agg["bot_tokens"]) if agg["bot_tokens"] else None,
                             "avg_days_to_alert": round(agg["days_to_alert_sum"] / agg["detected"], 1) if agg["detected"] else None,
                             "false_alerts_per_1000_token_days": round(1000 * agg["false_alerts"] / agg["token_days"], 1),
                             "owner_interruptions": agg["interruptions"] if act else None,
                             "bot_calls": agg["bot_calls"] if act or det == "none" else None,
                             "baseline_vs_truth": round(agg["baseline_ratio_sum"] / agg["baseline_ratio_n"], 2) if agg["baseline_ratio_n"] else None,
                             "bot_tokens": agg["bot_tokens"]})
        out[bot] = rows
    return out


def format_table(rows) -> str:
    cols = [("detector", "detector"), ("mode", "mode"), ("detected_pct", "bot tokens caught %"), ("avg_days_to_alert", "avg days to alert"),
            ("false_alerts_per_1000_token_days", "false alerts /1000 token-days"), ("owner_interruptions", "owner interrupted"), ("bot_calls", "bot calls"),
            ("baseline_vs_truth", "baseline / truth")]
    cell = lambda v: "-" if v is None else str(v)
    w = [max(len(h), *(len(cell(r[k])) for r in rows)) for k, h in cols]
    line = lambda vals: "  ".join(v.ljust(w[i]) if i < 2 else v.rjust(w[i]) for i, v in enumerate(vals))
    return "\n".join([line([h for _, h in cols]), line(["-" * x for x in w])] + [line([cell(r[k]) for k, _ in cols]) for r in rows])


def main():
    print("Scripted and synthetic: 60 tokens, 120 days, five seeds, a bot with a foothold inside the owner's network. Not a measurement of any real system.\n")
    for bot, rows in compare().items():
        print(f"Bot: {bot}")
        print(format_table(rows) + "\n")


if __name__ == "__main__":
    main()
