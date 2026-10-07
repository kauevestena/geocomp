# SPDX-License-Identifier: GPL-2.0-or-later
"""The parameter vector: what the adjustment estimates, and where each unknown sits.

``specs/06-adjustment-core.md`` sections 2.3 and 3.1.

Beyond station coordinates the adjustment estimates auxiliary unknowns --
one orientation per direction set, drift parameters per gravimeter session
(FR-702), and later scale and refraction coefficients. All of them are columns
of the same design matrix, so they are laid out here rather than bolted on.

**Fixed stations get no column.** A station held exactly is not an unknown, so
eliminating it is both the numerically cleanest treatment and the honest one:
the alternative, a pseudo-observation with an enormous weight, silently trades
exactness for conditioning. Weighted constraints *do* become observations,
because that is precisely what a weighted constraint is.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import numpy as np

from geocomp.core.errors import DataError, ValidationError
from geocomp.core.models import (
    GRAVITY_COMPONENT,
    BaselineFrame,
    ConstraintMode,
    Network,
    Observation,
    Position,
    Station,
)
from geocomp.core.uncertainty import Covariance
from geocomp.core.units import Unit

__all__ = [
    "DRIFT_PREFIX",
    "Frame",
    "ParameterLayout",
    "ParameterSlot",
    "WeightedConstraint",
    "drift_component",
    "is_drift_component",
    "orientation_owner",
    "weighted_constraints",
]


def orientation_owner(observation: Observation) -> str:
    """Whose orientation unknown a direction carries: its setup's.

    A direction's circle zero is arbitrary, so without an orientation unknown it
    is adjusted as an absolute azimuth -- not imprecise but unrelated to the
    geometry. The setup is named by ``setup_id``; by an explicit
    ``meta["orientation_owner"]`` where two setups share one (a pillar occupied
    twice); and failing both by the direction's **cluster**, because a
    direction set is one setup's by construction and some readers name only the
    set. Until this, a set naming only its cluster was silently adjusted as
    azimuths: a DynaML direction set read back without setup ids came out 38
    degrees from its own readings with nothing to say why. A direction outside
    a set cannot be constructed (``observation_requires_cluster``), so the
    refusal here is a guard, not a path anything should reach.
    """
    owner = (
        observation.setup_id
        or (observation.meta or {}).get("orientation_owner")
        or observation.cluster_id
    )
    if not owner:
        raise ValidationError(
            "direction_without_setup",
            observation=observation.id,
            expected=(
                "a setup id, or membership of a direction set; without one the "
                "direction has no orientation unknown and would be adjusted as an "
                "absolute azimuth"
            ),
        )
    return owner


class Frame(Enum):
    """The coordinate frame the adjustment works in, and its components.

    **Scope note.** P2 adjusts in a projected or local-cartesian frame. Geodetic
    (latitude, longitude, height) observation equations on the ellipsoid are a
    documented gap: they matter mainly for continental-scale GNSS networks,
    which is exactly the case ``specs/06`` section 1 assigns to DynAdjust
    (phase P6). A network in geographic coordinates is projected before
    adjustment, and the frame is recorded on the solution.
    """

    #: Heights only. Geometric levelling, trigonometric height networks.
    HEIGHT_1D = "height_1d"
    #: Planimetric. Classical triangulation, trilateration, traverses.
    PLANE_2D = "plane_2d"
    #: Three-dimensional, local cartesian or projected with an up component.
    SPACE_3D = "space_3d"
    #: Station gravity values. Not coordinates; the same machinery, different meaning.
    GRAVITY_1D = "gravity_1d"
    #: Geocentric X, Y, Z, with every observation evaluated at its own station's
    #: vertical (phase P9a). The frame for combining techniques over any extent;
    #: see :mod:`geocomp.core.adjustment.geocentric`.
    GEOCENTRIC_3D = "geocentric_3d"

    @property
    def components(self) -> tuple[str, ...]:
        """The parameter components a station has in this frame."""
        return {
            Frame.HEIGHT_1D: ("h",),
            Frame.PLANE_2D: ("e", "n"),
            Frame.SPACE_3D: ("e", "n", "u"),
            Frame.GRAVITY_1D: ("g",),
            Frame.GEOCENTRIC_3D: ("x", "y", "z"),
        }[self]

    @property
    def dimension(self) -> int:
        """Which of 1D, 2D and 3D this frame is, for the observation registry."""
        return {
            Frame.HEIGHT_1D: 1,
            Frame.PLANE_2D: 2,
            Frame.SPACE_3D: 3,
            Frame.GRAVITY_1D: 1,
            Frame.GEOCENTRIC_3D: 3,
        }[self]

    @property
    def position_components(self) -> tuple[str, ...]:
        """Where each of this frame's components lives in a projected position.

        A :class:`~geocomp.core.models.position.Position` is always three
        components named ``(easting, northing, up)``; a frame may estimate
        fewer. The mapping between them is stated **once, here**, because
        writing a solution and reading approximate coordinates are the two
        directions of the same correspondence, and phase P4 found them
        disagreeing: a 1D height solution was written into the *easting* slot
        while approximate heights were read from the *up* slot, so every
        levelling result reported a height of zero.

        **Gravity lives in no position slot.** Until phase P8 it was mapped to
        ``up`` for want of anywhere better, which put an acceleration in a field
        that enforces metres; a gravity solution could not even be written,
        because :class:`~geocomp.core.models.position.Position` refused it. A
        station's known gravity is now
        :attr:`~geocomp.core.models.station.ConstraintSpec.gravity` and its
        adjusted gravity
        :attr:`~geocomp.core.models.solution.AdjustedStation.gravity`, so this
        mapping is empty for ``GRAVITY_1D`` and the callers that read or write a
        position branch on the frame instead.
        """
        return {
            Frame.HEIGHT_1D: ("up",),
            Frame.PLANE_2D: ("easting", "northing"),
            Frame.SPACE_3D: ("easting", "northing", "up"),
            Frame.GRAVITY_1D: (),
            # A geocentric frame reads and writes cartesian positions, whose
            # components are named for themselves.
            Frame.GEOCENTRIC_3D: ("x", "y", "z"),
        }[self]

    @property
    def position_indices(self) -> tuple[int, ...]:
        """The same correspondence as indices into the position's triple."""
        if self is Frame.GEOCENTRIC_3D:
            return (0, 1, 2)
        names = ("easting", "northing", "up")
        return tuple(names.index(name) for name in self.position_components)

    @property
    def component_units(self) -> tuple[Unit, ...]:
        """The unit of each component: m/s² for gravity, metres otherwise."""
        if self is Frame.GRAVITY_1D:
            return (Unit.ACCELERATION,)
        return tuple(Unit.METRE for _ in self.components)


