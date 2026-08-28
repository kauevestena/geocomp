# SPDX-License-Identifier: GPL-2.0-or-later
"""Result layers as Processing outputs (FR-900, FR-901, FR-905).

Every algorithm that produces a :class:`~geocomp.core.models.Solution` offers
the same five layers, declared and filled by the two functions here rather than
by each algorithm separately. That is not only to avoid repetition: a user
should get the same map whichever adjustment they ran, and two hand-written
copies of this would diverge by the second change.

Styling goes through a **post-processor**, which is how Processing lets an
algorithm style an output it does not own. The sink may be a memory layer, a
GeoPackage or a shapefile depending on where the user pointed it, and the layer
object only exists after the algorithm has finished; the post-processor runs at
that moment, which is the only point at which there is something to style.

The exaggeration factor is declared once here, defaulting to **automatic**: an
algorithm has no map canvas to measure, so the first factor is computed from
the network's own extent, which is the closest honest substitute. Whatever it
resolves to reaches the layer name, so what the legend states is what the
geometry used (FR-901).
"""

from __future__ import annotations

from typing import Any, ClassVar

from qgis.core import (
    Qgis,
    QgsCoordinateReferenceSystem,
    QgsProcessing,
    QgsProcessingContext,
    QgsProcessingLayerPostProcessorInterface,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterNumber,
    QgsWkbTypes,
)
from qgis.PyQt.QtCore import QCoreApplication

from geocomp.core.models import Network, Solution
from geocomp.core.visualization import default_exaggeration
from geocomp.layers.builders import (
    correction_features,
    correction_layer_name,
    ellipse_features,
    ellipse_layer_name,
    fields_for,
    observation_features,
    residual_features,
    station_features,
)
from geocomp.layers.styles import apply_style

__all__ = [
    "EXAGGERATION",
    "LAYER_OUTPUTS",
    "OUTPUT_CORRECTION_LAYER",
    "OUTPUT_ELLIPSE_LAYER",
    "OUTPUT_OBSERVATION_LAYER",
    "OUTPUT_RESIDUAL_LAYER",
    "OUTPUT_STATION_LAYER",
    "add_result_layer_parameters",
    "resolve_exaggeration",
    "write_result_layers",
]

_CONTEXT = "GeoCompLayers"

OUTPUT_STATION_LAYER = "OUTPUT_STATION_LAYER"
OUTPUT_ELLIPSE_LAYER = "OUTPUT_ELLIPSE_LAYER"
OUTPUT_RESIDUAL_LAYER = "OUTPUT_RESIDUAL_LAYER"
OUTPUT_OBSERVATION_LAYER = "OUTPUT_OBSERVATION_LAYER"
OUTPUT_CORRECTION_LAYER = "OUTPUT_CORRECTION_LAYER"
EXAGGERATION = "EXAGGERATION"


def _source_types() -> tuple[Any, Any, Any]:
    """Point, line and polygon, as ``QgsProcessingParameterFeatureSink`` wants.

    **Not the same enum as the sink's geometry.** The parameter declares what
    *kind of layer* it produces (a ``ProcessingSourceType``); ``parameterAsSink``
    separately takes the WKB geometry type. Passing the WKB type to the
    parameter is accepted by nothing -- under PyQt6 it raises inside a C++
    virtual, which is fatal, so the whole provider aborts and every tier-3 test
    dies at once without naming the algorithm. That is what
    ``scripts/diagnose_provider.py`` exists to identify.

    QGIS 4 spells these ``Qgis.ProcessingSourceType.Vector*`` and QGIS 3 spells
    them ``QgsProcessing.TypeVector*``. The plugin targets QGIS 4; the older
    spelling is kept only so the test suite runs against a distribution's QGIS 3,
    which is how most contributors will have one, and can be deleted when 4.0 is
    everywhere.
    """
    if hasattr(Qgis, "ProcessingSourceType"):
        source = Qgis.ProcessingSourceType
        return source.VectorPoint, source.VectorLine, source.VectorPolygon
    return (
        QgsProcessing.TypeVectorPoint,
        QgsProcessing.TypeVectorLine,
        QgsProcessing.TypeVectorPolygon,
    )


