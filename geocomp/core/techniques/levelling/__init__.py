# SPDX-License-Identifier: GPL-2.0-or-later
"""Geometric levelling (FR-500 to FR-505).

``specs/10-module-levelling.md``. A small module with high leverage: it reuses
the adjustment core wholesale and delivers a complete second technique cheaply
(roadmap P4).

**And a third, later.** A gravity difference and a height difference are one
observation equation -- the same function in
:mod:`geocomp.core.adjustment.equations`, verified in
``tests/test_gravimetry_is_levelling.py`` (ADR-0002, Amendment 1). So the
weighting and datum work here is written for a **1D difference network** rather
than for levelling specifically, and phase P8 inherits it instead of writing it
again.
"""

from __future__ import annotations

from geocomp.core.techniques.levelling.closure import (
    ClosureCheck,
    SetupShare,
    line_closure,
    loop_closure,
)
from geocomp.core.techniques.levelling.line import (
    LevellingLine,
    LineReduction,
    SideShot,
    reduce_line,
    reverse_height_difference,
)
from geocomp.core.techniques.levelling.network import (
    Benchmark,
    LevellingNetworkResult,
    build_network,
    build_setup_network,
    weighting_for,
)
from geocomp.core.techniques.levelling.orthometric import (
    OrthometricCorrection,
    normal_orthometric_correction,
)
from geocomp.core.techniques.levelling.readings import (
    LevelSetup,
    StaffReading,
    ThreeWireReading,
    empirical_reading_sigma,
)
from geocomp.core.techniques.levelling.schemes import (
    ReciprocalPair,
    ReciprocalReduction,
    SetupReduction,
    reduce_reciprocal,
    reduce_setup,
)

__all__ = [
    "Benchmark",
    "ClosureCheck",
    "LevelSetup",
    "LevellingLine",
    "LevellingNetworkResult",
    "LineReduction",
    "OrthometricCorrection",
    "ReciprocalPair",
    "ReciprocalReduction",
    "SetupReduction",
    "SetupShare",
    "SideShot",
    "StaffReading",
    "ThreeWireReading",
    "build_network",
    "build_setup_network",
    "empirical_reading_sigma",
    "line_closure",
    "loop_closure",
    "normal_orthometric_correction",
    "reduce_line",
    "reduce_reciprocal",
    "reduce_setup",
    "reverse_height_difference",
    "weighting_for",
]
