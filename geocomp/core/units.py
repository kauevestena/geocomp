# SPDX-License-Identifier: GPL-2.0-or-later
"""Units, angle handling, and conversion to and from display formats.

``specs/04-data-model.md`` section 6 fixes the internal representation: **SI
throughout, angles in radians**. Degrees-minutes-seconds, gon, mGal and feet are
*display and interchange* formats, converted at the boundary and never stored.

That rule is worth stating plainly because the alternative is the most common
source of silent error in survey software: a value whose unit depends on where
it came from. Here a :class:`~geocomp.core.uncertainty.Quantity` carries its unit
and arithmetic checks it, so a metre added to a radian raises instead of
producing a number.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from enum import Enum

__all__ = [
    "DMS",
    "GON_PER_RADIAN",
    "KELVIN_AT_ZERO_CELSIUS",
    "TWO_PI",
    "Unit",
    "angular_difference",
    "celsius_to_kelvin",
    "circular_mean",
    "convert",
    "dimension_of",
    "dms_to_radians",
    "format_dms",
    "kelvin_to_celsius",
    "parse_angle",
    "radians_to_dms",
    "wrap_to_2pi",
    "wrap_to_pi",
]


class Unit(Enum):
    """The physical dimension of a quantity.

    Deliberately coarse. GeoComp needs to prevent the mistakes that actually
    happen -- mixing an angle with a length, or a gravity value with a distance
    -- not to implement a full dimensional algebra. ``DIMENSIONLESS`` covers
    ratios, scale factors and the results of trigonometric functions.
    """

    METRE = "m"
    RADIAN = "rad"
    DIMENSIONLESS = ""
    #: Gravity and gravity differences. SI: metres per second squared.
    ACCELERATION = "m/s^2"
    SECOND = "s"
    #: Temperature. Stored in kelvin because that is the SI unit and because the
    #: Celsius scale is affine rather than multiplicative, which :func:`convert`
    #: deliberately does not model -- see :func:`celsius_to_kelvin`.
    KELVIN = "K"
    #: Pressure -- atmospheric and water-vapour partial pressure alike.
    PASCAL = "Pa"

    @property
    def symbol(self) -> str:
        return self.value


# -- constants -----------------------------------------------------------

TWO_PI = 2.0 * math.pi
GON_PER_RADIAN = 200.0 / math.pi
#: 1 mGal = 1e-5 m/s^2; 1 uGal = 1e-8 m/s^2.
METRES_PER_SECOND_SQUARED_PER_MGAL = 1e-5
METRES_PER_SECOND_SQUARED_PER_UGAL = 1e-8
METRES_PER_INTERNATIONAL_FOOT = 0.3048
#: The US survey foot is exactly 1200/3937 m. It differs from the international
#: foot by about 2 ppm -- 2 mm per kilometre, which matters in geodetic work.
METRES_PER_US_SURVEY_FOOT = 1200.0 / 3937.0


# -- degrees, minutes, seconds -------------------------------------------


@dataclass(frozen=True)
class DMS:
    """A sexagesimal angle, as read from a field book.

    The sign belongs to the angle as a whole, not to any one component: an angle
    of -0 deg 00' 30" has ``negative=True`` with all components positive. Storing
    a sign on ``degrees`` alone loses the sign of angles between -1 and 0
    degrees, which is a real and easily missed defect.
    """

    degrees: int
    minutes: int
    seconds: float
    negative: bool = False

    def __post_init__(self) -> None:
        if self.degrees < 0 or self.minutes < 0 or self.seconds < 0:
            raise ValueError(
                "DMS components must be non-negative; use negative=True for the sign"
            )
        if self.minutes >= 60:
            raise ValueError(f"minutes must be below 60, got {self.minutes}")
        if self.seconds >= 60:
            raise ValueError(f"seconds must be below 60, got {self.seconds}")

    @property
    def decimal_degrees(self) -> float:
        magnitude = self.degrees + self.minutes / 60.0 + self.seconds / 3600.0
        return -magnitude if self.negative else magnitude

    @property
    def radians(self) -> float:
        return math.radians(self.decimal_degrees)

    @classmethod
    def from_decimal_degrees(cls, value: float) -> DMS:
        negative = value < 0
        magnitude = abs(value)
        degrees = int(magnitude)
        minutes_full = (magnitude - degrees) * 60.0
        minutes = int(minutes_full)
        seconds = (minutes_full - minutes) * 60.0

        # Guard the rounding boundary: 59.9999994" must not serialise as 60".
        if seconds >= 60.0 - 5e-10:
            seconds = 0.0
            minutes += 1
        if minutes >= 60:
            minutes = 0
            degrees += 1
        return cls(degrees, minutes, seconds, negative)

    @classmethod
    def from_radians(cls, value: float) -> DMS:
        return cls.from_decimal_degrees(math.degrees(value))


def dms_to_radians(degrees: float, minutes: float = 0.0, seconds: float = 0.0) -> float:
    """Convert sexagesimal components to radians.

    Accepts the three-column layout used by field books and by reference dataset
    RD-01 (``HG``/``HM``/``HS``). A negative value in *any* component makes the
    whole angle negative, which is how such a file expresses a negative angle:
    only the leading non-zero component carries the sign.
    """
    negative = degrees < 0 or minutes < 0 or seconds < 0
    magnitude = abs(degrees) + abs(minutes) / 60.0 + abs(seconds) / 3600.0
    return math.radians(-magnitude if negative else magnitude)


def radians_to_dms(value: float) -> DMS:
    return DMS.from_radians(value)


def format_dms(value: float, decimals: int = 1, symbols: bool = True) -> str:
    """Format radians as a sexagesimal string for display.

    Args:
        value: Angle in radians.
        decimals: Decimal places on the seconds.
        symbols: Use the degree, minute and second marks; otherwise separate
            with spaces, which is what most engines expect in a text file.
    """
    dms = DMS.from_radians(value)
    sign = "-" if dms.negative else ""
    # Two digits for the integer part, plus the point and the decimals when
    # there are any. Computing this as 3 + decimals pads "48" to "048" at
    # decimals=0.
    width = 2 if decimals == 0 else 3 + decimals
    if symbols:
        return f"{sign}{dms.degrees}° {dms.minutes:02d}' {dms.seconds:0{width}.{decimals}f}\""
    return f"{sign}{dms.degrees} {dms.minutes:02d} {dms.seconds:.{decimals}f}"


_DMS_PATTERN = re.compile(
    r"""^\s*(?P<sign>[+-])?\s*
        (?P<deg>\d+(?:\.\d+)?)\s*[°dD:\s]\s*
        (?:(?P<min>\d+(?:\.\d+)?)\s*['′mM:\s]\s*)?
        (?:(?P<sec>\d+(?:\.\d+)?)\s*["″sS]?\s*)?$""",  # noqa: RUF001 - U+2032/U+2033
        # are the real prime and double-prime marks used in field books and
        # vendor exports; they are not typos for a grave accent.
    re.VERBOSE,
)


def parse_angle(text: str, default_unit: str = "degrees") -> float:
    """Parse an angle written in any of the forms a user might type.

    Handles ``12.5``, ``12 30 45``, ``12-30-45``, ``12° 30' 45.5"`` and
    ``12d30m45s``. Returns radians.

    The decimal separator must be a period: this parses *file and field* input,
    which specs/18 section 5 requires to be locale-independent. Locale-aware
    parsing of what a user types into a widget belongs in the GUI layer.
    """
    stripped = text.strip()
    if not stripped:
        raise ValueError("empty angle")

    normalised = stripped.replace("-", " ") if _looks_sexagesimal(stripped) else stripped
    negative = stripped.lstrip().startswith("-")

    match = _DMS_PATTERN.match(normalised.lstrip("+-").strip())
    if match and (match.group("min") is not None or match.group("sec") is not None):
        value = dms_to_radians(
            float(match.group("deg")),
            float(match.group("min") or 0.0),
            float(match.group("sec") or 0.0),
        )
        return -abs(value) if negative else value

    try:
        scalar = float(stripped)
    except ValueError:
        raise ValueError(f"could not parse {text!r} as an angle") from None

    if default_unit == "degrees":
        return math.radians(scalar)
    if default_unit == "gon":
        return scalar / GON_PER_RADIAN
    if default_unit == "radians":
        return scalar
    raise ValueError(f"unknown default unit {default_unit!r}")


def _looks_sexagesimal(text: str) -> bool:
    """Whether a hyphen in *text* separates components rather than signing it."""
    body = text.lstrip().lstrip("+-")
    return body.count("-") >= 1


# -- angle arithmetic ----------------------------------------------------


def wrap_to_2pi(value: float) -> float:
    """Wrap an angle into ``[0, 2pi)``. For bearings and circle readings.

    The modulo alone does not honour the half-open range: for a tiny negative
    input the true result is just below ``2pi``, which is not representable
    distinctly from ``2pi`` in binary floating point, so ``%`` returns exactly
    ``2pi``. That surfaces as a circular mean of 359 deg and 1 deg reporting
    360 deg instead of 0 deg -- correct modulo a turn, but wrong by the
    function's own contract and surprising to every caller that compares
    against zero.
    """
    wrapped = value % TWO_PI
    return 0.0 if wrapped >= TWO_PI else wrapped


def wrap_to_pi(value: float) -> float:
    """Wrap an angle into ``(-pi, pi]``. For angular differences."""
    wrapped = (value + math.pi) % (2.0 * math.pi) - math.pi
    # The modulo above maps exactly -pi to -pi; the convention here is half-open
    # at the negative end so that a difference of half a turn has one
    # representation rather than two.
    return math.pi if wrapped == -math.pi else wrapped


def angular_difference(first: float, second: float) -> float:
    """The signed difference ``first - second``, wrapped into ``(-pi, pi]``.

    Using this rather than plain subtraction is what makes a comparison correct
    across the 0/2pi discontinuity.
    """
    return wrap_to_pi(first - second)


def circular_mean(angles: list[float] | tuple[float, ...]) -> float:
    """Mean of angles, computed on the unit circle.

    The arithmetic mean of 359 degrees and 1 degree is 180 degrees, which is
    the opposite of the right answer. Averaging the unit vectors gives 0
    degrees.

    This is not a hypothetical: reducing a face-left/face-right pair straddling
    the zero of the horizontal circle needs exactly this
    (``specs/09-module-total-station.md`` section 2.1).

    Raises:
        ValueError: for an empty input, or when the angles are so evenly spread
            that their mean direction is undefined -- a real condition that
            must not be papered over with an arbitrary answer.
    """
    if not angles:
        raise ValueError("circular_mean of no angles")
    sin_sum = math.fsum(math.sin(angle) for angle in angles)
    cos_sum = math.fsum(math.cos(angle) for angle in angles)
    if abs(sin_sum) < 1e-12 and abs(cos_sum) < 1e-12:
        raise ValueError("circular mean is undefined: the angles cancel out")
    return wrap_to_2pi(math.atan2(sin_sum, cos_sum))


# -- unit conversion -----------------------------------------------------

#: Multiplicative factors to the SI representation of each unit.
_TO_SI: dict[str, tuple[Unit, float]] = {
    # length
    "m": (Unit.METRE, 1.0),
    "metre": (Unit.METRE, 1.0),
    "meter": (Unit.METRE, 1.0),
    "km": (Unit.METRE, 1000.0),
    "mm": (Unit.METRE, 0.001),
    "ft": (Unit.METRE, METRES_PER_INTERNATIONAL_FOOT),
    "foot": (Unit.METRE, METRES_PER_INTERNATIONAL_FOOT),
    "us_survey_foot": (Unit.METRE, METRES_PER_US_SURVEY_FOOT),
    # angle
    "rad": (Unit.RADIAN, 1.0),
    "radian": (Unit.RADIAN, 1.0),
    "deg": (Unit.RADIAN, math.pi / 180.0),
    "degree": (Unit.RADIAN, math.pi / 180.0),
    "gon": (Unit.RADIAN, 1.0 / GON_PER_RADIAN),
    "arcsec": (Unit.RADIAN, math.pi / 648000.0),
    "mgon": (Unit.RADIAN, 1.0 / (GON_PER_RADIAN * 1000.0)),
    # acceleration
    "m/s^2": (Unit.ACCELERATION, 1.0),
    "mgal": (Unit.ACCELERATION, METRES_PER_SECOND_SQUARED_PER_MGAL),
    "ugal": (Unit.ACCELERATION, METRES_PER_SECOND_SQUARED_PER_UGAL),
    # dimensionless
    "": (Unit.DIMENSIONLESS, 1.0),
    "ppm": (Unit.DIMENSIONLESS, 1e-6),
    # time
    "s": (Unit.SECOND, 1.0),
    # temperature. Celsius is deliberately absent: it is an affine scale, and a
    # multiplicative table cannot express it. celsius_to_kelvin() does that.
    "k": (Unit.KELVIN, 1.0),
    "kelvin": (Unit.KELVIN, 1.0),
    # pressure
    "pa": (Unit.PASCAL, 1.0),
    "hpa": (Unit.PASCAL, 100.0),
    "mbar": (Unit.PASCAL, 100.0),
    "millibar": (Unit.PASCAL, 100.0),
    "mmhg": (Unit.PASCAL, 133.322387415),
    "torr": (Unit.PASCAL, 133.322387415),
    "inhg": (Unit.PASCAL, 3386.389),
}

#: 0 degrees Celsius in kelvin.
KELVIN_AT_ZERO_CELSIUS = 273.15


def celsius_to_kelvin(value: float) -> float:
    """Convert a temperature to kelvin.

    Separate from :func:`convert` because the Celsius scale is affine, and a
    table of multiplicative factors cannot express an offset. Trying to force it
    through would convert a *difference* of 20 degrees into 293.15 K, which is
    the kind of silent error the unit machinery exists to prevent.

    The offset does not change a variance, so a :class:`~geocomp.core.uncertainty.Quantity`
    keeps its uncertainty across this conversion unchanged.
    """
    return value + KELVIN_AT_ZERO_CELSIUS


def kelvin_to_celsius(value: float) -> float:
    """Convert a temperature from kelvin. See :func:`celsius_to_kelvin`."""
    return value - KELVIN_AT_ZERO_CELSIUS


def dimension_of(unit: str) -> Unit:
    """The dimension a named unit belongs to.

    ``dimension_of("hPa")`` is :attr:`Unit.PASCAL`. Useful at an import
    boundary, where a column's unit is a string the user chose and the value has
    to be converted once into the SI unit of whatever dimension that is.

    Raises:
        ValueError: for an unknown unit name -- deliberately not a
            ``GeoCompError``, matching :func:`convert`: an unknown unit is a
            programming or configuration mistake, not a datum to report.
    """
    entry = _TO_SI.get(unit.lower())
    if entry is None:
        raise ValueError(f"unknown unit {unit!r}")
    return entry[0]


def convert(value: float, from_unit: str, to_unit: str) -> float:
    """Convert *value* between two named units of the same dimension.

    Raises:
        ValueError: for an unknown unit, or a conversion between dimensions --
            which is a bug in the caller, not a value to coerce.
    """
    source = _TO_SI.get(from_unit.lower())
    target = _TO_SI.get(to_unit.lower())
    if source is None:
        raise ValueError(f"unknown unit {from_unit!r}")
    if target is None:
        raise ValueError(f"unknown unit {to_unit!r}")
    if source[0] is not target[0]:
        raise ValueError(
            f"cannot convert {from_unit!r} ({source[0].name}) to {to_unit!r} ({target[0].name})"
        )
    return value * source[1] / target[1]
