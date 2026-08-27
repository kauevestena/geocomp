# SPDX-License-Identifier: GPL-2.0-or-later
"""Custom dialogs that run before the Processing one (``specs/15`` section 3).

A handful of algorithms cannot be driven by the generated Processing dialog
alone -- not because the parameters are unusual, but because choosing them needs
something the generated dialog has no way to show. Field mapping is the first:
picking which column feeds which field is guesswork without a preview of the
data in them.

**The custom dialog never replaces the algorithm.** It collects parameters and
hands them to the same Processing dialog every other menu item opens, so there
is exactly one implementation, reachable identically from the menu, the toolbox
and the graphical modeller. ADR-0005 is what this preserves: a menu item that
reimplemented its algorithm would be a second code path with a second set of
defaults, and the two would diverge.

Which algorithms have one, and why, is declared in
:data:`geocomp.registry.CUSTOM_DIALOGS`.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtWidgets import QDialog, QFileDialog, QWidget

from geocomp.registry import CUSTOM_DIALOGS, PROVIDER_ID

__all__ = ["collect_parameters", "has_custom_dialog"]

_TR_CONTEXT = "GeoCompPrompts"


def _tr(text: str) -> str:
    return QCoreApplication.translate(_TR_CONTEXT, text)


def has_custom_dialog(algorithm_id: str) -> bool:
    """Whether *algorithm_id* opens a custom dialog before the standard one."""
    return _operation(algorithm_id) in CUSTOM_DIALOGS


def collect_parameters(
    algorithm_id: str, parent: QWidget | None = None, canvas: Any = None
) -> dict[str, Any] | None:
    """Run the custom dialog and return the parameters it collected.

    Returns ``None`` when the user cancelled, which the caller must treat as
    "do nothing" rather than "run with defaults" -- opening the Processing
    dialog after a cancelled file chooser would be a confusing second prompt
    for something already declined.

    An algorithm with no custom dialog returns an empty mapping, so the caller
    can pass the result straight through without branching.

    Args:
        canvas: The map canvas, for the dialogs that edit on it. ``None`` where
            there is none, and a dialog that needs one then declines to open
            rather than presenting a design tool with no map under it.
    """
    handler = _HANDLERS.get(_operation(algorithm_id))
    if handler is None:
        return {}
    return handler(parent, canvas)


def _operation(algorithm_id: str) -> str:
    prefix = f"{PROVIDER_ID}:"
    return algorithm_id[len(prefix) :] if algorithm_id.startswith(prefix) else algorithm_id


def _field_mapping(parent: QWidget | None, _canvas: Any = None) -> dict[str, Any] | None:
    """Choose a field book, map its columns, and hand both to the algorithm.

    The mapping is written to a temporary file because the algorithm takes a
    path -- which is the right parameter type, since a mapping's whole value is
    that it can be saved once and distributed (``specs/17`` section 5.1). The
    dialog's own *Save mapping* button is how a user keeps one; this file is
    only the handoff.
    """
    from geocomp.gui.mapping_dialog import FieldMappingDialog

    source, _filter = QFileDialog.getOpenFileName(
        parent,
        _tr("Choose a field book"),
        "",
        _tr("Field books (*.csv *.txt);;All files (*)"),
    )
    if not source:
        return None

    dialog = FieldMappingDialog(source, parent=parent)
    if dialog.exec() != QDialog.DialogCode.Accepted:
        return None

    handle = tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", prefix="geocomp-mapping-", delete=False, encoding="utf-8"
    )
    with handle:
        json.dump(dialog.mapping().to_dict(), handle, indent=2, sort_keys=True)
        handle.write("\n")

    return {"SOURCE": source, "MAPPING": str(Path(handle.name))}


def _interactive_preanalysis(
    parent: QWidget | None, canvas: Any = None
) -> dict[str, Any] | None:
    """Place a design on the canvas, then evaluate it with the algorithm.

    The dialog is where the design is *built*; the numbers a user acts on still
    come from ``geocomp:analysis_network_preanalysis``, so an interactive design
    and one loaded from a file are evaluated by the same code (ADR-0005).

    Without a canvas there is nothing to place a design on, so the item falls
    back to the plain Processing dialog rather than opening a design tool with
    no map under it.
    """
    if canvas is None:
        return {}

    from geocomp.gui.preanalysis_dialog import PreAnalysisDialog

    dialog = PreAnalysisDialog(canvas, parent=parent)
    if dialog.exec() != QDialog.DialogCode.Accepted:
        return None

    handle = tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", prefix="geocomp-design-", delete=False, encoding="utf-8"
    )
    with handle:
        json.dump(dialog.network().to_dict(), handle, indent=2, sort_keys=True)
        handle.write("\n")

    return {"NETWORK": str(Path(handle.name))}


#: One handler per entry in :data:`geocomp.registry.CUSTOM_DIALOGS`. The two are
#: held equal by a structural test: a declared dialog with no handler would
#: leave a menu item promising something that never appears.
_HANDLERS = {
    "analysis_network_preanalysis": _interactive_preanalysis,
    "totalstation_import_fieldbook": _field_mapping,
}
