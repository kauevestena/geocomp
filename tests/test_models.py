# SPDX-License-Identifier: GPL-2.0-or-later
"""The domain model (specs/04).

Organised around the three rules that make the model worth having, because each
one prevents a *plausible-looking wrong answer* rather than an obvious error:

* every geodetic value carries its uncertainty (FR-200);
* every coordinate set carries its CRS and epoch, and operations refuse rather
  than assume (FR-105);
* correlated observations stay clustered (FR-104).
"""

from __future__ import annotations

import json
import math
from datetime import UTC, datetime

import numpy as np
import pytest

from geocomp.core.errors import DataError, ValidationError
from geocomp.core.models import (
    OBSERVATION_TYPES,
    AdjustedStation,
    Campaign,
    Cluster,
    ClusterKind,
    ConstraintMode,
    ConstraintSpec,
    CoordinateSystem,
    DatumDefinition,
    Epoch,
    GnssSession,
    HeightType,
    MonitoringRole,
    Network,
    Observation,
    ObservationResult,
    ObservationStatus,
    ObservationType,
    Position,
    Project,
    Provenance,
    RejectionRecord,
    Solution,
    SolutionKind,
    Station,
    StationType,
    require_epoch,
)
from geocomp.core.uncertainty import Covariance, Quantity, UncertaintyMode
from geocomp.core.units import Unit

METRE, RADIAN, ACCEL = Unit.METRE, Unit.RADIAN, Unit.ACCELERATION
EPOCH = Epoch.from_decimal_year(2026.65, "test epoch")


def metres(value: float, sigma: float = 0.01) -> Quantity:
    return Quantity.from_std_dev(value, sigma, METRE)


def projected(easting: float, northing: float, height: float = 0.0, **kwargs) -> Position:
    defaults = {
        "system": CoordinateSystem.PROJECTED,
        "crs": "EPSG:31982",
        "epoch": EPOCH,
        "height_type": HeightType.ORTHOMETRIC,
    }
    return Position(values=(metres(easting), metres(northing), metres(height)), **{**defaults, **kwargs})


class TestEpoch:
    def test_decimal_year_from_an_instant(self):
        epoch = Epoch.from_datetime(datetime(2026, 7, 2, 12, tzinfo=UTC))
        assert epoch.decimal_year == pytest.approx(2026.5, abs=0.01)

    def test_a_naive_datetime_is_refused(self):
        """Timezone-naive instants are how epochs quietly shift by hours."""
        with pytest.raises(ValidationError) as caught:
            Epoch.from_datetime(datetime(2026, 7, 2, 12))
        assert caught.value.code == "validation.epoch_instant_naive"

    def test_years_since_is_signed(self):
        later = Epoch.from_decimal_year(2027.0)
        assert later.years_since(Epoch.from_decimal_year(2026.0)) == pytest.approx(1.0)

    def test_require_epoch_refuses_absence_rather_than_defaulting(self):
        """FR-105. An assumed epoch produces a confidently wrong displacement."""
        with pytest.raises(ValidationError) as caught:
            require_epoch(None, operation="compare epochs", subject="solution s1")
        assert caught.value.code == "validation.epoch_required"
        assert "will not assume" in caught.value.context["expected"]

    def test_require_epoch_passes_a_present_one_through(self):
        assert require_epoch(EPOCH, operation="x") is EPOCH

    def test_round_trip(self):
        original = Epoch.from_datetime(datetime(2026, 7, 2, 12, tzinfo=UTC), "campaign 1")
        assert Epoch.from_dict(original.to_dict()) == original


