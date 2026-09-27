# SPDX-License-Identifier: GPL-2.0-or-later
"""Technique networks brought together into one (``specs/13`` sections 2, 5 and 6).

Combining is not concatenating (section 2). This module does the part before
the adjustment: it merges the networks each technique produced, keeps every
correlated cluster whole (FR-104, criterion 5), tags every observation with its
technique, and brings everything that depends on a reference frame into **one
frame at one epoch**, recording each transformation it applied (FR-832,
criterion 4). What it cannot reconcile it refuses, naming the input.

**What depends on the frame, and what does not.** A GNSS vector, a GNSS point,
a GNSS ellipsoidal height and a held coordinate are *positions in a frame*; a
distance, an angle, a levelled height difference and a gravity reading are
measurements of the ground and belong to no frame. Only the first kind is
transformed:

* A **held coordinate** or a **GNSS point** is carried by the full
  transformation (``frames.transform_point``), and to the target epoch along
  its station's velocity -- refused without one.
* A **GNSS vector** is carried by scale and rotation only (the translation
  cancels between its ends), and changes epoch by the difference of its two
  ends' velocities -- refused without both.
* A **GNSS ellipsoidal height** moves by the vertical component of its
  station's displacement.
* **Approximate coordinates** are starting values: they are carried across a
  frame change so they stay close, never along a velocity, and not recorded,
  because nothing in the answer depends on them.

Terrestrial measurements are taken as made at the target epoch: a project's
total-station and levelling work spans weeks, over which a plate interior does
not deform measurably. A survey spanning years in a deforming region is outside
what this assumes, and ``specs/14`` is where its epochs are kept apart.

**Engine routing** (section 6, criterion 6) is decided here too, because it
depends only on what the combination contains: gravity has no DynAdjust
measurement type, so a combination with gravity is adjusted in-house, and the
reason travels with the result rather than being inferred by the reader.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from typing import Any

import numpy as np

from geocomp.core.adjustment.geocentric import ELLIPSOID
from geocomp.core.adjustment.parameters import geocentric_component
from geocomp.core.errors import ValidationError
from geocomp.core.geodesy.cartesian import cartesian_to_geodetic, enu_rotation, geodetic_to_cartesian_jacobian
from geocomp.core.geodesy.frames import (
    TRANSFORMATIONS,
    TransformationRecord,
    TransformationStep,
    canonical_frame,
    transform_point,
    transform_vector,
)
from geocomp.core.models import (
    OBSERVATION_TYPES,
    BaselineFrame,
    Cluster,
    ConstraintMode,
    ConstraintSpec,
    CoordinateSystem,
    Epoch,
    HeightType,
    Network,
    Observation,
    ObservationType,
    Position,
    Station,
    baseline_frame,
)
from geocomp.core.techniques.integration.techniques import TECHNIQUE_KEY, technique_of
from geocomp.core.uncertainty import Covariance, Quantity
from geocomp.core.units import Unit

__all__ = [
    "AppliedTransformation",
    "Combination",
    "Routing",
    "Velocity",
    "combine",
    "route",
]

_GRAVITY = (ObservationType.GRAVITY, ObservationType.GRAVITY_DIFFERENCE)
_GNSS_POSITIONAL = (
    ObservationType.GNSS_BASELINE,
    ObservationType.GNSS_POINT,
    ObservationType.ELLIPSOIDAL_HEIGHT,
)


@dataclass(frozen=True)
class Velocity:
    """A station's velocity, metres per year in X, Y, Z of the frame its
    input network is in, with its covariance if published."""

    value: tuple[float, float, float]
    covariance: np.ndarray | None = None


@dataclass(frozen=True)
class AppliedTransformation:
    """One transformation the combination applied, and to what (FR-832)."""

    input_id: str
    subject: str
    record: TransformationRecord

    def to_dict(self) -> dict[str, Any]:
        return {"input": self.input_id, "subject": self.subject, **self.record.to_dict()}


@dataclass(frozen=True)
class Routing:
    """Which engine adjusts the combination, and why (``specs/13`` section 6)."""

    engine: str
    reason: str
    gravity_observations: tuple[str, ...] = ()


@dataclass(frozen=True)
class Combination:
    """The merged network, in one frame at one epoch, and how it got there.

    Attributes:
        renamed: ``{new id: (input id, original id)}`` for every observation,
            cluster or setup whose id collided with an earlier input's and was
            prefixed with its input's. Station ids are never renamed: the same
            id in two inputs *is* the same mark, which is how the techniques
            tie together at all.
    """

    network: Network
    frame: str
    epoch: Epoch
    inputs: tuple[str, ...]
    techniques: tuple[str, ...]
    transformations: tuple[AppliedTransformation, ...] = ()
    renamed: dict[str, tuple[str, str]] = field(default_factory=dict)

    def provenance_parameters(self) -> dict[str, Any]:
        """What a Solution's provenance should say about the combination."""
        return {
            "combination": {
                "inputs": list(self.inputs),
                "frame": self.frame,
                "epoch": self.epoch.decimal_year,
                "techniques": list(self.techniques),
                "transformations": [t.to_dict() for t in self.transformations],
                "renamed": {new: list(old) for new, old in self.renamed.items()},
            }
        }


