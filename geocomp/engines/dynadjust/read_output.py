# SPDX-License-Identifier: GPL-2.0-or-later
"""Reading what ``dnaadjust`` wrote back (FR-322, FR-323).

``specs/07-engine-dynadjust.md`` section 5. One run writes up to four text
files -- ``.adj`` (the adjustment), ``.xyz`` (adjusted coordinates alone),
``.apu`` (positional uncertainty and variances) and ``.cor`` (corrections to the
initial coordinates) -- and this module turns them into the same
:class:`~geocomp.core.models.solution.Solution` the in-house core produces. That
identity is the whole point of FR-323: everything downstream stays
engine-agnostic, and P6 becomes a cross-validation rather than a second
pipeline.

Four things about these files decide the shape of the code here.

**They describe themselves.** Each begins with a key/value preamble naming the
version, the reference frame, the epoch, the coordinate types printed and the
units the variances are in. The parsers read the preamble first and lay out the
columns from it, so a file written with different flags is read correctly rather
than read wrongly (specs/07 section 5 rule 1).

**Angles are in HP notation, including the ones that do not look like it.** The
ellipse orientation in the ``.apu`` is ``RadtoDms(azimuth)``, so ``79.4724`` is
79 deg 47 min 24 sec and not 79.47 degrees. Reading it as decimal degrees rotates every
ellipse by up to a third of a degree -- small enough to look plausible on a map.

**Nothing is inferred.** A quantity DynAdjust did not report is ``None``
(specs/07 section 5 rule 2). The ``.apu`` and ``.cor`` files are written only
when asked for, so their absence is a configuration fact, and the ``.cor`` file
omits stations whose correction fell below ``--hz-corr-threshold`` or
``--vt-corr-threshold``, so a missing row there is not a missing station.

**Measurement rows carry no identifier.** They name a type letter, up to three
stations and a component, which is not enough to name a GeoComp observation.
:func:`match_observations` maps them back by the original file order DynAdjust
preserves by default, and *verifies* type and stations on every row rather than
trusting the order it relies on.
"""

from __future__ import annotations

import math
import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path

import numpy as np

from geocomp.core.errors import DataError
from geocomp.core.models.epoch import Epoch
from geocomp.core.models.observation import OBSERVATION_TYPES, ObservationType
from geocomp.core.models.position import CoordinateSystem, HeightType, Position
from geocomp.core.models.solution import (
    AdjustmentStatistics,
    ErrorEllipse,
    ObservationResult,
    TestResult,
)
from geocomp.core.uncertainty import Covariance, Quantity
from geocomp.core.units import Unit
from geocomp.engines.dynadjust.columns import (
    CONSTRAINT,
    CORR,
    HEIGHT,
    LAT_EAST,
    LON_NORTH,
    MSR,
    OUTLIER,
    PACORR,
    PAD2,
    PAD3,
    PREC,
    REL,
    STAT,
    STATION,
    STDDEV,
    XYZ,
    ZONE,
    Column,
    ColumnPlan,
    require_header,
    take_name,
)
from geocomp.engines.dynadjust.formats import hp_to_radians, parse_epoch, seconds_to_radians

__all__ = [
    "AdjustedMeasurement",
    "AngularFormat",
    "CoordinateRow",
    "OutputPreamble",
    "match_observations",
    "read_adj",
    "read_apu",
    "read_cor",
    "read_statistics",
    "read_xyz",
]

#: DynAdjust versions whose output layout this module was checked against, by
#: ``major.minor``. Patch releases are accepted: upstream's own version macro
#: bumps the patch for changes that do not touch the printers, and refusing them
#: would make GeoComp reject a bug-fix release it reads perfectly well.
SUPPORTED_LAYOUTS = ("1.4",)

#: Label width of the key/value preamble, ``PRINT_VAR_PAD`` in
#: ``dnaconsts-iostream.hpp``.
PREAMBLE_LABEL_WIDTH = 35

_COORDINATE_COLUMNS: dict[str, tuple[str, int]] = {
    "P": ("Latitude", LAT_EAST),
    "L": ("Longitude", LON_NORTH),
    "E": ("Easting", LAT_EAST),
    "N": ("Northing", LON_NORTH),
    "H": ("H(Ortho)", HEIGHT),
    "h": ("h(Ellipse)", HEIGHT),
    "z": ("Zone", ZONE),
    "X": ("X", XYZ),
    "Y": ("Y", XYZ),
    "Z": ("Z", XYZ),
}

#: The coordinate types whose value is an angle, and so must not be read as a
#: plain decimal number.
_ANGULAR_TYPES = frozenset("PL")

#: An angular row's ``Measured`` and ``Adjusted`` are angles, written in
#: whichever of the three angle formats the run chose.
_ANGLE_COLUMNS = frozenset({"Measured", "Adjusted"})

#: An angular row's correction, precisions and pre-adjustment correction are in
#: **seconds of arc** -- not in the angle format, and not in radians. Both
#: branches of ``PrintAdjMeasurementsAngular`` wrap them in ``Seconds(...)``,
#: whichever format the two value columns took. Reading them as an angle in the
#: same format as the value is a factor-of-3600 error on every angular residual.
_SECONDS_COLUMNS = frozenset(
    {"Correction", "Meas. SD", "Adj. SD", "Corr. SD", "Pre Adj Corr"}
)

#: The component letters ``PrintAdjMeasurementsAngular`` is called with. The
#: component, not the type, is what decides: a ``Y`` cluster prints ``P`` and
#: ``L`` as angles and ``H`` as a height, all under one type letter, so a rule
#: keyed on the type alone reads a height as an angle.
_ANGULAR_COMPONENTS = frozenset({"P", "L", "a", "v"})

#: The component letters ``PrintAdjMeasurementsLinear`` is called with, listed so
#: an unrecognised one is a visible gap rather than a silent default.
_LINEAR_COMPONENTS = frozenset({"H", "X", "Y", "Z", "e", "h", "n", "s", "u"})