@dataclass(frozen=True)
class ParameterSlot:
    """One estimated unknown.

    Attributes:
        kind: ``"station"`` or ``"auxiliary"``.
        owner: Station id, or the auxiliary parameter's owner (a setup id, an
            instrument id).
        component: Coordinate component, or the auxiliary parameter's name.
    """

    kind: str
    owner: str
    component: str

    @property
    def label(self) -> str:
        """``owner.component``: how a parameter is named in reports and refusals."""
        return f"{self.owner}.{self.component}"


@dataclass
class ParameterLayout:
    """Maps every estimated unknown to a column of the design matrix.

    Built once per adjustment. Fixed station components are deliberately absent
    from the column map: :meth:`column` returns ``None`` for them, and the
    observation equations simply skip that term. The fixed coordinate still
    enters the computed value, which is what holding a station means.
    """

    frame: Frame
    #: The network's stated cartesian frame, carried so the observation
    #: equations can refuse a baseline expressed in a different one. ``None``
    #: when the network did not say -- see :attr:`Network.cartesian_frame`.
    cartesian_frame: BaselineFrame | None = None
    slots: list[ParameterSlot] = field(default_factory=list)
    _columns: dict[tuple[str, str], int] = field(default_factory=dict, repr=False)
    #: Values of components that are held fixed, keyed as (owner, component).
    fixed_values: dict[tuple[str, str], float] = field(default_factory=dict)

    # -- construction ----------------------------------------------------

    @classmethod
    def build(
        cls,
        network: Network,
        frame: Frame,
        *,
        auxiliary: dict[str, tuple[str, ...]] | None = None,
    ) -> ParameterLayout:
        """Lay out the unknowns for *network* in *frame*.

        Args:
            network: Provides the stations and their constraints.
            frame: Which components each station contributes.
            auxiliary: ``{owner: (parameter name, ...)}`` for orientation and
                drift unknowns, in a stable order.
        """
        layout = cls(frame=frame, cartesian_frame=network.cartesian_frame)

        for station_id in sorted(network.stations):
            station = network.stations[station_id]
            for component in frame.components:
                if _is_fixed(station, component, frame):
                    layout.fixed_values[(station_id, component)] = _fixed_value(
                        station, component, frame
                    )
                    continue
                layout._add(ParameterSlot("station", station_id, component))

        for owner in sorted(auxiliary or {}):
            for name in (auxiliary or {})[owner]:
                layout._add(ParameterSlot("auxiliary", owner, name))

        if not layout.slots:
            raise ValidationError(
                "no_estimable_parameters",
                expected=(
                    "at least one unknown; every station appears to be fixed, so "
                    "there is nothing for the adjustment to estimate"
                ),
            )
        return layout

    def _add(self, slot: ParameterSlot) -> None:
        self._columns[(slot.owner, slot.component)] = len(self.slots)
        self.slots.append(slot)

    # -- access ----------------------------------------------------------

    @property
    def size(self) -> int:
        """The number of parameters."""
        return len(self.slots)

    def column(self, owner: str, component: str) -> int | None:
        """Column index of an unknown, or ``None`` when it is held fixed."""
        return self._columns.get((owner, component))

    def is_fixed(self, owner: str, component: str) -> bool:
        """Whether *owner*'s *component* is held, and so not a parameter."""
        return (owner, component) in self.fixed_values

    def labels(self) -> list[str]:
        """Every parameter's ``owner.component`` label, in column order."""
        return [slot.label for slot in self.slots]

    def station_columns(self, station_id: str) -> dict[str, int]:
        """The estimated components of one station, by component name."""
        return {
            component: column
            for component in self.frame.components
            if (column := self.column(station_id, component)) is not None
        }

    def station_ids(self) -> list[str]:
        """The stations with at least one parameter, in the order they first appear."""
        seen: list[str] = []
        for slot in self.slots:
            if slot.kind == "station" and slot.owner not in seen:
                seen.append(slot.owner)
        return seen

    def component_units(self) -> list[Unit]:
        """The unit of each column, for the resulting covariance."""
        units: list[Unit] = []
        for slot in self.slots:
            if slot.kind == "station":
                index = self.frame.components.index(slot.component)
                units.append(self.frame.component_units[index])
            elif slot.component == "orientation":
                units.append(Unit.RADIAN)
            elif is_drift_component(slot.component):
                # A drift coefficient multiplies a *dimensionless* elapsed time
                # (hours over a declared scale, specs/12 section 4.3), so each
                # one is an acceleration: the drift accumulated per unit of it.
                units.append(Unit.ACCELERATION)
            else:
                units.append(Unit.DIMENSIONLESS)
        return units


