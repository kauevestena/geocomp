# SPDX-License-Identifier: GPL-2.0-or-later
"""Transverse Mercator, forward and inverse, and UTM as a case of it.

``specs/07-engine-dynadjust.md`` section 4.4: *"converting to geodetic or
geocentric needs an inverse projection it does not carry either"*. This is that
inverse projection. Without it a projected network cannot reach DynAdjust at
all, which is why P6's cross-validation has one network instead of three.

**Krüger's series, in the form EPSG Guidance Note 7-2 gives for method 9807.**
The alternative -- the older Redfearn series in powers of ``e^2`` -- is what many
textbooks print and is accurate to a few millimetres at the edge of a UTM zone.
Krüger's, in powers of the third flattening *n*, is sub-micrometre over the same
domain because *n* is 1/600 where ``e^2`` is 1/150. The check against DynAdjust
in ``tests/test_geodesy.py`` measures which one this is: it agrees to 0.03 mm,
and Redfearn would show tens of times that.

The series is truncated at ``n^4``. Its error grows with distance from the
central meridian and is negligible within a zone; :func:`transverse_mercator`
refuses a point far enough out for that to stop being true, rather than
returning a number whose error nobody can see.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from geocomp.core.errors import ComputationError, ValidationError
from geocomp.core.geodesy.ellipsoid import ELLIPSOIDS, Ellipsoid

__all__ = [
    "ProjectionParameters",
    "inverse_transverse_mercator",
    "point_scale_factor",
    "transverse_mercator",
    "utm_parameters",
    "utm_zone",
]

#: Beyond this from the central meridian the n^4 truncation stops being
#: negligible and the projection stops being useful anyway -- a UTM zone is 3
#: degrees wide either side, and even a Gauss-Kruger belt is 3. At 10 degrees the
#: series is still good to well under a millimetre; the refusal is here so that a
#: point on the far side of the world produces an error rather than a plausible
#: coordinate.
_MAX_LONGITUDE_FROM_CENTRAL_MERIDIAN = math.radians(10.0)

#: Newton on the isometric latitude converges quadratically from a start already
#: correct to a few parts in 1e10, so this is reached in two or three passes.
_ISOMETRIC_TOLERANCE = 1e-15
_MAX_ITERATIONS = 12


@dataclass(frozen=True)
class ProjectionParameters:
    """A Transverse Mercator projection, by its five defining parameters.

    Attributes:
        central_meridian: Radians.
        latitude_of_origin: Radians. Zero for UTM and for every Gauss-Kruger
            belt; it is here because Transverse Mercator in general allows it.
        scale_factor: *k0* at the central meridian. 0.9996 for UTM.
        false_easting: Metres.
        false_northing: Metres. 10 000 000 in the southern hemisphere for UTM,
            which is what keeps northings positive.
    """

    ellipsoid: Ellipsoid
    central_meridian: float
    latitude_of_origin: float = 0.0
    scale_factor: float = 1.0
    false_easting: float = 0.0
    false_northing: float = 0.0
    name: str = ""


def utm_zone(longitude: float) -> int:
    """The UTM zone containing a longitude in radians. 1 to 60.

    The Norway and Svalbard exceptions are **not** applied. They widen zones 31V
    and 32V and shift the boundaries in 31X-37X, and a network that straddles
    one of them needs a decision this function cannot make on its own; the zone
    is taken as given by the caller in that case.
    """
    degrees = math.degrees(longitude)
    # Wrap to [-180, 180) so that a longitude arriving as 190 or -190 does not
    # produce zone 62 or zone -1.
    degrees = (degrees + 180.0) % 360.0 - 180.0
    return int((degrees + 180.0) // 6.0) + 1


def utm_parameters(
    zone: int, *, southern_hemisphere: bool, ellipsoid: Ellipsoid | None = None
) -> ProjectionParameters:
    """Standard UTM: k0 = 0.9996, 6-degree zones, 500 km false easting."""
    if not 1 <= zone <= 60:
        raise ValidationError(
            "utm_zone_out_of_range", received=zone, expected="a zone from 1 to 60"
        )
    ellipsoid = ellipsoid or ELLIPSOIDS["GRS80"]
    return ProjectionParameters(
        ellipsoid=ellipsoid,
        central_meridian=math.radians((zone - 1) * 6 - 180 + 3),
        latitude_of_origin=0.0,
        scale_factor=0.9996,
        false_easting=500000.0,
        false_northing=10000000.0 if southern_hemisphere else 0.0,
        name=f"UTM zone {zone}{'S' if southern_hemisphere else 'N'} on {ellipsoid.name}",
    )


# -- the series coefficients ------------------------------------------------


def _rectifying_radius(ellipsoid: Ellipsoid) -> float:
    """*B*: the radius of the sphere of equal meridian arc length."""
    n = ellipsoid.third_flattening
    return (ellipsoid.semi_major_axis / (1.0 + n)) * (
        1.0 + n**2 / 4.0 + n**4 / 64.0
    )


def _forward_coefficients(n: float) -> tuple[float, float, float, float]:
    return (
        n / 2.0 - (2.0 / 3.0) * n**2 + (5.0 / 16.0) * n**3 + (41.0 / 180.0) * n**4,
        (13.0 / 48.0) * n**2 - (3.0 / 5.0) * n**3 + (557.0 / 1440.0) * n**4,
        (61.0 / 240.0) * n**3 - (103.0 / 140.0) * n**4,
        (49561.0 / 161280.0) * n**4,
    )


def _inverse_coefficients(n: float) -> tuple[float, float, float, float]:
    """**Not** the forward coefficients negated -- a separate series.

    They agree to first order in *n* and diverge after that: h2 is 13/48 n^2 and
    h2' is 1/48 n^2. Reusing one set for both directions is a round trip that
    closes to about 3 metres at the edge of a zone.
    """
    return (
        n / 2.0 - (2.0 / 3.0) * n**2 + (37.0 / 96.0) * n**3 - (1.0 / 360.0) * n**4,
        (1.0 / 48.0) * n**2 + (1.0 / 15.0) * n**3 - (437.0 / 1440.0) * n**4,
        (17.0 / 480.0) * n**3 - (37.0 / 840.0) * n**4,
        (4397.0 / 161280.0) * n**4,
    )


def _meridian_arc(latitude: float, parameters: ProjectionParameters) -> float:
    """``B * xi`` at the given latitude on the central meridian, for M0."""
    if latitude == 0.0:
        return 0.0
    easting, northing = _project(latitude, parameters.central_meridian, parameters)
    del easting
    return (northing - parameters.false_northing) / parameters.scale_factor


# -- the projection ---------------------------------------------------------


def _project(
    latitude: float, longitude: float, parameters: ProjectionParameters
) -> tuple[float, float]:
    """The series itself, without the origin shift, so M0 can reuse it."""
    ellipsoid = parameters.ellipsoid
    e = math.sqrt(ellipsoid.eccentricity_squared)
    n = ellipsoid.third_flattening
    b = _rectifying_radius(ellipsoid)
    h1, h2, h3, h4 = _forward_coefficients(n)

    # Conformal latitude, via the isometric latitude Q.
    q = math.asinh(math.tan(latitude)) - e * math.atanh(e * math.sin(latitude))
    beta = math.atan(math.sinh(q))

    delta_longitude = longitude - parameters.central_meridian
    eta0 = math.atanh(math.cos(beta) * math.sin(delta_longitude))
    xi0 = math.asin(math.sin(beta) * math.cosh(eta0))

    xi = xi0 + sum(
        coefficient * math.sin(2 * order * xi0) * math.cosh(2 * order * eta0)
        for order, coefficient in enumerate((h1, h2, h3, h4), start=1)
    )
    eta = eta0 + sum(
        coefficient * math.cos(2 * order * xi0) * math.sinh(2 * order * eta0)
        for order, coefficient in enumerate((h1, h2, h3, h4), start=1)
    )

    return (
        parameters.false_easting + parameters.scale_factor * b * eta,
        parameters.false_northing + parameters.scale_factor * b * xi,
    )


def transverse_mercator(
    latitude: float, longitude: float, parameters: ProjectionParameters
) -> tuple[float, float]:
    """Geodetic to grid. Returns ``(easting, northing)`` in metres.

    Args:
        latitude: Radians.
        longitude: Radians, east positive.
    """
    _check_domain(longitude, parameters)
    easting, northing = _project(latitude, longitude, parameters)
    return easting, northing - parameters.scale_factor * _origin_arc(parameters)


def inverse_transverse_mercator(
    easting: float, northing: float, parameters: ProjectionParameters
) -> tuple[float, float]:
    """Grid to geodetic. Returns ``(latitude, longitude)`` in radians."""
    ellipsoid = parameters.ellipsoid
    e = math.sqrt(ellipsoid.eccentricity_squared)
    n = ellipsoid.third_flattening
    b = _rectifying_radius(ellipsoid)
    h1, h2, h3, h4 = _inverse_coefficients(n)

    eta = (easting - parameters.false_easting) / (b * parameters.scale_factor)
    xi = (
        northing - parameters.false_northing + parameters.scale_factor * _origin_arc(parameters)
    ) / (b * parameters.scale_factor)

    xi0 = xi - sum(
        coefficient * math.sin(2 * order * xi) * math.cosh(2 * order * eta)
        for order, coefficient in enumerate((h1, h2, h3, h4), start=1)
    )
    eta0 = eta - sum(
        coefficient * math.cos(2 * order * xi) * math.sinh(2 * order * eta)
        for order, coefficient in enumerate((h1, h2, h3, h4), start=1)
    )

    beta = math.asin(math.sin(xi0) / math.cosh(eta0))
    # Invert the isometric latitude by Newton, from the conformal latitude.
    q = math.asinh(math.tan(beta))
    isometric = q
    for _ in range(_MAX_ITERATIONS):
        updated = q + e * math.atanh(e * math.tanh(isometric))
        if abs(updated - isometric) < _ISOMETRIC_TOLERANCE:
            isometric = updated
            break
        isometric = updated
    else:  # pragma: no cover - the iteration is quadratic and starts close
        raise ComputationError(
            "inverse_projection_did_not_converge",
            received=[easting, northing],
            expected="a grid coordinate within the projection's domain",
        )

    latitude = math.atan(math.sinh(isometric))
    longitude = parameters.central_meridian + math.asin(math.tanh(eta0) / math.cos(beta))
    return latitude, longitude


def _origin_arc(parameters: ProjectionParameters) -> float:
    """*M0*, the meridian arc from the equator to the latitude of origin.

    Zero for UTM and for every Gauss-Kruger belt, which is why it is computed
    lazily: the general case is rare and the common one costs nothing.
    """
    if parameters.latitude_of_origin == 0.0:
        return 0.0
    return _meridian_arc(parameters.latitude_of_origin, parameters)


def _check_domain(longitude: float, parameters: ProjectionParameters) -> None:
    delta = abs(longitude - parameters.central_meridian)
    delta = min(delta, abs(2 * math.pi - delta))
    if delta > _MAX_LONGITUDE_FROM_CENTRAL_MERIDIAN:
        raise ComputationError(
            "projection_outside_domain",
            received=math.degrees(delta),
            expected=(
                f"within {math.degrees(_MAX_LONGITUDE_FROM_CENTRAL_MERIDIAN):.0f} "
                "degrees of the central meridian; the series is truncated at n^4 "
                "and a point further out gets a plausible coordinate with an "
                "error nobody can see"
            ),
            projection=parameters.name or "transverse mercator",
        )


def point_scale_factor(
    latitude: float, longitude: float, parameters: ProjectionParameters
) -> float:
    """*k* at a point: how much the projection stretches a distance there.

    ``techniques/total_station/reductions.reduce_to_projection`` takes this as a
    parameter the caller has to know from somewhere. This is where it comes
    from.

    Computed from the projection's own derivatives rather than from a second
    series: *k* is the ratio of a differential distance on the grid to the
    corresponding one on the ellipsoid, and both are available here. That makes
    it exact for whatever the projection actually does, including its truncation
    -- a series for *k* derived separately would describe a slightly different
    projection from the one being used.
    """
    step = 1e-8  # radians; about 60 mm on the ground, well inside the linear region
    east_ahead, north_ahead = _project(latitude, longitude + step, parameters)
    east_behind, north_behind = _project(latitude, longitude - step, parameters)

    grid = math.hypot(east_ahead - east_behind, north_ahead - north_behind) / (2 * step)
    ellipsoidal = parameters.ellipsoid.prime_vertical_radius(latitude) * math.cos(latitude)
    if ellipsoidal == 0.0:  # pragma: no cover - only exactly at a pole
        raise ComputationError(
            "point_scale_factor_undefined_at_the_pole",
            received=math.degrees(latitude),
            expected="a latitude where a parallel has non-zero length",
        )
    return grid / ellipsoidal
