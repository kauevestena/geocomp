# SPDX-License-Identifier: GPL-2.0-or-later
"""How a quantity is written for a person to read (FR-067; phase P12a).

``specs/15-ui-menu-and-settings.md`` section 2.3. Four settings promise it --
``interface.angle_format``, ``interface.angle_decimals``,
``interface.coordinate_decimals`` and ``interface.distance_unit`` -- and until
P12a no report read any of them: a user who chose gon saw decimal degrees, and
a UTM northing printed as ``7.3951e+06`` whatever they chose, because the
report's number formatter switches to an exponent at a million.

**What follows the settings, and what deliberately does not.**

* *Absolute angles* -- a direction, an orientation, a latitude -- in the chosen
  format, to the chosen places.
* *Small angles* -- a misclosure, a residual, a collimation error -- in the
  chosen format's small unit: arc-seconds for sexagesimal and decimal degrees,
  centesimal seconds for gon, microradians for radians.
* *Coordinates* to the chosen places, never with an exponent. In the units of
  their CRS, which the setting does not change: converting a metric grid to
  feet would describe a coordinate system that does not exist.
* *Distances* -- a measured or derived length -- in the chosen unit.

Uncertainties, residuals in length and misclosures in millimetres stay in SI.
They are precision figures with their own conventional units, and a report
mixing feet for a distance with millimetres for its uncertainty is still
unambiguous, where one converting both invites a reader to compare a foot with
a metre.

**Only what a person reads.** Every file GeoComp writes -- JSON, CSV, the
project store -- stays in SI with full precision (FR-095): a setting that
changed a file's numbers would make two users' files disagree about the same
survey.

This module is QGIS-free; :func:`geocomp.algorithms.display.display_format`
resolves the four settings into one.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from geocomp.core.errors import ValidationError
from geocomp.core.units import GON_PER_RADIAN, convert, format_dms

__all__ = ["ANGLE_FORMATS", "DISTANCE_UNITS", "DisplayFormat"]

#: ``interface.angle_format``'s choices, in the settings' order.
ANGLE_FORMATS = ("dms", "decimal_degrees", "gon", "radian")

#: ``interface.distance_unit``'s choices.
DISTANCE_UNITS = ("metre", "foot", "us_survey_foot")

#: Extra places a decimal format needs to resolve what one more place of
#: seconds resolves. ``angle_decimals`` counts places on the *smallest
#: customary unit* -- seconds, for DMS -- so that one setting means about the
#: same angle in every format: 0.1" is 2.8e-5 degrees (five places), 3.1e-5 gon
#: (five) and 4.8e-7 rad (seven).
_EXTRA_PLACES = {"decimal_degrees": 4, "gon": 4, "radian": 6}

_ARCSECONDS_PER_RADIAN = 180.0 * 3600.0 / math.pi
#: A centesimal second, ``cc``: 1e-4 gon.
_CC_PER_RADIAN = GON_PER_RADIAN * 1.0e4


def _missing(value: float | None) -> str | None:
    """The text for a value that cannot be formatted, or ``None`` if it can."""
    if value is None:
        return "—"
    if math.isnan(value):
        return "—"
    if math.isinf(value):
        return "∞" if value > 0 else "-∞"
    return None


@dataclass(frozen=True)
class DisplayFormat:
    """The four interface settings, and how each kind of quantity is written under them."""

    angle_format: str = "dms"
    angle_decimals: int = 1
    coordinate_decimals: int = 4
    distance_unit: str = "metre"

    def __post_init__(self) -> None:
        if self.angle_format not in ANGLE_FORMATS:
            raise ValidationError(
                "display_angle_format_unknown",
                received=self.angle_format,
                expected=list(ANGLE_FORMATS),
            )
        if self.distance_unit not in DISTANCE_UNITS:
            raise ValidationError(
                "display_distance_unit_unknown",
                received=self.distance_unit,
                expected=list(DISTANCE_UNITS),
            )
        for name, value, top in (
            ("angle_decimals", self.angle_decimals, 6),
            ("coordinate_decimals", self.coordinate_decimals, 9),
        ):
            if not 0 <= value <= top:
                raise ValidationError(
                    "display_decimals_out_of_range",
                    parameter=name,
                    received=value,
                    expected=f"a whole number from 0 to {top}",
                )

    # -- angles ------------------------------------------------------------

    def angle(self, radians: float | None) -> str:
        """An absolute angle -- a direction, an orientation, a latitude."""
        missing = _missing(radians)
        if missing is not None:
            return missing
        if self.angle_format == "dms":
            return format_dms(radians, decimals=self.angle_decimals)
        places = self.angle_decimals + _EXTRA_PLACES[self.angle_format]
        if self.angle_format == "decimal_degrees":
            return f"{math.degrees(radians):.{places}f}°"
        if self.angle_format == "gon":
            return f"{radians * GON_PER_RADIAN:.{places}f} gon"
        return f"{radians:.{places}f} rad"

    @property
    def small_angle_symbol(self) -> str:
        """The unit a small angle is written in, for a column heading."""
        if self.angle_format == "gon":
            return "cc"
        if self.angle_format == "radian":
            return "µrad"
        return "″"

    def small_angle(self, radians: float | None) -> str:
        """A misclosure, a residual, an index error: a number in :attr:`small_angle_symbol`."""
        missing = _missing(radians)
        if missing is not None:
            return missing
        if self.angle_format == "gon":
            value = radians * _CC_PER_RADIAN
        elif self.angle_format == "radian":
            value = radians * 1.0e6
        else:
            value = radians * _ARCSECONDS_PER_RADIAN
        return f"{value:.{self.angle_decimals}f}"

    # -- lengths -----------------------------------------------------------

    def coordinate(self, value: float | None) -> str:
        """A coordinate in its CRS's units, to the configured places, never with an exponent."""
        missing = _missing(value)
        if missing is not None:
            return missing
        return f"{value:.{self.coordinate_decimals}f}"

    @property
    def distance_symbol(self) -> str:
        """The unit a distance is written in, for a column heading."""
        return {"metre": "m", "foot": "ft", "us_survey_foot": "US ft"}[self.distance_unit]

    def distance(self, metres: float | None) -> str:
        """A length, converted to the configured unit, to the coordinate places."""
        missing = _missing(metres)
        if missing is not None:
            return missing
        value = convert(metres, "metre", self.distance_unit)
        return f"{value:.{self.coordinate_decimals}f}"