@dataclass(frozen=True)
class OutputPreamble:
    """The key/value block every DynAdjust output file opens with.

    It is what makes the parsers layout-independent: ``coordinate_types`` and
    ``station_corrections`` between them determine the whole coordinate table,
    and ``variance_units`` determines whether the ``.apu`` variances are
    cartesian or local.
    """

    version: str = ""
    reference_frame: str = ""
    epoch: Epoch | None = None
    geoid_model: str | None = None
    coordinate_types: str = "PLHhXYZ"
    station_corrections: bool = False
    #: ``"XYZ"`` or ``"ENU"``; only the ``.apu`` states it.
    variance_units: str = "XYZ"
    full_covariance: bool = False
    confidence: float = 0.95
    #: Confidence of the error-ellipse axes and variances, which DynAdjust
    #: reports at one sigma while the positional uncertainty is at 95%.
    ellipse_confidence: float = 0.683
    #: The ``dnaadjust`` invocation, verbatim. It is the *only* place the file
    #: records how angles were formatted -- see :func:`angular_format`.
    command_line: str = ""
    values: dict[str, str] = field(default_factory=dict)

    @property
    def angular_coordinates(self) -> bool:
        return bool(_ANGULAR_TYPES & set(self.coordinate_types))

    def option(self, name: str) -> str | None:
        """The value of ``--name`` in the recorded command line, if it is there."""
        match = re.search(rf"--{re.escape(name)}[= ]+([^\s-]\S*)", self.command_line)
        return match.group(1) if match else None


class AngularFormat(Enum):
    """How an angle is written in a DynAdjust output column.

    The distinction is not cosmetic and not recoverable from the number: HP's
    ``-36.331031467`` and decimal degrees' ``-36.552865187`` are the same angle,
    both are valid HP, and reading one as the other is an error of up to 0.6
    degrees -- 60 m on a 6 km sight. Nothing in the preamble's key/value block
    names the format; only the recorded command line does.
    """

    #: ``DDD.MMSSsssss``, DynAdjust's default (``--angular-stn-type 0``).
    HP = "hp"
    #: Plain decimal degrees (``--angular-stn-type 1``).
    DEGREES = "degrees"
    #: Whitespace-separated degrees, minutes and seconds, as the ``.cor`` file
    #: and ``--dms-msr-format 0`` write them.
    SEPARATED = "separated"


def _read_lines(path: str | Path) -> list[str]:
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    return text.splitlines()


def _percent(value: str) -> float | None:
    match = re.search(r"([-+]?\d+(?:\.\d+)?)\s*%", value)
    return float(match.group(1)) / 100.0 if match else None


def read_preamble(lines: Sequence[str], *, path: str | Path | None = None) -> OutputPreamble:
    """Parse the key/value block, and refuse a layout this module does not know.

    The version gate is on ``major.minor`` (see :data:`SUPPORTED_LAYOUTS`). A
    file with no version line is refused too: it is not a DynAdjust output, and
    reading it as one would produce numbers rather than an error.
    """
    values: dict[str, str] = {}
    for line in lines:
        if line.startswith("-----") and values:
            break
        label = line[:PREAMBLE_LABEL_WIDTH].strip()
        if not label.endswith(":"):
            continue
        values[label[:-1]] = line[PREAMBLE_LABEL_WIDTH:].strip()

    version = values.get("Version", "")
    number = version.split(",", 1)[0].strip()
    layout = ".".join(number.split(".")[:2])
    if layout not in SUPPORTED_LAYOUTS:
        raise DataError(
            "dynadjust_unsupported_output_version",
            path=str(path) if path is not None else None,
            received=number or None,
            expected=list(SUPPORTED_LAYOUTS),
            hint=(
                "the column layout of DynAdjust's output files is version-specific; "
                "this one has not been checked, and reading it would risk taking a "
                "value from the wrong column"
            ),
        )

    epoch_text = values.get("Epoch", "")
    geoid = values.get("Geoid model", "").strip()
    epoch = None
    if epoch_text:
        day, month, year = parse_epoch(epoch_text)
        # An instant, not a decimal year: DynAdjust states the epoch to the day,
        # and turning that into a fraction of a year and back loses which day it
        # was. ``Epoch.from_datetime`` keeps both.
        epoch = Epoch.from_datetime(
            datetime(year, month, day, tzinfo=UTC), label=epoch_text.strip()
        )
    return OutputPreamble(
        version=number,
        reference_frame=values.get("Reference frame", ""),
        epoch=epoch,
        geoid_model=geoid or None,
        coordinate_types=values.get("Station coordinate types", "PLHhXYZ"),
        station_corrections=values.get("Station coordinate corrections", "No").lower().startswith("y"),
        variance_units=values.get("Variance matrix units", "XYZ").strip().upper() or "XYZ",
        full_covariance=values.get("Full covariance matrix", "No").lower().startswith("y"),
        confidence=_percent(values.get("Test confidence interval", "")) or 0.95,
        ellipse_confidence=_percent(values.get("Error ellipse axes", "")) or 0.683,
        command_line=values.get("Command line arguments", ""),
        values=values,
    )


def station_angular_format(
    preamble: OutputPreamble,
    *,
    declared: AngularFormat | None = None,
) -> AngularFormat:
    """How this file writes latitude and longitude, or a refusal.

    ``declared`` wins: when GeoComp drove the run it knows which flags it
    passed, and that is better evidence than anything in the file. Otherwise the
    recorded command line is consulted -- the only place the format appears. A
    run launched from a project file (``-p``) records no options there, and then
    this **raises**: the number alone cannot say which format it is (both
    readings are valid HP), so guessing would put a plausible wrong coordinate
    into a solution rather than reporting that it could not be read.
    """
    if declared is not None:
        return declared
    option = preamble.option("angular-stn-type")
    if option is not None:
        return AngularFormat.DEGREES if option.strip() == "1" else AngularFormat.HP
    if preamble.command_line:
        # dnaadjust wrote its command line and did not set the option, so the
        # default applies. That is evidence, not an assumption.
        return AngularFormat.HP
    raise DataError(
        "dynadjust_angular_format_unknown",
        coordinate_types=preamble.coordinate_types,
        hint=(
            "the file records no command line, so whether latitude and longitude "
            "are in HP notation or decimal degrees cannot be established from it; "
            "pass angular_format= to say which"
        ),
    )


