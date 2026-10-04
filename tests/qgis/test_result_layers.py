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

from tests.conftest import REPO_ROOT
from tests.networks import trilateration
from tests.qgis.conftest import post_process, requires_modern_field_api, shipped_renderer

pytestmark = pytest.mark.qgis

ADJUSTING_ALGORITHMS = (
    "geocomp:analysis_network_adjust",
    "geocomp:totalstation_network",
)

LAYER_OUTPUT_NAMES = (
    "OUTPUT_STATION_LAYER",
    "OUTPUT_ELLIPSE_LAYER",
    "OUTPUT_RELATIVE_ELLIPSE_LAYER",
    "OUTPUT_RESIDUAL_LAYER",
    "OUTPUT_OBSERVATION_LAYER",
    "OUTPUT_CORRECTION_LAYER",
)

#: Read from the directory rather than listed, so a style added for a new layer
#: -- the GNSS baselines were the first -- is checked against QGIS without
#: anyone remembering to add it here. ``tests/structural/test_layer_styles.py``
#: holds the styles and the layers one to one, so this is the same set.
SHIPPED_STYLES = tuple(
    sorted(p.stem for p in (REPO_ROOT / "geocomp" / "resources" / "styles").glob("*.qml"))
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


@pytest.fixture(scope="module")
def styled(adjusted):
    """The layers of :func:`adjusted` as Processing loads them: post-processed,
    which is where they are named, styled and given their thematic maps."""
    results, layers, context = adjusted
    for name, layer in layers.items():
        post_process(results, name, layer, context)
    return layers


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
        not silently write six layers to disk."""
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


@requires_modern_field_api
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


@requires_modern_field_api
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


@requires_modern_field_api
class TestTheRelativeEllipses:
    """``specs/19`` section 3 item 4, criterion 3: a relative ellipse for every
    pair of stations an observation joins, from their joint covariance.

    On the sparse path (``pytest --sparse``) the solution carries only each
    station's own block, and the layer is produced empty rather than drawn as
    if the stations were uncorrelated."""

    @staticmethod
    def _solution_and_network(results, network_document):
        from geocomp.core.models import Network, Solution

        solution = Solution.from_dict(
            json.loads(Path(results["OUTPUT_SOLUTION"]).read_text(encoding="utf-8"))
        )
        network = Network.from_dict(json.loads(Path(network_document).read_text(encoding="utf-8")))
        return solution, network

    def test_one_per_observed_pair_of_estimated_stations(self, adjusted, network_document):
        from geocomp.core.visualization.relative import observed_pairs

        results, layers, _context = adjusted
        solution, network = self._solution_and_network(results, network_document)
        layer = layers["OUTPUT_RELATIVE_ELLIPSE_LAYER"]
        if solution.parameter_covariance is None:
            assert layer.featureCount() == 0
            return
        estimated = {station.station_id for station in solution.adjusted_stations}
        expected = {
            frozenset(pair) for pair in observed_pairs(network) if set(pair) <= estimated
        }
        drawn = {
            frozenset((feature["from_station"], feature["to_station"]))
            for feature in layer.getFeatures()
        }
        assert expected
        assert drawn == expected
        assert layer.featureCount() == len(expected)

    def test_each_is_the_ellipse_of_the_difference_from_the_joint_covariance(
        self, adjusted, network_document
    ):
        """Against :func:`~geocomp.core.statistics.ellipses.relative_ellipse`,
        given the two stations' columns of the full covariance."""
        import numpy as np

        from geocomp.core.statistics.ellipses import relative_ellipse

        results, layers, _context = adjusted
        solution, _network = self._solution_and_network(results, network_document)
        if solution.parameter_covariance is None:
            pytest.skip("the sparse path carries no covariance between stations")
        covariance = solution.parameter_covariance
        where = {label: index for index, label in enumerate(covariance.labels)}
        matrix = np.asarray(covariance.matrix, dtype=float)
        confidence = next(s.ellipse.confidence for s in solution.adjusted_stations if s.ellipse)
        checked = 0
        for feature in layers["OUTPUT_RELATIVE_ELLIPSE_LAYER"].getFeatures():
            first, second = feature["from_station"], feature["to_station"]
            truth = relative_ellipse(
                matrix,
                [where[f"{first}.e"], where[f"{first}.n"]],
                [where[f"{second}.e"], where[f"{second}.n"]],
                confidence=confidence,
                degrees_of_freedom=solution.statistics.degrees_of_freedom,
            )
            assert feature["semi_major"] == pytest.approx(truth.semi_major, rel=1e-9)
            assert feature["semi_minor"] == pytest.approx(truth.semi_minor, rel=1e-9)
            assert feature["orientation"] == pytest.approx(math.degrees(truth.orientation), abs=1e-7)
            assert feature["confidence"] == pytest.approx(confidence)
            checked += 1
        assert checked

    def test_each_is_drawn_at_the_middle_of_its_line_at_the_stated_factor(self, adjusted):
        _results, layers, _context = adjusted
        stations = {
            feature["station"]: feature.geometry().asPoint()
            for feature in layers["OUTPUT_STATION_LAYER"].getFeatures()
        }
        layer = layers["OUTPUT_RELATIVE_ELLIPSE_LAYER"]
        for feature in layer.getFeatures():
            a, b = stations[feature["from_station"]], stations[feature["to_station"]]
            centre = ((a.x() + b.x()) / 2.0, (a.y() + b.y()) / 2.0)
            assert feature["distance"] == pytest.approx(math.hypot(b.x() - a.x(), b.y() - a.y()))
            assert feature["exaggeration"] == 250.0
            ring = feature.geometry().asPolygon()[0]
            longest = max(math.hypot(p.x() - centre[0], p.y() - centre[1]) for p in ring)
            assert longest == pytest.approx(feature["semi_major"] * 250.0, rel=1e-4)
        if layer.featureCount():
            assert "250" in layer.name()
            assert "%" in layer.name()


@requires_modern_field_api
class TestTheStylesLoad:
    """FR-904 and FR-905: the QML files ship, QGIS accepts them, and the layers
    arrive already styled. A style that fails to load leaves a layer QGIS draws
    in a random colour, which looks deliberate."""

    @pytest.mark.parametrize("style", SHIPPED_STYLES)
    def test_qgis_accepts_every_shipped_style(self, geocomp_provider, style):
        from qgis.core import QgsVectorLayer

        from geocomp.layers.builders import LAYER_GEOMETRY, fields_for
        from geocomp.layers.styles import style_path

        layer = QgsVectorLayer(f"{LAYER_GEOMETRY[style]}?crs=EPSG:31982", style, "memory")
        layer.dataProvider().addAttributes(list(fields_for(style)))
        layer.updateFields()
        _message, ok = layer.loadNamedStyle(str(style_path(style)))
        assert ok, f"QGIS rejected {style}.qml"

    @pytest.mark.parametrize("output", LAYER_OUTPUT_NAMES)
    def test_each_produced_layer_draws_with_its_shipped_style(self, styled, output):
        """FR-905. The post-processor is the only thing that styles a Processing
        output, and Processing holds it weakly -- an instance that went out of
        scope would leave the layers silently unstyled.

        Until P12c-13 this asserted only that each layer had a renderer, which
        every vector layer has, styled or not."""
        from geocomp.algorithms.layer_outputs import LAYER_OUTPUTS

        style = next(style for name, style, *_ in LAYER_OUTPUTS if name == output)
        assert styled[output].renderer().dump() == shipped_renderer(style)

    def test_the_residual_categories_are_the_three_the_code_produces(self, adjusted):
        """The style names its categories by string. A renderer whose attribute
        values do not match draws everything in the fallback symbol, and the
        map then looks styled while saying nothing."""
        _results, layers, _context = adjusted
        produced = set(_values(layers["OUTPUT_RESIDUAL_LAYER"], "decision"))
        assert produced <= {"accepted", "rejected", "uncheckable"}
        # Until phase P8b a passing row carried no w-test, and every one of
        # them was drawn as "not testable"; this network's rows mostly pass.
        assert "accepted" in produced


@requires_modern_field_api
class TestTheThematicMapsReachTheAdjustment:
    """P12b, end to end: the post-processor that styles each layer also gives it
    its thematic maps (``specs/19`` section 4), and the fields they draw by are
    filled."""

    @pytest.fixture(scope="class")
    def processed(self, styled):
        return styled

    def test_the_residual_layer_offers_its_four_maps(self, processed):
        styles = set(processed["OUTPUT_RESIDUAL_LAYER"].styleManager().styles())
        assert {
            "W-test decision",
            "Standardised residual",
            "Redundancy number",
            "Minimal detectable bias",
            "External reliability",
        } <= styles

    def test_the_stations_offer_positional_uncertainty(self, processed):
        styles = set(processed["OUTPUT_STATION_LAYER"].styleManager().styles())
        assert {"Constraint", "Positional uncertainty"} <= styles

    def test_and_the_free_stations_have_one_to_draw(self, processed):
        """P12c: offered, but drawn as *not computed* for every station, until
        the in-house adjustment filled the field DynAdjust's reader always had.
        Only a held station has none."""
        layer = processed["OUTPUT_STATION_LAYER"]
        values = [feature["positional_uncertainty"] for feature in layer.getFeatures()]
        assert sum(isinstance(value, float) and value > 0.0 for value in values) >= 1

    def test_every_checkable_residual_has_its_mdb_as_a_displacement(self, processed):
        layer = processed["OUTPUT_RESIDUAL_LAYER"]
        rows = [
            (feature["mdb"], feature["mdb_displacement"]) for feature in layer.getFeatures()
        ]
        assert rows
        # A trilateration is distances only: each MDB already is a displacement.
        for mdb, displacement in rows:
            # A float, not "not None": a NULL attribute is a QVariant in QGIS 3.
            if isinstance(mdb, float):
                assert displacement == pytest.approx(mdb)
