# SPDX-License-Identifier: GPL-2.0-or-later
"""Reading gravimeter files: CG-5, Burris and CSV (``geocomp/io/gravimeter_files.py``).

The CG-5 cases are built here from the format's header and column layout, with
numbers of the test's own; the real survey the format is checked against in
full cannot be redistributed and is read in the ``reference`` workflow by
``tests/test_rd07.py``. The Burris cases are USGS's vendored test files.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from geocomp.core.errors import DataError, ValidationError
from geocomp.core.techniques.gravimetry import tidal_correction
from geocomp.io.gravimeter_files import (
    GravimeterFormat,
    detect_format,
    read_burris,
    read_cg5,
    read_gravimeter_file,
    read_gravity_csv,
)
from tests.gravimeter_samples import LAT, LON
from tests.gravimeter_samples import cg5_export as _cg5

MGAL = 1e-5
UGAL = 1e-8
USGS = Path(__file__).parent / "data" / "rd07" / "gsadjust"


class TestCg5:
    def test_reads_every_reading_with_its_header(self):
        read = read_cg5(_cg5(utc_is_local_minus=0.0), source="t")
        assert read.format is GravimeterFormat.CG5
        assert [r.station for r in read.readings] == ["1", "2", "3", "2", "1"]
        assert read.instruments == ("CG-5 40123",)
        first = read.readings[0]
        assert first.value.value == pytest.approx(3021.123 * MGAL)
        assert math.degrees(first.latitude) == pytest.approx(LAT)
        assert math.degrees(first.longitude) == pytest.approx(LON)
        assert first.height == 900.0
        assert first.session == "CG-5 40123 2026-03-10"
        assert first.instant == datetime(2026, 3, 10, 9, 0, tzinfo=UTC)

    def test_the_precision_is_the_standard_error_plus_a_floor(self):
        """SD 0.020 mGal over 60 s is 2.58 microgal; with a 5 microgal floor, 5.63."""
        read = read_cg5(_cg5(), additive_sigma=5 * UGAL)
        assert read.readings[0].value.std_dev == pytest.approx(
            math.hypot(0.020 * MGAL / math.sqrt(60), 5 * UGAL)
        )

    def test_a_floor_makes_the_precision_nominal_and_says_so(self):
        """A floor is a nominal figure, so a precision that includes one is
        approximate (FR-203); without one the instrument's statistic stands."""
        from geocomp.core.uncertainty import Strategy, UncertaintyMode

        floored = read_cg5(_cg5(), additive_sigma=5 * UGAL).readings[0].value
        assert floored.mode is UncertaintyMode.APPROXIMATE
        assert Strategy.NOMINAL_PRECISION in floored.strategies
        assert read_cg5(_cg5()).readings[0].value.mode is UncertaintyMode.RIGOROUS

    def test_a_zero_gmt_difference_is_an_assumption_stated_and_checked(self):
        read = read_cg5(_cg5(gmt_diff=0.0, utc_is_local_minus=0.0), replace_tide=True)
        (clock,) = [note for note in read.notes if "GMT difference is zero" in note]
        assert "taken as UTC" in clock and "agrees with Longman's" in clock
        untided = read_cg5(_cg5(gmt_diff=0.0, tide="NO"))
        (clock,) = [note for note in untided.notes if "GMT difference is zero" in note]
        assert "give the offset explicitly" in clock

    def test_the_instruments_tide_is_kept_and_said_to_be(self):
        read = read_cg5(_cg5(utc_is_local_minus=0.0))
        assert all(r.tide_applied for r in read.readings)
        assert any("Tide Correction: YES" in note for note in read.notes)

    def test_replacing_it_adds_it_back_first(self):
        text = _cg5(utc_is_local_minus=0.0)
        kept = read_cg5(text).readings[0]
        replaced = read_cg5(text, replace_tide=True).readings[0]
        tide = tidal_correction(kept.instant, kept.latitude, kept.longitude, 900.0).value
        assert not replaced.tide_applied
        assert replaced.value.value == pytest.approx(kept.value.value - round(tide / MGAL, 3) * MGAL)

    def test_a_tide_switched_off_is_left_for_geocomp(self):
        assert not any(r.tide_applied for r in read_cg5(_cg5(tide="NO")).readings)

    def test_a_bad_line_is_named(self):
        text = _cg5().replace("0.020    0.2", "0.0x0    0.2", 1)
        with pytest.raises(DataError) as caught:
            read_cg5(text, source="t")
        assert caught.value.code == "data.gravimeter_line_unreadable"


