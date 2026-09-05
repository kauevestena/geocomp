# SPDX-License-Identifier: GPL-2.0-or-later
"""The three P2 algorithms, run end to end in a real QGIS (FR-033).

Phase P2's mathematics is tested exhaustively without QGIS. What cannot be
tested there is the part that only exists inside QGIS: that the algorithms
register, that their parameters are declared in a way Processing accepts, and
that ``processAlgorithm`` runs to completion and produces the files and scalar
outputs a model would consume.

These are the checks the plan for P2 listed as *CI-pending* rather than
confirmed, so they are written as tests rather than reported as verified.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from geocomp.registry import ALGORITHMS
from tests.networks import trilateration

pytestmark = pytest.mark.qgis

ANALYSIS_IDS = (
    "geocomp:analysis_network_inspect",
    "geocomp:analysis_network_preanalysis",
    "geocomp:analysis_network_adjust",
)


@pytest.fixture(scope="module")
def network_document(tmp_path_factory) -> str:
    """RD-03's trilateration network, written as the JSON an algorithm reads."""
    path = tmp_path_factory.mktemp("networks") / "trilateration.json"
    path.write_text(json.dumps(trilateration().network.to_dict()), encoding="utf-8")
    return str(path)


def _algorithm(algorithm_id: str):
    from qgis.core import QgsApplication

    algorithm = QgsApplication.processingRegistry().algorithmById(algorithm_id)
    assert algorithm is not None, f"{algorithm_id} is not registered"
    return algorithm


def _run(algorithm_id: str, parameters: dict):
    """Run an algorithm and fail loudly rather than returning a partial result.

    ``catchExceptions=False`` on purpose: a swallowed exception here would show
    up as a missing output file three assertions later, and the traceback is
    what makes the failure diagnosable.
    """
    from qgis.core import QgsProcessingContext, QgsProcessingFeedback

    algorithm = _algorithm(algorithm_id).create({})
    context = QgsProcessingContext()
    feedback = QgsProcessingFeedback()
    results, ok = algorithm.run(parameters, context, feedback, catchExceptions=False)
    assert ok, f"{algorithm_id} reported failure"
    return results


class TestRegistration:
    def test_every_declared_algorithm_registers(self, geocomp_provider):
        """The registry is the single declaration; this is the other end of it."""
        from qgis.core import QgsApplication

        registered = {
            algorithm.id()
            for algorithm in QgsApplication.processingRegistry().algorithms()
            if algorithm.provider().id() == "geocomp"
        }
        assert registered == {spec.id for spec in ALGORITHMS}

    @pytest.mark.parametrize("algorithm_id", ANALYSIS_IDS)
    def test_each_analysis_algorithm_is_in_the_analysis_group(
        self, geocomp_provider, algorithm_id
    ):
        assert _algorithm(algorithm_id).groupId() == "analysis"

    @pytest.mark.parametrize("algorithm_id", ANALYSIS_IDS)
    def test_each_algorithm_documents_itself(self, geocomp_provider, algorithm_id):
        """FR-090 and specs/16 section 8: help text, and a name that is not the id."""
        algorithm = _algorithm(algorithm_id)
        assert algorithm.displayName()
        assert algorithm.displayName() != algorithm.name()
        assert len(algorithm.shortHelpString()) > 200
        assert algorithm.shortDescription()

    @pytest.mark.parametrize("algorithm_id", ANALYSIS_IDS)
    def test_every_parameter_is_described(self, geocomp_provider, algorithm_id):
        """A parameter whose description is its own name tells the user nothing."""
        for parameter in _algorithm(algorithm_id).parameterDefinitions():
            assert parameter.description(), f"{algorithm_id}: {parameter.name()} has no description"
            assert parameter.description() != parameter.name()


