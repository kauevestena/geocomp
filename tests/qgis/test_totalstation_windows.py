# SPDX-License-Identifier: GPL-2.0-or-later
"""The Total Station windows of the menu (ROADMAP P14a; FR-010 to FR-017).

**Menu equals toolbox** is what these hold. A field book typed into *Field
book* and computed in *Generalised pre-processing*, *Traverse* or *3D
radiation* gives what the same algorithms give when run from the toolbox --
because the windows run those algorithms, on the typed book written as the file
the import reads (ADR-0010). RD-01 is typed as its surveyor recorded it, and its
two known defects must surface in the window as they do in the toolbox; the
synthetic survey of ``tests/synthetic.py``, which has known points, is typed to
traverse and radiate from.
"""

from __future__ import annotations

import json
import math
import time
from pathlib import Path

import pytest

from tests import reference_rd01 as rd01
from tests import synthetic as syn

pytestmark = pytest.mark.qgis

#: RD-01's stochastic model, as the toolbox tests give it to the import.
RD01_IMPORT = {
    "SIGMA_DIRECTION": rd01.SIGMA_ANGLE,
    "SIGMA_ZENITH": rd01.SIGMA_ANGLE,
    "SIGMA_DISTANCE": 0.002,
}
NO_ATMOSPHERE = {"APPLY_ATMOSPHERIC": False}


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


def rd01_block() -> str:
    """RD-01 as it is typed: one line per pointing, angles in degrees, minutes and seconds."""
    import csv

    with open(rd01.RAW, encoding="utf-8") as handle:
        return "\n".join(
            "\t".join(
                [
                    row["E"],
                    row["hi"],
                    row["R"] if row["vis"] == "R" else row["V"],
                    row["pos"],
                    f"{row['HG']} {row['HM']} {row['HS']}",
                    f"{row['VG']} {row['VM']} {row['VS']}",
                    row["D"],
                    row["hs"],
                ]
            )
            for row in csv.DictReader(handle)
        )


def synthetic_block() -> str:
    """The synthetic survey as it would be typed: both faces of every pointing."""
    from geocomp.jobs.angles import AngleTyping, format_typed_angle

    def angle(radians: float) -> str:
        return format_typed_angle(radians % math.tau, AngleTyping.DMS, 6)

    lines = []
    for station, targets in syn.SETUPS.items():
        for target in targets:
            reading = (syn.azimuth(station, target) - syn.ORIENTATIONS[station]) % math.tau
            zenith = syn.zenith(station, target)
            distance = f"{syn.slope_distance(station, target):.6f}"
            for face, horizontal, vertical in (
                ("PD", reading, zenith),
                ("PI", reading + math.pi, math.tau - zenith),
            ):
                lines.append(
                    "\t".join(
                        [station, "1.5", target, face, angle(horizontal), angle(vertical), distance, "1.5"]
                    )
                )
    return "\n".join(lines)


@pytest.fixture
def windows(geocomp_provider, tmp_path):
    """A window manager of its own, with a map canvas, closed at the end."""
    from qgis.gui import QgsMapCanvas

    from geocomp.gui.windows import WindowManager

    canvas = QgsMapCanvas()
    manager = WindowManager(None, canvas)
    manager.canvas = canvas
    yield manager
    manager.close_all()


def type_book(manager, block: str, *, import_options: dict, preprocess: dict | None = None):
    """Type a field book into the job, as pasting it into the grid does."""
    job = manager.jobs.job("total_station")
    job.tables["field_book"].paste(0, "station", block)
    job.parameters("totalstation_fieldbook").update(import_options)
    job.parameters("totalstation_preprocess").update(preprocess or {})
    manager.jobs.touch("total_station")
    return job


