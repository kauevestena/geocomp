# SPDX-License-Identifier: GPL-2.0-or-later
"""Assembling levelling lines into an adjustable network (FR-504, FR-802).

``specs/10-module-levelling.md`` sections 4 and 5.

Reduced lines become ``HEIGHT_DIFFERENCE`` observations and the adjustment core
does the rest -- free and constrained solutions, the global test, data snooping,
reliability, per-benchmark and relative height uncertainties. Nothing here
reimplements any of it, which is what makes levelling a cheap second technique
rather than a second pipeline.

Three things this module does own.

**The weighting decision.** A reduced line arrives carrying an uncertainty
propagated from its staff readings. That figure is rigorous and usually
optimistic: it knows nothing of refraction, staff calibration or a tripod
settling between backsight and foresight. The ``k * sqrt(L)`` and
``k * sqrt(n)`` models of :mod:`geocomp.core.adjustment.weighting` are fitted to
lines that suffered all three. Both are offered, neither is chosen silently, and
the choice is recorded in the network's metadata so the variance factor can be
read in the light of it.

**Two ways to build a network, because there are two questions.**

:func:`build_network` treats each **line** as one observation between two
permanent points. Turning points do not appear: a turning point is a staff
position that existed for four minutes, nobody wants its height, and putting it
in the network would add one parameter and one observation each -- zero
redundancy, no effect on anything, and a solution cluttered with points that
cannot be checked.

:func:`build_setup_network` treats each **setup** as its own observations, so
every foresighted station is adjusted. This is the one to use for extreme sights
(FR-502): the several foresights of a setup share their backsight, and they
enter the adjustment as a :class:`~geocomp.core.models.observation.Cluster`
carrying that correlation (FR-104). Splitting them into independent observations
would discard a correlation that is real and that *helps* -- see
:mod:`geocomp.core.techniques.levelling.schemes`.

**The height-type refusal.** Levelling determines orthometric heights; GNSS
determines ellipsoidal ones. Differencing the two is wrong by the geoid
undulation -- tens of metres across much of Brazil -- and the result looks
entirely plausible. So mixing them without a geoid model raises, rather than
warning (FR-802, FR-804).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from geocomp.core.adjustment.weighting import DifferenceWeighting, ExtentKind
from geocomp.core.errors import ValidationError
from geocomp.core.findings import Finding, Severity
from geocomp.core.models import (
    Cluster,
    ClusterKind,
    ConstraintMode,
    ConstraintSpec,
    CoordinateSystem,
    HeightType,
    Network,
    Observation,
    ObservationType,
    Position,
    Station,
    StationType,
)
from geocomp.core.techniques.levelling.line import LineReduction
from geocomp.core.techniques.levelling.schemes import SetupReduction
from geocomp.core.uncertainty import Covariance, Quantity
from geocomp.core.units import Unit

__all__ = [
    "NO_CRS",
    "Benchmark",
    "LevellingNetworkResult",
    "build_network",
    "build_setup_network",
    "weighting_for",
]

#: Stand-in CRS for a levelling network with no planimetry. A
#: :class:`~geocomp.core.models.position.Position` requires a CRS and GeoComp
#: does not infer one; a levelling-only network genuinely has none, and saying
#: so explicitly beats borrowing an EPSG code that would claim a datum the
#: heights do not belong to.
NO_CRS = "LOCAL"


@dataclass(frozen=True)
class Benchmark:
    """A station whose height is known, and how well.

    Attributes:
        height: The published height, with its uncertainty. A ``None``
            uncertainty is not accepted: a benchmark held with no stated
            precision is either exact or weighted, and which of the two changes
            every statistic downstream.
        height_type: What the height is measured from. Checked across the whole
            network, not per station -- one ellipsoidal height among orthometric
            ones is exactly the mistake FR-802 exists to catch.
        fixed: Held exactly rather than weighted. A single fixed benchmark is
            the ordinary constrained levelling network; several are a network
            that will show the disagreement between them in its residuals,
            which is usually what you want to see.
    """

    station: str
    height: Quantity
    height_type: HeightType = HeightType.ORTHOMETRIC
    fixed: bool = True
    geoid_model: str | None = None

    def __post_init__(self) -> None:
        if self.height.unit is not Unit.METRE:
            raise ValidationError(
                "benchmark_height_wrong_unit",
                station=self.station,
                received=self.height.unit.name,
                expected=Unit.METRE.name,
            )
        if self.height_type is HeightType.NONE:
            raise ValidationError(
                "benchmark_without_height_type",
                station=self.station,
                expected=(
                    "ORTHOMETRIC, NORMAL or ELLIPSOIDAL; a benchmark whose height type "
                    "is unrecorded cannot be checked against the others"
                ),
            )
        if not self.fixed and self.height.is_exact:
            raise ValidationError(
                "weighted_benchmark_without_uncertainty",
                station=self.station,
                expected=(
                    "a height with a non-zero uncertainty; a weighted constraint with "
                    "no uncertainty is a fixed constraint under another name"
                ),
            )


@dataclass
class LevellingNetworkResult:
    """A network built from levelling lines, and what was decided building it."""

    network: Network
    weighting: DifferenceWeighting | None = None
    height_type: HeightType = HeightType.ORTHOMETRIC
    findings: tuple[Finding, ...] = ()
    meta: dict[str, Any] = field(default_factory=dict)


def weighting_for(
    mode: str,
    *,
    sigma_per_km: float = 0.0,
    sigma_per_setup: float = 0.0,
) -> DifferenceWeighting | None:
    """Build the weighting the ``level.weighting`` setting names.

    Returns ``None`` when the chosen model has no coefficient configured, so the
    caller falls back to the propagated reading uncertainty and says so. The
    alternative -- substituting the other model's coefficient because it happens
    to be present -- would weight the network by a figure the user never chose.
    """
    if mode == "length":
        if sigma_per_km <= 0.0:
            return None
        return DifferenceWeighting(ExtentKind.LENGTH, sigma_per_km, Unit.METRE, "km")
    if mode == "setups":
        if sigma_per_setup <= 0.0:
            return None
        return DifferenceWeighting(ExtentKind.COUNT, sigma_per_setup, Unit.METRE, "setups")
    raise ValidationError(
        "unknown_weighting_mode",
        received=mode,
        expected="one of: length, setups",
    )


def build_network(
    reductions: list[LineReduction],
    benchmarks: list[Benchmark],
    *,
    network_id: str = "levelling",
    crs: str = "",
    weighting: DifferenceWeighting | None = None,
    geoid_model: str | None = None,
) -> LevellingNetworkResult:
    """Turn reduced lines into a network the adjustment core can solve.

    One observation per line, between its two endpoints. **Turning points are
    not stations here**: see the module docstring, and use
    :func:`build_setup_network` when the intermediate points are wanted.

    Args:
        reductions: The lines, already reduced.
        benchmarks: The stations whose heights are known. May be empty, giving a
            free network -- which is a legitimate and often preferable thing to
            adjust first, because it shows the observations' internal
            consistency without a datum's errors mixed in.
        weighting: The stochastic model. ``None`` keeps each line's propagated
            uncertainty and records that it did.
        geoid_model: Names the model relating ellipsoidal and orthometric
            heights, which is what makes mixing them permissible at all.
    """
    if not reductions:
        raise ValidationError(
            "levelling_network_without_lines",
            network=network_id,
            expected="at least one reduced line",
        )

    height_type = _agreed_height_type(benchmarks, geoid_model)
    findings: list[Finding] = []
    network = Network(id=network_id, crs=crs or NO_CRS)

    known = {benchmark.station: benchmark for benchmark in benchmarks}
    for station_id in _line_stations(reductions):
        network.add_station(_station(station_id, known.get(station_id), crs, height_type))

    missing = sorted(set(known) - network.station_ids())
    if missing:
        raise ValidationError(
            "benchmark_not_in_network",
            network=network_id,
            received=missing,
            expected=(
                "benchmarks that the levelling actually touched; a constraint on a "
                "station no line reached does nothing and hides the fact that the "
                "network is unconstrained"
            ),
        )

    for reduction in reductions:
        _add_line(network, reduction, weighting, findings)

    orphans = sorted(
        shot.to_station
        for reduction in reductions
        for shot in reduction.side_shots
    )
    if orphans:
        findings.append(
            Finding(
                code="levelling_side_shots_not_adjusted",
                severity=Severity.INFO,
                message=(
                    f"{len(orphans)} side shot(s) were levelled from these lines and are "
                    "not in the network: a spur observed once has no redundancy, so "
                    "adjusting it would change nothing. Their heights follow from the "
                    "adjusted line. Use build_setup_network to adjust every point"
                ),
                stations=tuple(orphans),
            )
        )

    if weighting is None:
        findings.append(
            Finding(
                code="levelling_weighted_by_propagation",
                severity=Severity.INFO,
                message=(
                    "the network was weighted by each line's propagated reading "
                    "uncertainty, no k*sqrt(L) or k*sqrt(n) model having been "
                    "configured. That figure knows nothing of refraction, staff "
                    "calibration or a tripod settling, so expect a variance factor "
                    "above one"
                ),
            )
        )
    else:
        findings.append(
            Finding(
                code="levelling_weighted_by_model",
                severity=Severity.INFO,
                message=(
                    f"the network was weighted by {weighting.describe}, replacing each "
                    "line's propagated reading uncertainty"
                ),
            )
        )

    if not benchmarks:
        findings.append(
            Finding(
                code="levelling_network_is_free",
                severity=Severity.INFO,
                message=(
                    "no benchmark was supplied, so the network is free: it has one "
                    "datum defect and determines every height difference but no height. "
                    "Adjust it with an inner or minimum constraint"
                ),
            )
        )

    network.require_valid()
    return LevellingNetworkResult(
        network=network,
        weighting=weighting,
        height_type=height_type,
        findings=tuple(findings),
        meta={
            "weighting": weighting.to_dict() if weighting else None,
            "height_type": height_type.name,
            "geoid_model": geoid_model,
        },
    )


def _agreed_height_type(
    benchmarks: list[Benchmark], geoid_model: str | None
) -> HeightType:
    """The one height type of the network, or a refusal naming the offenders.

    FR-802 and FR-804. The refusal is hard rather than a warning: differencing
    an ellipsoidal height against an orthometric one is wrong by the geoid
    undulation, which is tens of metres across much of Brazil, and the resulting
    heights look entirely reasonable.
    """
    if not benchmarks:
        return HeightType.ORTHOMETRIC

    types = {benchmark.height_type for benchmark in benchmarks}
    if len(types) == 1:
        return next(iter(types))

    if geoid_model:
        # A geoid model makes the mixture *expressible*, but converting one type
        # to the other is FR-804's job and needs the model's grid, which GeoComp
        # does not carry yet. Refusing with a different message is honest;
        # returning one of the two types silently would not be.
        raise ValidationError(
            "geoid_conversion_not_available",
            geoid_model=geoid_model,
            received=sorted(height_type.value for height_type in types),
            expected=(
                "benchmarks of one height type. A geoid model was named, but converting "
                "between height types needs its grid, which arrives with the GNSS "
                "module; until then, convert the heights before building the network"
            ),
        )

    offenders = {
        benchmark.station: benchmark.height_type.value for benchmark in benchmarks
    }
    raise ValidationError(
        "mixed_height_types",
        received=offenders,
        expected=(
            "benchmarks of one height type, or a geoid model to relate them. "
            "Differencing an ellipsoidal height against an orthometric one is wrong "
            "by the geoid undulation and produces a plausible-looking answer"
        ),
    )


def _line_stations(reductions: list[LineReduction]) -> list[str]:
    """Only the lines' endpoints, in first-seen order.

    Turning points are deliberately absent. They are not stations in any sense
    that matters: no mark, no name anyone will use again, and no observation of
    their own once the line has been summed.
    """
    ordered: list[str] = []
    for reduction in reductions:
        for station in (reduction.from_station, reduction.to_station):
            if station not in ordered:
                ordered.append(station)
    return ordered


def _station(
    station_id: str,
    benchmark: Benchmark | None,
    crs: str,
    height_type: HeightType,
) -> Station:
    if benchmark is None:
        return Station(id=station_id, station_type=StationType.MARK)

    zero = Quantity.exact(0.0, Unit.METRE)
    position = Position(
        values=(zero, zero, benchmark.height),
        # A levelling network has no planimetry. The two zeros are placeholders
        # in a three-component Position, not coordinates, and the constraint
        # below names only "up" so nothing ever reads them as coordinates.
        system=CoordinateSystem.PROJECTED,
        crs=crs or NO_CRS,
        height_type=height_type,
        geoid_model=benchmark.geoid_model,
    )
    constraint = ConstraintSpec(
        mode=ConstraintMode.FIXED if benchmark.fixed else ConstraintMode.WEIGHTED,
        components=frozenset({"up"}),
        position=position,
        covariance=None
        if benchmark.fixed
        else Covariance.diagonal({"up": benchmark.height.variance}, {"up": Unit.METRE}),
    )
    return Station(
        id=station_id,
        approx_position=position,
        constraint=constraint,
        station_type=StationType.BENCHMARK,
    )


def _add_line(
    network: Network,
    reduction: LineReduction,
    weighting: DifferenceWeighting | None,
    findings: list[Finding],
) -> None:
    """Add one line's height difference as a single observation."""
    network.add_observation(
        Observation(
            id=reduction.line_id,
            type=ObservationType.HEIGHT_DIFFERENCE,
            stations=(reduction.from_station, reduction.to_station),
            values=(_weighted(reduction, weighting, findings),),
            meta={
                "line": reduction.line_id,
                "setups": reduction.setup_count,
                "length_km": reduction.length_km,
                "accumulated_imbalance": reduction.accumulated_imbalance,
            },
        )
    )


