"""Simple duplicate-guard rules for the support desk (ASI03, issue 9).

Compares two cheap, stateless/session-scoped duplicate rules against the KTP capacity gate
(`defenses/kinetic.py`) on top of the scoped credential with request binding and holds:

  idempotency_key   Blocks a repeated call with the identical canonical `(tool, args)` digest
                    (`cred.call_digest`) once an earlier identical call was allowed or held.
                    Coincides with KTP on identical-amount duplicate refunds, but diverges when
                    a grant is split across different amounts (e.g., 60 then 40 or 60 then 50)
                    because each split call carries a distinct digest.
  one_per_ticket    Allows at most one `issue_refund` call (allowed or held) per ticket.
                    Blocks both identical duplicates and split-grant overdraws, but diverges from
                    KTP by over-refusing legitimate multi-part refunds within an authorized grant.

Neither rule is wired into the main pipeline permanently; both are evaluated strictly as measured
defense conditions in `scenario_simple_rules.py`.
"""
import sys
from pathlib import Path

from adt.loader import load_file

HERE = Path(__file__).resolve().parent
cred = sys.modules.get("asi03_cred") or load_file(HERE / "credentials.py", "asi03_cred")


class _SimpleRuleBase:
    def __init__(self, ticket_id: str, operator_text: str, tier: int = cred.AGENT["tier"],
                 escalation: bool = True, bind_request: bool = True):
        self.inner = cred.ScopedBroker(
            ticket_id,
            tier=tier,
            escalation=escalation,
            review_money=False,
            operator_text=operator_text,
            bind_request=bind_request,
        )
        self.tally = {"duplicate_vetoes": 0, "tier_holds": 0, "allowed": 0, "denied": 0}

    def _veto(self, reason: str) -> cred.Decision:
        self.tally["duplicate_vetoes"] += 1
        return cred.Decision(False, reason, False, (cred.REPLAY,))


class IdempotencyKeyBroker(_SimpleRuleBase):
    """Scoped credential + canonical `(tool, args)` idempotency-key guard."""
    name = "scoped credential + idempotency key"

    def __init__(self, ticket_id: str, operator_text: str, tier: int = cred.AGENT["tier"],
                 escalation: bool = True, bind_request: bool = True):
        super().__init__(ticket_id, operator_text, tier=tier, escalation=escalation, bind_request=bind_request)
        self.seen_digests = set()

    def authorize(self, call, ticket_id, tickets) -> cred.Decision:
        if call.tool == "issue_refund":
            digest = cred.call_digest(call)
            if digest in self.seen_digests:
                return self._veto("silent veto: identical issue_refund call already authorized or held in this session")
        dec = self.inner.authorize(call, ticket_id, tickets)
        if call.tool == "issue_refund" and (dec.allow or dec.escalate):
            self.seen_digests.add(cred.call_digest(call))
        if dec.allow:
            self.tally["allowed"] += 1
        elif dec.escalate:
            self.tally["tier_holds"] += 1
        else:
            self.tally["denied"] += 1
        return dec


class OneRefundPerTicketBroker(_SimpleRuleBase):
    """Scoped credential + at most one refund per ticket."""
    name = "scoped credential + one refund per ticket"

    def __init__(self, ticket_id: str, operator_text: str, tier: int = cred.AGENT["tier"],
                 escalation: bool = True, bind_request: bool = True):
        super().__init__(ticket_id, operator_text, tier=tier, escalation=escalation, bind_request=bind_request)
        self.refunded_tickets = set()

    def authorize(self, call, ticket_id, tickets) -> cred.Decision:
        target_ticket = call.args.get("ticket_id") or ticket_id
        if call.tool == "issue_refund" and target_ticket in self.refunded_tickets:
            return self._veto(f"silent veto: ticket {target_ticket} already has an authorized or held refund")
        dec = self.inner.authorize(call, ticket_id, tickets)
        if call.tool == "issue_refund" and (dec.allow or dec.escalate):
            self.refunded_tickets.add(target_ticket)
        if dec.allow:
            self.tally["allowed"] += 1
        elif dec.escalate:
            self.tally["tier_holds"] += 1
        else:
            self.tally["denied"] += 1
        return dec
