# SPDX-License-Identifier: GPL-2.0-or-later
"""Observations, observation types and correlated clusters (FR-102 to FR-104).

``specs/04-data-model.md`` sections 2.5, 2.6 and 4.

The observation type **registry** is the extension point that keeps the
adjustment closed to modification: adding a type means adding a registry entry
declaring its arity, units, covariance shape and DynAdjust mapping -- not editing
the code that builds the design matrix
(``specs/03-architecture.md`` section 4).

The other load-bearing idea here is the :class:`Cluster`. A GNSS baseline is
three correlated components sharing one 3x3 covariance; a set of directions from
one setup shares an orientation unknown. Decomposing either into independent
scalars discards the correlation and falsifies every statistic downstream, so
the model does not allow it silently.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from geocomp.core.errors import DataError, ValidationError
from geocomp.core.models.epoch import Epoch
from geocomp.core.uncertainty import Covariance, Quantity
from geocomp.core.units import Unit

__all__ = [
    "OBSERVATION_TYPES",
    "Cluster",
    "ClusterKind",
    "Observation",
    "ObservationStatus",
    "ObservationType",
    "ObservationTypeSpec",
    "RejectionRecord",
    "observation_type_spec",
]


class ObservationType(Enum):
    """Every observation GeoComp can hold (FR-103, O4)."""

    DIRECTION = "direction"
    HORIZONTAL_ANGLE = "horizontal_angle"
    AZIMUTH = "azimuth"
    ASTRONOMIC_AZIMUTH = "astronomic_azimuth"
    ZENITH_ANGLE = "zenith_angle"
    VERTICAL_ANGLE = "vertical_angle"
    SLOPE_DISTANCE = "slope_distance"
    HORIZONTAL_DISTANCE = "horizontal_distance"
    ELLIPSOID_DISTANCE = "ellipsoid_distance"
    HEIGHT_DIFFERENCE = "height_difference"
    ORTHOMETRIC_HEIGHT = "orthometric_height"
    ELLIPSOIDAL_HEIGHT = "ellipsoidal_height"
    GEODETIC_LATITUDE = "geodetic_latitude"
    GEODETIC_LONGITUDE = "geodetic_longitude"
    ASTRONOMIC_LATITUDE = "astronomic_latitude"
    ASTRONOMIC_LONGITUDE = "astronomic_longitude"
    GNSS_BASELINE = "gnss_baseline"
    GNSS_POINT = "gnss_point"
    GRAVITY = "gravity"
    GRAVITY_DIFFERENCE = "gravity_difference"


@dataclass(frozen=True)
class ObservationTypeSpec:
    """What the rest of the system needs to know about one observation type.

    Attributes:
        arity: How many stations the observation relates.
        components: Names of the value components, in order.
        units: The unit of each component.
        always_clustered: Whether the type must be held in a
            :class:`Cluster` -- true where the components are inherently
            correlated and treating them as independent would be wrong.
        dimensionality: Which of 1D, 2D and 3D adjustment the type can
            contribute to (FR-227). A mismatch is rejected at validation rather
            than silently ignored.
        dynadjust_code: The DynAdjust measurement type letter, or ``None`` where
            DynAdjust has no equivalent. Gravity has none, which is why
            gravimetric networks run entirely on the in-house core
            (``specs/12-module-gravimetry.md`` section 1).
        dynadjust_verified: Whether the mapping has been confirmed against the
            DynAdjust User's Guide. ``specs/07-engine-dynadjust.md`` section 4.2
            marks unconfirmed entries **[C]**; this carries that marking into
            code so the P6 implementation cannot forget to check them.
    """

    type: ObservationType
    arity: int
    components: tuple[str, ...]
    units: tuple[Unit, ...]
    always_clustered: bool = False
    dimensionality: frozenset[int] = field(default_factory=lambda: frozenset({1, 2, 3}))
    dynadjust_code: str | None = None
    dynadjust_verified: bool = False

    def __post_init__(self) -> None:
        if len(self.components) != len(self.units):
            raise ValueError(f"{self.type.value}: component and unit counts differ")


def _spec(
    observation_type: ObservationType,
    arity: int,
    components: tuple[str, ...],
    units: tuple[Unit, ...],
    *,
    clustered: bool = False,
    dims: set[int] | None = None,
    dna: str | None = None,
    dna_verified: bool = False,
) -> ObservationTypeSpec:
    return ObservationTypeSpec(
        type=observation_type,
        arity=arity,
        components=components,
        units=units,
        always_clustered=clustered,
        dimensionality=frozenset(dims if dims is not None else {1, 2, 3}),
        dynadjust_code=dna,
        dynadjust_verified=dna_verified,
    )


ANGLE, LENGTH, ACCEL = Unit.RADIAN, Unit.METRE, Unit.ACCELERATION

#: The registry.
#:
#: **Every DynAdjust code is now verified** (phase P6), against upstream at
#: commit ``5cdb897``: the measurement tally in ``dnameasurement.hpp``, the
#: import parser's switch in ``dnainterop.cpp``, and Table 3.2 of the User's
#: Guide, which agree. P1 could confirm eight of them from the README and left
#: the rest marked unverified precisely so this could not be forgotten.
#:
#: Two pairs the spec's table had collapsed into one row each, and both would
#: have been silent errors: ``AZIMUTH`` is **B** while ``ASTRONOMIC_AZIMUTH`` is
#: **K** -- a geodetic azimuth written as K is adjusted against a deflection of
#: the vertical it never had; and ``ZENITH_ANGLE`` is **V** while
#: ``VERTICAL_ANGLE`` is **Z**, which differ by 90 degrees.
#:
#: ``HORIZONTAL_DISTANCE`` keeps no code deliberately. DynAdjust's ``M`` is a
#: *mean sea level* arc, reduced to a surface GeoComp does not model, and
#: equating the two is a metre-scale error over a long line
#: (``specs/07`` section 4.2). Gravity has none because DynAdjust has no
#: gravimetric measurement type at all, which is what forces ADR-0002.
OBSERVATION_TYPES: dict[ObservationType, ObservationTypeSpec] = {
    spec.type: spec
    for spec in (
        _spec(
            ObservationType.DIRECTION, 2, ("angle",), (ANGLE,),
            clustered=True, dims={2, 3}, dna="D", dna_verified=True,
        ),
        _spec(
            ObservationType.HORIZONTAL_ANGLE, 3, ("angle",), (ANGLE,),
            dims={2, 3}, dna="A", dna_verified=True,
        ),
        _spec(
            ObservationType.AZIMUTH, 2, ("angle",), (ANGLE,),
            dims={2, 3}, dna="B", dna_verified=True,
        ),
        _spec(
            ObservationType.ASTRONOMIC_AZIMUTH, 2, ("angle",), (ANGLE,),
            dims={2, 3}, dna="K", dna_verified=True,
        ),
        _spec(
            ObservationType.ZENITH_ANGLE, 2, ("angle",), (ANGLE,),
            dims={3}, dna="V", dna_verified=True,
        ),
        _spec(
            ObservationType.VERTICAL_ANGLE, 2, ("angle",), (ANGLE,),
            dims={3}, dna="Z", dna_verified=True,
        ),
        _spec(
            ObservationType.SLOPE_DISTANCE, 2, ("distance",), (LENGTH,),
            dims={3}, dna="S", dna_verified=True,
        ),
        # No DynAdjust equivalent, and the absence is verified rather than
        # unexamined: M is a *mean sea level* arc, not a horizontal distance.
        _spec(
            ObservationType.HORIZONTAL_DISTANCE, 2, ("distance",), (LENGTH,),
            dims={2, 3}, dna_verified=True,
        ),
        # Ellipsoid chord (C) and arc (E) are both confirmed upstream; GeoComp
        # models one type and selects the code from the reduction applied.
        _spec(
            ObservationType.ELLIPSOID_DISTANCE, 2, ("distance",), (LENGTH,),
            dims={2, 3}, dna="C", dna_verified=True,
        ),
        _spec(
            ObservationType.HEIGHT_DIFFERENCE, 2, ("height_difference",), (LENGTH,),
            dims={1, 3}, dna="L", dna_verified=True,
        ),
        _spec(
            ObservationType.ORTHOMETRIC_HEIGHT, 1, ("height",), (LENGTH,),
            dims={1, 3}, dna="H", dna_verified=True,
        ),
        _spec(
            ObservationType.ELLIPSOIDAL_HEIGHT, 1, ("height",), (LENGTH,),
            dims={1, 3}, dna="R", dna_verified=True,
        ),
        _spec(
            ObservationType.GEODETIC_LATITUDE, 1, ("latitude",), (ANGLE,),
            dims={2, 3}, dna="P", dna_verified=True,
        ),
        _spec(
            ObservationType.GEODETIC_LONGITUDE, 1, ("longitude",), (ANGLE,),
            dims={2, 3}, dna="Q", dna_verified=True,
        ),
        _spec(
            ObservationType.ASTRONOMIC_LATITUDE, 1, ("latitude",), (ANGLE,),
            dims={2, 3}, dna="I", dna_verified=True,
        ),
        _spec(
            ObservationType.ASTRONOMIC_LONGITUDE, 1, ("longitude",), (ANGLE,),
            dims={2, 3}, dna="J", dna_verified=True,
        ),
        _spec(
            ObservationType.GNSS_BASELINE, 2, ("dx", "dy", "dz"), (LENGTH,) * 3,
            clustered=True, dims={3}, dna="G", dna_verified=True,
        ),
        _spec(
            ObservationType.GNSS_POINT, 1, ("x", "y", "z"), (LENGTH,) * 3,
            clustered=True, dims={3}, dna="Y", dna_verified=True,
        ),
        # No DynAdjust *measurement type*, which is not the same as no
        # equivalent: a gravity difference is a 1D difference observation, the
        # same equation as a height difference (see
        # ``tests/test_gravimetry_is_levelling.py``), so a drift-corrected
        # gravimetric network can be relabelled as a level network and adjusted
        # by DynAdjust. Left unmapped deliberately: the relabelling loses the
        # units and cannot carry a jointly estimated drift, so it belongs in the
        # P6 cross-validation path rather than in the routine export. ADR-0002,
        # Amendment 1.
        _spec(
            ObservationType.GRAVITY, 1, ("gravity",), (ACCEL,),
            dims={1}, dna_verified=True,
        ),
        _spec(
            ObservationType.GRAVITY_DIFFERENCE, 2, ("gravity_difference",), (ACCEL,),
            dims={1}, dna_verified=True,
        ),
    )
}


def observation_type_spec(observation_type: ObservationType) -> ObservationTypeSpec:
    return OBSERVATION_TYPES[observation_type]


class ObservationStatus(Enum):
    """Whether an observation participates in an adjustment.

    ``REJECTED`` means a statistical test rejected it; ``EXCLUDED`` means a human
    removed it. Both are reversible and neither deletes the record (FR-255,
    FR-135) -- in a monitoring network, the displacement being measured is
    exactly what an automatic outlier remover will delete.
    """

    ACTIVE = "active"
    REJECTED = "rejected"
    EXCLUDED = "excluded"


@dataclass(frozen=True)
class RejectionRecord:
    """Why an observation was set aside, by what, and when (FR-255)."""

    reason: str
    test: str = ""
    statistic: float | None = None
    critical_value: float | None = None
    at: datetime | None = None
    by: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"reason": self.reason}
        if self.test:
            payload["test"] = self.test
        if self.statistic is not None:
            payload["statistic"] = self.statistic
        if self.critical_value is not None:
            payload["critical_value"] = self.critical_value
        if self.at is not None:
            payload["at"] = self.at.astimezone(UTC).isoformat()
        if self.by:
            payload["by"] = self.by
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> RejectionRecord:
        at = payload.get("at")
        return cls(
            reason=payload["reason"],
            test=payload.get("test", ""),
            statistic=payload.get("statistic"),
            critical_value=payload.get("critical_value"),
            at=datetime.fromisoformat(at) if at else None,
            by=payload.get("by", ""),
        )


@dataclass(frozen=True)
class Observation:
    """One measurement relating one or more stations (FR-102).

    Attributes:
        stations: Ordered; the meaning of the order is the type's business --
            for a horizontal angle it is (at, from, to).
        values: One :class:`Quantity` per component of the type. Every value
            carries its uncertainty (FR-200).
        cluster_id: Membership of a correlated group (FR-104). Required for
            types whose specification sets ``always_clustered``.
    """

    id: str
    type: ObservationType
    stations: tuple[str, ...]
    values: tuple[Quantity, ...]
    epoch: Epoch | None = None
    setup_id: str | None = None
    instrument_id: str | None = None
    cluster_id: str | None = None
    status: ObservationStatus = ObservationStatus.ACTIVE
    rejection: RejectionRecord | None = None
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        spec = OBSERVATION_TYPES[self.type]

        if len(self.stations) != spec.arity:
            raise DataError(
                "observation_arity",
                observation=self.id,
                type=self.type.value,
                received=len(self.stations),
                expected=spec.arity,
            )
        if len(self.values) != len(spec.components):
            raise DataError(
                "observation_component_count",
                observation=self.id,
                type=self.type.value,
                received=len(self.values),
                expected=len(spec.components),
            )
        for quantity, unit, name in zip(self.values, spec.units, spec.components, strict=True):
            if not isinstance(quantity, Quantity):
                raise DataError(
                    "observation_value_not_a_quantity",
                    observation=self.id,
                    component=name,
                    expected="a Quantity; every observation carries its uncertainty (FR-200)",
                )
            if quantity.unit is not unit:
                raise DataError(
                    "observation_value_unit",
                    observation=self.id,
                    component=name,
                    received=quantity.unit.name,
                    expected=unit.name,
                )
        if spec.always_clustered and self.cluster_id is None:
            raise DataError(
                "observation_requires_cluster",
                observation=self.id,
                type=self.type.value,
                expected=(
                    "a cluster id; the components of this type are correlated and "
                    "treating them as independent falsifies the adjustment (FR-104)"
                ),
            )
        if self.status is ObservationStatus.ACTIVE and self.rejection is not None:
            raise DataError(
                "active_observation_with_rejection", observation=self.id
            )

    @property
    def spec(self) -> ObservationTypeSpec:
        return OBSERVATION_TYPES[self.type]

    @property
    def is_active(self) -> bool:
        return self.status is ObservationStatus.ACTIVE

    @property
    def value(self) -> Quantity:
        """The single value, for scalar observation types."""
        if len(self.values) != 1:
            raise ValidationError(
                "observation_is_not_scalar",
                observation=self.id,
                components=len(self.values),
                expected="a single-component observation; use .values",
            )
        return self.values[0]

    def supports_dimension(self, dimension: int) -> bool:
        return dimension in self.spec.dimensionality

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": self.id,
            "type": self.type.name,
            "stations": list(self.stations),
            "values": [q.to_dict() for q in self.values],
            "status": self.status.name,
        }
        for key, value in (
            ("epoch", self.epoch.to_dict() if self.epoch else None),
            ("setup_id", self.setup_id),
            ("instrument_id", self.instrument_id),
            ("cluster_id", self.cluster_id),
            ("rejection", self.rejection.to_dict() if self.rejection else None),
            ("meta", dict(self.meta) if self.meta else None),
        ):
            if value is not None:
                payload[key] = value
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> Observation:
        epoch = payload.get("epoch")
        rejection = payload.get("rejection")
        return cls(
            id=payload["id"],
            type=ObservationType[payload["type"]],
            stations=tuple(payload["stations"]),
            values=tuple(Quantity.from_dict(v) for v in payload["values"]),
            epoch=Epoch.from_dict(epoch) if epoch else None,
            setup_id=payload.get("setup_id"),
            instrument_id=payload.get("instrument_id"),
            cluster_id=payload.get("cluster_id"),
            status=ObservationStatus[payload["status"]],
            rejection=RejectionRecord.from_dict(rejection) if rejection else None,
            meta=dict(payload.get("meta", {})),
        )


class ClusterKind(Enum):
    GNSS_BASELINE = "gnss_baseline"
    GNSS_POINT = "gnss_point"
    DIRECTION_SET = "direction_set"
    GENERIC = "generic"


@dataclass(frozen=True)
class Cluster:
    """Observations sharing one covariance matrix (FR-104).

    **A cluster is the atomic unit passed to an adjustment.** Splitting one into
    independent scalars discards correlation and falsifies every statistic that
    follows, so nothing in GeoComp does it implicitly.

    Attributes:
        observation_ids: Ordered. **The order defines the covariance ordering**,
            which is why it is stored explicitly rather than inferred.
        covariance: Full n x n over the ordered members.
    """

    id: str
    kind: ClusterKind
    observation_ids: tuple[str, ...]
    covariance: Covariance

    def __post_init__(self) -> None:
        if not self.observation_ids:
            raise DataError(
                "cluster_without_members",
                cluster=self.id,
                expected="at least one member observation",
            )
        if len(set(self.observation_ids)) != len(self.observation_ids):
            raise DataError("cluster_duplicate_members", cluster=self.id)

        # **One covariance row per component, not per observation.** A member
        # with three components -- a GNSS baseline is the case FR-104 exists for
        # -- contributes three rows, so a cluster of two baselines carries a 6x6.
        #
        # This was `size != len(observation_ids)` and made that cluster
        # impossible to build: the constructor refused the 6x6 the adjustment
        # requires and accepted the 2x2 the adjustment then rejected, so the
        # single most important correctness rule of the DynAdjust writer had no
        # representable input. Scalar members hid it, because for them the two
        # counts agree.
        #
        # The exact count needs the member observations, which a Cluster does
        # not hold -- it has their ids. So the divisibility is checked here and
        # the exact check lives in `Network.validate`, where they resolve.
        members = len(self.observation_ids)
        if self.covariance.size < members or self.covariance.size % members:
            raise DataError(
                "cluster_size_mismatch",
                cluster=self.id,
                observations=members,
                covariance=self.covariance.size,
                expected=(
                    f"a covariance over every component of every member: a whole "
                    f"multiple of {members}, one row per component "
                    f"(a GNSS baseline contributes three)"
                ),
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind.name,
            "observation_ids": list(self.observation_ids),
            "covariance": self.covariance.to_dict(),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> Cluster:
        return cls(
            id=payload["id"],
            kind=ClusterKind[payload["kind"]],
            observation_ids=tuple(payload["observation_ids"]),
            covariance=Covariance.from_dict(payload["covariance"]),
        )
