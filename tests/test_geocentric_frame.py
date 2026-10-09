# SPDX-License-Identifier: GPL-2.0-or-later
"""The geocentric frame: every observation at its own station's vertical (phase P9a).

``specs/06`` section 2.3, ``specs/13`` section 6. The network is placed at
Curitiba, where a GNSS survey tied to a total-station traverse and a levelling
line is exactly the combination P9 is for, and spans 3 km -- far enough that a
flat frame's single "up" is wrong by a clearly visible amount.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from geocomp.core.adjustment import Frame
from geocomp.core.adjustment.equations import evaluate
from geocomp.core.adjustment.geocentric import (
    ELLIPSOID,
    GEOCENTRIC_TYPES,
    HEIGHT_TYPE_KEY,
    UNDULATION,
)
from geocomp.core.adjustment.least_squares import AdjustmentOptions, adjust, to_solution
from geocomp.core.adjustment.parameters import ParameterLayout
from geocomp.core.adjustment.undulations import geoid_residuals
from geocomp.core.differentiation import central_difference_jacobian
from geocomp.core.errors import ValidationError
from geocomp.core.geodesy.cartesian import (
    cartesian_to_geodetic,
    enu_rotation,
    geodetic_to_cartesian,
)
from geocomp.core.geoid import Coverage, GeoidModel
from geocomp.core.models import (
    BaselineFrame,
    Cluster,
    ClusterKind,
    ConstraintMode,
    ConstraintSpec,
    CoordinateSystem,
    DatumDefinition,
    Epoch,
    HeightType,
    Network,
    Observation,
    ObservationType,
    Position,
    Station,
)
from geocomp.core.models.observation import BASELINE_FRAME_KEY
from geocomp.core.uncertainty import Covariance, Quantity, Strategy, UncertaintyMode
from geocomp.core.units import Unit

LATITUDE, LONGITUDE = math.radians(-25.45), math.radians(-49.23)
#: East, north, up offsets from the origin, metres: a 3 km network.
OFFSETS = {
    "A": (0.0, 0.0, 910.0),
    "B": (1500.0, 200.0, 925.0),
    "C": (3000.0, -300.0, 940.0),
    "D": (1800.0, 1900.0, 905.0),
    "E": (400.0, 2200.0, 930.0),
}
HELD = ("A", "C")


def _ecef(east: float, north: float, height: float) -> np.ndarray:
    """A point *east* and *north* metres along the ellipsoid from the origin."""
    radius = 6_378_137.0
    latitude = LATITUDE + north / radius
    longitude = LONGITUDE + east / (radius * math.cos(LATITUDE))
    return np.array(geodetic_to_cartesian(latitude, longitude, height, ELLIPSOID))


TRUTH = {name: _ecef(*offset) for name, offset in OFFSETS.items()}


def _cartesian(values, *, exact: bool = True) -> Position:
    make = (
        (lambda v: Quantity.exact(float(v), Unit.METRE))
        if exact
        else (lambda v: Quantity.from_std_dev(float(v), 1.0, Unit.METRE))
    )
    return Position(
        values=tuple(make(v) for v in values),
        system=CoordinateSystem.CARTESIAN,
        crs="EPSG:4988",
        height_type=HeightType.ELLIPSOIDAL,
    )


def _geometry(origin: str, target: str, instrument: float = 0.0, target_height: float = 0.0):
    """The sight in the origin's own horizon, computed from the truth."""
    lat_o, lon_o, _ = cartesian_to_geodetic(*TRUTH[origin], ELLIPSOID)
    lat_t, lon_t, _ = cartesian_to_geodetic(*TRUTH[target], ELLIPSOID)
    up_o = enu_rotation(lat_o, lon_o)[2]
    up_t = enu_rotation(lat_t, lon_t)[2]
    delta = (TRUTH[target] + target_height * up_t) - (TRUTH[origin] + instrument * up_o)
    return enu_rotation(lat_o, lon_o) @ delta


