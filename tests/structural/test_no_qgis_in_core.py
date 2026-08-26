# SPDX-License-Identifier: GPL-2.0-or-later
"""NFR-002: the geodetic core must not import QGIS or PyQt.

``specs/03-architecture.md`` section 1 gives four reasons -- testability,
reviewability by geodesists rather than QGIS developers, reuse outside QGIS, and
longevity across QGIS API changes. Reasons erode; a failing test does not.

The check is AST-based rather than textual, so a mention inside a docstring or a
comment (of which this package has many, deliberately) is not a false positive.
"""

from __future__ import annotations

import ast

from tests.conftest import PLUGIN_DIR, python_sources

FORBIDDEN_ROOTS = {"qgis", "PyQt5", "PyQt6", "PyQt", "processing"}


def _imported_roots(tree: ast.AST) -> set[str]:
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".", 1)[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level:  # relative import, cannot reach a third-party root
                continue
            if node.module:
                roots.add(node.module.split(".", 1)[0])
    return roots


def test_core_package_is_free_of_qgis_and_pyqt():
    offenders: list[str] = []
    core = PLUGIN_DIR / "core"
    assert core.is_dir(), "the core package must exist"

    for path in python_sources(core):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        forbidden = _imported_roots(tree) & FORBIDDEN_ROOTS
        if forbidden:
            offenders.append(f"{path.relative_to(PLUGIN_DIR.parent)}: {sorted(forbidden)}")

    assert not offenders, (
        "geocomp/core must not import qgis, PyQt or processing (NFR-002).\n"
        "Move the QGIS-facing part into geocomp/services or geocomp/gui.\n"
        + "\n".join(offenders)
    )


def test_core_is_importable_without_qgis():
    """The core imports in a plain interpreter -- the property the rule buys."""
    import importlib

    for module in (
        "geocomp.core.version",
        "geocomp.core.errors",
        "geocomp.core.cancellation",
        "geocomp.core.settings_def",
        "geocomp.core.settings_resolution",
        "geocomp.registry",
    ):
        importlib.import_module(module)
