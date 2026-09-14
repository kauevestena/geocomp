# SPDX-License-Identifier: GPL-2.0-or-later
"""The RTKLIB / ``rnx2rtkp`` adapter (``specs/08-engine-rtklib.md``).

GeoComp targets ``rnx2rtkp`` from both Takasu's RTKLIB and the RTKLIB-EX fork:
the command-line interface and the output formats are compatible, so this is one
adapter with a distribution and version identifier attached (FR-302).
"""

from __future__ import annotations

from geocomp.engines.rtklib.read_pos import (
    PosEpoch,
    PosFormat,
    PosSolution,
    SolutionStatus,
    read_pos,
)

__all__ = [
    "PosEpoch",
    "PosFormat",
    "PosSolution",
    "SolutionStatus",
    "read_pos",
]
