# SPDX-License-Identifier: GPL-2.0-or-later
"""Reading a total-station field book (FR-160, FR-166, FR-095).

``specs/17-persistence-and-interoperability.md`` section 5.1, with RD-01's
``topo_test/raw_data.csv`` as the reference layout (``specs/09`` section 5).

**Every record is reported, none aborts the import** (FR-166). A field book with
six bad rows needs one run and produces six findings with their row numbers, not
six runs each stopping at the next problem. That is why this returns an
:class:`ImportResult` carrying findings rather than raising on the first
malformed value.

**Numbers are parsed locale-independently and converted once, here** (FR-095).
A comma decimal separator is handled at the boundary and never again, so a file
written by a Brazilian colleague and one written by a British one produce
identical objects.

Uncertainties are attached at this boundary too, by
:func:`~geocomp.core.instruments.stochastic.resolve_sigma`. A reading that
reached the domain model without one could still find its way into an
adjustment, and the whole point of FR-200 is that it cannot.
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass, field
from pathlib import Path

from geocomp.core.errors import ValidationError
from geocomp.core.findings import Finding, Severity
from geocomp.core.instruments.profiles import InstrumentProfile, ProfileLibrary
from geocomp.core.instruments.stochastic import (
    DIRECTION,
    SLOPE_DISTANCE,
    ZENITH_ANGLE,
    StochasticDefaults,
    resolve_sigma,
)
from geocomp.core.techniques.total_station.readings import (
    Face,
    FacePair,
    FaceReading,
    Setup,
)
from geocomp.core.uncertainty import Quantity
from geocomp.core.units import parse_angle
from geocomp.io.mapping import AngleFormat, FieldMapping

__all__ = [
    "FieldBookRecord",
    "ImportResult",
    "read_field_book",
    "read_field_book_csv",
]


@dataclass(frozen=True)
class FieldBookRecord:
    """One source row, parsed but not yet assembled into setups.

    Kept as an intermediate because a preview dialog needs exactly this: the
    row number, what was understood, and what went wrong -- before anything is
    committed.
    """

    row: int
    station: str
    target: str
    face: Face
    horizontal: float
    zenith: float
    distance: float | None = None
    instrument_height: float | None = None
    target_height: float | None = None
    set_number: int = 1
    temperature: float | None = None
    pressure: float | None = None
    humidity: float | None = None
    extra: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ImportResult:
    """Everything an import produced, including what it could not use.

    Attributes:
        setups: Assembled instrument stations, ready for pre-processing.
        records: Every row that parsed, in source order.
        findings: Every problem, each naming its row. **The import did not
            stop at any of them.**
        unrecognised_columns: Source columns the mapping did not mention.
        row_count: How many data rows were read, so a UI can say "42 of 50".
    """

    setups: tuple[Setup, ...]
    records: tuple[FieldBookRecord, ...]
    findings: tuple[Finding, ...]
    unrecognised_columns: tuple[str, ...]
    row_count: int

    @property
    def rejected_rows(self) -> tuple[int, ...]:
        return tuple(
            sorted({int(f.value) for f in self.findings if f.value is not None and f.is_blocking})
        )

    @property
    def is_clean(self) -> bool:
        return not any(finding.is_blocking for finding in self.findings)


def read_field_book_csv(
    path: str | Path,
    mapping: FieldMapping,
    *,
    library: ProfileLibrary | None = None,
    defaults: StochasticDefaults | None = None,
    encoding: str = "utf-8-sig",
) -> ImportResult:
    """Read a CSV field book. See :func:`read_field_book`.

    ``utf-8-sig`` by default because instrument software and spreadsheet
    exporters routinely emit a byte-order mark, and a leading ``\\ufeff`` on the
    first header turns the first mapped column into an unrecognised one -- a
    confusing failure that costs nothing to prevent.
    """
    source = Path(path)
    if not source.is_file():
        raise ValidationError(
            "field_book_not_found",
            received=str(source),
            expected="a readable CSV file",
        )
    with open(source, encoding=encoding, newline="") as handle:
        rows = list(csv.reader(handle))
    return read_field_book(rows, mapping, library=library, defaults=defaults)


def read_field_book(
    rows: list[list[str]],
    mapping: FieldMapping,
    *,
    library: ProfileLibrary | None = None,
    defaults: StochasticDefaults | None = None,
) -> ImportResult:
    """Turn source rows into setups, reporting every problem it finds.

    Args:
        rows: The whole source, header included.
        mapping: How the columns map. Its ``skip_rows`` is applied first.
        library: Supplies the instrument profile, and through it the nominal
            precisions. Without one, ``defaults`` must supply them or the import
            refuses -- GeoComp does not invent a sigma.
        defaults: Per-type defaults from Global Settings.

    Returns:
        The setups, the parsed records, and the findings. **Never raises for a
        bad row** -- only for a mapping that cannot work at all, which is a
        problem with the import definition rather than with the data.
    """
    missing = mapping.missing_required()
    if missing:
        raise ValidationError(
            "mapping_missing_required_fields",
            received=list(missing),
            expected="a mapping supplying at least the station and the two angles",
        )

    body = rows[mapping.skip_rows :]
    if not body:
        return ImportResult((), (), (), (), 0)

    header = [column.strip() for column in body[0]]
    findings: list[Finding] = []
    records: list[FieldBookRecord] = []

    instrument = library.instrument(None) if library is not None else None

    for offset, raw in enumerate(body[1:], start=mapping.skip_rows + 2):
        if not any(cell.strip() for cell in raw):
            continue
        row = dict(zip(header, raw, strict=False))
        try:
            records.append(_parse_row(offset, row, mapping))
        except _RowError as error:
            findings.append(
                Finding(
                    code=error.code,
                    severity=Severity.BLOCKING,
                    message=f"row {offset}: {error}",
                    value=float(offset),
                )
            )

    setups, assembly_findings = _assemble(
        records, mapping, instrument=instrument, defaults=defaults
    )
    findings.extend(assembly_findings)

    return ImportResult(
        setups=tuple(setups),
        records=tuple(records),
        findings=tuple(findings),
        unrecognised_columns=mapping.unrecognised(header),
        row_count=max(len(body) - 1, 0),
    )


class _RowError(Exception):
    """A problem with one record. Carries a code so the finding is stable."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _parse_row(row_number: int, row: dict[str, str], mapping: FieldMapping) -> FieldBookRecord:
    """Parse one source row, or raise :class:`_RowError` naming what went wrong."""

    def text(name: str) -> str | None:
        column = mapping.for_field(name)
        if column is None:
            return None
        if column.column is None:
            return column.constant
        value = row.get(column.column)
        return value.strip() if value is not None else None

    def number(name: str) -> float | None:
        column = mapping.for_field(name)
        value = text(name)
        if value is None or value == "":
            return None
        try:
            return mapping.parse_number(value, unit=column.unit if column else "")
        except ValueError as error:
            raise _RowError(
                "unparseable_number",
                f"column for {name} holds {value!r}, which is not a number ({error})",
            ) from error

    station = text("station")
    if not station:
        raise _RowError("missing_station", "no occupied station")

    target = _resolve_target(row, mapping, text)
    face = _resolve_face(text("face"), mapping)

    horizontal = _angle(mapping, "horizontal", text, number)
    zenith = _angle(mapping, "zenith", text, number)

    set_text = text("set_number")
    try:
        set_number = int(set_text) if set_text else 1
    except ValueError as error:
        raise _RowError(
            "unparseable_set_number", f"set number {set_text!r} is not a whole number"
        ) from error

    known = mapping.source_columns
    return FieldBookRecord(
        row=row_number,
        station=station,
        target=target,
        face=face,
        horizontal=horizontal,
        zenith=zenith,
        distance=number("distance"),
        instrument_height=number("instrument_height"),
        target_height=number("target_height"),
        set_number=set_number,
        temperature=number("temperature"),
        pressure=number("pressure"),
        humidity=number("humidity"),
        # Carried, not discarded: a column GeoComp does not understand may still
        # be the one the surveyor needs to see next to the observation.
        extra={k: v for k, v in row.items() if k and k not in known},
    )


