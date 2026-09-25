# SPDX-License-Identifier: GPL-2.0-or-later
"""Gravimeter drift: the two treatments, and when each is possible (FR-701, FR-702).

``specs/12-module-gravimetry.md`` section 4.3.

A relative gravimeter's reading wanders even with the instrument at rest, and
jumps when it is transported. Two ways of dealing with it, and the difference
is the reason FR-702 exists:

**Joint estimation** (the default). Drift coefficients become unknowns of the
adjustment, beside the station values. A difference between two occupations
sees the drift at both, ``sum_k c_k (tau_to**k - tau_from**k)``, and the
repeated occupations that make the drift estimable also make it *checkable*:
an error in it shows in the residuals and in the reliability figures like an
error anywhere else.

**Pre-correction.** The classic field method: fit the drift to the repeated
readings at one base station, subtract it, and hand the adjustment
differences from which it has already gone. Simple, and adequate when the
drift really is what was fitted -- but whatever the fit got wrong goes
straight into every station value, and nothing downstream can see it,
because the readings that could have shown it were spent on the fit. Where
the base was read exactly as often as the model has parameters, the fit has
no redundancy at all and the model is imposed rather than tested; the result
says so, with :attr:`~geocomp.core.uncertainty.Strategy.MODEL_ASSUMED`.

**Time** is carried as seconds from the session's first occupation and enters
the model as ``tau = t / T`` with a declared scale ``T`` -- one hour by
default -- so that a coefficient is an acceleration with a stated meaning (the
degree-1 coefficient is the drift per hour) and the polynomial stays well
conditioned.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

import numpy as np

from geocomp.core.errors import ValidationError
from geocomp.core.uncertainty import Covariance, Quantity

__all__ = [
    "DEFAULT_TIME_SCALE",
    "DriftEstimate",
    "DriftMode",
    "DriftOptions",
    "DriftTreatment",
    "drift_is_estimable",
]

#: Seconds in the unit of the drift polynomial's time: one hour.
DEFAULT_TIME_SCALE = 3600.0


class DriftMode(Enum):
    """What the user asked for.

    There is no "automatic" choice, because there is nothing to choose between.
    Pre-correction needs the base read at ``degree + 1`` distinct times, and
    those readings alone make the joint design full rank -- so every session
    that can be pre-corrected can be estimated jointly, and one that cannot be
    estimated jointly cannot be pre-corrected either. Joint estimation is the
    default; pre-correction is there for the classical workflow and for
    comparison (``specs/12`` section 8, criterion 3).
    """

    JOINT = "joint"
    PRE_CORRECTED = "pre_corrected"


class DriftTreatment(Enum):
    """What a session actually got, recorded on the result."""

    JOINT = "joint"
    PRE_CORRECTED = "pre_corrected"


@dataclass(frozen=True)
class DriftOptions:
    """How drift is handled.

    Attributes:
        mode: See :class:`DriftMode`. Joint by default (FR-702).
        degree: Of the drift polynomial, per session. 1 is linear.
        time_scale: ``T`` in seconds; see the module docstring.
        base_stations: For pre-correction, the base station of each session.
            A session not listed uses its most occupied station, the earliest
            occupied breaking a tie.
        correlated: Carry the correlation between differences that share an
            occupation. ``False`` treats them as independent, which is what
            MCGravi and pyGrav do; the result then records the independence
            assumption, and it exists so that their published solutions can
            be reproduced, not because it is better.
    """

    mode: DriftMode = DriftMode.JOINT
    degree: int = 1
    time_scale: float = DEFAULT_TIME_SCALE
    base_stations: dict[str, str] | None = None
    correlated: bool = True

    def __post_init__(self) -> None:
        if self.degree < 1:
            raise ValidationError(
                "drift_degree_invalid",
                received=self.degree,
                expected="a polynomial degree of 1 or more",
            )
        if not self.time_scale > 0.0:
            raise ValidationError(
                "drift_time_scale_invalid",
                received=self.time_scale,
                expected="a positive time scale in seconds",
            )


@dataclass(frozen=True)
class DriftEstimate:
    """A session's drift, however it was obtained.

    Attributes:
        session: Whose drift.
        treatment: Estimated jointly, or fitted to base readings beforehand.
        coefficients: ``c_1 .. c_p`` in m/s^2: the drift accumulated per unit
            of ``tau**k``. With the default scale, ``c_1`` is the drift per hour.
        covariance: Over the coefficients, in that order.
        time_scale: ``T``, seconds.
        reference: The instant ``tau = 0``: the session's first occupation.
        base_station: The station the drift was fitted to, for a
            pre-correction; ``None`` for a joint estimate.
        verified: For a pre-correction, whether the base readings' residuals
            passed a chi-square test at the adjustment's confidence -- ``None``
            when there were no residuals to test, because the fit used every
            reading it had.
    """

    session: str
    treatment: DriftTreatment
    coefficients: tuple[Quantity, ...]
    covariance: Covariance
    time_scale: float
    reference: datetime
    base_station: str | None = None
    verified: bool | None = None


def drift_is_estimable(stations: list[str], elapsed: list[float], degree: int, time_scale: float) -> bool:
    """Whether a session's occupations can determine its drift by themselves.

    A session's readings follow ``g_station + offset + drift(tau)``; the offset
    is absorbed by the station values, so the drift is determined when the
    design over (one column per station, one per drift degree) has full column
    rank. In words: something was re-occupied, at enough different times for
    the polynomial's degree. A loop that returns to its start is enough for a
    line; a session that visits every station once is not.

    The check is local to the session and therefore conservative: a drift the
    rest of the network could pin down is refused here. Refusing is the right
    side to err on, since the alternative is a singular system reported as a
    datum problem with the wrong stations named.
    """
    if len(stations) != len(elapsed):
        raise ValidationError(
            "drift_occupation_mismatch",
            received=[len(stations), len(elapsed)],
            expected="one elapsed time per occupation",
        )
    names = sorted(set(stations))
    columns = len(names) + degree
    if len(stations) < columns:
        return False
    design = np.zeros((len(stations), columns))
    for row, (station, seconds) in enumerate(zip(stations, elapsed, strict=True)):
        design[row, names.index(station)] = 1.0
        tau = seconds / time_scale
        for power in range(1, degree + 1):
            design[row, len(names) + power - 1] = tau**power
    return int(np.linalg.matrix_rank(design)) == columns
