# SPDX-License-Identifier: GPL-2.0-or-later
"""The total-station field book, typed (FR-012, FR-013).

One job holds what a party brought back from the field with a total station:

* the **field book** -- one row per pointing: the station occupied, the point
  sighted, the face, the two angles, the slope distance and the two heights;
* the **known points** -- coordinates the survey starts from;
* the **orientations** -- an azimuth for a setup that sighted no known point.

The four Total Station windows of the menu work from the same job, as the four
algorithms of the toolbox work from the same field-book file.

**Nothing here computes.** A typed field book is *emitted* as the very inputs
``geocomp:totalstation_import_fieldbook`` reads -- rows under the logical field
names of :data:`geocomp.io.mapping.FIELDS`, and the :class:`~geocomp.io.FieldMapping`
that says so -- and the unchanged import, pre-processing, traverse and radiation
algorithms are run on them (ADR-0010). The chains are declared at the foot of
this module.

Three readings of the typed text are made at this boundary, each the kind a
file importer makes at its own:

* an angle is read in the job's typing convention and written in radians, with
  every digit (``repr``), so the importer reads back the same number;
* a **vertical angle** typed from the horizon is written as the zenith angle
  the importer takes, ``pi/2`` less the angle;
* a station left blank is the station of the row above, as it is on paper,
  where the occupied station is written once per setup.

**Rows keep their place.** The emitted file has the heading on its first line
and the grid's row *n* on line *n + 1*, blank where the grid's row is. So the
row an algorithm names in a finding or a report is always the grid's row plus
one, and :func:`as_typed` renumbers a finding for the grid.
"""

from __future__ import annotations

import csv
import io
import json
import math
import re
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, replace
from enum import Enum
from pathlib import Path
from typing import Any

from geocomp.core.errors import GeoCompError, ValidationError
from geocomp.core.findings import Finding
from geocomp.core.instruments.profiles import ProfileLibrary
from geocomp.core.instruments.stochastic import StochasticDefaults
from geocomp.io.fieldbook import ImportResult, read_field_book
from geocomp.io.mapping import AngleFormat, ColumnMapping, FieldMapping
from geocomp.jobs.angles import AngleTyping, format_typed_angle, parse_typed_angle
from geocomp.jobs.chains import Chain, ChainStep, InputFile, Ref
from geocomp.jobs.document import Job
from geocomp.jobs.tables import (
    CellKind,
    CellProblem,
    Column,
    TypedTable,
    parse_integer,
    parse_number,
)

__all__ = [
    "BOOK_COLUMNS",
    "FIELD_BOOK",
    "FILE_ROW_OFFSET",
    "IMPORT",
    "IMPORT_OPTIONS",
    "ORIENTATIONS",
    "ORIENTATION_COLUMNS",
    "POINTS",
    "POINT_COLUMNS",
    "PREPROCESS",
    "PREPROCESS_OPTIONS",
    "RADIATION",
    "RADIATION_OPTIONS",
    "TABLES",
    "TECHNIQUE",
    "TRAVERSE",
    "TRAVERSE_OPTIONS",
    "WINDOW_FIELD_BOOK",
    "WINDOW_PREPROCESS",
    "WINDOW_RADIATION",
    "WINDOW_TRAVERSE",
    "BookCheck",
    "Emission",
    "TotalStationBook",
    "VerticalAngle",
    "as_typed",
    "import_chain",
    "load_job",
    "new_job",
    "preprocess_chain",
    "radiation_chain",
    "traverse_chain",
]

TECHNIQUE = "total_station"

#: The job's tables.
FIELD_BOOK = "field_book"
POINTS = "points"
ORIENTATIONS = "orientations"

#: The algorithms the windows run. Ids are published (``specs/16`` section 2).
IMPORT = "geocomp:totalstation_import_fieldbook"
PREPROCESS = "geocomp:totalstation_preprocess"
TRAVERSE = "geocomp:totalstation_traverse"
RADIATION = "geocomp:totalstation_radiation"

#: The windows, by the name the registry and the job file know them by.
WINDOW_FIELD_BOOK = "totalstation_fieldbook"
WINDOW_PREPROCESS = "totalstation_preprocess"
WINDOW_TRAVERSE = "totalstation_traverse"
WINDOW_RADIATION = "totalstation_radiation"

