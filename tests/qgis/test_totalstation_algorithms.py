# SPDX-License-Identifier: GPL-2.0-or-later
"""The total-station chain, run end to end in a real QGIS.

``specs/ROADMAP.md`` states phase P3's goal as a user opening QGIS, picking Total
Station from the GeoComp menu, importing field data, and getting an adjusted,
statistically validated network -- **with no external engine installed**. These
tests run exactly that, on RD-01, through the Processing framework.

The mathematics is tested exhaustively without QGIS. What only exists inside
QGIS is that the algorithms register, that their parameters are declared in a
way Processing accepts, and that the three chain together with each one's output
being the next one's input (FR-033).
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from tests import reference_rd01 as rd01

pytestmark = pytest.mark.qgis

TOTAL_STATION_IDS = (
    "geocomp:totalstation_import_fieldbook",
    "geocomp:totalstation_preprocess",
    "geocomp:totalstation_network",
)


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


class TestRegistration:
    @pytest.mark.parametrize("algorithm_id", TOTAL_STATION_IDS)
    def test_each_is_in_the_total_station_group(self, geocomp_provider, algorithm_id):
        assert _algorithm(algorithm_id).groupId() == "totalstation"

    @pytest.mark.parametrize("algorithm_id", TOTAL_STATION_IDS)
    def test_each_documents_itself(self, geocomp_provider, algorithm_id):
        algorithm = _algorithm(algorithm_id)
        assert algorithm.displayName() and algorithm.displayName() != algorithm.name()
        assert len(algorithm.shortHelpString()) > 200
        assert algorithm.shortDescription()

    @pytest.mark.parametrize("algorithm_id", TOTAL_STATION_IDS)
    def test_every_parameter_is_described(self, geocomp_provider, algorithm_id):
        for parameter in _algorithm(algorithm_id).parameterDefinitions():
            assert parameter.description(), f"{algorithm_id}: {parameter.name()}"
            assert parameter.description() != parameter.name()

    def test_the_total_station_submenu_is_no_longer_empty(self, geocomp_provider):
        """P0 left the technique submenus present but disabled. This is the
        phase that fills the first one."""
        from geocomp.registry import algorithms_in_menu

        assert len(algorithms_in_menu("total_station")) == 3


class TestTheWholeChain:
    """Import, pre-process, adjust -- each step's output feeding the next."""

    @pytest.fixture(scope="class")
    def imported(self, geocomp_provider, tmp_path_factory):
        directory = tmp_path_factory.mktemp("rd01")
        return directory, _run(
            "geocomp:totalstation_import_fieldbook",
            {
                "SOURCE": str(rd01.RAW),
                "SIGMA_DIRECTION": rd01.SIGMA_ANGLE,
                "SIGMA_ZENITH": rd01.SIGMA_ANGLE,
                "SIGMA_DISTANCE": 0.002,
                "OUTPUT_READINGS": str(directory / "readings.json"),
                "OUTPUT_HTML": str(directory / "import.html"),
                "OUTPUT_FINDINGS": str(directory / "findings.csv"),
            },
        )

    def test_the_import_reads_every_row(self, imported):
        _directory, results = imported
        assert results["RECORD_COUNT"] == 12
        assert results["SETUP_COUNT"] == 3
        assert results["REJECTED_COUNT"] == 0

    def test_the_import_writes_a_readable_report_and_findings_table(self, imported):
        _directory, results = imported
        report = Path(results["OUTPUT_HTML"]).read_text(encoding="utf-8")
        assert report.startswith("<!doctype html>")
        with open(results["OUTPUT_FINDINGS"], encoding="utf-8") as handle:
            assert next(csv.reader(handle)) == ["code", "severity", "message", "row"]

    @pytest.fixture(scope="class")
    def reduced(self, imported):
        directory, results = imported
        return directory, _run(
            "geocomp:totalstation_preprocess",
            {
                "READINGS": results["OUTPUT_READINGS"],
                "APPLY_ATMOSPHERIC": False,
                "OUTPUT_REDUCED": str(directory / "reduced.json"),
                "OUTPUT_HTML": str(directory / "preprocess.html"),
                "OUTPUT_CSV": str(directory / "reduced.csv"),
            },
        )

    def test_pre_processing_reduces_every_pointing(self, reduced):
        _directory, results = reduced
        assert results["POINTING_COUNT"] == 6

    def test_it_catches_rd01_s_face_distance_blunder(self, reduced):
        """The acceptance criterion, through the Processing boundary: one
        pointing is blocked and the other five come through."""
        _directory, results = reduced
        assert results["BLOCKING_COUNT"] == 1
        assert results["USABLE_COUNT"] == 5

    def test_the_reduction_table_marks_the_unusable_pointing(self, reduced):
        _directory, results = reduced
        with open(results["OUTPUT_CSV"], encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        assert len(rows) == 6
        assert sum(1 for row in rows if row["usable"] == "no") == 1

    @pytest.fixture(scope="class")
    def adjusted(self, reduced):
        directory, results = reduced
        approximate = directory / "approximate.json"
        approximate.write_text(
            json.dumps(rd01.approximate_coordinates()), encoding="utf-8"
        )
        return directory, _run(
            "geocomp:totalstation_network",
            {
                "REDUCTIONS": results["OUTPUT_REDUCED"],
                "APPROXIMATE": str(approximate),
                "DIMENSION": 0,
                "DATUM": 1,
                "CRS": "EPSG:31982",
                "OUTPUT_NETWORK": str(directory / "network.json"),
                "OUTPUT_SOLUTION": str(directory / "solution.json"),
                "OUTPUT_HTML": str(directory / "network.html"),
                "OUTPUT_STATIONS": str(directory / "stations.csv"),
            },
        )

    def test_the_network_adjusts(self, adjusted):
        _directory, results = adjusted
        assert results["DEGREES_OF_FREEDOM"] == 4
        assert results["VARIANCE_FACTOR"] > 0.0

    def test_the_global_test_fails_which_is_the_right_answer_for_rd01(self, adjusted):
        """RD-01's distances disagree between stations by about 15 mm against an
        assumed 2 mm. A global test that passed would not be testing anything."""
        _directory, results = adjusted
        assert results["GLOBAL_TEST_PASSED"] is False

    def test_the_solution_reads_back_and_carries_its_provenance(self, adjusted):
        from geocomp.core.models import Solution

        _directory, results = adjusted
        payload = json.loads(Path(results["OUTPUT_SOLUTION"]).read_text(encoding="utf-8"))
        solution = Solution.from_dict(payload)
        assert len(solution.adjusted_stations) == 3
        assert solution.provenance is not None
        assert solution.provenance.algorithm_id == "geocomp:totalstation_network"
        assert all(station.ellipse is not None for station in solution.adjusted_stations)

    def test_the_network_document_feeds_the_analysis_algorithms(self, adjusted):
        """FR-033 and specs/16 section 9: the chain must be assemblable across
        groups, not only within one."""
        directory, results = adjusted
        inspection = _run(
            "geocomp:analysis_network_inspect",
            {
                "NETWORK": results["OUTPUT_NETWORK"],
                "FRAME": 0,
                "OUTPUT_HTML": str(directory / "inspect.html"),
            },
        )
        assert inspection["CAN_ADJUST"] is True
        assert inspection["COMPONENT_COUNT"] == 1

    def test_the_stations_csv_matches_the_solution(self, adjusted):
        from geocomp.core.models import Solution

        _directory, results = adjusted
        solution = Solution.from_dict(
            json.loads(Path(results["OUTPUT_SOLUTION"]).read_text(encoding="utf-8"))
        )
        with open(results["OUTPUT_STATIONS"], encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        assert {row["station"] for row in rows} == {
            station.station_id for station in solution.adjusted_stations
        }


class TestFailuresAreActionable:
    def test_a_readings_document_is_refused_where_reductions_are_expected(
        self, geocomp_provider, tmp_path
    ):
        """FR-035: the message must say which input was wrong and what to do."""
        from qgis.core import (
            QgsProcessingContext,
            QgsProcessingException,
            QgsProcessingFeedback,
        )

        wrong = tmp_path / "readings.json"
        wrong.write_text(json.dumps({"kind": "geocomp.readings", "setups": []}), encoding="utf-8")
        approximate = tmp_path / "approx.json"
        approximate.write_text(json.dumps(rd01.approximate_coordinates()), encoding="utf-8")

        algorithm = _algorithm("geocomp:totalstation_network").create({})
        with pytest.raises(QgsProcessingException) as caught:
            algorithm.run(
                {"REDUCTIONS": str(wrong), "APPROXIMATE": str(approximate)},
                QgsProcessingContext(),
                QgsProcessingFeedback(),
                catchExceptions=False,
            )
        assert "pre-processing" in str(caught.value).lower()

    def test_a_field_book_with_no_stochastic_model_refuses_by_name(
        self, geocomp_provider, tmp_path
    ):
        """GeoComp does not invent a sigma, and the boundary is where that has
        to hold."""
        from qgis.core import (
            QgsProcessingContext,
            QgsProcessingException,
            QgsProcessingFeedback,
        )

        library = tmp_path / "empty.json"
        library.write_text(json.dumps({"instruments": [], "reflectors": []}), encoding="utf-8")

        algorithm = _algorithm("geocomp:totalstation_import_fieldbook").create({})
        with pytest.raises(QgsProcessingException):
            algorithm.run(
                {"SOURCE": str(rd01.RAW), "PROFILES": str(library)},
                QgsProcessingContext(),
                QgsProcessingFeedback(),
                catchExceptions=False,
            )
