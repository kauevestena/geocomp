# SPDX-License-Identifier: GPL-2.0-or-later
"""Every ``Enum.MEMBER`` written in the plugin must be a member that exists.

A misspelled enum member is a runtime ``AttributeError`` on the line that runs
it, which in a dialog or a report branch may be a line no test without QGIS ever
reaches. One shipped: ``AngleFormat.SEXAGESIMAL_STRING``, for a member actually
called ``SEXAGESIMAL_TEXT``, sitting in the field-mapping dialog's label table.
It broke the dialog on construction and nothing here noticed, because the module
imports Qt and tier 1 cannot import it.

This check reads the *source* rather than importing it, so it covers the Qt-only
modules too. It resolves each enum from the module the file imports it from --
those live in ``core`` and ``io``, which import no Qt -- and then requires every
attribute access on that name to be a real member.

It is deliberately narrow. It does not try to resolve attributes on arbitrary
objects, only on names imported from a GeoComp module and found to be enums,
which is exactly the case that bit.
"""

from __future__ import annotations

import ast
import enum
import importlib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PLUGIN = REPO_ROOT / "geocomp"

#: Attributes every ``Enum`` class carries that are not members.
_NOT_MEMBERS = frozenset({"name", "value", "mro", "from_dict", "to_dict"} | set(dir(enum.Enum)))


def _sources() -> list[Path]:
    return sorted(path for path in PLUGIN.rglob("*.py") if "__pycache__" not in path.parts)


def _imported_enums(tree: ast.Module) -> dict[str, type[enum.Enum]]:
    """Names this module imports from GeoComp that turn out to be enums.

    A module that cannot be imported here is skipped rather than failed: that
    means it pulls in Qt, and its *enum* imports still resolve because the enums
    themselves live in the QGIS-free layers.
    """
    found: dict[str, type[enum.Enum]] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom) or not node.module:
            continue
        if not node.module.startswith("geocomp."):
            continue
        try:
            module = importlib.import_module(node.module)
        except ImportError:
            continue
        for alias in node.names:
            # `getattr` on a module can *raise*, not merely return the default:
            # a package with a lazy ``__getattr__`` resolves the name on access,
            # and `geocomp.reports` resolves its Qt-dependent half that way, so
            # asking for `ReportContext` here raises ModuleNotFoundError with no
            # QGIS. Guarding only `import_module` was enough until P5 made that
            # package lazy; a name that cannot be resolved is simply not an enum
            # this check can see, and skipping it is right.
            try:
                attribute = getattr(module, alias.name, None)
            except Exception:  # noqa: BLE001 - any failure means "cannot inspect"
                continue
            if isinstance(attribute, type) and issubclass(attribute, enum.Enum):
                found[alias.asname or alias.name] = attribute
    return found


def _bad_members(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    enums = _imported_enums(tree)
    if not enums:
        return []

    problems = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Attribute) or not isinstance(node.value, ast.Name):
            continue
        owner = enums.get(node.value.id)
        if owner is None or node.attr in _NOT_MEMBERS:
            continue
        if node.attr not in owner.__members__ and not hasattr(owner, node.attr):
            problems.append(
                f"{path.relative_to(REPO_ROOT)}:{node.lineno}: "
                f"{owner.__name__} has no member '{node.attr}'. "
                f"It has: {', '.join(sorted(owner.__members__))}"
            )
    return problems


@pytest.mark.parametrize("path", _sources(), ids=lambda p: str(p.relative_to(PLUGIN)))
def test_every_enum_member_reference_resolves(path):
    problems = _bad_members(path)
    assert not problems, "\n".join(problems)


def test_the_check_actually_resolves_some_enums():
    """Guards the resolution: if the import walk stopped finding enums, every
    assertion above would pass by having nothing to check."""
    checked = 0
    for path in _sources():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        checked += len(_imported_enums(tree))
    assert checked > 30, checked
