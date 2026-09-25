# SPDX-License-Identifier: GPL-2.0-or-later
"""Relative gravimeters: calibration and precision (FR-061, FR-069, FR-701).

``specs/12-module-gravimetry.md`` sections 4.1 and 6.

A relative gravimeter does not read gravity. A LaCoste & Romberg or a ZLS reads
a **counter**, in instrument units, and the manufacturer's calibration table
turns a counter reading into milligal; a Scintrex reads milligal directly, but
through a scale it was calibrated on. Either way a **calibration factor**,
determined on a calibration line of known gravity differences, corrects the
scale -- and that factor is known only to a few parts in ten thousand.

**Where the factor's uncertainty goes.** It multiplies every reading, so its
error is the same in every reading of one instrument: perfectly correlated. On
a single reading it is enormous -- a counter reading is thousands of milligal
from zero, and 1e-4 of that is a few hundred microgal -- and in a *difference*
almost all of it cancels, leaving ``sigma_k * |dg|``: negligible across a
street, dominant across a mountain range. Attaching it to each reading as
though independent would therefore be wrong by orders of magnitude, so this
module attaches it to **nothing**. :meth:`GravimeterProfile.reading_in_gravity`
applies the factor's *value* and returns the reading's own precision; the
network builder in :mod:`geocomp.core.techniques.gravimetry.network` puts the
factor's variance where it belongs, into the covariance of the differences,
correlated across all of them (FR-204).

**Applied-once.** A Scintrex CG-5 with its tide correction switched on writes
readings that already have Longman's tide removed. Removing it again doubles
it, and nothing downstream can tell. :attr:`GravimeterProfile.applies_tide`
records what the instrument did, and the reduction honours it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from geocomp.core.errors import ValidationError
from geocomp.core.uncertainty import Quantity, Strategy
from geocomp.core.units import METRES_PER_SECOND_SQUARED_PER_MGAL, Unit

__all__ = ["TABLE_CONSISTENCY", "CalibrationTable", "GravimeterProfile", "ReadingUnit"]

#: How far a calibration table's value column may disagree with its own
#: interval factors, m/s^2. Manufacturers print values to 0.01 mGal and factors
#: to five decimals over intervals of 100 counter units; a larger disagreement
#: than the printing explains is a transcription error in the table, and a
#: table with one in it converts every reading above that row wrongly.
TABLE_CONSISTENCY = 0.01 * METRES_PER_SECOND_SQUARED_PER_MGAL


class ReadingUnit(Enum):
    """What a gravimeter's reading is in."""

    #: Counter units, converted through a calibration table (LaCoste & Romberg
    #: G and D, ZLS Burris in dial mode).
    COUNTER = "counter"
    #: Gravity already, in the instrument's own calibrated scale (Scintrex
    #: CG-5 and CG-6, a Burris in feedback mode). Stored in m/s^2 like every
    #: gravity value.
    GRAVITY = "gravity"


