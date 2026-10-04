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

**Nothing slow on the GUI thread (NFR-004).** A solution with its full
covariance is large -- 37 MB for 625 stations, a second to parse -- so a document
or a store opened from the panel, or named by a layer that arrives, is read in
a :class:`~geocomp.services.task_service.GeoCompTask` and listed when it is
done. And the observation table holds its rows rather than an item per cell,
so filling it is a reset and Qt asks only for the cells it draws: as a
standard item model behind a filtering proxy it took 180 ms for 2,352
observations, the proxy's Python filter called once a row.
"""

from __future__ import annotations

import json
import math
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from qgis.core import QgsExpression, QgsProject, QgsVectorLayer
from qgis.gui import QgsDockWidget
from qgis.PyQt.QtCore import QAbstractTableModel, QCoreApplication, QModelIndex, Qt
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
    StationRow,
    matches,
    observation_rows,
    run_summary,
    station_rows,
    statistics_items,
)

if TYPE_CHECKING:
    from geocomp.services.task_service import GeoCompTask

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


class _RowTable(QAbstractTableModel):
    """A table that holds its rows: which the filter keeps, in order.

    Filtering is a predicate over a list and sorting a list sort, each the whole
    table at once; Qt asks :meth:`data` only for the cells it draws. *cell*
    gives a row's column as the text shown and the value it sorts by, and a
    column sorts by the value, with one that was never computed last in both
    directions.
    """

    def __init__(
        self,
        headers: list[str],
        cell: Callable[[Any, int], tuple[str, Any]],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.headers = headers
        self.cell = cell
        self.rows: list[Any] = []
        self.shown: list[Any] = []
        self._keep: Callable[[Any], bool] = lambda _row: True
        self._order: tuple[int, Qt.SortOrder] | None = None

    # -- what is shown -------------------------------------------------------

    def set_rows(self, rows: list[Any]) -> None:
        self.beginResetModel()
        self.rows = list(rows)
        self._select()
        self.endResetModel()

    def set_keep(self, keep: Callable[[Any], bool]) -> None:
        self.beginResetModel()
        self._keep = keep
        self._select()
        self.endResetModel()

    def _select(self) -> None:
        self.shown = [row for row in self.rows if self._keep(row)]
        if self._order is not None:
            self._sorted(*self._order)

    def sort(self, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder) -> None:
        self.layoutAboutToBeChanged.emit()
        before = self.persistentIndexList()
        where = [(self.shown[index.row()], index.column()) for index in before]
        self._order = (column, order)
        self._sorted(column, order)
        position = {id(row): number for number, row in enumerate(self.shown)}
        self.changePersistentIndexList(
            before, [self.index(position[id(row)], column) for row, column in where]
        )
        self.layoutChanged.emit()

    def _sorted(self, column: int, order: Qt.SortOrder) -> None:
        present = [row for row in self.shown if self.cell(row, column)[1] is not None]
        missing = [row for row in self.shown if self.cell(row, column)[1] is None]
        present.sort(
            key=lambda row: _key(self.cell(row, column)[1]),
            reverse=order == Qt.SortOrder.DescendingOrder,
        )
        self.shown = present + missing

    # -- the model's contract ------------------------------------------------

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: B008 -- Qt's own default
        return 0 if parent.isValid() else len(self.shown)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: B008 -- Qt's own default
        return 0 if parent.isValid() else len(self.headers)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or not 0 <= index.row() < len(self.shown):
            return None
        text, value = self.cell(self.shown[index.row()], index.column())
        if role == Qt.ItemDataRole.DisplayRole:
            return text
        if role == SORT_ROLE:
            return value
        return None

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole
    ) -> Any:
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.headers[section]
        return None


def _observation_cell(decisions: dict[str, str]) -> Callable[[ObservationRow, int], tuple[str, Any]]:
    def cell(row: ObservationRow, column: int) -> tuple[str, Any]:
        if column == 0:
            return row.observation_id, row.observation_id
        if column == 1:
            return _number(row.residual), row.residual
        if column == 2:
            return _number(row.standardised, 3), row.standardised
        if column == 3:
            return _number(row.redundancy, 3), row.redundancy
        if column == 4:
            # An uncheckable observation's MDB is infinite, which is how it sorts.
            return _number(row.mdb), row.mdb if row.mdb is not None else _infinite(row)
        if column == 5:
            return _number(row.external), row.external
        return decisions.get(row.decision, row.decision), row.decision

    return cell


def _station_cell(shown) -> Callable[[StationRow, int], tuple[str, Any]]:
    """Until P12c-15 the station table sorted its numbers as text, so 10.5 came
    before 9.2; each column now sorts by its value."""

    def cell(row: StationRow, column: int) -> tuple[str, Any]:
        if column == 0:
            return row.station_id, row.station_id
        if column == 1:
            return (
                ", ".join(
                    f"{name} {shown.coordinate(value)}"
                    for name, value in zip(row.components, row.values, strict=True)
                ),
                row.values[0] if row.values else None,
            )
        if column == 2:
            return (
                ", ".join(_number(value, 3) for value in row.std_devs),
                max(row.std_devs) if row.std_devs else None,
            )
        if column == 3:
            return _number(row.positional_uncertainty, 3), row.positional_uncertainty
        if column == 4:
            return _number(row.semi_major, 3), row.semi_major
        return _number(row.semi_minor, 3), row.semi_minor

    return cell


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
        self._tasks: list[GeoCompTask] = []
        self._reading: set[str] = set()
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
        self.observation_model = _RowTable(
            [
                _tr("Observation"),
                _tr("Residual"),
                _tr("w"),
                _tr("Redundancy"),
                _tr("MDB"),
                _tr("External reliability"),
                _tr("Decision"),
            ],
            _observation_cell(self._decision_labels()),
            observations,
        )
        self.observation_view = QTableView(observations)
        self.observation_view.setObjectName("geocompResultsObservations")
        self.observation_view.setModel(self.observation_model)
        self.observation_view.setSortingEnabled(True)
        self.observation_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.observation_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.observation_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        observations_layout.addWidget(self.observation_view)
        self.tabs.addTab(observations, _tr("Observations"))

        self.station_model = _RowTable(
            [
                _tr("Station"),
                _tr("Coordinates"),
                _tr("Standard deviations (m)"),
                _tr("Positional uncertainty (m)"),
                _tr("Semi-major (m)"),
                _tr("Semi-minor (m)"),
            ],
            _station_cell(None),  # replaced by the display format at each fill
            self.tabs,
        )
        self.station_table = QTableView(self.tabs)
        self.station_table.setObjectName("geocompResultsStations")
        self.station_table.setModel(self.station_model)
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
        self.station_table.selectionModel().selectionChanged.connect(self._station_selected)

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
        """List the solution document at *path*; ``None`` if it cannot be read, said in the panel.

        Reads on the calling thread. The panel's own buttons and the layers
        that arrive use :meth:`load_solution_file`, which does not.
        """
        try:
            solution = read_solution(path)
        except _UNREADABLE as error:
            self._unreadable(path, error)
            return None
        return self.add_solution(solution, path)

    def load_solution_file(self, path: str) -> GeoCompTask:
        """Read the solution document at *path* off the GUI thread, then list it (NFR-004)."""
        self._reading.add(path)

        def listed(solution: Solution) -> None:
            self._reading.discard(path)
            self.add_solution(solution, path)

        def refused(error: BaseException) -> None:
            self._reading.discard(path)
            self._unreadable(path, error)

        return self._in_background(
            _tr("Reading the solution %1").replace("%1", path),
            lambda _cancellation, _progress: read_solution(path),
            listed,
            refused,
        )

    @property
    def busy(self) -> bool:
        """Whether a document or a store is still being read."""
        return bool(self._tasks)

    def _unreadable(self, path: str, error: BaseException) -> None:
        if not isinstance(error, _UNREADABLE):
            raise error
        from geocomp.services.messages import reason_for

        self.status.setText(
            _tr("The solution %1 could not be read: %2")
            .replace("%1", path)
            .replace("%2", reason_for(error))
        )

    def _in_background(self, description, work, on_success, on_error) -> GeoCompTask:
        from geocomp.services.task_service import run_in_background

        self.status.setText(description)
        return run_in_background(
            description, work, on_success=on_success, on_error=on_error, keep=self._tasks
        )

    def open_store(self, path: str) -> int:
        """List every solution in the project store at *path*: the store's run history.

        Reads on the calling thread; the panel's button uses :meth:`load_store`.
        """
        try:
            solutions = read_store_solutions(path)
        except GeoCompError as error:
            self._store_unreadable(error)
            return 0
        return self._add_store(path, solutions)

    def load_store(self, path: str) -> GeoCompTask:
        """Read every solution in the project store at *path* off the GUI thread (NFR-004)."""
        return self._in_background(
            _tr("Reading the project store %1").replace("%1", path),
            lambda _cancellation, _progress: read_store_solutions(path),
            lambda solutions: self._add_store(path, solutions),
            self._store_unreadable,
        )

    def _add_store(self, path: str, solutions: list[Solution]) -> int:
        for solution in solutions:
            self.add_solution(solution, path)
        self.status.setText(
            _tr("%1 solution(s) from %2.").replace("%1", str(len(solutions))).replace("%2", path)
        )
        return len(solutions)

    def _store_unreadable(self, error: BaseException) -> None:
        if not isinstance(error, GeoCompError):
            raise error
        from geocomp.services.messages import message_for

        self.status.setText(message_for(error))

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
        self.observation_model.set_rows(observation_rows(solution))

    def _fill_stations(self, solution: Solution) -> None:
        from geocomp.algorithms.display import display_format

        self.station_model.cell = _station_cell(display_format())
        self.station_model.set_rows(station_rows(solution))

    # -- filtering -------------------------------------------------------------

    def set_filter(self, kind: str = "all", text: str = "") -> None:
        """Narrow the observation table to *kind* (one of ``FILTERS``) and ids containing *text*."""
        self.filter.setCurrentIndex(max(FILTERS.index(kind), 0))
        self.search.setText(text)
        self._filter_changed()

    def _filter_changed(self, *args) -> None:
        kind, text = self.filter.currentData() or "all", self.search.text().strip()
        self.observation_model.set_keep(lambda row: matches(row, kind, text))

    def visible_observations(self) -> list[str]:
        """The observation ids the table shows, in the order it shows them."""
        return [row.observation_id for row in self.observation_model.shown]

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

    def _station_selected(self, *args) -> None:
        rows = self.station_table.selectionModel().selectedRows()
        if rows:
            self.select_station(rows[0].data())

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

        seen = {run.source for run in self.runs} | self._reading
        for layer in layers:
            path = str(layer.customProperty(SOLUTION_PROPERTY) or "")
            if path and path not in seen and Path(path).is_file():
                seen.add(path)
                self.load_solution_file(path)

    # -- dialogs -------------------------------------------------------------------

    def _open_solution(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, _tr("Open solution"), "", _tr("GeoComp solution (*.json)")
        )
        if path:
            self.load_solution_file(path)

    def _open_store(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, _tr("Open project store"), "", _tr("GeoComp project (*.gpkg)")
        )
        if path:
            self.load_store(path)

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


#: What a solution document that cannot be listed raises when read.
_UNREADABLE = (OSError, ValueError, KeyError, TypeError, GeoCompError)


def read_solution(path: str) -> Solution:
    """The solution document at *path*. Touches no QGIS object, so it runs on a
    worker thread as well as on the GUI's."""
    return Solution.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def read_store_solutions(path: str) -> list[Solution]:
    """Every solution in the project store at *path*; as :func:`read_solution`,
    safe off the GUI thread, since the store opens its own connection."""
    from geocomp.io.store import open_store

    with open_store(path) as store:
        return store.read_solutions()


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
