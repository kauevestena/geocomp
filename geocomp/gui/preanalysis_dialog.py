# SPDX-License-Identifier: GPL-2.0-or-later
"""Interactive network pre-analysis on the map canvas (FR-272).

``specs/06`` section 8 and ``specs/15`` section 3. A design is placed on the
canvas -- stations clicked in, observations drawn between them -- and
re-evaluated after every change, so the expected precision and reliability move
while the user is still deciding where to put things.

That loop is the reason pre-analysis belongs in a GIS at all. A spreadsheet can
compute **Σ**x; what it cannot do is let a surveyor see the ellipses shrink as
they drag a station uphill onto ground they know is accessible, over the
orthophoto that told them so.

Everything about what an edit *means* lives in
:class:`~geocomp.core.preanalysis.session.DesignSession`, which has no Qt in it
and is tested without QGIS. This module is the canvas tool, the rubber bands and
the panel.

**The dialog does not replace the algorithm.** On accept it writes the design as
a network document and hands it to ``geocomp:analysis_network_preanalysis`` for
the full report, so the numbers a user acts on come from the same code path as
every non-interactive run (ADR-0005).
"""

from __future__ import annotations

import json
import math
import tempfile
from html import escape
from pathlib import Path
from typing import Any

from qgis.core import (
    QgsFeature,
    QgsField,
    QgsFields,
    QgsGeometry,
    QgsPointXY,
    QgsProject,
    QgsVectorLayer,
    QgsWkbTypes,
)
from qgis.gui import QgsMapCanvas, QgsMapTool, QgsRubberBand, QgsVertexMarker
from qgis.PyQt.QtCore import QCoreApplication, QEventLoop, QMetaType, Qt, QVariant, pyqtSignal
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from geocomp.core.models import Network, ObservationType, network_from_document
from geocomp.core.number_format import localised
from geocomp.core.preanalysis.session import DesignSession
from geocomp.core.units import Unit
from geocomp.core.visualization import default_exaggeration, ellipse_ring
from geocomp.services.messages import finding_text

__all__ = [
    "ADD_STATION",
    "CONNECT",
    "MOVE",
    "NETWORK_LAYER_FIELDS",
    "NETWORK_LAYER_PROPERTY",
    "REMOVE",
    "DesignMapTool",
    "PreAnalysisDialog",
    "is_preanalysis_network_layer",
    "network_layer_features",
    "network_layer_fields",
    "network_to_vector_layer",
    "network_to_vector_layers",
    "session_from_vector_layer",
    "write_network_geojson",
]

_TR_CONTEXT = "GeoCompPreAnalysis"
NETWORK_LAYER_PROPERTY = "geocomp/preanalysis_network"
NETWORK_GEOJSON_PROPERTY = "geocomp/preanalysis_geojson"

_TEXT = QMetaType.Type.QString
_REAL = QMetaType.Type.Double

NETWORK_LAYER_FIELDS: tuple[tuple[str, Any], ...] = (
    ("record_kind", _TEXT),
    ("network_id", _TEXT),
    ("crs", _TEXT),
    ("frame", _TEXT),
    ("datum", _TEXT),
    ("tolerance", _REAL),
    ("confidence", _REAL),
    ("station_id", _TEXT),
    ("station_type", _TEXT),
    ("easting", _REAL),
    ("northing", _REAL),
    ("height", _REAL),
    ("uncertainty", _REAL),
    ("semi_major", _REAL),
    ("semi_minor", _REAL),
    ("orientation", _REAL),
    ("observation_id", _TEXT),
    ("observation_type", _TEXT),
    ("from_station", _TEXT),
    ("from_type", _TEXT),
    ("from_easting", _REAL),
    ("from_northing", _REAL),
    ("from_height", _REAL),
    ("from_uncertainty", _REAL),
    ("from_semi_major", _REAL),
    ("from_semi_minor", _REAL),
    ("from_orientation", _REAL),
    ("to_station", _TEXT),
    ("to_type", _TEXT),
    ("to_easting", _REAL),
    ("to_northing", _REAL),
    ("to_height", _REAL),
    ("to_uncertainty", _REAL),
    ("to_semi_major", _REAL),
    ("to_semi_minor", _REAL),
    ("to_orientation", _REAL),
    ("unit", _TEXT),
    ("value", _REAL),
    ("sigma", _REAL),
    ("required_sigma", _REAL),
    ("redundancy", _REAL),
    ("mdb", _REAL),
    ("external_effect", _REAL),
    ("cluster_id", _TEXT),
)

ADD_STATION, MOVE, CONNECT, REMOVE = range(4)

#: How close a click must be to a station to count as hitting it, in pixels.
#: Generous, because the alternative is a click that silently adds a station on
#: top of an existing one.
_HIT_RADIUS = 12

_STATION_COLOUR = QColor(0, 114, 178)
_SELECTED_COLOUR = QColor(230, 159, 0)
_OBSERVATION_COLOUR = QColor(0, 158, 115)
_ELLIPSE_COLOUR = QColor(213, 94, 0)


def _tr(text: str) -> str:
    return QCoreApplication.translate(_TR_CONTEXT, text)


