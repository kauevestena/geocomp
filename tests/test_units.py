# SPDX-License-Identifier: GPL-2.0-or-later
"""``core/units.py``: the SI boundary, and the display formats either side of it.

``specs/04-data-model.md`` section 6 fixes the internal representation -- SI
throughout, angles in radians -- and makes degrees-minutes-seconds, gon, mGal
and feet interchange formats converted at the boundary.

**This file was written by the pre-P7 review**, which found the module at 64%
with no test file of its own: it was covered only incidentally, by importers
that happen to call `parse_angle` and by everything that calls `wrap_to_pi`. The
whole display half -- `DMS`, `radians_to_dms`, `format_dms` -- had no caller
anywhere in `geocomp/` or in the suite, and so no test. That half is the
instrument `interface.angle_format` will need when something finally honours it
(see `tests/structural/test_settings_are_honoured.py`), and its rounding is the
kind that is wrong in exactly one place and silently: the carry at 60 seconds
and again at 60 minutes.
"""

from __future__ import annotations

import math

import pytest

from geocomp.core.units import (
    DMS,
    GON_PER_RADIAN,
    Unit,
    angular_difference,
    celsius_to_kelvin,
    circular_mean,
    convert,
    dimension_of,
    dms_to_radians,
    format_dms,
    kelvin_to_celsius,
    parse_angle,
    radians_to_dms,
    wrap_to_2pi,
    wrap_to_pi,
)


class TestDMS:
    def test_components_convert_to_decimal_degrees(self):
        assert DMS(12, 30, 45.0).decimal_degrees == pytest.approx(12.5125)

    def test_the_sign_is_a_flag_not_a_negative_component(self):
        """Only the leading component of a written angle carries the sign, so
        modelling it as a negative degree field would make -0 deg 30' work out
        as +0.5 deg."""
        assert DMS(0, 30, 0.0, negative=True).decimal_degrees == pytest.approx(-0.5)
        assert DMS(0, 30, 0.0).decimal_degrees == pytest.approx(0.5)

    def test_radians_agree_with_the_decimal_degrees(self):
        dms = DMS(48, 6, 22.5)
        assert dms.radians == pytest.approx(math.radians(dms.decimal_degrees))

    @pytest.mark.parametrize(
        ("components", "message"),
        [
            ((-1, 0, 0.0), "non-negative"),
            ((0, -1, 0.0), "non-negative"),
            ((0, 0, -1.0), "non-negative"),
            ((0, 60, 0.0), "minutes must be below 60"),
            ((0, 0, 60.0), "seconds must be below 60"),
        ],
    )
    def test_impossible_components_are_refused(self, components, message):
        with pytest.raises(ValueError, match=message):
            DMS(*components)

    def test_a_round_trip_through_decimal_degrees_is_exact_enough(self):
        for value in (0.0, 1e-7, 12.5125, 89.999999, 180.0, 359.9999):
            assert DMS.from_decimal_degrees(value).decimal_degrees == pytest.approx(
                value, abs=1e-12
            )
            assert DMS.from_decimal_degrees(-value).decimal_degrees == pytest.approx(
                -value, abs=1e-12
            )

    def test_the_unrounded_seconds_carry_at_the_representable_boundary(self):
        """``from_decimal_degrees`` clamps within 5e-10 of a whole minute.

        That is all it can do: it has no decimal count to round to. The wider
        boundary belongs to the formatter, and is tested there.
        """
        dms = DMS.from_decimal_degrees(12.0 + 30.0 / 60.0 + 59.9999999999 / 3600.0)
        assert dms.seconds < 60.0
        assert (dms.degrees, dms.minutes) == (12, 31)

    def test_the_minute_carry_rolls_into_the_degree(self):
        """Both boundaries at once: 59' 59.9999999999" is the next whole degree."""
        dms = DMS.from_decimal_degrees(12.0 + 59.0 / 60.0 + 59.9999999999 / 3600.0)
        assert (dms.degrees, dms.minutes) == (13, 0)
        assert dms.seconds == pytest.approx(0.0, abs=1e-6)

    def test_from_radians_and_radians_to_dms_are_the_same_thing(self):
        value = math.radians(-7.25)
        assert radians_to_dms(value) == DMS.from_radians(value)
        assert radians_to_dms(value).negative
        assert radians_to_dms(value).decimal_degrees == pytest.approx(-7.25)


