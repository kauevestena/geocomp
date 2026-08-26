# SPDX-License-Identifier: GPL-2.0-or-later
"""Traverse, resection, intersection and radiation (specs/09 section 4).

The tests that carry the weight here are the ones with a **known truth**: a
figure is built from exact geometry, the observations are derived from it, and
the computation must return the geometry it started from. That catches a sign
error or a swapped easting and northing, which a self-consistency check cannot.
"""

from __future__ import annotations

import math

import pytest

from geocomp.core.errors import ComputationError, ValidationError
from geocomp.core.findings import Severity
from geocomp.core.techniques.total_station import (
    Leg,
    TraverseAdjustment,
    TraverseKind,
    adjust_traverse,
    forward_intersection,
    radiate,
    resection,
)
from geocomp.core.techniques.total_station.survey import _circumcircle
from geocomp.core.uncertainty import Quantity, Strategy, UncertaintyMode
from geocomp.core.units import Unit

METRE, RADIAN = Unit.METRE, Unit.RADIAN

#: A well-conditioned three-point figure, and a station comfortably inside it.
KNOWN = {"A": (0.0, 0.0), "B": (1000.0, 0.0), "C": (500.0, 900.0)}
STATION = (480.0, 300.0)
ORIENTATION = math.radians(37.0)


def m(value: float, sigma: float = 0.005) -> Quantity:
    return Quantity.from_std_dev(value, sigma, METRE)


def r(radians_value: float, sigma: float = 5e-6) -> Quantity:
    return Quantity.from_std_dev(radians_value, sigma, RADIAN)


def deg(value: float, sigma: float = 5e-6) -> Quantity:
    return r(math.radians(value), sigma)


def known_points(points=None) -> dict[str, tuple[Quantity, Quantity]]:
    return {
        name: (m(east, 0.0), m(north, 0.0))
        for name, (east, north) in (points or KNOWN).items()
    }


def directions_from(station: tuple[float, float], points=None) -> dict[str, Quantity]:
    """Exact reduced circle readings a station would observe."""
    return {
        name: r((math.atan2(east - station[0], north - station[1]) - ORIENTATION) % (2 * math.pi))
        for name, (east, north) in (points or KNOWN).items()
    }


class TestResection:
    def test_it_recovers_a_known_station(self):
        """The observations were derived from this position, so the computation
        must return it. Anything else is a sign or an axis error."""
        result = resection(known_points(), directions_from(STATION), approximate=(470.0, 290.0))
        assert result.position[0].value == pytest.approx(STATION[0], abs=1e-6)
        assert result.position[1].value == pytest.approx(STATION[1], abs=1e-6)

    def test_it_recovers_the_setup_orientation(self):
        """The third unknown, and the reason directions rather than azimuths are
        the input."""
        result = resection(known_points(), directions_from(STATION), approximate=(470.0, 290.0))
        assert result.orientation.value == pytest.approx(ORIENTATION, abs=1e-9)

    def test_it_converges_without_an_approximate_position(self):
        result = resection(known_points(), directions_from(STATION))
        assert result.position[0].value == pytest.approx(STATION[0], abs=1e-6)

    def test_the_result_carries_a_covariance_not_just_two_sigmas(self):
        result = resection(known_points(), directions_from(STATION), approximate=STATION)
        assert result.covariance.size == 2
        assert result.position[0].std_dev > 0.0
        assert result.covariance.matrix[0, 1] != 0.0

    def test_better_directions_give_a_better_position(self):
        precise = resection(
            known_points(),
            {k: r(v.value, 1e-6) for k, v in directions_from(STATION).items()},
            approximate=STATION,
        )
        vague = resection(
            known_points(),
            {k: r(v.value, 1e-4) for k, v in directions_from(STATION).items()},
            approximate=STATION,
        )
        assert vague.position[0].std_dev > precise.position[0].std_dev * 50

    def test_fewer_than_three_points_is_refused(self):
        """Two directions cannot fix a position and an orientation."""
        two = {k: KNOWN[k] for k in ("A", "B")}
        with pytest.raises(ValidationError) as caught:
            resection(known_points(two), directions_from(STATION, two))
        assert caught.value.code == "validation.resection_needs_three_points"

    def test_a_direction_to_an_unknown_point_is_refused(self):
        directions = directions_from(STATION)
        directions["D"] = deg(10.0)
        with pytest.raises(ValidationError) as caught:
            resection(known_points(), directions)
        assert caught.value.code == "validation.resection_direction_to_unknown_point"


