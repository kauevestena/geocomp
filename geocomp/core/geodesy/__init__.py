# SPDX-License-Identifier: GPL-2.0-or-later
"""Ellipsoidal geometry: the reductions the rest of GeoComp was missing.

``specs/07-engine-dynadjust.md`` section 4.4 named the gap precisely -- a
projected network cannot reach DynAdjust because GeoComp has no inverse
projection and no geodetic-to-geocentric conversion -- and three of P6's exit
criteria trace back to it.

Nothing here shifts a datum. Every function converts between two ways of writing
one point on **one** ellipsoid, exactly and reversibly. Moving between reference
frames or epochs is a different operation, with its own uncertainty, assigned to
the QGIS/PROJ infrastructure by ``specs/14-multi-epoch-monitoring.md`` section 3.
"""

from __future__ import annotations

from geocomp.core.geodesy.cartesian import (
    DEFAULT_ELLIPSOID,
    cartesian_to_geodetic,
    cartesian_to_geodetic_quantities,
    geodetic_to_cartesian,
    geodetic_to_cartesian_jacobian,
    geodetic_to_cartesian_quantities,
)
from geocomp.core.geodesy.ellipsoid import ELLIPSOIDS, Ellipsoid, ellipsoid_by_name
from geocomp.core.geodesy.projection import (
    ProjectionParameters,
    inverse_transverse_mercator,
    point_scale_factor,
    transverse_mercator,
    utm_parameters,
    utm_zone,
)

__all__ = [
    "DEFAULT_ELLIPSOID",
    "ELLIPSOIDS",
    "Ellipsoid",
    "ProjectionParameters",
    "cartesian_to_geodetic",
    "cartesian_to_geodetic_quantities",
    "ellipsoid_by_name",
    "geodetic_to_cartesian",
    "geodetic_to_cartesian_jacobian",
    "geodetic_to_cartesian_quantities",
    "inverse_transverse_mercator",
    "point_scale_factor",
    "transverse_mercator",
    "utm_parameters",
    "utm_zone",
]
