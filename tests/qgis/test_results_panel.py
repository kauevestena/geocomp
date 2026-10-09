# SPDX-License-Identifier: GPL-2.0-or-later
"""The results panel (specs/15 section 4; phase P12b).

*Run history with status, statistics summaries, per-observation results with
sorting and filtering, and links from a table row to the corresponding map
feature. Selecting a station shows its time series when the project has
multiple epochs.* Each clause is a test here; what the panel says is tested
without QGIS in ``tests/test_results_view.py``.
"""

from __future__ import annotations

import dataclasses
import json

import pytest

from tests.qgis.conftest import settle
from tests.test_project_store import reference  # noqa: F401 -- the fixture
from tests.test_results_view import VARIED

pytestmark = pytest.mark.qgis


@pytest.fixture
def project(qgis_app):
    from qgis.core import QgsProject

    instance = QgsProject.instance()
    instance.clear()
    yield instance
    instance.clear()


@pytest.fixture
def solution(reference):  # noqa: F811 -- the imported fixture
    _project, adjusted, _network = reference
    return dataclasses.replace(adjusted, observation_results=VARIED)


@pytest.fixture
def solution_file(tmp_path, solution):
    path = tmp_path / "solution.json"
    path.write_text(json.dumps(solution.to_dict()), encoding="utf-8")
    return str(path)


class Zoom:
    def __init__(self):
        self.layers = []

    def __call__(self, layer):
        self.layers.append(layer.name())


@pytest.fixture
def panel(qgis_app, project):
    from geocomp.gui.results_panel import ResultsPanel

    zoom = Zoom()
    widget = ResultsPanel(zoom=zoom)
    widget.zoom = zoom
    yield widget
    widget.deleteLater()


def _residual_layer(solution_path: str, ids):
    """A residual layer as an adjustment writes it: the result kind and the run named."""
    from qgis.core import QgsFeature, QgsGeometry, QgsPointXY, QgsVectorLayer

    from geocomp.algorithms.layer_outputs import RESULT_LAYER_PROPERTY, SOLUTION_PROPERTY

    layer = QgsVectorLayer(
        "LineString?crs=EPSG:31982&field=observation:string&field=decision:string",
        "Residuals",
        "memory",
    )
    features = []
    for index, observation in enumerate(ids):
        feature = QgsFeature(layer.fields())
        feature.setGeometry(
            QgsGeometry.fromPolylineXY([QgsPointXY(index, 0.0), QgsPointXY(index, 5.0)])
        )
        feature.setAttributes([observation, ""])
        features.append(feature)
    layer.dataProvider().addFeatures(features)
    layer.setCustomProperty(RESULT_LAYER_PROPERTY, "residuals")
    layer.setCustomProperty(SOLUTION_PROPERTY, solution_path)
    return layer


