"""Tool-budget guardrail brokers for the ASI08 unbounded-consumption experiment (Denial of Wallet, issue theme from the
Shirudo/budget discussion).

A metered tool, run_task(units), costs COST_PER_UNIT per unit. Harm is cumulative spend over a per-task budget, read from a
ledger, never from what the agent says. The brokers differ only in how they bound spend:

- NoBudgetBroker: no bound. Every call executes and the ledger accumulates, so a runaway or inflated plan overruns.
- SpendCapBroker: refuse a call once cumulative spend would exceed the per-task budget. Precise: it bounds dollars, so a
  large-but-affordable call or many small ones still run while they fit.
- UnitCapBroker: a flat per-call unit ceiling. Blunt: it bounds size, so it refuses a large call even when the call would
  have fit the budget, and it is the cost comparison against SpendCapBroker.

This is a local simulation of a spend meter, not a real billing system.
"""
COST_PER_UNIT = 1.0


class NoBudgetBroker:
    name = "no budget (every metered call executes)"

    def allow(self, units, spent, budget):
        return True, "no budget enforced"


class SpendCapBroker:
    name = "spend cap (refuse a call that would push cumulative spend over the per-task budget)"

    def allow(self, units, spent, budget):
        cost = units * COST_PER_UNIT
        if spent + cost > budget + 1e-9:
            return False, f"a ${cost:g} call would exceed the ${budget:g} budget (already spent ${spent:g})"
        return True, "within budget"


class UnitCapBroker:
    name = "unit cap (refuse any single call above the per-call unit ceiling)"

    def __init__(self, max_units):
        self.max_units = max_units

    def allow(self, units, spent, budget):
        if units > self.max_units:
            return False, f"a call of {units} units exceeds the {self.max_units}-unit ceiling"
        return True, "within the per-call ceiling"