class DesignMapTool(QgsMapTool):
    """Clicks on the canvas, turned into design edits.

    One tool with a mode rather than four tools, because the modes share the
    hit-testing and switching tools would clear the canvas selection each time.
    """

    # Qt signal names follow Qt's own convention, not Python's, so that a
    # reader who knows QgsMapTool recognises them.
    stationRequested = pyqtSignal(float, float)  # noqa: N815
    stationClicked = pyqtSignal(str)  # noqa: N815
    observationClicked = pyqtSignal(str)  # noqa: N815
    canvasRightClicked = pyqtSignal()  # noqa: N815

    def __init__(self, canvas, session: DesignSession) -> None:
        super().__init__(canvas)
        self.canvas = canvas
        self.session = session
        self.mode = ADD_STATION

    def canvasReleaseEvent(self, event) -> None:
        point = self.toMapCoordinates(event.pos())
        if event.button() == Qt.MouseButton.RightButton:
            self.canvasRightClicked.emit()
            return

        hit = self._station_at(point)
        if self.mode == ADD_STATION and hit is None:
            self.stationRequested.emit(point.x(), point.y())
        elif hit is not None:
            self.stationClicked.emit(hit)
        elif self.mode == REMOVE:
            observation_hit = self._observation_at(point)
            if observation_hit is not None:
                self.observationClicked.emit(observation_hit)
        elif self.mode == MOVE:
            # A click on empty ground in Move mode is the destination.
            self.stationRequested.emit(point.x(), point.y())

    def _station_at(self, point: QgsPointXY) -> str | None:
        """The station nearest the click, within the hit radius.

        In map units derived from the canvas scale rather than a fixed
        distance, so the tolerance stays the same on screen at every zoom --
        which is where a user's sense of "close enough" actually lives.
        """
        tolerance = _HIT_RADIUS * self.canvas.mapUnitsPerPixel()
        best: tuple[float, str] | None = None
        for station in self.session.network.stations.values():
            if station.approx_position is None:
                continue
            east, north, _up = station.approx_position.values
            distance = math.hypot(east.value - point.x(), north.value - point.y())
            if distance <= tolerance and (best is None or distance < best[0]):
                best = (distance, station.id)
        return best[1] if best else None

    def _observation_at(self, point: QgsPointXY) -> str | None:
        """The planned observation segment nearest the click, within the hit radius."""
        tolerance = _HIT_RADIUS * self.canvas.mapUnitsPerPixel()
        best: tuple[float, str] | None = None
        for observation in self.session.network.observations.values():
            if len(observation.stations) < 2:
                continue
            first = self.session.network.stations.get(observation.stations[0])
            second = self.session.network.stations.get(observation.stations[1])
            if (
                first is None
                or second is None
                or first.approx_position is None
                or second.approx_position is None
            ):
                continue
            e1, n1, _ = first.approx_position.values
            e2, n2, _ = second.approx_position.values
            distance = _segment_distance(point.x(), point.y(), e1.value, n1.value, e2.value, n2.value)
            if distance <= tolerance and (best is None or distance < best[0]):
                best = (distance, observation.id)
        return best[1] if best else None


