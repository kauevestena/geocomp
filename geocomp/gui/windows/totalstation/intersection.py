# SPDX-License-Identifier: GPL-2.0-or-later
"""Total Station ▸ Forward intersection, on typed sightings (FR-011, FR-017).

``specs/15-ui-menu-and-settings.md`` section 7.2. Four steps:

1. **Known stations** -- the job's known points: where the stations the point
   was sighted from stand.
2. **Sightings** -- the point's name, and the azimuth observed to it from each
   station, typed in the job's angle convention; the azimuth precision.
3. **Calculate** -- runs ``geocomp:totalstation_intersection``.
4. **Results** -- the point with its error ellipse, the algorithm's report, and
   the rays drawn on the map.

**The one Total Station window that does not read the field book.** The
algorithm takes *oriented* stations -- an azimuth to the point from each, not a
circle reading -- and turning a reading into an azimuth needs the setup's
orientation, which is a computation, and so not the window's to make. Where the
orientation is unknown the station is resected first, as the algorithm's own
help says.
"""

from __future__ import annotations

import json
from typing import Any

from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtWidgets import QLabel, QVBoxLayout, QWidget

from geocomp.algorithms.display import display_format
from geocomp.core.errors import GeoCompError
from geocomp.core.number_format import localised
from geocomp.gui.windows.totalstation.common import TotalStationWindow
from geocomp.gui.workbench.grid import GridWidget
from geocomp.gui.workbench.layers import add_points_layer
from geocomp.gui.workbench.parameters import ParameterForm
from geocomp.gui.workbench.window import DONE, Note, Step
from geocomp.jobs import total_station as ts
from geocomp.jobs.chains import Chain
from geocomp.services.messages import message_for

__all__ = ["IntersectionWindow"]

_TR_CONTEXT = "GeoCompTotalStationWindows"


def _tr(text: str) -> str:
    return QCoreApplication.translate(_TR_CONTEXT, text)


