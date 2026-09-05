# SPDX-License-Identifier: GPL-2.0-or-later
"""The normal orthometric correction (FR-504).

``specs/10-module-levelling.md`` section 5: *orthometric corrections (the
non-parallelism of level surfaces) are applied for precise levelling over
significant height ranges, as an option with its magnitude reported so the user
can see when it matters*.

**What the correction is for.** A levelled height difference is the sum of many
short vertical intervals measured between level surfaces, and level surfaces are
not parallel: gravity increases toward the poles, so they converge. The
consequence is that a levelled height difference is **path-dependent** -- level
from A to B along the coast and inland and the two runs disagree, by a real
amount that is not error. The orthometric correction removes that dependence and
turns levelled differences into differences of orthometric height.

**What is implemented here, and what is not.** This is the *normal* orthometric
correction: it uses the normal gravity field of the reference ellipsoid, so it
needs only latitude and height. The **rigorous** orthometric correction needs
observed gravity along the line::

    OC = sum_i (g_i - gamma_0) / gamma_0 * dn_i
         + (g_A - gamma_0) / gamma_0 * H_A
         - (g_B - gamma_0) / gamma_0 * H_B

and GeoComp has no gravity observations until phase P8. It is not approximated
here with an assumed gravity field pretending to be a measured one; the function
that needs P8's data arrives in P8, and this one says which it is in every
result it returns.

**The derivation**, since the formula is short enough to show rather than cite.
Normal gravity on the ellipsoid, to first order::

    gamma(phi) = gamma_e * (1 + beta * sin^2(phi))

The correction is the integral of ``(gamma - gamma_0) / gamma_0`` along the
path, plus the end terms. Over a section short enough that the height is nearly
constant at *H_m*, the surviving term is the latitude derivative::

    d/dphi [ beta * sin^2(phi) ] = beta * sin(2 phi)

so::

    OC = -beta * sin(2 * phi_m) * H_m * (phi_B - phi_A)

with the latitudes in radians. Negative going poleward in **either**
hemisphere -- ``sin(2 phi)`` and ``d phi`` change sign together across the
equator -- because level surfaces converge that way, so a given levelled
difference corresponds to a smaller orthometric one.

**Magnitude, so a reader can judge when to bother.** At mean latitude 30
degrees, mean height 1000 m, over one degree of latitude, the correction is
81 mm. At 100 m of height it is 8 mm, and over one minute of latitude at that
height, 0.12 mm. It matters for precise levelling that climbs, over long
north-south lines. It is negligible for a construction site, and GeoComp says
so rather than leaving the user to work it out.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from geocomp.core.errors import ValidationError
from geocomp.core.findings import Finding, Severity
from geocomp.core.uncertainty import Quantity, Strategy
from geocomp.core.units import Unit

__all__ = [
    "GRAVITY_FLATTENING",
    "OrthometricCorrection",
    "normal_orthometric_correction",
]

#: The gravity flattening *beta* of the Somigliana normal gravity formula,
#: ``gamma = gamma_e (1 + beta sin^2 phi)``, for GRS80 and WGS84 alike -- they
#: differ in it at the 1e-11 level, which is nine orders below anything this
#: correction is used for.
GRAVITY_FLATTENING = 0.0053024

#: Below this, the correction is smaller than the noise of any levelling it
#: could be applied to, and the result says so rather than reporting a number
#: whose only effect would be to make a report look thorough.
NEGLIGIBLE = 1.0e-4


@dataclass(frozen=True)
class OrthometricCorrection:
    """The correction for one section, with what it was computed from.

    Attributes:
        correction: To be **added** to the levelled height difference, metres.
        mean_latitude / mean_height: The values used, so a report can show why
            the correction is the size it is.
        is_negligible: Whether the correction is below the threshold at which it
            could matter to any levelling. Returned rather than left for the
            caller to compare, because the comparison is the whole judgement.
    """

    correction: Quantity
    mean_latitude: float
    mean_height: float
    latitude_difference: float
    is_negligible: bool
    findings: tuple[Finding, ...] = ()

    @property
    def millimetres(self) -> float:
        return self.correction.value * 1000.0


def normal_orthometric_correction(
    height_difference: Quantity,
    *,
    latitude_from: float,
    latitude_to: float,
    height_from: float,
    height_to: float,
    gravity_flattening: float = GRAVITY_FLATTENING,
) -> OrthometricCorrection:
    """The normal orthometric correction for one levelled section.

    Args:
        height_difference: The levelled difference, from the *from* station to
            the *to* station. Used for its uncertainty and its mode, not its
            value: the correction depends on the two heights and latitudes.
        latitude_from / latitude_to: Geodetic latitudes, **radians**.
        height_from / height_to: Approximate orthometric heights, metres. They
            need be no better than a few metres -- the correction depends on
            their mean linearly, and a 10 m error in a 1000 m height changes it
            by one per cent.
        gravity_flattening: *beta*. Exposed so a different reference field can
            be used, not because the default is in doubt.

    Returns:
        The correction to add, with an uncertainty. The uncertainty is
        deliberately crude and tagged
        :attr:`~geocomp.core.uncertainty.Strategy.DOMINANT_TERM`: the dominant
        error in a normal orthometric correction is not the arithmetic but the
        *normality assumption* -- that the real gravity field is the ellipsoid's
        -- and no propagation of the inputs can express that. Ten per cent of
        the correction is used as a stand-in, which is honest about being a
        stand-in and is what FR-203 exists to make visible.
    """
    if height_difference.unit is not Unit.METRE:
        raise ValidationError(
            "orthometric_correction_wrong_unit",
            received=height_difference.unit.name,
            expected=Unit.METRE.name,
        )
    for name, latitude in (("latitude_from", latitude_from), ("latitude_to", latitude_to)):
        if not -math.pi / 2.0 <= latitude <= math.pi / 2.0:
            raise ValidationError(
                "latitude_out_of_range",
                parameter=name,
                received=latitude,
                expected="a geodetic latitude in radians, between -pi/2 and pi/2",
            )

    mean_latitude = (latitude_from + latitude_to) / 2.0
    mean_height = (height_from + height_to) / 2.0
    latitude_difference = latitude_to - latitude_from

    value = (
        -gravity_flattening
        * math.sin(2.0 * mean_latitude)
        * mean_height
        * latitude_difference
    )
    negligible = abs(value) < NEGLIGIBLE

    correction = Quantity.approximate(
        value, abs(value) * 0.1, Unit.METRE, Strategy.DOMINANT_TERM
    )

    findings: list[Finding] = []
    if negligible:
        findings.append(
            Finding(
                code="orthometric_correction_negligible",
                severity=Severity.INFO,
                message=(
                    f"the normal orthometric correction for this section is "
                    f"{value * 1000.0:+.3f} mm, below the {NEGLIGIBLE * 1000.0:.1f} mm at "
                    "which it could matter to any levelling. Applying it changes nothing"
                ),
                value=abs(value),
                threshold=NEGLIGIBLE,
            )
        )
    else:
        findings.append(
            Finding(
                code="orthometric_correction_applied",
                severity=Severity.INFO,
                message=(
                    f"the normal orthometric correction for this section is "
                    f"{value * 1000.0:+.2f} mm, at mean latitude "
                    f"{math.degrees(mean_latitude):.4f} degrees and mean height "
                    f"{mean_height:.0f} m. This is the *normal* correction, from the "
                    "ellipsoid's gravity field; the rigorous one needs observed gravity "
                    "along the line and arrives with the gravimetry module"
                ),
                value=abs(value),
            )
        )

    return OrthometricCorrection(
        correction=correction,
        mean_latitude=mean_latitude,
        mean_height=mean_height,
        latitude_difference=latitude_difference,
        is_negligible=negligible,
        findings=tuple(findings),
    )
