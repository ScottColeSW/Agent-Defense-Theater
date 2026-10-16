"""Result records. The contract is common/RESULTS-SCHEMA.md."""
from datetime import datetime, timezone

OUTCOMES = {"attack_succeeded", "blocked", "task_succeeded", "task_failed", "flagged"}
TIERS = {"loud", "quiet", "adaptive", "blind", "n/a"}       # blind: written by a model that was never told about a defense
LAYERS = {"prevent", "detect", "contain", "none"}
MODES = {"live", "scripted"}

# field -> type(s). Extra fields are allowed and kept.
BASE = {
    "run_id": str, "item": str, "tier": str, "attack": str, "defense": str, "layer": str,
    "model": str, "crew": str, "outcome": str, "tokens_in": int, "tokens_out": int,
    "latency_ms": int, "mode": str, "prereg": str, "hardware_note": str, "timestamp": str,
}


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def validate(rec: dict) -> list:
    """Return a list of problems. An empty list means the record is valid."""
    errs = [f"missing {k}" for k in BASE if k not in rec]
    for k, t in BASE.items():
        if k in rec and not isinstance(rec[k], t):
            errs.append(f"{k} should be {t.__name__}")
    if rec.get("outcome") not in OUTCOMES:
        errs.append(f"outcome {rec.get('outcome')!r} not in {sorted(OUTCOMES)}")
    if rec.get("tier") not in TIERS:
        errs.append(f"tier {rec.get('tier')!r} not in {sorted(TIERS)}")
    if rec.get("layer") not in LAYERS:
        errs.append(f"layer {rec.get('layer')!r} not in {sorted(LAYERS)}")
    if rec.get("mode") not in MODES:
        errs.append(f"mode {rec.get('mode')!r} not in {sorted(MODES)}")
    return errs
