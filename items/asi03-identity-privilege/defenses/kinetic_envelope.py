"""The public decision table of the Kinetic Trust Protocol's kinetic envelope, as one pure function.

Source: ktp-rfc `specifications/kinetic-envelope.md` on main (9612f79, 2026-10-27) and its vector suite
`specifications/conformance/capacity-gate-v1.json` (17 vectors). This file imports nothing from the harness, so the
function can be checked against that suite on its own.

A is the demand a candidate action places on its environment and E the capacity the environment declares, on one
common scale. Both arrive as declared inputs. Nothing here senses, estimates or derives either one.

The table, in order:

  1. A declared profile must satisfy 0 <= m_veto < m_allow. An invalid profile is rejected before use. An omitted
     profile keeps the default m_veto = m_allow = 0.
  2. A and E must be finite, non-negative numbers. Anything else is rejected, and no margin is fabricated.
  3. E = 0 or A > E is `silent_veto` before any division. Approval does not lower it.
  4. Otherwise margin = 1 - A/E. margin <= m_veto is `silent_veto`; margin >= m_allow is `stable`; between the two,
     supervision deepens as the margin falls: metacognitive, then assisted, then regulated.
  5. capacityKnown = false clamps the result to at least `assisted`, and never lowers `regulated` or `silent_veto`.
  6. An existing supervision level is a floor: the result is never lower than it.

The band in step 4 is divided by the profile. It may declare `assisted_floor` and `metacognitive_floor` (the reference
profile's `assistedFloor` and `metacognitiveFloor`): regulated below the first, assisted up to the second, metacognitive
up to m_allow, with m_veto < assisted_floor < metacognitive_floor < m_allow. A profile that declares neither gets the
open interval split in three equal parts. That split is this gate's reading, not a sentence of the specification, which
says only that supervision deepens as the margin falls. With the default profile the band is empty and neither reading
applies.
"""
import math
from dataclasses import dataclass, field

LEVELS = ("stable", "metacognitive", "assisted", "regulated", "silent_veto")
RANK = {s: i for i, s in enumerate(LEVELS)}
DEFAULT_M_VETO = 0.0
DEFAULT_M_ALLOW = 0.0


@dataclass
class EnvelopeResult:
    supervision: str                      # one of LEVELS
    margin: float = None                  # 1 - A/E; None when evaluation stopped before division
    profile_accepted: bool = True
    division_performed: bool = False
    rationale: list = field(default_factory=list)

    @property
    def vetoed(self) -> bool:
        return self.supervision == "silent_veto"

    @property
    def execution_permitted(self) -> bool:
        """Autonomous execution: stable, or metacognitive (the agent's own check before acting, no reviewer)."""
        return self.supervision in ("stable", "metacognitive")

    @property
    def review_required(self) -> bool:
        return self.supervision in ("assisted", "regulated")


def _number(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def envelope(A, E, capacity_known: bool = True, thresholds: dict = None, existing: str = None) -> EnvelopeResult:
    """Evaluate one candidate action. `thresholds` is {"m_veto": x, "m_allow": y} or None for the default profile.
    `existing` is a supervision level already in force, which the result can only tighten."""
    why = []
    af = mf = None
    if thresholds is None:
        mv, ma = DEFAULT_M_VETO, DEFAULT_M_ALLOW
        why.append("profile omitted: m_veto = m_allow = 0")
    else:
        mv, ma = thresholds.get("m_veto"), thresholds.get("m_allow")
        if not (_number(mv) and _number(ma) and 0 <= mv < ma):
            return EnvelopeResult("silent_veto", None, False, False, ["profile rejected: thresholds must satisfy 0 <= m_veto < m_allow"])
        af = thresholds.get("assisted_floor", thresholds.get("assistedFloor"))
        mf = thresholds.get("metacognitive_floor", thresholds.get("metacognitiveFloor"))
        if (af is None) != (mf is None) or (af is not None and not (_number(af) and _number(mf) and mv < af < mf < ma)):
            return EnvelopeResult("silent_veto", None, False, False, ["profile rejected: band floors must satisfy m_veto < assisted_floor < metacognitive_floor < m_allow"])
    if not (_number(A) and _number(E)) or A < 0 or E < 0:
        return EnvelopeResult("silent_veto", None, True, False, ["invalid inputs: A and E must be finite, non-negative numbers on one scale; no margin fabricated"])
    floor = existing if existing in RANK else "stable"
    if E == 0 or A > E:
        why.append("E = 0" if E == 0 else f"A > E ({A:g} > {E:g})")
        why.append("capacity veto before division; approval does not lower it")
        return EnvelopeResult("silent_veto", None, True, False, why)
    margin = 1 - A / E
    if margin <= mv:
        sup = "silent_veto"
        why.append(f"margin {margin:.3f} <= m_veto {mv:g}")
    elif margin >= ma:
        sup = "stable"
        why.append(f"margin {margin:.3f} >= m_allow {ma:g}")
    else:
        if af is None:
            third = (ma - mv) / 3
            af, mf = mv + third, mv + 2 * third
            why.append("band floors not declared: equal thirds")
        sup = "regulated" if margin < af else ("assisted" if margin < mf else "metacognitive")
        why.append(f"margin {margin:.3f} inside ({mv:g}, {ma:g}), floors {af:g} and {mf:g}: {sup}")
    if not capacity_known and RANK[sup] < RANK["assisted"]:
        sup = "assisted"
        why.append("capacityKnown = false: at least assisted")
    if RANK[floor] > RANK[sup]:
        sup = floor
        why.append(f"existing supervision {floor} is a floor")
    return EnvelopeResult(sup, margin, True, True, why)