def _resolve_target(row, mapping: FieldMapping, text) -> str:
    """Which point was sighted.

    Three layouts, in order of directness: an explicit target column; a
    backsight/foresight pair plus a column saying which of the two this row
    reads (RD-01's ``vis``); or a lone foresight column.
    """
    explicit = text("target")
    if explicit:
        return explicit

    sighted = text("sighted")
    if sighted is not None and sighted != "":
        role = mapping.sighted_values.get(sighted.strip().upper()) or mapping.sighted_values.get(
            sighted.strip()
        )
        if role is None:
            raise _RowError(
                "unknown_sighted_value",
                f"{sighted!r} is not one of the configured sighted values "
                f"({', '.join(sorted(mapping.sighted_values))})",
            )
        target = text("backsight") if role == "backsight" else text("foresight")
        if not target:
            raise _RowError("missing_target", f"no {role} station on this row")
        return target

    foresight = text("foresight")
    if foresight:
        return foresight
    raise _RowError("missing_target", "no target, foresight or sighted column supplies a target")


def _resolve_face(value: str | None, mapping: FieldMapping) -> Face:
    """Which face, from the configured tokens.

    A field book with no face column at all is read as all-direct, which is what
    a single-face survey is. That is a real workflow, not a defect, and
    :func:`~geocomp.core.techniques.total_station.face.reduce_single_face`
    handles the consequences.
    """
    if value is None or value == "":
        return Face.DIRECT
    name = mapping.face_values.get(value.strip().upper()) or mapping.face_values.get(value.strip())
    if name is None:
        raise _RowError(
            "unknown_face_value",
            f"{value!r} is not one of the configured face values "
            f"({', '.join(sorted(mapping.face_values))})",
        )
    return Face.DIRECT if name == "direct" else Face.REVERSE


