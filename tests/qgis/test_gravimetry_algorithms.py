# SPDX-License-Identifier: GPL-2.0-or-later
"""The gravimetry chain, run end to end in a real QGIS (phase P8b).

``specs/ROADMAP.md`` P8b's exit: both algorithms run from the menu and the
toolbox on a CG-5 file and produce the P8a result as layers and a report;
values display in the configured unit and are stored in SI.

The mathematics is tested without QGIS in ``tests/test_gravimetry_*.py``. What
only exists here is that the two algorithms register, that Processing accepts
their parameters, that pre-processing's document is the network's input, and
that the outputs say what the settings ask them to.

Two surveys: a CG-5 export built from the format (the real one cannot be
redistributed), and USGS's synthetic Burris survey Test 2, whose truth is
published -- five stations and a drift of 0.01 mGal per hour.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from tests.gravimeter_samples import cg5_export
from tests.qgis.conftest import requires_modern_field_api

pytestmark = pytest.mark.qgis

PREPROCESS = "geocomp:gravimetry_preprocess"
NETWORK = "geocomp:gravimetry_network"
USGS = Path(__file__).resolve().parent.parent / "data" / "rd07" / "gsadjust"
TRUTH_MGAL = {"sta1": 50.0, "sta2": 48.0, "sta3": 45.0, "sta4": 48.5, "sta5": 46.0}


@pytest.fixture(autouse=True, scope="module")
def _registered(geocomp_provider):
    return geocomp_provider


def _algorithm(algorithm_id: str):
    from qgis.core import QgsApplication

    algorithm = QgsApplication.processingRegistry().algorithmById(algorithm_id)
    assert algorithm is not None, f"{algorithm_id} is not registered"
    return algorithm


def _run(algorithm_id: str, parameters: dict):
    """Run and return ``(results, context)`` -- the context owns any temporary layer."""
    from qgis.core import QgsProcessingContext, QgsProcessingFeedback

    context = QgsProcessingContext()
    results, ok = _algorithm(algorithm_id).create({}).run(
        parameters, context, QgsProcessingFeedback(), catchExceptions=False
    )
    assert ok, f"{algorithm_id} reported failure"
    return results, context


def _rows(path: Path) -> list[dict[str, str]]:
    with open(path, encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _burris_profiles(path: Path) -> Path:
    """USGS's meter B44: synthetic readings, tide-free, 3 microgal each."""
    from geocomp.core.instruments import ProfileLibrary
    from geocomp.core.instruments.gravimeter import GravimeterProfile

    library = ProfileLibrary()
    library.add_gravimeter(
        GravimeterProfile(
            id="B44",
            sigma_reading=3.0e-8,
            applies_tide=True,
            source="USGS GSadjust synthetic Test 2",
        )
    )
    path.write_text(json.dumps(library.to_dict()), encoding="utf-8")
    return path


@pytest.fixture()
def test2_readings(tmp_path) -> Path:
    document = tmp_path / "test2.json"
    _run(
        PREPROCESS,
        {
            "READINGS": str(USGS / "Test2.txt"),
            "PROFILES": str(_burris_profiles(tmp_path / "profiles.json")),
            "PRECISION_FLOOR": 0.0,
            "OUTPUT_READINGS": str(document),
            "OUTPUT_CSV": str(tmp_path / "corrections.csv"),
        },
    )
    return document


class TestRegistration:
    def test_both_are_in_the_gravimetry_menu_in_order(self):
        from geocomp.registry import algorithms_in_menu

        assert [spec.id for spec in algorithms_in_menu("gravimetry")] == [PREPROCESS, NETWORK]

    def test_the_defaults_come_from_the_settings(self):
        """``specs/15`` section 2.3: a setting nothing reads is worse than none."""
        from geocomp.services.settings_service import settings

        with settings.run_overrides({"gravimeter.drift_degree": 2, "gravimeter.drift_mode": "pre_corrected"}):
            algorithm = _algorithm(NETWORK).create({})
            algorithm.initAlgorithm({})
            assert algorithm.parameterDefinition("DRIFT_DEGREE").defaultValue() == 2
            assert algorithm.parameterDefinition("DRIFT_MODE").defaultValue() == 1


