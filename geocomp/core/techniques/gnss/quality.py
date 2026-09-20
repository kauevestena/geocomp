# SPDX-License-Identifier: GPL-2.0-or-later
"""What a GNSS session actually achieved, per session and per epoch (FR-603).

``specs/11-module-gnss.md`` section 5. Engine-agnostic: the inputs are already
parsed epochs, so a second engine's parser feeds the same summary.

**The reason this is a requirement rather than a nicety** is that a float
solution and a fixed one differ by two orders of magnitude in accuracy and by
nothing at all in appearance. A coordinate presented without its solution status
misrepresents the survey, and the single number that summarises a kinematic run
-- the percentage of epochs that fixed -- is not in the coordinate at all.

One indicator FR-603 names is **not** here, and its absence is recorded rather
than substituted for: see :attr:`SessionQuality.dilution_of_precision`.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from itertools import pairwise
from typing import Any

__all__ = ["EpochQuality", "SessionQuality", "summarise"]


@dataclass(frozen=True)
class EpochQuality:
    """One epoch's quality indicators, for a kinematic run's time series."""

    time: datetime
    status: str
    satellites: int
    ratio: float
    age: float


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
        dilution_of_precision: **Always ``None`` today, and deliberately so.**
            FR-603 names DOP, and ``rnx2rtkp`` does not write it: no column of
            the ``.pos`` file in any of its four output formats carries one
            (``specs/08`` section 7.1). It could be computed from the position
            covariance by dividing out an assumed a-priori sigma, but that
            number would be a function of the weighting RTKLIB happened to use
            and presenting it as DOP would be presenting a different quantity
            under a familiar name. The field exists so that an engine that
            *does* report DOP has somewhere to put it, and so the gap is visible
            rather than silently absent.
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
    dilution_of_precision: float | None = None
    per_epoch: tuple[EpochQuality, ...] = ()
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def duration_seconds(self) -> float | None:
        if self.start is None or self.end is None:
            return None
        return (self.end - self.start).total_seconds()

    @property
    def is_wholly_fixed(self) -> bool:
        return self.epochs > 0 and self.fixed_fraction == 1.0

    def to_dict(self) -> dict[str, Any]:
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
            "dilution_of_precision": self.dilution_of_precision,
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
        per_epoch=tuple(epochs) if keep_per_epoch else (),
    )


def _median(values: list[float]) -> float:
    """The middle of an already-sorted list."""
    if not values:
        return 0.0
    middle = len(values) // 2
    if len(values) % 2:
        return float(values[middle])
    return (values[middle - 1] + values[middle]) / 2.0
