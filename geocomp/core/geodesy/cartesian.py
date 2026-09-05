# SPDX-License-Identifier: GPL-2.0-or-later
"""Geodetic (phi, lambda, h) to geocentric cartesian (X, Y, Z), and back.

``specs/07-engine-dynadjust.md`` section 4.4. This is the conversion the DynAdjust
adapter refuses for want of: a projected easting is not a geocentric X, and a
station written as though it were sits 845 km above the Earth. Both directions
carry a Jacobian, because a coordinate that arrives with a covariance and leaves
without one has lost the thing GeoComp exists to keep (FR-201, FR-205).

**No datum shift happens here.** These are two ways of writing the *same* point
on the *same* ellipsoid, exact in both directions. Moving between frames --
SIRGAS2000 to ITRF, or across epochs -- is a different operation with its own
uncertainty, and ``specs/14-multi-epoch-monitoring.md`` section 3 assigns it to
the QGIS/PROJ infrastructure. Confusing the two is how a 1-metre datum shift gets
applied twice, or not at all.
"""

from __future__ import annotations

import math

import numpy as np

from geocomp.core.errors import ComputationError
from geocomp.core.geodesy.ellipsoid import ELLIPSOIDS, Ellipsoid
from geocomp.core.uncertainty import Covariance, Quantity
from geocomp.core.units import Unit

__all__ = [
    "cartesian_to_geodetic",
    "cartesian_to_geodetic_quantities",
    "geodetic_to_cartesian",
    "geodetic_to_cartesian_jacobian",
    "geodetic_to_cartesian_quantities",
]

#: Newton refinement stops here. Bowring's starting value is already good to
#: about 0.1 mm for terrestrial heights, so this is reached in one or two steps;
#: the loop exists so the answer does not depend on how good the guess was.
_LATITUDE_TOLERANCE = 1e-14
_MAX_ITERATIONS = 10

#: Above this geodetic latitude, ``h = p / cos(phi) - N`` is computed from a
#: cosine near zero and loses precision. The polar branch uses the Z equation
#: instead. 89.5 degrees, where the two branches agree to well below a micrometre.
_POLAR_LATITUDE = math.radians(89.5)


def geodetic_to_cartesian(
    latitude: float, longitude: float, height: float, ellipsoid: Ellipsoid
) -> tuple[float, float, float]:
    """Geodetic to geocentric cartesian. Closed form, exact.

    Args:
        latitude: Geodetic latitude, radians.
        longitude: Geodetic longitude, radians, east positive.
        height: Height above the **ellipsoid**, metres. An orthometric height
            passed here is wrong by the geoid undulation -- tens of metres in
            Brazil -- so the caller applies the geoid model first (FR-804).
    """
    e2 = ellipsoid.eccentricity_squared
    n = ellipsoid.prime_vertical_radius(latitude)
    cos_lat, sin_lat = math.cos(latitude), math.sin(latitude)

    return (
        (n + height) * cos_lat * math.cos(longitude),
        (n + height) * cos_lat * math.sin(longitude),
        (n * (1.0 - e2) + height) * sin_lat,
    )


def geodetic_to_cartesian_jacobian(
    latitude: float, longitude: float, height: float, ellipsoid: Ellipsoid
) -> np.ndarray:
    """d(X, Y, Z) / d(latitude, longitude, height), for covariance propagation.

    The two curvature radii appear here for a reason worth stating: differentiating
    ``(N + h) cos(phi)`` with respect to latitude gives ``-(M + h) sin(phi)``, not
    ``-(N + h) sin(phi)``, because *N* itself depends on latitude. Using *N* in
    both places is a plausible-looking error of about 0.3 percent in the
    propagated latitude variance at mid-latitudes.
    """
    m = ellipsoid.meridian_radius(latitude)
    n = ellipsoid.prime_vertical_radius(latitude)
    cos_lat, sin_lat = math.cos(latitude), math.sin(latitude)
    cos_lon, sin_lon = math.cos(longitude), math.sin(longitude)

    return np.array(
        [
            [-(m + height) * sin_lat * cos_lon, -(n + height) * cos_lat * sin_lon,
             cos_lat * cos_lon],
            [-(m + height) * sin_lat * sin_lon, (n + height) * cos_lat * cos_lon,
             cos_lat * sin_lon],
            [(m + height) * cos_lat, 0.0, sin_lat],
        ]
    )


