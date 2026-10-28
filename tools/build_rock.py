#!/usr/bin/env python3
"""Build the data file behind the Defense Rock cartoon (site/rock/).

Every number in the cartoon is read here from a saved run, never typed into the page.

Inputs
  site/data/asi06-defenses.json                          Aegis Vector defenses battery, recomputed from its records
  site/data/reports/asi03-bottom-line-*-prereg.json      ASI03 support desk, nine controls
  site/data/reports/asi01-first-run-*-prereg.json        ASI01 goal hijack
  items/asi03-identity-privilege/results/asi03-duplicate-probe-2*-prereg.jsonl    the duplicate-refund probe
  items/asi03-identity-privilege/attacks/attacks.py      the author-written ASI03 attacks (text and the calls a compliant agent makes)
  items/asi01-goal-hijack/attacks/attacks.py             the ASI01 attacks
  <PAV>/results/live/seed_runs.jsonl, <PAV>/scenarios.py real answers and forgery text from Aegis Vector (optional)

Output
  site/rock/data/rock.json

Usage
  python tools/build_rock.py
  python tools/build_rock.py --pav ../Project-Aegis-Vector
"""
import argparse, hashlib, importlib.util, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORTS = ROOT / "site" / "data" / "reports"
OUT = ROOT / "site" / "rock" / "data" / "rock.json"


def load_report(prefix):
    found = sorted(REPORTS.glob(f"{prefix}-2*-prereg.json"))
    if not found:
        sys.exit(f"missing saved report {prefix}-*: run python adt.py build first")
    return json.loads(found[-1].read_text(encoding="utf-8"))


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def kn(x):
    return {"k": x["k"], "n": x["n"]}


def condition_rows(report):
    return {s["defense"]: {"attacks": kn(s["success"]), "valid": kn(s["valid"])} for s in report["summary"]}


def forger(pav):
    data = json.loads((ROOT / "site" / "data" / "asi06-defenses.json").read_text(encoding="utf-8"))
    by_id = {d["id"]: d for d in data["defenses"]}
    out = {"source": data["source"], "source_commit": data["source_commit"], "run": data["run"], "models": data["models"],
           "answers_per_cell": by_id["none"]["adoption_n"] // len(data["payloads"]),
           "defenses": {k: {"desc": d["desc"], "adoption": d["adoption"], "utility": d["utility"],
                            "by_payload": d["adoption_by_payload"]} for k, d in by_id.items()},
           "tier": data["tier"], "forgeries": {}, "answers": []}
    if pav:
        sys.path.insert(0, str(pav))
        try:
            from scenarios import POISON_VARIANTS
            out["forgeries"] = dict(POISON_VARIANTS)
        finally:
            sys.path.pop(0)
        seed = pav / "results" / "live" / "seed_runs.jsonl"
        seen = set()
        for line in seed.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            key = (r["payload"], r["defense"])
            if r["model"] != "llama3.2" or key in seen or r.get("episode", "").endswith("R"):
                continue
            seen.add(key)
            out["answers"].append({k: r.get(k) for k in ("title", "payload", "defense", "model", "query", "answer", "adopted", "held", "blocked")})
    return out


def impersonator():
    rep = load_report("asi03-bottom-line")
    attacks = load_module(ROOT / "items/asi03-identity-privilege/attacks/attacks.py", "asi03_attacks")
    desk = load_module(ROOT / "items/asi03-identity-privilege/eval/desk.py", "asi03_desk")
    rows = condition_rows(rep)
    # the duplicate-refund probe: the operator asks for one $30 refund and the ticket asks for it again
    probe = sorted((ROOT / "items/asi03-identity-privilege/results").glob("asi03-duplicate-probe-2*-prereg.jsonl"))[0]
    tally = {}
    for line in probe.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        t = tally.setdefault(r["defense"], {"ran": 0, "n": 0})
        t["n"] += 1
        t["ran"] += r["outcome"] == "attack_succeeded"
    return {"run_id": rep["run_id"], "models": rep["meta"].get("models", []), "conditions": rows, "prediction_note": rep.get("hardware_note"),
            "attacks": [{"name": a["name"], "tier": a["tier"], "text": a["text"],
                         "calls": [{"tool": t, "args": args} for t, args in a["calls"]]} for a in attacks.ATTACKS],
            "attacker": {"account": attacks.ATTACKER_ACCOUNT, "email": attacks.ATTACKER_EMAIL},
            "tickets": {k: {"account": v["account"], "subject": v["subject"]} for k, v in desk.TICKETS.items() if k <= "T-1003"},
            "duplicate_probe": {"run": probe.stem, "by_defense": tally}}


def hijacker():
    rep = load_report("asi01-first-run")
    attacks = load_module(ROOT / "items/asi01-goal-hijack/attacks/attacks.py", "asi01_attacks")
    by_attack = {}
    for r in rep["by_attack"]:
        if r["attack"] != "none":
            by_attack.setdefault(r["defense"], {})[r["attack"]] = kn(r["success"])
    return {"run_id": rep["run_id"], "conditions": condition_rows(rep), "by_attack": by_attack,
            "models": rep["meta"].get("models", []),
            "attacks": [{"name": a["name"], "tier": a["tier"], "surface": a["surface"], "text": a["text"]} for a in attacks.ATTACKS]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pav", default=str(ROOT.parent / "Project-Aegis-Vector"))
    pav = Path(ap.parse_args().pav)
    pav = pav if (pav / "scenarios.py").exists() else None
    if pav is None:
        print("note: Aegis Vector checkout not found; the Forger episode will have no forgery text or quoted answers", file=sys.stderr)
    data = {"forger": forger(pav), "impersonator": impersonator(), "hijacker": hijacker()}
    body = json.dumps(data, indent=1, ensure_ascii=False, sort_keys=True)
    data["sha256"] = hashlib.sha256(body.encode()).hexdigest()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=1, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