_POINT, _LINE, _POLYGON = _source_types()

#: Parameter name, style name, sink source type and sink geometry of each result
#: layer, in the order they should appear in the dialog: what the adjustment
#: produced first.
LAYER_OUTPUTS: tuple[tuple[str, str, Any, Any], ...] = (
    (OUTPUT_STATION_LAYER, "stations", _POINT, QgsWkbTypes.Type.Point),
    (OUTPUT_ELLIPSE_LAYER, "ellipses", _POLYGON, QgsWkbTypes.Type.Polygon),
    (OUTPUT_RESIDUAL_LAYER, "residuals", _LINE, QgsWkbTypes.Type.LineString),
    (OUTPUT_OBSERVATION_LAYER, "observations", _LINE, QgsWkbTypes.Type.LineString),
    (OUTPUT_CORRECTION_LAYER, "corrections", _LINE, QgsWkbTypes.Type.LineString),
)

#: The largest ellipse spans this fraction of the network's shorter side in the
#: automatic factor. Small enough that ellipses do not overlap each other in a
#: dense network, large enough to see at a glance.
_TARGET_FRACTION = 0.05


def _tr(text: str) -> str:
    return QCoreApplication.translate(_CONTEXT, text)


class _StyledLayer(QgsProcessingLayerPostProcessorInterface):
    """Applies a shipped QML, and the name that states the exaggeration.

    Processing keeps only a weak reference to a post-processor, so an instance
    that went out of scope would be collected before it ran and the layer would
    arrive unstyled -- intermittently, depending on the collector. Instances are
    therefore kept in a class attribute, which is the documented idiom.
    """

    _alive: ClassVar[list[_StyledLayer]] = []

    def __init__(self, style: str, name: str) -> None:
        super().__init__()
        self.style = style
        self.name = name
        _StyledLayer._alive.append(self)

    def postProcessLayer(self, layer, context, feedback) -> None:
        if layer is None or not layer.isValid():
            return
        if self.name:
            layer.setName(self.name)
        apply_style(layer, self.style)


def add_result_layer_parameters(algorithm) -> None:
    """Declare the five result-layer sinks and the exaggeration factor.

    All optional and none created by default: an adjustment run from the
    modeller to feed another algorithm should not silently write five layers,
    while one run from the toolbox is a click away from all of them.
    """
    labels = {
        OUTPUT_STATION_LAYER: algorithm.tr("Adjusted stations (layer)"),
        OUTPUT_ELLIPSE_LAYER: algorithm.tr("Error ellipses (layer)"),
        OUTPUT_RESIDUAL_LAYER: algorithm.tr("Residuals (layer)"),
        OUTPUT_OBSERVATION_LAYER: algorithm.tr("Observations (layer)"),
        OUTPUT_CORRECTION_LAYER: algorithm.tr("Coordinate corrections (layer)"),
    }
    for name, _style, source_type, _geometry in LAYER_OUTPUTS:
        algorithm.addParameter(
            QgsProcessingParameterFeatureSink(
                name, labels[name], type=source_type, optional=True, createByDefault=False
            )
        )
    algorithm.addAdvancedParameter(
        QgsProcessingParameterNumber(
            EXAGGERATION,
            algorithm.tr("Ellipse exaggeration (0 = from the network's extent)"),
            type=QgsProcessingParameterNumber.Type.Double,
            defaultValue=0.0,
            minValue=0.0,
            maxValue=1.0e9,
        )
    )


