# SPDX-License-Identifier: GPL-2.0-or-later
"""The time-series panel and its tie to the map (FR-838, FR-903; ``specs/19`` section 5).

Criterion 6 of ``specs/19`` section 8: *the time series panel plots a
three-epoch series with uncertainty bands and threshold lines, and map-to-plot
selection works in both directions.* The curves themselves are
``series_curves``', tested without QGIS; what is tested here is that a layer
carrying a series document ties itself to the panel when it is added, that
selecting on the map plots, that picking in the plot selects on the map, and
that both exports write what is plotted.
"""

from __future__ import annotations

import json

import pytest

from geocomp.core.monitoring import evaluate_alerts, series, series_document, thresholds_from_rows
from geocomp.core.monitoring.document import SERIES_PROPERTY
from tests.monitoring_network import REFERENCE, epoch

pytestmark = pytest.mark.qgis

EPOCHS = (2024.0, 2025.0, 2026.0)


@pytest.fixture(scope="module")
def series_path(tmp_path_factory):
    solutions = [
        epoch(year, moves={"O1": (0.004 * (year - 2024.0), -0.003 * (year - 2024.0))}, seed=10 + n)
        for n, year in enumerate(EPOCHS)
    ]
    thresholds = thresholds_from_rows([["horizontal", "0.006", "O1", "crest"]])
    stations = series(solutions, reference=REFERENCE, confidence=0.95)
    document = series_document(
        stations,
        solutions,
        reference=REFERENCE,
        datum="translation_rotation",
        confidence=0.95,
        thresholds=thresholds,
        alerts=evaluate_alerts(thresholds, series=stations),
    )
    path = tmp_path_factory.mktemp("panel") / "series.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


@pytest.fixture
def panel(qgis_app, series_path):
    from geocomp.gui.time_series_panel import TimeSeriesPanel, attach_to_project, detach_from_project

    widget = TimeSeriesPanel()
    attach_to_project(widget)
    yield widget
    detach_from_project(widget)
    widget.deleteLater()


@pytest.fixture
def velocity_layer(qgis_app, series_path):
    """A velocity layer as the algorithm leaves it: a station field and the
    series document's path as a property. Built from a URI rather than typed
    fields, so it runs on any QGIS the suite runs on."""
    from qgis.core import QgsFeature, QgsGeometry, QgsPointXY, QgsProject, QgsVectorLayer

    document = json.loads(series_path.read_text())
    layer = QgsVectorLayer("Point?crs=EPSG:31982&field=station:string(20)", "velocities", "memory")
    features = []
    for station, (east, north) in document["display"]["positions"].items():
        feature = QgsFeature(layer.fields())
        feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(east, north)))
        feature.setAttribute("station", station)
        features.append(feature)
    layer.dataProvider().addFeatures(features)
    layer.setCustomProperty(SERIES_PROPERTY, str(series_path))
    yield layer
    if QgsProject.instance().mapLayer(layer.id()) is not None:
        QgsProject.instance().removeMapLayer(layer.id())


def _feature_id(layer, station):
    return next(f.id() for f in layer.getFeatures() if f["station"] == station)


class TestThePlot:
    def test_a_series_document_is_listed_by_station_and_component(self, panel, series_path):
        panel.load(str(series_path))
        assert panel.stations.count() == 9
        assert [panel.component.itemData(i) for i in range(panel.component.count())] == ["e", "n"]

    def test_selected_stations_are_overlaid_with_bands_and_the_fit(self, panel, series_path):
        panel.load(str(series_path))
        panel.select_stations(["O1", "O2"])
        curves = panel.plot.curves
        assert [c.station for c in curves] == ["O1", "O2"]
        o1 = curves[0]
        assert o1.epochs == EPOCHS
        assert all(lo < v < hi for lo, v, hi in zip(o1.low, o1.values, o1.high, strict=True))
        assert o1.fit is not None
        assert o1.values[-1] == pytest.approx(8.0, abs=2.5)  # 4 mm/yr east for two years

    def test_the_stations_alert_limit_is_drawn(self, panel, series_path):
        panel.load(str(series_path))
        panel.select_stations(["O1"])
        assert panel.plot.limits == [pytest.approx(6.0)]
        panel.select_stations(["O2"])
        assert panel.plot.limits == []

    def test_a_point_is_picked_and_described_with_its_epoch(self, panel, series_path):
        panel.load(str(series_path))
        panel.select_stations(["O1"])
        panel.plot.image()  # paints, placing the points
        point, station, index = panel.plot._points[2]
        assert panel.plot.nearest(point) == (station, index) == ("O1", 2)
        text = panel.plot.describe("O1", 2)
        assert "2026.0000" in text and "dam-2026.0" in text