def combine(
    inputs: Sequence[Network],
    *,
    frame: str,
    epoch: Epoch,
    velocities: Mapping[str, Velocity] | None = None,
    network_id: str = "combined",
) -> Combination:
    """Merge *inputs* into one network in *frame* at *epoch*.

    Args:
        velocities: Per station, in the frame of the input it comes from. Needed
            wherever a position must change epoch; never assumed zero.

    Raises:
        ValidationError: ``combination_frame_irreconcilable`` for an input whose
            frame GeoComp cannot transform from (naming the input and its frame);
            ``combination_input_without_frame`` for one that holds positions but
            states no frame; ``combination_epoch_without_velocity`` for a position
            that must change epoch with no velocity (naming the input and what);
            ``combination_station_held_differently`` when two inputs hold one
            station at positions more than a millimetre apart.
    """
    target = canonical_frame(frame)
    target_epoch = epoch.decimal_year
    velocities = dict(velocities or {})
    merged = Network(id=network_id, crs=target, epoch=epoch)
    applied: list[AppliedTransformation] = []
    renamed: dict[str, tuple[str, str]] = {}
    held_by: dict[str, str] = {}

    for network in inputs:
        context = _Context(network, target, target_epoch, velocities, applied)
        for station in network.stations.values():
            _merge_station(merged, context.station(station), network.id, held_by)

        cluster_ids = _namespaced(network.clusters, merged.clusters, network.id, renamed)
        observation_ids = _namespaced(network.observations, merged.observations, network.id, renamed)
        setup_ids = _setup_namespace(network, merged, renamed)

        transformed = context.observations()
        for identifier, observation in network.observations.items():
            observation = transformed.get(identifier, observation)
            meta = dict(observation.meta or {})
            meta.setdefault(TECHNIQUE_KEY, technique_of(observation))
            merged.add_observation(
                replace(
                    observation,
                    id=observation_ids[identifier],
                    cluster_id=(
                        cluster_ids.get(observation.cluster_id, observation.cluster_id)
                        if observation.cluster_id
                        else None
                    ),
                    setup_id=setup_ids.get(observation.setup_id, observation.setup_id),
                    meta=meta,
                )
            )
        for identifier, cluster in network.clusters.items():
            cluster = context.clusters.get(identifier, cluster)
            merged.add_cluster(
                replace(
                    cluster,
                    id=cluster_ids[identifier],
                    observation_ids=tuple(observation_ids[o] for o in cluster.observation_ids),
                )
            )

    techniques = tuple(dict.fromkeys(technique_of(o) for o in merged.observations.values()))
    return Combination(
        network=merged,
        frame=target,
        epoch=epoch,
        inputs=tuple(n.id for n in inputs),
        techniques=techniques,
        transformations=tuple(applied),
        renamed=renamed,
    )


