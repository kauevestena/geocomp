# SPDX-License-Identifier: GPL-2.0-or-later
"""Trigonometric levelling and leap-frog (specs/09 section 4.5, FR-410).

The spec is explicit that leap-frog "changes the error model, not just the
arithmetic", and that the correlation between the two sights "MUST be modelled,
not approximated by treating the two as independent". These tests are what makes
that claim checkable: with balanced sights the refraction uncertainty is removed
from the result *entirely*, and the demonstration is that inflating it by two
orders of magnitude changes nothing.
"""

from __future__ import annotations

import math

import pytest

from geocomp.core.errors import ValidationError
from geocomp.core.techniques.total_station import (
    Sight,
    leapfrog_height_difference,
    radial_height_difference,
)
from geocomp.core.techniques.total_station.reductions import DEFAULT_EARTH_RADIUS
from geocomp.core.uncertainty import Quantity, Strategy, UncertaintyMode
from geocomp.core.units import Unit

METRE, RADIAN, NONE = Unit.METRE, Unit.RADIAN, Unit.DIMENSIONLESS


def m(value: float, sigma: float = 0.003) -> Quantity:
    return Quantity.from_std_dev(value, sigma, METRE)


def deg(value: float, sigma: float = 5e-6) -> Quantity:
    return Quantity.from_std_dev(math.radians(value), sigma, RADIAN)


def sight(station: str, zenith: float, distance: float, target: float = 1.500) -> Sight:
    return Sight(station, deg(zenith), m(distance), m(target, 0.001))


class TestRadialHeightDifference:
    def test_it_is_the_closed_form_with_curvature_and_refraction(self):
        result = radial_height_difference(sight("B", 89.0, 1000.0), m(1.500, 0.001))
        d, z = 1000.0, math.radians(89.0)
        horizontal = d * math.sin(z)
        expected = (
            d * math.cos(z)
            + 1.500
            - 1.500
            + (1.0 - 0.13) * horizontal**2 / (2.0 * DEFAULT_EARTH_RADIUS)
        )
        assert result.value == pytest.approx(expected, abs=1e-9)

    def test_the_instrument_and_target_heights_both_enter(self):
        """Which is the difference from leap-frog, and why leap-frog is better
        on short sights: this one carries both height errors in full."""
        base = radial_height_difference(sight("B", 90.0, 100.0), m(1.500, 0.001))
        taller = radial_height_difference(sight("B", 90.0, 100.0, target=1.700), m(1.500, 0.001))
        assert taller.value == pytest.approx(base.value - 0.200, abs=1e-9)

    def test_the_default_refraction_coefficient_is_recorded_as_an_assumption(self):
        result = radial_height_difference(sight("B", 89.0, 1000.0), m(1.500, 0.001))
        assert Strategy.TYPE_DEFAULT in result.strategies
        assert result.mode is UncertaintyMode.APPROXIMATE

    def test_a_stated_coefficient_is_used_and_stays_rigorous(self):
        stated = Quantity.from_std_dev(0.20, 0.01, NONE)
        result = radial_height_difference(
            sight("B", 89.0, 1000.0), m(1.500, 0.001), refraction_coefficient=stated
        )
        assert Strategy.TYPE_DEFAULT not in result.strategies


