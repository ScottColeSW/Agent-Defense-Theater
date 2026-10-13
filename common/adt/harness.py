"""The shared harness: a scenario supplies attacks, defenses and cases; this runs them the same way every time.

Interfaces (see common/README.md):
  Scenario.cases()                      -> list of Case
  Scenario.defenses                     -> list of Defense
  Scenario.run_case(case, defense, runner, log) -> CaseResult
The harness handles models, pairing, scoring inputs, the recorder, the decision log and the preregistration check.
"""
import json
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

from . import gpucooler
from .decisionlog import DecisionLog
from .models import CachedRunner, ModelError, Reply
from .schema import now, validate

ROOT = Path(__file__).resolve().parents[2]
HARDWARE_NOTE = "One workstation, RTX 2080 Super 8 GB. Local models up to 8B parameters."


@dataclass
class Defense:
    name: str
    layer: str          # prevent | detect | contain | none
    description: str


@dataclass
class Case:
    kind: str           # "attack" or "legit"
    attack: str         # attack name, or "none"
    tier: str           # loud | quiet | adaptive | n/a
    task: str
    data: dict = field(default_factory=dict)


@dataclass
class CaseResult:
    outcome: str
    reply: Reply
    extra: dict = field(default_factory=dict)   # merged into the record (attempted, exceeds_tier, ...)
    gate_ms: int = 0


def _git(*args) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True).stdout.strip()


def check_prereg(prereg: Path, code_dirs: list) -> tuple:
    """A live result needs a prediction committed before the run, and code that matches a commit.
    Returns (ok, message, info)."""
    rel = prereg.relative_to(ROOT).as_posix()
    if not prereg.exists() or not _git("log", "-1", "--format=%H", "--", rel):
        return False, f"{rel} is not committed. Commit the prediction before the first run.", {}
    if _git("status", "--porcelain", "--", rel):
        return False, f"{rel} has uncommitted edits. Add an addendum after the run instead of editing the prediction.", {}
    dirty = _git("status", "--porcelain", "--", *[d.relative_to(ROOT).as_posix() + "/" for d in code_dirs
                                                  if d.exists()], ":(exclude)*/results/*")
    if dirty:
        return False, "Harness or item code has uncommitted changes, so the run could not be reproduced:\n" + dirty, {}
    return True, "ok", {"prereg_commit": _git("log", "-1", "--format=%H", "--", rel), "harness_commit": _git("rev-parse", "HEAD")}


def run(scenario, runners: list, out_dir: Path, mode: str = "live", exploratory: bool = False,
        defenses: list = None, progress=print) -> dict:
    """Run every case against every defense and model. Writes <run_id>.jsonl, a decision log and <run_id>.meta.json."""
    out_dir = Path(out_dir)
    tag = "scripted" if mode == "scripted" else ("exploratory" if exploratory else "prereg")
    exp = getattr(scenario, "experiment", "first-run")
    run_id = f"{scenario.item.lower()}-{exp}-{time.strftime('%Y%m%dT%H%M%S', time.gmtime())}-{tag}"
    out_dir.mkdir(parents=True, exist_ok=True)
    rec_path, log = out_dir / f"{run_id}.jsonl", DecisionLog(out_dir / f"{run_id}.decisions.jsonl")
    cases, defs = scenario.cases(), defenses or scenario.defenses
    info = {}
    if mode == "live" and not exploratory:
        ok, msg, info = check_prereg(scenario.prereg_path, scenario.code_dirs)
        if not ok:
            raise SystemExit("Refusing a live run without a committed prediction (use --exploratory to run anyway, labeled as such).\n" + msg)
    prereg = scenario.prereg_path.relative_to(ROOT).as_posix() if (mode == "live" and not exploratory) else ""
    t_start, n = time.time(), 0
    total = len(cases) * len(defs) * len(runners)
    defense_major = getattr(scenario, "order", "case-major") == "defense-major"
    pairs = [(c, d) for d in defs for c in cases] if defense_major else [(c, d) for c in cases for d in defs]
    with rec_path.open("w", encoding="utf-8") as f:
        for runner in runners:
            cr = CachedRunner(runner) if mode == "live" else runner
            for i, (case, d) in enumerate(pairs, 1):
                try:
                    res = scenario.run_case(case, d, cr, log)
                except ModelError as e:
                    # Counted, never hidden: a failed model call is a failed case, flagged so reports can show how many.
                    res = CaseResult("task_failed", Reply("", 0, 0, 0), {"model_error": str(e)[:200], "attempted": False, "exceeds_tier": False,
                                                                        "calls": 0, "denied": 0, "tier_ok": case.data.get("tier_ok", True)})
                    log.append(actor="harness", tier="n/a", delegation=[], action="model call", verdict="error", reason=str(e)[:200],
                               saw={"model": runner.name, "defense": d.name, "case": f"{case.attack}/{case.task}"})
                rec = {"run_id": run_id, "item": scenario.item, "tier": case.tier, "attack": case.attack,
                       "defense": d.name, "layer": d.layer, "model": runner.name, "crew": scenario.crew,
                       "outcome": res.outcome, "tokens_in": res.reply.tokens_in, "tokens_out": res.reply.tokens_out,
                       "latency_ms": res.reply.latency_ms + res.gate_ms, "mode": mode, "prereg": prereg,
                       "hardware_note": HARDWARE_NOTE, "timestamp": now(), "task": case.task,
                       # latency_ms = model_ms + review_ms + gate_ms. thermal_wait_ms is outside all three.
                       "model_ms": res.reply.latency_ms - res.extra.get("review_ms", 0), "review_ms": res.extra.get("review_ms", 0),
                       "gate_ms": res.gate_ms, **res.extra, **gpucooler.snapshot()}
                bad = validate(rec)
                if bad:
                    raise ValueError(f"invalid record: {bad}")
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                f.flush()
                n += 1
                if progress and (i % 25 == 0 or i == len(pairs)):
                    progress(f"  {runner.name}: {i}/{len(pairs)} ({n}/{total} records)")
    meta = {"run_id": run_id, "item": scenario.item, "experiment": exp, "mode": mode, "exploratory": exploratory, "models": [r.name for r in runners],
            "defenses": [d.name for d in defs], "cases": len(cases), "records": n, "seconds": round(time.time() - t_start, 1),
            "decision_log_head": log.head, "decision_log_entries": log.seq, "hardware_note": HARDWARE_NOTE, **info,
            "gpu": gpucooler.active.stats() if gpucooler.active else None,
            "started": now()}
    if gpucooler.active:
        (out_dir / f"{run_id}.gpu.json").write_text(json.dumps(gpucooler.active.timeline()), encoding="utf-8")
    (out_dir / f"{run_id}.meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    return meta
