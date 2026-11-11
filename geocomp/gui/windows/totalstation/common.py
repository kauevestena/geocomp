# SPDX-License-Identifier: GPL-2.0-or-later
"""What the Total Station windows share: the field book, read once, and its headings.

Every window of the technique works from the same typed field book, and each
needs to know the same thing about it before it can do anything: whether it
can be read. :class:`TotalStationWindow` asks once per state of the job --
with the importer's own reader, the profile library and the default precisions
the import algorithm would be run with -- and the windows show what it found.

A computation window does not let its algorithms loose on a book with a row
the importer rejects: the toolbox carries on past a rejected record because a
file is what it is, but a typed row is one keystroke from being right, and a
traverse computed around a missing leg is not what anyone meant.
"""

from __future__ import annotations

from typing import Any

from qgis.core import NULL, QgsApplication, QgsProcessingException
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from geocomp.algorithms.totalstation.common import load_profiles, stochastic_defaults
from geocomp.core.errors import GeoCompError
from geocomp.gui.workbench.grid import GridWidget
from geocomp.gui.workbench.parameters import ParameterForm
from geocomp.gui.workbench.window import BLOCKING, INFO, WARNING, Note, Workbench
from geocomp.jobs import total_station as ts
from geocomp.jobs.angles import AngleTyping
from geocomp.jobs.chains import fingerprint
from geocomp.jobs.tables import CellProblem, Column, parse_number
from geocomp.services.messages import finding_text, message_for

__all__ = ["TotalStationWindow", "column_heading", "typing_label", "vertical_label"]

_TR_CONTEXT = "GeoCompTotalStationWindows"


def _tr(text: str) -> str:
    return QCoreApplication.translate(_TR_CONTEXT, text)


def typing_label(typing: AngleTyping) -> str:
    """How a convention is named where it is chosen."""
    return {
        AngleTyping.DMS: _tr("Degrees, minutes and seconds, separated (87 31 15)"),
        AngleTyping.DMS_PACKED: _tr("Degrees.minutes-seconds, DDD.MMSS (87.3115)"),
        AngleTyping.DECIMAL_DEGREES: _tr("Decimal degrees (87.520833)"),
        AngleTyping.GON: _tr("Gon (97.245370)"),
    }[typing]


def _typing_mark(typing: AngleTyping) -> str:
    """How a convention is named in a column heading, where there is no room."""
    return {
        AngleTyping.DMS: _tr("D M S"),
        AngleTyping.DMS_PACKED: _tr("DDD.MMSS"),
        AngleTyping.DECIMAL_DEGREES: _tr("decimal °"),
        AngleTyping.GON: _tr("gon"),
    }[typing]


def vertical_label(vertical: ts.VerticalAngle) -> str:
    """How a vertical-circle convention is named where it is chosen."""
    return {
        ts.VerticalAngle.ZENITH: _tr("Zenith angle (90° is level)"),
        ts.VerticalAngle.ELEVATION: _tr("Vertical angle from the horizon (0° is level)"),
    }[vertical]


def column_heading(column: Column, typing: AngleTyping, vertical: ts.VerticalAngle) -> str:
    """A grid column's heading, stating the unit or the convention its cells are read in."""
    mark = _typing_mark(typing)
    headings = {
        "station": _tr("Station"),
        "instrument_height": _tr("Instr. height (m)"),
        "target": _tr("Target"),
        "face": _tr("Face (PD / PI)"),
        "horizontal": _tr("Hz (%1)").replace("%1", mark),
        "vertical": (
            _tr("Zenith (%1)") if vertical is ts.VerticalAngle.ZENITH else _tr("Vertical (%1)")
        ).replace("%1", mark),
        "distance": _tr("Slope distance (m)"),
        "target_height": _tr("Target height (m)"),
        "set_number": _tr("Set"),
        "note": _tr("Note"),
        "name": _tr("Point"),
        "easting": _tr("Easting (m)"),
        "northing": _tr("Northing (m)"),
        "height": _tr("Height (m)"),
        "origin": _tr("Origin"),
        "azimuth": _tr("Azimuth (%1)").replace("%1", mark),
    }
    return headings.get(column.key, column.key)


