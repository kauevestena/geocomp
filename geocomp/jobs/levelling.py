# SPDX-License-Identifier: GPL-2.0-or-later
"""The levelling field book, typed (FR-012, FR-013; ROADMAP P14c).

One job holds what a levelling party brought back:

* the **field book** -- one row per staff reading: the line, the setup, the
  station read, whether it is a backsight, a foresight or an intermediate
  sight, the reading (or the middle of three wires, with the upper and the
  lower), and the sight distance;
* the **benchmarks** -- the heights the network is held to.

The six windows of the Level menu work from it, as the six algorithms of the
toolbox work from the same book written as a file.

**Nothing here computes.** The book is *emitted* as the very inputs
``geocomp:levelling_import`` reads: rows under the logical field names of
:data:`geocomp.io.levelbook.LEVEL_FIELDS`, one row per reading, and the
:class:`~geocomp.io.levelbook.LevelMapping` that says so. The chains are
declared at the foot of this module.

Three readings of the typed text are made at this boundary, each the kind a
file importer makes at its own:

* **a number is written as it was typed**, with a decimal point for a comma,
  and never re-printed: the importer takes a sight distance's precision from
  the digits it was written to when nothing else gives one
  (``specs/10`` section 6), so ``32.4`` must reach it as ``32.4``;
* a **setup** is opened by a backsight, as on paper: a backsight row with no
  setup typed starts the next one, numbered in order, and a foresight or an
  intermediate sight with none typed belongs to the setup above it;
* a **line** left blank is the line of the row above.

A book with an upper or a lower wire typed on any row is read as a book of
three wires, every reading of it: the importer reads a book one way or the
other, and a row that lacks a wire is named rather than read differently.

**Rows keep their place**, as in the total-station book: the emitted file's
heading is its first line and the grid's row *n* is line *n + 1*.
"""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from geocomp.core.errors import GeoCompError, ValidationError
from geocomp.core.findings import Finding
from geocomp.core.instruments.level import LevelProfile
from geocomp.core.instruments.stochastic import StochasticDefaults
from geocomp.io.levelbook import LevelImportResult, LevelMapping, read_level_book
from geocomp.io.mapping import ColumnMapping
from geocomp.jobs.chains import Chain, ChainStep, InputFile, Ref
from geocomp.jobs.document import Job
from geocomp.jobs.tables import CellKind, CellProblem, Column, TypedTable, parse_number

__all__ = [
    "BENCHMARKS",
    "BENCHMARK_COLUMNS",
    "BOOK_COLUMNS",
    "CLOSURES",
    "CLOSURE_OPTIONS",
    "EQUAL",
    "EQUAL_OPTIONS",
    "EQUIDISTANT",
    "EQUIDISTANT_OPTIONS",
    "EXTREME",
    "EXTREME_OPTIONS",
    "FIELD_BOOK",
    "FILE_ROW_OFFSET",
    "IMPORT",
    "IMPORT_OPTIONS",
    "NETWORK",
    "NETWORK_OPTIONS",
    "TABLES",
    "TECHNIQUE",
    "WINDOW_CLOSURES",
    "WINDOW_EQUAL",
    "WINDOW_EQUIDISTANT",
    "WINDOW_EXTREME",
    "WINDOW_FIELD_BOOK",
    "WINDOW_NETWORK",
    "LevelCheck",
    "LevelEmission",
    "LevellingBook",
    "as_typed",
    "closures_chain",
    "equal_chain",
    "equidistant_chain",
    "extreme_chain",
    "import_chain",
    "load_job",
    "network_chain",
    "new_job",
]

TECHNIQUE = "levelling"

#: The job's tables.
FIELD_BOOK = "field_book"
BENCHMARKS = "benchmarks"

#: The algorithms the windows run. Ids are published (``specs/16`` section 2).
IMPORT = "geocomp:levelling_import"
EQUAL = "geocomp:levelling_equal_sights"
EQUIDISTANT = "geocomp:levelling_equidistant_sights"
EXTREME = "geocomp:levelling_extreme_sights"
CLOSURES = "geocomp:levelling_closures"
NETWORK = "geocomp:levelling_network"

#: The windows, by the name the registry and the job file know them by.
WINDOW_FIELD_BOOK = "levelling_fieldbook"
WINDOW_EQUAL = "levelling_equal_sights"
WINDOW_EQUIDISTANT = "levelling_equidistant_sights"
WINDOW_EXTREME = "levelling_extreme_sights"
WINDOW_CLOSURES = "levelling_closures"
WINDOW_NETWORK = "levelling_network"