def measurement_angular_format(
    preamble: OutputPreamble,
    *,
    declared: AngularFormat | None = None,
) -> AngularFormat:
    """How this file writes angular *measurements*.

    A second, independent setting: ``--angular-msr-type`` chooses degrees-minutes-seconds
    or decimal degrees, and ``--dms-msr-format`` then chooses how the former is
    written -- separated fields (the default), separated with symbols, or HP.
    A file may therefore hold station coordinates in HP and measurements in
    separated fields at the same time, which is what the shipped defaults do.
    """
    if declared is not None:
        return declared
    if preamble.option("angular-msr-type") == "1":
        return AngularFormat.DEGREES
    dms = preamble.option("dms-msr-format")
    if dms == "2":
        return AngularFormat.HP
    if dms == "1":
        raise DataError(
            "dynadjust_angular_measurement_format_unsupported",
            received="--dms-msr-format 1",
            hint=(
                "degrees, minutes and seconds written with symbols are not read yet; "
                "re-run with the default --dms-msr-format 0"
            ),
        )
    if preamble.command_line:
        return AngularFormat.SEPARATED
    raise DataError(
        "dynadjust_angular_format_unknown",
        hint=(
            "the file records no command line, so the format of its angular "
            "measurements cannot be established; pass angular_format= to say which"
        ),
    )


def read_angle(text: str, angular_format: AngularFormat, *, line: str = "") -> float:
    """One angular field, in whichever of the three formats, to radians."""
    if angular_format is AngularFormat.SEPARATED:
        return _separated_dms(text, line=line or text)
    value = _float(text, what="angle", line=line or text)
    if angular_format is AngularFormat.HP:
        return hp_to_radians(value)
    return math.radians(value)


def coordinate_plan(preamble: OutputPreamble) -> ColumnPlan:
    """The ``Adjusted Coordinates`` table's columns, for this file's flags.

    Mirrors ``AdjFile::print_stn_info_col_header``: station, constraint, one
    column per coordinate type in the order given, three standard deviations,
    optionally three corrections, then the free-text description.
    """
    columns: list[Column] = [
        Column("Station", STATION, "l"),
        Column("Const", CONSTRAINT, "l"),
    ]
    for kind in preamble.coordinate_types:
        if kind not in _COORDINATE_COLUMNS:
            continue
        label, width = _COORDINATE_COLUMNS[kind]
        columns.append(Column(label, width))
    columns.append(Column("", PAD2, "l"))
    columns += [Column(name, STDDEV) for name in ("SD(e)", "SD(n)", "SD(up)")]
    if preamble.station_corrections:
        columns.append(Column("", PAD2, "l"))
        columns += [Column(name, HEIGHT) for name in ("Corr(e)", "Corr(n)", "Corr(up)")]
    columns.append(Column("", PAD2, "l"))
    columns.append(Column("Description", len("Description"), "l"))
    return ColumnPlan(tuple(columns))


def measurement_plan(header: str) -> ColumnPlan:
    """The ``Adjusted Measurements`` table's columns.

    Two of them are optional and the preamble does not mention either, so they
    are taken from the header line itself: ``--output-tstat-adj-msr`` adds
    ``T-stat`` and ``--output-database-ids`` adds two identifier columns.
    """
    columns: list[Column] = [
        Column("M", PAD2, "l"),
        Column("Station 1", STATION, "l"),
        Column("Station 2", STATION, "l"),
        Column("Station 3", STATION, "l"),
        Column("*", PAD3, "l"),
        Column("C", PAD2, "l"),
        Column("Measured", MSR),
        Column("Adjusted", MSR),
        Column("Correction", CORR),
        Column("Meas. SD", PREC),
        Column("Adj. SD", PREC),
        Column("Corr. SD", PREC),
        Column("N-stat", STAT),
    ]
    if "T-stat" in header:
        columns.append(Column("T-stat", STAT))
    columns.append(Column("Pelzer Rel", REL))
    columns.append(Column("Pre Adj Corr", PACORR))
    columns.append(Column("Outlier?", OUTLIER))
    if "Meas. ID" in header:
        columns.append(Column("Meas. ID", STDDEV))
        columns.append(Column("Clust. ID", STDDEV))
    return ColumnPlan(tuple(columns))


def uncertainty_plan(preamble: OutputPreamble) -> ColumnPlan:
    """The ``.apu`` table's columns. ``--output-apu-vcv-units`` renames three."""
    suffixes = ("e", "n", "up") if preamble.variance_units == "ENU" else ("X", "Y", "Z")
    return ColumnPlan(
        (
            Column("Station", STATION, "l"),
            Column("", PAD2, "l"),
            Column("Latitude", LAT_EAST),
            Column("Longitude", LON_NORTH),
            Column("Hz PosU", STAT),
            Column("Vt PosU", STAT),
            Column("Semi-major", PREC),
            Column("Semi-minor", PREC),
            Column("Orientation", PREC),
            *(Column(f"Variance({suffix})", MSR) for suffix in suffixes),
        )
    )


CORRECTION_PLAN = ColumnPlan(
    (
        Column("Station", STATION, "l"),
        Column("", PAD2, "l"),
        Column("Azimuth", MSR),
        Column("V. Angle", MSR),
        Column("S. Distance", MSR),
        Column("H. Distance", MSR),
        Column("east", HEIGHT),
        Column("north", HEIGHT),
        Column("up", HEIGHT),
    )
)


def _float(text: str, *, what: str, line: str) -> float:
    try:
        return float(text)
    except ValueError as error:
        raise DataError(
            "dynadjust_output_not_a_number",
            field=what,
            received=text,
            line=line.rstrip()[:120],
        ) from error


def _optional_float(text: str, *, what: str, line: str) -> float | None:
    return _float(text, what=what, line=line) if text else None


def _normalise_name(line: str, start: int, width: int, known: Iterable[str] | None) -> tuple[str, str]:
    """Pull the station name at *start* out, and re-pad the row to nominal.

    ``std::setw`` pads but never truncates, so a name at least as wide as its
    column pushes every later field right by the overflow -- and, having no
    padding, leaves no separator before the next field. Re-padding the name to
    its nominal width restores the offsets the rest of the plan assumes, so the
    caller can slice normally whatever the name's length.
    """
    if not line[start : start + width].strip():
        return "", line
    resolution = take_name(line[start:], width=width, known=known)
    consumed = max(len(resolution.name), width)
    # The name is padded *or clipped* to exactly ``width`` here purely to restore
    # the offsets of the columns after it. Nothing reads the name back out of the
    # returned row -- the caller uses the name this function returns, which is
    # always the whole one -- so the clipping loses nothing.
    aligned = resolution.name.ljust(width)[:width]
    return resolution.name, line[:start] + aligned + line[start + consumed :]


