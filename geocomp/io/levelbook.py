# SPDX-License-Identifier: GPL-2.0-or-later
"""Reading a levelling field book (FR-160, FR-166, FR-095).

``specs/10-module-levelling.md`` section 6 and
``specs/17-persistence-and-interoperability.md`` section 5.1.

*Field-book layouts vary widely.* Two are supported, and which one a file is in
is worked out from the columns the mapping names rather than asked for:

* **One row per setup** -- backsight and foresight side by side. The compact
  layout, and the one a spreadsheet naturally produces.
* **One row per reading**, each carrying a setup identifier. The layout an
  instrument's own export uses, and the only one that can express a setup with
  several foresights (extreme sights, FR-502) at all.

Either may carry **three wires** instead of a single reading. Three wires give
the sight distance for free by stadia -- which is what makes the balance check of
``specs/10`` section 2.1 possible on a file that never recorded a distance -- and
a half-sum check that catches a misread wire on the spot.

**Every record is reported and none aborts the import** (FR-166), exactly as in
:mod:`geocomp.io.fieldbook`: a field book with six bad rows needs one run.

**Uncertainties are attached here, at the boundary**, through
:func:`~geocomp.core.instruments.stochastic.resolve_sigma`, so nothing without
one can reach the domain model (FR-200). Where a file states no sigma and no
level profile is supplied, the import refuses rather than inventing one, and the
refusal names the three ways to fix it.
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from geocomp.core.errors import ValidationError
from geocomp.core.findings import Finding, Severity
from geocomp.core.instruments.level import LevelProfile
from geocomp.core.instruments.profiles import ProfileLibrary
from geocomp.core.instruments.stochastic import (
    SIGHT_DISTANCE,
    STAFF_READING,
    StochasticDefaults,
    resolve_sigma,
)
from geocomp.core.techniques.levelling.line import LevellingLine
from geocomp.core.techniques.levelling.readings import (
    LevelSetup,
    StaffReading,
    ThreeWireReading,
)
from geocomp.core.uncertainty import Quantity, Strategy
from geocomp.core.units import Unit
from geocomp.io.mapping import ColumnMapping, parse_number

__all__ = [
    "LEVEL_FIELDS",
    "Layout",
    "LevelBookRecord",
    "LevelImportResult",
    "LevelMapping",
    "read_level_book",
    "read_level_book_csv",
]

#: The logical fields a levelling field book can supply. Ids are stable: a saved
#: mapping stores them, so renaming one breaks every mapping a user has kept.
LEVEL_FIELDS: tuple[str, ...] = (
    # Either layout
    "line",
    "setup",
    "level_id",
    "note",
    # Row-per-reading layout
    "station",
    "sight",
    "reading",
    "upper",
    "middle",
    "lower",
    "distance",
    # Row-per-setup layout
    "backsight_station",
    "foresight_station",
    "backsight_reading",
    "foresight_reading",
    "backsight_distance",
    "foresight_distance",
    "backsight_upper",
    "backsight_middle",
    "backsight_lower",
    "foresight_upper",
    "foresight_middle",
    "foresight_lower",
)

_READING_LAYOUT_CORE = frozenset({"station", "sight"})
_SETUP_LAYOUT_CORE = frozenset({"backsight_station", "foresight_station"})

#: Tokens meaning each kind of sight, defaulted to English words that a
#: Portuguese or Spanish field book will not use -- which is why they are
#: configurable and not hard-coded.
DEFAULT_SIGHT_VALUES: dict[str, str] = {
    "BS": "backsight",
    "FS": "foresight",
    "IS": "intermediate",
}


class Layout(Enum):
    """Which of the two shapes a file is in."""

    #: One row per reading, each naming its setup.
    READING = "reading"
    #: One row per setup, backsight and foresight side by side.
    SETUP = "setup"


@dataclass(frozen=True)
class LevelMapping:
    """A named, reusable description of one levelling source layout (FR-160).

    Attributes:
        columns: Reuses :class:`~geocomp.io.mapping.ColumnMapping`, but against
            :data:`LEVEL_FIELDS` -- the same mechanics, a different vocabulary.
            A levelling book has no faces and no angles, and offering a
            total-station field list would be offering nonsense.
        sight_values: Which source token means which kind of sight. Only the
            row-per-reading layout uses it.
        stadia_factor: The instrument's stadia constant, when three wires are
            read and no level profile is supplied. The profile wins when both
            are available -- an instrument constant belongs to the instrument.
    """

    name: str
    columns: tuple[ColumnMapping, ...] = ()
    decimal_separator: str = "auto"
    skip_rows: int = 0
    sight_values: dict[str, str] = field(
        default_factory=lambda: dict(DEFAULT_SIGHT_VALUES)
    )
    stadia_factor: float = 100.0
    description: str = ""

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValidationError(
                "mapping_without_name",
                expected="a name; a mapping exists to be saved and reused by it",
            )
        if self.decimal_separator not in (".", ",", "auto"):
            raise ValidationError(
                "unknown_decimal_separator",
                received=self.decimal_separator,
                expected="'.', ',' or 'auto'",
            )
        if self.skip_rows < 0:
            raise ValidationError(
                "negative_skip_rows", received=self.skip_rows, expected="zero or more"
            )
        unknown = sorted(
            mapping.field for mapping in self.columns if mapping.field not in LEVEL_FIELDS
        )
        if unknown:
            raise ValidationError(
                "unknown_level_mapping_field",
                received=unknown,
                expected=f"one of: {', '.join(LEVEL_FIELDS)}",
            )
        seen = [mapping.field for mapping in self.columns]
        duplicates = sorted({name for name in seen if seen.count(name) > 1})
        if duplicates:
            raise ValidationError(
                "duplicate_mapped_field",
                received=duplicates,
                expected="each GeoComp field mapped at most once",
            )
        if self.stadia_factor <= 0.0:
            raise ValidationError(
                "stadia_factor_not_positive",
                received=self.stadia_factor,
                expected="a positive stadia multiplication constant, usually 100",
            )

    # -- lookup ----------------------------------------------------------

    def for_field(self, name: str) -> ColumnMapping | None:
        for mapping in self.columns:
            if mapping.field == name:
                return mapping
        return None

    @property
    def mapped_fields(self) -> frozenset[str]:
        return frozenset(mapping.field for mapping in self.columns)

    @property
    def source_columns(self) -> frozenset[str]:
        return frozenset(m.column for m in self.columns if m.column is not None)

    @property
    def layout(self) -> Layout:
        """Which layout the mapped columns describe.

        Decided from the columns rather than declared, because a mapping that
        says "row per setup" while naming a ``sight`` column is a mapping that
        will produce wrong data quietly. Naming columns of both layouts is
        refused by name.
        """
        mapped = self.mapped_fields
        looks_like_readings = bool(mapped & _READING_LAYOUT_CORE)
        looks_like_setups = bool(mapped & _SETUP_LAYOUT_CORE)

        if looks_like_readings and looks_like_setups:
            raise ValidationError(
                "ambiguous_level_layout",
                mapping=self.name,
                received=sorted(mapped & (_READING_LAYOUT_CORE | _SETUP_LAYOUT_CORE)),
                expected=(
                    "columns of one layout: either station and sight, one row per "
                    "reading, or backsight_station and foresight_station, one row per "
                    "setup"
                ),
            )
        if looks_like_readings:
            return Layout.READING
        if looks_like_setups:
            return Layout.SETUP
        raise ValidationError(
            "unrecognised_level_layout",
            mapping=self.name,
            received=sorted(mapped),
            expected=(
                "station and sight for a row-per-reading book, or backsight_station "
                "and foresight_station for a row-per-setup one"
            ),
        )

    def missing_required(self) -> tuple[str, ...]:
        """Fields the layout needs and the mapping does not supply.

        A reading counts as supplied by a mapped ``middle`` wire, since three
        wires are a reading and then some.
        """
        mapped = set(self.mapped_fields)
        try:
            layout = self.layout
        except ValidationError:
            return ()

        if layout is Layout.READING:
            required = {"setup", "station", "sight"}
            if "reading" not in mapped and "middle" not in mapped:
                required.add("reading")
            return tuple(sorted(required - mapped))

        required = {"backsight_station", "foresight_station"}
        for side in ("backsight", "foresight"):
            if f"{side}_reading" not in mapped and f"{side}_middle" not in mapped:
                required.add(f"{side}_reading")
        return tuple(sorted(required - mapped))

    def unrecognised(self, header: list[str]) -> tuple[str, ...]:
        return tuple(
            column for column in header if column and column not in self.source_columns
        )

    def parse_number(self, text: str, *, unit: str = "") -> float:
        return parse_number(text, self.decimal_separator, unit=unit)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "name": self.name,
            "columns": [mapping.to_dict() for mapping in self.columns],
            "decimal_separator": self.decimal_separator,
            "sight_values": dict(self.sight_values),
            "stadia_factor": self.stadia_factor,
        }
        if self.skip_rows:
            payload["skip_rows"] = self.skip_rows
        if self.description:
            payload["description"] = self.description
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> LevelMapping:
        return cls(
            name=payload["name"],
            columns=tuple(ColumnMapping.from_dict(c) for c in payload.get("columns", ())),
            decimal_separator=payload.get("decimal_separator", "auto"),
            skip_rows=int(payload.get("skip_rows", 0)),
            sight_values=dict(payload.get("sight_values", DEFAULT_SIGHT_VALUES)),
            stadia_factor=float(payload.get("stadia_factor", 100.0)),
            description=payload.get("description", ""),
        )


@dataclass(frozen=True)
class LevelBookRecord:
    """One source row, parsed but not yet assembled into setups.

    The intermediate a preview dialog needs: the row number, what was
    understood, and what went wrong, before anything is committed.
    """

    row: int
    setup: str
    station: str
    sight: str
    reading: float
    distance: float | None = None
    #: The distance exactly as written in the file. Kept because the number of
    #: digits an observer chose is real information about how well they knew it
    #: -- see :func:`_distance_quantity`.
    distance_text: str = ""
    three_wire: tuple[float, float, float] | None = None
    line: str = ""
    level_id: str = ""
    note: str = ""


@dataclass(frozen=True)
class LevelImportResult:
    """Everything a levelling import produced, including what it could not use."""

    setups: tuple[LevelSetup, ...]
    lines: tuple[LevellingLine, ...]
    records: tuple[LevelBookRecord, ...]
    findings: tuple[Finding, ...]
    unrecognised_columns: tuple[str, ...]
    row_count: int

    @property
    def rejected_rows(self) -> tuple[int, ...]:
        return tuple(
            sorted(
                {
                    int(finding.value)
                    for finding in self.findings
                    if finding.value is not None and finding.is_blocking
                }
            )
        )

    @property
    def is_clean(self) -> bool:
        return not any(finding.is_blocking for finding in self.findings)


def read_level_book_csv(
    path: str | Path,
    mapping: LevelMapping,
    *,
    library: ProfileLibrary | None = None,
    level: LevelProfile | None = None,
    defaults: StochasticDefaults | None = None,
    encoding: str = "utf-8-sig",
) -> LevelImportResult:
    """Read a CSV levelling book. See :func:`read_level_book`."""
    source = Path(path)
    if not source.is_file():
        raise ValidationError(
            "field_book_not_found",
            received=str(source),
            expected="a readable CSV file",
        )
    with open(source, encoding=encoding, newline="") as handle:
        rows = list(csv.reader(handle))
    return read_level_book(rows, mapping, library=library, level=level, defaults=defaults)


def read_level_book(
    rows: list[list[str]],
    mapping: LevelMapping,
    *,
    library: ProfileLibrary | None = None,
    level: LevelProfile | None = None,
    defaults: StochasticDefaults | None = None,
) -> LevelImportResult:
    """Read a levelling field book into setups and lines.

    Args:
        rows: The whole file, header included.
        mapping: The layout description.
        library: Resolves ``level_id`` per row, for a book that changed
            instruments. A line that changes instrument mid-way is refused when
            it is reduced, not here -- the import's job is to report the file
            faithfully.
        level: The instrument, when the book names none.
        defaults: Global Settings type defaults, the last resort before refusal.

    Returns:
        A :class:`LevelImportResult`. **Nothing raises for a bad row**; every
        problem is a finding naming its row number (FR-166).
    """
    missing = mapping.missing_required()
    if missing:
        raise ValidationError(
            "level_mapping_incomplete",
            mapping=mapping.name,
            received=sorted(mapping.mapped_fields),
            expected=f"these fields as well: {', '.join(missing)}",
        )

    layout = mapping.layout
    body = rows[mapping.skip_rows :]
    if not body:
        raise ValidationError(
            "level_book_empty",
            expected="a header row and at least one data row",
        )

    header = [cell.strip() for cell in body[0]]
    findings: list[Finding] = []
    records: list[LevelBookRecord] = []

    for offset, raw in enumerate(body[1:], start=mapping.skip_rows + 2):
        if not any(cell.strip() for cell in raw):
            continue
        row = dict(zip(header, [cell.strip() for cell in raw], strict=False))
        try:
            records.extend(_parse_row(offset, row, mapping, layout, library, level, defaults))
        except _RowError as error:
            findings.append(
                Finding(
                    code=error.code,
                    severity=Severity.BLOCKING,
                    message=f"row {offset}: {error}",
                    value=float(offset),
                )
            )

    setups, lines, assembly_findings = _assemble(records, mapping, library, level, defaults)
    findings.extend(assembly_findings)

    return LevelImportResult(
        setups=tuple(setups),
        lines=tuple(lines),
        records=tuple(records),
        findings=tuple(findings),
        unrecognised_columns=mapping.unrecognised(header),
        row_count=max(len(body) - 1, 0),
    )


class _RowError(Exception):
    """One row could not be understood. Carries a code for the finding."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _value(row: dict[str, str], mapping: LevelMapping, name: str) -> str | None:
    column = mapping.for_field(name)
    if column is None:
        return None
    if column.column is None:
        return column.constant
    text = row.get(column.column)
    return text if text else None


