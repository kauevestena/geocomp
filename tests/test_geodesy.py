# SPDX-License-Identifier: GPL-2.0-or-later
"""Ellipsoidal geometry (``specs/07`` section 4.4, ``specs/09`` section 2.6).

Three independent kinds of check, because a coordinate conversion that is wrong
by a systematic amount still round-trips perfectly:

1. **Published defining constants.** GRS80's semi-minor axis and *e²* are
   printed in the standard; deriving them from *a* and 1/*f* must reproduce them.
2. **DynAdjust's own numbers.** ``tests/data/dynadjust/output/sample.xyz`` prints
   eleven stations as both geodetic and geocentric coordinates, computed by
   DynAdjust 1.4.0 on GDA2020. That is an independent implementation, already in
   the repository, and it is the check that would catch a formulation error the
   round trip cannot see.
3. **Analytic Jacobians against numerical ones**, as ``specs/05`` section 3
   requires of every propagation: a sign error here produces a plausible wrong
   variance and raises nothing.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from geocomp.core.errors import ComputationError, ValidationError
from geocomp.core.geodesy import (
    ELLIPSOIDS,
    Ellipsoid,
    cartesian_to_geodetic,
    cartesian_to_geodetic_quantities,
    ellipsoid_by_name,
    geodetic_to_cartesian,
    geodetic_to_cartesian_jacobian,
    geodetic_to_cartesian_quantities,
)
from geocomp.core.uncertainty import Quantity
from geocomp.core.units import Unit
from geocomp.engines.dynadjust.formats import hp_to_radians

from .conftest import REPO_ROOT

GRS80 = ELLIPSOIDS["GRS80"]

#: A spread that exercises every branch: the equator, both hemispheres, a pole,
#: the antimeridian, a height below the ellipsoid, and Curitiba.
POINTS = [
    (0.0, 0.0, 0.0),
    (-25.4284, -49.2733, 934.6),
    (52.0, 5.0, 73.0),
    (-33.8688, 151.2093, 58.0),
    (89.9, 10.0, 100.0),
    (-90.0, 0.0, 5.0),
    (45.0, 180.0, -1000.0),
    (-0.0001, -179.9999, 12.5),
]


class TestEllipsoidConstants:
    """The two defining numbers are stored; everything else is derived.

    Carrying a table of pre-rounded derived values is how an ellipsoid comes to
    disagree with itself in the eleventh digit, so the derivations are checked
    against what the standards print.
    """

    def test_grs80_semi_minor_axis(self):
        """IUGG 1980 publishes b = 6356752.3141 m."""
        assert GRS80.semi_minor_axis == pytest.approx(6356752.3141, abs=1e-4)

    def test_grs80_eccentricity_squared(self):
        """Published as e^2 = 0.00669438002290."""
        assert GRS80.eccentricity_squared == pytest.approx(0.00669438002290, abs=1e-14)

    def test_grs80_polar_radius_of_curvature(self):
        """c = a / (1 - f) = 6399593.6259 m, which is M at the pole."""
        assert GRS80.meridian_radius(math.pi / 2) == pytest.approx(6399593.6259, abs=1e-4)

    def test_the_prime_vertical_radius_at_the_equator_is_the_semi_major_axis(self):
        assert GRS80.prime_vertical_radius(0.0) == GRS80.semi_major_axis

    def test_wgs84_differs_from_grs80_only_in_flattening(self):
        """A tenth of a millimetre in b, and it is not a rounding error.

        The two ellipsoids are genuinely different by this much, so code that
        treats them as interchangeable is right about the map and wrong about
        the millimetre.
        """
        wgs84 = ELLIPSOIDS["WGS84"]
        assert wgs84.semi_major_axis == GRS80.semi_major_axis
        difference = abs(wgs84.semi_minor_axis - GRS80.semi_minor_axis)
        assert 1e-5 < difference < 1e-3

    def test_e_squared_avoids_the_cancelling_form(self):
        """``2f - f^2`` and ``1 - b^2/a^2`` are equal on paper, not in floats."""
        cancelling = 1.0 - (GRS80.semi_minor_axis / GRS80.semi_major_axis) ** 2
        assert GRS80.eccentricity_squared == pytest.approx(cancelling, rel=1e-11)
        assert GRS80.eccentricity_squared != cancelling

    def test_a_sphere_is_expressible(self):
        sphere = Ellipsoid("sphere", 6371000.0, math.inf)
        assert sphere.flattening == 0.0
        assert sphere.eccentricity_squared == 0.0
        assert sphere.semi_minor_axis == sphere.semi_major_axis

    @pytest.mark.parametrize("written", ["GRS80", "grs 80", "GRS-80", "grs_80"])
    def test_the_name_survives_the_ways_people_write_it(self, written):
        assert ellipsoid_by_name(written) is GRS80

    def test_an_unknown_ellipsoid_is_refused_by_name(self):
        with pytest.raises(ValidationError) as caught:
            ellipsoid_by_name("Krassowsky 1940")
        assert caught.value.code == "validation.ellipsoid_unknown"
        assert "GRS80" in caught.value.context["expected"]

    def test_an_impossible_flattening_is_refused(self):
        with pytest.raises(ValidationError):
            Ellipsoid("nonsense", 6378137.0, 0.0)


class TestAgainstDynAdjust:
    """The independent check, on eleven stations DynAdjust converted itself.

    ``sample.xyz`` is a committed fixture with coordinate types ``PLHhXYZ``, so
    each station appears as latitude, longitude and ellipsoidal height *and* as
    geocentric X, Y, Z, both written by DynAdjust 1.4.0 on GDA2020 -- which is
    realised on GRS80.
    """

    #: 0.25 mm, and the number is not arbitrary. The file prints latitude in HP
    #: notation to five decimals of a second: one unit in the last place is
    #: 1e-5 arcsec, which is 0.31 mm on the ground, so a correctly rounded value
    #: is already up to 0.155 mm from the truth. XYZ printed to four decimals
    #: adds 0.05 mm. The observed disagreement is 0.153 mm -- the limit of what
    #: the file can express, not a difference in formulation.
    TOLERANCE_METRES = 2.5e-4

    @staticmethod
    def stations():
        path = REPO_ROOT / "tests" / "data" / "dynadjust" / "output" / "sample.xyz"
        rows = []
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            tokens = line.split()
            if len(tokens) < 9 or tokens[1] != "FFF":
                continue
            rows.append(
                (
                    tokens[0],
                    hp_to_radians(tokens[2]),
                    hp_to_radians(tokens[3]),
                    float(tokens[5]),
                    (float(tokens[6]), float(tokens[7]), float(tokens[8])),
                )
            )
        return rows

    def test_the_fixture_still_has_both_coordinate_types(self):
        """If it stops carrying XYZ, this whole class silently tests nothing."""
        rows = self.stations()
        assert len(rows) == 11

    def test_geodetic_to_cartesian_matches(self):
        worst = 0.0
        for name, latitude, longitude, height, expected in self.stations():
            computed = geodetic_to_cartesian(latitude, longitude, height, GRS80)
            for got, want in zip(computed, expected, strict=True):
                worst = max(worst, abs(got - want))
                assert got == pytest.approx(want, abs=self.TOLERANCE_METRES), name
        assert worst < self.TOLERANCE_METRES

    def test_cartesian_to_geodetic_matches(self):
        for name, latitude, longitude, height, (x, y, z) in self.stations():
            got_lat, got_lon, got_h = cartesian_to_geodetic(x, y, z, GRS80)
            # Compare angles as ground distance, which is what the tolerance means.
            northing = abs(got_lat - latitude) * GRS80.meridian_radius(latitude)
            easting = (
                abs(got_lon - longitude)
                * GRS80.prime_vertical_radius(latitude)
                * math.cos(latitude)
            )
            assert northing == pytest.approx(0.0, abs=self.TOLERANCE_METRES), name
            assert easting == pytest.approx(0.0, abs=self.TOLERANCE_METRES), name
            assert got_h == pytest.approx(height, abs=self.TOLERANCE_METRES), name


class TestRoundTrip:
    """Necessary but not sufficient -- which is why it is not the only check.

    A shared sign error survives a round trip untouched. These pin the *other*
    property: that the inverse is exact rather than approximate, so it can be
    used to check something else.
    """

    @pytest.mark.parametrize("degrees_latitude,degrees_longitude,height", POINTS)
    def test_geodetic_survives_a_round_trip(self, degrees_latitude, degrees_longitude, height):
        latitude, longitude = math.radians(degrees_latitude), math.radians(degrees_longitude)
        x, y, z = geodetic_to_cartesian(latitude, longitude, height, GRS80)
        back_lat, back_lon, back_h = cartesian_to_geodetic(x, y, z, GRS80)

        assert back_lat * GRS80.semi_major_axis == pytest.approx(
            latitude * GRS80.semi_major_axis, abs=1e-6
        )
        assert back_h == pytest.approx(height, abs=1e-6)
        if abs(degrees_latitude) < 89.0:  # longitude is undefined at a pole
            assert math.cos(back_lon) == pytest.approx(math.cos(longitude), abs=1e-12)
            assert math.sin(back_lon) == pytest.approx(math.sin(longitude), abs=1e-12)

    def test_the_pole_is_handled_rather_than_divided_by(self):
        """``h = p / cos(phi)`` is a division by zero exactly at the pole."""
        x, y, z = geodetic_to_cartesian(math.pi / 2, 0.0, 100.0, GRS80)
        latitude, _, height = cartesian_to_geodetic(x, y, z, GRS80)
        assert latitude == pytest.approx(math.pi / 2)
        assert height == pytest.approx(100.0, abs=1e-6)

    def test_a_point_on_the_axis_gives_a_defined_longitude(self):
        latitude, longitude, height = cartesian_to_geodetic(
            0.0, 0.0, GRS80.semi_minor_axis + 42.0, GRS80
        )
        assert latitude == pytest.approx(math.pi / 2)
        assert longitude == 0.0
        assert height == pytest.approx(42.0)


class TestJacobians:
    """specs/05 section 3: every propagation's Jacobian is checked numerically."""

    @staticmethod
    def numerical(latitude, longitude, height, ellipsoid):
        columns = []
        point = [latitude, longitude, height]
        for index in range(3):
            step = 1e-7 if index < 2 else 1e-2
            forward, backward = list(point), list(point)
            forward[index] += step
            backward[index] -= step
            ahead = np.array(geodetic_to_cartesian(*forward, ellipsoid))
            behind = np.array(geodetic_to_cartesian(*backward, ellipsoid))
            columns.append((ahead - behind) / (2 * step))
        return np.column_stack(columns)

    @pytest.mark.parametrize("degrees_latitude,degrees_longitude,height", POINTS[:5])
    def test_the_analytic_jacobian_matches(self, degrees_latitude, degrees_longitude, height):
        latitude, longitude = math.radians(degrees_latitude), math.radians(degrees_longitude)
        analytic = geodetic_to_cartesian_jacobian(latitude, longitude, height, GRS80)
        numeric = self.numerical(latitude, longitude, height, GRS80)
        scale = max(float(np.max(np.abs(analytic))), 1.0)
        assert float(np.max(np.abs(analytic - numeric))) / scale < 1e-8

    def test_the_latitude_column_uses_the_meridian_radius_not_the_prime_vertical(self):
        """The trap this Jacobian exists to avoid, asserted directly.

        ``d/dphi[(N + h) cos(phi)]`` is ``-(M + h) sin(phi)``: *N* varies with
        latitude too. Substituting *N* for *M* is a 0.3 percent error in the
        propagated variance at mid-latitudes -- small enough to look right.
        """
        latitude, longitude, height = math.radians(45.0), 0.0, 0.0
        analytic = geodetic_to_cartesian_jacobian(latitude, longitude, height, GRS80)

        with_m = -(GRS80.meridian_radius(latitude) + height) * math.sin(latitude)
        with_n = -(GRS80.prime_vertical_radius(latitude) + height) * math.sin(latitude)
        assert analytic[0, 0] == pytest.approx(with_m)
        assert analytic[0, 0] != pytest.approx(with_n, rel=1e-4)


