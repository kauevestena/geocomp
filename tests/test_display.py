# SPDX-License-Identifier: GPL-2.0-or-later
"""A geocentric solution drawn on a map (``specs/19`` section 1.1).

The positions are the in-house projection's, which ``test_geodesy.py`` checks
against DynAdjust; what is checked here is what drawing adds: which grid, what
it is called, and that the ellipses and corrections turn with the grid rather
than lean by the meridian convergence.
"""

from __future__ import annotations

import math
from dataclasses import replace

import pytest

from geocomp.core.adjustment.geocentric import ELLIPSOID
from geocomp.core.geodesy.cartesian import cartesian_to_geodetic
from geocomp.core.geodesy.projection import utm_parameters
from geocomp.core.models import CoordinateSystem, HeightType
from geocomp.core.techniques.integration import adjust_combination, combine
from geocomp.core.visualization.display import display_grid, for_display, grid_bearing_of_north

from . import combined_network as field
from .test_integration import (
    GEOID,
    TARGET_EPOCH,
    control_input,
    gnss_input,
    levelling_input,
    sirgas_velocities,
    total_station_input,
)

LATITUDE, LONGITUDE = field.LATITUDE, field.LONGITUDE


@pytest.fixture(scope="module")
def adjusted():
    combined = combine(
        [gnss_input(), control_input(), total_station_input(), levelling_input()],
        frame="ITRF2020",
        epoch=TARGET_EPOCH,
        velocities=sirgas_velocities(),
    )
    result = adjust_combination(combined, geoid=GEOID)
    return result.solution, combined.network


class TestTheGrid:
    def test_sirgas_2000_is_drawn_in_its_own_utm_zone_by_code(self):
        grid = display_grid("SIRGAS2000", LATITUDE, LONGITUDE)
        assert grid.crs == "EPSG:31982"
        assert grid.name == "SIRGAS2000 / UTM zone 22S"

    def test_north_of_the_equator_the_northern_codes(self):
        grid = display_grid("SIRGAS 2000", math.radians(4.6), math.radians(-74.1))
        assert grid.crs == "EPSG:31972"

    def test_an_itrf_solution_is_drawn_on_its_own_frame_named(self):
        """Not on "SIRGAS 2000 / UTM": that is what QGIS matches a bare GRS80
        UTM string to, and for ITRF2020 at 2026 it is decimetres wrong."""
        grid = display_grid("ITRF2020", LATITUDE, LONGITUDE)
        assert grid.crs.startswith('PROJCRS["ITRF2020 / UTM zone 22S"')
        assert "International Terrestrial Reference Frame 2020" in grid.crs
        assert '"Longitude of natural origin",-51,' in grid.crs
        assert '"False northing",10000000,' in grid.crs

    def test_a_frame_geocomp_cannot_transform_is_still_drawn_under_its_name(self):
        """Drawing transforms nothing. Until P12c-13 the grid was refused for a
        frame GeoComp holds no transformation for, and a DynAdjust solution in
        GDA2020 never reached the map (FR-324)."""
        grid = display_grid("GDA2020", math.radians(-27.5), math.radians(153.0))
        assert grid.name == "GDA2020 / UTM zone 56S"
        assert grid.crs.startswith('PROJCRS["GDA2020 / UTM zone 56S"')
        assert 'DATUM["GDA2020"' in grid.crs

    def test_a_frame_with_no_name_is_still_refused(self):
        from geocomp.core.errors import ValidationError

        with pytest.raises(ValidationError):
            display_grid("  ", LATITUDE, LONGITUDE)

    def test_geodetic_north_leans_by_the_convergence(self):
        """gamma = atan(tan(dlambda) sin(phi)) on the sphere; the ellipsoid adds
        a few arc-seconds at most this close to the central meridian."""
        projection = utm_parameters(22, southern_hemisphere=True)
        dlambda = LONGITUDE - math.radians(-51.0)
        convergence = math.atan(math.tan(dlambda) * math.sin(LATITUDE))
        assert grid_bearing_of_north(LATITUDE, LONGITUDE, projection) == pytest.approx(-convergence, abs=2e-5)


