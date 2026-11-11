# SPDX-License-Identifier: GPL-2.0-or-later
"""What an algorithm computed, as layers of the project (FR-017, FR-905).

The sketch a window draws is gone when the window closes. What a user wants
kept on the map -- a traverse's stations, the points radiated from them -- is
added deliberately, from the Results step, as an ordinary point layer: in
memory, labelled with the points' names, the user's to style and to save. An
adjustment's styled result layers (P14b) are added the same way, from the
files its own sinks wrote.

The rows are the algorithm's: the table or the layer it wrote, read back.
Nothing is computed here, and a value the algorithm did not give is not
invented.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

from qgis.core import (
    NULL,
    QgsFeature,
    QgsFeatureRequest,
    QgsField,
    QgsGeometry,
    QgsPalLayerSettings,
    QgsPoint,
    QgsProject,
    QgsVectorLayer,
    QgsVectorLayerSimpleLabeling,
)
from qgis.PyQt.QtCore import QMetaType

from geocomp.algorithms.layer_outputs import LAYER_OUTPUTS, RESULT_LAYER_PROPERTY, SOLUTION_PROPERTY
from geocomp.layers.builders import exaggerated_layer_name
from geocomp.layers.styles import apply_style
from geocomp.layers.themes import add_thematic_styles

__all__ = ["POINT_FIELDS", "add_points_layer", "add_result_layers"]

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


def add_result_layers(
    files: Mapping[str, Path],
    *,
    group: str,
    labels: Mapping[str, str],
    solution: Path | None = None,
    project: QgsProject | None = None,
) -> list[QgsVectorLayer]:
    """Add the result layers an adjustment wrote to its files, styled, in a group of their own.

    The layers are the algorithm's, written by its own sinks during the run
    (FR-905): nothing is drawn here. What a toolbox run does when it loads
    them is done again -- the shipped style and its themes, the custom
    properties by which the results panel finds the run behind a layer, and a
    name that states the exaggeration the geometry was drawn at (FR-901),
    made again from what the features record.

    Each is a copy in memory, like :func:`add_points_layer`'s, so the user's to
    keep: saving the project asks where.

    Args:
        files: Each layer's file, by the algorithm's parameter name.
        group: The name of the layer-tree group they go in, translated.
        labels: The algorithm's label for each parameter, the name of a layer
            that is not drawn exaggerated, as the toolbox names it.
        solution: The solution document the run wrote.
        project: The project to add them to; the open one by default.

    Returns:
        The layers added, in the order a toolbox run lists them. One the run
        left empty -- relative ellipses where no observation joins two
        estimated stations -- is not added.
    """
    target = project if project is not None else QgsProject.instance()
    added: list[QgsVectorLayer] = []
    for name, style, _source_type, _geometry in LAYER_OUTPUTS:
        path = files.get(name)
        if path is None:
            continue
        source = QgsVectorLayer(str(path), labels.get(name, name), "ogr")
        if not source.isValid() or source.featureCount() == 0:
            continue
        # Copied into memory, as the points layers are: the file is in the
        # window's results folder, which the next calculation replaces, and a
        # layer still reading it would lose its data or hold the folder open.
        layer = source.materialize(QgsFeatureRequest())
        del source
        layer.setName(labels.get(name, name))
        first = next(layer.getFeatures(), None)
        if first is not None and first.fieldNameIndex("exaggeration") >= 0:
            confidence = (
                first["confidence"] if first.fieldNameIndex("confidence") >= 0 else None
            )
            drawn = exaggerated_layer_name(
                style,
                exaggeration=float(first["exaggeration"]),
                confidence=None if confidence in (None, NULL) else float(confidence),
            )
            if drawn:
                layer.setName(drawn)
        layer.setCustomProperty(RESULT_LAYER_PROPERTY, style)
        if solution is not None:
            layer.setCustomProperty(SOLUTION_PROPERTY, str(solution))
        if apply_style(layer, style):
            add_thematic_styles(layer, style)
        added.append(layer)
    if not added:
        return added
    node = target.layerTreeRoot().insertGroup(0, group)
    for layer in added:
        target.addMapLayer(layer, False)
        node.addLayer(layer)
    return added