class TestTheMap:
    def test_adding_the_layer_ties_it_to_the_panel(self, panel, velocity_layer, series_path):
        from qgis.core import QgsProject

        QgsProject.instance().addMapLayer(velocity_layer)
        assert panel.layer is velocity_layer
        assert panel.path == str(series_path)
        assert panel.stations.count() == 9

    def test_selecting_on_the_map_plots(self, panel, velocity_layer):
        from qgis.core import QgsProject

        QgsProject.instance().addMapLayer(velocity_layer)
        velocity_layer.selectByIds([_feature_id(velocity_layer, "O1"), _feature_id(velocity_layer, "O3")])
        assert sorted(panel.selected_stations()) == ["O1", "O3"]
        assert sorted(c.station for c in panel.plot.curves) == ["O1", "O3"]

    def test_picking_in_the_plot_selects_on_the_map(self, panel, velocity_layer):
        from qgis.core import QgsProject

        QgsProject.instance().addMapLayer(velocity_layer)
        velocity_layer.selectByIds([_feature_id(velocity_layer, "O1"), _feature_id(velocity_layer, "O2")])
        panel.pick("O2", 1)
        assert [f["station"] for f in velocity_layer.selectedFeatures()] == ["O2"]
        assert "O2" in panel.status.text() and "2025.0000" in panel.status.text()

    def test_a_layer_without_a_series_is_ignored(self, panel, qgis_app):
        from qgis.core import QgsProject, QgsVectorLayer

        plain = QgsVectorLayer("Point?field=station:string(20)", "plain", "memory")
        QgsProject.instance().addMapLayer(plain)
        try:
            assert panel.layer is None
        finally:
            QgsProject.instance().removeMapLayer(plain.id())


class TestExport:
    def test_csv_rows_are_what_is_selected(self, panel, series_path, tmp_path):
        panel.load(str(series_path))
        panel.select_stations(["O1"])
        target = tmp_path / "o1.csv"
        assert panel.export_csv(str(target)) == 3 * 2
        lines = target.read_text().splitlines()
        assert lines[0] == "station,solution,epoch,component,offset,std_dev"
        assert all(line.startswith("O1,") for line in lines[1:])

    def test_the_plot_as_an_image(self, panel, series_path, tmp_path):
        panel.load(str(series_path))
        panel.select_stations(["O1"])
        target = tmp_path / "o1.png"
        assert panel.export_image(str(target))
        assert target.stat().st_size > 1000


# -- the comparison's compatibility dialog (FR-831, specs/15 section 3) ------------


@pytest.fixture(scope="module")
def epochs_on_disk(tmp_path_factory):
    from dataclasses import replace

    from geocomp.core.models import DatumDefinition

    folder = tmp_path_factory.mktemp("compatibility")
    first, second = epoch(2025.0, seed=1), epoch(2026.0, moves={"O2": (0.008, -0.006)}, seed=2)
    held = replace(second, datum_definition=DatumDefinition.FIXED)
    fewer = replace(
        second, adjusted_stations=tuple(s for s in second.adjusted_stations if s.station_id != "O5")
    )
    paths = {}
    for name, solution in (("first", first), ("second", second), ("held", held), ("fewer", fewer)):
        path = folder / f"{name}.json"
        path.write_text(json.dumps(solution.to_dict()), encoding="utf-8")
        paths[name] = str(path)
    return paths


class TestCompatibilityDialog:
    def test_comparable_epochs_are_described_before_the_run(self, qgis_app, epochs_on_disk):
        from geocomp.gui.compare_dialog import check_compatibility

        result = check_compatibility(epochs_on_disk["first"], epochs_on_disk["fewer"])
        assert result.comparable
        text = "\n".join(result.lines)
        assert "dam-2025.0" in text and "dam-2026.0" in text
        assert "8 stations in both epochs" in text
        assert "O5" in text  # the station one epoch lacks, found before the run
        assert "independent" in text

    def test_an_incomparable_pair_is_refused_with_its_reason(self, qgis_app, epochs_on_disk):
        from geocomp.gui.compare_dialog import check_compatibility

        result = check_compatibility(epochs_on_disk["first"], epochs_on_disk["held"])
        assert not result.comparable
        assert "datum" in result.lines[0]

    def test_ok_is_offered_only_for_a_comparable_pair(self, qgis_app, epochs_on_disk):
        from qgis.PyQt.QtWidgets import QDialogButtonBox

        from geocomp.gui.compare_dialog import CompatibilityDialog

        dialog = CompatibilityDialog()
        ok = dialog.buttons.button(QDialogButtonBox.StandardButton.Ok)
        assert not ok.isEnabled()
        dialog.first.setFilePath(epochs_on_disk["first"])
        dialog.second.setFilePath(epochs_on_disk["held"])
        dialog.check()
        assert not ok.isEnabled()
        dialog.second.setFilePath(epochs_on_disk["second"])
        dialog.check()
        assert ok.isEnabled()
        assert dialog.parameters() == {"FIRST": epochs_on_disk["first"], "SECOND": epochs_on_disk["second"]}
