# SPDX-License-Identifier: GPL-2.0-or-later
"""How a quantity is written for a person to read (FR-067; phase P12a).

``geocomp/core/display_format.py``: the four interface settings had no reader
until P12a. These pin what each one does to what a report prints, and what it
must never do -- reach a file, or change a coordinate's units.
"""

from __future__ import annotations

import math

import pytest

from geocomp.core.display_format import ANGLE_FORMATS, DISTANCE_UNITS, DisplayFormat
from geocomp.core.errors import ValidationError
from geocomp.core.settings_def import setting

#: 123° 45' 06.7", in radians.
ANGLE = math.radians(123.0 + 45.0 / 60.0 + 6.7 / 3600.0)


class TestTheChoicesAreTheSettings:
    def test_the_formats_are_the_settings_choices(self):
        """The window offers what this formats, no more and no less."""
        assert setting("interface.angle_format").choices == ANGLE_FORMATS
        assert setting("interface.distance_unit").choices == DISTANCE_UNITS

    def test_the_defaults_are_the_settings_defaults(self):
        default = DisplayFormat()
        assert default.angle_format == setting("interface.angle_format").default
        assert default.angle_decimals == setting("interface.angle_decimals").default
        assert default.coordinate_decimals == setting("interface.coordinate_decimals").default
        assert default.distance_unit == setting("interface.distance_unit").default

    @pytest.mark.parametrize(
        "arguments",
        [
            {"angle_format": "mils"},
            {"distance_unit": "chain"},
            {"angle_decimals": 7},
            {"coordinate_decimals": -1},
        ],
    )
    def test_a_value_the_settings_would_not_hold_is_refused(self, arguments):
        with pytest.raises(ValidationError):
            DisplayFormat(**arguments)


class TestAngles:
    def test_sexagesimal_to_the_configured_places_on_the_seconds(self):
        assert DisplayFormat(angle_decimals=1).angle(ANGLE) == "123° 45' 06.7\""
        assert DisplayFormat(angle_decimals=0).angle(ANGLE) == "123° 45' 07\""

    @pytest.mark.parametrize(
        ("angle_format", "expected"),
        [
            ("decimal_degrees", f"{math.degrees(ANGLE):.5f}°"),
            ("gon", f"{ANGLE * 200.0 / math.pi:.5f} gon"),
            ("radian", f"{ANGLE:.7f} rad"),
        ],
    )
    def test_each_decimal_format_resolves_about_what_the_seconds_do(self, angle_format, expected):
        """One setting, one meaning: places on the smallest customary unit, so
        a tenth of a second is about the resolution in every format."""
        assert DisplayFormat(angle_format=angle_format, angle_decimals=1).angle(ANGLE) == expected

    @pytest.mark.parametrize(
        ("angle_format", "symbol", "expected"),
        [
            ("dms", "″", "12.3"),
            ("decimal_degrees", "″", "12.3"),
            ("gon", "cc", f"{math.radians(12.3 / 3600.0) * 200.0 / math.pi * 1.0e4:.1f}"),
            ("radian", "µrad", f"{math.radians(12.3 / 3600.0) * 1.0e6:.1f}"),
        ],
    )
    def test_a_small_angle_is_written_in_the_formats_small_unit(
        self, angle_format, symbol, expected
    ):
        shown = DisplayFormat(angle_format=angle_format)
        assert shown.small_angle_symbol == symbol
        assert shown.small_angle(math.radians(12.3 / 3600.0)) == expected

    def test_nothing_to_show_is_a_dash_not_a_number(self):
        shown = DisplayFormat()
        assert shown.angle(None) == "—"
        assert shown.small_angle(float("nan")) == "—"


class TestLengths:
    def test_a_utm_northing_is_never_written_with_an_exponent(self):
        """The report's number formatter switches to an exponent at a million,
        so every UTM northing in the southern hemisphere printed as 7.3951e+06."""
        assert DisplayFormat().coordinate(7395123.45678) == "7395123.4568"
        assert DisplayFormat(coordinate_decimals=2).coordinate(7395123.45678) == "7395123.46"

    def test_a_coordinate_keeps_its_crs_units_whatever_the_distance_unit(self):
        """A metric grid in feet describes a coordinate system that does not exist."""
        assert DisplayFormat(distance_unit="foot").coordinate(1000.0) == "1000.0000"

    @pytest.mark.parametrize(
        ("unit", "symbol", "expected"),
        [
            ("metre", "m", "100.0000"),
            ("foot", "ft", f"{100.0 / 0.3048:.4f}"),
            ("us_survey_foot", "US ft", f"{100.0 * 3937.0 / 1200.0:.4f}"),
        ],
    )
    def test_a_distance_is_converted_to_the_configured_unit(self, unit, symbol, expected):
        shown = DisplayFormat(distance_unit=unit)
        assert shown.distance_symbol == symbol
        assert shown.distance(100.0) == expected

    def test_the_two_feet_are_not_the_same_foot(self):
        """Two parts per million apart: 2 cm over 10 km, which is a survey."""
        international = float(DisplayFormat(distance_unit="foot").distance(10000.0))
        survey = float(DisplayFormat(distance_unit="us_survey_foot").distance(10000.0))
        # Each is rounded to a ten-thousandth of a foot, so they differ by no
        # better than two of those.
        assert international - survey == pytest.approx(10000.0 / 0.3048 * 2.0e-6, abs=2.0e-4)
