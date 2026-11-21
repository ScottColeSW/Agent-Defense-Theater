"""Confused-deputy defenses across a delegation hop (ASI03, issue 93).

A worker agent (the deputy) holds broad standing authority. An orchestrator that read an untrusted ticket delegates a
privileged action to it. The whole question is what the deputy checks before it acts, so the deputy's authorization is the
defense under test:

- none (`credentials.AmbientBroker`): the deputy uses its own broad standing token; it trusts the caller. A privileged
  action laundered through the orchestrator by an injected ticket executes.
- scoped_grant (`declared_grant.DeclaredGrantBroker`): the deputy authorizes only from the task's declared grant, the
  original user's delegated scope, never its own tier or the ticket text. Precise: it refuses the laundered action and
  keeps the one the user did authorize.
- taint_deny (below, ABAC/policy-as-code): the deputy refuses any consequential (privileged) action once untrusted input
  has entered the context. Safe but blunt: it also refuses a privileged action the user DID authorize when that action's
  context was tainted by an untrusted ticket.
"""
import sys
from pathlib import Path

from adt.loader import load_file

cred = sys.modules.get("asi03_cred") or load_file(Path(__file__).resolve().parent / "credentials.py", "asi03_cred")

TAINTED_CONTEXT = "TAINTED_CONTEXT"


class TaintDenyBroker:
    """ABAC/taint: refuse a consequential action once untrusted input has entered the context. Non-privileged work
    (reads, notes, closing a ticket) is unaffected."""
    name = "taint-deny (refuse privileged actions under untrusted context)"

    def __init__(self, ticket_id: str, tier: int = cred.AGENT["tier"], tainted: bool = False):
        self.inner = cred.ScopedBroker(ticket_id, tier=tier)
        self.tainted = tainted

    def authorize(self, call, ticket_id, tickets) -> "cred.Decision":
        if call.tool in cred.PRIVILEGED and self.tainted:
            return cred.Decision(False, "refused: a consequential action after untrusted input entered the context", False, (TAINTED_CONTEXT,))
        return self.inner.authorize(call, ticket_id, tickets)