def _number(
    row: dict[str, str], mapping: LevelMapping, name: str, *, required: bool = False
) -> float | None:
    text = _value(row, mapping, name)
    if text is None:
        if required:
            raise _RowError("level_missing_value", f"{name} is empty")
        return None
    column = mapping.for_field(name)
    try:
        return mapping.parse_number(text, unit=column.unit if column else "")
    except ValueError as error:
        raise _RowError(
            "level_unreadable_number", f"{name} is not a number: {text!r} ({error})"
        ) from None


def _three_wire(
    row: dict[str, str], mapping: LevelMapping, prefix: str
) -> tuple[float, float, float] | None:
    """Upper, middle and lower, or ``None`` when the layout has no wires."""
    names = [f"{prefix}{part}" for part in ("upper", "middle", "lower")]
    if not all(mapping.for_field(name) for name in names):
        return None
    values = [_number(row, mapping, name, required=True) for name in names]
    return (float(values[0]), float(values[1]), float(values[2]))


def _parse_row(
    number: int,
    row: dict[str, str],
    mapping: LevelMapping,
    layout: Layout,
    library: ProfileLibrary | None,
    level: LevelProfile | None,
    defaults: StochasticDefaults | None,
) -> list[LevelBookRecord]:
    line = _value(row, mapping, "line") or ""
    level_id = _value(row, mapping, "level_id") or ""
    note = _value(row, mapping, "note") or ""

    if layout is Layout.READING:
        setup = _value(row, mapping, "setup")
        station = _value(row, mapping, "station")
        if not setup or not station:
            raise _RowError("level_missing_value", "setup and station are both required")
        token = _value(row, mapping, "sight") or ""
        sight = mapping.sight_values.get(token, mapping.sight_values.get(token.upper()))
        if sight is None:
            raise _RowError(
                "level_unknown_sight",
                f"{token!r} is not a kind of sight; expected one of "
                f"{', '.join(sorted(mapping.sight_values))}",
            )
        wires = _three_wire(row, mapping, "")
        reading = (
            sum(wires) / 3.0 if wires else _number(row, mapping, "reading", required=True)
        )
        return [
            LevelBookRecord(
                row=number,
                setup=setup,
                station=station,
                sight=sight,
                reading=float(reading),
                distance=_number(row, mapping, "distance"),
                distance_text=_value(row, mapping, "distance") or "",
                three_wire=wires,
                line=line,
                level_id=level_id,
                note=note,
            )
        ]

    backsight_station = _value(row, mapping, "backsight_station")
    foresight_station = _value(row, mapping, "foresight_station")
    if not backsight_station or not foresight_station:
        raise _RowError(
            "level_missing_value", "backsight_station and foresight_station are required"
        )
    setup = _value(row, mapping, "setup") or f"setup-{number}"

    out: list[LevelBookRecord] = []
    for side, station in (
        ("backsight", backsight_station),
        ("foresight", foresight_station),
    ):
        wires = _three_wire(row, mapping, f"{side}_")
        reading = (
            sum(wires) / 3.0
            if wires
            else _number(row, mapping, f"{side}_reading", required=True)
        )
        out.append(
            LevelBookRecord(
                row=number,
                setup=setup,
                station=station,
                sight=side,
                reading=float(reading),
                distance=_number(row, mapping, f"{side}_distance"),
                distance_text=_value(row, mapping, f"{side}_distance") or "",
                three_wire=wires,
                line=line,
                level_id=level_id,
                note=note,
            )
        )
    return out