def _height(station: str) -> float:
    return cartesian_to_geodetic(*TRUTH[station], ELLIPSOID)[2]


def _geoid(offset: float = 0.0, sigma: float = 0.05) -> GeoidModel:
    """A geoid over the network: -2 m at the origin, tilting 10 cm in 3 km.

    Planar, so bilinear interpolation is exact and the interpolation term of
    its uncertainty is zero -- the model's *sigma* is all of it. *offset* makes
    the model wrong by that much everywhere, which is what the adjustment's
    geoid residuals are there to find.
    """
    span = 0.01
    latitudes = LATITUDE + np.array([-span, 0.0, span])
    longitudes = LONGITUDE + np.array([-span, 0.0, span])
    values = np.array(
        [
            [-2.0 + offset + 300.0 * (lat - LATITUDE) - 200.0 * (lon - LONGITUDE) for lon in longitudes]
            for lat in latitudes
        ]
    )
    return GeoidModel(
        id="curitiba-test-geoid",
        values=values,
        coverage=Coverage(LATITUDE - span, LATITUDE + span, LONGITUDE - span, LONGITUDE + span),
        sigma=sigma,
        name="Test geoid",
        version="1",
    )


GEOID = _geoid()


def _undulation(station: str) -> float:
    """The true undulation: what the error-free model says."""
    latitude, longitude, _ = cartesian_to_geodetic(*TRUTH[station], ELLIPSOID)
    return GEOID.undulation(latitude, longitude).value


def _orthometric(station: str) -> float:
    return _height(station) - _undulation(station)


def _observations() -> list[Observation]:
    """Exact observations of every geocentric type, from the truth."""
    found: list[Observation] = []
    sigma_angle = math.radians(2.0 / 3600.0)

    def add(identifier, kind, stations, values, sigma, unit, **extra):
        found.append(
            Observation(
                id=identifier,
                type=kind,
                stations=stations,
                values=tuple(Quantity.from_std_dev(v, sigma, unit) for v in values),
                **extra,
            )
        )

    for index, (a, b) in enumerate((("A", "B"), ("B", "C"), ("B", "D"), ("D", "E"), ("E", "A"), ("C", "D"))):
        local = _geometry(a, b, 1.55, 1.70)
        add(
            f"s{index}",
            ObservationType.SLOPE_DISTANCE,
            (a, b),
            [float(np.linalg.norm(local))],
            0.002,
            Unit.METRE,
            instrument_height=Quantity.exact(1.55, Unit.METRE),
            target_height=Quantity.exact(1.70, Unit.METRE),
        )
        add(
            f"z{index}",
            ObservationType.ZENITH_ANGLE,
            (a, b),
            [math.atan2(math.hypot(local[0], local[1]), local[2])],
            sigma_angle,
            Unit.RADIAN,
            instrument_height=Quantity.exact(1.55, Unit.METRE),
            target_height=Quantity.exact(1.70, Unit.METRE),
        )
        plain = _geometry(a, b)
        add(
            f"d{index}",
            ObservationType.DIRECTION,
            (a, b),
            [math.atan2(plain[0], plain[1])],
            sigma_angle,
            Unit.RADIAN,
            setup_id=f"set-{a}",
            cluster_id=f"set-{a}",
        )
        add(
            f"h{index}",
            ObservationType.HORIZONTAL_DISTANCE,
            (a, b),
            [math.hypot(plain[0], plain[1])],
            0.003,
            Unit.METRE,
        )
    local = _geometry("B", "E")
    add("az", ObservationType.AZIMUTH, ("B", "E"), [math.atan2(local[0], local[1])], sigma_angle, Unit.RADIAN)
    add(
        "va",
        ObservationType.VERTICAL_ANGLE,
        ("B", "E"),
        [math.pi / 2 - math.atan2(math.hypot(local[0], local[1]), local[2])],
        sigma_angle,
        Unit.RADIAN,
    )
    back, fore = _geometry("D", "B"), _geometry("D", "E")
    add(
        "ang",
        ObservationType.HORIZONTAL_ANGLE,
        ("D", "B", "E"),
        [math.remainder(math.atan2(fore[0], fore[1]) - math.atan2(back[0], back[1]), math.tau)],
        sigma_angle,
        Unit.RADIAN,
    )
    add(
        "gE",
        ObservationType.GNSS_BASELINE,
        ("A", "D"),
        list(TRUTH["D"] - TRUTH["A"]),
        0.004,
        Unit.METRE,
        meta={BASELINE_FRAME_KEY: BaselineFrame.ECEF.value},
        cluster_id="cgE",
    )
    add(
        "gL",
        ObservationType.GNSS_BASELINE,
        ("C", "E"),
        list(_geometry("C", "E")),
        0.004,
        Unit.METRE,
        meta={BASELINE_FRAME_KEY: BaselineFrame.LOCAL.value},
        cluster_id="cgL",
    )
    add(
        "dh",
        ObservationType.HEIGHT_DIFFERENCE,
        ("A", "B"),
        [_height("B") - _height("A")],
        0.002,
        Unit.METRE,
        meta={HEIGHT_TYPE_KEY: HeightType.ELLIPSOIDAL.name},
    )
    # An orthometric difference: H differs from h by the undulation, about
    # -2 m here and changing by centimetres between B and E.
    add(
        "dH",
        ObservationType.HEIGHT_DIFFERENCE,
        ("B", "E"),
        [_orthometric("E") - _orthometric("B")],
        0.002,
        Unit.METRE,
        meta={HEIGHT_TYPE_KEY: HeightType.ORTHOMETRIC.name},
    )
    add("eh", ObservationType.ELLIPSOIDAL_HEIGHT, ("D",), [_height("D")], 0.01, Unit.METRE)
    add(
        "oh",
        ObservationType.ORTHOMETRIC_HEIGHT,
        ("B",),
        [_orthometric("B")],
        0.01,
        Unit.METRE,
    )
    add("pt", ObservationType.GNSS_POINT, ("E",), list(TRUTH["E"]), 0.02, Unit.METRE, cluster_id="cpt")
    return found


