# SPDX-License-Identifier: GPL-2.0-or-later
"""Basic and geometric reductions (FR-404, FR-405).

``specs/09-module-total-station.md`` sections 2.5 and 2.6.

Two families:

* **Basic** -- from the corrected slope distance, zenith angle and the two
  heights, to a horizontal distance and a height difference. This is what the
  prototype notebook computes as ``DH``, ``DV`` and ``dH``; the difference here
  is that every one of them carries an uncertainty, and that the *d-z
  correlation from the common pointing is kept* rather than assumed away.
* **Geometric** -- curvature and refraction, reduction to the ellipsoid, and
  reduction to the projection plane. Each carries the uncertainty of the
  heights and coordinates it used (FR-205): a distance reduced to the ellipsoid
  is only as certain as the height it was reduced with.

``specs/05`` section 4.1 works the first of these through by hand as the
document's illustration of what rigorous propagation means, and

    sigma^2_dh = sin^2(z) sigma^2_d + d^2 cos^2(z) sigma^2_z
                 + 2 d sin(z) cos(z) sigma_dz

is implemented here with that third term present. Dropping it is the
``INDEPENDENCE_ASSUMED`` strategy and is recorded as such when the caller
supplies no correlation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from geocomp.core.errors import ValidationError
from geocomp.core.uncertainty import Covariance, Quantity, Strategy, UncertaintyMode
from geocomp.core.units import Unit

__all__ = [
    "DEFAULT_EARTH_RADIUS",
    "DEFAULT_REFRACTION_COEFFICIENT",
    "BasicReduction",
    "GeometricReduction",
    "curvature_and_refraction",
    "reduce_basic",
    "reduce_to_ellipsoid",
    "reduce_to_projection",
    "trigonometric_height",
]

#: Mean Earth radius, metres. The reduction is a second-order effect and the
#: difference between a mean radius and a properly computed radius of curvature
#: in the sight's azimuth is well below its own uncertainty.
DEFAULT_EARTH_RADIUS = 6_371_000.0

#: The conventional coefficient of refraction for daytime sights over land.
#: Poorly known and variable through the day, which is why its uncertainty is
#: an input rather than an assumption (``specs/09`` section 2.6).
DEFAULT_REFRACTION_COEFFICIENT = 0.13


@dataclass(frozen=True)
class BasicReduction:
    """A pointing reduced to a horizontal distance and a height difference.

    Attributes:
        horizontal_distance: ``d sin z``.
        vertical_component: ``d cos z``, before the heights are applied.
        height_difference: ``d cos z + hi - hs``.
        covariance: The joint covariance of the three, which is the part a
            scalar-by-scalar result would lose. The horizontal distance and the
            height difference are strongly correlated through the shared zenith
            angle, and a 3D adjustment that treats them as independent is
            wrong.
    """

    horizontal_distance: Quantity
    vertical_component: Quantity
    height_difference: Quantity
    covariance: Covariance


@dataclass(frozen=True)
class GeometricReduction:
    """A distance carried from the ground to a computation surface.

    Attributes:
        distance: The reduced distance.
        correction: What was applied, signed, so a user can see when it stops
            being negligible. ``specs/09`` requires this be reported rather
            than folded silently into the result.
    """

    distance: Quantity
    correction: Quantity


def reduce_basic(
    distance: Quantity,
    zenith: Quantity,
    instrument_height: Quantity,
    target_height: Quantity,
    *,
    correlation: float | None = None,
) -> BasicReduction:
    """Reduce a slope distance and zenith angle to the plane (FR-404).

    Args:
        correlation: The correlation coefficient between the distance and the
            zenith angle, which share a pointing. ``None`` means the caller has
            no correlation information, in which case zero is used **and
            recorded** as :attr:`Strategy.INDEPENDENCE_ASSUMED` -- the result is
            marked approximate rather than silently claiming rigour it does not
            have (``specs/05`` section 4.1).

    Returns:
        The three reduced quantities and their joint covariance.
    """
    for name, quantity, unit in (
        ("distance", distance, Unit.METRE),
        ("zenith", zenith, Unit.RADIAN),
        ("instrument_height", instrument_height, Unit.METRE),
        ("target_height", target_height, Unit.METRE),
    ):
        if quantity.unit is not unit:
            raise ValidationError(
                "reduction_wrong_unit",
                parameter=name,
                received=quantity.unit.name,
                expected=unit.name,
            )

    d, z = distance.value, zenith.value
    sin_z, cos_z = math.sin(z), math.cos(z)

    strategies = set(distance.strategies | zenith.strategies)
    strategies |= set(instrument_height.strategies | target_height.strategies)
    if correlation is None:
        rho = 0.0
        strategies.add(Strategy.INDEPENDENCE_ASSUMED)
    else:
        if not -1.0 <= correlation <= 1.0:
            raise ValidationError(
                "correlation_out_of_range",
                received=correlation,
                expected="a correlation coefficient between -1 and 1",
            )
        rho = correlation

    inputs = Covariance.from_quantities(
        {
            "distance": distance,
            "zenith": zenith,
            "instrument_height": instrument_height,
            "target_height": target_height,
        },
        correlations={("distance", "zenith"): rho} if rho else None,
    )

    # Rows: horizontal distance, vertical component, height difference.
    # Columns: d, z, hi, hs.
    jacobian = np.array(
        [
            [sin_z, d * cos_z, 0.0, 0.0],
            [cos_z, -d * sin_z, 0.0, 0.0],
            [cos_z, -d * sin_z, 1.0, -1.0],
        ]
    )
    covariance = inputs.transform(
        jacobian,
        ["horizontal_distance", "vertical_component", "height_difference"],
        [Unit.METRE, Unit.METRE, Unit.METRE],
        strategies=strategies,
    )

    mode = (
        UncertaintyMode.APPROXIMATE
        if strategies or covariance.mode is UncertaintyMode.APPROXIMATE
        else UncertaintyMode.RIGOROUS
    )
    values = {
        "horizontal_distance": d * sin_z,
        "vertical_component": d * cos_z,
        "height_difference": d * cos_z + instrument_height.value - target_height.value,
    }

    def carried(label: str) -> Quantity:
        return Quantity(
            value=values[label],
            variance=covariance.variance(label),
            unit=Unit.METRE,
            mode=mode,
            strategies=frozenset(strategies),
            covariance_ref=covariance.ref,
        )

    return BasicReduction(
        horizontal_distance=carried("horizontal_distance"),
        vertical_component=carried("vertical_component"),
        height_difference=carried("height_difference"),
        covariance=covariance,
    )


def curvature_and_refraction(
    horizontal_distance: Quantity,
    *,
    refraction_coefficient: Quantity | None = None,
    earth_radius: float = DEFAULT_EARTH_RADIUS,
) -> Quantity:
    """The combined curvature-and-refraction correction to a height difference.

        c = (1 - k) d^2 / (2 R)

    Earth curvature makes a level surface fall away from the line of sight;
    atmospheric refraction bends the sight back down, partly cancelling it. The
    net is positive: an uncorrected trigonometric height is too small.

    Args:
        refraction_coefficient: *k*, dimensionless. ``None`` uses
            :data:`DEFAULT_REFRACTION_COEFFICIENT` with a generous standard
            deviation and records :attr:`Strategy.TYPE_DEFAULT`, because a
            coefficient nobody measured is not known to the precision of one
            somebody did. *k* is the dominant error source on long sights, and
            this is where that shows up.
    """
    if refraction_coefficient is None:
        k = Quantity.approximate(
            DEFAULT_REFRACTION_COEFFICIENT, 0.05, Unit.DIMENSIONLESS, Strategy.TYPE_DEFAULT
        )
    else:
        k = refraction_coefficient

    d = horizontal_distance.value
    factor = d**2 / (2.0 * earth_radius)

    # d(c)/d(d) = (1 - k) d / R ; d(c)/d(k) = -d^2 / (2R).
    d_dd = (1.0 - k.value) * d / earth_radius
    d_dk = -factor

    inputs = Covariance.from_quantities(
        {"distance": horizontal_distance.detached(), "k": k.detached()}
    )
    propagated = inputs.transform(
        np.array([[d_dd, d_dk]]), ["correction"], [Unit.METRE]
    )

    return Quantity(
        value=(1.0 - k.value) * factor,
        variance=propagated.matrix[0, 0],
        unit=Unit.METRE,
        mode=propagated.mode,
        strategies=propagated.strategies,
    )


def trigonometric_height(
    reduction: BasicReduction,
    *,
    refraction_coefficient: Quantity | None = None,
    earth_radius: float = DEFAULT_EARTH_RADIUS,
) -> Quantity:
    """A height difference with curvature and refraction applied (FR-410).

    On a 100 m sight the correction is 0.7 mm; at 1 km it is 68 mm; at 5 km it
    is 1.7 m. Applying it is not optional at geodetic distances, and reporting
    its magnitude is what lets a user see where the threshold sits for their
    work.
    """
    correction = curvature_and_refraction(
        reduction.horizontal_distance.detached(),
        refraction_coefficient=refraction_coefficient,
        earth_radius=earth_radius,
    )
    return reduction.height_difference.detached() + correction


def reduce_to_ellipsoid(
    horizontal_distance: Quantity,
    mean_height: Quantity,
    *,
    earth_radius: float = DEFAULT_EARTH_RADIUS,
    geoid_undulation: Quantity | None = None,
) -> GeometricReduction:
    """Reduce a horizontal distance from the ground to the ellipsoid (FR-405).

        d_ellipsoid = d * R / (R + h)

    Args:
        mean_height: The mean height of the two ends above the reference
            surface. When it is an *orthometric* height, pass the geoid
            undulation as well so the ellipsoidal height is used -- reducing
            with the wrong height surface is a systematic scale error of about
            1.6 ppm per 10 m, which is exactly the size of the effect being
            corrected for.
        geoid_undulation: *N*, so that ``h = H + N``.

    The result carries the height's uncertainty (FR-205): a distance reduced to
    the ellipsoid is only as certain as the height it was reduced with.
    """
    height = mean_height if geoid_undulation is None else mean_height + geoid_undulation

    d = horizontal_distance.value
    h = height.value
    denominator = earth_radius + h
    if denominator <= 0.0:
        raise ValidationError(
            "height_below_earth_centre",
            received=h,
            expected="a height above the reference surface",
        )

    factor = earth_radius / denominator
    d_dd = factor
    d_dh = -d * earth_radius / denominator**2

    inputs = Covariance.from_quantities(
        {"distance": horizontal_distance.detached(), "height": height.detached()}
    )
    propagated = inputs.transform(np.array([[d_dd, d_dh]]), ["reduced"], [Unit.METRE])

    reduced = Quantity(
        value=d * factor,
        variance=propagated.matrix[0, 0],
        unit=Unit.METRE,
        mode=propagated.mode,
        strategies=propagated.strategies,
    )
    return GeometricReduction(
        distance=reduced,
        correction=Quantity(
            value=reduced.value - d,
            variance=reduced.variance,
            unit=Unit.METRE,
            mode=reduced.mode,
            strategies=reduced.strategies,
        ),
    )


def reduce_to_projection(
    ellipsoidal_distance: Quantity, point_scale_factor: Quantity
) -> GeometricReduction:
    """Reduce an ellipsoidal distance to the projection plane (FR-405).

        d_grid = d_ellipsoid * k

    Args:
        point_scale_factor: The scale factor of the project CRS at the line's
            midpoint. Supplied rather than computed here because it depends on
            the projection, which is QGIS's business and not the core's -- the
            caller obtains it from the CRS and passes it in.
    """
    if point_scale_factor.unit is not Unit.DIMENSIONLESS:
        raise ValidationError(
            "scale_factor_wrong_unit",
            received=point_scale_factor.unit.name,
            expected=Unit.DIMENSIONLESS.name,
        )
    reduced = ellipsoidal_distance * point_scale_factor
    return GeometricReduction(
        distance=reduced,
        correction=Quantity(
            value=reduced.value - ellipsoidal_distance.value,
            variance=reduced.variance,
            unit=Unit.METRE,
            mode=reduced.mode,
            strategies=reduced.strategies,
        ),
    )