def _weighted(
    reduction: LineReduction,
    weighting: DifferenceWeighting | None,
    findings: list[Finding],
) -> Quantity:
    """The line's height difference under the chosen stochastic model."""
    if weighting is None:
        return reduction.height_difference.detached()

    if weighting.kind is ExtentKind.LENGTH:
        if reduction.length_km is None:
            raise ValidationError(
                "line_length_unknown",
                line=reduction.line_id,
                expected=(
                    "sight distances, so the line's length is known. Length weighting "
                    "needs it; weight by setup count instead, or record the distances"
                ),
            )
        extent = float(reduction.length_km)
    elif weighting.kind is ExtentKind.COUNT:
        extent = float(reduction.setup_count)
    else:
        extent = 1.0

    if extent <= 0.0:
        raise ValidationError(
            "line_extent_not_positive",
            line=reduction.line_id,
            kind=weighting.kind.value,
            received=extent,
            expected=(
                "a positive extent; a zero one gives zero uncertainty and therefore an "
                "infinite weight that would dominate the network"
            ),
        )

    if reduction.length_km is not None and reduction.length_km < 1e-6:
        findings.append(
            Finding(
                code="levelling_line_very_short",
                severity=Severity.WARNING,
                message=(
                    f"line {reduction.line_id} is {reduction.length_km * 1000.0:.1f} m "
                    "long, so a length-weighted sigma for it is almost zero and its "
                    "weight almost infinite"
                ),
                stations=(reduction.from_station, reduction.to_station),
                value=float(reduction.length_km),
            )
        )

    return weighting.reweight(reduction.height_difference.detached(), extent)




