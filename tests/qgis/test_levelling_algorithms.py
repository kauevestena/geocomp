# SPDX-License-Identifier: GPL-2.0-or-later
"""The levelling chain, run end to end in a real QGIS.

``specs/ROADMAP.md`` phase P4: a second technique, cheaply, by reusing P2. These
tests run exactly that -- import a field book, reduce it by each of the three
schemes, close the loop, adjust the network -- through the Processing framework,
with no external engine installed.

The mathematics is tested exhaustively without QGIS in ``tests/test_levelling.py``
and ``tests/test_levelbook_import.py``. What only exists inside QGIS is that the
six algorithms register, that their parameters are declared in a way Processing
accepts, and that each one's output is the next one's input (FR-033).
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

import tests.reference_levelling as rd

pytestmark = pytest.mark.qgis

LEVELLING_IDS = (
    "geocomp:levelling_import",
    "geocomp:levelling_equal_sights",
    "geocomp:levelling_equidistant_sights",
    "geocomp:levelling_extreme_sights",
    "geocomp:levelling_closures",
    "geocomp:levelling_network",
)


@pytest.fixture(autouse=True, scope="module")
def _registered(geocomp_provider):
    """Every test in this module needs the provider registered.

    Autouse rather than threaded through each signature: there is no test here
    that is *about* an unregistered provider, so making every one of them say so
    would be noise.
    """
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


# -- the field books, written as CSV -------------------------------------


def _write_book(path: Path, rows: list[list[str]]) -> Path:
    with open(path, "w", encoding="utf-8", newline="") as handle:
        csv.writer(handle).writerows(rows)
    return path


def _mapping_document(path: Path, columns: list[dict], **extra) -> Path:
    payload = {"name": "tier3", "columns": columns, "decimal_separator": "."}
    payload.update(extra)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _reading_layout_mapping(path: Path) -> Path:
    return _mapping_document(
        path,
        [
            {"field": "setup", "column": "setup"},
            {"field": "station", "column": "point"},
            {"field": "sight", "column": "kind"},
            {"field": "reading", "column": "reading"},
            {"field": "distance", "column": "distance"},
        ],
    )


def _line_rows(book) -> list[list[str]]:
    """One row per reading, from a generated RD-04 book."""
    rows = [["setup", "point", "kind", "reading", "distance"]]
    for setup in book.line.setups:
        rows.append(
            [
                setup.id,
                setup.backsight.station,
                "BS",
                f"{setup.backsight.reading.value:.5f}",
                f"{setup.backsight.distance_value:.2f}",
            ]
        )
        for index, sight in enumerate(setup.foresights):
            rows.append(
                [
                    setup.id,
                    sight.station,
                    "FS" if index == 0 else "IS",
                    f"{sight.reading.value:.5f}",
                    f"{sight.distance_value:.2f}",
                ]
            )
    return rows


@pytest.fixture(scope="module")
def profiles(tmp_path_factory) -> str:
    """An RD-04 level profile library on disk."""
    from geocomp.core.instruments import ProfileLibrary

    library = ProfileLibrary()
    library.add_level(rd.profile())
    path = tmp_path_factory.mktemp("levelling") / "profiles.json"
    path.write_text(json.dumps(library.to_dict()), encoding="utf-8")
    return str(path)


@pytest.fixture(scope="module")
def imported(tmp_path_factory, profiles) -> dict:
    """The balanced RD-04 line, imported through the algorithm."""
    directory = tmp_path_factory.mktemp("import")
    book = _write_book(directory / "book.csv", _line_rows(rd.balanced_line()))
    mapping = _reading_layout_mapping(directory / "mapping.json")
    return _run(
        "geocomp:levelling_import",
        {
            "BOOK": str(book),
            "MAPPING": str(mapping),
            "PROFILES": profiles,
            "OUTPUT_SETUPS": str(directory / "setups.json"),
            "OUTPUT_HTML": str(directory / "import.html"),
        },
    )


class TestRegistration:
    def test_every_levelling_algorithm_is_registered(self):
        for algorithm_id in LEVELLING_IDS:
            assert _algorithm(algorithm_id) is not None

    def test_each_declares_a_display_name_and_help(self):
        for algorithm_id in LEVELLING_IDS:
            algorithm = _algorithm(algorithm_id)
            assert algorithm.displayName()
            assert algorithm.shortHelpString()
            assert "FR-" in algorithm.shortHelpString()

    def test_they_are_in_the_levelling_group(self):
        for algorithm_id in LEVELLING_IDS:
            assert _algorithm(algorithm_id).groupId() == "levelling"

    def test_every_parameter_is_accepted_by_processing(self):
        """The check that catches a wrong enum or a bad default before a user
        does. Under PyQt6 a bad parameter aborts the whole provider."""
        for algorithm_id in LEVELLING_IDS:
            algorithm = _algorithm(algorithm_id).create({})
            assert algorithm.parameterDefinitions()


class TestTheChain:
    def test_the_import_produces_setups_and_lines(self, imported):
        assert imported["SETUP_COUNT"] == 3
        assert imported["LINE_COUNT"] == 1
        assert imported["REJECTED_ROWS"] == 0
        assert Path(imported["OUTPUT_SETUPS"]).is_file()

    def test_equal_sights_reduces_the_line_to_the_truth(self, tmp_path, imported, profiles):
        book = rd.balanced_line()
        results = _run(
            "geocomp:levelling_equal_sights",
            {
                "SETUPS": imported["OUTPUT_SETUPS"],
                "PROFILES": profiles,
                "OUTPUT_REDUCTIONS": str(tmp_path / "reduced.json"),
                "OUTPUT_HTML": str(tmp_path / "reduced.html"),
                "OUTPUT_CSV": str(tmp_path / "reduced.csv"),
            },
        )
        assert results["LINE_COUNT"] == 1
        assert results["WORST_IMBALANCE"] == pytest.approx(0.0, abs=1e-9)

        payload = json.loads(Path(results["OUTPUT_REDUCTIONS"]).read_text(encoding="utf-8"))
        difference = payload["lines"][0]["height_difference"]["value"]
        assert difference == pytest.approx(book.true_difference, abs=1e-6)

    def test_the_report_and_csv_are_written(self, tmp_path, imported, profiles):
        results = _run(
            "geocomp:levelling_equal_sights",
            {
                "SETUPS": imported["OUTPUT_SETUPS"],
                "PROFILES": profiles,
                "OUTPUT_REDUCTIONS": str(tmp_path / "r.json"),
                "OUTPUT_HTML": str(tmp_path / "r.html"),
                "OUTPUT_CSV": str(tmp_path / "r.csv"),
            },
        )
        html = Path(results["OUTPUT_HTML"]).read_text(encoding="utf-8")
        assert "Accumulated imbalance" in html
        rows = list(csv.DictReader(Path(results["OUTPUT_CSV"]).open(encoding="utf-8")))
        assert rows and "height_difference_m" in rows[0]


class TestExtremeSights:
    def test_the_correlated_differences_are_produced(self, tmp_path, profiles):
        setup, truth = rd.extreme_sights_setup()
        rows = [["setup", "point", "kind", "reading", "distance"]]
        rows.append(
            [
                setup.id,
                setup.backsight.station,
                "BS",
                f"{setup.backsight.reading.value:.5f}",
                f"{setup.backsight.distance_value:.2f}",
            ]
        )
        for index, sight in enumerate(setup.foresights):
            rows.append(
                [
                    setup.id,
                    sight.station,
                    "FS" if index == 0 else "IS",
                    f"{sight.reading.value:.5f}",
                    f"{sight.distance_value:.2f}",
                ]
            )
        book = _write_book(tmp_path / "extreme.csv", rows)
        mapping = _reading_layout_mapping(tmp_path / "mapping.json")

        imported = _run(
            "geocomp:levelling_import",
            {
                "BOOK": str(book),
                "MAPPING": str(mapping),
                "PROFILES": profiles,
                "OUTPUT_SETUPS": str(tmp_path / "setups.json"),
                "OUTPUT_HTML": str(tmp_path / "import.html"),
            },
        )
        results = _run(
            "geocomp:levelling_extreme_sights",
            {
                "SETUPS": imported["OUTPUT_SETUPS"],
                "PROFILES": profiles,
                "OUTPUT_DIFFERENCES": str(tmp_path / "diff.json"),
                "OUTPUT_HTML": str(tmp_path / "diff.html"),
            },
        )
        assert results["SETUP_COUNT"] == 1
        assert results["DIFFERENCE_COUNT"] == 3

        payload = json.loads(Path(results["OUTPUT_DIFFERENCES"]).read_text(encoding="utf-8"))
        entry = payload["setups"][0]
        assert entry["to_stations"] == ["BM3", "S1", "S2"]
        for station, quantity in zip(
            entry["to_stations"], entry["height_differences"], strict=True
        ):
            assert quantity["value"] == pytest.approx(truth[station] - truth["BM1"], abs=1e-6)

        html = Path(results["OUTPUT_HTML"]).read_text(encoding="utf-8")
        assert "Overstated by" in html

    def test_it_refuses_when_no_setup_has_several_foresights(
        self, tmp_path, imported, profiles
    ):
        from qgis.core import QgsProcessingException

        with pytest.raises(QgsProcessingException):
            _run(
                "geocomp:levelling_extreme_sights",
                {
                    "SETUPS": imported["OUTPUT_SETUPS"],
                    "PROFILES": profiles,
                    "OUTPUT_DIFFERENCES": str(tmp_path / "diff.json"),
                },
            )


class TestEquidistantSights:
    def test_the_crossing_cancels_its_refraction(self, tmp_path, profiles):
        near, far, truth = rd.reciprocal_crossing(refraction=0.012)
        rows = [["setup", "point", "kind", "reading", "distance"]]
        for pair in (near, far):
            for kind, sight in (("BS", pair.near), ("FS", pair.far)):
                rows.append(
                    [
                        pair.setup_id,
                        sight.station,
                        kind,
                        f"{sight.reading.value:.5f}",
                        f"{sight.distance_value:.2f}",
                    ]
                )
        book = _write_book(tmp_path / "crossing.csv", rows)
        mapping = _reading_layout_mapping(tmp_path / "mapping.json")

        imported = _run(
            "geocomp:levelling_import",
            {
                "BOOK": str(book),
                "MAPPING": str(mapping),
                "PROFILES": profiles,
                "OUTPUT_SETUPS": str(tmp_path / "setups.json"),
                "OUTPUT_HTML": str(tmp_path / "import.html"),
            },
        )
        results = _run(
            "geocomp:levelling_equidistant_sights",
            {
                "SETUPS": imported["OUTPUT_SETUPS"],
                "INFLATION": 2.0,
                "DISCREPANCY_TOLERANCE": 0.005,
                "OUTPUT_DIFFERENCES": str(tmp_path / "crossing.json"),
                "OUTPUT_HTML": str(tmp_path / "crossing.html"),
            },
        )
        assert results["CROSSING_COUNT"] == 1
        assert results["WORST_DISCREPANCY"] == pytest.approx(0.024, abs=1e-6)

        payload = json.loads(Path(results["OUTPUT_DIFFERENCES"]).read_text(encoding="utf-8"))
        crossing = payload["crossings"][0]
        assert crossing["height_difference"]["value"] == pytest.approx(truth, abs=1e-6)


class TestClosuresAndTheNetwork:
    @pytest.fixture
    def loop_reductions(self, tmp_path, profiles) -> str:
        """The RD-04 loop, imported and reduced, as one reduction document."""
        books, _truth = rd.loop(noise=0.0003)
        rows = [["setup", "point", "kind", "reading", "distance", "line"]]
        for book in books:
            for setup in book.line.setups:
                rows.append(
                    [
                        setup.id,
                        setup.backsight.station,
                        "BS",
                        f"{setup.backsight.reading.value:.5f}",
                        f"{setup.backsight.distance_value:.2f}",
                        book.line.id,
                    ]
                )
                rows.append(
                    [
                        setup.id,
                        setup.foresights[0].station,
                        "FS",
                        f"{setup.foresights[0].reading.value:.5f}",
                        f"{setup.foresights[0].distance_value:.2f}",
                        book.line.id,
                    ]
                )
        source = _write_book(tmp_path / "loop.csv", rows)
        mapping = _mapping_document(
            tmp_path / "mapping.json",
            [
                {"field": "setup", "column": "setup"},
                {"field": "station", "column": "point"},
                {"field": "sight", "column": "kind"},
                {"field": "reading", "column": "reading"},
                {"field": "distance", "column": "distance"},
                {"field": "line", "column": "line"},
            ],
        )
        imported = _run(
            "geocomp:levelling_import",
            {
                "BOOK": str(source),
                "MAPPING": str(mapping),
                "PROFILES": profiles,
                "OUTPUT_SETUPS": str(tmp_path / "setups.json"),
                "OUTPUT_HTML": str(tmp_path / "import.html"),
            },
        )
        assert imported["LINE_COUNT"] == 3
        reduced = _run(
            "geocomp:levelling_equal_sights",
            {
                "SETUPS": imported["OUTPUT_SETUPS"],
                "PROFILES": profiles,
                "OUTPUT_REDUCTIONS": str(tmp_path / "reduced.json"),
                "OUTPUT_HTML": str(tmp_path / "reduced.html"),
            },
        )
        return reduced["OUTPUT_REDUCTIONS"]

    def test_the_loop_closes_within_a_configured_tolerance(self, tmp_path, loop_reductions):
        results = _run(
            "geocomp:levelling_closures",
            {
                "REDUCTIONS": loop_reductions,
                "MODE": 0,
                "TOLERANCE_COEFFICIENT": 0.008,
                "OUTPUT_CLOSURES": str(tmp_path / "closure.json"),
                "OUTPUT_HTML": str(tmp_path / "closure.html"),
                "OUTPUT_CSV": str(tmp_path / "closure.csv"),
            },
        )
        assert results["PASSED"] == 1
        assert abs(results["MISCLOSURE"]) < results["PERMISSIBLE"]

    def test_with_no_tolerance_there_is_no_verdict(self, tmp_path, loop_reductions):
        """Three states, not two. -1 is 'not judged'."""
        results = _run(
            "geocomp:levelling_closures",
            {
                "REDUCTIONS": loop_reductions,
                "MODE": 0,
                "TOLERANCE_COEFFICIENT": 0.0,
                "OUTPUT_CLOSURES": str(tmp_path / "closure.json"),
                "OUTPUT_HTML": str(tmp_path / "closure.html"),
            },
        )
        assert results["PASSED"] == -1
        assert results["PERMISSIBLE"] == -1.0

    def test_the_network_adjusts_and_recovers_the_heights(self, tmp_path, loop_reductions):
        results = _run(
            "geocomp:levelling_network",
            {
                "REDUCTIONS": loop_reductions,
                "BENCHMARKS": f"BM1={rd.HEIGHTS['BM1']:.3f}",
                "WEIGHTING": 0,
                "SIGMA_PER_KM": 0.0007,
                "OUTPUT_SOLUTION": str(tmp_path / "solution.json"),
                "OUTPUT_HTML": str(tmp_path / "solution.html"),
                "OUTPUT_CSV": str(tmp_path / "heights.csv"),
            },
        )
        assert results["DEGREES_OF_FREEDOM"] == 1
        assert results["WORST_HEIGHT_UNCERTAINTY"] > 0.0

        rows = {
            row["station"]: float(row["height_m"])
            for row in csv.DictReader(Path(results["OUTPUT_CSV"]).open(encoding="utf-8"))
        }
        for station in ("BM2", "BM4"):
            assert rows[station] == pytest.approx(rd.HEIGHTS[station], abs=0.002)

    def test_trigonometric_differences_join_the_network_with_their_own_factor(
        self, tmp_path, loop_reductions
    ):
        """specs/10 criterion 5, from the menu: the document *Trigonometric
        levelling* writes is adjusted with the lines, and each technique can be
        given its own variance component (P12c). Until then nothing read it."""
        from geocomp.core.uncertainty import Quantity
        from geocomp.core.units import Unit

        def difference(start, end, value):
            quantity = Quantity.from_std_dev(value, 0.004, Unit.METRE)
            return {"from": start, "to": end, "value": quantity.to_dict()}

        heights = rd.HEIGHTS
        trigonometric = tmp_path / "trigonometric.json"
        trigonometric.write_text(
            json.dumps(
                {
                    "kind": "geocomp.height_differences",
                    "version": 1,
                    "mode": "radial",
                    "differences": [
                        difference("BM1", "BM2", heights["BM2"] - heights["BM1"] + 0.003),
                        difference("BM2", "BM4", heights["BM4"] - heights["BM2"] - 0.002),
                        difference("BM4", "BM1", heights["BM1"] - heights["BM4"] + 0.001),
                        # A point no line reached: the trigonometric differences give it a height.
                        difference("BM2", "T1", 1.234),
                    ],
                }
            ),
            encoding="utf-8",
        )
        results = _run(
            "geocomp:levelling_network",
            {
                "REDUCTIONS": loop_reductions,
                "TRIGONOMETRIC": str(trigonometric),
                "VARIANCE_COMPONENTS": True,
                "BENCHMARKS": f"BM1={rd.HEIGHTS['BM1']:.3f}",
                "WEIGHTING": 0,
                "SIGMA_PER_KM": 0.0007,
                "OUTPUT_SOLUTION": str(tmp_path / "solution.json"),
                "OUTPUT_HTML": str(tmp_path / "solution.html"),
                "OUTPUT_CSV": str(tmp_path / "heights.csv"),
            },
        )
        assert results["DEGREES_OF_FREEDOM"] == 1 + 3, "three differences between benchmarks add three"
        rows = {
            row["station"]: float(row["height_m"])
            for row in csv.DictReader(Path(results["OUTPUT_CSV"]).open(encoding="utf-8"))
        }
        assert rows["T1"] == pytest.approx(rows["BM2"] + 1.234, abs=1e-6)

        solution = json.loads(Path(results["OUTPUT_SOLUTION"]).read_text(encoding="utf-8"))
        components = solution["provenance"]["parameters"]["variance_components"]
        assert set(components) == {"levelling", "total_station"}
        assert components["total_station"]["observations"] == 4
        report = Path(results["OUTPUT_HTML"]).read_text(encoding="utf-8")
        assert "Variance components by technique" in report

    def test_a_document_of_another_kind_is_refused_by_name(self, tmp_path, loop_reductions):
        from qgis.core import QgsProcessingException

        wrong = tmp_path / "not-heights.json"
        wrong.write_text(json.dumps({"kind": "geocomp.readings"}), encoding="utf-8")
        with pytest.raises(QgsProcessingException, match="Trigonometric levelling"):
            _run(
                "geocomp:levelling_network",
                {
                    "REDUCTIONS": loop_reductions,
                    "TRIGONOMETRIC": str(wrong),
                    "BENCHMARKS": f"BM1={rd.HEIGHTS['BM1']:.3f}",
                    "OUTPUT_SOLUTION": str(tmp_path / "solution.json"),
                },
            )

    def test_the_report_gives_relative_height_uncertainties(self, tmp_path, loop_reductions):
        """The 1D analogue of the relative error ellipse, which specs/10 section 4
        names and which no 2D-oriented station table shows."""
        results = _run(
            "geocomp:levelling_network",
            {
                "REDUCTIONS": loop_reductions,
                "BENCHMARKS": f"BM1={rd.HEIGHTS['BM1']:.3f}",
                "WEIGHTING": 0,
                "SIGMA_PER_KM": 0.0007,
                "OUTPUT_SOLUTION": str(tmp_path / "s.json"),
                "OUTPUT_HTML": str(tmp_path / "s.html"),
            },
        )
        html = Path(results["OUTPUT_HTML"]).read_text(encoding="utf-8")
        assert "Relative height uncertainties" in html

    def test_a_free_network_adjusts_without_benchmarks(self, tmp_path, loop_reductions):
        results = _run(
            "geocomp:levelling_network",
            {
                "REDUCTIONS": loop_reductions,
                "BENCHMARKS": "",
                "FREE": True,
                "WEIGHTING": 0,
                "SIGMA_PER_KM": 0.0007,
                "OUTPUT_SOLUTION": str(tmp_path / "free.json"),
                "OUTPUT_HTML": str(tmp_path / "free.html"),
            },
        )
        assert results["DEGREES_OF_FREEDOM"] == 1

    def test_a_malformed_benchmark_is_refused_with_an_actionable_message(
        self, tmp_path, loop_reductions
    ):
        from qgis.core import QgsProcessingException

        with pytest.raises(QgsProcessingException) as caught:
            _run(
                "geocomp:levelling_network",
                {
                    "REDUCTIONS": loop_reductions,
                    "BENCHMARKS": "BM1 100.000",
                    "WEIGHTING": 0,
                    "OUTPUT_SOLUTION": str(tmp_path / "bad.json"),
                },
            )
        assert "id=height" in str(caught.value)

    def test_the_solution_document_carries_heights_not_eastings(
        self, tmp_path, loop_reductions
    ):
        """The P2 defect P4 found: a 1D solution wrote its heights into the
        easting slot, so every levelling result reported a height of zero."""
        results = _run(
            "geocomp:levelling_network",
            {
                "REDUCTIONS": loop_reductions,
                "BENCHMARKS": f"BM1={rd.HEIGHTS['BM1']:.3f}",
                "WEIGHTING": 0,
                "SIGMA_PER_KM": 0.0007,
                "OUTPUT_SOLUTION": str(tmp_path / "solution.json"),
            },
        )
        payload = json.loads(Path(results["OUTPUT_SOLUTION"]).read_text(encoding="utf-8"))
        stations = {s["station_id"]: s for s in payload["adjusted_stations"]}
        values = stations["BM2"]["position"]["values"]
        assert values[2]["value"] == pytest.approx(rd.HEIGHTS["BM2"], abs=0.002)
        assert values[0]["value"] == 0.0

    def test_the_network_document_types_every_difference(self, tmp_path, loop_reductions):
        """What the Integration menu combines (``specs/10`` section 5): each
        difference says what it is a difference of, and the benchmark is held
        in height alone, as the lines held it."""
        from geocomp.core.models import HeightType, network_from_document

        results = _run(
            "geocomp:levelling_network",
            {
                "REDUCTIONS": loop_reductions,
                "BENCHMARKS": f"BM1={rd.HEIGHTS['BM1']:.3f}±0.002",
                "WEIGHTING": 0,
                "SIGMA_PER_KM": 0.0007,
                "OUTPUT_NETWORK": str(tmp_path / "network.json"),
            },
        )
        network = network_from_document(
            json.loads(Path(results["OUTPUT_NETWORK"]).read_text(encoding="utf-8"))
        )
        assert network.observations
        assert {o.meta["height_type"] for o in network.observations.values()} == {
            HeightType.ORTHOMETRIC.name
        }
        assert network.epoch is not None
        benchmark = network.stations["BM1"]
        assert benchmark.constraint.components == {"up"}
        assert benchmark.constraint.position.values[2].value == pytest.approx(rd.HEIGHTS["BM1"])


class TestTheToleranceGateAndTheOrthometricCorrection:
    """P12a: ``level.adjust_failing_lines`` and ``level.apply_orthometric_correction``.

    Both were settings with no behaviour behind them. ``specs/10`` section 3:
    *GeoComp does not adjust a line that failed its tolerance without an
    explicit acknowledgement*; section 5: the orthometric correction is *an
    option with its magnitude reported*.
    """

    #: BM2 published 30 mm high: line BM1-BM2 closes against it 30 mm out,
    #: an order of magnitude beyond 8 mm per root km over a fifth of a kilometre.
    WRONG_BM2 = f"BM1={rd.HEIGHTS['BM1']:.3f}, BM2={rd.HEIGHTS['BM2'] + 0.030:.3f}"

    loop_reductions = TestClosuresAndTheNetwork.loop_reductions

    def _network(self, tmp_path, reductions, **parameters):
        return _run(
            "geocomp:levelling_network",
            {
                "REDUCTIONS": reductions,
                "WEIGHTING": 0,
                "SIGMA_PER_KM": 0.0007,
                "OUTPUT_SOLUTION": str(tmp_path / "solution.json"),
                "OUTPUT_HTML": str(tmp_path / "solution.html"),
                **parameters,
            },
        )

    def test_a_line_that_failed_its_tolerance_is_not_adjusted(self, tmp_path, loop_reductions):
        from qgis.core import QgsProcessingException

        with pytest.raises(QgsProcessingException) as caught:
            self._network(
                tmp_path,
                loop_reductions,
                BENCHMARKS=self.WRONG_BM2,
                TOLERANCE_COEFFICIENT=0.008,
                ADJUST_FAILING=False,
            )
        message = str(caught.value)
        assert "BM1-BM2" in message
        assert "Adjust lines that failed their tolerance" in message

    def test_an_acknowledged_failure_is_adjusted_and_recorded(self, tmp_path, loop_reductions):
        results = self._network(
            tmp_path,
            loop_reductions,
            BENCHMARKS=self.WRONG_BM2,
            TOLERANCE_COEFFICIENT=0.008,
            ADJUST_FAILING=True,
        )
        solution = json.loads(Path(results["OUTPUT_SOLUTION"]).read_text(encoding="utf-8"))
        recorded = solution["provenance"]["parameters"]
        assert recorded["adjusted_despite_tolerance"] == ["BM1-BM2"]
        assert recorded["tolerance_coefficient"] == 0.008
        html = Path(results["OUTPUT_HTML"]).read_text(encoding="utf-8")
        assert "Closures before adjustment" in html
        assert "OUT OF TOLERANCE" in html

    def test_with_no_tolerance_nothing_is_judged_and_nothing_refused(self, tmp_path, loop_reductions):
        results = self._network(
            tmp_path, loop_reductions, BENCHMARKS=self.WRONG_BM2, TOLERANCE_COEFFICIENT=0.0
        )
        html = Path(results["OUTPUT_HTML"]).read_text(encoding="utf-8")
        assert "not judged" in html

    @staticmethod
    def _positions(latitudes: dict[str, float]):
        """The loop's benchmarks as a point layer in SIRGAS 2000 / UTM 23S.

        Projected, so the latitude the algorithm uses has to come back through
        QGIS's inverse projection -- the path a user's own layer takes.
        """
        from qgis.core import (
            QgsCoordinateReferenceSystem,
            QgsCoordinateTransform,
            QgsFeature,
            QgsGeometry,
            QgsPointXY,
            QgsProject,
            QgsVectorLayer,
        )

        layer = QgsVectorLayer("Point?crs=EPSG:31983&field=station:string", "marks", "memory")
        assert layer.isValid()
        to_utm = QgsCoordinateTransform(
            QgsCoordinateReferenceSystem("EPSG:4674"),
            QgsCoordinateReferenceSystem("EPSG:31983"),
            QgsProject.instance(),
        )
        features = []
        for station, latitude in latitudes.items():
            feature = QgsFeature(layer.fields())
            feature["station"] = station
            feature.setGeometry(QgsGeometry.fromPointXY(to_utm.transform(QgsPointXY(-45.0, latitude))))
            features.append(feature)
        layer.dataProvider().addFeatures(features)
        return layer

    LATITUDES = (("BM1", -20.0), ("BM2", -20.5), ("BM4", -21.0))

    def test_the_correction_is_applied_and_its_magnitude_reported(self, tmp_path, loop_reductions):
        layer = self._positions(dict(self.LATITUDES))
        plain = self._network(
            tmp_path,
            loop_reductions,
            BENCHMARKS=f"BM1={rd.HEIGHTS['BM1']:.3f}",
            OUTPUT_CSV=str(tmp_path / "plain.csv"),
        )
        corrected = self._network(
            tmp_path,
            loop_reductions,
            BENCHMARKS=f"BM1={rd.HEIGHTS['BM1']:.3f}",
            ORTHOMETRIC=True,
            POSITIONS=layer,
            POSITION_ID="station",
            OUTPUT_CSV=str(tmp_path / "corrected.csv"),
        )
        html = Path(corrected["OUTPUT_HTML"]).read_text(encoding="utf-8")
        assert "Orthometric corrections" in html
        # The mean latitude of BM1-BM2, read back through the inverse projection
        # and written in the default display format, sexagesimal.
        assert "-20° 15' 00.0\"" in html
        solution = json.loads(Path(corrected["OUTPUT_SOLUTION"]).read_text(encoding="utf-8"))
        assert solution["provenance"]["parameters"]["orthometric_correction"] == "normal"

        def heights(path):
            return {
                row["station"]: float(row["height_m"])
                for row in csv.DictReader(Path(path).open(encoding="utf-8"))
            }

        before, after = heights(plain["OUTPUT_CSV"]), heights(corrected["OUTPUT_CSV"])
        assert after["BM2"] != before["BM2"]
        # Half a degree at a few hundred metres: millimetres at most, not metres.
        assert abs(after["BM2"] - before["BM2"]) < 0.01

    def test_without_positions_the_correction_is_refused(self, tmp_path, loop_reductions):
        from qgis.core import QgsProcessingException

        with pytest.raises(QgsProcessingException) as caught:
            self._network(
                tmp_path,
                loop_reductions,
                BENCHMARKS=f"BM1={rd.HEIGHTS['BM1']:.3f}",
                ORTHOMETRIC=True,
            )
        assert "latitudes" in str(caught.value)

    def test_a_station_missing_from_the_positions_is_named(self, tmp_path, loop_reductions):
        from qgis.core import QgsProcessingException

        layer = self._positions(dict(self.LATITUDES[:2]))
        with pytest.raises(QgsProcessingException) as caught:
            self._network(
                tmp_path,
                loop_reductions,
                BENCHMARKS=f"BM1={rd.HEIGHTS['BM1']:.3f}",
                ORTHOMETRIC=True,
                POSITIONS=layer,
                POSITION_ID="station",
            )
        assert "BM4" in str(caught.value)

    def test_a_free_network_is_not_corrected_at_an_arbitrary_height(self, tmp_path, loop_reductions):
        from qgis.core import QgsProcessingException

        with pytest.raises(QgsProcessingException) as caught:
            self._network(
                tmp_path,
                loop_reductions,
                FREE=True,
                ORTHOMETRIC=True,
                POSITIONS=self._positions(dict(self.LATITUDES)),
                POSITION_ID="station",
            )
        assert "benchmark" in str(caught.value)