def resolve_exaggeration(requested: float, solution: Solution) -> float:
    """The factor to draw at: the one asked for, or one fitted to the network.

    An algorithm has no map canvas, so "fit the view" has to mean fit the
    *data*: the network's own bounding box stands in for the extent it will
    first be looked at in. A single-station solution has no extent at all and
    gets 1, which is honest -- there is nothing to scale against.
    """
    if requested > 0.0:
        return requested

    eastings = []
    northings = []
    sizes = []
    for station in solution.adjusted_stations:
        east, north, _up = station.position.values
        eastings.append(east.value)
        northings.append(north.value)
        if station.ellipse is not None:
            sizes.append(station.ellipse.semi_major)

    if len(eastings) < 2 or not sizes:
        return 1.0

    width = max(eastings) - min(eastings)
    height = max(northings) - min(northings)
    if width <= 0.0 or height <= 0.0:
        # A network strung along one line: the span it does have is the only
        # thing there is to scale against.
        span = max(width, height)
        if span <= 0.0:
            return 1.0
        width = height = span
    return default_exaggeration((width, height), sizes, target_fraction=_TARGET_FRACTION)


def write_result_layers(
    algorithm,
    parameters: dict[str, Any],
    context: QgsProcessingContext,
    solution: Solution,
    network: Network,
    feedback=None,
) -> dict[str, Any]:
    """Fill whichever result-layer sinks the user asked for.

    Returns the destination ids, ready to merge into the algorithm's results.
    """
    exaggeration = resolve_exaggeration(
        algorithm.parameterAsDouble(parameters, EXAGGERATION, context), solution
    )
    if feedback is not None and _any_requested(parameters):
        feedback.pushInfo(
            _tr("Ellipses and correction vectors are drawn exaggerated %1x.").replace(
                "%1", f"{exaggeration:g}"
            )
        )

    producers = {
        OUTPUT_STATION_LAYER: lambda: station_features(solution, network),
        OUTPUT_ELLIPSE_LAYER: lambda: ellipse_features(solution, exaggeration=exaggeration),
        OUTPUT_RESIDUAL_LAYER: lambda: residual_features(solution, network),
        OUTPUT_OBSERVATION_LAYER: lambda: observation_features(network, solution),
        OUTPUT_CORRECTION_LAYER: lambda: correction_features(
            solution, exaggeration=exaggeration
        ),
    }
    names = {
        OUTPUT_ELLIPSE_LAYER: ellipse_layer_name(solution, exaggeration=exaggeration),
        OUTPUT_CORRECTION_LAYER: correction_layer_name(exaggeration=exaggeration),
    }

    # A CRS authority code, not a string: QGIS 4 takes a
    # QgsCoordinateReferenceSystem here and refuses the str that QGIS 3 accepted.
    crs = QgsCoordinateReferenceSystem(solution.crs)

    outputs: dict[str, Any] = {}
    for name, style, _source_type, geometry in LAYER_OUTPUTS:
        # Nothing is built for a sink nobody asked for -- not even its field
        # list. All five are optional, so the common case is that most are
        # absent, and an adjustment that requested no layers must not be able
        # to fail inside the layer code: the layers are a view of the result,
        # and a view must never take the result down with it.
        if not parameters.get(name):
            outputs[name] = None
            continue
        sink, destination = algorithm.parameterAsSink(
            parameters, name, context, fields_for(style), geometry, crs
        )
        outputs[name] = destination
        if sink is None:
            continue
        for feature in producers[name]():
            sink.addFeature(feature)
        _register_style(context, destination, style, names.get(name, ""))

    return outputs


def _any_requested(parameters: dict[str, Any]) -> bool:
    return any(parameters.get(name) for name, *_rest in LAYER_OUTPUTS)


def _register_style(
    context: QgsProcessingContext, destination: str, style: str, name: str
) -> None:
    if not destination:
        return
    details = context.layerToLoadOnCompletionDetails(destination)
    if details is None:
        return
    details.setPostProcessor(_StyledLayer(style, name))
