# SPDX-License-Identifier: GPL-2.0-or-later
"""Styled result layers from an adjustment (FR-900, FR-901, FR-905).

``specs/19-visualization.md`` sections 1 to 3.

A user who runs an adjustment sees the result. They do not then style five
layers by hand, which is what FR-905 means by *immediately interpretable* and
what the proposal's "visualização imediata" asked for.

Each layer is described in two halves: :data:`LAYER_FIELDS` names its columns,
and a ``*_features`` function fills them. The halves are split so the same
features can go either into a memory layer, which is what a dialog wants, or
into a Processing sink, which is what an algorithm wants, without either path
inventing its own attribute table. The key of :data:`LAYER_FIELDS` is the name
of the QML that styles it, which is the whole of the pairing: a style and the
table it is applied to cannot drift apart without the name breaking.

**The exaggeration factor is a required keyword argument** of both builders
that draw at a scale, and each states it in the layer's own name. ``specs/19``
section 3 calls an unstated exaggeration the one thing that turns a quality
visualisation into a misrepresentation, so it is not something a caller can
forget: there is no default to fall through to, and the name that reaches the
legend is composed from the same number the geometry used.
"""

from __future__ import annotations

import math
from collections.abc import Iterator
from typing import Any

from qgis.core import (
    QgsFeature,
    QgsField,
    QgsFields,
    QgsGeometry,
    QgsPointXY,
    QgsVectorLayer,
)
from qgis.PyQt.QtCore import QCoreApplication, QMetaType

from geocomp.core.models import Network, Solution
from geocomp.core.visualization import displacement_arrow, ellipse_ring
from geocomp.layers.styles import apply_style

__all__ = [
    "LAYER_FIELDS",
    "correction_features",
    "correction_layer",
    "ellipse_features",
    "ellipse_layer",
    "exaggeration_label",
    "fields_for",
    "observation_features",
    "observation_layer",
    "residual_features",
    "residual_layer",
    "station_features",
    "station_layer",
]

_CONTEXT = "GeoCompLayers"

_TEXT = QMetaType.Type.QString
_REAL = QMetaType.Type.Double
_INT = QMetaType.Type.Int


def _tr(text: str) -> str:
    return QCoreApplication.translate(_CONTEXT, text)


#: The attribute table of each result layer, keyed by the QML that styles it.
#:
#: One key per style and one style per key. A layer that borrowed another's
#: style would look styled and convey nothing: QGIS does not fail on a
#: categorised renderer whose attribute is missing, it draws every feature in
#: the fallback symbol.
LAYER_FIELDS: dict[str, tuple[tuple[str, Any], ...]] = {
    "stations": (
        ("station", _TEXT),
        ("easting", _REAL),
        ("northing", _REAL),
        ("height", _REAL),
        ("sigma_e", _REAL),
        ("sigma_n", _REAL),
        ("sigma_h", _REAL),
        ("positional_uncertainty", _REAL),
        ("semi_major", _REAL),
        ("semi_minor", _REAL),
        ("orientation", _REAL),
        ("confidence", _REAL),
        ("constraint", _TEXT),
    ),
    "ellipses": (
        ("station", _TEXT),
        ("semi_major", _REAL),
        ("semi_minor", _REAL),
        ("orientation", _REAL),
        ("semi_vertical", _REAL),
        ("confidence", _REAL),
        ("exaggeration", _REAL),
    ),
    "residuals": (
        ("observation", _TEXT),
        ("type", _TEXT),
        ("from_station", _TEXT),
        ("to_station", _TEXT),
        ("residual", _REAL),
        ("standardised", _REAL),
        ("redundancy", _REAL),
        ("mdb", _REAL),
        ("external_reliability", _REAL),
        ("decision", _TEXT),
    ),
    "observations": (
        ("observation", _TEXT),
        ("type", _TEXT),
        ("from_station", _TEXT),
        ("to_station", _TEXT),
        ("value", _REAL),
        ("sigma", _REAL),
        ("status", _TEXT),
        ("cluster", _TEXT),
        ("station_count", _INT),
    ),
    "corrections": (
        ("station", _TEXT),
        ("correction_e", _REAL),
        ("correction_n", _REAL),
        ("correction_h", _REAL),
        ("magnitude", _REAL),
        ("exaggeration", _REAL),
    ),
}