def _station_rows(lines: Sequence[str], header_index: int) -> list[str]:
    """The data rows of a table: everything up to the first blank line."""
    rows: list[str] = []
    for line in lines[header_index + 2 :]:
        if not line.strip():
            break
        if line.startswith("---"):
            continue
        rows.append(line)
    return rows


def target_system(preamble: OutputPreamble) -> CoordinateSystem:
    """Which representation a coordinate table will be read into.

    Wanted separately from the reading because it decides whether an angular
    format is needed at all: under the shipped default ``PLHhXYZ`` the position
    is built from X, Y and Z, so latitude and longitude are never converted and
    a file that cannot state its angular format is still read perfectly.
    """
    present = {kind for kind in preamble.coordinate_types if kind in _COORDINATE_COLUMNS}
    if {"X", "Y", "Z"} <= present:
        return CoordinateSystem.CARTESIAN
    if {"P", "L"} <= present:
        return CoordinateSystem.GEODETIC
    if {"E", "N"} <= present:
        return CoordinateSystem.PROJECTED
    raise DataError(
        "dynadjust_output_has_no_usable_coordinates",
        coordinate_types=preamble.coordinate_types,
        hint="none of X/Y/Z, P/L or E/N was printed, so the table has no position to read",
    )


def _coordinate_position(
    plan: ColumnPlan,
    preamble: OutputPreamble,
    row: str,
    angular_format: AngularFormat,
) -> Position:
    """Build the :class:`Position` the row's coordinate columns describe.

    **Cartesian wins when X, Y and Z were printed**, which the default
    ``--stn-coord-types PLHhXYZ`` does. Two reasons, both about not lying:
    those columns are in metres, so the components share one unit with the
    ``.apu`` variances that will be attached to them; and the in-house core also
    works in a metre frame, so the two solutions are directly comparable rather
    than comparable after a conversion nobody checked (specs/07 section 6).

    **The components carry no uncertainty here.** The table's ``SD(e)``,
    ``SD(n)`` and ``SD(up)`` are standard deviations in the *local* frame, and
    the position's components are not: attaching a metre of northing to a
    latitude in radians, or to X, would put a real number on the wrong axis. The
    local figures are returned beside the position instead, and the covariance
    that does belong on these components comes from the ``.apu``.
    """
    present = {kind for kind in preamble.coordinate_types if kind in _COORDINATE_COLUMNS}

    def read(kind: str) -> float:
        label, _ = _COORDINATE_COLUMNS[kind]
        text = plan.value(row, label)
        if kind in _ANGULAR_TYPES:
            return read_angle(text, angular_format, line=row)
        return _float(text, what=label, line=row)

    height_kind = "h" if "h" in present else ("H" if "H" in present else None)
    height_type = {
        "h": HeightType.ELLIPSOIDAL,
        "H": HeightType.ORTHOMETRIC,
        None: HeightType.NONE,
    }[height_kind]

    system = target_system(preamble)
    if system is CoordinateSystem.CARTESIAN:
        components = (read("X"), read("Y"), read("Z"))
        units = (Unit.METRE, Unit.METRE, Unit.METRE)
        # A geocentric position is by construction referred to the ellipsoid.
        height_type = HeightType.ELLIPSOIDAL
    elif system is CoordinateSystem.GEODETIC:
        components = (read("P"), read("L"), read(height_kind) if height_kind else 0.0)
        units = (Unit.RADIAN, Unit.RADIAN, Unit.METRE)
    else:
        components = (read("E"), read("N"), read(height_kind) if height_kind else 0.0)
        units = (Unit.METRE, Unit.METRE, Unit.METRE)

    values = tuple(
        Quantity.exact(value, unit) for value, unit in zip(components, units, strict=True)
    )
    return Position(
        values=values,  # type: ignore[arg-type]
        system=system,
        crs=preamble.reference_frame or "LOCAL",
        epoch=preamble.epoch,
        height_type=height_type,
        geoid_model=preamble.geoid_model,
    )


@dataclass(frozen=True)
class CoordinateRow:
    """One row of the ``Adjusted Coordinates`` table.

    Not an :class:`~geocomp.core.models.solution.AdjustedStation`: that type
    carries a covariance and an ellipse, and this table has neither. Those come
    from the ``.apu``, and joining the two is
    :func:`~geocomp.engines.dynadjust.solution.adjusted_stations`' job.

    Attributes:
        constraint: DynAdjust's three-character code, ``C`` or ``F`` per axis --
            which stations were held, and on which components.
        local_sigmas: ``SD(e)``, ``SD(n)``, ``SD(up)`` in metres, in the local
            frame. Kept separate from ``position`` because they are not the
            standard deviations of its components.
        correction: The e/n/up shift from the initial coordinates, present only
            when the run passed ``--stn-corrections``.
    """

    station_id: str
    position: Position
    constraint: str
    local_sigmas: tuple[float, float, float]
    correction: tuple[float, float, float] | None = None
    description: str = ""


