"""Policy shadow mode for the support desk (ASI03, issue 18).

A purple-team capability: run a policy observe-only. The shadow broker evaluates every call exactly as the enforcing
broker would, records the decision it WOULD have made (allow, hold or veto, with reason codes), but lets the call proceed
as the baseline does. So you can measure a policy's effect, how often it would change an outcome the baseline lets through
and how often it would block valid work, before turning it on.

State (issue 18 asks this be decided and documented): the enforcing broker reserves demand when it allows or holds, so its
decisions over a task depend on earlier ones. Shadow mode UPDATES that hypothetical state by calling the enforcing broker's
own `authorize`, so the sequence of would-decisions is exactly what the enforcing broker would have produced on this task.
What differs is only the returned decision: the call proceeds as baseline, while the enforcing broker's state advances as if
it had run. The would-decisions are kept in `would` for the scenario to read and compare against a real enforcing run.
"""
import sys
from pathlib import Path

from adt.loader import load_file

cred = sys.modules.get("asi03_cred") or load_file(Path(__file__).resolve().parent / "credentials.py", "asi03_cred")

VETO_CODES = ("KINETIC_CAPACITY_EXCEEDED", "LEASE_EXCEEDED")


class ShadowBroker:
    """Observe-only wrapper: records what `enforcing` would decide, but allows the call like the baseline."""

    def __init__(self, enforcing):
        self.enforcing = enforcing
        self.name = "policy shadow of " + getattr(enforcing, "name", "a policy")
        self.would = []                        # [(call, would_decision)] the enforcing policy would have made
        self.tally = {"would_allow": 0, "would_hold": 0, "would_veto": 0}

    def authorize(self, call, ticket_id, tickets) -> cred.Decision:
        would = self.enforcing.authorize(call, ticket_id, tickets)   # advances the enforcing broker's hypothetical state
        self.would.append((call, would))
        if would.allow:
            self.tally["would_allow"] += 1
            verb = "allow"
        elif would.escalate:
            self.tally["would_hold"] += 1
            verb = "hold"
        else:
            self.tally["would_veto"] += 1
            verb = "veto"
        return cred.Decision(True, f"policy shadow (observe-only): the call proceeds as baseline; the policy would {verb} ({would.reason})")

    def would_veto(self, call_filter=None) -> int:
        """How many recorded would-decisions are vetoes (never a hold), optionally among calls matching call_filter."""
        return sum(1 for c, d in self.would if (call_filter is None or call_filter(c)) and not d.allow and not d.escalate)