#: The parameters of each algorithm a window lets the user set. The others are
#: the files the chain itself places; the instrument -- ``PROFILES`` and
#: ``LEVEL_ID`` -- is the *Levelling field book* window's, given to every
#: algorithm that takes one.
IMPORT_OPTIONS = ("PROFILES", "LEVEL_ID", "SIGMA_READING", "STADIA_FACTOR")
INSTRUMENT = ("PROFILES", "LEVEL_ID")
EQUAL_OPTIONS = (
    "COLLIMATION",
    "COLLIMATION_SIGMA",
    "MAX_SIGHT_LENGTH",
    "MAX_SIGHT_IMBALANCE",
    "MAX_ACCUMULATED_IMBALANCE",
)
EQUIDISTANT_OPTIONS = ("INFLATION", "DISCREPANCY_TOLERANCE")
EXTREME_OPTIONS = ("ONLY_MULTIPLE", "MAX_SIGHT_LENGTH", "MAX_SIGHT_IMBALANCE")
CLOSURE_OPTIONS = (
    "MODE",
    "LOOP_ID",
    "KNOWN_DIFFERENCE",
    "KNOWN_SIGMA",
    "TOLERANCE_COEFFICIENT",
    "WEIGHTING",
)
NETWORK_OPTIONS = (
    "FREE",
    "WEIGHTING",
    "SIGMA_PER_KM",
    "SIGMA_PER_SETUP",
    "VARIANCE_COMPONENTS",
    "CONFIDENCE",
    "ALPHA",
    "BETA",
    "TOLERANCE_COEFFICIENT",
    "ADJUST_FAILING",
    "ORTHOMETRIC",
    "EPOCH",
)

#: An algorithm numbers a book's rows as lines of the file, whose first line is
#: the heading; the grid numbers its rows from one. Line = row + this.
FILE_ROW_OFFSET = 1

#: The kinds of sight, with the spellings typed for them: the English
#: abbreviations the importer's default mapping reads, and the Portuguese and
#: Spanish words of a *caderneta* and a *libreta* -- ré and vante, espalda and
#: frente as the glossary has them, atrás and adelante as they are also said.
_SIGHTS = (
    ("BS", ("B", "BACK", "BACKSIGHT", "R", "RE", "RÉ", "E", "ESPALDA", "ATRAS", "ATRÁS")),
    ("FS", ("F", "FORE", "FORESIGHT", "V", "VANTE", "FRENTE", "ADELANTE")),
    ("IS", ("I", "INT", "INTERMEDIATE", "INTERMEDIARIA", "INTERMEDIÁRIA", "INTERMEDIA")),
)

BOOK_COLUMNS: tuple[Column, ...] = (
    Column("line", CellKind.NAME, carries=True),
    Column("setup", CellKind.NAME),
    Column("station", CellKind.NAME),
    Column("sight", CellKind.CHOICE, choices=_SIGHTS),
    Column("reading", CellKind.NUMBER),
    Column("upper", CellKind.NUMBER),
    Column("lower", CellKind.NUMBER),
    Column("distance", CellKind.NUMBER),
    Column("note", CellKind.TEXT),
)

#: A benchmark the network is held to: exactly, or with a standard deviation.
BENCHMARK_COLUMNS: tuple[Column, ...] = (
    Column("name", CellKind.NAME),
    Column("height", CellKind.NUMBER),
    Column("sigma", CellKind.NUMBER),
)

#: A job saved before a table was declared opens with that table empty.
TABLES: dict[str, tuple[Column, ...]] = {
    FIELD_BOOK: BOOK_COLUMNS,
    BENCHMARKS: BENCHMARK_COLUMNS,
}

#: A row is a reading when one of these was typed. A row holding only the line
#: carried down, a setup's name or a note is not one yet, and is not emitted.
_OBSERVED = ("station", "sight", "reading", "upper", "lower", "distance")

#: What the importer is told each typed kind of sight means.
_SIGHT_VALUES = {"BS": "backsight", "FS": "foresight", "IS": "intermediate"}

#: The characters the network's benchmark list is written with, which a
#: benchmark's name therefore cannot hold.
_BENCHMARK_SEPARATORS = (",", ";", "=", "±")

_MAPPING_NAME = "GeoComp typed levelling book"


def new_job(name: str = "") -> Job:
    """An empty levelling job."""
    return Job(
        TECHNIQUE,
        {table: TypedTable(columns) for table, columns in TABLES.items()},
        name=name,
    )


