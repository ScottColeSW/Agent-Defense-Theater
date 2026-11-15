"""Model-free controls for every single-decision JSON reply reader (#24)."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from adt.loader import ROOT, load_file


# path, reader, unique reply, normal value, duplicated key, first value, parse-failure value
CASES = [
    ("items/asi03-identity-privilege/defenses/escalation.py", "parse_verdict",
     {"decision": "approve", "reason": "ok"}, (True, "ok", True), "decision", "deny",
     (False, "unparseable reply: denied", False)),
    ("items/asi01-goal-hijack/defenses/goalguard.py", "parse_fits",
     {"fits": True, "reason": "ok"}, (True, "ok", True), "fits", False,
     (False, "unparseable reply: does not fit", False)),
    ("items/asi01-goal-hijack/defenses/goalguard.py", "parse_plan",
     {"plan": ["add_note"]}, {"add_note"}, "plan", ["get_deal"], None),
    ("blackice/rungs/bi01-contain/scenario.py", "parse_quarantine",
     {"quarantine": ["T1"]}, {"T1"}, "quarantine", [], set()),
    ("blackice/rungs/bi01-contain/scenario_structured_verdict.py", "parse_alarms",
     {"alarms": [{"id": "A1", "verdict": "act"}]}, [{"id": "A1", "verdict": "act"}],
     "alarms", [], []),
    ("items/asi05-code-execution/scenario.py", "_parse_code",
     {"code_lines": ["print(1)"]}, "print(1)", "code_lines", ["pass"], None),
    ("items/asi05-code-execution/scenario.py", "_parse_code",
     {"code": "print(1)"}, "print(1)", "code", "pass", None),
    ("items/asi06-memory-context-poisoning/scenario.py", "_parse_filer",
     {"relation": "new", "related_id": "C1", "reason": "ok"}, ("new", "C1", "ok"),
     "relation", "collides", None),
    ("items/asi06-memory-context-poisoning/scenario.py", "_parse_filer",
     {"relation": "reinforces", "related_id": "C1", "reason": "ok"}, ("reinforces", "C1", "ok"),
     "related_id", "C2", None),
    ("items/asi06-memory-context-poisoning/scenario.py", "_parse_decider",
     {"needs_cfo_approval": False}, False, "needs_cfo_approval", True, None),
    ("items/asi07-inter-agent-communication/scenario.py", "_parse_decider",
     {"calls": [{"tool": "send_offer", "args": {"deal_id": "D-101"}}]},
     [("send_offer", {"deal_id": "D-101"})], "calls", [], []),
    ("items/asi08-cascading-failures/scenario.py", "_parse_review",
     {"agree": True, "cash_on_cash": 0.12}, {"agree": True, "figure": 0.12},
     "agree", False, {"agree": False, "figure": None}),
    ("items/asi08-cascading-failures/scenario.py", "_parse_review",
     {"agree": True, "cash_on_cash": 0.12}, {"agree": True, "figure": 0.12},
     "cash_on_cash", 0.02, {"agree": False, "figure": None}),
    ("items/asi10-rogue-agents/scenario.py", "_parse_tick",
     {"tool": "send_offer", "args": {"deal_id": "D-101"}, "report": "ok"},
     ("send_offer", {"deal_id": "D-101"}, "ok"), "tool", "none", None),
    ("items/asi10-rogue-agents/scenario.py", "_parse_tick",
     {"tool": "send_offer", "args": {"deal_id": "D-101"}, "report": "ok"},
     ("send_offer", {"deal_id": "D-101"}, "ok"), "args", {"deal_id": "D-102"}, None),
]
IDS = [f"{path.split('/')[1]}-{reader}-{key}" for path, reader, _, _, key, _, _ in CASES]


@pytest.mark.parametrize("path,name,reply,normal,key,first,failure", CASES, ids=IDS)
def test_unique_reply_unchanged(path, name, reply, normal, key, first, failure):
    reader = getattr(load_file(ROOT / path, f"duplicate_control_{name}"), name)
    assert reader(json.dumps(reply)) == normal


@pytest.mark.parametrize("path,name,reply,normal,key,first,failure", CASES, ids=IDS)
@pytest.mark.parametrize("reverse", [False, True])
def test_duplicate_reply_uses_parse_failure(path, name, reply, normal, key, first, failure, reverse):
    reader = getattr(load_file(ROOT / path, f"duplicate_regression_{name}"), name)
    pair = json.dumps(key) + ": " + json.dumps(first)
    text = json.dumps(reply)
    text = text[:-1] + ", " + pair + "}" if reverse else "{" + pair + ", " + text[1:]
    # The harness's reading: ambiguity is a parse failure, in either key order.
    assert reader(text) == failure
    assert reader(text) == reader("not JSON")


@pytest.mark.parametrize("path,name,text,failure", [
    ("blackice/rungs/bi01-contain/scenario_structured_verdict.py", "parse_alarms",
     '{"alarms": [{"id": "A1", "verdict": "ignore", "verdict": "act"}]}', []),
    ("items/asi07-inter-agent-communication/scenario.py", "_parse_decider",
     '{"calls": [{"tool": "add_note", "tool": "send_offer", "args": {}}]}', []),
    ("items/asi07-inter-agent-communication/scenario.py", "_parse_decider",
     '{"calls": [{"tool": "send_offer", "args": {"amount": 1, "amount": 100}}]}', []),
    ("items/asi10-rogue-agents/scenario.py", "_parse_tick",
     '{"tool": "send_offer", "args": {"amount": 1, "amount": 100}}', None),
])
def test_nested_duplicate_is_also_ambiguous(path, name, text, failure):
    reader = getattr(load_file(ROOT / path, f"nested_duplicate_{name}"), name)
    assert reader(text) == failure


@pytest.mark.parametrize("decision", ["approve or deny", "approved? no, deny"])
def test_ambiguous_verdict_is_not_a_well_formed_approval(decision):
    path = ROOT / "items/asi03-identity-privilege/defenses/escalation.py"
    reader = load_file(path, "ambiguous_verdict").parse_verdict
    assert reader(json.dumps({"decision": decision, "reason": "unsure"})) == (
        False, "unparseable reply: denied", False,
    )


@pytest.mark.parametrize("decision,approve", [(" APPROVE ", True), (" DENY ", False)])
def test_exact_verdict_still_allows_case_and_whitespace(decision, approve):
    path = ROOT / "items/asi03-identity-privilege/defenses/escalation.py"
    reader = load_file(path, "exact_verdict").parse_verdict
    assert reader(json.dumps({"decision": decision, "reason": "ok"})) == (approve, "ok", True)
