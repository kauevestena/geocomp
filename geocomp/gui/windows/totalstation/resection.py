# SPDX-License-Identifier: GPL-2.0-or-later
"""Total Station ▸ Resection, on the typed field book (FR-011, FR-017).

``specs/15-ui-menu-and-settings.md`` section 7.2. Four steps:

1. **Occupied station** -- the station to fix, chosen from those the field book
   occupies, with the points it sighted; and, in Advanced mode, a position to
   start the iteration from, typed or picked on the map.
2. **Known points** -- the job's known points, of which the station must have
   sighted at least three.
3. **Calculate** -- runs the import, the pre-processing and
   ``geocomp:totalstation_resection``.
4. **Results** -- the station's coordinates with their standard deviations, the
   setup's orientation, the algorithm's report, and the rays drawn on the map.

The danger circle is the algorithm's to detect, and its refusal is shown in its
words: a window that judged the geometry itself would be a second
implementation of the one check that matters most here.
"""

from __future__ import annotations

import json
import math
from typing import Any

from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtWidgets import (
    QComboBox,
    QFormLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from geocomp.algorithms.display import display_format
from geocomp.core.errors import GeoCompError
from geocomp.core.number_format import localised
from geocomp.gui.windows.totalstation.common import TotalStationWindow
from geocomp.gui.workbench.layers import add_points_layer
from geocomp.gui.workbench.parameters import ParameterForm
from geocomp.gui.workbench.window import DONE, INFO, Note, Step
from geocomp.jobs import total_station as ts
from geocomp.jobs.chains import Chain
from geocomp.services.messages import message_for

__all__ = ["ResectionWindow"]

_TR_CONTEXT = "GeoCompTotalStationWindows"

#: Directions to fewer known points fix no position and orientation together.
_MINIMUM = 3


def _tr(text: str) -> str:
    return QCoreApplication.translate(_TR_CONTEXT, text)


class ResectionWindow(TotalStationWindow):
    """Fix the occupied station from directions it observed to known points."""

    REPORT = ("resection", "OUTPUT_HTML")

    def build(self) -> None:
        """The station and the known points, then the run and its results."""
        self.add_step(
            Step(
                "station",
                _tr("Occupied station"),
                self._station_page(),
                problem=self._station_problem,
            )
        )
        self.add_step(
            Step(
                "known",
                _tr("Known points"),
                self.known_points_page(
                    _tr(
                        "Give the coordinates of at least three of the points the station "
                        "sighted; more give residuals. No height is needed. Traverse, 3D "
                        "radiation and Forward intersection share these points."
                    )
                ),
                problem=self._known_problem,
                notes=self._known_notes,
            )
        )
        self.add_run_steps(_tr("Calculate"), _tr("Results"))
        self.results.add_action(
            _tr("Use as a known point"),
            self.use_as_known_point,
            _tr(
                "Add the resected station to the job's known points, for the other windows to "
                "start from. A resection gives no height: type it there."
            ),
        )
        self.results.add_action(
            _tr("Add the station to the map"),
            self.add_to_map,
            _tr("Add the resected station to the project as a point layer."),
        )
        self._load_stations()

    def chain(self) -> Chain:
        """The import, the pre-processing, and the resection of the station chosen."""
        return ts.resection_chain(self.book)

    def _options(self) -> dict[str, Any]:
        return self.job.parameters(ts.WINDOW_RESECTION)

    # -- step 1: the occupied station ------------------------------------------------

    def _station_page(self) -> QWidget:
        page = QWidget(self)
        self.station_combo = QComboBox(page)
        self.station_combo.setObjectName("geocompResectionStation")
        self.station_combo.setEditable(True)
        self.station_combo.currentTextChanged.connect(self._station_changed)
        self.sighted_label = QLabel(page)
        self.sighted_label.setWordWrap(True)
        self.approximate_form = ParameterForm(
            ts.RESECTION, ("APPROX_EASTING", "APPROX_NORTHING"), self._options, parent=page
        )
        self.approximate_form.changed.connect(lambda _name="": self.touch())
        self.pick_button = QPushButton(_tr("Pick the approximate position on the map"), page)
        self.pick_button.clicked.connect(
            lambda _checked=False: self.pick_into(
                self.approximate_form, "APPROX_EASTING", "APPROX_NORTHING"
            )
        )
        # Advanced in the algorithm, and so here: in Basic mode the iteration
        # starts from the known points' centroid, which converges from inside.
        self.pick_button.setVisible(bool(self.approximate_form.names))
        form = QFormLayout()
        form.addRow(self.approximate_form.label("STATION"), self.station_combo)
        layout = QVBoxLayout(page)
        layout.addLayout(form)
        layout.addWidget(self.sighted_label)
        layout.addWidget(self.approximate_form)
        layout.addWidget(self.pick_button)
        layout.addStretch(1)
        return page

    def station(self) -> str:
        """The station to resect, as the algorithm's ``STATION`` parameter holds it."""
        return str(self._options().get("STATION") or "").strip()

    def set_station(self, station: str) -> None:
        """Make *station* the one to resect."""
        options = self._options()
        if station.strip():
            options["STATION"] = station.strip()
        else:
            options.pop("STATION", None)
        self._load_stations()
        self.touch()

    def _load_stations(self) -> None:
        """Set the station step's widgets from the job and the field book."""
        self._loading = True
        try:
            self.station_combo.clear()
            self.station_combo.addItems(self.book.stations())
            self.station_combo.setCurrentText(self.station())
        finally:
            self._loading = False
        self._show_sighted()

    def _station_changed(self, text: str) -> None:
        if not getattr(self, "_loading", False) and text.strip() != self.station():
            self.set_station(text)

    def _show_sighted(self) -> None:
        station = self.station()
        sighted = self.book.targets(station) if station else ()
        self.sighted_label.setText(
            _tr("Sighted from '%1': %2.").replace("%1", station).replace("%2", ", ".join(sighted))
            if sighted
            else ""
        )

    def _station_problem(self) -> str:
        station = self.station()
        if not station:
            return _tr("Choose the station the instrument occupied: the one to resect.")
        if station not in self.book.stations():
            return _tr("The field book has no setup at '%1'. Choose one of its stations.").replace(
                "%1", station
            )
        sighted = self.book.targets(station)
        if len(sighted) < _MINIMUM:
            return (
                _tr(
                    "Station '%1' sighted %2 point(s). A resection needs directions to at "
                    "least three known points: choose a station that sighted three."
                )
                .replace("%1", station)
                .replace("%2", str(len(sighted)))
            )
        return ""

    # -- step 2: the known points ------------------------------------------------------

    def _known_problem(self) -> str:
        try:
            known = self.book.known_positions()
        except GeoCompError as error:
            return message_for(error)
        station = self.station()
        sighted = [target for target in self.book.targets(station) if target != station]
        placed = [target for target in sighted if target in known]
        if len(placed) < _MINIMUM:
            return (
                _tr(
                    "Only %1 of the points '%2' sighted are known. Give the coordinates of at "
                    "least three of: %3."
                )
                .replace("%1", str(len(placed)))
                .replace("%2", station)
                .replace("%3", ", ".join(sighted))
            )
        return ""

    def _known_notes(self) -> list[Note]:
        notes = self.points_notes()
        try:
            known = self.book.known_positions()
        except GeoCompError:
            return notes
        station = self.station()
        unknown = [
            target
            for target in self.book.targets(station)
            if target not in known and target != station
        ]
        if unknown and len(self.book.targets(station)) - len(unknown) >= _MINIMUM:
            notes.append(
                Note(INFO, _tr("Sighted but not known, so not used: %1.").replace("%1", ", ".join(unknown)))
            )
        return notes

    def note_chosen(self, note: Note) -> None:
        """Go to the row of the known points a line of the strip is about."""
        if note.table == ts.POINTS and note.row is not None:
            table = self.job.tables[ts.POINTS]
            self.points_grid.select_row(note.row, table.index_of(note.column) if note.column else 0)

    # -- results ---------------------------------------------------------------------

    def figures(self, scalars: dict[str, Any]) -> list[tuple[str, str]]:
        """The station's coordinates, their standard deviations and the setup's orientation."""
        shown = display_format()

        def millimetres(key: str) -> str:
            value = scalars.get(key)
            return "" if value is None else localised(f"{float(value) * 1000.0:.1f}") + " mm"

        def coordinate(key: str) -> str:
            value = scalars.get(key)
            return "" if value is None else shown.coordinate(float(value)) + " m"

        orientation = scalars.get("resection.ORIENTATION")
        return [
            (_tr("Easting"), coordinate("resection.EASTING")),
            (_tr("Northing"), coordinate("resection.NORTHING")),
            (_tr("Standard deviation of the easting"), millimetres("resection.SIGMA_EASTING")),
            (_tr("Standard deviation of the northing"), millimetres("resection.SIGMA_NORTHING")),
            (
                _tr("Setup orientation"),
                "" if orientation is None else shown.angle(math.radians(float(orientation))),
            ),
        ]

    def position(self) -> tuple[str, float, float, float] | None:
        """The station the last run fixed, as its position document gives it."""
        path = self.output_path("resection", "OUTPUT_POSITION")
        if path is None:
            return None
        for name, values in json.loads(path.read_text(encoding="utf-8")).items():
            return str(name), float(values[0]), float(values[1]), float(values[2])
        return None

    def use_as_known_point(self) -> bool:
        """Write the resected station into the job's known points. Returns whether there was one."""
        position = self.position()
        if position is None:
            return False
        self.keep_point(*position, origin="resection")
        return True

    def add_to_map(self) -> None:
        """Add the resected station to the project as a point layer."""
        position = self.position()
        if position is None:
            return
        name, easting, northing, _up = position
        scalars = self.scalars()
        add_points_layer(
            _tr("Resected station (%1)").replace("%1", self.job.name or _tr("untitled job")),
            self.job.crs,
            [
                {
                    "name": name,
                    "easting": easting,
                    "northing": northing,
                    "origin": "resection",
                    "sigma_e": scalars.get("resection.SIGMA_EASTING"),
                    "sigma_n": scalars.get("resection.SIGMA_NORTHING"),
                }
            ],
        )

    def draw(self) -> None:
        """The known points, and the station fixed with a ray to each known point it sighted."""
        known = self.placed_points()
        for easting, northing in known.values():
            self.sketch.add_point(easting, northing)
        if self.step("calculate").state != DONE:
            return
        position = self.position()
        if position is None:
            return
        name, easting, northing, _up = position
        self.sketch.add_point(easting, northing, computed=True)
        for target in self.book.targets(name):
            if target in known and target != name:
                self.sketch.add_line([(easting, northing), known[target]])

    def reload_pages(self) -> None:
        """Another job is the current one: show its station, points and options."""
        self._load_stations()
        self.points_grid.set_table(self.book.points)
        self.approximate_form.reload()

    def refresh(self) -> None:
        """Also offer the stations the field book occupies now."""
        if hasattr(self, "station_combo"):
            stations = list(self.book.stations())
            if [self.station_combo.itemText(i) for i in range(self.station_combo.count())] != stations:
                self._load_stations()
            else:
                self._show_sighted()
            self.points_grid.reload()
        super().refresh()
