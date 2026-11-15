# SPDX-License-Identifier: GPL-2.0-or-later
"""The Level windows of the menu (ROADMAP P14c; FR-010 to FR-017).

**Menu equals toolbox**, as for the Total Station windows: RD-04's books typed
into *Levelling field book* and computed in each Level window give what the
same algorithms give on the same books written as CSV, the layout the toolbox
tests write them in (``tests/qgis/test_levelling_algorithms.py``).
"""

from __future__ import annotations

import csv
import json
import time
from pathlib import Path

import pytest

from tests import reference_levelling as rd

pytestmark = pytest.mark.qgis


def wait(window, seconds: float = 120.0) -> None:
    """Let the window's background run end, as the event loop would."""
    from qgis.PyQt.QtCore import QCoreApplication

    deadline = time.monotonic() + seconds
    QCoreApplication.processEvents()
    while window.runner.is_running and time.monotonic() < deadline:
        QCoreApplication.processEvents()
        time.sleep(0.005)
    QCoreApplication.processEvents()


def calculate(window):
    """Run the window's algorithms and return how it ended, failing on a failure."""
    window.refresh()
    assert window.calculate(), window.run_page.status.text()
    wait(window)
    outcome = window.last_outcome
    assert outcome is not None and outcome.succeeded, outcome.error if outcome else "no run"
    return outcome


def run(algorithm_id: str, parameters: dict) -> dict:
    """The toolbox route: the same algorithm, run directly."""
    from qgis.core import QgsApplication, QgsProcessingContext, QgsProcessingFeedback

    algorithm = QgsApplication.processingRegistry().algorithmById(algorithm_id).create({})
    results, ok = algorithm.run(
        parameters, QgsProcessingContext(), QgsProcessingFeedback(), catchExceptions=False
    )
    assert ok, f"{algorithm_id} reported failure"
    return results


# -- RD-04's books, as rows ---------------------------------------------------


def book_rows(setups, line: str = "") -> list[list[str]]:
    """One row per reading: setup, station, kind, reading, distance, line."""
    rows = []
    for setup in setups:
        sights = [("BS", setup.backsight)] + [
            ("FS" if index == 0 else "IS", sight) for index, sight in enumerate(setup.foresights)
        ]
        for kind, sight in sights:
            rows.append(
                [
                    setup.id,
                    sight.station,
                    kind,
                    f"{sight.reading.value:.5f}",
                    f"{sight.distance_value:.2f}",
                    line,
                ]
            )
    return rows


def crossing_rows(near, far) -> list[list[str]]:
    """A reciprocal crossing, one setup from each bank."""
    return [
        [pair.setup_id, sight.station, kind, f"{sight.reading.value:.5f}", f"{sight.distance_value:.2f}", ""]
        for pair in (near, far)
        for kind, sight in (("BS", pair.near), ("FS", pair.far))
    ]


@pytest.fixture(scope="module")
def profiles(tmp_path_factory) -> str:
    """An RD-04 level profile library on disk."""
    from geocomp.core.instruments import ProfileLibrary

    library = ProfileLibrary()
    library.add_level(rd.profile())
    path = tmp_path_factory.mktemp("levels") / "profiles.json"
    path.write_text(json.dumps(library.to_dict()), encoding="utf-8")
    return str(path)


@pytest.fixture
def windows(geocomp_provider):
    """A window manager of its own, closed at the end."""
    from geocomp.gui.windows import WindowManager

    manager = WindowManager(None, None)
    yield manager
    manager.close_all()


def type_book(manager, rows: list[list[str]], profiles: str):
    """Type the rows into the levelling job's grid, as pasting them does, with RD-04's level."""
    job = manager.jobs.job("levelling")
    block = "\n".join(
        "\t".join([line, setup, station, kind, reading, "", "", distance])
        for setup, station, kind, reading, distance, line in rows
    )
    job.tables["field_book"].paste(0, "line", block)
    job.parameters("levelling_fieldbook")["PROFILES"] = profiles
    manager.jobs.touch("levelling")
    return job


