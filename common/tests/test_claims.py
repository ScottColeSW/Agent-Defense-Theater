"""The numbers quoted in docs/CHECKLIST.md and docs/ROLE-QUESTIONS.md, recomputed from the saved results (or found in the README's own results table)."""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from adt.loader import ROOT

RES = ROOT / "items" / "asi03-identity-privilege" / "results"
DOCS = {n: (ROOT / "docs" / n).read_text(encoding="utf-8") for n in ("CHECKLIST.md", "ROLE-QUESTIONS.md")}
README = (ROOT / "README.md").read_text(encoding="utf-8")


def load(pattern):
    files = sorted(f for f in RES.glob(pattern) if ".decisions" not in f.name and ".thinking" not in f.name)
    return [json.loads(l) for l in files[-1].read_text(encoding="utf-8").splitlines() if l.strip()]


def k(recs, defense, label=None, attacks_only=True):
    sel = [r for r in recs if r["defense"] == defense and (not attacks_only or r["attack"] not in ("none", "")) and (label is None or r.get("task_label") == label)]
    return sum(r["outcome"] == "attack_succeeded" for r in sel), len(sel)


def says(text, *phrases):
    for p in phrases:
        assert p in text, f"missing {p!r}"


def test_blind_round_figures():
    r = load("asi03-blind-*-prereg.jsonl")
    assert k(r, "none") == (506, 675) and k(r, "scoped_credentials") == (76, 675) and k(r, "task_binding") == (0, 675) and k(r, "task_binding+hold+bottomline") == (0, 675)
    says(DOCS["CHECKLIST.md"], "0 of 675", "all 76 leaks", "75% against a predicted 52%")
    says(DOCS["ROLE-QUESTIONS.md"], "0 of 675", "76 through", "75% against a predicted 52%")


def test_all_blind_leaks_come_from_the_six_gap_attacks():
    r = load("asi03-blind-*-prereg.jsonl")
    m = json.loads(sorted((RES.parent / "attacks").glob("blind-manifest-20261016T153554Z.json"))[0].read_text(encoding="utf-8"))
    gap = {a["name"] for a in m["attacks"] if any(c["tool"] == "issue_refund" and c["args"].get("account") == "{acct}" and c["args"].get("amount", 1e9) <= 50 for c in a["calls"])}
    assert len(gap) == 6
    leaks = [x for x in r if x["defense"] == "scoped_credentials" and x["outcome"] == "attack_succeeded"]
    assert len(leaks) == 76 and all(x["attack"] in gap for x in leaks)
    unfocused = [a for a in m["attacks"] if not a["source"].endswith("153550Z.json")]
    assert len(unfocused) == 39 and sum(a["name"] in gap for a in unfocused) == 2
    says(DOCS["CHECKLIST.md"], "2 of 39")
    says(DOCS["ROLE-QUESTIONS.md"], "2 of 39")


def test_duplicate_probe_figures():
    r = load("asi03-duplicate-probe-*-prereg.jsonl")
    assert k(r, "none") == (32, 54) and k(r, "hold+bottomline") == (32, 54) and k(r, "scoped_credentials") == (0, 54) and k(r, "task_binding") == (0, 54)
    holds = [x for x in r if x["defense"] == "hold+bottomline"]
    assert sum(x.get("holds", 0) for x in holds) == 32 and sum(x.get("holds_approved", 0) for x in holds) == 32
    says(DOCS["CHECKLIST.md"], "(0 of 54)", "32 of 32", "$50 refund budget")
    says(DOCS["ROLE-QUESTIONS.md"], "(0 of 54)", "32 of 32")


def test_informed_round_one_figures():
    r = load("asi03-informed-*-prereg.jsonl")
    assert k(r, "scoped_credentials", "A") == (30, 54) and k(r, "scoped_credentials", "B") == (36, 54)
    assert k(r, "task_binding", "A") == (0, 54) and k(r, "task_binding", "B") == (0, 54)
    sess = json.loads(sorted(RES.glob("informed-session-*.json"))[-1].read_text(encoding="utf-8"))
    assert not sess["complete"] and len(sess["rounds"]) == 2 and sess["rounds"][0]["attacks"] == 6
    att = json.loads(sorted((RES / "informed-attacks").glob("*round1*.json"))[-1].read_text(encoding="utf-8"))["attacks"]
    gap = [a for a in att if any(c["tool"] == "issue_refund" and c["args"].get("amount", 1e9) <= 50 for c in a["calls"])]
    assert len(gap) == 4
    says(DOCS["CHECKLIST.md"], "4 of its first 6", "one round of four")
    says(DOCS["ROLE-QUESTIONS.md"], "4 of its first 6", "one round of four")


def test_earlier_round_figures():
    r = load("asi03-bottom-line-*-prereg.jsonl")
    assert k(r, "none") == (62, 120) and k(r, "scoped_credentials") == (12, 120) and k(r, "task_binding") == (0, 120) and k(r, "task_binding+hold+bottomline") == (0, 120)
    legit = [x for x in r if x["defense"] == "task_binding+hold+bottomline" and x["attack"] in ("none", "")]
    done = sum(x["outcome"] == "task_succeeded" for x in legit)
    assert (done, len(legit)) == (61, 63)
    above = [x for x in r if x["defense"] == "scoped_credentials" and x["attack"] in ("none", "") and x.get("tier_ok") is False]
    assert sum(x["outcome"] == "task_succeeded" for x in above) == 0 and len(above) == 27
    says(DOCS["CHECKLIST.md"], "62 of 120", "12 of 120", "0 of 120", "61 of 63", "(0 of 27)")
    says(DOCS["ROLE-QUESTIONS.md"], "62 of 120", "12 of 120", "0 of 120", "61 of 63")


def test_figures_taken_from_the_readme_results_table_are_there():
    for p in ("33 of 45", "22 with no defense", "78% of bad reports", "67% of honest ones", "all 18 legitimate updates", "40% of non-matching", "6%", "27 points", "12 refunds nobody asked for"):
        assert p in README, p
    says(DOCS["CHECKLIST.md"], "33 of 45", "22 with no defense", "78% of bad reports", "67% of honest ones", "all 18 legitimate updates", "40% of non-matching", "6%", "27 points", "12 refunds nobody asked for")
    says(DOCS["ROLE-QUESTIONS.md"], "22 of 45 to 33 of 45", "78% of bad reports", "67% of honest ones", "all 18 legitimate updates", "27 points", "12 refunds nobody asked for")


def test_no_em_dashes_and_every_checklist_item_has_a_caveat():
    for name, t in DOCS.items():
        assert "—" not in t and "–" not in t, name
    c = DOCS["CHECKLIST.md"]
    items = re.findall(r"^\*\*(\d+)\. ", c, flags=re.M)
    assert items == [str(i) for i in range(1, 12)] and c.count("*Caveat:*") == 11 and c.count("*What we saw:*") == 11