def build_setup_network(
    reductions: list[SetupReduction],
    benchmarks: list[Benchmark],
    *,
    network_id: str = "levelling_setups",
    crs: str = "",
    geoid_model: str | None = None,
) -> LevellingNetworkResult:
    """Turn reduced *setups* into a network, one observation per foresight.

    The form to use for extreme sights (FR-502), and the only one in which the
    correlation between a setup's foresights reaches the adjustment: each such
    setup contributes a :class:`~geocomp.core.models.observation.Cluster`
    carrying the full covariance from :func:`reduce_setup`, so the shared
    backsight cancels in every difference the adjustment forms between two of
    them, exactly as it does in reality.

    No weighting model is applied. A setup's height differences come straight
    from its staff readings, and there is no line length or setup count to scale
    by -- ``k * sqrt(L)`` is a model of how error accumulates *along a line*, and
    a single setup is not one. Substituting it here would be applying a model
    outside the regime it was fitted in.
    """
    if not reductions:
        raise ValidationError(
            "levelling_network_without_setups",
            network=network_id,
            expected="at least one reduced setup",
        )

    height_type = _agreed_height_type(benchmarks, geoid_model)
    findings: list[Finding] = []
    network = Network(id=network_id, crs=crs or NO_CRS)
    known = {benchmark.station: benchmark for benchmark in benchmarks}

    ordered: list[str] = []
    for reduction in reductions:
        for station in (reduction.from_station, *reduction.to_stations):
            if station not in ordered:
                ordered.append(station)
    for station_id in ordered:
        network.add_station(_station(station_id, known.get(station_id), crs, height_type))

    missing = sorted(set(known) - network.station_ids())
    if missing:
        raise ValidationError(
            "benchmark_not_in_network",
            network=network_id,
            received=missing,
            expected="benchmarks that the levelling actually touched",
        )

    clustered = 0
    for reduction in reductions:
        observation_ids = [
            f"{reduction.setup_id}.{station}" for station in reduction.to_stations
        ]
        cluster_id = f"{reduction.setup_id}" if reduction.is_clustered else None

        for index, station in enumerate(reduction.to_stations):
            network.add_observation(
                Observation(
                    id=observation_ids[index],
                    type=ObservationType.HEIGHT_DIFFERENCE,
                    stations=(reduction.from_station, station),
                    values=(reduction.height_differences[index].detached(),),
                    setup_id=reduction.setup_id,
                    cluster_id=cluster_id,
                    meta={"setup": reduction.setup_id},
                )
            )

        if cluster_id is not None:
            clustered += 1
            network.add_cluster(
                Cluster(
                    id=cluster_id,
                    kind=ClusterKind.GENERIC,
                    observation_ids=tuple(observation_ids),
                    covariance=Covariance(
                        matrix=np.asarray(reduction.covariance.matrix, dtype=float),
                        labels=tuple(observation_ids),
                        units=tuple(reduction.covariance.units),
                        mode=reduction.covariance.mode,
                        strategies=reduction.covariance.strategies,
                    ),
                )
            )

    if clustered:
        findings.append(
            Finding(
                code="levelling_setups_clustered",
                severity=Severity.INFO,
                message=(
                    f"{clustered} setup(s) carried several foresights and entered the "
                    "network as correlated clusters. They share their backsight, so it "
                    "cancels in every difference the adjustment forms between two "
                    "points of one setup -- which makes those differences better "
                    "determined, not worse"
                ),
            )
        )

    if not benchmarks:
        findings.append(
            Finding(
                code="levelling_network_is_free",
                severity=Severity.INFO,
                message=(
                    "no benchmark was supplied, so the network is free: it has one "
                    "datum defect and determines every height difference but no height"
                ),
            )
        )

    network.require_valid()
    return LevellingNetworkResult(
        network=network,
        weighting=None,
        height_type=height_type,
        findings=tuple(findings),
        meta={"height_type": height_type.name, "geoid_model": geoid_model},
    )