def cartesian_to_geodetic(
    x: float, y: float, z: float, ellipsoid: Ellipsoid
) -> tuple[float, float, float]:
    """Geocentric cartesian to geodetic. Bowring's start, refined to convergence.

    Bowring's 1976 approximation is good to about 0.1 mm for heights within a few
    kilometres of the ellipsoid, which is enough for a coordinate and not enough
    for a *round trip* to be exact -- and a round trip that loses 0.1 mm is a
    round trip that cannot be used to check anything else. The Newton step
    removes it, in one or two iterations, and makes the identity exact to
    floating point.

    Returns:
        ``(latitude, longitude, height)`` in radians and metres.
    """
    a = ellipsoid.semi_major_axis
    b = ellipsoid.semi_minor_axis
    e2 = ellipsoid.eccentricity_squared

    p = math.hypot(x, y)
    longitude = math.atan2(y, x)

    if p < 1e-9:
        # On the polar axis: longitude is undefined and any value is as correct
        # as another, so it is 0 by convention rather than by accident.
        sign = 1.0 if z >= 0.0 else -1.0
        return sign * math.pi / 2.0, 0.0, abs(z) - b

    # Bowring's parametric latitude, then his closed-form geodetic latitude.
    theta = math.atan2(z * a, p * b)
    latitude = math.atan2(
        z + ellipsoid.second_eccentricity_squared * b * math.sin(theta) ** 3,
        p - e2 * a * math.cos(theta) ** 3,
    )

    for _ in range(_MAX_ITERATIONS):
        sin_lat = math.sin(latitude)
        n = a / math.sqrt(1.0 - e2 * sin_lat * sin_lat)
        height = _height(p, z, latitude, n, e2)
        # tan(phi) = z / (p (1 - e^2 N/(N+h))) -- the exact relation, solved for
        # phi by fixed-point iteration on the bracketed factor.
        factor = 1.0 - e2 * n / (n + height)
        if factor <= 0.0:  # pragma: no cover - only below the ellipsoid's centre
            raise ComputationError(
                "cartesian_to_geodetic_degenerate",
                received=[x, y, z],
                expected="a point outside the ellipsoid's focal region",
            )
        updated = math.atan2(z, p * factor)
        converged = abs(updated - latitude) < _LATITUDE_TOLERANCE
        latitude = updated
        if converged:
            break

    sin_lat = math.sin(latitude)
    n = a / math.sqrt(1.0 - e2 * sin_lat * sin_lat)
    return latitude, longitude, _height(p, z, latitude, n, e2)


def _height(p: float, z: float, latitude: float, n: float, e2: float) -> float:
    """Ellipsoidal height, by whichever of the two equations is conditioned.

    ``h = p / cos(phi) - N`` divides by a cosine that vanishes at the pole;
    ``h = z / sin(phi) - N(1 - e^2)`` divides by a sine that vanishes at the
    equator. Each is exact where the other is not, so the branch is on latitude
    rather than on a tolerance.
    """
    if abs(latitude) < _POLAR_LATITUDE:
        return p / math.cos(latitude) - n
    return z / math.sin(latitude) - n * (1.0 - e2)


# -- the same two conversions, carrying uncertainty ------------------------


def geodetic_to_cartesian_quantities(
    latitude: Quantity, longitude: Quantity, height: Quantity, ellipsoid: Ellipsoid
) -> tuple[Quantity, Quantity, Quantity]:
    """Convert, propagating the full covariance (FR-201)."""
    _require_angle(latitude, "latitude")
    _require_angle(longitude, "longitude")
    _require_length(height, "height")

    values = geodetic_to_cartesian(latitude.value, longitude.value, height.value, ellipsoid)
    jacobian = geodetic_to_cartesian_jacobian(
        latitude.value, longitude.value, height.value, ellipsoid
    )
    inputs = Covariance.from_quantities(
        {
            "latitude": latitude.detached(),
            "longitude": longitude.detached(),
            "height": height.detached(),
        }
    )
    propagated = inputs.transform(jacobian, ["x", "y", "z"], [Unit.METRE] * 3)
    return tuple(
        Quantity(
            value=value,
            variance=propagated.matrix[index, index],
            unit=Unit.METRE,
            mode=propagated.mode,
            strategies=propagated.strategies,
        )
        for index, value in enumerate(values)
    )


def cartesian_to_geodetic_quantities(
    x: Quantity, y: Quantity, z: Quantity, ellipsoid: Ellipsoid
) -> tuple[Quantity, Quantity, Quantity]:
    """Convert, propagating the full covariance (FR-201).

    The Jacobian is the **inverse of the forward one**, evaluated at the answer.
    That is exact by the inverse function theorem, and it is deliberately not a
    second hand-derived formula: two derivations of the same matrix are two
    chances to get a sign wrong, and the second one has no independent check.
    """
    for name, quantity in (("x", x), ("y", y), ("z", z)):
        _require_length(quantity, name)

    latitude, longitude, height = cartesian_to_geodetic(x.value, y.value, z.value, ellipsoid)
    forward = geodetic_to_cartesian_jacobian(latitude, longitude, height, ellipsoid)
    jacobian = np.linalg.inv(forward)

    inputs = Covariance.from_quantities(
        {"x": x.detached(), "y": y.detached(), "z": z.detached()}
    )
    propagated = inputs.transform(
        jacobian,
        ["latitude", "longitude", "height"],
        [Unit.RADIAN, Unit.RADIAN, Unit.METRE],
    )
    return tuple(
        Quantity(
            value=value,
            variance=propagated.matrix[index, index],
            unit=unit,
            mode=propagated.mode,
            strategies=propagated.strategies,
        )
        for index, (value, unit) in enumerate(
            zip((latitude, longitude, height), (Unit.RADIAN, Unit.RADIAN, Unit.METRE),
                strict=True)
        )
    )


def _require_angle(quantity: Quantity, name: str) -> None:
    if quantity.unit is not Unit.RADIAN:
        raise ComputationError(
            "geodetic_angle_wrong_unit",
            component=name,
            received=quantity.unit.name,
            expected="radians; degrees and gon convert through core.units first",
        )


def _require_length(quantity: Quantity, name: str) -> None:
    if quantity.unit is not Unit.METRE:
        raise ComputationError(
            "geodetic_length_wrong_unit",
            component=name,
            received=quantity.unit.name,
            expected="metres",
        )


#: Convenience for the common case, so a caller that has only a frame name does
#: not have to reach into the registry.
DEFAULT_ELLIPSOID = ELLIPSOIDS["GRS80"]
