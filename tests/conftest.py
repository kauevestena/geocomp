# SPDX-License-Identifier: GPL-2.0-or-later
"""Shared fixtures and paths.

The tier-1 tests here run with **no QGIS and no engine binaries**
(``specs/20-testing-and-validation.md`` section 1). That is not a convenience:
it is what lets the geodetic mathematics be tested exhaustively in seconds, and
it is enforced for the core by ``structural/test_no_qgis_in_core.py``.
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN_DIR = REPO_ROOT / "geocomp"
SPECS_DIR = REPO_ROOT / "specs"
KRUMM_DIR = REPO_ROOT / "tests" / "data" / "krumm"

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


def has_dynadjust() -> bool:
    """Whether a DynAdjust suite is on ``PATH``.

    Tier-4 tests skip on this. Almost everything about the DynAdjust adapter is
    tested against committed output instead, which is deliberate: the engine
    tier is for what only a real engine can show -- that the files GeoComp
    writes are ones DynAdjust accepts, and that the pipeline drives it to a
    solution -- not for the parsing, which fixtures cover better because they
    pin the exact bytes.
    """
    return all(shutil.which(program) for program in ("dnaimport", "dnaadjust"))


requires_dynadjust = pytest.mark.skipif(
    not has_dynadjust(), reason="requires the DynAdjust programs on PATH (tier 4)"
)


def krumm_corpus() -> Path | None:
    """Where the Krumm example networks are.

    ``tests/data/krumm/`` -- vendored, so the reference tests are part of the
    ordinary suite rather than something a contributor has to opt into. They are
    GNU Gama's files at a pinned commit, copied unchanged; ``PROVENANCE.md``
    beside them records the chain and ``scripts/check_krumm_corpus.py`` proves
    the copy is verbatim.

    ``GEOCOMP_KRUMM_DIR`` still overrides, which is what you want when checking
    the reader against a *different* revision of the corpus.
    """
    override = os.environ.get("GEOCOMP_KRUMM_DIR")
    path = Path(override) if override else KRUMM_DIR
    return path if (path / "2D").is_dir() else None


requires_krumm = pytest.mark.skipif(
    krumm_corpus() is None,
    reason="tests/data/krumm is missing, and GEOCOMP_KRUMM_DIR names no corpus either",
)
