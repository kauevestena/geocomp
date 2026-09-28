# SPDX-License-Identifier: GPL-2.0-or-later
"""The combination beyond P9a's geocentric core (``specs/13`` section 6.2).

What the Integration menu needs from the combination that the three-technique
test of ``test_integration.py`` does not exercise:

* a **local** combination -- total station and levelling in one projected
  system, adjusted in three dimensions or in heights alone;
* a total-station network **in a grid** (UTM) joining a geocentric one, placed
  by the projection the caller names;
* a levelling network's **benchmarks**, which hold a height on a placeholder
  planimetry and must neither be read as coordinates nor silently dropped;
* the routing rules a local system and orthometric heights add.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from geocomp.core.adjustment.geocentric import ELLIPSOID, HEIGHT_TYPE_KEY
from geocomp.core.adjustment.parameters import Frame
from geocomp.core.errors import ValidationError
from geocomp.core.geodesy.cartesian import cartesian_to_geodetic
from geocomp.core.geodesy.projection import transverse_mercator, utm_parameters
from geocomp.core.models import (
    ConstraintMode,
    ConstraintSpec,
    CoordinateSystem,
    Epoch,
    HeightType,
    Network,
    Observation,
    ObservationType,
    Position,
    Station,
)
from geocomp.core.techniques.integration import (
    GridFrame,
    adjust_combination,
    adjustment_frame,
    combine,
    route,
)
from geocomp.core.uncertainty import Covariance, Quantity
from geocomp.core.units import Unit

from . import combined_network as field
from .conftest import requires_dynadjust
from .test_integration import (
    GEOID,
    TARGET_EPOCH,
    TRUTH,
    _undulation,
    control_input,
    gnss_input,
    levelling_input,
    sirgas_velocities,
    total_station_input,
)

UTM_22S = utm_parameters(22, southern_hemisphere=True)
SURVEY_EPOCH = Epoch.from_decimal_year(2026.7)
GRID = "EPSG:31982"
GRIDS = {GRID: GridFrame(frame="SIRGAS2000", projection=UTM_22S)}


def _metres(value: float, sigma: float | None = None) -> Quantity:
    return (
        Quantity.exact(value, Unit.METRE)
        if sigma is None
        else Quantity.from_std_dev(value, sigma, Unit.METRE)
    )


def _projected(east, north, up, crs=GRID, *, sigma=None) -> Position:
    return Position(
        values=(_metres(east, sigma), _metres(north, sigma), _metres(up, sigma)),
        system=CoordinateSystem.PROJECTED,
        crs=crs,
        height_type=HeightType.ORTHOMETRIC,
    )


def benchmark(station_id: str, height: float, *, sigma: float | None = None) -> Station:
    """A benchmark exactly as the levelling network builds one: the height on
    two placeholder zeros, held in ``up`` alone, the same position as its start."""
    position = Position(
        values=(_metres(0.0), _metres(0.0), _metres(height, sigma)),
        system=CoordinateSystem.PROJECTED,
        crs="LOCAL",
        height_type=HeightType.ORTHOMETRIC,
    )
    return Station(
        id=station_id,
        approx_position=position,
        constraint=ConstraintSpec(
            mode=ConstraintMode.FIXED if sigma is None else ConstraintMode.WEIGHTED,
            components=frozenset({"up"}),
            position=position,
            covariance=None if sigma is None else Covariance.diagonal({"up": sigma**2}, {"up": Unit.METRE}),
        ),
    )


def _orthometric(station: str) -> float:
    return cartesian_to_geodetic(*TRUTH[station], ELLIPSOID)[2] - _undulation(station)


def _grid(station: str) -> tuple[float, float, float]:
    latitude, longitude, _ = cartesian_to_geodetic(*TRUTH[station], ELLIPSOID)
    east, north = transverse_mercator(latitude, longitude, UTM_22S)
    return east, north, _orthometric(station)


def grid_total_station_input() -> Network:
    """The total station's survey as the total-station menu writes it: in UTM
    22S, each station starting a few decimetres off, heights orthometric."""
    network = total_station_input()
    network.crs = GRID
    rng = np.random.default_rng(11)
    for name in list(network.stations):
        east, north, up = np.array(_grid(name)) + rng.uniform(-0.3, 0.3, 3)
        network.stations[name] = Station(id=name, approx_position=_projected(east, north, up, sigma=1.0))
    return network


def levelling_with_benchmark(*, sigma: float | None = 0.005, network_id: str = "levelling") -> Network:
    network = levelling_input()
    network.id = network_id
    network.crs = "LOCAL"
    network.stations["M03"] = benchmark("M03", _orthometric("M03"), sigma=sigma)
    return network


def _geocentric(*inputs, **extra):
    return combine(
        list(inputs), frame="ITRF2020", epoch=TARGET_EPOCH, velocities=sirgas_velocities(), **extra
    )


def _xyz(solution, station):
    return np.array([q.value for q in solution.station(station).position.values])


# -- a total-station network in a grid ------------------------------------------


class TestGridInput:
    def test_its_starting_positions_are_placed_by_the_named_projection(self):
        """Taken first, so its starts are the ones kept: each within the
        decimetres it was perturbed by, plus the frames' drift since 2000.4.
        Its orthometric heights are lifted by the median difference at the
        stations the GNSS input places -- the geoid, near enough to start."""
        combined = _geocentric(grid_total_station_input(), gnss_input(), control_input(), grids=GRIDS)
        for name in field.OFFSETS:
            start = np.array([q.value for q in combined.network.stations[name].approx_position.values])
            assert np.linalg.norm(start - TRUTH[name]) < 1.0, name

    def test_the_answer_does_not_depend_on_where_it_started(self):
        grid = adjust_combination(
            _geocentric(
                grid_total_station_input(), gnss_input(), control_input(), levelling_input(), grids=GRIDS
            ),
            geoid=GEOID,
        )
        plain = adjust_combination(
            _geocentric(gnss_input(), control_input(), total_station_input(), levelling_input()), geoid=GEOID
        )
        for name in ("M03", "M04", "M05", "M06"):
            assert np.linalg.norm(_xyz(grid.solution, name) - _xyz(plain.solution, name)) < 1e-5, name

    def test_a_grid_nobody_named_is_irreconcilable_by_input(self):
        with pytest.raises(ValidationError) as caught:
            _geocentric(gnss_input(), control_input(), grid_total_station_input())
        assert caught.value.code == "validation.combination_frame_irreconcilable"
        assert caught.value.context["input"] == "total-station"

    def test_a_point_held_in_grid_coordinates_is_refused(self):
        """Its height is orthometric, so holding it in the geocentric frame
        would put the geoid into the residuals."""
        network = grid_total_station_input()
        position = _projected(*_grid("M06"))
        network.stations["M06"] = Station(
            id="M06",
            approx_position=position,
            constraint=ConstraintSpec(
                mode=ConstraintMode.FIXED,
                components=frozenset({"easting", "northing", "up"}),
                position=position,
            ),
        )
        with pytest.raises(ValidationError) as caught:
            _geocentric(gnss_input(), control_input(), network, grids=GRIDS)
        assert caught.value.code == "validation.combination_projected_hold"
        assert caught.value.context["station"] == "M06"

    @pytest.mark.parametrize("frame", ["ITRF2020", None])
    def test_a_combination_needs_its_epoch(self, frame):
        with pytest.raises(ValidationError) as caught:
            combine([total_station_input()], frame=frame, epoch=None)
        assert caught.value.code == "validation.combination_epoch_required"


# -- benchmarks in a geocentric combination -------------------------------------


class TestBenchmarks:
    def test_a_weighted_benchmark_becomes_an_orthometric_height_observation(self):
        combined = _geocentric(
            gnss_input(), control_input(), total_station_input(), levelling_with_benchmark()
        )
        observation = combined.network.observations["benchmark:M03"]
        assert observation.type is ObservationType.ORTHOMETRIC_HEIGHT
        assert observation.values[0].value == pytest.approx(_orthometric("M03"))
        assert observation.values[0].variance == pytest.approx(0.005**2)
        assert observation.meta["technique"] == "levelling"
        station = combined.network.stations["M03"]
        assert station.constraint.mode is ConstraintMode.FREE
        # The placeholder zeros are gone; the GNSS input's start is kept.
        assert station.approx_position.system is CoordinateSystem.CARTESIAN

    def test_it_is_tested_against_the_geoid_like_any_other(self):
        result = adjust_combination(
            _geocentric(gnss_input(), control_input(), total_station_input(), levelling_with_benchmark()),
            geoid=GEOID,
        )
        assert "benchmark:M03" in {o.id for o in result.run.observations}
        assert "M03" in {r.station_id for r in result.geoid}
        adjusted = _xyz(result.solution, "M03")
        assert np.linalg.norm(adjusted - TRUTH["M03"]) < 0.02

    def test_one_held_exactly_is_refused_by_name(self):
        with pytest.raises(ValidationError) as caught:
            _geocentric(gnss_input(), control_input(), levelling_with_benchmark(sigma=None))
        assert caught.value.code == "validation.combination_benchmark_held_exactly"
        assert caught.value.context["station"] == "M03"
        assert caught.value.context["input"] == "levelling"

    def test_the_same_benchmark_in_two_networks_is_one_observation(self):
        combined = _geocentric(
            gnss_input(),
            control_input(),
            levelling_with_benchmark(),
            levelling_with_benchmark(network_id="levelling-2"),
        )
        benchmarks = [o for o in combined.network.observations.values() if o.meta.get("benchmark")]
        assert len(benchmarks) == 1

    def test_two_networks_disagreeing_on_it_are_refused(self):
        second = levelling_with_benchmark(network_id="levelling-2")
        second.stations["M03"] = benchmark("M03", _orthometric("M03") + 0.005, sigma=0.005)
        with pytest.raises(ValidationError) as caught:
            _geocentric(gnss_input(), control_input(), levelling_with_benchmark(), second)
        assert caught.value.code == "validation.combination_station_held_differently"
        assert caught.value.context["received"] == ["levelling", "levelling-2"]

    def test_a_station_reached_only_through_heights_is_refused(self):
        """Nothing places it horizontally; a singular matrix would say so less
        usefully."""
        levelling = levelling_with_benchmark()
        levelling.add_station(Station(id="RN9"))
        levelling.add_observation(
            Observation(
                id="l-M03-RN9",
                type=ObservationType.HEIGHT_DIFFERENCE,
                stations=("M03", "RN9"),
                values=(_metres(1.234, 0.001),),
                meta={HEIGHT_TYPE_KEY: HeightType.ORTHOMETRIC.name},
            )
        )
        combined = _geocentric(gnss_input(), control_input(), total_station_input(), levelling)
        with pytest.raises(ValidationError) as caught:
            adjust_combination(combined, geoid=GEOID)
        assert caught.value.code == "validation.combination_station_without_horizontal"
        assert caught.value.context["stations"] == ["RN9"]


# -- a local combination: total station and levelling ---------------------------

#: A small survey in UTM 22S, in metres: easting, northing, orthometric height.
LOCAL = {
    "P1": (675_000.0, 7_185_000.0, 912.000),
    "P2": (675_820.0, 7_185_140.0, 925.310),
    "P3": (675_380.0, 7_185_760.0, 904.225),
    "P4": (675_960.0, 7_185_640.0, 931.870),
}
PAIRS = (("P1", "P2"), ("P1", "P3"), ("P1", "P4"), ("P2", "P3"), ("P2", "P4"), ("P3", "P4"))


def _held(name: str, components) -> ConstraintSpec:
    return ConstraintSpec(
        mode=ConstraintMode.FIXED, components=frozenset(components), position=_projected(*LOCAL[name])
    )


def local_total_station(*, heights_only: bool = False) -> Network:
    """Slope distances and zenith angles over every pair -- or, reduced,
    the trigonometric height differences alone."""
    rng = np.random.default_rng(5)
    network = Network(id="total-station", crs=GRID)
    for name, (east, north, up) in LOCAL.items():
        constraint = (
            _held(name, {"easting", "northing", "up"})
            if name == "P1"
            else _held(name, {"easting", "northing"})
            if name == "P2"
            else ConstraintSpec()
        )
        start = np.array((east, north, up)) + rng.uniform(-0.2, 0.2, 3)
        network.add_station(
            Station(id=name, approx_position=_projected(*start, sigma=1.0), constraint=constraint)
        )
    for a, b in PAIRS:
        d = np.array(LOCAL[b]) - np.array(LOCAL[a])
        if heights_only:
            network.add_observation(
                Observation(
                    id=f"t-{a}-{b}",
                    type=ObservationType.HEIGHT_DIFFERENCE,
                    stations=(a, b),
                    values=(_metres(d[2] + rng.normal(0, 0.004), 0.004),),
                    meta={"technique": "total_station"},
                )
            )
            continue
        network.add_observation(
            Observation(
                id=f"s-{a}-{b}",
                type=ObservationType.SLOPE_DISTANCE,
                stations=(a, b),
                values=(_metres(float(np.linalg.norm(d)) + rng.normal(0, 0.002), 0.002),),
            )
        )
        zenith = math.atan2(math.hypot(d[0], d[1]), d[2])
        sigma = math.radians(3.0 / 3600.0)
        network.add_observation(
            Observation(
                id=f"z-{a}-{b}",
                type=ObservationType.ZENITH_ANGLE,
                stations=(a, b),
                values=(Quantity.from_std_dev(zenith + rng.normal(0, sigma), sigma, Unit.RADIAN),),
            )
        )
    return network


def local_levelling() -> Network:
    """A loop P1 -> P3 -> P4 -> P1, P1 its benchmark, in no CRS at all."""
    rng = np.random.default_rng(6)
    network = Network(id="levelling", crs="LOCAL")
    network.add_station(benchmark("P1", LOCAL["P1"][2]))
    for name in ("P3", "P4"):
        network.add_station(Station(id=name))
    for a, b in (("P1", "P3"), ("P3", "P4"), ("P4", "P1")):
        network.add_observation(
            Observation(
                id=f"l-{a}-{b}",
                type=ObservationType.HEIGHT_DIFFERENCE,
                stations=(a, b),
                values=(_metres(LOCAL[b][2] - LOCAL[a][2] + rng.normal(0, 0.0008), 0.0008),),
                meta={HEIGHT_TYPE_KEY: HeightType.ORTHOMETRIC.name},
            )
        )
    return network


@pytest.fixture(scope="module")
def result():
    # Levelling first: its benchmark's placeholder must not shadow the
    # total station's start, nor its height hold the full one.
    combined = combine([local_levelling(), local_total_station()], frame=None, epoch=SURVEY_EPOCH)
    return combined, adjust_combination(combined)


class TestLocalCombination:
    def test_it_stays_in_the_inputs_one_system(self, result):
        combined, adjusted = result
        assert not combined.geocentric
        assert combined.frame == GRID
        assert combined.transformations == ()
        assert adjustment_frame(combined) is Frame.SPACE_3D
        assert adjusted.solution.crs == GRID

    def test_a_benchmark_and_a_control_point_agreeing_are_one_hold(self, result):
        combined, _ = result
        station = combined.network.stations["P1"]
        assert station.constraint.components == {"easting", "northing", "up"}
        assert station.approx_position.values[0].value == pytest.approx(LOCAL["P1"][0], abs=0.5)

    def test_both_techniques_carry_the_heights(self, result):
        _, adjusted = result
        assert {s.technique for s in adjusted.breakdown} == {"total_station", "levelling"}
        for name in ("P3", "P4"):
            up = adjusted.solution.station(name).position.values[2].value
            assert up == pytest.approx(LOCAL[name][2], abs=0.003), name

    def test_heights_alone_are_adjusted_in_the_height_frame(self):
        combined = combine(
            [local_total_station(heights_only=True), local_levelling()], frame=None, epoch=SURVEY_EPOCH
        )
        assert adjustment_frame(combined) is Frame.HEIGHT_1D
        adjusted = adjust_combination(combined)
        assert {s.technique for s in adjusted.breakdown} == {"total_station", "levelling"}
        assert adjusted.run.converged

    def test_a_levelling_only_mark_in_three_dimensions_is_refused(self):
        levelling = local_levelling()
        levelling.add_station(Station(id="RN9"))
        levelling.add_observation(
            Observation(
                id="l-P4-RN9",
                type=ObservationType.HEIGHT_DIFFERENCE,
                stations=("P4", "RN9"),
                values=(_metres(-2.5, 0.001),),
            )
        )
        with pytest.raises(ValidationError) as caught:
            adjust_combination(combine([local_total_station(), levelling], frame=None, epoch=SURVEY_EPOCH))
        assert caught.value.code == "validation.combination_station_without_horizontal"
        assert caught.value.context["stations"] == ["RN9"]

    def test_two_systems_are_refused_naming_each_input(self):
        other = local_levelling()
        other.crs = "EPSG:31983"
        with pytest.raises(ValidationError) as caught:
            combine([local_total_station(), other], frame=None, epoch=SURVEY_EPOCH)
        assert caught.value.code == "validation.combination_frames_differ"
        assert caught.value.context["inputs"] == {"total-station": GRID, "levelling": "EPSG:31983"}

    def test_a_gnss_position_needs_a_geocentric_frame(self):
        with pytest.raises(ValidationError) as caught:
            combine([local_total_station(), gnss_input()], frame=None, epoch=SURVEY_EPOCH)
        assert caught.value.code == "validation.combination_gnss_in_local_frame"
        assert caught.value.context["input"] == "gnss"

    def test_a_geoid_has_nothing_to_relate_here(self):
        combined = combine([local_total_station(), local_levelling()], frame=None, epoch=SURVEY_EPOCH)
        with pytest.raises(ValidationError) as caught:
            adjust_combination(combined, geoid=GEOID)
        assert caught.value.code == "validation.combination_geoid_in_local_frame"


class TestRouting:
    def test_a_local_system_stays_in_house_with_the_reason(self):
        combined = combine([local_total_station()], frame=None, epoch=SURVEY_EPOCH)
        routing = route(combined.network, "dynadjust")
        assert routing.engine == "in_house"
        assert "local system" in routing.reason and GRID in routing.reason

    def test_the_in_house_path_proceeds_when_routing_overrode_the_request(self):
        combined = combine([local_total_station(), local_levelling()], frame=None, epoch=SURVEY_EPOCH)
        adjusted = adjust_combination(combined, requested_engine="dynadjust")
        assert adjusted.routing.engine == "in_house"
        assert adjusted.solution.provenance.parameters["routing"]["engine"] == "in_house"


class TestDynAdjustPath:
    """DynAdjust adjusting a combination routing allows it (``specs/13`` §6.2)."""

    def test_a_combination_routing_keeps_in_house_is_refused(self, tmp_path):
        from geocomp.engines.dynadjust.combination import adjust_with_dynadjust

        combined = _geocentric(gnss_input(), control_input(), total_station_input(), levelling_input())
        with pytest.raises(ValidationError) as caught:
            adjust_with_dynadjust(combined, tmp_path)
        assert caught.value.code == "validation.combination_not_for_dynadjust"
        assert "orthometric" in caught.value.context["reason"]

    @requires_dynadjust
    def test_it_agrees_with_the_in_house_core(self, tmp_path):
        """GNSS in ITRF2014, control in SIRGAS 2000 and the total station,
        combined in ITRF2020 and adjusted by both engines. They differ by how
        DynAdjust carries a reflector's height along a slope distance
        (``specs/07`` section 6.3): under a millimetre on this survey."""
        from geocomp.engines.dynadjust.combination import adjust_with_dynadjust

        combined = _geocentric(gnss_input(), control_input(), total_station_input())
        dynadjust = adjust_with_dynadjust(combined, tmp_path)
        in_house = adjust_combination(combined)
        assert dynadjust.routing.engine == "dynadjust"
        assert dynadjust.breakdown == () and dynadjust.run is None
        parameters = dynadjust.solution.provenance.parameters
        assert parameters["routing"]["engine"] == "dynadjust"
        assert parameters["combination"]["inputs"] == ["gnss", "control", "total-station"]
        assert any(stage["program"] == "dnaadjust" for stage in parameters["stages"])
        for name in ("M03", "M04", "M05", "M06"):
            difference = _xyz(dynadjust.solution, name) - _xyz(in_house.solution, name)
            assert np.linalg.norm(difference) < 1e-3, name