#: Drift coefficients are auxiliary unknowns named ``drift_1``, ``drift_2``, ...
#: by polynomial degree (``specs/12`` section 4.3).
DRIFT_PREFIX = "drift_"


def drift_component(degree: int) -> str:
    """The auxiliary parameter name of the degree-*degree* drift coefficient."""
    if degree < 1:
        raise ValidationError(
            "drift_degree_invalid",
            received=degree,
            expected="a polynomial degree of 1 or more; degree 0 is an offset, and a "
            "difference observation cannot see one",
        )
    return f"{DRIFT_PREFIX}{degree}"


def is_drift_component(component: str) -> bool:
    return component.startswith(DRIFT_PREFIX) and component[len(DRIFT_PREFIX):].isdigit()


def _is_fixed(station: Station, component: str, frame: Frame) -> bool:
    constraint = station.constraint
    if constraint.mode is not ConstraintMode.FIXED:
        return False
    if frame is Frame.GEOCENTRIC_3D:
        held = _geocentric_components(station)
        # A geodetic hold is all three axes or a refusal; a cartesian one, each.
        return held is not None and (held == _GEODETIC or component in held)
    return _constraint_name(component, frame) in constraint.components


_GEODETIC = ("latitude", "longitude", "height")


def _geocentric_components(station: Station) -> tuple[str, ...] | None:
    """The position components a constraint holds, as the geocentric frame sees them.

    A cartesian constraint names X, Y and Z directly. A **geodetic** one names
    latitude, longitude and height, none of which is an ECEF axis, and matching
    the names against ``x``, ``y``, ``z`` -- what this did until P9a -- found
    nothing and left every geodetically held station **free**, silently. Held
    whole, it holds all three axes; held in part (a height alone, say), it
    constrains a combination no subset of X, Y, Z expresses, and is refused: the
    height of a benchmark enters the combined model as a height observation.

    Returns the constrained names, or ``None`` for a constraint that holds
    nothing.
    """
    from geocomp.core.models import CoordinateSystem

    constraint = station.constraint
    position = constraint.position
    if constraint.mode is ConstraintMode.FREE or position is None or not constraint.components:
        return None
    if position.system is not CoordinateSystem.GEODETIC:
        return tuple(name for name in ("x", "y", "z") if name in constraint.components) or None
    held = tuple(name for name in _GEODETIC if name in constraint.components)
    if len(held) != len(_GEODETIC):
        raise ValidationError(
            "geocentric_frame_partial_geodetic_constraint",
            station=station.id,
            received=list(held),
            expected=(
                "latitude, longitude and height held together, or a cartesian "
                "constraint; a height alone holds no subset of X, Y and Z, so "
                "enter it as an ellipsoidal or orthometric height observation"
            ),
        )
    return held