#: The parameters of each algorithm a window lets the user set. The others are
#: the files the chain itself places.
IMPORT_OPTIONS = ("PROFILES", "SIGMA_DIRECTION", "SIGMA_ZENITH", "SIGMA_DISTANCE")
PREPROCESS_OPTIONS = (
    "TEMPERATURE",
    "PRESSURE",
    "HUMIDITY",
    "TEMPERATURE_SIGMA",
    "PRESSURE_SIGMA",
    "APPLY_ATMOSPHERIC",
    "COLLIMATION_TOLERANCE",
    "DISTANCE_TOLERANCE",
    "CORRELATION",
)
TRAVERSE_OPTIONS = (
    "ROUTE",
    "BACKSIGHT",
    "START_EASTING",
    "START_NORTHING",
    "START_AZIMUTH",
    "KIND",
    "METHOD",
    "CLOSE_EASTING",
    "CLOSE_NORTHING",
    "CLOSE_AZIMUTH",
    "ANGULAR_TOLERANCE",
    "RELATIVE_LIMIT",
)
RADIATION_OPTIONS = ("INSTRUMENT_HEIGHT", "TARGET_HEIGHT", "CORRELATION")

#: An algorithm numbers a field book's rows as lines of the file, whose first
#: line is the heading; the grid numbers its rows from one. Line = row + this.
FILE_ROW_OFFSET = 1


class VerticalAngle(Enum):
    """What the field book's vertical circle reads. The values are stored in the job file."""

    #: From the zenith: 90 degrees is level. What most instruments record.
    ZENITH = "zenith"
    #: From the horizon: zero is level, positive upwards.
    ELEVATION = "elevation"


#: The faces, with the spellings typed for them. ``PD`` and ``PI`` are the
#: Brazilian *posição direta* and *inversa*, RD-01's own tokens and the ones
#: the importer's default mapping reads; ``CD`` and ``CI`` the Spanish *círculo
#: directo* and *inverso* the glossary gives for them.
_FACES = (
    ("PD", ("1", "F1", "FL", "CL", "CD", "D", "DIRECT", "DIRETA", "DIRECTA")),
    ("PI", ("2", "F2", "FR", "CR", "CI", "I", "REVERSE", "INVERSA")),
)

BOOK_COLUMNS: tuple[Column, ...] = (
    Column("station", CellKind.NAME, carries=True),
    Column("instrument_height", CellKind.NUMBER, carries=True),
    Column("target", CellKind.NAME),
    Column("face", CellKind.CHOICE, choices=_FACES),
    Column("horizontal", CellKind.ANGLE),
    Column("vertical", CellKind.ANGLE),
    Column("distance", CellKind.NUMBER),
    Column("target_height", CellKind.NUMBER, carries=True),
    Column("set_number", CellKind.INTEGER),
    Column("note", CellKind.TEXT),
)

POINT_COLUMNS: tuple[Column, ...] = (
    Column("name", CellKind.NAME),
    Column("easting", CellKind.NUMBER),
    Column("northing", CellKind.NUMBER),
    Column("height", CellKind.NUMBER),
    Column("origin", CellKind.TEXT),
)

ORIENTATION_COLUMNS: tuple[Column, ...] = (
    Column("station", CellKind.NAME),
    Column("azimuth", CellKind.ANGLE),
)

TABLES: dict[str, tuple[Column, ...]] = {
    FIELD_BOOK: BOOK_COLUMNS,
    POINTS: POINT_COLUMNS,
    ORIENTATIONS: ORIENTATION_COLUMNS,
}

#: A row is a pointing when one of these was typed. A row that holds only what
#: a new row starts with -- the station and the heights carried from the row
#: above -- or only a note is not one yet, and is not emitted.
_OBSERVED = ("target", "face", "horizontal", "vertical", "distance", "set_number")

#: The emitted file's columns: logical fields of ``geocomp.io.mapping.FIELDS``,
#: named as themselves so the mapping is the identity.
_EMITTED = (
    "station",
    "target",
    "face",
    "horizontal",
    "zenith",
    "distance",
    "instrument_height",
    "target_height",
    "set_number",
)