class PreAnalysisDialog(QDialog):
    """Place a design on the canvas and watch what it would achieve."""

    def __init__(self, canvas: QgsMapCanvas, crs: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("geocompPreAnalysisDialog")
        self.setWindowTitle(_tr("GeoComp — Interactive pre-analysis"))
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.Tool)
        self.resize(980, 680)

        self.canvas = canvas
        self.session = DesignSession(crs=crs or _canvas_crs(canvas))
        self._pending: str | None = None
        self._markers: list[QgsVertexMarker] = []
        self._bands: list[QgsRubberBand] = []
        self._counter = 0
        self.exaggeration = 1.0
        self.exported_geojson_path: Path | None = None
        self.exported_stations_layer: QgsVectorLayer | None = None
        self.exported_observations_layer: QgsVectorLayer | None = None
        self.exported_layers: tuple[QgsVectorLayer, QgsVectorLayer] | tuple[()] = ()
        self.exported_layer: QgsVectorLayer | None = None

        layout = QVBoxLayout(self)
        layout.addWidget(self._mode_group())
        layout.addWidget(self._settings_group())
        tables_row = QHBoxLayout()
        tables_row.addWidget(self._observations_group(), stretch=3)
        tables_row.addWidget(self._summary_group(), stretch=2)
        layout.addLayout(tables_row, stretch=1)
        layout.addWidget(self._findings_group())
        layout.addLayout(self._history_row())

        self._buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        self._buttons.accepted.connect(self.accept)
        self._buttons.rejected.connect(self.reject)
        layout.addWidget(self._buttons)

        self.tool = DesignMapTool(canvas, self.session)
        self.tool.stationRequested.connect(self._on_ground_clicked)
        self.tool.stationClicked.connect(self._on_station_clicked)
        self.tool.observationClicked.connect(self._on_observation_clicked)
        self.tool.canvasRightClicked.connect(self._clear_pending)
        self._previous_tool = canvas.mapTool()
        canvas.setMapTool(self.tool)

        self._refresh()

    # -- construction ----------------------------------------------------

    def _mode_group(self) -> QGroupBox:
        group = QGroupBox(_tr("Click on the map to…"), self)
        self._modes = QButtonGroup(group)
        row = QHBoxLayout(group)
        for mode, label, name in (
            (ADD_STATION, _tr("Add station"), "geocompPreAnalysisAdd"),
            (MOVE, _tr("Move"), "geocompPreAnalysisMove"),
            (CONNECT, _tr("Connect"), "geocompPreAnalysisConnect"),
            (REMOVE, _tr("Remove"), "geocompPreAnalysisRemove"),
        ):
            button = QRadioButton(label, group)
            button.setObjectName(name)
            button.setChecked(mode == ADD_STATION)
            self._modes.addButton(button, mode)
            row.addWidget(button)
        self._modes.idClicked.connect(self._on_mode_changed)
        return group

    def _settings_group(self) -> QGroupBox:
        group = QGroupBox(_tr("Design"), self)
        form = QFormLayout(group)

        self._observation_type = QComboBox(group)
        self._observation_type.setObjectName("geocompPreAnalysisObservationType")
        for value, label in (
            (ObservationType.HORIZONTAL_DISTANCE, _tr("Horizontal distance")),
            (ObservationType.DIRECTION, _tr("Direction")),
            (ObservationType.AZIMUTH, _tr("Azimuth")),
            (ObservationType.HEIGHT_DIFFERENCE, _tr("Height difference")),
        ):
            self._observation_type.addItem(label, value.name)

        self._tolerance = QDoubleSpinBox(group)
        self._tolerance.setObjectName("geocompPreAnalysisTolerance")
        self._tolerance.setSuffix(_tr(" mm"))
        self._tolerance.setDecimals(1)
        self._tolerance.setRange(0.0, 100000.0)
        self._tolerance.setSpecialValueText(_tr("(none)"))
        self._tolerance.setValue(5.0)
        self.session.tolerance = 0.005
        self._tolerance.valueChanged.connect(self._on_tolerance_changed)

        self._apply_precision = QPushButton(_tr("Apply"), group)
        self._apply_precision.setObjectName("geocompPreAnalysisApplyPrecision")
        self._apply_precision.clicked.connect(self._on_apply_required_precision)

        tolerance_row = QHBoxLayout()
        tolerance_row.addWidget(self._tolerance, stretch=1)
        tolerance_row.addWidget(self._apply_precision)

        form.addRow(_tr("Connect draws"), self._observation_type)
        form.addRow(_tr("Required precision"), tolerance_row)
        return group

    def _summary_group(self) -> QGroupBox:
        group = QGroupBox(_tr("Expected precision"), self)
        self._summary = QLabel(group)
        self._summary.setObjectName("geocompPreAnalysisSummary")
        self._summary.setWordWrap(True)

        self._table = QTableWidget(0, 4, group)
        self._table.setObjectName("geocompPreAnalysisTable")
        self._table.setHorizontalHeaderLabels(
            [
                _tr("Station"),
                _tr("Positional uncertainty (mm)"),
                _tr("Semi-major (mm)"),
                _tr("Semi-minor (mm)"),
            ]
        )
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        layout = QVBoxLayout(group)
        layout.addWidget(self._summary)
        layout.addWidget(self._table)
        return group

    def _observations_group(self) -> QGroupBox:
        group = QGroupBox(_tr("Planned observations"), self)
        self._observations_table = QTableWidget(0, 6, group)
        self._observations_table.setObjectName("geocompPreAnalysisObservationsTable")
        self._observations_table.setHorizontalHeaderLabels(
            [
                _tr("Observation"),
                _tr("Type"),
                _tr("Stations"),
                _tr("Standard deviation"),
                _tr("Required precision"),
                _tr("Redundancy"),
            ]
        )
        self._observations_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        layout = QVBoxLayout(group)
        layout.addWidget(self._observations_table)
        return group

    def _findings_group(self) -> QGroupBox:
        group = QGroupBox(_tr("Findings"), self)
        self._findings = QLabel(group)
        self._findings.setObjectName("geocompPreAnalysisFindings")
        self._findings.setWordWrap(True)
        self._findings.setTextFormat(Qt.TextFormat.RichText)
        layout = QVBoxLayout(group)
        layout.addWidget(self._findings)
        return group

    def _history_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        self._undo = QPushButton(_tr("Undo"), self)
        self._undo.setObjectName("geocompPreAnalysisUndo")
        self._undo.clicked.connect(self._on_undo)
        self._redo = QPushButton(_tr("Redo"), self)
        self._redo.setObjectName("geocompPreAnalysisRedo")
        self._redo.clicked.connect(self._on_redo)
        self._export_layer = QPushButton(_tr("Export layer"), self)
        self._export_layer.setObjectName("geocompPreAnalysisExportLayer")
        self._export_layer.clicked.connect(self._on_export_layer)
        self._import_layer = QPushButton(_tr("Import layer"), self)
        self._import_layer.setObjectName("geocompPreAnalysisImportLayer")
        self._import_layer.clicked.connect(self._on_import_layer)
        row.addWidget(self._undo)
        row.addWidget(self._redo)
        row.addStretch(1)
        row.addWidget(self._import_layer)
        row.addWidget(self._export_layer)
        return row

    # -- canvas interaction ----------------------------------------------

    def _on_mode_changed(self, mode: int) -> None:
        self.tool.mode = mode
        if self.canvas.mapTool() is not self.tool:
            self.canvas.setMapTool(self.tool)
        self._clear_pending()

    def _on_ground_clicked(self, easting: float, northing: float) -> None:
        if self.tool.mode == MOVE and self._pending:
            self.session.move_station(self._pending, easting, northing)
            self._clear_pending()
        elif self.tool.mode == ADD_STATION:
            self._counter += 1
            name = self._unused_name()
            self.session.add_station(name, easting, northing)
        self._refresh()

    def _on_station_clicked(self, station_id: str) -> None:
        if self.tool.mode == REMOVE:
            self.session.remove_station(station_id)
            self._clear_pending()
        elif self.tool.mode == MOVE:
            self._pending = station_id
        elif self.tool.mode == CONNECT:
            if self._pending is None:
                self._pending = station_id
            elif self._pending != station_id:
                self.session.add_observation(
                    ObservationType[self._observation_type.currentData()],
                    (self._pending, station_id),
                )
                self._pending = None
        self._refresh()

    def _on_observation_clicked(self, observation_id: str) -> None:
        if self.tool.mode == REMOVE and observation_id in self.session.network.observations:
            self.session.remove_observation(observation_id)
            self._clear_pending()

    def _clear_pending(self) -> None:
        self._pending = None
        self._refresh()

    def _on_undo(self) -> None:
        self.session.undo()
        self._clear_pending()

    def _on_redo(self) -> None:
        self.session.redo()
        self._clear_pending()

    def _on_tolerance_changed(self, value: float) -> None:
        self.session.tolerance = None if value <= 0.0 else value / 1000.0
        self._refresh()

    def _on_apply_required_precision(self) -> None:
        if self.session.apply_required_precisions():
            self._refresh()

    def _on_export_layer(self) -> None:
        if not self.session.network.stations:
            return
        if self.exported_geojson_path is not None:
            default_path = str(self.exported_geojson_path)
        else:
            default_dir = QgsProject.instance().homePath() or str(Path.home())
            default_name = f"{self.session.network.id or 'design'}_planned_network.geojson"
            default_path = str(Path(default_dir) / default_name)

        destination, _filter = QFileDialog.getSaveFileName(
            self,
            _tr("Export layer"),
            default_path,
            "GeoJSON (*.geojson);;All files (*)",
        )
        if not destination:
            return
        target = Path(destination)
        if target.suffix.lower() != ".geojson":
            target = target.with_suffix(".geojson")
        self.export_layer_to_project(name=target.stem, path=target)

    def _on_import_layer(self) -> None:
        project_layers = [
            layer
            for layer in QgsProject.instance().mapLayers().values()
            if isinstance(layer, QgsVectorLayer) and is_preanalysis_network_layer(layer)
        ]
        if project_layers:
            self.import_from_layer(project_layers[-1])
            return

        source, _filter = QFileDialog.getOpenFileName(
            self,
            _tr("Import layer"),
            "",
            "GeoPackage / GeoJSON / JSON (*.gpkg *.geojson *.json *.shp);;All files (*)",
        )
        if not source:
            return
        self.import_from_path(source)

    def to_vector_layers(
        self, name: str = "", path: str | Path | None = None
    ) -> tuple[QgsVectorLayer, QgsVectorLayer]:
        """Write a single ``.geojson`` containing both stations (``Point``) and observations
        (``LineString``), and return the two QGIS layers backed by that file."""
        return network_to_vector_layers(
            self.session, name=name or _tr("Planned network"), path=path
        )

    def to_vector_layer(
        self, name: str = "", path: str | Path | None = None
    ) -> QgsVectorLayer:
        """Build the planned-observations QGIS vector layer from the shared ``.geojson`` datasource."""
        _stations_layer, observations_layer = self.to_vector_layers(name=name, path=path)
        return observations_layer

    def export_layer_to_project(
        self, name: str = "", path: str | Path | None = None
    ) -> tuple[QgsVectorLayer, QgsVectorLayer]:
        """Export the current design to a single ``.geojson`` file and add both the stations
        (``Point``) and observations (``LineString``) layers to the active QGIS project."""
        project = QgsProject.instance()
        for prev in self.exported_layers:
            if prev is not None and prev.id() in project.mapLayers():
                project.removeMapLayer(prev.id())
        stations_layer, observations_layer = self.to_vector_layers(name=name, path=path)
        project.addMapLayer(observations_layer)
        project.addMapLayer(stations_layer)
        raw_source = stations_layer.source() or ""
        self.exported_geojson_path = Path(raw_source.split("|", 1)[0]) if raw_source else None
        self.exported_stations_layer = stations_layer
        self.exported_observations_layer = observations_layer
        self.exported_layers = (stations_layer, observations_layer)
        self.exported_layer = observations_layer
        return stations_layer, observations_layer

    def import_from_layer(self, layer: QgsVectorLayer) -> bool:
        """Import a planned network from *layer* (or its paired ``.geojson`` sublayers) into the session."""
        if layer is None or not layer.isValid() or not is_preanalysis_network_layer(layer):
            return False
        imported = session_from_vector_layer(layer)
        if not imported.network.stations:
            return False
        self.session.load_network(imported.network, tolerance=imported.tolerance)
        self.session.frame = imported.frame
        self.session.datum = imported.datum
        self.session.confidence = imported.confidence
        self._tolerance.blockSignals(True)
        self._tolerance.setValue(
            0.0 if self.session.tolerance is None else self.session.tolerance * 1000.0
        )
        self._tolerance.blockSignals(False)
        self._clear_pending()
        return True

    def import_from_path(self, path: str) -> bool:
        """Import a planned network from a file.

        A ``.geojson`` or other vector layer file, or a GeoComp network JSON document.
        """
        source = Path(path)
        if source.is_file() and source.suffix.lower() in {".geojson", ".json"}:
            try:
                payload = json.loads(source.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                # Not a JSON document after all: read below as a vector layer.
                payload = None
            if isinstance(payload, dict) and payload.get("type") == "FeatureCollection":
                imported = DesignSession.from_geojson_dict(payload)
                if imported.network.stations:
                    self.session.load_network(imported.network, tolerance=imported.tolerance)
                    self.session.frame = imported.frame
                    self.session.datum = imported.datum
                    self.session.confidence = imported.confidence
                    self._tolerance.blockSignals(True)
                    self._tolerance.setValue(
                        0.0 if self.session.tolerance is None else self.session.tolerance * 1000.0
                    )
                    self._tolerance.blockSignals(False)
                    self._clear_pending()
                    return True
            elif isinstance(payload, dict):
                try:
                    network = network_from_document(payload)
                except Exception:  # noqa: BLE001 -- any refusal means "not a network document"
                    network = None
                if network is not None:
                    self.session.load_network(network)
                    self._clear_pending()
                    return True

        layer = QgsVectorLayer(path, "imported_network", "ogr")
        if layer.isValid() and is_preanalysis_network_layer(layer):
            return self.import_from_layer(layer)
        return False

    def _unused_name(self) -> str:
        while True:
            candidate = f"P{self._counter}"
            if candidate not in self.session.network.stations:
                return candidate
            self._counter += 1

    # -- rendering -------------------------------------------------------

    def _refresh(self) -> None:
        """Re-evaluate and repaint. Called after every edit, because a panel
        that lagged one click behind would be worse than none: the user would
        be reading the design they had before the change they just made."""
        state = self.session.evaluate()
        self._render_panel(state)
        self._render_canvas(state)
        self._undo.setEnabled(self.session.can_undo)
        self._redo.setEnabled(self.session.can_redo)
        self._export_layer.setEnabled(bool(self.session.network.stations))
        self._apply_precision.setEnabled(state.is_evaluable and self.session.tolerance is not None)
        self._buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(state.is_evaluable)

    def _render_panel(self, state) -> None:
        report = state.report
        self._table.setRowCount(0 if report is None else len(report.stations))
        if report is None:
            self._summary.setText(_tr("Nothing to evaluate yet."))
        else:
            worst = report.worst_station()
            self._summary.setText(
                _tr(
                    "%1 station(s), %2 observation(s), %3 degree(s) of freedom. Worst: %4 mm at %5."
                )
                .replace("%1", str(len(report.stations)))
                .replace("%2", str(report.observation_count))
                .replace("%3", str(report.degrees_of_freedom))
                .replace("%4", localised(f"{worst.positional_uncertainty * 1000:.1f}"))
                .replace("%5", worst.station_id)
            )
            for row, station in enumerate(report.stations):
                for column, text in enumerate(
                    (
                        station.station_id,
                        localised(f"{station.positional_uncertainty * 1000:.1f}"),
                        localised(f"{station.ellipse.semi_major * 1000:.1f}"),
                        localised(f"{station.ellipse.semi_minor * 1000:.1f}"),
                    )
                ):
                    self._table.setItem(row, column, QTableWidgetItem(text))

        self._render_observations(report)

        if not state.findings:
            self._findings.setText(_tr("Nothing to report."))
        else:
            self._findings.setText(
                "<br>".join(
                    f"<span style='color:{'#d55e00' if f.is_blocking else '#e69f00'}'>"
                    f"{escape(finding_text(f))}</span>"
                    for f in state.findings
                )
            )

    def _render_observations(self, report) -> None:
        observations = list(self.session.network.observations.values())
        self._observations_table.setRowCount(len(observations))
        reliability_by_id = report.reliability.by_observation() if report is not None else {}
        required_by_id = (
            self.session.required_observation_sigmas(report) if report is not None else {}
        )
        for row, observation in enumerate(observations):
            quantity = observation.values[0]
            assumed_text = _format_observation_sigma(quantity.std_dev, quantity.unit)
            required_sigma = required_by_id.get(observation.id)
            required_text = (
                "—"
                if required_sigma is None
                else _format_observation_sigma(required_sigma, quantity.unit)
            )
            reliability = reliability_by_id.get(observation.id)
            redundancy_text = (
                "—" if reliability is None else localised(f"{reliability.redundancy:.2f}")
            )
            for column, text in enumerate(
                (
                    observation.id,
                    _type_label(observation.type),
                    " → ".join(observation.stations),
                    assumed_text,
                    required_text,
                    redundancy_text,
                )
            ):
                self._observations_table.setItem(row, column, QTableWidgetItem(text))

    def _render_canvas(self, state) -> None:
        self._clear_canvas()
        positions = {}
        for station in self.session.network.stations.values():
            if station.approx_position is None:
                continue
            east, north, _up = station.approx_position.values
            positions[station.id] = QgsPointXY(east.value, north.value)
            marker = QgsVertexMarker(self.canvas)
            marker.setCenter(positions[station.id])
            marker.setIconType(QgsVertexMarker.IconType.ICON_CIRCLE)
            marker.setIconSize(10)
            marker.setPenWidth(3)
            marker.setColor(
                _SELECTED_COLOUR if station.id == self._pending else _STATION_COLOUR
            )
            self._markers.append(marker)

        for observation in self.session.network.observations.values():
            points = [positions[name] for name in observation.stations if name in positions]
            if len(points) < 2:
                continue
            band = QgsRubberBand(self.canvas, QgsWkbTypes.GeometryType.LineGeometry)
            band.setColor(_OBSERVATION_COLOUR)
            band.setWidth(2)
            for point in points:
                band.addPoint(point, False)
            band.updatePosition()
            band.show()
            self._bands.append(band)

        if state.report is not None:
            self._render_ellipses(state.report, positions)

    def _render_ellipses(self, report, positions) -> None:
        """Expected ellipses, exaggerated by a factor fitted to the extent.

        Stated in the group box's title, because an unstated exaggeration turns
        a quality visualisation into a misrepresentation (FR-901) -- and this is
        the view a user judges a design by.
        """
        extent = self.canvas.extent()
        self.exaggeration = default_exaggeration(
            (extent.width(), extent.height()),
            [station.ellipse.semi_major for station in report.stations],
        )
        for station in report.stations:
            centre = positions.get(station.station_id)
            if centre is None:
                continue
            drawn = ellipse_ring(
                (centre.x(), centre.y()), station.ellipse, exaggeration=self.exaggeration
            )
            band = QgsRubberBand(self.canvas, QgsWkbTypes.GeometryType.PolygonGeometry)
            band.setColor(_ELLIPSE_COLOUR)
            band.setFillColor(QColor(213, 94, 0, 30))
            band.setWidth(1)
            for east, north in drawn.ring:
                band.addPoint(QgsPointXY(east, north), False)
            band.updatePosition()
            band.show()
            self._bands.append(band)

        self._summary.parent().setTitle(
            _tr("Expected precision (ellipses exaggerated %1x)").replace(
                "%1", f"{self.exaggeration:g}"
            )
        )

    def _clear_canvas(self) -> None:
        for marker in self._markers:
            self.canvas.scene().removeItem(marker)
        for band in self._bands:
            self.canvas.scene().removeItem(band)
        self._markers.clear()
        self._bands.clear()

    # -- lifecycle -------------------------------------------------------

    def exec(self) -> int:
        """Run the dialog without modal-blocking the map canvas.

        ``QDialog.exec()`` sets ``Qt.WA_ShowModal``, which makes the dialog the
        application's active modal widget and causes Qt to drop every mouse
        event on the QGIS main window and map canvas. Showing the dialog with
        ``NonModal`` and spinning a local :class:`QEventLoop` until
        :attr:`finished` fires keeps the caller waiting for ``Accepted`` or
        ``Rejected`` while leaving the canvas free to receive
        :class:`DesignMapTool` clicks.
        """
        self.setModal(False)
        self.setWindowModality(Qt.WindowModality.NonModal)
        self.show()
        self.raise_()
        loop = QEventLoop(self)
        self.finished.connect(loop.exit)
        self.destroyed.connect(loop.quit)
        return loop.exec()

    def done(self, result: int) -> None:
        """Always give the canvas back.

        A dialog that left its map tool installed would leave the user clicking
        stations into a design that is no longer on screen, with no way to tell
        why the canvas had stopped behaving.
        """
        self._clear_canvas()
        if self.canvas.mapTool() is self.tool:
            if self._previous_tool is None:
                # ``setMapTool(None)`` does not clear the current tool -- the
                # canvas keeps it -- so a canvas that had no tool before would
                # be left holding this one, still turning clicks into stations
                # for a design no longer on screen.
                self.canvas.unsetMapTool(self.tool)
            else:
                self.canvas.setMapTool(self._previous_tool)
        super().done(result)

    def network(self) -> Network:
        """The design as a network, ready to write out and evaluate in full."""
        return self.session.network


def _canvas_crs(canvas) -> str:
    try:
        return canvas.mapSettings().destinationCrs().authid()
    except AttributeError:  # pragma: no cover - only a canvas double lacks this
        return ""


def _type_label(observation_type: ObservationType) -> str:
    labels = {
        ObservationType.HORIZONTAL_DISTANCE: _tr("Horizontal distance"),
        ObservationType.DIRECTION: _tr("Direction"),
        ObservationType.AZIMUTH: _tr("Azimuth"),
        ObservationType.HEIGHT_DIFFERENCE: _tr("Height difference"),
    }
    return labels.get(observation_type, observation_type.name.replace("_", " ").capitalize())


def _format_observation_sigma(sigma: float, unit: Unit) -> str:
    if unit is Unit.METRE:
        return f"{localised(f'{sigma * 1000.0:.2f}')} mm"
    if unit is Unit.RADIAN:
        return f'{localised(f"{math.degrees(sigma) * 3600.0:.2f}")}″'
    return localised(f"{sigma:.4g}")


def _segment_distance(
    px: float, py: float, x1: float, y1: float, x2: float, y2: float
) -> float:
    dx = x2 - x1
    dy = y2 - y1
    length_sq = dx * dx + dy * dy
    if length_sq <= 0.0:
        return math.hypot(px - x1, py - y1)
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / length_sq))
    proj_x = x1 + t * dx
    proj_y = y1 + t * dy
    return math.hypot(px - proj_x, py - proj_y)


