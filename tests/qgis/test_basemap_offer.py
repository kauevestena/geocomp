# SPDX-License-Identifier: GPL-2.0-or-later
"""The base-map offer: ``basemaps.offer_on_result_layers`` has a behaviour (P12a).

``specs/17`` section 5.6: *the plugin offers to add configured base map
services*. Until P12a the switch for that offer was declared, labelled, stored
-- and read by nothing, because there was no offer. These tests are the offer:
it appears when GeoComp's results arrive and only then, it asks rather than
adds, it asks once, and the user can turn it off from the question itself.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.qgis


@pytest.fixture
def project(qgis_app):
    from qgis.core import QgsProject

    instance = QgsProject.instance()
    instance.clear()
    yield instance
    instance.clear()


@pytest.fixture
def bar(qgis_app):
    from qgis.gui import QgsMessageBar

    return QgsMessageBar()


@pytest.fixture
def offer(project, bar):
    from geocomp.gui.basemap_offer import BaseMapOffer

    watcher = BaseMapOffer(bar, project)
    yield watcher
    watcher.unload()


def _layer(name: str = "stations", *, result: bool = True):
    from qgis.core import QgsVectorLayer

    from geocomp.algorithms.layer_outputs import RESULT_LAYER_PROPERTY

    layer = QgsVectorLayer("Point?crs=EPSG:31983", name, "memory")
    if result:
        layer.setCustomProperty(RESULT_LAYER_PROPERTY, "stations")
    return layer


def _buttons(bar) -> dict[str, object]:
    from qgis.PyQt.QtWidgets import QPushButton

    return {
        button.objectName(): button
        for item in bar.items()
        for button in item.findChildren(QPushButton)
        if button.objectName().startswith("geocompBaseMapOffer")
    }


class TestWhenItAsks:
    def test_a_result_layer_brings_the_offer(self, project, bar, offer):
        from geocomp.core.basemaps import DEFAULT_SERVICES

        project.addMapLayer(_layer())
        buttons = _buttons(bar)
        assert set(buttons) == {
            *(f"geocompBaseMapOffer_{service.id}" for service in DEFAULT_SERVICES),
            "geocompBaseMapOfferNever",
        }

    def test_nothing_is_added_until_the_user_chooses(self, project, bar, offer):
        project.addMapLayer(_layer())
        assert len(project.mapLayers()) == 1

    def test_an_ordinary_layer_brings_nothing(self, project, bar, offer):
        project.addMapLayer(_layer("roads", result=False))
        assert not bar.items()

    def test_it_asks_once_per_project(self, project, bar, offer):
        project.addMapLayer(_layer("stations"))
        project.addMapLayer(_layer("ellipses"))
        assert len(bar.items()) == 1

    def test_switched_off_it_does_not_ask(self, project, bar, offer):
        from geocomp.services.settings_service import settings

        with settings.run_overrides({"basemaps.offer_on_result_layers": False}):
            project.addMapLayer(_layer())
        assert not bar.items()

    def test_a_project_with_a_base_map_is_not_asked(self, project, bar, offer):
        from geocomp.core.basemaps import DEFAULT_SERVICES
        from geocomp.layers.basemaps import add_base_map

        add_base_map(DEFAULT_SERVICES[1], project)
        bar.clearWidgets()
        project.addMapLayer(_layer())
        assert not bar.items()

    def test_a_configured_default_is_offered_alone(self, project, bar, offer):
        from geocomp.services.settings_service import settings

        with settings.run_overrides({"basemaps.default_service": "opentopomap"}):
            project.addMapLayer(_layer())
        assert set(_buttons(bar)) == {
            "geocompBaseMapOffer_opentopomap",
            "geocompBaseMapOfferNever",
        }

    def test_a_new_project_is_asked_again(self, project, bar, offer):
        """Every unsaved project has the same empty file name."""
        project.addMapLayer(_layer())
        project.clear()
        bar.clearWidgets()
        project.addMapLayer(_layer())
        assert len(bar.items()) == 1

    def test_after_unloading_it_watches_nothing(self, project, bar, offer):
        offer.unload()
        project.addMapLayer(_layer())
        assert not bar.items()


class TestWhatTheAnswersDo:
    def test_choosing_a_service_adds_it_beneath_the_results(self, project, bar, offer):
        from geocomp.core.basemaps import DEFAULT_SERVICES

        project.addMapLayer(_layer())
        service = DEFAULT_SERVICES[0]
        _buttons(bar)[f"geocompBaseMapOffer_{service.id}"].click()

        names = [node.name() for node in project.layerTreeRoot().findLayers()]
        assert names[-1] == service.name
        assert names[0] == "stations"

    def test_dont_offer_again_turns_the_setting_off(self, project, bar, offer):
        from geocomp.services.settings_service import settings

        project.addMapLayer(_layer())
        try:
            _buttons(bar)["geocompBaseMapOfferNever"].click()
            assert settings.value("basemaps.offer_on_result_layers") is False
            assert not bar.items()
        finally:
            settings.reset_global("basemaps.offer_on_result_layers")