def toolbox_setups(tmp_path: Path, rows: list[list[str]], profiles: str) -> str:
    """The toolbox's import of the same rows, written as a CSV file."""
    book = tmp_path / "book.csv"
    with open(book, "w", encoding="utf-8", newline="") as handle:
        csv.writer(handle).writerows([["setup", "point", "kind", "reading", "distance", "line"], *rows])
    mapping = tmp_path / "mapping.json"
    mapping.write_text(
        json.dumps(
            {
                "name": "tier3",
                "decimal_separator": ".",
                "columns": [
                    {"field": "setup", "column": "setup"},
                    {"field": "station", "column": "point"},
                    {"field": "sight", "column": "kind"},
                    {"field": "reading", "column": "reading"},
                    {"field": "distance", "column": "distance"},
                    {"field": "line", "column": "line"},
                ],
            }
        ),
        encoding="utf-8",
    )
    return run(
        "geocomp:levelling_import",
        {
            "BOOK": str(book),
            "MAPPING": str(mapping),
            "PROFILES": profiles,
            "OUTPUT_SETUPS": str(tmp_path / "setups.json"),
        },
    )["OUTPUT_SETUPS"]


def loop_rows() -> list[list[str]]:
    books, _truth = rd.loop(noise=0.0003)
    return [row for book in books for row in book_rows(book.line.setups, book.line.id)]


class TestLevelFieldBook:
    def test_a_typed_book_is_checked_by_the_import(self, windows, profiles):
        window = windows.open("levelling_fieldbook")
        from qgis.PyQt.QtWidgets import QApplication

        rows = book_rows(rd.balanced_line().line.setups, "rd04-line")
        QApplication.clipboard().setText(
            "\n".join("\t".join([r[5], r[0], r[1], r[2], r[3], "", "", r[4]]) for r in rows)
        )
        window.grid.view.setCurrentIndex(window.grid.model.index(0, 0))
        window.grid.view.paste()
        window.import_form.set_value("PROFILES", profiles)
        window.refresh()
        assert [step.state for step in window.steps] == ["done", "done", "ready", "locked"]
        assert window.notes_shown() == []
        calculate(window)
        assert window.results.figures() == {"Setups": "3", "Lines": "1", "Rejected rows": "0"}

    def test_a_cell_that_cannot_be_read_is_named_with_its_row_and_column(self, windows, profiles):
        job = type_book(windows, book_rows(rd.balanced_line().line.setups), profiles)
        job.tables["field_book"].set_cell(2, "sight", "X")
        window = windows.open("levelling_fieldbook")
        window.go_to("field_book")
        note, *others = window.notes_shown()
        assert note.text.startswith("Row 3, Sight (BS / FS / IS): 'X' is not a value")
        assert (note.row, note.column) == (2, "sight")
        # The row is kept from the reader, so its setup has no backsight, and the line breaks
        # where the setup is missing: both said as well.
        assert others[0].text == (
            "Setup S2 has 0 backsight(s) and 1 foresight(s); it needs exactly one backsight and "
            "at least one foresight."
        )
        assert others[1].text.startswith("Line line: The levelling line 'line' breaks at setup 'S3'")

    def test_a_reading_the_importer_refuses_is_named_by_its_row(self, windows, profiles):
        job = type_book(windows, book_rows(rd.balanced_line().line.setups), profiles)
        job.tables["field_book"].set_cell(3, "lower", "1.2")
        window = windows.open("levelling_fieldbook")
        window.refresh()
        window.go_to("field_book")
        rows = {note.row for note in window.notes_shown() if note.severity == "blocking"}
        assert 0 in rows, "a book with one wire is read as three: row 1 lacks its upper wire"

    def test_the_reading_heading_says_middle_wire_in_a_book_of_three(self, windows, profiles):
        from qgis.PyQt.QtCore import Qt

        job = type_book(windows, book_rows(rd.balanced_line().line.setups), profiles)
        window = windows.open("levelling_fieldbook")
        assert window.grid.model.headerData(4, Qt.Orientation.Horizontal) == "Reading (m)"
        job.tables["field_book"].set_cell(0, "upper", "1.5")
        window.grid.edited.emit()
        assert window.grid.model.headerData(4, Qt.Orientation.Horizontal) == "Middle wire (m)"