class TestTheDangerCircle:
    """specs/09 section 4.2: detected and reported, never solved.

    Every point on the circle through three known points sees them in the same
    directions, so the three do not determine a position there. A number
    returned from that configuration looks exactly like a coordinate and is not
    one, which is why this refuses rather than reporting a large uncertainty.
    """

    @staticmethod
    def _on_the_circle(angle_degrees: float = 230.0) -> tuple[float, float]:
        circle = _circumcircle([KNOWN["A"], KNOWN["B"], KNOWN["C"]])
        assert circle is not None
        (centre_x, centre_y), radius = circle
        return (
            centre_x + radius * math.cos(math.radians(angle_degrees)),
            centre_y + radius * math.sin(math.radians(angle_degrees)),
        )

    def test_the_circumcircle_passes_through_all_three_points(self):
        """Guards the detector: a wrong circle would make the test below fire
        somewhere harmless and never where it matters."""
        circle = _circumcircle([KNOWN["A"], KNOWN["B"], KNOWN["C"]])
        assert circle is not None
        (centre_x, centre_y), radius = circle
        for east, north in KNOWN.values():
            assert math.hypot(east - centre_x, north - centre_y) == pytest.approx(radius)

    def test_a_station_on_the_circle_is_refused_by_name(self):
        station = self._on_the_circle()
        with pytest.raises(ComputationError) as caught:
            resection(known_points(), directions_from(station), approximate=station)
        assert caught.value.code == "computation.resection_danger_circle"
        assert "danger circle" in caught.value.context["expected"]

    @pytest.mark.parametrize("angle", [200.0, 230.0, 260.0, 320.0])
    def test_it_is_refused_anywhere_on_the_circle(self, angle):
        station = self._on_the_circle(angle)
        with pytest.raises(ComputationError):
            resection(known_points(), directions_from(station), approximate=station)

    def test_a_station_well_off_the_circle_is_solved_normally(self):
        """A detector that fired everywhere would make resection unusable."""
        result = resection(known_points(), directions_from(STATION), approximate=STATION)
        assert result.is_reliable
        assert not result.findings

    def test_collinear_known_points_are_refused_with_their_own_message(self):
        """Three points in a line define no circle at all, which is a different
        problem from lying on one and deserves a different message."""
        collinear = {"A": (0.0, 0.0), "B": (500.0, 0.0), "C": (1000.0, 0.0)}
        with pytest.raises(ComputationError) as caught:
            resection(
                known_points(collinear),
                directions_from((500.0, 400.0), collinear),
                approximate=(500.0, 400.0),
            )
        assert caught.value.code == "computation.resection_collinear_known_points"

    def test_the_check_also_fires_without_an_approximate_position(self):
        """The up-front check needs one; the mid-iteration check does not, and
        must produce the same named refusal rather than a singular matrix."""
        station = self._on_the_circle()
        with pytest.raises(ComputationError) as caught:
            resection(known_points(), directions_from(station))
        assert "danger" in caught.value.code or "indeterminate" in caught.value.code


