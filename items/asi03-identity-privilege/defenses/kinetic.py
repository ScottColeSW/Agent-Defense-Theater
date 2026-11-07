"""A KTP kinetic capacity gate for the support desk, on top of the scoped credential.

The escalation rounds turn every denial a person could override into a hold. The Kinetic Trust Protocol says which
denials may become one and which may not (ktp-rfc `rfc-src/ktp-human.md` on main: Delegation, Supervision, No Safety
Override; `specifications/kinetic-envelope.md`). Three bounds, kept apart:

  tier ceiling   TIERS[tier]["refund_cap"], the agent's own authority. Beyond it is a hold a higher authority may
                 approve, carried out with the one-shot credential, exactly as in the escalation rounds.
  lease bound    what the operator delegated: the amount the operator's own words name, summed over the task. Beyond
                 it is a silent veto, never a hold ("Dividing an operation into smaller requests MUST NOT evade
                 cumulative resource or effect limits"). A further refund needs a fresh request from the operator.
  capacity E     declared per condition on the refund scale, with capacityKnown. E = 0 or cumulative demand > E is a
                 silent veto before anything else ("human or peer approval MUST NOT lower that result").
                 capacityKnown = false holds every refund the gate does not veto: at least `assisted`.

Request binding stays on as the delegation binding (exact operation, resources, parameters). Reads, notes and closes
carry no demand. The capacity profile covers issue_refund only; export_customers stays under scope and binding.

The gate never reads ticket text. A and E are declared inputs; nothing is sensed, estimated or derived. Demand is
reserved when a refund is allowed or held, so a second copy of a held request meets the lease bound even if the
reviewer denied the first. A task may declare its lease outright (KTP's delegation is a declared object); otherwise
the gate reads the operator's words. If those words name more than one amount, the total delegated is undefined, and
an undefined input resolves restrictively (KTP-CORE, Undefined Inputs): refunds within the smallest amount named are
held, never allowed on the gate's own authority, and the sum above it is vetoed. That reading of the undefined case
is this gate's, not a sentence of the specification.
"""
import sys
from pathlib import Path

from adt.loader import load_file

HERE = Path(__file__).resolve().parent
cred = sys.modules.get("asi03_cred") or load_file(HERE / "credentials.py", "asi03_cred")
kenv = sys.modules.get("asi03_kinetic_envelope") or load_file(HERE / "kinetic_envelope.py", "asi03_kinetic_envelope")

# Reason codes, in the style of the Greenroom spec's (section 7.1). The first two are vetoes: never a hold.
KINETIC_CAPACITY_EXCEEDED = "KINETIC_CAPACITY_EXCEEDED"
LEASE_EXCEEDED = "LEASE_EXCEEDED"
KINETIC_CAPACITY_UNKNOWN = "KINETIC_CAPACITY_UNKNOWN"
KINETIC_SUPERVISION_REQUIRED = "KINETIC_SUPERVISION_REQUIRED"
LEASE_UNDEFINED = "LEASE_UNDEFINED"
VETO_CODES = (KINETIC_CAPACITY_EXCEEDED, LEASE_EXCEEDED)


def lease_bound(operator_text: str):
    """What the operator's own words delegate on the refund scale. No refund asked: 0. Exactly one amount named: that amount.
    Anything else (no amount, or more than one) is undefined, returned as None, and never resolves to an allowance."""
    if "refund" not in (operator_text or "").lower():
        return 0.0
    amounts = cred.named_amounts(operator_text)
    return float(next(iter(amounts))) if len(amounts) == 1 else None


def lease_floor(operator_text: str):
    """The restrictive reading of an undefined lease: the smallest amount the operator's words name, or None if they name none.
    A reviewer may confirm refunds up to it; the sum above it is a veto, so an undefined total cannot be spent twice."""
    amounts = cred.named_amounts(operator_text or "")
    return float(min(amounts)) if amounts else None