@dataclass(frozen=True)
class CalibrationTable:
    """A manufacturer's counter-to-gravity table, piecewise linear.

    Attributes:
        rows: ``(counter, gravity, factor)`` per row: a counter reading, the
            gravity it corresponds to in m/s^2, and the factor for the interval
            *above* it, in m/s^2 per counter unit. A reading ``r`` between two
            rows converts as ``gravity[k] + (r - counter[k]) * factor[k]``. The
            last row's factor covers one more interval of the same width.
        source: The document the table was transcribed from.
    """

    rows: tuple[tuple[float, float, float], ...]
    source: str = ""

    def __post_init__(self) -> None:
        if len(self.rows) < 2:
            raise ValidationError(
                "calibration_table_too_short",
                received=len(self.rows),
                expected="at least two rows; one row has no interval to interpolate over",
            )
        for index, (lower, upper) in enumerate(zip(self.rows, self.rows[1:], strict=False)):
            counter, gravity, factor = lower
            if not upper[0] > counter:
                raise ValidationError(
                    "calibration_table_not_increasing",
                    row=index + 1,
                    expected="counter readings strictly increasing down the table",
                )
            if not factor > 0.0:
                raise ValidationError(
                    "calibration_table_factor_not_positive",
                    row=index,
                    received=factor,
                    expected="a positive interval factor",
                )
            implied = gravity + (upper[0] - counter) * factor
            if abs(implied - upper[1]) > TABLE_CONSISTENCY:
                raise ValidationError(
                    "calibration_table_inconsistent",
                    row=index + 1,
                    received=upper[1],
                    implied=implied,
                    expected=(
                        "a value equal, to the table's printed precision, to the previous "
                        "row's value plus its factor times the interval. The rows disagree "
                        "by more than printing explains, so one of them was mistyped"
                    ),
                )
        if not self.rows[-1][2] > 0.0:
            raise ValidationError(
                "calibration_table_factor_not_positive",
                row=len(self.rows) - 1,
                received=self.rows[-1][2],
                expected="a positive interval factor",
            )

    @property
    def span(self) -> tuple[float, float]:
        """The counter readings the table can convert, inclusive."""
        last_interval = self.rows[-1][0] - self.rows[-2][0]
        return self.rows[0][0], self.rows[-1][0] + last_interval

    def to_gravity(self, reading: Quantity) -> Quantity:
        """Convert a counter reading, carrying its precision through the local factor."""
        if reading.unit is not Unit.DIMENSIONLESS:
            raise ValidationError(
                "counter_reading_unit",
                received=reading.unit.name,
                expected="a dimensionless counter reading",
            )
        low, high = self.span
        if not low <= reading.value <= high:
            raise ValidationError(
                "gravimeter_reading_outside_table",
                received=reading.value,
                expected=f"a counter reading between {low} and {high}; the table cannot be "
                "extrapolated, because the next interval's factor is not in it",
            )
        row = max(k for k, entry in enumerate(self.rows) if entry[0] <= reading.value)
        counter, gravity, factor = self.rows[row]
        return Quantity(
            value=gravity + (reading.value - counter) * factor,
            variance=reading.variance * factor**2,
            unit=Unit.ACCELERATION,
            mode=reading.mode,
            strategies=reading.strategies,
        )

    def to_dict(self) -> dict[str, Any]:
        return {"rows": [list(row) for row in self.rows], "source": self.source}

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> CalibrationTable:
        return cls(
            rows=tuple(tuple(float(v) for v in row) for row in payload["rows"]),  # type: ignore[misc]
            source=payload.get("source", ""),
        )


def _unit_factor() -> Quantity:
    return Quantity.exact(1.0, Unit.DIMENSIONLESS)


