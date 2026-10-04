# SPDX-License-Identifier: GPL-2.0-or-later
"""*Classical network* carries measured distances to the grid (FR-405, specs/09 §2.6).

The reduction itself is tested without QGIS in ``tests/test_grid_reduction.py``,
with GeoComp's own scale factor. What only QGIS can answer is checked here:
that the scale factor it supplies for the CRS is the same number, that the
algorithm applies the reduction where the coordinates are in the CRS's grid,
and that it leaves alone the coordinates that are a local plane -- RD-01's, in
EPSG:31982, which lie hundreds of kilometres outside that zone.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from tests import reference_rd01 as rd01
from tests.test_grid_reduction import utm_k

pytestmark = pytest.mark.qgis

#: RD-01's triangle moved into SIRGAS 2000 / UTM zone 22S, 200 km west of the
#: central meridian, where the scale factor is about 1.0001.
SHIFT = (300_000.0, 7_400_000.0)


def _run(algorithm_id: str, parameters: dict):
    from qgis.core import QgsApplication, QgsProcessingContext, QgsProcessingFeedback

    algorithm = QgsApplication.processingRegistry().algorithmById(algorithm_id).create({})
    feedback = QgsProcessingFeedback()
    results, ok = algorithm.run(parameters, QgsProcessingContext(), feedback, catchExceptions=False)
    assert ok, f"{algorithm_id} reported failure"
    return results


def _qgis_k(easting: float, northing: float) -> float:
    from qgis.core import (
        QgsCoordinateReferenceSystem,
        QgsCoordinateTransform,
        QgsPoint,
        QgsPointXY,
        QgsProject,
    )

    crs = QgsCoordinateReferenceSystem("EPSG:31982")
    to_geographic = QgsCoordinateTransform(crs, crs.toGeographicCrs(), QgsProject.instance())
    point = to_geographic.transform(QgsPointXY(easting, northing))
    factors = crs.factors(QgsPoint(point.x(), point.y()))
    assert factors.isValid()
    return factors.meridionalScale()


@pytest.mark.parametrize(
    "point",
    [(500_000.0, 7_400_000.0), (300_000.0, 7_400_000.0), (170_000.0, 7_000_000.0), (780_000.0, 9_900_000.0)],
)
def test_qgis_and_geocomp_agree_on_the_scale_factor(qgis_app, point):
    """Two implementations, PROJ's and GeoComp's Krüger series, of one number.

    To 0.01 ppm. They differ by about 0.005 ppm, and the difference is GeoComp's:
    :func:`~geocomp.core.geodesy.point_scale_factor` differentiates the
    projection numerically, and at the central meridian, where *k* is 0.9996 by
    definition, QGIS gives it to 4e-11 and GeoComp to 5e-9. A thousand times
    below what a distance meter resolves.
    """
    assert _qgis_k(*point) == pytest.approx(utm_k(*point), abs=1e-8)


class TestClassicalNetwork:
    @pytest.fixture(scope="class")
    def reduced(self, geocomp_provider, tmp_path_factory):
        directory = tmp_path_factory.mktemp("grid")
        imported = _run(
            "geocomp:totalstation_import_fieldbook",
            {
                "SOURCE": str(rd01.RAW),
                "SIGMA_DIRECTION": rd01.SIGMA_ANGLE,
                "SIGMA_ZENITH": rd01.SIGMA_ANGLE,
                "SIGMA_DISTANCE": 0.002,
                "OUTPUT_READINGS": str(directory / "readings.json"),
            },
        )
        preprocessed = _run(
            "geocomp:totalstation_preprocess",
            {
                "READINGS": imported["OUTPUT_READINGS"],
                "APPLY_ATMOSPHERIC": False,
                "OUTPUT_REDUCED": str(directory / "reduced.json"),
            },
        )
        return directory, preprocessed["OUTPUT_REDUCED"]

    def _adjust(self, reduced, name: str, *, shift=(0.0, 0.0), **extra):
        directory, observations = reduced
        approximate = directory / f"{name}-approximate.json"
        approximate.write_text(
            json.dumps(
                {
                    station: [e + shift[0], n + shift[1], u]
                    for station, (e, n, u) in rd01.approximate_coordinates().items()
                }
            ),
            encoding="utf-8",
        )
        results = _run(
            "geocomp:totalstation_network",
            {
                "REDUCTIONS": observations,
                "APPROXIMATE": str(approximate),
                "DIMENSION": 0,
                "DATUM": 1,
                "CRS": "EPSG:31982",
                "OUTPUT_NETWORK": str(directory / f"{name}-network.json"),
                "OUTPUT_SOLUTION": str(directory / f"{name}-solution.json"),
                "OUTPUT_HTML": str(directory / f"{name}.html"),
                **extra,
            },
        )
        solution = json.loads(Path(results["OUTPUT_SOLUTION"]).read_text(encoding="utf-8"))
        network = json.loads(Path(results["OUTPUT_NETWORK"]).read_text(encoding="utf-8"))
        report = Path(results["OUTPUT_HTML"]).read_text(encoding="utf-8")
        return solution, network, report

    @staticmethod
    def _recorded(solution) -> dict:
        return solution["provenance"]["parameters"]["grid_reduction"]

    @staticmethod
    def _length(solution, a: str, b: str) -> float:
        from geocomp.core.models import Solution

        stations = {s.station_id: s.position.values for s in Solution.from_dict(solution).adjusted_stations}
        (ea, na, _), (eb, nb, _) = stations[a], stations[b]
        return math.hypot(eb.value - ea.value, nb.value - na.value)

    def test_rd01_where_it_is_given_is_a_local_plane(self, reduced):
        """(0, 0) in UTM 22S is nowhere near Brazil: read as a local plane, not reduced."""
        solution, network, report = self._adjust(reduced, "local")
        assert self._recorded(solution) == {"applied": False, "reason": "outside_area"}
        assert not any("grid_reduction" in (o.get("meta") or {}) for o in network["observations"])
        assert "local plane" in report

    def test_in_the_zone_its_distances_are_reduced(self, reduced):
        plain, _network, _report = self._adjust(
            reduced, "plain", shift=SHIFT, REDUCE_TO_GRID=False
        )
        grid, network, report = self._adjust(reduced, "grid", shift=SHIFT)

        recorded = self._recorded(grid)
        assert recorded["applied"] is True
        from geocomp.core.models import ObservationType

        horizontal = [
            o
            for o in network["observations"]
            if o["type"] == ObservationType.HORIZONTAL_DISTANCE.name
        ]
        assert recorded["distances"] == len(horizontal) == 5
        k = _qgis_k(SHIFT[0], SHIFT[1])
        low, high = recorded["ppm"]
        assert low == pytest.approx((k - 1.0) * 1e6, abs=0.1)
        assert high == pytest.approx((k - 1.0) * 1e6, abs=0.1)
        # The heights are zero and N is zero, so the whole factor is k, and the
        # adjusted triangle is the measured one scaled by it.
        assert self._length(grid, "1", "2") / self._length(plain, "1", "2") == pytest.approx(
            k, rel=1e-8
        )
        assert all("grid_reduction" in (o.get("meta") or {}) for o in horizontal)
        assert "Distances reduced to the grid" in report

    def test_turned_off_it_says_so(self, reduced):
        solution, _network, _report = self._adjust(
            reduced, "off", shift=SHIFT, REDUCE_TO_GRID=False
        )
        assert self._recorded(solution) == {"applied": False, "reason": "not_asked"}

    def test_the_undulation_reaches_the_reduction(self, reduced):
        """N = 100 m is 15.7 ppm off the distances, and the record says so."""
        solution, _network, _report = self._adjust(
            reduced, "undulation", shift=SHIFT, GEOID_UNDULATION=100.0
        )
        recorded = self._recorded(solution)
        k = _qgis_k(SHIFT[0], SHIFT[1])
        expected = (k * 6_371_000.0 / (6_371_000.0 + 100.0) - 1.0) * 1e6
        assert recorded["geoid_undulation"] == 100.0
        assert recorded["ppm"][0] == pytest.approx(expected, abs=0.1)
