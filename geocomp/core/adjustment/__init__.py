# SPDX-License-Identifier: GPL-2.0-or-later
"""Least-squares adjustment (specs/06).

GeoComp implements its own adjustment *in addition to* driving DynAdjust
(ADR-0002). The reasons are concrete rather than a preference for building
things: gravimetric networks have no DynAdjust measurement type at all,
pre-analysis needs the design matrix before any observation exists, CI must run
without engine binaries, the teaching profile needs every intermediate visible,
and two independent implementations agreeing is the strongest correctness
evidence available -- which is what makes phase P6 a cross-validation.
"""

from __future__ import annotations

from geocomp.core.adjustment.difference_network import (
    ApproximateValues,
    approximate_values,
    connected_components,
)
from geocomp.core.adjustment.equations import SUPPORTED_TYPES, EquationRow, evaluate, supports
from geocomp.core.adjustment.parameters import Frame, ParameterLayout, ParameterSlot
from geocomp.core.adjustment.weighting import DifferenceWeighting, ExtentKind

__all__ = [
    "SUPPORTED_TYPES",
    "ApproximateValues",
    "DifferenceWeighting",
    "EquationRow",
    "ExtentKind",
    "Frame",
    "ParameterLayout",
    "ParameterSlot",
    "approximate_values",
    "connected_components",
    "evaluate",
    "supports",
]