class TestPosition:
    def test_components_must_be_quantities_not_floats(self):
        """FR-200 enforced at the type boundary, not by convention."""
        with pytest.raises(ValidationError) as caught:
            Position(values=(1.0, 2.0, 3.0), system=CoordinateSystem.PROJECTED, crs="EPSG:31982")
        assert caught.value.code == "validation.position_component_not_a_quantity"

    def test_geodetic_components_must_be_angles_and_a_height(self):
        with pytest.raises(ValidationError) as caught:
            Position(
                values=(metres(1.0), metres(2.0), metres(3.0)),
                system=CoordinateSystem.GEODETIC,
                crs="EPSG:4674",
            )
        assert caught.value.code == "validation.position_component_unit"

    def test_a_position_without_a_crs_is_refused(self):
        with pytest.raises(ValidationError) as caught:
            Position(values=(metres(1), metres(2), metres(3)), system=CoordinateSystem.PROJECTED, crs="")
        assert caught.value.code == "validation.position_without_crs"

    def test_components_are_reachable_by_name(self):
        position = projected(100.0, 200.0, 5.0)
        assert position.component("easting").value == pytest.approx(100.0)
        assert position.component("northing").value == pytest.approx(200.0)

    def test_an_unknown_component_lists_the_valid_names(self):
        with pytest.raises(ValidationError) as caught:
            projected(1, 2).component("latitude")
        assert caught.value.context["expected"] == ["easting", "northing", "up"]

    def test_mixing_height_types_is_refused(self):
        """FR-802 / FR-804: in much of Brazil this error is tens of metres, and
        the resulting numbers look entirely reasonable."""
        orthometric = projected(1, 2, 3)
        ellipsoidal = projected(1, 2, 3, height_type=HeightType.ELLIPSOIDAL)
        with pytest.raises(ValidationError) as caught:
            orthometric.require_comparable_height(ellipsoidal, "difference")
        assert caught.value.code == "validation.incompatible_height_types"

    def test_matching_height_types_are_comparable(self):
        projected(1, 2, 3).require_comparable_height(projected(4, 5, 6), "difference")

    def test_two_dimensional_positions_impose_no_height_constraint(self):
        flat = projected(1, 2, height_type=HeightType.NONE)
        flat.require_comparable_height(projected(1, 2, 3), "difference")

    def test_round_trip(self):
        original = projected(1.5, 2.5, 3.5, geoid_model="MAPGEO2015")
        restored = Position.from_dict(original.to_dict())
        assert restored.crs == original.crs
        assert restored.geoid_model == "MAPGEO2015"
        assert restored.values[0].value == original.values[0].value


class TestObservationTypeRegistry:
    def test_every_type_is_registered(self):
        assert set(OBSERVATION_TYPES) == set(ObservationType)

    def test_every_spec_is_internally_consistent(self):
        for spec in OBSERVATION_TYPES.values():
            assert len(spec.components) == len(spec.units)
            assert spec.arity >= 1
            assert spec.dimensionality

    def test_gravity_has_no_dynadjust_equivalent(self):
        """The clearest refutation of the archived roadmap's premise: a required
        menu group with no engine behind it (ADR-0002)."""
        for observation_type in (ObservationType.GRAVITY, ObservationType.GRAVITY_DIFFERENCE):
            assert OBSERVATION_TYPES[observation_type].dynadjust_code is None

    def test_gnss_types_carry_verified_dynadjust_codes(self):
        assert OBSERVATION_TYPES[ObservationType.GNSS_BASELINE].dynadjust_code == "G"
        assert OBSERVATION_TYPES[ObservationType.GNSS_POINT].dynadjust_code == "Y"
        assert OBSERVATION_TYPES[ObservationType.GNSS_BASELINE].dynadjust_verified

    def test_unverified_mappings_are_marked_not_silently_trusted(self):
        """specs/07 section 4.2 marks unconfirmed codes [C]. Anything carrying a
        code must either be verified or have no code at all -- a guessed code
        would produce a file DynAdjust accepts and adjusts wrongly."""
        for spec in OBSERVATION_TYPES.values():
            if spec.dynadjust_code is not None:
                assert spec.dynadjust_verified, f"{spec.type.value} has an unverified code"

    def test_correlated_types_are_marked_as_always_clustered(self):
        for observation_type in (
            ObservationType.GNSS_BASELINE,
            ObservationType.GNSS_POINT,
            ObservationType.DIRECTION,
        ):
            assert OBSERVATION_TYPES[observation_type].always_clustered

    def test_gravity_is_a_one_dimensional_problem(self):
        assert OBSERVATION_TYPES[ObservationType.GRAVITY].dimensionality == frozenset({1})


