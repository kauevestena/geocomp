# SPDX-License-Identifier: GPL-2.0-or-later
"""The synthetic survey, checked against the geometry it was generated from.

``tests/synthetic.py`` is the fixture the Processing algorithms for traverse,
resection, intersection, radiation and trigonometric levelling are tested on,
and those tests only run where QGIS does. A fixture nobody has verified would
turn a CI failure into a guess about whose fault it is, so this module verifies
it here, without QGIS: every core routine is asked to recover the coordinates
the observations were computed from.

That makes these tests the strongest kind available for these routines. The
expected values are not previous outputs; they are the survey itself.
"""

from __future__ import annotations

import math

import pytest

from geocomp.core.errors import ComputationError
from geocomp.core.techniques.total_station.levelling import (
    Sight,
    leapfrog_height_difference,
    radial_height_difference,
)
from geocomp.core.techniques.total_station.survey import (
    Leg,
    TraverseAdjustment,
    TraverseKind,
    adjust_traverse,
    forward_intersection,
    radiate,
    resection,
)
from geocomp.core.uncertainty import Quantity
from geocomp.core.units import Unit
from tests import synthetic as syn

ARCSECOND = math.radians(1.0 / 3600.0)


def _metres(value: float, sigma: float = syn.SIGMA_DISTANCE) -> Quantity:
    return Quantity.from_std_dev(value, sigma, Unit.METRE)


def _radians(value: float, sigma: float = syn.SIGMA_DIRECTION) -> Quantity:
    return Quantity.from_std_dev(value, sigma, Unit.RADIAN)


class TestTheFixtureItself:
    def test_the_circle_readings_recover_their_azimuths(self):
        """The generated reading is the azimuth less the setup's orientation.

        Every algorithm in the group relies on that, and the orientations here
        are deliberately non-zero so that an implementation which assumed the
        circle pointed north would fail rather than pass.
        """
        document = syn.reductions_document()
        for setup in document["setups"]:
            station = setup["station"]
            for pointing in setup["pointings"]:
                recovered = (
                    pointing["horizontal"]["value"] + syn.ORIENTATIONS[station]
                ) % math.tau
                assert recovered == pytest.approx(
                    syn.azimuth(station, pointing["target"]), abs=1e-12
                )

    def test_the_slope_distance_and_zenith_agree_with_the_plane_reduction(self):
        for station, targets in syn.SETUPS.items():
            for target in targets:
                slope = syn.slope_distance(station, target)
                z = syn.zenith(station, target)
                assert slope * math.sin(z) == pytest.approx(
                    syn.horizontal_distance(station, target), abs=1e-9
                )
                assert slope * math.cos(z) == pytest.approx(
                    syn.height_difference(station, target), abs=1e-9
                )

    def test_the_leap_frog_station_sights_are_exactly_balanced(self):
        """Refraction cancels in proportion to how equal the two sights are, so
        the fixture places one instrument station where they are equal exactly.
        The leap-frog test below has nothing to tolerate as a result."""
        assert syn.horizontal_distance("L", "A") == pytest.approx(
            syn.horizontal_distance("L", "D"), abs=1e-9
        )

    def test_every_setup_that_a_route_station_needs_exists(self):
        for index in range(len(syn.ROUTE) - 1):
            occupied = syn.ROUTE[index]
            backsight = syn.BACKSIGHT if index == 0 else syn.ROUTE[index - 1]
            foresight = syn.ROUTE[index + 1]
            sighted = syn.SETUPS[occupied]
            assert backsight in sighted and foresight in sighted


