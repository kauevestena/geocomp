# SPDX-License-Identifier: GPL-2.0-or-later
"""Adding a configured base map to the project (FR-167).

``specs/17-persistence-and-interoperability.md`` section 5.6. The *services* are
declared in :mod:`geocomp.core.basemaps`, which is QGIS-free and where the URI
is built and tested; this module is the thin part that needs QGIS, and it is
thin on purpose.

**Three things it will not do**, each because the spec says so or because the
alternative is worse:

*It does not bundle imagery, and it does not hard-code a service.* The
catalogue is data, replaceable wholesale by ``basemaps.catalogue``.

*It honours what the user already has.* ``basemaps.reuse_existing_layer``
defaults to true, and :func:`existing_base_map` looks for a raster layer already
in the project whose source is the same service before adding a second one. A
plugin that stacks a fourth OpenStreetMap on someone's carefully arranged
project is a plugin they turn off.

*It puts the base map at the bottom.* A base map inserted above the result
layers hides the thing the user just computed, which reads as the adjustment
having failed.
"""

from __future__ import annotations

from qgis.core import QgsCoordinateReferenceSystem, QgsProject, QgsRasterLayer

from geocomp.core.basemaps import BaseMapService

__all__ = ["add_base_map", "base_map_layer", "existing_base_map"]

#: Tile services are served in Web Mercator. Stated rather than left to QGIS's
#: guess: a base map that lands in the project's own CRS renders as a smear at
#: high latitudes and, worse, silently misplaces itself relative to the network.
TILE_CRS = "EPSG:3857"

#: **All three kinds load through the ``wms`` provider.** There is no provider
#: called ``xyz`` or ``wmts`` in QGIS: the kind goes in the *URI* as ``type=``,
#: which :meth:`BaseMapService.uri` already writes, and the provider key stays
#: ``wms`` for all of them. Passing the kind as the provider key produced
#: ``Invalid data provider xyz`` and an invalid layer for every service --
#: caught by the CI QGIS job, which is the only environment that can catch it,
#: since without a runtime the layer is never constructed at all.
PROVIDER = "wms"


def base_map_layer(service: BaseMapService) -> QgsRasterLayer:
    """Build the raster layer for *service*, without adding it to a project.

    Separate from :func:`add_base_map` so a caller can check
    :meth:`~qgis.core.QgsRasterLayer.isValid` and report a service that is
    misconfigured or unreachable, rather than adding an invalid layer that
    shows as a broken entry in the legend with no explanation.
    """
    layer = QgsRasterLayer(service.uri(), service.name, PROVIDER)
    if layer.isValid():
        layer.setCrs(QgsCoordinateReferenceSystem(TILE_CRS))
        # The attribution travels with the layer, so it reaches a print layout
        # and a copied project rather than living only in the catalogue file.
        metadata = layer.metadata()
        metadata.setRights([service.attribution])
        layer.setMetadata(metadata)
    return layer


def existing_base_map(service: BaseMapService, project: QgsProject | None = None) -> object | None:
    """A layer already in *project* serving the same tiles, if there is one.

    Matched on the service URL rather than the layer name, because the name is
    the user's to change and often is: "Basemap", "fundo", "OSM cinza". The URL
    is what determines whether adding another would be a duplicate.
    """
    project = project or QgsProject.instance()
    for layer in project.mapLayers().values():
        source = layer.source() or ""
        if service.url in source or service.url.replace("&", "%26") in source:
            return layer
    return None


def add_base_map(
    service: BaseMapService,
    project: QgsProject | None = None,
    *,
    reuse_existing: bool = True,
) -> tuple[object | None, str]:
    """Add *service* to the project, or reuse what is already there.

    Returns the layer and one of ``"added"``, ``"reused"`` or ``"invalid"``. The
    reason is returned rather than logged so the caller can put it in the same
    report as everything else it did -- a base map that could not be added is
    something the user should read once, in the place they are already looking.
    """
    project = project or QgsProject.instance()

    if reuse_existing:
        found = existing_base_map(service, project)
        if found is not None:
            return found, "reused"

    layer = base_map_layer(service)
    if not layer.isValid():
        return None, "invalid"

    project.addMapLayer(layer, False)
    # Bottom of the tree: above the results, a base map hides what was just
    # computed, and the adjustment reads as having produced nothing. `addLayer`
    # appends, and the tree is ordered top to bottom, so appending *is* the
    # bottom -- unambiguously, which `insertLayer(-1, ...)` is not.
    project.layerTreeRoot().addLayer(layer)
    return layer, "added"
