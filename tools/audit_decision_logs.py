#!/usr/bin/env python3
"""Offline decision-log auditor for Agent Defense Theater.

Addresses two unclaimed field-context stubs from docs/OPEN-WORK.md:
1. Repetitive tool-loop detection: detects contiguous runs of identical
   (actor, defense, case, action, args) calls within consecutive log sequences
   and measures per-run tool-call diversity.
2. Unintended-route anomaly audit: flags structural anomalies in decision logs
   such as repeated allowed state-mutating calls within a single episode,
   unrestricted ambient-token allows, and missing decision rationales.

Usage:
    python tools/audit_decision_logs.py
    python tools/audit_decision_logs.py --item asi03 --sample 10
    python tools/audit_decision_logs.py --json-out audit_report.json
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def iter_decision_logs(item_filter: str | None = None) -> list[Path]:
    paths = sorted(ROOT.glob("items/*/results/*-prereg.decisions.jsonl"))
    if item_filter:
        token = item_filter.lower()
        paths = [p for p in paths if token in p.as_posix().lower()]
    return paths


def read_entries(path: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line_no, raw in enumerate(fh, start=1):
            line = raw.strip()
            if not line:
                continue
            obj = json.loads(line)
            obj["_line"] = line_no
            entries.append(obj)
    return entries


def _call_signature(entry: dict[str, Any]) -> tuple[str, str, str, str, str]:
    saw = entry.get("saw") or {}
    return (
        str(entry.get("actor", "")),
        str(saw.get("defense", "unknown")),
        str(saw.get("case", "unknown")),
        str(entry.get("action", "")),
        json.dumps(saw.get("args", {}), sort_keys=True),
    )


def detect_contiguous_loops(entries: list[dict[str, Any]], min_streak: int = 2) -> list[dict[str, Any]]:
    """Find contiguous streaks of identical tool calls by the same actor/case/defense."""
    if not entries:
        return []

    streaks: list[dict[str, Any]] = []
    cur_sig = _call_signature(entries[0])
    cur_group = [entries[0]]

    for entry in entries[1:]:
        sig = _call_signature(entry)
        prev_seq = cur_group[-1].get("seq")
        curr_seq = entry.get("seq")
        is_contiguous = (
            isinstance(prev_seq, int)
            and isinstance(curr_seq, int)
            and curr_seq == prev_seq + 1
        )
        if sig == cur_sig and is_contiguous:
            cur_group.append(entry)
        else:
            if len(cur_group) >= min_streak:
                streaks.append(_summarize_streak(cur_sig, cur_group))
            cur_sig = sig
            cur_group = [entry]

    if len(cur_group) >= min_streak:
        streaks.append(_summarize_streak(cur_sig, cur_group))

    return streaks


def _summarize_streak(
    sig: tuple[str, str, str, str, str], group: list[dict[str, Any]]
) -> dict[str, Any]:
    actor, defense, case, action, args_json = sig
    allowed = sum(1 for e in group if e.get("verdict") == "allow")
    denied = sum(1 for e in group if e.get("verdict") == "deny")
    return {
        "actor": actor,
        "defense": defense,
        "case": case,
        "action": action,
        "args": args_json,
        "seq_start": group[0].get("seq"),
        "seq_end": group[-1].get("seq"),
        "streak_length": len(group),
        "allowed": allowed,
        "denied": denied,
    }


def analyze_log(path: Path, min_streak: int = 2) -> dict[str, Any]:
    entries = read_entries(path)
    total = len(entries)
    allow_count = sum(1 for e in entries if e.get("verdict") == "allow")
    deny_count = sum(1 for e in entries if e.get("verdict") == "deny")

    action_counts: Counter[str] = Counter()
    ambient_allows = 0
    empty_reasons = 0

    for e in entries:
        action_counts[str(e.get("action", ""))] += 1
        reason = str(e.get("reason", "")).strip()
        if not reason:
            empty_reasons += 1
        if e.get("verdict") == "allow" and "holds every scope" in reason:
            ambient_allows += 1

    streaks = detect_contiguous_loops(entries, min_streak=min_streak)
    repeat_allow_streaks = [s for s in streaks if s["allowed"] >= 2]
    max_streak = max((s["streak_length"] for s in streaks), default=0)
    overall_diversity = round(len(action_counts) / total, 4) if total else 0.0

    return {
        "file": path.relative_to(ROOT).as_posix(),
        "entries": total,
        "allow": allow_count,
        "deny": deny_count,
        "unique_actions": len(action_counts),
        "overall_tool_diversity": overall_diversity,
        "ambient_token_allows": ambient_allows,
        "empty_reasons": empty_reasons,
        "contiguous_loop_count": len(streaks),
        "repeat_allow_loops": len(repeat_allow_streaks),
        "max_streak": max_streak,
        "sample_loops": streaks[:5],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit saved ADT decision logs.")
    parser.add_argument("--item", help="Filter logs by item substring (e.g., asi03)")
    parser.add_argument("--min-streak", type=int, default=2, help="Minimum contiguous repeat length")
    parser.add_argument("--sample", type=int, default=8, help="Number of loop streaks to print")
    parser.add_argument("--json-out", help="Optional path to write full JSON report")
    args = parser.parse_args()

    logs = iter_decision_logs(args.item)
    if not logs:
        print("No matching preregistered decision logs found.")
        return 1

    reports = [analyze_log(p, min_streak=args.min_streak) for p in logs]
    total_entries = sum(r["entries"] for r in reports)
    total_loops = sum(r["contiguous_loop_count"] for r in reports)
    total_repeat_allows = sum(r["repeat_allow_loops"] for r in reports)

    print(f"Audited {len(reports)} preregistered decision logs ({total_entries} total entries)")
    print(
        f"Detected {total_loops} contiguous tool-call streaks "
        f"({total_repeat_allows} with >=2 allowed repeats).\n"
    )
    print(
        f"{'Log File':<66} {'Entries':>7} {'Allow':>6} {'Deny':>6} "
        f"{'Loops':>6} {'RepAllow':>8} {'MaxStrk':>7}"
    )
    print("-" * 112)
    for r in reports:
        print(
            f"{r['file']:<66} {r['entries']:>7} {r['allow']:>6} {r['deny']:>6} "
            f"{r['contiguous_loop_count']:>6} {r['repeat_allow_loops']:>8} {r['max_streak']:>7}"
        )

    flagged = [r for r in reports if r["sample_loops"]]
    if flagged and args.sample > 0:
        print("\nSample contiguous repetitive tool-loop streaks:")
        shown = 0
        for r in flagged:
            for lc in r["sample_loops"]:
                print(
                    f"  - [{r['file']}] seq={lc['seq_start']}..{lc['seq_end']} "
                    f"actor={lc['actor']} defense={lc['defense']} case={lc['case']} "
                    f"action={lc['action']} streak={lc['streak_length']} "
                    f"(allow={lc['allowed']}, deny={lc['denied']})"
                )
                shown += 1
                if shown >= args.sample:
                    break
            if shown >= args.sample:
                break

    if args.json_out:
        out_path = Path(args.json_out)
        out_path.write_text(json.dumps(reports, indent=2), encoding="utf-8")
        print(f"\nWrote detailed JSON report to {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