def route(network: Network, requested: str = "in_house") -> Routing:
    """Which engine may adjust *network*, given the one asked for.

    Gravity has no DynAdjust measurement type (``specs/12`` section 1), so a
    combination containing any goes to the in-house core whatever was asked --
    and says so, rather than dropping the gravity observations to satisfy the
    request (criterion 6).
    """
    gravity = tuple(o.id for o in network.observations.values() if o.type in _GRAVITY)
    if requested not in ("in_house", "dynadjust"):
        raise ValidationError("engine_unknown", received=requested, expected=["in_house", "dynadjust"])
    if gravity and requested == "dynadjust":
        return Routing(
            engine="in_house",
            reason=(
                f"{len(gravity)} gravity observation(s) take part, and DynAdjust has no "
                "measurement type for gravity; the in-house core adjusts them instead of "
                "their being dropped"
            ),
            gravity_observations=gravity,
        )
    if requested == "dynadjust":
        missing = sorted(
            {
                o.type.value
                for o in network.observations.values()
                if not OBSERVATION_TYPES[o.type].dynadjust_code
            }
        )
        if missing:
            return Routing(
                engine="in_house",
                reason=(
                    f"DynAdjust has no measurement type for {', '.join(missing)} "
                    "(specs/07 section 4.2); the in-house core adjusts the whole "
                    "combination rather than a part of it"
                ),
            )
        return Routing(engine="dynadjust", reason="requested, and every observation has a DynAdjust type")
    return Routing(
        engine="in_house",
        reason="requested" + (" (gravity observations included)" if gravity else ""),
        gravity_observations=gravity,
    )


# -- internals ---------------------------------------------------------------


