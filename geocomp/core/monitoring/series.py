# SPDX-License-Identifier: GPL-2.0-or-later
"""A station through several epochs: its series and its velocity (``specs/14`` §6, §7; FR-836, FR-838).

Each epoch is brought into the first's frame (``compare.py``), and each
station's position at each epoch is kept with **that epoch's own** covariance --
what a time series plots, as offsets from the first epoch with their
uncertainty bands. The velocity is the weighted least-squares line through
them, per station, all components together:

    x(t) = x0 + v (t - t_mean)

The epochs are taken as **independent** of one another -- each solution is an
adjustment of its own campaign -- and the velocity says so
(``INDEPENDENCE_ASSUMED``): epochs sharing reference stations or products are
positively correlated, which makes the stated velocity uncertainty an
overestimate of the truth's.

**Against a reference block.** Epochs adjusted as free networks each carry
their own realisation of the datum -- a translation and a turn apart -- and a
series read straight off them would plot that as motion. Given the reference
block, every epoch's offsets and covariance are S-transformed onto it
(``congruency.py``), as the two-epoch analysis does.

A velocity is tested against zero with its own covariance, chi-square over the
components, because its uncertainty is propagated from each epoch's
a-posteriori covariance rather than estimated from the line's residuals. Three
epochs and more also give the line's own redundancy, reported as its degrees of
freedom and its ``v^T P v``, so a reader can see when the points do not lie on
a line -- which a constant velocity does not describe.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from geocomp.core.errors import ValidationError
from geocomp.core.models import Solution, TestResult
from geocomp.core.monitoring.compare import compare
from geocomp.core.monitoring.congruency import s_matrix
from geocomp.core.statistics.distributions import chi2_quantile
from geocomp.core.uncertainty import Strategy, UncertaintyMode

__all__ = ["SeriesPoint", "StationSeries", "series"]


@dataclass(frozen=True)
class SeriesPoint:
    """One epoch of one station: its offset from the first epoch, per component."""

    solution_id: str
    epoch: float
    offsets: tuple[float, ...]
    std_devs: tuple[float, ...]


@dataclass(frozen=True)
class StationSeries:
    """One station through the epochs, and its velocity.

    Attributes:
        velocity: Metres a year per component, or ``None`` from fewer than two epochs.
        velocity_covariance: Its covariance.
        velocity_test: Against zero; ``passed`` means no motion detected.
        degrees_of_freedom: Of the line: components times (epochs - 2).
        weighted_squares: The line's ``v^T P v``; large against its degrees of
            freedom means the motion is not at a constant rate.
    """

    station_id: str
    components: tuple[str, ...]
    points: tuple[SeriesPoint, ...]
    velocity: tuple[float, ...] | None = None
    velocity_covariance: np.ndarray | None = None
    velocity_test: TestResult | None = None
    degrees_of_freedom: int = 0
    weighted_squares: float = 0.0
    #: The fitted line's own offset, at :attr:`line_epoch` (the epochs' mean):
    #: a plot draws the line that was fitted, not one forced through zero.
    line_epoch: float | None = None
    line_offset: tuple[float, ...] | None = None
    mode: UncertaintyMode = UncertaintyMode.APPROXIMATE
    strategies: frozenset[Strategy] = frozenset({Strategy.INDEPENDENCE_ASSUMED})

    @property
    def velocity_std_devs(self) -> tuple[float, ...] | None:
        """The standard deviation of each velocity component; ``None`` without a covariance."""
        if self.velocity_covariance is None:
            return None
        return tuple(float(np.sqrt(max(v, 0.0))) for v in np.diag(self.velocity_covariance))

    @property
    def horizontal_speed(self) -> float | None:
        """The horizontal speed in metres a year; ``None`` without a velocity in ``e`` and ``n``."""
        if self.velocity is None or "e" not in self.components or "n" not in self.components:
            return None
        return float(
            np.hypot(self.velocity[self.components.index("e")], self.velocity[self.components.index("n")])
        )

    @property
    def speed(self) -> float | None:
        """What a velocity alert is judged on: the horizontal speed where the
        series has a plan, otherwise the vertical rate's size -- a settlement
        series from levelling has only the height to move in."""
        horizontal = self.horizontal_speed
        if horizontal is not None or self.velocity is None:
            return horizontal
        for name in ("u", "h"):
            if name in self.components:
                return abs(float(self.velocity[self.components.index(name)]))
        return None

    def to_rows(self) -> list[dict[str, float | str]]:
        """Plottable rows: one per epoch and component, value and band."""
        rows: list[dict[str, float | str]] = []
        for point in self.points:
            for component, offset, sigma in zip(self.components, point.offsets, point.std_devs, strict=True):
                rows.append(
                    {
                        "station": self.station_id,
                        "solution": point.solution_id,
                        "epoch": point.epoch,
                        "component": component,
                        "offset": offset,
                        "std_dev": sigma,
                    }
                )
        return rows


def series(
    solutions: Sequence[Solution],
    *,
    stations: Sequence[str] | None = None,
    reference: Sequence[str] | None = None,
    datum: str | None = None,
    confidence: float = 0.95,
) -> tuple[StationSeries, ...]:
    """Each station's series across *solutions*, and its velocity.

    The solutions are ordered by epoch; the earliest is the frame and origin of
    the series. A station absent from an epoch has no point there.

    Args:
        reference: The stable block every epoch is referred to; ``None`` takes
            the solutions' datum as they are (right for epochs held the same way).

    Raises:
        ValidationError: ``monitoring_series_too_short`` for fewer than two
            solutions; and whatever :func:`compare` refuses between the first
            and any other.
    """
    ordered = sorted(solutions, key=lambda s: s.epoch.decimal_year if s.epoch is not None else float("-inf"))
    if len(ordered) < 2:
        raise ValidationError(
            "monitoring_series_too_short",
            received=len(ordered),
            expected="two epochs at least",
        )
    first = ordered[0]
    wanted = set(stations) if stations is not None else None
    collected: dict[str, list[SeriesPoint]] = {}
    covariances: dict[str, list[np.ndarray]] = {}
    components: tuple[str, ...] = ()
    for later in ordered[1:]:
        comparison = compare(first, later)
        components = comparison.components
        k = comparison.dimension
        transform = (
            np.eye(len(comparison.difference))
            if reference is None
            else s_matrix(comparison, [s for s in reference if s in comparison.stations], datum)
        )
        offsets_all = transform @ comparison.difference
        first_sigma = transform @ comparison.first_covariance @ transform.T
        second_sigma = transform @ comparison.second_covariance @ transform.T
        for i, station in enumerate(comparison.stations):
            if wanted is not None and station not in wanted:
                continue
            block = slice(i * k, i * k + k)
            if station not in collected:
                sigma = first_sigma[block, block]
                collected[station] = [_point(first.id, comparison.first_epoch, np.zeros(k), sigma)]
                covariances[station] = [sigma]
            sigma = second_sigma[block, block]
            collected[station].append(_point(later.id, comparison.second_epoch, offsets_all[block], sigma))
            covariances[station].append(sigma)
    return tuple(
        _fit(station, components, collected[station], covariances[station], confidence)
        for station in collected
    )


def _point(solution_id: str, epoch: float, offsets: np.ndarray, sigma: np.ndarray) -> SeriesPoint:
    return SeriesPoint(
        solution_id=solution_id,
        epoch=float(epoch),
        offsets=tuple(float(v) for v in offsets),
        std_devs=tuple(float(np.sqrt(max(v, 0.0))) for v in np.diag(sigma)),
    )


def _fit(station, components, points, covariances, confidence) -> StationSeries:
    """The weighted line through one station's epochs, all components at once."""
    k = len(components)
    if len(points) < 2:
        return StationSeries(station_id=station, components=components, points=tuple(points))
    epochs = np.array([p.epoch for p in points])
    middle = float(epochs.mean())
    normal = np.zeros((2 * k, 2 * k))
    right = np.zeros(2 * k)
    rows = []
    for point, sigma, epoch in zip(points, covariances, epochs, strict=True):
        design = np.hstack([np.eye(k), (epoch - middle) * np.eye(k)])
        weight = np.linalg.pinv(sigma, hermitian=True)
        normal += design.T @ weight @ design
        right += design.T @ weight @ np.asarray(point.offsets)
        rows.append((design, weight, np.asarray(point.offsets)))
    covariance = np.linalg.pinv(normal, hermitian=True)
    estimate = covariance @ right
    squares = float(sum((y - a @ estimate) @ w @ (y - a @ estimate) for a, w, y in rows))
    velocity = estimate[k:]
    velocity_covariance = covariance[k:, k:]
    statistic = float(velocity @ np.linalg.pinv(velocity_covariance, hermitian=True) @ velocity)
    critical = chi2_quantile(confidence, k)
    test = TestResult(
        name=f"velocity of {station}",
        statistic=statistic,
        critical_high=critical,
        confidence=confidence,
        passed=statistic <= critical,
        note=f"chi-square({k}) with each epoch's own covariance",
    )
    return StationSeries(
        station_id=station,
        components=components,
        points=tuple(points),
        velocity=tuple(float(v) for v in velocity),
        velocity_covariance=velocity_covariance,
        velocity_test=test,
        degrees_of_freedom=k * (len(points) - 2),
        weighted_squares=squares,
        line_epoch=middle,
        line_offset=tuple(float(v) for v in estimate[:k]),
    )