def network(*, perturb: float = 0.0, seed: int = 3) -> Network:
    rng = np.random.default_rng(seed)
    built = Network(id="curitiba", crs="EPSG:4988")
    for name, truth in TRUTH.items():
        constraint = (
            ConstraintSpec(
                mode=ConstraintMode.FIXED,
                components=frozenset({"x", "y", "z"}),
                position=_cartesian(truth),
            )
            if name in HELD
            else ConstraintSpec()
        )
        start = truth + rng.uniform(-perturb, perturb, 3)
        built.add_station(
            Station(id=name, approx_position=_cartesian(start, exact=False), constraint=constraint)
        )
    members: dict[str, list[Observation]] = {}
    for observation in _observations():
        built.add_observation(observation)
        if observation.cluster_id:
            members.setdefault(observation.cluster_id, []).append(observation)
    for cluster_id, group in members.items():
        variances = [v.variance for o in group for v in o.values]
        units = tuple(v.unit for o in group for v in o.values)
        built.add_cluster(
            Cluster(
                id=cluster_id,
                kind={
                    ObservationType.DIRECTION: ClusterKind.DIRECTION_SET,
                    ObservationType.GNSS_BASELINE: ClusterKind.GNSS_BASELINE,
                }.get(group[0].type, ClusterKind.GNSS_POINT),
                observation_ids=tuple(o.id for o in group),
                covariance=Covariance(
                    matrix=np.diag(variances),
                    labels=tuple(f"{o.id}.{k}" for o in group for k in range(len(o.values))),
                    units=units,
                ),
            )
        )
    return built


OPTIONS = AdjustmentOptions(frame=Frame.GEOCENTRIC_3D, datum=DatumDefinition.FIXED, geoid=GEOID)


