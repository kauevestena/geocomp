# SPDX-License-Identifier: GPL-2.0-or-later
"""Positions, coordinate systems and height types (FR-105).

``specs/04-data-model.md`` section 3. A position is never a bare triple: it
carries its CRS, its epoch, its height type, and an uncertainty on every
component.

``height_type`` is explicit because mixing ellipsoidal and orthometric heights
is one of the most damaging errors in combined GNSS and levelling work -- in
much of Brazil the geoid undulation is tens of metres, so the mistake is large,
systematic, and produces numbers that look entirely plausible.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from geocomp.core.errors import ValidationError
from geocomp.core.models.epoch import Epoch
from geocomp.core.uncertainty import Quantity
from geocomp.core.units import Unit

__all__ = ["CoordinateSystem", "HeightType", "Position"]


class CoordinateSystem(Enum):
    """How the three components of a position are to be read."""

    #: Latitude, longitude, height. Angles in radians, height in metres.
    GEODETIC = "geodetic"
    #: Geocentric X, Y, Z in metres.
    CARTESIAN = "cartesian"
    #: Projected easting, northing, up in metres.
    PROJECTED = "projected"

    @property
    def component_names(self) -> tuple[str, str, str]:
        return {
            CoordinateSystem.GEODETIC: ("latitude", "longitude", "height"),
            CoordinateSystem.CARTESIAN: ("x", "y", "z"),
            CoordinateSystem.PROJECTED: ("easting", "northing", "up"),
        }[self]

    @property
    def component_units(self) -> tuple[Unit, Unit, Unit]:
        if self is CoordinateSystem.GEODETIC:
            return (Unit.RADIAN, Unit.RADIAN, Unit.METRE)
        return (Unit.METRE, Unit.METRE, Unit.METRE)


class HeightType(Enum):
    """What the third component of a position is measured from.

    ``NONE`` is for a genuinely two-dimensional position, and is distinct from
    "we did not record which" -- there is no value for the latter, because
    guessing is exactly the failure this enumeration prevents.
    """

    #: Above the reference ellipsoid (h). What GNSS determines.
    ELLIPSOIDAL = "ellipsoidal"
    #: Above the geoid (H). What levelling determines.
    ORTHOMETRIC = "orthometric"
    #: Above the quasi-geoid.
    NORMAL = "normal"
    #: A 2D position; the third component carries no height information.
    NONE = "none"


@dataclass(frozen=True)
class Position:
    """Three coordinates with their uncertainties, CRS, epoch and height type.

    Attributes:
        values: Three :class:`~geocomp.core.uncertainty.Quantity`, in the order
            given by ``system.component_names``.
        system: How to read the components.
        crs: Authority and code, e.g. ``"EPSG:4674"``.
        epoch: The reference epoch, or ``None`` when unknown. Operations that
            need one refuse rather than assume (FR-105).
        height_type: What the third component is measured from.
        geoid_model: Which model related ellipsoidal and orthometric heights,
            when one was applied (FR-804). Two solutions computed with different
            geoid models are not comparable, and this is what makes that
            visible.
    """

    values: tuple[Quantity, Quantity, Quantity]
    system: CoordinateSystem
    crs: str
    epoch: Epoch | None = None
    height_type: HeightType = HeightType.NONE
    geoid_model: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if len(self.values) != 3:
            raise ValidationError("position_component_count", received=len(self.values))
        expected = self.system.component_units
        for quantity, unit, name in zip(self.values, expected, self.system.component_names, strict=True):
            if not isinstance(quantity, Quantity):
                raise ValidationError(
                    "position_component_not_a_quantity",
                    component=name,
                    received=type(quantity).__name__,
                    expected="a Quantity; every coordinate carries its uncertainty (FR-200)",
                )
            if quantity.unit is not unit:
                raise ValidationError(
                    "position_component_unit",
                    component=name,
                    received=quantity.unit.name,
                    expected=unit.name,
                )
        if not self.crs:
            raise ValidationError(
                "position_without_crs",
                expected="a CRS such as 'EPSG:4674'; GeoComp does not infer one",
            )

    # -- access ----------------------------------------------------------

    def __getitem__(self, index: int) -> Quantity:
        return self.values[index]

    def component(self, name: str) -> Quantity:
        """Return a component by its name in this coordinate system."""
        try:
            return self.values[self.system.component_names.index(name)]
        except ValueError:
            raise ValidationError(
                "unknown_position_component",
                component=name,
                expected=list(self.system.component_names),
            ) from None

    @property
    def height(self) -> Quantity:
        return self.values[2]

    @property
    def has_height(self) -> bool:
        return self.height_type is not HeightType.NONE

    def std_devs(self) -> tuple[float, float, float]:
        return tuple(q.std_dev for q in self.values)  # type: ignore[return-value]

    # -- height discipline -----------------------------------------------

    def require_comparable_height(self, other: Position, operation: str) -> None:
        """Raise unless the heights of *self* and *other* can be combined.

        Heights of different types may only be combined through a geoid model
        (FR-802, FR-804). This is a hard refusal, not a warning: the resulting
        numbers would be wrong by the geoid undulation while looking entirely
        reasonable.
        """
        if not self.has_height or not other.has_height:
            return
        if self.height_type is other.height_type:
            return
        raise ValidationError(
            "incompatible_height_types",
            operation=operation,
            received=[self.height_type.value, other.height_type.value],
            expected=(
                "heights of the same type, or a geoid model to relate them; "
                "differencing ellipsoidal and orthometric heights is wrong by "
                "the geoid undulation"
            ),
        )

    # -- serialisation ---------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "values": [q.to_dict() for q in self.values],
            "system": self.system.name,
            "crs": self.crs,
            "height_type": self.height_type.name,
        }
        if self.epoch is not None:
            payload["epoch"] = self.epoch.to_dict()
        if self.geoid_model:
            payload["geoid_model"] = self.geoid_model
        if self.meta:
            payload["meta"] = dict(self.meta)
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> Position:
        epoch = payload.get("epoch")
        return cls(
            values=tuple(Quantity.from_dict(v) for v in payload["values"]),  # type: ignore[arg-type]
            system=CoordinateSystem[payload["system"]],
            crs=payload["crs"],
            epoch=Epoch.from_dict(epoch) if epoch else None,
            height_type=HeightType[payload["height_type"]],
            geoid_model=payload.get("geoid_model"),
            meta=dict(payload.get("meta", {})),
        )

    def __repr__(self) -> str:
        names = self.system.component_names
        body = ", ".join(f"{n}={q.value!r}" for n, q in zip(names, self.values, strict=True))
        return f"Position({body}, {self.crs}, {self.height_type.value})"
