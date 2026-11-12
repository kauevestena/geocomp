# SPDX-License-Identifier: GPL-2.0-or-later
"""The frame the menu's windows are built in (FR-010, FR-011, FR-016; ``specs/15`` section 7).

Four parts, each held here on its own: the guided, non-modal window and its
hand-back of the map; the grid a field book is typed into; the options form
made from an algorithm's own parameters; and the runner that runs a window's
algorithms in the background and refuses any it was not declared to run.
"""

from __future__ import annotations

import time

import pytest

pytestmark = pytest.mark.qgis


def _wait(runner, outcomes, seconds: float = 60.0) -> None:
    from qgis.PyQt.QtCore import QCoreApplication

    deadline = time.monotonic() + seconds
    while not outcomes and time.monotonic() < deadline:
        QCoreApplication.processEvents()
        time.sleep(0.005)


@pytest.fixture
def manager(geocomp_provider):
    from qgis.gui import QgsMapCanvas

    from geocomp.gui.windows import WindowManager

    canvas = QgsMapCanvas()
    windows = WindowManager(None, canvas)
    windows.canvas = canvas
    yield windows
    windows.close_all()


class TestTheFrame:
    def test_a_window_is_not_modal(self, manager):
        """The map stays usable beside it, which is what a sketch and a pick need."""
        from qgis.PyQt.QtCore import Qt

        window = manager.open("totalstation_traverse")
        assert not window.isModal()
        assert window.windowModality() == Qt.WindowModality.NonModal

    def test_one_of_each_is_open(self, manager):
        first = manager.open("totalstation_fieldbook")
        assert manager.open("totalstation_fieldbook") is first
        assert manager.open_windows == ("totalstation_fieldbook",)

    def test_a_locked_step_cannot_be_gone_to(self, manager):
        window = manager.open("totalstation_traverse")
        assert window.step("start").state == "locked"
        assert not window.go_to("start")
        assert window.current == 0
        assert not window.next_button.isEnabled()

    def test_the_steps_are_numbered_and_marked(self, manager):
        window = manager.open("totalstation_fieldbook")
        texts = [window.step_list.item(row).text() for row in range(window.step_list.count())]
        assert texts[0] == "1.  Job and instrument  ✓"
        assert texts[1].startswith("2.  Field book")

    def test_a_computation_window_sends_the_user_to_the_field_book(self, manager):
        window = manager.open("totalstation_preprocess")
        assert window.banner.text().startswith("The field book is empty.")
        assert window.banner_button.isVisibleTo(window)
        window.banner_button.click()
        assert "totalstation_fieldbook" in manager.open_windows

    def test_closing_gives_the_map_back_and_takes_the_sketch_off_it(self, manager):
        canvas = manager.canvas
        before_tool = canvas.mapTool()
        before_items = len(canvas.scene().items())
        job = manager.jobs.job("total_station")
        job.tables["points"].paste(0, "name", "A\t0\t0\t0\nB\t10\t10\t0")
        window = manager.open("totalstation_radiation")
        window.refresh()
        assert window.sketch.item_count == 2
        window.pick_point(lambda x, y: None)
        assert canvas.mapTool() is not before_tool
        window.close_now()
        assert canvas.mapTool() is before_tool
        assert len(canvas.scene().items()) == before_items
        assert manager.open_windows == ()

    def test_closing_the_last_window_asks_about_unsaved_changes(self, manager, monkeypatch):
        window = manager.open("totalstation_fieldbook")
        window.job.tables["field_book"].paste(0, "station", "A")
        window.touch()
        asked = []
        monkeypatch.setattr(window, "ask_to_save", lambda: asked.append(1) or "cancel")
        window.reject()
        assert asked and window.isVisible(), "cancelled, so still open"
        monkeypatch.setattr(window, "ask_to_save", lambda: "keep")
        window.reject()
        assert manager.open_windows == ()
        assert manager.jobs.job("total_station").tables["field_book"].cell(0, "station") == "A"

    def test_a_job_replaced_under_an_open_window_is_shown(self, manager, tmp_path):
        from geocomp.jobs import total_station as ts

        saved = ts.new_job("other")
        saved.tables["field_book"].paste(0, "station", "Q\t1.5\tR\tPD\t0 00 00\t90 00 00\t10")
        saved.save(tmp_path / "other")
        window = manager.open("totalstation_fieldbook")
        assert window.open_job_file(tmp_path / "other.gcjob")
        assert window.grid.model.table.cell(0, "station") == "Q"
        assert window.name_edit.text() == "other"
        assert window.current == 0


