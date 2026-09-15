# SPDX-License-Identifier: GPL-2.0-or-later
"""A parsed ``.pos`` becomes a baseline observation (FR-602, FR-206).

``specs/08-engine-rtklib.md`` section 8. The bridge between
:mod:`geocomp.engines.rtklib.read_pos`, which knows the file format, and
:mod:`geocomp.core.techniques.gnss.baselines`, which knows what a baseline is
and imports no engine. Everything here is what makes this *RTKLIB's* baseline
rather than a baseline in general.

## 1. The ECEF baseline is a subtraction, and needs no rotation

``rnx2rtkp -e`` writes the rover's absolute ECEF position per epoch and its base
in the ``% ref pos`` header. In relative mode the base is held, so the rover's
covariance *is* the baseline's covariance, and the vector is one subtraction::

    d = rover_position - reference_position

Measured on the committed fixtures: ``[2022.7707, -468.6291, 2610.2891]``,
length 3335.3896 m, against the length of the independently computed ENU
baseline in ``enu.pos`` -- 3335.3895 m. **They agree to 0.05 mm**, which is what
a DynAdjust ``G`` or ``X`` measurement wants with nothing done to it.

That agreement is also the check that the *rotation* is right: rotating the
subtraction above by ``enu_rotation`` at the base reproduces ``enu.pos``'s
printed components to 0.006 / 0.047 / 0.024 mm, and its printed standard
deviations to every digit written.

## 2. The covariance is printed to 0.1 mm, so it is worth about one digit

Every deviation and cross column is written ``%8.4f``. At the sub-centimetre
magnitudes a fixed static solution reaches, that is one or two significant
figures, and the covariance built from them is uncertain by several per cent.
:func:`~geocomp.core.uncertainty.covariance_from_printed` exists for exactly
this and is used here -- but **the half-width passed to it is not the printing's
half-width**, and getting that wrong is a quiet way to disable the check:

The file prints ``v = sqvar(c) = sign(c)*sqrt(|c|)``, so the covariance is
``c = sign(v)*v**2`` and ``dc/dv = 2|v|``. A printed value uncertain by
``0.5e-4`` therefore gives a covariance uncertain by ``2*|v|*0.5e-4``. At
``|v| = 0.0025`` that is ``2.5e-7``, not ``5e-5``: passing the printed
half-width straight through would be **two hundred times too loose** and would
condition away matrices that are indefinite for a real reason.
"""

from __future__ import annotations

import numpy as np

from geocomp.core.errors import DataError
from geocomp.core.geodesy.cartesian import cartesian_to_geodetic
from geocomp.core.geodesy.ellipsoid import ELLIPSOIDS, Ellipsoid
from geocomp.core.models import BaselineFrame
from geocomp.core.techniques.gnss.baselines import (
    Baseline,
    components_from_covariance,
)
from geocomp.core.techniques.gnss.quality import EpochQuality, SessionQuality, summarise
from geocomp.core.uncertainty import covariance_from_printed
from geocomp.core.units import Unit
from geocomp.engines.rtklib.read_pos import PosEpoch, PosFormat, PosSolution

__all__ = [
    "PRINTED_HALF_WIDTH",
    "baseline_from_solution",
    "printed_covariance_half_width",
    "quality_from_solution",
]

#: Half the place value of the last digit ``solution.c`` writes for a deviation
#: or a cross term -- ``%8.4f``, so 0.1 mm, so 0.5e-4 m.
PRINTED_HALF_WIDTH = 0.5e-4

#: Statuses that count as ambiguity-resolved, in RTKLIB's vocabulary.
_FIXED_STATUSES = frozenset({"FIXED"})


def printed_covariance_half_width(epoch: PosEpoch) -> float:
    """How far rounding alone can move an entry of *epoch*'s covariance.

    The printed quantity is a signed square root, so the covariance's
    sensitivity to it is ``2|v|`` -- see section 2 of the module docstring. The
    largest ``|v|`` in the matrix bounds the whole of it, which is what
    :func:`covariance_from_printed` needs: one number that no entry's error
    exceeds.
    """
    largest = float(np.max(np.abs(np.sqrt(np.abs(epoch.covariance.matrix)))))
    return 2.0 * largest * PRINTED_HALF_WIDTH


