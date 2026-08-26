# SPDX-License-Identifier: GPL-2.0-or-later
"""Bundled resources: icons, layer styles, templates.

Paths are resolved relative to this package so they work identically from a
development checkout and from an installed plugin ZIP.
"""

from __future__ import annotations

from pathlib import Path

__all__ = ["ICONS_DIR", "RESOURCES_DIR", "icon_path"]

RESOURCES_DIR = Path(__file__).parent
ICONS_DIR = RESOURCES_DIR / "icons"


def icon_path(name: str) -> str:
    """Absolute path to a bundled icon.

    Returns the path whether or not the file exists: ``QIcon`` renders an empty
    icon for a missing file, which is a cosmetic problem, whereas raising here
    would take down menu construction for a missing decoration.
    """
    return str(ICONS_DIR / name)