class TestTheGrid:
    @pytest.fixture
    def grid(self, qgis_app):
        from geocomp.gui.workbench.grid import GridWidget
        from geocomp.jobs import total_station as ts
        from geocomp.jobs.angles import AngleTyping
        from geocomp.jobs.tables import TypedTable

        return GridWidget(TypedTable(ts.BOOK_COLUMNS), lambda column: column.key, lambda: AngleTyping.DMS)

    def test_there_is_always_a_row_to_type_into(self, grid):
        model = grid.model
        assert model.rowCount() == 1
        assert model.setData(model.index(0, 0), "E1")
        assert model.table.row_count == 1 and model.rowCount() == 2

    def test_typing_nothing_in_the_spare_row_adds_nothing(self, grid):
        assert not grid.model.setData(grid.model.index(0, 0), "  ")
        assert grid.model.table.row_count == 0

    def test_a_new_row_carries_the_station_and_heights(self, grid):
        from qgis.PyQt.QtCore import Qt

        model = grid.model
        model.setData(model.index(0, 0), "E1")
        model.setData(model.index(0, 1), "1.5")
        model.setData(model.index(1, 2), "P2")
        assert model.data(model.index(1, 0), Qt.ItemDataRole.DisplayRole) == "E1"
        assert model.data(model.index(1, 1), Qt.ItemDataRole.DisplayRole) == "1.5"

    def test_an_unreadable_cell_is_tinted_and_says_why(self, grid):
        from qgis.PyQt.QtCore import Qt

        model = grid.model
        model.setData(model.index(0, 4), "87.5")
        assert model.data(model.index(0, 4), Qt.ItemDataRole.BackgroundRole) is not None
        assert "has decimals" in model.data(model.index(0, 4), Qt.ItemDataRole.ToolTipRole)
        assert model.data(model.index(0, 4), Qt.ItemDataRole.DisplayRole) == "87.5", "kept as typed"

    def test_enter_moves_along_the_row_then_down(self, grid):
        model, view = grid.model, grid.view
        model.setData(model.index(0, 0), "E1")
        view.setCurrentIndex(model.index(0, model.columnCount() - 1))
        view.advance()
        assert (view.currentIndex().row(), view.currentIndex().column()) == (1, 0)

    def test_paste_copy_undo_and_redo(self, grid):
        from qgis.PyQt.QtWidgets import QApplication

        QApplication.clipboard().setText("A\t1.5\tB\nA\t1.5\tC")
        grid.view.setCurrentIndex(grid.model.index(0, 0))
        grid.view.paste()
        assert grid.model.table.row_count == 2
        grid.view.selectAll()
        grid.view.copy()
        assert QApplication.clipboard().text().startswith("A\t1.5\tB")
        grid.undo_button.click()
        assert grid.model.table.row_count == 0
        grid.redo_button.click()
        assert grid.model.table.row_count == 2

    def test_rows_are_deleted_by_selection(self, grid):
        grid.model.paste(grid.model.index(0, 0), "A\nB\nC")
        grid.select_row(1)
        grid.remove_selected_rows()
        assert [grid.model.table.cell(r, "station") for r in range(2)] == ["A", "C"]


