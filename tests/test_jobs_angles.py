# SPDX-License-Identifier: GPL-2.0-or-later
"""Typing an angle into a field-book grid (FR-012, ``specs/15`` section 7.4).

Two properties carry the module:

* **A convention is strict.** ``87.3115`` is an angle in three of the four
  conventions and a different one in each, so a cell is read in the job's or
  refused -- never guessed.
* **Typed equals imported.** An angle typed as degrees, minutes and seconds is
  the same number, to the last bit, as the same three values read by the file
  importer.
"""

from __future__ import annotations

import math

import pytest

from geocomp.core.errors import ValidationError
from geocomp.core.units import dms_to_radians
from geocomp.jobs import AngleTyping, format_typed_angle, parse_typed_angle


class TestSeparated:
    @pytest.mark.parametrize(
        "text",
        ["87 31 15", "87-31-15", "87:31:15", "87°31'15\"", "87d31m15s", "  87  31  15  ", "87º 31′ 15″"],  # noqa: RUF001
    )
    def test_the_separators_a_surveyor_types(self, text):
        assert parse_typed_angle(text, AngleTyping.DMS) == dms_to_radians(87, 31, 15)

    def test_seconds_may_carry_a_fraction_with_either_decimal_mark(self):
        expected = dms_to_radians(199, 6, 38.25)
        assert parse_typed_angle("199 06 38.25", AngleTyping.DMS) == expected
        assert parse_typed_angle("199 06 38,25", AngleTyping.DMS) == expected

    def test_degrees_alone_and_degrees_with_minutes(self):
        assert parse_typed_angle("90", AngleTyping.DMS) == math.radians(90.0)
        assert parse_typed_angle("90 30", AngleTyping.DMS) == dms_to_radians(90, 30, 0)
        assert parse_typed_angle("90 30.5", AngleTyping.DMS) == dms_to_radians(90, 30.5, 0)

    def test_a_negative_angle_keeps_its_sign_below_one_degree(self):
        assert parse_typed_angle("-0 00 30", AngleTyping.DMS) == -dms_to_radians(0, 0, 30)

    def test_it_is_the_importers_arithmetic_to_the_last_bit(self):
        """What the importer evaluates for a sexagesimal triple
        (``geocomp.io.fieldbook._angle``), written out."""
        for degrees, minutes, seconds in ((199, 6, 38), (19, 6, 35), (269, 0, 9), (0, 0, 0), (88, 7, 40)):
            imported = math.radians(degrees + minutes / 60.0 + seconds / 3600.0)
            typed = parse_typed_angle(f"{degrees} {minutes} {seconds}", AngleTyping.DMS)
            assert typed == imported

    def test_decimal_degrees_are_not_taken_for_a_separated_angle(self):
        """The silent factor-of-sixty error the strictness exists to prevent."""
        with pytest.raises(ValidationError) as refusal:
            parse_typed_angle("87.5208", AngleTyping.DMS)
        assert refusal.value.code == "validation.typed_angle_fraction_misplaced"

    def test_a_fraction_before_the_last_part_is_refused(self):
        with pytest.raises(ValidationError) as refusal:
            parse_typed_angle("87.5 31 15", AngleTyping.DMS)
        assert refusal.value.code == "validation.typed_angle_fraction_misplaced"

    @pytest.mark.parametrize("text", ["87 60 00", "87 31 60", "87 75"])
    def test_sixty_minutes_or_seconds_are_refused_not_carried(self, text):
        with pytest.raises(ValidationError) as refusal:
            parse_typed_angle(text, AngleTyping.DMS)
        assert refusal.value.code == "validation.typed_angle_sexagesimal_out_of_range"

    @pytest.mark.parametrize("text", ["abc", "87 31 15 02", "", "87 x 15", "1e3"])
    def test_what_is_not_an_angle_is_refused(self, text):
        with pytest.raises(ValidationError) as refusal:
            parse_typed_angle(text, AngleTyping.DMS)
        assert refusal.value.code == "validation.typed_angle_not_dms"