class TestFieldBook:
    def test_a_typed_book_is_checked_by_the_import(self, windows):
        window = windows.open("totalstation_fieldbook")
        window.grid.view.setCurrentIndex(window.grid.model.index(0, 0))
        from qgis.PyQt.QtWidgets import QApplication

        QApplication.clipboard().setText(rd01_block())
        window.grid.view.paste()
        window.job.parameters("totalstation_fieldbook").update(RD01_IMPORT)
        window.refresh()
        assert [step.state for step in window.steps] == ["done", "done", "ready", "locked"]
        assert window.notes_shown() == []
        calculate(window)
        assert window.results.figures() == {
            "Records read": "12",
            "Setups": "3",
            "Rejected records": "0",
        }
        assert [step.state for step in window.steps][2:] == ["done", "done"]

    def test_a_cell_that_cannot_be_read_is_named_with_its_row_and_column(self, windows):
        type_book(windows, rd01_block(), import_options=RD01_IMPORT)
        window = windows.open("totalstation_fieldbook")
        window.job.tables["field_book"].set_cell(2, "horizontal", "199.1108")
        window.refresh()
        window.go_to("field_book")
        (note,) = window.notes_shown()
        assert note.text.startswith("Row 3, Hz (D M S): '199.1108' has decimals")
        assert (note.row, note.column) == (2, "horizontal")
        assert window.step("calculate").state == "locked"
        window.note_chosen(note)
        assert window.grid.view.currentIndex().row() == 2

    def test_a_row_the_importer_rejects_is_named_as_the_grid_numbers_it(self, windows):
        type_book(windows, rd01_block(), import_options=RD01_IMPORT)
        window = windows.open("totalstation_fieldbook")
        window.job.tables["field_book"].set_cell(4, "target", "")
        window.refresh()
        window.go_to("field_book")
        notes = window.notes_shown()
        assert notes[0].severity == "blocking"
        assert notes[0].row == 4
        assert notes[0].text.startswith("Row 5")

    def test_a_readings_document_from_the_toolbox_opens_into_the_grid(self, windows, tmp_path):
        imported = run(
            "geocomp:totalstation_import_fieldbook",
            {"SOURCE": str(rd01.RAW), **RD01_IMPORT, "OUTPUT_READINGS": str(tmp_path / "r.json")},
        )
        window = windows.open("totalstation_fieldbook")
        assert window.open_readings_file(imported["OUTPUT_READINGS"])
        table = window.job.tables["field_book"]
        assert table.row_count == 12
        assert (table.cell(2, "station"), table.cell(2, "target"), table.cell(2, "face")) == (
            "1",
            "2",
            "PD",
        )
        assert table.cell(2, "horizontal") == "199 06 38.0000"

    def test_a_file_that_is_not_a_readings_document_is_refused_in_words(self, windows, tmp_path, monkeypatch):
        other = tmp_path / "other.json"
        other.write_text('{"kind": "geocomp.reductions"}', encoding="utf-8")
        window = windows.open("totalstation_fieldbook")
        said = []
        monkeypatch.setattr(window, "say", said.append)
        assert not window.open_readings_file(other)
        assert said == [
            f"'{other}' is not a GeoComp readings document. Choose the file Import field book wrote."
        ]

    def test_the_headings_state_the_convention_and_a_change_rereads_the_cells(self, windows):
        from geocomp.jobs.angles import AngleTyping

        type_book(windows, "1\t1.5\t2\tPD\t87.3115\t90.0000\t10", import_options=RD01_IMPORT)
        window = windows.open("totalstation_fieldbook")
        model = window.grid.model
        from qgis.PyQt.QtCore import Qt

        heading = model.headerData(4, Qt.Orientation.Horizontal)
        assert heading == "Hz (D M S)"
        assert window.book.problems()
        window.typing_combo.setCurrentIndex(window.typing_combo.findData(AngleTyping.DMS_PACKED.value))
        assert model.headerData(4, Qt.Orientation.Horizontal) == "Hz (DDD.MMSS)"
        assert not window.book.problems()
        assert window.job.tables["field_book"].cell(0, "horizontal") == "87.3115"