class TestMenuEqualsToolbox:
    def test_equal_sights_gives_the_toolboxs_reductions(self, windows, profiles, tmp_path):
        rows = book_rows(rd.balanced_line().line.setups, "rd04-line")
        type_book(windows, rows, profiles)
        window = windows.open("levelling_equal_sights")
        calculate(window)
        toolbox = run(
            "geocomp:levelling_equal_sights",
            {
                "SETUPS": toolbox_setups(tmp_path, rows, profiles),
                "PROFILES": profiles,
                "OUTPUT_REDUCTIONS": str(tmp_path / "reduced.json"),
            },
        )
        menu = json.loads(window.output_path("equal", "OUTPUT_REDUCTIONS").read_text("utf-8"))
        expected = json.loads(Path(toolbox["OUTPUT_REDUCTIONS"]).read_text(encoding="utf-8"))
        menu.pop("source", None)
        expected.pop("source", None)
        assert menu == expected
        (line,) = menu["lines"]
        assert line["height_difference"]["value"] == pytest.approx(
            rd.balanced_line().true_difference, abs=1e-9
        )
        assert window.results.figures()["Lines reduced"] == "1"

    def test_extreme_sights_gives_the_toolboxs_differences(self, windows, profiles, tmp_path):
        setup, _truth = rd.extreme_sights_setup()
        rows = book_rows((setup,))
        type_book(windows, rows, profiles)
        window = windows.open("levelling_extreme_sights")
        window.refresh()
        (note,) = window.notes_shown()
        assert note.text == "Setups with several foresights, as typed: RD04-extreme."
        calculate(window)
        toolbox = run(
            "geocomp:levelling_extreme_sights",
            {
                "SETUPS": toolbox_setups(tmp_path, rows, profiles),
                "PROFILES": profiles,
                "OUTPUT_DIFFERENCES": str(tmp_path / "differences.json"),
            },
        )
        scalars = window.scalars()
        assert scalars["extreme.DIFFERENCE_COUNT"] == toolbox["DIFFERENCE_COUNT"] == 3
        assert scalars["extreme.WORST_UNCERTAINTY"] == toolbox["WORST_UNCERTAINTY"]

    def test_equidistant_sights_gives_the_toolboxs_crossing(self, windows, profiles, tmp_path):
        near, far, truth = rd.reciprocal_crossing(refraction=0.012)
        rows = crossing_rows(near, far)
        type_book(windows, rows, profiles)
        window = windows.open("levelling_equidistant_sights")
        window.form.set_value("INFLATION", 2.0)
        calculate(window)
        toolbox = run(
            "geocomp:levelling_equidistant_sights",
            {
                "SETUPS": toolbox_setups(tmp_path, rows, profiles),
                "INFLATION": 2.0,
                "OUTPUT_DIFFERENCES": str(tmp_path / "crossing.json"),
            },
        )
        scalars = window.scalars()
        assert scalars["equidistant.CROSSING_COUNT"] == toolbox["CROSSING_COUNT"] == 1
        assert scalars["equidistant.WORST_DISCREPANCY"] == toolbox["WORST_DISCREPANCY"]
        crossing = json.loads(
            window.output_path("equidistant", "OUTPUT_DIFFERENCES").read_text("utf-8")
        )["crossings"][0]
        assert crossing["height_difference"]["value"] == pytest.approx(truth, abs=1e-6)

    def test_the_loop_closes_as_the_toolbox_closes_it(self, windows, profiles, tmp_path):
        rows = loop_rows()
        type_book(windows, rows, profiles)
        window = windows.open("levelling_closures")
        window.form.set_value("TOLERANCE_COEFFICIENT", 0.008)
        calculate(window)
        reduced = run(
            "geocomp:levelling_equal_sights",
            {
                "SETUPS": toolbox_setups(tmp_path, rows, profiles),
                "PROFILES": profiles,
                "OUTPUT_REDUCTIONS": str(tmp_path / "reduced.json"),
            },
        )
        toolbox = run(
            "geocomp:levelling_closures",
            {
                "REDUCTIONS": reduced["OUTPUT_REDUCTIONS"],
                "MODE": 0,
                "TOLERANCE_COEFFICIENT": 0.008,
                "OUTPUT_CLOSURES": str(tmp_path / "closure.json"),
            },
        )
        scalars = window.scalars()
        for name in ("MISCLOSURE", "PERMISSIBLE", "PASSED"):
            assert scalars[f"closures.{name}"] == toolbox[name], name
        assert window.results.figures()["Verdict"] == "Within tolerance"

    def test_the_network_adjusts_as_the_toolbox_adjusts_it(self, windows, profiles, tmp_path):
        rows = loop_rows()
        job = type_book(windows, rows, profiles)
        job.tables["benchmarks"].paste(0, "name", f"BM1\t{rd.HEIGHTS['BM1']:.3f}")
        window = windows.open("levelling_network")
        window.weighting_form.set_value("SIGMA_PER_KM", 0.0007)
        calculate(window)
        reduced = run(
            "geocomp:levelling_equal_sights",
            {
                "SETUPS": toolbox_setups(tmp_path, rows, profiles),
                "PROFILES": profiles,
                "OUTPUT_REDUCTIONS": str(tmp_path / "reduced.json"),
            },
        )
        toolbox = run(
            "geocomp:levelling_network",
            {
                "REDUCTIONS": reduced["OUTPUT_REDUCTIONS"],
                "BENCHMARKS": f"BM1={rd.HEIGHTS['BM1']:.3f}",
                "SIGMA_PER_KM": 0.0007,
                "OUTPUT_CSV": str(tmp_path / "heights.csv"),
            },
        )
        scalars = window.scalars()
        for name in ("DEGREES_OF_FREEDOM", "VARIANCE_FACTOR_APOSTERIORI", "OUTLIER_COUNT"):
            assert scalars[f"network.{name}"] == toolbox[name], name
        assert window.output_path("network", "OUTPUT_CSV").read_text("utf-8") == Path(
            toolbox["OUTPUT_CSV"]
        ).read_text(encoding="utf-8")
        assert window.results.figures()["Degrees of freedom"] == "1"