class TestPropagation:
    def test_a_position_arrives_with_its_uncertainty_and_leaves_with_it(self):
        latitude = Quantity.from_std_dev(math.radians(-25.4284), 1e-8, Unit.RADIAN)
        longitude = Quantity.from_std_dev(math.radians(-49.2733), 1e-8, Unit.RADIAN)
        height = Quantity.from_std_dev(934.6, 0.02, Unit.METRE)

        x, y, z = geodetic_to_cartesian_quantities(latitude, longitude, height, GRS80)

        for component in (x, y, z):
            assert component.unit is Unit.METRE
            assert component.std_dev > 0.0
        # 1e-8 rad is 64 mm on the ground, so the horizontal components dominate
        # the 20 mm height: a propagated sigma near 20 mm would mean the angular
        # part was dropped.
        assert max(component.std_dev for component in (x, y, z)) > 0.03

    def test_the_inverse_propagates_back(self):
        x = Quantity.from_std_dev(-4251956.4559, 0.005, Unit.METRE)
        y = Quantity.from_std_dev(2869868.5766, 0.005, Unit.METRE)
        z = Quantity.from_std_dev(-3777753.7504, 0.005, Unit.METRE)

        latitude, longitude, height = cartesian_to_geodetic_quantities(x, y, z, GRS80)

        assert latitude.unit is Unit.RADIAN
        assert longitude.unit is Unit.RADIAN
        assert height.unit is Unit.METRE
        # 5 mm of cartesian uncertainty is about 5 mm on the ground, so the
        # angular sigma should be about 5 mm / a.
        assert latitude.std_dev * GRS80.semi_major_axis == pytest.approx(0.005, rel=0.5)

    def test_a_latitude_that_is_not_an_angle_is_refused(self):
        """The model carries angles in radians only (``core/units.py``).

        The guard is not pedantry about a label: -25.4 is a plausible latitude
        in degrees and a point 25 radians round the Earth, and the second one
        converts without complaint into a coordinate nobody would question.
        """
        with pytest.raises(ComputationError) as caught:
            geodetic_to_cartesian_quantities(
                Quantity.exact(-25.4284, Unit.DIMENSIONLESS),
                Quantity.exact(-49.2733, Unit.RADIAN),
                Quantity.exact(934.6, Unit.METRE),
                GRS80,
            )
        assert caught.value.code == "computation.geodetic_angle_wrong_unit"

    def test_a_height_that_is_not_a_length_is_refused(self):
        with pytest.raises(ComputationError) as caught:
            geodetic_to_cartesian_quantities(
                Quantity.exact(0.0, Unit.RADIAN),
                Quantity.exact(0.0, Unit.RADIAN),
                Quantity.exact(934.6, Unit.DIMENSIONLESS),
                GRS80,
            )
        assert caught.value.code == "computation.geodetic_length_wrong_unit"

    def test_a_cartesian_component_that_is_not_a_length_is_refused(self):
        with pytest.raises(ComputationError) as caught:
            cartesian_to_geodetic_quantities(
                Quantity.exact(-4251956.4559, Unit.METRE),
                Quantity.exact(2869868.5766, Unit.DIMENSIONLESS),
                Quantity.exact(-3777753.7504, Unit.METRE),
                GRS80,
            )
        assert caught.value.code == "computation.geodetic_length_wrong_unit"