class TestPreprocessingACg5File:
    def test_the_instruments_tide_is_kept_and_the_document_written(self, tmp_path):
        source = tmp_path / "survey.txt"
        source.write_text(cg5_export(utc_is_local_minus=0.0), encoding="latin-1")
        results, _context = _run(
            PREPROCESS,
            {
                "READINGS": str(source),
                "PRECISION_FLOOR": 0.005,
                "OUTPUT_READINGS": str(tmp_path / "reduced.json"),
                "OUTPUT_CSV": str(tmp_path / "corrections.csv"),
                "OUTPUT_DRIFT": str(tmp_path / "drift.csv"),
            },
        )
        assert results["READING_COUNT"] == 5
        assert results["SESSION_COUNT"] == 1
        assert results["LARGEST_TIDE"] == 0.0
        document = json.loads((tmp_path / "reduced.json").read_text(encoding="utf-8"))
        assert document["format"] == "geocomp.gravity_readings"
        assert document["file_format"] == "cg5"
        assert [g["id"] for g in document["profiles"]["gravimeters"]] == ["CG-5 40123"]
        # No profile was given, and the notes and the factor both say so.
        assert any("No gravimeter profile" in note for note in document["notes"])
        rows = _rows(tmp_path / "corrections.csv")
        assert len(rows) == 5
        assert all(row["tide_mgal"] == "" for row in rows)
        assert {row["uncertainty"] for row in rows} == {"approximate"}
        (drift,) = _rows(tmp_path / "drift.csv")
        assert drift["estimable_jointly"] == "True"
        assert drift["base_station"] in {"1", "2"}

    def test_replacing_the_tide_computes_geocomps(self, tmp_path):
        source = tmp_path / "survey.txt"
        source.write_text(cg5_export(utc_is_local_minus=0.0), encoding="latin-1")
        results, _context = _run(
            PREPROCESS,
            {
                "READINGS": str(source),
                "REPLACE_TIDE": True,
                "OUTPUT_READINGS": str(tmp_path / "reduced.json"),
                "OUTPUT_CSV": str(tmp_path / "corrections.csv"),
            },
        )
        assert results["LARGEST_TIDE"] > 1.0e-7
        assert all(row["tide_mgal"] for row in _rows(tmp_path / "corrections.csv"))

    def test_the_display_unit_names_the_columns(self, tmp_path):
        from geocomp.services.settings_service import settings

        source = tmp_path / "survey.txt"
        source.write_text(cg5_export(utc_is_local_minus=0.0), encoding="latin-1")
        with settings.run_overrides({"gravimeter.display_unit": "ugal"}):
            _run(
                PREPROCESS,
                {"READINGS": str(source), "OUTPUT_CSV": str(tmp_path / "corrections.csv")},
            )
        rows = _rows(tmp_path / "corrections.csv")
        assert float(rows[0]["reduced_ugal"]) == pytest.approx(3021.123e3, abs=1.0)

    def test_a_hand_written_library_missing_a_field_is_named(self, tmp_path):
        from qgis.core import QgsProcessingException

        source = tmp_path / "survey.txt"
        source.write_text(cg5_export(utc_is_local_minus=0.0), encoding="latin-1")
        library = tmp_path / "profiles.json"
        library.write_text(
            json.dumps({"gravimeters": [{"id": "CG-5 40123", "calibration_factor": {"value": 1.0}}]}),
            encoding="utf-8",
        )
        with pytest.raises(QgsProcessingException, match="profile library"):
            _run(PREPROCESS, {"READINGS": str(source), "PROFILES": str(library)})

    def test_a_file_of_no_known_format_is_refused_with_what_was_expected(self, tmp_path):
        from qgis.core import QgsProcessingException

        source = tmp_path / "notes.txt"
        source.write_text("shopping list\nmilk\n", encoding="utf-8")
        with pytest.raises(QgsProcessingException, match="CG-5"):
            _run(PREPROCESS, {"READINGS": str(source)})


