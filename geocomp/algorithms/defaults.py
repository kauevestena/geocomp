# SPDX-License-Identifier: GPL-2.0-or-later
"""Parameter defaults from the Global Settings (FR-068, FR-071; phase P12a).

``specs/15-ui-menu-and-settings.md`` section 2.3: before P12a, 36 declared
settings were read by nothing. The window let a user change the default
meteorology, the levelling tolerance or the confidence level, stored and
resolved the value correctly -- and every algorithm went on using a literal of
its own, so nothing changed. The numbers agreed at the defaults, which is why
nobody noticed.

**A parameter's default *is* its setting.** Each algorithm declares the
parameter with ``defaultValue=configured("section.key")``, read when the
algorithm is instantiated -- which Processing does for every dialog and every
run -- through the run, project and global scopes (FR-068). There is one value,
not a setting and a literal that happen to agree, and so:

* changing the setting changes what a run that does not override it computes;
* a parameter hidden in Basic mode runs at the setting, exactly as it would in
  Advanced mode left untouched (FR-071) -- the Basic/Advanced identity holds by
  construction, and ``tests/qgis/test_basic_advanced_identity.py`` checks it
  for every algorithm.

Keys are written out in full at each use, never composed: the structural test
that finds a setting's readers searches for the literal key.
"""

from __future__ import annotations

from typing import Any

__all__ = ["configured", "configured_epoch"]


def configured(key: str) -> Any:
    """The effective value of the setting *key*, to be used as a parameter default."""
    from geocomp.services.settings_service import settings

    return settings.value(key)


def configured_epoch(fallback: float) -> float:
    """The stated default reference epoch as a decimal year, or *fallback* when none is.

    ``reference_systems.default_epoch`` is zero until a user states one
    (``specs/15`` section 2.1: GeoComp does not assume an epoch). An algorithm
    whose parameter has always had a literal default keeps it as the fallback,
    so an unconfigured installation computes what it always did.
    """
    stated = float(configured("reference_systems.default_epoch") or 0.0)
    return stated if stated > 0.0 else fallback
