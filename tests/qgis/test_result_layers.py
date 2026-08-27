# SPDX-License-Identifier: GPL-2.0-or-later
"""Styled result layers, run through Processing (FR-900, FR-901, FR-905).

The geometry is checked without QGIS in ``tests/test_visualization_geometry.py``
and the style/field pairing in ``tests/structural/test_layer_styles.py``. What
is left, and what only a QGIS runtime can answer, is whether the sinks are
declared in a way Processing accepts, whether the features reach them, whether
QGIS actually loads the QML files, and whether the exaggeration factor survives
into the place the user reads it.

That last one is the point of the whole module. ``specs/19`` section 3 calls an
unstated exaggeration the single most important thing to get right, so the
tests here follow one factor from the parameter, through the geometry, into the
layer's name and into every feature's attributes, and check that all four agree.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from tests.networks import trilateration

pytestmark = pytest.mark.qgis

ADJUSTING_ALGORITHMS = (
    "geocomp:analysis_network_adjust",
    "geocomp:totalstation_network",
)

LAYER_OUTPUT_NAMES = (
    "OUTPUT_STATION_LAYER",
    "OUTPUT_ELLIPSE_LAYER",
    "OUTPUT_RESIDUAL_LAYER",
    "OUTPUT_OBSERVATION_LAYER",
    "OUTPUT_CORRECTION_LAYER",
)


def _algorithm(algorithm_id: str):
    from qgis.core import QgsApplication

    algorithm = QgsApplication.processingRegistry().algorithmById(algorithm_id)
    assert algorithm is not None, f"{algorithm_id} is not registered"
    return algorithm


@pytest.fixture(scope="module")
def network_document(tmp_path_factory) -> str:
    path = tmp_path_factory.mktemp("layers") / "trilateration.json"
    path.write_text(json.dumps(trilateration().network.to_dict()), encoding="utf-8")
    return str(path)


@pytest.fixture(scope="module")
def adjusted(geocomp_provider, network_document, tmp_path_factory):
    """One adjustment with every layer requested, and the layers it produced."""
    from qgis.core import QgsProcessing, QgsProcessingContext, QgsProcessingFeedback

    directory = tmp_path_factory.mktemp("layer-run")
    parameters = {
        "NETWORK": network_document,
        "FRAME": 0,
        "DATUM": 0,
        "OUTPUT_SOLUTION": str(directory / "solution.json"),
        "EXAGGERATION": 250.0,
    }
    for name in LAYER_OUTPUT_NAMES:
        parameters[name] = QgsProcessing.TEMPORARY_OUTPUT

    algorithm = _algorithm("geocomp:analysis_network_adjust").create({})
    context = QgsProcessingContext()
    results, ok = algorithm.run(
        parameters, context, QgsProcessingFeedback(), catchExceptions=False
    )
    assert ok

    from qgis.core import QgsProcessingUtils

    layers = {}
    for name in LAYER_OUTPUT_NAMES:
        layer = QgsProcessingUtils.mapLayerFromString(results[name], context)
        assert layer is not None, f"{name} produced no layer"
        layers[name] = layer
    return results, layers, context


def _values(layer, field: str) -> list:
    index = layer.fields().indexFromName(field)
    assert index >= 0, f"{layer.name()} has no field {field!r}"
    return [feature[index] for feature in layer.getFeatures()]


class TestDeclaration:
    @pytest.mark.parametrize("algorithm_id", ADJUSTING_ALGORITHMS)
    def test_both_adjustments_offer_the_same_layers(self, geocomp_provider, algorithm_id):
        """A user should get the same map whichever adjustment they ran."""
        declared = {p.name() for p in _algorithm(algorithm_id).parameterDefinitions()}
        assert set(LAYER_OUTPUT_NAMES) <= declared
        assert "EXAGGERATION" in declared

    @pytest.mark.parametrize("algorithm_id", ADJUSTING_ALGORITHMS)
    def test_no_layer_is_created_unless_asked_for(self, geocomp_provider, algorithm_id):
        """An adjustment run from the modeller to feed another algorithm should
        not silently write five layers to disk."""
        from qgis.core import QgsProcessingParameterDefinition

        for parameter in _algorithm(algorithm_id).parameterDefinitions():
            if parameter.name() in LAYER_OUTPUT_NAMES:
                assert parameter.flags() & QgsProcessingParameterDefinition.Flag.FlagOptional
                assert not parameter.createByDefault()

    @pytest.mark.parametrize("algorithm_id", ADJUSTING_ALGORITHMS)
    def test_the_exaggeration_is_an_advanced_parameter(self, geocomp_provider, algorithm_id):
        """FR-070: the default is usable, so the control belongs behind
        Advanced rather than in front of every user."""
        from qgis.core import QgsProcessingParameterDefinition

        parameter = next(
            p
            for p in _algorithm(algorithm_id).parameterDefinitions()
            if p.name() == "EXAGGERATION"
        )
        assert parameter.flags() & QgsProcessingParameterDefinition.Flag.FlagAdvanced


class TestTheLayersArrive:
    def test_every_requested_layer_is_produced_and_valid(self, adjusted):
        _results, layers, _context = adjusted
        for name, layer in layers.items():
            assert layer.isValid(), name

    def test_there_is_one_station_and_one_ellipse_per_adjusted_station(self, adjusted):
        from geocomp.core.models import Solution

        results, layers, _context = adjusted
        solution = Solution.from_dict(
            json.loads(Path(results["OUTPUT_SOLUTION"]).read_text(encoding="utf-8"))
        )
        assert layers["OUTPUT_STATION_LAYER"].featureCount() == len(solution.adjusted_stations)
        assert layers["OUTPUT_ELLIPSE_LAYER"].featureCount() == len(solution.adjusted_stations)

    def test_there_is_one_residual_per_observation_result(self, adjusted):
        from geocomp.core.models import Solution

        results, layers, _context = adjusted
        solution = Solution.from_dict(
            json.loads(Path(results["OUTPUT_SOLUTION"]).read_text(encoding="utf-8"))
        )
        assert layers["OUTPUT_RESIDUAL_LAYER"].featureCount() == len(
            solution.observation_results
        )

    def test_the_station_layer_carries_the_coordinates_it_was_built_from(self, adjusted):
        from geocomp.core.models import Solution

        results, layers, _context = adjusted
        solution = Solution.from_dict(
            json.loads(Path(results["OUTPUT_SOLUTION"]).read_text(encoding="utf-8"))
        )
        expected = {
            station.station_id: station.position.values[0].value
            for station in solution.adjusted_stations
        }
        layer = layers["OUTPUT_STATION_LAYER"]
        for feature in layer.getFeatures():
            geometry = feature.geometry().asPoint()
            assert geometry.x() == pytest.approx(expected[feature["station"]], abs=1e-9)

    def test_the_ellipse_polygons_are_closed_rings_around_their_stations(self, adjusted):
        from qgis.core import QgsGeometry

        _results, layers, _context = adjusted
        stations = {
            feature["station"]: feature.geometry().asPoint()
            for feature in layers["OUTPUT_STATION_LAYER"].getFeatures()
        }
        for feature in layers["OUTPUT_ELLIPSE_LAYER"].getFeatures():
            ring = feature.geometry().asPolygon()[0]
            assert len(ring) > 8
            centre = stations[feature["station"]]
            assert feature.geometry().contains(QgsGeometry.fromPointXY(centre))


class TestTheExaggerationReachesTheReader:
    def test_the_layer_name_states_the_factor_and_the_confidence(self, adjusted):
        """The name is what reaches the legend. ``specs/19`` section 3 calls an
        unstated exaggeration the one thing that turns a quality visualisation
        into a misrepresentation."""
        _results, layers, _context = adjusted
        name = layers["OUTPUT_ELLIPSE_LAYER"].name()
        assert "250" in name
        assert "%" in name

    def test_every_feature_records_the_factor_it_was_drawn_at(self, adjusted):
        """A layer renamed by a user must not be able to lose the factor."""
        _results, layers, _context = adjusted
        assert set(_values(layers["OUTPUT_ELLIPSE_LAYER"], "exaggeration")) == {250.0}

    def test_the_drawn_ring_is_the_true_ellipse_times_the_factor(self, adjusted):
        """The number in the name is the number the geometry used, which is the
        whole of the requirement. A ring drawn at some other scale while the
        name said 250 would be exactly the misrepresentation being guarded."""
        _results, layers, _context = adjusted
        stations = {
            feature["station"]: feature.geometry().asPoint()
            for feature in layers["OUTPUT_STATION_LAYER"].getFeatures()
        }
        for feature in layers["OUTPUT_ELLIPSE_LAYER"].getFeatures():
            centre = stations[feature["station"]]
            ring = feature.geometry().asPolygon()[0]
            longest = max(math.hypot(p.x() - centre.x(), p.y() - centre.y()) for p in ring)
            assert longest == pytest.approx(feature["semi_major"] * 250.0, rel=1e-4)

    def test_an_unset_factor_is_fitted_to_the_network_rather_than_left_at_one(
        self, geocomp_provider, network_document, tmp_path
    ):
        """An algorithm has no map canvas, so the first factor comes from the
        network's own extent. Leaving it at 1 would produce a layer of
        invisible ellipses that looks like an empty result."""
        from qgis.core import (
            QgsProcessing,
            QgsProcessingContext,
            QgsProcessingFeedback,
            QgsProcessingUtils,
        )

        algorithm = _algorithm("geocomp:analysis_network_adjust").create({})
        context = QgsProcessingContext()
        results, ok = algorithm.run(
            {
                "NETWORK": network_document,
                "FRAME": 0,
                "DATUM": 0,
                "OUTPUT_ELLIPSE_LAYER": QgsProcessing.TEMPORARY_OUTPUT,
            },
            context,
            QgsProcessingFeedback(),
            catchExceptions=False,
        )
        assert ok
        layer = QgsProcessingUtils.mapLayerFromString(results["OUTPUT_ELLIPSE_LAYER"], context)
        factors = set(_values(layer, "exaggeration"))
        assert len(factors) == 1
        factor = factors.pop()
        assert factor > 1.0
        assert f"{factor:g}" in layer.name()


class TestTheStylesLoad:
    """FR-904 and FR-905: the QML files ship, QGIS accepts them, and the layers
    arrive already styled. A style that fails to load leaves a layer QGIS draws
    in a random colour, which looks deliberate."""

    @pytest.mark.parametrize(
        "style", ("stations", "ellipses", "residuals", "observations", "corrections")
    )
    def test_qgis_accepts_every_shipped_style(self, geocomp_provider, style):
        from qgis.core import QgsVectorLayer

        from geocomp.layers.builders import LAYER_GEOMETRY, fields_for
        from geocomp.layers.styles import style_path

        layer = QgsVectorLayer(f"{LAYER_GEOMETRY[style]}?crs=EPSG:31982", style, "memory")
        layer.dataProvider().addAttributes(list(fields_for(style)))
        layer.updateFields()
        _message, ok = layer.loadNamedStyle(str(style_path(style)))
        assert ok, f"QGIS rejected {style}.qml"

    def test_the_produced_layers_are_not_left_with_the_default_renderer(self, adjusted):
        """The post-processor is the only thing that styles a Processing
        output, and Processing holds it weakly -- an instance that went out of
        scope would leave the layers silently unstyled."""
        _results, layers, _context = adjusted
        for name, layer in layers.items():
            assert layer.renderer() is not None, name

    def test_the_residual_categories_are_the_three_the_code_produces(self, adjusted):
        """The style names its categories by string. A renderer whose attribute
        values do not match draws everything in the fallback symbol, and the
        map then looks styled while saying nothing."""
        _results, layers, _context = adjusted
        produced = set(_values(layers["OUTPUT_RESIDUAL_LAYER"], "decision"))
        assert produced <= {"accepted", "rejected", "uncheckable"}
        assert produced
