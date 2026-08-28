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
from geocomp.core.models import ConstraintMode, Network, Station
from geocomp.core.uncertainty import Covariance
from geocomp.core.units import Unit

__all__ = [
    "Frame",
    "ParameterLayout",
    "ParameterSlot",
    "WeightedConstraint",
    "weighted_constraints",
]


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

    @property
    def components(self) -> tuple[str, ...]:
        return {
            Frame.HEIGHT_1D: ("h",),
            Frame.PLANE_2D: ("e", "n"),
            Frame.SPACE_3D: ("e", "n", "u"),
            Frame.GRAVITY_1D: ("g",),
        }[self]

    @property
    def dimension(self) -> int:
        """Which of 1D, 2D and 3D this frame is, for the observation registry."""
        return {
            Frame.HEIGHT_1D: 1,
            Frame.PLANE_2D: 2,
            Frame.SPACE_3D: 3,
            Frame.GRAVITY_1D: 1,
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

        Gravity maps to ``up`` for want of anywhere better. That is a recorded
        wart, not a claim: a gravity value in a metre-typed slot is
        dimensionally wrong and phase P8 fixes it (``specs/12`` and
        ``tests/test_gravimetry_is_levelling.py``).
        """
        return {
            Frame.HEIGHT_1D: ("up",),
            Frame.PLANE_2D: ("easting", "northing"),
            Frame.SPACE_3D: ("easting", "northing", "up"),
            Frame.GRAVITY_1D: ("up",),
        }[self]

    @property
    def position_indices(self) -> tuple[int, ...]:
        """The same correspondence as indices into the position's triple."""
        names = ("easting", "northing", "up")
        return tuple(names.index(name) for name in self.position_components)

    @property
    def component_units(self) -> tuple[Unit, ...]:
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
        layout = cls(frame=frame)

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
        return len(self.slots)

    def column(self, owner: str, component: str) -> int | None:
        """Column index of an unknown, or ``None`` when it is held fixed."""
        return self._columns.get((owner, component))

    def is_fixed(self, owner: str, component: str) -> bool:
        return (owner, component) in self.fixed_values

    def labels(self) -> list[str]:
        return [slot.label for slot in self.slots]

    def station_columns(self, station_id: str) -> dict[str, int]:
        """The estimated components of one station, by component name."""
        return {
            component: column
            for component in self.frame.components
            if (column := self.column(station_id, component)) is not None
        }

    def station_ids(self) -> list[str]:
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
            else:
                # Orientation unknowns are angles; drift is an acceleration rate,
                # carried as dimensionless here and reported with its own unit.
                units.append(Unit.RADIAN if slot.component == "orientation" else Unit.DIMENSIONLESS)
        return units


def _is_fixed(station: Station, component: str, frame: Frame) -> bool:
    constraint = station.constraint
    if constraint.mode is not ConstraintMode.FIXED:
        return False
    return _constraint_name(component, frame) in constraint.components


def _fixed_value(station: Station, component: str, frame: Frame) -> float:
    position = station.constraint.position
    if position is None:  # pragma: no cover - ConstraintSpec guarantees this
        raise ValidationError("fixed_station_without_position", station=station.id)
    return position.component(_constraint_name(component, frame)).value


def _constraint_name(component: str, frame: Frame) -> str:
    """Map a frame component onto the position component name it constrains.

    ``ConstraintSpec`` names components as the position's coordinate system does
    (``easting``, ``northing``, ``up``); the adjustment works with short names.
    Keeping the translation in one place stops the two vocabularies leaking into
    each other.
    """
    if frame is Frame.GRAVITY_1D:
        return "up"
    return {"e": "easting", "n": "northing", "u": "up", "h": "up"}[component]


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
        if constraint.position is None or constraint.covariance is None:
            continue  # pragma: no cover - ConstraintSpec guarantees both

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
