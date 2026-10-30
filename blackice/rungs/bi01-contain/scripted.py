"""Black ICE, rung 2 (contain), first test, scripted run: containment under spoofed alarms.

Scripted and synthetic. The fleet, the bot and the spoofer are written by the author, so this shows the trade-offs under those
assumptions. It is not a measurement of any real system and never counts as a result. The model Warden conditions in FIRST-RUNG.md
are not here: a scripted stand-in for a model would only be the rule again. They need a live, preregistered run.

Question: an automatic quarantine stops a thief the moment it is noticed, and gives an attacker a lever. Forge the signal and the
defense quarantines the owner's tokens. Which policies keep the bot out without letting a spoofer lock out legitimate work?

Usage
  python blackice/rungs/bi01-contain/scripted.py
"""
import hashlib
import hmac
import random
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "common"))
from adt import loosekeys as lk  # noqa: E402

LOCATIONS = 6              # where tokens are kept; a canary is planted in each
WINDOW = 3                 # days within which two signals count as the same incident
CONDITIONS = [
    dict(name="no containment", mode=None),
    dict(name="one signal quarantines", mode="single"),
    dict(name="two signals required", mode="corroborated"),
    dict(name="two signals, gateway-signed", mode="corroborated", signed=True),
]
ATTACKS = ["none", "loud", "quiet", "adaptive"]
SEEDS = range(7, 12)