@dataclass(frozen=True)
class GravimeterProfile:
    """One relative gravimeter, as calibrated (``specs/12`` section 6).

    Attributes:
        id: Readings reference the instrument by it.
        reading_unit: Counter units or gravity; see :class:`ReadingUnit`.
        table: Required for a counter-reading instrument, refused otherwise.
        calibration_factor: Multiplies the (table-converted) reading. Its
            variance is the calibration's uncertainty, propagated into the
            differences by the network builder -- never onto a single reading.
        sigma_reading: Nominal standard deviation of one reading, m/s^2. Zero
            means the profile states none, and then every reading must bring
            its own.
        applies_tide: The instrument's readings already have the tide removed.
        source: The calibration certificate or report the numbers came from.
    """

    id: str
    name: str = ""
    model: str = ""
    serial: str = ""
    reading_unit: ReadingUnit = ReadingUnit.GRAVITY
    table: CalibrationTable | None = None
    calibration_factor: Quantity = field(default_factory=_unit_factor)
    sigma_reading: float = 0.0
    applies_tide: bool = False
    source: str = ""

    def __post_init__(self) -> None:
        if not self.id or not self.id.strip():
            raise ValidationError(
                "gravimeter_profile_without_id",
                expected="a non-empty id; readings reference the instrument by it",
            )
        if self.reading_unit is ReadingUnit.COUNTER and self.table is None:
            raise ValidationError(
                "counter_gravimeter_without_table",
                gravimeter=self.id,
                expected="the manufacturer's calibration table; a counter reading means nothing without it",
            )
        if self.reading_unit is ReadingUnit.GRAVITY and self.table is not None:
            raise ValidationError(
                "gravity_gravimeter_with_table",
                gravimeter=self.id,
                expected="no table for an instrument that reads gravity; converting twice is a silent error",
            )
        if self.calibration_factor.unit is not Unit.DIMENSIONLESS or not self.calibration_factor.value > 0.0:
            raise ValidationError(
                "gravimeter_calibration_factor_invalid",
                gravimeter=self.id,
                received=self.calibration_factor.value,
                expected="a positive dimensionless factor, close to 1",
            )
        if self.sigma_reading < 0.0:
            raise ValidationError(
                "gravimeter_sigma_negative",
                gravimeter=self.id,
                received=self.sigma_reading,
                expected="a non-negative standard deviation in m/s^2",
            )

    @property
    def label(self) -> str:
        return self.name or self.id

    def reading_in_gravity(self, reading: Quantity) -> Quantity:
        """A reading on the instrument's calibrated gravity scale.

        The table (for a counter instrument) and the calibration factor's
        *value* are applied; the factor's *uncertainty* is not, for the reason
        the module docstring gives. A reading that brings no precision of its
        own takes the profile's nominal one, labelled as such.
        """
        if self.reading_unit is ReadingUnit.COUNTER:
            assert self.table is not None  # guaranteed by __post_init__
            gravity = self.table.to_gravity(self._with_precision(reading, Unit.DIMENSIONLESS))
        else:
            gravity = self._with_precision(reading, Unit.ACCELERATION)
        factor = self.calibration_factor.value
        return Quantity(
            value=gravity.value * factor,
            variance=gravity.variance * factor**2,
            unit=Unit.ACCELERATION,
            mode=gravity.mode,
            strategies=gravity.strategies,
        )

    def _with_precision(self, reading: Quantity, unit: Unit) -> Quantity:
        if reading.unit is not unit:
            raise ValidationError(
                "gravimeter_reading_unit",
                gravimeter=self.id,
                received=reading.unit.name,
                expected=unit.name,
            )
        if reading.variance > 0.0:
            return reading
        if self.sigma_reading <= 0.0:
            raise ValidationError(
                "gravimeter_reading_without_precision",
                gravimeter=self.id,
                expected=(
                    "a standard deviation on the reading or a sigma_reading on the profile; "
                    "GeoComp does not invent a weight"
                ),
            )
        sigma = self.sigma_reading
        if self.reading_unit is ReadingUnit.COUNTER:
            # The nominal figure is in gravity; a counter reading needs it in
            # counter units, through the table's factor where the reading is.
            assert self.table is not None
            row = max(
                (k for k, entry in enumerate(self.table.rows) if entry[0] <= reading.value),
                default=0,
            )
            sigma /= self.table.rows[row][2]
        return Quantity.approximate(reading.value, sigma, unit, Strategy.NOMINAL_PRECISION)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": self.id,
            "reading_unit": self.reading_unit.value,
            "calibration_factor": self.calibration_factor.to_dict(),
            "sigma_reading": self.sigma_reading,
            "applies_tide": self.applies_tide,
        }
        for key in ("name", "model", "serial", "source"):
            if getattr(self, key):
                payload[key] = getattr(self, key)
        if self.table is not None:
            payload["table"] = self.table.to_dict()
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> GravimeterProfile:
        table = payload.get("table")
        factor = payload.get("calibration_factor")
        return cls(
            id=payload["id"],
            name=payload.get("name", ""),
            model=payload.get("model", ""),
            serial=payload.get("serial", ""),
            reading_unit=ReadingUnit(payload.get("reading_unit", ReadingUnit.GRAVITY.value)),
            table=CalibrationTable.from_dict(table) if table else None,
            calibration_factor=Quantity.from_dict(factor) if factor else _unit_factor(),
            sigma_reading=float(payload.get("sigma_reading", 0.0)),
            applies_tide=bool(payload.get("applies_tide", False)),
            source=payload.get("source", ""),
        )