class TestPacked:
    def test_minutes_and_seconds_are_read_from_the_digits(self):
        """87.3115 as a float is 87.31149999..., which read arithmetically
        gives 87 31 14.99999 -- so the digits are read, not the number."""
        assert parse_typed_angle("87.3115", AngleTyping.DMS_PACKED) == dms_to_radians(87, 31, 15)

    def test_fractional_seconds_follow_the_fourth_digit(self):
        assert parse_typed_angle("199.063825", AngleTyping.DMS_PACKED) == dms_to_radians(199, 6, 38.25)

    def test_short_fractions_are_padded_on_the_right(self):
        assert parse_typed_angle("90", AngleTyping.DMS_PACKED) == math.radians(90.0)
        assert parse_typed_angle("90.3", AngleTyping.DMS_PACKED) == dms_to_radians(90, 30, 0)
        assert parse_typed_angle("90,3", AngleTyping.DMS_PACKED) == dms_to_radians(90, 30, 0)

    @pytest.mark.parametrize("text", ["87.6000", "87.3160", "87.9"])
    def test_sixty_minutes_or_seconds_are_refused(self, text):
        with pytest.raises(ValidationError) as refusal:
            parse_typed_angle(text, AngleTyping.DMS_PACKED)
        assert refusal.value.code == "validation.typed_angle_sexagesimal_out_of_range"

    def test_a_separated_angle_is_refused(self):
        with pytest.raises(ValidationError) as refusal:
            parse_typed_angle("87 31 15", AngleTyping.DMS_PACKED)
        assert refusal.value.code == "validation.typed_angle_not_packed"


class TestDecimal:
    def test_decimal_degrees(self):
        assert parse_typed_angle("87.520833", AngleTyping.DECIMAL_DEGREES) == math.radians(87.520833)
        assert parse_typed_angle("-1,5", AngleTyping.DECIMAL_DEGREES) == -math.radians(1.5)

    def test_gon(self):
        assert parse_typed_angle("100", AngleTyping.GON) == pytest.approx(math.pi / 2.0, abs=1e-15)

    @pytest.mark.parametrize("typing", [AngleTyping.DECIMAL_DEGREES, AngleTyping.GON])
    def test_a_separated_angle_is_refused(self, typing):
        with pytest.raises(ValidationError) as refusal:
            parse_typed_angle("87 31 15", typing)
        assert refusal.value.code == "validation.typed_angle_not_a_number"


class TestTheSameTextIsADifferentAngleInEachConvention:
    def test_which_is_why_none_is_guessed(self):
        values = {
            typing: parse_typed_angle("87.3115", typing)
            for typing in (AngleTyping.DMS_PACKED, AngleTyping.DECIMAL_DEGREES, AngleTyping.GON)
        }
        assert len({round(value, 9) for value in values.values()}) == 3


class TestFormatting:
    @pytest.mark.parametrize("typing", list(AngleTyping))
    @pytest.mark.parametrize("radians", [0.0, 1.0, 3.4751159, 6.2831, -0.000145, math.pi / 2.0])
    def test_what_is_written_reads_back_within_a_ten_thousandth_of_a_second(self, typing, radians):
        text = format_typed_angle(radians, typing)
        assert parse_typed_angle(text, typing) == pytest.approx(radians, abs=5e-10)

    def test_the_default_convention_writes_three_parts(self):
        assert format_typed_angle(dms_to_radians(87, 31, 15), AngleTyping.DMS) == "87 31 15.0000"
        assert format_typed_angle(dms_to_radians(87, 31, 15), AngleTyping.DMS, 0) == "87 31 15"

    def test_packed_writes_minutes_and_seconds_after_the_mark(self):
        assert format_typed_angle(dms_to_radians(87, 31, 15), AngleTyping.DMS_PACKED, 0) == "87.3115"
        assert format_typed_angle(dms_to_radians(87, 1, 5.5), AngleTyping.DMS_PACKED, 1) == "87.01055"

    def test_seconds_that_round_to_sixty_are_carried(self):
        almost = dms_to_radians(87, 59, 59.99999)
        assert format_typed_angle(almost, AngleTyping.DMS, 2) == "88 00 00.00"
        assert format_typed_angle(almost, AngleTyping.DMS_PACKED, 0) == "88.0000"
