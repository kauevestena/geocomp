# SPDX-License-Identifier: GPL-2.0-or-later
"""Stations and their datum constraints (FR-101, FR-222).

``specs/04-data-model.md`` sections 2.3 and 2.4.

Constraints are **per component**, not per station, because a station is
routinely fixed in height and free in plan -- a benchmark used in a 3D network --
or the reverse. Modelling the constraint as a station-level flag makes that
common case inexpressible.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from geocomp.core.errors import DataError, ValidationError
from geocomp.core.models.position import Position
from geocomp.core.uncertainty import Covariance

__all__ = [
    "ConstraintMode",
    "ConstraintSpec",
    "MonitoringRole",
    "Station",
    "StationType",
]


class StationType(Enum):
    MARK = "mark"
    BENCHMARK = "benchmark"
    GNSS_CORS = "gnss_cors"
    OBJECT_POINT = "object_point"
    REFERENCE_POINT = "reference_point"
    #: Exists only in a pre-analysis design and has no observations yet (FR-270).
    PLANNED = "planned"


class MonitoringRole(Enum):
    """Whether a station is assumed stable or is on the structure (FR-835).

    The distinction drives deformation analysis: if the datum is defined by
    holding stations that have themselves moved, that motion is redistributed
    across the network and appears as everything *else* moving.
    """

    #: Part of the stable block against which movement is measured.
    REFERENCE = "reference"
    #: On the structure being monitored.
    OBJECT = "object"


class ConstraintMode(Enum):
    FREE = "free"
    FIXED = "fixed"
    WEIGHTED = "weighted"


@dataclass(frozen=True)
class ConstraintSpec:
    """How a station is tied to the datum, component by component.

    Attributes:
        mode: Free, held exactly, or constrained with a covariance.
        components: Which components the constraint applies to, named as in the
            constraining position's coordinate system.
        position: The constraining coordinates, with their epoch.
        covariance: Required when ``mode`` is ``WEIGHTED`` -- a weighted
            constraint without an uncertainty is not a weighted constraint.
    """

    mode: ConstraintMode = ConstraintMode.FREE
    components: frozenset[str] = field(default_factory=frozenset)
    position: Position | None = None
    covariance: Covariance | None = None

    def __post_init__(self) -> None:
        if self.mode is ConstraintMode.FREE:
            if self.components or self.position is not None:
                raise ValidationError(
                    "free_constraint_with_detail",
                    expected="a free station carries no constraining position or components",
                )
            return

        if self.position is None:
            raise ValidationError(
                "constraint_without_position",
                mode=self.mode.value,
                expected="the coordinates the station is constrained to",
            )
        if not self.components:
            raise ValidationError(
                "constraint_without_components",
                mode=self.mode.value,
                expected="the components the constraint applies to, e.g. {'height'}",
            )
        valid = set(self.position.system.component_names)
        unknown = sorted(set(self.components) - valid)
        if unknown:
            raise ValidationError(
                "constraint_unknown_components",
                received=unknown,
                expected=sorted(valid),
            )
        if self.mode is ConstraintMode.WEIGHTED and self.covariance is None:
            raise ValidationError(
                "weighted_constraint_without_covariance",
                expected=(
                    "a covariance; a weighted constraint with no uncertainty is "
                    "a fixed constraint under another name"
                ),
            )

    @property
    def is_free(self) -> bool:
        return self.mode is ConstraintMode.FREE

    def constrains(self, component: str) -> bool:
        return not self.is_free and component in self.components

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"mode": self.mode.name}
        if self.components:
            payload["components"] = sorted(self.components)
        if self.position is not None:
            payload["position"] = self.position.to_dict()
        if self.covariance is not None:
            payload["covariance"] = self.covariance.to_dict()
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ConstraintSpec:
        position = payload.get("position")
        covariance = payload.get("covariance")
        return cls(
            mode=ConstraintMode[payload["mode"]],
            components=frozenset(payload.get("components", ())),
            position=Position.from_dict(position) if position else None,
            covariance=Covariance.from_dict(covariance) if covariance else None,
        )


@dataclass(frozen=True)
class Station:
    """A geodetic point (FR-101).

    Identifiers come from the field book and GeoComp never renames one: a
    surrogate key is added internally where a format needs it, and reversed on
    the way back out (``specs/07-engine-dynadjust.md`` section 4.3).
    """

    id: str
    name: str = ""
    description: str = ""
    approx_position: Position | None = None
    constraint: ConstraintSpec = field(default_factory=ConstraintSpec)
    station_type: StationType = StationType.MARK
    monitoring_role: MonitoringRole | None = None
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id or not self.id.strip():
            raise DataError("station_without_id")
        if self.station_type is not StationType.PLANNED and self.constraint.mode is not ConstraintMode.FREE:
            if self.constraint.position is None:  # pragma: no cover - ConstraintSpec enforces this
                raise DataError("constrained_station_without_position", station=self.id)

    @property
    def display_name(self) -> str:
        return self.name or self.id

    @property
    def is_planned(self) -> bool:
        """A design-only station, with no observations yet (FR-270)."""
        return self.station_type is StationType.PLANNED

    @property
    def is_reference(self) -> bool:
        return self.monitoring_role is MonitoringRole.REFERENCE

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": self.id,
            "station_type": self.station_type.name,
            "constraint": self.constraint.to_dict(),
        }
        for key, value in (
            ("name", self.name),
            ("description", self.description),
            ("approx_position", self.approx_position.to_dict() if self.approx_position else None),
            ("monitoring_role", self.monitoring_role.name if self.monitoring_role else None),
            ("meta", dict(self.meta) if self.meta else None),
        ):
            if value:
                payload[key] = value
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> Station:
        position = payload.get("approx_position")
        role = payload.get("monitoring_role")
        return cls(
            id=payload["id"],
            name=payload.get("name", ""),
            description=payload.get("description", ""),
            approx_position=Position.from_dict(position) if position else None,
            constraint=ConstraintSpec.from_dict(payload["constraint"]),
            station_type=StationType[payload["station_type"]],
            monitoring_role=MonitoringRole[role] if role else None,
            meta=dict(payload.get("meta", {})),
        )