@pytest.fixture(scope="module")
def setup():
    """The network, its layout, and a point 2 m from the truth to differentiate at."""
    built = network()
    auxiliary = {f"set-{s}": ("orientation",) for s in OFFSETS}
    auxiliary.update({"B": (UNDULATION,), "E": (UNDULATION,)})
    layout = ParameterLayout.build(built, Frame.GEOCENTRIC_3D, auxiliary=auxiliary)
    rng = np.random.default_rng(1)
    x = np.zeros(layout.size)
    for slot_index, slot in enumerate(layout.slots):
        if slot.kind == "station":
            x[slot_index] = TRUTH[slot.owner][("x", "y", "z").index(slot.component)] + rng.uniform(-2, 2)
        else:
            x[slot_index] = rng.uniform(-0.01, 0.01)
    return built, layout, x


class TestJacobians:
    """Every geocentric equation against its numerical derivative, at the same
    tolerance ``tests/test_adjustment.py`` holds the flat frames to. The
    turning of each station's frame is part of the derivative, and a Jacobian
    that left it out would fail here by about d / R."""

    def test_every_type_is_covered(self):
        assert {o.type for o in _observations()} == set(GEOCENTRIC_TYPES)

    @pytest.mark.parametrize("identifier", [o.id for o in _observations()])
    def test_the_analytic_jacobian_matches_the_numerical_one(self, setup, identifier):
        built, layout, x = setup
        observation = built.observations[identifier]
        rows = evaluate(observation, layout, x)
        analytic = np.array([row.to_dense(layout.size) for row in rows])

        def values(v):
            return np.array([row.computed for row in evaluate(observation, layout, np.asarray(v, float))])

        # A fixed 5 cm step. The default is relative to |x|: 38 m here, where X
        # and Y are millions of metres, and over a 1.5 km sight that step's own
        # truncation error is 5e-5, which would be blamed on the analytic side.
        # Too small a step fails the other way -- a coordinate of 6e6 m carries
        # 1e-9 m of rounding, which a 1 mm step turns into 1e-7 of derivative.
        # At 5 cm both are near 1e-8.
        numeric = central_difference_jacobian(values, x, step=0.05)
        scale = max(1.0, float(np.max(np.abs(numeric))))
        assert np.max(np.abs(analytic - numeric)) <= 1e-7 * scale


class TestTheNetworkIsRecovered:
    def test_exact_observations_return_the_truth_from_a_poor_start(self):
        """Every type at once, from starting coordinates up to 5 m out."""
        run = adjust(network(perturb=5.0), OPTIONS)
        assert run.converged
        for name in set(OFFSETS) - set(HELD):
            columns = run.layout.station_columns(name)
            estimate = np.array([run.parameters[columns[c]] for c in ("x", "y", "z")])
            assert np.max(np.abs(estimate - TRUTH[name])) < 1e-6, name

    def test_the_solution_is_cartesian_with_a_horizontal_ellipse(self):
        """X-Y is not a horizontal plane, so the ellipse is drawn in each
        station's own east-north plane -- and it must agree with rotating the
        covariance there by hand."""
        run = adjust(network(), OPTIONS)
        solution = to_solution(
            run,
            network(),
            solution_id="g",
            crs="EPSG:4988",
            epoch=Epoch.from_decimal_year(2026.7),
            datum=DatumDefinition.FIXED,
        )
        adjusted = {s.station_id: s for s in solution.adjusted_stations}
        station = adjusted["B"]
        assert station.position.system is CoordinateSystem.CARTESIAN
        latitude, longitude, _ = cartesian_to_geodetic(*(q.value for q in station.position.values), ELLIPSOID)
        rotation = enu_rotation(latitude, longitude)
        horizontal = (rotation @ np.asarray(station.covariance.matrix) @ rotation.T)[:2, :2]
        eigen = np.sqrt(np.linalg.eigvalsh(horizontal))
        assert station.ellipse is not None
        ratio = station.ellipse.semi_major / eigen.max()
        assert station.ellipse.semi_minor / eigen.min() == pytest.approx(ratio, rel=1e-9)


    def test_the_correction_is_stated_in_each_stations_horizon(self):
        """P13-12. A geocentric shift is turned into east, north and up at the
        station, as DynAdjust states its corrections and as the map draws them;
        X, Y and Z would be drawn as an arrow pointing nowhere in particular."""
        started = network(perturb=5.0)
        run = adjust(started, OPTIONS)
        solution = to_solution(
            run,
            started,
            solution_id="g",
            crs="EPSG:4988",
            epoch=Epoch.from_decimal_year(2026.7),
            datum=DatumDefinition.FIXED,
        )
        assert solution.adjusted_stations
        for station in solution.adjusted_stations:
            adjusted = np.array([q.value for q in station.position.values])
            start = np.array([q.value for q in started.stations[station.station_id].approx_position.values])
            latitude, longitude, _ = cartesian_to_geodetic(*adjusted, ELLIPSOID)
            expected = enu_rotation(latitude, longitude) @ (adjusted - start)
            assert station.correction == pytest.approx(tuple(expected), abs=1e-9)
            assert np.linalg.norm(station.correction) == pytest.approx(np.linalg.norm(adjusted - start))


