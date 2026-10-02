# SPDX-License-Identifier: GPL-2.0-or-later
"""The results panel (specs/15 section 4; phase P12b).

*A dockable panel showing the current project's solutions: run history with
status, statistics summaries, per-observation results with sorting and
filtering, and links from a table row to the corresponding map feature.
Selecting a station shows its time series when the project has multiple
epochs.* And: *this is where the teaching value concentrates -- the statistics
are visible, next to the map, rather than buried in an output file.*

**Where the runs come from.** Every result layer an adjustment adds to the
project names the solution document it was drawn from
(:data:`~geocomp.algorithms.layer_outputs.SOLUTION_PROPERTY`), so the panel
lists a run as soon as its layers arrive, as the time-series panel does with a
series. A solution document, or a project store and every solution in it, can
also be opened by hand.

**A row is a link.** Selecting an observation selects its feature on the
residual layers drawn from the same run, and a station its point; the map
zooms there. A station that the time-series panel has a series for is shown
there too. What the panel shows is read by
:mod:`geocomp.core.visualization.results`, without QGIS, and the decision in
the table is the one the residual layer is drawn by.
"""

from __future__ import annotations

import json
import math
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from qgis.core import QgsExpression, QgsProject, QgsVectorLayer
from qgis.gui import QgsDockWidget
from qgis.PyQt.QtCore import QCoreApplication, QSortFilterProxyModel, Qt
from qgis.PyQt.QtGui import QStandardItem, QStandardItemModel
from qgis.PyQt.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSplitter,
    QTableView,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from geocomp.core.errors import GeoCompError
from geocomp.core.models import Solution
from geocomp.core.visualization.results import (
    FILTERS,
    ObservationRow,
    matches,
    observation_rows,
    run_summary,
    station_rows,
    statistics_items,
)

__all__ = ["ResultsPanel", "attach_to_project", "detach_from_project"]

_CONTEXT = "GeoCompResultsPanel"

#: The role each cell sorts by: the number itself, not its text.
SORT_ROLE = Qt.ItemDataRole.UserRole + 1


def _tr(text: str) -> str:
    return QCoreApplication.translate(_CONTEXT, text)


def _number(value: Any, digits: int = 5) -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return _tr("yes") if value else _tr("no")
    if isinstance(value, float):
        if math.isinf(value):
            return "∞"
        return f"{value:.{digits}g}"
    return str(value)


@dataclass
class _Run:
    solution: Solution
    source: str