def run(cond: dict, attack: str, seed: int, days: int = 90, grants: int = 120) -> dict:
    rng, brng, srng = random.Random(seed), random.Random(seed + 1), random.Random(seed + 2)
    fleet = lk._fleet(rng, grants)
    for g in fleet:
        g["loc"] = g["i"] % LOCATIONS
        g["uses"] = {d for d in g["uses"] if d < days}
    state = {g["i"]: {"q": False, "bot_first": None, "contained": None, "ever_bot": False} for g in fleet}
    key = secrets.token_bytes(16)                                      # held by the gateway only

    def signed(kind, subject, day):
        return {"kind": kind, "subject": subject, "day": day, "sig": hmac.new(key, f"{kind}|{subject}|{day}".encode(), hashlib.sha256).hexdigest()}

    def forged(kind, subject, day):
        return {"kind": kind, "subject": subject, "day": day, "sig": secrets.token_hex(32)}       # the spoofer cannot sign

    def valid(e):
        good = hmac.new(key, f"{e['kind']}|{e['subject']}|{e['day']}".encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(good, e["sig"])

    seen_new, seen_canary = {}, {}                                     # token -> last day, location -> last day
    bot_ok = interrupted = false_q = ignored = spoof_events = benign = 0
    leaked_locs = {g["loc"] for g in fleet if g["leaked"]}
    leaked = [g for g in fleet if g["leaked"]]
    mode = cond["mode"]

    def quarantine(i, day):
        st = state[i]
        if st["q"]:
            return
        st["q"] = True
        if not st["ever_bot"]:
            nonlocal false_q
            false_q += 1                                               # no bot has touched this token: the owner is being hit
        elif st["contained"] is None and st["bot_first"] is not None:
            st["contained"] = day - st["bot_first"]

    for day in range(days):
        events = []
        # the owner's workloads
        for g in fleet:
            if day in g["uses"]:
                st = state[g["i"]]
                if st["q"]:
                    interrupted += 1                                   # one refused call, then the owner restores it from its own network
                    st["q"] = False
                elif rng.random() < 0.02:
                    benign += 1                                        # honest use from a new office: a real, harmless alarm
                    events.append(signed("new_source", g["i"], day))
        # the bot: three attempts a day on leaked tokens, and now and then the canary it harvested with them
        for _ in range(3 if leaked else 0):
            g = brng.choice(leaked)
            st = state[g["i"]]
            if st["q"]:
                continue
            bot_ok += 1
            st["ever_bot"] = True
            if st["bot_first"] is None:
                st["bot_first"] = day
            events.append(signed("new_source", g["i"], day))
        for loc in sorted(leaked_locs):
            if brng.random() < 0.10:
                events.append(signed("canary_hit", loc, day))
        # the spoofer
        if attack == "loud" and day < 10:
            for _ in range(30):
                events.append(forged("canary_hit", srng.randrange(LOCATIONS), day)); spoof_events += 1
        elif attack == "quiet":
            g = srng.choice([g for g in fleet if g["uses"]])
            events.append(forged("new_source", g["i"], day)); spoof_events += 1
        elif attack == "adaptive":
            for _ in range(3):                                         # a plausible pair, shaped to satisfy two-signal corroboration
                g = srng.choice([g for g in fleet if g["uses"]])
                events.append(forged("new_source", g["i"], day)); events.append(forged("canary_hit", g["loc"], day)); spoof_events += 2
        # the Warden
        for e in events:
            if cond.get("signed") and not valid(e):
                ignored += 1
                continue
            (seen_new if e["kind"] == "new_source" else seen_canary)[e["subject"]] = e["day"]
            if mode == "single":
                targets = [e["subject"]] if e["kind"] == "new_source" else [g["i"] for g in fleet if g["loc"] == e["subject"]]
                for i in targets:
                    quarantine(i, day)
            elif mode == "corroborated":
                cand = [e["subject"]] if e["kind"] == "new_source" else [g["i"] for g in fleet if g["loc"] == e["subject"]]
                for i in cand:
                    loc = fleet[i]["loc"]
                    if day - seen_new.get(i, -99) <= WINDOW and day - seen_canary.get(loc, -99) <= WINDOW:
                        quarantine(i, day)
    owned = [i for i, st in state.items() if st["ever_bot"]]
    times = [st["contained"] for st in state.values() if st["contained"] is not None]
    return {"bot_successes": bot_ok, "tokens_owned": len(owned), "never_contained": sum(1 for i in owned if state[i]["contained"] is None),
            "legit_interrupted": interrupted, "false_quarantines": false_q, "forged_ignored": ignored, "spoofed_events": spoof_events,
            "benign_alarms": benign, "days_to_contain_sum": sum(times), "contained_n": len(times)}


def compare(seeds=SEEDS, **kw) -> dict:
    out = {}
    for attack in ATTACKS:
        rows = []
        for cond in CONDITIONS:
            agg = {}
            for s in seeds:
                for k, v in run(cond, attack, s, **kw).items():
                    agg[k] = agg.get(k, 0) + v
            agg["avg_days_to_contain"] = round(agg["days_to_contain_sum"] / agg["contained_n"], 1) if agg["contained_n"] else None
            rows.append({"condition": cond["name"], **agg})
        out[attack] = rows
    return out


def format_table(rows) -> str:
    cols = [("condition", "condition"), ("bot_successes", "bot succeeded"), ("tokens_owned", "tokens owned"), ("never_contained", "never contained"),
            ("avg_days_to_contain", "avg days to contain"), ("legit_interrupted", "legit interrupted"), ("false_quarantines", "owner tokens quarantined"),
            ("forged_ignored", "forged ignored")]
    w = [max(len(h), *(len(str(r[k])) for r in rows)) for k, h in cols]
    line = lambda vals: "  ".join(str(v).ljust(w[i]) if i == 0 else str(v).rjust(w[i]) for i, v in enumerate(vals))
    return "\n".join([line(h for _, h in cols), line("-" * x for x in w)] + [line(r[k] for k, _ in cols) for r in rows])


def main():
    print("Scripted and synthetic: 120 grants, 90 days, five seeds, a scavenger bot and a spoofer. Not a measurement of any real system.\n")
    for attack, rows in compare().items():
        print(f"Spoofer: {attack}")
        print(format_table(rows) + "\n")


if __name__ == "__main__":
    main()