def read_coordinates(
    path: str | Path,
    *,
    known: Iterable[str] | None = None,
    angular_format: AngularFormat | None = None,
) -> tuple[list[CoordinateRow], OutputPreamble]:
    """The ``Adjusted Coordinates`` table of a ``.adj`` or ``.xyz`` file.

    Both files carry the same table, written by the same code, so one reader
    serves both. The corrections are present only when the run asked for them,
    and are ``None`` otherwise rather than zero -- a station that did not move
    and a station whose movement was not reported are different facts.
    """
    lines = _read_lines(path)
    preamble = read_preamble(lines, path=path)
    plan = coordinate_plan(preamble)
    header_index = require_header(lines, plan, what="Adjusted Coordinates")
    # Resolved once, and only when it is actually needed. Under the shipped
    # default the position comes from X, Y and Z, so no angle is read and a
    # ``.xyz`` -- which records no command line at all -- is still read exactly.
    resolved = (
        station_angular_format(preamble, declared=angular_format)
        if target_system(preamble) is CoordinateSystem.GEODETIC
        else AngularFormat.HP
    )

    rows: list[CoordinateRow] = []
    for raw in _station_rows(lines, header_index):
        name, row = _normalise_name(raw, 0, STATION, known)
        if not name:
            continue
        sigmas = tuple(
            _float(plan.value(row, label), what=label, line=row)
            for label in ("SD(e)", "SD(n)", "SD(up)")
        )
        correction: tuple[float, float, float] | None = None
        if preamble.station_corrections:
            correction = tuple(  # type: ignore[assignment]
                _float(plan.value(row, label), what=label, line=row)
                for label in ("Corr(e)", "Corr(n)", "Corr(up)")
            )
        description_start = plan.offsets()[plan.index("Description")][0]
        rows.append(
            CoordinateRow(
                station_id=name,
                position=_coordinate_position(plan, preamble, row, resolved),
                constraint=plan.value(row, "Const"),
                local_sigmas=sigmas,  # type: ignore[arg-type]
                correction=correction,
                description=row[description_start:].strip(),
            )
        )
    return rows, preamble


def read_xyz(
    path: str | Path,
    *,
    known: Iterable[str] | None = None,
    angular_format: AngularFormat | None = None,
) -> list[CoordinateRow]:
    """The adjusted coordinates alone, from a ``.xyz`` file."""
    rows, _ = read_coordinates(path, known=known, angular_format=angular_format)
    return rows


_STATISTIC_LABELS = {
    "Number of unknown parameters": "n_parameters",
    "Number of measurements": "n_observations",
    "Degrees of freedom": "degrees_of_freedom",
    "Chi squared": "chi_squared",
    "Rigorous Sigma Zero": "sigma_zero",
    "Estimated Variance Factor": "sigma_zero",
}

_CHI_SQUARE = re.compile(
    r"^Chi-Square test \(([\d.]+)%\)\s+"
    r"([\d.eE+-]+)\s*<\s*([\d.eE+-]+)\s*<\s*([\d.eE+-]+)"
    r"\s+\*{3}\s*(.+?)\s*\*{3}"
)
_CORRECTION_VECTOR = re.compile(r"^\s+([-\d.eE+]+),\s*([-\d.eE+]+),\s*([-\d.eE+]+)\s+\(e, n, up\)")


def read_statistics(path: str | Path) -> AdjustmentStatistics:
    """The solution summary and iteration record of a ``.adj`` file.

    ``Rigorous Sigma Zero`` is the *variance* factor, not its square root:
    DynAdjust prints chi-squared and degrees of freedom beside it, and the two
    divide to give it. It goes into ``variance_factor_aposteriori`` unchanged.

    ``max_correction`` is the largest absolute *component* of the final
    iteration's correction, not the vector's magnitude, because that is the
    quantity DynAdjust itself compares against ``--iteration-threshold``
    (``dna_adjust::maxCorr_``, from ``compute_maximum_value``).
    """
    lines = _read_lines(path)
    read_preamble(lines, path=path)

    numbers: dict[str, float] = {}
    iterations = 0
    converged = False
    max_correction: float | None = None
    global_test: TestResult | None = None
    seen_solution = False

    for index, line in enumerate(lines):
        label = line[:PREAMBLE_LABEL_WIDTH].strip()
        value = line[PREAMBLE_LABEL_WIDTH:].strip()

        if label == "ITERATION" and value.isdigit():
            iterations = max(iterations, int(value))
        elif label == "SOLUTION":
            seen_solution = True
            converged = value.strip().lower().startswith("converged")
        elif label == "Maximum station correction":
            vector = _CORRECTION_VECTOR.match(lines[index + 1]) if index + 1 < len(lines) else None
            if vector:
                max_correction = max(abs(float(component)) for component in vector.groups())
        elif label in _STATISTIC_LABELS:
            first = value.split()[0] if value.split() else ""
            if first:
                numbers[_STATISTIC_LABELS[label]] = _float(first, what=label, line=line)

        test = _CHI_SQUARE.match(line.strip())
        if test:
            low, statistic, high, verdict = (
                float(test.group(2)),
                float(test.group(3)),
                float(test.group(4)),
                test.group(5),
            )
            global_test = TestResult(
                name="chi_square",
                statistic=statistic,
                critical_low=low,
                critical_high=high,
                confidence=float(test.group(1)) / 100.0,
                passed=verdict.strip().upper().startswith("PASS"),
            )

    if not seen_solution:
        raise DataError(
            "dynadjust_output_has_no_solution",
            path=str(path),
            hint="the file records no SOLUTION line, so the adjustment did not reach one",
        )

    return AdjustmentStatistics(
        n_observations=int(numbers.get("n_observations", 0)),
        n_parameters=int(numbers.get("n_parameters", 0)),
        degrees_of_freedom=int(numbers.get("degrees_of_freedom", 0)),
        variance_factor_aposteriori=numbers.get("sigma_zero"),
        global_test=global_test,
        iterations=iterations,
        converged=converged,
        max_correction=max_correction,
    )


@dataclass(frozen=True)
class AdjustedMeasurement:
    """One row of the ``Adjusted Measurements`` table, as the file states it.

    Deliberately *not* an :class:`~geocomp.core.models.solution.ObservationResult`
    yet: the row carries no observation identifier, only a type letter, the
    stations and -- for a cluster -- which component this row is. Turning that
    into a GeoComp observation id is :func:`match_observations`' job, and keeping
    the two apart is what stops a plausible-looking guess being made here.
    """

    code: str
    stations: tuple[str, ...]
    component: str
    measured: float
    adjusted: float
    correction: float
    measured_sigma: float
    adjusted_sigma: float
    correction_sigma: float
    n_statistic: float | None
    pelzer: float | None
    pre_adjustment_correction: float | None
    outlier: bool
    ignored: bool
    t_statistic: float | None = None
    database_id: str | None = None
    cluster_id: str | None = None

    @property
    def angular(self) -> bool:
        """Is this row's value an angle -- radians rather than metres?

        Answered by the component letter when there is one and by the type
        letter otherwise, exactly as the reader decided it. Every value on this
        record is already in SI, so this says which SI unit, not what conversion
        is still owed.
        """
        return _is_angular(self.code, self.component, _ANGULAR_CODES, line="")


