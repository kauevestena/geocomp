# SPDX-License-Identifier: GPL-2.0-or-later
"""Custom dialogs stay enumerated and stay wired (``specs/15`` section 3).

Most menu items open the generated Processing dialog. A small, enumerated set
opens a custom one first, because choosing their parameters needs something the
generated dialog cannot show. Every custom dialog is a place the UI stops being
generated and starts having to be maintained, which is why the set is small and
why each member records its reason.

Two failures are worth catching without QGIS. A declared dialog with no handler
leaves a menu item promising something that never appears; a handler for an
algorithm nobody registered is dead code that will be copied when the next one
is written.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from geocomp.registry import ALGORITHMS, CUSTOM_DIALOGS

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PROMPTS = REPO_ROOT / "geocomp" / "gui" / "prompts.py"
SPEC = REPO_ROOT / "specs" / "15-ui-menu-and-settings.md"


def _handlers() -> set[str]:
    """The keys of ``_HANDLERS``, read by parsing -- the module imports Qt."""
    tree = ast.parse(PROMPTS.read_text(encoding="utf-8"), filename=str(PROMPTS))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "_HANDLERS" for target in node.targets
        ):
            assert isinstance(node.value, ast.Dict)
            return {key.value for key in node.value.keys if isinstance(key, ast.Constant)}
    raise AssertionError("prompts.py declares no _HANDLERS table")


def test_every_declared_dialog_has_a_handler():
    assert set(CUSTOM_DIALOGS) == _handlers()


def test_every_declared_dialog_names_a_registered_algorithm():
    registered = {spec.name for spec in ALGORITHMS}
    assert set(CUSTOM_DIALOGS) <= registered


@pytest.mark.parametrize("operation", sorted(CUSTOM_DIALOGS))
def test_each_records_why_the_generated_dialog_is_insufficient(operation):
    """A reason is what stops the list growing: "it would be nicer" does not
    survive being written down next to the others."""
    reason = CUSTOM_DIALOGS[operation]
    assert len(reason) > 80
    assert "FR-" in reason


@pytest.mark.parametrize("operation", sorted(CUSTOM_DIALOGS))
def test_each_is_the_one_the_specification_enumerates(operation):
    """``specs/15`` section 3 lists them in a table. A dialog in the code that
    is not in the table is one nobody agreed to maintain."""
    requirement = CUSTOM_DIALOGS[operation].rsplit("FR-", 1)[1][:3]
    assert f"FR-{requirement}" in SPEC.read_text(encoding="utf-8")


def test_the_set_stays_small():
    """Not arbitrary: a growing list means the generated UI is being abandoned
    a dialog at a time. ``specs/15`` enumerates six across the whole project."""
    assert len(CUSTOM_DIALOGS) <= 6
