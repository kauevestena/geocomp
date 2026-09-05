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
from geocomp.core.geodesy.projection import (
    inverse_transverse_mercator,
    point_scale_factor,
    transverse_mercator,
    utm_parameters,
    utm_zone,
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


class TestTransverseMercator:
    """The inverse projection ``specs/07`` section 4.4 names as missing.

    Validated against an arbiter rather than against another series: the
    meridian arc is integrated numerically, so nothing about Kruger's expansion
    is assumed in checking Kruger's expansion. That matters here, because the
    comparison with DynAdjust does **not** agree to the printing precision and
    the quadrature is what says which implementation is right.
    """

    PARAMETERS = utm_parameters(55, southern_hemisphere=True, ellipsoid=GRS80)

    @staticmethod
    def meridian_arc(latitude: float, ellipsoid=GRS80, order: int = 64) -> float:
        """The arc from the equator, by Gauss-Legendre on M(phi).

        NumPy only. SciPy is optional (ADR-0008) and a reference value that
        needs it would not be checked in the environment CI actually runs.
        """
        nodes, weights = np.polynomial.legendre.leggauss(order)
        half = latitude / 2.0
        return float(
            half
            * np.sum(
                weights
                * np.array([ellipsoid.meridian_radius(half * node + half) for node in nodes])
            )
        )

    @pytest.mark.parametrize("degrees", [-84.0, -45.0, -36.5, -20.0, 0.0, 12.5, 60.0, 84.0])
    def test_the_meridian_arc_matches_numerical_quadrature(self, degrees):
        """Sub-micrometre, over the whole range of latitudes."""
        latitude = math.radians(degrees)
        _, northing = transverse_mercator(latitude, self.PARAMETERS.central_meridian,
                                          self.PARAMETERS)
        arc = (northing - self.PARAMETERS.false_northing) / self.PARAMETERS.scale_factor
        assert arc == pytest.approx(self.meridian_arc(latitude), abs=1e-6)

    def test_the_central_meridian_lands_on_the_false_easting(self):
        easting, _ = transverse_mercator(
            math.radians(-36.5), self.PARAMETERS.central_meridian, self.PARAMETERS
        )
        assert easting == pytest.approx(500000.0, abs=1e-9)

    def test_the_scale_factor_on_the_central_meridian_is_k0(self):
        k = point_scale_factor(
            math.radians(-36.5), self.PARAMETERS.central_meridian, self.PARAMETERS
        )
        assert k == pytest.approx(0.9996, abs=1e-8)

    def test_the_scale_factor_grows_away_from_the_central_meridian(self):
        near = point_scale_factor(
            math.radians(-36.5), self.PARAMETERS.central_meridian, self.PARAMETERS
        )
        far = point_scale_factor(
            math.radians(-36.5), self.PARAMETERS.central_meridian + math.radians(2.8),
            self.PARAMETERS,
        )
        assert far > near
        assert far == pytest.approx(1.0003, abs=1e-4)  # the usual value at a zone edge

    @pytest.mark.parametrize("degrees_latitude", [-45.0, -36.5, -8.0, 0.0, 20.0, 60.0])
    @pytest.mark.parametrize("offset", [-2.9, -1.0, 0.0, 1.5, 2.9])
    def test_the_projection_round_trips(self, degrees_latitude, offset):
        latitude = math.radians(degrees_latitude)
        longitude = self.PARAMETERS.central_meridian + math.radians(offset)
        easting, northing = transverse_mercator(latitude, longitude, self.PARAMETERS)
        back_lat, back_lon = inverse_transverse_mercator(easting, northing, self.PARAMETERS)

        assert back_lat * GRS80.semi_major_axis == pytest.approx(
            latitude * GRS80.semi_major_axis, abs=1e-6
        )
        assert back_lon * GRS80.semi_major_axis == pytest.approx(
            longitude * GRS80.semi_major_axis, abs=1e-6
        )

    def test_the_inverse_series_is_not_the_forward_one(self):
        """h2 is 13/48 n^2 and h2' is 1/48 n^2, and the round trip is the proof.

        Reusing one set of coefficients for both directions leaves a round trip
        that closes to metres rather than micrometres -- so this asserts the
        round trip closes far tighter than that could.
        """
        latitude = math.radians(-45.0)
        longitude = self.PARAMETERS.central_meridian + math.radians(2.9)
        easting, northing = transverse_mercator(latitude, longitude, self.PARAMETERS)
        back = inverse_transverse_mercator(easting, northing, self.PARAMETERS)
        assert abs(back[0] - latitude) * GRS80.semi_major_axis < 1e-6

    def test_a_point_outside_the_domain_is_refused(self):
        with pytest.raises(ComputationError) as caught:
            transverse_mercator(0.0, self.PARAMETERS.central_meridian + math.radians(45.0),
                                self.PARAMETERS)
        assert caught.value.code == "computation.projection_outside_domain"

    @pytest.mark.parametrize(
        "degrees,zone",
        [(-180.0, 1), (-177.0, 1), (-174.1, 1), (-173.9, 2), (0.0, 31), (3.0, 31), (146.0, 55),
         (147.0, 55), (179.9, 60), (180.0, 1), (-183.0, 60)],
    )
    def test_the_utm_zone(self, degrees, zone):
        assert utm_zone(math.radians(degrees)) == zone

    def test_an_impossible_zone_is_refused(self):
        with pytest.raises(ValidationError) as caught:
            utm_parameters(0, southern_hemisphere=True)
        assert caught.value.code == "validation.utm_zone_out_of_range"


class TestAgainstDynAdjustsProjection:
    """DynAdjust's own UTM, and the sub-millimetre it does not agree on.

    ``grid.xyz`` is fifteen stations on **exact whole arcseconds** -- values HP
    notation represents without rounding -- all constrained, so DynAdjust's
    output is a pure coordinate conversion of the input rather than an
    adjustment. Eastings printed to five decimals. There is essentially no
    quantisation in this comparison, which is what makes the residual
    meaningful.

    **Easting agrees to 0.005 mm. Northing does not**, by an amount that grows
    with latitude and is independent of longitude: 0.004 mm at 8 degrees,
    0.085 mm at 36.5, 0.253 mm at 45. That signature is a meridian-arc
    difference, and quadrature says whose:
    ``test_the_meridian_arc_matches_numerical_quadrature`` puts GeoComp within a
    micrometre of the integral, so the difference is DynAdjust's truncation.
    Recorded in ``specs/07-engine-dynadjust.md`` section 4.5, because a
    cross-validation that expects exact agreement in northing will keep
    rediscovering it.
    """

    PARAMETERS = utm_parameters(55, southern_hemisphere=True, ellipsoid=GRS80)

    #: Whole arcseconds, matching grid-stn.xml. Kept here rather than parsed
    #: from the XML so the test states its own inputs.
    LATITUDES = ((-45, 0, 0), (-36, 30, 0), (-20, 15, 30), (-8, 0, 45), (0, 0, 0))
    LONGITUDES = ((144, 30, 0), (147, 0, 0), (149, 45, 15))

    #: 0.3 mm: DynAdjust's meridian-arc truncation at 45 degrees, plus the
    #: printing half-ulp. Not a tolerance on GeoComp's accuracy -- the
    #: quadrature test above bounds that at a micrometre.
    TOLERANCE_METRES = 3e-4

    @staticmethod
    def radians(degrees, minutes, seconds):
        sign = -1.0 if degrees < 0 else 1.0
        return sign * math.radians(abs(degrees) + minutes / 60.0 + seconds / 3600.0)

    @classmethod
    def expected(cls):
        path = REPO_ROOT / "tests" / "data" / "dynadjust" / "output" / "grid.xyz"
        rows = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            tokens = line.split()
            if len(tokens) >= 5 and tokens[0].startswith("P") and tokens[1] == "FFF":
                rows[tokens[0]] = (float(tokens[2]), float(tokens[3]), int(tokens[4]))
        return rows

    def points(self):
        for index, (latitude, longitude) in enumerate(
            (lat, lon) for lat in self.LATITUDES for lon in self.LONGITUDES
        ):
            yield f"P{index:02d}", self.radians(*latitude), self.radians(*longitude)

    def test_the_fixture_covers_what_it_claims_to(self):
        assert len(self.expected()) == 15

    def test_the_easting_agrees_to_the_printed_precision(self):
        """No truncation difference here: DynAdjust's easting is GeoComp's."""
        expected = self.expected()
        for name, latitude, longitude in self.points():
            easting, _ = transverse_mercator(latitude, longitude, self.PARAMETERS)
            assert easting == pytest.approx(expected[name][0], abs=1e-5), name

    def test_the_northing_agrees_to_dynadjusts_truncation(self):
        expected = self.expected()
        for name, latitude, longitude in self.points():
            _, northing = transverse_mercator(latitude, longitude, self.PARAMETERS)
            assert northing == pytest.approx(expected[name][1], abs=self.TOLERANCE_METRES), name

    def test_the_northing_difference_is_the_meridian_arc_and_nothing_else(self):
        """The claim in this class's docstring, asserted rather than asserted at.

        If the difference were in the projection proper it would vary with
        longitude. It does not: at one latitude, all three longitudes differ
        from DynAdjust by the same amount to within the printing precision.
        """
        expected = self.expected()
        for row, latitude_parts in enumerate(self.LATITUDES):
            latitude = self.radians(*latitude_parts)
            differences = []
            for column, longitude_parts in enumerate(self.LONGITUDES):
                longitude = self.radians(*longitude_parts)
                _, northing = transverse_mercator(latitude, longitude, self.PARAMETERS)
                differences.append(northing - expected[f"P{row * 3 + column:02d}"][1])
            assert max(differences) - min(differences) < 2e-5, latitude_parts

    def test_the_zone_agrees(self):
        expected = self.expected()
        for name, _, longitude in self.points():
            assert utm_zone(longitude) == expected[name][2], name
