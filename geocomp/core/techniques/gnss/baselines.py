# SPDX-License-Identifier: GPL-2.0-or-later
"""GNSS baselines as observations the adjustment can use (FR-602, FR-104).

``specs/11-module-gnss.md`` section 4 and ``specs/08-engine-rtklib.md`` section 8.
Engine-agnostic by construction: nothing here imports an engine or an I/O
module, so a second GNSS engine reuses all of it. The ``.pos``-specific half --
which epoch is the answer, and how much a printed covariance can be trusted --
lives in :mod:`geocomp.engines.rtklib.baseline`.

Three things in this module are the whole of why it exists.

**A baseline is ECEF, and it says so.** The frame is carried on the
:class:`~geocomp.core.models.observation.BaselineFrame` the observation records,
because the two consumers of a baseline disagreed about it until this phase:
DynAdjust's ``G`` measurement is geocentric, the in-house core's
``Frame.SPACE_3D`` is local east/north/up, and an ECEF vector adjusted in-house
came out wrong by a rotation with nothing raised. :func:`rotate_baseline_to_local`
is what makes the in-house path available rather than merely refused.

**Antenna height reduction happens once.** Not by the caller remembering, but
because :func:`reduce_to_marks` records what it applied on the baseline it
returns and refuses a second application by name. ``specs/11`` acceptance
criterion 5 asks for a test that a double reduction is prevented; a flag a
caller has to check is not that.

**Processing every pair is not the same as observing every pair.** *n*
simultaneously observing stations yield ``n(n-1)/2`` baselines of which only
``n-1`` are independent, and feeding all of them to an adjustment as though they
were independent inflates the redundancy and understates the uncertainty of
everything downstream. :func:`independent_subset` names the independent set and
**marks** the rest rather than discarding them -- ``specs/11`` section 3.1 allows
the full set in Advanced mode, with the consequence stated.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from typing import Any

import numpy as np

from geocomp.core.errors import DataError, ValidationError
from geocomp.core.geodesy.cartesian import (
    ecef_to_enu,
    ecef_to_enu_covariance,
    enu_rotation,
)
from geocomp.core.models import (
    BaselineFrame,
    Cluster,
    ClusterKind,
    Observation,
    ObservationType,
)
from geocomp.core.models.observation import BASELINE_FRAME_KEY
from geocomp.core.uncertainty import Covariance, Quantity, Strategy, UncertaintyMode
from geocomp.core.units import Unit

__all__ = [
    "AntennaOffset",
    "AntennaReduction",
    "Baseline",
    "LoopClosure",
    "components_from_covariance",
    "independent_subset",
    "loop_closure",
    "reduce_to_marks",
    "rotate_baseline_to_local",
    "to_cluster",
]

#: Component names per frame. ECEF names match what ``<GPSBaseline>`` writes;
#: LOCAL names match ``Frame.SPACE_3D.components``, which is what the design
#: matrix indexes rows by.
_COMPONENTS: dict[BaselineFrame, tuple[str, str, str]] = {
    BaselineFrame.ECEF: ("x", "y", "z"),
    BaselineFrame.LOCAL: ("e", "n", "u"),
}


@dataclass(frozen=True)
class AntennaOffset:
    """Where the antenna reference point stood relative to the mark.

    The three components are the RINEX ``ANTENNA: DELTA H/E/N`` convention: *up*
    from the mark, then *east* and *north* eccentricity. They are
    :class:`Quantity` because they are measured -- a tape reading to the antenna
    rim is an observation like any other, and FR-204 requires its uncertainty to
    reach the result.

    ``method`` matches :attr:`GnssSession.antenna_height_method` and the values
    of ``geocomp.io.rinex.HeightMethod``. It is a string rather than that enum
    on purpose: ``core`` does not import ``io`` anywhere in this project, and
    the method is a property of how the survey was done, not of the file it was
    read from.
    """

    up: Quantity
    east: Quantity | None = None
    north: Quantity | None = None
    method: str = "unstated"

    def __post_init__(self) -> None:
        for name in ("up", "east", "north"):
            quantity = getattr(self, name)
            if quantity is not None and quantity.unit is not Unit.METRE:
                raise DataError(
                    "antenna_offset_unit",
                    component=name,
                    received=quantity.unit.name,
                    expected="METRE",
                )

    @property
    def is_eccentric(self) -> bool:
        return bool(
            (self.east is not None and self.east.value) or (self.north is not None and self.north.value)
        )

    def vector(self) -> tuple[Quantity, Quantity, Quantity]:
        """(east, north, up), the order the rotation expects."""
        zero = Quantity.exact(0.0, Unit.METRE)
        return (self.east or zero, self.north or zero, self.up)


@dataclass(frozen=True)
class AntennaReduction:
    """What :func:`reduce_to_marks` subtracted, kept so it cannot happen twice.

    Its presence on a :class:`Baseline` *is* the record. ``specs/08`` section 8
    rule 4 requires the reduction to be "recorded so it can never be applied
    twice", and a record that lives anywhere but on the reduced object can be
    separated from it by any caller that copies the components out.
    """

    base: AntennaOffset
    rover: AntennaOffset

    @property
    def is_eccentric(self) -> bool:
        return self.base.is_eccentric or self.rover.is_eccentric


@dataclass(frozen=True)
class Baseline:
    """One determined vector between two marks, with its covariance whole.

    Attributes:
        components: Three :class:`Quantity` in the order
            :data:`_COMPONENTS` gives for :attr:`frame`.
        covariance: The full 3x3 over those components. The authority --
            :attr:`components` carries only the diagonal, and reducing a
            baseline to three standard deviations is the error FR-104 exists to
            prevent.
        base_horizon: Geodetic latitude and longitude of the base station, in
            radians.
        rover_horizon: The same for the rover. **Both are carried, because they
            are not the same horizon.** Over a 3 km baseline the local vertical
            turns by about 0.03 degrees, which is 0.8 mm across a 1.5 m antenna
            offset -- larger than the millimetre the rest of this module is
            careful about, so the antenna reduction rotates each end's offset at
            its own end.
        antenna_reduction: ``None`` until :func:`reduce_to_marks` runs. Once set,
            a second reduction raises.
    """

    id: str
    base_station: str
    rover_station: str
    components: tuple[Quantity, Quantity, Quantity]
    covariance: Covariance
    base_horizon: tuple[float, float]
    rover_horizon: tuple[float, float]
    frame: BaselineFrame = BaselineFrame.ECEF
    base_session: str = ""
    rover_session: str = ""
    is_independent: bool | None = None
    antenna_reduction: AntennaReduction | None = None
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.base_station == self.rover_station:
            raise DataError(
                "baseline_between_one_station",
                baseline=self.id,
                station=self.base_station,
                expected="two distinct stations",
            )
        if len(self.components) != 3:
            raise DataError(
                "baseline_component_count",
                baseline=self.id,
                received=len(self.components),
                expected="three components",
            )
        for index, quantity in enumerate(self.components):
            if quantity.unit is not Unit.METRE:
                raise DataError(
                    "baseline_component_unit",
                    baseline=self.id,
                    component=_COMPONENTS[self.frame][index],
                    received=quantity.unit.name,
                    expected="METRE",
                )
        if self.covariance.size != 3:
            raise DataError(
                "baseline_covariance_size",
                baseline=self.id,
                received=self.covariance.size,
                expected="a 3x3 over the three components",
            )

    @property
    def length(self) -> Quantity:
        """The chord, with its uncertainty propagated from the full 3x3.

        Rotation-invariant, so it is the same number in either frame -- which is
        what ``tests/test_gnss_baselines.py`` uses to check that a rotation
        changed the representation and not the vector.
        """
        values = np.array([q.value for q in self.components])
        distance = float(np.linalg.norm(values))
        if distance == 0.0:
            return Quantity.exact(0.0, Unit.METRE)
        jacobian = (values / distance).reshape(1, 3)
        propagated = self.covariance.transform(jacobian, ["length"], [Unit.METRE])
        return Quantity(
            value=distance,
            variance=float(propagated.matrix[0, 0]),
            unit=Unit.METRE,
            mode=propagated.mode,
            strategies=propagated.strategies,
        )

    @property
    def component_names(self) -> tuple[str, str, str]:
        return _COMPONENTS[self.frame]


def rotate_baseline_to_local(baseline: Baseline) -> Baseline:
    """Rotate an ECEF baseline into the local horizon at its base station.

    This is what makes a GNSS baseline usable by the in-house adjustment core,
    whose ``Frame.SPACE_3D`` estimates east, north and up. The covariance goes
    through ``R Sigma R^T`` (FR-201): the correlations are carried, not dropped,
    and the result's length is unchanged because a rotation preserves it.

    **The horizon is the base station's**, which is the local-geodetic
    convention and the only choice that makes two baselines sharing a base
    directly comparable. A network whose baselines have different bases is
    adjusted in a projected frame instead; ``specs/06`` section 1 already
    assigns the ellipsoidal case to DynAdjust, which takes ECEF and needs no
    rotation at all.

    Raises:
        ValidationError: if *baseline* is already local. Rotating twice is a
            different wrong answer from not rotating at all, and both are
            silent, so neither is allowed.
    """
    if baseline.frame is BaselineFrame.LOCAL:
        raise ValidationError(
            "baseline_already_local",
            baseline=baseline.id,
            expected="an ECEF baseline; this one has already been rotated",
        )

    latitude, longitude = baseline.base_horizon
    values = tuple(q.value for q in baseline.components)
    rotated = ecef_to_enu(values, latitude, longitude)
    covariance = ecef_to_enu_covariance(baseline.covariance, latitude, longitude)

    return replace(
        baseline,
        frame=BaselineFrame.LOCAL,
        components=components_from_covariance(rotated, covariance),
        covariance=covariance,
    )


def reduce_to_marks(baseline: Baseline, base: AntennaOffset, rover: AntennaOffset) -> Baseline:
    """Reduce an antenna-to-antenna baseline to mark-to-mark (FR-602, FR-204).

    An engine determines the vector between two *antenna reference points*. The
    adjustment wants the vector between two *marks*, and the difference is the
    two antenna offsets rotated into ECEF at their own stations::

        d_mark = d_ARP - R(rover)^T . o_rover + R(base)^T . o_base

    Both offsets' uncertainties are propagated into the result, which is the
    point of FR-204: an antenna height read to the nearest centimetre puts a
    centimetre into the baseline's height component, and a result that did not
    say so would be claiming a precision the survey does not have.

    Raises:
        ValidationError: if the baseline is not ECEF (the rotation above is
            defined there), if a reduction has already been applied, or if
            either offset's method is ``slant`` -- a slant height is measured to
            the antenna *rim* and needs the antenna's radius and phase-centre
            model to become a vertical offset, which is FR-063's antenna
            database and not yet present. Treating it as vertical would be wrong
            by centimetres in height, quietly.
    """
    if baseline.antenna_reduction is not None:
        raise ValidationError(
            "antenna_height_already_reduced",
            baseline=baseline.id,
            expected=(
                "a baseline that has not been reduced; this one already carries "
                "its reduction, and applying a second would double the offset"
            ),
        )
    if baseline.frame is not BaselineFrame.ECEF:
        raise ValidationError(
            "antenna_reduction_needs_ecef",
            baseline=baseline.id,
            received=baseline.frame.value,
            expected="an ECEF baseline -- reduce before rotating, not after",
        )
    for name, offset in (("base", base), ("rover", rover)):
        if offset.method == "slant":
            raise ValidationError(
                "antenna_height_is_slant",
                baseline=baseline.id,
                end=name,
                expected=(
                    "a vertical offset from the mark to the antenna reference "
                    "point. A slant height is measured to the antenna rim and "
                    "needs the antenna's dimensions to be converted; GeoComp "
                    "has no antenna database yet, and assuming vertical is "
                    "wrong by centimetres in height"
                ),
            )

    base_rotation = enu_rotation(*baseline.base_horizon).T
    rover_rotation = enu_rotation(*baseline.rover_horizon).T

    base_vector = np.array([q.value for q in base.vector()])
    rover_vector = np.array([q.value for q in rover.vector()])
    shift = base_rotation @ base_vector - rover_rotation @ rover_vector

    values = np.array([q.value for q in baseline.components]) + shift

    # The offsets enter linearly, so the Jacobian of the sum with respect to the
    # six offset components is the two rotations side by side. Their covariances
    # are diagonal -- three independent tape readings at each end -- which is the
    # only assumption here and it is the honest one: nothing measures the
    # correlation between two separate setups.
    offsets = Covariance.from_quantities(
        {
            f"{end}.{axis}": quantity.detached()
            for end, offset in (("base", base), ("rover", rover))
            for axis, quantity in zip(("e", "n", "u"), offset.vector(), strict=True)
        }
    )
    jacobian = np.hstack([base_rotation, -rover_rotation])
    propagated = offsets.transform(jacobian, list(baseline.component_names), [Unit.METRE] * 3)
    covariance = Covariance(
        matrix=baseline.covariance.matrix + propagated.matrix,
        labels=baseline.covariance.labels,
        units=baseline.covariance.units,
        mode=_weaker(baseline.covariance, propagated),
        strategies=frozenset(baseline.covariance.strategies | propagated.strategies),
    )

    return replace(
        baseline,
        components=components_from_covariance(tuple(float(v) for v in values), covariance),
        covariance=covariance,
        antenna_reduction=AntennaReduction(base=base, rover=rover),
    )


def independent_subset(
    baselines: list[Baseline],
) -> tuple[list[Baseline], list[Baseline]]:
    """Split *baselines* into an independent set and the dependent remainder.

    ``n`` stations observing simultaneously produce ``n(n-1)/2`` baselines of
    which only ``n-1`` carry new information; the rest are exact linear
    combinations. An adjustment given all of them reports a redundancy it does
    not have and an uncertainty smaller than the data supports -- a classic
    error, and one that leaves no trace in the result.

    The independent set is a maximum spanning forest over the station graph,
    chosen by union-find in the shape of
    :func:`geocomp.core.preanalysis.inspection._connected_components`. "Maximum"
    is by **quality**: a baseline whose covariance has the smaller trace is
    preferred, so the independent set is the best-determined spanning tree
    rather than whichever one the input order happened to produce.

    Both lists come back with :attr:`Baseline.is_independent` set, and **nothing
    is discarded** -- ``specs/11`` section 3.1 offers the independent set by
    default and the full set in Advanced mode with the consequence stated, which
    needs the dependent ones to still exist and to know what they are.

    Returns:
        ``(independent, dependent)``, each in the input's order.
    """
    parent: dict[str, str] = {}

    def find(item: str) -> str:
        parent.setdefault(item, item)
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    def union(a: str, b: str) -> bool:
        root_a, root_b = find(a), find(b)
        if root_a == root_b:
            return False
        parent[root_b] = root_a
        return True

    order = sorted(
        range(len(baselines)),
        key=lambda index: (float(np.trace(baselines[index].covariance.matrix)), index),
    )
    chosen: set[int] = set()
    for index in order:
        baseline = baselines[index]
        if union(baseline.base_station, baseline.rover_station):
            chosen.add(index)

    independent: list[Baseline] = []
    dependent: list[Baseline] = []
    for index, baseline in enumerate(baselines):
        marked = replace(baseline, is_independent=index in chosen)
        (independent if index in chosen else dependent).append(marked)
    return independent, dependent


@dataclass(frozen=True)
class LoopClosure:
    """By how much a circuit of baselines fails to return where it started.

    Attributes:
        loop: The stations in circuit order. The circuit closes back onto the
            first, which is not repeated here.
        legs: The baseline ids traversed, in the order :attr:`loop` gives.
        misclosure: The sum of the traversed vectors, which a perfect set of
            baselines would leave at zero.
        covariance: The full 3x3 over the misclosure. **Always approximate.**
            The legs of a loop normally come from one session and share
            satellites, clocks and atmosphere, so adding their covariances as
            though they were independent understates the truth. That is
            recorded as :data:`Strategy.INDEPENDENCE_ASSUMED` rather than left
            for the reader to infer, because a misclosure judged against an
            over-optimistic sigma looks significant when it is not.
        perimeter_m: The summed leg lengths, so the misclosure can also be
            expressed against the distance travelled.
    """

    loop: tuple[str, ...]
    legs: tuple[str, ...]
    misclosure: tuple[Quantity, Quantity, Quantity]
    covariance: Covariance
    perimeter_m: float

    @property
    def magnitude_m(self) -> float:
        """The length of the misclosure vector."""
        return float(np.linalg.norm([component.value for component in self.misclosure]))

    @property
    def parts_per_million(self) -> float:
        """Misclosure against distance travelled, the conventional form.

        Zero for a degenerate perimeter rather than an infinity, because a
        quality figure that can be ``inf`` propagates into reports that cannot
        print it.
        """
        if self.perimeter_m <= 0.0:
            return 0.0
        return 1.0e6 * self.magnitude_m / self.perimeter_m


def loop_closure(baselines: list[Baseline], loop: Sequence[str]) -> LoopClosure:
    """Sum the baselines around *loop* and report what fails to cancel.

    A closed circuit of measured vectors must come back to where it began, so
    the sum is zero but for the errors in the legs. That makes closure the one
    check on a set of baselines needing **no external coordinate at all**: it
    asks whether the measurements agree with each other rather than with
    somebody's published position, and so it measures what the processing
    controls instead of what the reference does. ``specs/20`` section 6 rests
    RD-06's GNSS criterion on exactly that distinction.

    **The sum is taken in ECEF, and a local-frame baseline is refused.** East,
    north and up at one station are not east, north and up at another, so
    adding local vectors around a circuit adds three different frames and
    returns a misclosure that is mostly rotation. Over the 65 m GGAO triangle
    the two horizons differ by about 2e-6 radians and the error would hide
    under a millimetre; over a 50 km loop it would not, and a check that is
    silently wrong only at the scale where it matters is worse than none.

    Antenna reduction has to match too. A loop mixing baselines reduced to the
    marks with baselines still at the antenna reference points closes by the
    difference of the antenna heights, which looks exactly like a measurement
    error and is not one.

    Args:
        baselines: The available baselines; only those the loop names are used.
        loop: Three or more distinct stations in circuit order.

    Returns:
        The :class:`LoopClosure`, whose misclosure is zero for a perfect set.

    Raises:
        ValidationError: The loop is too short, repeats a station, or names a
            leg no baseline covers.
        DataError: A leg is not ECEF, or the legs disagree about whether the
            antenna reduction has been applied.
    """
    stations = tuple(loop)
    if len(stations) < 3:
        raise ValidationError(
            "gnss_loop_too_short",
            received=len(stations),
            expected=(
                "at least three stations; a two-station circuit retraces one "
                "baseline and closes by construction"
            ),
        )
    if len(set(stations)) != len(stations):
        raise ValidationError(
            "gnss_loop_repeats_a_station",
            loop=stations,
            expected="distinct stations; a repeated one splits the circuit into two loops",
        )

    available = {(line.base_station, line.rover_station): line for line in baselines}
    legs: list[str] = []
    total = np.zeros(3)
    matrix = np.zeros((3, 3))
    perimeter = 0.0
    strategies: set[Strategy] = {Strategy.INDEPENDENCE_ASSUMED}
    reductions: set[bool] = set()

    for index, start in enumerate(stations):
        end = stations[(index + 1) % len(stations)]
        # Either orientation carries the same information; traversing a
        # baseline against its sense is a negation, not a different measurement.
        if (start, end) in available:
            line, sign = available[(start, end)], 1.0
        elif (end, start) in available:
            line, sign = available[(end, start)], -1.0
        else:
            raise ValidationError(
                "gnss_loop_leg_missing",
                base=start,
                rover=end,
                expected="a baseline between these two stations, in either orientation",
            )
        if line.frame is not BaselineFrame.ECEF:
            raise DataError(
                "gnss_loop_leg_not_ecef",
                baseline=line.id,
                frame=line.frame.value,
                expected=(
                    "ECEF; local east/north/up differs from station to station, so a "
                    "circuit of local vectors sums three different frames"
                ),
            )
        reductions.add(line.antenna_reduction is not None)
        values = np.array([component.value for component in line.components])
        total += sign * values
        # Negating a vector leaves its covariance unchanged, so the sign does
        # not appear here.
        matrix += line.covariance.matrix
        perimeter += float(np.linalg.norm(values))
        strategies |= set(line.covariance.strategies)
        legs.append(line.id)

    if len(reductions) > 1:
        raise DataError(
            "gnss_loop_mixed_antenna_reduction",
            loop=stations,
            expected=(
                "every leg reduced to the marks, or none of them; a mixed loop closes by the antenna heights"
            ),
        )

    covariance = Covariance(
        matrix=matrix,
        labels=_COMPONENTS[BaselineFrame.ECEF],
        units=(Unit.METRE,) * 3,
        mode=UncertaintyMode.APPROXIMATE,
        strategies=frozenset(strategies),
    )
    return LoopClosure(
        loop=stations,
        legs=tuple(legs),
        misclosure=components_from_covariance(tuple(total), covariance),
        covariance=covariance,
        perimeter_m=perimeter,
    )


def to_cluster(baselines: list[Baseline], *, cluster_id: str) -> tuple[list[Observation], Cluster]:
    """Build the correlated observation cluster an adjustment takes (FR-104).

    Every baseline becomes a three-component ``GNSS_BASELINE`` observation, and
    the whole set shares one ``3n x 3n``. **Member order is the contract**: the
    DynaML writer slices the matrix by position and never reads its labels
    (``engines/dynadjust/dynaml.py`` ``_cluster_blocks``), so the order of
    ``observation_ids`` is what pairs a block with an observation. The labels
    follow ``m{i}.{x|y|z}``, which is what both DynAdjust readers already emit,
    so a cluster built here and one read from a file are indistinguishable.

    **Cross-baseline correlations are absent, and that is stated rather than
    invented** (``specs/08`` section 8 rule 5). ``rnx2rtkp`` processes one
    baseline per run and supplies no correlation between two of them; filling
    the off-diagonal blocks with zeros is not a claim that they are uncorrelated
    but a record that nothing measured them, and
    :attr:`Cluster.covariance` carries the strategies that say so.

    Raises:
        DataError: if *baselines* is empty, or if they do not all share one
            frame -- a cluster mixing an ECEF baseline with a rotated one has no
            single meaning and would be written or adjusted as though it did.
    """
    if not baselines:
        raise DataError(
            "baseline_cluster_empty",
            cluster=cluster_id,
            expected="at least one baseline",
        )
    frames = {baseline.frame for baseline in baselines}
    if len(frames) != 1:
        raise DataError(
            "baseline_cluster_mixed_frames",
            cluster=cluster_id,
            received=sorted(frame.value for frame in frames),
            expected="one frame for every member of a cluster",
        )
    frame = frames.pop()

    count = len(baselines)
    size = 3 * count
    matrix = np.zeros((size, size))
    observations: list[Observation] = []
    strategies: set[Any] = set()
    for index, baseline in enumerate(baselines):
        matrix[3 * index : 3 * index + 3, 3 * index : 3 * index + 3] = baseline.covariance.matrix
        strategies |= set(baseline.covariance.strategies)
        observations.append(
            Observation(
                id=f"{cluster_id}-{baseline.id}",
                type=ObservationType.GNSS_BASELINE,
                stations=(baseline.base_station, baseline.rover_station),
                values=baseline.components,
                cluster_id=cluster_id,
                meta={**baseline.meta, BASELINE_FRAME_KEY: frame.value},
            )
        )

    cluster = Cluster(
        id=cluster_id,
        kind=ClusterKind.GNSS_BASELINE,
        observation_ids=tuple(o.id for o in observations),
        covariance=Covariance(
            matrix=matrix,
            labels=tuple(f"m{i}.{c}" for i in range(count) for c in ("x", "y", "z")),
            units=(Unit.METRE,) * size,
            mode=_weakest(baselines),
            strategies=frozenset(strategies),
        ),
    )
    return observations, cluster


def components_from_covariance(
    values: tuple[float, ...], covariance: Covariance
) -> tuple[Quantity, Quantity, Quantity]:
    """Three components carrying the covariance's diagonal.

    The covariance stays the authority; these exist so a caller that wants one
    component at a time can have it, and :class:`Observation` requires them.
    Public because an engine adapter building a :class:`Baseline` needs exactly
    this and should not be reaching into a private helper to get it.
    """
    return tuple(  # type: ignore[return-value]
        Quantity(
            value=float(value),
            variance=float(covariance.matrix[index, index]),
            unit=Unit.METRE,
            mode=covariance.mode,
            strategies=covariance.strategies,
        )
        for index, value in enumerate(values)
    )


def _weaker(left: Covariance, right: Covariance) -> UncertaintyMode:
    """The weaker of two modes.

    A sum is no better than its worst term, and letting the rigorous one win is
    how an approximation launders itself into a result that claims to be
    rigorous (``specs/05`` section 2.3).
    """
    if UncertaintyMode.APPROXIMATE in (left.mode, right.mode):
        return UncertaintyMode.APPROXIMATE
    return left.mode


def _weakest(baselines: list[Baseline]) -> UncertaintyMode:
    modes = {baseline.covariance.mode for baseline in baselines}
    if UncertaintyMode.APPROXIMATE in modes:
        return UncertaintyMode.APPROXIMATE
    return next(iter(modes))