class TestInspect:
    def test_a_sound_network_reports_that_it_can_be_adjusted(
        self, geocomp_provider, network_document, tmp_path
    ):
        results = _run(
            "geocomp:analysis_network_inspect",
            {
                "NETWORK": network_document,
                "FRAME": 0,
                "OUTPUT_HTML": str(tmp_path / "inspect.html"),
                "OUTPUT_CSV": str(tmp_path / "findings.csv"),
            },
        )
        assert results["CAN_ADJUST"] is True
        assert results["BLOCKING_COUNT"] == 0
        assert results["COMPONENT_COUNT"] == 1

        report = Path(results["OUTPUT_HTML"]).read_text(encoding="utf-8")
        assert report.startswith("<!doctype html>")
        assert "</html>" in report

        with open(results["OUTPUT_CSV"], encoding="utf-8") as handle:
            rows = list(csv.reader(handle))
        assert rows[0] == ["code", "severity", "message", "stations", "observations"]

    def test_a_disconnected_network_is_blocked_and_named(
        self, geocomp_provider, tmp_path
    ):
        """The finding a user most needs: two halves that share no observation."""
        reference = trilateration()
        payload = reference.network.to_dict()
        payload["observations"] = [
            o for o in payload["observations"] if "E" not in o["stations"]
        ]
        document = tmp_path / "split.json"
        document.write_text(json.dumps(payload), encoding="utf-8")

        results = _run(
            "geocomp:analysis_network_inspect",
            {
                "NETWORK": str(document),
                "FRAME": 0,
                "OUTPUT_HTML": str(tmp_path / "split.html"),
            },
        )
        assert results["CAN_ADJUST"] is False
        assert results["BLOCKING_COUNT"] >= 1

    def test_failing_on_blocking_is_opt_in(self, geocomp_provider, tmp_path):
        """A model that chains inspect into adjust needs the run to stop; an
        interactive check needs it to report and succeed."""
        from qgis.core import QgsProcessingContext, QgsProcessingException, QgsProcessingFeedback

        payload = trilateration().network.to_dict()
        payload["observations"] = []
        document = tmp_path / "empty.json"
        document.write_text(json.dumps(payload), encoding="utf-8")

        parameters = {
            "NETWORK": str(document),
            "FRAME": 0,
            "FAIL_ON_BLOCKING": True,
            "OUTPUT_HTML": str(tmp_path / "empty.html"),
        }
        algorithm = _algorithm("geocomp:analysis_network_inspect").create({})
        with pytest.raises(QgsProcessingException):
            algorithm.run(
                parameters,
                QgsProcessingContext(),
                QgsProcessingFeedback(),
                catchExceptions=False,
            )


