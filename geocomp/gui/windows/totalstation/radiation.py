# SPDX-License-Identifier: GPL-2.0-or-later
"""Total Station ▸ 3D radiation, on the typed field book (FR-011, FR-014, FR-017).

``specs/15-ui-menu-and-settings.md`` section 7.2. Four steps:

1. **Known stations** -- the points the survey starts from: typed, pasted,
   picked on the map, or taken from a traverse computed in *Traverse*.
2. **Orientations and heights** -- an azimuth for a setup that sighted no known
   point, and the heights the algorithm uses where a reading carries none.
3. **Calculate** -- runs the import, the pre-processing and
   ``geocomp:totalstation_radiation``.
4. **Results** -- every radiated point with its uncertainties, the algorithm's
   report, and the rays drawn on the map.

The known points and the orientations are tables of the job, shared with the
other Total Station windows; the heights and the correlation are the
algorithm's parameters.
"""

from __future__ import annotations

import csv
import json
from typing import Any

from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from geocomp.core.errors import GeoCompError
from geocomp.core.number_format import localised
from geocomp.gui.windows.totalstation.common import TotalStationWindow
from geocomp.gui.workbench.grid import GridWidget
from geocomp.gui.workbench.layers import add_points_layer
from geocomp.gui.workbench.parameters import ParameterForm
from geocomp.gui.workbench.window import DONE, Note, Step
from geocomp.jobs import total_station as ts
from geocomp.jobs.chains import Chain
from geocomp.jobs.tables import parse_number
from geocomp.services.messages import message_for

__all__ = ["RadiationWindow"]

_TR_CONTEXT = "GeoCompTotalStationWindows"


def _tr(text: str) -> str:
    return QCoreApplication.translate(_TR_CONTEXT, text)