def network_layer_fields() -> QgsFields:
    """The attribute fields of an exported pre-analysis network layer."""
    fields = QgsFields()
    for name, field_type in NETWORK_LAYER_FIELDS:
        fields.append(QgsField(name, field_type))
    return fields


def network_layer_features(session: DesignSession) -> list[QgsFeature]:
    """Build one :class:`QgsFeature` per station (``Point``) and planned observation (``LineString``)."""
    fields = network_layer_fields()
    features: list[QgsFeature] = []
    for record in session.to_feature_records():
        feature = QgsFeature(fields)
        if record.get("record_kind") == "station":
            east = float(record.get("easting") or record.get("from_easting") or 0.0)
            north = float(record.get("northing") or record.get("from_northing") or 0.0)
            feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(east, north)))
        else:
            fe = float(record.get("from_easting") or 0.0)
            fn = float(record.get("from_northing") or 0.0)
            te = float(record.get("to_easting") or fe)
            tn = float(record.get("to_northing") or fn)
            feature.setGeometry(
                QgsGeometry.fromPolylineXY([QgsPointXY(fe, fn), QgsPointXY(te, tn)])
            )
        feature.setAttributes([record.get(name) for name, _type in NETWORK_LAYER_FIELDS])
        features.append(feature)
    return features


