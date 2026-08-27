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

import math

from qgis.core import QgsPointXY, QgsWkbTypes
from qgis.gui import QgsMapTool, QgsRubberBand, QgsVertexMarker
from qgis.PyQt.QtCore import QCoreApplication, Qt, pyqtSignal
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
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

from geocomp.core.models import ObservationType
from geocomp.core.preanalysis.session import DesignSession
from geocomp.core.visualization import default_exaggeration, ellipse_ring

__all__ = ["ADD_STATION", "CONNECT", "MOVE", "REMOVE", "DesignMapTool", "PreAnalysisDialog"]

_TR_CONTEXT = "GeoCompPreAnalysis"

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


class PreAnalysisDialog(QDialog):
    """Place a design on the canvas and watch what it would achieve."""

    def __init__(self, canvas, crs: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("geocompPreAnalysisDialog")
        self.setWindowTitle(_tr("GeoComp — Interactive pre-analysis"))
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.Tool)
        self.resize(520, 720)

        self.canvas = canvas
        self.session = DesignSession(crs=crs or _canvas_crs(canvas))
        self._pending: str | None = None
        self._markers: list[QgsVertexMarker] = []
        self._bands: list[QgsRubberBand] = []
        self._counter = 0
        self.exaggeration = 1.0

        layout = QVBoxLayout(self)
        layout.addWidget(self._mode_group())
        layout.addWidget(self._settings_group())
        layout.addWidget(self._summary_group(), stretch=1)
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
        self._tolerance.valueChanged.connect(self._on_tolerance_changed)

        form.addRow(_tr("Connect draws"), self._observation_type)
        form.addRow(_tr("Required precision"), self._tolerance)
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
        row.addWidget(self._undo)
        row.addWidget(self._redo)
        row.addStretch(1)
        return row

    # -- canvas interaction ----------------------------------------------

    def _on_mode_changed(self, mode: int) -> None:
        self.tool.mode = mode
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
                .replace("%4", f"{worst.positional_uncertainty * 1000:.1f}")
                .replace("%5", worst.station_id)
            )
            for row, station in enumerate(report.stations):
                for column, text in enumerate(
                    (
                        station.station_id,
                        f"{station.positional_uncertainty * 1000:.1f}",
                        f"{station.ellipse.semi_major * 1000:.1f}",
                        f"{station.ellipse.semi_minor * 1000:.1f}",
                    )
                ):
                    self._table.setItem(row, column, QTableWidgetItem(text))

        if not state.findings:
            self._findings.setText(_tr("Nothing to report."))
        else:
            self._findings.setText(
                "<br>".join(
                    f"<span style='color:{'#d55e00' if f.is_blocking else '#e69f00'}'>"
                    f"{f.message}</span>"
                    for f in state.findings
                )
            )

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

    def done(self, result: int) -> None:
        """Always give the canvas back.

        A dialog that left its map tool installed would leave the user clicking
        stations into a design that is no longer on screen, with no way to tell
        why the canvas had stopped behaving.
        """
        self._clear_canvas()
        if self.canvas.mapTool() is self.tool:
            self.canvas.setMapTool(self._previous_tool)
        super().done(result)

    def network(self):
        """The design as a network, ready to write out and evaluate in full."""
        return self.session.network


def _canvas_crs(canvas) -> str:
    try:
        return canvas.mapSettings().destinationCrs().authid()
    except AttributeError:  # pragma: no cover - only a canvas double lacks this
        return ""