def load_job(path: str | Path) -> Job:
    """Open a levelling job file.

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
class LevelEmission:
    """A typed levelling book as the inputs the import algorithm reads.

    Attributes:
        rows: The heading, then one line per row of the grid, in place; a row
            that is not a reading is a line of empty cells.
        three_wire: Whether the book is read as three wires.
    """

    rows: tuple[tuple[str, ...], ...]
    three_wire: bool

    @property
    def reading_count(self) -> int:
        """How many rows are readings."""
        return sum(1 for row in self.rows[1:] if any(row))

    def mapping(self, stadia_factor: float = 100.0) -> LevelMapping:
        """The mapping that reads the rows: each column under its own field's name."""
        return LevelMapping(
            name=_MAPPING_NAME,
            columns=tuple(ColumnMapping(field=name, column=name) for name in self.rows[0]),
            decimal_separator=".",
            sight_values=dict(_SIGHT_VALUES),
            stadia_factor=stadia_factor,
        )

    def csv_text(self) -> str:
        """The rows as the CSV file the import algorithm is given."""
        stream = io.StringIO()
        csv.writer(stream, lineterminator="\n").writerows(self.rows)
        return stream.getvalue()

    def mapping_text(self) -> str:
        """The mapping as the JSON document the import algorithm is given.

        Without a stadia factor: the document's would override the import's
        own parameter, which is where the *Levelling field book* window sets it.
        """
        payload = self.mapping().to_dict()
        payload.pop("stadia_factor", None)
        return json.dumps(payload, indent=2, sort_keys=True) + "\n"


@dataclass(frozen=True)
class LevelCheck:
    """What reading a typed levelling book found, before anything is run.

    Attributes:
        problems: Cells that cannot be read.
        findings: What the importer's own reader says of the rows that can be,
            numbered as it numbers them (:func:`as_typed` renumbers one).
        refusal: Why the book could not be read at all, when it could not.
        entries: How many rows are readings.
        setups: How many setups the reader assembled.
        lines: How many lines.
    """

    problems: tuple[CellProblem, ...] = ()
    findings: tuple[Finding, ...] = ()
    refusal: GeoCompError | None = None
    entries: int = 0
    setups: int = 0
    lines: int = 0

    @property
    def blocking(self) -> tuple[Finding, ...]:
        """The findings that reject a row or a setup."""
        return tuple(finding for finding in self.findings if finding.is_blocking)

    @property
    def is_usable(self) -> bool:
        """Whether the book can be computed from."""
        return self.setups > 0 and not self.problems and self.refusal is None and not self.blocking


#: Findings whose ``value`` is the row of the book they are about, as the
#: reader numbers it, though their context names no row.
_ROW_VALUED = frozenset({"level_setup_malformed", "level_setup_refused"})


def as_typed(finding: Finding) -> tuple[Finding, int | None]:
    """*finding* with its row numbered as the grid numbers it, and that row counted from zero.

    The importer numbers rows as lines of a file with a heading
    (:data:`FILE_ROW_OFFSET`): a row's finding names it in its context, and a
    setup's carries the row of the setup's first reading as its value. Any
    other finding is returned as it is, about no row.
    """
    context = dict(finding.context or {})
    row = context.get("row")
    if row is not None and str(row).isdigit():
        typed = int(row) - FILE_ROW_OFFSET
        context["row"] = str(typed)
        moved = replace(
            finding,
            value=float(typed) if finding.value is not None else None,
            context=context,
        )
        return moved, typed - 1
    if (finding.code in _ROW_VALUED or finding.wording in _ROW_VALUED) and finding.value is not None:
        typed = int(finding.value) - FILE_ROW_OFFSET
        return replace(finding, value=float(typed)), typed - 1
    return finding, None