def write_network_geojson(
    session: DesignSession, path: str | Path | None = None
) -> Path:
    """Write the planned network as a single ``.geojson`` containing both ``Point`` (station)
    and ``LineString`` (observation) features."""
    if path is None:
        home = QgsProject.instance().homePath()
        if home and Path(home).is_dir():
            target = Path(home) / f"{session.network.id or 'design'}_planned_network.geojson"
        else:
            handle = tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".geojson",
                prefix="geocomp-planned-network-",
                delete=False,
                encoding="utf-8",
            )
            handle.close()
            target = Path(handle.name)
    else:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)

    payload = session.to_geojson_dict()
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


def network_to_vector_layers(
    session: DesignSession, name: str = "", path: str | Path | None = None
) -> tuple[QgsVectorLayer, QgsVectorLayer]:
    """Write a single ``.geojson`` datasource containing both station ``Point`` features and
    observation ``LineString`` features, and open it as two QGIS OGR layers."""
    target = write_network_geojson(session, path=path)
    base_name = name or _tr("Planned network")
    stations_layer = QgsVectorLayer(
        f"{target}|geometrytype=Point",
        f"{base_name} — {_tr('Stations')}",
        "ogr",
    )
    observations_layer = QgsVectorLayer(
        f"{target}|geometrytype=LineString",
        f"{base_name} — {_tr('Planned observations')}",
        "ogr",
    )
    for layer in (stations_layer, observations_layer):
        layer.setCustomProperty(NETWORK_LAYER_PROPERTY, "true")
        layer.setCustomProperty(NETWORK_GEOJSON_PROPERTY, str(target))
    return stations_layer, observations_layer