class TestTheTraverseCloses:
    """A traverse computed from exact observations of a closed loop must close."""

    @pytest.fixture
    def legs(self) -> list[Leg]:
        built = []
        for index in range(len(syn.ROUTE) - 1):
            occupied = syn.ROUTE[index]
            backsight = syn.BACKSIGHT if index == 0 else syn.ROUTE[index - 1]
            foresight = syn.ROUTE[index + 1]
            built.append(
                Leg(
                    origin=occupied,
                    target=foresight,
                    angle=_radians(syn.interior_angle(occupied, backsight, foresight)),
                    distance=_metres(syn.horizontal_distance(occupied, foresight)),
                )
            )
        return built

    @pytest.fixture
    def result(self, legs):
        start = (_metres(syn.COORDINATES["A"][0]), _metres(syn.COORDINATES["A"][1]))
        return adjust_traverse(
            legs,
            start,
            _radians(syn.start_azimuth()),
            kind=TraverseKind.CLOSED,
            close_azimuth=_radians(syn.azimuth("D", "A")),
            method=TraverseAdjustment.COMPASS,
        )

    def test_the_misclosures_vanish(self, result):
        assert abs(result.angular_misclosure) < 1e-12
        assert result.linear_misclosure < 1e-9

    def test_the_perimeter_is_the_sum_of_the_four_sides(self, result):
        assert result.perimeter.value == pytest.approx(syn.perimeter(), abs=1e-9)

    def test_every_station_lands_on_its_true_coordinates(self, result):
        for name in ("B", "C", "D"):
            easting, northing = result.coordinates[name]
            assert easting.value == pytest.approx(syn.COORDINATES[name][0], abs=1e-6)
            assert northing.value == pytest.approx(syn.COORDINATES[name][1], abs=1e-6)

    def test_a_blunder_in_one_angle_shows_up_as_a_misclosure(self, legs):
        """Non-vacuousness: the closure above is a property of the data, not
        something ``adjust_traverse`` reports regardless."""
        legs[1] = Leg(
            origin=legs[1].origin,
            target=legs[1].target,
            angle=_radians(legs[1].angle.value + 60.0 * ARCSECOND),
            distance=legs[1].distance,
        )
        start = (_metres(syn.COORDINATES["A"][0]), _metres(syn.COORDINATES["A"][1]))
        spoilt = adjust_traverse(
            legs,
            start,
            _radians(syn.start_azimuth()),
            kind=TraverseKind.CLOSED,
            close_azimuth=_radians(syn.azimuth("D", "A")),
        )
        assert spoilt.angular_misclosure == pytest.approx(60.0 * ARCSECOND, rel=1e-9)
        assert any(
            finding.code == "angular_misclosure_beyond_tolerance" for finding in spoilt.findings
        )


class TestTheResectionRecoversItsStation:
    @pytest.fixture
    def result(self):
        known = {
            name: (_metres(syn.COORDINATES[name][0]), _metres(syn.COORDINATES[name][1]))
            for name in ("A", "B", "C")
        }
        directions = {
            name: _radians((syn.azimuth("R", name) - syn.ORIENTATIONS["R"]) % math.tau)
            for name in ("A", "B", "C")
        }
        return resection(known, directions)

    def test_the_position_is_the_one_the_directions_were_computed_from(self, result):
        easting, northing = result.position
        assert easting.value == pytest.approx(syn.COORDINATES["R"][0], abs=1e-6)
        assert northing.value == pytest.approx(syn.COORDINATES["R"][1], abs=1e-6)

    def test_the_setup_orientation_comes_back_too(self, result):
        """Three directions determine three unknowns: two coordinates and the
        orientation. Recovering the orientation is what shows the third one is
        being solved rather than assumed."""
        recovered = result.orientation.value % math.tau
        assert recovered == pytest.approx(syn.ORIENTATIONS["R"], abs=1e-9)

    def test_the_geometry_is_not_flagged_as_dangerous(self, result):
        """R sits well inside the circle through A, B and C -- about a fifth of
        the circumradius from its centre -- so a danger-circle finding here
        would mean the detector fires on safe geometry."""
        assert not any("danger" in finding.code for finding in result.findings)


