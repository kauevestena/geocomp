#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Write the print layout templates GeoComp ships (specs/19 section 6; phase P12b).

The ``.qpt`` files in ``geocomp/resources/layouts/`` are the artefact, exactly
as the QML styles are: an organisation adapts one in QGIS's layout designer
and saves over it, and *Create print layout* uses whatever is there. This
script only wrote the first version, through QGIS's own layout API so the XML
is what QGIS writes, and can rewrite them::

    QT_QPA_PLATFORM=offscreen python3 scripts/build_layout_templates.py

**Every item has an id**, which is how *Create print layout* finds what to fill:
``title``, ``map``, ``legend``, ``scalebar``, ``north``, ``notes`` (what the
exaggeration and the classes mean), ``footer``. A template missing one still
loads; that item is simply not filled.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT = REPO_ROOT / "geocomp" / "resources" / "layouts"

#: The three standard deliverables of specs/19 section 6, and their titles.
TEMPLATES = {
    "network_map": "Network map",
    "displacement_map": "Displacement map",
    "quality_map": "Network quality",
}


def _label(layout, item_id: str, text: str, x, y, w, h, size: float, bold: bool = False):
    from qgis.core import QgsLayoutItemLabel, QgsLayoutPoint, QgsLayoutSize, QgsTextFormat, QgsUnitTypes
    from qgis.PyQt.QtGui import QFont

    label = QgsLayoutItemLabel(layout)
    label.setId(item_id)
    label.setText(text)
    font = QFont("Sans Serif")
    font.setBold(bold)
    text_format = QgsTextFormat()
    text_format.setFont(font)
    text_format.setSize(size)
    label.setTextFormat(text_format)
    label.attemptMove(QgsLayoutPoint(x, y, QgsUnitTypes.LayoutMillimeters))
    label.attemptResize(QgsLayoutSize(w, h, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(label)
    return label


def build(name: str, title: str) -> Path:
    from qgis.core import (
        QgsLayoutItemLegend,
        QgsLayoutItemMap,
        QgsLayoutItemPage,
        QgsLayoutItemPicture,
        QgsLayoutItemScaleBar,
        QgsLayoutPoint,
        QgsLayoutSize,
        QgsPrintLayout,
        QgsProject,
        QgsReadWriteContext,
        QgsUnitTypes,
    )

    mm = QgsUnitTypes.LayoutMillimeters
    project = QgsProject()
    layout = QgsPrintLayout(project)
    layout.initializeDefaults()
    layout.setName(title)
    layout.pageCollection().page(0).setPageSize("A4", QgsLayoutItemPage.Landscape)

    _label(layout, "title", title, 10, 8, 277, 12, 18, bold=True)

    map_item = QgsLayoutItemMap(layout)
    map_item.setId("map")
    map_item.attemptMove(QgsLayoutPoint(10, 24, mm))
    map_item.attemptResize(QgsLayoutSize(200, 168, mm))
    map_item.setFrameEnabled(True)
    layout.addLayoutItem(map_item)

    legend = QgsLayoutItemLegend(layout)
    legend.setId("legend")
    legend.setTitle("Legend")
    legend.setLinkedMap(map_item)
    legend.attemptMove(QgsLayoutPoint(215, 24, mm))
    legend.attemptResize(QgsLayoutSize(72, 100, mm))
    layout.addLayoutItem(legend)

    scale = QgsLayoutItemScaleBar(layout)
    scale.setId("scalebar")
    scale.setLinkedMap(map_item)
    scale.applyDefaultSettings()
    scale.setStyle("Single Box")
    scale.attemptMove(QgsLayoutPoint(215, 128, mm))
    layout.addLayoutItem(scale)

    north = QgsLayoutItemPicture(layout)
    north.setId("north")
    north.setPicturePath(":/images/north_arrows/layout_default_north_arrow.svg")
    north.setLinkedMap(map_item)
    north.attemptMove(QgsLayoutPoint(270, 172, mm))
    north.attemptResize(QgsLayoutSize(16, 18, mm))
    layout.addLayoutItem(north)

    _label(layout, "notes", "", 215, 146, 52, 44, 8)
    _label(layout, "footer", "", 10, 196, 277, 6, 7)

    OUTPUT.mkdir(parents=True, exist_ok=True)
    path = OUTPUT / f"{name}.qpt"
    if not layout.saveAsTemplate(str(path), QgsReadWriteContext()):
        raise SystemExit(f"QGIS could not write {path}")
    return path


def main() -> int:
    from qgis.core import QgsApplication

    application = QgsApplication([], False)
    application.initQgis()
    for name, title in TEMPLATES.items():
        print(build(name, title).relative_to(REPO_ROOT))
    application.exitQgis()
    return 0


if __name__ == "__main__":
    sys.exit(main())