class _Context:
    """One input's frame and epoch, and the transformations it needs."""

    def __init__(self, network, target, target_epoch, velocities, applied):
        self.network = network
        self.target = target
        self.target_epoch = target_epoch
        self.velocities = velocities
        self.applied = applied
        self.clusters: dict[str, Cluster] = {}
        self.epoch = network.epoch.decimal_year if network.epoch is not None else None
        self.source = self._source_frame()

    def _source_frame(self) -> str | None:
        if not self.network.crs:
            return None
        try:
            return canonical_frame(self.network.crs)
        except ValidationError as error:
            raise ValidationError(
                "combination_frame_irreconcilable",
                input=self.network.id,
                received=self.network.crs,
                expected=error.context.get("expected"),
                hint=(
                    "every input must be in a frame GeoComp can transform from; "
                    "combining without the transformation would absorb a datum "
                    "shift into the residuals"
                ),
            ) from error

    def _require_frame(self, subject: str) -> str:
        if self.source is None:
            raise ValidationError(
                "combination_input_without_frame",
                input=self.network.id,
                subject=subject,
                expected=(
                    "the input network's frame (its crs): it holds a position, and a "
                    "position without its frame cannot be brought into another"
                ),
            )
        return self.source

    def _epoch_of(self, observation: Observation | None = None, *, subject: str = "") -> float:
        """The epoch of *observation*, or of the input; refused if neither says.

        FR-105: no epoch is assumed. Only a starting value (*subject* empty)
        falls back to the target's, because nothing in the answer depends on
        where it started.
        """
        if observation is not None and observation.epoch is not None:
            return observation.epoch.decimal_year
        if self.epoch is not None:
            return self.epoch
        if not subject:
            return self.target_epoch
        raise ValidationError(
            "combination_input_without_epoch",
            input=self.network.id,
            subject=subject,
            expected=(
                "the epoch of the input (or of the observation or position): it "
                "is a position in a frame that moves, and taking it to be at the "
                "combination's epoch would assume it (FR-105)"
            ),
        )

    def _velocity(self, station_id: str, subject: str, epoch: float) -> Velocity | None:
        if abs(epoch - self.target_epoch) <= 1e-9:
            return None
        velocity = self.velocities.get(station_id)
        if velocity is None:
            raise ValidationError(
                "combination_epoch_without_velocity",
                input=self.network.id,
                subject=subject,
                received=[epoch, self.target_epoch],
                expected=(
                    f"a velocity for {station_id}: {subject} is at {epoch:.4f} and the "
                    f"combination at {self.target_epoch:.4f}, and moving it assumes "
                    "a velocity -- zero is a decimetre a decade in most of Brazil"
                ),
            )
        return velocity

    def _point(self, xyz, *, station_id, subject, epoch, covariance=None, record=True):
        source = self._require_frame(subject)
        velocity = self._velocity(station_id, subject, epoch)
        moved = transform_point(
            xyz,
            source=source,
            target=self.target,
            epoch=epoch,
            target_epoch=self.target_epoch,
            covariance=covariance,
            velocity=None if velocity is None else velocity.value,
            velocity_covariance=None if velocity is None else velocity.covariance,
        )
        if record and not moved.record.is_identity:
            self.applied.append(AppliedTransformation(self.network.id, subject, moved.record))
        return moved

    # -- stations ------------------------------------------------------------

    def station(self, station: Station) -> Station:
        approximate = station.approx_position
        if approximate is not None and self.source is not None and self.source != self.target:
            approximate = self._approximate(station.id, approximate)
        constraint = station.constraint
        if constraint.mode is not ConstraintMode.FREE and constraint.position is not None:
            constraint = self._constraint(station.id, constraint)
        return replace(station, approx_position=approximate, constraint=constraint)

    def _approximate(self, station_id: str, position: Position) -> Position:
        if position.system not in (CoordinateSystem.CARTESIAN, CoordinateSystem.GEODETIC):
            return position
        xyz = [geocentric_component(position, c, station_id) for c in ("x", "y", "z")]
        moved = transform_point(xyz, source=self.source, target=self.target, epoch=self._epoch_of())
        return _cartesian(moved.xyz, self.target, self._epoch(), position)

    def _constraint(self, station_id: str, constraint: ConstraintSpec) -> ConstraintSpec:
        position = constraint.position
        if position.system not in (CoordinateSystem.CARTESIAN, CoordinateSystem.GEODETIC):
            return constraint
        subject = f"station {station_id} ({constraint.mode.value} position)"
        xyz = [geocentric_component(position, c, station_id, held=True) for c in ("x", "y", "z")]
        covariance = _ecef_covariance(position, constraint)
        epoch = position.epoch.decimal_year if position.epoch is not None else self._epoch_of(subject=subject)
        moved = self._point(xyz, station_id=station_id, subject=subject, epoch=epoch, covariance=covariance)
        return replace(
            constraint,
            components=frozenset({"x", "y", "z"}),
            position=_cartesian(moved.xyz, self.target, self._epoch(), position),
            covariance=(
                None
                if moved.covariance is None
                else Covariance(
                    matrix=moved.covariance,
                    labels=("x", "y", "z"),
                    units=(Unit.METRE,) * 3,
                    mode=constraint.covariance.mode,
                    strategies=constraint.covariance.strategies,
                )
            ),
        )

    def _epoch(self) -> Epoch:
        return Epoch.from_decimal_year(self.target_epoch)

    # -- observations --------------------------------------------------------

    def observations(self) -> dict[str, Observation]:
        """The frame-dependent observations, transformed; clusters rebuilt."""
        out: dict[str, Observation] = {}
        jacobians: dict[str, np.ndarray] = {}
        added: dict[str, np.ndarray] = {}
        for identifier, observation in self.network.observations.items():
            if observation.type not in _GNSS_POSITIONAL:
                continue
            result = self._observation(observation)
            if result is None:
                continue
            out[identifier], jacobians[identifier], added[identifier] = result
        for cluster_id, cluster in self.network.clusters.items():
            members = [m for m in cluster.observation_ids if m in jacobians]
            if not members:
                continue
            self.clusters[cluster_id] = _rebuilt(cluster, self.network, jacobians, added)
            for position, member in enumerate(cluster.observation_ids):
                observation = out.get(member, self.network.observations[member])
                out[member] = _with_cluster_variances(observation, self.clusters[cluster_id], position)
        return out

    def _observation(self, observation: Observation):
        # A GNSS vector, point or height is a position in a frame at an epoch:
        # both are required, never taken to be the combination's own.
        subject = f"observation {observation.id}"
        source = self._require_frame(subject)
        epoch = self._epoch_of(observation, subject=subject)
        if source == self.target and abs(epoch - self.target_epoch) <= 1e-9:
            return None
        values = np.array([q.value for q in observation.values])
        if observation.type is ObservationType.GNSS_POINT:
            (station_id,) = observation.stations
            moved = self._point(values, station_id=station_id, subject=subject, epoch=epoch)
            added = np.zeros((3, 3))
            velocity = self.velocities.get(station_id)
            moved_years = moved.record.target_epoch - moved.record.source_epoch
            if velocity is not None and velocity.covariance is not None and moved_years:
                added = np.asarray(velocity.covariance) * moved_years**2
            return _with_values(observation, moved.xyz), _jacobian(moved.record), added
        if observation.type is ObservationType.ELLIPSOIDAL_HEIGHT:
            (station_id,) = observation.stations
            xyz = self._station_xyz(station_id)
            moved = self._point(xyz, station_id=station_id, subject=subject, epoch=epoch)
            latitude, longitude, _ = cartesian_to_geodetic(*xyz, ELLIPSOID)
            up = enu_rotation(latitude, longitude)[2]
            shift = float(up @ (moved.xyz - np.asarray(xyz)))
            return _with_values(observation, values + shift), np.eye(1), np.zeros((1, 1))
        return self._baseline(observation, values, epoch, subject)

    def _baseline(self, observation, values, epoch, subject):
        base, rover = observation.stations
        local = baseline_frame(observation) is BaselineFrame.LOCAL
        source = self._require_frame(subject)
        jacobian = np.eye(3)
        steps = []
        vector = values
        if not local:
            vector, _, record = transform_vector(values, source=source, target=self.target, epoch=epoch)
            jacobian = _jacobian(record)
            steps.extend(record.steps)
        added = np.zeros((3, 3))
        if abs(epoch - self.target_epoch) > 1e-9:
            first = self._velocity(base, subject, epoch)
            second = self._velocity(rover, subject, epoch)
            interval = self.target_epoch - epoch
            relative = (np.array(second.value) - np.array(first.value)) * interval
            if local:
                latitude, longitude, _ = cartesian_to_geodetic(*self._station_xyz(base), ELLIPSOID)
                relative = enu_rotation(latitude, longitude) @ relative
            vector = vector + relative
            for velocity in (first, second):
                if velocity.covariance is not None:
                    added = added + np.asarray(velocity.covariance) * interval**2
            steps.append(
                TransformationStep(
                    kind="epoch",
                    description=f"moved by the difference of {base}'s and {rover}'s velocities",
                    from_epoch=epoch,
                    to_epoch=self.target_epoch,
                )
            )
        if steps:
            self.applied.append(
                AppliedTransformation(
                    self.network.id,
                    subject,
                    TransformationRecord(
                        source=source,
                        target=self.target,
                        source_epoch=epoch,
                        target_epoch=self.target_epoch,
                        steps=tuple(steps),
                    ),
                )
            )
        return _with_values(observation, vector), jacobian, added

    def _station_xyz(self, station_id: str) -> list[float]:
        station = self.network.stations.get(station_id)
        position = None if station is None else (station.approx_position or station.constraint.position)
        if position is None:
            raise ValidationError(
                "combination_station_without_position",
                input=self.network.id,
                station=station_id,
                expected="an approximate position, to know which way is up there",
            )
        return [geocentric_component(position, c, station_id) for c in ("x", "y", "z")]