def _angle(mapping: FieldMapping, name: str, text, number) -> float:
    """One angle, in radians, in whichever layout the mapping declares."""
    if mapping.angle_format is AngleFormat.SEXAGESIMAL_TRIPLE:
        parts = [number(f"{name}_{part}") for part in ("degrees", "minutes", "seconds")]
        if all(part is None for part in parts):
            raise _RowError("missing_angle", f"no {name} angle on this row")
        degrees, minutes, seconds = (part or 0.0 for part in parts)
        if not 0.0 <= minutes < 60.0 or not 0.0 <= seconds < 60.0:
            raise _RowError(
                "sexagesimal_out_of_range",
                f"{name} reads {degrees} {minutes} {seconds}: minutes and seconds must be "
                "below 60. A value above it usually means the columns are in the wrong "
                "order or the angle is already decimal",
            )
        sign = -1.0 if degrees < 0 else 1.0
        return math.radians(sign * (abs(degrees) + minutes / 60.0 + seconds / 3600.0))

    raw = text(name)
    if raw is None or raw == "":
        raise _RowError("missing_angle", f"no {name} angle on this row")

    if mapping.angle_format is AngleFormat.SEXAGESIMAL_TEXT:
        try:
            return parse_angle(raw)
        except ValueError as error:
            raise _RowError(
                "unparseable_angle", f"{name} reads {raw!r}, which is not an angle ({error})"
            ) from error

    value = number(name)
    if value is None:
        raise _RowError("missing_angle", f"no {name} angle on this row")
    if mapping.angle_format is AngleFormat.DECIMAL_DEGREES:
        return math.radians(value)
    if mapping.angle_format is AngleFormat.GON:
        return value * math.pi / 200.0
    return value