class IntersectionWindow(TotalStationWindow):
    """Fix a point from the azimuths observed to it from two or more known stations."""

    NEEDS_USABLE_BOOK = False
    REPORT = ("intersection", "OUTPUT_HTML")

    def build(self) -> None:
        """The known stations and the sightings, then the run and its results."""
        self.add_step(
            Step(
                "stations",
                _tr("Known stations"),
                self.known_points_page(
                    _tr(
                        "Give the coordinates of the stations the point was sighted from. No "
                        "height is needed. Traverse and Resection can add the stations they "
                        "computed."
                    )
                ),
                problem=self._stations_problem,
                notes=self.points_notes,
            )
        )
        self.add_step(
            Step(
                "sightings",
                _tr("Sightings"),
                self._sightings_page(),
                problem=self._sightings_problem,
                notes=self._sightings_notes,
            )
        )
        self.add_run_steps(_tr("Calculate"), _tr("Results"))
        self.results.add_action(
            _tr("Use as a known point"),
            self.use_as_known_point,
            _tr(
                "Add the intersected point to the job's known points, for the other windows to "
                "start from. An intersection gives no height: type it there."
            ),
        )
        self.results.add_action(
            _tr("Add the point to the map"),
            self.add_to_map,
            _tr("Add the intersected point to the project as a point layer."),
        )

    def chain(self) -> Chain:
        """The intersection of the sightings typed."""
        return ts.intersection_chain(self.book)

    def _options(self) -> dict[str, Any]:
        return self.job.parameters(ts.WINDOW_INTERSECTION)

    # -- step 1: the known stations ------------------------------------------------

    def _stations_problem(self) -> str:
        try:
            self.book.known_positions()
        except GeoCompError as error:
            return message_for(error)
        return ""

    # -- step 2: the sightings -----------------------------------------------------------

    def _sightings_page(self) -> QWidget:
        page = QWidget(self)
        self.target_form = ParameterForm(ts.INTERSECTION, ("TARGET",), self._options, parent=page)
        self.target_form.changed.connect(lambda _name="": self.touch())
        self.sightings_grid = GridWidget(
            self.book.sightings, self.heading, lambda: self.book.angle_typing, page
        )
        self.sightings_grid.edited.connect(self.touch)
        self.precision_form = ParameterForm(
            ts.INTERSECTION, ("SIGMA_AZIMUTH", "CONFIDENCE"), self._options, parent=page
        )
        self.precision_form.changed.connect(lambda _name="": self.touch())
        note = QLabel(
            _tr(
                "One row per station: the azimuth observed from it to the point, clockwise "
                "from north, in the job's angle convention. An azimuth, not a circle reading: "
                "a station whose orientation is not known is resected first."
            ),
            page,
        )
        note.setWordWrap(True)
        layout = QVBoxLayout(page)
        layout.addWidget(self.target_form)
        layout.addWidget(note)
        layout.addWidget(self.sightings_grid, 1)
        layout.addWidget(self.precision_form)
        return page

    def _sightings_problem(self) -> str:
        try:
            observed = self.book.observed_azimuths()
            known = self.book.known_positions()
        except GeoCompError as error:
            return message_for(error)
        unknown = [station for station in observed if station not in known]
        if unknown:
            return _tr(
                "These stations have a sighting but no coordinates; add them to the known "
                "stations: %1."
            ).replace("%1", ", ".join(unknown))
        if len(observed) < 2:
            return _tr(
                "Give the azimuth to the point from at least two stations: one ray fixes no "
                "point."
            )
        return ""

    def _sightings_notes(self) -> list[Note]:
        return [
            self.cell_note(ts.SIGHTINGS, problem)
            for problem in self.book.sightings.problems(self.book.angle_typing)
        ]

    def note_chosen(self, note: Note) -> None:
        """Go to the row a line of the strip is about."""
        grids = {ts.POINTS: self.points_grid, ts.SIGHTINGS: self.sightings_grid}
        grid = grids.get(note.table)
        if grid is not None and note.row is not None:
            table = self.job.tables[note.table]
            grid.select_row(note.row, table.index_of(note.column) if note.column else 0)

    # -- results ---------------------------------------------------------------------------

    def figures(self, scalars: dict[str, Any]) -> list[tuple[str, str]]:
        """The point's coordinates, its error ellipse, and whether the geometry is weak."""
        shown = display_format()

        def millimetres(key: str) -> str:
            value = scalars.get(key)
            return "" if value is None else localised(f"{float(value) * 1000.0:.1f}") + " mm"

        def coordinate(key: str) -> str:
            value = scalars.get(key)
            return "" if value is None else shown.coordinate(float(value)) + " m"

        weak = scalars.get("intersection.WEAK_GEOMETRY")
        return [
            (_tr("Easting"), coordinate("intersection.EASTING")),
            (_tr("Northing"), coordinate("intersection.NORTHING")),
            (_tr("Semi-major axis"), millimetres("intersection.SEMI_MAJOR")),
            (_tr("Semi-minor axis"), millimetres("intersection.SEMI_MINOR")),
            (
                _tr("Weak geometry"),
                "" if weak is None else _tr("Yes: see the report") if weak else _tr("No"),
            ),
        ]

    def position(self) -> tuple[str, float, float, float] | None:
        """The point the last run fixed, as its position document gives it."""
        path = self.output_path("intersection", "OUTPUT_POSITION")
        if path is None:
            return None
        for name, values in json.loads(path.read_text(encoding="utf-8")).items():
            return str(name), float(values[0]), float(values[1]), float(values[2])
        return None

    def use_as_known_point(self) -> bool:
        """Write the intersected point into the job's known points. Returns whether there was one."""
        position = self.position()
        if position is None:
            return False
        self.keep_point(*position, origin="intersection")
        return True

    def add_to_map(self) -> None:
        """Add the intersected point to the project as a point layer."""
        position = self.position()
        if position is None:
            return
        name, easting, northing, _up = position
        add_points_layer(
            _tr("Intersected point (%1)").replace("%1", self.job.name or _tr("untitled job")),
            self.job.crs,
            [{"name": name, "easting": easting, "northing": northing, "origin": "intersection"}],
        )

    def draw(self) -> None:
        """The known stations, and the point fixed with the ray to it from each station."""
        known = self.placed_points()
        for easting, northing in known.values():
            self.sketch.add_point(easting, northing)
        if self.step("calculate").state != DONE:
            return
        position = self.position()
        if position is None:
            return
        _name, easting, northing, _up = position
        self.sketch.add_point(easting, northing, computed=True)
        try:
            stations = self.book.observed_azimuths()
        except GeoCompError:
            return
        for station in stations:
            if station in known:
                self.sketch.add_line([known[station], (easting, northing)])

    def reload_pages(self) -> None:
        """Another job is the current one: show its points, sightings and options."""
        self.points_grid.set_table(self.book.points)
        self.sightings_grid.set_table(self.book.sightings)
        self.target_form.reload()
        self.precision_form.reload()

    def refresh(self) -> None:
        """Also re-read the tables when another window changed them."""
        if hasattr(self, "sightings_grid"):
            self.points_grid.reload()
            self.sightings_grid.reload()
        super().refresh()
