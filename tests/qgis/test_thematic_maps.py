# SPDX-License-Identifier: GPL-2.0-or-later
"""Thematic quality maps: every FR-902 attribute, as a named style (phase P12b).

``specs/19-visualization.md`` section 4 and criterion 5: *thematic maps render
correctly for each listed attribute, including the redundancy-number map.*
Here a map "renders correctly" when each feature lands in the class its value
belongs to -- the uncheckable observation in the uncheckable class above all,
since that is the one the redundancy map exists to show.

The layers are built from memory-layer URIs, so these run on any QGIS; the same
styles reaching a real adjustment's layers is asserted in
``test_result_layers.py``, which needs the field API of QGIS 3.38.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.qgis

RESIDUAL_FIELDS = (
    "decision:string",
    "standardised:double",
    "redundancy:double",
    "mdb:double",
    "external_reliability:double",
    "mdb_displacement:double",
)

#: (decision, |w|, r, mdb, external, mdb_displacement) -- one of each kind.
RESIDUALS = {
    "good": ("accepted", 0.4, 0.62, 0.003, 0.0015, 0.003),
    "weak": ("accepted", 1.6, 0.21, 0.008, 0.004, 0.008),
    "suspect": ("rejected", 3.7, 0.44, 0.005, 0.002, 0.005),
    "blind": ("uncheckable", None, 0.004, None, None, None),
    "engine": ("", None, None, None, None, None),
    "gravity": ("accepted", 0.9, 0.35, 2.0e-7, 0.001, None),
}


@pytest.fixture
def residuals(qgis_app):
    from qgis.core import QgsFeature, QgsGeometry, QgsPointXY, QgsVectorLayer

    uri = "LineString?crs=EPSG:31983&field=observation:string&" + "&".join(
        f"field={field}" for field in RESIDUAL_FIELDS
    )
    layer = QgsVectorLayer(uri, "Residuals", "memory")
    features = []
    for index, (name, row) in enumerate(RESIDUALS.items()):
        feature = QgsFeature(layer.fields())
        feature.setGeometry(
            QgsGeometry.fromPolylineXY([QgsPointXY(index, 0.0), QgsPointXY(index, 10.0)])
        )
        feature.setAttributes([name, *row])
        features.append(feature)
    layer.dataProvider().addFeatures(features)
    return layer


def _styled(layer, style: str):
    from geocomp.layers.styles import apply_style
    from geocomp.layers.themes import add_thematic_styles

    assert apply_style(layer, style)
    return add_thematic_styles(layer, style)


def _lines(fields: str, rows):
    """A line layer of *fields* (a memory URI's), one feature per row."""
    from qgis.core import QgsFeature, QgsGeometry, QgsPointXY, QgsVectorLayer

    layer = QgsVectorLayer(f"LineString?crs=EPSG:31983&{fields}", "lines", "memory")
    features = []
    for index, row in enumerate(rows):
        feature = QgsFeature(layer.fields())
        feature.setGeometry(QgsGeometry.fromPolylineXY([QgsPointXY(index, 0), QgsPointXY(index, 1)]))
        feature.setAttributes(list(row))
        features.append(feature)
    layer.dataProvider().addFeatures(features)
    return layer


def _class_of(layer, observation: str, key: str = "observation") -> str:
    """The legend label of the class the feature whose *key* is *observation* is
    drawn in, under the current style."""
    from qgis.core import QgsExpressionContext, QgsExpressionContextUtils, QgsRenderContext

    renderer = layer.renderer()
    labels = {item.ruleKey(): item.label() for item in renderer.legendSymbolItems()}
    # As QGIS renders a layer: with its scope, so an expression's column
    # references resolve. Without it they evaluate to NULL and fit no class.
    context = QgsRenderContext()
    context.setExpressionContext(
        QgsExpressionContext(QgsExpressionContextUtils.globalProjectLayerScopes(layer))
    )
    renderer.startRender(context, layer.fields())
    try:
        feature = next(
            f for f in layer.getFeatures() if f[key] == observation
        )
        context.expressionContext().setFeature(feature)
        keys = renderer.legendKeysForFeature(feature, context)
    finally:
        renderer.stopRender(context)
    assert len(keys) == 1, f"{observation} is drawn in {len(keys)} classes"
    return labels[next(iter(keys))]


class TestTheStylesOnOffer:
    def test_the_residuals_offer_their_four_maps_and_open_on_the_decision(self, residuals):
        added = _styled(residuals, "residuals")
        assert added == [
            "Standardised residual",
            "Redundancy number",
            "Minimal detectable bias",
            "External reliability",
        ]
        manager = residuals.styleManager()
        assert manager.currentStyle() == "W-test decision"
        assert residuals.renderer().classAttribute() == "decision"
        assert set(manager.styles()) == {"W-test decision", *added}

    def test_adding_twice_adds_nothing(self, residuals):
        _styled(residuals, "residuals")
        from geocomp.layers.themes import add_thematic_styles

        assert add_thematic_styles(residuals, "residuals") == []

    def test_every_theme_file_is_offered_and_every_offer_has_a_file(self, qgis_app):
        from geocomp.layers.styles import STYLE_DIR
        from geocomp.layers.themes import THEMES, theme_labels

        offered = {theme.id for themes in THEMES.values() for theme in themes}
        files = {path.stem for path in (STYLE_DIR / "themes").glob("*.qml")}
        assert offered == files
        assert offered <= set(theme_labels())

    def test_every_fr902_attribute_has_a_map(self, qgis_app):
        """Observation type and the trajectory's solution status are those
        layers' default styles; every other attribute is a theme."""
        from geocomp.layers.themes import THEMES

        themes = {theme.id for themes in THEMES.values() for theme in themes}
        assert {
            "positional_uncertainty",
            "standardised_residual",
            "redundancy",
            "mdb_displacement",
            "external_reliability",
            "baseline_status",
            "epoch",
        } <= themes


class TestEachMapDrawsEachFeatureInItsClass:
    def test_the_redundancy_map_shows_the_blind_spot(self, residuals):
        _styled(residuals, "residuals")
        residuals.styleManager().setCurrentStyle("Redundancy number")
        assert _class_of(residuals, "blind") == "Uncheckable (r below 0.01)"
        assert _class_of(residuals, "good") == "r 0.5 to 1"
        assert _class_of(residuals, "weak") == "r 0.1 to 0.3"
        assert _class_of(residuals, "engine") == "Not computed"

    @pytest.mark.parametrize(
        ("r", "expected"),
        [
            (0.0099999995, "Uncheckable (r below 0.01)"),
            (0.01, "r 0.01 to 0.1"),
            (-1.0e-17, "Uncheckable (r below 0.01)"),
        ],
    )
    def test_every_r_falls_in_exactly_one_class(self, residuals, r, expected):
        """The uncheckable class once ended at 0.00999999 and the next began at
        0.01, and an r between them was drawn in no class at all. A rounding
        error below zero is uncheckable too."""
        from qgis.core import QgsFeature, QgsGeometry, QgsPointXY

        # Added, not changed: a memory layer rounds a changed double to the
        # field's precision, five places, and 0.0099999995 would arrive as 0.01.
        edge = QgsFeature(residuals.fields())
        edge.setGeometry(QgsGeometry.fromPolylineXY([QgsPointXY(9, 0), QgsPointXY(9, 10)]))
        edge.setAttributes(["edge", "accepted", 0.5, r, None, None, None])
        assert residuals.dataProvider().addFeatures([edge])[0]
        _styled(residuals, "residuals")
        residuals.styleManager().setCurrentStyle("Redundancy number")
        assert _class_of(residuals, "edge") == expected

    def test_the_standardised_residual_map_bands_by_sigma(self, residuals):
        _styled(residuals, "residuals")
        residuals.styleManager().setCurrentStyle("Standardised residual")
        assert _class_of(residuals, "good") == "|w| below 1"
        assert _class_of(residuals, "weak") == "|w| 1 to 2"
        assert _class_of(residuals, "suspect") == "|w| 3 or more"
        assert _class_of(residuals, "blind") == "Not tested"

    def test_the_mdb_map_fits_its_classes_and_keeps_the_others(self, residuals):
        from geocomp.core.visualization.classes import fitted_bounds

        _styled(residuals, "residuals")
        residuals.styleManager().setCurrentStyle("Minimal detectable bias")
        values = [row[5] for row in RESIDUALS.values() if row[5] is not None]
        bounds = fitted_bounds(values, 4)
        data = [r for r in residuals.renderer().ranges() if r.upperValue() >= 0.0]
        assert [r.lowerValue() for r in data] == pytest.approx(list(bounds[:-1]))
        assert data[-1].upperValue() == pytest.approx(bounds[-1])
        assert data[-1].label().endswith(" m")
        assert _class_of(residuals, "blind") == "Uncheckable: no finite MDB"
        assert _class_of(residuals, "gravity") == "MDB not a length (see the table)"
        assert _class_of(residuals, "engine") == "Not computed"
        assert _class_of(residuals, "weak") == data[-1].label()

    def test_the_external_reliability_map(self, residuals):
        _styled(residuals, "residuals")
        residuals.styleManager().setCurrentStyle("External reliability")
        assert _class_of(residuals, "blind") == "Uncheckable: no finite effect"
        largest = max(row[4] for row in RESIDUALS.values() if row[4] is not None)
        top = [r for r in residuals.renderer().ranges() if r.upperValue() >= 0.0][-1]
        assert top.upperValue() == pytest.approx(largest)

    def test_the_positional_uncertainty_map(self, qgis_app):
        from qgis.core import QgsFeature, QgsGeometry, QgsPointXY, QgsVectorLayer

        layer = QgsVectorLayer(
            "Point?crs=EPSG:31983&field=observation:string&field=constraint:string"
            "&field=positional_uncertainty:double",
            "Stations",
            "memory",
        )
        rows = [("A", "fixed", None), ("B", "free", 0.002), ("C", "free", 0.004),
                ("D", "free", 0.007), ("E", "free", 0.012)]
        features = []
        for index, row in enumerate(rows):
            feature = QgsFeature(layer.fields())
            feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(index, 0.0)))
            feature.setAttributes(list(row))
            features.append(feature)
        layer.dataProvider().addFeatures(features)
        assert _styled(layer, "stations") == ["Positional uncertainty"]
        assert layer.styleManager().currentStyle() == "Constraint"
        layer.styleManager().setCurrentStyle("Positional uncertainty")
        assert _class_of(layer, "A") == "Not computed"
        assert _class_of(layer, "E").startswith("0.0")

    def test_the_epoch_map_has_one_class_per_epoch_in_time_order(self, qgis_app):
        from qgis.core import QgsFeature, QgsGeometry, QgsPointXY, QgsVectorLayer

        layer = QgsVectorLayer(
            "LineString?crs=EPSG:31983&field=observation:string&field=type:string"
            "&field=epoch:double",
            "Observations",
            "memory",
        )
        rows = [("a", "distance", 2024.5), ("b", "distance", 2023.25),
                ("c", "distance", None), ("d", "distance", 2024.5)]
        features = []
        for index, row in enumerate(rows):
            feature = QgsFeature(layer.fields())
            feature.setGeometry(
                QgsGeometry.fromPolylineXY([QgsPointXY(index, 0), QgsPointXY(index, 1)])
            )
            feature.setAttributes(list(row))
            features.append(feature)
        layer.dataProvider().addFeatures(features)
        assert _styled(layer, "observations") == ["Epoch"]
        layer.styleManager().setCurrentStyle("Epoch")
        labels = [category.label() for category in layer.renderer().categories()]
        assert labels == ["2023.250", "2024.500", "No epoch stated"]
        assert _class_of(layer, "a") == _class_of(layer, "d") == "2024.500"
        assert _class_of(layer, "c") == "No epoch stated"

    def test_the_gnss_solution_status_map(self, qgis_app):
        layer = _lines(
            "field=baseline:string&field=independent:string&field=solution_status:string",
            [("fixed", "yes", "FIXED"), ("float", "yes", "FLOAT"), ("ppp", "no", "PPP"),
             ("unknown", "yes", "")],
        )
        assert _styled(layer, "gnss_baselines") == ["GNSS solution status"]
        assert layer.styleManager().currentStyle() == "Independence"
        layer.styleManager().setCurrentStyle("GNSS solution status")
        assert _class_of(layer, "fixed", "baseline") == "Fixed (ambiguities resolved)"
        assert _class_of(layer, "float", "baseline") == "Float"
        assert _class_of(layer, "ppp", "baseline") == "PPP"
        assert _class_of(layer, "unknown", "baseline") == "Not recorded"

    def test_the_gravity_mdb_map_states_the_layers_unit(self, qgis_app):
        layer = _lines(
            "field=observation:string&field=decision:string&field=standardised:double"
            "&field=redundancy:double&field=mdb:double&field=unit:string",
            [("a", "accepted", 0.5, 0.5, 12.0, "µGal"), ("b", "accepted", 1.2, 0.3, 30.0, "µGal"),
             ("c", "uncheckable", None, 0.002, None, "µGal"), ("d", "", None, None, None, "µGal")],
        )
        assert _styled(layer, "gravity_differences") == [
            "Standardised residual",
            "Redundancy number",
            "Minimal detectable bias",
        ]
        layer.styleManager().setCurrentStyle("Minimal detectable bias")
        data = [r for r in layer.renderer().ranges() if r.upperValue() >= 0.0]
        assert data[-1].upperValue() == pytest.approx(30.0)
        assert all(r.label().endswith(" µGal") for r in data)
        assert _class_of(layer, "c") == "Uncheckable: no finite MDB"
        assert _class_of(layer, "d") == "Not computed"
        assert _class_of(layer, "b") == data[-1].label()

    def test_no_epoch_map_for_a_network_that_states_none(self, qgis_app):
        from qgis.core import QgsVectorLayer

        layer = QgsVectorLayer(
            "LineString?crs=EPSG:31983&field=type:string&field=epoch:double", "o", "memory"
        )
        assert _styled(layer, "observations") == []


