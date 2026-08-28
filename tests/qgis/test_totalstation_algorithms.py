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
import math
from pathlib import Path

import pytest

from tests import reference_rd01 as rd01
from tests import synthetic as syn

pytestmark = pytest.mark.qgis

TOTAL_STATION_IDS = (
    "geocomp:totalstation_import_fieldbook",
    "geocomp:totalstation_preprocess",
    "geocomp:totalstation_traverse",
    "geocomp:totalstation_resection",
    "geocomp:totalstation_intersection",
    "geocomp:totalstation_network",
    "geocomp:totalstation_trig_levelling",
    "geocomp:totalstation_radiation",
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

    def test_the_total_station_submenu_holds_every_algorithm(self, geocomp_provider):
        """P0 left the technique submenus present but disabled. This is the
        phase that fills the first one, and the menu is the only place the
        count can drift from the registry unnoticed."""
        from geocomp.registry import algorithms_in_menu

        entries = algorithms_in_menu("total_station")
        assert len(entries) == len(TOTAL_STATION_IDS)
        assert {entry.id for entry in entries} == set(TOTAL_STATION_IDS)


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
        approximate.write_text(json.dumps(rd01.approximate_coordinates()), encoding="utf-8")
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
        wrong.write_text(
            json.dumps({"kind": "geocomp.readings", "setups": []}), encoding="utf-8"
        )
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


class TestTheSyntheticSurvey:
    """Traverse, resection, intersection, radiation and trigonometric levelling.

    RD-01 cannot check any of these: it has no known point, so there is nothing
    to traverse between, resect from or radiate off. ``tests/synthetic.py``
    generates the readings a total station would have recorded standing at
    coordinates chosen in advance, and ``tests/test_synthetic_survey.py``
    verifies that fixture against the core routines without QGIS. What is left
    for these tests is the Processing boundary: parameters in, documents out,
    and the geometry surviving the round trip through JSON.
    """

    @pytest.fixture(scope="class")
    def workspace(self, geocomp_provider, tmp_path_factory):
        directory = tmp_path_factory.mktemp("synthetic")
        reductions = directory / "reductions.json"
        reductions.write_text(json.dumps(syn.reductions_document()), encoding="utf-8")
        known = directory / "known.json"
        known.write_text(json.dumps(syn.known_points()), encoding="utf-8")
        return directory, reductions, known

    # -- traverse --------------------------------------------------------

    @pytest.fixture(scope="class")
    def traverse(self, workspace):
        directory, reductions, _known = workspace
        return _run(
            "geocomp:totalstation_traverse",
            {
                "REDUCTIONS": str(reductions),
                "ROUTE": ",".join(syn.ROUTE),
                "BACKSIGHT": syn.BACKSIGHT,
                "START_EASTING": syn.COORDINATES["A"][0],
                "START_NORTHING": syn.COORDINATES["A"][1],
                "START_AZIMUTH": math.degrees(syn.start_azimuth()),
                "CLOSE_AZIMUTH": math.degrees(syn.azimuth("D", "A")),
                "KIND": 0,
                "METHOD": 0,
                "OUTPUT_COORDINATES": str(directory / "traverse.json"),
                "OUTPUT_HTML": str(directory / "traverse.html"),
                "OUTPUT_CSV": str(directory / "traverse.csv"),
            },
        )

    def test_the_loop_closes_on_itself(self, traverse):
        assert abs(traverse["ANGULAR_MISCLOSURE"]) < 1.0e-9
        assert traverse["LINEAR_MISCLOSURE"] < 1.0e-6
        assert traverse["WITHIN_TOLERANCE"] is True

    def test_an_exact_closure_is_not_reported_as_the_worst_possible_one(self, traverse):
        """The relative precision is a ratio the misclosure divides into, so an
        exact closure has none. Reporting zero there would read as 1:0."""
        assert traverse["RELATIVE_PRECISION"] > 1.0e6

    def test_every_station_comes_back_where_it_was_generated(self, traverse):
        coordinates = json.loads(
            Path(traverse["OUTPUT_COORDINATES"]).read_text(encoding="utf-8")
        )
        for name in ("B", "C", "D"):
            easting, northing, _up = coordinates[name]
            assert easting == pytest.approx(syn.COORDINATES[name][0], abs=1e-5)
            assert northing == pytest.approx(syn.COORDINATES[name][1], abs=1e-5)

    def test_the_stations_table_carries_a_row_per_station(self, traverse):
        with open(traverse["OUTPUT_CSV"], encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        assert {row["station"] for row in rows} >= {"B", "C", "D"}

    def test_a_loop_left_without_a_closing_azimuth_infers_it(self, workspace):
        """A blank closing azimuth used to fall through to zero, which turned an
        untouched field into a misclosure of several hundred degrees. A loop
        that backsights the station it returns from closes on the line its start
        azimuth refers to, and that is what gets used."""
        directory, reductions, _known = workspace
        results = _run(
            "geocomp:totalstation_traverse",
            {
                "REDUCTIONS": str(reductions),
                "ROUTE": ",".join(syn.ROUTE),
                "BACKSIGHT": syn.BACKSIGHT,
                "START_EASTING": syn.COORDINATES["A"][0],
                "START_NORTHING": syn.COORDINATES["A"][1],
                "START_AZIMUTH": math.degrees(syn.start_azimuth()),
                "KIND": 0,
                "METHOD": 0,
                "OUTPUT_COORDINATES": str(directory / "inferred.json"),
            },
        )
        assert abs(results["ANGULAR_MISCLOSURE"]) < 1.0e-9
        assert results["WITHIN_TOLERANCE"] is True

    def test_a_route_through_a_station_that_was_not_occupied_is_refused_by_name(
        self, workspace
    ):
        from qgis.core import (
            QgsProcessingContext,
            QgsProcessingException,
            QgsProcessingFeedback,
        )

        _directory, reductions, _known = workspace
        algorithm = _algorithm("geocomp:totalstation_traverse").create({})
        with pytest.raises(QgsProcessingException) as caught:
            algorithm.run(
                {
                    "REDUCTIONS": str(reductions),
                    "ROUTE": "A,B,Z,A",
                    "BACKSIGHT": "D",
                },
                QgsProcessingContext(),
                QgsProcessingFeedback(),
                catchExceptions=False,
            )
        assert "Z" in str(caught.value)

    # -- resection -------------------------------------------------------

    def test_the_resection_recovers_the_occupied_station(self, workspace):
        directory, reductions, known = workspace
        results = _run(
            "geocomp:totalstation_resection",
            {
                "REDUCTIONS": str(reductions),
                "STATION": "R",
                "KNOWN": str(known),
                "OUTPUT_POSITION": str(directory / "resection.json"),
                "OUTPUT_HTML": str(directory / "resection.html"),
            },
        )
        assert results["EASTING"] == pytest.approx(syn.COORDINATES["R"][0], abs=1e-5)
        assert results["NORTHING"] == pytest.approx(syn.COORDINATES["R"][1], abs=1e-5)
        assert results["ORIENTATION"] % 360.0 == pytest.approx(
            math.degrees(syn.ORIENTATIONS["R"]) % 360.0, abs=1e-6
        )

    def test_the_resected_position_is_written_as_approximate_coordinates(self, workspace):
        """The document has to be the shape Classical network takes as its
        starting values, or the chain stops here (FR-033)."""
        directory, reductions, known = workspace
        results = _run(
            "geocomp:totalstation_resection",
            {
                "REDUCTIONS": str(reductions),
                "STATION": "R",
                "KNOWN": str(known),
                "OUTPUT_POSITION": str(directory / "resection-chain.json"),
            },
        )
        payload = json.loads(Path(results["OUTPUT_POSITION"]).read_text(encoding="utf-8"))
        assert list(payload) == ["R"]
        assert len(payload["R"]) == 3

    def test_a_station_sighting_too_few_known_points_is_refused(self, workspace):
        """Two directions cannot fix a position and an orientation. Station L
        sighted exactly two."""
        from qgis.core import (
            QgsProcessingContext,
            QgsProcessingException,
            QgsProcessingFeedback,
        )

        _directory, reductions, known = workspace
        algorithm = _algorithm("geocomp:totalstation_resection").create({})
        with pytest.raises(QgsProcessingException) as caught:
            algorithm.run(
                {"REDUCTIONS": str(reductions), "STATION": "L", "KNOWN": str(known)},
                QgsProcessingContext(),
                QgsProcessingFeedback(),
                catchExceptions=False,
            )
        assert "three" in str(caught.value).lower()

    # -- intersection ----------------------------------------------------

    def test_the_intersection_recovers_a_point_nobody_occupied(self, workspace):
        directory, _reductions, _known = workspace
        sightings = directory / "sightings.json"
        sightings.write_text(
            json.dumps(syn.sightings_document("P1", ("A", "C"))), encoding="utf-8"
        )
        results = _run(
            "geocomp:totalstation_intersection",
            {
                "SIGHTINGS": str(sightings),
                "TARGET": "P1",
                "OUTPUT_POSITION": str(directory / "intersection.json"),
                "OUTPUT_HTML": str(directory / "intersection.html"),
            },
        )
        assert results["EASTING"] == pytest.approx(syn.COORDINATES["P1"][0], abs=1e-4)
        assert results["NORTHING"] == pytest.approx(syn.COORDINATES["P1"][1], abs=1e-4)
        assert results["SEMI_MAJOR"] >= results["SEMI_MINOR"]
        assert results["WEAK_GEOMETRY"] is False

    def test_one_sighting_is_refused_rather_than_extrapolated(self, workspace):
        from qgis.core import (
            QgsProcessingContext,
            QgsProcessingException,
            QgsProcessingFeedback,
        )

        directory, _reductions, _known = workspace
        lonely = directory / "one-sighting.json"
        lonely.write_text(json.dumps(syn.sightings_document("P1", ("A",))), encoding="utf-8")
        algorithm = _algorithm("geocomp:totalstation_intersection").create({})
        with pytest.raises(QgsProcessingException):
            algorithm.run(
                {"SIGHTINGS": str(lonely), "TARGET": "P1"},
                QgsProcessingContext(),
                QgsProcessingFeedback(),
                catchExceptions=False,
            )

    # -- radiation -------------------------------------------------------

    @pytest.fixture(scope="class")
    def radiated(self, workspace):
        directory, reductions, known = workspace
        return directory, _run(
            "geocomp:totalstation_radiation",
            {
                "REDUCTIONS": str(reductions),
                "STATIONS": str(known),
                "INSTRUMENT_HEIGHT": syn.INSTRUMENT_HEIGHT,
                "TARGET_HEIGHT": syn.TARGET_HEIGHT,
                "CORRELATION": 0.0,
                "OUTPUT_POINTS": str(directory / "points.json"),
                "OUTPUT_HTML": str(directory / "radiation.html"),
                "OUTPUT_CSV": str(directory / "points.csv"),
            },
        )

    def test_only_the_points_that_are_not_already_known_are_radiated(self, radiated):
        """Setup A sighted two control stations and two detail points. Radiating
        the control stations back would be busywork that also looks like new
        information."""
        _directory, results = radiated
        assert results["POINT_COUNT"] == 2

    def test_each_detail_point_lands_where_it_was_generated(self, radiated):
        _directory, results = radiated
        points = json.loads(Path(results["OUTPUT_POINTS"]).read_text(encoding="utf-8"))
        assert set(points) == {"P1", "P2"}
        for name, values in points.items():
            for value, expected in zip(values, syn.COORDINATES[name], strict=True):
                assert value == pytest.approx(expected, abs=1e-5)

    def test_the_orientation_is_derived_from_the_known_points(self, radiated):
        """No orientations document was given. The setup sighted two stations
        whose coordinates are known, and that is enough to orient it -- which is
        what a detail survey actually does. The proof is that the radiated
        points land correctly, so what is checked here is that the report says
        where the orientation came from and how well its sources agreed."""
        _directory, results = radiated
        report = Path(results["OUTPUT_HTML"]).read_text(encoding="utf-8")
        assert "from known points" in report
        assert "0.0" in report

    def test_control_that_disagrees_with_itself_is_reported(self, workspace):
        """Two known points that imply different orientations disagree about
        where they are, and every point radiated from the setup carries that.
        With only two sources the spread is the whole disagreement -- computed
        as a range of signed deviations, because a range of absolute ones is
        identically zero for a pair and would report perfect agreement exactly
        when there is none."""
        from qgis.core import QgsProcessingContext, QgsProcessingFeedback

        directory, reductions, _known = workspace
        moved = dict(syn.known_points())
        moved["B"] = [moved["B"][0] + 0.500, moved["B"][1], moved["B"][2]]
        displaced = directory / "displaced.json"
        displaced.write_text(json.dumps(moved), encoding="utf-8")

        warnings: list[str] = []

        class Listening(QgsProcessingFeedback):
            def pushWarning(self, message):  # noqa: N802 - Qt naming
                warnings.append(message)

        algorithm = _algorithm("geocomp:totalstation_radiation").create({})
        results, ok = algorithm.run(
            {
                "REDUCTIONS": str(reductions),
                "STATIONS": str(displaced),
                "OUTPUT_POINTS": str(directory / "displaced-points.json"),
                "OUTPUT_HTML": str(directory / "displaced.html"),
            },
            QgsProcessingContext(),
            Listening(),
            catchExceptions=False,
        )
        assert ok
        assert results["POINT_COUNT"] == 2
        assert any("not where it is recorded" in message for message in warnings)

    def test_the_points_table_carries_the_full_covariance(self, radiated):
        """Three coordinates from one pointing are strongly correlated, and
        ``specs/09`` section 4.6 refuses to let the export imply otherwise."""
        _directory, results = radiated
        with open(results["OUTPUT_CSV"], encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        assert len(rows) == 2
        for row in rows:
            assert float(row["cov_en"]) != 0.0

    # -- trigonometric levelling -----------------------------------------

    def test_a_balanced_leap_frog_pair_recovers_the_height_difference(self, workspace):
        """Station L stands exactly midway between A and D, so the curvature and
        refraction corrections on its two sights are equal and subtract away.
        What comes back is the height difference and nothing added to it."""
        directory, _reductions, _known = workspace
        only_l = directory / "leapfrog.json"
        only_l.write_text(
            json.dumps(syn.reductions_document({"L": syn.SETUPS["L"]})), encoding="utf-8"
        )
        results = _run(
            "geocomp:totalstation_trig_levelling",
            {
                "REDUCTIONS": str(only_l),
                "MODE": 1,
                "OUTPUT_HEIGHTS": str(directory / "leapfrog-heights.json"),
                "OUTPUT_HTML": str(directory / "leapfrog.html"),
                "OUTPUT_CSV": str(directory / "leapfrog.csv"),
            },
        )
        assert results["RESULT_COUNT"] == 1
        payload = json.loads(Path(results["OUTPUT_HEIGHTS"]).read_text(encoding="utf-8"))
        difference = payload["differences"][0]
        assert (difference["from"], difference["to"]) == ("A", "D")
        assert difference["value"]["value"] == pytest.approx(
            syn.height_difference("A", "D"), abs=1e-6
        )

    def test_a_radial_height_difference_carries_the_curvature_correction(self, workspace):
        """The synthetic sight is a straight line between marks and so contains
        no curvature or refraction. What the algorithm adds is ``(1 - k) d^2 /
        2R``, stated here in closed form rather than hidden in a tolerance."""
        directory, _reductions, _known = workspace
        one_sight = directory / "radial.json"
        one_sight.write_text(
            json.dumps(syn.reductions_document({"A": ("B",)})), encoding="utf-8"
        )
        results = _run(
            "geocomp:totalstation_trig_levelling",
            {
                "REDUCTIONS": str(one_sight),
                "MODE": 0,
                "INSTRUMENT_HEIGHT": syn.INSTRUMENT_HEIGHT,
                "TARGET_HEIGHT": syn.TARGET_HEIGHT,
                "REFRACTION": 0.13,
                "OUTPUT_HEIGHTS": str(directory / "radial-heights.json"),
            },
        )
        assert results["RESULT_COUNT"] == 1
        payload = json.loads(Path(results["OUTPUT_HEIGHTS"]).read_text(encoding="utf-8"))
        expected = syn.height_difference("A", "B") + syn.curvature_and_refraction(
            syn.horizontal_distance("A", "B")
        )
        assert payload["differences"][0]["value"]["value"] == pytest.approx(expected, abs=1e-6)


class TestBasicAndAdvancedAgree:
    """FR-070 and FR-071, across the whole Total Station group.

    Advanced parameters are collapsed in Basic mode, not removed, so the value
    used is the parameter's own default in both modes. Gating must change what
    is *shown*, never what is *computed* -- otherwise two users of the same
    version get different answers from the same data and neither can tell why.

    P3's exit criteria name this for the phase; the Analysis group has its own
    copy, and the two together cover every algorithm that declares an advanced
    parameter.
    """

    @pytest.fixture(scope="class")
    def workspace(self, geocomp_provider, tmp_path_factory):
        directory = tmp_path_factory.mktemp("gating")
        reductions = directory / "reductions.json"
        reductions.write_text(json.dumps(syn.reductions_document()), encoding="utf-8")
        known = directory / "known.json"
        known.write_text(json.dumps(syn.known_points()), encoding="utf-8")
        return directory, reductions, known

    def _advanced_defaults(self, algorithm_id: str, *, skip: tuple[str, ...] = ()) -> dict:
        """Every advanced parameter at its own declared default.

        A parameter whose default is ``None`` is *absent*, not zero, and passing
        it explicitly is the same as leaving it out -- which is the point being
        checked. ``skip`` drops the ones the caller set deliberately: passing
        their defaults back would override the caller's choice and compare two
        different computations rather than two ways of asking for one.
        """
        from qgis.core import QgsProcessingParameterDefinition

        flag = QgsProcessingParameterDefinition.Flag.FlagAdvanced
        return {
            parameter.name(): parameter.defaultValue()
            for parameter in _algorithm(algorithm_id).parameterDefinitions()
            if parameter.flags() & flag and parameter.name() not in skip
        }

    @pytest.mark.parametrize("algorithm_id", TOTAL_STATION_IDS)
    def test_every_algorithm_declares_the_gating(self, geocomp_provider, algorithm_id):
        """An algorithm with no advanced parameters would make its own parity
        test vacuous, so the declaration is checked before the behaviour."""
        assert self._advanced_defaults(algorithm_id), algorithm_id

    def test_the_traverse_computes_the_same_either_way(self, workspace):
        directory, reductions, _known = workspace
        common = {
            "REDUCTIONS": str(reductions),
            "ROUTE": ",".join(syn.ROUTE),
            "BACKSIGHT": syn.BACKSIGHT,
            "START_EASTING": syn.COORDINATES["A"][0],
            "START_NORTHING": syn.COORDINATES["A"][1],
            "START_AZIMUTH": math.degrees(syn.start_azimuth()),
            "KIND": 0,
            "METHOD": 0,
        }
        advanced = self._advanced_defaults("geocomp:totalstation_traverse")
        basic_run = _run(
            "geocomp:totalstation_traverse",
            {**common, "OUTPUT_COORDINATES": str(directory / "gating-basic.json")},
        )
        advanced_run = _run(
            "geocomp:totalstation_traverse",
            {
                **common,
                **advanced,
                "OUTPUT_COORDINATES": str(directory / "gating-advanced.json"),
            },
        )
        for key in ("ANGULAR_MISCLOSURE", "LINEAR_MISCLOSURE", "WITHIN_TOLERANCE"):
            assert basic_run[key] == advanced_run[key], key
        assert Path(basic_run["OUTPUT_COORDINATES"]).read_text(encoding="utf-8") == Path(
            advanced_run["OUTPUT_COORDINATES"]
        ).read_text(encoding="utf-8")

    def test_pre_processing_computes_the_same_either_way(self, geocomp_provider, tmp_path):
        imported = _run(
            "geocomp:totalstation_import_fieldbook",
            {
                "SOURCE": str(rd01.RAW),
                "SIGMA_DIRECTION": rd01.SIGMA_ANGLE,
                "SIGMA_ZENITH": rd01.SIGMA_ANGLE,
                "SIGMA_DISTANCE": 0.002,
                "OUTPUT_READINGS": str(tmp_path / "readings.json"),
            },
        )
        common = {"READINGS": imported["OUTPUT_READINGS"], "APPLY_ATMOSPHERIC": False}
        advanced = self._advanced_defaults(
            "geocomp:totalstation_preprocess", skip=tuple(common)
        )
        basic_run = _run(
            "geocomp:totalstation_preprocess",
            {**common, "OUTPUT_REDUCED": str(tmp_path / "basic.json")},
        )
        advanced_run = _run(
            "geocomp:totalstation_preprocess",
            {**common, **advanced, "OUTPUT_REDUCED": str(tmp_path / "advanced.json")},
        )
        for key in ("POINTING_COUNT", "BLOCKING_COUNT", "USABLE_COUNT"):
            assert basic_run[key] == advanced_run[key], key
        assert Path(basic_run["OUTPUT_REDUCED"]).read_text(encoding="utf-8") == Path(
            advanced_run["OUTPUT_REDUCED"]
        ).read_text(encoding="utf-8")
