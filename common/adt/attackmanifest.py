"""Consolidating blind attacks from several generator models into one set a run can use.

Each generator's file stays separate and unedited (attacks/generated/*.json, each pinned by its own attacks_sha256). A manifest then
lists which files are included and which attacks survive de-duplication, and is itself pinned by a hash a preregistration cites.

De-duplication is mechanical, never a judgment: two attacks are duplicates when the word sets of their normalized text overlap by at
least THRESHOLD (Jaccard). Files are taken in sorted name order and the earlier attack wins, so the same files always give the same set.
Every dropped attack is kept in the manifest with what it duplicated. Each kept attack carries its generator and the privileged tools it
asks for (read from its calls), so results can be split by generator and the effect of a model family is visible.

`load()` refuses a manifest whose attacks were edited, or whose source file changed since the manifest was made."""
import json
import re
import time
from pathlib import Path

from . import attackgen
from .loader import ROOT

FORMAT = 1
THRESHOLD = 0.8
RULE = f"token-jaccard >= {THRESHOLD} on lowercased word sets of the text; sorted file order, earlier attack wins"


def _words(text: str) -> frozenset:
    return frozenset(re.findall(r"[a-z0-9_@.\-]+", text.lower()))


def _jaccard(a: frozenset, b: frozenset) -> float:
    return len(a & b) / len(a | b) if a | b else 1.0


def source_files(item: str) -> list:
    return sorted(attackgen.generated_dir(item).glob("*.json"))


def _rel(p: Path) -> str:
    p = Path(p).resolve()
    return p.relative_to(ROOT).as_posix() if ROOT in p.parents else str(p)


def consolidate(item: str, files: list = None, threshold: float = THRESHOLD) -> dict:
    brief = attackgen.load_brief(item)
    privileged = {t["name"] for t in brief["tools"] if t["privileged"]}
    files = [Path(f) for f in (files or source_files(item))]
    if not files:
        raise ValueError(f"No generated attack files for {item.upper()}. Run: adt attackgen {item.lower()} --models ...")
    kept, dropped, sources, seen = [], [], [], []
    for f in sorted(files, key=lambda p: p.name):
        doc = json.loads(f.read_text(encoding="utf-8"))
        attackgen.load(f)                                    # refuses a file that was edited since it was generated
        if doc["item"] != item.upper():
            raise ValueError(f"{f.name} is for {doc['item']}, not {item.upper()}")
        k0, d0 = len(kept), len(dropped)
        for a in doc["attacks"]:
            w = _words(a["text"])
            dup = next(((b, s) for b, bw in seen if (s := _jaccard(w, bw)) >= threshold), None)
            if dup:
                dropped.append({"name": a["name"], "source": f.name, "duplicate_of": dup[0], "similarity": round(dup[1], 3)})
                continue
            seen.append((a["name"], w))
            kept.append({**a, "generator": doc["generator"]["model"], "source": f.name,
                         "privileged_tools": sorted({c["tool"] for c in a["calls"]} & privileged)})
        sources.append({"file": _rel(f), "generator": doc["generator"]["model"], "reported_model": doc["generator"].get("reported_model"),
                        "attacks_sha256": doc["attacks_sha256"], "kept": len(kept) - k0, "dropped_as_duplicates": len(dropped) - d0})
    return {"format": FORMAT, "item": item.upper(), "created": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "rule": RULE,
            "threshold": threshold, "sources": sources, "attacks_sha256": attackgen.sha(kept), "attacks": kept, "dropped": dropped}


def save(item: str, manifest: dict) -> Path:
    p = attackgen.generated_dir(item).parent / f"blind-manifest-{manifest['created'].replace('-', '').replace(':', '')}.json"
    p.write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return p


def load(path) -> list:
    """The manifest's attacks in the item attack format (`calls` as (tool, args) pairs), each with `generator`. ValueError if anything
    behind it changed: the manifest's attacks, or a source file."""
    path = Path(path)
    m = json.loads(path.read_text(encoding="utf-8"))
    if attackgen.sha(m["attacks"]) != m["attacks_sha256"]:
        raise ValueError(f"{path.name} has been edited since it was made (attacks_sha256 does not match).")
    for s in m["sources"]:
        src = ROOT / s["file"] if not Path(s["file"]).is_absolute() else Path(s["file"])
        if not src.exists():
            raise ValueError(f"{path.name} names {s['file']}, which is missing.")
        attackgen.load(src)                                  # raises if that file was edited
        if json.loads(src.read_text(encoding="utf-8"))["attacks_sha256"] != s["attacks_sha256"]:
            raise ValueError(f"{s['file']} is not the file {path.name} was made from (its attacks_sha256 differs).")
    return [dict(a, calls=[(c["tool"], c["args"]) for c in a["calls"]]) for a in m["attacks"]]


def summary(m: dict) -> str:
    by = {}
    for a in m["attacks"]:
        by[a["generator"]] = by.get(a["generator"], 0) + 1
    lines = [f"{m['item']}: {len(m['attacks'])} attacks kept, {len(m['dropped'])} dropped as duplicates ({m['rule']})"]
    lines += [f"  {g}: {n} kept" for g, n in sorted(by.items())]
    both = sum(1 for a in m["attacks"] if len(a["privileged_tools"]) > 1)
    lines.append(f"  {both} ask for more than one privileged tool; {sum(1 for a in m['attacks'] if not a['privileged_tools'])} ask for none")
    return "\n".join(lines)