def baseline_from_solution(
    solution: PosSolution,
    *,
    base_station: str,
    rover_station: str,
    baseline_id: str = "",
    base_session: str = "",
    rover_session: str = "",
    ellipsoid: Ellipsoid | None = None,
) -> Baseline:
    """The ECEF baseline a relative ``rnx2rtkp`` run determined.

    Args:
        solution: A parsed ``.pos``. **Must be** :attr:`PosFormat.XYZ`: that is
            the format whose columns already are what a baseline needs, and
            deriving one from the LLH or ENU formats would mean inverting a
            projection or a rotation the engine has already applied, losing
            precision to no purpose.

    The **last** epoch is the answer, not the first and not a mean: a static run
    writes the filter's state every epoch, so the earlier ones are a converging
    filter's guesses (:meth:`PosSolution.last` says the same and is reused).

    Raises:
        DataError: if the format is not XYZ, or if the file carries no
            ``% ref pos`` -- without the base there is no baseline, only an
            absolute position, and returning one labelled as a baseline would be
            the FR-602 error this whole module exists to avoid.
    """
    if solution.format is not PosFormat.XYZ:
        raise DataError(
            "pos_not_geocentric",
            file=str(solution.path),
            received=solution.format.value,
            expected=(
                "an ECEF solution (rnx2rtkp -e). A baseline is a geocentric "
                "vector; the other formats have already had a projection or a "
                "rotation applied and undoing it would lose precision for "
                "nothing"
            ),
        )
    if solution.reference_position is None:
        raise DataError(
            "pos_without_reference_position",
            file=str(solution.path),
            expected=(
                "a '% ref pos' header naming the base station -- without it the "
                "file holds absolute positions, not a baseline"
            ),
        )

    epoch = solution.last()
    reference = np.asarray(solution.reference_position, dtype=float)
    rover = np.asarray(epoch.position, dtype=float)
    components = rover - reference

    covariance = covariance_from_printed(
        epoch.covariance.matrix,
        ("x", "y", "z"),
        (Unit.METRE,) * 3,
        half_width=printed_covariance_half_width(epoch),
    )
    # No strategy is asserted here, and that is a decision rather than an
    # omission. RECORDED_PRECISION would be the wrong label: the sigma is the
    # engine's own, not one invented from how many digits were written, and its
    # own docstring forbids it "for an observation whose sigma becomes an
    # adjustment weight" -- which is precisely what this becomes.
    # covariance_from_printed adds ROUNDING_CONDITIONED itself, and only if it
    # actually had to move the matrix.

    shape = ellipsoid or ELLIPSOIDS["GRS80"]
    base_latitude, base_longitude, _ = cartesian_to_geodetic(*reference, shape)
    rover_latitude, rover_longitude, _ = cartesian_to_geodetic(*rover, shape)

    return Baseline(
        id=baseline_id or f"{base_station}-{rover_station}",
        base_station=base_station,
        rover_station=rover_station,
        components=components_from_covariance(
            tuple(float(v) for v in components), covariance
        ),
        covariance=covariance,
        base_horizon=(base_latitude, base_longitude),
        rover_horizon=(rover_latitude, rover_longitude),
        frame=BaselineFrame.ECEF,
        base_session=base_session,
        rover_session=rover_session,
        meta={
            "engine": "rtklib",
            "program": solution.program,
            "solution_status": epoch.status.name,
            "satellites": epoch.satellites,
            "ratio": epoch.ratio,
            "epochs": len(solution.epochs),
        },
    )


def quality_from_solution(
    solution: PosSolution, *, session_id: str = "", keep_per_epoch: bool = False
) -> SessionQuality:
    """Summarise a run's quality indicators (FR-603).

    The statuses, satellite counts and ratios are RTKLIB's; the summary is not,
    which is why ``fixed_statuses`` is passed in rather than assumed by
    :func:`~geocomp.core.techniques.gnss.quality.summarise`.
    """
    epochs = [
        EpochQuality(
            time=epoch.time,
            status=epoch.status.name,
            satellites=epoch.satellites,
            ratio=epoch.ratio,
            age=epoch.age,
        )
        for epoch in solution.epochs
    ]
    return summarise(
        session_id or solution.path.stem,
        epochs,
        fixed_statuses=_FIXED_STATUSES,
        keep_per_epoch=keep_per_epoch,
    )
