# SPDX-License-Identifier: GPL-2.0-or-later
"""A geocentric solution, drawn on a map (``specs/19`` section 1.1, phase P9b).

A combined solution is in geocentric X, Y, Z (``Frame.GEOCENTRIC_3D``), and no
map draws those: X and Y are not a plane anyone looks at, and a layer in them
would put every station inside the Earth. This re-expresses a solution **for
display** in the UTM zone of its centroid -- easting, northing and ellipsoidal
height, the covariance turned into each station's horizon -- and leaves the
solution itself as it was computed.

**The grid names the solution's own frame.** A SIRGAS 2000 solution is drawn in
SIRGAS 2000's UTM zone by EPSG code. An ITRF one is drawn in a Transverse
Mercator grid on *that* ITRF, defined in WKT2 so the layer's CRS says
"ITRF2020 / UTM zone 22S". The obvious shortcut -- a bare GRS80 UTM string --
is matched by QGIS to "SIRGAS 2000 / UTM", which for an ITRF2020 solution at
2026 is a label decimetres of plate motion wrong.

**Ellipses and corrections are turned by the grid convergence.** The solution
states an ellipse's orientation from geodetic north; a UTM grid's north differs
from it by the meridian convergence, over a degree at a zone's edge. Drawn
without the turn, every ellipse on the map would lean by that much.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace

import numpy as np

from geocomp.core.adjustment.geocentric import ELLIPSOID
from geocomp.core.geodesy.cartesian import cartesian_to_geodetic, enu_rotation, geodetic_to_cartesian
from geocomp.core.geodesy.frames import canonical_frame
from geocomp.core.geodesy.projection import (
    ProjectionParameters,
    transverse_mercator,
    utm_parameters,
    utm_zone,
)
from geocomp.core.models import CoordinateSystem, HeightType, Network, Position, Solution
from geocomp.core.uncertainty import Covariance, Quantity
from geocomp.core.units import Unit

__all__ = ["DisplayGrid", "display_grid", "for_display", "grid_bearing_of_north"]

#: SIRGAS 2000 / UTM, by zone: 17N-22N and 17S-25S (EPSG 31971-31985).
_SIRGAS_NORTH = {zone: 31971 + zone - 17 for zone in range(17, 23)}
_SIRGAS_SOUTH = {zone: 31977 + zone - 17 for zone in range(17, 26)}

#: Latitude step for finding which way geodetic north points on the grid.
_NUDGE = 1e-7


@dataclass(frozen=True)
class DisplayGrid:
    """The grid a geocentric solution is drawn in.

    Attributes:
        crs: What QGIS reads: an EPSG code, or a WKT2 definition naming the frame.
        name: For a legend or a message, e.g. ``ITRF2020 / UTM zone 22S``.
    """

    crs: str
    name: str
    projection: ProjectionParameters


def display_grid(frame: str, latitude: float, longitude: float) -> DisplayGrid:
    """The UTM grid, on *frame*, of the zone containing *latitude*, *longitude*
    (radians)."""
    frame = canonical_frame(frame)
    zone = utm_zone(longitude)
    south = latitude < 0.0
    projection = utm_parameters(zone, southern_hemisphere=south)
    name = f"{frame} / UTM zone {zone}{'S' if south else 'N'}"
    codes = _SIRGAS_SOUTH if south else _SIRGAS_NORTH
    if frame == "SIRGAS2000" and zone in codes:
        return DisplayGrid(crs=f"EPSG:{codes[zone]}", name=name, projection=projection)
    return DisplayGrid(crs=_wkt(frame, zone, south), name=name, projection=projection)


def for_display(
    solution: Solution, network: Network | None = None
) -> tuple[Solution, Network | None, DisplayGrid | None]:
    """*solution* and *network* re-expressed in a display grid, if geocentric.

    A solution that is not in geocentric cartesian coordinates comes back as it
    is, with no grid: it is already something a map can draw.
    """
    positions = [s.position for s in solution.adjusted_stations]
    if not positions or any(p.system is not CoordinateSystem.CARTESIAN for p in positions):
        return solution, network, None
    centre = np.mean([[q.value for q in p.values] for p in positions], axis=0)
    latitude, longitude, _ = cartesian_to_geodetic(*centre, ELLIPSOID)
    grid = display_grid(solution.crs, latitude, longitude)

    stations = tuple(_station(station, grid) for station in solution.adjusted_stations)
    shown = replace(solution, crs=grid.crs, adjusted_stations=stations)
    if network is not None:
        network = replace(
            network,
            crs=grid.crs,
            stations={
                # Where to draw it, from its start or its hold. The constraint
                # itself is left as it is: only its mode reaches the map, and
                # its components and covariance are named in X, Y, Z.
                identifier: replace(
                    station,
                    approx_position=_position(station.approx_position or station.constraint.position, grid),
                )
                for identifier, station in network.stations.items()
            },
        )
    return shown, network, grid


def grid_bearing_of_north(latitude: float, longitude: float, projection: ProjectionParameters) -> float:
    """Which way geodetic north points on the grid: a clockwise angle from grid
    north, radians. Minus the meridian convergence, whichever sign convention
    that is quoted in."""
    east, north = transverse_mercator(latitude, longitude, projection)
    east2, north2 = transverse_mercator(latitude + _NUDGE, longitude, projection)
    return math.atan2(east2 - east, north2 - north)


# -- internals ---------------------------------------------------------------


def _station(station, grid: DisplayGrid):
    xyz = np.array([q.value for q in station.position.values])
    latitude, longitude, height = cartesian_to_geodetic(*xyz, ELLIPSOID)
    east, north = transverse_mercator(latitude, longitude, grid.projection)
    rotation = enu_rotation(latitude, longitude)
    bearing = grid_bearing_of_north(latitude, longitude, grid.projection)

    covariance = None
    variances = [q.variance for q in station.position.values]
    if station.covariance is not None and np.shape(station.covariance.matrix) == (3, 3):
        local = rotation @ np.asarray(station.covariance.matrix) @ rotation.T
        variances = [float(local[k, k]) for k in range(3)]
        covariance = Covariance(
            matrix=local,
            labels=tuple(f"{station.station_id}.{c}" for c in ("e", "n", "u")),
            units=(Unit.METRE,) * 3,
            mode=station.covariance.mode,
            strategies=station.covariance.strategies,
        )
    position = Position(
        values=tuple(
            Quantity(value=float(v), variance=float(var), unit=Unit.METRE)
            for v, var in zip((east, north, height), variances, strict=True)
        ),
        system=CoordinateSystem.PROJECTED,
        crs=grid.crs,
        epoch=station.position.epoch,
        height_type=HeightType.ELLIPSOIDAL,
        geoid_model=station.position.geoid_model,
    )
    ellipse = station.ellipse
    if ellipse is not None:
        ellipse = replace(ellipse, orientation=(ellipse.orientation + bearing) % math.pi)
    correction = station.correction
    if correction is not None:
        e, n, u = correction
        correction = (
            e * math.cos(bearing) + n * math.sin(bearing),
            -e * math.sin(bearing) + n * math.cos(bearing),
            u,
        )
    return replace(station, position=position, covariance=covariance, ellipse=ellipse, correction=correction)


def _position(position: Position | None, grid: DisplayGrid) -> Position | None:
    """A network position on the grid; one that is not geocentric or geodetic
    cannot be placed, and is dropped rather than drawn somewhere wrong."""
    if position is None:
        return None
    values = [q.value for q in position.values]
    if position.system is CoordinateSystem.GEODETIC:
        values = list(geodetic_to_cartesian(*values, ELLIPSOID))
    elif position.system is not CoordinateSystem.CARTESIAN:
        return None
    latitude, longitude, height = cartesian_to_geodetic(*values, ELLIPSOID)
    east, north = transverse_mercator(latitude, longitude, grid.projection)
    return Position(
        values=tuple(Quantity.exact(float(v), Unit.METRE) for v in (east, north, height)),
        system=CoordinateSystem.PROJECTED,
        crs=grid.crs,
        epoch=position.epoch,
        height_type=HeightType.ELLIPSOIDAL,
    )


def _wkt(frame: str, zone: int, south: bool) -> str:
    """A WKT2 UTM grid on *frame*, so the layer's CRS names it."""
    datum = f"International Terrestrial Reference Frame {frame[4:]}" if frame.startswith("ITRF") else frame
    degree = 'ANGLEUNIT["degree",0.0174532925199433]'
    metre = 'LENGTHUNIT["metre",1]'
    hemisphere = "S" if south else "N"
    return (
        f'PROJCRS["{frame} / UTM zone {zone}{hemisphere}",'
        f'BASEGEOGCRS["{frame}",DATUM["{datum}",'
        f'ELLIPSOID["GRS 1980",6378137,298.257222101,{metre}]],'
        f'PRIMEM["Greenwich",0,{degree}]],'
        f'CONVERSION["UTM zone {zone}{hemisphere}",METHOD["Transverse Mercator",ID["EPSG",9807]],'
        f'PARAMETER["Latitude of natural origin",0,{degree},ID["EPSG",8801]],'
        f'PARAMETER["Longitude of natural origin",{(zone - 1) * 6 - 177},{degree},ID["EPSG",8802]],'
        f'PARAMETER["Scale factor at natural origin",0.9996,SCALEUNIT["unity",1],ID["EPSG",8805]],'
        f'PARAMETER["False easting",500000,{metre},ID["EPSG",8806]],'
        f'PARAMETER["False northing",{10000000 if south else 0},{metre},ID["EPSG",8807]]],'
        f'CS[Cartesian,2],AXIS["easting (E)",east,ORDER[1],{metre}],'
        f'AXIS["northing (N)",north,ORDER[2],{metre}]]'
    )