#: The geometry each layer carries, in the spelling a memory-layer URI uses.
LAYER_GEOMETRY: dict[str, str] = {
    "stations": "Point",
    "ellipses": "Polygon",
    "residuals": "LineString",
    "observations": "LineString",
    "corrections": "LineString",
}


def fields_for(style: str) -> QgsFields:
    """The attribute table of the layer *style* is applied to."""
    fields = QgsFields()
    for name, kind in LAYER_FIELDS[style]:
        fields.append(QgsField(name, kind))
    return fields


def exaggeration_label(exaggeration: float, confidence: float | None = None) -> str:
    """The text that has to reach the legend, composed from the drawn factor.

    Built here rather than at each call site so that every layer states it the
    same way, and so that a layer's name and its geometry cannot disagree: both
    come from the same argument.
    """
    factor = f"{exaggeration:g}"
    if confidence is None:
        return _tr("exaggerated %1x").replace("%1", factor)
    percent = f"{confidence * 100.0:g}"
    return _tr("%1% confidence, exaggerated %2x").replace("%1", percent).replace("%2", factor)


# -- stations -------------------------------------------------------------


def station_features(
    solution: Solution, network: Network | None = None
) -> Iterator[QgsFeature]:
    """Adjusted stations, one point each.

    Args:
        network: Supplies each station's constraint mode, which the style uses
            to give held stations their own symbol. The solution records *how*
            the datum was defined but not which station carried it, and a fixed
            station is a different kind of thing on a map, not a more precise
            one.
    """
    fields = fields_for("stations")
    constraints = _constraint_modes(network)
    for station in solution.adjusted_stations:
        east, north, up = station.position.values
        ellipse = station.ellipse
        feature = QgsFeature(fields)
        feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(east.value, north.value)))
        feature.setAttributes(
            [
                station.station_id,
                east.value,
                north.value,
                up.value,
                east.std_dev,
                north.std_dev,
                up.std_dev,
                station.positional_uncertainty,
                ellipse.semi_major if ellipse else None,
                ellipse.semi_minor if ellipse else None,
                math.degrees(ellipse.orientation) if ellipse else None,
                ellipse.confidence if ellipse else None,
                constraints.get(station.station_id, "free"),
            ]
        )
        yield feature


def station_layer(
    solution: Solution, *, network: Network | None = None, crs: str = "", name: str = ""
) -> QgsVectorLayer:
    """Adjusted stations, sized by their positional uncertainty."""
    return _build(
        "stations",
        crs or solution.crs,
        name or _tr("Adjusted stations"),
        station_features(solution, network),
    )


# -- ellipses -------------------------------------------------------------


def ellipse_features(solution: Solution, *, exaggeration: float) -> Iterator[QgsFeature]:
    """Error ellipses, drawn at *exaggeration* and each recording it (FR-901).

    The factor has no default. A caller that has not decided one has not
    decided what the map means, and drawing at 1:1 silently would produce a
    layer of invisible ellipses that looks like an empty result.
    """
    fields = fields_for("ellipses")
    for station in solution.adjusted_stations:
        if station.ellipse is None:
            continue
        drawn = ellipse_ring(_plan(station), station.ellipse, exaggeration=exaggeration)
        feature = QgsFeature(fields)
        feature.setGeometry(_polygon(drawn.ring))
        feature.setAttributes(
            [
                station.station_id,
                drawn.semi_major,
                drawn.semi_minor,
                math.degrees(drawn.orientation),
                station.ellipse.semi_vertical,
                drawn.confidence,
                drawn.exaggeration,
            ]
        )
        yield feature


