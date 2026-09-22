# SPDX-License-Identifier: GPL-2.0-or-later
"""The GNSS baseline layer, run through Processing (FR-357, FR-902).

``specs/11-module-gnss.md`` section 4.2. The attribute table and the style are
paired without QGIS in ``tests/structural/test_layer_styles.py``, and what a
baseline *is* has its own tier-1 suite. What only a QGIS runtime can answer is
whether the sink is declared in a way Processing accepts, whether the features
reach it, and whether the three-state ``independent`` column really renders as
three categories rather than as a fallback symbol.

**The fixture is built rather than recorded**, and deliberately: three solutions
over three stations are what it takes to have a dependent baseline at all, and
the committed ``.pos`` corpus has one relative solution. Each file here is
``xyz.pos`` with its two input names and its reference position rewritten, so
the numbers are still RTKLIB's -- only the topology is arranged.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.conftest import REPO_ROOT
from tests.qgis.conftest import requires_modern_field_api

pytestmark = pytest.mark.qgis

SOURCE = REPO_ROOT / "tests" / "data" / "rtklib" / "pos" / "xyz.pos"
STYLE_DIR = REPO_ROOT / "geocomp" / "resources" / "styles"

#: How far station 1111 sits from 0759, in metres of ECEF x. Large enough that
#: the two are distinct points on the map and small enough to stay a plausible
#: baseline.
OFFSET = 100.0


def _rewrite(text: str, *, rover: str, base: str, reference: tuple[float, float, float],
             offset: float) -> str:
    """One ``.pos`` re-labelled and translated, header and data together."""
    inputs = iter((f"{rover}0920.05o", f"{base}0920.05o"))
    lines = []
    for line in text.splitlines():
        if line.startswith("% inp file") and line.rstrip().endswith(".05o"):
            lines.append(f"% inp file  : {next(inputs)}")
        elif line.startswith("% ref pos"):
            lines.append(
                "% ref pos   : {:16.4f} {:16.4f} {:16.4f}".format(*reference)
            )
        elif line.startswith("%") or not line.strip():
            lines.append(line)
        else:
            parts = line.split()
            parts[2] = f"{float(parts[2]) + offset:.4f}"
            lines.append(" ".join(parts))
    return "\n".join(lines) + "\n"


def _last_position(text: str) -> tuple[float, float, float]:
    data = [line for line in text.splitlines() if line.strip() and not line.startswith("%")]
    parts = data[-1].split()
    return (float(parts[2]), float(parts[3]), float(parts[4]))


@pytest.fixture(scope="module")
def solution_folder(tmp_path_factory) -> Path:
    """Three baselines over three stations: 3040-0759, 3040-1111, 0759-1111.

    Two of the three span the station graph, so exactly one comes back
    dependent -- which is the state the layer exists to show.
    """
    text = SOURCE.read_text(encoding="utf-8")
    base_position = (-3978242.1933, 3382841.1747, 3649902.2990)
    rover_position = _last_position(text)

    folder = tmp_path_factory.mktemp("gnss-baselines")
    (folder / "a.pos").write_text(
        _rewrite(text, rover="0759", base="3040", reference=base_position, offset=0.0),
        encoding="utf-8",
    )
    (folder / "b.pos").write_text(
        _rewrite(text, rover="1111", base="3040", reference=base_position, offset=OFFSET),
        encoding="utf-8",
    )
    # 0759 is where a.pos put it, so the triangle closes: the third baseline is
    # an exact combination of the other two, which is what makes it dependent.
    (folder / "c.pos").write_text(
        _rewrite(text, rover="1111", base="0759", reference=rover_position, offset=OFFSET),
        encoding="utf-8",
    )
    return folder


def _algorithm():
    from qgis.core import QgsApplication

    algorithm = QgsApplication.processingRegistry().algorithmById("geocomp:gnss_build_baselines")
    assert algorithm is not None, "geocomp:gnss_build_baselines is not registered"
    return algorithm


def _run(folder: Path, tmp_path: Path, **extra):
    from qgis.core import (
        QgsProcessing,
        QgsProcessingContext,
        QgsProcessingFeedback,
        QgsProcessingUtils,
    )

    parameters = {
        "FOLDER": str(folder),
        "INDEPENDENT_ONLY": False,
        "OUTPUT_JSON": str(tmp_path / "baselines.json"),
        "OUTPUT_LAYER": QgsProcessing.TEMPORARY_OUTPUT,
    }
    parameters.update(extra)
    algorithm = _algorithm().create({})
    context = QgsProcessingContext()
    results, ok = algorithm.run(
        parameters, context, QgsProcessingFeedback(), catchExceptions=False
    )
    assert ok
    layer = QgsProcessingUtils.mapLayerFromString(results["OUTPUT_LAYER"], context)
    assert layer is not None, "OUTPUT_LAYER produced no layer"
    return results, layer


def _values(layer, field: str) -> list:
    index = layer.fields().indexFromName(field)
    assert index >= 0, f"{layer.name()} has no field {field!r}"
    return [feature[index] for feature in layer.getFeatures()]


class TestDeclaration:
    def test_the_layer_is_offered_and_not_created_unless_asked_for(self, geocomp_provider):
        """A baselines run feeding another algorithm should not silently write
        a layer, while one run from the toolbox is a click away from it."""
        from qgis.core import QgsProcessingParameterDefinition

        parameters = {p.name(): p for p in _algorithm().parameterDefinitions()}
        assert "OUTPUT_LAYER" in parameters
        parameter = parameters["OUTPUT_LAYER"]
        assert parameter.flags() & QgsProcessingParameterDefinition.Flag.FlagOptional
        assert not parameter.createByDefault()


@requires_modern_field_api
class TestTheLayerArrives:
    def test_every_built_baseline_is_drawn_dependent_ones_included(
        self, geocomp_provider, solution_folder, tmp_path
    ):
        """``specs/11`` section 3.1: the dependent ones are marked rather than
        discarded, and a map that dropped them would be the reason nobody
        noticed they were there."""
        _results, layer = _run(solution_folder, tmp_path)
        assert layer.isValid()
        assert layer.featureCount() == 3
        assert sorted(_values(layer, "independent")) == ["no", "yes", "yes"]

    def test_the_dependent_one_is_the_baseline_that_closes_the_triangle(
        self, geocomp_provider, solution_folder, tmp_path
    ):
        """Not merely that *a* baseline is dependent: which one. The spanning
        forest is chosen by covariance trace with ties broken by input order,
        and all three solutions carry the same covariance here, so the third
        file is the one that closes the loop."""
        _results, layer = _run(solution_folder, tmp_path)
        dependent = [
            feature["baseline"]
            for feature in layer.getFeatures()
            if feature["independent"] == "no"
        ]
        assert dependent == ["0759-1111"]

    def test_the_geometry_joins_the_two_stations_the_baseline_connects(
        self, geocomp_provider, solution_folder, tmp_path
    ):
        """The vector is geocentric and undrawable; what the map shows is the
        pair of marks, from the horizons the baseline itself carries."""
        _results, layer = _run(solution_folder, tmp_path)
        ends = {}
        for feature in layer.getFeatures():
            line = feature.geometry().asPolyline()
            assert len(line) == 2
            ends[feature["baseline"]] = line

        # 0759 is the rover of the first baseline and the base of the third,
        # and it is one station, so the two must coincide.
        assert ends["3040-0759"][1].x() == pytest.approx(ends["0759-1111"][0].x(), abs=1e-12)
        assert ends["3040-0759"][1].y() == pytest.approx(ends["0759-1111"][0].y(), abs=1e-12)

    def test_the_components_carry_the_frame_that_names_their_axes(
        self, geocomp_provider, solution_folder, tmp_path
    ):
        """``d1/d2/d3`` are only meaningful beside ``frame``: a rotated
        baseline puts east, north and up in the same three columns."""
        _results, layer = _run(solution_folder, tmp_path)
        assert set(_values(layer, "frame")) == {"ecef"}
        for feature in layer.getFeatures():
            assert feature["d1"] != 0.0
            assert feature["sigma_d1"] > 0.0
            assert feature["length"] > 0.0

    def test_the_quality_reaches_the_attribute_table(
        self, geocomp_provider, solution_folder, tmp_path
    ):
        """FR-603. A baseline reported without its fixed fraction looks the
        same whether its ambiguities resolved or not."""
        _results, layer = _run(solution_folder, tmp_path)
        fractions = _values(layer, "fixed_fraction")
        assert len(fractions) == 3
        for fraction in fractions:
            assert fraction is not None
            assert 0.0 < fraction <= 1.0
        assert set(_values(layer, "solution_status")) == {"FIXED"}

    def test_the_json_and_the_layer_agree_about_what_was_kept(
        self, geocomp_provider, solution_folder, tmp_path
    ):
        """The layer draws everything built; the JSON carries what was kept.
        Both must name the same dependent baseline, or one of the two is
        describing a different run."""
        results, layer = _run(solution_folder, tmp_path)
        document = json.loads(Path(results["OUTPUT_JSON"]).read_text(encoding="utf-8"))
        drawn = {
            feature["baseline"]: feature["independent"] for feature in layer.getFeatures()
        }
        assert set(document["dependent"]) == {name for name, v in drawn.items() if v == "no"}
        assert set(document["independent"]) == {name for name, v in drawn.items() if v == "yes"}
        assert set(document["quality"]) == set(drawn)

    def test_keeping_only_the_independent_subset_still_draws_all_three(
        self, geocomp_provider, solution_folder, tmp_path
    ):
        """The point of the layer: the adjustment gets two baselines, and the
        reader gets to see that a third was processed and set aside."""
        results, layer = _run(solution_folder, tmp_path, INDEPENDENT_ONLY=True)
        document = json.loads(Path(results["OUTPUT_JSON"]).read_text(encoding="utf-8"))
        assert len(document["observations"]) == 2
        assert layer.featureCount() == 3


@pytest.fixture(scope="module")
def marked_baselines(solution_folder):
    """The same three baselines, built through the core rather than the
    algorithm -- which is what the memory-layer builder takes.

    Deliberately not the algorithm's own objects: a builder that only ever
    sees what one algorithm hands it is untested for everything else, and
    ``gnss_baseline_layer`` is public for the dialogs still to come.
    """
    from geocomp.core.techniques.gnss import independent_subset
    from geocomp.engines.rtklib.baseline import baseline_from_solution
    from geocomp.engines.rtklib.read_pos import read_pos

    built = []
    for path in sorted(solution_folder.glob("*.pos")):
        solution = read_pos(path)
        rover, base = (Path(n).stem[:4].upper() for n in solution.inputs[:2])
        built.append(
            baseline_from_solution(solution, base_station=base, rover_station=rover)
        )
    independent, dependent = independent_subset(built)
    return [*independent, *dependent]


@requires_modern_field_api
class TestTheStyleLoads:
    """FR-904 and FR-905. Checked on the memory layer rather than on the sink,
    because that is where styling is deterministic: a Processing sink is styled
    by a post-processor, and a post-processor runs when QGIS loads the layer
    into a project rather than when ``run()`` returns. Asserting a renderer on
    the sink would be asserting on whether this test happened to trigger that,
    not on whether the style is right.
    """

    def test_qgis_accepts_the_baseline_style(self, geocomp_provider):
        from qgis.core import QgsVectorLayer

        from geocomp.layers.builders import LAYER_GEOMETRY, fields_for
        from geocomp.layers.styles import style_path

        layer = QgsVectorLayer(
            f"{LAYER_GEOMETRY['gnss_baselines']}?crs=EPSG:4326", "baselines", "memory"
        )
        layer.dataProvider().addAttributes(list(fields_for("gnss_baselines")))
        layer.updateFields()
        _message, ok = layer.loadNamedStyle(str(style_path("gnss_baselines")))
        assert ok, "QGIS rejected gnss_baselines.qml"

    def test_the_built_layer_is_categorised_on_independence(
        self, geocomp_provider, marked_baselines
    ):
        """A categorised renderer whose attribute is missing does not fail --
        it draws every feature in the fallback symbol, so the map looks styled
        and says nothing."""
        from geocomp.layers.builders import gnss_baseline_layer

        renderer = gnss_baseline_layer(marked_baselines).renderer()
        assert renderer is not None
        assert renderer.type() == "categorizedSymbol"
        assert renderer.classAttribute() == "independent"

    def test_the_drawn_values_are_categories_the_style_declares(
        self, geocomp_provider, marked_baselines
    ):
        from geocomp.layers.builders import gnss_baseline_layer

        layer = gnss_baseline_layer(marked_baselines)
        declared = {category.value() for category in layer.renderer().categories()}
        assert set(_values(layer, "independent")) <= declared

    def test_the_layer_is_drawable_with_nothing_but_the_baselines(
        self, geocomp_provider, marked_baselines
    ):
        """No network, no adjustment, no station list: the horizons a baseline
        already carries are enough, which is what makes this layer available
        the moment processing finishes."""
        from geocomp.layers.builders import gnss_baseline_layer

        layer = gnss_baseline_layer(marked_baselines)
        assert layer.isValid()
        assert layer.featureCount() == len(marked_baselines)
        assert layer.crs().authid() == "EPSG:4326"
        assert not layer.extent().isEmpty()


# -- the trajectory layer -------------------------------------------------


@pytest.fixture(scope="module")
def trajectory():
    """The committed ECEF solution, every epoch of it.

    Built from the fixture rather than from a run: the four processing
    algorithms need ``rnx2rtkp``, which is tier 4, and what is being checked
    here is the layer.
    """
    from geocomp.engines.rtklib.read_pos import read_pos
    from geocomp.engines.rtklib.trajectory import trajectory_from_solution

    return trajectory_from_solution(read_pos(SOURCE))


class TestTheTrajectoryIsOffered:
    @pytest.mark.parametrize(
        "algorithm_id",
        (
            "geocomp:gnss_relative_static",
            "geocomp:gnss_relative_kinematic",
            "geocomp:gnss_absolute_static",
            "geocomp:gnss_absolute_kinematic",
        ),
    )
    def test_every_mode_offers_it_and_creates_none_by_default(
        self, geocomp_provider, algorithm_id
    ):
        """All four, not only the kinematic pair: a static run's epochs are its
        filter converging, and a parameter present on two of four otherwise
        identical algorithms is a difference nobody would remember."""
        from qgis.core import QgsApplication, QgsProcessingParameterDefinition

        algorithm = QgsApplication.processingRegistry().algorithmById(algorithm_id)
        assert algorithm is not None, f"{algorithm_id} is not registered"
        parameters = {p.name(): p for p in algorithm.parameterDefinitions()}
        assert "OUTPUT_LAYER" in parameters
        assert parameters["OUTPUT_LAYER"].flags() & (
            QgsProcessingParameterDefinition.Flag.FlagOptional
        )
        assert not parameters["OUTPUT_LAYER"].createByDefault()


@requires_modern_field_api
class TestTheTrajectoryLayer:
    def test_one_feature_per_epoch(self, geocomp_provider, trajectory):
        from geocomp.layers.builders import gnss_trajectory_layer

        layer = gnss_trajectory_layer(trajectory)
        assert layer.isValid()
        assert layer.featureCount() == len(trajectory)
        assert layer.crs().authid() == "EPSG:4326"

    def test_the_points_are_where_the_epochs_are(self, geocomp_provider, trajectory):
        from geocomp.layers.builders import gnss_trajectory_layer

        layer = gnss_trajectory_layer(trajectory)
        for feature, point in zip(layer.getFeatures(), trajectory, strict=True):
            geometry = feature.geometry().asPoint()
            assert geometry.x() == pytest.approx(point.longitude_degrees, abs=1e-12)
            assert geometry.y() == pytest.approx(point.latitude_degrees, abs=1e-12)

    def test_the_quality_columns_are_filled(self, geocomp_provider, trajectory):
        from geocomp.layers.builders import gnss_trajectory_layer

        layer = gnss_trajectory_layer(trajectory)
        assert set(_values(layer, "status")) <= {
            "FIXED",
            "FLOAT",
            "SBAS",
            "DGPS",
            "SINGLE",
            "PPP",
        }
        assert set(_values(layer, "fixed")) <= {"yes", "no"}
        assert all(count > 0 for count in _values(layer, "satellites"))
        assert all(value > 0.0 for value in _values(layer, "drms"))

    def test_fixed_agrees_with_status(self, geocomp_provider, trajectory):
        """The convenience column cannot be allowed to disagree with the one it
        summarises -- that is worse than not having it."""
        from geocomp.layers.builders import gnss_trajectory_layer

        for feature in gnss_trajectory_layer(trajectory).getFeatures():
            assert feature["fixed"] == ("yes" if feature["status"] == "FIXED" else "no")

    def test_the_epoch_is_written_as_a_round_trippable_string(
        self, geocomp_provider, trajectory
    ):
        """A QDateTime field loses the time through a shapefile, and for a
        trajectory the time is the identity of the row."""
        from datetime import datetime

        from geocomp.layers.builders import gnss_trajectory_layer

        layer = gnss_trajectory_layer(trajectory)
        for feature, point in zip(layer.getFeatures(), trajectory, strict=True):
            assert datetime.fromisoformat(feature["epoch"]) == point.quality.time

    def test_qgis_accepts_the_trajectory_style(self, geocomp_provider):
        from qgis.core import QgsVectorLayer

        from geocomp.layers.builders import LAYER_GEOMETRY, fields_for
        from geocomp.layers.styles import style_path

        layer = QgsVectorLayer(
            f"{LAYER_GEOMETRY['gnss_trajectory']}?crs=EPSG:4326", "trajectory", "memory"
        )
        layer.dataProvider().addAttributes(list(fields_for("gnss_trajectory")))
        layer.updateFields()
        _message, ok = layer.loadNamedStyle(str(style_path("gnss_trajectory")))
        assert ok, "QGIS rejected gnss_trajectory.qml"

    def test_the_layer_is_categorised_on_solution_status(
        self, geocomp_provider, trajectory
    ):
        """``specs/11`` section 5: a map of epochs coloured by status is the
        fastest way to see what a session actually achieved."""
        from geocomp.layers.builders import gnss_trajectory_layer

        renderer = gnss_trajectory_layer(trajectory).renderer()
        assert renderer.type() == "categorizedSymbol"
        assert renderer.classAttribute() == "status"

    def test_every_status_the_file_contains_has_a_category(
        self, geocomp_provider, trajectory
    ):
        """The fixture holds both float and fixed epochs, so this is not
        vacuous: a renderer whose values do not match draws everything in the
        fallback symbol and the map says nothing."""
        from geocomp.layers.builders import gnss_trajectory_layer

        layer = gnss_trajectory_layer(trajectory)
        produced = set(_values(layer, "status"))
        assert len(produced) >= 2
        declared = {category.value() for category in layer.renderer().categories()}
        assert produced <= declared
