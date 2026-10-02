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