def ellipse_layer(
    solution: Solution, *, exaggeration: float, crs: str = "", name: str = ""
) -> QgsVectorLayer:
    """Error ellipses, named for the factor and confidence they were drawn at."""
    return _build(
        "ellipses",
        crs or solution.crs,
        name or ellipse_layer_name(solution, exaggeration=exaggeration),
        ellipse_features(solution, exaggeration=exaggeration),
    )


def ellipse_layer_name(solution: Solution, *, exaggeration: float) -> str:
    """What the legend will read. Composed from the factor the ring used."""
    confidence = next(
        (
            station.ellipse.confidence
            for station in solution.adjusted_stations
            if station.ellipse is not None
        ),
        None,
    )
    return _tr("Error ellipses (%1)").replace(
        "%1", exaggeration_label(exaggeration, confidence)
    )


# -- residuals ------------------------------------------------------------


def residual_features(solution: Solution, network: Network) -> Iterator[QgsFeature]:
    """One line per observation, carrying what the w-test decided about it.

    Not drawn at a scale, and deliberately: the residual of a distance or an
    angle is a scalar, so there is no vector to exaggerate. What the map has to
    show is *which* observations are suspect and which could not be tested at
    all, and that is categorical (``specs/19`` section 2).
    """
    fields = fields_for("residuals")
    positions = _positions(solution, network)
    for result in solution.observation_results:
        observation = network.observations.get(result.observation_id)
        if observation is None:
            continue
        geometry = _connecting_line(observation.stations, positions)
        if geometry is None:
            continue
        feature = QgsFeature(fields)
        feature.setGeometry(geometry)
        feature.setAttributes(
            [
                result.observation_id,
                observation.type.name,
                observation.stations[0],
                observation.stations[-1],
                result.residual,
                result.standardised_residual,
                result.redundancy,
                result.minimal_detectable_bias,
                result.external_reliability,
                _decision(result),
            ]
        )
        yield feature


def residual_layer(
    solution: Solution, network: Network, *, crs: str = "", name: str = ""
) -> QgsVectorLayer:
    """Observations categorised by what the w-test decided about them."""
    return _build(
        "residuals",
        crs or solution.crs,
        name or _tr("Residuals"),
        residual_features(solution, network),
    )


# -- observations ---------------------------------------------------------


def observation_features(
    network: Network, solution: Solution | None = None
) -> Iterator[QgsFeature]:
    """The network as it was measured, one line per observation.

    Positions come from the solution where there is one and from the network's
    approximate coordinates otherwise, so this layer is drawable before any
    adjustment has been run -- which is when a user most wants to look at the
    geometry.
    """
    fields = fields_for("observations")
    positions = _positions(solution, network)

    for observation in network.observations.values():
        geometry = _connecting_line(observation.stations, positions)
        if geometry is None:
            continue
        first = observation.values[0]
        feature = QgsFeature(fields)
        feature.setGeometry(geometry)
        feature.setAttributes(
            [
                observation.id,
                observation.type.name,
                observation.stations[0],
                observation.stations[-1],
                first.value,
                first.std_dev,
                observation.status.value,
                observation.cluster_id,
                len(observation.stations),
            ]
        )
        yield feature


def observation_layer(
    network: Network, *, solution: Solution | None = None, crs: str = "", name: str = ""
) -> QgsVectorLayer:
    """The measured network, categorised by observation type."""
    return _build(
        "observations",
        crs or network.crs,
        name or _tr("Observations"),
        observation_features(network, solution),
    )


# -- corrections ----------------------------------------------------------


def correction_features(solution: Solution, *, exaggeration: float) -> Iterator[QgsFeature]:
    """The shift from each station's approximate position to its adjusted one.

    A genuine two-dimensional vector, so unlike the residuals this one is drawn
    at a scale -- and, like the ellipses, states the scale. Large corrections
    concentrated in one part of a network are the signature of bad approximate
    coordinates or of a blunder near there.
    """
    fields = fields_for("corrections")
    for station in solution.adjusted_stations:
        if station.correction is None:
            continue
        east, north, up = station.correction
        # The correction moved the station *to* where it now is, so the arrow
        # starts from the adjusted position less the correction.
        adjusted = _plan(station)
        tail, tip = displacement_arrow(
            (adjusted[0] - east, adjusted[1] - north), (east, north), exaggeration=exaggeration
        )
        feature = QgsFeature(fields)
        feature.setGeometry(QgsGeometry.fromPolylineXY([QgsPointXY(*tail), QgsPointXY(*tip)]))
        feature.setAttributes(
            [
                station.station_id,
                east,
                north,
                up,
                math.hypot(east, north),
                exaggeration,
            ]
        )
        yield feature