class TestTheCg5Clock:
    """``GMT DIFF.`` can be read two ways; the file's own tide column decides."""

    @pytest.mark.parametrize("convention", [+3.0, -3.0])
    def test_the_tide_column_settles_which_way_the_offset_runs(self, convention):
        text = _cg5(gmt_diff=3.0, utc_is_local_minus=convention)
        read = read_cg5(text, replace_tide=True)
        assert read.readings[0].instant == datetime(2026, 3, 10, 9, 0, tzinfo=UTC) - timedelta(
            hours=convention
        )
        assert any("agrees with Longman" in note for note in read.notes)

    def test_a_file_that_cannot_settle_it_is_refused(self):
        """No tide column to compare, and GeoComp's tide needs UTC."""
        with pytest.raises(ValidationError) as caught:
            read_cg5(_cg5(gmt_diff=3.0, tide="NO"))
        assert caught.value.code == "validation.gravimeter_clock_unsettled"

    def test_unless_the_offset_is_given(self):
        read = read_cg5(_cg5(gmt_diff=3.0, tide="NO"), utc_offset_hours=-3.0)
        assert read.readings[0].instant == datetime(2026, 3, 10, 12, 0, tzinfo=UTC)

    def test_a_kept_tide_does_not_need_it(self):
        """Only elapsed time matters then, and the offset cancels."""
        read = read_cg5(_cg5(gmt_diff=3.0, utc_is_local_minus=3.0))
        times = [r.instant for r in read.readings]
        assert times[1] - times[0] == timedelta(minutes=20)


class TestBurris:
    def test_reads_usgs_test_4_with_both_meters(self):
        read = read_burris((USGS / "Test4.txt").read_text(), source="Test4")
        assert read.format is GravimeterFormat.BURRIS
        assert len(read.readings) == 22
        assert read.instruments == ("B108", "B44")
        assert {r.session for r in read.readings} == {"B44 2010-01-01", "B108 2010-01-01"}

    def test_a_zero_tide_column_leaves_the_tide_to_the_profile(self):
        """The meter applied none, so the profile decides: a synthetic, tide-free
        survey like USGS's says so there, and a real one with the correction off
        gets GeoComp's -- the default, with no profile."""
        read = read_burris((USGS / "Test2.txt").read_text())
        assert all(r.tide_applied is None for r in read.readings)

    def test_a_non_zero_tide_column_was_applied(self):
        line = (
            "rg37 abc B44 2017/12/05 15:56:20 2769.695 2800 0.482 -0.103 0.005 -0.033 "
            "-0.002 0 1600 35.142072 -106.669613\n"
        )
        (reading,) = read_burris(line).readings
        assert reading.tide_applied is True
        (replaced,) = read_burris(line, replace_tide=True).readings
        assert replaced.tide_applied is False
        assert replaced.value.value == pytest.approx((2769.695 + 0.103) * 1e-5)

    def test_no_precision_is_stated_so_none_is_invented(self):
        read = read_burris((USGS / "Test2.txt").read_text())
        assert all(r.value.variance == 0.0 for r in read.readings)
        floored = read_burris((USGS / "Test2.txt").read_text(), additive_sigma=3 * UGAL)
        assert all(r.value.std_dev == pytest.approx(3 * UGAL) for r in floored.readings)


class TestCsv:
    TEXT = (
        "station,time,reading_mgal,sd_mgal,instrument,latitude_deg,longitude_deg,sensor_height_m,tide_applied\n"
        "A,2026-03-10T09:00:00-03:00,3021.123,0.004,CG-6 7,-25.45,-49.23,0.21,false\n"
        "B,2026-03-10T09:20:00Z,3021.456,,CG-6 7,-25.45,-49.23,,true\n"
    )

    def test_reads_times_with_their_offsets(self):
        read = read_gravity_csv(self.TEXT)
        assert read.readings[0].instant == datetime(2026, 3, 10, 12, 0, tzinfo=UTC)
        assert read.readings[0].sensor_height.value == 0.21
        assert read.readings[0].value.std_dev == pytest.approx(0.004 * MGAL)
        assert read.readings[0].tide_applied is False
        assert read.readings[1].tide_applied is True

    def test_a_naive_time_is_refused(self):
        with pytest.raises(DataError) as caught:
            read_gravity_csv(self.TEXT.replace("-03:00", ""))
        assert caught.value.code == "data.gravimeter_csv_naive_time"

    def test_required_columns_are_named(self):
        with pytest.raises(DataError) as caught:
            read_gravity_csv("station,time\nA,2026-03-10T09:00:00Z\n")
        assert caught.value.code == "data.gravimeter_csv_columns"


class TestDetection:
    def test_each_format_is_recognised_by_its_content(self, tmp_path):
        assert detect_format(_cg5()) is GravimeterFormat.CG5
        assert detect_format((USGS / "Test1.txt").read_text()) is GravimeterFormat.BURRIS
        assert detect_format(TestCsv.TEXT) is GravimeterFormat.CSV
        path = tmp_path / "anything.dat"
        path.write_text(TestCsv.TEXT)
        assert read_gravimeter_file(path).format is GravimeterFormat.CSV

    def test_anything_else_is_refused(self):
        with pytest.raises(DataError) as caught:
            detect_format("just some text\n")
        assert caught.value.code == "data.gravimeter_format_unknown"
