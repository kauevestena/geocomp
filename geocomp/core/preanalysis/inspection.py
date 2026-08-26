# SPDX-License-Identifier: GPL-2.0-or-later
"""Network inspection on real data (FR-273).

``specs/06-adjustment-core.md`` section 5.2.

Distinct from pre-analysis, which is design simulation. This runs on data that
exists and catches the problems that otherwise surface as a confusing singular
normal matrix twenty seconds into an adjustment: a disconnected component, a
station with too few observations, a duplicate, a missing approximate
coordinate.

Fast, needs no adjustment, and returns **findings rather than raising**, because
an importer must be able to report every problem at once rather than stopping at
the first (FR-166).
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from enum import Enum

from geocomp.core.adjustment.equations import supports
from geocomp.core.adjustment.parameters import Frame
from geocomp.core.models import Network

__all__ = ["Finding", "InspectionReport", "Severity", "inspect"]


class Severity(Enum):
    """How much a finding matters.

    ``BLOCKING`` means the adjustment cannot run; ``WARNING`` means it can but
    the result may not mean what the user expects. The distinction is what lets
    a UI offer "adjust anyway" honestly.
    """

    BLOCKING = "blocking"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True)
class Finding:
    """One thing worth telling the user about a network."""

    code: str
    severity: Severity
    message: str
    stations: tuple[str, ...] = ()
    observations: tuple[str, ...] = ()


@dataclass(frozen=True)
class InspectionReport:
    """Everything inspection found."""

    findings: tuple[Finding, ...]
    station_count: int
    observation_count: int
    active_observation_count: int
    components: tuple[tuple[str, ...], ...]

    @property
    def blocking(self) -> tuple[Finding, ...]:
        return tuple(f for f in self.findings if f.severity is Severity.BLOCKING)

    @property
    def warnings(self) -> tuple[Finding, ...]:
        return tuple(f for f in self.findings if f.severity is Severity.WARNING)

    @property
    def can_adjust(self) -> bool:
        return not self.blocking

    @property
    def is_connected(self) -> bool:
        return len(self.components) <= 1


def inspect(network: Network, *, frame: Frame = Frame.PLANE_2D) -> InspectionReport:
    """Check *network* for the problems that block or distort an adjustment."""
    findings: list[Finding] = []
    active = network.active_observations

    findings.extend(_referential_findings(network))
    findings.extend(_support_findings(active, frame))
    components = _connected_components(network)
    findings.extend(_connectivity_findings(network, components))
    findings.extend(_observation_count_findings(network, active, frame))
    findings.extend(_duplicate_findings(active))
    findings.extend(_approximate_coordinate_findings(network))

    if not active:
        findings.append(
            Finding(
                "no_active_observations",
                Severity.BLOCKING,
                "the network has no active observations, so there is nothing to adjust",
            )
        )

    return InspectionReport(
        findings=tuple(findings),
        station_count=len(network.stations),
        observation_count=len(network.observations),
        active_observation_count=len(active),
        components=components,
    )


def _referential_findings(network: Network) -> list[Finding]:
    """Reuse the model's own integrity check rather than duplicating it."""
    return [
        Finding("referential_integrity", Severity.BLOCKING, problem)
        for problem in network.validate()
    ]


def _support_findings(active, frame: Frame) -> list[Finding]:
    findings: list[Finding] = []
    for observation in active:
        if not supports(observation.type):
            findings.append(
                Finding(
                    "unsupported_observation_type",
                    Severity.BLOCKING,
                    f"observation {observation.id} is of type {observation.type.value}, "
                    "which the in-house adjustment does not yet implement",
                    observations=(observation.id,),
                )
            )
        elif frame.dimension not in observation.spec.dimensionality:
            findings.append(
                Finding(
                    "wrong_dimensionality",
                    Severity.BLOCKING,
                    f"observation {observation.id} of type {observation.type.value} cannot "
                    f"contribute to a {frame.dimension}D adjustment",
                    observations=(observation.id,),
                )
            )
    return findings


