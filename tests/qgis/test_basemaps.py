# SPDX-License-Identifier: GPL-2.0-or-later
"""Adding a base map to a QGIS project (FR-167).

``specs/17-persistence-and-interoperability.md`` section 5.6. The record, its
validation and its URI are tier 1 (``tests/test_basemaps.py``); what needs a
QGIS runtime is what the project does with them, and that is what is here:
where the layer lands in the tree, whether an existing one is reused, and that
the attribution travels with the layer rather than staying in the catalogue.

**No network is touched.** A tile layer is valid the moment QGIS parses its
URI; it does not fetch anything until it is drawn. So these tests assert on the
project and the layer, never on an image -- a test that needed tiles would fail
in CI for a reason that has nothing to do with GeoComp.
"""

from __future__ import annotations

import pytest

from geocomp.core.basemaps import DEFAULT_SERVICES, BaseMapService
from tests.conftest import requires_qgis

pytestmark = [pytest.mark.qgis, requires_qgis]


@pytest.fixture
def project(qgis_app):
    from qgis.core import QgsProject

    instance = QgsProject.instance()
    instance.clear()
    yield instance
    instance.clear()


@pytest.fixture
def service() -> BaseMapService:
    return DEFAULT_SERVICES[0]


def test_the_layer_is_valid(qgis_app, service) -> None:
    """A tile layer parses its URI without fetching anything."""
    from geocomp.layers.basemaps import base_map_layer

    assert base_map_layer(service).isValid()


def test_it_is_added_in_web_mercator(project, service) -> None:
    """Left to QGIS's guess, a tile layer lands misplaced against the network."""
    from geocomp.layers.basemaps import add_base_map

    layer, outcome = add_base_map(service, project)
    assert outcome == "added"
    assert layer.crs().authid() == "EPSG:3857"


def test_the_attribution_travels_with_the_layer(project, service) -> None:
    """So it reaches a print layout and a copied project, not just the catalogue."""
    from geocomp.layers.basemaps import add_base_map

    layer, _outcome = add_base_map(service, project)
    assert service.attribution in layer.metadata().rights()


def test_it_goes_to_the_bottom_of_the_tree(project, service) -> None:
    """Above the results it hides what was just computed."""
    from qgis.core import QgsVectorLayer

    from geocomp.layers.basemaps import add_base_map

    result = QgsVectorLayer("Point?crs=EPSG:31982", "Adjusted stations", "memory")
    project.addMapLayer(result)

    _layer, _outcome = add_base_map(service, project)
    names = [node.layer().name() for node in project.layerTreeRoot().findLayers()]
    assert names[-1] == service.name


def test_an_existing_base_map_is_reused_rather_than_stacked(project, service) -> None:
    """A plugin that stacks a fourth OpenStreetMap is one people turn off."""
    from geocomp.layers.basemaps import add_base_map

    first, first_outcome = add_base_map(service, project)
    second, second_outcome = add_base_map(service, project)

    assert (first_outcome, second_outcome) == ("added", "reused")
    assert second.id() == first.id()
    assert len(project.mapLayers()) == 1


def test_a_renamed_base_map_is_still_recognised(project, service) -> None:
    """Matched on the URL: the name is the user's to change, and often is."""
    from geocomp.layers.basemaps import add_base_map, existing_base_map

    layer, _outcome = add_base_map(service, project)
    layer.setName("fundo cinza")

    assert existing_base_map(service, project) is not None
    assert add_base_map(service, project)[1] == "reused"


def test_reuse_can_be_turned_off(project, service) -> None:
    """`basemaps.reuse_existing_layer`, for a user who wants two of them."""
    from geocomp.layers.basemaps import add_base_map

    add_base_map(service, project)
    _second, outcome = add_base_map(service, project, reuse_existing=False)
    assert outcome == "added"
    assert len(project.mapLayers()) == 2


def test_a_different_service_is_not_mistaken_for_the_first(project) -> None:
    from geocomp.layers.basemaps import add_base_map

    add_base_map(DEFAULT_SERVICES[0], project)
    _layer, outcome = add_base_map(DEFAULT_SERVICES[1], project)
    assert outcome == "added"
    assert len(project.mapLayers()) == 2


def test_an_unusable_service_is_reported_not_added(project) -> None:
    """An invalid layer in the legend is a broken entry with no explanation."""
    from geocomp.layers.basemaps import add_base_map

    broken = BaseMapService(
        id="broken",
        name="Broken",
        url="ftp://not-a-tile-service.invalid/{z}/{x}/{y}.png",
        attribution="none",
    )
    layer, outcome = add_base_map(broken, project)
    assert (layer, outcome) == (None, "invalid")
    assert not project.mapLayers()
