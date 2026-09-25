# SPDX-License-Identifier: GPL-2.0-or-later
"""Reducing a reading: scale, tide, and the height of the sensor above the mark.

``specs/12`` sections 4.1, 4.2 and 4.4. Each step is small; what these tests
guard is that each happens exactly once, with its uncertainty carried, and that
a reading missing what a step needs is refused rather than reduced by a guess.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime

import pytest

from geocomp.core.errors import ValidationError
from geocomp.core.instruments import GravimeterProfile, ProfileLibrary
from geocomp.core.techniques.gravimetry import (
    MODEL_UNCERTAINTY,
    NORMAL_FREE_AIR_GRADIENT,
    GravityReading,
    ReductionOptions,
    reduce_readings,
    tidal_correction,
)
from geocomp.core.uncertainty import Quantity, Strategy, UncertaintyMode
from geocomp.core.units import METRES_PER_SECOND_SQUARED_PER_MGAL as MGAL
from geocomp.core.units import METRES_PER_SECOND_SQUARED_PER_UGAL as UGAL
from geocomp.core.units import Unit

AT = datetime(2013, 9, 15, 6, 0, tzinfo=UTC)
LAT, LON = math.radians(9.7), math.radians(1.6)


def _library(*, applies_tide: bool = False) -> ProfileLibrary:
    library = ProfileLibrary()
    library.add_gravimeter(GravimeterProfile(id="CG-5", applies_tide=applies_tide, sigma_reading=5 * UGAL))
    return library


def _reading(**overrides) -> GravityReading:
    fields = {
        "id": "r1",
        "station": "A",
        "instant": AT,
        "value": Quantity.from_std_dev(2639.321 * MGAL, 7 * UGAL, Unit.ACCELERATION),
        "instrument": "CG-5",
        "session": "day 1",
        "latitude": LAT,
        "longitude": LON,
    }
    fields.update(overrides)
    return GravityReading(**fields)


class TestTheTide:
    def test_is_added_once(self):
        (reduced,) = reduce_readings([_reading()], _library())
        tide = tidal_correction(AT, LAT, LON, 0.0)
        assert reduced.tide == tide
        assert reduced.gravity.value == pytest.approx(2639.321 * MGAL + tide.value)

    def test_and_its_uncertainty_is_carried(self):
        (reduced,) = reduce_readings([_reading()], _library())
        assert reduced.gravity.std_dev == pytest.approx(math.hypot(7 * UGAL, MODEL_UNCERTAINTY))
        assert reduced.gravity.mode is UncertaintyMode.APPROXIMATE
        assert Strategy.NOMINAL_PRECISION in reduced.gravity.strategies

    def test_not_at_all_when_the_instrument_already_removed_it(self):
        """The applied-once rule: a CG-5 with its tide correction on."""
        (reduced,) = reduce_readings([_reading()], _library(applies_tide=True))
        assert reduced.tide is None
        assert reduced.gravity.value == 2639.321 * MGAL

    def test_the_reading_can_say_so_for_itself(self):
        """The CG-5's option is per survey, so a file can override its profile."""
        (reduced,) = reduce_readings([_reading(tide_applied=True)], _library())
        assert reduced.tide is None
        (again,) = reduce_readings([_reading(tide_applied=False)], _library(applies_tide=True))
        assert again.tide is not None

    def test_a_reading_that_needs_one_needs_a_place(self):
        with pytest.raises(ValidationError) as caught:
            reduce_readings([_reading(latitude=None)], _library())
        assert caught.value.code == "validation.gravity_reading_without_location"

    def test_switching_the_model_off_is_refused_where_nothing_removed_it(self):
        with pytest.raises(ValidationError) as caught:
            reduce_readings([_reading()], _library(), ReductionOptions(tide_model=None))
        assert caught.value.code == "validation.gravity_reading_tide_not_removed"


class TestTheHeightOfTheSensor:
    def test_is_reduced_to_the_mark_with_the_normal_gradient(self):
        """Gravity is larger at the mark, 0.3086 mGal per metre below the sensor."""
        height = Quantity.from_std_dev(0.25, 0.002, Unit.METRE)
        (reduced,) = reduce_readings([_reading(sensor_height=height, tide_applied=True)], _library())
        assert reduced.to_mark.value == pytest.approx(-NORMAL_FREE_AIR_GRADIENT * 0.25)
        assert reduced.to_mark.value == pytest.approx(0.07715 * MGAL)
        assert reduced.to_mark.std_dev == pytest.approx(3.086e-6 * 0.002)

    def test_a_measured_gradient_overrides_it_and_its_uncertainty_counts(self):
        height = Quantity.exact(0.25, Unit.METRE)
        options = ReductionOptions(station_gradients={"A": (-2.8e-6, 0.1e-6)})
        (reduced,) = reduce_readings([_reading(sensor_height=height, tide_applied=True)], _library(), options)
        assert reduced.to_mark.value == pytest.approx(2.8e-6 * 0.25)
        assert reduced.to_mark.std_dev == pytest.approx(0.25 * 0.1e-6)

    def test_no_height_means_no_reduction_and_the_result_says_so(self):
        (reduced,) = reduce_readings([_reading(tide_applied=True)], _library())
        assert reduced.to_mark is None

    def test_a_height_is_a_length(self):
        with pytest.raises(ValidationError):
            _reading(sensor_height=Quantity.exact(0.25, Unit.DIMENSIONLESS))


class TestTheReading:
    def test_a_naive_instant_is_refused(self):
        with pytest.raises(ValidationError) as caught:
            _reading(instant=AT.replace(tzinfo=None))
        assert caught.value.code == "validation.gravity_reading_instant_naive"

    def test_ids_are_unique(self):
        with pytest.raises(ValidationError) as caught:
            reduce_readings([_reading(), _reading()], _library())
        assert caught.value.code == "validation.duplicate_gravity_reading"

    def test_the_uncalibrated_value_is_kept_for_the_scale_term(self):
        library = ProfileLibrary()
        library.add_gravimeter(
            GravimeterProfile(
                id="CG-5", calibration_factor=Quantity.from_std_dev(1.0003, 1e-4, Unit.DIMENSIONLESS)
            )
        )
        (reduced,) = reduce_readings([_reading(tide_applied=True)], library)
        assert reduced.instrument_gravity == pytest.approx(2639.321 * MGAL)
        assert reduced.gravity.value == pytest.approx(1.0003 * 2639.321 * MGAL)
