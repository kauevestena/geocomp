# SPDX-License-Identifier: GPL-2.0-or-later
"""Alert thresholds, evaluated (``specs/14`` section 7, FR-837).

A threshold names what it watches -- a displacement's magnitude, its
horizontal or vertical part, a velocity, or simply significance -- the limit,
and the stations it applies to (all of them, or a group). Evaluating it gives
one :class:`Alert` per station it covers, exceeded or not, so a result says
which stations were checked as well as which crossed the line.

**Not significant is not below threshold.** A displacement larger than its
limit but not statistically significant is flagged: the threshold is the
owner's criterion of concern, significance is the survey's, and a monitoring
report that let the second silence the first would hide exactly the case --
large, uncertain motion -- that needs a closer look. The alert carries both.

GeoComp flags; it does not notify (section 7). Where the flags are drawn and
reported is the map's and the report's business (phase P10b).
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from enum import Enum

from geocomp.core.errors import ValidationError
from geocomp.core.monitoring.congruency import Displacement
from geocomp.core.monitoring.series import StationSeries

__all__ = ["Alert", "AlertKind", "AlertThreshold", "evaluate_alerts", "thresholds_from_rows"]


class AlertKind(Enum):
    #: The whole displacement vector's length, metres.
    MAGNITUDE = "magnitude"
    #: Its horizontal part, metres.
    HORIZONTAL = "horizontal"
    #: The absolute vertical displacement, metres.
    VERTICAL = "vertical"
    #: The horizontal speed from a series, metres a year.
    VELOCITY = "velocity"
    #: The displacement's joint test: exceeded when significant.
    SIGNIFICANCE = "significance"


@dataclass(frozen=True)
class AlertThreshold:
    """One alarm criterion.

    Attributes:
        limit: Metres, or metres a year for a velocity; unused for significance.
        stations: The stations it applies to; ``None`` for every station.
        group: A name for the stations, for the report.
    """

    kind: AlertKind
    limit: float = 0.0
    stations: frozenset[str] | None = None
    group: str = ""

    def __post_init__(self) -> None:
        if self.kind is not AlertKind.SIGNIFICANCE and not self.limit > 0.0:
            raise ValidationError(
                "monitoring_alert_limit",
                kind=self.kind.value,
                received=self.limit,
                expected="a positive limit",
            )

    def applies_to(self, station_id: str) -> bool:
        return self.stations is None or station_id in self.stations


@dataclass(frozen=True)
class Alert:
    """One threshold at one station."""

    station_id: str
    threshold: AlertThreshold
    value: float | None
    exceeded: bool
    significant: bool | None = None


def evaluate_alerts(
    thresholds: Sequence[AlertThreshold],
    *,
    displacements: Iterable[Displacement] = (),
    series: Iterable[StationSeries] = (),
) -> tuple[Alert, ...]:
    """Every threshold at every station it covers and has a value for."""
    displacements = tuple(displacements)
    series = tuple(series)
    alerts: list[Alert] = []
    for threshold in thresholds:
        if threshold.kind is AlertKind.VELOCITY:
            for station in series:
                if not threshold.applies_to(station.station_id):
                    continue
                speed = station.speed
                significant = None if station.velocity_test is None else not station.velocity_test.passed
                alerts.append(
                    Alert(
                        station_id=station.station_id,
                        threshold=threshold,
                        value=speed,
                        exceeded=speed is not None and speed > threshold.limit,
                        significant=significant,
                    )
                )
            continue
        for displacement in displacements:
            if not threshold.applies_to(displacement.station_id):
                continue
            value = {
                AlertKind.MAGNITUDE: displacement.magnitude,
                AlertKind.HORIZONTAL: displacement.horizontal_magnitude,
                AlertKind.VERTICAL: displacement.vertical_magnitude,
                AlertKind.SIGNIFICANCE: None,
            }[threshold.kind]
            exceeded = (
                displacement.significant
                if threshold.kind is AlertKind.SIGNIFICANCE
                else value is not None and value > threshold.limit
            )
            alerts.append(
                Alert(
                    station_id=displacement.station_id,
                    threshold=threshold,
                    value=value,
                    exceeded=exceeded,
                    significant=displacement.significant,
                )
            )
    return tuple(alerts)


def thresholds_from_rows(rows: Iterable[Sequence[str]]) -> tuple[AlertThreshold, ...]:
    """Alert thresholds from the rows of a CSV file: ``kind, limit, stations, group``.

    The file a monitoring project keeps its alarm criteria in (``specs/14``
    section 7). ``kind`` is one of :class:`AlertKind`'s values; ``limit`` is in
    metres, or metres a year for ``velocity``, and empty for ``significance``;
    ``stations`` are separated by spaces or semicolons and empty for every
    station; ``group`` names them in the report. A header row, blank rows and
    rows starting ``#`` are skipped.

    Raises:
        ValidationError: ``monitoring_threshold_row`` naming the row and what is
            wrong with it -- a criterion silently dropped is an alarm that never
            sounds.
    """
    kinds = {kind.value: kind for kind in AlertKind}
    thresholds: list[AlertThreshold] = []
    for number, row in enumerate(rows, start=1):
        cells = [cell.strip() for cell in row]
        if not cells or not any(cells) or cells[0].startswith("#") or cells[0].lower() == "kind":
            continue
        cells += [""] * (4 - len(cells))
        kind = kinds.get(cells[0].lower())
        if kind is None:
            raise ValidationError(
                "monitoring_threshold_row", row=number, received=cells[0], expected=sorted(kinds)
            )
        limit = 0.0
        if kind is not AlertKind.SIGNIFICANCE:
            try:
                limit = float(cells[1])
            except ValueError:
                raise ValidationError(
                    "monitoring_threshold_row",
                    row=number,
                    received=cells[1] or "(empty)",
                    expected="a positive limit in metres, or metres a year for a velocity",
                ) from None
        names = frozenset(cells[2].replace(";", " ").split()) or None
        thresholds.append(AlertThreshold(kind=kind, limit=limit, stations=names, group=cells[3]))
    return tuple(thresholds)
