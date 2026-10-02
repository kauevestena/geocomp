# SPDX-License-Identifier: GPL-2.0-or-later
"""Class bounds and the MDB displacement behind the thematic maps (FR-902; phase P12b)."""

from __future__ import annotations

import math

import numpy as np
import pytest

from geocomp.core.units import Unit
from geocomp.core.visualization.classes import fitted_bounds, mdb_displacement


class TestFittedBounds:
    def test_four_classes_are_the_quartiles(self):
        values = [float(v) for v in range(1, 101)]
        bounds = fitted_bounds(values, 4)
        assert bounds == pytest.approx(tuple(np.quantile(values, [0, 0.25, 0.5, 0.75, 1.0])))

    def test_every_value_falls_in_a_class(self):
        values = [0.0031, 0.0007, 0.012, 0.0049, 0.0018]
        bounds = fitted_bounds(values, 4)
        assert bounds[0] == min(values) and bounds[-1] == max(values)

    def test_missing_and_non_finite_values_are_not_classified(self):
        """An uncheckable observation's MDB is None, and has its own class in
        the style; it must not drag a bound to infinity."""
        assert fitted_bounds([1.0, None, math.inf, 2.0, math.nan, 3.0], 2) == (1.0, 2.0, 3.0)

    def test_fewer_levels_than_classes_gives_fewer_classes(self):
        """Two classes with the same bounds would be one class drawn twice."""
        bounds = fitted_bounds([1.0, 1.0, 1.0, 2.0], 4)
        assert len(bounds) == 3
        assert list(bounds) == sorted(set(bounds))
        assert (bounds[0], bounds[-1]) == (1.0, 2.0)

    def test_one_level_is_one_class_of_zero_width(self):
        assert fitted_bounds([5.0, 5.0], 4) == (5.0, 5.0)

    def test_nothing_to_classify_is_no_classes(self):
        assert fitted_bounds([None, math.nan], 4) == ()
        assert fitted_bounds([], 4) == ()


class TestMdbAsADisplacement:
    def test_a_lengths_mdb_already_is_one(self):
        assert mdb_displacement(0.004, Unit.METRE, 250.0) == 0.004

    def test_an_angles_mdb_is_the_sideways_shift_at_its_sight(self):
        """Two arcseconds over 500 m: about 4.8 mm sideways at the target."""
        mdb = math.radians(2.0 / 3600.0)
        assert mdb_displacement(mdb, Unit.RADIAN, 500.0) == pytest.approx(mdb * 500.0)
        assert mdb_displacement(mdb, Unit.RADIAN, 500.0) == pytest.approx(0.004848, abs=1e-6)

    def test_a_direction_and_a_distance_now_share_a_scale(self):
        """The reason the field exists: on raw values the 2-arcsecond MDB
        (1e-5 rad) would rank below the 1 mm one."""
        direction = mdb_displacement(math.radians(2.0 / 3600.0), Unit.RADIAN, 500.0)
        distance = mdb_displacement(0.001, Unit.METRE, 500.0)
        assert direction > distance

    def test_no_displacement_where_there_is_none(self):
        assert mdb_displacement(None, Unit.METRE, 10.0) is None
        assert mdb_displacement(1.0e-7, Unit.ACCELERATION, 10.0) is None
        assert mdb_displacement(1.0e-5, Unit.RADIAN, None) is None
        assert mdb_displacement(1.0e-5, Unit.RADIAN, 0.0) is None