_MAPPING_NAME = "GeoComp typed field book"
_RECORD = re.compile(r"^row (\d+)$")


def new_job(name: str = "") -> Job:
    """An empty total-station job, in the default conventions."""
    return Job(
        TECHNIQUE,
        {table: TypedTable(columns) for table, columns in TABLES.items()},
        name=name,
        entry={"angle_typing": AngleTyping.DMS.value, "vertical_angle": VerticalAngle.ZENITH.value},
    )


def load_job(path: str | Path) -> Job:
    """Open a total-station job file.

    Raises:
        ValidationError: :meth:`~geocomp.jobs.document.Job.load`'s refusals,
            and ``job_other_technique`` for the job of another technique.
    """
    job = Job.load(path, TABLES)
    if job.technique != TECHNIQUE:
        raise ValidationError(
            "job_other_technique", path=str(path), technique=job.technique, expected=TECHNIQUE
        )
    return job


@dataclass(frozen=True)
class Emission:
    """A typed field book as the inputs the import algorithm reads.

    Attributes:
        rows: The heading, then one line per row of the grid, in place; a row
            that is not a pointing is a line of empty cells.
        mapping: The mapping that reads them.
    """

    rows: tuple[tuple[str, ...], ...]
    mapping: FieldMapping

    @property
    def pointing_count(self) -> int:
        """How many rows are pointings."""
        return sum(1 for row in self.rows[1:] if any(row))

    def csv_text(self) -> str:
        """The rows as the CSV file the import algorithm is given."""
        stream = io.StringIO()
        csv.writer(stream, lineterminator="\n").writerows(self.rows)
        return stream.getvalue()

    def mapping_text(self) -> str:
        """The mapping as the JSON document the import algorithm is given."""
        return json.dumps(self.mapping.to_dict(), indent=2, sort_keys=True) + "\n"


@dataclass(frozen=True)
class BookCheck:
    """What reading a typed field book found, before anything is run.

    Attributes:
        problems: Cells that cannot be read, in the field book.
        findings: What the importer's own reader says of the rows that can be,
            numbered as it numbers them (:func:`as_typed` renumbers one).
        refusal: Why the book could not be read at all, when it could not: no
            precision configured for a reading, the usual case.
        pointings: How many rows are pointings.
        records: How many of them the reader accepted.
        setups: How many setups they make.
    """

    problems: tuple[CellProblem, ...] = ()
    findings: tuple[Finding, ...] = ()
    refusal: GeoCompError | None = None
    pointings: int = 0
    records: int = 0
    setups: int = 0

    @property
    def blocking(self) -> tuple[Finding, ...]:
        """The findings that reject a row."""
        return tuple(finding for finding in self.findings if finding.is_blocking)

    @property
    def is_usable(self) -> bool:
        """Whether the field book can be computed from: something typed, and nothing refused."""
        return (
            self.records > 0 and not self.problems and self.refusal is None and not self.blocking
        )


def as_typed(finding: Finding) -> Finding:
    """*finding* with its row numbered as the grid numbers it.

    The importer numbers rows as lines of a file with a heading
    (:data:`FILE_ROW_OFFSET`). A finding that names no row is returned as it is.
    """
    row = finding.context.get("row") if finding.context else None
    if row is None or not str(row).isdigit():
        return finding
    typed = int(row) - FILE_ROW_OFFSET
    return replace(
        finding,
        value=float(typed) if finding.value is not None else None,
        context={**finding.context, "row": str(typed)},
    )