def _assemble(
    records: list[LevelBookRecord],
    mapping: LevelMapping,
    library: ProfileLibrary | None,
    level: LevelProfile | None,
    defaults: StochasticDefaults | None,
) -> tuple[list[LevelSetup], list[LevellingLine], list[Finding]]:
    """Group records into setups, and setups into lines."""
    findings: list[Finding] = []
    setups: list[LevelSetup] = []
    order: list[str] = []
    grouped: dict[str, list[LevelBookRecord]] = {}

    for record in records:
        if record.setup not in grouped:
            grouped[record.setup] = []
            order.append(record.setup)
        grouped[record.setup].append(record)

    line_of: dict[str, str] = {}
    for setup_id in order:
        members = grouped[setup_id]
        backsights = [r for r in members if r.sight == "backsight"]
        foresights = [r for r in members if r.sight in ("foresight", "intermediate")]

        if len(backsights) != 1 or not foresights:
            findings.append(
                Finding(
                    code="level_setup_malformed",
                    severity=Severity.BLOCKING,
                    message=(
                        f"setup {setup_id} has {len(backsights)} backsight(s) and "
                        f"{len(foresights)} foresight(s); it needs exactly one "
                        "backsight and at least one foresight"
                    ),
                    value=float(members[0].row),
                )
            )
            continue

        instrument = _resolve_level(members[0].level_id, library, level)
        try:
            setups.append(
                LevelSetup(
                    id=setup_id,
                    backsight=_reading(backsights[0], mapping, instrument, defaults),
                    foresights=tuple(
                        _reading(record, mapping, instrument, defaults)
                        for record in foresights
                    ),
                    level_id=instrument.id if instrument else (members[0].level_id or None),
                )
            )
        except ValidationError as error:
            findings.append(
                Finding(
                    code=error.code.split(".")[-1],
                    severity=Severity.BLOCKING,
                    message=f"setup {setup_id}: {error}",
                    value=float(members[0].row),
                )
            )
            continue
        line_of[setup_id] = members[0].line

        for record in members:
            if record.three_wire is None:
                continue
            wires = _wire_quantities(record, instrument, defaults)
            problem = wires.check(
                _half_sum_tolerance(instrument), label=f"{record.station} in setup {setup_id}"
            )
            if problem is not None:
                findings.append(problem)

    lines = _lines(setups, line_of, findings)
    return setups, lines, findings