_SPEC_BY_CODE = {
    spec.dynadjust_code: spec for spec in OBSERVATION_TYPES.values() if spec.dynadjust_code
}

#: The type letters whose value is an angle, from the registry rather than a
#: second list here -- adding an observation type stays one registry entry.
_ANGULAR_CODES = frozenset(
    code for code, spec in _SPEC_BY_CODE.items() if spec.units and spec.units[0] is Unit.RADIAN
)


def _is_angular(code: str, component: str, angular_codes: frozenset[str] | set[str], *, line: str) -> bool:
    """Is this row's value an angle?

    The component letter decides when there is one, because a single measurement
    can hold both kinds: a ``Y`` cluster prints ``P``, ``L`` and ``H``, the first
    two angles and the third a height. Only a row with no component falls back to
    the type letter. An unrecognised component raises rather than defaulting --
    a wrong guess here is a factor-of-3600 error that looks like a blunder.
    """
    component = component.strip()
    if not component:
        return code in angular_codes
    if component in _ANGULAR_COMPONENTS:
        return True
    if component in _LINEAR_COMPONENTS:
        return False
    raise DataError(
        "dynadjust_unknown_measurement_component",
        code=code,
        component=component,
        line=line.rstrip()[:120],
        hint="the component letter is not one this parser knows to be angular or linear",
    )


def read_measurements(
    path: str | Path,
    *,
    known: Iterable[str] | None = None,
    angular_format: AngularFormat | None = None,
) -> list[AdjustedMeasurement]:
    """The ``Adjusted Measurements`` table of a ``.adj`` file.

    Present only when the run passed ``--output-adj-msr``; an ``.adj`` without
    it yields an empty list, which is a configuration fact rather than a
    failure (specs/07 section 5 rule 2).
    """
    lines = _read_lines(path)
    preamble = read_preamble(lines, path=path)
    header_index = next(
        (index for index, line in enumerate(lines) if line.startswith("M Station 1")),
        None,
    )
    if header_index is None:
        return []
    plan = measurement_plan(lines[header_index])
    if not plan.matches(lines[header_index]):
        raise DataError(
            "dynadjust_unrecognised_output_layout",
            table="Adjusted Measurements",
            expected=plan.header().rstrip(),
            found=lines[header_index].rstrip(),
        )
    header = plan.header()

    rows = _station_rows(lines, header_index)
    # Resolve the angular format once, and only if some row actually needs it.
    angular_codes = _ANGULAR_CODES
    needs_angles = any(
        _is_angular(plan.value(row, "M"), plan.value(row, "C"), angular_codes, line=row)
        for row in rows
    )
    resolved = (
        measurement_angular_format(preamble, declared=angular_format) if needs_angles else None
    )

    results: list[AdjustedMeasurement] = []
    for raw in rows:
        row = raw
        names: list[str] = []
        for position in range(3):
            name, row = _normalise_name(row, PAD2 + position * STATION, STATION, known)
            names.append(name)
        code = plan.value(row, "M")
        if not code:
            continue

        component = plan.value(row, "C")
        angular = _is_angular(code, component, angular_codes, line=row)

        def read(label: str, *, line: str = row, angular: bool = angular) -> float:
            text = plan.value(line, label)
            if not angular:
                return _float(text, what=label, line=line)
            if label in _ANGLE_COLUMNS:
                return read_angle(text, resolved, line=line)  # type: ignore[arg-type]
            if label in _SECONDS_COLUMNS:
                return seconds_to_radians(_float(text, what=label, line=line))
            return _float(text, what=label, line=line)

        def read_optional(label: str, *, line: str = row, angular: bool = angular) -> float | None:
            text = plan.value(line, label)
            if not text:
                return None
            return read(label, line=line, angular=angular)

        results.append(
            AdjustedMeasurement(
                code=code,
                stations=tuple(name for name in names if name),
                component=component,
                measured=read("Measured"),
                adjusted=read("Adjusted"),
                correction=read("Correction"),
                measured_sigma=read("Meas. SD"),
                adjusted_sigma=read("Adj. SD"),
                correction_sigma=read("Corr. SD"),
                # Dimensionless, whatever the row's type: read plainly.
                n_statistic=read_optional("N-stat", angular=False),
                pelzer=read_optional("Pelzer Rel", angular=False),
                pre_adjustment_correction=read_optional("Pre Adj Corr"),
                outlier=plan.value(row, "Outlier?").strip() == "*",
                ignored=plan.value(row, "*").strip() == "*",
                t_statistic=read_optional("T-stat") if "T-stat" in header else None,
                database_id=(plan.value(row, "Meas. ID") or None) if "Meas. ID" in header else None,
                cluster_id=(plan.value(row, "Clust. ID") or None) if "Clust. ID" in header else None,
            )
        )
    return results


@dataclass(frozen=True)
class StationUncertainty:
    """One station's block of the ``.apu`` file.

    ``covariance`` is the station's own 3x3 matrix, in the frame
    ``variance_units`` names. ``cross`` holds the covariance with each other
    station, present only under ``--output-all-covariances``; the key is the
    other station's name and the matrix is *not* symmetric, being a block of the
    full matrix rather than a variance of anything.
    """

    station_id: str
    #: As the ``.apu`` states them, in radians -- or ``None`` when the file did
    #: not say whether they were HP or decimal degrees and the caller did not
    #: either. Carried because the covariance is cartesian while the ellipse and
    #: the ``.adj``'s standard deviations are local, and rotating between the two
    #: needs exactly these two angles. They are never guessed: an ``.apu``
    #: records no command line, so without a declaration the two angles are
    #: absent and everything else in the file is still returned.
    latitude: float | None
    longitude: float | None
    horizontal_uncertainty: float
    vertical_uncertainty: float
    ellipse: ErrorEllipse
    covariance: Covariance
    cross: dict[str, np.ndarray] = field(default_factory=dict)