class TestSexagesimalComponents:
    def test_three_columns_convert_to_radians(self):
        assert dms_to_radians(12, 30, 45.0) == pytest.approx(math.radians(12.5125))

    def test_a_negative_in_any_column_makes_the_whole_angle_negative(self):
        """RD-01's layout: only the leading non-zero component carries the sign,
        so a file writing ``0 -30 0`` means minus half a degree, not plus."""
        expected = -math.radians(0.5)
        assert dms_to_radians(-0, -30, 0.0) == pytest.approx(expected)
        assert dms_to_radians(0.0, 0.0, -1800.0) == pytest.approx(expected)

    def test_omitted_components_default_to_zero(self):
        assert dms_to_radians(90) == pytest.approx(math.pi / 2.0)


class TestFormatting:
    def test_the_default_form_uses_the_marks(self):
        assert format_dms(math.radians(12.5125)) == "12° 30' 45.0\""

    def test_seconds_are_zero_padded_to_two_integer_digits(self):
        """``12 30 5.0`` and ``12 30 05.0`` sort and align differently, and a
        fixed-width engine file needs the second."""
        assert format_dms(math.radians(12 + 30 / 60 + 5 / 3600)) == "12° 30' 05.0\""

    def test_the_space_separated_form_is_what_a_text_file_wants(self):
        assert format_dms(math.radians(12.5125), symbols=False) == "12 30 45.0"

    def test_zero_decimals_still_pads_the_seconds(self):
        assert format_dms(math.radians(12 + 30 / 60 + 5 / 3600), decimals=0) == "12° 30' 05\""

    def test_more_decimals_widen_the_field_by_exactly_that_much(self):
        assert format_dms(math.radians(12.5125), decimals=4) == "12° 30' 45.0000\""

    def test_a_negative_angle_signs_the_whole_string_once(self):
        """Not each component: ``-12° -30' -45"`` would read as a different
        angle to every parser, this module's included."""
        assert format_dms(-math.radians(12.5125)) == "-12° 30' 45.0\""

    def test_seconds_that_round_to_sixty_carry_into_the_minute(self):
        """A defect found by the pre-P7 review, which first called this function.

        At the default one decimal place every angle whose seconds are 59.95 or
        more used to print as ``60.0`` -- one angle in about 1200. The result was
        wrong twice: ``DMS(12, 30, 60.0)`` is refused by this module's own
        validation, so GeoComp could not read back what it had written; and the
        string parses as an angle 0.0003 degrees away from the one printed.
        """
        value = math.radians(12.0 + 30.0 / 60.0 + 59.97 / 3600.0)
        assert format_dms(value) == "12° 31' 00.0\""
        assert format_dms(value, decimals=0) == "12° 31' 00\""
        # Enough decimals to hold it and no carry is needed or made.
        assert format_dms(value, decimals=4) == "12° 30' 59.9700\""

    def test_the_carry_propagates_into_the_degree(self):
        assert format_dms(math.radians(12.0 + 59.0 / 60.0 + 59.97 / 3600.0)) == "13° 00' 00.0\""
        assert format_dms(math.radians(359.0 + 59.0 / 60.0 + 59.97 / 3600.0)) == "360° 00' 00.0\""

    def test_nothing_this_function_prints_is_refused_by_the_dms_validation(self):
        """The round trip that the 60-second bug broke: what is written must be
        readable. Swept over the whole boundary rather than at one value."""
        for step in range(0, 200):
            seconds = 59.9 + step * 0.0005
            value = math.radians(12.0 + 30.0 / 60.0 + seconds / 3600.0)
            for decimals in (0, 1, 2, 3):
                text = format_dms(value, decimals=decimals, symbols=False)
                degrees, minutes, second_text = text.split()
                DMS(int(degrees), int(minutes), float(second_text))  # must not raise

    def test_formatting_round_trips_through_parsing(self):
        for degrees in (0.0, 12.5125, -7.25, 359.75):
            text = format_dms(math.radians(degrees), decimals=6)
            assert parse_angle(text) == pytest.approx(math.radians(degrees), abs=1e-12)


