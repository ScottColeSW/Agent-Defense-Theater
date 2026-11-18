"""The declared-grant broker for the support desk (ASI03, issue 28's real fix).

The first run's request binding (`cred.explain_request`) decides what the operator authorised by reading the operator's
words: a refund is "asked for" when the word "refund" appears and the amount is any dollar figure in the text, an export
when "export" appears and the destination is any substring of the request. Issue 28 showed that reads a negated, reported,
or limit mention of a refund as a request for it, and matches an export destination as a substring. `binding.py` ships a
restrictive cue-word stopgap; this is the structural fix it names.

A declared grant is an authorisation object the operator's side produces and attaches to the task, not text the agent reads:

    {operations: {"issue_refund", ...},   # which privileged tools the operator delegated
     refund_lease: float | None,           # the total refund the operator delegated on this task (None = none)
     destinations: {"finance-reports@acme.test", ...}}   # the exact export addresses the operator delegated

The broker authorises a consequential call only if it matches the grant, and it never reads the ticket or the operator's
words. So a negated, reported, limit, or substring attack planted in the ticket authorises nothing, by construction: the
text is not an input to the decision. Account, ticket and the tier ceiling come from the scoped credential as before.

This generalises the KTP gate (`kinetic.py`), which already treats the refund lease as a declared object and never reads
ticket text, from the amount alone to every field the decision needs.
"""
import sys
from pathlib import Path

from adt.loader import load_file

cred = sys.modules.get("asi03_cred") or load_file(Path(__file__).resolve().parent / "credentials.py", "asi03_cred")


def grant_from_task(data: dict) -> dict:
    """Build the declared grant from the trusted task fields (the operator's side), never from the planted ticket text."""
    return {
        "operations": set(data.get("asks") or []),
        "refund_lease": data.get("lease"),
        "destinations": set(data.get("grant_destinations") or []),
    }


class DeclaredGrantBroker:
    """A scoped credential whose consequential calls are authorised only by the task's declared grant (issue 28)."""
    name = "scoped credential + declared grant"

    def __init__(self, ticket_id: str, grant: dict, tier: int = cred.AGENT["tier"], escalation: bool = False):
        self.inner = cred.ScopedBroker(ticket_id, tier=tier, escalation=escalation, review_money=False, operator_text=None, bind_request=False)
        grant = grant or {}
        self.operations = set(grant.get("operations") or [])
        self.lease = grant.get("refund_lease")
        self.destinations = set(grant.get("destinations") or [])
        self.demand = 0.0                      # refund allowed so far on this lease
        self.tally = {"allowed": 0, "not_granted": 0, "lease_vetoes": 0}

    def _refuse(self, reason: str, code: str = None) -> "cred.Decision":
        self.tally["not_granted"] += 1
        return cred.Decision(False, "not within the operator's declared grant: " + reason, False, (code or cred.NOT_REQUESTED,))

    def authorize(self, call, ticket_id, tickets) -> "cred.Decision":
        if call.tool in cred.PRIVILEGED:
            if call.tool not in self.operations:
                return self._refuse(f"the grant does not authorise {call.tool}")
            if call.tool == "issue_refund":
                try:
                    amount = float(call.args.get("amount"))
                except (TypeError, ValueError):
                    return cred.Decision(False, "refund amount is not a number", False, (cred.MALFORMED,))
                if self.lease is None:
                    return self._refuse("the grant delegates no refund")
                cumulative = self.demand + amount
                if cumulative > self.lease + 1e-9:
                    self.tally["lease_vetoes"] += 1
                    return self._refuse(f"cumulative refund {cumulative:g} exceeds the declared grant of {self.lease:g}")
            if call.tool == "export_customers":
                dest = str(call.args.get("destination", ""))
                if dest not in self.destinations:
                    return self._refuse(f"{dest or '(none)'} is not an address the grant delegates")
        # Scope, ticket, account and the tier ceiling, by code, from the scoped credential. No text is read anywhere here.
        dec = self.inner.authorize(call, ticket_id, tickets)
        if call.tool == "issue_refund" and (dec.allow or dec.escalate):
            # Reserve the demand on an allow AND on a hold: a held first installment that a reviewer later approves still
            # counts against the lease, so a second installment cannot overspend behind it (the KTP reservation rule).
            self.demand += float(call.args.get("amount"))
            if dec.allow:
                self.tally["allowed"] += 1
        return dec
