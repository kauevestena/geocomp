# SPDX-License-Identifier: GPL-2.0-or-later
"""Measured distances carried to the grid of a projected CRS (FR-405).

``specs/09-module-total-station.md`` section 2.6.

A plane adjustment computes a distance from two grid coordinates. A total
station measures one on the ground. The two differ by two factors, and on a
projected CRS neither is small:

* **to the ellipsoid**, ``R / (R + h)`` -- about 157 ppm for each kilometre of
  height above it;
* **to the grid**, the point scale factor *k* of the projection -- on UTM, 0.9996
  at the central meridian and about 1.001 at a zone's edge, so -400 to +1000 ppm.

Until P12c-13's audit found it, nothing applied either: *Classical network*
adjusted ground distances as though they were grid distances, which against grid
control shows up as residuals and a variance factor nobody can explain. The two
reductions themselves had existed since P3 in :mod:`.reductions`, each carrying
the uncertainty of what it used; this applies them to a network.

**Where the scale factor comes from.** *k* depends on the projection, which is
QGIS's business rather than the core's, so it is a function the caller supplies:
grid coordinates in, *k* out. The algorithm builds it from the CRS through QGIS;
a test can build it from :func:`geocomp.core.geodesy.point_scale_factor`.

**Over a line, Simpson's rule.** *k* varies along a line, and the factor the
line needs is its mean. ``(k1 + 4 km + k2) / 6`` is exact when *k* is quadratic
in position, which on a Transverse Mercator it is to the first order that
matters; over a 10 km line at a zone's edge, the midpoint alone would be off by
about 0.1 ppm, Simpson's by nothing measurable.

**What is treated as exact, and why.** *k* is evaluated at the approximate
coordinates. It changes by about 0.007 ppm per metre of position at a UTM zone's
edge, so the approximate position's error is below anything a distance meter
resolves, and *k* enters as exact. The height does not: a metre of height is
0.16 ppm, so the approximate height's uncertainty is carried
(:func:`.reductions.reduce_to_ellipsoid`).
"""

from __future__ import annotations

import dataclasses
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from geocomp.core.errors import ValidationError
from geocomp.core.models import HeightType, Network, Observation, ObservationType
from geocomp.core.techniques.total_station.reductions import (
    DEFAULT_EARTH_RADIUS,
    reduce_to_ellipsoid,
    reduce_to_projection,
)
from geocomp.core.uncertainty import Quantity
from geocomp.core.units import Unit

__all__ = ["GRID_REDUCTION", "GridReduction", "ScaleFactor", "reduce_distances_to_grid"]

#: The key under which a reduced observation records what was done to it, in
#: its ``meta``. Its presence is also what stops a second reduction.
GRID_REDUCTION = "grid_reduction"

#: Grid coordinates (easting, northing) in, the projection's point scale factor out.
ScaleFactor = Callable[[float, float], float]

#: The two distance types a grid reduction applies to. A horizontal distance is
#: measured on the ground and is reduced twice; an ellipsoid distance is already
#: on the ellipsoid and is only scaled.
_REDUCED = (ObservationType.HORIZONTAL_DISTANCE, ObservationType.ELLIPSOID_DISTANCE)


@dataclass(frozen=True)
class GridReduction:
    """One distance's journey from where it was measured to the grid.

    Attributes:
        observation_id: The distance.
        measured: As observed.
        height: The mean ellipsoidal height it was reduced to the ellipsoid
            with; ``None`` for an ellipsoid distance, which needs none.
        scale_factor: The line's mean point scale factor, by Simpson's rule.
        grid: The distance in the grid, with the uncertainty of the height
            added to the measurement's.
    """

    observation_id: str
    measured: Quantity
    height: Quantity | None
    scale_factor: float
    grid: Quantity

    @property
    def factor(self) -> float:
        """The combined factor applied: grid over measured."""
        return self.grid.value / self.measured.value

    @property
    def parts_per_million(self) -> float:
        """The reduction as a scale, in parts per million: what a reader compares
        with a distance meter's own ppm."""
        return (self.factor - 1.0) * 1e6

    def to_dict(self) -> dict[str, Any]:
        """The record an observation carries in its ``meta``."""
        return {
            "measured": self.measured.to_dict(),
            "height": self.height.to_dict() if self.height is not None else None,
            "scale_factor": self.scale_factor,
            "factor": self.factor,
        }


