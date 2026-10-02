# SPDX-License-Identifier: GPL-2.0-or-later
"""``geocomp:project_print_layout`` -- a print layout for a standard deliverable (FR-931; P12b).

``specs/19-visualization.md`` section 6: *print layout templates ship for the
standard deliverables -- network map with ellipses, displacement map, quality
map -- as QGIS layout templates the user can adapt.* The templates are
``resources/layouts/*.qpt``, ordinary QGIS layout templates; this algorithm
makes a layout from one and fills it, and the result is a layout in the
project's layout manager like any other, to edit, print or export.

**The exaggeration is stated on the page.** ``specs/19`` section 3 calls an
unstated exaggeration the single most important thing to get right, and FR-901
asks for it *in any layout that includes the layer*. Every exaggerated layer
already states its factor in its own name, so the legend states it; the notes
box says what the legend's factors mean, and that the scale bar measures the
map rather than the ellipses.

**A quality map shows a thematic style** without changing the layer: the map
item holds the chosen style as an override (FR-902; ``layers/themes.py``), so
the network map and the quality map can sit in one project, each drawn its own
way.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qgis.core import (
    Qgis,
    QgsCoordinateTransform,
    QgsLayoutItemLabel,
    QgsLayoutItemLegend,
    QgsLayoutItemMap,
    QgsLayoutItemPicture,
    QgsLayoutItemScaleBar,
    QgsPrintLayout,
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingOutputString,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFile,
    QgsProcessingParameterMultipleLayers,
    QgsProcessingParameterString,
    QgsProject,
    QgsReadWriteContext,
    QgsRectangle,
    QgsVectorLayer,
)
from qgis.PyQt.QtXml import QDomDocument

from geocomp.algorithms.base import GeoCompAlgorithm

__all__ = ["PrintLayoutAlgorithm"]

TEMPLATE = "TEMPLATE"
TEMPLATE_FILE = "TEMPLATE_FILE"
LAYERS = "LAYERS"
QUALITY = "QUALITY"
TITLE = "TITLE"
NAME = "NAME"
LAYOUT = "LAYOUT"

#: The shipped templates, in the order the parameter offers them.
TEMPLATES = ("network_map", "displacement_map", "quality_map")

#: The result layers each deliverable draws, when no layers are chosen.
KINDS: dict[str, tuple[str, ...]] = {
    "network_map": (
        "stations",
        "ellipses",
        "corrections",
        "observations",
        "gnss_baselines",
        "gravity_stations",
        "gravity_differences",
    ),
    "displacement_map": ("displacements", "displacement_ellipses", "velocities", "stations"),
    "quality_map": ("residuals", "gravity_differences", "stations"),
}

#: The thematic maps a quality map can show, in the order offered; the
#: redundancy number first, the one ``specs/19`` section 4 singles out.
QUALITY_THEMES = (
    "redundancy",
    "standardised_residual",
    "mdb_displacement",
    "external_reliability",
    "positional_uncertainty",
)


def _no_threading() -> Any:
    # QGIS 4 spells it Qgis.ProcessingAlgorithmFlag.NoThreading; QGIS 3 kept it
    # on the algorithm class.
    flags = getattr(Qgis, "ProcessingAlgorithmFlag", None)
    if flags is not None and hasattr(flags, "NoThreading"):
        return flags.NoThreading
    return QgsProcessingAlgorithm.FlagNoThreading


class PrintLayoutAlgorithm(GeoCompAlgorithm):
    """Makes a print layout from a shipped or adapted template, filled with result layers."""

    TR_CONTEXT = "PrintLayoutAlgorithm"

    def displayName(self) -> str:
        return self.tr("Create print layout")

    def shortDescription(self) -> str:
        return self.tr(
            "A print layout for a network map, a displacement map or a quality map, ready to adapt."
        )

    def flags(self):
        # It adds a layout to the project, which only the main thread may do.
        return super().flags() | _no_threading()

    def help_body(self) -> str:
        return self.tr(
            "<p>Makes a print layout in the project from one of three templates: a network "
            "map with its error ellipses, a displacement map, and a quality map drawn by "
            "one of the thematic maps. The layout has the title, the map, a legend, a scale "
            "bar and a north arrow, and lands in the project's layout manager to edit, "
            "print or export like any other.</p>"
            "<p><b>The exaggeration is stated.</b> Every exaggerated layer names its factor, "
            "so the legend states it, and the notes say that the scale bar measures the map "
            "and not the ellipses or vectors.</p>"
            "<p>With no layers chosen, the layout draws the GeoComp result layers in the "
            "project that suit it, and any configured base map already there. A template of "
            "your own -- a shipped one adapted in the layout designer -- can be given "
            "instead; its items are found by their ids: title, map, legend, scalebar, "
            "north, notes, footer.</p>"
        )

    def initAlgorithm(self, config: dict[str, Any] | None = None) -> None:
        self.addParameter(
            QgsProcessingParameterEnum(
                TEMPLATE,
                self.tr("Deliverable"),
                options=[
                    self.tr("Network map with error ellipses"),
                    self.tr("Displacement map"),
                    self.tr("Quality map"),
                ],
                defaultValue=0,
            )
        )
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                LAYERS, self.tr("Layers (empty: the project's GeoComp result layers)"), optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                QUALITY,
                self.tr("Quality map drawn by"),
                options=[_theme_label(theme) for theme in QUALITY_THEMES],
                defaultValue=0,
            )
        )
        self.addParameter(
            QgsProcessingParameterString(TITLE, self.tr("Title"), defaultValue="", optional=True)
        )
        self.addAdvancedParameter(
            QgsProcessingParameterFile(
                TEMPLATE_FILE,
                self.tr("Template of your own (.qpt)"),
                extension="qpt",
                optional=True,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterString(
                NAME, self.tr("Layout name (empty: from the title)"), defaultValue="", optional=True
            )
        )
        self.addOutput(QgsProcessingOutputString(LAYOUT, self.tr("Layout")))

    def processAlgorithm(
        self,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> dict[str, Any]:
        from geocomp.resources import LAYOUTS_DIR

        project = context.project() or QgsProject.instance()
        template = TEMPLATES[self.parameterAsEnum(parameters, TEMPLATE, context)]
        layers = self._layers(parameters, context, project, template)

        path = self.parameterAsFile(parameters, TEMPLATE_FILE, context) or str(
            LAYOUTS_DIR / f"{template}.qpt"
        )
        layout = self._load(project, path)
        title = (self.parameterAsString(parameters, TITLE, context) or "").strip() or (
            self._default_title(template)
        )
        layout.setName(
            _unique(project, (self.parameterAsString(parameters, NAME, context) or "").strip() or title)
        )

        map_item = _item(layout, "map", QgsLayoutItemMap)
        if map_item is None:
            raise QgsProcessingException(
                self.tr("The template %1 has no map item with the id 'map'.").replace("%1", path)
            )
        drawn = layers + _base_maps(project)
        map_item.setLayers(drawn)
        map_item.setCrs(layers[0].crs())
        map_item.zoomToExtent(_extent(layers, map_item.crs(), project))

        theme = ""
        if template == "quality_map":
            theme = QUALITY_THEMES[self.parameterAsEnum(parameters, QUALITY, context)]
            shown = self._show_theme(map_item, layers, theme)
            if not shown:
                feedback.pushWarning(
                    self.tr(
                        "None of these layers has the '%1' map; they are drawn in their own "
                        "styles. Run the adjustment again to give its layers their thematic maps."
                    ).replace("%1", _theme_label(theme))
                )

        legend = _item(layout, "legend", QgsLayoutItemLegend)
        if legend is not None:
            legend.setLinkedMap(map_item)
            legend.setAutoUpdateModel(False)
            root = legend.model().rootGroup()
            root.clear()
            for layer in layers:
                root.addLayer(layer)
            legend.setTitle(self.tr("Legend"))
            legend.adjustBoxSize()

        scale = _item(layout, "scalebar", QgsLayoutItemScaleBar)
        if scale is not None:
            scale.setLinkedMap(map_item)
            scale.applyDefaultSize()
        north = _item(layout, "north", QgsLayoutItemPicture)
        if north is not None:
            north.setLinkedMap(map_item)

        _set_text(layout, "title", title)
        _set_text(layout, "notes", self._notes(layers, theme))
        _set_text(
            layout,
            "footer",
            self.tr("GeoComp %1 · %2")
            .replace("%1", _version())
            .replace("%2", map_item.crs().authid() or map_item.crs().description()),
        )

        project.layoutManager().addLayout(layout)
        feedback.pushInfo(
            self.tr("Layout '%1': %2 layer(s).").replace("%1", layout.name()).replace(
                "%2", str(len(layers))
            )
        )
        return {LAYOUT: layout.name()}

    # -- pieces ----------------------------------------------------------------------

    def _layers(self, parameters, context, project, template: str) -> list:
        from geocomp.algorithms.layer_outputs import RESULT_LAYER_PROPERTY

        chosen = self.parameterAsLayerList(parameters, LAYERS, context)
        if not chosen:
            kinds = KINDS[template]
            chosen = [
                layer
                for layer in project.mapLayers().values()
                if isinstance(layer, QgsVectorLayer)
                and layer.customProperty(RESULT_LAYER_PROPERTY) in kinds
            ]
        if not chosen:
            raise QgsProcessingException(
                self.tr(
                    "There is nothing to draw: no layers were chosen and the project holds no "
                    "GeoComp result layers for this map. Run an adjustment with its layers, or "
                    "choose the layers."
                )
            )
        # The layer tree's order, top first, which is what a map item draws by.
        order = {layer.id(): index for index, layer in enumerate(project.layerTreeRoot().layerOrder())}
        return sorted(chosen, key=lambda layer: order.get(layer.id(), len(order)))

    def _load(self, project, path: str) -> QgsPrintLayout:
        try:
            text = Path(path).read_text(encoding="utf-8")
        except OSError as error:
            raise QgsProcessingException(
                self.tr("The template %1 could not be read: %2").replace("%1", path).replace(
                    "%2", str(error)
                )
            ) from error
        document = QDomDocument()
        document.setContent(text)
        layout = QgsPrintLayout(project)
        _items, ok = layout.loadFromTemplate(document, QgsReadWriteContext())
        if not ok:
            raise QgsProcessingException(
                self.tr("The template %1 is not a QGIS layout template.").replace("%1", path)
            )
        return layout

    def _show_theme(self, map_item, layers, theme: str) -> int:
        """Hold the thematic style *theme* on the map item; return how many layers have it."""
        from geocomp.layers.themes import theme_labels

        label = theme_labels()[theme]
        overrides = {}
        for layer in layers:
            manager = layer.styleManager()
            if label in manager.styles():
                overrides[layer.id()] = manager.style(label).xmlData()
        if overrides:
            map_item.setKeepLayerStyles(True)
            map_item.setLayerStyleOverrides(overrides)
        return len(overrides)

    def _notes(self, layers, theme: str) -> str:
        notes = []
        factors = sorted({factor for layer in layers for factor in _exaggerations(layer)})
        if factors:
            notes.append(
                self.tr(
                    "Ellipses and vectors are drawn exaggerated, %1, as each legend entry "
                    "states. The scale bar measures the map, not them."
                ).replace("%1", ", ".join(f"{factor:g}x" for factor in factors))
            )
        if theme:
            notes.append(self.tr("Coloured by %1.").replace("%1", _theme_label(theme).lower()))
            if theme in ("mdb_displacement", "external_reliability", "positional_uncertainty"):
                notes.append(
                    self.tr(
                        "Its classes are fitted to this network, so the map is relative to "
                        "it; the legend states every bound."
                    )
                )
        return "\n".join(notes)

    def _default_title(self, template: str) -> str:
        return {
            "network_map": self.tr("Network map"),
            "displacement_map": self.tr("Displacement map"),
            "quality_map": self.tr("Network quality"),
        }[template]


def _theme_label(theme: str) -> str:
    from geocomp.layers.themes import theme_labels

    return theme_labels()[theme]


def _item(layout, item_id: str, kind):
    item = layout.itemById(item_id)
    return item if isinstance(item, kind) else None


def _set_text(layout, item_id: str, text: str) -> None:
    item = _item(layout, item_id, QgsLayoutItemLabel)
    if item is not None:
        item.setText(text)


def _exaggerations(layer) -> set[float]:
    index = layer.fields().indexFromName("exaggeration")
    if index < 0:
        return set()
    factors = set()
    for feature in layer.getFeatures():
        try:
            factors.add(float(feature[index]))
        except (TypeError, ValueError):
            continue
    return factors


def _extent(layers, crs, project) -> QgsRectangle:
    extent = None
    for layer in layers:
        box = QgsRectangle(layer.extent())
        if box.isNull():
            continue
        if layer.crs() != crs:
            box = QgsCoordinateTransform(layer.crs(), crs, project).transformBoundingBox(box)
        if extent is None:
            extent = box
        else:
            extent.combineExtentWith(box)
    if extent is None:
        return QgsRectangle()
    # A margin, and a floor for a single point, so a lone station is not drawn
    # at the edge of an extent of zero size.
    margin = max(extent.width(), extent.height()) * 0.1 or 10.0
    return QgsRectangle(
        extent.xMinimum() - margin,
        extent.yMinimum() - margin,
        extent.xMaximum() + margin,
        extent.yMaximum() + margin,
    )


def _base_maps(project) -> list:
    """The configured base maps already in the project, drawn beneath the results."""
    from geocomp.core.basemaps import load_catalogue
    from geocomp.core.errors import GeoCompError
    from geocomp.layers.basemaps import existing_base_map
    from geocomp.services.settings_service import settings

    try:
        catalogue = load_catalogue(settings.value("basemaps.catalogue"))
    except GeoCompError:
        return []
    found = [existing_base_map(service, project) for service in catalogue.services]
    return [layer for layer in found if layer is not None]


def _unique(project, name: str) -> str:
    manager = project.layoutManager()
    if manager.layoutByName(name) is None:
        return name
    counter = 2
    while manager.layoutByName(f"{name} ({counter})") is not None:
        counter += 1
    return f"{name} ({counter})"


def _version() -> str:
    from geocomp.core.version import __version__

    return __version__
