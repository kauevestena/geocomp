# SPDX-License-Identifier: GPL-2.0-or-later
"""GNSS baselines and session quality (FR-602, FR-603, FR-104).

``specs/11-module-gnss.md`` sections 4 and 5. The *engine-agnostic* half of the
GNSS module: what a processed session becomes once it exists, independent of
which program produced it. The ``rnx2rtkp`` specifics -- running it, reading its
configuration and parsing its ``.pos`` -- are in
:mod:`geocomp.engines.rtklib`, and the bridge between them is
:mod:`geocomp.engines.rtklib.baseline`.

Like every technique package this imports no engine, no I/O module and no QGIS.
"""

from __future__ import annotations

from geocomp.core.techniques.gnss.baselines import (
    AntennaOffset,
    AntennaReduction,
    Baseline,
    components_from_covariance,
    independent_subset,
    reduce_to_marks,
    rotate_baseline_to_local,
    to_cluster,
)
from geocomp.core.techniques.gnss.quality import (
    EpochQuality,
    SessionQuality,
    summarise,
)

__all__ = [
    "AntennaOffset",
    "AntennaReduction",
    "Baseline",
    "EpochQuality",
    "SessionQuality",
    "components_from_covariance",
    "independent_subset",
    "reduce_to_marks",
    "rotate_baseline_to_local",
    "summarise",
    "to_cluster",
]