class TestMenuEqualsToolbox:
    """RD-01 typed and pre-processed in the windows, against the toolbox on its CSV."""

    @pytest.fixture
    def preprocessed(self, windows):
        type_book(windows, rd01_block(), import_options=RD01_IMPORT, preprocess=NO_ATMOSPHERE)
        window = windows.open("totalstation_preprocess")
        calculate(window)
        return window

    def test_the_reductions_are_the_toolboxs_to_the_last_bit(self, preprocessed, tmp_path):
        readings = run(
            "geocomp:totalstation_import_fieldbook",
            {"SOURCE": str(rd01.RAW), **RD01_IMPORT, "OUTPUT_READINGS": str(tmp_path / "r.json")},
        )
        toolbox = run(
            "geocomp:totalstation_preprocess",
            {
                "READINGS": readings["OUTPUT_READINGS"],
                **NO_ATMOSPHERE,
                "OUTPUT_REDUCED": str(tmp_path / "reduced.json"),
            },
        )
        menu = json.loads(preprocessed.output_path("preprocess", "OUTPUT_REDUCED").read_text("utf-8"))
        expected = json.loads(Path(toolbox["OUTPUT_REDUCED"]).read_text(encoding="utf-8"))
        # Everything but the name of the file it came from.
        assert menu.pop("source", None) == "fieldbook.csv"
        expected.pop("source", None)
        assert menu == expected

    def test_both_known_defects_of_rd01_surface_in_the_window(self, preprocessed):
        """The 1.000 m face-pair difference is blocked, and 3,1,2 is reduced to
        199.110139 degrees, not the prototype's 19.110139."""
        assert preprocessed.results.figures() == {
            "Pointings reduced": "6",
            "Usable pointings": "5",
            "Blocking findings": "1",
        }
        document = json.loads(
            preprocessed.output_path("preprocess", "OUTPUT_REDUCED").read_text("utf-8")
        )
        (setup,) = [setup for setup in document["setups"] if setup["station"] == "1"]
        (pointing,) = [p for p in setup["pointings"] if p["target"] == "2"]
        assert math.degrees(pointing["horizontal"]["value"]) % 360.0 == pytest.approx(
            rd01.CORRECT_DEGREES, abs=1e-9
        )

    def test_the_window_shows_the_algorithms_own_report(self, preprocessed):
        text = preprocessed.results.report.toHtml()
        assert "Generated by GeoComp" in text

    def test_the_equivalent_toolbox_run_is_shown(self, preprocessed):
        shown = preprocessed.run_page.equivalent.toPlainText()
        assert 'processing.run("geocomp:totalstation_import_fieldbook"' in shown
        assert 'processing.run("geocomp:totalstation_preprocess"' in shown

    def test_an_edit_puts_the_result_out_of_date_and_never_shows_it_as_current(self, preprocessed):
        preprocessed.run_page.automatic.setChecked(False)
        preprocessed.job.tables["field_book"].set_cell(0, "distance", "11.509")
        preprocessed.touch()
        preprocessed.refresh()
        assert preprocessed.step("calculate").state == "stale"
        assert preprocessed.step("results").state == "stale"
        assert preprocessed.results.notice.isVisibleTo(preprocessed.results)

    def test_a_book_with_a_rejected_row_is_not_computed_from(self, windows):
        type_book(windows, rd01_block(), import_options=RD01_IMPORT)
        windows.jobs.job("total_station").tables["field_book"].set_cell(4, "target", "")
        window = windows.open("totalstation_preprocess")
        window.refresh()
        assert "1 row(s) of the field book are rejected" in window.banner.text()
        assert window.step("calculate").state == "locked"
        assert not window.calculate()


