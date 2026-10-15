"""Tempo and threat surfaces for a report, computed from the saved records of a run.

Tempo: how long a case takes from the agent being given the task (with the planted instruction already in what it reads) to an unsafe call
being carried out, and how long each defense takes to decide, set against the agent's own time. It is the machine side of the clock only.
People are not modeled: a hold that would wait for a person here goes to a model or a rule and is decided in about a second or less.

Threat surfaces: crosswalk/threat-surfaces.json groups the planted attacks by the author's classification of their primary mechanism.
"""
import json
import statistics

from .loader import ROOT

SURFACES = ROOT / "crosswalk" / "threat-surfaces.json"


def _ms(r, k):
    v = r.get(k) or 0
    return v if isinstance(v, (int, float)) else 0


def case_ms(r) -> int:
    """Everything before an action could happen or be refused: the agent, any reviewer, our gate and the tool servers. The GPU cooler's wait is not in it."""
    return _ms(r, "model_ms") + _ms(r, "review_ms") + _ms(r, "gate_ms") + _ms(r, "tool_ms")


def tempo(records: list) -> dict:
    """Per-condition mean times, the time to an unsafe call where one was carried out, and what is not modeled."""
    by = {}
    for r in records:
        by.setdefault(r["defense"], []).append(r)
    rows = []
    for d, rs in by.items():
        mean = lambda k: round(sum(_ms(r, k) for r in rs) / len(rs), 1)
        agent, review, gate, tools = mean("model_ms"), mean("review_ms"), mean("gate_ms"), mean("tool_ms")
        decide = review + gate
        rows.append({"defense": d, "agent_ms": agent, "reviewer_ms": review, "gate_ms": gate, "tools_ms": tools, "decide_ms": round(decide, 1),
                     "decide_share": round(decide / (agent + decide), 4) if (agent + decide) else 0, "cases": len(rs)})
    harm = sorted(case_ms(r) for r in records if r.get("outcome") == "attack_succeeded")
    blocked = sorted(case_ms(r) for r in records if r.get("outcome") == "blocked")
    return {
        "rows": rows,
        "to_unsafe_call": {"n": len(harm), "median_ms": round(statistics.median(harm)) if harm else None,
                           "fastest_ms": harm[0] if harm else None, "slowest_ms": harm[-1] if harm else None},
        "to_refusal": {"n": len(blocked), "median_ms": round(statistics.median(blocked)) if blocked else None},
        "holds": sum(r.get("holds") or 0 for r in records),
        "human": "Every hold in this run was decided by a model or a rule, in about a second or less. A real hold waits for a person, "
                 "and that wait would be minutes or hours, far longer than the machine side shown here.",
    }


def surfaces(records: list) -> dict:
    """Attack success by threat surface and condition, over planted-attack records only. Unclassified attack names are counted and left out."""
    data = json.loads(SURFACES.read_text(encoding="utf-8"))
    attacks = [r for r in records if r.get("attack") not in (None, "none")]
    defs = list(dict.fromkeys(r["defense"] for r in attacks))
    cells, names, unclassified = {}, {s: set() for s in data["surfaces"]}, set()
    for r in attacks:
        s = data["attacks"].get(r["attack"])
        if s is None:
            unclassified.add(r["attack"])
            continue
        names[s].add(r["attack"])
        c = cells.setdefault((s, r["defense"]), [0, 0])
        c[0] += r["outcome"] == "attack_succeeded"
        c[1] += 1
    rows = [{"id": s, "label": meta["label"], "what": meta["what"], "attacks": sorted(names[s]),
             "cells": {d: {"k": cells[(s, d)][0], "n": cells[(s, d)][1]} for d in defs if (s, d) in cells}}
            for s, meta in data["surfaces"].items() if names[s]]
    listed = set().union(*names.values()) if names else set()
    return {"rows": rows, "defenses": defs, "unclassified": sorted(unclassified), "note": data["note"],
            "why": {a: w for a, w in data["why"].items() if a in listed}}