class TestForwardIntersection:
    @staticmethod
    def _sightings(target: tuple[float, float], stations=("A", "B"), sigma: float = 5e-6):
        return {
            name: (
                (m(KNOWN[name][0], 0.0), m(KNOWN[name][1], 0.0)),
                r(
                    math.atan2(target[0] - KNOWN[name][0], target[1] - KNOWN[name][1]),
                    sigma,
                ),
            )
            for name in stations
        }

    def test_it_recovers_a_known_point_from_two_stations(self):
        result = forward_intersection("P", self._sightings(STATION))
        assert result.position[0].value == pytest.approx(STATION[0], abs=1e-6)
        assert result.position[1].value == pytest.approx(STATION[1], abs=1e-6)

    def test_a_third_station_improves_it(self):
        two = forward_intersection("P", self._sightings(STATION, ("A", "B")))
        three = forward_intersection("P", self._sightings(STATION, ("A", "B", "C")))
        assert three.position[0].value == pytest.approx(STATION[0], abs=1e-6)
        assert three.position[0].std_dev < two.position[0].std_dev

    def test_with_redundancy_there_are_residuals(self):
        result = forward_intersection("P", self._sightings(STATION, ("A", "B", "C")))
        assert set(result.residuals) == {"A", "B", "C"}

    def test_weak_geometry_is_reported_through_the_ellipse(self):
        """specs/09 section 4.3: near-parallel rays are reported rather than
        left for the user to discover."""
        weak = {
            "A": ((m(0.0, 0.0), m(0.0, 0.0)), r(math.atan2(0.0, 1000.0))),
            "B": ((m(10.0, 0.0), m(0.0, 0.0)), r(math.atan2(-10.0, 1000.0))),
        }
        result = forward_intersection("P", weak)
        codes = {f.code for f in result.findings}
        assert "weak_intersection_geometry" in codes

    def test_good_geometry_is_not_reported(self):
        result = forward_intersection("P", self._sightings(STATION))
        assert not result.findings

    def test_one_station_is_refused(self):
        with pytest.raises(ValidationError) as caught:
            forward_intersection("P", self._sightings(STATION, ("A",)))
        assert caught.value.code == "validation.intersection_needs_two_stations"

    def test_exactly_parallel_rays_are_refused_rather_than_returning_a_number(self):
        parallel = {
            "A": ((m(0.0, 0.0), m(0.0, 0.0)), r(0.0)),
            "B": ((m(100.0, 0.0), m(0.0, 0.0)), r(0.0)),
        }
        with pytest.raises(ComputationError) as caught:
            forward_intersection("P", parallel)
        assert caught.value.code == "computation.intersection_indeterminate"


class TestRadiation:
    @staticmethod
    def _radiate(correlation: float | None = 0.0):
        return radiate(
            "P",
            (m(100.0, 0.0), m(200.0, 0.0), m(50.0, 0.0)),
            r(0.0, 0.0),
            deg(45.0),
            deg(88.0),
            m(150.0, 0.003),
            m(1.500, 0.001),
            m(1.600, 0.001),
            correlation=correlation,
        )

    def test_the_coordinates_are_the_closed_form(self):
        result = self._radiate()
        horizontal = 150.0 * math.sin(math.radians(88.0))
        assert result.position[0].value == pytest.approx(
            100.0 + horizontal * math.sin(math.radians(45.0)), abs=1e-9
        )
        assert result.position[1].value == pytest.approx(
            200.0 + horizontal * math.cos(math.radians(45.0)), abs=1e-9
        )
        assert result.position[2].value == pytest.approx(
            50.0 + 150.0 * math.cos(math.radians(88.0)) + 1.5 - 1.6, abs=1e-9
        )

    def test_the_three_coordinates_are_strongly_correlated(self):
        """specs/09 section 4.6: they come from one pointing, and treating them
        as independent is wrong. This is the routine production case -- a detail
        survey radiates hundreds of points from one setup."""
        result = self._radiate()
        correlation = result.covariance.to_correlation()
        assert abs(correlation[0, 1]) > 0.5

    def test_the_covariance_is_the_result_not_an_extra(self):
        result = self._radiate()
        assert result.covariance.size == 3
        assert result.covariance.labels == ("easting", "northing", "up")

    def test_an_unstated_correlation_is_recorded_as_an_assumption(self):
        result = self._radiate(correlation=None)
        assert Strategy.INDEPENDENCE_ASSUMED in result.position[0].strategies
        assert result.position[0].mode is UncertaintyMode.APPROXIMATE

    def test_the_station_uncertainty_propagates_into_the_radiated_point(self):
        """A point radiated from a poorly known station cannot be better known
        than the station is."""
        vague_station = radiate(
            "P",
            (m(100.0, 0.05), m(200.0, 0.05), m(50.0, 0.05)),
            r(0.0, 0.0),
            deg(45.0),
            deg(88.0),
            m(150.0, 0.003),
            m(1.500, 0.001),
            m(1.600, 0.001),
            correlation=0.0,
        )
        assert vague_station.position[0].std_dev > self._radiate().position[0].std_dev
        assert vague_station.position[0].std_dev > 0.05


