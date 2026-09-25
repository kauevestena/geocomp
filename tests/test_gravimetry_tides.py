# SPDX-License-Identifier: GPL-2.0-or-later
"""The solid-Earth tide correction (``specs/12`` section 4.2, FR-701).

Judged against ETERNA with the Hartmann-Wenzel (1995) catalogue -- the committed
series in ``tests/data/rd07/eterna_hw95.json``, regenerated in CI by
``scripts/check_tide_reference.py``. The second reference, the CG-5 firmware's
own correction over a real survey, is not redistributable and runs in the
``reference`` workflow through ``scripts/check_rd07.py``.

The comparison is made with a **rigid** Earth on both sides: amplitude 1 in
ETERNA, amplification 1 here. That isolates what the stated uncertainty is
meant to be -- how well Longman's closed form describes the Moon and the Sun --
from the choice of gravimetric factor, which is a separate approximation.
"""

from __future__ import annotations

import json
import math
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from geocomp.core.errors import ValidationError
from geocomp.core.techniques.gravimetry.tides import (
    DEFAULT_AMPLIFICATION,
    MODEL_UNCERTAINTY,
    tidal_correction,
)
from geocomp.core.uncertainty import Strategy, UncertaintyMode
from geocomp.core.units import METRES_PER_SECOND_SQUARED_PER_UGAL as UGAL
from geocomp.core.units import Unit

SERIES = Path(__file__).parent / "data" / "rd07" / "eterna_hw95.json"
NM_S2 = 1e-9


def _series():
    document = json.loads(SERIES.read_text(encoding="utf-8"))
    for series in document["series"]:
        start = datetime.strptime(series["start_utc"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
        step = timedelta(seconds=series["interval_s"])
        times = [start + k * step for k in range(len(series["gravity_nm_s2"]))]
        yield series, times


def _disagreement(series, times):
    """ETERNA's change in gravity plus Longman's correction: zero if they agree."""
    latitude = math.radians(series["latitude_deg"])
    longitude = math.radians(series["longitude_deg"])
    return [
        eterna * NM_S2 + tidal_correction(t, latitude, longitude, series["height_m"], amplification=1.0).value
        for eterna, t in zip(series["gravity_nm_s2"], times, strict=True)
    ]


def _rms(values):
    return math.sqrt(sum(v * v for v in values) / len(values))


class TestAgainstEterna:
    @pytest.mark.parametrize("index", range(6))
    def test_each_series_agrees_to_the_formulas_accuracy(self, index):
        """0.76 to 1.21 microgal rms and 2.0 to 4.2 at worst, measured; the
        bounds leave a hundredth of a microgal for floating point and nothing
        for a transcription error, which would be tens of microgal."""
        series, times = list(_series())[index]
        misfit = _disagreement(series, times)
        assert _rms(misfit) < 1.22 * UGAL
        assert max(abs(v) for v in misfit) < 4.25 * UGAL

    def test_the_stated_uncertainty_is_derived_from_the_series(self):
        """MODEL_UNCERTAINTY is the worst rms above, times the default factor,
        rounded up to 0.1 microgal. If the series or the formula changes, this
        is where the stated figure and the evidence for it part company."""
        worst = max(_rms(_disagreement(series, times)) for series, times in _series())
        derived = math.ceil(worst * DEFAULT_AMPLIFICATION / (0.1 * UGAL)) * 0.1 * UGAL
        assert MODEL_UNCERTAINTY == pytest.approx(derived)

    def test_the_series_is_the_one_the_script_writes(self):
        document = json.loads(SERIES.read_text(encoding="utf-8"))
        assert document["generator"]["pygtide"] == "0.9.1"
        assert document["generator"]["catalogue"] == "Hartmann and Wenzel (1995)"
        assert document["generator"]["wavegroup"] == [[0.0, 10.0, 1.0, 0.0]]
        assert len(document["series"]) == 6


class TestTheCorrection:
    AT = datetime(2013, 9, 15, 6, 0, tzinfo=UTC)
    LAT, LON = math.radians(9.7), math.radians(1.6)

    def test_is_positive_when_eterna_says_gravity_fell(self):
        """The sign that matters: with the Moon overhead gravity reads low, and
        the correction that removes the tide is positive."""
        series, times = next(_series())
        lowest = min(range(len(times)), key=lambda k: series["gravity_nm_s2"][k])
        assert series["gravity_nm_s2"][lowest] < -500.0
        correction = tidal_correction(times[lowest], self.LAT, self.LON, 0.0)
        assert correction.value > 50.0 * UGAL

    def test_is_an_approximate_acceleration_with_the_model_uncertainty(self):
        correction = tidal_correction(self.AT, self.LAT, self.LON, 0.0)
        assert correction.unit is Unit.ACCELERATION
        assert correction.std_dev == pytest.approx(MODEL_UNCERTAINTY)
        assert correction.mode is UncertaintyMode.APPROXIMATE
        assert Strategy.NOMINAL_PRECISION in correction.strategies

    def test_scales_with_the_amplification(self):
        rigid = tidal_correction(self.AT, self.LAT, self.LON, 0.0, amplification=1.0).value
        elastic = tidal_correction(self.AT, self.LAT, self.LON, 0.0).value
        assert elastic == pytest.approx(DEFAULT_AMPLIFICATION * rigid)

    def test_the_timezone_is_honoured_not_assumed(self):
        """The same instant written in two zones is one correction."""
        from datetime import timezone

        brasilia = self.AT.astimezone(timezone(timedelta(hours=-3)))
        assert tidal_correction(brasilia, self.LAT, self.LON, 0.0).value == pytest.approx(
            tidal_correction(self.AT, self.LAT, self.LON, 0.0).value, abs=1e-15
        )

    def test_a_naive_instant_is_refused(self):
        with pytest.raises(ValidationError) as caught:
            tidal_correction(self.AT.replace(tzinfo=None), self.LAT, self.LON, 0.0)
        assert caught.value.code == "validation.tide_instant_naive"

    def test_degrees_are_refused_where_radians_are_expected(self):
        """A latitude of 25 is 25 radians, not 25 degrees, and is refused."""
        with pytest.raises(ValidationError) as caught:
            tidal_correction(self.AT, 25.0, self.LON, 0.0)
        assert caught.value.code == "validation.tide_latitude_out_of_range"

    def test_a_non_positive_factor_is_refused(self):
        with pytest.raises(ValidationError):
            tidal_correction(self.AT, self.LAT, self.LON, 0.0, amplification=0.0)

    def test_changes_by_tens_of_microgal_in_an_hour(self):
        """Why it is applied per reading, at the reading's instant."""
        values = [
            tidal_correction(self.AT + timedelta(minutes=10 * k), self.LAT, self.LON, 0.0).value
            for k in range(7)
        ]
        assert max(values) - min(values) > 10.0 * UGAL