def _assemble(
    records: list[FieldBookRecord],
    mapping: FieldMapping,
    *,
    instrument: InstrumentProfile | None,
    defaults: StochasticDefaults | None,
) -> tuple[list[Setup], list[Finding]]:
    """Group records into setups, pairing faces where both are present.

    A pointing whose opposite face is missing becomes a single-face reading
    rather than being dropped: it is still a measurement, it is just one the
    instrument's constants have to correct instead of the pair cancelling them.
    """
    findings: list[Finding] = []
    by_station: dict[str, list[FieldBookRecord]] = {}
    for record in records:
        by_station.setdefault(record.station, []).append(record)

    setups: list[Setup] = []
    for station, station_records in by_station.items():
        instrument_heights = {
            r.instrument_height for r in station_records if r.instrument_height is not None
        }
        if len(instrument_heights) > 1:
            findings.append(
                Finding(
                    code="inconsistent_instrument_height",
                    severity=Severity.WARNING,
                    message=(
                        f"station {station} records {len(instrument_heights)} different "
                        "instrument heights. The first was used; check the field book"
                    ),
                    stations=(station,),
                )
            )
        height = next(iter(sorted(instrument_heights)), None)
        if height is None:
            findings.append(
                Finding(
                    code="missing_instrument_height",
                    severity=Severity.WARNING,
                    message=(
                        f"station {station} records no instrument height; zero was assumed, "
                        "which is right only for a leap-frog setup"
                    ),
                    stations=(station,),
                )
            )
            height = 0.0

        setup = Setup(
            station=station,
            instrument_height=_quantity(
                height, "instrument_height", instrument, defaults, station
            ),
            instrument_id=instrument.id if instrument is not None else None,
        )
        _add_readings(setup, station_records, instrument, defaults, findings)
        setups.append(setup)

    return setups, findings


def _add_readings(
    setup: Setup,
    records: list[FieldBookRecord],
    instrument: InstrumentProfile | None,
    defaults: StochasticDefaults | None,
    findings: list[Finding],
) -> None:
    by_target: dict[tuple[str, int], dict[Face, FieldBookRecord]] = {}
    for record in records:
        key = (record.target, record.set_number)
        faces = by_target.setdefault(key, {})
        if record.face in faces:
            findings.append(
                Finding(
                    code="repeated_face",
                    severity=Severity.WARNING,
                    message=(
                        f"row {record.row}: a second {record.face.value} pointing to "
                        f"{record.target} in set {record.set_number}. The first was kept; "
                        "give the repetition its own set number to use both"
                    ),
                    observations=(record.target,),
                    value=float(record.row),
                )
            )
            continue
        faces[record.face] = record

    for (target, set_number), faces in sorted(by_target.items()):
        del set_number
        readings = {
            face: _reading(record, target, instrument, defaults)
            for face, record in faces.items()
        }
        if Face.DIRECT in readings and Face.REVERSE in readings:
            setup.pairs.append(FacePair(readings[Face.DIRECT], readings[Face.REVERSE]))
        else:
            setup.singles.extend(readings.values())


def _reading(
    record: FieldBookRecord,
    target: str,
    instrument: InstrumentProfile | None,
    defaults: StochasticDefaults | None,
) -> FaceReading:
    return FaceReading(
        target=target,
        face=record.face,
        horizontal=_quantity(record.horizontal, DIRECTION, instrument, defaults, record.station),
        zenith=_quantity(record.zenith, ZENITH_ANGLE, instrument, defaults, record.station),
        distance=(
            None
            if record.distance is None
            else _quantity(record.distance, SLOPE_DISTANCE, instrument, defaults, record.station)
        ),
        target_height=(
            None
            if record.target_height is None
            else _quantity(record.target_height, "target_height", instrument, defaults, record.station)
        ),
        set_number=record.set_number,
        extra=dict(record.extra),
    )


def _quantity(
    value: float,
    kind: str,
    instrument: InstrumentProfile | None,
    defaults: StochasticDefaults | None,
    observation_id: str,
) -> Quantity:
    """Attach the uncertainty at the boundary, or refuse.

    Refusing here rather than downstream is the point: a reading that reached
    the domain model without a sigma could still find its way into an
    adjustment, and the whole of FR-200 is that it cannot.
    """
    quantity, _source = resolve_sigma(
        kind,
        value,
        instrument=instrument,
        defaults=defaults,
        observation_id=observation_id,
    )
    return quantity
