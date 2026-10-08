# SPDX-License-Identifier: GPL-2.0-or-later
"""Inputs held in the project's own layers, as alternatives to their files (FR-160, FR-320).

Two of them, since P12c-44:

* **a field book** -- rows with a header, a CSV, an ``.xlsx`` sheet, or the
  attribute table of a layer of the user's own design. A layer is read as a
  file is: its field names are the header, each feature is a row in the order
  the layer gives them, and every value is text, so one field mapping reads the
  same book whichever of the three it arrives as. A layer's geometry is not
  read; where a book was observed from is the network's business, not its own.
* **stations** -- a point layer, each feature a station: its name from a field
  the user names, its position from the point, carried into the network's CRS
  when the layer's is another, and its height from a field, or from the point's
  Z when no field is named.

An algorithm offering both declares two optional inputs, and exactly one of
them must be given (:func:`file_or_layer`).
"""

from __future__ import annotations

import datetime
import math
from pathlib import Path
from typing import Any

from qgis.core import (
    Qgis,
    QgsProcessing,
    QgsProcessingException,
    QgsProcessingParameterVectorLayer,
)
from qgis.PyQt.QtCore import QCoreApplication

from geocomp.core.errors import GeoCompError

__all__ = [
    "book_layer_parameter",
    "book_rows",
    "cell_text",
    "file_or_layer",
    "point_type",
    "rows_of_layer",
    "stations_of_layer",
]

_CONTEXT = "GeoCompLayerSources"


def _tr(text: str) -> str:
    return QCoreApplication.translate(_CONTEXT, text)


def _any_vector() -> Any:
    """A layer of any vector type, a table without geometry included, as QGIS 3 and 4 spell it."""
    if hasattr(Qgis, "ProcessingSourceType"):
        return Qgis.ProcessingSourceType.Vector
    return QgsProcessing.TypeVector


def point_type() -> Any:
    """A layer of points, as QGIS 3 and 4 spell it."""
    if hasattr(Qgis, "ProcessingSourceType"):
        return Qgis.ProcessingSourceType.VectorPoint
    return QgsProcessing.TypeVectorPoint


def book_layer_parameter(name: str) -> QgsProcessingParameterVectorLayer:
    """The field book as a layer of the project, the alternative to its file."""
    return QgsProcessingParameterVectorLayer(
        name,
        _tr("Field book, as a layer of the project"),
        types=[_any_vector()],
        optional=True,
    )


def cell_text(value: Any) -> str:
    """A layer's value as the text a CSV of it would hold.

    An empty value is ``""`` -- ``None`` under QGIS 4, a null ``QVariant`` under
    QGIS 3. A whole number held in a decimal field is written without its
    ``.0``, because station names are often numbers and a field book's ``12`` is
    not station ``12.0``; any other decimal is its shortest exact text.
    """
    if value is None:
        return ""
    for convert in ("toPyDateTime", "toPyDate", "toPyTime"):
        if hasattr(value, convert):
            return "" if value.isNull() else getattr(value, convert)().isoformat()
    if hasattr(value, "isNull") and value.isNull():
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return str(int(value)) if value.is_integer() and abs(value) < 1e15 else repr(value)
    if isinstance(value, (datetime.date, datetime.time)):
        return value.isoformat()
    return str(value)


def rows_of_layer(layer: Any) -> list[list[str]]:
    """*layer*'s attribute table as a field book's rows: the field names, then one row per feature."""
    names = [field.name() for field in layer.fields()]
    rows = [names]
    for feature in layer.getFeatures():
        rows.append([cell_text(feature[name]) for name in names])
    return rows


def file_or_layer(
    algorithm: Any, parameters: dict[str, Any], context: Any, *, file: str, layer: str
) -> tuple[str, Any]:
    """The one of the file input *file* and the layer input *layer* that was given.

    Returns ``(path, None)`` for the file and ``("", layer)`` for the layer.

    Raises:
        QgsProcessingException: for neither or both, naming the two inputs by
            the labels the dialog shows them by (specs/16 §7).
    """
    path = algorithm.parameterAsFile(parameters, file, context)
    source = algorithm.parameterAsVectorLayer(parameters, layer, context)
    if bool(path) == (source is not None):
        template = (
            _tr("'%1' and '%2' are two ways of giving the same input, and both were given. "
                "Give one of them.")
            if path
            else _tr("Neither '%1' nor '%2' was given. Give one of them.")
        )
        raise QgsProcessingException(
            template.replace("%1", algorithm.parameterDefinition(file).description()).replace(
                "%2", algorithm.parameterDefinition(layer).description()
            )
        )
    return (path, None) if path else ("", source)


