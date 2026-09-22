# SPDX-License-Identifier: GPL-2.0-or-later
"""The reference station database (FR-063), and what its coordinates mean (FR-105).

``specs/11-module-gnss.md`` section 7. Relative positioning needs a base, and a
base is not merely a position: it is a position **in a frame, at an epoch**,
with a velocity that carries it to any other epoch. Processing against a base
whose published coordinates are in a different frame or at a different epoch
from the project, without saying so, is a systematic error in every point
derived from it -- and it is invisible, because the solution is internally
consistent either way.

Three rules follow, and each is enforced here rather than left to a caller.

**A station without an epoch is refused where an epoch is required** (FR-105),
through the same :func:`~geocomp.core.models.epoch.require_epoch` every other
module uses. There is no default epoch and no "probably today".

**Propagating to another epoch is exact and always recorded.** The published
velocity is a linear rate; applying it is a multiplication, and the result says
which epoch it is now at and where it came from. RD-06's own two stations show
why this matters in the other direction too: they share a velocity exactly, so
their *baseline* is epoch-invariant while neither *position* is.

**Changing frame is refused, not guessed** (FR-832). A frame change is a
Helmert transformation whose parameters GeoComp does not hold; PROJ does, and
``specs/14`` section 3 assigns the operation to the QGIS/PROJ infrastructure in
phase P10. Silently treating ITRF2020 coordinates as SIRGAS2000 is a
decimetre-scale error that no test in this project would catch, so the request
raises and names what would satisfy it.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from geocomp.core.errors import DataError, ValidationError
from geocomp.core.models.epoch import Epoch, require_epoch
from geocomp.core.uncertainty import Quantity
from geocomp.core.units import Unit

__all__ = [
    "ReferenceStation",
    "StationDatabase",
    "propagate_to_epoch",
    "require_same_frame",
]


@dataclass(frozen=True)
class ReferenceStation:
    """One station whose coordinates somebody else published.

    Attributes:
        position: Geocentric cartesian X, Y, Z. :class:`Quantity`, because a
            published coordinate has an uncertainty even when the sheet that
            carries it declines to print one -- see ``specs/22`` section 5,
            where exactly that gap is what RD-06's residual comes down to.
        frame: The reference frame the coordinates are in, verbatim from the
            source: ``"ITRF2020"``, ``"SIRGAS2000"``. Never normalised, because
            normalising is how a frame quietly becomes a different one.
        epoch: When they are valid. ``None`` is allowed on the record -- a
            source may genuinely not state one -- and refused at the point of
            use.
        velocity_per_year: X, Y, Z metres per year, when published.
        antenna: Antenna type, for the calibration lookup.
        source: Where the coordinates came from, for provenance (FR-134).
    """

    id: str
    position: tuple[Quantity, Quantity, Quantity]
    frame: str
    name: str = ""
    epoch: Epoch | None = None
    velocity_per_year: tuple[float, float, float] | None = None
    antenna: str = ""
    source: str = ""
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            raise DataError("reference_station_without_id")
        if not self.frame:
            raise DataError(
                "reference_station_without_frame",
                station=self.id,
                expected=(
                    "the reference frame the published coordinates are in. A "
                    "coordinate without its frame is a number, not a position"
                ),
            )
        if len(self.position) != 3:
            raise DataError(
                "reference_station_position_count",
                station=self.id,
                received=len(self.position),
                expected="three geocentric components",
            )
        for index, quantity in enumerate(self.position):
            if quantity.unit is not Unit.METRE:
                raise DataError(
                    "reference_station_position_unit",
                    station=self.id,
                    component="xyz"[index],
                    received=quantity.unit.name,
                    expected="METRE",
                )

    @property
    def xyz(self) -> tuple[float, float, float]:
        return tuple(q.value for q in self.position)  # type: ignore[return-value]

    def epoch_for(self, operation: str) -> Epoch:
        """This station's epoch, or a refusal naming *operation* (FR-105)."""
        return require_epoch(self.epoch, operation=operation, subject=self.id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "position": [q.to_dict() for q in self.position],
            "frame": self.frame,
            "epoch": self.epoch.to_dict() if self.epoch else None,
            "velocity_per_year": list(self.velocity_per_year) if self.velocity_per_year else None,
            "antenna": self.antenna,
            "source": self.source,
            "meta": dict(self.meta),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ReferenceStation:
        velocity = payload.get("velocity_per_year")
        epoch = payload.get("epoch")
        return cls(
            id=payload["id"],
            name=payload.get("name", ""),
            position=tuple(Quantity.from_dict(q) for q in payload["position"]),  # type: ignore[arg-type]
            frame=payload["frame"],
            epoch=Epoch.from_dict(epoch) if epoch else None,
            velocity_per_year=tuple(velocity) if velocity else None,  # type: ignore[arg-type]
            antenna=payload.get("antenna", ""),
            source=payload.get("source", ""),
            meta=dict(payload.get("meta", {})),
        )


def propagate_to_epoch(station: ReferenceStation, target: Epoch) -> ReferenceStation:
    """Move *station*'s coordinates to *target* along its published velocity.

    Exact, because a published velocity is a linear rate by definition. The
    result records the epoch it is now at and keeps the original in ``meta``, so
    a provenance record can say what was applied rather than only that something
    was (FR-134).

    The uncertainty grows with the interval: a velocity known to *v* has moved a
    coordinate by *v·dt* with uncertainty *sigma_v·dt*, and over the decades
    that separate a published epoch from an observation that term stops being
    negligible. Where the source publishes no velocity uncertainty this adds
    none and says so through the unchanged quantity, rather than inventing one.

    Raises:
        ValidationError: if the station has no epoch to propagate *from*
            (FR-105), or no published velocity. Assuming zero velocity is a real
            choice with real consequences -- 15 mm/year is typical, so a decade
            is 15 cm -- and it is the caller's to make explicitly.
    """
    origin = station.epoch_for("propagate a reference station to another epoch")
    if station.velocity_per_year is None:
        raise ValidationError(
            "reference_station_without_velocity",
            station=station.id,
            expected=(
                "a published velocity. Treating an unstated velocity as zero is "
                "a decimetre-scale assumption over a decade, so GeoComp will not "
                "make it silently"
            ),
        )

    interval = target.decimal_year - origin.decimal_year
    moved = tuple(
        Quantity(
            value=quantity.value + rate * interval,
            variance=quantity.variance,
            unit=Unit.METRE,
            mode=quantity.mode,
            strategies=quantity.strategies,
        )
        for quantity, rate in zip(station.position, station.velocity_per_year, strict=True)
    )
    return replace(
        station,
        position=moved,  # type: ignore[arg-type]
        epoch=target,
        meta={
            **station.meta,
            "propagated_from_epoch": origin.decimal_year,
            "propagated_years": interval,
        },
    )


def require_same_frame(station: ReferenceStation, frame: str, *, operation: str) -> None:
    """Refuse a frame mismatch rather than transforming it (FR-832, P10).

    GeoComp does not hold Helmert parameters; PROJ does, and ``specs/14``
    section 3 assigns the transformation to the QGIS/PROJ infrastructure in
    phase P10. Until then a mismatch is an error with a name, not a conversion
    with a guess -- ITRF2020 read as SIRGAS2000 is wrong by decimetres and
    internally consistent, which is the worst combination there is.
    """
    if station.frame != frame:
        raise ValidationError(
            "reference_station_frame_mismatch",
            station=station.id,
            received=station.frame,
            expected=(
                f"coordinates in {frame}, the frame this {operation} works in. "
                "Transforming between frames needs Helmert parameters GeoComp "
                "does not hold; phase P10 routes this through PROJ (FR-832)"
            ),
        )


@dataclass
class StationDatabase:
    """The configured reference stations (FR-063).

    A plain JSON file rather than a service: the stations a user cares about are
    a handful of CORS near their work, the file is diffable and shareable, and
    nothing here needs a network -- which matters, because the archives that
    would serve them are exactly what ``specs/22`` section 5 records as
    unreachable.
    """

    stations: dict[str, ReferenceStation] = field(default_factory=dict)

    def add(self, station: ReferenceStation) -> None:
        if station.id in self.stations:
            raise DataError("duplicate_reference_station", station=station.id)
        self.stations[station.id] = station

    def get(self, station_id: str) -> ReferenceStation:
        try:
            return self.stations[station_id]
        except KeyError:
            raise DataError(
                "reference_station_not_found",
                station=station_id,
                expected=f"one of {sorted(self.stations) or 'an empty database'}",
            ) from None

    def resolve(
        self, station_id: str, *, frame: str, epoch: Epoch | None = None, operation: str = "processing"
    ) -> ReferenceStation:
        """Fetch a station, checked against the frame and moved to the epoch.

        The one call a processing algorithm should make: it applies FR-832's
        frame check and FR-105's epoch rule together, so neither can be
        forgotten at a call site that only remembered the other.
        """
        station = self.get(station_id)
        require_same_frame(station, frame, operation=operation)
        if epoch is None:
            return station
        if station.epoch is not None and station.epoch.decimal_year == epoch.decimal_year:
            return station
        return propagate_to_epoch(station, epoch)

    def to_dict(self) -> dict[str, Any]:
        return {"stations": [s.to_dict() for s in self.stations.values()]}

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> StationDatabase:
        database = cls()
        for row in payload.get("stations", []):
            database.add(ReferenceStation.from_dict(row))
        return database

    def write(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), indent=2) + "\n", encoding="utf-8")

    @classmethod
    def read(cls, path: str | Path) -> StationDatabase:
        location = Path(path)
        if not location.is_file():
            raise DataError(
                "reference_station_database_missing",
                file=str(location),
                expected="a JSON reference-station database; see specs/11 section 7",
            )
        try:
            payload = json.loads(location.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise DataError(
                "reference_station_database_unreadable", file=str(location), received=str(exc)
            ) from exc
        return cls.from_dict(payload)
