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
    "GNSS_HORIZON_CRS",
    "LAYER_FIELDS",
    "correction_features",
    "correction_layer",
    "ellipse_features",
    "ellipse_layer",
    "exaggeration_label",
    "fields_for",
    "gnss_baseline_features",
    "gnss_baseline_layer",
    "gnss_baseline_positions",
    "gnss_trajectory_features",
    "gnss_trajectory_layer",
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
    # GNSS baselines (FR-357, phase P7c). Distinct from "observations" because a
    # baseline carries three components and a quality record, and the
    # observations layer records only `values[0]` -- which for a baseline is the
    # first component alone, a number that means nothing on a map.
    #
    # The components are `d1/d2/d3` rather than `dx/dy/dz` because a baseline is
    # not always geocentric: `rotate_baseline_to_local` produces one in east,
    # north and up for the in-house adjustment, and a column headed `dx` holding
    # an east component is the kind of label that is read rather than checked.
    # `frame` names which three axes they are, in the same vocabulary
    # `BaselineFrame` uses, and sits beside them in the attribute table.
    "gnss_baselines": (
        ("baseline", _TEXT),
        ("base_station", _TEXT),
        ("rover_station", _TEXT),
        ("length", _REAL),
        ("sigma_length", _REAL),
        ("frame", _TEXT),
        ("d1", _REAL),
        ("d2", _REAL),
        ("d3", _REAL),
        ("sigma_d1", _REAL),
        ("sigma_d2", _REAL),
        ("sigma_d3", _REAL),
        ("independent", _TEXT),
        ("reduced", _TEXT),
        ("solution_status", _TEXT),
        ("fixed_fraction", _REAL),
    ),
    # GNSS trajectory (FR-357, FR-902, phase P7c). The other half of FR-357:
    # one point per epoch of a processed run, which is what a kinematic session
    # produces and what "imported as a point layer or a trajectory" in
    # specs/11 section 3.2 asks for.
    #
    # The sigmas are north, east and up whatever frame the engine wrote, so a
    # column means one thing across every file -- see
    # `core/techniques/gnss/trajectory.py`.
    "gnss_trajectory": (
        ("epoch", _TEXT),
        ("status", _TEXT),
        ("fixed", _TEXT),
        ("satellites", _INT),
        ("ratio", _REAL),
        ("age", _REAL),
        ("latitude", _REAL),
        ("longitude", _REAL),
        ("height", _REAL),
        ("sigma_n", _REAL),
        ("sigma_e", _REAL),
        ("sigma_u", _REAL),
        ("drms", _REAL),
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
    "gnss_baselines": "LineString",
    "gnss_trajectory": "Point",
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


# -- GNSS baselines -------------------------------------------------------

#: The frame the horizons a baseline carries are drawn in.
#:
#: :attr:`Baseline.base_horizon` is geodetic latitude and longitude on the
#: ellipsoid the engine's positions were expressed on -- ITRF in practice, since
#: that is what precise products are in. Calling that EPSG:4326 is wrong by the
#: few centimetres the realisations differ by, and right to far better than any
#: map draws; the ``.pos`` file does not state its realisation, so there is
#: nothing more exact to use. A caller who knows better passes ``crs``.
GNSS_HORIZON_CRS = "EPSG:4326"


def gnss_baseline_positions(baselines) -> dict[str, tuple[float, float]]:
    """Where to draw each end, from the baselines' own recorded horizons.

    A baseline is a geocentric vector and has no position of its own, but it
    carries the geodetic latitude and longitude of both its ends -- which is
    exactly what the map needs, in degrees and longitude first. So this layer is
    drawable straight out of the GNSS module, with no network, no adjustment and
    no station list.

    Where two baselines disagree about one station -- they will, by the
    millimetres that separate two determinations of it -- the first wins. A
    station drawn twice would double every line touching it.
    """
    positions: dict[str, tuple[float, float]] = {}
    for baseline in baselines:
        for station, horizon in (
            (baseline.base_station, baseline.base_horizon),
            (baseline.rover_station, baseline.rover_horizon),
        ):
            if station not in positions:
                latitude, longitude = horizon
                positions[station] = (math.degrees(longitude), math.degrees(latitude))
    return positions


def gnss_baseline_features(
    baselines, positions: dict[str, tuple[float, float]] | None = None
) -> Iterator[QgsFeature]:
    """One line per determined baseline, with its quality (FR-357).

    Args:
        baselines: :class:`~geocomp.core.techniques.gnss.baselines.Baseline`
            objects. Typed loosely so this module does not import the GNSS
            technique package: ``layers`` sits above ``core`` and reaches down,
            never the other way.
        positions: Station id to ``(easting, northing)``, for drawing the
            baselines somewhere other than their own horizons -- a projected
            network, say. ``None`` uses :func:`gnss_baseline_positions`.

    A baseline whose ends are not both in *positions* is skipped rather than
    drawn at the origin, which is the rule :func:`_connecting_line` applies to
    every other layer.
    """
    baselines = list(baselines)
    if positions is None:
        positions = gnss_baseline_positions(baselines)
    fields = fields_for("gnss_baselines")
    for baseline in baselines:
        geometry = _connecting_line((baseline.base_station, baseline.rover_station), positions)
        if geometry is None:
            continue
        length = baseline.length
        components = baseline.components
        fixed_fraction = baseline.meta.get("fixed_fraction")
        feature = QgsFeature(fields)
        feature.setGeometry(geometry)
        feature.setAttributes(
            [
                baseline.id,
                baseline.base_station,
                baseline.rover_station,
                length.value,
                length.std_dev,
                baseline.frame.value,
                components[0].value,
                components[1].value,
                components[2].value,
                components[0].std_dev,
                components[1].std_dev,
                components[2].std_dev,
                _independence(baseline),
                "yes" if baseline.antenna_reduction is not None else "no",
                str(baseline.meta.get("solution_status", "")),
                float(fixed_fraction) if fixed_fraction is not None else None,
            ]
        )
        yield feature


def gnss_baseline_layer(
    baselines,
    positions: dict[str, tuple[float, float]] | None = None,
    *,
    crs: str = "",
    name: str = "",
) -> QgsVectorLayer:
    """Determined baselines, categorised by whether they are independent."""
    return _build(
        "gnss_baselines",
        crs or GNSS_HORIZON_CRS,
        name or _tr("GNSS baselines"),
        gnss_baseline_features(baselines, positions),
    )


def _independence(baseline) -> str:
    """Independent, dependent, or not yet assessed -- as three states, not two.

    Text rather than a boolean because ``is_independent`` is ``None`` until
    :func:`~geocomp.core.techniques.gnss.baselines.independent_subset` has run,
    and a map that rendered that third state as "no" would report an
    unassessed baseline as one carrying no new information. The style gives it
    its own symbol for the same reason.
    """
    if baseline.is_independent is None:
        return ""
    return "yes" if baseline.is_independent else "no"


# -- GNSS trajectory ------------------------------------------------------


def gnss_trajectory_features(points) -> Iterator[QgsFeature]:
    """One point per solution epoch, with its quality (FR-357, FR-603).

    Args:
        points: :class:`~geocomp.core.techniques.gnss.trajectory.TrajectoryPoint`
            objects. Typed loosely for the same reason the baseline builder is:
            ``layers`` reaches down into ``core`` and never the other way.

    The epoch is written as an ISO-8601 string rather than a date field.
    ``QDateTime`` round-trips through a shapefile as a date alone, losing the
    time, and for a trajectory the time *is* the identity of the row.
    """
    fields = fields_for("gnss_trajectory")
    for point in points:
        quality = point.quality
        north, east, up = point.sigmas
        feature = QgsFeature(fields)
        feature.setGeometry(
            QgsGeometry.fromPointXY(
                QgsPointXY(point.longitude_degrees, point.latitude_degrees)
            )
        )
        feature.setAttributes(
            [
                quality.time.isoformat(),
                quality.status,
                # A separate column from `status`, because the one question
                # asked of a trajectory more than any other is how much of it
                # fixed, and answering it should not mean knowing which of
                # RTKLIB's six status names count.
                "yes" if quality.status == "FIXED" else "no",
                quality.satellites,
                quality.ratio,
                quality.age,
                point.latitude_degrees,
                point.longitude_degrees,
                point.height,
                north,
                east,
                up,
                point.drms,
            ]
        )
        yield feature


def gnss_trajectory_layer(points, *, crs: str = "", name: str = "") -> QgsVectorLayer:
    """A processed run's epochs, categorised by solution status."""
    return _build(
        "gnss_trajectory",
        crs or GNSS_HORIZON_CRS,
        name or _tr("GNSS trajectory"),
        gnss_trajectory_features(points),
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