def _lines(
    setups: list[LevelSetup], line_of: dict[str, str], findings: list[Finding]
) -> list[LevellingLine]:
    """Group setups into lines, in source order.

    A book that names no line gives one line holding every setup, which is the
    common case and the right default. A discontinuity is a finding rather than
    a refusal: the setups are still worth having, and the user is better told
    which two do not join than handed nothing.
    """
    grouped: dict[str, list[LevelSetup]] = {}
    order: list[str] = []
    for setup in setups:
        name = line_of.get(setup.id, "") or "line"
        if name not in grouped:
            grouped[name] = []
            order.append(name)
        grouped[name].append(setup)

    lines: list[LevellingLine] = []
    for name in order:
        try:
            lines.append(LevellingLine(id=name, setups=tuple(grouped[name])))
        except ValidationError as error:
            findings.append(
                Finding(
                    code=error.code.split(".")[-1],
                    severity=Severity.BLOCKING,
                    message=f"line {name}: {error}",
                )
            )
    return lines


def _resolve_level(
    level_id: str, library: ProfileLibrary | None, level: LevelProfile | None
) -> LevelProfile | None:
    if level_id and library is not None:
        return library.level(level_id)
    if level is not None:
        return level
    if library is not None and library.default_level:
        return library.level(None)
    return None


