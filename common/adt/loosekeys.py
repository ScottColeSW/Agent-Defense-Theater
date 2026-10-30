"""Loose keys: find tokens that sit unused and exposed, and shrink the window a scavenger has to use them.

Four parts, all defensive and all local (no network, nothing is revoked for you):

  scan      token-shaped strings in files and the environment, reported by fingerprint and a masked preview, never in full
  audit     a grant inventory (what each token is allowed to do, when it was made, when it was last used) checked for
            tokens that were never used, idle, without an expiry, longer-lived than policy, or wider than their use
  canary    fake tokens planted where a scavenger looks. A real client never presents one, so any presentation is an alarm
  simulate  a synthetic fleet and a scripted bot, to compare countermeasures on attacks stopped AND legitimate work kept

The simulation is scripted and synthetic. It shows how the countermeasures trade off under the author's assumptions. It is not a
measurement of any real system and never counts as a result.
"""
import hashlib
import json
import math
import os
import random
import re
import secrets
import string
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ----------------------------------------------------------------------------- finding token-shaped strings

DETECTORS = [
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b")),
    ("github", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{50,})\b")),
    ("slack", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b")),
    ("google_access", re.compile(r"\bya29\.[A-Za-z0-9_-]{20,}")),
    ("google_refresh", re.compile(r"\b1//[A-Za-z0-9_-]{30,}")),
    ("aws_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("llm_api_key", re.compile(r"\bsk-(?:ant-)?[A-Za-z0-9_-]{24,}")),
    ("oauth_field", re.compile(r"""(?ix)["']?\b(access_token|refresh_token|client_secret|id_token)\b["']?\s*[:=]\s*["']?([A-Za-z0-9._~+/=-]{16,})""")),
    ("bearer", re.compile(r"(?i)\bBearer\s+([A-Za-z0-9._~+/=-]{20,})")),
]
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", ".pytest_cache"}
MAX_BYTES = 2_000_000
# where a token sits changes how likely a scavenger is to find it
EXPOSURE = [(re.compile(r"\.(log|out|err)$|history|\.bash_history|\.zsh_history", re.I), "log"),
            (re.compile(r"(^|[\\/])\.env(\.|$)|\.ini$|\.cfg$|\.conf$|\.ya?ml$|\.toml$|\.json$", re.I), "config")]


def fingerprint(token: str) -> str:
    """A stable name for a token that cannot be turned back into it."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]


def mask(token: str) -> str:
    return token[:4] + "..." + f"({len(token)} chars)" if len(token) > 8 else "(short)"


@dataclass
class Finding:
    where: str
    line: int
    kind: str
    fingerprint: str
    preview: str
    exposure: str
    canary: bool = False

    def to_dict(self):
        return asdict(self)


def _exposure(name: str) -> str:
    for rx, label in EXPOSURE:
        if rx.search(name):
            return label
    return "file"


def scan_text(text: str, where: str = "(text)", canaries=None) -> list:
    """Token-shaped strings in `text`. The secret is never kept: only its fingerprint and a masked preview."""
    canaries, out = canaries or set(), []
    exposure = _exposure(where)
    for n, line in enumerate(text.splitlines(), 1):
        taken = []
        for kind, rx in DETECTORS:
            for m in rx.finditer(line):
                tok = m.group(m.lastindex) if m.lastindex else m.group(0)
                if any(tok in t or t in tok for t in taken):
                    continue                                    # the same token matched by a broader shape
                taken.append(tok)
                fp = fingerprint(tok)
                out.append(Finding(where, n, kind, fp, mask(tok), exposure, fp in canaries))
    return out


def scan_paths(paths, canaries=None) -> list:
    """Walk files and folders, skipping VCS and dependency folders, big files and binaries. Symlinks are not followed."""
    found = []
    for root in paths:
        root = Path(root)
        files = [root] if root.is_file() else (p for p in sorted(root.rglob("*")) if p.is_file() and not p.is_symlink()
                                              and not (set(p.relative_to(root).parts[:-1]) & SKIP_DIRS))
        for p in files:
            try:
                if p.stat().st_size > MAX_BYTES:
                    continue
                raw = p.read_bytes()
            except OSError:
                continue
            if b"\x00" in raw[:4096]:
                continue
            found += scan_text(raw.decode("utf-8", "replace"), str(p), canaries)
    return found


def scan_env(environ=None, canaries=None) -> list:
    """Environment variables that hold token-shaped values. Names are reported, values never."""
    out = []
    for name, value in sorted((environ if environ is not None else os.environ).items()):
        for f in scan_text(f"{name}={value}", f"env:{name}", canaries):
            f.exposure = "env"
            out.append(f)
    return out


# ----------------------------------------------------------------------------- the grant inventory

@dataclass
class Policy:
    idle_days: int = 30            # unused this long: flag
    grace_days: int = 7            # a brand new grant may be unused
    max_ttl_days: int = 90         # longer than this without an expiry or with a later one: flag
    wide_scopes: tuple = ("*", "admin", ".all", "full_access", "write:all")


def _t(s):
    if not s:
        return None
    d = datetime.fromisoformat(s.replace("Z", "+00:00"))
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def audit_grants(grants, policy: Policy = None, now=None) -> list:
    """One entry per grant: its flags, a risk score and a suggested action. Flags:
    NEVER_USED, IDLE, NO_EXPIRY, LONG_LIVED, EXPIRED_STILL_ACTIVE, WIDE_SCOPE, UNUSED_SCOPES."""
    policy, now = policy or Policy(), _t(now) if now else datetime.now(timezone.utc)
    out = []
    for g in grants:
        created, last, exp = _t(g.get("created")), _t(g.get("last_used")), _t(g.get("expires"))
        age = (now - created).days if created else None
        idle = (now - last).days if last else None
        flags = []
        if last is None and age is not None and age > policy.grace_days:
            flags.append("NEVER_USED")
        elif idle is not None and idle >= policy.idle_days:
            flags.append("IDLE")
        if exp is None:
            flags.append("NO_EXPIRY")
        elif created and (exp - created).days > policy.max_ttl_days:
            flags.append("LONG_LIVED")
        if exp is not None and exp < now and g.get("active", True):
            flags.append("EXPIRED_STILL_ACTIVE")
        scopes = set(g.get("scopes") or [])
        if any(w in s for s in scopes for w in policy.wide_scopes):
            flags.append("WIDE_SCOPE")
        used = g.get("scopes_used")
        if used is not None and scopes - set(used):
            flags.append("UNUSED_SCOPES")
        weight = {"NEVER_USED": 40, "IDLE": 25, "NO_EXPIRY": 15, "LONG_LIVED": 10, "EXPIRED_STILL_ACTIVE": 35, "WIDE_SCOPE": 20, "UNUSED_SCOPES": 10}
        score = min(100, sum(weight[f] for f in flags))
        # the most reversible action that closes the exposure: quarantine what may come back, revoke what never ran
        if "EXPIRED_STILL_ACTIVE" in flags or "NEVER_USED" in flags:
            action = "revoke"
        elif "IDLE" in flags:
            action = "quarantine"
        elif {"WIDE_SCOPE", "UNUSED_SCOPES"} & set(flags):
            action = "narrow_scopes"
        elif {"NO_EXPIRY", "LONG_LIVED"} & set(flags):
            action = "set_expiry"
        else:
            action = "keep"
        out.append({"id": g.get("id"), "app": g.get("app"), "kind": g.get("kind"), "flags": flags, "score": score, "action": action,
                    "idle_days": idle, "age_days": age,
                    "narrow_to": sorted(used) if "UNUSED_SCOPES" in flags and used else None})
    return sorted(out, key=lambda r: -r["score"])


def plan_countermeasures(audit) -> dict:
    """A plan a person carries out at the provider. Nothing here calls out or revokes anything."""
    by = {}
    for r in audit:
        by.setdefault(r["action"], []).append(r["id"])
    return {"revoke": by.get("revoke", []), "quarantine": by.get("quarantine", []), "narrow_scopes": by.get("narrow_scopes", []),
            "set_expiry": by.get("set_expiry", []), "keep": by.get("keep", []),
            "also": ["Bind each token to the network or workload that uses it, so a copy elsewhere is refused.",
                     "Alert on the first use of a token from a source it has never come from (idle time alone is reset by the thief's own use).",
                     "Plant canary tokens where a scavenger looks; any presentation is an alarm."]}


# ----------------------------------------------------------------------------- canary tokens and the gate

CANARY_SHAPES = {"github": ("ghp_", 36), "slack": ("xoxb-", 40), "llm_api_key": ("sk-", 48), "google_access": ("ya29.", 60)}
_ALPHABET = string.ascii_letters + string.digits


def new_canary(kind: str = "github") -> str:
    """A fake token in a real token's shape. It opens nothing. The caller plants it; the registry keeps only its fingerprint."""
    prefix, n = CANARY_SHAPES[kind]
    return prefix + "".join(secrets.choice(_ALPHABET) for _ in range(n))


class CanaryRegistry:
    """Fingerprints of the canaries we planted and where. No token is stored."""

    def __init__(self, path):
        self.path = Path(path)
        self.items = json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else {}

    def plant(self, kind: str, where: str, label: str = "") -> str:
        token = new_canary(kind)
        self.items[fingerprint(token)] = {"kind": kind, "where": where, "label": label, "planted": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.items, indent=1), encoding="utf-8")
        return token                                                       # shown once, to be planted

    @property
    def fingerprints(self) -> set:
        return set(self.items)


@dataclass
class Presented:
    verdict: str                     # allow | refuse | alarm
    reason: str
    fingerprint: str = ""


class TokenGate:
    """The check a tool gateway makes on every token presented. `live` maps fingerprint -> {sources: set, suspended: bool}."""

    def __init__(self, live: dict, canaries: set, bind_source: bool = False, log=None):
        self.live, self.canaries, self.bind_source, self.log = live, set(canaries), bind_source, log

    def _record(self, fp, verdict, reason, source):
        if self.log:
            self.log.append(actor="token-gate", tier="n/a", delegation=[], action="present_token", saw={"fingerprint": fp, "source": source},
                            verdict=verdict.upper(), reason=reason)

    def present(self, token: str, source: str) -> Presented:
        fp = fingerprint(token)
        if fp in self.canaries:
            self._record(fp, "alarm", "a planted canary was presented: someone is harvesting tokens", source)
            return Presented("alarm", "canary presented", fp)
        g = self.live.get(fp)
        if g is None:
            self._record(fp, "refuse", "unknown token", source)
            return Presented("refuse", "unknown token", fp)
        if g.get("suspended"):
            self._record(fp, "refuse", "token is quarantined", source)
            return Presented("refuse", "quarantined", fp)
        if self.bind_source and g["sources"] and source not in g["sources"]:
            self._record(fp, "alarm", "first use from a source this token has never come from", source)
            return Presented("alarm", "new source", fp)
        g["sources"].add(source)
        return Presented("allow", "known token, known source", fp)


def check_events(lines, canaries: set) -> list:
    """Scan access or auth log lines for a canary being presented. Returns line numbers, fingerprints and any address on the line."""
    hits = []
    for n, line in enumerate(lines, 1):
        for f in scan_text(line, "(events)", canaries):
            if f.canary:
                ip = re.search(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", line)
                hits.append({"line": n, "fingerprint": f.fingerprint, "from": ip.group(0) if ip else None})
    return hits


# ----------------------------------------------------------------------------- the scripted comparison

OWNER, BOT = "workload-net", "unknown-net"


def _fleet(rng, n):
    """Synthetic grants, each labeled by the author: active (used often), seasonal (used about quarterly) or abandoned."""
    fleet = []
    for i in range(n):
        kind = rng.choices(["active", "seasonal", "abandoned"], [0.5, 0.2, 0.3])[0]
        token = f"tok-{i:03d}-" + "".join(rng.choice(_ALPHABET) for _ in range(24))
        uses = ([d for d in range(0, 180) if rng.random() < 0.35] if kind == "active"
                else [d for d in range(rng.randrange(0, 90), 180, 90)] if kind == "seasonal" else [d for d in range(0, rng.randrange(1, 20))])
        fleet.append({"i": i, "token": token, "kind": kind, "uses": set(uses), "leaked": rng.random() < 0.25})
    return fleet


def simulate(policy: dict, seed: int = 7, grants: int = 120, days: int = 180, inside: float = 0.0) -> dict:
    """One policy against a scavenger bot over `days`. policy: {name, idle_days (None = never act), action: revoke|quarantine,
    bind_source (bool), canary (bool)}. `inside` is the share of the bot's attempts that come from the owner's own network
    (a foothold on the same host), which source binding cannot tell apart. Scripted and synthetic. Reports bot successes next to legitimate use interrupted."""
    rng = random.Random(seed)
    fleet = _fleet(rng, grants)
    live = {fingerprint(g["token"]): {"sources": {OWNER} if g["uses"] else set(), "suspended": False, "revoked": False, "last": max(g["uses"], default=-999), "g": g}
            for g in fleet}
    canary_tok = new_canary("github")
    gate = TokenGate({k: v for k, v in live.items()}, {fingerprint(canary_tok)} if policy.get("canary") else set(), bind_source=policy.get("bind_source", False))
    brng = random.Random(seed + 1)
    scavenged = [g for g in fleet if g["leaked"]]
    bot_ok = bot_blocked = alarms = interrupted = permanent = 0
    owned = set()
    for day in range(days):
        # the owner's workloads
        for g in fleet:
            if day in g["uses"]:
                st = live[fingerprint(g["token"])]
                if st["revoked"]:
                    permanent += 1                                   # work that no longer runs at all
                elif st["suspended"]:
                    interrupted += 1                                 # one failed call, then the owner restores it
                    st["suspended"] = False
                    st["sources"].add(OWNER); st["last"] = day
                else:
                    r = gate.present(g["token"], OWNER)
                    if r.verdict == "allow":
                        st["last"] = day
        # the bot tries a few scavenged tokens a day, and the canary if it harvested one
        for _ in range(3):
            if policy.get("canary") and brng.random() < 0.15:
                gate.present(canary_tok, BOT); alarms += 1
            if not scavenged:
                break
            g = brng.choice(scavenged)
            st = live[fingerprint(g["token"])]
            if st["revoked"]:
                bot_blocked += 1
                continue
            r = gate.present(g["token"], OWNER if brng.random() < inside else BOT)
            if r.verdict == "allow":
                bot_ok += 1; owned.add(g["i"]); st["last"] = day      # the thief's use resets the idle clock
            else:
                bot_blocked += 1; alarms += r.verdict == "alarm"
        # the idle sweep, once a day
        if policy.get("idle_days") is not None:
            for k, st in live.items():
                if not st["revoked"] and not st["suspended"] and day - st["last"] >= policy["idle_days"]:
                    if policy["action"] == "revoke":
                        st["revoked"] = True
                    else:
                        st["suspended"] = True
    abandoned_open = sum(1 for st in live.values() if st["g"]["kind"] == "abandoned" and not st["revoked"] and not st["suspended"])
    return {"policy": policy["name"], "bot_successes": bot_ok, "bot_blocked": bot_blocked, "tokens_taken_over": len(owned), "alarms": alarms,
            "legit_interrupted": interrupted, "legit_broken_for_good": permanent, "abandoned_still_open": abandoned_open,
            "legit_uses": sum(len(g["uses"]) for g in fleet if g["kind"] != "abandoned")}


POLICIES = [
    dict(name="no countermeasure", idle_days=None, action="revoke"),
    dict(name="revoke idle at 90 days", idle_days=90, action="revoke"),
    dict(name="revoke idle at 30 days", idle_days=30, action="revoke"),
    dict(name="revoke idle at 7 days", idle_days=7, action="revoke"),
    dict(name="quarantine idle at 30 days", idle_days=30, action="quarantine"),
    dict(name="quarantine at 30 + bind to source + canary", idle_days=30, action="quarantine", bind_source=True, canary=True),
    dict(name="bind to source + canary only", idle_days=None, action="quarantine", bind_source=True, canary=True),
]


def compare(seeds=range(7, 12), **kw) -> list:
    """Every policy over several seeds, summed. Same synthetic fleets for every policy."""
    rows = []
    for pol in POLICIES:
        agg = {}
        for s in seeds:
            for k, v in simulate(pol, seed=s, **kw).items():
                if k != "policy":
                    agg[k] = agg.get(k, 0) + v
        rows.append({"policy": pol["name"], **agg})
    return rows


def format_table(rows) -> str:
    cols = [("policy", "policy"), ("bot_successes", "bot succeeded"), ("tokens_taken_over", "tokens owned"), ("alarms", "alarms"),
            ("legit_interrupted", "legit interrupted"), ("legit_broken_for_good", "legit broken for good"), ("abandoned_still_open", "abandoned still open")]
    w = [max(len(h), *(len(str(r[k])) for r in rows)) for k, h in cols]
    line = lambda vals: "  ".join(str(v).ljust(w[i]) if i == 0 else str(v).rjust(w[i]) for i, v in enumerate(vals))
    return "\n".join([line(h for _, h in cols), line("-" * x for x in w)] + [line(r[k] for k, _ in cols) for r in rows])