def correction_layer(
    solution: Solution, *, exaggeration: float, crs: str = "", name: str = ""
) -> QgsVectorLayer:
    """Coordinate correction vectors, named for the factor they were drawn at."""
    return _build(
        "corrections",
        crs or solution.crs,
        name or correction_layer_name(exaggeration=exaggeration),
        correction_features(solution, exaggeration=exaggeration),
    )


def correction_layer_name(*, exaggeration: float) -> str:
    return _tr("Coordinate corrections (%1)").replace("%1", exaggeration_label(exaggeration))


# -- helpers --------------------------------------------------------------


def _build(style: str, crs: str, name: str, features: Iterator[QgsFeature]) -> QgsVectorLayer:
    geometry = LAYER_GEOMETRY[style]
    uri = f"{geometry}?crs={crs}" if crs else geometry
    layer = QgsVectorLayer(uri, name, "memory")
    layer.dataProvider().addAttributes(list(fields_for(style)))
    layer.updateFields()
    collected = list(features)
    if collected:
        layer.dataProvider().addFeatures(collected)
    layer.updateExtents()
    apply_style(layer, style)
    return layer


def _plan(station) -> tuple[float, float]:
    east, north, _up = station.position.values
    return east.value, north.value


def _positions(
    solution: Solution | None = None, network: Network | None = None
) -> dict[str, tuple[float, float]]:
    """Where to draw each station, adjusted position first.

    **A held station is not in ``adjusted_stations``** -- it has no estimated
    parameters -- so a solution alone locates only the stations that moved. Any
    observation touching a fixed one would then have no line, and the residual
    map would silently omit exactly the observations that tie the network to its
    datum. The network's approximate and constraint positions fill the gap.
    """
    positions: dict[str, tuple[float, float]] = {}
    if solution is not None:
        positions.update(
            {station.station_id: _plan(station) for station in solution.adjusted_stations}
        )
    if network is not None:
        for station in network.stations.values():
            if station.id in positions:
                continue
            position = station.approx_position or station.constraint.position
            if position is not None:
                east, north, _up = position.values
                positions[station.id] = (east.value, north.value)
    return positions


def _connecting_line(stations, positions) -> QgsGeometry | None:
    """The line through the stations an observation connects.

    An observation on one station -- a height, a GNSS point -- has no line. A
    three-station angle is drawn through its vertex, which is where the angle
    actually is.
    """
    points = [positions[name] for name in stations if name in positions]
    if len(points) < 2:
        return None
    return QgsGeometry.fromPolylineXY([QgsPointXY(east, north) for east, north in points])


def _polygon(ring) -> QgsGeometry:
    return QgsGeometry.fromPolygonXY([[QgsPointXY(east, north) for east, north in ring]])


def _decision(result) -> str:
    """The three answers the w-test actually gives (``specs/19`` section 2).

    An uncheckable observation is not a passing one: nothing was tested. The
    style gives it its own symbol for that reason, so the string has to
    distinguish it here.
    """
    if result.is_uncheckable or result.w_test is None:
        return "uncheckable"
    return "accepted" if result.w_test.passed else "rejected"


def _constraint_modes(network: Network | None) -> dict[str, str]:
    """Each station's constraint mode, as the style's categories name them.

    Empty where no network was supplied: the layer still draws, every station
    falls into the free category, and nothing claims a datum status it was not
    told.
    """
    if network is None:
        return {}
    return {station.id: station.constraint.mode.value for station in network.stations.values()}