class TestObservation:
    def test_arity_is_enforced(self):
        with pytest.raises(DataError) as caught:
            Observation(
                id="a",
                type=ObservationType.HORIZONTAL_ANGLE,
                stations=("1", "2"),
                values=(Quantity.from_std_dev(1.0, 0.1, RADIAN),),
            )
        assert caught.value.code == "data.observation_arity"
        assert caught.value.context["expected"] == 3

    def test_units_are_enforced(self):
        with pytest.raises(DataError) as caught:
            Observation(
                id="b",
                type=ObservationType.SLOPE_DISTANCE,
                stations=("1", "2"),
                values=(Quantity.from_std_dev(1.0, 0.1, RADIAN),),
            )
        assert caught.value.code == "data.observation_value_unit"

    def test_values_must_be_quantities(self):
        with pytest.raises(DataError) as caught:
            Observation(
                id="c", type=ObservationType.SLOPE_DISTANCE, stations=("1", "2"), values=(10.0,)
            )
        assert caught.value.code == "data.observation_value_not_a_quantity"

    def test_a_correlated_type_requires_a_cluster(self):
        """FR-104: three components of a GNSS baseline are not three scalars."""
        with pytest.raises(DataError) as caught:
            Observation(
                id="d",
                type=ObservationType.GNSS_BASELINE,
                stations=("1", "2"),
                values=tuple(metres(v, 0.002) for v in (1.0, 2.0, 3.0)),
            )
        assert caught.value.code == "data.observation_requires_cluster"

    def test_with_a_cluster_the_same_observation_is_accepted(self):
        observation = Observation(
            id="d",
            type=ObservationType.GNSS_BASELINE,
            stations=("1", "2"),
            values=tuple(metres(v, 0.002) for v in (1.0, 2.0, 3.0)),
            cluster_id="c1",
        )
        assert observation.cluster_id == "c1"

    def test_an_active_observation_cannot_carry_a_rejection(self):
        with pytest.raises(DataError):
            Observation(
                id="e",
                type=ObservationType.SLOPE_DISTANCE,
                stations=("1", "2"),
                values=(metres(10.0),),
                status=ObservationStatus.ACTIVE,
                rejection=RejectionRecord(reason="outlier"),
            )

    def test_rejection_is_recorded_not_deleted(self):
        """FR-255. In a monitoring network the displacement being measured is
        exactly what an automatic outlier remover would delete."""
        observation = Observation(
            id="f",
            type=ObservationType.SLOPE_DISTANCE,
            stations=("1", "2"),
            values=(metres(10.0),),
            status=ObservationStatus.REJECTED,
            rejection=RejectionRecord(reason="w-test", test="baarda", statistic=4.2),
        )
        assert not observation.is_active
        assert observation.rejection.statistic == pytest.approx(4.2)

    def test_scalar_accessor_refuses_a_multi_component_observation(self):
        observation = Observation(
            id="g",
            type=ObservationType.GNSS_BASELINE,
            stations=("1", "2"),
            values=tuple(metres(v) for v in (1.0, 2.0, 3.0)),
            cluster_id="c",
        )
        with pytest.raises(ValidationError):
            _ = observation.value

    def test_dimensionality_is_queryable(self):
        gravity = Observation(
            id="h",
            type=ObservationType.GRAVITY,
            stations=("1",),
            values=(Quantity.from_std_dev(9.78, 1e-7, ACCEL),),
        )
        assert gravity.supports_dimension(1)
        assert not gravity.supports_dimension(3)

    def test_round_trip(self):
        original = Observation(
            id="i",
            type=ObservationType.ZENITH_ANGLE,
            stations=("1", "2"),
            values=(Quantity.from_std_dev(math.radians(88.13), 2.4e-5, RADIAN),),
            epoch=EPOCH,
            instrument_id="ts-01",
        )
        assert Observation.from_dict(original.to_dict()).to_dict() == original.to_dict()