class TestWhyTheFrameExists:
    def test_a_flat_frame_misreads_a_zenith_angle_three_kilometres_away(self):
        """The same zenith angle, A to C, read against A's vertical in the
        geocentric frame and against one shared vertical in a flat frame: at
        3 km the flat reading puts C about 0.7 m too high -- the curvature the
        flat frame assumes away."""
        local = _geometry("A", "C")
        horizontal = math.hypot(local[0], local[1])
        zenith = math.atan2(horizontal, local[2])
        flat_height_difference = horizontal / math.tan(zenith)
        true_difference = _height("C") - _height("A")
        assert flat_height_difference - true_difference == pytest.approx(
            -(horizontal**2) / (2 * 6.37e6), rel=0.02
        )
        assert abs(flat_height_difference - true_difference) > 0.6


class TestHeightSystems:
    def test_an_orthometric_observation_without_a_geoid_is_refused(self):
        """``specs/13`` criterion 2: it would be wrong by the undulation."""
        with pytest.raises(ValidationError) as caught:
            adjust(network(), AdjustmentOptions(frame=Frame.GEOCENTRIC_3D, datum=DatumDefinition.FIXED))
        assert caught.value.code == "validation.mixed_height_types"
        assert caught.value.context["stations"] == ["B", "E"]

    def test_a_height_difference_of_unstated_type_is_refused(self):
        built = network()
        observation = built.observations["dh"]
        built.observations["dh"] = Observation(
            id=observation.id,
            type=observation.type,
            stations=observation.stations,
            values=observation.values,
        )
        with pytest.raises(ValidationError) as caught:
            adjust(built, OPTIONS)
        assert caught.value.code == "validation.height_difference_type_unstated"

    def test_a_projected_position_is_refused_not_misread(self):
        built = network()
        station = built.stations["B"]
        built.stations["B"] = Station(
            id="B",
            approx_position=Position(
                values=tuple(Quantity.exact(v, Unit.METRE) for v in (500000.0, 7185000.0, 925.0)),
                system=CoordinateSystem.PROJECTED,
                crs="EPSG:31982",
                height_type=HeightType.ELLIPSOIDAL,
            ),
            constraint=station.constraint,
        )
        with pytest.raises(ValidationError) as caught:
            adjust(built, OPTIONS)
        assert caught.value.code == "validation.geocentric_frame_projected_position"

    def test_a_held_orthometric_position_is_refused(self):
        """Converted as though ellipsoidal, it would be held an undulation --
        two metres here, tens in much of Brazil -- from where it is."""
        built = network()
        latitude, longitude, height = cartesian_to_geodetic(*TRUTH["A"], ELLIPSOID)
        built.stations["A"] = Station(
            id="A",
            approx_position=built.stations["A"].approx_position,
            constraint=ConstraintSpec(
                mode=ConstraintMode.FIXED,
                components=frozenset({"latitude", "longitude", "height"}),
                position=Position(
                    values=(
                        Quantity.exact(latitude, Unit.RADIAN),
                        Quantity.exact(longitude, Unit.RADIAN),
                        Quantity.exact(height - _undulation("A"), Unit.METRE),
                    ),
                    system=CoordinateSystem.GEODETIC,
                    crs="EPSG:4988",
                    height_type=HeightType.ORTHOMETRIC,
                ),
            ),
        )
        with pytest.raises(ValidationError) as caught:
            adjust(built, OPTIONS)
        assert caught.value.code == "validation.geocentric_frame_orthometric_constraint"