def _fixed_value(station: Station, component: str, frame: Frame) -> float:
    if frame is Frame.GRAVITY_1D:
        gravity = station.constraint.gravity
        if gravity is None:  # pragma: no cover - ConstraintSpec guarantees this
            raise ValidationError("fixed_station_without_gravity", station=station.id)
        return gravity.value
    position = station.constraint.position
    if position is None:  # pragma: no cover - ConstraintSpec guarantees this
        raise ValidationError("fixed_station_without_position", station=station.id)
    if frame is Frame.GEOCENTRIC_3D:
        return geocentric_component(position, component, station.id, held=True)
    return position.component(_constraint_name(component, frame)).value


def geocentric_component(
    position: Position, component: str, station_id: str, *, held: bool = False
) -> float:
    """One of X, Y, Z from a cartesian or geodetic position.

    A projected position is refused: undoing a projection needs its parameters,
    which a frame does not carry, and the integration layer converts before it
    gets here (``specs/13`` section 5).

    So is a **held** geodetic position whose height is orthometric: converting
    it as though ellipsoidal would hold the station an undulation -- tens of
    metres -- from where it is. An orthometric benchmark enters the combined
    model as an ``ORTHOMETRIC_HEIGHT`` observation instead, where the geoid can
    relate it. A starting position that far off is harmless and is accepted.
    """
    from geocomp.core.models import CoordinateSystem, HeightType

    index = ("x", "y", "z").index(component)
    if position.system is CoordinateSystem.CARTESIAN:
        return position.values[index].value
    orthometric = position.height_type is HeightType.ORTHOMETRIC
    if held and orthometric and position.system is CoordinateSystem.GEODETIC:
        raise ValidationError(
            "geocentric_frame_orthometric_constraint",
            station=station_id,
            expected=(
                "an ellipsoidal height on a held position; hold an orthometric "
                "benchmark as an ORTHOMETRIC_HEIGHT observation, which the geoid "
                "relates to the frame's ellipsoidal heights"
            ),
        )
    if position.system is CoordinateSystem.GEODETIC:
        from geocomp.core.adjustment.geocentric import ELLIPSOID
        from geocomp.core.geodesy.cartesian import geodetic_to_cartesian

        latitude, longitude, height = (quantity.value for quantity in position.values)
        return geodetic_to_cartesian(latitude, longitude, height, ELLIPSOID)[index]
    raise ValidationError(
        "geocentric_frame_projected_position",
        station=station_id,
        received=position.system.value,
        expected=(
            "a cartesian or geodetic position; a projected one needs its projection "
            "undone first, which the combination does before adjusting"
        ),
    )