class TestParsing:
    @pytest.mark.parametrize(
        ("text", "expected_degrees"),
        [
            ("12.5", 12.5),
            ("12 30 45", 12.5125),
            ("12-30-45", 12.5125),
            ("12° 30' 45.5\"", 12.0 + 30.0 / 60.0 + 45.5 / 3600.0),
            ("12d30m45s", 12.5125),
            ("12:30:45", 12.5125),
            ("12 30", 12.5),
            ("-12 30 45", -12.5125),
            ("+12 30 45", 12.5125),
            ("  12 30 45  ", 12.5125),
        ],
    )
    def test_the_forms_a_user_might_type(self, text, expected_degrees):
        assert parse_angle(text) == pytest.approx(math.radians(expected_degrees))

    def test_two_components_without_a_mark_fill_left_to_right(self):
        """A defect found by the pre-P7 review: ``12 30`` was 12 deg 00' 30".

        The pattern's minute group requires a *trailing* separator, so a bare
        second number fell through into the seconds group -- and ``12 30`` came
        out sixty times smaller than every field book means by it, while
        ``12 deg 30'`` with the mark was read correctly. Two spellings of one
        angle disagreeing by a factor of sixty, depending on whether the typist
        reached for the prime.
        """
        assert parse_angle("12 30") == pytest.approx(math.radians(12.5))
        assert parse_angle("12-30") == pytest.approx(math.radians(12.5))
        assert parse_angle("12:30") == pytest.approx(math.radians(12.5))

    def test_an_explicit_second_mark_still_means_seconds(self):
        """The rule is *fill left to right unless told otherwise*, not *the
        second number is always minutes*."""
        assert parse_angle('12 45"') == pytest.approx(math.radians(12.0 + 45.0 / 3600.0))
        assert parse_angle("12 45s") == pytest.approx(math.radians(12.0 + 45.0 / 3600.0))

    def test_a_hyphenated_negative_scalar_is_not_read_as_components(self):
        """``-12.5`` has one hyphen and it is the sign, not a separator."""
        assert parse_angle("-12.5") == pytest.approx(math.radians(-12.5))

    @pytest.mark.parametrize(
        ("default_unit", "expected"),
        [("degrees", math.radians(50.0)), ("gon", 50.0 / GON_PER_RADIAN), ("radians", 50.0)],
    )
    def test_a_bare_scalar_takes_the_declared_unit(self, default_unit, expected):
        assert parse_angle("50", default_unit) == pytest.approx(expected)

    def test_a_sexagesimal_string_ignores_the_default_unit(self):
        """It states its own: ``12 30 45`` is not 12.5125 gon."""
        assert parse_angle("12 30 45", "gon") == pytest.approx(math.radians(12.5125))

    @pytest.mark.parametrize("text", ["", "   ", "\t\n"])
    def test_an_empty_angle_is_refused(self, text):
        with pytest.raises(ValueError, match="empty angle"):
            parse_angle(text)

    def test_something_that_is_not_an_angle_is_refused_by_name(self):
        with pytest.raises(ValueError, match="could not parse"):
            parse_angle("north-ish")

    def test_an_unknown_default_unit_is_refused(self):
        with pytest.raises(ValueError, match="unknown default unit"):
            parse_angle("50", "furlongs")


