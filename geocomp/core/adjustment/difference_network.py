# SPDX-License-Identifier: GPL-2.0-or-later
"""One-dimensional difference networks: what levelling and gravimetry share.

``specs/06-adjustment-core.md`` section 2.3, ``specs/10-module-levelling.md``
section 4 and ``specs/12-module-gravimetry.md``.

A levelling network and a drift-corrected gravimetric network are the same
object: stations carrying one unknown each, connected by observations of the
*difference* between two of them. ADR-0002, Amendment 1 records that they share
their observation equation; this module is where they share everything else that
follows from the shape.

**Why starting values need a module at all.** A difference network is linear, so
the adjustment converges in one iteration from any starting point -- but
:func:`~geocomp.core.adjustment.least_squares.starting_values` still refuses to
invent one, and rightly: for a 2D or 3D network a wrong starting point is a
wrong answer. Here the values are *derivable*, exactly and cheaply, by walking
the observations outward from whatever is known. Deriving them is therefore
neither a guess nor a convenience; it is the arithmetic the user would otherwise
do by hand, and doing it by hand for a hundred benchmarks is where a sign error
enters.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from geocomp.core.adjustment.parameters import Frame
from geocomp.core.errors import ValidationError
from geocomp.core.models import ConstraintMode, Network, Observation, ObservationType

__all__ = ["ApproximateValues", "approximate_values", "connected_components"]

#: Observation types this module can walk. Both are two-station differences of
#: the frame's single component, which is the only property being used.
DIFFERENCE_TYPES = {
    ObservationType.HEIGHT_DIFFERENCE: Frame.HEIGHT_1D,
    ObservationType.GRAVITY_DIFFERENCE: Frame.GRAVITY_1D,
}

#: Types that state a component's value outright rather than a difference.
ABSOLUTE_TYPES = {
    ObservationType.ORTHOMETRIC_HEIGHT: Frame.HEIGHT_1D,
    ObservationType.ELLIPSOIDAL_HEIGHT: Frame.HEIGHT_1D,
    ObservationType.GRAVITY: Frame.GRAVITY_1D,
}


@dataclass
class ApproximateValues:
    """Starting values, and an honest account of where each came from.

    Attributes:
        values: ``{station: {component: value}}``, ready for the ``approximate``
            argument of :func:`~geocomp.core.adjustment.least_squares.adjust`.
        anchored: Stations reached from something known -- a constraint or an
            absolute observation.
        floating: Stations in a component that contained nothing known, and were
            therefore anchored at an arbitrary zero. Not a problem in itself: a
            free network is adjusted exactly this way. It *is* a problem when
            the user believed the network was constrained, so it is reported
            rather than left to be discovered in the datum defect.
        components: How many disconnected pieces the network is in. More than
            one means it cannot be adjusted as a single network, whatever the
            datum, and the caller is better told here than by a singular normal
            matrix.
    """

    values: dict[str, dict[str, float]] = field(default_factory=dict)
    anchored: frozenset[str] = frozenset()
    floating: frozenset[str] = frozenset()
    components: int = 0

    @property
    def is_connected(self) -> bool:
        return self.components <= 1


def _component_name(frame: Frame) -> str:
    if frame not in (Frame.HEIGHT_1D, Frame.GRAVITY_1D):
        raise ValidationError(
            "not_a_difference_frame",
            received=frame.value,
            expected=(
                "HEIGHT_1D or GRAVITY_1D; this module is about networks of one unknown "
                "per station connected by differences"
            ),
        )
    return frame.components[0]


def _usable(observation: Observation, frame: Frame) -> bool:
    return (
        observation.is_active
        and DIFFERENCE_TYPES.get(observation.type) is frame
        and len(observation.stations) == 2
    )


def connected_components(network: Network, frame: Frame) -> list[set[str]]:
    """The station sets the difference observations connect, largest first.

    A network in two pieces has two datum defects, not one, and no single
    constraint can remove both. Reported as sets rather than a count so the
    caller can name the stations in each -- which is what
    ``specs/06`` section 3's rank diagnosis does for the singular case, and
    this is the same courtesy applied before the matrix is ever formed.
    """
    _component_name(frame)
    neighbours: dict[str, set[str]] = {station: set() for station in network.stations}
    for observation in network.observations.values():
        if not _usable(observation, frame):
            continue
        first, second = observation.stations
        if first in neighbours and second in neighbours:
            neighbours[first].add(second)
            neighbours[second].add(first)

    seen: set[str] = set()
    found: list[set[str]] = []
    for station in network.stations:
        if station in seen:
            continue
        group: set[str] = set()
        queue = deque([station])
        seen.add(station)
        while queue:
            current = queue.popleft()
            group.add(current)
            for neighbour in neighbours[current]:
                if neighbour not in seen:
                    seen.add(neighbour)
                    queue.append(neighbour)
        found.append(group)

    return sorted(found, key=len, reverse=True)


def approximate_values(
    network: Network,
    frame: Frame,
    *,
    known: dict[str, float] | None = None,
) -> ApproximateValues:
    """Derive starting values by walking the differences outward from what is known.

    Seeds, in order of precedence:

    1. *known*, passed in by the caller.
    2. A station's constraint -- a fixed or weighted benchmark states its value.
    3. An absolute observation on it: an orthometric height, an observed gravity.
    4. Failing all three, an arbitrary zero at one station per disconnected
       piece, which is reported in
       :attr:`ApproximateValues.floating` rather than silently assumed.

    Args:
        network: Stations and observations. Only active observations are walked;
            a rejected one keeps its record but does not define a height.
        frame: ``HEIGHT_1D`` or ``GRAVITY_1D``.
        known: Values the caller already has, overriding anything in the network.

    Returns:
        The values and the account of how they were obtained.
    """
    component = _component_name(frame)
    seeds: dict[str, float] = {}

    for station in network.stations.values():
        constraint = station.constraint
        if constraint.mode is ConstraintMode.FREE or constraint.position is None:
            continue
        # A 1D constraint names the frame's component under the *position's*
        # naming, which is "up" for a projected position and "height" for a
        # geodetic one. Try both rather than requiring one, because a benchmark
        # legitimately arrives either way.
        for name in ("up", "height", component):
            if name in constraint.position.system.component_names:
                seeds[station.id] = constraint.position.component(name).value
                break

    for observation in network.observations.values():
        if not observation.is_active or ABSOLUTE_TYPES.get(observation.type) is not frame:
            continue
        station = observation.stations[0]
        seeds.setdefault(station, observation.values[0].value)

    for station, value in (known or {}).items():
        if station not in network.stations:
            raise ValidationError(
                "known_value_for_unknown_station",
                station=station,
                expected="a station in the network",
            )
        seeds[station] = value

    edges: dict[str, list[tuple[str, float]]] = {station: [] for station in network.stations}
    for observation in network.observations.values():
        if not _usable(observation, frame):
            continue
        first, second = observation.stations
        if first not in edges or second not in edges:
            continue
        difference = observation.values[0].value
        edges[first].append((second, difference))
        edges[second].append((first, -difference))

    values: dict[str, float] = {}
    anchored: set[str] = set()
    floating: set[str] = set()

    for group in connected_components(network, frame):
        roots = sorted(group & set(seeds))
        if roots:
            queue = deque(roots)
            for root in roots:
                values[root] = seeds[root]
                anchored.add(root)
        else:
            root = sorted(group)[0]
            values[root] = 0.0
            floating.add(root)
            queue = deque([root])

        while queue:
            current = queue.popleft()
            for neighbour, difference in edges[current]:
                if neighbour in values:
                    continue
                values[neighbour] = values[current] + difference
                (anchored if current in anchored else floating).add(neighbour)
                queue.append(neighbour)

    return ApproximateValues(
        values={station: {component: value} for station, value in values.items()},
        anchored=frozenset(anchored),
        floating=frozenset(floating),
        components=len(connected_components(network, frame)),
    )
