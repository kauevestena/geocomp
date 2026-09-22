# SPDX-License-Identifier: GPL-2.0-or-later
"""A processed run as a sequence of positioned epochs (FR-357, FR-603).

``specs/11-module-gnss.md`` sections 3.2 and 4.3. The other half of FR-357: a
baseline is what a *static* session becomes and reaches the adjustment, while a
kinematic run is a time series that reaches the map instead. Engine-agnostic
like the rest of this package -- the ``.pos``-specific part, which of the four
output formats a file is in and how to get a coordinate out of each, lives in
:mod:`geocomp.engines.rtklib.trajectory`.

**Every point is in one frame, and it is the local horizon.** An engine writes
its covariance in whichever frame the run was configured for -- geocentric for
an ECEF run, east/north/up for a baseline run, north/east/up for a geodetic one
-- and a layer whose ``sigma`` columns meant a different thing per file would be
unreadable. So a :class:`TrajectoryPoint` carries its covariance rotated to
``(n, e, u)`` at its own position, which is also the frame in which a horizontal
and a vertical uncertainty are separable at all: those two numbers are what a
reader of a trajectory asks for, and neither exists in ECEF.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from geocomp.core.errors import DataError
from geocomp.core.techniques.gnss.quality import EpochQuality
from geocomp.core.uncertainty import Covariance
from geocomp.core.units import Unit

__all__ = ["LOCAL_LABELS", "TrajectoryPoint", "reorder_to_local"]

#: The component order every trajectory point's covariance is put in.
LOCAL_LABELS: tuple[str, str, str] = ("n", "e", "u")


@dataclass(frozen=True)
class TrajectoryPoint:
    """One epoch, positioned and with its quality attached.

    Attributes:
        latitude / longitude: Geodetic, **radians**, on the ellipsoid the engine
            worked with. Radians rather than degrees because everything else in
            ``core.geodesy`` is, and a mixed convention inside one package is
            how a factor of 57.3 gets lost.
        height: Above the **ellipsoid**, metres. Not orthometric: no ``.pos``
            file carries a geoid model, and labelling an ellipsoidal height as
            orthometric would be wrong by the undulation -- tens of metres in
            Brazil.
        covariance: 3x3 over :data:`LOCAL_LABELS`, metres.
        quality: The epoch's status, satellite count, ratio and age (FR-603).
            A position without it is a coordinate whose accuracy is unstated by
            two orders of magnitude.
    """

    latitude: float
    longitude: float
    height: float
    covariance: Covariance
    quality: EpochQuality
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.covariance.labels != LOCAL_LABELS:
            raise DataError(
                "trajectory_point_frame",
                received=str(self.covariance.labels),
                expected=(
                    f"a covariance over {LOCAL_LABELS} -- rotate it with "
                    "reorder_to_local before constructing the point"
                ),
            )

    @property
    def latitude_degrees(self) -> float:
        return math.degrees(self.latitude)

    @property
    def longitude_degrees(self) -> float:
        return math.degrees(self.longitude)

    @property
    def sigmas(self) -> tuple[float, float, float]:
        """North, east and up standard deviations, metres."""
        return tuple(  # type: ignore[return-value]
            float(v) for v in np.sqrt(np.diag(self.covariance.matrix))
        )

    @property
    def drms(self) -> float:
        """Distance root mean square: ``sqrt(sigma_n^2 + sigma_e^2)``.

        The conventional single number for horizontal accuracy, and named for
        what it is rather than called "horizontal accuracy" -- DRMS is about a
        63 to 68 per cent probability circle depending on how elongated the
        error ellipse is, not a 95 per cent one, and calling it accuracy invites
        the wrong reading.
        """
        north, east, _up = self.sigmas
        return math.hypot(north, east)


def reorder_to_local(covariance: Covariance) -> Covariance:
    """Permute a covariance already in local components into ``(n, e, u)``.

    For the ENU output format, whose components are the same three in a
    different order. A permutation, not a rotation: the matrix is reindexed and
    nothing is recomputed, so the correlations are carried exactly and no
    strategy is added -- there is no approximation to record.

    Raises:
        DataError: if the labels are not a permutation of ``(n, e, u)``. An ECEF
            covariance needs
            :func:`~geocomp.core.geodesy.cartesian.ecef_to_enu_covariance`,
            which is a rotation and a different operation entirely.
    """
    if set(covariance.labels) != set(LOCAL_LABELS):
        raise DataError(
            "trajectory_covariance_not_local",
            received=str(covariance.labels),
            expected=(
                f"a permutation of {LOCAL_LABELS}; a geocentric covariance is "
                "rotated by ecef_to_enu_covariance, not reordered"
            ),
        )
    if covariance.labels == LOCAL_LABELS:
        return covariance
    order = [covariance.labels.index(name) for name in LOCAL_LABELS]
    return Covariance(
        matrix=covariance.matrix[np.ix_(order, order)],
        labels=LOCAL_LABELS,
        units=(Unit.METRE,) * 3,
        mode=covariance.mode,
        strategies=covariance.strategies,
    )