class TestPreAnalysis:
    def test_a_design_reports_precision_and_reliability(
        self, geocomp_provider, network_document, tmp_path
    ):
        results = _run(
            "geocomp:analysis_network_preanalysis",
            {
                "NETWORK": network_document,
                "FRAME": 0,
                "DATUM": 0,
                "TOLERANCE": 0.0,
                "OUTPUT_HTML": str(tmp_path / "design.html"),
                "OUTPUT_CSV": str(tmp_path / "design.csv"),
            },
        )
        assert results["DEGREES_OF_FREEDOM"] > 0
        assert results["WORST_STATION"]
        assert results["WORST_UNCERTAINTY"] > 0.0

        with open(results["OUTPUT_CSV"], encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        assert rows
        assert all(float(row["positional_uncertainty"]) > 0.0 for row in rows)

    def test_a_tolerance_is_judged_rather_than_reported(
        self, geocomp_provider, network_document, tmp_path
    ):
        """A tolerance no design could meet must fail it, and one every design
        meets must pass -- otherwise the parameter is decorative."""
        impossible = _run(
            "geocomp:analysis_network_preanalysis",
            {"NETWORK": network_document, "FRAME": 0, "DATUM": 0, "TOLERANCE": 1e-6,
             "OUTPUT_HTML": str(tmp_path / "tight.html")},
        )
        generous = _run(
            "geocomp:analysis_network_preanalysis",
            {"NETWORK": network_document, "FRAME": 0, "DATUM": 0, "TOLERANCE": 100.0,
             "OUTPUT_HTML": str(tmp_path / "loose.html")},
        )
        assert impossible["MEETS_TOLERANCE"] is False
        assert generous["MEETS_TOLERANCE"] is True


class TestAdjust:
    def test_the_adjustment_runs_and_writes_a_readable_solution(
        self, geocomp_provider, network_document, tmp_path
    ):
        results = _run(
            "geocomp:analysis_network_adjust",
            {
                "NETWORK": network_document,
                "FRAME": 0,
                "DATUM": 0,
                "OUTPUT_SOLUTION": str(tmp_path / "solution.json"),
                "OUTPUT_HTML": str(tmp_path / "adjust.html"),
                "OUTPUT_STATIONS_CSV": str(tmp_path / "stations.csv"),
                "OUTPUT_RESIDUALS_CSV": str(tmp_path / "residuals.csv"),
            },
        )

        assert results["ITERATIONS"] >= 1
        assert results["DEGREES_OF_FREEDOM"] > 0
        assert results["VARIANCE_FACTOR_APOSTERIORI"] > 0.0

        from geocomp.core.models import Solution

        payload = json.loads(Path(results["OUTPUT_SOLUTION"]).read_text(encoding="utf-8"))
        solution = Solution.from_dict(payload)
        assert solution.adjusted_stations
        assert solution.observation_results
        assert solution.provenance is not None
        assert solution.provenance.algorithm_id == "geocomp:analysis_network_adjust"
        assert all(station.ellipse is not None for station in solution.adjusted_stations)

        with open(results["OUTPUT_STATIONS_CSV"], encoding="utf-8") as handle:
            stations = list(csv.DictReader(handle))
        assert {row["station"] for row in stations} == {
            station.station_id for station in solution.adjusted_stations
        }

        with open(results["OUTPUT_RESIDUALS_CSV"], encoding="utf-8") as handle:
            residuals = list(csv.DictReader(handle))
        assert len(residuals) == len(solution.observation_results)

    def test_a_blunder_is_reported_as_a_candidate_and_not_removed(
        self, geocomp_provider, tmp_path
    ):
        """FR-255 through the algorithm boundary: the observation is flagged,
        and it is still in the solution's results afterwards."""
        reference = trilateration(blunder=0.5, blunder_on="d4")
        document = tmp_path / "blundered.json"
        document.write_text(json.dumps(reference.network.to_dict()), encoding="utf-8")

        results = _run(
            "geocomp:analysis_network_adjust",
            {
                "NETWORK": str(document),
                "FRAME": 0,
                "DATUM": 0,
                "OUTPUT_SOLUTION": str(tmp_path / "blundered.json.solution"),
                "OUTPUT_HTML": str(tmp_path / "blundered.html"),
            },
        )
        assert results["OUTLIER_COUNT"] >= 1
        assert results["WORST_OUTLIER"] == "d4"

        from geocomp.core.models import Solution

        solution = Solution.from_dict(
            json.loads(Path(results["OUTPUT_SOLUTION"]).read_text(encoding="utf-8"))
        )
        assert "d4" in {result.observation_id for result in solution.observation_results}

    def test_a_missing_network_document_fails_with_a_message_naming_it(
        self, geocomp_provider, tmp_path
    ):
        """FR-035: the failure must name the offending input."""
        from qgis.core import QgsProcessingContext, QgsProcessingException, QgsProcessingFeedback

        algorithm = _algorithm("geocomp:analysis_network_adjust").create({})
        with pytest.raises(QgsProcessingException) as caught:
            algorithm.run(
                {"NETWORK": str(tmp_path / "nope.json"), "FRAME": 0, "DATUM": 0},
                QgsProcessingContext(),
                QgsProcessingFeedback(),
                catchExceptions=False,
            )
        assert "nope.json" in str(caught.value)

    def test_basic_and_advanced_defaults_give_identical_numbers(
        self, geocomp_provider, network_document, tmp_path
    ):
        """FR-071. Every advanced parameter is omitted in one run and passed at
        its own default in the other; gating must change what is shown, never
        what is computed."""
        from qgis.core import QgsProcessingParameterDefinition

        algorithm = _algorithm("geocomp:analysis_network_adjust")
        advanced_flag = QgsProcessingParameterDefinition.Flag.FlagAdvanced
        advanced = {
            parameter.name(): parameter.defaultValue()
            for parameter in algorithm.parameterDefinitions()
            if parameter.flags() & advanced_flag
        }
        assert advanced, "the algorithm declares no advanced parameters"

        basic_run = _run(
            "geocomp:analysis_network_adjust",
            {"NETWORK": network_document, "FRAME": 0, "DATUM": 0,
             "OUTPUT_HTML": str(tmp_path / "basic.html")},
        )
        advanced_run = _run(
            "geocomp:analysis_network_adjust",
            {"NETWORK": network_document, "FRAME": 0, "DATUM": 0,
             "OUTPUT_HTML": str(tmp_path / "advanced.html"), **advanced},
        )

        for key in ("VARIANCE_FACTOR_APOSTERIORI", "DEGREES_OF_FREEDOM", "ITERATIONS",
                    "OUTLIER_COUNT", "WORST_OUTLIER"):
            assert basic_run[key] == advanced_run[key], key