class TestTheIntersectionRecoversItsTarget:
    def _sighting(self, station: str, east: float, north: float):
        return (
            (_metres(syn.COORDINATES[station][0]), _metres(syn.COORDINATES[station][1])),
            _radians(
                math.atan2(
                    east - syn.COORDINATES[station][0], north - syn.COORDINATES[station][1]
                )
                % math.tau
            ),
        )

    def _beyond(self, offset: float) -> tuple[float, float]:
        """A point three baselines past B, pushed *offset* metres off the line
        through A and B. At ``offset = 0`` the two rays are parallel."""
        east = syn.COORDINATES["B"][0] - syn.COORDINATES["A"][0]
        north = syn.COORDINATES["B"][1] - syn.COORDINATES["A"][1]
        length = math.hypot(east, north)
        return (
            syn.COORDINATES["A"][0] + 3.0 * east - offset * north / length,
            syn.COORDINATES["A"][1] + 3.0 * north + offset * east / length,
        )

    def test_two_azimuths_fix_the_point(self):
        sightings = {
            name: self._sighting(name, *syn.COORDINATES["P1"][:2]) for name in ("A", "C")
        }
        result = forward_intersection("P1", sightings)
        easting, northing = result.position
        assert easting.value == pytest.approx(syn.COORDINATES["P1"][0], abs=1e-6)
        assert northing.value == pytest.approx(syn.COORDINATES["P1"][1], abs=1e-6)

    def test_good_geometry_raises_no_finding(self):
        """Without this the weak-geometry test below would pass on an
        implementation that flagged every intersection."""
        sightings = {
            name: self._sighting(name, *syn.COORDINATES["P1"][:2]) for name in ("A", "C")
        }
        assert forward_intersection("P1", sightings).findings == ()

    def test_near_parallel_rays_are_reported_as_weak(self):
        """Reported *through the ellipse*, which ``specs/09`` section 4.3 asks
        for: the position still comes out right, and what tells the user not to
        trust it is that the ellipse is far longer than it is wide."""
        target = self._beyond(2.0)
        sightings = {name: self._sighting(name, *target) for name in ("A", "B")}
        result = forward_intersection("weak", sightings)
        assert result.position[0].value == pytest.approx(target[0], abs=1e-4)
        assert any(finding.code == "weak_intersection_geometry" for finding in result.findings)

    def test_exactly_parallel_rays_are_refused_rather_than_answered(self):
        """Collinear stations sighting a point on their own line determine
        nothing. A number here would look like a coordinate."""
        target = self._beyond(0.0)
        sightings = {name: self._sighting(name, *target) for name in ("A", "B")}
        with pytest.raises(ComputationError):
            forward_intersection("parallel", sightings)


class TestRadiationRecoversTheDetailPoints:
    @pytest.mark.parametrize("target", ("P1", "P2"))
    def test_a_radiated_point_lands_where_it_was_generated(self, target):
        station = "A"
        origin = tuple(_metres(value) for value in syn.COORDINATES[station])
        result = radiate(
            target,
            origin,
            Quantity.exact(syn.ORIENTATIONS[station], Unit.RADIAN),
            _radians((syn.azimuth(station, target) - syn.ORIENTATIONS[station]) % math.tau),
            _radians(syn.zenith(station, target), syn.SIGMA_ZENITH),
            _metres(syn.slope_distance(station, target)),
            _metres(syn.INSTRUMENT_HEIGHT, 0.001),
            _metres(syn.TARGET_HEIGHT, 0.001),
            correlation=0.0,
        )
        for value, expected in zip(result.position, syn.COORDINATES[target], strict=True):
            assert value.value == pytest.approx(expected, abs=1e-6)

    def test_the_three_coordinates_are_correlated(self):
        """They come from one pointing. ``specs/09`` section 4.6 is explicit
        that treating them as independent is wrong."""
        origin = tuple(_metres(value) for value in syn.COORDINATES["A"])
        result = radiate(
            "P1",
            origin,
            Quantity.exact(syn.ORIENTATIONS["A"], Unit.RADIAN),
            _radians((syn.azimuth("A", "P1") - syn.ORIENTATIONS["A"]) % math.tau),
            _radians(syn.zenith("A", "P1"), syn.SIGMA_ZENITH),
            _metres(syn.slope_distance("A", "P1")),
            _metres(syn.INSTRUMENT_HEIGHT, 0.001),
            _metres(syn.TARGET_HEIGHT, 0.001),
            correlation=0.0,
        )
        correlation = result.covariance.to_correlation()
        assert abs(correlation[0, 1]) > 0.1