class TestTheyLast:
    def test_the_styles_survive_a_project_save_and_reload(self, residuals, tmp_path):
        """Criterion 4 of specs/19: a style must survive the project."""
        from qgis.core import QgsProject, QgsVectorFileWriter, QgsVectorLayer

        path = tmp_path / "residuals.gpkg"
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "GPKG"
        QgsVectorFileWriter.writeAsVectorFormatV3(
            residuals, str(path), QgsProject.instance().transformContext(), options
        )
        layer = QgsVectorLayer(str(path), "Residuals", "ogr")
        assert layer.isValid()
        added = _styled(layer, "residuals")

        project = QgsProject.instance()
        project.clear()
        project.addMapLayer(layer)
        project_path = tmp_path / "project.qgz"
        assert project.write(str(project_path))
        project.clear()
        assert project.read(str(project_path))
        reloaded = next(iter(project.mapLayers().values()))
        assert set(reloaded.styleManager().styles()) == {"W-test decision", *added}
        reloaded.styleManager().setCurrentStyle("Redundancy number")
        assert "redundancy" in reloaded.renderer().classAttribute()
        project.clear()


class TestTheLegendSpeaksTheLanguage:
    def test_the_labels_go_through_the_style_catalogue(self, residuals):
        """FR-090: until P12b every legend label stayed English."""
        from qgis.PyQt.QtCore import QCoreApplication, QTranslator

        from geocomp.layers.styles import STYLE_CONTEXT

        class Marking(QTranslator):
            def translate(self, context, source, disambiguation=None, n=-1):
                # None, not "": an empty string is a translation, to Qt.
                return f"«{source}»" if context == STYLE_CONTEXT else None

        translator = Marking()
        QCoreApplication.installTranslator(translator)
        try:
            _styled(residuals, "residuals")
            labels = [c.label() for c in residuals.renderer().categories()]
            residuals.styleManager().setCurrentStyle("Redundancy number")
            ranges = [r.label() for r in residuals.renderer().ranges()]
        finally:
            QCoreApplication.removeTranslator(translator)
        assert "«Blunder candidate»" in labels
        assert "«Uncheckable (r below 0.01)»" in ranges
