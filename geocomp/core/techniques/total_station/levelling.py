# SPDX-License-Identifier: GPL-2.0-or-later
"""Trigonometric levelling, including leap-frog (FR-410).

``specs/09-module-total-station.md`` section 4.5.

Height differences from zenith angles and slope distances, with curvature and
refraction, instrument and target heights.

**Leap-frog changes the error model, not just the arithmetic.** The instrument
is set between two targets and observes both, and two things then cancel that do
not cancel in a radial sight:

* The **instrument height** cancels *exactly*. It appears with the same sign in
  both sights and disappears from the difference, so it never has to be
  measured -- which removes what is routinely the dominant error in a short
  trigonometric height.
* The **refraction** largely cancels, because the two sights pass through the
  same air at the same moment and therefore share the same coefficient *k*.

The second is the one that must be modelled rather than approximated. Treating
the two sights as independent would give each its own *k*, and the two
uncertainties would then add in quadrature instead of subtracting -- **the
result would be a standard deviation several times too large**, which is the
opposite of the usual failure and no less wrong. ``specs/09`` section 4.5 is
explicit that the correlation is what produces the cancellation and must be
modelled.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from geocomp.core.errors import ValidationError
from geocomp.core.findings import Finding, Severity
from geocomp.core.techniques.total_station.reductions import (
    DEFAULT_EARTH_RADIUS,
    DEFAULT_REFRACTION_COEFFICIENT,
)
from geocomp.core.uncertainty import Covariance, Quantity, Strategy
from geocomp.core.units import Unit

__all__ = ["LeapFrogResult", "Sight", "leapfrog_height_difference", "radial_height_difference"]


@dataclass(frozen=True)
class Sight:
    """One pointing from the instrument to a target on a station.

    Attributes:
        station: The station the target stands on.
        zenith: Zenith angle, radians.
        distance: Slope distance, metres.
        target_height: Height of the target above the station mark, metres.
    """

    station: str
    zenith: Quantity
    distance: Quantity
    target_height: Quantity

    def __post_init__(self) -> None:
        for name, quantity, unit in (
            ("zenith", self.zenith, Unit.RADIAN),
            ("distance", self.distance, Unit.METRE),
            ("target_height", self.target_height, Unit.METRE),
        ):
            if quantity.unit is not unit:
                raise ValidationError(
                    "sight_wrong_unit",
                    station=self.station,
                    parameter=name,
                    received=quantity.unit.name,
                    expected=unit.name,
                )

    @property
    def horizontal_distance(self) -> float:
        return self.distance.value * math.sin(self.zenith.value)


@dataclass(frozen=True)
class LeapFrogResult:
    """A height difference observed from a free station between the two points.

    Attributes:
        height_difference: From ``backward.station`` to ``forward.station``.
        sight_imbalance: Forward minus backward horizontal distance, metres.
            The number that decides how much refraction actually cancelled: the
            method's benefit is proportional to how equal the two sights are,
            and an imbalanced pair gets much less of it.
        refraction_cancellation: How much smaller the uncertainty is than the
            same pair would have with independent refraction, as a ratio. 1.0
            means nothing cancelled; 0.1 means the modelled correlation removed
            ninety per cent of the refraction contribution.
    """

    height_difference: Quantity
    sight_imbalance: float
    refraction_cancellation: float
    findings: tuple[Finding, ...] = ()


def radial_height_difference(
    sight: Sight,
    instrument_height: Quantity,
    *,
    refraction_coefficient: Quantity | None = None,
    earth_radius: float = DEFAULT_EARTH_RADIUS,
) -> Quantity:
    """Height difference from the instrument's station to a target's (FR-410).

        dH = d cos(z) + hi - hs + (1 - k) d_h^2 / (2 R)

    The ordinary radial case, where nothing cancels: the instrument height, the
    target height and the refraction all contribute in full.
    """
    k = _coefficient(refraction_coefficient)
    inputs = Covariance.from_quantities(
        {
            "distance": sight.distance.detached(),
            "zenith": sight.zenith.detached(),
            "instrument_height": instrument_height.detached(),
            "target_height": sight.target_height.detached(),
            "k": k.detached(),
        }
    )

    d, z = sight.distance.value, sight.zenith.value
    sin_z, cos_z = math.sin(z), math.cos(z)
    horizontal = d * sin_z
    correction = (1.0 - k.value) * horizontal**2 / (2.0 * earth_radius)

    # d(correction)/dd and /dz go through the horizontal distance.
    d_corr_dh = (1.0 - k.value) * horizontal / earth_radius
    jacobian = np.array(
        [
            [
                cos_z + d_corr_dh * sin_z,
                -d * sin_z + d_corr_dh * d * cos_z,
                1.0,
                -1.0,
                -(horizontal**2) / (2.0 * earth_radius),
            ]
        ]
    )
    propagated = inputs.transform(jacobian, ["height_difference"], [Unit.METRE])

    return Quantity(
        value=d * cos_z + instrument_height.value - sight.target_height.value + correction,
        variance=propagated.matrix[0, 0],
        unit=Unit.METRE,
        mode=propagated.mode,
        strategies=propagated.strategies,
    )


def leapfrog_height_difference(
    backward: Sight,
    forward: Sight,
    *,
    refraction_coefficient: Quantity | None = None,
    earth_radius: float = DEFAULT_EARTH_RADIUS,
    imbalance_tolerance: float = 0.05,
) -> LeapFrogResult:
    """Height difference between two stations from one instrument between them.

        dH = (d_f cos z_f - hs_f + c_f) - (d_b cos z_b - hs_b + c_b)

    The instrument height does not appear: it cancels exactly, which is the
    method's first benefit and why it need never be measured.

    The refraction corrections *c* share one coefficient *k*, and that shared
    dependence is carried through a single Jacobian rather than being applied to
    each sight separately -- which is what makes the cancellation appear in the
    uncertainty as well as in the value.

    Args:
        imbalance_tolerance: Relative difference between the two sight lengths
            beyond which the imbalance is reported. Refraction cancels in
            proportion to how equal the sights are; a badly imbalanced pair gets
            little of the method's benefit and the user should know.
    """
    k = _coefficient(refraction_coefficient)

    inputs = Covariance.from_quantities(
        {
            "backward_distance": backward.distance.detached(),
            "backward_zenith": backward.zenith.detached(),
            "backward_target": backward.target_height.detached(),
            "forward_distance": forward.distance.detached(),
            "forward_zenith": forward.zenith.detached(),
            "forward_target": forward.target_height.detached(),
            # One k for both sights. This single shared column is the whole
            # point: it is what makes the two refraction corrections subtract
            # rather than add in quadrature.
            "k": k.detached(),
        }
    )

    order = list(inputs.labels)
    jacobian = np.zeros((1, len(order)))

    def contribution(sight: Sight, sign: float, prefix: str) -> float:
        d, z = sight.distance.value, sight.zenith.value
        sin_z, cos_z = math.sin(z), math.cos(z)
        horizontal = d * sin_z
        correction = (1.0 - k.value) * horizontal**2 / (2.0 * earth_radius)
        d_corr_dh = (1.0 - k.value) * horizontal / earth_radius

        jacobian[0, order.index(f"{prefix}_distance")] = sign * (cos_z + d_corr_dh * sin_z)
        jacobian[0, order.index(f"{prefix}_zenith")] = sign * (
            -d * sin_z + d_corr_dh * d * cos_z
        )
        jacobian[0, order.index(f"{prefix}_target")] = -sign
        jacobian[0, order.index("k")] += sign * -(horizontal**2) / (2.0 * earth_radius)
        return sign * (d * cos_z - sight.target_height.value + correction)

    value = contribution(forward, 1.0, "forward") + contribution(backward, -1.0, "backward")
    propagated = inputs.transform(jacobian, ["height_difference"], [Unit.METRE])

    height_difference = Quantity(
        value=value,
        variance=propagated.matrix[0, 0],
        unit=Unit.METRE,
        mode=propagated.mode,
        strategies=propagated.strategies,
    )

    cancellation = _refraction_cancellation(
        backward.horizontal_distance, forward.horizontal_distance
    )

    findings: list[Finding] = []
    imbalance = forward.horizontal_distance - backward.horizontal_distance
    longer = max(forward.horizontal_distance, backward.horizontal_distance)
    if longer > 0.0 and abs(imbalance) / longer > imbalance_tolerance:
        findings.append(
            Finding(
                code="leapfrog_sights_imbalanced",
                severity=Severity.WARNING,
                message=(
                    f"the two sights differ by {imbalance:+.2f} m over {longer:.1f} m. "
                    "Leap-frog cancels refraction in proportion to how equal the sights "
                    "are, so an imbalanced pair gets much less of the method's benefit"
                ),
                stations=(backward.station, forward.station),
                value=abs(imbalance) / longer,
                threshold=imbalance_tolerance,
            )
        )

    return LeapFrogResult(
        height_difference=height_difference,
        sight_imbalance=imbalance,
        refraction_cancellation=cancellation,
        findings=tuple(findings),
    )


def _refraction_cancellation(backward: float, forward: float) -> float:
    """How much of the refraction uncertainty the shared *k* removes.

    The refraction correction is ``(1 - k) h^2 / 2R``, so its sensitivity to *k*
    is ``-h^2 / 2R``. With one shared coefficient the two sights' sensitivities
    **subtract**:

        shared      = ((h_f^2 - h_b^2) / 2R)^2 var(k)

    With independent coefficients they would add in quadrature:

        independent = ((h_f^2)^2 + (h_b^2)^2) / (2R)^2 var(k)

    The ratio of standard deviations is therefore

        |h_f^2 - h_b^2| / sqrt(h_f^4 + h_b^4)

    -- independent of *R* and of var(k), which is what makes it a property of
    the *geometry* the surveyor controls. Zero for equal sights, one when only
    one sight exists, so it reads as "the fraction of the refraction uncertainty
    that survived".
    """
    denominator = math.hypot(forward**2, backward**2)
    if denominator == 0.0:
        return 0.0
    return abs(forward**2 - backward**2) / denominator


def _coefficient(refraction_coefficient: Quantity | None) -> Quantity:
    """The refraction coefficient, defaulted and recorded when not supplied."""
    if refraction_coefficient is not None:
        return refraction_coefficient
    return Quantity.approximate(
        DEFAULT_REFRACTION_COEFFICIENT, 0.05, Unit.DIMENSIONLESS, Strategy.TYPE_DEFAULT
    )
