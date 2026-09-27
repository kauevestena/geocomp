# SPDX-License-Identifier: GPL-2.0-or-later
"""Integration: techniques adjusted together (``specs/13-module-integration.md``, phase P9)."""

from __future__ import annotations

from geocomp.core.techniques.integration.adjustment import CombinedAdjustment, adjust_combination
from geocomp.core.techniques.integration.breakdown import TechniqueSummary, technique_breakdown
from geocomp.core.techniques.integration.combine import (
    AppliedTransformation,
    Combination,
    Routing,
    Velocity,
    combine,
    route,
)
from geocomp.core.techniques.integration.techniques import TECHNIQUE_KEY, Technique, technique_of

__all__ = [
    "TECHNIQUE_KEY",
    "AppliedTransformation",
    "Combination",
    "CombinedAdjustment",
    "Routing",
    "Technique",
    "TechniqueSummary",
    "Velocity",
    "adjust_combination",
    "combine",
    "route",
    "technique_breakdown",
    "technique_of",
]
