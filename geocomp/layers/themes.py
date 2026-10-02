# SPDX-License-Identifier: GPL-2.0-or-later
"""Thematic quality maps, as named styles on the result layers (FR-902; phase P12b).

``specs/19-visualization.md`` section 4: *networks are styled by positional
uncertainty; standardised residual; redundancy number; MDB; external
reliability; GNSS solution status; observation type; and epoch or campaign.*

**Each map is a named style on the layer that carries the attribute**, in QGIS's
own style manager: right-click the layer, *Styles*, and choose. There is no
separate layer per map to keep in step with the first, and no algorithm to
re-run to look at the same result another way; a project saved with the layer
keeps every style. The style the layer opens in is still its default -- the
w-test's decision on the residuals, the constraint on the stations -- renamed
from QGIS's "default" to say what it shows.

**The styles are QML files** in ``resources/styles/themes/`` (FR-904). Where an
attribute's scale belongs to the network -- an uncertainty, an MDB -- the file
fixes how each class looks and this module fits the class bounds to the values
present (:func:`geocomp.core.visualization.classes.fitted_bounds`); where it has
a meaning of its own -- a redundancy number, a ``|w|`` -- the file's bands
stand. Observation type and the GNSS status are already the default style of
the observations and trajectory layers; they need nothing here.
"""

from __future__ import annotations

import math

from qgis.core import QgsRendererCategory, QgsRendererRange
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtGui import QColor

from geocomp.core.visualization.classes import fitted_bounds
from geocomp.core.visualization.themes import THEMES, Theme
from geocomp.layers.styles import apply_style

__all__ = ["THEMES", "Theme", "add_thematic_styles", "theme_labels"]

_CONTEXT = "GeoCompLayers"

#: Okabe-Ito, in the order the epoch map assigns it: the categorical palette
#: that stays distinct under every common colour-vision deficiency.
_CATEGORY_COLOURS = (
    (0, 114, 178),
    (213, 94, 0),
    (0, 158, 115),
    (230, 159, 0),
    (204, 121, 167),
    (86, 180, 233),
    (0, 0, 0),
)


def _tr(text: str) -> str:
    return QCoreApplication.translate(_CONTEXT, text)


def theme_labels() -> dict[str, str]:
    """The name each style has in the layer's *Styles* menu, translated.

    Keyed by theme id, and by ``"default:<style>"`` for the style a layer opens
    in. Written out in full so the translation extractor finds each one.
    """
    return {
        "positional_uncertainty": _tr("Positional uncertainty"),
        "standardised_residual": _tr("Standardised residual"),
        "redundancy": _tr("Redundancy number"),
        "mdb_displacement": _tr("Minimal detectable bias"),
        "gravity_mdb": _tr("Minimal detectable bias"),
        "external_reliability": _tr("External reliability"),
        "epoch": _tr("Epoch"),
        "baseline_status": _tr("GNSS solution status"),
        "default:stations": _tr("Constraint"),
        "default:residuals": _tr("W-test decision"),
        "default:observations": _tr("Observation type"),
        "default:gnss_baselines": _tr("Independence"),
        "default:gravity_differences": _tr("W-test decision"),
    }


def add_thematic_styles(layer, style: str) -> list[str]:
    """Give *layer*, already styled as *style*, its thematic maps as named styles.

    The layer stays on its default style, renamed to say what it shows. A map
    whose attribute the layer holds no value of -- an epoch map of a network
    that states no epochs -- is not added: a style that draws every feature as
    *not stated* is a menu entry with nothing behind it. Returns the names
    added. Calling it twice adds nothing the second time.
    """
    themes = THEMES.get(style, ())
    if not themes:
        return []
    labels = theme_labels()
    manager = layer.styleManager()
    current = manager.currentStyle()
    default_label = labels.get(f"default:{style}", current)
    if current != default_label and default_label not in manager.styles():
        manager.renameStyle(current, default_label)
        current = default_label

    added: list[str] = []
    for theme in themes:
        label = labels[theme.id]
        if label in manager.styles():
            continue
        if theme.fit == "categories" and not _values(layer, theme.field):
            continue
        manager.addStyleFromLayer(label)
        manager.setCurrentStyle(label)
        if not apply_style(layer, f"themes/{theme.id}"):
            manager.setCurrentStyle(current)
            manager.removeStyle(label)
            continue
        if theme.fit == "quartiles":
            _fit_ranges(layer, theme)
        elif theme.fit == "categories":
            _fill_categories(layer, theme)
        added.append(label)
    manager.setCurrentStyle(current)
    return added


def _values(layer, field: str) -> list[float]:
    index = layer.fields().indexFromName(field)
    if index < 0:
        return []
    values: list[float] = []
    for feature in layer.getFeatures():
        value = feature[index]
        try:
            number = float(value)
        except (TypeError, ValueError):
            continue
        if math.isfinite(number):
            values.append(number)
    return values


def _unit(layer, theme: Theme) -> str:
    if theme.unit:
        return theme.unit
    index = layer.fields().indexFromName(theme.unit_field)
    if index < 0:
        return ""
    for feature in layer.getFeatures():
        if feature[index]:
            return str(feature[index])
    return ""


def _fit_ranges(layer, theme: Theme) -> None:
    """Replace the file's placeholder data classes with quartile bounds.

    The file's classes with negative bounds are not data -- uncheckable, not
    computed -- and are kept as they are. The others are templates: as many as
    there are, their symbols in order, from best to worst.
    """
    renderer = layer.renderer()
    ranges = list(renderer.ranges())
    special = [item for item in ranges if item.upperValue() < 0.0]
    templates = [item for item in ranges if item.upperValue() >= 0.0]
    bounds = fitted_bounds(_values(layer, theme.field), len(templates))
    classes = len(bounds) - 1
    unit = _unit(layer, theme)

    fitted: list[QgsRendererRange] = []
    for index in range(classes):
        # Fewer distinct values than templates: spread the symbols used across
        # the range, so one class is not drawn as if it were the best of four.
        source = templates[round(index * (len(templates) - 1) / max(classes - 1, 1))]
        lower, upper = bounds[index], bounds[index + 1]
        fitted.append(
            QgsRendererRange(
                lower, upper, source.symbol().clone(), _range_label(lower, upper, unit)
            )
        )
    renderer.deleteAllClasses()
    for item in special + fitted:
        renderer.addClassRange(item)
    layer.triggerRepaint()


def _range_label(lower: float, upper: float, unit: str) -> str:
    suffix = f" {unit}" if unit else ""
    if lower == upper:
        return f"{lower:.3g}{suffix}"
    return f"{lower:.3g} \u2013 {upper:.3g}{suffix}"


def _fill_categories(layer, theme: Theme) -> None:
    """One category per value present, in order, coloured in palette order."""
    renderer = layer.renderer()
    template = renderer.sourceSymbol()
    for position, value in enumerate(sorted(set(_values(layer, theme.field)))):
        symbol = template.clone()
        red, green, blue = _CATEGORY_COLOURS[position % len(_CATEGORY_COLOURS)]
        symbol.setColor(QColor(red, green, blue))
        renderer.addCategory(QgsRendererCategory(value, symbol, f"{value:.3f}"))
    # The file's own category -- no epoch stated -- goes after the epochs, so
    # the legend reads in time order and ends with what has none.
    if renderer.categories():
        renderer.moveCategory(0, len(renderer.categories()) - 1)
    layer.triggerRepaint()
