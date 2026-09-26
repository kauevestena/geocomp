# SPDX-License-Identifier: GPL-2.0-or-later
"""Relative gravimeter readings, and their reduction (FR-701).

``specs/12-module-gravimetry.md`` sections 3, 4.1, 4.2 and 4.4.

A reading becomes a gravity value at a mark in three steps, each with its
uncertainty carried (FR-204, FR-703):

1. **Scale** -- through the instrument's calibration table and factor
   (:meth:`~geocomp.core.instruments.gravimeter.GravimeterProfile.reading_in_gravity`).
   The factor's *uncertainty* is left for the network builder, which puts it
   into the covariance of the differences where it belongs.
2. **Tide** -- Longman's correction at the reading's instant and place
   (:func:`~geocomp.core.techniques.gravimetry.tides.tidal_correction`), unless
   the instrument already applied one. Applying it twice is the silent error
   the applied-once rule exists for.
3. **To the mark** -- the sensor sits some tens of centimetres above the mark,
   and gravity falls by about 3 microgal per centimetre of height. A relative
   network whose sensor heights all match loses nothing by skipping this; one
   that combines relative readings with an absolute value quoted at the mark
   does not, and the error is a few tens of microgal and looks like nothing.

**Drift is not here.** It is a property of a *sequence* of readings, not of one,
and it is either estimated jointly with the station values or removed from the
sequence by the network builder
(:mod:`~geocomp.core.techniques.gravimetry.network`).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from geocomp.core.errors import ValidationError
from geocomp.core.instruments.profiles import ProfileLibrary
from geocomp.core.techniques.gravimetry.tides import (
    DEFAULT_AMPLIFICATION,
    MODEL_UNCERTAINTY,
    TIDE_SYSTEM,
    TideModel,
    tidal_correction,
)
from geocomp.core.uncertainty import Quantity, Strategy, UncertaintyMode, combine_modes
from geocomp.core.units import Unit

__all__ = [
    "NORMAL_FREE_AIR_GRADIENT",
    "GravityReading",
    "ReducedReading",
    "ReductionOptions",
    "reduce_readings",
]

#: dg/dh of normal gravity near the ellipsoid, s^-2: gravity falls by 0.3086
#: mGal per metre of height. A station's measured gradient differs from it by
#: up to a few tens of per cent, which is why a measured one can be given.
NORMAL_FREE_AIR_GRADIENT = -3.086e-6


@dataclass(frozen=True)
class GravityReading:
    """One relative gravimeter reading, as the instrument recorded it.

    Attributes:
        id: Unique within a survey; differences are named after their readings.
        station: The mark the instrument stood over.
        instant: When. Timezone-aware; the tide depends on it to the minute.
        value: Counter units (dimensionless) or gravity (m/s^2), per the
            instrument's profile. Its variance is the reading's own precision;
            zero means "take the profile's nominal one".
        instrument: The gravimeter profile id.
        session: A stretch of the instrument's operation with one drift
            behaviour -- typically a day, or the time between two transports
            that may have caused a tare. Drift parameters are estimated per
            session.
        latitude: Radians, where the tide is evaluated.
        longitude: Radians, east positive.
        height: Metres; the tide changes by parts per million per kilometre.
        sensor_height: Height of the sensor above the mark, metres. ``None``
            means the reading already refers to the mark and is not reduced --
            a statement the result records, not a default it hides.
        tide_applied: Whether the reading already has the tide removed.
            ``None`` defers to the profile's ``applies_tide``.
    """

    id: str
    station: str
    instant: datetime
    value: Quantity
    instrument: str
    session: str
    latitude: float | None = None
    longitude: float | None = None
    height: float | None = None
    sensor_height: Quantity | None = None
    tide_applied: bool | None = None

    def __post_init__(self) -> None:
        if not self.id or not self.station or not self.session:
            raise ValidationError(
                "gravity_reading_incomplete",
                reading=self.id,
                expected="an id, a station and a session",
            )
        if self.instant.tzinfo is None:
            raise ValidationError(
                "gravity_reading_instant_naive",
                reading=self.id,
                expected="a timezone-aware instant; a timezone guessed wrong by an hour "
                "is tens of microgal of tide",
            )
        if self.sensor_height is not None and self.sensor_height.unit is not Unit.METRE:
            raise ValidationError(
                "gravity_reading_sensor_height_unit",
                reading=self.id,
                received=self.sensor_height.unit.name,
                expected=Unit.METRE.name,
            )

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": self.id,
            "station": self.station,
            "instant": self.instant.isoformat(),
            "value": self.value.to_dict(),
            "instrument": self.instrument,
            "session": self.session,
        }
        for key in ("latitude", "longitude", "height", "tide_applied"):
            if getattr(self, key) is not None:
                payload[key] = getattr(self, key)
        if self.sensor_height is not None:
            payload["sensor_height"] = self.sensor_height.to_dict()
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> GravityReading:
        height = payload.get("sensor_height")
        return cls(
            id=payload["id"],
            station=payload["station"],
            instant=datetime.fromisoformat(payload["instant"]),
            value=Quantity.from_dict(payload["value"]),
            instrument=payload["instrument"],
            session=payload["session"],
            latitude=payload.get("latitude"),
            longitude=payload.get("longitude"),
            height=payload.get("height"),
            sensor_height=Quantity.from_dict(height) if height else None,
            tide_applied=payload.get("tide_applied"),
        )


@dataclass(frozen=True)
class ReductionOptions:
    """How readings are reduced. Every choice here is recorded on the result.

    Attributes:
        tide_model: ``None`` removes no tide, which is only right when every
            instrument applied its own; the reduction refuses otherwise.
        amplification: The gravimetric factor for the tide.
        tide_uncertainty: The tide model's standard uncertainty, m/s^2.
        vertical_gradient: dg/dh, s^-2, used to reduce a reading to its mark.
        vertical_gradient_sigma: Its standard uncertainty, s^-2. Zero is a
            claim that the gradient is exact, which the normal gradient is not;
            it is the default only because a relative network with matching
            sensor heights does not depend on it at all.
        station_gradients: Measured gradients by station, overriding the
            default for those stations: ``{station: (gradient, sigma)}``.
    """

    tide_model: TideModel | None = TideModel.LONGMAN_1959
    amplification: float = DEFAULT_AMPLIFICATION
    tide_uncertainty: float = MODEL_UNCERTAINTY
    vertical_gradient: float = NORMAL_FREE_AIR_GRADIENT
    vertical_gradient_sigma: float = 0.0
    station_gradients: dict[str, tuple[float, float]] | None = None


@dataclass(frozen=True)
class ReducedReading:
    """A reading on the calibrated scale, tide-free, at its mark.

    Attributes:
        reading: What was recorded.
        gravity: The reduced value, m/s^2. Its variance combines the reading's
            precision, the tide model's and the height reduction's, as
            independent terms -- which the tide model's error is not quite,
            since it varies slowly; the strategy records that.
        instrument_gravity: The reading converted through the table but not
            through the calibration factor, m/s^2. It is what the factor
            multiplies, so the network builder needs it to propagate the
            factor's uncertainty into the differences.
        tide: The correction applied, or ``None`` when the instrument had
            already applied one.
        to_mark: The height reduction applied, or ``None`` when the reading
            was taken to refer to the mark.
    """

    reading: GravityReading
    gravity: Quantity
    instrument_gravity: float
    tide: Quantity | None
    to_mark: Quantity | None

    @property
    def tide_system(self) -> str:
        return TIDE_SYSTEM

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "reading": self.reading.to_dict(),
            "gravity": self.gravity.to_dict(),
            "instrument_gravity": self.instrument_gravity,
        }
        if self.tide is not None:
            payload["tide"] = self.tide.to_dict()
        if self.to_mark is not None:
            payload["to_mark"] = self.to_mark.to_dict()
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ReducedReading:
        tide = payload.get("tide")
        to_mark = payload.get("to_mark")
        return cls(
            reading=GravityReading.from_dict(payload["reading"]),
            gravity=Quantity.from_dict(payload["gravity"]),
            instrument_gravity=float(payload["instrument_gravity"]),
            tide=Quantity.from_dict(tide) if tide else None,
            to_mark=Quantity.from_dict(to_mark) if to_mark else None,
        )


def reduce_readings(
    readings: list[GravityReading],
    profiles: ProfileLibrary,
    options: ReductionOptions | None = None,
) -> list[ReducedReading]:
    """Scale, de-tide and reduce every reading to its mark.

    Raises:
        ValidationError: a reading whose instrument applied no tide when the
            options remove none; a reading that needs a tide and has no
            location; an unknown instrument. Each names the reading.
    """
    options = options or ReductionOptions()
    seen: set[str] = set()
    reduced: list[ReducedReading] = []
    for reading in readings:
        if reading.id in seen:
            raise ValidationError("duplicate_gravity_reading", reading=reading.id)
        seen.add(reading.id)
        profile = profiles.gravimeter(reading.instrument)
        scaled = profile.reading_in_gravity(reading.value)
        factor = profile.calibration_factor.value

        tide = _tide(reading, profile.applies_tide, options)
        to_mark = _to_mark(reading, options)

        terms = [scaled] + [term for term in (tide, to_mark) if term is not None]
        mode, strategies = combine_modes(*terms)
        if tide is not None:
            strategies |= {Strategy.INDEPENDENCE_ASSUMED}
            mode = UncertaintyMode.APPROXIMATE
        gravity = Quantity(
            value=sum(term.value for term in terms),
            variance=sum(term.variance for term in terms),
            unit=Unit.ACCELERATION,
            mode=mode,
            strategies=frozenset(strategies),
        )
        reduced.append(
            ReducedReading(
                reading=reading,
                gravity=gravity,
                instrument_gravity=scaled.value / factor,
                tide=tide,
                to_mark=to_mark,
            )
        )
    return reduced


def _tide(reading: GravityReading, applies_tide: bool, options: ReductionOptions) -> Quantity | None:
    already = applies_tide if reading.tide_applied is None else reading.tide_applied
    if already:
        return None
    if options.tide_model is None:
        raise ValidationError(
            "gravity_reading_tide_not_removed",
            reading=reading.id,
            expected=(
                "a tide model, since neither the reading nor its instrument says the "
                "tide was already removed. Skipping it leaves a few hundred microgal "
                "that change by the hour in every difference"
            ),
        )
    if reading.latitude is None or reading.longitude is None:
        raise ValidationError(
            "gravity_reading_without_location",
            reading=reading.id,
            expected="the latitude and longitude the tide is to be computed for, in radians",
        )
    return tidal_correction(
        reading.instant,
        reading.latitude,
        reading.longitude,
        reading.height or 0.0,
        amplification=options.amplification,
        model_uncertainty=options.tide_uncertainty,
    )


def _to_mark(reading: GravityReading, options: ReductionOptions) -> Quantity | None:
    height = reading.sensor_height
    if height is None:
        return None
    gradient, sigma = (options.station_gradients or {}).get(
        reading.station, (options.vertical_gradient, options.vertical_gradient_sigma)
    )
    if not math.isfinite(gradient) or sigma < 0.0:
        raise ValidationError(
            "gravity_vertical_gradient_invalid",
            station=reading.station,
            received=gradient,
            expected="a finite gradient in s^-2 and a non-negative sigma",
        )
    # The mark is `height` below the sensor, where gravity is larger by
    # -gradient * height. A gradient's error and a height's error are
    # independent of each other.
    return Quantity(
        value=-gradient * height.value,
        variance=(gradient**2) * height.variance + (height.value**2) * sigma**2,
        unit=Unit.ACCELERATION,
        mode=height.mode,
        strategies=height.strategies,
    )