class TestCluster:
    def test_the_covariance_must_match_the_member_count(self):
        with pytest.raises(DataError) as caught:
            Cluster(
                id="c",
                kind=ClusterKind.GNSS_BASELINE,
                observation_ids=("a", "b"),
                covariance=Covariance(np.eye(3), ("x", "y", "z"), (METRE,) * 3),
            )
        assert caught.value.code == "data.cluster_size_mismatch"

    def test_duplicate_members_are_refused(self):
        with pytest.raises(DataError):
            Cluster(
                id="c",
                kind=ClusterKind.GNSS_BASELINE,
                observation_ids=("a", "a"),
                covariance=Covariance(np.eye(2), ("x", "y"), (METRE, METRE)),
            )

    def test_round_trip_preserves_the_covariance_exactly(self):
        original = Cluster(
            id="c",
            kind=ClusterKind.GNSS_BASELINE,
            observation_ids=("a", "b"),
            covariance=Covariance(
                np.array([[4e-6, 1e-6], [1e-6, 9e-6]]), ("a", "b"), (METRE, METRE)
            ),
        )
        restored = Cluster.from_dict(original.to_dict())
        assert np.array_equal(restored.covariance.matrix, original.covariance.matrix)


class TestConstraints:
    def test_a_free_station_carries_no_constraint_detail(self):
        assert ConstraintSpec().is_free

    def test_a_free_constraint_with_detail_is_refused(self):
        with pytest.raises(ValidationError):
            ConstraintSpec(mode=ConstraintMode.FREE, components=frozenset({"easting"}))

    def test_a_constraint_needs_a_position(self):
        with pytest.raises(ValidationError) as caught:
            ConstraintSpec(mode=ConstraintMode.FIXED, components=frozenset({"easting"}))
        assert caught.value.code == "validation.constraint_without_position"

    def test_a_constraint_needs_components(self):
        with pytest.raises(ValidationError) as caught:
            ConstraintSpec(mode=ConstraintMode.FIXED, position=projected(1, 2, 3))
        assert caught.value.code == "validation.constraint_without_components"

    def test_a_weighted_constraint_needs_a_covariance(self):
        """Without one it is a fixed constraint under another name."""
        with pytest.raises(ValidationError) as caught:
            ConstraintSpec(
                mode=ConstraintMode.WEIGHTED,
                components=frozenset({"up"}),
                position=projected(1, 2, 3),
            )
        assert caught.value.code == "validation.weighted_constraint_without_covariance"

    def test_per_component_constraint_is_expressible(self):
        """The routine case: a benchmark fixed in height and free in plan."""
        constraint = ConstraintSpec(
            mode=ConstraintMode.FIXED,
            components=frozenset({"up"}),
            position=projected(1, 2, 3),
        )
        assert constraint.constrains("up")
        assert not constraint.constrains("easting")

    def test_unknown_components_are_refused(self):
        with pytest.raises(ValidationError) as caught:
            ConstraintSpec(
                mode=ConstraintMode.FIXED,
                components=frozenset({"latitude"}),
                position=projected(1, 2, 3),
            )
        assert caught.value.code == "validation.constraint_unknown_components"

    def test_round_trip(self):
        original = ConstraintSpec(
            mode=ConstraintMode.FIXED, components=frozenset({"up"}), position=projected(1, 2, 3)
        )
        assert ConstraintSpec.from_dict(original.to_dict()).components == original.components


