# SPDX-License-Identifier: GPL-2.0-or-later
"""FR-005 / ADR-0005: the menu and the algorithm set cannot drift apart.

Many plugins grow a dialog that does the work and, separately, an algorithm that
does roughly the same work; the two diverge and users get different answers from
the menu and the toolbox. GeoComp's defence is that the menu is *generated* from
:mod:`geocomp.registry`, and this test holds that generation honest.

Deliberately AST-based: the registry names implementations by module path and
class name rather than importing them, so this whole check runs with **no QGIS
runtime** -- which is what lets it run on every commit rather than only in the
QGIS job.
"""

from __future__ import annotations

import ast

from geocomp.registry import (
    ALGORITHMS,
    MENU_GROUPS,
    PROCESSING_GROUPS,
    TOOLBOX_ONLY_JUSTIFICATIONS,
)
from tests.conftest import REPO_ROOT


def _module_path(dotted: str):
    return REPO_ROOT / (dotted.replace(".", "/") + ".py")


def _class_names(path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}


def test_every_registered_algorithm_has_an_implementation():
    missing: list[str] = []
    for spec in ALGORITHMS:
        path = _module_path(spec.module)
        if not path.exists():
            missing.append(f"{spec.id}: module {spec.module} does not exist")
        elif spec.class_name not in _class_names(path):
            missing.append(f"{spec.id}: class {spec.class_name} not found in {spec.module}")
    assert not missing, "\n".join(missing)


def test_every_algorithm_implementation_is_registered():
    """The other direction: a class written but never declared is unreachable.

    Scans the algorithms package for ``GeoCompAlgorithm`` subclasses and requires
    each to appear in the registry.
    """
    registered = {spec.class_name for spec in ALGORITHMS}
    unregistered: list[str] = []

    algorithms_dir = REPO_ROOT / "geocomp" / "algorithms"
    for path in sorted(algorithms_dir.rglob("*.py")):
        if path.name in ("__init__.py", "base.py") or "__pycache__" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            bases = {b.id for b in node.bases if isinstance(b, ast.Name)}
            if "GeoCompAlgorithm" in bases and node.name not in registered:
                unregistered.append(f"{path.relative_to(REPO_ROOT)}: {node.name}")

    assert not unregistered, (
        "These algorithm classes exist but are not declared in geocomp.registry, "
        "so they appear in neither the toolbox nor the menu:\n" + "\n".join(unregistered)
    )


def test_menu_placements_reference_declared_groups():
    menu_ids = {group.id for group in MENU_GROUPS}
    group_ids = {group.id for group in PROCESSING_GROUPS}
    for spec in ALGORITHMS:
        assert spec.group in group_ids, f"{spec.id}: unknown processing group {spec.group}"
        if spec.menu is not None:
            assert spec.menu in menu_ids, f"{spec.id}: unknown menu group {spec.menu}"


def test_toolbox_only_is_a_justified_exception_not_a_default():
    """ADR-0005 permits an algorithm without a menu route only for operations
    belonging to no survey technique, and only with the reason written down."""
    for spec in ALGORITHMS:
        if spec.menu is None:
            assert spec.name in TOOLBOX_ONLY_JUSTIFICATIONS, (
                f"{spec.id} has no menu route and no recorded justification. "
                "Give it a menu group, or add the reason to TOOLBOX_ONLY_JUSTIFICATIONS."
            )

    stale = set(TOOLBOX_ONLY_JUSTIFICATIONS) - {spec.name for spec in ALGORITHMS}
    assert not stale, f"justifications for algorithms that no longer exist: {sorted(stale)}"


def test_menu_module_builds_from_the_registry_not_a_hand_written_list():
    """Guards the mechanism itself: if someone hard-codes menu entries, the
    generation guarantee is gone even though every other test still passes."""
    source = (REPO_ROOT / "geocomp" / "gui" / "menu.py").read_text(encoding="utf-8")
    assert "MENU_GROUPS" in source, "menu.py must iterate the declared menu groups"
    assert "algorithms_in_menu" in source, "menu.py must pull its items from the registry"