class TestTheParameterForm:
    def _form(self, names, stored, **options):
        from geocomp.gui.workbench.parameters import ParameterForm

        return ParameterForm("geocomp:totalstation_traverse", names, lambda: stored, **options)

    def test_the_labels_and_defaults_are_the_algorithms(self, geocomp_provider):
        stored: dict = {}
        form = self._form(("START_AZIMUTH", "KIND"), stored)
        assert form.label("START_AZIMUTH") == "Start azimuth (°)"
        assert form.default("KIND") == 0
        assert form.names == ("START_AZIMUTH", "KIND")

    def test_only_what_is_changed_is_kept(self, geocomp_provider):
        stored: dict = {}
        form = self._form(("START_EASTING",), stored)
        form.set_value("START_EASTING", 1000.0)
        assert stored == {"START_EASTING": 1000.0}
        form.set_value("START_EASTING", 0.0)
        assert stored == {}, "set back to the default, the choice is the algorithm's again"

    def test_a_number_typed_is_stored_with_either_decimal_mark(self, geocomp_provider):
        stored: dict = {}
        form = self._form(("START_NORTHING",), stored)
        editor = form.editor("START_NORTHING")
        assert editor.text() == "0", "the algorithm's default, shown"
        editor.setText("5000,25")
        editor.textEdited.emit("5000,25")
        assert stored == {"START_NORTHING": 5000.25}

    def test_a_number_out_of_range_is_marked_and_not_stored(self, geocomp_provider):
        from geocomp.core.settings_def import MODE_ADVANCED
        from geocomp.services.settings_service import settings

        stored: dict = {}
        with settings.run_overrides({"interface.mode": MODE_ADVANCED}):
            form = self._form(("ANGULAR_TOLERANCE",), stored)
        editor = form.editor("ANGULAR_TOLERANCE")
        editor.setText("9")
        editor.textEdited.emit("9")
        assert stored == {}
        assert editor.toolTip() == "Between 0 and 5."
        editor.setText("abc")
        editor.textEdited.emit("abc")
        assert editor.toolTip() == "Not a number."

    def test_an_optional_number_left_empty_is_not_set(self, geocomp_provider):
        stored: dict = {"CLOSE_EASTING": 10.0}
        form = self._form(("CLOSE_EASTING",), stored, always=("CLOSE_EASTING",))
        editor = form.editor("CLOSE_EASTING")
        assert editor.text() == "10"
        editor.setText("")
        editor.textEdited.emit("")
        assert stored == {}

    def test_a_choice_is_stored_by_its_index(self, geocomp_provider):
        stored: dict = {}
        form = self._form(("KIND",), stored)
        combo = form.widget("KIND")
        assert combo.count() == 3 and combo.currentIndex() == 0
        combo.setCurrentIndex(2)
        combo.activated.emit(2)
        assert stored == {"KIND": 2}

    def test_a_file_is_typed_or_chosen(self, geocomp_provider):
        from geocomp.gui.workbench.parameters import ParameterForm

        stored: dict = {}
        form = ParameterForm(
            "geocomp:totalstation_import_fieldbook", ("PROFILES",), lambda: stored
        )
        editor = form.editor("PROFILES")
        editor.setText("/data/profiles.json")
        editor.textEdited.emit("/data/profiles.json")
        assert stored == {"PROFILES": "/data/profiles.json"}

    def test_basic_mode_hides_what_the_algorithm_hides(self, geocomp_provider):
        from geocomp.core.settings_def import MODE_ADVANCED, MODE_BASIC
        from geocomp.services.settings_service import settings

        with settings.run_overrides({"interface.mode": MODE_BASIC}):
            basic = self._form(("KIND", "ANGULAR_TOLERANCE"), {})
        with settings.run_overrides({"interface.mode": MODE_ADVANCED}):
            advanced = self._form(("KIND", "ANGULAR_TOLERANCE"), {})
        assert basic.names == ("KIND",)
        assert advanced.names == ("KIND", "ANGULAR_TOLERANCE")

    def test_a_window_may_show_what_it_cannot_do_without(self, geocomp_provider):
        from geocomp.core.settings_def import MODE_BASIC
        from geocomp.services.settings_service import settings

        with settings.run_overrides({"interface.mode": MODE_BASIC}):
            form = self._form(("CLOSE_EASTING",), {}, always=("CLOSE_EASTING",))
        assert form.names == ("CLOSE_EASTING",)

    def test_a_changed_global_setting_changes_the_default(self, geocomp_provider):
        from geocomp.services.settings_service import settings

        with settings.run_overrides({"total_station.traverse_relative_precision": 20000}):
            form = self._form(("RELATIVE_LIMIT",), {})
        assert form.default("RELATIVE_LIMIT") == 20000


class TestTheRunner:
    def test_it_refuses_an_algorithm_its_window_does_not_declare(self, geocomp_provider, tmp_path):
        from geocomp.jobs.chains import Chain, ChainStep
        from geocomp.services.chain_runner import ChainRunner

        runner = ChainRunner(["geocomp:totalstation_import_fieldbook"])
        chain = Chain((ChainStep("adjust", "geocomp:analysis_network_adjust"),))
        with pytest.raises(ValueError, match="does not declare"):
            runner.run(chain, tmp_path)

    def test_a_failure_is_said_in_the_algorithms_own_words(self, geocomp_provider, tmp_path):
        from geocomp.jobs.chains import Chain, ChainStep, InputFile
        from geocomp.services.chain_runner import ChainRunner

        runner = ChainRunner(["geocomp:totalstation_import_fieldbook"])
        outcomes: list = []
        runner.finished.connect(outcomes.append)
        runner.run(
            Chain(
                (
                    ChainStep(
                        "import",
                        "geocomp:totalstation_import_fieldbook",
                        {"SOURCE": InputFile("empty.csv", "")},
                        {"OUTPUT_READINGS": "readings.json"},
                    ),
                )
            ),
            tmp_path,
        )
        _wait(runner, outcomes)
        (outcome,) = outcomes
        assert not outcome.succeeded and outcome.failed_step == "import"
        assert "is empty" in outcome.error
        assert not runner.is_running

    def test_a_previous_runs_output_is_not_taken_for_this_ones(self, geocomp_provider, tmp_path):
        from geocomp.jobs.chains import Chain, ChainStep, InputFile
        from geocomp.services.chain_runner import ChainRunner

        stale = tmp_path / "import" / "readings.json"
        stale.parent.mkdir()
        stale.write_text("{}", encoding="utf-8")
        runner = ChainRunner(["geocomp:totalstation_import_fieldbook"])
        outcomes: list = []
        runner.finished.connect(outcomes.append)
        runner.run(
            Chain(
                (
                    ChainStep(
                        "import",
                        "geocomp:totalstation_import_fieldbook",
                        {"SOURCE": InputFile("empty.csv", "")},
                        {"OUTPUT_READINGS": "readings.json"},
                    ),
                )
            ),
            tmp_path,
        )
        _wait(runner, outcomes)
        assert not stale.exists()
        assert outcomes[0].output("import", "OUTPUT_READINGS") is None
