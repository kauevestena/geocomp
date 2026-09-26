# SPDX-License-Identifier: GPL-2.0-or-later
"""Relative and absolute gravimetry (FR-700 to FR-703).

``specs/12-module-gravimetry.md``. The adjustment is not new here: a gravity
difference and a height difference are one observation equation, and the core
has adjusted both since phase P2 (ADR-0002, Amendment 1). What this package
adds is everything *around* it, which no external engine supplies:

* :mod:`.tides` -- the solid-Earth tide, by Longman (1959), checked against
  ETERNA and against a CG-5's own firmware.
* :mod:`.readings` -- a reading on the calibrated scale, tide-free, at its
  mark, with every term's uncertainty carried.
* :mod:`.drift` -- the two drift treatments and when each is possible.
* :mod:`.network` -- occupations, differences with their exact covariance,
  absolute values weighted, and a result that states its datum, its drift and
  its uncheckable observations.

The instrument itself -- calibration table, factor and precision -- lives with
the other instruments, in :mod:`geocomp.core.instruments.gravimeter`.
"""

from __future__ import annotations

from geocomp.core.techniques.gravimetry.drift import (
    DEFAULT_TIME_SCALE,
    DriftEstimate,
    DriftMode,
    DriftOptions,
    DriftTreatment,
    drift_is_estimable,
)
from geocomp.core.techniques.gravimetry.network import (
    AbsoluteGravity,
    DatumReport,
    DriftPreview,
    GravityNetwork,
    GravityNetworkResult,
    Occupation,
    SessionReport,
    TreatmentComparison,
    adjust_gravity_network,
    build_gravity_network,
    compare_treatments,
    drift_previews,
    group_occupations,
)
from geocomp.core.techniques.gravimetry.readings import (
    NORMAL_FREE_AIR_GRADIENT,
    GravityReading,
    ReducedReading,
    ReductionOptions,
    reduce_readings,
)
from geocomp.core.techniques.gravimetry.tides import (
    DEFAULT_AMPLIFICATION,
    MODEL_UNCERTAINTY,
    TIDE_SYSTEM,
    TideModel,
    tidal_correction,
)

__all__ = [
    "DEFAULT_AMPLIFICATION",
    "DEFAULT_TIME_SCALE",
    "MODEL_UNCERTAINTY",
    "NORMAL_FREE_AIR_GRADIENT",
    "TIDE_SYSTEM",
    "AbsoluteGravity",
    "DatumReport",
    "DriftEstimate",
    "DriftMode",
    "DriftOptions",
    "DriftPreview",
    "DriftTreatment",
    "GravityNetwork",
    "GravityNetworkResult",
    "GravityReading",
    "Occupation",
    "ReducedReading",
    "ReductionOptions",
    "SessionReport",
    "TideModel",
    "TreatmentComparison",
    "adjust_gravity_network",
    "build_gravity_network",
    "compare_treatments",
    "drift_is_estimable",
    "drift_previews",
    "group_occupations",
    "reduce_readings",
    "tidal_correction",
]