class TotalStationBook:
    """A total-station job, read as the field book it is.

    Args:
        job: The job. It is edited in place: the book holds no data of its own.
    """

    def __init__(self, job: Job) -> None:
        self.job = job

    # -- the tables ------------------------------------------------------

    @property
    def table(self) -> TypedTable:
        """The field book's grid."""
        return self.job.tables[FIELD_BOOK]

    @property
    def points(self) -> TypedTable:
        """The known points."""
        return self.job.tables[POINTS]

    @property
    def orientations(self) -> TypedTable:
        """The orientations given for setups that sighted no known point."""
        return self.job.tables[ORIENTATIONS]

    # -- the conventions -------------------------------------------------

    @property
    def angle_typing(self) -> AngleTyping:
        """The convention the job's angles are typed in."""
        try:
            return AngleTyping(self.job.entry.get("angle_typing", AngleTyping.DMS.value))
        except ValueError:
            return AngleTyping.DMS

    @angle_typing.setter
    def angle_typing(self, typing: AngleTyping) -> None:
        # The cells are not rewritten: what was typed is kept as typed, and is
        # read from now on in the other convention. The window says so.
        self.job.entry["angle_typing"] = typing.value

    @property
    def vertical(self) -> VerticalAngle:
        """What the vertical column holds."""
        try:
            return VerticalAngle(self.job.entry.get("vertical_angle", VerticalAngle.ZENITH.value))
        except ValueError:
            return VerticalAngle.ZENITH

    @vertical.setter
    def vertical(self, vertical: VerticalAngle) -> None:
        self.job.entry["vertical_angle"] = vertical.value

    # -- reading ---------------------------------------------------------

    def problems(self) -> tuple[CellProblem, ...]:
        """Every cell of the field book that cannot be read in the job's conventions."""
        return self.table.problems(self.angle_typing)

    def pointing_rows(self) -> tuple[int, ...]:
        """The grid's rows that are pointings, in order."""
        table = self.table
        return tuple(
            row
            for row in table.filled_rows()
            if any(table.cell(row, key) for key in _OBSERVED)
        )

    def _stations_by_row(self) -> Iterator[tuple[int, str]]:
        """Each pointing row with the station it was made from, blank ones carried down."""
        table = self.table
        pointings = set(self.pointing_rows())
        current = ""
        for row in table.filled_rows():
            current = table.cell(row, "station") or current
            if row in pointings:
                yield row, current

    def stations(self) -> tuple[str, ...]:
        """The stations occupied, in the order the field book first names them."""
        return tuple(dict.fromkeys(station for _row, station in self._stations_by_row() if station))

    def targets(self, station: str | None = None) -> tuple[str, ...]:
        """The points sighted -- from *station*, or from anywhere -- in the field book's order."""
        table = self.table
        return tuple(
            dict.fromkeys(
                table.cell(row, "target")
                for row, occupied in self._stations_by_row()
                if (station is None or occupied == station) and table.cell(row, "target")
            )
        )

    def point_names(self) -> tuple[str, ...]:
        """Every point the field book names, occupied or sighted, in its order."""
        return tuple(dict.fromkeys((*self.stations(), *self.targets())))

    # -- emission --------------------------------------------------------

    def emit(self) -> Emission:
        """The field book as the import algorithm's inputs.

        Raises:
            ValidationError: ``field_book_cells_unreadable`` while a cell
                cannot be read, ``field_book_empty`` for a book without a
                pointing. What an algorithm is run on is the whole book or
                nothing: a row left out in silence is a point missing from a
                survey.
        """
        problems = self.problems()
        if problems:
            raise ValidationError("field_book_cells_unreadable", count=len(problems))
        emission = self._emission(skip=frozenset())
        if emission.pointing_count == 0:
            raise ValidationError("field_book_empty")
        return emission

    def _emission(self, *, skip: frozenset[int]) -> Emission:
        table = self.table
        typing, vertical = self.angle_typing, self.vertical
        blank = ("",) * len(_EMITTED)
        lines: list[tuple[str, ...]] = [blank] * table.row_count
        for row, station in self._stations_by_row():
            if row in skip:
                continue

            def cell(key: str, row: int = row) -> str:
                return table.cell(row, key)

            def number(key: str, row: int = row) -> str:
                text = table.cell(row, key)
                return repr(parse_number(text)) if text else ""

            zenith = ""
            if cell("vertical"):
                angle = parse_typed_angle(cell("vertical"), typing)
                zenith = repr(angle if vertical is VerticalAngle.ZENITH else math.pi / 2.0 - angle)
            lines[row] = (
                station,
                cell("target"),
                table.column("face").choice(cell("face")) if cell("face") else "",
                repr(parse_typed_angle(cell("horizontal"), typing)) if cell("horizontal") else "",
                zenith,
                number("distance"),
                number("instrument_height"),
                number("target_height"),
                str(parse_integer(cell("set_number"))) if cell("set_number") else "",
            )
        mapping = FieldMapping(
            name=_MAPPING_NAME,
            columns=tuple(ColumnMapping(field=name, column=name) for name in _EMITTED),
            angle_format=AngleFormat.RADIANS,
            decimal_separator=".",
            face_values={"PD": "direct", "PI": "reverse"},
        )
        return Emission(rows=(_EMITTED, *lines), mapping=mapping)

    def read(
        self,
        *,
        library: ProfileLibrary | None = None,
        defaults: StochasticDefaults | None = None,
    ) -> ImportResult:
        """The field book as the importer's own reader reads it.

        The same function the import algorithm calls, on the same rows, so a
        window that shows what it returns shows what the algorithm will find.

        Raises:
            ValidationError: :meth:`emit`'s refusals.
            GeoCompError: the reader's, for a book it cannot read at all.
        """
        emission = self.emit()
        return read_field_book(
            [list(row) for row in emission.rows], emission.mapping, library=library, defaults=defaults
        )

    def check(
        self,
        *,
        library: ProfileLibrary | None = None,
        defaults: StochasticDefaults | None = None,
    ) -> BookCheck:
        """Everything wrong with the field book as it stands, in one pass (FR-012).

        Cells that cannot be read are reported as such, and their rows are kept
        from the reader, which would only say the same less exactly. Every
        other row is read by the importer's reader, and what it finds is
        returned with the row numbered as it numbers it.
        """
        problems = self.problems()
        emission = self._emission(skip=frozenset(problem.row for problem in problems))
        try:
            result = read_field_book(
                [list(row) for row in emission.rows],
                emission.mapping,
                library=library,
                defaults=defaults,
            )
        except GeoCompError as error:
            return BookCheck(problems=problems, refusal=error, pointings=len(self.pointing_rows()))
        return BookCheck(
            problems=problems,
            findings=result.findings,
            pointings=len(self.pointing_rows()),
            records=len(result.records),
            setups=len(result.setups),
        )

    # -- opening a toolbox document ---------------------------------------

    def fill_from_readings(self, document: Mapping[str, Any], *, source: str = "") -> int:
        """Put a ``geocomp.readings`` document's pointings in the field book (FR-014).

        The document the toolbox's *Import field book* wrote. The grid is
        replaced, as one edit that can be undone, by one row per reading, in
        the order of the source's rows where the document records them. Angles
        are written in the job's convention to four decimals of a second --
        about 5e-10 rad, a tenth of what the finest instrument resolves, and
        not the bit-for-bit equality typing gives. The precisions in the
        document are not carried: the Field book window's first step supplies them when
        the book is read again.

        Returns:
            How many rows were written.

        Raises:
            ValidationError: ``readings_document_not_readings`` for a document
                of another kind, ``readings_document_malformed`` for one that
                lacks what a reading needs.
        """
        if not isinstance(document, Mapping) or document.get("kind") != "geocomp.readings":
            raise ValidationError("readings_document_not_readings", path=source)
        try:
            readings = list(self._readings(document))
        except (KeyError, TypeError, ValueError) as error:
            raise ValidationError(
                "readings_document_malformed", path=source, reason=repr(error)
            ) from error
        # Source order where every reading records its row; the document's otherwise.
        if readings and all(order is not None for order, _cells in readings):
            readings.sort(key=lambda item: item[0])
        self.table.replace(cells for _order, cells in readings)
        return len(readings)

    def _readings(self, document: Mapping[str, Any]) -> Iterator[tuple[int | None, list[str]]]:
        typing, vertical = self.angle_typing, self.vertical
        for setup in document.get("setups") or ():
            station = str(setup["station"])
            height = _plain(float(setup["instrument_height"]["value"]))
            entries = [
                reading
                for pair in setup.get("pairs") or ()
                for reading in (pair["direct"], pair["reverse"])
            ]
            entries.extend(setup.get("singles") or ())
            for reading in entries:
                zenith = float(reading["zenith"]["value"])
                shown = zenith if vertical is VerticalAngle.ZENITH else math.pi / 2.0 - zenith
                set_number = int(reading.get("set_number", 1))
                match = _RECORD.match(str(reading.get("record") or ""))
                cells = {
                    "station": station,
                    "instrument_height": height,
                    "target": str(reading["target"]),
                    "face": "PD" if reading["face"] == "direct" else "PI",
                    "horizontal": format_typed_angle(float(reading["horizontal"]["value"]), typing),
                    "vertical": format_typed_angle(shown, typing),
                    "distance": _value(reading.get("distance")),
                    "target_height": _value(reading.get("target_height")),
                    "set_number": "" if set_number == 1 else str(set_number),
                }
                yield (
                    int(match.group(1)) if match else None,
                    [cells.get(column.key, "") for column in BOOK_COLUMNS],
                )

    # -- known points and orientations -------------------------------------

    def known_stations(self) -> dict[str, tuple[float, float, float]]:
        """The known points, by name: easting, northing and height, in metres.

        Raises:
            ValidationError: ``known_points_unreadable`` while a cell cannot be
                read, ``known_point_incomplete`` for a row that lacks its name
                or a coordinate, ``known_point_repeated`` for a name given
                twice, ``known_points_missing`` when there is none.
        """
        table = self.points
        problems = table.problems()
        if problems:
            raise ValidationError("known_points_unreadable", count=len(problems))
        stations: dict[str, tuple[float, float, float]] = {}
        for row in table.filled_rows():
            cells = {key: table.cell(row, key) for key in ("name", "easting", "northing", "height")}
            if not all(cells.values()):
                raise ValidationError("known_point_incomplete", row=row + 1)
            if cells["name"] in stations:
                raise ValidationError("known_point_repeated", point=cells["name"])
            stations[cells["name"]] = (
                parse_number(cells["easting"]),
                parse_number(cells["northing"]),
                parse_number(cells["height"]),
            )
        if not stations:
            raise ValidationError("known_points_missing")
        return stations

    def given_orientations(self) -> dict[str, float]:
        """The orientations given, by station, in degrees -- what the radiation algorithm reads.

        Raises:
            ValidationError: ``orientations_unreadable`` while an azimuth
                cannot be read, ``orientation_incomplete`` for a row that lacks
                its station or its azimuth.
        """
        table = self.orientations
        problems = table.problems(self.angle_typing)
        if problems:
            raise ValidationError("orientations_unreadable", count=len(problems))
        given: dict[str, float] = {}
        for row in table.filled_rows():
            station, azimuth = table.cell(row, "station"), table.cell(row, "azimuth")
            if not station or not azimuth:
                raise ValidationError("orientation_incomplete", row=row + 1)
            given[station] = math.degrees(parse_typed_angle(azimuth, self.angle_typing))
        return given

    def set_point(
        self, name: str, easting: float, northing: float, height: float | None, *, origin: str = ""
    ) -> int:
        """Write a known point, over the row of that name if there is one. Returns its row.

        For what a window fills in itself: a point picked on the map, a station
        a traverse gave. Coordinates are written with every digit.
        """
        table = self.points
        row = next(
            (index for index in table.filled_rows() if table.cell(index, "name") == name), None
        )
        cells = [name, _plain(easting), _plain(northing), "" if height is None else _plain(height), origin]
        rows = table.to_list()
        if row is None:
            rows = [cells_ for index, cells_ in enumerate(rows) if not table.is_blank(index)]
            rows.append(cells)
            row = len(rows) - 1
        else:
            rows[row] = cells
        table.replace(rows)
        return row