def network_to_vector_layer(
    session: DesignSession, name: str = "", path: str | Path | None = None
) -> QgsVectorLayer:
    """Create the planned-observations :class:`QgsVectorLayer` backed by the network ``.geojson``."""
    _stations_layer, observations_layer = network_to_vector_layers(
        session, name=name, path=path
    )
    return observations_layer


def is_preanalysis_network_layer(layer: QgsVectorLayer) -> bool:
    """Whether *layer* carries the attributes needed to reconstruct a pre-analysis network."""
    if layer is None or not layer.isValid():
        return False
    if layer.customProperty(NETWORK_LAYER_PROPERTY) == "true":
        return True
    names = {field.name() for field in layer.fields()}
    return (
        {"from_station", "to_station", "observation_type"} <= names
        or {"station_id", "station_type", "record_kind"} <= names
    )


def session_from_vector_layer(layer: QgsVectorLayer) -> DesignSession:
    """Reconstruct a :class:`DesignSession` from an exported pre-analysis :class:`QgsVectorLayer`
    (reading both ``Point`` station and ``LineString`` observation layers sharing its datasource)."""
    raw_source = (
        layer.customProperty(NETWORK_GEOJSON_PROPERTY)
        or (layer.source() or "").split("|", 1)[0]
    )
    layers_to_read: list[QgsVectorLayer] = []
    seen_ids: set[str] = set()

    if raw_source:
        for proj_layer in QgsProject.instance().mapLayers().values():
            if not isinstance(proj_layer, QgsVectorLayer) or not proj_layer.isValid():
                continue
            proj_base = (
                proj_layer.customProperty(NETWORK_GEOJSON_PROPERTY)
                or (proj_layer.source() or "").split("|", 1)[0]
            )
            if proj_base and str(proj_base) == str(raw_source):
                layers_to_read.append(proj_layer)
                seen_ids.add(proj_layer.id())

    if layer.id() not in seen_ids:
        layers_to_read.append(layer)

    source_path = Path(str(raw_source)) if raw_source else None
    if source_path is not None and source_path.is_file():
        wkb_types = {
            QgsWkbTypes.geometryType(candidate.wkbType()) for candidate in layers_to_read
        }
        if QgsWkbTypes.GeometryType.PointGeometry not in wkb_types:
            pt_layer = QgsVectorLayer(f"{source_path}|geometrytype=Point", "stations", "ogr")
            if pt_layer.isValid():
                layers_to_read.insert(0, pt_layer)
        if QgsWkbTypes.GeometryType.LineGeometry not in wkb_types:
            ln_layer = QgsVectorLayer(
                f"{source_path}|geometrytype=LineString", "observations", "ogr"
            )
            if ln_layer.isValid():
                layers_to_read.append(ln_layer)

    records: list[dict[str, object]] = []
    for candidate in layers_to_read:
        records.extend(_records_from_single_layer(candidate))
    return DesignSession.from_feature_records(records, default_crs=layer.crs().authid())