class TestTraverse:
    @staticmethod
    def _square(side: float = 100.0, angle_degrees: float = 90.0, distance_sigma: float = 0.003):
        return [
            Leg(origin, target, deg(angle_degrees), m(side, distance_sigma))
            for origin, target in [("1", "2"), ("2", "3"), ("3", "4"), ("4", "1")]
        ]

    def test_a_perfect_closed_traverse_has_no_misclosure(self):
        result = adjust_traverse(
            self._square(),
            (m(0.0, 0.0), m(0.0, 0.0)),
            deg(180.0),
            kind=TraverseKind.CLOSED,
            close_azimuth=deg(180.0),
        )
        assert result.linear_misclosure == pytest.approx(0.0, abs=1e-9)
        assert result.angular_misclosure == pytest.approx(0.0, abs=1e-12)

    def test_it_walks_the_figure_it_was_given(self):
        result = adjust_traverse(
            self._square(),
            (m(0.0, 0.0), m(0.0, 0.0)),
            deg(180.0),
            kind=TraverseKind.CLOSED,
            close_azimuth=deg(180.0),
        )
        corners = {name: (q[0].value, q[1].value) for name, q in result.coordinates.items()}
        assert corners["1"] == pytest.approx((0.0, 0.0), abs=1e-9)
        assert corners["2"] == pytest.approx((100.0, 0.0), abs=1e-9)
        assert corners["3"] == pytest.approx((100.0, 100.0), abs=1e-9)
        assert corners["4"] == pytest.approx((0.0, 100.0), abs=1e-9)

    def test_the_perimeter_carries_the_leg_uncertainties(self):
        """FR-200: a sum of measured distances is a measured length."""
        result = adjust_traverse(
            self._square(distance_sigma=0.003),
            (m(0.0, 0.0), m(0.0, 0.0)),
            deg(180.0),
            kind=TraverseKind.CLOSED,
            close_azimuth=deg(180.0),
        )
        assert result.perimeter.value == pytest.approx(400.0)
        assert result.perimeter.std_dev == pytest.approx(0.003 * 2.0, rel=1e-9)

    def test_a_misclosure_is_distributed_by_the_compass_rule(self):
        """Bowditch spreads the closing error proportionally to the distance
        travelled, so the last station takes all of it and the first none."""
        legs = self._square()
        legs[-1] = Leg("4", "1", deg(90.0), m(100.100, 0.003))
        result = adjust_traverse(
            legs,
            (m(0.0, 0.0), m(0.0, 0.0)),
            deg(180.0),
            kind=TraverseKind.CLOSED,
            close_azimuth=deg(180.0),
            method=TraverseAdjustment.COMPASS,
            relative_precision_limit=1.0,
        )
        assert result.linear_misclosure == pytest.approx(0.100, abs=1e-9)
        assert result.relative_precision == pytest.approx(400.1 / 0.100, rel=1e-6)
        # Station 1 is the start and is not moved; station 2 takes a quarter.
        assert result.coordinates["1"][0].value == pytest.approx(0.0, abs=1e-12)

    def test_the_transit_rule_gives_a_different_answer_on_the_same_data(self):
        """Which is the pedagogical point of offering both: the student sees
        that a classical rule is a choice of assumption, not a computation."""
        legs = self._square()
        legs[-1] = Leg("4", "1", deg(90.0), m(100.100, 0.003))
        arguments = {
            "legs": legs,
            "start": (m(0.0, 0.0), m(0.0, 0.0)),
            "start_azimuth": deg(180.0),
            "kind": TraverseKind.CLOSED,
            "close_azimuth": deg(180.0),
            "relative_precision_limit": 1.0,
        }
        compass = adjust_traverse(method=TraverseAdjustment.COMPASS, **arguments)
        transit = adjust_traverse(method=TraverseAdjustment.TRANSIT, **arguments)
        assert compass.coordinates["3"][1].value != pytest.approx(
            transit.coordinates["3"][1].value, abs=1e-6
        )

    def test_classical_results_are_labelled_approximate(self):
        """FR-203. A compass distribution is not least squares: it produces no
        residuals, no redundancy numbers and no rigorous covariance, and
        presenting its output as rigorous would misrepresent the survey."""
        result = adjust_traverse(
            self._square(),
            (m(0.0, 0.0), m(0.0, 0.0)),
            deg(180.0),
            kind=TraverseKind.CLOSED,
            close_azimuth=deg(180.0),
        )
        for easting, northing in result.coordinates.values():
            assert easting.mode is UncertaintyMode.APPROXIMATE
            assert northing.mode is UncertaintyMode.APPROXIMATE

    def test_a_poor_closure_is_reported_against_the_configured_limit(self):
        legs = self._square()
        legs[-1] = Leg("4", "1", deg(90.0), m(101.0, 0.003))
        result = adjust_traverse(
            legs,
            (m(0.0, 0.0), m(0.0, 0.0)),
            deg(180.0),
            kind=TraverseKind.CLOSED,
            close_azimuth=deg(180.0),
            relative_precision_limit=5000.0,
        )
        codes = {f.code for f in result.findings}
        assert "relative_precision_beyond_tolerance" in codes

    def test_an_angular_misclosure_beyond_tolerance_is_reported(self):
        legs = self._square(angle_degrees=90.0 + 1.0 / 60.0)
        result = adjust_traverse(
            legs,
            (m(0.0, 0.0), m(0.0, 0.0)),
            deg(180.0),
            kind=TraverseKind.CLOSED,
            close_azimuth=deg(180.0),
            relative_precision_limit=1.0,
        )
        codes = {f.code for f in result.findings}
        assert "angular_misclosure_beyond_tolerance" in codes

    def test_an_open_traverse_says_it_cannot_be_checked(self):
        """No misclosure exists, which is different from a misclosure of zero.
        A blunder anywhere in an open traverse is invisible."""
        result = adjust_traverse(
            self._square()[:2],
            (m(0.0, 0.0), m(0.0, 0.0)),
            deg(180.0),
            kind=TraverseKind.OPEN,
        )
        assert result.linear_misclosure is None
        assert result.angular_misclosure is None
        assert result.relative_precision is None
        assert not result.is_checkable
        assert "open_traverse_unchecked" in {f.code for f in result.findings}

    def test_a_connected_traverse_needs_its_closing_point(self):
        with pytest.raises(ValidationError) as caught:
            adjust_traverse(
                self._square(),
                (m(0.0, 0.0), m(0.0, 0.0)),
                deg(180.0),
                kind=TraverseKind.CONNECTED,
            )
        assert caught.value.code == "validation.connected_traverse_without_closing_point"

    def test_a_traverse_with_no_legs_is_refused(self):
        with pytest.raises(ValidationError) as caught:
            adjust_traverse([], (m(0.0, 0.0), m(0.0, 0.0)), deg(180.0))
        assert caught.value.code == "validation.traverse_without_legs"

    def test_a_leg_with_a_wrong_unit_is_refused(self):
        with pytest.raises(ValidationError) as caught:
            Leg("1", "2", m(90.0), m(100.0))
        assert caught.value.code == "validation.leg_angle_wrong_unit"

    def test_leaving_the_misclosure_undistributed_is_an_option(self):
        """Reporting a misclosure without absorbing it is a legitimate choice --
        it is what a check measurement is for."""
        legs = self._square()
        legs[-1] = Leg("4", "1", deg(90.0), m(100.100, 0.003))
        result = adjust_traverse(
            legs,
            (m(0.0, 0.0), m(0.0, 0.0)),
            deg(180.0),
            kind=TraverseKind.CLOSED,
            close_azimuth=deg(180.0),
            method=TraverseAdjustment.NONE,
            relative_precision_limit=1.0,
        )
        assert result.linear_misclosure == pytest.approx(0.100, abs=1e-9)
        assert result.coordinates["4"][0].value == pytest.approx(0.0, abs=1e-9)


class TestSeverityIsUsedConsistently:
    def test_traverse_tolerance_breaches_are_warnings_not_blocks(self):
        """The result stands and is reportable; whether it is acceptable is the
        surveyor's call against their specification, not GeoComp's."""
        legs = TestTraverse._square()
        legs[-1] = Leg("4", "1", deg(90.0), m(101.0, 0.003))
        result = adjust_traverse(
            legs,
            (m(0.0, 0.0), m(0.0, 0.0)),
            deg(180.0),
            kind=TraverseKind.CLOSED,
            close_azimuth=deg(180.0),
        )
        assert result.findings
        assert all(f.severity is not Severity.BLOCKING for f in result.findings)