def _constraint_name(component: str, frame: Frame) -> str:
    """Map a frame component onto the position component name it constrains.

    ``ConstraintSpec`` names components as the position's coordinate system does
    (``easting``, ``northing``, ``up``); the adjustment works with short names.
    Keeping the translation in one place stops the two vocabularies leaking into
    each other.
    """
    if frame is Frame.GRAVITY_1D:
        return GRAVITY_COMPONENT
    return {
        "e": "easting",
        "n": "northing",
        "u": "up",
        "h": "up",
        "x": "x",
        "y": "y",
        "z": "z",
    }[component]


@dataclass(frozen=True)
class WeightedConstraint:
    """A station held with an uncertainty rather than exactly (FR-222).

    Attributes:
        station_id: Whose height or coordinates are constrained.
        components: The frame components constrained, in the order the
            covariance block below is written.
        columns: The parameter columns those components occupy.
        values: The constraining values, in the same order.
        covariance: The constraint's covariance over exactly those components.

    A weighted constraint is an **observation of the station's coordinates**,
    and is treated as one: it contributes a row per component, with weight
    ``Sigma^-1``, so it moves under the adjustment, carries a residual, and
    counts towards the redundancy. That is the whole point of choosing weighted
    over fixed -- a published benchmark height is data, not truth, and holding
    it exactly forces every disagreement into the observations.

    Before this existed, ``ConstraintMode.WEIGHTED`` was declared, validated
    (:class:`~geocomp.core.models.station.ConstraintSpec` refuses one without a
    covariance) and then **silently ignored** by the adjustment: the station was
    estimated as though free, its published height discarded. A network held
    only by weighted constraints was rank-deficient rather than constrained, and
    one held by a fixed benchmark and several weighted ones quietly threw away
    all but the first. It was found in phase P5, checking that a geoid-derived
    height's uncertainty reached the adjusted heights -- it could not, because
    the constraint carrying it was not there.
    """

    station_id: str
    components: tuple[str, ...]
    columns: tuple[int, ...]
    values: tuple[float, ...]
    covariance: np.ndarray

    @property
    def size(self) -> int:
        """The number of parameters the constraint observes."""
        return len(self.columns)


def weighted_constraints(
    network: Network, layout: ParameterLayout, frame: Frame
) -> list[WeightedConstraint]:
    """Every weighted constraint in *network*, as rows the adjustment can use.

    Components that are not estimated -- fixed, or outside the frame -- are
    skipped, and a constraint left with nothing to say is dropped rather than
    contributing an empty row.

    Raises:
        DataError: ``weighted_constraint_singular``, when the covariance over
            the constrained components cannot be inverted. Refusing beats
            substituting a pseudo-inverse, which would apply a weight the user
            never specified to a constraint they thought they had given.
    """
    found: list[WeightedConstraint] = []
    for station in network.stations.values():
        constraint = station.constraint
        if constraint.mode is not ConstraintMode.WEIGHTED:
            continue
        if frame is Frame.GRAVITY_1D:
            gravity = _weighted_gravity(station, layout)
            if gravity is not None:
                found.append(gravity)
            continue
        if constraint.position is None or constraint.covariance is None:
            continue

        if frame is Frame.GEOCENTRIC_3D:
            geocentric = _weighted_geocentric(station, layout)
            if geocentric is not None:
                found.append(geocentric)
            continue

        columns = layout.station_columns(station.id)
        components: list[str] = []
        indices: list[int] = []
        values: list[float] = []
        for component in frame.components:
            name = _constraint_name(component, frame)
            if name not in constraint.components or component not in columns:
                continue
            components.append(name)
            indices.append(columns[component])
            values.append(constraint.position.component(name).value)

        if not components:
            continue

        block = _covariance_block(constraint.covariance, components, station.id)
        found.append(
            WeightedConstraint(
                station_id=station.id,
                components=tuple(components),
                columns=tuple(indices),
                values=tuple(values),
                covariance=block,
            )
        )
    return found


