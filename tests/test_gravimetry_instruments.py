# SPDX-License-Identifier: GPL-2.0-or-later
"""Gravimeter profiles, calibration tables and the scale correction (``specs/12`` section 4.1).

**What these tests can and cannot claim.** ``specs/12`` section 8 asks the scale
correction to reproduce a worked example to published precision. No published
calibration-table example was reachable from the development environment, so
the table here is *constructed* -- in the shape of a LaCoste & Romberg table,
counter readings every 100 units -- and the expected values are its own
arithmetic, written out. That checks the interpolation and the propagation; it
does not check agreement with a manufacturer's worked example, and
``specs/ROADMAP.md`` records criterion 1 as met for the tide and the drift and
not for the table.
"""

from __future__ import annotations

import pytest

from geocomp.core.errors import ValidationError
from geocomp.core.instruments import (
    CalibrationTable,
    GravimeterProfile,
    ProfileLibrary,
    ReadingUnit,
)
from geocomp.core.uncertainty import Quantity, Strategy, UncertaintyMode
from geocomp.core.units import METRES_PER_SECOND_SQUARED_PER_MGAL as MGAL
from geocomp.core.units import Unit

#: Counter, value in mGal, factor in mGal per counter unit -- the columns of a
#: LaCoste & Romberg table. Each value is the previous one plus 100 times the
#: previous factor, which is what makes a table self-consistent.
ROWS_MGAL = (
    (2300.0, 2363.52, 1.02523),
    (2400.0, 2466.043, 1.02518),
    (2500.0, 2568.561, 1.02514),
)


def _table() -> CalibrationTable:
    return CalibrationTable(
        rows=tuple((c, v * MGAL, f * MGAL) for c, v, f in ROWS_MGAL),
        source="constructed for the test",
    )


def _counter_meter(**overrides) -> GravimeterProfile:
    fields = {
        "id": "G-1",
        "reading_unit": ReadingUnit.COUNTER,
        "table": _table(),
        "calibration_factor": Quantity.from_std_dev(1.00030, 0.00010, Unit.DIMENSIONLESS),
        "sigma_reading": 0.010 * MGAL,
    }
    fields.update(overrides)
    return GravimeterProfile(**fields)


class TestTheCalibrationTable:
    def test_interpolates_within_a_row(self):
        """2345.67 counter units: 2363.52 + 45.67 * 1.02523 mGal."""
        reading = Quantity.from_std_dev(2345.67, 0.01, Unit.DIMENSIONLESS)
        gravity = _table().to_gravity(reading)
        assert gravity.unit is Unit.ACCELERATION
        assert gravity.value == pytest.approx((2363.52 + 45.67 * 1.02523) * MGAL, abs=1e-12)

    def test_carries_the_precision_through_the_local_factor(self):
        reading = Quantity.from_std_dev(2450.0, 0.01, Unit.DIMENSIONLESS)
        assert _table().to_gravity(reading).std_dev == pytest.approx(0.01 * 1.02518 * MGAL)

    def test_the_last_row_covers_one_more_interval(self):
        assert _table().span == (2300.0, 2600.0)
        _table().to_gravity(Quantity.exact(2599.0, Unit.DIMENSIONLESS))

    def test_does_not_extrapolate(self):
        with pytest.raises(ValidationError) as caught:
            _table().to_gravity(Quantity.exact(2299.0, Unit.DIMENSIONLESS))
        assert caught.value.code == "validation.gravimeter_reading_outside_table"

    def test_a_mistyped_row_is_refused(self):
        """A value that disagrees with its own interval factor by more than the
        table's printing explains -- here, a transposed digit."""
        rows = list(ROWS_MGAL)
        rows[1] = (2400.0, 2466.403, 1.02518)
        with pytest.raises(ValidationError) as caught:
            CalibrationTable(rows=tuple((c, v * MGAL, f * MGAL) for c, v, f in rows))
        assert caught.value.code == "validation.calibration_table_inconsistent"

    def test_rows_must_increase(self):
        rows = (ROWS_MGAL[1], ROWS_MGAL[0])
        with pytest.raises(ValidationError):
            CalibrationTable(rows=tuple((c, v * MGAL, f * MGAL) for c, v, f in rows))

    def test_survives_serialisation(self):
        assert CalibrationTable.from_dict(_table().to_dict()) == _table()


