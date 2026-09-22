# SPDX-License-Identifier: GPL-2.0-or-later
"""A parsed ``.pos`` becomes a trajectory (FR-357, FR-356).

``specs/08-engine-rtklib.md`` section 7 and ``specs/11-module-gnss.md`` section
4.3. The companion of :mod:`geocomp.engines.rtklib.baseline`: that module turns
the last epoch of a relative run into one observation for the adjustment, this
one turns **every** epoch into a positioned point for the map.

All four output formats are handled, and each needs something different:

* ``llh`` and ``llh_dms`` are already geodetic -- degrees to radians, and the
  ``-g`` file's seven position columns collapse through
  :attr:`PosEpoch.decimal_position`, whose last three are otherwise a
  longitude's minutes, its seconds and the height.
* ``xyz`` is geocentric: one :func:`cartesian_to_geodetic`, and the covariance
  **rotated** -- not relabelled -- into the horizon at that epoch's own
  position.
* ``enu`` is a baseline from ``% ref pos``, which is written in geodetic degrees
  for this format. The point is the base in ECEF plus the rotated baseline, back
  to geodetic; the covariance is a permutation, because ENU and the local
  horizon are the same three axes in a different order.

**The rotation is at each epoch's own position, not at the first.** Over a
kinematic run of any extent the local vertical turns, and a covariance rotated
at the wrong place is wrong by that angle -- silently, since the numbers stay
plausible. It costs one 3x3 per epoch.
"""

from __future__ import annotations

import math

from geocomp.core.errors import DataError
from geocomp.core.geodesy.cartesian import (
    cartesian_to_geodetic,
    ecef_to_enu_covariance,
    enu_to_ecef,
    geodetic_to_cartesian,
)
from geocomp.core.geodesy.ellipsoid import ELLIPSOIDS, Ellipsoid
from geocomp.core.techniques.gnss.quality import EpochQuality
from geocomp.core.techniques.gnss.trajectory import (
    TrajectoryPoint,
    reorder_to_local,
)
from geocomp.engines.rtklib.read_pos import PosEpoch, PosFormat, PosSolution

__all__ = ["trajectory_from_solution"]

_GEODETIC = (PosFormat.LLH, PosFormat.LLH_DMS)


def trajectory_from_solution(
    solution: PosSolution, *, ellipsoid: Ellipsoid | None = None
) -> list[TrajectoryPoint]:
    """Every epoch of *solution* as a positioned point.

    Args:
        ellipsoid: Defaults to GRS80. ``rnx2rtkp`` labels its output WGS84; the
            two differ in flattening by about 0.1 mm of semi-minor axis, which
            is below what any of this resolves, and GRS80 is what the rest of
            GeoComp defaults to.

    Raises:
        DataError: if an ENU solution carries no ``% ref pos``. Without the base
            an ENU file holds three offsets from nowhere, and placing them at
            the geocentre would put the trajectory off the coast of Africa
            rather than failing.
    """
    shape = ellipsoid or ELLIPSOIDS["GRS80"]
    if solution.format in _GEODETIC:
        return [_from_geodetic(epoch) for epoch in solution.epochs]
    if solution.format is PosFormat.XYZ:
        return [_from_cartesian(epoch, shape) for epoch in solution.epochs]

    reference = solution.reference_position
    if reference is None:
        raise DataError(
            "pos_without_reference_position",
            file=str(solution.path),
            expected=(
                "a '% ref pos' header naming the base -- an ENU solution is "
                "offsets from it, and without it there is no position"
            ),
        )
    base = (math.radians(reference[0]), math.radians(reference[1]), reference[2])
    origin = geodetic_to_cartesian(*base, shape)
    return [_from_enu(epoch, base, origin, shape) for epoch in solution.epochs]


def _quality(epoch: PosEpoch) -> EpochQuality:
    return EpochQuality(
        time=epoch.time,
        status=epoch.status.name,
        satellites=epoch.satellites,
        ratio=epoch.ratio,
        age=epoch.age,
    )


def _from_geodetic(epoch: PosEpoch) -> TrajectoryPoint:
    latitude, longitude, height = epoch.decimal_position
    return TrajectoryPoint(
        latitude=math.radians(latitude),
        longitude=math.radians(longitude),
        height=height,
        # Already (n, e, u): the geodetic layouts name their deviations sdn,
        # sde, sdu in that order, which is what LOCAL_LABELS is.
        covariance=reorder_to_local(epoch.covariance),
        quality=_quality(epoch),
    )


def _from_cartesian(epoch: PosEpoch, shape: Ellipsoid) -> TrajectoryPoint:
    x, y, z = epoch.decimal_position
    latitude, longitude, height = cartesian_to_geodetic(x, y, z, shape)
    return TrajectoryPoint(
        latitude=latitude,
        longitude=longitude,
        height=height,
        # Rotate, then reorder. `enu_rotation`'s rows are east, north, up in
        # that order, so passing LOCAL_LABELS to the rotation would *relabel*
        # rows 0 and 1 rather than permute them -- north and east swapped, with
        # every number still plausible. Caught by the cross-format check in
        # `tests/test_gnss_trajectory.py`, which is why that test exists.
        covariance=reorder_to_local(
            ecef_to_enu_covariance(epoch.covariance, latitude, longitude)
        ),
        quality=_quality(epoch),
    )


def _from_enu(
    epoch: PosEpoch,
    base: tuple[float, float, float],
    origin: tuple[float, float, float],
    shape: Ellipsoid,
) -> TrajectoryPoint:
    east, north, up = epoch.decimal_position
    shift = enu_to_ecef((east, north, up), base[0], base[1])
    latitude, longitude, height = cartesian_to_geodetic(
        origin[0] + shift[0], origin[1] + shift[1], origin[2] + shift[2], shape
    )
    return TrajectoryPoint(
        latitude=latitude,
        longitude=longitude,
        height=height,
        # The components are already local -- at the *base*, where the file's
        # axes are defined. Reordering rather than re-rotating is therefore the
        # honest operation: re-rotating at the rover would be correcting for a
        # turn the engine never applied.
        covariance=reorder_to_local(epoch.covariance),
        quality=_quality(epoch),
    )