def reduce_distances_to_grid(
    network: Network,
    *,
    scale_factor: ScaleFactor,
    undulation: Quantity | None = None,
    earth_radius: float = DEFAULT_EARTH_RADIUS,
) -> tuple[Network, tuple[GridReduction, ...]]:
    """The network with each measured distance carried to the grid (FR-405).

    Every active horizontal distance is reduced to the ellipsoid at the mean
    height of its two ends and then to the grid; every ellipsoid distance is
    only scaled. Each reduced observation keeps its id, carries its new value
    with the height's uncertainty added, and records the measured value and the
    factors in its ``meta`` under :data:`GRID_REDUCTION`. A distance that
    already carries that record is left alone, so reducing twice reduces once.

    Args:
        scale_factor: *k* at a grid coordinate (see :data:`ScaleFactor`).
        undulation: *N*, so that ``h = H + N``. Required when the approximate
            heights are orthometric, which is what a total-station network
            built from a field book has.
        earth_radius: For the reduction to the ellipsoid.

    Returns:
        A new network, the input untouched, and the record of every reduction.

    Raises:
        ValidationError: ``grid_reduction_without_position`` naming every
            station a distance ends at that has no approximate position;
            ``grid_reduction_without_height`` every one whose position carries
            no height type, since the height is then of unknown meaning;
            ``grid_reduction_without_undulation`` when the heights are
            orthometric and no *N* is given; and
            ``grid_reduction_of_clustered_distance`` for a distance held in a
            correlated cluster, whose covariance this would leave describing
            the measured value rather than the reduced one.
    """
    distances = [
        observation
        for observation in network.observations.values()
        if observation.type in _REDUCED
        and observation.is_active
        and GRID_REDUCTION not in observation.meta
    ]
    _check(network, distances, undulation)

    reduced = dataclasses.replace(
        network,
        stations=dict(network.stations),
        observations=dict(network.observations),
        clusters=dict(network.clusters),
        meta=dict(network.meta),
    )
    records = []
    for observation in distances:
        record = _reduce(network, observation, scale_factor, undulation, earth_radius)
        meta = {**observation.meta, GRID_REDUCTION: record.to_dict()}
        reduced.observations[observation.id] = dataclasses.replace(
            observation, values=(record.grid,), meta=meta
        )
        records.append(record)
    return reduced, tuple(records)


def _check(network: Network, distances: list[Observation], undulation: Quantity | None) -> None:
    ends = sorted({station for observation in distances for station in observation.stations})
    unplaced = [name for name in ends if network.stations[name].approx_position is None]
    if unplaced:
        raise ValidationError(
            "grid_reduction_without_position",
            received=unplaced,
            expected="an approximate position for every station a distance ends at",
        )
    clustered = sorted(observation.id for observation in distances if observation.cluster_id)
    if clustered:
        raise ValidationError(
            "grid_reduction_of_clustered_distance",
            received=clustered,
            expected="distances that are not part of a correlated cluster",
        )
    measured = [
        observation
        for observation in distances
        if observation.type is ObservationType.HORIZONTAL_DISTANCE
    ]
    types = {
        name: network.stations[name].approx_position.height_type
        for name in sorted({station for observation in measured for station in observation.stations})
    }
    heightless = [name for name, kind in types.items() if kind is HeightType.NONE]
    if heightless:
        raise ValidationError(
            "grid_reduction_without_height",
            received=heightless,
            expected="an approximate height, orthometric or ellipsoidal, for every station",
        )
    if undulation is None and HeightType.ORTHOMETRIC in types.values():
        raise ValidationError(
            "grid_reduction_without_undulation",
            received=sorted(name for name, kind in types.items() if kind is HeightType.ORTHOMETRIC),
            expected="the geoid undulation, so that each orthometric height becomes an ellipsoidal one",
        )


def _reduce(
    network: Network,
    observation: Observation,
    scale_factor: ScaleFactor,
    undulation: Quantity | None,
    earth_radius: float,
) -> GridReduction:
    start, end = (network.stations[name].approx_position for name in observation.stations)
    (e1, n1, h1), (e2, n2, h2) = start.values, end.values
    k = (
        scale_factor(e1.value, n1.value)
        + 4.0 * scale_factor((e1.value + e2.value) / 2.0, (n1.value + n2.value) / 2.0)
        + scale_factor(e2.value, n2.value)
    ) / 6.0
    (measured,) = observation.values

    height = None
    on_ellipsoid = measured
    if observation.type is ObservationType.HORIZONTAL_DISTANCE:
        height = (
            _ellipsoidal(h1, start.height_type, undulation)
            + _ellipsoidal(h2, end.height_type, undulation)
        ) * 0.5
        on_ellipsoid = reduce_to_ellipsoid(measured, height, earth_radius=earth_radius).distance
    grid = reduce_to_projection(on_ellipsoid, Quantity.exact(k, Unit.DIMENSIONLESS)).distance
    return GridReduction(
        observation_id=observation.id,
        measured=measured,
        height=height,
        scale_factor=k,
        grid=grid,
    )


def _ellipsoidal(height: Quantity, kind: HeightType, undulation: Quantity | None) -> Quantity:
    """*h* from a station's approximate height; :func:`_check` has already
    refused an orthometric height with no *N* to add."""
    if kind is HeightType.ORTHOMETRIC and undulation is not None:
        return height.detached() + undulation.detached()
    return height.detached()
