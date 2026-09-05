# SPDX-License-Identifier: GPL-2.0-or-later
"""Applying the shipped QML styles (FR-904, FR-905).

``specs/19`` section 2: code applies a style, it does not *contain* one. A
renderer built in Python cannot be edited in the layer properties dialog, and a
user preparing a report against their own template needs to restyle without
touching the plugin.

So the styles live in ``geocomp/resources/styles/`` as ordinary QML, which is
the format QGIS itself writes when a user saves a style. Restyling the layer
and saving over the file is the supported way to change what GeoComp produces.
"""

from __future__ import annotations

from pathlib import Path

from qgis.PyQt.QtCore import QCoreApplication

from geocomp.resources import STYLES_DIR
from geocomp.services.logging import log

__all__ = ["STYLE_DIR", "apply_style", "style_path"]

#: Re-exported so callers that only want a style path need one import.
STYLE_DIR = STYLES_DIR

_CONTEXT = "GeoCompLayers"


def _tr(text: str) -> str:
    return QCoreApplication.translate(_CONTEXT, text)


def style_path(name: str) -> Path:
    """The QML file for *name*, e.g. ``"stations"``."""
    return STYLE_DIR / f"{name}.qml"


def apply_style(layer, name: str) -> bool:
    """Apply the shipped style *name* to *layer*.

    A missing or unloadable style is logged and survived rather than raised.
    The layer with its data is worth far more than the styling of it, and an
    adjustment that refused to produce results because a QML file failed to
    parse would be trading the whole output for a cosmetic problem.

    Returns whether the style was applied, so a caller that does care can tell.
    """
    path = style_path(name)
    if not path.is_file():
        log.warning(
            _tr("The style file '%1' is missing, so the layer is unstyled.").replace(
                "%1", str(path)
            )
        )
        return False

    message, ok = layer.loadNamedStyle(str(path))
    if not ok:
        log.warning(
            _tr("The style file '%1' could not be applied: %2")
            .replace("%1", str(path))
            .replace("%2", str(message))
        )
        return False
    layer.triggerRepaint()
    return True
