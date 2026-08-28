# SPDX-License-Identifier: GPL-2.0-or-later
"""DynAdjust's number and angle conventions, in one place (FR-320, FR-163).

Confirmed against upstream at commit ``5cdb897``: Appendix B of the User's
Guide, which specifies the DNA formats column by column, plus its statement that
DynaML's elements *"follow the definitions contained in the DNA format
specification"* -- so the two formats share these conventions and this module
serves both the writer and the readers.

**Angles travel in HP notation**, which is the one convention here most likely
to be got wrong. ``91.41495`` is not 91.41495 degrees; it is
91 deg 41 min 49.5 sec -- degrees, then minutes and seconds packed into the decimal part
as ``DDD.MMSSsssss``. Reading it as decimal degrees is an error of up to about
0.6°, which on a 2 km sight is 20 m: large enough to ruin an adjustment and
small enough to look like a blunder in the field rather than a units bug.

**Angular standard deviations are in seconds of arc**, not in HP notation and
not in radians. The two live side by side in the same record -- ``<Value>`` in
HP, ``<StdDev>`` in seconds -- which is exactly the kind of asymmetry that gets
implemented once as "whatever the other field did".

GeoComp holds every angle in radians and every distance in metres
(``specs/04`` section 6), so all of this is a boundary conversion and none of it
leaks inward.
"""

from __future__ import annotations

import math

from geocomp.core.errors import ValidationError

__all__ = [
    "format_epoch",
    "format_metres",
    "format_variance",
    "hp_to_radians",
    "parse_epoch",
    "radians_to_hp",
    "radians_to_seconds",
    "seconds_to_radians",
]

#: Decimals kept on a linear value, in metres. Four is DynAdjust's own default
#: for output (Guide C.8.4) and a tenth of a millimetre is below the noise of
#: any terrestrial observation, so nothing is lost.
LINEAR_DECIMALS = 4

#: Decimals kept on the seconds part of an HP angle. Five gives 10 microarcsec,
#: which is finer than any instrument reports and finer than the adjustment can
#: use, so the round trip is exact for every real observation.
SECONDS_DECIMALS = 5


def radians_to_hp(radians: float) -> str:
    """Radians to DynAdjust's ``DDD.MMSSsssss`` notation.

    Negative angles carry the sign on the degrees, as vertical angles in the
    Guide's own examples do (``-0 20 10.331`` is written ``-0.2010331``). The
    sign is applied to the assembled string rather than to the components,
    because ``-0`` degrees with positive minutes is a real case and negating
    each part separately loses it.
    """
    if not math.isfinite(radians):
        raise ValidationError(
            "angle_not_finite",
            received=radians,
            expected="a finite angle in radians",
        )

    degrees_total = math.degrees(abs(radians))
    degrees = int(degrees_total)
    minutes_total = (degrees_total - degrees) * 60.0
    minutes = int(minutes_total)
    seconds = (minutes_total - minutes) * 60.0

    # Rounding the seconds can carry into the minutes and then the degrees;
    # doing it here rather than in the format string keeps 59.999999 from being
    # written as "60.00000".
    seconds = round(seconds, SECONDS_DECIMALS)
    if seconds >= 60.0:
        seconds -= 60.0
        minutes += 1
    if minutes >= 60:
        minutes -= 60
        degrees += 1

    fraction = f"{minutes:02d}{seconds:0{SECONDS_DECIMALS + 3}.{SECONDS_DECIMALS}f}".replace(".", "")
    sign = "-" if radians < 0 else ""
    return f"{sign}{degrees}.{fraction}"