def _plain(value: float) -> str:
    """*value* with every digit and no exponent, as a cell holds a number GeoComp wrote."""
    text = repr(float(value))
    return f"{value:.12f}".rstrip("0").rstrip(".") if "e" in text or "E" in text else text


def _value(quantity: Mapping[str, Any] | None) -> str:
    return "" if not quantity else _plain(float(quantity["value"]))


# -- the chains the windows run (FR-011) -------------------------------------


def _options(job: Job, window: str, names: Sequence[str]) -> dict[str, Any]:
    """What the user set in *window*, of the parameters it may set.

    A parameter never touched is left out, and the algorithm takes its own
    default -- the one the toolbox dialog would show.
    """
    chosen = job.parameters(window)
    return {name: chosen[name] for name in names if name in chosen and chosen[name] is not None}


def _import_step(book: TotalStationBook) -> ChainStep:
    emission = book.emit()
    return ChainStep(
        key="import",
        algorithm=IMPORT,
        parameters={
            **_options(book.job, WINDOW_FIELD_BOOK, IMPORT_OPTIONS),
            "SOURCE": InputFile("fieldbook.csv", emission.csv_text()),
            "MAPPING": InputFile("mapping.json", emission.mapping_text()),
        },
        outputs={
            "OUTPUT_READINGS": "readings.json",
            "OUTPUT_HTML": "report.html",
            "OUTPUT_FINDINGS": "findings.csv",
        },
    )


