# SPDX-License-Identifier: GPL-2.0-or-later
"""The RTKLIB / ``rnx2rtkp`` adapter (``specs/08-engine-rtklib.md``).

GeoComp targets ``rnx2rtkp`` from both Takasu's RTKLIB and the RTKLIB-EX fork:
the command-line interface and the output formats are compatible, so this is one
adapter with a distribution and version identifier attached (FR-302).
"""

from __future__ import annotations

from geocomp.engines.rtklib.config import (
    PROFILES,
    PositioningMode,
    RtklibConfig,
    parse_config,
    profile,
    write_config,
)
from geocomp.engines.rtklib.engine import (
    PROGRAM,
    RtklibEngine,
    RtklibJob,
    RtklibResult,
    command_line,
    parse_version,
    program_filenames,
)
from geocomp.engines.rtklib.read_pos import (
    PosEpoch,
    PosFormat,
    PosSolution,
    SolutionStatus,
    read_pos,
)

__all__ = [
    "PROFILES",
    "PROGRAM",
    "PosEpoch",
    "PosFormat",
    "PosSolution",
    "PositioningMode",
    "RtklibConfig",
    "RtklibEngine",
    "RtklibJob",
    "RtklibResult",
    "SolutionStatus",
    "command_line",
    "parse_config",
    "parse_version",
    "profile",
    "program_filenames",
    "read_pos",
    "write_config",
]
