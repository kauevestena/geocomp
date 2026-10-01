# SPDX-License-Identifier: GPL-2.0-or-later
"""Multi-epoch comparison and structural monitoring (``specs/14``, phase P10a).

The pipeline of ``specs/14`` section 8, as functions: :func:`compare` checks two
epochs and brings them into one frame; :func:`analyse` tests the reference
block, refers the difference to it and tests every displacement; :func:`strain`
separates rigid-body motion from deformation; :func:`series` follows each
station through the epochs to a velocity; :func:`evaluate_alerts` flags what
crossed a threshold. :mod:`~geocomp.core.monitoring.document` writes what they
found as the documents the report, the layers and the time-series panel read.
"""

from __future__ import annotations

from geocomp.core.monitoring.alerts import (
    Alert,
    AlertKind,
    AlertThreshold,
    evaluate_alerts,
    thresholds_from_rows,
)
from geocomp.core.monitoring.compare import INDEPENDENCE_BIAS, Comparison, Finding, compare
from geocomp.core.monitoring.congruency import (
    DATUM_CHOICES,
    NOT_SIGNIFICANT,
    SIGNIFICANT,
    Congruency,
    DeformationAnalysis,
    Displacement,
    LocalisationStep,
    ReferenceCheck,
    analyse,
    check_reference,
    congruency,
    datum_basis,
    default_datum,
    s_matrix,
    s_transform,
)
from geocomp.core.monitoring.document import (
    comparison_document,
    epoch_metadata,
    read_comparison_document,
    read_series_document,
    refused_document,
    series_document,
)
from geocomp.core.monitoring.series import SeriesPoint, StationSeries, series
from geocomp.core.monitoring.strain import Strain, strain

__all__ = [
    "DATUM_CHOICES",
    "INDEPENDENCE_BIAS",
    "NOT_SIGNIFICANT",
    "SIGNIFICANT",
    "Alert",
    "AlertKind",
    "AlertThreshold",
    "Comparison",
    "Congruency",
    "DeformationAnalysis",
    "Displacement",
    "Finding",
    "LocalisationStep",
    "ReferenceCheck",
    "SeriesPoint",
    "StationSeries",
    "Strain",
    "analyse",
    "check_reference",
    "compare",
    "comparison_document",
    "congruency",
    "datum_basis",
    "default_datum",
    "epoch_metadata",
    "evaluate_alerts",
    "read_comparison_document",
    "read_series_document",
    "refused_document",
    "s_matrix",
    "s_transform",
    "series",
    "series_document",
    "strain",
    "thresholds_from_rows",
]
