# SPDX-License-Identifier: GPL-2.0-or-later
"""Shared fixtures and paths.

The tier-1 tests here run with **no QGIS and no engine binaries**
(``specs/20-testing-and-validation.md`` section 1). That is not a convenience:
it is what lets the geodetic mathematics be tested exhaustively in seconds, and
it is enforced for the core by ``structural/test_no_qgis_in_core.py``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN_DIR = REPO_ROOT / "geocomp"
SPECS_DIR = REPO_ROOT / "specs"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def plugin_dir() -> Path:
    return PLUGIN_DIR


@pytest.fixture(scope="session")
def specs_dir() -> Path:
    return SPECS_DIR


def python_sources(root: Path):
    """Yield every Python source file under *root*, skipping caches."""
    for path in sorted(root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        yield path


def has_qgis() -> bool:
    """Whether a QGIS runtime is importable.

    Tier-3 tests skip on this. In CI the QGIS job has it; a contributor running
    ``pytest`` locally without QGIS still gets the whole of tiers 1 and 2.
    """
    try:
        import qgis.core  # noqa: F401
    except Exception:  # noqa: BLE001 - any failure to import means "no QGIS here"
        return False
    return True


requires_qgis = pytest.mark.skipif(not has_qgis(), reason="requires a QGIS runtime")
