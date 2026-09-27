# SPDX-License-Identifier: GPL-2.0-or-later
"""The combined adjustment (``specs/13`` section 6, criteria 6 to 8).

Once :func:`~geocomp.core.techniques.integration.combine.combine` has put every
technique's observations in one frame at one epoch, the adjustment is the core's
ordinary business in ``Frame.GEOCENTRIC_3D``: each station's own vertical, the
geoid relating orthometric observations to the ellipsoidal heights it computes,
and every cluster whole. This module runs it and gathers what a combination
reports beyond a single-technique adjustment: the routing and its reason, the
per-technique breakdown, the geoid's residuals and, when asked, the variance
components by technique.

**Gravity is adjusted beside the geometry, not inside it.** No observation in
the combination relates gravity to position -- a vertical gradient would, and
is not modelled -- so the normal equations of the two are block-diagonal, and
adjusting them together would give exactly the answers adjusting them apart
gives. Apart keeps each in the parameter space it belongs to, and the gravity
network's drift model with it. What the combination guarantees is the thing
``specs/13`` asks: gravity is not dropped, it is adjusted by the in-house core,
and the reason is on the result.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from geocomp.core.adjustment.least_squares import AdjustmentOptions, AdjustmentRun, adjust, to_solution
from geocomp.core.adjustment.parameters import Frame
from geocomp.core.adjustment.undulations import GeoidResidual, geoid_residuals
from geocomp.core.adjustment.variance_components import VarianceComponents, estimate_variance_components
from geocomp.core.errors import ValidationError
from geocomp.core.geoid import GeoidModel
from geocomp.core.models import DatumDefinition, ObservationType, Solution
from geocomp.core.models.solution import Provenance
from geocomp.core.techniques.integration.breakdown import TechniqueSummary, technique_breakdown
from geocomp.core.techniques.integration.combine import Combination, Routing, route

__all__ = ["CombinedAdjustment", "adjust_combination"]

_GRAVITY = (ObservationType.GRAVITY, ObservationType.GRAVITY_DIFFERENCE)


@dataclass(frozen=True)
class CombinedAdjustment:
    """A combination adjusted, and everything it concluded.

    Attributes:
        solution: The geometric solution, in the combination's frame and epoch,
            with provenance naming every input and transformation.
        run: The raw geometric adjustment.
        routing: Which engine, and why.
        breakdown: Per technique, and for the constraint and geoid rows.
        geoid: The geoid model tested at each station it was needed at.
        variance_components: When asked for.
        gravity: The gravity network's own result, when there was one.
    """

    combination: Combination
    solution: Solution
    run: AdjustmentRun
    routing: Routing
    breakdown: tuple[TechniqueSummary, ...]
    geoid: tuple[GeoidResidual, ...]
    variance_components: VarianceComponents | None = None
    gravity: object | None = None


def adjust_combination(
    combination: Combination,
    *,
    geoid: GeoidModel | None = None,
    requested_engine: str = "in_house",
    gravity=None,
    estimate_components: bool = False,
    datum: DatumDefinition = DatumDefinition.FIXED,
    confidence: float = 0.95,
    solution_id: str = "combined",
) -> CombinedAdjustment:
    """Adjust *combination* in-house, with *gravity* beside it if given.

    Args:
        gravity: A :class:`~geocomp.core.techniques.gravimetry.network.GravityNetwork`,
            built with its drift model. Gravity observations merged into the
            combination itself are refused: without their drift unknowns they
            would be adjusted as though drift-free.
        requested_engine: The engine asked for. This function is the in-house
            path: asked for DynAdjust, it proceeds only when routing overrides
            the request (gravity, or a type DynAdjust lacks) and records why;
            otherwise it refuses rather than substitute an engine.
        estimate_components: Estimate a variance factor per technique; the
            solution is then the rescaled network's.

    Raises:
        ValidationError: ``combination_gravity_without_its_network``;
            ``combination_routed_to_dynadjust``.
    """
    network = combination.network
    merged_gravity = [o.id for o in network.observations.values() if o.type in _GRAVITY]
    if merged_gravity:
        raise ValidationError(
            "combination_gravity_without_its_network",
            observations=merged_gravity[:10],
            expected=(
                "gravity passed as its own network (gravity=), built with its drift "
                "model; merged into the geometry it would be adjusted as though drift-free"
            ),
        )
    routing = route(_with_gravity(network, gravity), requested_engine)
    if routing.engine != "in_house":
        # Adjusting in-house after routing chose DynAdjust would substitute an
        # engine behind the request; running DynAdjust on a combination is P9b.
        raise ValidationError(
            "combination_routed_to_dynadjust",
            reason=routing.reason,
            expected=(
                "requested_engine='in_house' here; running DynAdjust on a "
                "combination is the Integration menu's (P9b)"
            ),
        )

    options = AdjustmentOptions(frame=Frame.GEOCENTRIC_3D, datum=datum, confidence=confidence, geoid=geoid)
    components = None
    if estimate_components:
        components = estimate_variance_components(network, options)
        run, adjusted_network = components.run, components.network
    else:
        run, adjusted_network = adjust(network, options), network

    provenance = Provenance(
        created=datetime.now(UTC),
        algorithm_id="combined_adjustment",
        engine="in_house",
        parameters={
            **combination.provenance_parameters(),
            "routing": {"engine": routing.engine, "reason": routing.reason},
            "geoid_model": geoid.id if geoid is not None and run.undulations else None,
            "variance_components": (
                None
                if components is None
                else {c.group: {"factor": c.factor, "std_dev": c.std_dev} for c in components.components}
            ),
        },
        input_ids=combination.inputs,
    )
    solution = to_solution(
        run,
        adjusted_network,
        solution_id=solution_id,
        crs=combination.frame,
        epoch=combination.epoch,
        datum=datum,
        provenance=provenance,
        confidence=confidence,
    )

    gravity_result = None
    if gravity is not None:
        from geocomp.core.techniques.gravimetry.network import adjust_gravity_network

        gravity_result = adjust_gravity_network(
            gravity, confidence=confidence, solution_id=f"{solution_id}:gravity"
        )

    return CombinedAdjustment(
        combination=combination,
        solution=solution,
        run=run,
        routing=routing,
        breakdown=technique_breakdown(run, adjusted_network),
        geoid=geoid_residuals(run),
        variance_components=components,
        gravity=gravity_result,
    )


def _with_gravity(network, gravity):
    """The network as routing should see it: with the gravity observations in."""
    if gravity is None:
        return network
    from dataclasses import replace

    return replace(network, observations={**network.observations, **gravity.network.observations})