class RadiationWindow(TotalStationWindow):
    """Radiate the field book's points from known, oriented stations."""

    REPORT = ("radiation", "OUTPUT_HTML")
    TABLE = ("radiation", "OUTPUT_CSV")

    def build(self) -> None:
        """Known stations, orientations and heights, then the run and its results."""
        self.add_step(
            Step(
                "stations",
                _tr("Known stations"),
                self._stations_page(),
                problem=self._stations_problem,
                notes=self._stations_notes,
            )
        )
        self.add_step(
            Step(
                "orientations",
                _tr("Orientations and heights"),
                self._orientations_page(),
                problem=self._orientations_problem,
                notes=self._orientations_notes,
            )
        )
        self.add_run_steps(_tr("Calculate"), _tr("Results"))
        self.results.add_action(
            _tr("Add points to the map"),
            self.add_to_map,
            _tr("Add the radiated points, with their uncertainties, to the project as a layer."),
        )

    def chain(self) -> Chain:
        """The import, the pre-processing, and the radiation from the known stations."""
        return ts.radiation_chain(self.book)

    # -- step 1: known stations ------------------------------------------------------

    def _stations_page(self) -> QWidget:
        page = QWidget(self)
        self.points_grid = GridWidget(self.book.points, self.heading, parent=page)
        self.points_grid.edited.connect(self.touch)
        self.pick_button = QPushButton(_tr("Pick on the map"), self.points_grid)
        self.pick_button.setToolTip(
            _tr("Click a point on the map to fill the easting and northing of the current row.")
        )
        self.pick_button.clicked.connect(lambda _checked=False: self.pick_station())
        self.points_grid.buttons.insertWidget(self.points_grid.buttons.count() - 1, self.pick_button)
        note = QLabel(
            _tr(
                "Give at least the stations the instrument occupied. A known point the setup "
                "also sighted orients it; Traverse can add the stations it computed."
            ),
            page,
        )
        note.setWordWrap(True)
        layout = QVBoxLayout(page)
        layout.addWidget(self.points_grid, 1)
        layout.addWidget(note)
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

    def _stations_problem(self) -> str:
        try:
            stations = self.book.known_stations()
        except GeoCompError as error:
            return message_for(error)
        occupied = set(self.book.stations())
        if not occupied & set(stations):
            return _tr(
                "None of the known points is a station the field book occupies. Add the "
                "coordinates of at least one: %1."
            ).replace("%1", ", ".join(sorted(occupied)))
        return ""

    def _stations_notes(self) -> list[Note]:
        notes = [self.cell_note(ts.POINTS, problem) for problem in self.book.points.problems()]
        try:
            stations = self.book.known_stations()
        except GeoCompError:
            return notes
        missing = [name for name in self.book.stations() if name not in stations]
        if missing:
            notes.append(
                Note(
                    "info",
                    _tr("Not known, so not radiated from: %1.").replace("%1", ", ".join(missing)),
                )
            )
        return notes

    # -- step 2: orientations and heights ----------------------------------------------

    def _orientations_page(self) -> QWidget:
        page = QWidget(self)
        self.orientations_grid = GridWidget(
            self.book.orientations, self.heading, lambda: self.book.angle_typing, page
        )
        self.orientations_grid.edited.connect(self.touch)
        self.form = ParameterForm(
            ts.RADIATION,
            ts.RADIATION_OPTIONS,
            lambda: self.job.parameters(ts.WINDOW_RADIATION),
            parent=page,
        )
        self.form.changed.connect(lambda _name="": self.touch())
        note = QLabel(
            _tr(
                "An orientation is needed only for a setup that sighted no known point: one "
                "that did is oriented from it. The azimuth is typed in the job's angle "
                "convention. The heights are used where a reading carries none of its own."
            ),
            page,
        )
        note.setWordWrap(True)
        layout = QVBoxLayout(page)
        layout.addWidget(note)
        layout.addWidget(self.orientations_grid, 1)
        layout.addWidget(self.form)
        return page

    def _orientations_problem(self) -> str:
        try:
            self.book.given_orientations()
        except GeoCompError as error:
            return message_for(error)
        return ""

    def _orientations_notes(self) -> list[Note]:
        return [
            self.cell_note(ts.ORIENTATIONS, problem)
            for problem in self.book.orientations.problems(self.book.angle_typing)
        ]

    def note_chosen(self, note: Note) -> None:
        """Go to the row a line of the strip is about."""
        grids = {ts.POINTS: self.points_grid, ts.ORIENTATIONS: self.orientations_grid}
        grid = grids.get(note.table)
        if grid is not None and note.row is not None:
            table = self.job.tables[note.table]
            grid.select_row(note.row, table.index_of(note.column) if note.column else 0)

    # -- results ---------------------------------------------------------------------------

    def figures(self, scalars: dict[str, Any]) -> list[tuple[str, str]]:
        """How many points, and the largest uncertainty among them."""
        worst = scalars.get("radiation.WORST_UNCERTAINTY")
        return [
            (_tr("Points radiated"), str(scalars.get("radiation.POINT_COUNT", ""))),
            (
                _tr("Largest standard deviation"),
                "" if worst is None else localised(f"{float(worst) * 1000.0:.1f}") + " mm",
            ),
        ]

    def radiated(self) -> list[dict[str, Any]]:
        """The points the last run radiated, as the algorithm's table gives them."""
        path = self.output_path("radiation", "OUTPUT_CSV")
        if path is None:
            document = self.output_path("radiation", "OUTPUT_POINTS")
            if document is None:
                return []
            return [
                {"name": name, "easting": v[0], "northing": v[1], "height": v[2], "origin": ""}
                for name, v in json.loads(document.read_text(encoding="utf-8")).items()
            ]
        with open(path, encoding="utf-8", newline="") as handle:
            return [
                {
                    "name": row["point"],
                    "easting": float(row["easting"]),
                    "northing": float(row["northing"]),
                    "height": float(row["up"]),
                    "origin": row["from"],
                    "sigma_e": float(row["sigma_e"]),
                    "sigma_n": float(row["sigma_n"]),
                    "sigma_u": float(row["sigma_u"]),
                }
                for row in csv.DictReader(handle)
            ]

    def add_to_map(self) -> None:
        """Add the radiated points to the project as a point layer."""
        add_points_layer(
            _tr("Radiated points (%1)").replace("%1", self.job.name or _tr("untitled job")),
            self.job.crs,
            self.radiated(),
        )

    def draw(self) -> None:
        """The known stations, and a ray from each to the points it radiated."""
        known: dict[str, tuple[float, float]] = {}
        table = self.book.points
        for row in table.filled_rows():
            try:
                known[table.cell(row, "name")] = (
                    parse_number(table.cell(row, "easting")),
                    parse_number(table.cell(row, "northing")),
                )
            except GeoCompError:
                continue
        for easting, northing in known.values():
            self.sketch.add_point(easting, northing)
        if self.step("calculate").state != DONE:
            return
        for point in self.radiated():
            self.sketch.add_point(point["easting"], point["northing"], computed=True)
            origin = known.get(str(point.get("origin") or ""))
            if origin is not None:
                self.sketch.add_line([origin, (point["easting"], point["northing"])])

    def reload_pages(self) -> None:
        """Another job is the current one: show its points, orientations and options."""
        self.points_grid.set_table(self.book.points)
        self.orientations_grid.set_table(self.book.orientations)
        self.form.reload()

    def refresh(self) -> None:
        """Also re-read the tables when another window changed them."""
        if hasattr(self, "points_grid"):
            self.points_grid.reload()
            self.orientations_grid.reload()
        super().refresh()