def _preprocess_step(book: TotalStationBook) -> ChainStep:
    # One instrument per job: the profile library chosen in the Field book
    # window's first step is the one pre-processing corrects with.
    profiles = _options(book.job, WINDOW_FIELD_BOOK, ("PROFILES",))
    return ChainStep(
        key="preprocess",
        algorithm=PREPROCESS,
        parameters={
            **profiles,
            **_options(book.job, WINDOW_PREPROCESS, PREPROCESS_OPTIONS),
            "READINGS": Ref("import", "OUTPUT_READINGS"),
        },
        outputs={
            "OUTPUT_REDUCED": "reduced.json",
            "OUTPUT_HTML": "report.html",
            "OUTPUT_CSV": "reductions.csv",
        },
    )


def import_chain(book: TotalStationBook) -> Chain:
    """What the Field book window runs: the import, on the typed book.

    Raises:
        ValidationError: :meth:`TotalStationBook.emit`'s refusals.
    """
    return Chain((_import_step(book),))


def preprocess_chain(book: TotalStationBook) -> Chain:
    """What Generalised pre-processing runs: the import, then the pre-processing of what it read.

    Raises:
        ValidationError: :meth:`TotalStationBook.emit`'s refusals.
    """
    return Chain((_import_step(book), _preprocess_step(book)))


