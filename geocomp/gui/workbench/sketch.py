# SPDX-License-Identifier: GPL-2.0-or-later
"""The sketch a window draws on the map, and picking a point from it (FR-014, FR-017).

Posição's *Croqui*: while a job is worked on, what has coordinates is drawn
over the map -- the known points, the traverse an algorithm computed, the rays
to the points it radiated -- so a station typed with its easting and northing
swapped is seen at once, on the orthophoto, where it obviously is not.

**The sketch is not a layer.** It is markers and rubber bands on the canvas,
gone when the window closes (FR-010), because it is a view of work in
progress and a project should not acquire layers by a window being opened.
What a user wants kept is added to the project deliberately, as a layer, from
the window's Results step.

Coordinates are the job's, in the job's CRS; they are carried into the map's
only to be drawn, and a point picked on the map is carried back.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsCsException,
    QgsPointXY,
    QgsProject,
    QgsWkbTypes,
)
from qgis.gui import QgsMapCanvas, QgsMapToolEmitPoint, QgsRubberBand, QgsVertexMarker
from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtGui import QColor, QMouseEvent

__all__ = ["CanvasSketch", "PointPickTool"]

#: Colours from the palette the pre-analysis canvas uses, which stays legible
#: over both an orthophoto and a street map.
KNOWN_COLOUR = QColor(0, 114, 178)
COMPUTED_COLOUR = QColor(213, 94, 0)
LINE_COLOUR = QColor(0, 0, 0, 170)


class CanvasSketch:
    """Markers and lines a window draws on the map canvas, in the job's CRS.

    Args:
        canvas: The map canvas, or ``None`` where there is none: the sketch
            then draws nothing, and a window works without a map.
        crs: Gives the job's CRS as an authority id, or ``""`` for a local
            plane, which is drawn as though it were the map's.
    """

    def __init__(self, canvas: QgsMapCanvas | None, crs: Callable[[], str]) -> None:
        self._canvas = canvas
        self._crs = crs
        self._markers: list[QgsVertexMarker] = []
        self._bands: list[QgsRubberBand] = []

    @property
    def item_count(self) -> int:
        """How many markers and lines are on the canvas."""
        return len(self._markers) + len(self._bands)

    def clear(self) -> None:
        """Take everything this sketch drew off the canvas."""
        if self._canvas is None:
            return
        for item in (*self._markers, *self._bands):
            self._canvas.scene().removeItem(item)
        self._markers.clear()
        self._bands.clear()

    def add_point(self, easting: float, northing: float, *, computed: bool = False) -> None:
        """Mark a point: a known one, or one an algorithm computed."""
        position = self._to_map(easting, northing)
        if self._canvas is None or position is None:
            return
        marker = QgsVertexMarker(self._canvas)
        marker.setCenter(position)
        marker.setIconType(
            QgsVertexMarker.IconType.ICON_CIRCLE if computed else QgsVertexMarker.IconType.ICON_BOX
        )
        marker.setIconSize(10)
        marker.setPenWidth(3)
        marker.setColor(COMPUTED_COLOUR if computed else KNOWN_COLOUR)
        self._markers.append(marker)

    def add_line(self, vertices: Sequence[tuple[float, float]]) -> None:
        """Draw a line through *vertices*: a traverse's legs, a ray to a radiated point."""
        positions = [self._to_map(easting, northing) for easting, northing in vertices]
        if self._canvas is None or len(positions) < 2 or any(p is None for p in positions):
            return
        band = QgsRubberBand(self._canvas, QgsWkbTypes.GeometryType.LineGeometry)
        band.setColor(LINE_COLOUR)
        band.setWidth(2)
        for position in positions:
            band.addPoint(position, False)
        band.updatePosition()
        band.show()
        self._bands.append(band)

    # -- between the job's CRS and the map's ---------------------------------

    def _transform(self, *, to_map: bool) -> QgsCoordinateTransform | None:
        if self._canvas is None:
            return None
        job = QgsCoordinateReferenceSystem(self._crs()) if self._crs() else None
        shown = self._canvas.mapSettings().destinationCrs()
        if job is None or not job.isValid() or not shown.isValid() or job == shown:
            return None
        source, target = (job, shown) if to_map else (shown, job)
        return QgsCoordinateTransform(source, target, QgsProject.instance())

    def _to_map(self, easting: float, northing: float) -> QgsPointXY | None:
        transform = self._transform(to_map=True)
        point = QgsPointXY(easting, northing)
        if transform is None:
            return point
        try:
            return transform.transform(point)
        except QgsCsException:
            return None

    def from_map(self, point: QgsPointXY) -> tuple[float, float] | None:
        """A point of the map in the job's CRS, or ``None`` where it cannot be carried there."""
        transform = self._transform(to_map=False)
        if transform is None:
            return point.x(), point.y()
        try:
            carried = transform.transform(point)
        except QgsCsException:
            return None
        return carried.x(), carried.y()


class PointPickTool(QgsMapToolEmitPoint):
    """One click on the map, snapped where the project's snapping says, as a point.

    The tool a window lends the canvas while a coordinate is being picked. It
    emits :attr:`picked` with the map's coordinates and does nothing else; the
    window gives the canvas its previous tool back.
    """

    #: A point was clicked: its x and y in the map's CRS.
    picked = pyqtSignal(float, float)

    def __init__(self, canvas: QgsMapCanvas) -> None:
        super().__init__(canvas)
        self._canvas = canvas

    def canvasReleaseEvent(self, event: QMouseEvent) -> None:
        """Emit the clicked point, moved onto a feature when snapping finds one."""
        point = self.toMapCoordinates(event.pos())
        match = self._canvas.snappingUtils().snapToMap(point)
        if match.isValid():
            point = match.point()
        self.picked.emit(point.x(), point.y())