class TestTheNetwork:
    def test_usgs_test_2_is_recovered(self, tmp_path, test2_readings):
        results, _context = _run(
            NETWORK,
            {
                "READINGS": str(test2_readings),
                "KNOWN_GRAVITY": "sta1=50.0",
                "OUTPUT_SOLUTION": str(tmp_path / "solution.json"),
                "OUTPUT_HTML": str(tmp_path / "report.html"),
                "OUTPUT_CSV": str(tmp_path / "gravity.csv"),
            },
        )
        assert results["DATUM_DEFECT"] == 1
        rows = {row["station"]: row for row in _rows(tmp_path / "gravity.csv")}
        assert set(rows) == set(TRUTH_MGAL)
        assert rows["sta1"]["determined_by"] == "held"
        for station, truth in TRUTH_MGAL.items():
            value = float(rows[station]["gravity_mgal"])
            sigma = float(rows[station]["sigma_mgal"])
            assert abs(value - truth) <= max(3.0 * sigma, 1e-9), station
        solution = json.loads((tmp_path / "solution.json").read_text(encoding="utf-8"))
        from geocomp.core.units import Unit

        assert all(s["gravity"]["unit"] == Unit.ACCELERATION.name for s in solution["adjusted_stations"])
        report = (tmp_path / "report.html").read_text(encoding="utf-8")
        assert "held fixed at sta1" in report
        assert "estimated with the station values" in report

    def test_without_known_gravity_the_report_says_every_value_is_relative(
        self, tmp_path, test2_readings
    ):
        _run(
            NETWORK,
            {"READINGS": str(test2_readings), "OUTPUT_HTML": str(tmp_path / "report.html")},
        )
        assert "inner constraint" in (tmp_path / "report.html").read_text(encoding="utf-8")

    def test_a_lone_absolute_value_is_named_uncheckable(self, tmp_path, test2_readings):
        results, _context = _run(
            NETWORK,
            {
                "READINGS": str(test2_readings),
                "KNOWN_GRAVITY": "sta1=50.0±0.005",
                "OUTPUT_HTML": str(tmp_path / "report.html"),
            },
        )
        assert results["UNCHECKABLE_COUNT"] >= 1
        report = (tmp_path / "report.html").read_text(encoding="utf-8")
        assert "Uncheckable observations" in report
        assert "absolute:sta1" in report

    def test_pre_correction_runs_and_says_so(self, tmp_path, test2_readings):
        _run(
            NETWORK,
            {
                "READINGS": str(test2_readings),
                "KNOWN_GRAVITY": "sta1=50.0",
                "DRIFT_MODE": 1,
                "OUTPUT_HTML": str(tmp_path / "report.html"),
            },
        )
        assert "fitted to base" in (tmp_path / "report.html").read_text(encoding="utf-8")

    def test_a_malformed_known_gravity_is_refused(self, tmp_path, test2_readings):
        from qgis.core import QgsProcessingException

        with pytest.raises(QgsProcessingException, match="station=value"):
            _run(NETWORK, {"READINGS": str(test2_readings), "KNOWN_GRAVITY": "sta1 50.0"})

    def test_a_document_pre_processing_did_not_write_is_refused(self, tmp_path):
        from qgis.core import QgsProcessingException

        other = tmp_path / "other.json"
        other.write_text(json.dumps({"lines": []}), encoding="utf-8")
        with pytest.raises(QgsProcessingException, match="Pre-processing"):
            _run(NETWORK, {"READINGS": str(other)})

    def test_the_cg5_chain_runs_from_file_to_report(self, tmp_path):
        """The exit criterion's shape: a CG-5 file in, the P8a result out."""
        source = tmp_path / "survey.txt"
        source.write_text(cg5_export(utc_is_local_minus=0.0), encoding="latin-1")
        _run(
            PREPROCESS,
            {
                "READINGS": str(source),
                "PRECISION_FLOOR": 0.005,
                "OUTPUT_READINGS": str(tmp_path / "reduced.json"),
            },
        )
        results, _context = _run(
            NETWORK,
            {
                "READINGS": str(tmp_path / "reduced.json"),
                "KNOWN_GRAVITY": "1=979000.0",
                "OUTPUT_SOLUTION": str(tmp_path / "solution.json"),
                "OUTPUT_HTML": str(tmp_path / "report.html"),
            },
        )
        assert results["DEGREES_OF_FREEDOM"] == 1
        solution = json.loads((tmp_path / "solution.json").read_text(encoding="utf-8"))
        # No calibration was given: the solution may not call itself rigorous.
        assert solution["uncertainty_mode"] == "APPROXIMATE"
        assert solution["provenance"]["uncertainty_mode"] == "APPROXIMATE"
        assert "model_assumed" in (tmp_path / "report.html").read_text(encoding="utf-8")


@requires_modern_field_api
class TestTheLayers:
    def _layers(self, tmp_path, readings, **extra):
        from qgis.core import QgsProcessing, QgsProcessingUtils

        parameters = {
            "READINGS": str(readings),
            "KNOWN_GRAVITY": "sta1=50.0",
            "OUTPUT_STATIONS": QgsProcessing.TEMPORARY_OUTPUT,
            "OUTPUT_DIFFERENCES": QgsProcessing.TEMPORARY_OUTPUT,
        }
        parameters.update(extra)
        results, context = _run(NETWORK, parameters)
        stations = QgsProcessingUtils.mapLayerFromString(results["OUTPUT_STATIONS"], context)
        differences = QgsProcessingUtils.mapLayerFromString(results["OUTPUT_DIFFERENCES"], context)
        assert stations is not None and differences is not None
        return stations, differences, context

    def test_every_station_is_drawn_the_held_one_included(self, tmp_path, test2_readings):
        stations, _differences, _context = self._layers(tmp_path, test2_readings)
        features = {f["station"]: f for f in stations.getFeatures()}
        assert set(features) == set(TRUTH_MGAL)
        assert features["sta1"]["role"] == "held"
        assert features["sta1"]["gravity"] == pytest.approx(50.0)
        assert {f["unit"] for f in features.values()} == {"mGal"}
        for name, truth in TRUTH_MGAL.items():
            assert features[name]["gravity_si"] == pytest.approx(truth * 1e-5, abs=5e-8)

    def test_the_differences_carry_the_decision_in_the_display_unit(self, tmp_path, test2_readings):
        from geocomp.services.settings_service import settings

        with settings.run_overrides({"gravimeter.display_unit": "ugal"}):
            _stations, differences, _context = self._layers(tmp_path, test2_readings)
        features = list(differences.getFeatures())
        assert features
        assert {f["unit"] for f in features} == {"µGal"}
        assert {f["decision"] for f in features} <= {"accepted", "rejected", "uncheckable"}
        assert all(abs(f["residual"]) < 50.0 for f in features)
        assert "µGal" in differences.name()
