"""The governance view of a report: which crosswalk rows a test supplies evidence for, and what that test found.

The crosswalk is docs/GOVERNANCE-CROSSWALK.md (also crosswalk/governance.csv). crosswalk/governance-links.json says which pass-bar criteria of each
test bear on which row. The mapping is the author's and is not a claim of compliance.
"""
import csv
import json

from .loader import ROOT

CSV = ROOT / "crosswalk" / "governance.csv"
LINKS = ROOT / "crosswalk" / "governance-links.json"


def load():
    rows = list(csv.DictReader(CSV.open(encoding="utf-8")))
    return rows, json.loads(LINKS.read_text(encoding="utf-8"))


def view(item: str, experiment: str, pass_bar):
    """Rows for one test, each with the criteria (id, status, result) that bear on it. None when there is nothing to show."""
    if not pass_bar:
        return None
    rows, links = load()
    mine = links["tests"].get(f"{item.lower()}/{experiment}", {})
    by_id = {c["id"]: c for c in pass_bar}
    out = []
    for r in rows:
        crit = [{"id": i, "text": by_id[i]["text"], "status": by_id[i]["status"], "result": by_id[i]["result"]} for i in mine.get(r["id"], []) if i in by_id]
        where = links["always"].get(r["id"])
        if crit or where:
            out.append({"id": r["id"], "measurement": r["measurement"], "nist": r["nist_ai_rmf"], "eu": r["eu_ai_act"], "iso": r["iso_iec_42001"],
                        "criteria": crit, "where": where if not crit else None})
    return {"rows": out, "gaps": links["gaps"]}
