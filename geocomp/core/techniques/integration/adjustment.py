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

**A local combination** (P9b) is adjusted in the frame its observations need:
heights alone when every observation is a height or a height difference --
total-station work reduced to trigonometric differences, with levelling -- and
three dimensions otherwise. In three dimensions, geocentric or local, a station
known only through heights has no horizontal position anything determines, and
is refused by name rather than left for a singular matrix to report.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime

from geocomp.core.adjustment.difference_network import approximate_values
from geocomp.core.adjustment.least_squares import (
    AdjustmentOptions,
    AdjustmentRun,
    adjust,
    to_observation_results,
    to_solution,
)
from geocomp.core.adjustment.parameters import Frame
from geocomp.core.adjustment.undulations import GeoidResidual, geoid_residuals
from geocomp.core.adjustment.variance_components import VarianceComponents, estimate_variance_components
from geocomp.core.errors import ValidationError
from geocomp.core.geoid import GeoidModel
from geocomp.core.models import (
    ConstraintMode,
    DatumDefinition,
    HeightType,
    Network,
    ObservationType,
    Solution,
)
from geocomp.core.models.solution import Provenance
from geocomp.core.statistics.reliability import DEFAULT_ALPHA, DEFAULT_BETA, reliability
from geocomp.core.statistics.tests import data_snooping, global_test
from geocomp.core.techniques.integration.breakdown import TechniqueSummary, technique_breakdown
from geocomp.core.techniques.integration.combine import Combination, Routing, route

__all__ = ["CombinedAdjustment", "adjust_combination", "adjustment_frame", "stations_without_horizontal"]

_GRAVITY = (ObservationType.GRAVITY, ObservationType.GRAVITY_DIFFERENCE)

#: What the height frame adjusts, and what fixes nothing horizontal anywhere.
_HEIGHTS = frozenset(
    {
        ObservationType.HEIGHT_DIFFERENCE,
        ObservationType.ORTHOMETRIC_HEIGHT,
        ObservationType.ELLIPSOIDAL_HEIGHT,
    }
)
#: What the solution's heights are, by the frame it was adjusted in: the
#: geocentric frame computes ellipsoidal heights; a local one's are the
#: levelling's and the total station's, along the plumb line, in heights alone,
#: and whatever the inputs held them as in three dimensions.
_HEIGHT_TYPES = {
    Frame.GEOCENTRIC_3D: HeightType.ELLIPSOIDAL,
    Frame.HEIGHT_1D: HeightType.ORTHOMETRIC,
    Frame.SPACE_3D: HeightType.NONE,
}

_HORIZONTAL_HOLDS = frozenset({"x", "y", "z", "latitude", "longitude", "easting", "northing"})


