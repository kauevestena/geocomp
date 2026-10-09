# SPDX-License-Identifier: GPL-2.0-or-later
"""Bundled resources: icons, layer styles, report and layout templates.

Paths are resolved relative to this package so they work identically from a
development checkout and from an installed plugin ZIP.
"""

from __future__ import annotations

from pathlib import Path

__all__ = [
    "DATASETS_DIR",
    "DATASET_ORDER",
    "ICONS_DIR",
    "LAYOUTS_DIR",
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
#: Print layout templates (``.qpt``) for the standard deliverables (P12b).
LAYOUTS_DIR = RESOURCES_DIR / "layouts"


def icon_path(name: str) -> str:
    """Absolute path to a bundled icon.

    Returns the path whether or not the file exists: ``QIcon`` renders an empty
    icon for a missing file, which is a cosmetic problem, whereas raising here
    would take down menu construction for a missing decoration.
    """
    return str(ICONS_DIR / name)


#: The order the datasets are offered in, which is published: *Install
#: tutorial dataset* takes its dataset as an enum, and a saved model stores the
#: index. Until P13-2 the order was the folders' names sorted, so a new dataset
#: whose name sorted before an existing one moved it -- ``rd04-loop`` would have
#: turned a model's ``rtklib-sample`` into the levelling loop. A new dataset is
#: appended here; ``tests/test_tutorial_dataset.py`` holds the list and the
#: folders to each other both ways.
DATASET_ORDER: tuple[str, ...] = (
    "rd01",
    "rtklib-sample",
    "rd04-loop",
    "rd08-dam",
    "rd07-usgs",
    "combined-curitiba",
    "ggao-triangle",
)


def available_datasets() -> list[str]:
    """The reference datasets that ship, in their published order.

    Read from the directory, so a dataset a build left out is not offered: the
    folders that exist, in :data:`DATASET_ORDER`, then any the order does not
    name yet, sorted -- which the tests refuse, so a build never ships one.
    """
    if not DATASETS_DIR.is_dir():
        return []
    present = {path.name for path in DATASETS_DIR.iterdir() if path.is_dir()}
    return [name for name in DATASET_ORDER if name in present] + sorted(present - set(DATASET_ORDER))


def dataset_dir(name: str) -> Path:
    """The folder of a shipped dataset. Returns the path whether or not it
    exists, so the caller can report a missing one in its own terms."""
    return DATASETS_DIR / name
