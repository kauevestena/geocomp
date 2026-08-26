# SPDX-License-Identifier: GPL-2.0-or-later
"""The GeoComp domain model.

``specs/04-data-model.md``. Pure Python: nothing here imports QGIS, so the whole
model is testable and reviewable without a QGIS runtime (NFR-002).

Three rules run through all of it, and each exists because breaking it produces
a plausible-looking wrong answer rather than an error:

* **Every geodetic value carries its uncertainty** (FR-200). Positions and
  observations hold :class:`~geocomp.core.uncertainty.Quantity`, never a float.
* **Every coordinate set carries its CRS and epoch** (FR-105). Operations that
  need an epoch refuse a set that has none rather than assuming one.
* **Correlated observations stay clustered** (FR-104). A GNSS baseline is one
  three-component observation with a 3x3 covariance, not three scalars.
"""

from __future__ import annotations

from geocomp.core.models.epoch import Epoch, require_epoch
from geocomp.core.models.network import Campaign, GnssSession, Network, Project
from geocomp.core.models.observation import (
    OBSERVATION_TYPES,
    Cluster,
    ClusterKind,
    Observation,
    ObservationStatus,
    ObservationType,
    ObservationTypeSpec,
    RejectionRecord,
    observation_type_spec,
)
from geocomp.core.models.position import CoordinateSystem, HeightType, Position
from geocomp.core.models.solution import (
    AdjustedStation,
    AdjustmentStatistics,
    DatumDefinition,
    ErrorEllipse,
    ObservationResult,
    Provenance,
    Solution,
    SolutionKind,
    TestResult,
)
from geocomp.core.models.station import (
    ConstraintMode,
    ConstraintSpec,
    MonitoringRole,
    Station,
    StationType,
)

__all__ = [
    "OBSERVATION_TYPES",
    "AdjustedStation",
    "AdjustmentStatistics",
    "Campaign",
    "Cluster",
    "ClusterKind",
    "ConstraintMode",
    "ConstraintSpec",
    "CoordinateSystem",
    "DatumDefinition",
    "Epoch",
    "ErrorEllipse",
    "GnssSession",
    "HeightType",
    "MonitoringRole",
    "Network",
    "Observation",
    "ObservationResult",
    "ObservationStatus",
    "ObservationType",
    "ObservationTypeSpec",
    "Position",
    "Project",
    "Provenance",
    "RejectionRecord",
    "Solution",
    "SolutionKind",
    "Station",
    "StationType",
    "TestResult",
    "observation_type_spec",
    "require_epoch",
]