class TotalStationWindow(Workbench):
    """A window over the total-station job."""

    #: Whether the window computes from the field book, and so needs it usable.
    NEEDS_USABLE_BOOK = True

    def __init__(self, *arguments: Any, **options: Any) -> None:
        self._checked: tuple[str, ts.BookCheck, str] | None = None
        super().__init__(*arguments, **options)

    def banner_action_label(self) -> str:
        """A problem with the field book is put right in the Field book window."""
        return _tr("Open the field book")

    def banner_action(self) -> None:
        """Bring the Field book window forward."""
        self.open_field_book()

    @property
    def book(self) -> ts.TotalStationBook:
        """The current job, read as a field book."""
        return ts.TotalStationBook(self.job)

    def heading(self, column: Column) -> str:
        """A column's heading in the job's conventions."""
        book = self.book
        return column_heading(column, book.angle_typing, book.vertical)

    def open_field_book(self) -> None:
        """Bring the Field book window forward, to put right what it shows."""
        if self._open_window is not None:
            self._open_window(ts.WINDOW_FIELD_BOOK)

    # -- the field book, read once per state of the job -----------------------

    def import_option(self, name: str) -> Any:
        """What the import will be run with for *name*: the job's choice, or the algorithm's default."""
        chosen = self.job.parameters(ts.WINDOW_FIELD_BOOK).get(name)
        if chosen is not None:
            return chosen
        registered = QgsApplication.processingRegistry().algorithmById(ts.IMPORT)
        if registered is None:
            return None
        # Made afresh, so the default is Global Settings' of the moment, and
        # held while it is read: the definition belongs to the instance.
        algorithm = registered.create({})
        definition = algorithm.parameterDefinition(name)
        value = None if definition is None else definition.defaultValue()
        return None if value is None or value == NULL else value

    def book_check(self) -> tuple[ts.BookCheck, str]:
        """What reading the field book finds, and why its profile library could not be read.

        Read with the importer's own reader, the library and the defaults the
        import algorithm would be given -- so what is shown before a run is
        what the run will find. Kept until the job changes.
        """
        job = self.job
        options = {name: self.import_option(name) for name in ts.IMPORT_OPTIONS}
        state = fingerprint(
            [id(job), job.tables[ts.FIELD_BOOK].revision, dict(job.entry), options]
        )
        if self._checked is not None and self._checked[0] == state:
            return self._checked[1], self._checked[2]
        refusal = ""
        library = None
        try:
            library = load_profiles(str(options["PROFILES"] or ""))
        except QgsProcessingException as error:
            refusal = str(error)
        defaults = stochastic_defaults(
            float(options["SIGMA_DIRECTION"] or 0.0),
            float(options["SIGMA_ZENITH"] or 0.0),
            float(options["SIGMA_DISTANCE"] or 0.0),
        )
        check = self.book.check(library=library, defaults=defaults)
        self._checked = (state, check, refusal)
        return check, refusal

    def book_problem(self, *, rejected_rows_block: bool) -> str:
        """Why the field book cannot be computed from, in one sentence, or ``""``."""
        check, refusal = self.book_check()
        if refusal:
            return refusal
        if check.pointings == 0:
            return _tr(
                "The field book is empty. Type the observations in its grid, or paste them "
                "from a spreadsheet."
            )
        if check.problems:
            return _tr("%1 cell(s) of the field book cannot be read. Correct the cells marked.").replace(
                "%1", str(len(check.problems))
            )
        if check.refusal is not None:
            return message_for(check.refusal)
        if rejected_rows_block and check.blocking:
            return _tr(
                "%1 row(s) of the field book are rejected. Correct them: each is named below."
            ).replace("%1", str(len(check.blocking)))
        return ""

    def precondition(self) -> str:
        """A computation window needs a field book that can be computed from."""
        if not self.NEEDS_USABLE_BOOK:
            return ""
        problem = self.book_problem(rejected_rows_block=True)
        if not problem:
            return ""
        return _tr("%1 Put it right in the Field book window.").replace("%1", problem)

    def book_notes(self) -> list[Note]:
        """Every problem and finding of the field book, each leading to its row."""
        check, _refusal = self.book_check()
        notes = [self.cell_note(ts.FIELD_BOOK, problem) for problem in check.problems]
        for finding in check.findings:
            typed = ts.as_typed(finding)
            row = typed.context.get("row") if typed.context else None
            notes.append(
                Note(
                    {"blocking": BLOCKING, "warning": WARNING}.get(finding.severity.value, INFO),
                    finding_text(typed),
                    table=ts.FIELD_BOOK,
                    row=int(row) - 1 if row is not None and str(row).isdigit() else None,
                )
            )
        return notes

    def cell_note(self, table: str, problem: CellProblem) -> Note:
        """A cell that cannot be read, as a line of the strip naming its row and column."""
        column = self.job.tables[table].column(problem.column)
        return Note(
            BLOCKING,
            _tr("Row %1, %2: %3")
            .replace("%1", str(problem.row + 1))
            .replace("%2", self.heading(column))
            .replace("%3", message_for(problem.error)),
            table=table,
            row=problem.row,
            column=problem.column,
        )

    # -- the known points, which several windows show ---------------------------

    def known_points_page(self, note: str) -> QWidget:
        """The job's known points, typed, pasted or picked on the map, with *note* beneath.

        One table, shared by every window that reads it: a point given in
        *3D radiation* is known to *Resection* too.
        """
        page = QWidget(self)
        self.points_grid = GridWidget(self.book.points, self.heading, parent=page)
        self.points_grid.edited.connect(self.touch)
        self.pick_button = QPushButton(_tr("Pick on the map"), self.points_grid)
        self.pick_button.setToolTip(
            _tr("Click a point on the map to fill the easting and northing of the current row.")
        )
        self.pick_button.clicked.connect(lambda _checked=False: self.pick_station())
        self.points_grid.buttons.insertWidget(self.points_grid.buttons.count() - 1, self.pick_button)
        label = QLabel(note, page)
        label.setWordWrap(True)
        layout = QVBoxLayout(page)
        layout.addWidget(self.points_grid, 1)
        layout.addWidget(label)
        return page

    def pick_station(self) -> None:
        """Take the current row's easting and northing from a click on the map."""
        row = self.points_grid.current_row()

        def picked(x: float, y: float) -> None:
            table = self.book.points
            while table.row_count <= row:
                table.insert_row()
            table.set_cell(row, "easting", f"{x:.4f}")
            table.set_cell(row, "northing", f"{y:.4f}")
            if not table.cell(row, "origin"):
                table.set_cell(row, "origin", _tr("map"))
            self.points_grid.reload()
            self.touch()

        self.pick_point(picked)

    def pick_into(self, form: ParameterForm, easting: str, northing: str) -> None:
        """Take a point from the map into two of the algorithm's parameters."""

        def picked(x: float, y: float) -> None:
            form.set_value(easting, round(x, 4))
            form.set_value(northing, round(y, 4))

        self.pick_point(picked)

    def points_notes(self) -> list[Note]:
        """Each cell of the known points that cannot be read."""
        return [self.cell_note(ts.POINTS, problem) for problem in self.book.points.problems()]

    def placed_points(self) -> dict[str, tuple[float, float]]:
        """The known points whose easting and northing can be read, by name: for the sketch."""
        placed: dict[str, tuple[float, float]] = {}
        table = self.book.points
        for row in table.filled_rows():
            try:
                placed[table.cell(row, "name")] = (
                    parse_number(table.cell(row, "easting")),
                    parse_number(table.cell(row, "northing")),
                )
            except GeoCompError:
                continue
        return placed

    def keep_point(self, name: str, easting: float, northing: float, up: float, origin: str) -> None:
        """Write a computed point into the known points, keeping a height typed for it.

        A plane computation gives no height, and writes zero for one. A height
        already typed for the point is worth more than that zero, so it stays.
        """
        book = self.book
        typed = next(
            (
                book.points.cell(row, "height")
                for row in book.points.filled_rows()
                if book.points.cell(row, "name") == name
            ),
            "",
        )
        try:
            height = parse_number(typed) if typed else up
        except GeoCompError:
            height = up
        book.set_point(name, round(easting, 4), round(northing, 4), height, origin=origin)
        self.touch()