class TestStation:
    def test_a_station_needs_an_identifier(self):
        with pytest.raises(DataError):
            Station(id="  ")

    def test_display_name_falls_back_to_the_identifier(self):
        assert Station(id="RN-42").display_name == "RN-42"
        assert Station(id="RN-42", name="Marco 42").display_name == "Marco 42"

    def test_a_planned_station_is_recognised(self):
        assert Station(id="p1", station_type=StationType.PLANNED).is_planned

    def test_monitoring_roles(self):
        assert Station(id="r1", monitoring_role=MonitoringRole.REFERENCE).is_reference
        assert not Station(id="o1", monitoring_role=MonitoringRole.OBJECT).is_reference

    def test_round_trip(self):
        original = Station(
            id="1",
            name="Marco 1",
            approx_position=projected(100.0, 200.0, 5.0),
            station_type=StationType.BENCHMARK,
            monitoring_role=MonitoringRole.REFERENCE,
        )
        assert Station.from_dict(original.to_dict()).to_dict() == original.to_dict()


class TestNetwork:
    @pytest.fixture
    def network(self):
        net = Network(id="tri", crs="EPSG:31982", epoch=EPOCH)
        for station_id, (easting, northing) in {"1": (0.0, 0.0), "2": (11.5, 0.0), "3": (5.2, 12.0)}.items():
            net.add_station(Station(id=station_id, approx_position=projected(easting, northing)))
        net.add_observation(
            Observation(
                id="d12",
                type=ObservationType.HORIZONTAL_DISTANCE,
                stations=("1", "2"),
                values=(metres(11.508, 0.003),),
            )
        )
        return net

    def test_a_consistent_network_validates_clean(self, network):
        assert network.validate() == []

    def test_an_unknown_station_reference_is_reported_not_raised(self, network):
        """FR-166: an importer must report every bad record, not stop at the first."""
        network.add_observation(
            Observation(
                id="d19",
                type=ObservationType.HORIZONTAL_DISTANCE,
                stations=("1", "ghost"),
                values=(metres(5.0),),
            )
        )
        problems = network.validate()
        assert len(problems) == 1
        assert "ghost" in problems[0]

    def test_require_valid_raises_with_every_problem(self, network):
        network.add_observation(
            Observation(
                id="bad",
                type=ObservationType.HORIZONTAL_DISTANCE,
                stations=("nope", "nowhere"),
                values=(metres(5.0),),
            )
        )
        with pytest.raises(DataError) as caught:
            network.require_valid()
        assert len(caught.value.context["problems"]) == 2

    def test_duplicate_ids_are_refused(self, network):
        with pytest.raises(DataError):
            network.add_station(Station(id="1"))
        with pytest.raises(DataError):
            network.add_observation(
                Observation(
                    id="d12",
                    type=ObservationType.HORIZONTAL_DISTANCE,
                    stations=("1", "2"),
                    values=(metres(1.0),),
                )
            )

    def test_a_dangling_cluster_reference_is_reported(self, network):
        network.add_observation(
            Observation(
                id="b13",
                type=ObservationType.GNSS_BASELINE,
                stations=("1", "3"),
                values=tuple(metres(v, 0.002) for v in (5.2, 12.0, 0.3)),
                cluster_id="missing",
            )
        )
        assert any("missing" in problem for problem in network.validate())

    def test_active_observations_exclude_rejected_ones(self, network):
        network.add_observation(
            Observation(
                id="d13",
                type=ObservationType.HORIZONTAL_DISTANCE,
                stations=("1", "3"),
                values=(metres(13.0),),
                status=ObservationStatus.REJECTED,
                rejection=RejectionRecord(reason="outlier"),
            )
        )
        assert {o.id for o in network.active_observations} == {"d12"}

    def test_observations_at_a_station(self, network):
        assert {o.id for o in network.observations_at("2")} == {"d12"}


