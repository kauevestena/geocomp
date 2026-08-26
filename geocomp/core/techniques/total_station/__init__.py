# SPDX-License-Identifier: GPL-2.0-or-later
"""Total station: the largest technique module (FR-400 to FR-412).

``specs/09-module-total-station.md``. The pipeline, each stage separately
callable and separately inspectable, which is the teaching requirement from
``specs/01`` section 3:

    raw readings -> face reduction -> instrument corrections -> atmospheric
      correction -> EDM corrections -> geometric reductions -> observations

Uncertainty is propagated at every stage; no stage produces a bare float.
"""

from __future__ import annotations

from geocomp.core.techniques.total_station.atmosphere import (
    Atmosphere,
    AtmosphericCorrection,
    apply_atmospheric_correction,
    refractive_index,
    saturation_vapour_pressure,
)
from geocomp.core.techniques.total_station.corrections import (
    EdmCorrection,
    apply_edm_corrections,
    apply_instrument_corrections,
)
from geocomp.core.techniques.total_station.face import (
    FaceReduction,
    SetupDiagnostics,
    reduce_face_pair,
    reduce_single_face,
    setup_diagnostics,
)
from geocomp.core.techniques.total_station.pipeline import (
    PreprocessingOptions,
    ProcessedPointing,
    SetupResult,
    preprocess_setup,
    to_observations,
)
from geocomp.core.techniques.total_station.readings import (
    Face,
    FacePair,
    FaceReading,
    Setup,
)
from geocomp.core.techniques.total_station.reductions import (
    BasicReduction,
    GeometricReduction,
    curvature_and_refraction,
    reduce_basic,
    reduce_to_ellipsoid,
    reduce_to_projection,
    trigonometric_height,
)

__all__ = [
    "Atmosphere",
    "AtmosphericCorrection",
    "BasicReduction",
    "EdmCorrection",
    "Face",
    "FacePair",
    "FaceReading",
    "FaceReduction",
    "GeometricReduction",
    "PreprocessingOptions",
    "ProcessedPointing",
    "Setup",
    "SetupDiagnostics",
    "SetupResult",
    "apply_atmospheric_correction",
    "apply_edm_corrections",
    "apply_instrument_corrections",
    "curvature_and_refraction",
    "preprocess_setup",
    "reduce_basic",
    "reduce_face_pair",
    "reduce_single_face",
    "reduce_to_ellipsoid",
    "reduce_to_projection",
    "refractive_index",
    "saturation_vapour_pressure",
    "setup_diagnostics",
    "to_observations",
    "trigonometric_height",
]