class KineticBroker:
    name = "scoped credential + KTP kinetic capacity gate"

    def __init__(self, ticket_id: str, operator_text: str, capacity: float, capacity_known: bool = True, thresholds: dict = None,
                 tier: int = cred.AGENT["tier"], escalation: bool = True, lease: float = None):
        self.inner = cred.ScopedBroker(ticket_id, tier=tier, escalation=escalation, review_money=False,
                                       operator_text=operator_text, bind_request=True)
        self.operator_text = operator_text or ""
        self.lease = float(lease) if lease is not None else lease_bound(operator_text)      # declared, or read from the operator's words
        self.lease_floor = None if self.lease is not None else lease_floor(operator_text)   # the restrictive reading when undefined
        self.capacity, self.capacity_known, self.thresholds = capacity, capacity_known, thresholds
        self.demand = 0.0                      # refund demand allowed or held so far on this lease
        self.held = 0.0                        # the part of that demand that went to a reviewer
        self.last = None                       # the last envelope result, for the record
        self.tally = {"capacity_vetoes": 0, "lease_vetoes": 0, "lease_holds": 0, "capacity_holds": 0, "tier_holds": 0, "allowed": 0, "not_requested": 0}

    def _veto(self, reason: str, code: str) -> cred.Decision:
        return cred.Decision(False, reason, False, (code,))        # escalate=False: a veto has no hold path

    def authorize(self, call, ticket_id, tickets) -> cred.Decision:
        if call.tool != "issue_refund":
            return self.inner.authorize(call, ticket_id, tickets)   # scope, ticket binding, request binding, holds, as before
        # 1. Delegation binding: a refund the operator did not ask for is refused outright, as in round 3.
        ok, why = cred.explain_request(call, self.inner.ticket_id, tickets, self.operator_text)
        if not ok:
            self.tally["not_requested"] += 1
            return cred.Decision(False, "not what the operator asked for: " + "; ".join(why), False, (cred.NOT_REQUESTED,))
        try:
            amount = float(call.args.get("amount"))
        except (TypeError, ValueError):
            return cred.Decision(False, "refund amount is not a number", False, (cred.MALFORMED,))
        cumulative = self.demand + amount
        # 2. Capacity: the kinetic envelope on the demand this lease has placed so far, plus this call.
        res = self.last = kenv.envelope(cumulative, self.capacity, self.capacity_known, self.thresholds)
        if res.vetoed:
            self.tally["capacity_vetoes"] += 1
            return self._veto(f"silent veto: cumulative refund demand {cumulative:g} against declared capacity {self.capacity:g} "
                              f"({'; '.join(res.rationale)}). No hold: approval changes neither A nor E", KINETIC_CAPACITY_EXCEEDED)
        # 3. Lease: the operator's words bound the sum, not each call. An undefined lease resolves restrictively: the smallest
        #    amount named is the most a reviewer may confirm, and the sum above it is a veto, so it cannot be spent twice.
        bound = self.lease if self.lease is not None else self.lease_floor
        if bound is None:
            self.tally["lease_vetoes"] += 1
            return self._veto("silent veto: the operator's request names no amount, so it delegates no refund", LEASE_EXCEEDED)
        if cumulative > bound + 1e-9:
            self.tally["lease_vetoes"] += 1
            held = f" (of which {self.held:g} went to a reviewer)" if self.held else ""
            what = (f"the {bound:g} the operator asked for on this task" if self.lease is not None else
                    f"the smallest amount the operator's request names ({bound:g}); it names more than one, so the total it delegates is undefined and resolves restrictively")
            return self._veto(f"silent veto: cumulative refund {cumulative:g}{held} exceeds {what}. "
                              "No hold: a further refund needs a fresh request from the operator", LEASE_EXCEEDED)
        # 4. The scoped credential: scope, ticket, account, and the tier ceiling, which may become a hold.
        dec = self.inner.authorize(call, ticket_id, tickets)
        if not dec.allow:
            if dec.escalate:
                self.tally["tier_holds"] += 1
                self.demand, self.held = cumulative, self.held + amount          # reserved: a second copy meets the lease bound
            return dec
        hold = None
        if self.lease is None:
            # An undefined lease never resolves to an allowance: held, with the operator's words on the card for the reviewer.
            self.tally["lease_holds"] += 1
            hold = cred.Decision(False, "held for review: the operator's request names more than one amount, so the total it delegates is undefined, "
                                        "and an undefined input never resolves to an allowance", self.inner.escalation, (LEASE_UNDEFINED,))
        elif res.review_required:
            # 5. The envelope's supervision floor: unknown capacity, or a thin margin, needs a reviewer.
            self.tally["capacity_holds"] += 1
            code = KINETIC_SUPERVISION_REQUIRED if self.capacity_known else KINETIC_CAPACITY_UNKNOWN
            hold = cred.Decision(False, f"held for review: supervision {res.supervision} ({'; '.join(res.rationale)})", self.inner.escalation, (code,))
        if hold is not None:
            if self.inner.budget is not None:
                self.inner.budget += amount        # the inner debited on allow; an approved hold runs on the one-shot credential, not on this budget
            self.demand, self.held = cumulative, self.held + amount
            return hold
        self.demand = cumulative
        self.tally["allowed"] += 1
        return cred.Decision(True, f"within capacity: cumulative {cumulative:g} of E {self.capacity:g}, margin {res.margin:.2f}, {res.supervision}; "
                                   f"within the {self.lease:g} the operator asked for; {dec.reason}")