def traverse_chain(book: TotalStationBook) -> Chain:
    """What Traverse runs: import, pre-processing, and the traverse over the reductions.

    Raises:
        ValidationError: :meth:`TotalStationBook.emit`'s refusals.
    """
    return Chain(
        (
            _import_step(book),
            _preprocess_step(book),
            ChainStep(
                key="traverse",
                algorithm=TRAVERSE,
                parameters={
                    **_options(book.job, WINDOW_TRAVERSE, TRAVERSE_OPTIONS),
                    "REDUCTIONS": Ref("preprocess", "OUTPUT_REDUCED"),
                },
                outputs={
                    "OUTPUT_COORDINATES": "coordinates.json",
                    "OUTPUT_HTML": "report.html",
                    "OUTPUT_CSV": "stations.csv",
                },
            ),
        )
    )


def radiation_chain(book: TotalStationBook) -> Chain:
    """What 3D radiation runs: import, pre-processing, and the radiation from the known points.

    Raises:
        ValidationError: :meth:`TotalStationBook.emit`'s refusals, and those
            of :meth:`TotalStationBook.known_stations` and
            :meth:`TotalStationBook.given_orientations`.
    """
    stations = {name: list(values) for name, values in book.known_stations().items()}
    orientations = book.given_orientations()
    return Chain(
        (
            _import_step(book),
            _preprocess_step(book),
            ChainStep(
                key="radiation",
                algorithm=RADIATION,
                parameters={
                    **_options(book.job, WINDOW_RADIATION, RADIATION_OPTIONS),
                    "REDUCTIONS": Ref("preprocess", "OUTPUT_REDUCED"),
                    "STATIONS": InputFile("stations.json", _document(stations)),
                    "ORIENTATIONS": (
                        InputFile("orientations.json", _document(orientations))
                        if orientations
                        else None
                    ),
                },
                outputs={
                    "OUTPUT_POINTS": "points.json",
                    "OUTPUT_HTML": "report.html",
                    "OUTPUT_CSV": "points.csv",
                },
            ),
        )
    )


def _document(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
