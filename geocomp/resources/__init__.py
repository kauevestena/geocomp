# SPDX-License-Identifier: GPL-2.0-or-later
"""Bundled resources: icons, layer styles, templates.

Paths are resolved relative to this package so they work identically from a
development checkout and from an installed plugin ZIP.
"""

from __future__ import annotations

from pathlib import Path

__all__ = [
    "DATASETS_DIR",
    "ICONS_DIR",
    "RESOURCES_DIR",
    "STYLES_DIR",
    "available_datasets",
    "dataset_dir",
    "icon_path",
]

RESOURCES_DIR = Path(__file__).parent
ICONS_DIR = RESOURCES_DIR / "icons"
STYLES_DIR = RESOURCES_DIR / "styles"
DATASETS_DIR = RESOURCES_DIR / "datasets"


def icon_path(name: str) -> str:
    """Absolute path to a bundled icon.

    Returns the path whether or not the file exists: ``QIcon`` renders an empty
    icon for a missing file, which is a cosmetic problem, whereas raising here
    would take down menu construction for a missing decoration.
    """
    return str(ICONS_DIR / name)


def available_datasets() -> list[str]:
    """The reference datasets that ship, in a stable order.

    Read from the directory rather than listed in code. A dataset is a folder
    of files, and a list that had to be edited alongside it would eventually
    disagree with it -- most likely by naming one that a build left out, which
    is the failure hardest to notice.
    """
    if not DATASETS_DIR.is_dir():
        return []
    return sorted(path.name for path in DATASETS_DIR.iterdir() if path.is_dir())


def dataset_dir(name: str) -> Path:
    """The folder of a shipped dataset. Returns the path whether or not it
    exists, so the caller can report a missing one in its own terms."""
    return DATASETS_DIR / name
