# SPDX-License-Identifier: GPL-2.0-or-later
"""Print layout templates for the standard deliverables (FR-931; specs/19 section 6; P12b).

And specs/19 criterion 2's second half: *the exaggeration factor stated in the
legend; a test asserts the legend text is present and correct* -- here, in the
legend of a layout that includes the ellipses, which is where FR-901 says it
must also appear.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.qgis

ALGORITHM = "geocomp:project_print_layout"
ELLIPSES = "Error ellipses (95% confidence, exaggerated 250x)"
ITEM_IDS = ("title", "map", "legend", "scalebar", "north", "notes", "footer")


@pytest.fixture(autouse=True, scope="module")
def _registered(geocomp_provider):
    return geocomp_provider


@pytest.fixture
def project(qgis_app):
    from qgis.core import QgsProject

    instance = QgsProject.instance()
    instance.clear()
    yield instance
    instance.clear()


def _layer(geometry: str, fields: str, name: str, kind: str, rows):
    from qgis.core import QgsFeature, QgsGeometry, QgsPointXY, QgsVectorLayer

    from geocomp.algorithms.layer_outputs import RESULT_LAYER_PROPERTY

    layer = QgsVectorLayer(f"{geometry}?crs=EPSG:31982&{fields}", name, "memory")
    features = []
    for index, row in enumerate(rows):
        feature = QgsFeature(layer.fields())
        x, y = 500000.0 + 100.0 * index, 7400000.0 + 50.0 * index
        if geometry == "Point":
            feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(x, y)))
        elif geometry == "LineString":
            feature.setGeometry(
                QgsGeometry.fromPolylineXY([QgsPointXY(x, y), QgsPointXY(x + 80.0, y + 30.0)])
            )
        else:
            feature.setGeometry(QgsGeometry.fromRect(_rect(x, y)))
        feature.setAttributes(list(row))
        features.append(feature)
    layer.dataProvider().addFeatures(features)
    layer.updateExtents()
    layer.setCustomProperty(RESULT_LAYER_PROPERTY, kind)
    return layer


def _rect(x, y):
    from qgis.core import QgsRectangle

    return QgsRectangle(x - 5.0, y - 3.0, x + 5.0, y + 3.0)


@pytest.fixture
def results(project):
    from geocomp.layers.styles import apply_style
    from geocomp.layers.themes import add_thematic_styles

    stations = _layer(
        "Point",
        "field=station:string&field=constraint:string&field=positional_uncertainty:double",
        "Adjusted stations",
        "stations",
        [("A", "fixed", None), ("B", "free", 0.004), ("C", "free", 0.009)],
    )
    ellipses = _layer(
        "Polygon",
        "field=station:string&field=exaggeration:double&field=confidence:double",
        ELLIPSES,
        "ellipses",
        [("B", 250.0, 0.95), ("C", 250.0, 0.95)],
    )
    residuals = _layer(
        "LineString",
        "field=observation:string&field=decision:string&field=standardised:double"
        "&field=redundancy:double&field=mdb:double&field=external_reliability:double"
        "&field=mdb_displacement:double",
        "Residuals",
        "residuals",
        [
            ("d1", "accepted", 0.4, 0.6, 0.003, 0.001, 0.003),
            ("d2", "uncheckable", None, 0.005, None, None, None),
        ],
    )
    for layer, style in ((stations, "stations"), (residuals, "residuals")):
        apply_style(layer, style)
        add_thematic_styles(layer, style)
    for layer in (stations, ellipses, residuals):
        project.addMapLayer(layer)
    return {"stations": stations, "ellipses": ellipses, "residuals": residuals}


def _run(parameters: dict):
    from qgis.core import QgsApplication, QgsProcessingContext, QgsProcessingFeedback

    algorithm = QgsApplication.processingRegistry().algorithmById(ALGORITHM).create({})
    results, ok = algorithm.run(
        parameters, QgsProcessingContext(), QgsProcessingFeedback(), catchExceptions=False
    )
    assert ok
    return results


def _layout(project, name: str):
    layout = project.layoutManager().layoutByName(name)
    assert layout is not None, f"no layout named {name!r}"
    return layout


class TestTheTemplates:
    @pytest.mark.parametrize("template", ["network_map", "displacement_map", "quality_map"])
    def test_each_shipped_template_loads_with_every_item(self, project, template):
        from qgis.core import QgsPrintLayout, QgsReadWriteContext
        from qgis.PyQt.QtXml import QDomDocument

        from geocomp.resources import LAYOUTS_DIR

        document = QDomDocument()
        document.setContent((LAYOUTS_DIR / f"{template}.qpt").read_text(encoding="utf-8"))
        layout = QgsPrintLayout(project)
        _items, ok = layout.loadFromTemplate(document, QgsReadWriteContext())
        assert ok
        assert all(layout.itemById(item) is not None for item in ITEM_IDS)


class TestTheNetworkMap:
    def test_the_layout_lands_in_the_project_with_the_results_drawn(self, project, results):
        from qgis.core import QgsLayoutItemMap

        outcome = _run({"TEMPLATE": 0})
        layout = _layout(project, outcome["LAYOUT"])
        map_item = layout.itemById("map")
        assert isinstance(map_item, QgsLayoutItemMap)
        drawn = {layer.name() for layer in map_item.layers()}
        assert {"Adjusted stations", ELLIPSES} <= drawn
        assert "Residuals" not in drawn
        assert map_item.extent().contains(results["stations"].extent())

    def test_the_legend_states_the_exaggeration(self, project, results):
        """FR-901: in any layout that includes the layer."""
        outcome = _run({"TEMPLATE": 0})
        legend = _layout(project, outcome["LAYOUT"]).itemById("legend")
        names = [node.layer().name() for node in legend.model().rootGroup().findLayers()]
        assert ELLIPSES in names

    def test_the_notes_say_what_the_factor_means(self, project, results):
        outcome = _run({"TEMPLATE": 0})
        notes = _layout(project, outcome["LAYOUT"]).itemById("notes").text()
        assert "250x" in notes and "scale bar" in notes

    def test_a_title_and_a_second_layout_of_the_same_name(self, project, results):
        first = _run({"TEMPLATE": 0, "TITLE": "Ponte Nova, 2026"})["LAYOUT"]
        second = _run({"TEMPLATE": 0, "TITLE": "Ponte Nova, 2026"})["LAYOUT"]
        assert first == "Ponte Nova, 2026"
        assert second == "Ponte Nova, 2026 (2)"
        assert _layout(project, first).itemById("title").text() == "Ponte Nova, 2026"


class TestTheQualityMap:
    def test_it_holds_the_thematic_style_without_changing_the_layer(self, project, results):
        outcome = _run({"TEMPLATE": 2, "QUALITY": 0})
        map_item = _layout(project, outcome["LAYOUT"]).itemById("map")
        residuals = results["residuals"]
        assert map_item.keepLayerStyles()
        overrides = map_item.layerStyleOverrides()
        assert overrides[residuals.id()] == residuals.styleManager().style(
            "Redundancy number"
        ).xmlData()
        assert residuals.styleManager().currentStyle() == "W-test decision"

    def test_the_notes_name_the_map_and_say_when_it_is_relative(self, project, results):
        outcome = _run({"TEMPLATE": 2, "QUALITY": 2})
        notes = _layout(project, outcome["LAYOUT"]).itemById("notes").text()
        assert "minimal detectable bias" in notes
        assert "fitted to this network" in notes


class TestWhatItRefuses:
    def test_nothing_to_draw(self, project):
        from qgis.core import QgsProcessingException

        with pytest.raises(QgsProcessingException) as caught:
            _run({"TEMPLATE": 1})
        assert "nothing to draw" in str(caught.value)

    def test_a_template_without_a_map(self, project, results, tmp_path):
        from qgis.core import QgsLayoutItemLabel, QgsPrintLayout, QgsProcessingException, QgsReadWriteContext

        layout = QgsPrintLayout(project)
        layout.initializeDefaults()
        layout.addLayoutItem(QgsLayoutItemLabel(layout))
        path = tmp_path / "no_map.qpt"
        assert layout.saveAsTemplate(str(path), QgsReadWriteContext())
        with pytest.raises(QgsProcessingException) as caught:
            _run({"TEMPLATE": 0, "TEMPLATE_FILE": str(path)})
        assert "'map'" in str(caught.value)
