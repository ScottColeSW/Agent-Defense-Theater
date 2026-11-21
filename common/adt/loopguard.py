"""Live runtime duplicate tool-loop detector (non-mutating observer for DecisionLog).

Implements the empirical detection rule established in docs/LOG-AUDIT-FINDINGS.md (issue #12):
  1. Non-harness agent actor (actor != "harness")
  2. Recorded, non-empty canonicalized tool arguments (saw["args"])
  3. Contiguous identical (action, canonical_args) where the immediately preceding call had verdict == "allow"

Designed as a zero-overhead, read-only observer that never alters DecisionLog entries or hash chains.
"""
import json
from dataclasses import dataclass, field
from typing import Callable, Optional


def canonical_args(saw: Optional[dict]) -> Optional[str]:
    """Return canonical JSON string of saw['args'] when present and non-empty, else None."""
    if not isinstance(saw, dict) or "args" not in saw:
        return None
    args = saw["args"]
    if args is None or args == {} or args == []:
        return None
    return json.dumps(args, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


@dataclass
class LoopAlert:
    seq: int
    prev_seq: int
    actor: str
    action: str
    args_json: str
    prev_verdict: str
    verdict: str
    streak: int
    context: dict = field(default_factory=dict)


class RuntimeLoopDetector:
    """Tracks per-actor contiguous tool calls in memory and flags duplicate-allow replays."""

    def __init__(self, on_alert: Optional[Callable[[LoopAlert], None]] = None):
        self.on_alert = on_alert
        self._last_by_actor: dict[str, dict] = {}
        self.alerts: list[LoopAlert] = []
        self.total_observed: int = 0

    def reset(self) -> None:
        """Reset state between independent cases or runs."""
        self._last_by_actor.clear()
        self.alerts.clear()
        self.total_observed = 0

    def observe(self, entry: dict, context: Optional[dict] = None) -> Optional[LoopAlert]:
        """Inspect a finalized DecisionLog entry without mutating it."""
        self.total_observed += 1
        actor = entry.get("actor", "")
        if not actor or actor == "harness":
            return None

        action = entry.get("action", "")
        verdict = entry.get("verdict", "")
        seq = int(entry.get("seq", self.total_observed))
        c_args = canonical_args(entry.get("saw"))

        prev = self._last_by_actor.get(actor)
        alert: Optional[LoopAlert] = None

        if (
            c_args is not None
            and prev is not None
            and prev["action"] == action
            and prev["args_json"] == c_args
        ):
            streak = prev["streak"] + 1
            if prev["verdict"] == "allow":
                alert = LoopAlert(
                    seq=seq,
                    prev_seq=prev["seq"],
                    actor=actor,
                    action=action,
                    args_json=c_args,
                    prev_verdict=prev["verdict"],
                    verdict=verdict,
                    streak=streak,
                    context=dict(context) if context else {},
                )
                self.alerts.append(alert)
                if self.on_alert is not None:
                    self.on_alert(alert)
        else:
            streak = 1

        self._last_by_actor[actor] = {
            "seq": seq,
            "action": action,
            "args_json": c_args,
            "verdict": verdict,
            "streak": streak,
        }
        return alert