def book_rows(
    algorithm: Any, parameters: dict[str, Any], context: Any, *, file: str, layer: str
) -> tuple[list[list[str]], str]:
    """The field book's rows and its name, from the file *file* or the layer *layer* -- exactly one.

    Raises:
        QgsProcessingException: for neither or both, or a file that cannot be read.
    """
    path, source = file_or_layer(algorithm, parameters, context, file=file, layer=layer)
    if source is not None:
        return rows_of_layer(source), source.name()
    book = Path(path)
    if not book.is_file():
        raise QgsProcessingException(
            _tr("The field book '%1' does not exist. Check the path.").replace("%1", str(book))
        )
    from geocomp.io.tabular import read_rows
    from geocomp.services.messages import message_for

    try:
        return read_rows(book), book.name
    except GeoCompError as error:
        raise QgsProcessingException(message_for(error)) from error


def stations_of_layer(
    layer: Any, *, name_field: str, height_field: str, crs: str, context: Any, feedback: Any
) -> dict[str, tuple[float, float, float]]:
    """Each point of *layer* as a station: easting, northing and height in *crs*.

    The name is *name_field*'s value, as :func:`cell_text` gives it. The height
    is *height_field*'s, read as a field book's numbers are; with no field
    named, it is the point's Z. A layer in a CRS other than *crs* is carried
    into it -- horizontally: the height is kept as given, because a change of
    map projection does not move a height. A layer with no CRS, or a *crs*
    QGIS does not know, is taken as it stands.

    Raises:
        QgsProcessingException: for a station without a name, a position or a
            height, a station named twice, or a layer without stations.
    """
    from qgis.core import (
        QgsCoordinateReferenceSystem,
        QgsCoordinateTransform,
        QgsCsException,
        QgsPointXY,
    )

    from geocomp.io.mapping import parse_number

    target = QgsCoordinateReferenceSystem(crs)
    transform = None
    if layer.crs().isValid() and target.isValid() and layer.crs() != target:
        transform = QgsCoordinateTransform(layer.crs(), target, context.transformContext())
        feedback.pushInfo(
            _tr("The stations of '%1' are carried from %2 to %3; their heights are kept as given.")
            .replace("%1", layer.name())
            .replace("%2", layer.crs().authid())
            .replace("%3", target.authid())
        )

    def refuse(template: str, station: str = "", extra: str = "") -> QgsProcessingException:
        return QgsProcessingException(
            template.replace("%1", station).replace("%2", layer.name()).replace("%3", extra)
        )

    coordinates: dict[str, tuple[float, float, float]] = {}
    for feature in layer.getFeatures():
        name = cell_text(feature[name_field]).strip()
        if not name:
            raise refuse(
                _tr("Feature %1 of '%2' has no station name. Name it, or remove it from the layer."),
                str(feature.id()),
            )
        if name in coordinates:
            raise refuse(_tr("Station '%1' appears twice in '%2'. Keep one of its points."), name)
        geometry = feature.geometry()
        points = [] if geometry is None or geometry.isNull() else list(geometry.vertices())
        if not points:
            raise refuse(
                _tr("Station '%1' in '%2' has no position. Give it its point, or remove it from "
                    "the layer."),
                name,
            )
        if len(points) > 1:
            raise refuse(
                _tr("Station '%1' in '%2' is %3 points. Give it one."), name, str(len(points))
            )
        point = points[0]
        if height_field:
            text = cell_text(feature[height_field]).strip()
            try:
                up = parse_number(text, "auto")
                if not math.isfinite(up):
                    raise ValueError(text)
            except ValueError as error:
                raise refuse(
                    _tr("The height of station '%1' in '%2' is not a number: '%3'. Correct it "
                        "in the layer."),
                    name,
                    text,
                ) from error
        else:
            up = point.z()
            if math.isnan(up):
                raise refuse(
                    _tr("Station '%1' in '%2' has no Z. Give it one, or name the field that "
                        "holds the heights."),
                    name,
                )
        easting, northing = point.x(), point.y()
        if transform is not None:
            try:
                carried = transform.transform(QgsPointXY(easting, northing))
            except QgsCsException as error:
                raise refuse(
                    _tr("Station '%1' in '%2' cannot be carried into %3. Check the CRS of the "
                        "layer."),
                    name,
                    target.authid(),
                ) from error
            easting, northing = carried.x(), carried.y()
        coordinates[name] = (easting, northing, up)
    if not coordinates:
        raise refuse(_tr("The layer '%2' holds no stations. Choose the layer that holds them."))
    return coordinates