def _triple(line: str, plan: ColumnPlan, labels: Sequence[str]) -> list[float]:
    return [_float(plan.value(line, label), what=label, line=line) for label in labels]


def read_apu(
    path: str | Path,
    *,
    known: Iterable[str] | None = None,
    angular_format: AngularFormat | None = None,
) -> tuple[list[StationUncertainty], OutputPreamble]:
    """Positional uncertainty and variances, from a ``.apu`` file.

    Each station occupies three lines: its own variance matrix is written as an
    **upper triangle** spread over them, with the second and third indented past
    the columns the first used. Under ``--output-all-covariances`` a further
    three-line block follows per other station, each a **full** 3x3 rather than
    a triangle -- so the two shapes must not be read by the same rule, and
    aren't.

    The ellipse orientation is in HP notation (``RadtoDms(azimuth)`` in
    ``PrintPosUncertainty``), so ``79.4724`` is 79 deg 47 min 24 sec.
    """
    lines = _read_lines(path)
    preamble = read_preamble(lines, path=path)
    plan = uncertainty_plan(preamble)
    header_index = require_header(lines, plan, what="Positional uncertainty")
    try:
        resolved: AngularFormat | None = station_angular_format(preamble, declared=angular_format)
    except DataError:
        resolved = None

    suffixes = ("e", "n", "up") if preamble.variance_units == "ENU" else ("X", "Y", "Z")
    axes = tuple(suffix.lower() for suffix in suffixes)
    variance_labels = [f"Variance({suffix})" for suffix in suffixes]
    # The continuation lines are indented past the columns the first row used,
    # so the second starts one variance column in and the third two.
    first_variance = plan.offsets()[plan.index(variance_labels[0])][0]

    def continuation(line: str, skipped: int) -> list[float]:
        start = first_variance + skipped * MSR
        return [
            _float(line[start + step * MSR : start + (step + 1) * MSR].strip(), what="variance", line=line)
            for step in range(3 - skipped)
        ]

    rows = [line for line in lines[header_index + 2 :] if line.strip()]
    stations: list[StationUncertainty] = []
    index = 0
    current: StationUncertainty | None = None

    while index < len(rows):
        raw = rows[index]
        name, row = _normalise_name(raw, 0, STATION, known)
        if not name:
            raise DataError("dynadjust_apu_row_without_a_station", line=raw.rstrip()[:120])
        has_position = bool(plan.value(row, "Hz PosU"))

        if has_position:
            upper = _triple(row, plan, variance_labels)
            upper += continuation(rows[index + 1], 1)
            upper += continuation(rows[index + 2], 2)
            matrix = np.array(
                [
                    [upper[0], upper[1], upper[2]],
                    [upper[1], upper[3], upper[4]],
                    [upper[2], upper[4], upper[5]],
                ],
                dtype=float,
            )
            current = StationUncertainty(
                station_id=name,
                latitude=(
                    read_angle(plan.value(row, "Latitude"), resolved, line=row)
                    if resolved is not None
                    else None
                ),
                longitude=(
                    read_angle(plan.value(row, "Longitude"), resolved, line=row)
                    if resolved is not None
                    else None
                ),
                horizontal_uncertainty=_float(plan.value(row, "Hz PosU"), what="Hz PosU", line=row),
                vertical_uncertainty=_float(plan.value(row, "Vt PosU"), what="Vt PosU", line=row),
                ellipse=ErrorEllipse(
                    semi_major=_float(plan.value(row, "Semi-major"), what="Semi-major", line=row),
                    semi_minor=_float(plan.value(row, "Semi-minor"), what="Semi-minor", line=row),
                    # Always HP, whatever --angular-stn-type says: the
                    # orientation is written as RadtoDms(azimuth) with no branch
                    # on that option (``PrintPosUncertainty``).
                    orientation=hp_to_radians(
                        _float(plan.value(row, "Orientation"), what="Orientation", line=row)
                    ),
                    confidence=preamble.ellipse_confidence,
                ),
                covariance=Covariance(
                    matrix=matrix,
                    # The same ``station.component`` labelling the in-house core
                    # uses, so a block from either engine reads the same way.
                    labels=tuple(f"{name}.{axis}" for axis in axes),
                    units=(Unit.METRE, Unit.METRE, Unit.METRE),
                ),
            )
            stations.append(current)
        else:
            if current is None:
                raise DataError("dynadjust_apu_covariance_before_any_station", line=raw.rstrip()[:120])
            block = np.array(
                [
                    _triple(row, plan, variance_labels),
                    continuation(rows[index + 1], 0),
                    continuation(rows[index + 2], 0),
                ],
                dtype=float,
            )
            current.cross[name] = block
        index += 3

    return stations, preamble


@dataclass(frozen=True)
class StationCorrection:
    """One row of the ``.cor`` file: how far a station moved, and which way."""

    station_id: str
    azimuth: float
    vertical_angle: float
    slope_distance: float
    horizontal_distance: float
    east: float
    north: float
    up: float


_DMS_FIELD = re.compile(r"^(-?)\s*(\d+)\s+(\d+)\s+([\d.]+)$")


def _separated_dms(text: str, *, line: str) -> float:
    """``"84 42 21"`` to radians.

    The ``.cor`` file writes angles as separated fields
    (``FormatDmsString(..., 4, true, false)``), not in the HP notation the
    ``.adj`` uses for the same kind of quantity -- so a reader that assumed one
    format for both would silently divide by 100 in one of the two files.
    """
    match = _DMS_FIELD.match(text.strip())
    if not match:
        raise DataError("dynadjust_cor_angle_unreadable", received=text, line=line.rstrip()[:120])
    sign, degrees, minutes, seconds = match.groups()
    magnitude = float(degrees) + float(minutes) / 60.0 + float(seconds) / 3600.0
    return math.radians(-magnitude if sign == "-" else magnitude)