class TestTheGeoidInTheCombination:
    """``specs/13`` section 3, items 2 to 5, in the geocentric frame."""

    def test_each_orthometric_station_gets_an_undulation_and_a_prior(self):
        run = adjust(network(), OPTIONS)
        assert list(run.undulations) == ["B", "E"]
        assert run.layout.column("B", UNDULATION) is not None
        assert run.layout.column("A", UNDULATION) is None
        for station, undulation in run.undulations.items():
            assert undulation.value == pytest.approx(_undulation(station))
            assert undulation.std_dev == pytest.approx(0.05)
        assert run.geoid_model == GEOID.id

    @pytest.mark.dense_only

    def test_the_model_used_is_recorded_on_the_solution(self):
        """Item 3, and FR-203: which model, and that its priors were taken as
        independent between stations -- an approximation, so the solution
        says it is one."""
        run = adjust(network(), OPTIONS)
        solution = to_solution(
            run,
            network(),
            solution_id="s",
            crs="EPSG:4988",
            epoch=Epoch.from_decimal_year(2026.7),
            datum=DatumDefinition.FIXED,
        )
        assert {s.position.geoid_model for s in solution.adjusted_stations} == {GEOID.id}
        assert Strategy.INDEPENDENCE_ASSUMED in solution.parameter_covariance.strategies
        assert solution.uncertainty_mode is UncertaintyMode.APPROXIMATE

    def test_a_model_wrong_by_twenty_centimetres_is_found_by_its_residuals(self):
        """Item 5. GNSS fixes the ellipsoidal heights and the orthometric
        observations the orthometric ones, so the network measures ``N`` itself
        and the prior's residual is how far the model was from it. Four times
        the model's stated 5 cm, so the w-test flags it; at twice, the prior
        still pulls the adjusted value 8 mm towards the model and the statistic
        sits just under 1.96."""
        run = adjust(
            network(),
            AdjustmentOptions(
                frame=Frame.GEOCENTRIC_3D, datum=DatumDefinition.FIXED, geoid=_geoid(offset=0.20)
            ),
        )
        residuals = {r.station_id: r for r in geoid_residuals(run)}
        assert set(residuals) == {"B", "E"}
        for station, result in residuals.items():
            assert result.model == pytest.approx(_undulation(station) + 0.20, abs=1e-9)
            assert result.adjusted == pytest.approx(_undulation(station), abs=0.02)
            assert result.residual == pytest.approx(-0.20, abs=0.02)
            assert result.model_std_dev == pytest.approx(0.05)
            assert result.redundancy > 0.5
            assert result.standardised < -1.96

    def test_an_exact_model_leaves_nothing_to_find(self):
        for result in geoid_residuals(adjust(network(), OPTIONS)):
            assert abs(result.residual) < 1e-6

    def test_a_point_outside_the_models_coverage_is_refused(self):
        far = GeoidModel(
            id="elsewhere",
            values=np.zeros((2, 2)),
            coverage=Coverage(0.0, 0.01, 0.0, 0.01),
            sigma=0.05,
        )
        with pytest.raises(ValidationError) as caught:
            adjust(
                network(),
                AdjustmentOptions(frame=Frame.GEOCENTRIC_3D, datum=DatumDefinition.FIXED, geoid=far),
            )
        assert caught.value.code == "validation.geoid_outside_coverage"


