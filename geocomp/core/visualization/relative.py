# SPDX-License-Identifier: GPL-2.0-or-later
"""Relative error ellipses: how well the vector between two stations is known (specs/19 §3 item 4).

``specs/19`` §3 item 4. A relative ellipse is the error ellipse of the
*difference* between two stations' positions, from their joint covariance:

    Sigma_d = J Sigma J^T,   J = [ -I  +I ] over the two stations' components

-- :func:`~geocomp.core.statistics.ellipses.relative_ellipse`, with a held
station contributing nothing. It answers "how well do I know this line", which
is usually the question a survey was for, and it is often far smaller than
either station's absolute ellipse: two stations fixed by the same observations
move together.

Drawn for every pair of stations an observation joins, at the middle of the
line between them. A solution that carries only each station's own covariance
block -- from the sparse path (NFR-008), or from DynAdjust without
``--output-all-covariances`` -- has nothing to draw them from, and gets none
rather than ellipses that would assume the stations uncorrelated.

A geocentric solution's difference is in X, Y, Z: it is turned into the
horizon at the line's middle and then onto the display grid, as the absolute
ellipses are (:mod:`~geocomp.core.visualization.display`).
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

import numpy as np

from geocomp.core.geodesy.cartesian import cartesian_to_geodetic, enu_rotation
from geocomp.core.models import CoordinateSystem, ErrorEllipse, Network, Solution
from geocomp.core.statistics.ellipses import error_ellipse

if TYPE_CHECKING:
    from geocomp.core.visualization.display import DisplayGrid

__all__ = ["RelativeEllipse", "observed_pairs", "relative_ellipses"]


@dataclass(frozen=True)
class RelativeEllipse:
    """The ellipse of the line from *first* to *second*, and where to draw it.

    Attributes:
        centre: The line's middle, in the plane the stations are drawn in.
        distance: The line's length in that plane.
    """

    first: str
    second: str
    ellipse: ErrorEllipse
    centre: tuple[float, float]
    distance: float


def observed_pairs(network: Network) -> list[tuple[str, str]]:
    """Every pair of distinct stations some observation joins, once, in the order first met."""
    seen: dict[frozenset[str], tuple[str, str]] = {}
    for observation in network.observations.values():
        stations = list(dict.fromkeys(observation.stations))
        for i, first in enumerate(stations):
            for second in stations[i + 1 :]:
                seen.setdefault(frozenset((first, second)), (first, second))
    return list(seen.values())


def relative_ellipses(
    solution: Solution,
    pairs: Iterable[tuple[str, str]],
    *,
    shown: Solution | None = None,
    grid: DisplayGrid | None = None,
) -> list[RelativeEllipse]:
    """The relative ellipse of each pair, at the solution's own confidence.

    Args:
        shown: The solution as it is drawn, when that differs -- a geocentric
            one in its display grid (:func:`~geocomp.core.visualization.display.for_display`);
            the centres and lengths are read from it.
        grid: That grid, so a geocentric ellipse is turned onto it.

    Returns:
        Nothing when the solution carries no covariance between stations, or no
        horizontal components. A pair with a station the solution does not
        estimate -- a held one -- is left out: it has nowhere to be drawn from,
        and the line's ellipse would be the free station's own.
    """
    covariance = solution.parameter_covariance
    if covariance is None:
        return []
    stations = {s.station_id: s for s in solution.adjusted_stations}
    drawn = {s.station_id: s for s in (shown or solution).adjusted_stations}
    if not stations:
        return []
    cartesian = next(iter(stations.values())).position.system is CoordinateSystem.CARTESIAN
    components = ("x", "y", "z") if cartesian else ("e", "n")
    where = {label: index for index, label in enumerate(covariance.labels)}
    if not any(f"{station}.{components[0]}" in where for station in stations):
        return []
    matrix = np.asarray(covariance.matrix, dtype=float)
    confidence = next((s.ellipse.confidence for s in stations.values() if s.ellipse is not None), 0.95)
    dof = solution.statistics.degrees_of_freedom if solution.statistics is not None else None

    found: list[RelativeEllipse] = []
    for first, second in pairs:
        if first not in stations or second not in stations or first not in drawn or second not in drawn:
            continue
        # The difference second - first as a selection of the parameters; a
        # held station has none, and contributes no uncertainty to the line.
        selector = np.zeros((len(components), matrix.shape[0]))
        for row, component in enumerate(components):
            if (column := where.get(f"{second}.{component}")) is not None:
                selector[row, column] += 1.0
            if (column := where.get(f"{first}.{component}")) is not None:
                selector[row, column] -= 1.0
        if not selector.any():
            continue
        difference = selector @ matrix @ selector.T
        bearing = 0.0
        if cartesian:
            middle = 0.5 * (_xyz(stations[first]) + _xyz(stations[second]))
            latitude, longitude, _height = cartesian_to_geodetic(*middle, _ellipsoid())
            rotation = enu_rotation(latitude, longitude)
            difference = (rotation @ difference @ rotation.T)[:2, :2]
            if grid is not None:
                from geocomp.core.visualization.display import grid_bearing_of_north

                bearing = grid_bearing_of_north(latitude, longitude, grid.projection)
        ellipse = error_ellipse(difference, confidence=confidence, degrees_of_freedom=dof)
        if bearing:
            ellipse = replace(ellipse, orientation=(ellipse.orientation + bearing) % math.pi)
        (e1, n1), (e2, n2) = _plan(drawn[first]), _plan(drawn[second])
        found.append(
            RelativeEllipse(
                first=first,
                second=second,
                ellipse=ellipse,
                centre=(0.5 * (e1 + e2), 0.5 * (n1 + n2)),
                distance=math.hypot(e2 - e1, n2 - n1),
            )
        )
    return found


def _xyz(station) -> np.ndarray:
    return np.array([q.value for q in station.position.values], dtype=float)


def _plan(station) -> tuple[float, float]:
    east, north = station.position.values[0].value, station.position.values[1].value
    return float(east), float(north)


def _ellipsoid():
    from geocomp.core.adjustment.geocentric import ELLIPSOID

    return ELLIPSOID