@dataclass(frozen=True)
class CombinedAdjustment:
    """A combination adjusted, and everything it concluded.

    Attributes:
        solution: The geometric solution, in the combination's frame and epoch,
            with provenance naming every input and transformation.
        run: The raw geometric adjustment; ``None`` when DynAdjust ran it.
        routing: Which engine, and why.
        breakdown: Per technique, and for the constraint and geoid rows; empty
            when DynAdjust ran it, whose output carries no redundancy numbers.
        geoid: The geoid model tested at each station it was needed at.
        variance_components: When asked for.
        gravity: The gravity network's own result, when there was one.
    """

    combination: Combination
    solution: Solution
    run: AdjustmentRun | None
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
            the request (gravity, a type DynAdjust lacks, a local system,
            orthometric heights) and records why; otherwise it refuses rather
            than substitute an engine --
            :func:`geocomp.engines.dynadjust.combination.adjust_with_dynadjust`
            is the DynAdjust path.
        estimate_components: Estimate a variance factor per technique; the
            solution is then the rescaled network's.

    Raises:
        ValidationError: ``combination_gravity_without_its_network``;
            ``combination_routed_to_dynadjust``; ``combination_geoid_in_local_frame``;
            ``combination_station_without_horizontal``; ``combination_disconnected``.
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
        # engine behind the request.
        raise ValidationError(
            "combination_routed_to_dynadjust",
            reason=routing.reason,
            expected=(
                "requested_engine='in_house' here, or the DynAdjust path "
                "(geocomp.engines.dynadjust.combination.adjust_with_dynadjust)"
            ),
        )
    if geoid is not None and not combination.geocentric:
        raise ValidationError(
            "combination_geoid_in_local_frame",
            frame=combination.frame,
            expected=(
                "no geoid for a local combination: its heights are what its inputs "
                "say they are, and nothing in it is ellipsoidal for a geoid to relate"
            ),
        )

    frame = adjustment_frame(combination)
    approximate = None
    if frame is Frame.HEIGHT_1D:
        start = approximate_values(network, frame)
        if not start.is_connected:
            raise ValidationError(
                "combination_disconnected",
                received=start.components,
                expected="one network: the inputs share no station that ties these pieces together",
            )
        approximate = start.values
    else:
        missing = stations_without_horizontal(network)
        if missing:
            raise ValidationError(
                "combination_station_without_horizontal",
                stations=missing[:10],
                count=len(missing),
                expected=(
                    "an observation that fixes each station horizontally -- a GNSS vector, "
                    "a direction, a distance -- or a horizontal hold; these are reached "
                    "only through heights, so nothing determines where they are"
                ),
            )

    options = AdjustmentOptions(frame=frame, datum=datum, confidence=confidence, geoid=geoid)
    components = None
    if estimate_components:
        components = estimate_variance_components(network, options, approximate=approximate)
        run, adjusted_network = components.run, components.network
    else:
        run, adjusted_network = adjust(network, options, approximate=approximate), network

    breakdown = technique_breakdown(run, adjusted_network)
    residuals = geoid_residuals(run)
    provenance = Provenance(
        created=datetime.now(UTC),
        algorithm_id="combined_adjustment",
        engine="in_house",
        parameters={
            **combination.provenance_parameters(),
            "routing": {"engine": routing.engine, "reason": routing.reason},
            "adjustment_frame": frame.value,
            "geoid_model": geoid.id if geoid is not None and run.undulations else None,
            # The per-technique figures travel on the solution, so a report
            # rendered from the saved document later says what this one does.
            "technique_breakdown": [_summary(s) for s in breakdown],
            "geoid_residuals": [{k: _plain(v) for k, v in asdict(r).items()} for r in residuals],
            "variance_components": (
                None
                if components is None
                else {
                    c.group: {
                        "factor": float(c.factor),
                        "std_dev": float(c.std_dev),
                        "redundancy": float(c.redundancy),
                        "observations": int(c.observations),
                    }
                    for c in components.components
                }
            ),
        },
        input_ids=combination.inputs,
    )
    test = global_test(run.variance_factor_aposteriori, run.degrees_of_freedom, confidence=confidence)
    snooping = data_snooping(
        run.residuals,
        run.cofactor_residuals,
        run.system.weight,
        run.system.row_labels,
        variance_factor=run.variance_factor_aposteriori,
        degrees_of_freedom=run.degrees_of_freedom,
        confidence=confidence,
    )
    checks = reliability(
        run.cofactor_residuals,
        run.system.weight,
        run.system.design,
        run.cofactor_parameters,
        run.system.row_labels,
        alpha=DEFAULT_ALPHA,
        beta=DEFAULT_BETA,
    )
    solution = to_solution(
        run,
        adjusted_network,
        solution_id=solution_id,
        crs=combination.frame,
        epoch=combination.epoch,
        datum=datum,
        height_type=_HEIGHT_TYPES[frame],
        provenance=provenance,
        observation_results=to_observation_results(run, snooping=snooping, reliability=checks),
        global_test=test,
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
        breakdown=breakdown,
        geoid=residuals,
        variance_components=components,
        gravity=gravity_result,
    )


def adjustment_frame(combination: Combination) -> Frame:
    """The frame the combination is adjusted in: geocentric, or for a local one
    heights alone when that is all it holds, and three dimensions otherwise."""
    if combination.geocentric:
        return Frame.GEOCENTRIC_3D
    types = {o.type for o in combination.network.observations.values() if o.is_active}
    return Frame.HEIGHT_1D if types and types <= _HEIGHTS else Frame.SPACE_3D


def stations_without_horizontal(network: Network) -> list[str]:
    """Stations nothing places horizontally: reached only through heights, and
    not held in a horizontal component."""
    touched: dict[str, set[ObservationType]] = {}
    for observation in network.observations.values():
        if observation.is_active:
            for station in observation.stations:
                touched.setdefault(station, set()).add(observation.type)
    return sorted(
        station.id
        for station in network.stations.values()
        if touched.get(station.id, set()) <= _HEIGHTS
        and not (
            station.constraint.mode is not ConstraintMode.FREE
            and station.constraint.components & _HORIZONTAL_HOLDS
        )
    )


def _summary(summary: TechniqueSummary) -> dict:
    return {**{k: _plain(v) for k, v in asdict(summary).items()}, "uncheckable": list(summary.uncheckable)}


def _plain(value):
    """A number as JSON will take it: NumPy's integers are not ints to ``json``."""
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return value
    if isinstance(value, int):
        return int(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return value


def _with_gravity(network, gravity):
    """The network as routing should see it: with the gravity observations in."""
    if gravity is None:
        return network
    from dataclasses import replace

    return replace(network, observations={**network.observations, **gravity.network.observations})
