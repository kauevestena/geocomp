# SPDX-License-Identifier: GPL-2.0-or-later
"""The four Integration presets, run through Processing (``specs/13`` section 1).

The combination is tested without QGIS in ``tests/test_integration.py`` and
``tests/test_integration_modes.py``. What only a QGIS runtime can show is that
the presets register and are accepted by Processing, that each takes the
network documents the technique algorithms write, reads a projected input's
grid from QGIS's own CRS, and produces one solution, a report with the
per-technique section, and the outputs it declares (ROADMAP P9b exit).
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pytest

from tests import combined_network as field
from tests.qgis.conftest import requires_modern_field_api

pytestmark = pytest.mark.qgis

PRESETS = (
    "geocomp:integration_gnss_total_station",
    "geocomp:integration_total_station_level",
    "geocomp:integration_gnss_level",
    "geocomp:integration_multiple",
)


@pytest.fixture(autouse=True, scope="module")
def _registered(geocomp_provider):
    return geocomp_provider


def _algorithm(algorithm_id: str):
    from qgis.core import QgsApplication

    algorithm = QgsApplication.processingRegistry().algorithmById(algorithm_id)
    assert algorithm is not None, f"{algorithm_id} is not registered"
    return algorithm


def _run(algorithm_id: str, parameters: dict):
    from qgis.core import QgsProcessingContext, QgsProcessingFeedback

    algorithm = _algorithm(algorithm_id).create({})
    results, ok = algorithm.run(
        parameters, QgsProcessingContext(), QgsProcessingFeedback(), catchExceptions=False
    )
    assert ok, f"{algorithm_id} reported failure"
    return results


def _write(path: Path, network) -> str:
    path.write_text(json.dumps(network.to_dict(), indent=2), encoding="utf-8")
    return str(path)


def _gnss():
    """The GNSS input, its two control marks starting exactly where they are
    -- the base coordinates a processing would have used -- so holding them
    there holds the truth."""
    from dataclasses import replace

    from geocomp.core.geodesy.frames import transform_point
    from tests.test_integration import _cartesian, gnss_input

    network = gnss_input()
    for name in field.HELD:
        xyz = transform_point(field.TRUTH[name], source="ITRF2020", target="ITRF2014", epoch=2020.0).xyz
        network.stations[name] = replace(
            network.stations[name], approx_position=_cartesian(xyz, "ITRF2014", network.epoch)
        )
    return network


def _geoid_file(path: Path) -> str:
    """The test's planar geoid as an ESRI ASCII grid: exact under bilinear
    interpolation, so the file and the in-memory model are the same model."""
    from tests.test_integration import GEOID

    step = math.degrees(GEOID.coverage.north - GEOID.coverage.south) / 2.0
    lines = [
        "ncols 3",
        "nrows 3",
        f"xllcenter {math.degrees(GEOID.coverage.west)!r}",
        f"yllcenter {math.degrees(GEOID.coverage.south)!r}",
        f"cellsize {step!r}",
    ]
    lines.extend(" ".join(repr(float(v)) for v in row) for row in np.asarray(GEOID.values)[::-1])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(path)


def _outputs(tmp_path: Path) -> dict:
    return {
        "OUTPUT_SOLUTION": str(tmp_path / "solution.json"),
        "OUTPUT_HTML": str(tmp_path / "report.html"),
    }


def _solution(results):
    from geocomp.core.models import Solution

    return Solution.from_dict(json.loads(Path(results["OUTPUT_SOLUTION"]).read_text(encoding="utf-8")))


class TestRegistration:
    def test_the_four_presets_are_registered_in_the_integration_group(self):
        for algorithm_id in PRESETS:
            assert _algorithm(algorithm_id).groupId() == "integration"

    def test_every_parameter_is_accepted_by_processing(self):
        for algorithm_id in PRESETS:
            algorithm = _algorithm(algorithm_id).create({})
            for definition in algorithm.parameterDefinitions():
                assert definition.name(), algorithm_id

    def test_each_has_its_own_help(self):
        texts = {_algorithm(a).shortHelpString() for a in PRESETS}
        assert len(texts) == 4


class TestGnssAndTotalStation:
    @pytest.fixture(scope="class")
    def run(self, tmp_path_factory):
        from tests.test_integration_modes import grid_total_station_input

        tmp_path = tmp_path_factory.mktemp("gnss-ts")
        results = _run(
            "geocomp:integration_gnss_total_station",
            {
                "GNSS": _write(tmp_path / "gnss.json", _gnss()),
                # In UTM 22S: its starts reach the geocentric frame through the
                # projection QGIS says EPSG:31982 is.
                "TOTAL_STATION": _write(tmp_path / "ts.json", grid_total_station_input()),
                "FIXED_STATIONS": ",".join(field.HELD),
                **_outputs(tmp_path),
            },
        )
        return results

    def test_one_solution_in_the_chosen_frame(self, run):
        solution = _solution(run)
        assert solution.crs == "ITRF2020"
        assert solution.provenance.algorithm_id == "geocomp:integration_gnss_total_station"
        assert solution.provenance.parameters["fixed"] == list(field.HELD)
        assert run["ENGINE_USED"] == "in_house"

    def test_the_marks_land_on_the_truth(self, run):
        solution = _solution(run)
        for station in solution.adjusted_stations:
            xyz = np.array([q.value for q in station.position.values])
            assert np.linalg.norm(xyz - field.TRUTH[station.station_id]) < 0.03, station.station_id

    def test_the_report_has_the_techniques_section(self, run):
        html = Path(run["OUTPUT_HTML"]).read_text(encoding="utf-8")
        assert "<h2>Techniques</h2>" in html
        assert "<td>Total station</td>" in html


class TestTotalStationAndLevel:
    def test_it_combines_in_the_total_stations_own_system(self, tmp_path):
        from tests.test_integration_modes import GRID, LOCAL, local_levelling, local_total_station

        results = _run(
            "geocomp:integration_total_station_level",
            {
                "TOTAL_STATION": _write(tmp_path / "ts.json", local_total_station()),
                "LEVELLING": _write(tmp_path / "levelling.json", local_levelling()),
                "EPOCH": "2026.7",
                **_outputs(tmp_path),
            },
        )
        solution = _solution(results)
        assert solution.crs == GRID
        assert solution.epoch.decimal_year == pytest.approx(2026.7)
        for station in solution.adjusted_stations:
            assert station.position.values[2].value == pytest.approx(LOCAL[station.station_id][2], abs=0.005)
        assert results["DEGREES_OF_FREEDOM"] > 0
        html = Path(results["OUTPUT_HTML"]).read_text(encoding="utf-8")
        assert "<td>Levelling</td>" in html

    def test_without_an_epoch_anywhere_it_asks_for_one(self, tmp_path):
        from qgis.core import QgsProcessingException

        from tests.test_integration_modes import local_levelling, local_total_station

        with pytest.raises(QgsProcessingException, match="epoch"):
            _run(
                "geocomp:integration_total_station_level",
                {
                    "TOTAL_STATION": _write(tmp_path / "ts.json", local_total_station()),
                    "LEVELLING": _write(tmp_path / "levelling.json", local_levelling()),
                    **_outputs(tmp_path),
                },
            )


class TestGnssAndLevel:
    def test_the_geoid_is_named_and_tested(self, tmp_path):
        from tests.test_integration_modes import levelling_with_benchmark

        results = _run(
            "geocomp:integration_gnss_level",
            {
                "GNSS": _write(tmp_path / "gnss.json", _gnss()),
                "LEVELLING": _write(tmp_path / "levelling.json", levelling_with_benchmark()),
                "GEOID": _geoid_file(tmp_path / "curitiba-planar.asc"),
                "GEOID_SIGMA": 0.03,
                "FIXED_STATIONS": ",".join(field.HELD),
                # Asked for; orthometric heights keep it in-house, with the reason.
                "ENGINE": 1,
                **_outputs(tmp_path),
            },
        )
        assert results["ENGINE_USED"] == "in_house"
        solution = _solution(results)
        parameters = solution.provenance.parameters
        assert parameters["geoid_model"] == "curitiba-planar"
        assert "orthometric" in parameters["routing"]["reason"]
        assert parameters["geoid_residuals"]
        html = Path(results["OUTPUT_HTML"]).read_text(encoding="utf-8")
        assert "Geoid residuals" in html and "curitiba-planar" in html

    def test_an_exactly_held_benchmark_is_refused_by_name(self, tmp_path):
        from qgis.core import QgsProcessingException

        from tests.test_integration_modes import levelling_with_benchmark

        with pytest.raises(QgsProcessingException, match="exactly"):
            _run(
                "geocomp:integration_gnss_level",
                {
                    "GNSS": _write(tmp_path / "gnss.json", _gnss()),
                    "LEVELLING": _write(tmp_path / "levelling.json", levelling_with_benchmark(sigma=None)),
                    "GEOID": _geoid_file(tmp_path / "curitiba-planar.asc"),
                    "FIXED_STATIONS": ",".join(field.HELD),
                    **_outputs(tmp_path),
                },
            )


class TestMultiple:
    def test_three_techniques_one_solution_and_the_components(self, tmp_path):
        from tests.test_integration import levelling_input, total_station_input

        results = _run(
            "geocomp:integration_multiple",
            {
                "GNSS": _write(tmp_path / "gnss.json", _gnss()),
                "TOTAL_STATION": _write(tmp_path / "ts.json", total_station_input()),
                "LEVELLING": _write(tmp_path / "levelling.json", levelling_input()),
                "GEOID": _geoid_file(tmp_path / "curitiba-planar.asc"),
                "GEOID_SIGMA": 0.03,
                "FIXED_STATIONS": ",".join(field.HELD),
                "VARIANCE_COMPONENTS": True,
                "OUTPUT_NETWORK": str(tmp_path / "combined.json"),
                **_outputs(tmp_path),
            },
        )
        solution = _solution(results)
        components = solution.provenance.parameters["variance_components"]
        assert set(components) >= {"gnss", "total_station", "levelling"}
        combined = json.loads(Path(results["OUTPUT_NETWORK"]).read_text(encoding="utf-8"))
        assert combined["crs"] == "ITRF2020"
        html = Path(results["OUTPUT_HTML"]).read_text(encoding="utf-8")
        assert "Variance components" in html

    def test_two_techniques_are_sent_to_their_own_preset(self, tmp_path):
        from qgis.core import QgsProcessingException

        from tests.test_integration import total_station_input

        with pytest.raises(QgsProcessingException, match="at least 3"):
            _run(
                "geocomp:integration_multiple",
                {
                    "GNSS": _write(tmp_path / "gnss.json", _gnss()),
                    "TOTAL_STATION": _write(tmp_path / "ts.json", total_station_input()),
                    "FIXED_STATIONS": ",".join(field.HELD),
                    **_outputs(tmp_path),
                },
            )


@requires_modern_field_api
class TestTheLayers:
    """A geocentric solution drawn in its own frame's UTM grid (``specs/19``
    section 1.1): X, Y, Z are not a plane, and a layer in them would put every
    station inside the Earth."""

    def test_the_stations_are_drawn_in_utm_on_the_solutions_frame(self, tmp_path):
        from qgis.core import QgsProcessing, QgsProcessingContext, QgsProcessingFeedback, QgsProcessingUtils

        from geocomp.core.adjustment.geocentric import ELLIPSOID
        from geocomp.core.geodesy.cartesian import cartesian_to_geodetic
        from geocomp.core.geodesy.projection import transverse_mercator, utm_parameters
        from tests.test_integration import total_station_input

        context = QgsProcessingContext()
        algorithm = _algorithm("geocomp:integration_gnss_total_station").create({})
        results, ok = algorithm.run(
            {
                "GNSS": _write(tmp_path / "gnss.json", _gnss()),
                "TOTAL_STATION": _write(tmp_path / "ts.json", total_station_input()),
                "FIXED_STATIONS": ",".join(field.HELD),
                "OUTPUT_STATION_LAYER": QgsProcessing.TEMPORARY_OUTPUT,
                "OUTPUT_ELLIPSE_LAYER": QgsProcessing.TEMPORARY_OUTPUT,
                **_outputs(tmp_path),
            },
            context,
            QgsProcessingFeedback(),
            catchExceptions=False,
        )
        assert ok
        layer = QgsProcessingUtils.mapLayerFromString(results["OUTPUT_STATION_LAYER"], context)
        assert layer.crs().description() == "ITRF2020 / UTM zone 22S"
        projection = utm_parameters(22, southern_hemisphere=True)
        for feature in layer.getFeatures():
            latitude, longitude, _ = cartesian_to_geodetic(*field.TRUTH[feature["station"]], ELLIPSOID)
            east, north = transverse_mercator(latitude, longitude, projection)
            point = feature.geometry().asPoint()
            assert math.hypot(point.x() - east, point.y() - north) < 0.05
        ellipses = QgsProcessingUtils.mapLayerFromString(results["OUTPUT_ELLIPSE_LAYER"], context)
        assert ellipses.featureCount() == layer.featureCount()