class TestAngleArithmetic:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [(0.0, 0.0), (math.pi, math.pi), (-math.pi, math.pi), (3 * math.pi, math.pi)],
    )
    def test_wrap_to_pi_keeps_the_half_open_range(self, value, expected):
        assert wrap_to_pi(value) == pytest.approx(expected)

    def test_wrap_to_2pi_never_returns_a_full_turn(self):
        """The float trap this function documents: ``-1e-18 % 2pi`` is exactly
        ``2pi``, which is outside the half-open range the name promises and
        surprises every caller that compares against zero."""
        assert wrap_to_2pi(-1e-18) == 0.0
        assert wrap_to_2pi(-1e-18) < 2.0 * math.pi

    def test_a_difference_across_the_discontinuity_is_small(self):
        difference = angular_difference(math.radians(1.0), math.radians(359.0))
        assert difference == pytest.approx(math.radians(2.0))

    def test_the_circular_mean_of_359_and_1_is_zero_not_180(self):
        mean = circular_mean([math.radians(359.0), math.radians(1.0)])
        assert mean == pytest.approx(0.0, abs=1e-12)

    def test_the_circular_mean_of_nothing_is_refused(self):
        with pytest.raises(ValueError, match="no angles"):
            circular_mean([])

    def test_angles_that_cancel_have_no_mean_and_say_so(self):
        """Not an arbitrary answer: the mean direction of a set spread evenly
        round the circle is genuinely undefined, and papering over it would
        return a bearing nobody chose."""
        with pytest.raises(ValueError, match="undefined"):
            circular_mean([0.0, math.pi])


class TestUnitConversion:
    @pytest.mark.parametrize(
        ("name", "dimension"),
        [
            ("m", Unit.METRE), ("KM", Unit.METRE), ("ft", Unit.METRE),
            ("rad", Unit.RADIAN), ("gon", Unit.RADIAN), ("arcsec", Unit.RADIAN),
            ("mgal", Unit.ACCELERATION), ("hpa", Unit.PASCAL),
            ("ppm", Unit.DIMENSIONLESS), ("s", Unit.SECOND), ("kelvin", Unit.KELVIN),
        ],
    )
    def test_a_named_unit_reports_its_dimension_case_insensitively(self, name, dimension):
        assert dimension_of(name) is dimension

    def test_an_unknown_unit_is_a_value_error_not_a_geocomp_error(self):
        """Deliberate: an unknown unit name is a programming or configuration
        mistake, not a datum to report to a surveyor."""
        with pytest.raises(ValueError, match="unknown unit"):
            dimension_of("smoots")

    @pytest.mark.parametrize(
        ("value", "source", "target", "expected"),
        [
            (1.0, "km", "m", 1000.0),
            (1000.0, "mm", "m", 1.0),
            (1.0, "ft", "m", 0.3048),
            (200.0, "gon", "deg", 180.0),
            (3600.0, "arcsec", "deg", 1.0),
            (1.0, "mgal", "m/s^2", 1e-5),
            (1.0, "ppm", "", 1e-6),
        ],
    )
    def test_conversion_within_a_dimension(self, value, source, target, expected):
        assert convert(value, source, target) == pytest.approx(expected)

    def test_the_us_survey_foot_is_not_the_international_foot(self):
        """Two feet differ by 2 ppm, which is 2 mm in a kilometre -- inside a
        survey's tolerance to notice and outside its tolerance to accept."""
        difference = convert(1000.0, "us_survey_foot", "m") - convert(1000.0, "ft", "m")
        assert difference == pytest.approx(0.00061, abs=1e-5)

    @pytest.mark.parametrize(
        ("source", "target"),
        [("m", "rad"), ("gon", "km"), ("mgal", "s")],
    )
    def test_converting_across_dimensions_is_refused(self, source, target):
        with pytest.raises(ValueError, match="cannot convert"):
            convert(1.0, source, target)

    @pytest.mark.parametrize(("source", "target"), [("smoots", "m"), ("m", "smoots")])
    def test_an_unknown_unit_on_either_side_is_refused(self, source, target):
        with pytest.raises(ValueError, match="unknown unit"):
            convert(1.0, source, target)

    def test_celsius_is_absent_from_the_multiplicative_table(self):
        """It is an affine scale. A table of factors cannot express it, and
        pretending otherwise would make 0 degrees Celsius convert to 0 K."""
        with pytest.raises(ValueError, match="unknown unit"):
            dimension_of("celsius")

    def test_temperature_converts_through_its_own_functions(self):
        assert celsius_to_kelvin(0.0) == pytest.approx(273.15)
        assert kelvin_to_celsius(273.15) == pytest.approx(0.0)
        assert kelvin_to_celsius(celsius_to_kelvin(21.7)) == pytest.approx(21.7)
