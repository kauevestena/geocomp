# SPDX-License-Identifier: GPL-2.0-or-later
"""Integration: techniques adjusted together (``specs/13`` section 7, criteria 4 to 8).

The survey is ``tests/combined_network.py``'s six stations near Curitiba, split
the way it would arrive from the field -- four inputs, each in its own frame:

* **gnss**: three correlated baselines and an ellipsoidal height, processed in
  ITRF2014 at epoch 2020.0;
* **control**: the two held marks, published in SIRGAS 2000 -- that is, at epoch
  2000.4 -- with their velocities;
* **total-station**: direction sets, zenith angles and slope distances, which
  belong to no frame;
* **levelling**: an orthometric loop through the four free stations.

The combination is adjusted in ITRF2020 at 2020.0, which is where the truth is
defined, so every input needs something done to it and the answer can be checked
against the truth the measurements were drawn from.
"""

from __future__ import annotations

import math
from dataclasses import replace

import numpy as np
import pytest

from geocomp.core.adjustment.geocentric import ELLIPSOID, HEIGHT_TYPE_KEY
from geocomp.core.errors import ValidationError
from geocomp.core.geodesy.cartesian import cartesian_to_geodetic
from geocomp.core.geodesy.frames import transform_point, transform_vector
from geocomp.core.geoid import Coverage, GeoidModel
from geocomp.core.models import (
    Cluster,
    ClusterKind,
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
from geocomp.core.techniques.integration.adjustment import adjust_combination
from geocomp.core.techniques.integration.breakdown import GEOID as GEOID_ROWS
from geocomp.core.techniques.integration.combine import Velocity, combine, route
from geocomp.core.uncertainty import Quantity
from geocomp.core.units import Unit

from . import combined_network as field

TARGET_EPOCH = Epoch.from_decimal_year(2020.0)
GNSS_EPOCH = Epoch.from_decimal_year(2020.0)
#: A plate-interior velocity, the same at every station (they are 3 km apart).
VELOCITY = (-0.0020, -0.0055, 0.0118)
#: The truth is defined in ITRF2020 at 2020.0.
TRUTH = field.TRUTH


def _geoid(offset: float = 0.0) -> GeoidModel:
    """Planar, so interpolation is exact: -1 m at CTB1, tilting a few cm across."""
    span = 0.01
    lats = field.LATITUDE + np.array([-span, 0.0, span])
    lons = field.LONGITUDE + np.array([-span, 0.0, span])
    values = np.array(
        [
            [-1.0 + offset + 250.0 * (a - field.LATITUDE) + 150.0 * (b - field.LONGITUDE) for b in lons]
            for a in lats
        ]
    )
    return GeoidModel(
        id="curitiba-planar",
        values=values,
        coverage=Coverage(
            field.LATITUDE - span, field.LATITUDE + span, field.LONGITUDE - span, field.LONGITUDE + span
        ),
        sigma=0.03,
    )


GEOID = _geoid()


def _undulation(station: str) -> float:
    latitude, longitude, _ = cartesian_to_geodetic(*TRUTH[station], ELLIPSOID)
    return GEOID.undulation(latitude, longitude).value


def _cartesian(xyz, frame: str, epoch: Epoch, *, sigma: float | None = None) -> Position:
    make = (
        (lambda v: Quantity.exact(float(v), Unit.METRE))
        if sigma is None
        else (lambda v: Quantity.from_std_dev(float(v), sigma, Unit.METRE))
    )
    return Position(
        values=tuple(make(v) for v in xyz),
        system=CoordinateSystem.CARTESIAN,
        crs=frame,
        epoch=epoch,
        height_type=HeightType.ELLIPSOIDAL,
    )


def _free(network: Network, stations, frame: str, epoch: Epoch) -> None:
    rng = np.random.default_rng(len(network.id))
    for name in stations:
        start = TRUTH[name] + rng.uniform(-0.5, 0.5, 3)
        network.add_station(Station(id=name, approx_position=_cartesian(start, frame, epoch, sigma=1.0)))


def gnss_input() -> Network:
    """Baselines as processed in ITRF2014 at 2020.0: the truth's vectors,
    carried into that frame, with noise from their stated covariance."""
    network = Network(id="gnss", crs="ITRF2014", epoch=GNSS_EPOCH)
    _free(network, field.OFFSETS, "ITRF2014", GNSS_EPOCH)
    rng = np.random.default_rng(1)
    ids = []
    for base, rover in (("CTB1", "M05"), ("CTB2", "M04"), ("CTB1", "M06"), ("CTB2", "M03")):
        vector, _, _ = transform_vector(
            TRUTH[rover] - TRUTH[base], source="ITRF2020", target="ITRF2014", epoch=2020.0
        )
        noisy = vector + rng.multivariate_normal(np.zeros(3), field.GNSS_COVARIANCE)
        identifier = f"g-{base}-{rover}"
        network.add_observation(
            Observation(
                id=identifier,
                type=ObservationType.GNSS_BASELINE,
                stations=(base, rover),
                values=tuple(
                    Quantity(float(v), float(field.GNSS_COVARIANCE[k, k]), Unit.METRE)
                    for k, v in enumerate(noisy)
                ),
                cluster_id="gnss",
            )
        )
        ids.append(identifier)
    matrix = np.kron(np.eye(len(ids)), field.GNSS_COVARIANCE)
    network.add_cluster(
        Cluster(
            id="gnss",
            kind=ClusterKind.GNSS_BASELINE,
            observation_ids=tuple(ids),
            covariance=_covariance(matrix, [f"m{i}.{c}" for i in range(len(ids)) for c in "xyz"]),
        )
    )
    height = cartesian_to_geodetic(*TRUTH["M03"], ELLIPSOID)[2]
    shift = (
        transform_point(TRUTH["M03"], source="ITRF2020", target="ITRF2014", epoch=2020.0).xyz - TRUTH["M03"]
    )
    lat, lon, _ = cartesian_to_geodetic(*TRUTH["M03"], ELLIPSOID)
    from geocomp.core.geodesy.cartesian import enu_rotation

    up_shift = float(enu_rotation(lat, lon)[2] @ shift)
    network.add_observation(
        Observation(
            id="r-M03",
            type=ObservationType.ELLIPSOIDAL_HEIGHT,
            stations=("M03",),
            values=(Quantity.from_std_dev(height + up_shift + rng.normal(0, 0.01), 0.01, Unit.METRE),),
        )
    )
    return network


def _covariance(matrix, labels):
    from geocomp.core.uncertainty import Covariance

    return Covariance(matrix=np.asarray(matrix), labels=tuple(labels), units=(Unit.METRE,) * len(labels))


SIRGAS_EPOCH = Epoch.from_decimal_year(2000.4)


def control_input(*, crs: str = "SIRGAS2000") -> Network:
    """The two marks as SIRGAS 2000 publishes them: the truth carried back to
    ITRF2000 at 2000.4 along the velocity."""
    network = Network(id="control", crs=crs, epoch=SIRGAS_EPOCH)
    for name in field.HELD:
        published = transform_point(
            TRUTH[name],
            source="ITRF2020",
            target="SIRGAS2000",
            epoch=2020.0,
            velocity=_itrf2020_velocity(),
        ).xyz
        network.add_station(
            Station(
                id=name,
                approx_position=_cartesian(published, crs, SIRGAS_EPOCH, sigma=1.0),
                constraint=ConstraintSpec(
                    mode=ConstraintMode.FIXED,
                    components=frozenset({"x", "y", "z"}),
                    position=_cartesian(published, crs, SIRGAS_EPOCH),
                ),
            )
        )
    return network


def _itrf2020_velocity() -> tuple[float, float, float]:
    return VELOCITY


def sirgas_velocities() -> dict[str, Velocity]:
    """The same velocity as SIRGAS 2000 (ITRF2000) sees it, at each mark.

    Per mark, because it differs: the scale rate between the frames acts on
    position, 0.11 ppb a year on 3 km apart -- 0.3 micrometres a year, which
    twenty years make 6.
    """
    velocities = {}
    for name in field.HELD:
        moved = transform_point(
            TRUTH[name], source="ITRF2020", target="SIRGAS2000", epoch=2020.0, velocity=VELOCITY
        )
        velocities[name] = Velocity(tuple(float(v) for v in moved.velocity))
    return velocities


def total_station_input() -> Network:
    """The survey's terrestrial half: no frame, as a total station has none."""
    survey = field.survey(seed=7)
    network = Network(id="total-station")
    for name in field.OFFSETS:
        network.add_station(Station(id=name))
    for observation in survey.observations.values():
        if observation.type in (ObservationType.GNSS_BASELINE, ObservationType.ELLIPSOIDAL_HEIGHT):
            continue
        network.add_observation(observation)
    for cluster in survey.clusters.values():
        if cluster.kind is ClusterKind.DIRECTION_SET:
            network.add_cluster(cluster)
    return network


LOOP = (("M03", "M04"), ("M04", "M05"), ("M05", "M06"), ("M06", "M03"))


def levelling_input(*, typed: bool = True) -> Network:
    network = Network(id="levelling")
    for name in {s for pair in LOOP for s in pair}:
        network.add_station(Station(id=name))
    rng = np.random.default_rng(3)
    for a, b in LOOP:
        h = {s: cartesian_to_geodetic(*TRUTH[s], ELLIPSOID)[2] for s in (a, b)}
        orthometric = (h[b] - _undulation(b)) - (h[a] - _undulation(a))
        length = np.linalg.norm(TRUTH[b] - TRUTH[a]) / 1000.0
        sigma = 0.001 * math.sqrt(length)
        network.add_observation(
            Observation(
                id=f"l-{a}-{b}",
                type=ObservationType.HEIGHT_DIFFERENCE,
                stations=(a, b),
                values=(Quantity.from_std_dev(orthometric + rng.normal(0, sigma), sigma, Unit.METRE),),
                meta={HEIGHT_TYPE_KEY: HeightType.ORTHOMETRIC.name} if typed else {},
            )
        )
    return network


def inputs():
    return [gnss_input(), control_input(), total_station_input(), levelling_input()]


@pytest.fixture(scope="module")
def combination():
    return combine(inputs(), frame="ITRF2020", epoch=TARGET_EPOCH, velocities=sirgas_velocities())


@pytest.fixture(scope="module")
def adjusted(combination):
    return adjust_combination(combination, geoid=GEOID)


class TestCriterion4Frames:
    def test_two_frames_are_transformed_and_the_record_says_how(self, combination):
        subjects = {t.subject: t for t in combination.transformations}
        held = subjects["station CTB1 (fixed position)"]
        assert held.input_id == "control"
        assert [s.code or s.kind for s in held.record.steps] == ["EPSG:9052", "EPSG:9994", "epoch"]
        baseline = subjects["observation g-CTB1-M05"]
        assert baseline.input_id == "gnss"
        assert [s.code for s in baseline.record.steps] == ["EPSG:9991"]
        recorded = combination.provenance_parameters()["combination"]
        assert recorded["frame"] == "ITRF2020"
        assert len(recorded["transformations"]) == len(combination.transformations)

    def test_the_held_marks_arrive_where_the_truth_is(self, combination):
        """Published in SIRGAS 2000 at 2000.4, carried to ITRF2020 at 2020.0
        along their velocity: back to the truth to a micrometre."""
        for name in field.HELD:
            held = combination.network.stations[name].constraint.position
            assert held.crs == "ITRF2020"
            assert np.abs(np.array([q.value for q in held.values]) - TRUTH[name]).max() < 1e-6

    def test_an_irreconcilable_frame_is_refused_naming_the_input(self):
        with pytest.raises(ValidationError) as caught:
            combine(
                [gnss_input(), control_input(crs="WGS84")],
                frame="ITRF2020",
                epoch=TARGET_EPOCH,
                velocities=sirgas_velocities(),
            )
        assert caught.value.code == "validation.combination_frame_irreconcilable"
        assert caught.value.context["input"] == "control"
        assert caught.value.context["received"] == "WGS84"

    def test_a_held_mark_that_must_move_without_a_velocity_is_refused(self):
        with pytest.raises(ValidationError) as caught:
            combine([control_input()], frame="ITRF2020", epoch=TARGET_EPOCH)
        assert caught.value.code == "validation.combination_epoch_without_velocity"
        assert caught.value.context["input"] == "control"
        assert "CTB1" in caught.value.context["subject"]

    def test_gnss_without_an_epoch_is_refused_not_assumed(self):
        """FR-105: an input in a frame that moves, with no epoch, is not taken to
        be at the combination's -- even when the frames already agree."""
        gnss = gnss_input()
        gnss.epoch = None
        with pytest.raises(ValidationError) as caught:
            combine([gnss], frame="ITRF2014", epoch=TARGET_EPOCH)
        assert caught.value.code == "validation.combination_input_without_epoch"
        assert caught.value.context["input"] == "gnss"

    def test_gnss_without_a_frame_is_refused_not_assumed(self):
        gnss = gnss_input()
        gnss.crs = ""
        with pytest.raises(ValidationError) as caught:
            combine([gnss], frame="ITRF2020", epoch=TARGET_EPOCH)
        assert caught.value.code == "validation.combination_input_without_frame"

    def test_a_position_without_a_frame_is_refused(self):
        control = control_input()
        control.crs = ""
        with pytest.raises(ValidationError) as caught:
            combine([control], frame="ITRF2020", epoch=TARGET_EPOCH, velocities=sirgas_velocities())
        assert caught.value.code == "validation.combination_input_without_frame"


class TestCriterion5Clusters:
    def test_the_baseline_cluster_survives_whole(self, combination):
        """Its 12 x 12 covariance carried through the transformation -- parts
        per billion -- and every member still in it, in order."""
        cluster = combination.network.clusters["gnss"]
        assert cluster.observation_ids == ("g-CTB1-M05", "g-CTB2-M04", "g-CTB1-M06", "g-CTB2-M03")
        matrix = np.asarray(cluster.covariance.matrix)
        expected = np.kron(np.eye(4), field.GNSS_COVARIANCE)
        assert matrix.shape == (12, 12)
        assert np.allclose(matrix, expected, rtol=1e-8, atol=0)
        assert matrix[0, 1] != 0.0

    def test_the_direction_sets_survive_whole(self, combination):
        sets = [c for c in combination.network.clusters.values() if c.kind is ClusterKind.DIRECTION_SET]
        assert len(sets) == len(field.SETUPS)

    def test_every_observation_knows_its_technique(self, combination):
        assert set(combination.techniques) == {"gnss", "total_station", "levelling"}
        assert all("technique" in o.meta for o in combination.network.observations.values())


class TestCriterion6Routing:
    def test_gravity_goes_in_house_with_the_reason(self):
        network = Network(id="g")
        network.add_station(Station(id="A"))
        network.add_station(Station(id="B"))
        network.add_observation(
            Observation(
                id="dg",
                type=ObservationType.GRAVITY_DIFFERENCE,
                stations=("A", "B"),
                values=(Quantity.from_std_dev(1e-5, 1e-8, Unit.ACCELERATION),),
            )
        )
        routing = route(network, "dynadjust")
        assert routing.engine == "in_house"
        assert "gravity" in routing.reason and "DynAdjust" in routing.reason
        assert routing.gravity_observations == ("dg",)

    def test_without_gravity_dynadjust_is_honoured(self, combination):
        assert route(combination.network, "dynadjust").engine == "dynadjust"

    def test_a_type_dynadjust_lacks_keeps_the_whole_combination_in_house(self, combination):
        """A horizontal distance has no DynAdjust type. Sending the rest would
        adjust a different network, so none of it goes, and the reason says so."""
        network = replace(combination.network, observations=dict(combination.network.observations))
        network.observations["hd"] = Observation(
            id="hd",
            type=ObservationType.HORIZONTAL_DISTANCE,
            stations=("M03", "M04"),
            values=(Quantity.from_std_dev(1234.5, 0.003, Unit.METRE),),
        )
        routing = route(network, "dynadjust")
        assert routing.engine == "in_house"
        assert "horizontal_distance" in routing.reason

    def test_gravity_is_adjusted_beside_the_geometry_not_dropped(self, combination):
        from geocomp.core.techniques.gravimetry import build_gravity_network, reduce_readings
        from tests.test_gravimetry_network import _held_at_truth, _library, _readings

        library = _library("Test2")
        gravity = build_gravity_network(reduce_readings(_readings("Test2"), library), library)
        _held_at_truth(gravity)
        result = adjust_combination(combination, geoid=GEOID, requested_engine="dynadjust", gravity=gravity)
        assert result.routing.engine == "in_house"
        assert "gravity" in result.routing.reason
        assert result.gravity is not None
        assert result.gravity.solution.statistics.converged
        assert result.solution.provenance.parameters["routing"]["engine"] == "in_house"

    def test_dynadjust_asked_for_and_allowed_is_not_quietly_replaced(self, combination):
        with pytest.raises(ValidationError) as caught:
            adjust_combination(combination, geoid=GEOID, requested_engine="dynadjust")
        assert caught.value.code == "validation.combination_routed_to_dynadjust"

    def test_gravity_merged_into_the_geometry_is_refused(self, combination):
        network = combination.network
        merged = replace(network, observations=dict(network.observations))
        merged.observations["dg"] = Observation(
            id="dg",
            type=ObservationType.GRAVITY_DIFFERENCE,
            stations=("M03", "M04"),
            values=(Quantity.from_std_dev(1e-5, 1e-8, Unit.ACCELERATION),),
        )
        with pytest.raises(ValidationError) as caught:
            adjust_combination(replace(combination, network=merged), geoid=GEOID)
        assert caught.value.code == "validation.combination_gravity_without_its_network"


class TestCriterion8ThreeTechniques:
    def test_one_solution_near_the_truth(self, adjusted):
        solution = adjusted.solution
        assert solution.crs == "ITRF2020"
        assert solution.statistics.converged
        for station in solution.adjusted_stations:
            ours = np.array([q.value for q in station.position.values])
            assert np.abs(ours - TRUTH[station.station_id]).max() < 0.02, station.station_id

    def test_the_geoid_model_is_on_the_solution(self, adjusted):
        assert {s.position.geoid_model for s in adjusted.solution.adjusted_stations} == {GEOID.id}
        assert {r.station_id for r in adjusted.geoid} == {"M03", "M04", "M05", "M06"}

    def test_the_provenance_names_every_input(self, adjusted):
        parameters = adjusted.solution.provenance.parameters
        assert parameters["combination"]["inputs"] == ["gnss", "control", "total-station", "levelling"]
        assert parameters["geoid_model"] == GEOID.id

    def test_an_untyped_levelled_difference_is_refused_not_guessed(self):
        combined = combine(
            [gnss_input(), control_input(), total_station_input(), levelling_input(typed=False)],
            frame="ITRF2020",
            epoch=TARGET_EPOCH,
            velocities=sirgas_velocities(),
        )
        with pytest.raises(ValidationError) as caught:
            adjust_combination(combined, geoid=GEOID)
        assert caught.value.code == "validation.height_difference_type_unstated"


class TestCriterion7Breakdown:
    def test_every_technique_and_the_geoid_are_reported(self, adjusted):
        groups = [s.technique for s in adjusted.breakdown]
        assert set(groups) == {"gnss", "total_station", "levelling", GEOID_ROWS}

    def test_it_adds_up(self, adjusted):
        run = adjusted.run
        total = float(run.residuals @ run.system.weight @ run.residuals)
        assert sum(s.weighted_squares for s in adjusted.breakdown) == pytest.approx(total, rel=1e-9)
        assert sum(s.redundancy for s in adjusted.breakdown) == pytest.approx(
            run.degrees_of_freedom, rel=1e-9
        )
        assert sum(s.redundancy_share for s in adjusted.breakdown) == pytest.approx(1.0)
        assert sum(s.rows for s in adjusted.breakdown) == run.system.observation_count

    def test_the_levelling_carries_its_loops_closure(self, adjusted):
        """GNSS and the total station fix the ellipsoidal heights, so four
        levelled differences over four undulations leave the levelling one
        thing to check: its loop's closure. A redundancy of one, which the
        breakdown makes visible and an overall figure would hide."""
        levelling = next(s for s in adjusted.breakdown if s.technique == "levelling")
        assert levelling.rows == 4
        assert levelling.redundancy == pytest.approx(1.0, abs=0.02)

    def test_variance_components_by_technique_on_the_combination(self, combination):
        """The estimator on combined data (criterion 3 is shown on its own
        survey in ``test_variance_components.py``): one factor per technique,
        the geoid priors as the known part, and the factors on the provenance."""
        result = adjust_combination(combination, geoid=GEOID, estimate_components=True)
        groups = [c.group for c in result.variance_components.components]
        assert groups == ["gnss", "total_station", "levelling"]
        assert all(c.factor > 0 and c.std_dev > 0 for c in result.variance_components.components)
        recorded = result.solution.provenance.parameters["variance_components"]
        assert set(recorded) == set(groups)


class TestIdentifiers:
    def test_colliding_ids_are_namespaced_and_recorded(self):
        first, second = levelling_input(), levelling_input()
        second.id = "levelling-2"
        combined = combine([first, second], frame="ITRF2020", epoch=TARGET_EPOCH)
        assert "levelling-2:l-M03-M04" in combined.network.observations
        assert combined.renamed["levelling-2:l-M03-M04"] == ("levelling-2", "l-M03-M04")
        assert "l-M03-M04" in combined.network.observations
        # Stations are never renamed: the same mark in two inputs is the tie.
        assert set(combined.network.stations) == {"M03", "M04", "M05", "M06"}

    def test_two_setups_of_one_name_keep_two_orientations(self):
        first, second = total_station_input(), total_station_input()
        second.id = "total-station-2"
        combined = combine([first, second], frame="ITRF2020", epoch=TARGET_EPOCH)
        setups = {o.setup_id for o in combined.network.observations.values() if o.setup_id}
        assert len(setups) == 2 * len(field.SETUPS)

    def test_a_station_held_in_two_places_is_refused(self):
        other = control_input()
        station = other.stations["CTB1"]
        shifted = replace(
            station.constraint,
            position=replace(
                station.constraint.position,
                values=tuple(
                    Quantity.exact(q.value + 0.05, Unit.METRE) for q in station.constraint.position.values
                ),
            ),
        )
        other.stations["CTB1"] = replace(station, constraint=shifted)
        other.id = "control-2"
        with pytest.raises(ValidationError) as caught:
            combine(
                [control_input(), other], frame="ITRF2020", epoch=TARGET_EPOCH, velocities=sirgas_velocities()
            )
        assert caught.value.code == "validation.combination_station_held_differently"
        assert caught.value.context["received"] == ["control", "control-2"]