class LevellingBook:
    """A levelling job, read as the field book it is.

    Args:
        job: The job. It is edited in place: the book holds no data of its own.
    """

    def __init__(self, job: Job) -> None:
        self.job = job

    @property
    def table(self) -> TypedTable:
        """The field book's grid."""
        return self.job.tables[FIELD_BOOK]

    @property
    def benchmarks(self) -> TypedTable:
        """The benchmarks the network is held to."""
        return self.job.tables[BENCHMARKS]

    # -- reading ---------------------------------------------------------

    def problems(self) -> tuple[CellProblem, ...]:
        """Every cell of the field book that cannot be read."""
        return self.table.problems()

    def reading_rows(self) -> tuple[int, ...]:
        """The grid's rows that are readings, in order."""
        table = self.table
        return tuple(
            row for row in table.filled_rows() if any(table.cell(row, key) for key in _OBSERVED)
        )

    def _resolved(self) -> Iterator[tuple[int, str, str]]:
        """Each reading row with its line and its setup, as :mod:`this module <geocomp.jobs.levelling>`
        reads blanks: a line carried down, a setup opened by a backsight."""
        table = self.table
        readings = set(self.reading_rows())
        line, setup, opened = "", "", 0
        for row in table.filled_rows():
            line = table.cell(row, "line") or line
            if row not in readings:
                continue
            typed = table.cell(row, "setup")
            backsight = _sight(table, row) == "BS"
            if backsight:
                opened += 1
            if typed:
                setup = typed
            elif backsight:
                setup = str(opened)
            yield row, line, setup

    @property
    def three_wire(self) -> bool:
        """Whether the book is read as three wires: an upper or a lower one typed on some row."""
        table = self.table
        return any(
            table.cell(row, "upper") or table.cell(row, "lower") for row in self.reading_rows()
        )

    def stations(self) -> tuple[str, ...]:
        """The stations read, in the order the book first names them."""
        table = self.table
        return tuple(
            dict.fromkeys(
                table.cell(row, "station")
                for row in self.reading_rows()
                if table.cell(row, "station")
            )
        )

    def setups(self) -> dict[str, list[tuple[str, str]]]:
        """Each setup, by name in the book's order, with its sights as typed: kind and station."""
        table = self.table
        setups: dict[str, list[tuple[str, str]]] = {}
        for row, _line, setup in self._resolved():
            setups.setdefault(setup, []).append((_sight(table, row), table.cell(row, "station")))
        return setups

    # -- emission --------------------------------------------------------

    def emit(self) -> LevelEmission:
        """The field book as the import algorithm's inputs.

        Raises:
            ValidationError: ``level_book_cells_unreadable`` while a cell
                cannot be read, ``level_book_empty`` for a book without a
                reading: what an algorithm is run on is the whole book or
                nothing.
        """
        problems = self.problems()
        if problems:
            raise ValidationError("level_book_cells_unreadable", count=len(problems))
        emission = self._emission(skip=frozenset())
        if emission.reading_count == 0:
            raise ValidationError("level_book_empty")
        return emission

    def _emission(self, *, skip: frozenset[int]) -> LevelEmission:
        table = self.table
        wires = self.three_wire
        heading: tuple[str, ...] = (
            "line",
            "setup",
            "station",
            "sight",
            *(("upper", "middle", "lower") if wires else ("reading",)),
            "distance",
            "note",
        )
        lines: list[tuple[str, ...]] = [("",) * len(heading)] * table.row_count
        for row, line, setup in self._resolved():
            if row in skip:
                continue
            sight = _sight(table, row)
            reading = _typed_number(table.cell(row, "reading"))
            values = (
                (
                    _typed_number(table.cell(row, "upper")),
                    reading,
                    _typed_number(table.cell(row, "lower")),
                )
                if wires
                else (reading,)
            )
            lines[row] = (
                line,
                setup,
                table.cell(row, "station"),
                sight,
                *values,
                _typed_number(table.cell(row, "distance")),
                table.cell(row, "note"),
            )
        return LevelEmission(rows=(heading, *lines), three_wire=wires)

    def read(
        self,
        *,
        level: LevelProfile | None = None,
        defaults: StochasticDefaults | None = None,
        stadia_factor: float = 100.0,
    ) -> LevelImportResult:
        """The field book as the importer's own reader reads it.

        The same function the import algorithm calls, on the same rows, with
        the level and the defaults the algorithm resolves from its parameters.

        Raises:
            ValidationError: :meth:`emit`'s refusals.
            GeoCompError: the reader's, for a book it cannot read at all.
        """
        emission = self.emit()
        return read_level_book(
            [list(row) for row in emission.rows],
            emission.mapping(stadia_factor),
            level=level,
            defaults=defaults,
        )

    def check(
        self,
        *,
        level: LevelProfile | None = None,
        defaults: StochasticDefaults | None = None,
        stadia_factor: float = 100.0,
    ) -> LevelCheck:
        """Everything wrong with the field book as it stands, in one pass (FR-012).

        Cells that cannot be read are reported as such, and their rows kept
        from the reader; every other row is read by the importer's reader.
        """
        problems = self.problems()
        entries = len(self.reading_rows())
        emission = self._emission(skip=frozenset(problem.row for problem in problems))
        if emission.reading_count == 0:
            return LevelCheck(problems=problems, entries=entries)
        try:
            result = read_level_book(
                [list(row) for row in emission.rows],
                emission.mapping(stadia_factor),
                level=level,
                defaults=defaults,
            )
        except GeoCompError as error:
            return LevelCheck(problems=problems, refusal=error, entries=entries)
        return LevelCheck(
            problems=problems,
            findings=result.findings,
            entries=entries,
            setups=len(result.setups),
            lines=len(result.lines),
        )

    # -- benchmarks ------------------------------------------------------

    def known_benchmarks(self) -> dict[str, tuple[str, str]]:
        """The benchmarks, by name: their height and standard deviation as typed, decimal point for a comma.

        The standard deviation is ``""`` for a benchmark held exactly.

        Raises:
            ValidationError: ``benchmarks_unreadable`` while a cell cannot be
                read, ``benchmark_incomplete`` for a row without its name or
                its height, ``benchmark_repeated`` for a name given twice,
                ``benchmark_name_unusable`` for a name holding a character the
                network's list is written with.
        """
        table = self.benchmarks
        problems = table.problems()
        if problems:
            raise ValidationError("benchmarks_unreadable", count=len(problems))
        known: dict[str, tuple[str, str]] = {}
        for row in table.filled_rows():
            name, height = table.cell(row, "name"), table.cell(row, "height")
            if not name or not height:
                raise ValidationError("benchmark_incomplete", row=row + 1)
            if any(mark in name for mark in _BENCHMARK_SEPARATORS):
                raise ValidationError(
                    "benchmark_name_unusable", name=name, marks=" ".join(_BENCHMARK_SEPARATORS)
                )
            if name in known:
                raise ValidationError("benchmark_repeated", name=name)
            known[name] = (_typed_number(height), _typed_number(table.cell(row, "sigma")))
        return known

    def benchmarks_text(self) -> str:
        """The benchmarks as the network algorithm's ``BENCHMARKS`` parameter takes them.

        ``BM1=100.000, BM2=103.750±0.002``: each height as typed, and a standard
        deviation where one was typed, to hold that benchmark with a weight.

        Raises:
            ValidationError: :meth:`known_benchmarks`'s refusals.
        """
        return ", ".join(
            f"{name}={height}±{sigma}" if sigma and parse_number(sigma) > 0.0 else f"{name}={height}"
            for name, (height, sigma) in self.known_benchmarks().items()
        )


