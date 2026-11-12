# SPDX-License-Identifier: GPL-2.0-or-later
"""The names of the menu windows, translated (FR-091).

A window's name is the label of its menu item and the title of the window.
Source strings are literals so the extractor finds them, keyed by the stable
names of :data:`geocomp.registry.WINDOWS`.

Where a window stands where an algorithm's launcher stood, it keeps the
algorithm's name -- *Traverse* is still *Traverse* -- because the operation is
the same one and the toolbox still calls it that. *Field book* is the one new
name: it is where observations are typed, and the algorithm that reads a
field-book *file* is *Import field book*, in the toolbox.
"""

from __future__ import annotations

from qgis.PyQt.QtCore import QCoreApplication

__all__ = ["window_label"]

_TR_CONTEXT = "GeoCompWindows"


def _tr(text: str) -> str:
    return QCoreApplication.translate(_TR_CONTEXT, text)


def window_label(name: str) -> str:
    """Translated name of the window *name*.

    An unknown name falls back to its own text rather than raising: a missing
    label is a cosmetic fault and should not stop the menu being built.
    """
    return {
        "totalstation_fieldbook": _tr("Field book"),
        "totalstation_preprocess": _tr("Generalised pre-processing"),
        "totalstation_traverse": _tr("Traverse"),
        "totalstation_radiation": _tr("3D radiation"),
        "totalstation_resection": _tr("Resection"),
        "totalstation_intersection": _tr("Forward intersection"),
        "totalstation_network": _tr("Classical network"),
        "totalstation_trig_levelling": _tr("Trigonometric levelling"),
        # A levelling field book is not a total station's, and the two are
        # named apart: the translations differ (caderneta de campo, caderneta de
        # nivelamento), and one source string can carry only one.
        "levelling_fieldbook": _tr("Levelling field book"),
        "levelling_equal_sights": _tr("Equal sights"),
        "levelling_equidistant_sights": _tr("Equidistant sights"),
        "levelling_extreme_sights": _tr("Extreme sights"),
        "levelling_closures": _tr("Closures and tolerances"),
        "levelling_network": _tr("Levelling network adjustment"),
    }.get(name, name.replace("_", " ").capitalize())