class TestTraverse:
    @pytest.fixture
    def traverse(self, windows):
        type_book(windows, synthetic_block(), import_options={}, preprocess=NO_ATMOSPHERE)
        window = windows.open("totalstation_traverse")
        window.set_route(list(syn.ROUTE))
        window.set_backsight(syn.BACKSIGHT)
        window.start_form.set_value("START_EASTING", syn.COORDINATES["A"][0])
        window.start_form.set_value("START_NORTHING", syn.COORDINATES["A"][1])
        window.start_form.set_value("START_AZIMUTH", math.degrees(syn.start_azimuth()))
        calculate(window)
        return window

    def test_the_route_is_chosen_among_the_books_stations(self, windows):
        type_book(windows, synthetic_block(), import_options={})
        window = windows.open("totalstation_traverse")
        offered = [window.available.item(i).text() for i in range(window.available.count())]
        assert offered[:6] == ["A", "B", "C", "D", "R", "L"]
        assert window.step("route").problem().startswith("Add at least two stations")
        assert window.step("start").state == "locked"

    def test_the_loop_closes_on_itself(self, traverse):
        scalars = traverse.scalars()
        assert abs(scalars["traverse.ANGULAR_MISCLOSURE"]) < 1e-6
        assert scalars["traverse.LINEAR_MISCLOSURE"] < 1e-4
        assert scalars["traverse.WITHIN_TOLERANCE"] is True
        assert traverse.results.figures()["Within tolerance"] == "Yes"

    def test_every_station_comes_back_where_it_was_surveyed(self, traverse):
        for name, (easting, northing, _up) in traverse.coordinates().items():
            assert easting == pytest.approx(syn.COORDINATES[name][0], abs=1e-4)
            assert northing == pytest.approx(syn.COORDINATES[name][1], abs=1e-4)

    def test_the_toolbox_on_the_same_book_gives_the_same_figures(self, traverse, tmp_path):
        folder = traverse.results_folder()
        readings = run(
            "geocomp:totalstation_import_fieldbook",
            {
                "SOURCE": str(folder / "import" / "fieldbook.csv"),
                "MAPPING": str(folder / "import" / "mapping.json"),
                "OUTPUT_READINGS": str(tmp_path / "readings.json"),
            },
        )
        reduced = run(
            "geocomp:totalstation_preprocess",
            {
                "READINGS": readings["OUTPUT_READINGS"],
                **NO_ATMOSPHERE,
                "OUTPUT_REDUCED": str(tmp_path / "reduced.json"),
            },
        )
        toolbox = run(
            "geocomp:totalstation_traverse",
            {
                "REDUCTIONS": reduced["OUTPUT_REDUCED"],
                "ROUTE": ",".join(syn.ROUTE),
                "BACKSIGHT": syn.BACKSIGHT,
                "START_EASTING": syn.COORDINATES["A"][0],
                "START_NORTHING": syn.COORDINATES["A"][1],
                "START_AZIMUTH": math.degrees(syn.start_azimuth()),
                "OUTPUT_COORDINATES": str(tmp_path / "coordinates.json"),
            },
        )
        scalars = traverse.scalars()
        for name in ("ANGULAR_MISCLOSURE", "LINEAR_MISCLOSURE", "RELATIVE_PRECISION", "WITHIN_TOLERANCE"):
            assert scalars[f"traverse.{name}"] == toolbox[name], name
        assert json.loads(Path(toolbox["OUTPUT_COORDINATES"]).read_text("utf-8")) == {
            name: list(values) for name, values in traverse.coordinates().items()
        }

    def test_the_traverse_is_drawn_and_its_stations_become_known_points(self, traverse):
        assert traverse.sketch.item_count >= len(syn.ROUTE)
        assert traverse.use_as_known_stations() == 4
        assert traverse.book.known_stations().keys() == {"A", "B", "C", "D"}

    def test_a_run_that_fails_is_not_retried_by_itself(self, traverse):
        """Automatic recalculation repeats a run only for inputs that changed
        since one failed; otherwise a failing chain would run every second."""
        traverse.set_route(["A", "B", "Z", "A"])
        traverse.refresh()
        assert traverse.calculate()
        wait(traverse)
        assert not traverse.last_outcome.succeeded
        assert "Z" in traverse.last_outcome.error
        traverse.refresh()
        assert not traverse._recalculate_timer.isActive()
        traverse.set_route(list(syn.ROUTE))
        traverse.refresh()
        # The failed run wrote in a folder of its own, and the last good result is untouched.
        assert traverse.step("calculate").state == "done", "the earlier result is current again"
        assert traverse.results.figures()["Within tolerance"] == "Yes"

    def test_a_connected_traverse_asks_for_where_it_arrives(self, traverse):
        traverse.kind_form.set_value("KIND", 1)
        traverse.refresh()
        assert traverse.step("start").problem().startswith("A connected traverse")
        assert traverse.step("options").state == "locked"