class TestTheRunHistory:
    def test_a_run_is_listed_with_its_status_and_shown(self, panel, solution):
        panel.add_solution(solution, "here")
        assert panel.run_table.rowCount() == 1
        assert panel.run_table.item(0, 0).text() == solution.id
        expected = "passed" if solution.statistics.global_test.passed else "FAILED"
        assert panel.run_table.item(0, 3).text() == expected
        assert panel.current.solution is solution
        assert panel.statistics.rowCount() > 10
        assert panel.observation_model.rowCount() == len(VARIED)

    def test_the_same_run_twice_is_one_row(self, panel, solution):
        panel.add_solution(solution, "here")
        panel.add_solution(solution, "here")
        assert panel.run_table.rowCount() == 1

    def test_a_run_arrives_with_its_layers(self, panel, project, solution_file, solution):
        from geocomp.gui.results_panel import attach_to_project, detach_from_project

        attach_to_project(panel)
        try:
            project.addMapLayer(_residual_layer(solution_file, ["passes"]))
            project.addMapLayer(_residual_layer(solution_file, ["blunder"]))
            # NFR-004: read off the GUI thread, so listed when the read is done,
            # and read once although two layers name it.
            assert panel.busy
            assert len(panel._tasks) == 1
            settle(panel)
        finally:
            detach_from_project(panel)
        assert [run.source for run in panel.runs] == [solution_file]

    def test_a_project_store_lists_every_run_in_it(self, panel, tmp_path, reference):  # noqa: F811
        from geocomp.io.store import open_store

        project_, solution, _network = reference
        path = tmp_path / "project.gpkg"
        with open_store(path, create=True) as store:
            store.write(project_)
            store.write_solution(solution)
        assert panel.open_store(str(path)) == 1
        assert panel.runs[0].solution.id == solution.id

    def test_an_unreadable_solution_is_said_not_listed(self, panel, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("{not json", encoding="utf-8")
        assert panel.add_solution_file(str(bad)) is None
        assert panel.run_table.rowCount() == 0
        assert str(bad) in panel.status.text()

    def test_a_refused_solution_is_said_in_words(self, panel, tmp_path, solution, geocomp_provider):
        """Found by P12c-7: the panel showed the refusal's developer diagnostic,
        code and context, rather than its sentence. The provider registers the
        templates, and the plugin loads it before it builds the panel."""
        payload = solution.to_dict()
        payload["crs"] = ""
        refused = tmp_path / "no_crs.json"
        refused.write_text(json.dumps(payload), encoding="utf-8")
        assert panel.add_solution_file(str(refused)) is None
        text = panel.status.text()
        assert "has no coordinate reference system" in text
        assert "solution_without_crs" not in text


class TestNothingSlowOnTheGuiThread:
    """NFR-004. A 625-station solution with its covariance is 37 MB and took a
    second to read; until P12c-15 the panel read it on the GUI thread whenever a
    layer named it or a button opened it."""

    def test_the_open_button_reads_on_a_worker_thread(self, panel, solution_file, monkeypatch):
        import threading

        from geocomp.gui import results_panel

        threads = []
        reader = results_panel.read_solution

        def recording(path):
            threads.append(threading.current_thread())
            return reader(path)

        monkeypatch.setattr(results_panel, "read_solution", recording)
        monkeypatch.setattr(
            results_panel.QFileDialog, "getOpenFileName", lambda *args: (solution_file, "")
        )
        panel._open_solution()
        assert panel.busy
        assert panel.runs == []  # nothing listed until the read is done
        settle(panel)
        assert threads and threads[0] is not threading.main_thread()
        assert [run.source for run in panel.runs] == [solution_file]

    def test_an_unreadable_file_is_said_when_the_read_fails(self, panel, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("{", encoding="utf-8")
        panel.load_solution_file(str(bad))
        settle(panel)
        assert panel.runs == []
        assert "could not be read" in panel.status.text()

    def test_a_store_is_read_in_the_background_too(self, panel, tmp_path, reference):  # noqa: F811
        from geocomp.io.store import open_store

        project_, solution, _network = reference
        path = tmp_path / "project.gpkg"
        with open_store(path, create=True) as store:
            store.write(project_)
            store.write_solution(solution)
        panel.load_store(str(path))
        settle(panel)
        assert [run.solution.id for run in panel.runs] == [solution.id]

    def test_the_observation_table_fills_filters_and_sorts_within_the_bound(self, panel):
        """5,000 rows, each step under NFR-004's 200 ms with room to spare: the
        table holds the rows and Qt asks only for the cells it draws. As a
        standard item model behind a Python filter, 2,352 rows took 180 ms.

        Each step is timed as the best of three runs of the sequence, and every
        run does the same work. A step takes 2 to 25 ms here; on a shared CI
        runner one took 218 ms once, which was the runner stalling, not the
        table. A table that really is slow is slow in all three runs."""
        import time

        from qgis.PyQt.QtCore import Qt

        from geocomp.core.visualization.results import ObservationRow

        rows = [
            ObservationRow(
                observation_id=f"o{index}",
                residual=0.001 * ((index * 7919) % 101 - 50),
                standardised=None if index % 97 == 0 else ((index * 31) % 89) / 20.0,
                redundancy=0.5,
                mdb=0.01,
                external=0.1,
                decision="accepted" if index % 13 else "rejected",
            )
            for index in range(5000)
        ]
        model = panel.observation_model
        steps = (
            lambda: model.set_rows(rows),
            lambda: panel.set_filter("rejected"),
            lambda: panel.set_filter("all"),
            lambda: panel.observation_view.sortByColumn(2, Qt.SortOrder.DescendingOrder),
        )
        best = [float("inf")] * len(steps)
        for _run in range(3):
            for number, step in enumerate(steps):
                started = time.perf_counter()
                step()
                best[number] = min(best[number], time.perf_counter() - started)
        assert max(best) < 0.2, best
        shown = panel.visible_observations()
        assert len(shown) == 5000
        # Sorted descending by w, the rows with none last.
        assert all(row.standardised is None for row in model.shown[-52:])


class TestTheObservationTable:
    def test_each_filter_narrows_the_table(self, panel, solution):
        panel.add_solution(solution, "here")
        panel.set_filter("rejected")
        assert panel.visible_observations() == ["blunder"]
        panel.set_filter("uncheckable")
        assert panel.visible_observations() == ["blind"]
        panel.set_filter("untested")
        assert panel.visible_observations() == ["engine"]
        panel.set_filter("all", "pass")
        assert panel.visible_observations() == ["passes"]

    def test_a_column_sorts_by_number_with_the_empty_last(self, panel, solution):
        from qgis.PyQt.QtCore import Qt

        panel.add_solution(solution, "here")
        panel.set_filter("all")
        panel.observation_view.sortByColumn(2, Qt.SortOrder.AscendingOrder)
        assert panel.visible_observations()[:2] == ["passes", "blunder"]

    def test_an_uncheckable_mdb_sorts_as_infinite(self, panel, solution):
        """It is the largest MDB there is, not a missing one."""
        from qgis.PyQt.QtCore import Qt

        panel.add_solution(solution, "here")
        panel.observation_view.sortByColumn(4, Qt.SortOrder.DescendingOrder)
        assert panel.visible_observations()[0] == "blind"
        # The engine's row has no MDB at all: last, sorted either way.
        assert panel.visible_observations()[-1] == "engine"
        panel.observation_view.sortByColumn(4, Qt.SortOrder.AscendingOrder)
        assert panel.visible_observations()[-1] == "engine"


class TestTheStationTable:
    def test_a_column_sorts_by_number_not_by_text(self, panel):
        """Until P12c-15 the table sorted as text, so 10.5 came before 9.2."""
        from qgis.PyQt.QtCore import Qt

        from geocomp.core.visualization.results import StationRow

        rows = [
            StationRow(name, ("e", "n"), (0.0, 0.0), (0.001, 0.001), value, None, None)
            for name, value in (("A", 10.5), ("B", 9.2), ("C", None), ("D", 0.75))
        ]
        panel.station_model.set_rows(rows)
        panel.station_table.sortByColumn(3, Qt.SortOrder.AscendingOrder)
        assert [row.station_id for row in panel.station_model.shown] == ["D", "B", "A", "C"]
        panel.station_table.sortByColumn(3, Qt.SortOrder.DescendingOrder)
        assert [row.station_id for row in panel.station_model.shown] == ["A", "B", "D", "C"]

    def test_selecting_a_row_selects_its_station(self, panel, solution, monkeypatch):
        chosen = []
        monkeypatch.setattr(panel, "select_station", chosen.append)
        panel.add_solution(solution, "here")
        panel.station_table.selectRow(0)
        assert chosen == [panel.station_model.shown[0].station_id]


class TestTheLinksToTheMap:
    def test_a_row_selects_its_feature_on_the_runs_layer_and_zooms(
        self, panel, project, solution_file
    ):
        layer = _residual_layer(solution_file, ["passes", "blunder", "blind"])
        other = _residual_layer("/elsewhere/solution.json", ["blunder"])
        project.addMapLayer(layer)
        project.addMapLayer(other)
        panel.add_solution_file(solution_file)
        assert panel.select_observation("blunder") == 1
        assert [f["observation"] for f in layer.selectedFeatures()] == ["blunder"]
        assert other.selectedFeatureCount() == 0
        assert panel.zoom.layers == ["Residuals"]

    def test_selecting_in_the_table_selects_on_the_map(self, panel, project, solution_file):
        layer = _residual_layer(solution_file, ["passes", "blunder"])
        project.addMapLayer(layer)
        panel.add_solution_file(solution_file)
        panel.set_filter("rejected")
        panel.observation_view.selectRow(0)
        assert [f["observation"] for f in layer.selectedFeatures()] == ["blunder"]

    def test_a_station_shows_its_time_series_when_there_is_one(self, panel, solution):
        class Series:
            def __init__(self):
                self.document = {
                    "stations": [
                        {"station": station.station_id}
                        for station in solution.adjusted_stations
                    ]
                }
                self.selected = []
                self.shown = False

            def select_stations(self, stations):
                self.selected = stations

            def show(self):
                self.shown = True

        series = Series()
        panel._series_panel = series
        panel.add_solution(solution, "here")
        station = solution.adjusted_stations[0].station_id
        panel.select_station(station)
        assert series.selected == [station] and series.shown

    def test_without_a_series_nothing_is_asked_of_it(self, panel, solution):
        panel.add_solution(solution, "here")
        assert panel.select_station(solution.adjusted_stations[0].station_id) == 0
