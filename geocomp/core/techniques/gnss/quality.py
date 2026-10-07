# SPDX-License-Identifier: GPL-2.0-or-later
"""What a GNSS session actually achieved, per session and per epoch (FR-603).

``specs/11-module-gnss.md`` section 5. Engine-agnostic: the inputs are already
parsed epochs, so a second engine's parser feeds the same summary.

**The reason this is a requirement rather than a nicety** is that a float
solution and a fixed one differ by two orders of magnitude in accuracy and by
nothing at all in appearance. A coordinate presented without its solution status
misrepresents the survey, and the single number that summarises a kinematic run
-- the percentage of epochs that fixed -- is not in the coordinate at all.

Dilution of precision is computed here from the satellite geometry an engine
reports -- each used satellite's azimuth and elevation -- by the definition
RTKLIB's own ``dops()`` uses (P12c-35). ``rnx2rtkp`` writes no DOP in its
solution file, but it writes the geometry in its solution-status file, and the
DOP of that geometry is what the engine would have reported.

Cycle slips and rejected observations are the engine's own detections, per
signal and epoch, read from the same file (P12c-36); this module only counts
them. A signal is a satellite and a frequency, ``G20/1``.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from itertools import pairwise
from typing import Any

import numpy as np

__all__ = [
    "DilutionOfPrecision",
    "EpochQuality",
    "SessionQuality",
    "dilution_of_precision",
    "summarise",
]


@dataclass(frozen=True)
class DilutionOfPrecision:
    """How the satellite geometry scales ranging error into a solution (FR-603).

    Dimensionless. ``geometric`` is GDOP, ``position`` PDOP, ``horizontal``
    HDOP and ``vertical`` VDOP, in RTKLIB's sense: the receiver clock is the
    fourth unknown and every satellite weighs the same.
    """

    geometric: float
    position: float
    horizontal: float
    vertical: float

    def to_dict(self) -> dict[str, float]:
        """The four values as a summary records them."""
        return {
            "gdop": self.geometric,
            "pdop": self.position,
            "hdop": self.horizontal,
            "vdop": self.vertical,
        }


def dilution_of_precision(
    azimuths_elevations: list[tuple[float, float]], *, elevation_mask: float = 0.0
) -> DilutionOfPrecision | None:
    """The DOP of one epoch's satellites, each an ``(azimuth, elevation)`` in radians.

    RTKLIB's definition (``dops()`` in ``src/rtkcmn.c`` at the pinned commit):
    a satellite below *elevation_mask*, or at or below the horizon, does not
    count; each that does adds the row ``[cos e sin a, cos e cos a, sin e, 1]``;
    and the DOPs are square roots of the diagonal of the inverse of the normal
    matrix -- all four terms for GDOP, the first three for PDOP, the first two
    for HDOP and the third for VDOP.

    Returns ``None`` for fewer than four satellites or a geometry with no
    inverse, where RTKLIB returns zeros: a zero would read as a perfect
    geometry, which is the opposite of what happened.
    """
    rows = [
        (
            math.cos(elevation) * math.sin(azimuth),
            math.cos(elevation) * math.cos(azimuth),
            math.sin(elevation),
            1.0,
        )
        for azimuth, elevation in azimuths_elevations
        if elevation >= elevation_mask and elevation > 0.0
    ]
    if len(rows) < 4:
        return None
    design = np.asarray(rows, dtype=float)
    normal = design.T @ design
    try:
        cofactor = np.linalg.inv(normal)
    except np.linalg.LinAlgError:
        return None
    diagonal = np.diag(cofactor)
    if not np.all(np.isfinite(diagonal)) or np.any(diagonal < 0.0):
        return None
    return DilutionOfPrecision(
        geometric=float(math.sqrt(diagonal.sum())),
        position=float(math.sqrt(diagonal[:3].sum())),
        horizontal=float(math.sqrt(diagonal[:2].sum())),
        vertical=float(math.sqrt(diagonal[2])),
    )


@dataclass(frozen=True)
class EpochQuality:
    """One epoch's quality indicators, for a kinematic run's time series."""

    time: datetime
    status: str
    satellites: int
    ratio: float
    age: float
    dop: DilutionOfPrecision | None = None
    #: The signals a cycle slip was detected on at this epoch; ``None`` when
    #: the engine reported nothing about it, as distinct from reporting none.
    slips: tuple[str, ...] | None = None
    #: The signals rejected as outliers at this epoch; ``None`` likewise.
    rejections: tuple[str, ...] | None = None


@dataclass(frozen=True)
class SessionQuality:
    """Per-session quality indicators (FR-603).

    Attributes:
        status_counts: Epoch count per solution status, by the status's own
            name. A mapping rather than a fixed set of fields, so an engine that
            reports a status GeoComp has not seen is counted rather than
            dropped.
        fixed_fraction: Epochs with resolved ambiguities over all epochs. For a
            kinematic run this is the most informative single number there is.
        ratio_best / ratio_median: The ambiguity ratio factor -- the evidence
            that the fixed solution is the right one. A fixed solution with a
            ratio barely over the threshold deserves to be looked at, and a
            report that gave only "fixed" would not let anyone.
        satellites_least / satellites_most: The range actually tracked, which is
            what makes a solution possible in an obstructed site.
        dilution_of_precision: The median of each DOP over the epochs that
            have one, component by component; ``None`` when no epoch does --
            the engine reported no geometry, or never four satellites.
        dilution_of_precision_worst: The DOP of the epoch whose PDOP was
            largest: a session whose median is good can still have had a
            stretch where the geometry was not.
        cycle_slips / rejections: How many signals, over all epochs, the
            engine detected a cycle slip on or rejected as an outlier. A slip
            the engine finds from the two frequencies together is two signals.
            ``None`` when the engine reported on no epoch, which is not zero.
        satellites_slipped / satellites_rejected: The satellites those
            signals belong to: a dozen slips on one low satellite and a dozen
            across the sky are different sessions.
    """

    session_id: str
    epochs: int
    status_counts: dict[str, int]
    fixed_fraction: float
    satellites_least: int
    satellites_most: int
    ratio_best: float
    ratio_median: float
    start: datetime | None = None
    end: datetime | None = None
    interval: float | None = None
    dilution_of_precision: DilutionOfPrecision | None = None
    dilution_of_precision_worst: DilutionOfPrecision | None = None
    cycle_slips: int | None = None
    rejections: int | None = None
    satellites_slipped: tuple[str, ...] = ()
    satellites_rejected: tuple[str, ...] = ()
    per_epoch: tuple[EpochQuality, ...] = ()
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def duration_seconds(self) -> float | None:
        """How long the solution spans, in seconds; ``None`` when its start or end is unknown."""
        if self.start is None or self.end is None:
            return None
        return (self.end - self.start).total_seconds()

    @property
    def is_wholly_fixed(self) -> bool:
        """Whether every epoch has its ambiguities fixed, and there is at least one epoch."""
        return self.epochs > 0 and self.fixed_fraction == 1.0

    def to_dict(self) -> dict[str, Any]:
        """The indicators as a run summary holds them; times in ISO 8601."""
        return {
            "session_id": self.session_id,
            "epochs": self.epochs,
            "status_counts": dict(self.status_counts),
            "fixed_fraction": self.fixed_fraction,
            "satellites_least": self.satellites_least,
            "satellites_most": self.satellites_most,
            "ratio_best": self.ratio_best,
            "ratio_median": self.ratio_median,
            "start": self.start.isoformat() if self.start else None,
            "end": self.end.isoformat() if self.end else None,
            "interval": self.interval,
            "dilution_of_precision": (
                self.dilution_of_precision.to_dict() if self.dilution_of_precision else None
            ),
            "dilution_of_precision_worst": (
                self.dilution_of_precision_worst.to_dict()
                if self.dilution_of_precision_worst
                else None
            ),
            "cycle_slips": self.cycle_slips,
            "rejections": self.rejections,
            "satellites_slipped": list(self.satellites_slipped),
            "satellites_rejected": list(self.satellites_rejected),
        }


def summarise(
    session_id: str,
    epochs: list[EpochQuality],
    *,
    fixed_statuses: frozenset[str] = frozenset({"FIX"}),
    keep_per_epoch: bool = False,
) -> SessionQuality:
    """Reduce a run's epochs to one :class:`SessionQuality`.

    Args:
        fixed_statuses: Which status names count as ambiguity-resolved. Passed
            in rather than hard-coded because it is the *engine's* vocabulary,
            and this module deliberately knows nothing about which engine ran.
        keep_per_epoch: Carry the whole series. Off by default: a 24-hour
            kinematic run at 1 Hz is 86 400 epochs, and a session summary that
            silently held all of them would make every project file enormous.

    The interval is the **median** gap between epochs, not the mean: a run with
    one gap in the middle has a mean that describes neither side of it, and the
    interval is used to decide whether a session was long enough for the mode
    it was processed in.
    """
    if not epochs:
        return SessionQuality(
            session_id=session_id,
            epochs=0,
            status_counts={},
            fixed_fraction=0.0,
            satellites_least=0,
            satellites_most=0,
            ratio_best=0.0,
            ratio_median=0.0,
        )

    counts = Counter(epoch.status for epoch in epochs)
    fixed = sum(count for status, count in counts.items() if status in fixed_statuses)
    satellites = [epoch.satellites for epoch in epochs]
    ratios = sorted(epoch.ratio for epoch in epochs)
    times = sorted(epoch.time for epoch in epochs)
    gaps = sorted(
        (later - earlier).total_seconds()
        for earlier, later in pairwise(times)
    )

    dops = [epoch.dop for epoch in epochs if epoch.dop is not None]
    slips = [epoch.slips for epoch in epochs if epoch.slips is not None]
    rejections = [epoch.rejections for epoch in epochs if epoch.rejections is not None]

    return SessionQuality(
        session_id=session_id,
        epochs=len(epochs),
        status_counts=dict(counts),
        fixed_fraction=fixed / len(epochs),
        satellites_least=min(satellites),
        satellites_most=max(satellites),
        ratio_best=max(ratios),
        ratio_median=_median(ratios),
        start=times[0],
        end=times[-1],
        interval=_median(gaps) if gaps else None,
        dilution_of_precision=_median_dop(dops),
        dilution_of_precision_worst=max(dops, key=lambda dop: dop.position) if dops else None,
        cycle_slips=sum(map(len, slips)) if slips else None,
        rejections=sum(map(len, rejections)) if rejections else None,
        satellites_slipped=_satellites(slips),
        satellites_rejected=_satellites(rejections),
        per_epoch=tuple(epochs) if keep_per_epoch else (),
    )


def _median_dop(dops: list[DilutionOfPrecision]) -> DilutionOfPrecision | None:
    """Each component's median over *dops*: four medians, not the median epoch's four values."""
    if not dops:
        return None
    return DilutionOfPrecision(
        geometric=_median(sorted(dop.geometric for dop in dops)),
        position=_median(sorted(dop.position for dop in dops)),
        horizontal=_median(sorted(dop.horizontal for dop in dops)),
        vertical=_median(sorted(dop.vertical for dop in dops)),
    )


def _satellites(signals: list[tuple[str, ...]]) -> tuple[str, ...]:
    """The satellites a list of epochs' signals belong to, each once, in order."""
    return tuple(sorted({signal.split("/")[0] for epoch in signals for signal in epoch}))


def _median(values: list[float]) -> float:
    """The middle of an already-sorted list."""
    if not values:
        return 0.0
    middle = len(values) // 2
    if len(values) % 2:
        return float(values[middle])
    return (values[middle - 1] + values[middle]) / 2.0