def _records_from_single_layer(layer: QgsVectorLayer) -> list[dict[str, object]]:
    field_names = [field.name() for field in layer.fields()]
    records: list[dict[str, object]] = []
    for feature in layer.getFeatures():
        record: dict[str, object] = {
            name: _clean_attribute(feature[name]) for name in field_names
        }
        geometry = feature.geometry()
        if geometry is not None and not geometry.isEmpty():
            gtype = QgsWkbTypes.geometryType(geometry.wkbType())
            if gtype == QgsWkbTypes.GeometryType.PointGeometry or record.get("record_kind") == "station":
                pt = _extract_point(geometry)
                if pt is not None:
                    px, py = pt
                    record.setdefault("record_kind", "station")
                    record["easting"] = px
                    record["northing"] = py
                    record["from_easting"] = px
                    record["from_northing"] = py
            else:
                points = _extract_endpoints(geometry)
                if points is not None:
                    (x1, y1), (x2, y2) = points
                    fe = record.get("from_easting")
                    fn = record.get("from_northing")
                    if (
                        fe is None
                        or fn is None
                        or math.hypot(x1 - float(fe), y1 - float(fn)) > 1e-6
                    ):
                        record["from_easting"] = x1
                        record["from_northing"] = y1
                    te = record.get("to_easting")
                    tn = record.get("to_northing")
                    if (
                        te is None
                        or tn is None
                        or math.hypot(x2 - float(te), y2 - float(tn)) > 1e-6
                    ):
                        record["to_easting"] = x2
                        record["to_northing"] = y2
        records.append(record)
    return records


