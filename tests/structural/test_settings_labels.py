# SPDX-License-Identifier: GPL-2.0-or-later
"""FR-060, FR-091: every setting reaches the dialog with a translated label.

The Global Settings window is *generated* from
:data:`~geocomp.core.settings_def.SETTINGS` (``specs/15`` section 2), so a new
setting appears in the UI the moment it is declared -- which is the point. What
does not follow automatically is its **name**: ``setting_label`` falls back to
the dotted key, so a setting nobody labelled renders as
``total_station.atmospheric_model`` in every language, including English.

That is exactly what happened. Phase P3 declared seventeen settings and labelled
none of them; nobody noticed until phase P4 opened the same dialog to add the
Level section. A generated UI needs a generated-UI check.

Parsed rather than imported: ``settings_dialog`` imports Qt, and this must run
in the tier-1 job that has no QGIS (``specs/20`` section 2).
"""

from __future__ import annotations

import ast

from geocomp.core.settings_def import SECTIONS, SETTINGS
from tests.conftest import PLUGIN_DIR

DIALOG = PLUGIN_DIR / "gui" / "settings_dialog.py"


def _mapping_keys(function_name: str) -> set[object]:
    """The literal dict keys returned by *function_name* in the dialog module.

    Reads the ``return {...}.get(...)`` form the three label functions share. A
    tuple key (used by ``choice_label``) comes back as a tuple of strings.
    """
    tree = ast.parse(DIALOG.read_text(encoding="utf-8"), filename=str(DIALOG))
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef) or node.name != function_name:
            continue
        for inner in ast.walk(node):
            if not isinstance(inner, ast.Dict):
                continue
            keys: set[object] = set()
            for key in inner.keys:
                if isinstance(key, ast.Constant):
                    keys.add(key.value)
                elif isinstance(key, ast.Tuple) and all(
                    isinstance(element, ast.Constant) for element in key.elts
                ):
                    keys.add(tuple(element.value for element in key.elts))
            return keys
    raise AssertionError(f"{function_name} not found in {DIALOG}")


def test_the_parser_finds_the_mappings():
    """Guards the introspection: an empty result would make the rest pass
    vacuously, which is the failure mode this whole file exists to prevent."""
    assert len(_mapping_keys("setting_label")) > 10
    assert len(_mapping_keys("section_label")) == len(SECTIONS)
    assert len(_mapping_keys("choice_label")) > 10


def test_every_setting_has_a_label():
    labelled = _mapping_keys("setting_label")
    missing = sorted(setting.key for setting in SETTINGS if setting.key not in labelled)
    assert not missing, (
        "These settings would render as their raw dotted key in the Global "
        "Settings dialog. Add each to setting_label() in "
        "geocomp/gui/settings_dialog.py:\n" + "\n".join(missing)
    )


def test_every_choice_has_a_label():
    labelled = _mapping_keys("choice_label")
    missing = sorted(
        f"{setting.key} = {choice}"
        for setting in SETTINGS
        for choice in (setting.choices or ())
        if (setting.key, choice) not in labelled
    )
    assert not missing, (
        "These choice values would render as their stored string. Add each to "
        "choice_label() in geocomp/gui/settings_dialog.py:\n" + "\n".join(missing)
    )


def test_every_section_has_a_label():
    labelled = _mapping_keys("section_label")
    missing = sorted(section.id for section in SECTIONS if section.id not in labelled)
    assert not missing, f"unlabelled settings sections: {missing}"


def test_no_stale_labels():
    """A label for a setting that no longer exists is dead weight, and hides the
    fact that the setting it named was renamed rather than removed."""
    keys = {setting.key for setting in SETTINGS}
    stale = sorted(str(key) for key in _mapping_keys("setting_label") if key not in keys)
    assert not stale, f"labels for settings that no longer exist: {stale}"

    pairs = {
        (setting.key, choice) for setting in SETTINGS for choice in (setting.choices or ())
    }
    stale_choices = sorted(
        str(key) for key in _mapping_keys("choice_label") if key not in pairs
    )
    assert not stale_choices, f"labels for choices that no longer exist: {stale_choices}"
