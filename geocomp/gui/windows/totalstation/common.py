# SPDX-License-Identifier: GPL-2.0-or-later
"""What the Total Station windows share: the field book's reading, its headings, the known points.

The book is read once per state of the job by :class:`~geocomp.gui.windows.book.BookWindow`,
which the Level windows share; what is the total station's own is here -- the
importer, the profile library and the default precisions it is run with, the
headings in the job's angle conventions, and the known points several windows
type, pick and fill.
"""

from __future__ import annotations

from typing import Any

from qgis.core import QgsProcessingException
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from geocomp.algorithms.totalstation.common import load_profiles, stochastic_defaults
from geocomp.core.errors import GeoCompError
from geocomp.core.findings import Finding
from geocomp.gui.windows.book import BookWindow
from geocomp.gui.workbench.grid import GridWidget
from geocomp.gui.workbench.parameters import ParameterForm
from geocomp.gui.workbench.window import Note
from geocomp.jobs import total_station as ts
from geocomp.jobs.angles import AngleTyping
from geocomp.jobs.tables import Column, parse_number

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


class TotalStationWindow(BookWindow):
    """A window over the total-station job."""

    FIELD_BOOK_WINDOW = ts.WINDOW_FIELD_BOOK
    FIELD_BOOK_TABLE = ts.FIELD_BOOK
    IMPORT_ALGORITHM = ts.IMPORT
    IMPORT_OPTIONS = ts.IMPORT_OPTIONS

    def banner_action_label(self) -> str:
        """A problem with the field book is put right in the Field book window."""
        return _tr("Open the field book")

    @property
    def book(self) -> ts.TotalStationBook:
        """The current job, read as a field book."""
        return ts.TotalStationBook(self.job)

    def heading(self, column: Column) -> str:
        """A column's heading in the job's conventions."""
        book = self.book
        return column_heading(column, book.angle_typing, book.vertical)

    def read_book(self, options: dict[str, Any]) -> tuple[ts.BookCheck, str]:
        """The book as the import reads it, with the profile library and default precisions given."""
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
        return self.book.check(library=library, defaults=defaults), refusal

    def typed_finding(self, finding: Finding) -> tuple[Finding, int | None]:
        """The finding renumbered for the grid, and its row counted from zero."""
        typed = ts.as_typed(finding)
        row = typed.context.get("row") if typed.context else None
        return typed, int(row) - 1 if row is not None and str(row).isdigit() else None

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