class TestGnssSession:
    def test_a_session_that_ends_before_it_starts_is_refused(self):
        with pytest.raises(DataError) as caught:
            GnssSession(
                id="s1",
                station_id="1",
                start=datetime(2026, 8, 26, 12, tzinfo=UTC),
                end=datetime(2026, 8, 26, 10, tzinfo=UTC),
            )
        assert caught.value.code == "data.gnss_session_ends_before_it_starts"

    def test_antenna_height_must_be_a_length(self):
        with pytest.raises(DataError):
            GnssSession(id="s", station_id="1", antenna_height=Quantity.from_std_dev(1.5, 0.002, RADIAN))

    def test_overlap_detection_finds_baseline_candidates(self):
        first = GnssSession(
            id="a",
            station_id="1",
            start=datetime(2026, 8, 26, 10, tzinfo=UTC),
            end=datetime(2026, 8, 26, 14, tzinfo=UTC),
        )
        overlapping = GnssSession(
            id="b",
            station_id="2",
            start=datetime(2026, 8, 26, 12, tzinfo=UTC),
            end=datetime(2026, 8, 26, 16, tzinfo=UTC),
        )
        disjoint = GnssSession(
            id="c",
            station_id="3",
            start=datetime(2026, 8, 26, 15, tzinfo=UTC),
            end=datetime(2026, 8, 26, 18, tzinfo=UTC),
        )
        assert first.overlaps(overlapping)
        assert not first.overlaps(disjoint)

    def test_sessions_without_times_do_not_claim_to_overlap(self):
        assert not GnssSession(id="a", station_id="1").overlaps(GnssSession(id="b", station_id="2"))

    def test_duration(self):
        session = GnssSession(
            id="a",
            station_id="1",
            start=datetime(2026, 8, 26, 10, tzinfo=UTC),
            end=datetime(2026, 8, 26, 14, tzinfo=UTC),
        )
        assert session.duration_seconds == pytest.approx(4 * 3600)


class TestSolution:
    def test_a_solution_without_an_epoch_is_refused(self):
        """FR-105 enforced at construction, not only at comparison time."""
        with pytest.raises(ValidationError) as caught:
            Solution(
                id="s", network_id="n", kind=SolutionKind.ADJUSTMENT, crs="EPSG:31982", epoch=None
            )
        assert caught.value.code == "validation.solution_without_epoch"

    def test_a_solution_without_a_crs_is_refused(self):
        with pytest.raises(ValidationError):
            Solution(id="s", network_id="n", kind=SolutionKind.ADJUSTMENT, crs="", epoch=EPOCH)

    @pytest.fixture
    def solution(self):
        return Solution(
            id="s1",
            network_id="tri",
            kind=SolutionKind.ADJUSTMENT,
            crs="EPSG:31982",
            epoch=EPOCH,
            datum_definition=DatumDefinition.INNER_CONSTRAINT,
            adjusted_stations=(AdjustedStation(station_id="1", position=projected(0.0, 0.0)),),
            observation_results=(
                ObservationResult(observation_id="d12", residual=0.0012, redundancy=0.45),
                ObservationResult(observation_id="d13", residual=0.0003, redundancy=0.001),
            ),
        )

    def test_station_lookup_lists_the_available_ones_on_failure(self, solution):
        with pytest.raises(ValidationError) as caught:
            solution.station("nope")
        assert caught.value.context["expected"] == ["1"]

    def test_uncheckable_observations_are_identifiable(self, solution):
        """specs/06 section 4.2: a network full of these can pass every
        statistical test and still be wrong."""
        assert [r.observation_id for r in solution.uncheckable_observations()] == ["d13"]

    def test_comparability_reports_every_difference(self, solution):
        other = Solution(
            id="s2",
            network_id="tri",
            kind=SolutionKind.ADJUSTMENT,
            crs="EPSG:4674",
            epoch=Epoch.from_decimal_year(2027.1),
            datum_definition=DatumDefinition.CONSTRAINED,
        )
        findings = solution.is_comparable_with(other)
        assert len(findings) == 3
        assert any("reference frames" in f for f in findings)
        assert any("epochs" in f for f in findings)
        assert any("datum definitions" in f for f in findings)

    def test_a_datum_difference_is_flagged_as_unresolvable_by_transformation(self, solution):
        """A minimum-constraint and a constrained solution of the same data are
        not made comparable by a coordinate transformation."""
        other = Solution(
            id="s2",
            network_id="tri",
            kind=SolutionKind.ADJUSTMENT,
            crs=solution.crs,
            epoch=solution.epoch,
            datum_definition=DatumDefinition.CONSTRAINED,
        )
        finding = solution.is_comparable_with(other)[0]
        assert "cannot reconcile" in finding

    def test_identical_solutions_are_comparable(self, solution):
        assert solution.is_comparable_with(solution) == []

    def test_round_trip(self, solution):
        assert Solution.from_dict(solution.to_dict()).to_dict() == solution.to_dict()