class TestRadiation:
    @pytest.fixture
    def radiation(self, windows):
        job = type_book(windows, synthetic_block(), import_options={}, preprocess=NO_ATMOSPHERE)
        job.tables["points"].paste(
            0,
            "name",
            "\n".join(
                "\t".join([name, *(f"{value:.4f}" for value in syn.COORDINATES[name])])
                for name in syn.CONTROL
            ),
        )
        window = windows.open("totalstation_radiation")
        window.form.set_value("INSTRUMENT_HEIGHT", syn.INSTRUMENT_HEIGHT)
        window.form.set_value("TARGET_HEIGHT", syn.TARGET_HEIGHT)
        calculate(window)
        return window

    def test_the_detail_points_are_where_they_were_surveyed(self, radiation):
        points = {point["name"]: point for point in radiation.radiated()}
        assert points.keys() == {"P1", "P2"}
        for name, point in points.items():
            assert point["easting"] == pytest.approx(syn.COORDINATES[name][0], abs=1e-4)
            assert point["northing"] == pytest.approx(syn.COORDINATES[name][1], abs=1e-4)
            assert point["origin"] == "A"
        assert radiation.results.figures()["Points radiated"] == "2"

    def test_the_points_can_be_added_to_the_project_as_a_layer(self, radiation):
        """FR-017: what the user wants kept is added deliberately, with the
        algorithm's own standard deviations."""
        from qgis.core import QgsProject

        project = QgsProject.instance()
        before = set(project.mapLayers())
        radiation.add_to_map()
        (added,) = [project.mapLayer(i) for i in set(project.mapLayers()) - before]
        try:
            features = {feature["name"]: feature for feature in added.getFeatures()}
            assert features.keys() == {"P1", "P2"}
            assert features["P1"]["sigma_e"] > 0.0
            assert features["P1"].geometry().constGet().z() == pytest.approx(
                syn.COORDINATES["P1"][2], abs=1e-3
            )
        finally:
            project.removeMapLayer(added.id())

    def test_the_rays_are_drawn(self, radiation):
        # Four known points, two radiated ones, and a ray to each.
        assert radiation.sketch.item_count == 4 + 2 + 2

    def test_without_a_known_occupied_station_it_says_which_to_give(self, windows):
        job = type_book(windows, synthetic_block(), import_options={})
        job.tables["points"].paste(0, "name", "P1\t1\t2\t3")
        window = windows.open("totalstation_radiation")
        window.refresh()
        assert window.step("stations").problem().startswith(
            "None of the known points is a station the field book occupies"
        )

    def test_a_point_picked_on_the_map_fills_the_current_row(self, windows):
        """FR-014: the canvas is lent for one click and given back after it."""
        type_book(windows, synthetic_block(), import_options={})
        window = windows.open("totalstation_radiation")
        canvas = windows.canvas
        before = canvas.mapTool()
        window.points_grid.select_row(0)
        window.pick_station()
        assert window.is_picking and canvas.mapTool() is window._pick_tool
        window._pick_tool.picked.emit(1234.5, 6789.25)
        table = window.job.tables["points"]
        assert (table.cell(0, "easting"), table.cell(0, "northing")) == ("1234.5000", "6789.2500")
        assert not window.is_picking
        assert canvas.mapTool() is before


class TestTheJob:
    def test_a_saved_job_reopens_with_its_results_current(self, windows, tmp_path):
        from geocomp.gui.windows import WindowManager
        from geocomp.services.jobs_service import JobsService

        type_book(windows, rd01_block(), import_options=RD01_IMPORT, preprocess=NO_ATMOSPHERE)
        window = windows.open("totalstation_preprocess")
        assert window.save_job_to(tmp_path / "rd01")
        calculate(window)
        results = tmp_path / "rd01_results" / "totalstation_preprocess"
        assert (results / "preprocess" / "reduced.json").is_file()
        assert windows.jobs.save("total_station") == tmp_path / "rd01.gcjob"

        other = WindowManager(None, None, JobsService())
        try:
            other.jobs.open("total_station", tmp_path / "rd01.gcjob")
            reopened = other.open("totalstation_preprocess")
            assert reopened.step("calculate").state == "done"
            assert reopened.results.figures() == window.results.figures()
        finally:
            other.close_all()

    def test_the_project_remembers_the_job(self, windows, tmp_path):
        windows.jobs.save("total_station", tmp_path / "remembered.gcjob")
        assert windows.jobs.remembered("total_station") == tmp_path / "remembered.gcjob"

    def test_one_book_is_shared_by_every_window(self, windows):
        book = windows.open("totalstation_fieldbook")
        traverse = windows.open("totalstation_traverse")
        book.grid.model.paste(book.grid.model.index(0, 0), "Z9\t1.5\tY8\tPD\t0 00 00\t90 00 00\t10")
        traverse.refresh()
        assert "Z9" in [traverse.available.item(i).text() for i in range(traverse.available.count())]

    def test_another_technique_s_job_is_refused_in_words(self, windows, tmp_path, monkeypatch):
        other = tmp_path / "level.gcjob"
        other.write_text(
            json.dumps({"kind": "geocomp.job", "version": 1, "technique": "level"}), encoding="utf-8"
        )
        window = windows.open("totalstation_fieldbook")
        said = []
        monkeypatch.setattr(window, "say", said.append)
        assert not window.open_job_file(other)
        assert said and "is the job of another technique" in said[0]
