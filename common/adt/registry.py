"""The list of runnable tests: every experiment of every built item. The runner UI and the CLI read the same list."""
import time

from . import harness
from .loader import ITEMS, ROOT, experiments, load_scenario, results_dir

_cache = {"at": 0.0, "tests": None}
TTL_S = 5.0          # check_prereg shells out to git, so do not do it on every request


def get_scenario(test_id: str):
    item, _, exp = test_id.partition("/")
    return load_scenario(item, exp or None)


def _last_result(item: str, exp: str):
    import json
    best = None
    for m in sorted(results_dir(item).glob("*-prereg.meta.json")):
        meta = json.loads(m.read_text(encoding="utf-8"))
        if meta.get("experiment", "first-run") == exp:
            best = meta
    return best and {k: best[k] for k in ("run_id", "records", "seconds", "started", "models") if k in best}


def list_tests(refresh: bool = False) -> list:
    if not refresh and _cache["tests"] is not None and time.time() - _cache["at"] < TTL_S:
        return _cache["tests"]
    out = []
    for folder in sorted(ITEMS.glob("asi*-*")):
        item = folder.name.split("-")[0]
        for exp in experiments(item):
            sc = load_scenario(item, exp)
            cases = sc.cases()
            ready, msg, _ = harness.check_prereg(sc.prereg_path, sc.code_dirs)
            last = _last_result(item, exp)
            out.append({
                "id": f"{item}/{exp}", "item": item.upper(), "folder": folder.name, "experiment": exp,
                "title": getattr(sc, "title", f"{item.upper()} {exp}"), "summary": getattr(sc, "summary", ""),
                "cases": len(cases), "attack_cases": sum(c.kind == "attack" for c in cases), "legit_cases": sum(c.kind == "legit" for c in cases),
                "defenses": [{"name": d.name, "layer": d.layer, "description": d.description} for d in sc.defenses],
                "has_reviewer": hasattr(sc, "configure"), "reviewer_default": getattr(sc, "reviewer_model", None),
                "prereg": {"path": sc.prereg_path.relative_to(ROOT).as_posix(), "ready": ready, "message": "ok" if ready else msg},
                "last_result": last, "live_seconds_estimate": last["seconds"] if last else None,
            })
    _cache.update(at=time.time(), tests=out)
    return out
