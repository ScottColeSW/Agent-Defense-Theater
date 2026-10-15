"""Detailed report for one saved run: summary, breakdowns, latency split, integrity, predictions, pass bar and the reviewer's decisions."""
import json
import tempfile
from pathlib import Path

from . import decisionlog, glance, governance, scorer, tempo
from .loader import ITEMS, experiments, item_folder, load_scenario

DEFAULT_LABELS = {"success": "Attack succeeded", "valid": "Valid work done", "success_axis": "attacks that got through (lower is better)",
                  "valid_axis": "valid work completed (higher is better)"}
LABELS = {
    "result": "Preregistered live run. The prediction was committed before it ran, so it counts as a result.",
    "exploratory": "Exploratory live run. No committed prediction, so it is not a result.",
    "scripted": "Scripted run. Human-written replies that illustrate a mechanism. It is never a result.",
}
RECORD_FIELDS = ["model", "defense", "attack", "tier", "task", "ticket", "outcome", "calls", "holds", "holds_approved", "model_ms",
                 "review_ms", "gate_ms", "thermal_wait_ms", "gpu_temp_c", "tokens_in", "tokens_out", "thinking_chars", "model_error", "attempted", "exceeds_tier"]


def _kind(path: Path) -> str:
    if path.name.endswith("-scripted.jsonl"):
        return "scripted"
    return "result" if path.name.endswith("-prereg.jsonl") else "exploratory"


def _files():
    for p in sorted(ITEMS.glob("asi*-*/results/*.jsonl")):
        if ".decisions" not in p.name:
            yield p
    base = Path(tempfile.gettempdir()) / "adt"
    for p in sorted(base.glob("asi*-*/*/*.jsonl")):
        if ".decisions" not in p.name:
            yield p


def find_run(run_id: str):
    return next((p for p in _files() if p.stem == run_id), None)


def _meta(path: Path) -> dict:
    m = path.with_name(path.name.replace(".jsonl", ".meta.json"))
    return json.loads(m.read_text(encoding="utf-8")) if m.exists() else {}


def list_reports() -> list:
    out = []
    for p in _files():
        m = _meta(p)
        if not m:
            continue                       # an unfinished run has no metadata and is not a report
        out.append({"run_id": m["run_id"], "item": m["item"], "experiment": m.get("experiment", "first-run"), "kind": _kind(p),
                    "models": m.get("models", []), "records": m.get("records"), "seconds": m.get("seconds"), "started": m.get("started"),
                    "gpu": m.get("gpu"), "label": LABELS[_kind(p)]})
    return sorted(out, key=lambda r: r["started"] or "", reverse=True)


def _plain(rows: list) -> list:
    for r in rows:
        for v in r.values():
            if isinstance(v, dict) and "ci" in v:
                v["ci"] = list(v["ci"])
    return rows


def build_report(run_id: str, records: bool = True):
    path = find_run(run_id)
    if not path:
        return None
    meta, kind = _meta(path), _kind(path)
    recs = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    live = [r for r in recs if r.get("mode") == "live"]
    scored = live if kind != "scripted" else recs
    log_path = path.with_name(path.name.replace(".jsonl", ".decisions.jsonl"))
    ver = decisionlog.verify(log_path) if log_path.exists() else None
    log = [json.loads(l) for l in log_path.read_text(encoding="utf-8").splitlines() if l.strip()] if log_path.exists() else []
    reviews = [{"defense": e["saw"].get("defense"), "case": e["saw"].get("case"), "verdict": e["verdict"], "reason": e["reason"], "card": e["saw"].get("card", "")}
               for e in log if e["actor"].startswith("approver:")]
    by = lambda keys: _plain(scorer.summarize(scored, keys))
    rows = by(("defense",))
    gpu_path = path.with_name(path.name.replace(".jsonl", ".gpu.json"))
    temps = [r["gpu_temp_c"] for r in recs if "gpu_temp_c" in r]
    item, exp = meta.get("item", "").lower(), meta.get("experiment", "first-run")
    sc = load_scenario(item, exp) if exp in experiments(item) else None
    ctx = {"reviews": len(reviews), "unparseable": sum(1 for r in reviews if "unparseable" in r["reason"] or "unavailable" in r["reason"]), "records": scored}
    think_path = path.with_name(path.name.replace(".jsonl", ".thinking.jsonl"))
    thinking = [json.loads(l) for l in think_path.read_text(encoding="utf-8").splitlines()[:400] if l.strip()] if think_path.exists() else []
    out = {
        "run_id": run_id, "item": meta.get("item"), "folder": item_folder(item).name, "experiment": exp, "kind": kind, "label": LABELS[kind], "meta": meta,
        "title": getattr(sc, "title", run_id) if sc else run_id,
        "integrity": None if not ver else {"ok": ver.ok, "entries": ver.entries, "head": ver.head, "recorded_head": meta.get("decision_log_head"),
                                           "matches_recorded": ver.head == meta.get("decision_log_head"), "reason": ver.reason, "first_bad": ver.first_bad},
        "summary": rows, "by_tier": by(("defense", "tier")), "by_attack": by(("defense", "attack")), "by_model": by(("defense", "model")),
        "by_task": by(("defense", "task")),
        "attack_tiers": [{"name": n, "tier": t} for n, t in sorted({(r["attack"], r["tier"]) for r in recs if r["attack"] != "none"},
                                                                    key=lambda x: ["loud", "quiet", "adaptive"].index(x[1]))],
        "reviewer": {d: {"approve": sum(1 for r in reviews if r["defense"] == d and r["verdict"] == "approve"),
                         "deny": sum(1 for r in reviews if r["defense"] == d and r["verdict"] == "deny")} for d in sorted({r["defense"] for r in reviews})},
        "reviews": reviews[:800], "reviews_total": len(reviews),
        "errors": [{"model": r["model"], "defense": r["defense"], "attack": r["attack"], "task": r["task"], "error": r["model_error"]} for r in recs if r.get("model_error")],
        "gpu": json.loads(gpu_path.read_text(encoding="utf-8")) if gpu_path.exists() else None,
        "gpu_temp_range": [min(temps), max(temps)] if temps else None,
        "prediction": getattr(sc, "predictions", None) if (sc and kind == "result") else None,
        "pass_bar": sc.pass_bar(rows, ctx) if (sc and kind == "result" and hasattr(sc, "pass_bar") and rows) else None,
        "hardware_note": meta.get("hardware_note"),
        "labels": {**DEFAULT_LABELS, **(getattr(sc, "labels", None) or {})} if sc else DEFAULT_LABELS,
        "analysis": sc.analyze(scored) if (sc and hasattr(sc, "analyze") and scored) else [],
        "thinking": [{**t, "thinking": t["thinking"][:1500]} for t in thinking[:60]], "thinking_total": len(thinking),
    }
    out["governance"] = governance.view(item, exp, out["pass_bar"])
    out["tempo"] = tempo.tempo(scored) if scored else None
    out["surfaces"] = tempo.surfaces(scored) if scored else None
    out["glance"] = glance.view(rows, out["surfaces"], out["tempo"], exp, item, scored) if kind in ("result", "exploratory") else None
    if out["gpu"]:
        s = out["gpu"]["samples"]
        out["gpu"]["samples"] = s[::max(1, len(s) // 600)]
    if records:
        out["records"] = {"fields": RECORD_FIELDS, "rows": [[r.get(f) for f in RECORD_FIELDS] for r in recs]}
    return out