def _half_sum_tolerance(level: LevelProfile | None) -> float:
    """When to call a half-sum residual a misread wire.

    Three sigma of the residual's own distribution, which is
    ``sqrt(1.5) * sigma`` for three readings of equal precision. Derived rather
    than picked, so it tightens automatically with a better instrument. Falls
    back to two millimetres when no reading sigma is known -- generous, and it
    still catches the failure it is for, which is a wire read a whole
    centimetre wrong.
    """
    sigma = level.reading_sigma if level is not None else None
    if sigma is None:
        return 0.002
    return 3.0 * (1.5**0.5) * sigma


def _wire_quantities(
    record: LevelBookRecord,
    level: LevelProfile | None,
    defaults: StochasticDefaults | None,
) -> ThreeWireReading:
    upper, middle, lower = record.three_wire  # type: ignore[misc]
    return ThreeWireReading(
        upper=_staff_quantity(upper, record, level, defaults),
        middle=_staff_quantity(middle, record, level, defaults),
        lower=_staff_quantity(lower, record, level, defaults),
    )


def _staff_quantity(
    value: float,
    record: LevelBookRecord,
    level: LevelProfile | None,
    defaults: StochasticDefaults | None,
):
    quantity, _ = resolve_sigma(
        STAFF_READING,
        value,
        level=level,
        defaults=defaults,
        observation_id=f"row {record.row} ({record.station})",
    )
    return quantity