class TestTheNetworkWindow:
    def test_without_benchmarks_it_asks_for_one_or_a_free_network(self, windows, profiles):
        type_book(windows, loop_rows(), profiles)
        window = windows.open("levelling_network")
        window.refresh()
        assert window.step("benchmarks").problem().startswith("Give at least one benchmark")
        window.free_form.set_value("FREE", True)
        window.refresh()
        assert window.step("benchmarks").problem() == ""
        assert not window.benchmarks_grid.isEnabled()
        assert "BENCHMARKS" not in window.chain().steps[-1].parameters

    def test_the_orthometric_correction_is_sent_to_the_toolbox(self, windows, profiles):
        type_book(windows, loop_rows(), profiles)
        window = windows.open("levelling_network")
        window.free_form.set_value("FREE", True)
        window.options_form.set_value("ORTHOMETRIC", True)
        window.refresh()
        assert window.step("options").problem().startswith("The normal orthometric correction")
        assert window.step("calculate").state == "locked"


class TestTheBook:
    def test_a_book_with_a_rejected_row_is_not_computed_from(self, windows, profiles):
        job = type_book(windows, book_rows(rd.balanced_line().line.setups), profiles)
        job.tables["field_book"].set_cell(1, "reading", "")
        job.tables["field_book"].set_cell(1, "distance", "")
        job.tables["field_book"].set_cell(1, "station", "T1")
        window = windows.open("levelling_equal_sights")
        window.refresh()
        assert "row(s) of the field book are rejected" in window.banner.text()
        assert window.banner.text().endswith("Put it right in the Levelling field book window.")
        assert window.banner_button.text() == "Open the levelling field book"
        assert window.step("calculate").state == "locked"

    def test_the_two_techniques_keep_two_jobs(self, windows, profiles):
        type_book(windows, book_rows(rd.balanced_line().line.setups), profiles)
        level = windows.open("levelling_fieldbook")
        station = windows.open("totalstation_fieldbook")
        assert level.job is not station.job
        assert level.job.technique == "levelling" and station.job.technique == "total_station"