class TestTheSolutionDrawn:
    def test_a_projected_solution_is_left_as_it_is(self, adjusted):
        solution, network = adjusted
        shown, _network, grid = for_display(solution, network)
        again, _, none = for_display(shown)
        assert grid is not None and none is None
        assert again is shown

    def test_positions_are_easting_northing_and_ellipsoidal_height(self, adjusted):
        solution, network = adjusted
        shown, _network, grid = for_display(solution, network)
        assert shown.crs == grid.crs
        for before, after in zip(solution.adjusted_stations, shown.adjusted_stations, strict=True):
            position = after.position
            assert position.system is CoordinateSystem.PROJECTED
            assert position.height_type is HeightType.ELLIPSOIDAL
            xyz = [q.value for q in before.position.values]
            assert position.values[2].value == pytest.approx(cartesian_to_geodetic(*xyz, ELLIPSOID)[2])
            assert 500_000 < position.values[0].value < 800_000
            assert 7_000_000 < position.values[1].value < 7_500_000

    def test_the_variances_are_turned_into_the_horizon_not_relabelled(self, adjusted):
        """A rotation keeps the trace; the vertical takes most of a GNSS
        network's variance, which X, Y, Z share out."""
        solution, network = adjusted
        shown, _network, _grid = for_display(solution, network)
        for before, after in zip(solution.adjusted_stations, shown.adjusted_stations, strict=True):
            total = sum(q.variance for q in before.position.values)
            assert sum(q.variance for q in after.position.values) == pytest.approx(total, rel=1e-9)
            east, north, up = (q.variance for q in after.position.values)
            assert up > max(east, north)

    def test_ellipses_turn_with_the_grid_and_keep_their_size(self, adjusted):
        solution, network = adjusted
        shown, _network, grid = for_display(solution, network)
        for before, after in zip(solution.adjusted_stations, shown.adjusted_stations, strict=True):
            xyz = [q.value for q in before.position.values]
            latitude, longitude, _ = cartesian_to_geodetic(*xyz, ELLIPSOID)
            turn = grid_bearing_of_north(latitude, longitude, grid.projection)
            assert after.ellipse.semi_major == before.ellipse.semi_major
            assert after.ellipse.semi_minor == before.ellipse.semi_minor
            expected = (before.ellipse.orientation + turn) % math.pi
            assert after.ellipse.orientation == pytest.approx(expected, abs=1e-12)

    def test_corrections_turn_and_keep_their_length(self, adjusted):
        """Stated east, north, up at each station, as ``to_solution`` gives
        them when it has the starting coordinates."""
        solution, network = adjusted
        stations = tuple(replace(s, correction=(0.03, -0.04, 0.002)) for s in solution.adjusted_stations)
        solution = replace(solution, adjusted_stations=stations)
        shown, _network, grid = for_display(solution, network)
        for before, after in zip(solution.adjusted_stations, shown.adjusted_stations, strict=True):
            assert math.hypot(*after.correction[:2]) == pytest.approx(0.05)
            assert after.correction[2] == 0.002
            xyz = [q.value for q in before.position.values]
            latitude, longitude, _ = cartesian_to_geodetic(*xyz, ELLIPSOID)
            turn = grid_bearing_of_north(latitude, longitude, grid.projection)
            azimuth = math.atan2(*after.correction[:2])
            assert azimuth == pytest.approx(math.atan2(0.03, -0.04) + turn, abs=1e-12)

    def test_held_stations_are_placed_from_the_network(self, adjusted):
        """A held mark is not in the solution; the map finds it in the network,
        so that is re-expressed too -- and its hold's mode is kept for the
        symbol."""
        solution, network = adjusted
        _shown, shown_network, grid = for_display(solution, network)
        for name in field.HELD:
            station = shown_network.stations[name]
            assert station.approx_position.system is CoordinateSystem.PROJECTED
            assert station.approx_position.crs == grid.crs
            assert station.constraint.mode is network.stations[name].constraint.mode
            assert 500_000 < station.approx_position.values[0].value < 800_000