def _connected_components(network: Network) -> tuple[tuple[str, ...], ...]:
    """Group stations into connected components, by union-find over observations.

    A network in two pieces cannot be adjusted as one: the two halves have
    independent datums, which shows up later as a rank deficiency nobody expects.
    """
    parent = {station_id: station_id for station_id in network.stations}

    def find(item: str) -> str:
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    def union(a: str, b: str) -> None:
        root_a, root_b = find(a), find(b)
        if root_a != root_b:
            parent[root_b] = root_a

    for observation in network.active_observations:
        known = [s for s in observation.stations if s in parent]
        for other in known[1:]:
            union(known[0], other)

    groups: dict[str, list[str]] = defaultdict(list)
    for station_id in network.stations:
        groups[find(station_id)].append(station_id)

    return tuple(tuple(sorted(members)) for members in sorted(groups.values(), key=len, reverse=True))


def _connectivity_findings(
    network: Network, components: tuple[tuple[str, ...], ...]
) -> list[Finding]:
    findings: list[Finding] = []
    if len(components) > 1:
        findings.append(
            Finding(
                "network_not_connected",
                Severity.BLOCKING,
                f"the network falls into {len(components)} disconnected parts; each has its "
                "own datum and they cannot be adjusted together",
                stations=tuple(component[0] for component in components),
            )
        )

    connected: set[str] = set()
    for observation in network.active_observations:
        connected.update(observation.stations)
    isolated = sorted(set(network.stations) - connected)
    if isolated:
        findings.append(
            Finding(
                "isolated_stations",
                Severity.BLOCKING,
                f"{len(isolated)} station(s) take part in no active observation and cannot "
                "be determined: " + ", ".join(isolated),
                stations=tuple(isolated),
            )
        )
    return findings


def _observation_count_findings(network: Network, active, frame: Frame) -> list[Finding]:
    """Flag stations with too few observations to be determined.

    A rough necessary condition, not a sufficient one -- three distances can
    still leave a station undetermined if they are collinear. It catches the
    common case cheaply; the rank diagnosis catches the rest exactly.
    """
    counts: dict[str, int] = defaultdict(int)
    for observation in active:
        for station_id in set(observation.stations):
            counts[station_id] += len(observation.spec.components)

    findings: list[Finding] = []
    needed = frame.dimension
    for station_id, station in sorted(network.stations.items()):
        if not station.constraint.is_free:
            continue
        count = counts.get(station_id, 0)
        if 0 < count < needed:
            findings.append(
                Finding(
                    "insufficient_observations",
                    Severity.WARNING,
                    f"station {station_id} appears in only {count} observation component(s), "
                    f"but a {frame.dimension}D position needs at least {needed}",
                    stations=(station_id,),
                )
            )
    return findings


def _duplicate_findings(active) -> list[Finding]:
    """Observations of the same quantity between the same stations.

    Not an error -- repeated measurements are good practice -- but worth
    surfacing, because a duplicated *import* is a common mistake that inflates
    redundancy and makes the network look stronger than it is.
    """
    seen: dict[tuple, list[str]] = defaultdict(list)
    for observation in active:
        seen[(observation.type, observation.stations)].append(observation.id)

    findings: list[Finding] = []
    for (observation_type, stations), ids in sorted(seen.items(), key=lambda item: item[1]):
        if len(ids) > 1:
            findings.append(
                Finding(
                    "repeated_observations",
                    Severity.INFO,
                    f"{len(ids)} observations of type {observation_type.value} between "
                    f"{' and '.join(stations)}: {', '.join(ids)}. Repeated measurements are "
                    "expected; a duplicated import is not",
                    stations=tuple(stations),
                    observations=tuple(ids),
                )
            )
    return findings


def _approximate_coordinate_findings(network: Network) -> list[Finding]:
    missing = sorted(
        station_id
        for station_id, station in network.stations.items()
        if station.approx_position is None
    )
    if not missing:
        return []
    return [
        Finding(
            "missing_approximate_coordinates",
            Severity.WARNING,
            f"{len(missing)} station(s) have no approximate position: "
            + ", ".join(missing)
            + ". The linearised model needs a point to linearise about; supply them, or "
            "generate them from the observations",
            stations=tuple(missing),
        )
    ]