def _reading(
    record: LevelBookRecord,
    mapping: LevelMapping,
    level: LevelProfile | None,
    defaults: StochasticDefaults | None,
) -> StaffReading:
    """One record as a :class:`StaffReading`, with its uncertainty attached."""
    if record.three_wire is not None:
        wires = _wire_quantities(record, level, defaults)
        factor = level.stadia_factor if level is not None else mapping.stadia_factor
        sigma = level.stadia_sigma if level is not None else None
        return StaffReading(
            station=record.station,
            reading=wires.mean(),
            distance=wires.stadia_distance(factor, sigma),
            three_wire=wires,
            meta={"row": record.row, "note": record.note} if record.note else {"row": record.row},
        )

    reading = _staff_quantity(record.reading, record, level, defaults)
    distance = (
        _distance_quantity(record, level, defaults) if record.distance is not None else None
    )

    return StaffReading(
        station=record.station,
        reading=reading,
        distance=distance,
        meta={"row": record.row, "note": record.note} if record.note else {"row": record.row},
    )


def _distance_quantity(
    record: LevelBookRecord,
    level: LevelProfile | None,
    defaults: StochasticDefaults | None,
) -> Quantity:
    """A recorded sight distance, with an uncertainty that never has to be invented.

    The usual precedence first. When nothing supplies a sigma, fall back to the
    precision the number was **written to**: ``32.4`` lies in ``[32.35, 32.45)``,
    so its standard deviation is ``0.05 / sqrt(3)`` under the uniform
    distribution rounding produces.

    **This is not a hole in "GeoComp does not invent a sigma".** The digits an
    observer chose are real information, present in the file; and the fallback is
    permitted here and nowhere else because a sight distance's uncertainty
    reaches the answer only multiplied by a collimation error of order 1e-4. A
    staff reading's sigma becomes an adjustment weight, so it still refuses.
    ``specs/05`` section 2.3.
    """
    value = float(record.distance)  # type: ignore[arg-type]
    try:
        quantity, _source = resolve_sigma(
            SIGHT_DISTANCE,
            value,
            level=level,
            defaults=defaults,
            observation_id=f"row {record.row} ({record.station})",
        )
        return quantity
    except ValidationError as error:
        if error.code != "validation.missing_stochastic_model":  # pragma: no cover
            raise
    return Quantity.approximate(
        value,
        _recorded_precision_sigma(record.distance_text),
        Unit.METRE,
        Strategy.RECORDED_PRECISION,
    )


def _recorded_precision_sigma(text: str) -> float:
    """Half the last written digit, as a uniform-distribution standard deviation.

    A value written with no decimal point is known to half a unit; one written
    to three decimals, to half a millimetre. An empty or unparseable text falls
    back to half a metre, which is a generous and honest bound on a sight
    distance nobody wrote carefully.
    """
    cleaned = text.strip().replace(",", ".")
    if "." in cleaned:
        decimals = len(cleaned.rsplit(".", 1)[1])
        half_width = 0.5 * 10.0**-decimals
    elif cleaned:
        half_width = 0.5
    else:
        return 0.5
    return half_width / math.sqrt(3.0)