def hp_to_radians(value: str | float) -> float:
    """``DDD.MMSSsssss`` to radians.

    The inverse of :func:`radians_to_hp`, and the reason both live here: a
    reader and a writer that each carry their own copy of this convention drift,
    and the drift is invisible until a round trip is tested.
    """
    text = str(value).strip()
    if not text:
        raise ValidationError("hp_angle_empty", expected="an angle in DDD.MMSSsss notation")
    try:
        number = float(text)
    except ValueError as error:
        raise ValidationError(
            "hp_angle_malformed",
            received=text,
            expected="a number in DDD.MMSSsss notation, e.g. 91.41495 for 91d 41' 49.5\"",
        ) from error

    sign = -1.0 if number < 0 else 1.0
    number = abs(number)
    degrees = int(number)
    rest = (number - degrees) * 100.0
    minutes = int(round(rest, 8))
    # round() above absorbs the binary representation error that otherwise makes
    # 41 arrive as 40.999999999 and truncate to 40 -- a one-minute error, which
    # is 30 cm at a kilometre and looks like a survey mistake.
    if minutes >= 60:
        raise ValidationError(
            "hp_angle_minutes_out_of_range",
            received=text,
            expected="minutes below 60 in DDD.MMSSsss notation",
        )
    seconds = round((rest - minutes) * 100.0, 6)
    if seconds >= 60.0:
        raise ValidationError(
            "hp_angle_seconds_out_of_range",
            received=text,
            expected="seconds below 60 in DDD.MMSSsss notation",
        )
    return sign * math.radians(degrees + minutes / 60.0 + seconds / 3600.0)


def radians_to_seconds(radians: float) -> str:
    """An angular standard deviation, in seconds of arc (Guide Table B.4)."""
    return f"{math.degrees(radians) * 3600.0:.{SECONDS_DECIMALS}f}"


def seconds_to_radians(value: str | float) -> float:
    """Seconds of arc to radians."""
    return math.radians(float(value) / 3600.0)


def format_metres(value: float) -> str:
    return f"{value:.{LINEAR_DECIMALS}f}"


def format_variance(value: float) -> str:
    """A variance, written so it reads back as the **same double**.

    ``specs/07`` acceptance criterion 2 asks for a GNSS covariance to round-trip
    *to full double precision*, and that rules out a fixed number of decimals.
    Upstream's own files use ``%.13e``, which is fourteen significant digits and
    silently drops the last two of a double: ``1.234567890123456e-07`` comes
    back as ``1.2345678901235e-07``. Matching their style would have looked
    right and lost data, which is the whole failure mode the criterion names.

    ``repr`` of a Python float is the *shortest* string that reads back
    identically, so it is exact by construction and no longer than it must be.
    The ``float()`` conversion is load-bearing rather than defensive: under
    NumPy 2, ``repr`` of a ``np.float64`` is ``"np.float64(1.9e-06)"``, and a
    covariance is NumPy throughout. That exact trap was hit once already, in
    the CSV exporter (``geocomp/algorithms/reporting.py``).
    """
    return repr(float(value))


def format_epoch(day: int, month: int, year: int) -> str:
    """``dd.mm.yyyy``, DynAdjust's epoch format (Guide Table B.5)."""
    return f"{day:02d}.{month:02d}.{year:04d}"


def parse_epoch(text: str) -> tuple[int, int, int]:
    """``dd.mm.yyyy`` to ``(day, month, year)``.

    Refuses anything else rather than guessing. ``01.03.2010`` is unambiguous
    only because the format is stated; read as ISO it would be a different date
    entirely, and an epoch wrong by two months is a datum shift in a monitoring
    comparison.
    """
    parts = text.strip().split(".")
    if len(parts) != 3:
        raise ValidationError(
            "epoch_malformed",
            received=text,
            expected="dd.mm.yyyy, as DynAdjust writes it (e.g. 01.03.2010)",
        )
    try:
        day, month, year = (int(part) for part in parts)
    except ValueError as error:
        raise ValidationError(
            "epoch_malformed", received=text, expected="dd.mm.yyyy with numeric parts"
        ) from error
    if not (1 <= month <= 12 and 1 <= day <= 31):
        raise ValidationError(
            "epoch_out_of_range", received=text, expected="a real date in dd.mm.yyyy"
        )
    return day, month, year
