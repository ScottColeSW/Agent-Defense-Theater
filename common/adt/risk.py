"""Risk vs Confidence: a demonstrative executive view built on the measured runs.

The point of this module is the balance an executive actually weighs, risk against confidence, told in two layers
that are kept strictly apart so neither is mistaken for the other.

Confidence (measured). How well the strongest defense contained OUR attack suite, read straight from the committed
    preregistered runs via the same scorer every report uses, with the sample size and a 95% Wilson interval. The
    lower edge of that interval is reported as the floor: what the containment can be defended as being at least,
    not the point estimate. Never a bare 100%.

Residual risk (assumptions). A transparent model whose every input is shown and adjustable, and none of which is a
    measurement:

        residual_usd_per_year = exposure_attempts_per_year * (1 - containment) * breach_impact_usd

    The baseline uses the undefended condition's containment; the defended figure uses the strongest defense's. The
    difference is the loss the defense avoids per year under these assumptions.

Guardrails, surfaced wherever this prints:
  - Confidence measures the attacks WE wrote, not every possible attack. The attacker is the author one level up,
    so a high number is an upper bound on confidence, not a guarantee.
  - The frequency and dollar inputs are assumptions for demonstration, chosen to be reasonable and clear, not findings.
  - Small samples make the interval wide; read the floor and the n, not the headline percent.
"""
import json

from . import scorer
from .loader import item_folders


# Demonstration assumptions: reasonable, clearly labeled, overridable from the command line. NOT measurements.
ASSUMPTIONS = {
    "exposure_attempts_per_year": 1000,     # adversary attempts of this attack class against one live deployment, per year
    "breach_impact_usd": 50_000,            # cost of one successful breach of this class
}


def item_label(item: str) -> str:
    """A short human name from the item's folder, e.g. asi05 -> 'Code execution'. Derived, so it never goes stale."""
    folder = next((f for f in item_folders() if f.name.split("-")[0] == item), None)
    if folder is None:
        return item.upper()
    return folder.name.split("-", 1)[1].replace("-", " ").capitalize() if "-" in folder.name else item.upper()


def prereg_files(item: str, experiment: str = "first-run") -> list:
    """The committed (`-prereg`) result files for one item and experiment. Experiment is read from each run's meta."""
    folder = next((f for f in item_folders() if f.name.split("-")[0] == item), None)
    if folder is None:
        return []
    out = []
    for p in sorted((folder / "results").glob(f"{item}-*-prereg.jsonl")):
        if ".decisions" in p.name:
            continue
        meta = p.with_name(p.name.replace(".jsonl", ".meta.json"))
        exp = json.loads(meta.read_text(encoding="utf-8")).get("experiment", "first-run") if meta.exists() else "first-run"
        if exp == experiment:
            out.append(p)
    return out


def item_risk(item: str, experiment: str = "first-run", assumptions: dict = ASSUMPTIONS) -> dict | None:
    """One Risk-vs-Confidence row for an item, or None when it has no preregistered run for that experiment.

    containment is measured; every dollar figure is assumptions applied to that measurement. The strongest defense is
    the one with the lowest attack-success rate; the baseline is the undefended (`none`) condition, or the worst
    condition when no condition is labeled `none`."""
    recs = scorer.load_records(prereg_files(item, experiment), live_only=True)
    if not recs:
        return None
    rows = [r for r in scorer.summarize(recs, by=("defense",)) if r["success"]["n"]]
    if not rows:
        return None
    baseline = next((r for r in rows if r["layer"] == "none"), None) or max(rows, key=lambda r: r["success"]["rate"])
    defended = [r for r in rows if r is not baseline] or rows
    best = min(defended, key=lambda r: r["success"]["rate"])

    exposure = assumptions["exposure_attempts_per_year"]
    impact = assumptions["breach_impact_usd"]

    def residual(success_share):
        return exposure * success_share["rate"] * impact

    s_best, s_base = best["success"], baseline["success"]
    lo, hi = s_best["ci"]                                   # Wilson interval on the success rate
    # The headline residual is computed at the 95% floor (the success rate's upper edge), never at the point estimate,
    # so a run that saw zero failures still carries the residual its sample size cannot rule out, instead of a bare $0.
    residual_floor = exposure * hi * impact
    return {
        "item": item,
        "label": item_label(item),
        "experiment": experiment,
        "attack_n": s_best["n"],
        "best_defense": best["defense"],
        "baseline_defense": baseline["defense"],
        "containment_rate": 1 - s_best["rate"],            # measured, point estimate
        "containment_floor": 1 - hi,                        # measured, defensible lower bound (95%)
        "containment_ceiling": 1 - lo,
        "success_best": s_best,
        "success_baseline": s_base,
        "residual_point_usd": residual(s_best),            # assumptions x point estimate (can be $0)
        "residual_floor_usd": residual_floor,              # assumptions x 95% floor: the headline residual, never $0 at finite n
        "residual_baseline_usd": residual(s_base),
        # Avoided is a central estimate: baseline point minus defended point, so it never goes negative when the
        # undefended run itself saw no successes. The floor residual above is the separate, conservative downside.
        "risk_reduced_usd": residual(s_base) - residual(s_best),
    }


def all_item_risks(items=None, experiment: str = "first-run", assumptions: dict = ASSUMPTIONS) -> list:
    """A row per item that has a preregistered run for the experiment, ordered by item id."""
    if items is None:
        items = sorted({f.name.split("-")[0] for f in item_folders()})
    out = []
    for it in items:
        r = item_risk(it, experiment, assumptions)
        if r:
            out.append(r)
    return out
