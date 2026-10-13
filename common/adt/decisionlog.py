"""Tamper-evident decision log: a hash chain, one JSON line per decision.

Each entry holds the hash of the previous entry, so editing or deleting history breaks
the chain at that point. This shows tampering after the fact. It does not prevent it,
and a writer with full control can rebuild the whole chain; see common/decision-log/.
"""
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from .schema import now

GENESIS = "0" * 64


def _digest(entry: dict) -> str:
    body = {k: v for k, v in entry.items() if k != "hash"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


class DecisionLog:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.seq, self.prev = 0, GENESIS
        if self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    e = json.loads(line)
                    self.seq, self.prev = e["seq"], e["hash"]

    def append(self, *, actor: str, tier: str, delegation: list, action: str, saw: dict, verdict: str, reason: str) -> dict:
        self.seq += 1
        entry = {"seq": self.seq, "ts": now(), "actor": actor, "tier": tier, "delegation": delegation,
                 "action": action, "saw": saw, "verdict": verdict, "reason": reason, "prev": self.prev}
        entry["hash"] = _digest(entry)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        self.prev = entry["hash"]
        return entry

    @property
    def head(self) -> str:
        """The hash to anchor somewhere else (a commit message, a signed note) to catch a rebuilt chain."""
        return self.prev


@dataclass
class Verification:
    ok: bool
    entries: int
    head: str
    first_bad: int = 0
    reason: str = ""


def verify(path) -> Verification:
    path = Path(path)
    prev, n = GENESIS, 0
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            return Verification(False, n, prev, i, "line is not valid JSON")
        if e.get("seq") != n + 1:
            return Verification(False, n, prev, i, f"sequence jumps from {n} to {e.get('seq')} (entry removed or reordered)")
        if e.get("prev") != prev:
            return Verification(False, n, prev, e["seq"], "prev hash does not match the entry before it")
        if _digest(e) != e.get("hash"):
            return Verification(False, n, prev, e["seq"], "entry contents do not match its hash (edited)")
        prev, n = e["hash"], n + 1
    return Verification(True, n, prev)