def _sight(table: TypedTable, row: int) -> str:
    """The kind of sight a row types, or ``""`` for none that can be read: a cell problem."""
    text = table.cell(row, "sight")
    try:
        return table.column("sight").choice(text) if text else ""
    except ValidationError:
        return ""


def _typed_number(text: str) -> str:
    """A typed number as the file carries it: as typed, with a decimal point for a comma.

    The digits are kept: they are the precision a sight distance was written
    to, which the importer reads when nothing else gives it one.
    """
    return text.strip().replace(",", ".")


# -- the chains the windows run (FR-011) -------------------------------------


def _options(job: Job, window: str, names: Sequence[str]) -> dict[str, Any]:
    """What the user set in *window*, of the parameters it may set.

    A parameter never touched is left out, and the algorithm takes its own
    default -- the one the toolbox dialog would show.
    """
    chosen = job.parameters(window)
    return {name: chosen[name] for name in names if name in chosen and chosen[name] is not None}


def _import_step(book: LevellingBook) -> ChainStep:
    emission = book.emit()
    return ChainStep(
        key="import",
        algorithm=IMPORT,
        parameters={
            **_options(book.job, WINDOW_FIELD_BOOK, IMPORT_OPTIONS),
            "BOOK": InputFile("book.csv", emission.csv_text()),
            "MAPPING": InputFile("mapping.json", emission.mapping_text()),
        },
        outputs={"OUTPUT_SETUPS": "setups.json", "OUTPUT_HTML": "report.html"},
    )


def _equal_step(book: LevellingBook) -> ChainStep:
    # One instrument per job: the level chosen in the field book window is the
    # one every reduction corrects with.
    return ChainStep(
        key="equal",
        algorithm=EQUAL,
        parameters={
            **_options(book.job, WINDOW_FIELD_BOOK, INSTRUMENT),
            **_options(book.job, WINDOW_EQUAL, EQUAL_OPTIONS),
            "SETUPS": Ref("import", "OUTPUT_SETUPS"),
        },
        outputs={
            "OUTPUT_REDUCTIONS": "reduced.json",
            "OUTPUT_HTML": "report.html",
            "OUTPUT_CSV": "lines.csv",
        },
    )