def _geodetic(station: str, *, height_type: HeightType = HeightType.ELLIPSOIDAL) -> Position:
    latitude, longitude, height = cartesian_to_geodetic(*TRUTH[station], ELLIPSOID)
    return Position(
        values=(
            Quantity.exact(latitude, Unit.RADIAN),
            Quantity.exact(longitude, Unit.RADIAN),
            Quantity.exact(height, Unit.METRE),
        ),
        system=CoordinateSystem.GEODETIC,
        crs="EPSG:4988",
        height_type=height_type,
    )


class TestGeodeticConstraints:
    """A control station published in latitude, longitude and height -- the
    ordinary form of one. Until P9a the geocentric frame matched the
    constraint's names against x, y and z, found none, and left it **free**."""

    @staticmethod
    def _held(mode: ConstraintMode, components=("latitude", "longitude", "height"), covariance=None):
        built = network(perturb=2.0)
        built.stations["C"] = Station(
            id="C",
            approx_position=built.stations["C"].approx_position,
            constraint=ConstraintSpec(
                mode=mode,
                components=frozenset(components),
                position=_geodetic("C"),
                covariance=covariance,
            ),
        )
        return built

    def test_a_geodetic_hold_holds_all_three_axes(self):
        run = adjust(self._held(ConstraintMode.FIXED), OPTIONS)
        assert run.layout.station_columns("C") == {}
        assert run.layout.fixed_values[("C", "x")] == pytest.approx(TRUTH["C"][0], abs=1e-6)

    def test_a_weighted_geodetic_hold_is_carried_to_x_y_z(self):
        """Its covariance is over radians and metres; read as metres, a
        latitude sigma of 1e-8 rad would be a 1e-8 m sigma -- 6 cm taken for a
        hundred-thousandth of a millimetre."""
        sigma_angle, sigma_height = 0.01 / 6.378e6, 0.02
        covariance = Covariance(
            matrix=np.diag([sigma_angle**2, sigma_angle**2, sigma_height**2]),
            labels=("latitude", "longitude", "height"),
            units=(Unit.RADIAN, Unit.RADIAN, Unit.METRE),
        )
        run = adjust(self._held(ConstraintMode.WEIGHTED, covariance=covariance), OPTIONS)
        labels = [label for label in run.system.row_labels if label[0] == "constraint:C"]
        assert [component for _, component in labels] == ["x", "y", "z"]
        rows = [run.system.row_labels.index(label) for label in labels]
        block = np.linalg.inv(run.system.weight[np.ix_(rows, rows)])
        latitude, longitude, height = cartesian_to_geodetic(*TRUTH["C"], ELLIPSOID)
        local = enu_rotation(latitude, longitude) @ block @ enu_rotation(latitude, longitude).T
        # A radian of latitude is M + h metres; one of longitude, (N + h) cos(phi).
        north = sigma_angle * (ELLIPSOID.meridian_radius(latitude) + height)
        east = sigma_angle * (ELLIPSOID.prime_vertical_radius(latitude) + height) * math.cos(latitude)
        assert math.sqrt(local[0, 0]) == pytest.approx(east, rel=1e-6)
        assert math.sqrt(local[1, 1]) == pytest.approx(north, rel=1e-6)
        assert math.sqrt(local[2, 2]) == pytest.approx(sigma_height, rel=1e-6)
        columns = run.layout.station_columns("C")
        adjusted = np.array([run.parameters[columns[c]] for c in ("x", "y", "z")])
        assert np.abs(adjusted - TRUTH["C"]).max() < 1e-4

    def test_a_height_alone_is_refused(self):
        with pytest.raises(ValidationError) as caught:
            adjust(self._held(ConstraintMode.FIXED, components=("height",)), OPTIONS)
        assert caught.value.code == "validation.geocentric_frame_partial_geodetic_constraint"