def _weighted_geocentric(station: Station, layout: ParameterLayout) -> WeightedConstraint | None:
    """A station held weighted, as an observation of its X, Y and Z.

    A geodetic constraint's covariance is over latitude, longitude and height;
    it is carried to X, Y, Z through the Jacobian of the conversion, correlations
    and all, rather than read as though its variances were in metres.
    """
    from geocomp.core.models import CoordinateSystem

    held = _geocentric_components(station)
    constraint = station.constraint
    columns = layout.station_columns(station.id)
    if held is None or constraint.covariance is None:
        return None
    position = constraint.position
    if position.system is CoordinateSystem.GEODETIC:
        from geocomp.core.adjustment.geocentric import ELLIPSOID
        from geocomp.core.geodesy.cartesian import geodetic_to_cartesian_jacobian

        axes = ("x", "y", "z")
        if any(axis not in columns for axis in axes):
            return None
        latitude, longitude, height = (q.value for q in position.values)
        jacobian = geodetic_to_cartesian_jacobian(latitude, longitude, height, ELLIPSOID)
        block = _covariance_block(constraint.covariance, list(held), station.id)
        return WeightedConstraint(
            station_id=station.id,
            components=axes,
            columns=tuple(columns[axis] for axis in axes),
            values=tuple(geocentric_component(position, axis, station.id, held=True) for axis in axes),
            covariance=jacobian @ block @ jacobian.T,
        )
    axes = tuple(axis for axis in held if axis in columns)
    if not axes:
        return None
    return WeightedConstraint(
        station_id=station.id,
        components=axes,
        columns=tuple(columns[axis] for axis in axes),
        values=tuple(position.values[("x", "y", "z").index(axis)].value for axis in axes),
        covariance=_covariance_block(constraint.covariance, list(axes), station.id),
    )


def _weighted_gravity(station: Station, layout: ParameterLayout) -> WeightedConstraint | None:
    """A station of known gravity, held with that value's own variance."""
    constraint = station.constraint
    column = layout.column(station.id, "g")
    if GRAVITY_COMPONENT not in constraint.components or constraint.gravity is None or column is None:
        return None
    return WeightedConstraint(
        station_id=station.id,
        components=(GRAVITY_COMPONENT,),
        columns=(column,),
        values=(constraint.gravity.value,),
        covariance=np.array([[constraint.gravity.variance]]),
    )


def _covariance_block(covariance: Covariance, components: list[str], station: str) -> np.ndarray:
    """The constraint's covariance over exactly the constrained components.

    Taken as a **block**, not as a set of variances: a weighted constraint from
    a GNSS solution has correlated components, and reducing it to its diagonal
    would discard the correlation that makes the constraint what it is (FR-104).
    """
    try:
        indices = [covariance.labels.index(name) for name in components]
    except ValueError as error:
        raise DataError(
            "weighted_constraint_components_missing",
            station=station,
            received=list(covariance.labels),
            expected=components,
        ) from error

    block = np.asarray(covariance.matrix, dtype=float)[np.ix_(indices, indices)]
    if not np.all(np.isfinite(block)) or np.linalg.matrix_rank(block) < len(indices):
        raise DataError(
            "weighted_constraint_singular",
            station=station,
            components=components,
            expected=(
                "an invertible covariance over the constrained components. A "
                "singular one is a constraint with an infinitely precise "
                "direction in it, which is a fixed constraint written as a "
                "weighted one"
            ),
        )
    return block
