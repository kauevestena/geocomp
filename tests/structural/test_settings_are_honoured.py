# SPDX-License-Identifier: GPL-2.0-or-later
"""A declared setting must be read by something, or be listed as not yet read.

The Global Settings window is generated from ``core/settings_def.py``: declare a
``SettingDef`` and a control appears, resolving correctly through run, project
and global scope. Nothing generates the *use* of the value. A setting can
therefore be declared, labelled, translated, shown, stored, resolved and
recorded in provenance while no computation ever reads it -- and from the
outside it is indistinguishable from one that works.

The pre-P7 review found **36 of 47 declared settings in that state**. This is
the same shape as the defect phase P4 recorded one level up, when the dialog
rendered raw dotted keys for all seventeen settings P3 had declared: the dialog
is generated from the declarations, the labels were not, and nobody looked. The
labels are guarded now by ``test_settings_labels.py``. This file guards the
behaviour.

It cannot prove a setting is *honoured correctly* -- only that some module names
it. That is worth having anyway: it is the difference between a value nobody
reads and a value somebody reads, and every one of the 36 failed at the first
hurdle.
"""

from __future__ import annotations

import ast

from tests.conftest import PLUGIN_DIR

#: Where a setting is declared and where it is displayed. Naming a key in either
#: is not using it.
DECLARATION_SITES = ("core/settings_def.py", "gui/settings_dialog.py")

#: Settings that are declared and read by nothing, each with the phase that owes
#: the wiring. **Do not add to this list to make a new setting pass.** A setting
#: added here without a phase behind it is a control the user can change that
#: silently does nothing, which is worse than an absent control: it invites a
#: choice and then discards it.
#:
#: Empty since P12a, which wired the 36 the pre-P7 review found and three more
#: this test had been passing because a comment named them
#: (`specs/15-ui-menu-and-settings.md` section 2.3).
NOT_YET_HONOURED: dict[str, str] = {}


def _code_strings(text: str) -> set[str]:
    """Every string literal in *text* that is code: not a comment, not a docstring.

    Until P12a this test asked whether a key appeared *anywhere* in a module, and
    three settings passed on a comment alone -- ``stochastic.outlier_alpha``
    named in a remark about data snooping, and both face tolerances in a note
    that a core constant "mirrors" them. Nothing read any of the three. A key
    in a comment is a sentence about a setting, not a use of one.
    """
    tree = ast.parse(text)
    docstrings = {
        id(node.body[0].value)
        for node in ast.walk(tree)
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
        and node.body
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
        and isinstance(node.body[0].value.value, str)
    }
    return {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings
    }


def _readers() -> dict[str, list[str]]:
    """For each declared key, the modules naming it outside its declaration."""
    from geocomp.core.settings_def import SETTINGS

    sources = {
        path.relative_to(PLUGIN_DIR).as_posix(): _code_strings(path.read_text(encoding="utf-8"))
        for path in PLUGIN_DIR.rglob("*.py")
    }
    for site in DECLARATION_SITES:
        sources.pop(site, None)
    return {
        # Within a literal rather than equal to one: QGIS's own storage key is
        # the setting's behind a prefix, ``f"{SETTINGS_PREFIX}/interface.language"``.
        definition.key: sorted(
            name
            for name, strings in sources.items()
            if any(definition.key in text for text in strings)
        )
        for definition in SETTINGS
    }


def test_a_comment_is_not_a_reader():
    """Guards the scan against the false pass P12a found."""
    strings = _code_strings(
        '''"""Module docstring naming level.weighting."""
# A comment naming stochastic.outlier_alpha.
def f():
    """A docstring naming total_station.collimation_tolerance."""
    return settings.value("level.tolerance_coefficient")
'''
    )
    assert "level.tolerance_coefficient" in strings
    assert not any(
        "weighting" in text or "outlier_alpha" in text or "collimation" in text for text in strings
    )


def test_there_are_settings_to_check():
    """Guards the scan: an empty walk would make both checks below vacuous."""
    readers = _readers()
    assert len(readers) > 40
    assert any(readers.values()), "no setting is read by anything -- the scan is broken"


def test_every_declared_setting_is_read_or_declared_unread():
    unaccounted = sorted(
        key for key, users in _readers().items() if not users and key not in NOT_YET_HONOURED
    )
    assert not unaccounted, (
        "these settings are declared and read by nothing. A control the user can "
        "change that silently does nothing is worse than no control. Wire it, or "
        "add it to NOT_YET_HONOURED with the phase that will: " + str(unaccounted)
    )


def test_the_not_yet_honoured_list_has_no_stale_entries():
    """So that wiring one and forgetting the list cannot leave a false record."""
    readers = _readers()
    now_read = sorted(key for key in NOT_YET_HONOURED if readers.get(key))
    assert not now_read, (
        "these are listed as not yet honoured but something now reads them; "
        "remove them from NOT_YET_HONOURED: " + str(now_read)
    )
    undeclared = sorted(set(NOT_YET_HONOURED) - set(readers))
    assert not undeclared, (
        "NOT_YET_HONOURED names settings that are no longer declared: " + str(undeclared)
    )
