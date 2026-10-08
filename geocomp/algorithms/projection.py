# SPDX-License-Identifier: GPL-2.0-or-later
"""Which projection a CRS is, from QGIS's own database (specs/07 §4.4).

``core.geodesy.projection`` inverts a Transverse Mercator; what it cannot do is
tell which one a CRS string names, because that needs a projection database.
QGIS carries one, so the algorithms ask it: the combination, to place a
projected network geocentrically (P9b), and *Adjust with DynAdjust*, to give
DynAdjust the latitude and longitude of a projected network's stations
(P12c-45). UTM and Transverse Mercator on GRS80 are read; anything else is
``None``, and the caller refuses the network by name rather than placing it
with a projection it is not in.
"""

from __future__ import annotations

import math

from geocomp.core.errors import GeoCompError
from geocomp.core.geodesy.ellipsoid import ELLIPSOIDS
from geocomp.core.geodesy.projection import ProjectionParameters, utm_parameters

__all__ = ["projection_of", "projection_of_crs"]


def projection_of(proj: str) -> ProjectionParameters | None:
    """A UTM or Transverse Mercator PROJ definition on GRS80, as parameters.

    ``None`` for anything else: the combination then refuses the input by name,
    which is better than placing it with a projection it is not in.
    """
    tokens: dict[str, str] = {}
    for token in proj.split():
        key, _, value = token.lstrip("+").partition("=")
        tokens[key] = value
    # Stated, not defaulted: "+datum=WGS84" names no ellipsoid and is not GRS80.
    if tokens.get("ellps") != "GRS80":
        return None
    ellipsoid = ELLIPSOIDS["GRS80"]
    try:
        if tokens.get("proj") == "utm":
            return utm_parameters(
                int(tokens["zone"]), southern_hemisphere="south" in tokens, ellipsoid=ellipsoid
            )
        if tokens.get("proj") == "tmerc":
            return ProjectionParameters(
                ellipsoid=ellipsoid,
                central_meridian=math.radians(float(tokens.get("lon_0", 0.0))),
                latitude_of_origin=math.radians(float(tokens.get("lat_0", 0.0))),
                scale_factor=float(tokens.get("k", tokens.get("k_0", 1.0))),
                false_easting=float(tokens.get("x_0", 0.0)),
                false_northing=float(tokens.get("y_0", 0.0)),
                name=proj,
            )
    except (KeyError, ValueError, GeoCompError):
        return None
    return None


def projection_of_crs(crs: str) -> ProjectionParameters | None:
    """The projection the CRS *crs* names -- ``EPSG:31982``, say -- or ``None``.

    ``None`` as well for a CRS QGIS does not know and for a geographic one,
    which is not projected at all.
    """
    from qgis.core import QgsCoordinateReferenceSystem

    reference = QgsCoordinateReferenceSystem(crs.strip())
    if not reference.isValid() or reference.isGeographic():
        return None
    return projection_of(reference.toProj())
