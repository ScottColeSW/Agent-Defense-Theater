#!/usr/bin/env python3
"""Build the data file behind the Black ICE page (site/blackice.html).

Inputs
  blackice/rungs/bi01-contain/results/bi01-first-run-*-prereg.jsonl   the preregistered live run (the latest one)
  blackice/rungs/bi01-contain/scenario.py                             the committed predictions
  blackice/rungs/bi01-contain/learner.py                              the scripted, synthetic learning-advisor comparison

Output
  site/data/blackice.json

Usage
  python tools/build_blackice.py
"""
import hashlib, importlib.util, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUNG = ROOT / "blackice" / "rungs" / "bi01-contain"
OUT = ROOT / "site" / "data" / "blackice.json"
sys.path.insert(0, str(ROOT / "common"))


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def main():
    from adt.loader import load_scenario
    sc = load_scenario("bi01", "first-run")
    runs = sorted(p for p in (RUNG / "results").glob("bi01-first-run-*-prereg.jsonl"))
    if not runs:
        sys.exit("no preregistered BI01 run found")
    recs = [json.loads(l) for l in runs[-1].read_text(encoding="utf-8").splitlines() if l.strip()]
    meta = json.loads(runs[-1].with_suffix(".meta.json").read_text(encoding="utf-8"))
    defenses = {}
    for d in [x.name for x in sc.defenses]:
        att = [r for r in recs if r["defense"] == d and r["attack"] != "none"]
        val = [r for r in recs if r["defense"] == d and r["attack"] == "none"]
        defenses[d] = {"description": next(x.description for x in sc.defenses if x.name == d),
                       "forged": {"k": sum(r["outcome"] == "attack_succeeded" for r in att), "n": len(att)},
                       "valid": {"k": sum(r["outcome"] == "task_succeeded" for r in val), "n": len(val)},
                       "predicted": {"forged": sc.predictions[d]["attack"], "valid": sc.predictions[d]["utility"]}}
    learner = load(RUNG / "learner.py", "bi01_learner")
    data = {"bi01": {"run_id": meta["run_id"], "models": meta["models"], "records": meta["records"], "defenses": defenses,
                     "prereg": "blackice/rungs/bi01-contain/PREREGISTRATION.md"},
            "learner": {"bots": learner.BOTS, "detectors": learner.DETECTORS, "rows": learner.compare()}}
    body = json.dumps(data, sort_keys=True, indent=1)
    data["sha256"] = hashlib.sha256(body.encode()).hexdigest()
    OUT.write_text(json.dumps(data, sort_keys=True, indent=1), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
