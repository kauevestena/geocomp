# SPDX-License-Identifier: GPL-2.0-or-later
"""External process adapters (FR-303).

``specs/03-architecture.md`` section 3.3. One interface -- detect, prepare, run,
parse -- so that adding an engine does not change any calling code, and so that
DynAdjust's output and the in-house core's are the same
:class:`~geocomp.core.models.Solution` (FR-323).

Nothing here imports Qt. The one part that needs it, downloading through the
user's configured proxy, takes an injected fetcher instead
(:mod:`geocomp.engines.manager`), so that verification and extraction -- where
the security is -- are tested in every CI job rather than only the one with
QGIS.
"""

from __future__ import annotations

from geocomp.engines.base import (
    DEFAULT_TIMEOUT,
    Engine,
    EngineAbsentError,
    EngineRun,
    EngineVersion,
    discover,
    require,
    run_process,
)
from geocomp.engines.manager import (
    PINNED,
    EngineRelease,
    EngineStatus,
    extract,
    install,
    installation_root,
    locate,
    verify,
)

__all__ = [
    "DEFAULT_TIMEOUT",
    "PINNED",
    "Engine",
    "EngineAbsentError",
    "EngineRelease",
    "EngineRun",
    "EngineStatus",
    "EngineVersion",
    "discover",
    "extract",
    "install",
    "installation_root",
    "locate",
    "require",
    "run_process",
    "verify",
]
