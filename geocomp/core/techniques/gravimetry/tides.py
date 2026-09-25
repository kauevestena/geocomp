# SPDX-License-Identifier: GPL-2.0-or-later
"""The solid-Earth tide on a gravimeter reading (FR-701).

``specs/12-module-gravimetry.md`` section 4.2.

The Sun and the Moon pull on the gravimeter's proof mass and on the Earth
beneath it by different amounts, and the difference reaches a few hundred
microgal and changes by tens of microgal an hour. A relative survey measures
differences of a few hundred microgal between stations visited an hour apart,
so the tide is never negligible and never constant: it is removed from every
reading, at the instant the reading was taken.

**The model is Longman (1959)**, the closed-form expression that relative
gravimeters' own firmware uses -- the Scintrex CG-5 among them, which is how
this implementation is checked (below). It is a truncated lunar and solar
theory in closed form: no catalogue of tidal waves, no data file, nothing to
download, which matters in a plugin that must work offline. Its price is
accuracy, and that price is measured rather than asserted:

* Against the **CG-5's own firmware**, over 2,096 readings of a real survey
  whose file records the correction the instrument applied, this
  implementation agrees to 0.60 microgal rms and 1.51 microgal at worst, where
  the instrument prints to 1 microgal. That is the check that the formula is
  transcribed correctly.
* Against **ETERNA** with the Hartmann-Wenzel (1995) catalogue -- the reference
  implementation of the field, through pygtide -- the rigid-Earth tides agree
  to 0.76 to 1.21 microgal rms and 2.0 to 4.2 microgal at worst, at three
  latitudes and two epochs, slightly worse in 2026 than in 2013 because
  Longman's mean elements are polynomials in time from 1899. That is the
  formula's own accuracy, and it is what :data:`MODEL_UNCERTAINTY` is derived
  from.

``tests/data/rd07`` carries the ETERNA series and ``specs/22`` section 5 the
CG-5 comparison; ``tests/test_gravimetry_tides.py`` fails if either stops
holding.

**Two things this model does not do, stated so a user does not assume them.**
It applies one gravimetric factor, :data:`DEFAULT_AMPLIFICATION`, to every
frequency, where a real elastic Earth has slightly different factors for the
diurnal, semidiurnal and long-period tides; that is a further approximation the
figure above does not include. And it removes the *whole* tide, the permanent
part included, so the values it produces are in the **tide-free** system; an
absolute value published in the zero-tide system, which IAG Resolution 16
(1983) recommends, differs from a tide-free one by a latitude-dependent few
microgal. GeoComp records the system rather than converting silently.

**Ocean loading is not modelled.** It needs per-station loading coefficients
from a service this project cannot reach and so cannot test against; it is
deferred, and recorded as deferred in ``specs/ROADMAP.md``, rather than written
and left unverified.

Reference: I. M. Longman, *Formulas for computing the tidal accelerations due
to the moon and the sun*, Journal of Geophysical Research 64(12), 2351-2355,
1959.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime
from enum import Enum

from geocomp.core.errors import ValidationError
from geocomp.core.uncertainty import Quantity, Strategy
from geocomp.core.units import Unit

__all__ = [
    "DEFAULT_AMPLIFICATION",
    "MODEL_UNCERTAINTY",
    "TIDE_SYSTEM",
    "TideModel",
    "tidal_correction",
]


class TideModel(Enum):
    """Which tidal model computed a correction, recorded with the result."""

    #: Longman (1959): closed form, offline, a few microgal.
    LONGMAN_1959 = "longman_1959"


#: The gravimetric factor: how much an elastic Earth amplifies the tide a rigid
#: one would show a gravimeter. Longman suggested about 1.2; 1.16 is the modern
#: value, and it is the one the CG-5 firmware applies -- the comparison in
#: ``specs/22`` section 5 matches the firmware at 1.16 to 0.04 microgal in the
#: mean, and misses it by 1 microgal in the mean and 7 at worst at 1.20.
DEFAULT_AMPLIFICATION = 1.16

#: The standard uncertainty of a Longman correction, m/s^2. **Derived, not
#: chosen**: it is the worst rms disagreement between Longman's rigid-Earth tide
#: and ETERNA's Hartmann-Wenzel one over the series in ``tests/data/rd07``,
#: multiplied by :data:`DEFAULT_AMPLIFICATION` and rounded up to 0.1 microgal.
#: ``tests/test_gravimetry_tides.py`` recomputes it from that series and fails
#: if the two part.
MODEL_UNCERTAINTY = 1.5e-8

#: The permanent-tide convention of a Longman-corrected value.
TIDE_SYSTEM = "tide-free"

# -- Longman's constants, in SI -------------------------------------------

_ARCSEC = math.pi / (180.0 * 3600.0)
_DEGREE = math.pi / 180.0
_REVOLUTION = 2.0 * math.pi

#: Newton's constant as Longman used it, 6.670e-8 cgs.
_G = 6.670e-11
_MOON_MASS = 7.3537e22
_SUN_MASS = 1.993e30
#: Eccentricity of the Moon's orbit, and the ratio of the Sun's mean motion to
#: the Moon's.
_E = 0.054899720
_M = 0.074804
#: Mean Earth-Moon and Earth-Sun distances, and Longman's equatorial radius.
_C_MOON = 3.84402e8
_C_SUN = 1.495e11
_A_EARTH = 6.378270e6
#: Inclination of the Moon's orbit to the ecliptic, and of the equator to the
#: ecliptic.
_I_MOON = (5.0 + 8.0 / 60.0 + 43.3546 / 3600.0) * _DEGREE
_OBLIQUITY = (23.0 + 27.0 / 60.0 + 8.26 / 3600.0) * _DEGREE
#: Longman's time origin: Greenwich mean noon, 31 December 1899.
_EPOCH = datetime(1899, 12, 31, 12, 0, 0, tzinfo=UTC)
_SECONDS_PER_CENTURY = 36525.0 * 86400.0


def _dms(degrees: float, minutes: float, seconds: float) -> float:
    return (degrees * 3600.0 + minutes * 60.0 + seconds) * _ARCSEC


def tidal_correction(
    instant: datetime,
    latitude: float,
    longitude: float,
    height: float,
    *,
    amplification: float = DEFAULT_AMPLIFICATION,
    model_uncertainty: float = MODEL_UNCERTAINTY,
) -> Quantity:
    """The correction to *add* to a reading to remove the solid-Earth tide.

    Positive when the tide is lifting the proof mass -- the Moon or the Sun
    overhead -- because the gravimeter then reads low. That is the sign of
    Longman's vertical tidal acceleration and of the correction a CG-5 records.

    Args:
        instant: When the reading was taken. Timezone-aware; a naive one is
            refused, because the tide changes by up to a microgal a minute and
            a timezone guessed wrong by an hour is tens of microgal.
        latitude: Radians, north positive.
        longitude: Radians, **east** positive. Longman measured longitude
            westward; the conversion is made here, once.
        height: Metres above the ellipsoid. A few tens of metres change the
            result by parts per million, so an orthometric height serves.
        amplification: The gravimetric factor. See :data:`DEFAULT_AMPLIFICATION`.
        model_uncertainty: Standard uncertainty of the model, m/s^2.

    Returns:
        The correction in m/s^2, labelled approximate: its uncertainty is the
        model's nominal figure, not one propagated from the inputs, whose own
        uncertainties -- a position known to a kilometre, a clock to a second --
        are orders of magnitude smaller in their effect.
    """
    if instant.tzinfo is None:
        raise ValidationError(
            "tide_instant_naive",
            received=instant.isoformat(),
            expected="a timezone-aware instant; the tide depends on the time to the minute",
        )
    if not -math.pi / 2 <= latitude <= math.pi / 2:
        raise ValidationError(
            "tide_latitude_out_of_range",
            received=latitude,
            expected="a latitude in radians, between -pi/2 and pi/2",
        )
    if amplification <= 0.0:
        raise ValidationError(
            "tide_amplification_invalid",
            received=amplification,
            expected="a positive gravimetric factor, typically 1.16",
        )
    moon, sun = _longman(instant.astimezone(UTC), latitude, longitude, height)
    return Quantity.approximate(
        amplification * (moon + sun),
        model_uncertainty,
        Unit.ACCELERATION,
        Strategy.NOMINAL_PRECISION,
    )


def _longman(instant: datetime, latitude: float, longitude: float, height: float) -> tuple[float, float]:
    """Longman's lunar and solar vertical tidal accelerations, rigid Earth, m/s^2.

    Symbols follow Longman's paper. The time argument is in Julian centuries
    from his epoch; he used ephemeris time and UT is used here, which moves the
    Moon by under a minute of arc and the result by a few hundredths of a
    microgal.
    """
    centuries = (instant - _EPOCH).total_seconds() / _SECONDS_PER_CENTURY
    hours = instant.hour + instant.minute / 60.0 + (instant.second + instant.microsecond * 1e-6) / 3600.0

    # Mean elements: the Moon's mean longitude s, its perigee p, the Sun's mean
    # longitude h, the Moon's ascending node, and the solar perigee p1, all from
    # the vernal equinox.
    s = (
        _dms(270, 26, 11.72)
        + (1336 * _REVOLUTION + 1108406.05 * _ARCSEC) * centuries
        + 7.128 * _ARCSEC * centuries**2
        + 0.0072 * _ARCSEC * centuries**3
    )
    p = (
        _dms(334, 19, 46.42)
        + (11 * _REVOLUTION + 392522.51 * _ARCSEC) * centuries
        - 37.15 * _ARCSEC * centuries**2
        - 0.036 * _ARCSEC * centuries**3
    )
    h = _dms(279, 41, 48.05) + 129602768.11 * _ARCSEC * centuries + 1.080 * _ARCSEC * centuries**2
    node = (
        _dms(259, 10, 57.12)
        - (5 * _REVOLUTION + 482912.63 * _ARCSEC) * centuries
        + 7.58 * _ARCSEC * centuries**2
        + 0.008 * _ARCSEC * centuries**3
    )
    p1 = (
        _dms(281, 13, 15.0)
        + 6189.03 * _ARCSEC * centuries
        + 1.63 * _ARCSEC * centuries**2
        + 0.012 * _ARCSEC * centuries**3
    )
    e1 = 0.01675104 - 0.00004180 * centuries - 0.000000126 * centuries**2

    # The Moon's orbit against the equator: its inclination I, the
    # longitude nu of its intersection A with the equator, and alpha, the arc
    # from A to the orbit's ascending node on the ecliptic.
    cos_inclination = math.cos(_I_MOON) * math.cos(_OBLIQUITY) - math.sin(_I_MOON) * math.sin(
        _OBLIQUITY
    ) * math.cos(node)
    inclination = math.acos(cos_inclination)
    nu = math.asin(math.sin(_I_MOON) * math.sin(node) / math.sin(inclination))
    alpha = math.atan2(
        math.sin(_OBLIQUITY) * math.sin(node) / math.sin(inclination),
        math.cos(node) * math.cos(nu) + math.sin(node) * math.sin(nu) * math.cos(_OBLIQUITY),
    )
    xi = node - alpha
    sigma = s - xi

    # The Moon's true longitude in its orbit, from A: the equation of
    # the centre, evection and variation, to Longman's order.
    true_longitude = (
        sigma
        + 2.0 * _E * math.sin(s - p)
        + 1.25 * _E**2 * math.sin(2.0 * (s - p))
        + 3.75 * _M * _E * math.sin(s - 2.0 * h + p)
        + 11.0 / 8.0 * _M**2 * math.sin(2.0 * (s - h))
    )

    # Hour angle of the mean Sun at the station, and the right ascensions of the
    # meridian from A and from the equinox. East longitude adds.
    t = 15.0 * _DEGREE * (hours - 12.0) + longitude
    chi = t + h - nu
    chi1 = t + h
    solar_longitude = h + 2.0 * e1 * math.sin(h - p1)

    # Zenith distances of the Moon and the Sun.
    sin_lat, cos_lat = math.sin(latitude), math.cos(latitude)
    cos_theta = sin_lat * math.sin(inclination) * math.sin(true_longitude) + cos_lat * (
        math.cos(inclination / 2.0) ** 2 * math.cos(true_longitude - chi)
        + math.sin(inclination / 2.0) ** 2 * math.cos(true_longitude + chi)
    )
    cos_phi = sin_lat * math.sin(_OBLIQUITY) * math.sin(solar_longitude) + cos_lat * (
        math.cos(_OBLIQUITY / 2.0) ** 2 * math.cos(solar_longitude - chi1)
        + math.sin(_OBLIQUITY / 2.0) ** 2 * math.cos(solar_longitude + chi1)
    )

    # Distance of the station from the Earth's centre, and the
    # reciprocal distances of the Moon and the Sun.
    geocentric = math.sqrt(1.0 / (1.0 + 0.006738 * sin_lat**2))
    r = geocentric * _A_EARTH + height
    a_moon = 1.0 / (_C_MOON * (1.0 - _E**2))
    a_sun = 1.0 / (_C_SUN * (1.0 - e1**2))
    inverse_moon = (
        1.0 / _C_MOON
        + a_moon * _E * math.cos(s - p)
        + a_moon * _E**2 * math.cos(2.0 * (s - p))
        + 15.0 / 8.0 * a_moon * _M * _E * math.cos(s - 2.0 * h + p)
        + a_moon * _M**2 * math.cos(2.0 * (s - h))
    )
    inverse_sun = 1.0 / _C_SUN + a_sun * e1 * math.cos(h - p1)

    # The accelerations themselves: the Moon to its second-order
    # parallax term, the Sun to its first.
    moon = _G * _MOON_MASS * (
        r * inverse_moon**3 * (3.0 * cos_theta**2 - 1.0)
        + 1.5 * r**2 * inverse_moon**4 * (5.0 * cos_theta**3 - 3.0 * cos_theta)
    )
    sun = _G * _SUN_MASS * r * inverse_sun**3 * (3.0 * cos_phi**2 - 1.0)
    return moon, sun