class TestTrigonometricLevellingOverTheFixture:
    def test_a_radial_height_difference_carries_the_curvature_term(self):
        """The synthetic sight is a straight line between marks, so it contains
        no curvature or refraction. A trigonometric height computed from it and
        then corrected is high by exactly ``(1 - k) d^2 / 2R`` -- stated here in
        closed form, so the test checks the correction instead of tolerating
        it."""
        station, target = "A", "B"
        sight = Sight(
            station=target,
            zenith=_radians(syn.zenith(station, target), syn.SIGMA_ZENITH),
            distance=_metres(syn.slope_distance(station, target)),
            target_height=_metres(syn.TARGET_HEIGHT, 0.001),
        )
        difference = radial_height_difference(
            sight,
            _metres(syn.INSTRUMENT_HEIGHT, 0.001),
            refraction_coefficient=Quantity.from_std_dev(0.13, 0.05, Unit.DIMENSIONLESS),
        )
        expected = syn.height_difference(station, target) + syn.curvature_and_refraction(
            syn.horizontal_distance(station, target)
        )
        assert difference.value == pytest.approx(expected, abs=1e-6)

    def test_the_balanced_leap_frog_pair_recovers_the_height_difference_exactly(self):
        """Both sights from L are the same length, so the curvature and
        refraction terms are equal and subtract away completely -- and the true
        height difference between A and D comes back with nothing added."""
        sights = [
            Sight(
                station=target,
                zenith=_radians(syn.zenith("L", target), syn.SIGMA_ZENITH),
                distance=_metres(syn.slope_distance("L", target)),
                target_height=_metres(syn.TARGET_HEIGHT, 0.001),
            )
            for target in ("A", "D")
        ]
        result = leapfrog_height_difference(
            *sights,
            refraction_coefficient=Quantity.from_std_dev(0.13, 0.05, Unit.DIMENSIONLESS),
        )
        assert result.height_difference.value == pytest.approx(
            syn.height_difference("A", "D"), abs=1e-9
        )
        assert result.sight_imbalance == pytest.approx(0.0, abs=1e-9)

    @pytest.mark.parametrize("sigma_k", (0.0, 0.05, 0.5))
    def test_the_balanced_result_does_not_depend_on_how_well_k_is_known(self, sigma_k):
        """The cancellation has to appear in the uncertainty, not only in the
        value: with balanced sights the refraction coefficient's own
        uncertainty must not reach the answer at all."""
        sights = [
            Sight(
                station=target,
                zenith=_radians(syn.zenith("L", target), syn.SIGMA_ZENITH),
                distance=_metres(syn.slope_distance("L", target)),
                target_height=_metres(syn.TARGET_HEIGHT, 0.001),
            )
            for target in ("A", "D")
        ]
        result = leapfrog_height_difference(
            *sights,
            refraction_coefficient=Quantity.from_std_dev(0.13, sigma_k, Unit.DIMENSIONLESS),
        )
        reference = leapfrog_height_difference(
            *sights,
            refraction_coefficient=Quantity.exact(0.13, Unit.DIMENSIONLESS),
        )
        assert result.height_difference.std_dev == pytest.approx(
            reference.height_difference.std_dev, rel=1e-9
        )
