# SPDX-License-Identifier: GPL-2.0-or-later
"""Total Station ▸ Classical network, on the typed field book (FR-011, FR-017).

``specs/15-ui-menu-and-settings.md`` section 7.2. Five steps:

1. **Approximate coordinates** -- the job's known points, which the network is
   linearised about: typed, pasted, picked on the map, or put there by
   *Traverse*, *Resection* or *Forward intersection*.
2. **Datum** -- the dimension, and how the datum defect is removed; the
   stations held, or those the datum is defined over, ticked among the
   network's own rather than typed as a list.
3. **Options** -- the CRS, the reduction to the grid, the confidence level.
4. **Calculate** -- runs the import, the pre-processing and
   ``geocomp:totalstation_network``.
5. **Results** -- the global test, the variance factor and the outlier
   candidates, the adjusted stations, the algorithm's report, the network drawn
   on the map; and the algorithm's own styled result layers, a click away.

Free and constrained are both a tick away, which is the *redes livres e
amarradas* comparison the research project names as a teaching goal: adjust,
change the datum, and watch the result go out of date and come back.
"""

from __future__ import annotations

import csv
import json
from typing import Any

from qgis.core import QgsApplication
from qgis.PyQt.QtCore import QCoreApplication, Qt
from qgis.PyQt.QtWidgets import (
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from geocomp.core.errors import GeoCompError
from geocomp.core.number_format import localised
from geocomp.gui.windows.totalstation.common import TotalStationWindow
from geocomp.gui.workbench.layers import add_result_layers
from geocomp.gui.workbench.parameters import ParameterForm
from geocomp.gui.workbench.window import DONE, INFO, Note, Step
from geocomp.jobs import total_station as ts
from geocomp.jobs.chains import Chain
from geocomp.services.messages import message_for

__all__ = ["NetworkWindow"]

_TR_CONTEXT = "GeoCompTotalStationWindows"

#: The algorithm's ``DIMENSION`` choices: 2D, 3D, 1D, in its order.
_PLANIMETRIC = 0


def _tr(text: str) -> str:
    return QCoreApplication.translate(_TR_CONTEXT, text)


class NetworkWindow(TotalStationWindow):
    """Adjust the typed field book as a network, free or constrained."""

    REPORT = ("network", "OUTPUT_HTML")
    TABLE = ("network", "OUTPUT_STATIONS")

    def build(self) -> None:
        """Approximate coordinates, datum and options, then the run and its results."""
        self.add_step(
            Step(
                "approximate",
                _tr("Approximate coordinates"),
                self.known_points_page(
                    _tr(
                        "Every station of the network needs approximate coordinates, height "
                        "included: they are what the adjustment is linearised about. Traverse, "
                        "Resection and Forward intersection can add the ones they compute."
                    )
                ),
                problem=self._approximate_problem,
                notes=self._approximate_notes,
            )
        )
        self.add_step(
            Step(
                "datum",
                _tr("Datum"),
                self._datum_page(),
                problem=self._datum_problem,
            )
        )
        self.add_step(
            Step("options", _tr("Options"), self._options_page(), problem=self._options_problem)
        )
        self.add_run_steps(_tr("Calculate"), _tr("Results"))
        self.results.add_action(
            _tr("Add result layers to the map"),
            self.add_layers,
            _tr(
                "Add the algorithm's styled layers -- adjusted stations, error ellipses, "
                "residuals, observations, corrections -- to the project, in a group."
            ),
        )
        self.results.add_action(
            _tr("Use as known points"),
            self.use_as_known_points,
            _tr(
                "Write the adjusted coordinates into the job's known points, for 3D radiation "
                "to start from."
            ),
        )
        self._load_stations()

    def chain(self) -> Chain:
        """The import, the pre-processing, and the adjustment of the network."""
        return ts.network_chain(self.book)

    def _options(self) -> dict[str, Any]:
        return self.job.parameters(ts.WINDOW_NETWORK)

    # -- step 1: approximate coordinates -------------------------------------------

    def _approximate_problem(self) -> str:
        try:
            known = self.book.known_stations()
        except GeoCompError as error:
            return message_for(error)
        if not set(known) & set(self.book.stations()):
            return _tr(
                "None of the known points is a station the field book occupies. Give the "
                "approximate coordinates of the stations: %1."
            ).replace("%1", ", ".join(self.book.stations()))
        return ""

    def _approximate_notes(self) -> list[Note]:
        notes = self.points_notes()
        try:
            known = self.book.known_stations()
        except GeoCompError:
            return notes
        left_out = [name for name in self.book.point_names() if name not in known]
        if left_out:
            notes.append(
                Note(
                    INFO,
                    _tr(
                        "Without approximate coordinates, so left out of the network with "
                        "every observation to them: %1."
                    ).replace("%1", ", ".join(left_out)),
                )
            )
        return notes

    def note_chosen(self, note: Note) -> None:
        """Go to the row of the known points a line of the strip is about."""
        if note.table == ts.POINTS and note.row is not None:
            table = self.job.tables[ts.POINTS]
            self.points_grid.select_row(note.row, table.index_of(note.column) if note.column else 0)

    # -- step 2: the datum ---------------------------------------------------------------

    def _datum_page(self) -> QWidget:
        page = QWidget(self)
        self.datum_form = ParameterForm(
            ts.NETWORK, ("DIMENSION", "DATUM"), self._options, parent=page
        )
        self.datum_form.changed.connect(lambda _name="": self._datum_changed())
        self.stations_label = QLabel(page)
        self.stations_label.setWordWrap(True)
        self.stations_list = QListWidget(page)
        self.stations_list.setObjectName("geocompNetworkStations")
        self.stations_list.itemChanged.connect(self._station_ticked)
        layout = QVBoxLayout(page)
        layout.addWidget(self.datum_form)
        layout.addWidget(self.stations_label)
        layout.addWidget(self.stations_list, 1)
        return page

    def datum(self) -> int:
        """The datum definition, as the algorithm's ``DATUM`` parameter numbers it."""
        value = self.datum_form.value("DATUM")
        return ts.DATUM_DEFAULT if value is None else int(value)

    def _listed(self) -> str:
        """The parameter the station list sets under the datum chosen, or ``""`` for none."""
        datum = self.datum()
        if datum in ts.DATUM_HOLDING:
            return "FIXED_STATIONS"
        return "DATUM_STATIONS" if datum == ts.DATUM_MINIMUM else ""

    def ticked(self) -> list[str]:
        """The stations the datum chosen reads, as the algorithm's parameter lists them."""
        listed = self._listed()
        if not listed:
            return []
        return [
            name.strip()
            for name in str(self._options().get(listed) or "").split(",")
            if name.strip()
        ]

    def set_ticked(self, stations: list[str]) -> None:
        """Make *stations* those the datum chosen reads."""
        listed = self._listed()
        if not listed:
            return
        options = self._options()
        if stations:
            options[listed] = ",".join(stations)
        else:
            options.pop(listed, None)
        self._load_stations()
        self.touch()

    def _load_stations(self) -> None:
        """Set the datum step's list from the known points and the choice stored."""
        listed = self._listed()
        ticked = self.ticked()
        self.stations_label.setText(
            _tr("Stations held at their approximate coordinates:")
            if listed == "FIXED_STATIONS"
            else _tr("Stations the datum is defined over; none ticked means all of them:")
            if listed == "DATUM_STATIONS"
            else _tr(
                "A free network: the datum is defined over every station, and none is held."
            )
        )
        self.stations_list.setVisible(bool(listed))
        table = self.book.points
        names = [table.cell(row, "name") for row in table.filled_rows() if table.cell(row, "name")]
        names.extend(name for name in ticked if name not in names)
        self.stations_list.blockSignals(True)
        try:
            self.stations_list.clear()
            for name in dict.fromkeys(names):
                item = QListWidgetItem(name, self.stations_list)
                item.setFlags(
                    Qt.ItemFlag.ItemIsUserCheckable
                    | Qt.ItemFlag.ItemIsEnabled
                    | Qt.ItemFlag.ItemIsSelectable
                )
                item.setCheckState(
                    Qt.CheckState.Checked if name in ticked else Qt.CheckState.Unchecked
                )
        finally:
            self.stations_list.blockSignals(False)

    def _station_ticked(self, _item: QListWidgetItem) -> None:
        self.set_ticked(
            [
                self.stations_list.item(row).text()
                for row in range(self.stations_list.count())
                if self.stations_list.item(row).checkState() == Qt.CheckState.Checked
            ]
        )

    def _datum_changed(self) -> None:
        self._load_stations()
        self.touch()

    def _datum_problem(self) -> str:
        if self._listed() != "FIXED_STATIONS":
            return ""
        ticked = self.ticked()
        if not ticked:
            return _tr("Tick the stations to hold: a constrained network holds at least one.")
        try:
            known = self.book.known_stations()
        except GeoCompError:
            return ""
        missing = [name for name in ticked if name not in known]
        if missing:
            return _tr(
                "These stations are held but have no approximate coordinates; add them or "
                "untick them: %1."
            ).replace("%1", ", ".join(missing))
        return ""

    # -- step 3: options -------------------------------------------------------------------

    def _options_page(self) -> QWidget:
        page = QWidget(self)
        self.options_form = ParameterForm(
            ts.NETWORK,
            ("CRS", "REDUCE_TO_GRID", "GEOID_UNDULATION", "CONFIDENCE", "EPOCH", "EXAGGERATION"),
            self._options,
            defaults=lambda: {"CRS": self.job.crs or None},
            parent=page,
        )
        self.options_form.changed.connect(lambda _name="": self.touch())
        note = QLabel(
            _tr(
                "These are the algorithm's own parameters. The CRS is the job's, chosen in the "
                "Field book window, unless another is typed here; a job on a local plane takes "
                "the algorithm's default."
            ),
            page,
        )
        note.setWordWrap(True)
        layout = QVBoxLayout(page)
        layout.addWidget(self.options_form)
        layout.addWidget(note)
        layout.addStretch(1)
        return page

    def _options_problem(self) -> str:
        if str(self.options_form.value("CRS") or "").strip():
            return ""
        return _tr(
            "Give the CRS the network is adjusted in, such as EPSG:31982: the job is on a local "
            "plane and Global Settings names no preferred CRS. For a survey with no datum, "
            "give the projected CRS of the area it lies in."
        )

    # -- results ---------------------------------------------------------------------------

    def figures(self, scalars: dict[str, Any]) -> list[tuple[str, str]]:
        """The global test, the variance factor, the redundancy and the outlier candidates."""
        variance = scalars.get("network.VARIANCE_FACTOR")
        passed = scalars.get("network.GLOBAL_TEST_PASSED")
        return [
            (
                _tr("Global test"),
                _tr("Not tested: no redundancy")
                if passed is None
                else _tr("Passes")
                if passed
                else _tr("Fails: see the report"),
            ),
            (
                _tr("Variance factor"),
                "" if variance is None else localised(f"{float(variance):.3f}"),
            ),
            (_tr("Degrees of freedom"), str(scalars.get("network.DEGREES_OF_FREEDOM", ""))),
            (_tr("Outlier candidates"), str(scalars.get("network.OUTLIER_COUNT", ""))),
        ]

    def adjusted(self) -> dict[str, tuple[float, float, float]]:
        """The stations the last run adjusted, as the algorithm's table gives them."""
        path = self.output_path("network", "OUTPUT_STATIONS")
        if path is None:
            return {}
        with open(path, encoding="utf-8", newline="") as handle:
            return {
                row["station"]: (float(row["x"]), float(row["y"]), float(row["z"]))
                for row in csv.DictReader(handle)
            }

    def observed_pairs(self) -> list[tuple[str, str]]:
        """Each pair of stations an observation of the last run joins, as its network document lists them."""
        path = self.output_path("network", "OUTPUT_NETWORK")
        if path is None:
            return []
        document = json.loads(path.read_text(encoding="utf-8"))
        pairs: dict[tuple[str, str], None] = {}
        for observation in document.get("observations", ()):
            stations = [str(name) for name in observation.get("stations", ())]
            if len(stations) == 2 and stations[0] != stations[1]:
                pairs[tuple(sorted(stations))] = None
        return list(pairs)

    def add_layers(self) -> int:
        """Add the algorithm's result layers to the project. Returns how many."""
        files = {
            name: path
            for name, _file in ts.NETWORK_LAYERS
            if (path := self.output_path("network", name)) is not None
        }
        registered = QgsApplication.processingRegistry().algorithmById(ts.NETWORK)
        labels: dict[str, str] = {}
        if registered is not None:
            # Held while its definitions are read: they belong to the instance.
            algorithm = registered.create({})
            for name in files:
                definition = algorithm.parameterDefinition(name)
                if definition is not None:
                    labels[name] = definition.description()
        added = add_result_layers(
            files,
            group=_tr("Classical network (%1)").replace("%1", self.job.name or _tr("untitled job")),
            labels=labels,
            solution=self.output_path("network", "OUTPUT_SOLUTION"),
        )
        return len(added)

    def use_as_known_points(self) -> int:
        """Write the adjusted stations into the job's known points. Returns how many.

        A plane adjustment does not estimate heights, so a height typed for a
        station stays; a 3D or height adjustment's are written.
        """
        adjusted = self.adjusted()
        planimetric = int(self.datum_form.value("DIMENSION") or 0) == _PLANIMETRIC
        book = self.book
        for name, (easting, northing, up) in adjusted.items():
            if planimetric:
                self.keep_point(name, easting, northing, up, origin="network")
            else:
                book.set_point(name, round(easting, 4), round(northing, 4), up, origin="network")
        if adjusted:
            self.touch()
        return len(adjusted)

    def draw(self) -> None:
        """The approximate coordinates, and the network the algorithm adjusted."""
        for easting, northing in self.placed_points().values():
            self.sketch.add_point(easting, northing)
        if self.step("calculate").state != DONE:
            return
        adjusted = self.adjusted()
        for easting, northing, _up in adjusted.values():
            self.sketch.add_point(easting, northing, computed=True)
        for first, second in self.observed_pairs():
            if first in adjusted and second in adjusted:
                self.sketch.add_line([adjusted[first][:2], adjusted[second][:2]])

    def reload_pages(self) -> None:
        """Another job is the current one: show its points, datum and options."""
        self.points_grid.set_table(self.book.points)
        self.datum_form.reload()
        self.options_form.reload()
        self._load_stations()

    def refresh(self) -> None:
        """Also re-read the points, and the CRS, which another window may have changed."""
        if hasattr(self, "options_form") and getattr(self, "_crs_shown", None) != self.job.crs:
            # The job's CRS is the form's default for the network's: shown anew
            # when the Field book window changes it.
            self._crs_shown = self.job.crs
            self.options_form.reload()
        if hasattr(self, "stations_list"):
            self.points_grid.reload()
            table = self.book.points
            names = [table.cell(row, "name") for row in table.filled_rows() if table.cell(row, "name")]
            shown = [self.stations_list.item(i).text() for i in range(self.stations_list.count())]
            if [name for name in shown if name in names] != list(dict.fromkeys(names)):
                self._load_stations()
        super().refresh()