def import_chain(book: LevellingBook) -> Chain:
    """What the *Levelling field book* window runs: the import, on the typed book.

    Raises:
        ValidationError: :meth:`LevellingBook.emit`'s refusals.
    """
    return Chain((_import_step(book),))


def equal_chain(book: LevellingBook) -> Chain:
    """What *Equal sights* runs: the import, then the reduction of each line.

    Raises:
        ValidationError: :meth:`LevellingBook.emit`'s refusals.
    """
    return Chain((_import_step(book), _equal_step(book)))


def equidistant_chain(book: LevellingBook) -> Chain:
    """What *Equidistant sights* runs: the import, then the reciprocal crossings.

    Raises:
        ValidationError: :meth:`LevellingBook.emit`'s refusals.
    """
    return Chain(
        (
            _import_step(book),
            ChainStep(
                key="equidistant",
                algorithm=EQUIDISTANT,
                parameters={
                    **_options(book.job, WINDOW_EQUIDISTANT, EQUIDISTANT_OPTIONS),
                    "SETUPS": Ref("import", "OUTPUT_SETUPS"),
                },
                outputs={
                    "OUTPUT_DIFFERENCES": "differences.json",
                    "OUTPUT_HTML": "report.html",
                    "OUTPUT_CSV": "crossings.csv",
                },
            ),
        )
    )


def extreme_chain(book: LevellingBook) -> Chain:
    """What *Extreme sights* runs: the import, then each setup's correlated differences.

    Raises:
        ValidationError: :meth:`LevellingBook.emit`'s refusals.
    """
    return Chain(
        (
            _import_step(book),
            ChainStep(
                key="extreme",
                algorithm=EXTREME,
                parameters={
                    **_options(book.job, WINDOW_FIELD_BOOK, INSTRUMENT),
                    **_options(book.job, WINDOW_EXTREME, EXTREME_OPTIONS),
                    "SETUPS": Ref("import", "OUTPUT_SETUPS"),
                },
                outputs={
                    "OUTPUT_DIFFERENCES": "differences.json",
                    "OUTPUT_HTML": "report.html",
                    "OUTPUT_CSV": "differences.csv",
                },
            ),
        )
    )


def closures_chain(book: LevellingBook) -> Chain:
    """What *Closures and tolerances* runs: the import, the reduction, the closure.

    Raises:
        ValidationError: :meth:`LevellingBook.emit`'s refusals.
    """
    return Chain(
        (
            _import_step(book),
            _equal_step(book),
            ChainStep(
                key="closures",
                algorithm=CLOSURES,
                parameters={
                    **_options(book.job, WINDOW_CLOSURES, CLOSURE_OPTIONS),
                    "REDUCTIONS": Ref("equal", "OUTPUT_REDUCTIONS"),
                },
                outputs={
                    "OUTPUT_CLOSURES": "closure.json",
                    "OUTPUT_HTML": "report.html",
                    "OUTPUT_CSV": "distribution.csv",
                },
            ),
        )
    )


def network_chain(book: LevellingBook) -> Chain:
    """What *Levelling network adjustment* runs: the import, the reduction, the adjustment.

    The benchmarks are the job's, written as the algorithm's list. A free
    network is given none, as the algorithm would ignore them.

    Raises:
        ValidationError: :meth:`LevellingBook.emit`'s refusals, and those of
            :meth:`LevellingBook.known_benchmarks`.
    """
    options = _options(book.job, WINDOW_NETWORK, NETWORK_OPTIONS)
    if not options.get("FREE"):
        benchmarks = book.benchmarks_text()
        if benchmarks:
            options["BENCHMARKS"] = benchmarks
    return Chain(
        (
            _import_step(book),
            _equal_step(book),
            ChainStep(
                key="network",
                algorithm=NETWORK,
                parameters={**options, "REDUCTIONS": Ref("equal", "OUTPUT_REDUCTIONS")},
                outputs={
                    "OUTPUT_SOLUTION": "solution.json",
                    "OUTPUT_HTML": "report.html",
                    "OUTPUT_CSV": "heights.csv",
                    "OUTPUT_NETWORK": "network.json",
                },
            ),
        )
    )