def _jacobian(record: TransformationRecord) -> np.ndarray:
    """The linear map a record's Helmert steps applied, in order -- what a
    cluster's covariance is carried through. Epoch steps add, they do not map."""
    by_code = {helmert.code: helmert for helmert in TRANSFORMATIONS}
    jacobian = np.eye(3)
    for step in record.steps:
        if step.kind != "helmert":
            continue
        _t, m = by_code[step.code].at(step.epoch)
        jacobian = (np.linalg.inv(m) if step.inverse else m) @ jacobian
    return jacobian


def _rebuilt(cluster: Cluster, network: Network, jacobians, added) -> Cluster:
    """The cluster's covariance carried through each member's own Jacobian."""
    blocks, extra = [], []
    for member in cluster.observation_ids:
        size = len(network.observations[member].values)
        blocks.append(jacobians.get(member, np.eye(size)))
        extra.append(added.get(member, np.zeros((size, size))))
    jacobian = _block_diagonal(blocks)
    matrix = jacobian @ np.asarray(cluster.covariance.matrix) @ jacobian.T + _block_diagonal(extra)
    return replace(
        cluster,
        covariance=Covariance(
            matrix=matrix,
            labels=cluster.covariance.labels,
            units=cluster.covariance.units,
            mode=cluster.covariance.mode,
            strategies=cluster.covariance.strategies,
        ),
    )


def _block_diagonal(blocks: list[np.ndarray]) -> np.ndarray:
    size = sum(b.shape[0] for b in blocks)
    out = np.zeros((size, size))
    start = 0
    for block in blocks:
        n = block.shape[0]
        out[start : start + n, start : start + n] = block
        start += n
    return out


def _with_values(observation: Observation, values) -> Observation:
    return replace(
        observation,
        values=tuple(
            Quantity(
                value=float(v),
                variance=q.variance,
                unit=q.unit,
                mode=q.mode,
                strategies=q.strategies,
            )
            for v, q in zip(values, observation.values, strict=True)
        ),
    )