class TestTheProfile:
    def test_a_counter_meter_needs_a_table(self):
        with pytest.raises(ValidationError) as caught:
            _counter_meter(table=None)
        assert caught.value.code == "validation.counter_gravimeter_without_table"

    def test_a_gravity_meter_refuses_one(self):
        """Converting twice is a silent error."""
        with pytest.raises(ValidationError) as caught:
            GravimeterProfile(id="CG-5", table=_table())
        assert caught.value.code == "validation.gravity_gravimeter_with_table"

    def test_the_factor_is_applied_and_its_uncertainty_is_not(self):
        """Its uncertainty belongs to differences, correlated across all of them;
        on one counter reading it would be a quarter of a milligal."""
        meter = _counter_meter()
        reading = Quantity.from_std_dev(2345.67, 0.01, Unit.DIMENSIONLESS)
        gravity = meter.reading_in_gravity(reading)
        table = _table().to_gravity(reading)
        assert gravity.value == pytest.approx(1.00030 * table.value)
        assert gravity.std_dev == pytest.approx(1.00030 * table.std_dev)

    def test_a_reading_without_precision_takes_the_nominal_one_labelled(self):
        meter = GravimeterProfile(id="CG-5", sigma_reading=0.005 * MGAL)
        gravity = meter.reading_in_gravity(Quantity.exact(2639.321 * MGAL, Unit.ACCELERATION))
        assert gravity.std_dev == pytest.approx(0.005 * MGAL)
        assert gravity.mode is UncertaintyMode.APPROXIMATE
        assert Strategy.NOMINAL_PRECISION in gravity.strategies

    def test_a_counter_reading_gets_the_nominal_precision_in_counter_units(self):
        """The profile states it in gravity; the table's factor converts it."""
        meter = _counter_meter()
        gravity = meter.reading_in_gravity(Quantity.exact(2450.0, Unit.DIMENSIONLESS))
        assert gravity.std_dev == pytest.approx(0.010 * MGAL * 1.00030)

    def test_no_precision_anywhere_is_refused(self):
        with pytest.raises(ValidationError) as caught:
            GravimeterProfile(id="CG-5").reading_in_gravity(Quantity.exact(1.0, Unit.ACCELERATION))
        assert caught.value.code == "validation.gravimeter_reading_without_precision"

    def test_the_reading_unit_is_checked(self):
        with pytest.raises(ValidationError) as caught:
            GravimeterProfile(id="CG-5", sigma_reading=1e-8).reading_in_gravity(
                Quantity.exact(2639.0, Unit.DIMENSIONLESS)
            )
        assert caught.value.code == "validation.gravimeter_reading_unit"

    def test_survives_serialisation(self):
        meter = _counter_meter(applies_tide=True, serial="G-1", source="certificate 42")
        assert GravimeterProfile.from_dict(meter.to_dict()) == meter


class TestTheLibrary:
    def test_holds_gravimeters_and_a_default(self):
        library = ProfileLibrary()
        library.add_gravimeter(_counter_meter())
        library.add_gravimeter(GravimeterProfile(id="CG-5", sigma_reading=5e-8))
        assert library.gravimeter(None).id == "G-1"
        assert library.gravimeter("CG-5").id == "CG-5"

    def test_refuses_to_invent_one(self):
        with pytest.raises(ValidationError) as caught:
            ProfileLibrary().gravimeter(None)
        assert caught.value.code == "validation.no_gravimeter_profile"
        library = ProfileLibrary()
        library.add_gravimeter(_counter_meter())
        with pytest.raises(ValidationError) as caught:
            library.gravimeter("CG-6")
        assert caught.value.code == "validation.unknown_gravimeter_profile"

    def test_round_trips(self):
        library = ProfileLibrary()
        library.add_gravimeter(_counter_meter())
        again = ProfileLibrary.from_dict(library.to_dict())
        assert again.gravimeters == library.gravimeters
        assert again.default_gravimeter == "G-1"