class _ObservationFilter(QSortFilterProxyModel):
    """Sorts by number, with the empty last, and filters through ``matches``."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.rows: list[ObservationRow] = []
        self.kind = "all"
        self.text = ""
        self.setSortRole(SORT_ROLE)

    def filterAcceptsRow(self, source_row, source_parent) -> bool:
        if source_row >= len(self.rows):
            return True
        return matches(self.rows[source_row], self.kind, self.text)

    def lessThan(self, left, right) -> bool:
        first, second = left.data(SORT_ROLE), right.data(SORT_ROLE)
        if first is None or second is None:
            # Last in both directions: Qt reverses this comparison to sort
            # descending, so a value that was never computed would otherwise
            # head the column it is missing from.
            if first is None and second is None:
                return False
            ascending = self.sortOrder() == Qt.SortOrder.AscendingOrder
            return (second is None) == ascending
        return _key(first) < _key(second)


def _key(value: Any) -> tuple:
    if isinstance(value, (int, float)):
        return (0, float(value), "")
    return (1, 0.0, str(value))


class ResultsPanel(QgsDockWidget):
    """The project's adjustments, their statistics and their observations, beside the map."""

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        zoom: Callable[[QgsVectorLayer], None] | None = None,
        series_panel: Any = None,
    ) -> None:
        super().__init__(_tr("GeoComp results"), parent)
        self.setObjectName("geocompResultsPanel")
        self.runs: list[_Run] = []
        self._zoom = zoom
        self._series_panel = series_panel
        self._current = -1

        body = QWidget(self)
        layout = QVBoxLayout(body)
        bar = QHBoxLayout()
        self.open_solution_button = QPushButton(_tr("Open solution…"), body)
        self.open_store_button = QPushButton(_tr("Open project store…"), body)
        bar.addWidget(self.open_solution_button)
        bar.addWidget(self.open_store_button)
        bar.addStretch(1)
        layout.addLayout(bar)

        split = QSplitter(Qt.Orientation.Vertical, body)
        self.run_table = QTableWidget(0, 8, split)
        self.run_table.setObjectName("geocompResultsRuns")
        self.run_table.setHorizontalHeaderLabels(
            [
                _tr("Solution"),
                _tr("Created"),
                _tr("Algorithm"),
                _tr("Global test"),
                _tr("Variance factor"),
                _tr("Degrees of freedom"),
                _tr("Blunder candidates"),
                _tr("Uncheckable"),
            ]
        )
        self.run_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.run_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.run_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        self.tabs = QTabWidget(split)
        self.statistics = QTableWidget(0, 2, self.tabs)
        self.statistics.setObjectName("geocompResultsStatistics")
        self.statistics.setHorizontalHeaderLabels([_tr("Quantity"), _tr("Value")])
        self.statistics.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabs.addTab(self.statistics, _tr("Statistics"))

        observations = QWidget(self.tabs)
        observations_layout = QVBoxLayout(observations)
        filters = QHBoxLayout()
        self.search = QLineEdit(observations)
        self.search.setPlaceholderText(_tr("Filter by observation id"))
        self.filter = QComboBox(observations)
        for kind, label in zip(FILTERS, self._filter_labels(), strict=True):
            self.filter.addItem(label, kind)
        filters.addWidget(self.search, stretch=1)
        filters.addWidget(self.filter)
        observations_layout.addLayout(filters)
        self.observation_model = QStandardItemModel(0, 7, observations)
        self.observation_model.setHorizontalHeaderLabels(
            [
                _tr("Observation"),
                _tr("Residual"),
                _tr("w"),
                _tr("Redundancy"),
                _tr("MDB"),
                _tr("External reliability"),
                _tr("Decision"),
            ]
        )
        self.observation_proxy = _ObservationFilter(observations)
        self.observation_proxy.setSourceModel(self.observation_model)
        self.observation_view = QTableView(observations)
        self.observation_view.setObjectName("geocompResultsObservations")
        self.observation_view.setModel(self.observation_proxy)
        self.observation_view.setSortingEnabled(True)
        self.observation_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.observation_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.observation_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        observations_layout.addWidget(self.observation_view)
        self.tabs.addTab(observations, _tr("Observations"))

        self.station_table = QTableWidget(0, 6, self.tabs)
        self.station_table.setObjectName("geocompResultsStations")
        self.station_table.setHorizontalHeaderLabels(
            [
                _tr("Station"),
                _tr("Coordinates"),
                _tr("Standard deviations (m)"),
                _tr("Positional uncertainty (m)"),
                _tr("Semi-major (m)"),
                _tr("Semi-minor (m)"),
            ]
        )
        self.station_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.station_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.station_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.station_table.setSortingEnabled(True)
        self.tabs.addTab(self.station_table, _tr("Stations"))

        split.addWidget(self.run_table)
        split.addWidget(self.tabs)
        split.setStretchFactor(1, 3)
        layout.addWidget(split)
        self.status = QLabel(body)
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.setWidget(body)

        self.open_solution_button.clicked.connect(self._open_solution)
        self.open_store_button.clicked.connect(self._open_store)
        self.run_table.itemSelectionChanged.connect(self._run_selected)
        self.search.textChanged.connect(self._filter_changed)
        self.filter.currentIndexChanged.connect(self._filter_changed)
        self.observation_view.selectionModel().selectionChanged.connect(self._observation_selected)
        self.station_table.itemSelectionChanged.connect(self._station_selected)

    # -- the runs ------------------------------------------------------------

    def add_solution(self, solution: Solution, source: str = "") -> int:
        """List *solution*, replacing the same one from the same source; return its row."""
        for index, run in enumerate(self.runs):
            if run.solution.id == solution.id and run.source == source:
                self.runs[index] = _Run(solution, source)
                self._fill_runs()
                return index
        self.runs.append(_Run(solution, source))
        self._fill_runs()
        index = len(self.runs) - 1
        if self._current < 0:
            self.show_run(index)
        return index

    def add_solution_file(self, path: str) -> int | None:
        """List the solution document at *path*; ``None`` if it cannot be read, said in the panel."""
        try:
            payload = json.loads(Path(path).read_text(encoding="utf-8"))
            solution = Solution.from_dict(payload)
        except (OSError, ValueError, KeyError, TypeError, GeoCompError) as error:
            self.status.setText(
                _tr("The solution %1 could not be read: %2")
                .replace("%1", path)
                .replace("%2", str(error))
            )
            return None
        return self.add_solution(solution, path)

    def open_store(self, path: str) -> int:
        """List every solution in the project store at *path*: the store's run history."""
        from geocomp.io.store import open_store

        try:
            with open_store(path) as store:
                solutions = store.read_solutions()
        except GeoCompError as error:
            from geocomp.services.messages import message_for

            self.status.setText(message_for(error))
            return 0
        for solution in solutions:
            self.add_solution(solution, path)
        self.status.setText(
            _tr("%1 solution(s) from %2.").replace("%1", str(len(solutions))).replace("%2", path)
        )
        return len(solutions)

    def _fill_runs(self) -> None:
        self.run_table.blockSignals(True)
        try:
            self.run_table.setRowCount(len(self.runs))
            for row, run in enumerate(self.runs):
                summary = run_summary(run.solution)
                test = (
                    "—"
                    if summary.global_test is None
                    else _tr("passed") if summary.global_test else _tr("FAILED")
                )
                cells = [
                    summary.id + (" " + _tr("(superseded)") if summary.superseded else ""),
                    summary.created.isoformat(timespec="seconds") if summary.created else "—",
                    summary.algorithm,
                    test,
                    _number(summary.variance_factor, 4),
                    str(summary.degrees_of_freedom),
                    str(summary.candidates),
                    str(summary.uncheckable),
                ]
                for column, text in enumerate(cells):
                    item = QTableWidgetItem(text)
                    if column == 0 and run.source:
                        item.setToolTip(run.source)
                    self.run_table.setItem(row, column, item)
            if 0 <= self._current < len(self.runs):
                self.run_table.selectRow(self._current)
        finally:
            self.run_table.blockSignals(False)

    def _run_selected(self) -> None:
        rows = {index.row() for index in self.run_table.selectedIndexes()}
        if rows:
            self.show_run(min(rows))

    def show_run(self, index: int) -> None:
        """Show run *index*: its statistics, its observations, its stations."""
        if not 0 <= index < len(self.runs):
            return
        self._current = index
        solution = self.runs[index].solution
        self._fill_statistics(solution)
        self._fill_observations(solution)
        self._fill_stations(solution)
        self.run_table.blockSignals(True)
        self.run_table.selectRow(index)
        self.run_table.blockSignals(False)
        if solution.is_approximate:
            self.status.setText(
                _tr(
                    "This solution's uncertainties are approximate; its report names the "
                    "strategies used."
                )
            )

    @property
    def current(self) -> _Run | None:
        return self.runs[self._current] if 0 <= self._current < len(self.runs) else None

    def _fill_statistics(self, solution: Solution) -> None:
        labels = self._statistics_labels()
        items = statistics_items(solution)
        self.statistics.setRowCount(len(items))
        for row, (key, value) in enumerate(items):
            self.statistics.setItem(row, 0, QTableWidgetItem(labels.get(key, key)))
            self.statistics.setItem(row, 1, QTableWidgetItem(self._value(key, value)))

    def _value(self, key: str, value: Any) -> str:
        if key == "global_test" and value is not None:
            return _tr("passed") if value else _tr("FAILED")
        return _number(value)

    def _fill_observations(self, solution: Solution) -> None:
        rows = observation_rows(solution)
        labels = self._decision_labels()
        self.observation_model.removeRows(0, self.observation_model.rowCount())
        for row in rows:
            cells = [
                (row.observation_id, row.observation_id),
                (_number(row.residual), row.residual),
                (_number(row.standardised, 3), row.standardised),
                (_number(row.redundancy, 3), row.redundancy),
                # An uncheckable observation's MDB is infinite, which is how it sorts.
                (_number(row.mdb), row.mdb if row.mdb is not None else _infinite(row)),
                (_number(row.external), row.external),
                (labels.get(row.decision, row.decision), row.decision),
            ]
            items = []
            for text, sort in cells:
                item = QStandardItem(text)
                item.setData(sort, SORT_ROLE)
                items.append(item)
            self.observation_model.appendRow(items)
        self.observation_proxy.rows = rows
        self.observation_proxy.invalidateFilter()

    def _fill_stations(self, solution: Solution) -> None:
        from geocomp.algorithms.display import display_format

        shown = display_format()
        rows = station_rows(solution)
        self.station_table.setSortingEnabled(False)
        self.station_table.setRowCount(len(rows))
        for index, row in enumerate(rows):
            cells = [
                row.station_id,
                ", ".join(
                    f"{name} {shown.coordinate(value)}"
                    for name, value in zip(row.components, row.values, strict=True)
                ),
                ", ".join(_number(value, 3) for value in row.std_devs),
                _number(row.positional_uncertainty, 3),
                _number(row.semi_major, 3),
                _number(row.semi_minor, 3),
            ]
            for column, text in enumerate(cells):
                self.station_table.setItem(index, column, QTableWidgetItem(text))
        self.station_table.setSortingEnabled(True)

    # -- filtering -------------------------------------------------------------

    def set_filter(self, kind: str = "all", text: str = "") -> None:
        """Narrow the observation table to *kind* (one of ``FILTERS``) and ids containing *text*."""
        self.filter.setCurrentIndex(max(FILTERS.index(kind), 0))
        self.search.setText(text)
        self._filter_changed()

    def _filter_changed(self, *args) -> None:
        self.observation_proxy.kind = self.filter.currentData() or "all"
        self.observation_proxy.text = self.search.text().strip()
        self.observation_proxy.invalidateFilter()

    def visible_observations(self) -> list[str]:
        """The observation ids the table shows, in the order it shows them."""
        return [
            self.observation_proxy.index(row, 0).data()
            for row in range(self.observation_proxy.rowCount())
        ]

    # -- links to the map ----------------------------------------------------------

    def _observation_selected(self, *args) -> None:
        rows = self.observation_view.selectionModel().selectedRows()
        if rows:
            self.select_observation(rows[0].data())

    def select_observation(self, observation_id: str) -> int:
        """Select *observation_id* on this run's residual and observation layers; return the count."""
        return self._select("residuals", "observation", observation_id) + self._select(
            "observations", "observation", observation_id
        )

    def _station_selected(self) -> None:
        rows = {index.row() for index in self.station_table.selectedIndexes()}
        if rows:
            item = self.station_table.item(min(rows), 0)
            if item is not None:
                self.select_station(item.text())

    def select_station(self, station_id: str) -> int:
        """Select *station_id* on this run's station layers, and show its time series if there is one."""
        selected = self._select("stations", "station", station_id)
        series = self._series_panel
        if series is not None and getattr(series, "document", None):
            known = {record["station"] for record in series.document["stations"]}
            if station_id in known:
                series.select_stations([station_id])
                series.show()
        return selected

    def _select(self, kind: str, field: str, value: str) -> int:
        from geocomp.algorithms.layer_outputs import RESULT_LAYER_PROPERTY, SOLUTION_PROPERTY

        run = self.current
        if run is None or not run.source:
            return 0
        count = 0
        for layer in QgsProject.instance().mapLayers().values():
            if not isinstance(layer, QgsVectorLayer):
                continue
            if layer.customProperty(RESULT_LAYER_PROPERTY) != kind:
                continue
            if str(layer.customProperty(SOLUTION_PROPERTY) or "") != run.source:
                continue
            if layer.fields().indexFromName(field) < 0:
                continue
            layer.selectByExpression(f'"{field}" = {QgsExpression.quotedValue(value)}')
            selected = layer.selectedFeatureCount()
            count += selected
            if selected and self._zoom is not None:
                self._zoom(layer)
        return count

    # -- the project -------------------------------------------------------------

    def layers_added(self, layers) -> None:
        """List the run behind any result layer that names its solution document."""
        from geocomp.algorithms.layer_outputs import SOLUTION_PROPERTY

        seen = {run.source for run in self.runs}
        for layer in layers:
            path = str(layer.customProperty(SOLUTION_PROPERTY) or "")
            if path and path not in seen and Path(path).is_file():
                seen.add(path)
                self.add_solution_file(path)

    # -- dialogs -------------------------------------------------------------------

    def _open_solution(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, _tr("Open solution"), "", _tr("GeoComp solution (*.json)")
        )
        if path:
            self.add_solution_file(path)

    def _open_store(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, _tr("Open project store"), "", _tr("GeoComp project (*.gpkg)")
        )
        if path:
            self.open_store(path)

    # -- labels ----------------------------------------------------------------------

    @staticmethod
    def _filter_labels() -> list[str]:
        return [
            _tr("All observations"),
            _tr("Blunder candidates"),
            _tr("Uncheckable"),
            _tr("Not tested"),
        ]

    @staticmethod
    def _decision_labels() -> dict[str, str]:
        return {
            "accepted": _tr("Passes the w-test"),
            "rejected": _tr("Blunder candidate"),
            "uncheckable": _tr("Uncheckable"),
            "": _tr("Not tested"),
        }

    @staticmethod
    def _statistics_labels() -> dict[str, str]:
        return {
            "observations": _tr("Observations"),
            "parameters": _tr("Parameters"),
            "constraints": _tr("Constraints"),
            "degrees_of_freedom": _tr("Degrees of freedom"),
            "variance_factor_apriori": _tr("Variance factor, a priori"),
            "variance_factor_aposteriori": _tr("Variance factor, a posteriori"),
            "global_test": _tr("Global test"),
            "test_statistic": _tr("Test statistic"),
            "critical_low": _tr("Lower critical value"),
            "critical_high": _tr("Upper critical value"),
            "confidence": _tr("Confidence level"),
            "candidates": _tr("Blunder candidates"),
            "uncheckable": _tr("Uncheckable observations"),
            "iterations": _tr("Iterations"),
            "converged": _tr("Converged"),
            "max_correction": _tr("Largest last correction"),
            "condition_number": _tr("Condition number"),
            "uncertainty_mode": _tr("Uncertainty mode"),
        }


def _infinite(row: ObservationRow) -> float | None:
    return math.inf if row.decision == "uncheckable" else None


def attach_to_project(panel: ResultsPanel) -> None:
    """Watch the project for result layers; list the runs of those already there."""
    project = QgsProject.instance()
    project.layersAdded.connect(panel.layers_added)
    panel.layers_added(list(project.mapLayers().values()))


def detach_from_project(panel: ResultsPanel) -> None:
    try:
        QgsProject.instance().layersAdded.disconnect(panel.layers_added)
    except (TypeError, RuntimeError):
        pass