class TestLeapFrog:
    @staticmethod
    def _pair(backward_distance: float, forward_distance: float):
        return (
            sight("A", 90.5, backward_distance),
            sight("B", 89.5, forward_distance),
        )

    def test_the_value_is_the_difference_of_the_two_radial_results(self):
        """The arithmetic identity that must hold whatever the error model:
        leap-frog is two radial sights differenced, with the instrument height
        cancelling."""
        backward, forward = self._pair(500.0, 500.0)
        instrument = m(1.500, 0.001)
        expected = (
            radial_height_difference(forward, instrument).value
            - radial_height_difference(backward, instrument).value
        )
        result = leapfrog_height_difference(backward, forward)
        assert result.height_difference.value == pytest.approx(expected, abs=1e-9)

    def test_the_instrument_height_cancels_and_need_not_be_measured(self):
        """It is not an argument at all -- which is the point. The signature
        makes the cancellation structural rather than something the caller has
        to trust."""
        import inspect

        parameters = inspect.signature(leapfrog_height_difference).parameters
        assert "instrument_height" not in parameters

    @pytest.mark.parametrize("sigma_k", [0.0, 0.05, 0.5, 5.0])
    def test_balanced_sights_remove_the_refraction_uncertainty_entirely(self, sigma_k):
        """The headline property. With equal sights the two refraction
        corrections share one coefficient and subtract exactly, so the result's
        uncertainty does not depend on how badly *k* is known -- even absurdly
        badly. Treating the sights as independent would make this grow.
        """
        backward, forward = self._pair(500.0, 500.0)
        result = leapfrog_height_difference(
            backward,
            forward,
            refraction_coefficient=Quantity.from_std_dev(0.13, sigma_k, NONE),
        )
        assert result.height_difference.std_dev == pytest.approx(0.003808, abs=1e-5)
        assert result.refraction_cancellation == pytest.approx(0.0, abs=1e-12)

    def test_imbalanced_sights_keep_most_of_it(self):
        """The contrast that proves the previous test is measuring something."""
        backward, forward = self._pair(100.0, 900.0)
        tight = leapfrog_height_difference(
            backward, forward, refraction_coefficient=Quantity.from_std_dev(0.13, 0.05, NONE)
        )
        loose = leapfrog_height_difference(
            backward, forward, refraction_coefficient=Quantity.from_std_dev(0.13, 0.5, NONE)
        )
        assert loose.height_difference.std_dev > 5.0 * tight.height_difference.std_dev
        assert tight.refraction_cancellation > 0.9

    def test_the_cancellation_ratio_is_a_property_of_the_geometry_alone(self):
        """It depends on the two sight lengths and on nothing else -- not on the
        earth radius, not on how well k is known. That is what makes it
        actionable: the surveyor controls it by where they stand."""
        first = leapfrog_height_difference(
            *self._pair(300.0, 700.0),
            refraction_coefficient=Quantity.from_std_dev(0.13, 0.01, NONE),
        )
        second = leapfrog_height_difference(
            *self._pair(300.0, 700.0),
            refraction_coefficient=Quantity.from_std_dev(0.20, 2.0, NONE),
        )
        assert first.refraction_cancellation == pytest.approx(second.refraction_cancellation)

        expected = abs(700.0**2 - 300.0**2) / math.hypot(700.0**2, 300.0**2)
        assert first.refraction_cancellation == pytest.approx(expected, rel=1e-3)

    def test_an_imbalanced_pair_is_reported(self):
        result = leapfrog_height_difference(*self._pair(100.0, 900.0))
        assert "leapfrog_sights_imbalanced" in {f.code for f in result.findings}

    def test_a_balanced_pair_is_not_reported(self):
        result = leapfrog_height_difference(*self._pair(500.0, 505.0))
        assert not result.findings

    def test_the_imbalance_is_reported_signed(self):
        """Which sight is longer matters to the surveyor moving the tripod."""
        result = leapfrog_height_difference(*self._pair(100.0, 900.0))
        assert result.sight_imbalance > 0.0
        reversed_result = leapfrog_height_difference(*self._pair(900.0, 100.0))
        assert reversed_result.sight_imbalance < 0.0

    def test_balanced_sights_beat_imbalanced_ones_overall(self):
        balanced = leapfrog_height_difference(*self._pair(500.0, 500.0))
        imbalanced = leapfrog_height_difference(*self._pair(100.0, 900.0))
        assert balanced.height_difference.std_dev < imbalanced.height_difference.std_dev

    def test_a_wrong_unit_in_a_sight_is_refused(self):
        with pytest.raises(ValidationError) as caught:
            Sight("A", m(1.0), m(100.0), m(1.5))
        assert caught.value.code == "validation.sight_wrong_unit"