def read_cor(path: str | Path, *, known: Iterable[str] | None = None) -> list[StationCorrection]:
    """Corrections to the initial coordinates, from a ``.cor`` file.

    **Not every station need appear.** ``PrintCorStation`` returns early for a
    station whose correction is under ``--hz-corr-threshold`` or
    ``--vt-corr-threshold``, so a station missing here moved less than the
    caller asked to hear about -- it is not a station missing from the
    adjustment.
    """
    lines = _read_lines(path)
    read_preamble(lines, path=path)
    header_index = require_header(lines, CORRECTION_PLAN, what="Corrections to stations")

    corrections: list[StationCorrection] = []
    for raw in _station_rows(lines, header_index):
        name, row = _normalise_name(raw, 0, STATION, known)
        if not name:
            continue
        corrections.append(
            StationCorrection(
                station_id=name,
                azimuth=_separated_dms(CORRECTION_PLAN.value(row, "Azimuth"), line=row),
                vertical_angle=_separated_dms(CORRECTION_PLAN.value(row, "V. Angle"), line=row),
                slope_distance=_float(
                    CORRECTION_PLAN.value(row, "S. Distance"), what="S. Distance", line=row
                ),
                horizontal_distance=_float(
                    CORRECTION_PLAN.value(row, "H. Distance"), what="H. Distance", line=row
                ),
                east=_float(CORRECTION_PLAN.value(row, "east"), what="east", line=row),
                north=_float(CORRECTION_PLAN.value(row, "north"), what="north", line=row),
                up=_float(CORRECTION_PLAN.value(row, "up"), what="up", line=row),
            )
        )
    return corrections


def printed_rows(network) -> list[tuple[str, str, tuple[str, ...]]]:
    """``(observation id, the code DynAdjust prints, stations)``, one per row.

    Mirrors ``write_measurement_file``: clusters first, in the network's cluster
    order, then whatever observations were not in one -- because that is the
    order GeoComp wrote the file in, and DynAdjust preserves the input order by
    default (``--sort-adj-msr-field 0``).

    The code is the **cluster's**, not the member's, which is the part that
    cannot be read off the observation alone: a cluster of several baselines is
    printed as ``X`` and a single one as ``G``, though both hold the same type
    of observation. Keeping this rule in step with the writer's is what makes
    the two round-trip; the row-by-row check in :func:`match_observations` is
    what catches it when they drift apart.
    """
    rows: list[tuple[str, str, tuple[str, ...]]] = []
    seen: set[str] = set()

    def emit(observation, code: str) -> None:
        spec = OBSERVATION_TYPES[observation.type]
        for _ in spec.components:
            rows.append((observation.id, code, observation.stations))

    for cluster in network.clusters.values():
        members = [
            network.observations[identifier]
            for identifier in cluster.observation_ids
            if identifier in network.observations
        ]
        if not members:
            continue
        code = _cluster_code(members)
        for member in members:
            seen.add(member.id)
            emit(member, code or _own_code(member))

    for observation in network.observations.values():
        if observation.id in seen:
            continue
        emit(observation, _own_code(observation))
    return rows


def _own_code(observation) -> str:
    spec = OBSERVATION_TYPES[observation.type]
    if not spec.dynadjust_code:
        raise DataError(
            "dynadjust_observation_has_no_code",
            observation=observation.id,
            type=observation.type.value,
            hint="DynAdjust has no measurement type for this observation",
        )
    return spec.dynadjust_code


def _cluster_code(members: list) -> str | None:
    """The type letter a cluster of *members* is written under, or ``None``.

    ``None`` for a cluster whose members are written individually, which is what
    ``_write_cluster`` falls through to.
    """
    kind = members[0].type
    if kind is ObservationType.GNSS_BASELINE:
        return "G" if len(members) == 1 else "X"
    if kind is ObservationType.GNSS_POINT:
        return "Y"
    if kind is ObservationType.DIRECTION:
        return "D"
    return None


def match_observations(
    rows: Sequence[AdjustedMeasurement],
    network,
) -> list[ObservationResult]:
    """Map measurement rows back onto the network's observation identifiers.

    DynAdjust's rows carry no identifier, so the only thing tying them to
    GeoComp's observations is the order GeoComp wrote them in. That order is
    *used* but never *trusted*: every row's type letter and stations are checked
    against the observation it lands on, and a disagreement raises rather than
    producing results attributed to the wrong observation.

    A multi-component observation -- a GNSS baseline, a Y cluster -- occupies one
    row per component, all mapping to the same observation id. The residuals stay
    per component, distinguished by the row's ``C`` letter, because that is what
    DynAdjust reports and combining them into one figure would be a statistic
    nobody computed.
    """
    expected = printed_rows(network)
    if len(rows) != len(expected):
        raise DataError(
            "dynadjust_measurement_count_mismatch",
            received=len(rows),
            expected=len(expected),
            hint=(
                "the adjusted-measurement table has a different number of rows than "
                "the network has observation components; the two cannot be matched "
                "by order"
            ),
        )

    results: list[ObservationResult] = []
    for row, (identifier, code, stations) in zip(rows, expected, strict=True):
        if row.code != code:
            raise DataError(
                "dynadjust_measurement_type_mismatch",
                observation=identifier,
                received=row.code,
                expected=code,
                hint="the rows are not in the order the network was written in",
            )
        if row.stations and tuple(row.stations) != tuple(stations)[: len(row.stations)]:
            raise DataError(
                "dynadjust_measurement_station_mismatch",
                observation=identifier,
                received=list(row.stations),
                expected=list(stations),
            )
        results.append(
            ObservationResult(
                observation_id=identifier,
                residual=row.correction,
                standardised_residual=row.n_statistic,
                adjusted_value=row.adjusted,
            )
        )
    return results


def read_adj(
    path: str | Path,
    *,
    known: Iterable[str] | None = None,
    angular_format: AngularFormat | None = None,
) -> tuple[list[CoordinateRow], list[AdjustedMeasurement], AdjustmentStatistics, OutputPreamble]:
    """Everything a ``.adj`` file holds, read in one pass over the file.

    Returned as its four parts rather than as a
    :class:`~geocomp.core.models.solution.Solution`: assembling one needs the
    ``.apu`` for the covariances and the network for the observation
    identifiers, and neither belongs to this file.
    """
    lines = _read_lines(path)
    preamble = read_preamble(lines, path=path)
    rows, _ = read_coordinates(path, known=known, angular_format=angular_format)
    measurements = read_measurements(path, known=known, angular_format=angular_format)
    statistics = read_statistics(path)
    return rows, measurements, statistics, preamble