class TestProvenance:
    def test_records_the_geocomp_version_by_default(self):
        from geocomp.core.version import __version__

        assert Provenance.now().geocomp_version == __version__

    def test_round_trip(self):
        original = Provenance.now(
            algorithm_id="geocomp:project_system_report",
            engine="dynadjust",
            engine_version="1.2.3",
            exit_code=0,
            uncertainty_mode=UncertaintyMode.APPROXIMATE,
        )
        assert Provenance.from_dict(original.to_dict()).to_dict() == original.to_dict()


class TestProjectSerialisation:
    def test_a_full_project_round_trips_byte_identically(self):
        """NFR-007. Integer-valued inputs are included deliberately: a Quantity
        that stored an int would serialise as 0 and return as 0.0, breaking
        idempotence in a way that is easy to miss."""
        network = Network(id="tri", crs="EPSG:31982", epoch=EPOCH)
        network.add_station(Station(id="1", approx_position=projected(0, 0)))
        network.add_station(Station(id="2", approx_position=projected(11.5, 0)))
        network.add_observation(
            Observation(
                id="d12",
                type=ObservationType.HORIZONTAL_DISTANCE,
                stations=("1", "2"),
                values=(metres(11.508, 0.003),),
                epoch=EPOCH,
            )
        )
        project = Project(id="p1", default_crs="EPSG:31982", default_epoch=EPOCH)
        project.add_network(network)
        project.add_campaign(Campaign(id="c2026", epoch=EPOCH))
        project.add_gnss_session(GnssSession(id="s1", station_id="1"))

        text = json.dumps(project.to_dict())
        assert json.dumps(Project.from_dict(json.loads(text)).to_dict()) == text

    def test_quantities_survive_at_full_precision(self):
        network = Network(id="n")
        network.add_observation(
            Observation(
                id="d",
                type=ObservationType.HORIZONTAL_DISTANCE,
                stations=("1", "2"),
                values=(Quantity.from_std_dev(11.50812345678901, 0.00312345678901, METRE),),
            )
        )
        restored = Network.from_dict(json.loads(json.dumps(network.to_dict())))
        original_value = network.observations["d"].values[0]
        restored_value = restored.observations["d"].values[0]
        assert restored_value.value == original_value.value
        assert restored_value.variance == original_value.variance

    def test_a_newer_schema_version_is_refused(self):
        """FR-133: reading a schema you do not understand silently corrupts it."""
        project = Project(id="p", schema_version=99)
        with pytest.raises(ValidationError) as caught:
            project.require_schema_version(1)
        assert caught.value.code == "validation.schema_version_too_new"

    def test_the_current_schema_version_is_accepted(self):
        Project(id="p", schema_version=1).require_schema_version(1)

    def test_duplicate_networks_are_refused(self):
        project = Project(id="p")
        project.add_network(Network(id="n"))
        with pytest.raises(DataError):
            project.add_network(Network(id="n"))
