# SPDX-License-Identifier: GPL-2.0-or-later
"""FR-005, ADR-0005 and ADR-0010: the menu, its windows and the algorithms cannot drift apart.

Many plugins grow a dialog that does the work and, separately, an algorithm that
does roughly the same work; the two diverge and users get different answers from
the menu and the toolbox. GeoComp's defence is that the menu is *generated* from
:mod:`geocomp.registry`, and that a menu window computes nothing: it runs the
algorithms the registry says it runs. This test holds both honest.

Until P14a it was ``test_menu_algorithm_parity.py``, and every algorithm had to
have a menu item or a written reason not to. Since ADR-0010 the menu holds
windows, so an algorithm is reached from the menu by being *run by a window* --
or, until its group is rebuilt, by a legacy launcher.

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
    WINDOWS,
    algorithms_run_by_windows,
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

    **A class whose name begins with an underscore is exempt**, because it is a
    shared base rather than an algorithm: the four GNSS modes differ by three
    class attributes and are one ``_GnssProcessAlgorithm`` underneath, and
    registering that base would put a menu entry on something with no
    ``displayName``. The underscore is the same privacy convention the rest of
    the codebase uses, so this is not a carve-out for one class -- but it is
    narrow: a *public* class still has to be registered or removed.
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
            if node.name.startswith("_"):
                continue
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


def test_every_algorithm_is_reached_from_the_menu_or_says_why_not():
    """An algorithm is run by a window, has a legacy launcher, or is a written exception.

    ADR-0010 makes "no menu item" the norm -- the menu holds windows -- but not
    "unreachable from the menu": an algorithm is reached through a window that
    runs it, and one that no window runs and that has no launcher must say why
    in ``TOOLBOX_ONLY_JUSTIFICATIONS``.
    """
    by_window = algorithms_run_by_windows()
    for spec in ALGORITHMS:
        if spec.menu is None and spec.name not in by_window:
            assert spec.name in TOOLBOX_ONLY_JUSTIFICATIONS, (
                f"{spec.id} has no launcher, no window runs it and no justification is recorded. "
                "Name it in a WindowSpec, give it a launcher, or add the reason to "
                "TOOLBOX_ONLY_JUSTIFICATIONS."
            )

    stale = set(TOOLBOX_ONLY_JUSTIFICATIONS) - {spec.name for spec in ALGORITHMS}
    assert not stale, f"justifications for algorithms that no longer exist: {sorted(stale)}"


def test_every_window_has_an_implementation():
    missing: list[str] = []
    for spec in WINDOWS:
        path = _module_path(spec.module)
        if not path.exists():
            missing.append(f"{spec.name}: module {spec.module} does not exist")
        elif spec.class_name not in _class_names(path):
            missing.append(f"{spec.name}: class {spec.class_name} not found in {spec.module}")
    assert not missing, "\n".join(missing)


def test_every_window_implementation_is_registered():
    """A window written but never declared is unreachable, and runs undeclared algorithms."""
    declared = {(spec.module, spec.class_name) for spec in WINDOWS}
    windows_dir = REPO_ROOT / "geocomp" / "gui" / "windows"
    unregistered: list[str] = []
    for path in sorted(windows_dir.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        dotted = ".".join(path.relative_to(REPO_ROOT).with_suffix("").parts)
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in tree.body:
            if not isinstance(node, ast.ClassDef) or node.name.startswith("_"):
                continue
            bases = {b.id for b in node.bases if isinstance(b, ast.Name)}
            # A technique's shared base names itself after the technique, and is
            # not a window: it has no steps of its own; nor is the one they share.
            shared = {"BookWindow", "TotalStationWindow", "LevelWindow"}
            if bases & ({"Workbench"} | shared) and node.name not in shared:
                if (dotted, node.name) not in declared:
                    unregistered.append(f"{dotted}.{node.name}")
    assert not unregistered, (
        "These window classes exist but are not declared in geocomp.registry.WINDOWS:\n"
        + "\n".join(unregistered)
    )


def test_a_window_stands_where_a_launcher_of_its_name_stood():
    """While a group is half rebuilt, a window and a launcher must not both
    offer the same operation: the user would get two items, one of each kind."""
    launched = {spec.name for spec in ALGORITHMS if spec.menu is not None}
    assert not {spec.name for spec in WINDOWS} & launched


def test_menu_module_builds_from_the_registry_not_a_hand_written_list():
    """Guards the mechanism itself: if someone hard-codes menu entries, the
    generation guarantee is gone even though every other test still passes."""
    source = (REPO_ROOT / "geocomp" / "gui" / "menu.py").read_text(encoding="utf-8")
    assert "MENU_GROUPS" in source, "menu.py must iterate the declared menu groups"
    assert "entries_in_menu" in source, "menu.py must pull its items from the registry"