def _clean_attribute(value: Any) -> object:
    if isinstance(value, QVariant):
        return None if value.isNull() else value.value()
    return value


def _extract_point(geometry: QgsGeometry) -> tuple[float, float] | None:
    try:
        if geometry.isMultipart():
            pts = geometry.asMultiPoint()
            if pts:
                return float(pts[0].x()), float(pts[0].y())
        else:
            pt = geometry.asPoint()
            return float(pt.x()), float(pt.y())
    except Exception:  # noqa: BLE001 -- a geometry QGIS cannot read is no point
        return None
    return None


def _extract_endpoints(
    geometry: QgsGeometry,
) -> tuple[tuple[float, float], tuple[float, float]] | None:
    try:
        if geometry.isMultipart():
            lines = geometry.asMultiPolyline()
            if lines and lines[0]:
                first = lines[0][0]
                last = lines[-1][-1]
                return (float(first.x()), float(first.y())), (float(last.x()), float(last.y()))
        else:
            line = geometry.asPolyline()
            if line:
                first = line[0]
                last = line[-1]
                return (float(first.x()), float(first.y())), (float(last.x()), float(last.y()))
            point = geometry.asPoint()
            return (float(point.x()), float(point.y())), (float(point.x()), float(point.y()))
    except Exception:  # noqa: BLE001 -- a geometry QGIS cannot read is no line
        return None
    return None
