# SPDX-License-Identifier: GPL-2.0-or-later
"""The time-series panel (FR-838, FR-903; ``specs/19`` section 5, phase P10b).

A dockable panel plotting stations' offsets across the monitoring epochs: per
component, with the uncertainty band, the fitted velocity line, the alert
limits, and each epoch's metadata on hover.

**The map and the plot are one selection.** A layer written by *Time series
and velocities* carries the path of its series document
(:data:`~geocomp.algorithms.monitoring.time_series.SERIES_PROPERTY`). When such
a layer is added to the project the panel attaches to it: selecting stations on
the map plots them, overlaid; clicking a point in the plot selects that station
on the map and shows that epoch. ``specs/19`` calls this the interaction that
makes monitoring analysis in a GIS worth doing.

What is drawn comes from :func:`~geocomp.core.visualization.monitoring.series_curves`,
the function the report's plots use, so the panel and the report cannot show
two different bands. The panel exports the plotted rows as CSV and the plot as
an image.
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any

from qgis.core import QgsProject, QgsVectorLayer
from qgis.gui import QgsDockWidget
from qgis.PyQt.QtCore import QCoreApplication, QPointF, QRectF, Qt, pyqtSignal
from qgis.PyQt.QtGui import QColor, QImage, QPainter, QPainterPath, QPen, QPolygonF
from qgis.PyQt.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from geocomp.core.errors import GeoCompError
from geocomp.core.monitoring import read_series_document
from geocomp.core.monitoring.document import SERIES_PROPERTY
from geocomp.core.number_format import localised
from geocomp.core.statistics.distributions import normal_quantile
from geocomp.core.visualization.monitoring import Curve, series_curves, series_limits

__all__ = ["SeriesPlot", "TimeSeriesPanel", "attach_to_project", "detach_from_project"]

_TR_CONTEXT = "GeoCompTimeSeries"


#: Okabe--Ito, colour-vision-deficiency safe, one per overlaid station.
_PALETTE = ("#0072b2", "#d55e00", "#009e73", "#cc79a7", "#e69f00", "#56b4e9", "#000000")
_ALERT = "#d55e00"


def _tr(text: str) -> str:
    return QCoreApplication.translate(_TR_CONTEXT, text)


class SeriesPlot(QWidget):
    """The plot: curves, bands, fitted lines and limits, in millimetres.

    Emits :attr:`picked` with the station and the index of the epoch clicked.
    """

    picked = pyqtSignal(str, int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(320, 200)
        self.setMouseTracking(True)
        self.curves: list[Curve] = []
        self.limits: list[float] = []
        self.highlight: tuple[str, int] | None = None
        self._points: list[tuple[QPointF, str, int]] = []

    def set_curves(self, curves: list[Curve], limits: list[float]) -> None:
        self.curves = curves
        self.limits = [1000.0 * limit for limit in limits]
        self.highlight = None
        self.update()

    # -- geometry ------------------------------------------------------------

    def _bounds(self) -> tuple[float, float, float, float]:
        epochs = [t for c in self.curves for t in c.epochs]
        values = [v for c in self.curves for v in (*c.low, *c.high)] + [0.0]
        values += [s * limit for limit in self.limits for s in (1.0, -1.0)]
        t0, t1 = min(epochs), max(epochs)
        low, high = min(values), max(values)
        pad = 0.08 * ((high - low) or 1.0)
        return t0, (t1 - t0) or 1.0, low - pad, (high - low + 2 * pad) or 1.0

    def _mapper(self):
        t0, span_t, low, span_v = self._bounds()
        left, right, top, bottom = 52.0, 12.0, 12.0, 28.0
        width = max(1.0, self.width() - left - right)
        height = max(1.0, self.height() - top - bottom)

        def to_screen(t: float, v: float) -> QPointF:
            return QPointF(left + (t - t0) / span_t * width, top + (low + span_v - v) / span_v * height)

        return to_screen, (left, top, width, height), (low, low + span_v)

    # -- painting ------------------------------------------------------------

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        try:
            self.paint(painter)
        finally:
            painter.end()

    def paint(self, painter: QPainter) -> None:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#ffffff"))
        self._points = []
        if not self.curves:
            painter.drawText(
                QRectF(self.rect()),
                Qt.AlignmentFlag.AlignCenter,
                _tr("Select stations on a velocity layer, or open a series document."),
            )
            return
        to_screen, (left, top, width, height), (low, high) = self._mapper()
        painter.setPen(QPen(QColor("#000000")))
        painter.drawRect(QRectF(left, top, width, height))
        zero = to_screen(self.curves[0].epochs[0], 0.0)
        painter.setPen(QPen(QColor("#999999")))
        painter.drawLine(QPointF(left, zero.y()), QPointF(left + width, zero.y()))
        self._axis_labels(painter, to_screen, low, high)
        dashed = QPen(QColor(_ALERT))
        dashed.setStyle(Qt.PenStyle.DashLine)
        for limit in self.limits:
            for value in (limit, -limit):
                y = to_screen(self.curves[0].epochs[0], value).y()
                painter.setPen(dashed)
                painter.drawLine(QPointF(left, y), QPointF(left + width, y))
        for number, curve in enumerate(self.curves):
            colour = QColor(_PALETTE[number % len(_PALETTE)])
            band = QColor(colour)
            band.setAlpha(40)
            polygon = QPolygonF(
                [to_screen(t, v) for t, v in zip(curve.epochs, curve.high, strict=True)]
                + [to_screen(t, v) for t, v in reversed(list(zip(curve.epochs, curve.low, strict=True)))]
            )
            path = QPainterPath()
            path.addPolygon(polygon)
            painter.fillPath(path, band)
            if curve.fit is not None:
                pen = QPen(colour)
                pen.setStyle(Qt.PenStyle.DotLine)
                painter.setPen(pen)
                (ta, a), (tb, b) = curve.fit
                painter.drawLine(to_screen(ta, a), to_screen(tb, b))
            painter.setPen(QPen(colour))
            painter.setBrush(colour)
            for index, (t, v, lo, hi) in enumerate(
                zip(curve.epochs, curve.values, curve.low, curve.high, strict=True)
            ):
                point = to_screen(t, v)
                painter.drawLine(to_screen(t, lo), to_screen(t, hi))
                radius = 5.0 if self.highlight == (curve.station, index) else 3.0
                painter.drawEllipse(point, radius, radius)
                self._points.append((point, curve.station, index))
            painter.drawText(QPointF(left + 6, top + 14 + 14 * number), curve.station)

    def _axis_labels(self, painter: QPainter, to_screen, low: float, high: float) -> None:
        painter.setPen(QPen(QColor("#333333")))
        epochs = sorted({t for c in self.curves for t in c.epochs})
        for epoch in epochs:
            point = to_screen(epoch, low)
            painter.drawText(QPointF(point.x() - 16, point.y() + 16), localised(f"{epoch:.2f}"))
        for value in (low, 0.0, high):
            point = to_screen(epochs[0], value)
            painter.drawText(QPointF(4, point.y() + 4), localised(f"{value:.1f}"))

    # -- picking -------------------------------------------------------------

    def nearest(self, position: QPointF, tolerance: float = 8.0) -> tuple[str, int] | None:
        best, best_distance = None, tolerance
        for point, station, index in self._points:
            distance = math.hypot(point.x() - position.x(), point.y() - position.y())
            if distance <= best_distance:
                best, best_distance = (station, index), distance
        return best

    def mousePressEvent(self, event) -> None:
        hit = self.nearest(event.position() if hasattr(event, "position") else QPointF(event.pos()))
        if hit is not None:
            self.highlight = hit
            self.update()
            self.picked.emit(*hit)

    def mouseMoveEvent(self, event) -> None:
        hit = self.nearest(event.position() if hasattr(event, "position") else QPointF(event.pos()))
        self.setToolTip(self.describe(*hit) if hit else "")

    def describe(self, station: str, index: int) -> str:
        for curve in self.curves:
            if curve.station == station:
                value = curve.values[index]
                band = curve.high[index] - value
                return (
                    _tr("%1, epoch %2 (%3): %4 ± %5 mm")
                    .replace("%1", station)
                    .replace("%2", localised(f"{curve.epochs[index]:.4f}"))
                    .replace("%3", curve.solutions[index])
                    .replace("%4", localised(f"{value:.2f}"))
                    .replace("%5", localised(f"{band:.2f}"))
                )
        return ""

    def image(self, width: int = 960, height: int = 540) -> QImage:
        """The plot rendered off screen at a fixed size, for export."""
        image = QImage(width, height, QImage.Format.Format_ARGB32)
        size = self.size()
        self.resize(width, height)
        painter = QPainter(image)
        try:
            self.paint(painter)
        finally:
            painter.end()
            self.resize(size)
        return image


class TimeSeriesPanel(QgsDockWidget):
    """The dockable panel, and its tie to a velocity layer on the map."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(_tr("GeoComp time series"), parent)
        self.setObjectName("geocompTimeSeriesPanel")
        self.document: dict[str, Any] | None = None
        self.path = ""
        self.layer: QgsVectorLayer | None = None
        self._syncing = False

        body = QWidget(self)
        layout = QVBoxLayout(body)
        bar = QHBoxLayout()
        self.open_button = QPushButton(_tr("Open series…"), body)
        self.component = QComboBox(body)
        self.csv_button = QPushButton(_tr("Export CSV…"), body)
        self.image_button = QPushButton(_tr("Export image…"), body)
        for widget in (self.open_button, self.component, self.csv_button, self.image_button):
            bar.addWidget(widget)
        layout.addLayout(bar)
        split = QSplitter(Qt.Orientation.Horizontal, body)
        self.stations = QListWidget(split)
        self.stations.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.plot = SeriesPlot(split)
        split.addWidget(self.stations)
        split.addWidget(self.plot)
        split.setStretchFactor(1, 4)
        layout.addWidget(split)
        self.status = QLabel(body)
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.setWidget(body)

        self.open_button.clicked.connect(self._open)
        self.csv_button.clicked.connect(self._export_csv)
        self.image_button.clicked.connect(self._export_image)
        self.component.currentIndexChanged.connect(self.refresh)
        self.stations.itemSelectionChanged.connect(self._list_changed)
        self.plot.picked.connect(self.pick)

    # -- the document ----------------------------------------------------------

    def load(self, path: str) -> None:
        """Read the series document at *path* and show it."""
        try:
            document = read_series_document(json.loads(Path(path).read_text(encoding="utf-8")))
        except (OSError, ValueError, GeoCompError) as error:
            from geocomp.services.messages import reason_for

            self.status.setText(
                _tr("The series document could not be read: %1").replace("%1", reason_for(error))
            )
            return
        self.path = path
        self.set_document(document)

    def set_document(self, document: dict[str, Any]) -> None:
        self.document = document
        self._syncing = True
        try:
            self.component.clear()
            for name in document["components"]:
                self.component.addItem(_component(name), name)
            self.stations.clear()
            for record in document["stations"]:
                self.stations.addItem(QListWidgetItem(record["station"]))
        finally:
            self._syncing = False
        self.status.setText(
            _tr("%1 stations over %2 epochs; band %3% confidence.")
            .replace("%1", str(len(document["stations"])))
            .replace("%2", str(len(document["epochs"])))
            .replace("%3", f"{100.0 * document['confidence']:g}")
        )
        self.refresh()

    def selected_stations(self) -> list[str]:
        return [item.text() for item in self.stations.selectedItems()]

    def select_stations(self, stations: list[str]) -> None:
        """Select *stations* in the list, which plots them."""
        wanted = set(stations)
        self._syncing = True
        try:
            for row in range(self.stations.count()):
                item = self.stations.item(row)
                item.setSelected(item.text() in wanted)
        finally:
            self._syncing = False
        self.refresh()

    def refresh(self) -> None:
        if self.document is None:
            self.plot.set_curves([], [])
            return
        component = self.component.currentData() or (self.document["components"] or [""])[0]
        stations = self.selected_stations()
        factor = normal_quantile(0.5 + self.document["confidence"] / 2.0)
        curves = series_curves(self.document, stations, component, band_factor=factor)
        limits = sorted({limit for s in stations for limit in series_limits(self.document, s, component)})
        self.plot.set_curves(curves, limits)

    # -- the map ---------------------------------------------------------------

    def layers_added(self, layers) -> None:
        """Attach to the first added layer that carries a series document."""
        for layer in layers:
            if isinstance(layer, QgsVectorLayer) and layer.customProperty(SERIES_PROPERTY):
                self.attach(layer)
                return

    def attach(self, layer: QgsVectorLayer) -> None:
        """Tie the panel to *layer*: its selection is the plot's."""
        if self.layer is not None:
            try:
                self.layer.selectionChanged.disconnect(self._map_changed)
            except (TypeError, RuntimeError):
                pass
        self.layer = layer
        layer.selectionChanged.connect(self._map_changed)
        path = str(layer.customProperty(SERIES_PROPERTY) or "")
        if path and path != self.path:
            self.load(path)
        self.show()

    def _map_changed(self, *args) -> None:
        if self._syncing or self.layer is None:
            return
        stations = [str(f["station"]) for f in self.layer.selectedFeatures()]
        self.select_stations(stations)

    def _list_changed(self) -> None:
        if self._syncing:
            return
        self.refresh()
        self._select_on_map(self.selected_stations())

    def pick(self, station: str, index: int) -> None:
        """A point clicked in the plot: select the station on the map, show the epoch."""
        self._select_on_map([station])
        self.status.setText(self.plot.describe(station, index))

    def _select_on_map(self, stations: list[str]) -> None:
        if self.layer is None:
            return
        self._syncing = True
        try:
            ids = [f.id() for f in self.layer.getFeatures() if str(f["station"]) in set(stations)]
            self.layer.selectByIds(ids)
        finally:
            self._syncing = False

    # -- export ----------------------------------------------------------------

    def export_csv(self, path: str) -> int:
        """The plotted stations' rows, every component. Returns the rows written."""
        if self.document is None:
            return 0
        wanted = set(self.selected_stations()) or {r["station"] for r in self.document["stations"]}
        rows = 0
        with open(path, "w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["station", "solution", "epoch", "component", "offset", "std_dev"])
            for record in self.document["stations"]:
                if record["station"] not in wanted:
                    continue
                for point in record["points"]:
                    for name, offset, sigma in zip(
                        record["components"], point["offsets"], point["std_devs"], strict=True
                    ):
                        writer.writerow(
                            [record["station"], point["solution"], point["epoch"], name, offset, sigma]
                        )
                        rows += 1
        return rows

    def export_image(self, path: str) -> bool:
        return self.plot.image().save(path)

    def _open(self) -> None:
        path, _filter = QFileDialog.getOpenFileName(
            self, _tr("Open a series document"), "", _tr("GeoComp monitoring document (*.json)")
        )
        if path:
            self.load(path)

    def _export_csv(self) -> None:
        path, _filter = QFileDialog.getSaveFileName(self, _tr("Export the series"), "", "CSV (*.csv)")
        if path:
            self.status.setText(_tr("%1 rows written.").replace("%1", str(self.export_csv(path))))

    def _export_image(self) -> None:
        path, _filter = QFileDialog.getSaveFileName(self, _tr("Export the plot"), "", "PNG (*.png)")
        if path and self.export_image(path):
            self.status.setText(_tr("Plot written."))


def _component(name: str) -> str:
    return {"e": _tr("East"), "n": _tr("North"), "u": _tr("Up"), "h": _tr("Height")}.get(name, name)


def attach_to_project(panel: TimeSeriesPanel) -> None:
    """Watch the project for series layers; attach to one already there."""
    project = QgsProject.instance()
    project.layersAdded.connect(panel.layers_added)
    panel.layers_added(list(project.mapLayers().values()))


def detach_from_project(panel: TimeSeriesPanel) -> None:
    try:
        QgsProject.instance().layersAdded.disconnect(panel.layers_added)
    except (TypeError, RuntimeError):
        pass
