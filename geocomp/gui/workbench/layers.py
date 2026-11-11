# SPDX-License-Identifier: GPL-2.0-or-later
"""Points an algorithm computed, as a layer of the project (FR-017).

The sketch a window draws is gone when the window closes. What a user wants
kept on the map -- a traverse's stations, the points radiated from them -- is
added deliberately, from the Results step, as an ordinary point layer: in
memory, labelled with the points' names, the user's to style and to save.

The rows are the algorithm's: the table it wrote, read back. Nothing is
computed here, and a value the table does not carry is not invented.
"""

from __future__ import annotations

from collections.abc import Sequence

from qgis.core import (
    QgsFeature,
    QgsField,
    QgsGeometry,
    QgsPalLayerSettings,
    QgsPoint,
    QgsProject,
    QgsVectorLayer,
    QgsVectorLayerSimpleLabeling,
)
from qgis.PyQt.QtCore import QMetaType

__all__ = ["POINT_FIELDS", "add_points_layer"]

#: The layer's fields, in order. Names are stable and English, as every
#: GeoComp layer's are; a standard deviation the algorithm did not give is null.
POINT_FIELDS: tuple[tuple[str, QMetaType.Type], ...] = (
    ("name", QMetaType.Type.QString),
    ("easting", QMetaType.Type.Double),
    ("northing", QMetaType.Type.Double),
    ("height", QMetaType.Type.Double),
    ("origin", QMetaType.Type.QString),
    ("sigma_e", QMetaType.Type.Double),
    ("sigma_n", QMetaType.Type.Double),
    ("sigma_u", QMetaType.Type.Double),
)


def add_points_layer(
    name: str,
    crs: str,
    points: Sequence[dict[str, object]],
    *,
    project: QgsProject | None = None,
) -> QgsVectorLayer:
    """Add *points* to the project as a labelled point layer, and return it.

    Args:
        name: The layer's name, already translated.
        crs: The job's CRS as an authority id, or ``""`` for a local plane:
            the layer then has no CRS, as the survey has no datum.
        points: One mapping per point, by the names of :data:`POINT_FIELDS`.
            ``name``, ``easting`` and ``northing`` are needed; the rest may be
            absent.
        project: The project to add it to; the open one by default.
    """
    source = "PointZ" + (f"?crs={crs}" if crs else "")
    layer = QgsVectorLayer(source, name, "memory")
    provider = layer.dataProvider()
    provider.addAttributes([QgsField(field, kind) for field, kind in POINT_FIELDS])
    layer.updateFields()
    features = []
    for point in points:
        feature = QgsFeature(layer.fields())
        height = point.get("height")
        feature.setGeometry(
            QgsGeometry(
                QgsPoint(
                    float(point["easting"]),
                    float(point["northing"]),
                    float(height) if height is not None else 0.0,
                )
            )
        )
        feature.setAttributes([point.get(field) for field, _kind in POINT_FIELDS])
        features.append(feature)
    provider.addFeatures(features)
    layer.updateExtents()

    labels = QgsPalLayerSettings()
    labels.fieldName = "name"
    layer.setLabeling(QgsVectorLayerSimpleLabeling(labels))
    layer.setLabelsEnabled(True)
    (project if project is not None else QgsProject.instance()).addMapLayer(layer)
    return layer
