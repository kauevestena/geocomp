# SPDX-License-Identifier: GPL-2.0-or-later
"""The least-squares iteration driver.

``specs/06-adjustment-core.md`` sections 2.2 and 6. Linearise, solve, update,
repeat, then assemble the result and its statistics into the one
:class:`~geocomp.core.models.Solution` type every engine fills.

**Non-convergence is a reported failure, never a silently returned last
iterate.** A result that looks like coordinates but is really iteration seven of
a diverging sequence is worse than no result, because nothing about it says so.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from geocomp.core.adjustment.datum import DatumDefect, constraint_matrix, detect_defect
from geocomp.core.adjustment.normal_equations import LinearisedSystem, assemble, solve
from geocomp.core.adjustment.parameters import (
    Frame,
    ParameterLayout,
    weighted_constraints,
)
from geocomp.core.errors import ComputationError, ValidationError
from geocomp.core.models import (
    AdjustedStation,
    AdjustmentStatistics,
    CoordinateSystem,
    DatumDefinition,
    Epoch,
    HeightType,
    Network,
    Observation,
    ObservationResult,
    ObservationType,
    Position,
    Provenance,
    Solution,
    SolutionKind,
)
from geocomp.core.statistics.ellipses import error_ellipse
from geocomp.core.uncertainty import Covariance, Quantity
from geocomp.core.units import Unit, circular_mean

__all__ = [
    "AdjustmentOptions",
    "AdjustmentRun",
    "adjust",
    "starting_values",
    "to_observation_results",
    "to_solution",
]


@dataclass
class AdjustmentOptions:
    """How the adjustment is to be run.

    Attributes:
        frame: The working coordinate frame.
        datum: How the datum defect is removed. ``INNER_CONSTRAINT`` and
            ``MINIMUM_CONSTRAINT`` both use the G matrix; the difference is
            which stations define it.
        datum_stations: For an inner-constraint solution, the stations the datum
            is defined on -- the **stable reference block** in a deformation
            analysis (FR-835). ``None`` means all of them.
        variance_factor_apriori: sigma_0^2 assumed a priori.
        convergence: Maximum parameter correction accepted as converged, in the
            frame's linear unit. 0.1 mm by default, per ``specs/06`` section 2.2.
        max_iterations: After which non-convergence is reported as a failure.
        confidence: For the global test and the error ellipses.
    """

    frame: Frame = Frame.PLANE_2D
    datum: DatumDefinition = DatumDefinition.CONSTRAINED
    datum_stations: list[str] | None = None
    variance_factor_apriori: float = 1.0
    convergence: float = 1e-4
    max_iterations: int = 20
    confidence: float = 0.95
    auxiliary: dict[str, tuple[str, ...]] = field(default_factory=dict)


@dataclass
class AdjustmentRun:
    """Everything one adjustment produced, before it becomes a Solution.

    Kept separate so the statistics modules can work from the raw matrices --
    the residual cofactor matrix, redundancy numbers and reliability all need
    Qxx and Qvv, which a Solution does not carry.
    """

    layout: ParameterLayout
    system: LinearisedSystem
    parameters: np.ndarray
    residuals: np.ndarray
    cofactor_parameters: np.ndarray
    cofactor_residuals: np.ndarray
    redundancy: np.ndarray
    variance_factor_aposteriori: float
    #: The sigma_0^2 assumed a priori, carried through so the Solution records
    #: the value the global test was actually run against rather than assuming 1.
    variance_factor_apriori: float
    degrees_of_freedom: int
    iterations: int
    converged: bool
    max_correction: float
    condition_number: float
    defect: DatumDefect
    method: str
    observations: list[Observation]

    @property
    def parameter_covariance(self) -> np.ndarray:
        """Sigma_x = sigma_0^2 * Qxx, using the a posteriori variance factor."""
        return self.variance_factor_aposteriori * self.cofactor_parameters


def adjust(
    network: Network,
    options: AdjustmentOptions | None = None,
    *,
    approximate: dict[str, dict[str, float]] | None = None,
) -> AdjustmentRun:
    """Run the adjustment to convergence.

    Args:
        network: Stations, observations and clusters. Only active observations
            participate -- a rejected one keeps its record but not its weight.
        options: See :class:`AdjustmentOptions`.
        approximate: Starting coordinates, ``{station: {component: value}}``.
            Defaults to each station's approximate position.

    Raises:
        ComputationError: on non-convergence, or on a rank deficiency the datum
            choice does not resolve. Both name what went wrong.
    """
    options = options or AdjustmentOptions()
    observations = list(network.active_observations)
    if not observations:
        raise ComputationError(
            "no_active_observations",
            network=network.id,
            expected="at least one active observation",
        )

    # A direction is meaningless without the orientation unknown of its setup:
    # the circle's zero is arbitrary, so a direction treated as an absolute
    # azimuth is not merely imprecise, it is unrelated to the geometry. Deriving
    # the unknowns from the observations rather than requiring the caller to
    # declare them removes a footgun that produces a diverging adjustment and no
    # explanation -- which is exactly how this was found, in phase P3.
    auxiliary = _with_orientation_unknowns(observations, options.auxiliary)
    layout = ParameterLayout.build(network, options.frame, auxiliary=auxiliary)
    values = starting_values(network, layout, options, approximate, auxiliary=auxiliary)
    x = np.array([values[slot.owner][slot.component] for slot in layout.slots])

    defect = detect_defect(observations, options.frame)
    constraints = _constraints_for(options, layout, values, defect)
    # FR-222. A weighted benchmark is an observation of its own coordinates, so
    # it belongs in the system beside the levelled differences rather than in a
    # datum-removal step -- see WeightedConstraint for what happened while these
    # rows were missing.
    weighted = weighted_constraints(network, layout, options.frame)

    converged = False
    correction = float("inf")
    iteration = 0
    system: LinearisedSystem | None = None
    result = None

    # `iteration` is read after the loop -- in the non-convergence message and
    # in the result -- so the usual rename to `_iteration` would break both.
    for iteration in range(1, options.max_iterations + 1):  # noqa: B007
        system = assemble(observations, network.clusters, layout, x, weighted=weighted)
        result = solve(system, layout, constraints=constraints)
        x = x + result.x
        correction = float(np.max(np.abs(result.x))) if result.x.size else 0.0
        if correction < options.convergence:
            converged = True
            break

    if system is None or result is None:  # pragma: no cover - loop always runs once
        raise ComputationError("adjustment_did_not_run", network=network.id)

    if not converged:
        raise ComputationError(
            "adjustment_did_not_converge",
            network=network.id,
            iterations=iteration,
            max_correction=correction,
            threshold=options.convergence,
            expected=(
                "convergence within the iteration limit. Check the approximate "
                "coordinates and the observations for a gross error; a diverging "
                "adjustment usually means one of the two is badly wrong"
            ),
        )

    # Re-linearise *and* re-solve at the converged parameters, so the reported
    # design matrix, residuals, cofactor and statistics all describe the
    # solution rather than the last step towards it. The final correction is
    # below the convergence threshold by construction; taking it makes the
    # residuals exact rather than exact-to-within-the-threshold.
    system = assemble(observations, network.clusters, layout, x, weighted=weighted)
    result = solve(system, layout, constraints=constraints)
    x = x + result.x
    residuals = system.design @ result.x - system.misclosure

    degrees_of_freedom = system.observation_count - layout.size + defect.size * bool(
        constraints is not None
    )
    weighted = float(residuals @ system.weight @ residuals)
    variance_factor = (
        weighted / degrees_of_freedom if degrees_of_freedom > 0 else float("nan")
    )

    cofactor_residuals = _residual_cofactor(system, result.cofactor)
    redundancy = np.diag(cofactor_residuals @ system.weight)

    return AdjustmentRun(
        layout=layout,
        system=system,
        parameters=x,
        residuals=residuals,
        cofactor_parameters=result.cofactor,
        cofactor_residuals=cofactor_residuals,
        redundancy=redundancy,
        variance_factor_aposteriori=variance_factor,
        variance_factor_apriori=options.variance_factor_apriori,
        degrees_of_freedom=degrees_of_freedom,
        iterations=iteration,
        converged=True,
        max_correction=correction,
        condition_number=result.condition_number,
        defect=defect,
        method=result.method,
        observations=observations,
    )


def _residual_cofactor(system: LinearisedSystem, cofactor_parameters: np.ndarray) -> np.ndarray:
    """Qvv = Q_ll - A Qxx A^T, with Q_ll the inverse of the weight matrix.

    The diagonal of ``Qvv P`` gives the redundancy numbers, which is what makes
    data snooping and reliability possible at all.
    """
    q_ll = np.linalg.inv(system.weight)
    return q_ll - system.design @ cofactor_parameters @ system.design.T


def _with_orientation_unknowns(
    observations: list[Observation], declared: dict[str, tuple[str, ...]]
) -> dict[str, tuple[str, ...]]:
    """Add an orientation unknown for every direction set that lacks one.

    Keyed by the setup id each direction names. A caller that has already
    declared one keeps theirs, so an explicitly shared orientation -- two setups
    on one pillar, say -- is not overridden.
    """
    auxiliary = {owner: tuple(names) for owner, names in declared.items()}
    for observation in observations:
        if observation.type is not ObservationType.DIRECTION:
            continue
        owner = observation.setup_id or observation.meta.get("orientation_owner")
        if owner is None:
            continue
        names = auxiliary.get(owner, ())
        if "orientation" not in names:
            auxiliary[owner] = (*names, "orientation")
    return auxiliary


def _initial_orientations(
    observations: list[Observation],
    auxiliary: dict[str, tuple[str, ...]],
    coordinates: dict[str, dict[str, float]],
    frame: Frame,
) -> dict[str, float]:
    """Estimate each direction set's orientation from the approximate coordinates.

    The orientation is the difference between the azimuth a target *should* have
    and the circle reading it *did* have, averaged over the set. Starting it at
    zero instead -- which is what a plain default does -- linearises the whole
    set half a turn or more from the solution, and the adjustment diverges with
    a message about convergence that says nothing about the real cause.

    The average is circular, for the same reason face reduction's is: the
    differences straddle the zero of the circle as often as not.
    """
    if frame.dimension < 2:
        return {}

    per_owner: dict[str, list[float]] = {}
    for observation in observations:
        if observation.type is not ObservationType.DIRECTION:
            continue
        owner = observation.setup_id or observation.meta.get("orientation_owner")
        if owner is None or "orientation" not in auxiliary.get(owner, ()):
            continue
        origin_id, target_id = observation.stations
        origin = coordinates.get(origin_id)
        target = coordinates.get(target_id)
        if origin is None or target is None:
            continue
        azimuth = math.atan2(target["e"] - origin["e"], target["n"] - origin["n"])
        per_owner.setdefault(owner, []).append(azimuth - observation.values[0].value)

    return {
        owner: circular_mean(differences) for owner, differences in per_owner.items()
    }


def starting_values(
    network: Network,
    layout: ParameterLayout,
    options: AdjustmentOptions,
    approximate: dict[str, dict[str, float]] | None,
    *,
    auxiliary: dict[str, tuple[str, ...]] | None = None,
) -> dict[str, dict[str, float]]:
    """Assemble the starting parameter values, including fixed components."""
    values: dict[str, dict[str, float]] = {}

    for station_id, station in network.stations.items():
        supplied = (approximate or {}).get(station_id, {})
        entry: dict[str, float] = {}
        for component in options.frame.components:
            if (station_id, component) in layout.fixed_values:
                entry[component] = layout.fixed_values[(station_id, component)]
            elif component in supplied:
                entry[component] = float(supplied[component])
            elif station.approx_position is not None:
                entry[component] = _from_position(station, component, options.frame)
            else:
                raise ValidationError(
                    "missing_approximate_coordinates",
                    station=station_id,
                    component=component,
                    expected=(
                        "an approximate position on the station, or a value in the "
                        "approximate argument; the linearised model needs a point "
                        "to linearise about"
                    ),
                )
        values[station_id] = entry

    auxiliary = auxiliary if auxiliary is not None else options.auxiliary
    orientations = _initial_orientations(
        network.active_observations, auxiliary, values, options.frame
    )
    for owner, names in auxiliary.items():
        values.setdefault(owner, {})
        for name in names:
            default = orientations.get(owner, 0.0) if name == "orientation" else 0.0
            values[owner].setdefault(name, default)

    return values


def _from_position(station, component: str, frame: Frame) -> float:
    """Read one frame component out of a station's approximate position.

    The reading half of :attr:`~geocomp.core.adjustment.parameters.Frame.position_components`;
    :func:`to_solution` is the writing half, and both go through that one
    mapping so they cannot drift apart again.
    """
    position = station.approx_position
    index = frame.components.index(component)
    name = frame.position_components[index]
    if position.system is CoordinateSystem.PROJECTED:
        return position.component(name).value
    return position.values[frame.position_indices[index]].value


def _constraints_for(
    options: AdjustmentOptions,
    layout: ParameterLayout,
    values: dict[str, dict[str, float]],
    defect: DatumDefect,
) -> np.ndarray | None:
    """The G matrix, for the datum modes that need one."""
    if options.datum not in (
        DatumDefinition.INNER_CONSTRAINT,
        DatumDefinition.MINIMUM_CONSTRAINT,
    ):
        return None
    if defect.size == 0:
        return None
    return constraint_matrix(layout, values, defect, station_ids=options.datum_stations)


def to_observation_results(
    run: AdjustmentRun,
    *,
    snooping=None,
    reliability=None,
) -> list[ObservationResult]:
    """Gather what the adjustment and its tests concluded about each row.

    One :class:`~geocomp.core.models.ObservationResult` per **row** of the
    design matrix, not per observation: a GNSS baseline contributes three, and
    collapsing them would hide which component carries the residual.

    Lives here rather than in the calling algorithm because phase P6 assembles
    the same structure from DynAdjust's output, and two assemblers would drift.

    Args:
        snooping: A :class:`~geocomp.core.statistics.tests.SnoopingReport`, for
            the standardised residuals and w-test decisions.
        reliability: A :class:`~geocomp.core.statistics.reliability.ReliabilityReport`,
            for the minimal detectable bias and the external effect.
    """
    by_row_reliability = {}
    if reliability is not None:
        by_row_reliability = {result.row: result for result in reliability.results}

    by_row_candidate = {}
    if snooping is not None:
        by_row_candidate = {candidate.row: candidate for candidate in snooping.candidates}
        by_row_candidate.update({candidate.row: candidate for candidate in snooping.uncheckable})

    statistics = dict(snooping.statistics) if snooping is not None else {}

    results: list[ObservationResult] = []
    for row, (observation_id, _component) in enumerate(run.system.row_labels):
        reliability_result = by_row_reliability.get(row)
        candidate = by_row_candidate.get(row)

        w_test = None
        if candidate is not None and snooping is not None:
            w_test = candidate.to_test_result(snooping.confidence, snooping.distribution)

        results.append(
            ObservationResult(
                observation_id=observation_id,
                residual=float(run.residuals[row]),
                standardised_residual=statistics.get(row),
                redundancy=float(run.redundancy[row]),
                w_test=w_test,
                minimal_detectable_bias=(
                    reliability_result.minimal_detectable_bias if reliability_result else None
                ),
                external_reliability=(
                    reliability_result.external_effect if reliability_result else None
                ),
            )
        )
    return results


def to_solution(
    run: AdjustmentRun,
    network: Network,
    *,
    solution_id: str,
    crs: str,
    epoch: Epoch,
    datum: DatumDefinition,
    system: CoordinateSystem = CoordinateSystem.PROJECTED,
    height_type: HeightType = HeightType.NONE,
    geoid_model: str | None = None,
    provenance: Provenance | None = None,
    observation_results: list[ObservationResult] | None = None,
    global_test=None,
    confidence: float = 0.95,
) -> Solution:
    """Assemble an :class:`AdjustmentRun` into the shared Solution type.

    This is the boundary that makes phase P6 a cross-validation: DynAdjust's
    parser fills the same structure, so visualisation, reporting and multi-epoch
    analysis never learn which engine produced a result.

    Args:
        system: How to read the three components. ``PROJECTED`` is the ordinary
            case and the default. ``CARTESIAN`` is for a network held in
            geocentric X, Y and Z -- the adjustment is the same arithmetic
            either way, since :class:`Frame` ``SPACE_3D`` is three orthogonal
            metres whatever they are called, but the *label* is not a detail:
            it is what lets a comparison against a DynAdjust solution know that
            the two are in one frame, and what stops it differencing an easting
            against an X if they are not (specs/07 section 6).
        geoid_model: The model that related the height systems, when one did
            (FR-804). Recorded on every adjusted position, so a report and a
            multi-epoch comparison can both see it.
    """
    covariance = run.parameter_covariance
    units = run.layout.component_units()
    adjusted: list[AdjustedStation] = []

    for station_id in run.layout.station_ids():
        columns = run.layout.station_columns(station_id)
        if not columns:
            continue

        # Each frame component goes into *its own* slot of the position triple,
        # never simply the next free one: a 1D frame estimates a height, and a
        # height belongs in "up". Padding in order would put it in "easting",
        # which is what phase P2 did and phase P4 found -- see
        # Frame.position_components.
        quantities: list[Quantity] = [Quantity.exact(0.0, Unit.METRE)] * 3
        for component, index in zip(
            run.layout.frame.components, run.layout.frame.position_indices, strict=True
        ):
            column = columns.get(component)
            if column is None:
                value = run.layout.fixed_values[(station_id, component)]
                quantities[index] = Quantity.exact(value, Unit.METRE)
            else:
                quantities[index] = Quantity(
                    value=float(run.parameters[column]),
                    variance=float(covariance[column, column]),
                    unit=units[column],
                )

        indices = [columns[c] for c in run.layout.frame.components if c in columns]
        block = Covariance(
            matrix=covariance[np.ix_(indices, indices)],
            labels=tuple(
                f"{station_id}.{c}" for c in run.layout.frame.components if c in columns
            ),
            units=tuple(units[i] for i in indices),
        )

        # The ellipse is part of the answer, not an optional extra: FR-254 asks
        # for it wherever a station is reported, and computing it here means a
        # DynAdjust solution carries one on the same terms.
        ellipse = None
        if len(indices) >= 2:
            ellipse = error_ellipse(
                covariance[np.ix_(indices[:2], indices[:2])],
                confidence=confidence,
                degrees_of_freedom=run.degrees_of_freedom,
            )

        adjusted.append(
            AdjustedStation(
                station_id=station_id,
                position=Position(
                    values=tuple(quantities[:3]),  # type: ignore[arg-type]
                    system=system,
                    crs=crs,
                    epoch=epoch,
                    height_type=height_type,
                    # FR-804. Which model related the height systems is part of
                    # the answer, not a note beside it: two solutions computed
                    # with different geoid models are not comparable, and this
                    # is what makes the difference visible instead of silent.
                    geoid_model=geoid_model,
                ),
                covariance=block,
                ellipse=ellipse,
            )
        )

    statistics = AdjustmentStatistics(
        n_observations=run.system.observation_count,
        n_parameters=run.layout.size,
        n_constraints=run.defect.size if run.method == "bordered" else 0,
        degrees_of_freedom=run.degrees_of_freedom,
        variance_factor_apriori=run.variance_factor_apriori,
        variance_factor_aposteriori=run.variance_factor_aposteriori,
        global_test=global_test,
        iterations=run.iterations,
        converged=run.converged,
        max_correction=run.max_correction,
        condition_number=run.condition_number,
    )

    return Solution(
        id=solution_id,
        network_id=network.id,
        kind=SolutionKind.ADJUSTMENT,
        crs=crs,
        epoch=epoch,
        datum_definition=datum,
        adjusted_stations=tuple(adjusted),
        parameter_covariance=Covariance(
            matrix=covariance,
            labels=tuple(run.layout.labels()),
            units=tuple(units),
        ),
        observation_results=tuple(observation_results or ()),
        statistics=statistics,
        provenance=provenance,
    )