def _with_cluster_variances(observation: Observation, cluster: Cluster, position: int) -> Observation:
    """Keep an observation's own variances in step with its cluster's matrix.

    A cluster's members are one type and so one size, which is what locates
    this member's block.
    """
    size = len(observation.values)
    diagonal = np.diag(np.asarray(cluster.covariance.matrix))
    return replace(
        observation,
        values=tuple(
            replace(q, variance=float(diagonal[position * size + k]))
            for k, q in enumerate(observation.values)
        ),
    )


def _ecef_covariance(position: Position, constraint: ConstraintSpec) -> np.ndarray | None:
    """A weighted constraint's covariance over X, Y, Z, whatever it was stated in."""
    covariance = constraint.covariance
    if covariance is None:
        return None
    if position.system is CoordinateSystem.CARTESIAN:
        indices = [covariance.labels.index(name) for name in ("x", "y", "z")]
        return np.asarray(covariance.matrix)[np.ix_(indices, indices)]
    indices = [covariance.labels.index(name) for name in ("latitude", "longitude", "height")]
    latitude, longitude, height = (q.value for q in position.values)
    jacobian = geodetic_to_cartesian_jacobian(latitude, longitude, height, ELLIPSOID)
    return jacobian @ np.asarray(covariance.matrix)[np.ix_(indices, indices)] @ jacobian.T


def _cartesian(xyz, frame: str, epoch: Epoch, original: Position) -> Position:
    exact = all(q.variance == 0.0 for q in original.values)
    return Position(
        values=tuple(
            Quantity.exact(float(v), Unit.METRE)
            if exact
            else Quantity.from_std_dev(float(v), 1.0, Unit.METRE)
            for v in xyz
        ),
        system=CoordinateSystem.CARTESIAN,
        crs=frame,
        epoch=epoch,
        height_type=HeightType.ELLIPSOIDAL,
    )


def _merge_station(merged: Network, station: Station, input_id: str, held_by: dict[str, str]) -> None:
    existing = merged.stations.get(station.id)
    held = station.constraint.mode is not ConstraintMode.FREE
    if existing is None:
        merged.add_station(station)
        if held:
            held_by[station.id] = input_id
        return
    existing_held = existing.constraint.mode is not ConstraintMode.FREE
    if held and existing_held:
        first, second = existing.constraint.position, station.constraint.position
        comparable = first.system is second.system is CoordinateSystem.CARTESIAN
        separation = (
            float(
                np.linalg.norm([a.value - b.value for a, b in zip(first.values, second.values, strict=True)])
            )
            if comparable
            else float("inf")
        )
        if separation > 1e-3:
            raise ValidationError(
                "combination_station_held_differently",
                station=station.id,
                received=[held_by[station.id], input_id],
                separation=round(separation, 4) if comparable else None,
                expected=(
                    "one held position per station, or held positions that agree once "
                    "in one frame and epoch; two holds a distance apart force that "
                    "distance into the residuals"
                ),
            )
        return
    if held and not existing_held:
        approximate = existing.approx_position or station.approx_position
        merged.stations[station.id] = replace(station, approx_position=approximate)
        held_by[station.id] = input_id
    elif existing.approx_position is None and station.approx_position is not None:
        merged.stations[station.id] = replace(existing, approx_position=station.approx_position)


def _namespaced(items: Mapping[str, Any], taken: Mapping[str, Any], input_id: str, renamed):
    """Each id as it will be in the merged network: itself, unless taken."""
    mapping: dict[str, str] = {}
    for identifier in items:
        new = identifier if identifier not in taken else f"{input_id}:{identifier}"
        if new != identifier:
            renamed[new] = (input_id, identifier)
        mapping[identifier] = new
    return mapping


def _setup_namespace(network: Network, merged: Network, renamed) -> dict[str, str]:
    """Setup ids that collide with an earlier input's, which would otherwise
    share one orientation unknown between two instrument setups."""
    taken = {o.setup_id for o in merged.observations.values() if o.setup_id}
    mapping: dict[str, str] = {}
    for observation in network.observations.values():
        setup = observation.setup_id
        if setup and setup in taken and setup not in mapping:
            mapping[setup] = f"{network.id}:{setup}"
            renamed[mapping[setup]] = (network.id, setup)
    return mapping
