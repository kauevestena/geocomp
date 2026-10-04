# SPDX-License-Identifier: GPL-2.0-or-later
"""Every runtime dependency is one with a recorded decision (NFR-005).

A QGIS plugin cannot assume its user can run ``pip``, so NFR-005 asks that each
dependency beyond what QGIS ships be justified in writing. The writing is the
table in ``specs/03-architecture.md`` section 3.7. Until P12c-13 nothing held
the code to it, and two of the six packages GeoComp imports were missing from
it: ``psycopg2``, recorded only in specs/17, and QGIS's own ``processing``.

This reads every import in ``geocomp/`` and asks that each package outside the
standard library be one the table names, under one of the names it is known by.
"""

from __future__ import annotations

import ast
import sys

from tests.conftest import REPO_ROOT

PACKAGE = REPO_ROOT / "geocomp"
ARCHITECTURE = REPO_ROOT / "specs" / "03-architecture.md"

#: Each importable name, and how specs/03 section 3.7 names the dependency.
RECORDED = {
    "numpy": "NumPy",
    "scipy": "SciPy",
    "qgis": "`qgis.core`",
    "osgeo": "GDAL/OGR",
    "processing": "`processing`",
    "psycopg2": "`psycopg2`",
}


def _imported() -> dict[str, set[str]]:
    """Every top-level package imported anywhere in the plugin, and where."""
    found: dict[str, set[str]] = {}
    for path in PACKAGE.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names = [node.module]
            else:
                continue
            for name in names:
                top = name.split(".")[0]
                if top not in sys.stdlib_module_names and top not in {"geocomp", "__future__"}:
                    found.setdefault(top, set()).add(str(path.relative_to(REPO_ROOT)))
    return found


def _section() -> str:
    text = ARCHITECTURE.read_text(encoding="utf-8")
    return text.split("### 3.7 Dependencies", 1)[1].split("\n### ", 1)[0]


def test_the_scan_finds_the_dependencies_everyone_knows_about():
    """Guards the scan: one that found nothing would pass everything."""
    assert {"numpy", "qgis"} <= set(_imported())


def test_every_imported_package_has_a_recorded_decision():
    unrecorded = {name: sorted(where)[:3] for name, where in _imported().items() if name not in RECORDED}
    assert not unrecorded, f"imported with no decision in specs/03 section 3.7: {unrecorded}"


def test_every_recorded_name_is_in_the_table():
    table = [line for line in _section().splitlines() if line.startswith("| ")]
    for name, label in RECORDED.items():
        assert any(line.startswith(f"| {label} ") for line in table), (
            f"{name} is recorded here as {label!r}, and specs/03 section 3.7 has no such row"
        )
