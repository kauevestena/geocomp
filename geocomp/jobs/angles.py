# SPDX-License-Identifier: GPL-2.0-or-later
"""How an angle is typed into a field-book grid (FR-012).

A surveyor types an angle one of four ways, and which one is a property of the
*job*, chosen in the Field book window's first step and shown in the column's header:

* **degrees, minutes and seconds, separated** -- ``87 31 15``, ``87-31-15``,
  ``87°31'15"``. The default.
* **packed** -- ``87.3115`` for 87°31'15", the minutes and seconds written after
  the decimal mark, as Posição and most Brazilian field software take them.
* **decimal degrees** -- ``87.520833``.
* **gon** -- ``97.245370``.

**A convention is strict, because guessing between them is a silent error of up
to a factor of sixty.** ``87.3115`` is a valid angle in three of the four and a
different angle in each, so a cell is read in the job's convention or refused:
a fraction on the degrees of a separated angle is not quietly taken as decimal
degrees, and minutes or seconds of sixty or more are not carried. What a
refusal says is the presentation layer's (``geocomp/gui/workbench/messages.py``).

The decimal mark may be a comma. A field book never uses a comma to group
thousands, which is the assumption ``geocomp.io.mapping.parse_number`` already
rests on.

This is reading what was typed, at the boundary, into radians -- the same
boundary conversion the file importers make, by the same arithmetic
(:func:`geocomp.core.units.dms_to_radians`), so an angle typed here and the same
angle read from a CSV are the same number to the last bit.
"""

from __future__ import annotations

import math
import re
from enum import Enum

from geocomp.core.errors import ValidationError
from geocomp.core.units import DMS, GON_PER_RADIAN, dms_to_radians

__all__ = ["AngleTyping", "format_typed_angle", "parse_typed_angle"]


class AngleTyping(Enum):
    """The convention a job's angles are typed in. The values are stored in the job file."""

    DMS = "dms"
    DMS_PACKED = "dms_packed"
    DECIMAL_DEGREES = "decimal_degrees"
    GON = "gon"


#: What may stand between the parts of a separated angle: spaces, a hyphen, a
#: colon, and the degree, minute and second marks in their typed and typeset forms.
_SEPARATORS = re.compile(r"[\s:°ºd'′m\"″s-]+", re.IGNORECASE)  # noqa: RUF001 -- the real marks
_NUMBER = re.compile(r"^\d+(?:\.\d+)?$")
_WHOLE = re.compile(r"^\d+$")
_PACKED = re.compile(r"^(?P<degrees>\d+)(?:\.(?P<fraction>\d*))?$")


def parse_typed_angle(text: str, typing: AngleTyping) -> float:
    """The angle *text* types, in radians, read in the convention *typing*.

    Raises:
        ValidationError: for text that is not an angle in that convention. Each
            convention has its own code, because what the user should type
            instead differs.
    """
    cleaned = text.strip().replace(",", ".")
    negative = cleaned.startswith("-")
    body = cleaned.lstrip("+-").strip()
    if typing is AngleTyping.DMS:
        magnitude = _separated(body, text)
    elif typing is AngleTyping.DMS_PACKED:
        magnitude = _packed(body, text)
    else:
        if not _NUMBER.match(body):
            raise ValidationError("typed_angle_not_a_number", received=text)
        scalar = float(body)
        magnitude = math.radians(scalar) if typing is AngleTyping.DECIMAL_DEGREES else scalar / GON_PER_RADIAN
    return -magnitude if negative else magnitude


def _separated(body: str, text: str) -> float:
    parts = [part for part in _SEPARATORS.split(body) if part]
    if not 1 <= len(parts) <= 3 or not all(_NUMBER.match(part) for part in parts):
        raise ValidationError("typed_angle_not_dms", received=text)
    # Only the last part may carry a fraction, and not when it is the degrees:
    # "87.5" alone is decimal degrees, which is another convention.
    if not all(_WHOLE.match(part) for part in parts[:-1]) or (
        len(parts) == 1 and not _WHOLE.match(parts[0])
    ):
        raise ValidationError("typed_angle_fraction_misplaced", received=text)
    degrees, minutes, seconds = (*(float(part) for part in parts), 0.0, 0.0)[:3]
    if minutes >= 60.0 or seconds >= 60.0:
        raise ValidationError("typed_angle_sexagesimal_out_of_range", received=text)
    return dms_to_radians(degrees, minutes, seconds)


def _packed(body: str, text: str) -> float:
    """``DDD.MMSSsss``, read from its digits: 87.3115 as a float is 87.31149999."""
    match = _PACKED.match(body)
    if match is None:
        raise ValidationError("typed_angle_not_packed", received=text)
    digits = (match.group("fraction") or "").ljust(4, "0")
    minutes, seconds = float(digits[:2]), float(f"{digits[2:4]}.{digits[4:] or '0'}")
    if minutes >= 60.0 or seconds >= 60.0:
        raise ValidationError("typed_angle_sexagesimal_out_of_range", received=text)
    return dms_to_radians(float(match.group("degrees")), minutes, seconds)


def format_typed_angle(radians: float, typing: AngleTyping, decimals: int = 4) -> str:
    """*radians* as it would be typed in the convention *typing*, to read back the same.

    *decimals* are those of the seconds, in the two sexagesimal conventions. A
    decimal angle is written to four more, so that it holds the same precision:
    0.0001" is about 3e-8 of a degree.

    For what GeoComp fills in itself -- a document opened from the toolbox, a
    change of convention -- never for what the user typed, which is kept as
    typed.
    """
    if typing is AngleTyping.DECIMAL_DEGREES:
        return f"{math.degrees(radians):.{decimals + 4}f}"
    if typing is AngleTyping.GON:
        return f"{radians * GON_PER_RADIAN:.{decimals + 4}f}"
    sexagesimal = DMS.from_radians(radians)
    degrees, minutes, seconds = sexagesimal.degrees, sexagesimal.minutes, round(sexagesimal.seconds, decimals)
    # A seconds value that rounds to 60 is carried, as core.units.format_dms carries it.
    if seconds >= 60.0:
        seconds, minutes = 0.0, minutes + 1
    if minutes >= 60:
        minutes, degrees = 0, degrees + 1
    sign = "-" if sexagesimal.negative else ""
    if typing is AngleTyping.DMS:
        return f"{sign}{degrees} {minutes:02d} {seconds:0{3 + decimals if decimals else 2}.{decimals}f}"
    whole, _mark, fraction = f"{seconds:0{3 + decimals if decimals else 2}.{decimals}f}".partition(".")
    return f"{sign}{degrees}.{minutes:02d}{whole}{fraction}"
