# SPDX-License-Identifier: GPL-2.0-or-later
"""The adjustment core (specs/06).

Organised around the acceptance criteria of ``specs/06`` section 7. The tests
that matter most are the *identities* -- properties that hold for every network,
not just the ones here:

* redundancy numbers sum to the degrees of freedom;
* a free and a constrained solution of the same data agree on residuals and on
  the variance factor;
* design simulation reproduces the adjustment's covariance;
* every analytic Jacobian matches a numerical one.

An identity that holds across configurations catches errors a single worked
example never would.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from geocomp.core.adjustment import Frame, ParameterLayout, evaluate
from geocomp.core.adjustment.datum import DefectComponent, constraint_matrix, detect_defect
from geocomp.core.adjustment.least_squares import (
    AdjustmentOptions,
    adjust,
    starting_values,
    to_observation_results,
    to_solution,
)
from geocomp.core.adjustment.normal_equations import assemble, diagnose_rank, solve
from geocomp.core.errors import ComputationError, ValidationError
from geocomp.core.models import (
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
from geocomp.core.uncertainty import Covariance, Quantity
from geocomp.core.units import Unit
from tests.networks import free_trilateration, levelling_loop, triangulateration, trilateration

METRE, RADIAN, ACCEL = Unit.METRE, Unit.RADIAN, Unit.ACCELERATION


def constrained(frame: Frame) -> AdjustmentOptions:
    return AdjustmentOptions(frame=frame, datum=DatumDefinition.CONSTRAINED)


def inner(frame: Frame, stations: list[str] | None = None) -> AdjustmentOptions:
    return AdjustmentOptions(
        frame=frame, datum=DatumDefinition.INNER_CONSTRAINT, datum_stations=stations
    )


class TestParameterLayout:
    def test_fixed_components_get_no_column(self):
        reference = trilateration()
        layout = ParameterLayout.build(reference.network, Frame.PLANE_2D)
        assert layout.column("A", "e") is None
        assert layout.is_fixed("A", "e")
        assert layout.column("B", "e") is not None

    def test_fixed_values_are_carried(self):
        reference = trilateration()
        layout = ParameterLayout.build(reference.network, Frame.PLANE_2D)
        assert layout.fixed_values[("A", "e")] == pytest.approx(0.0)

    def test_auxiliary_parameters_get_columns(self):
        reference = trilateration()
        layout = ParameterLayout.build(
            reference.network, Frame.PLANE_2D, auxiliary={"setup1": ("orientation",)}
        )
        assert layout.column("setup1", "orientation") == layout.size - 1

    def test_a_fully_fixed_network_has_nothing_to_estimate(self):
        network = Network(id="all-fixed")
        position = Position(
            values=tuple(Quantity.exact(0.0, METRE) for _ in range(3)),
            system=CoordinateSystem.PROJECTED,
            crs="EPSG:31982",
            height_type=HeightType.NONE,
        )
        network.add_station(
            Station(
                id="A",
                constraint=ConstraintSpec(
                    mode=ConstraintMode.FIXED,
                    components=frozenset({"easting", "northing"}),
                    position=position,
                ),
            )
        )
        with pytest.raises(ValidationError) as caught:
            ParameterLayout.build(network, Frame.PLANE_2D)
        assert caught.value.code == "validation.no_estimable_parameters"


#: One case per supported observation type: the equation, a frame it is
#: valid in, and a point to differentiate at.
JACOBIAN_CASES = [
    (ObservationType.HEIGHT_DIFFERENCE, ("1", "2"), (2.5,), (METRE,),
     Frame.HEIGHT_1D, ["1", "2"], [10.0, 12.5], {}),
    (ObservationType.ORTHOMETRIC_HEIGHT, ("1",), (10.0,), (METRE,),
     Frame.HEIGHT_1D, ["1"], [10.0], {}),
    (ObservationType.HORIZONTAL_DISTANCE, ("1", "2"), (11.5,), (METRE,),
     Frame.PLANE_2D, ["1", "2"], [0.0, 0.0, 11.5, 0.3], {}),
    (ObservationType.AZIMUTH, ("1", "2"), (1.0,), (RADIAN,),
     Frame.PLANE_2D, ["1", "2"], [0.0, 0.0, 11.5, 7.3], {}),
    (ObservationType.HORIZONTAL_ANGLE, ("2", "1", "3"), (1.1,), (RADIAN,),
     Frame.PLANE_2D, ["1", "2", "3"], [0.0, 0.0, 11.5, 0.3, 5.2, 12.0], {}),
    (ObservationType.DIRECTION, ("1", "2"), (1.0,), (RADIAN,),
     Frame.PLANE_2D, ["1", "2"], [0.0, 0.0, 11.5, 7.3], {"cluster_id": "c"}),
    (ObservationType.SLOPE_DISTANCE, ("1", "2"), (13.2,), (METRE,),
     Frame.SPACE_3D, ["1", "2"], [0.0, 0.0, 0.0, 11.5, 0.3, 6.4], {}),
    (ObservationType.ZENITH_ANGLE, ("1", "2"), (1.53,), (RADIAN,),
     Frame.SPACE_3D, ["1", "2"], [0.0, 0.0, 0.0, 11.5, 0.3, 6.4], {}),
    (ObservationType.VERTICAL_ANGLE, ("1", "2"), (0.04,), (RADIAN,),
     Frame.SPACE_3D, ["1", "2"], [0.0, 0.0, 0.0, 11.5, 0.3, 6.4], {}),
    (ObservationType.GNSS_BASELINE, ("1", "2"), (11.5, 0.3, 6.4), (METRE, METRE, METRE),
     Frame.SPACE_3D, ["1", "2"], [0.0, 0.0, 0.0, 11.5, 0.3, 6.4], {"cluster_id": "c"}),
    (ObservationType.GNSS_POINT, ("1",), (1.0, 2.0, 3.0), (METRE, METRE, METRE),
     Frame.SPACE_3D, ["1"], [1.0, 2.0, 3.0], {"cluster_id": "c"}),
    (ObservationType.GRAVITY, ("1",), (9.78,), (ACCEL,),
     Frame.GRAVITY_1D, ["1"], [9.78], {}),
    (ObservationType.GRAVITY_DIFFERENCE, ("1", "2"), (1e-5,), (ACCEL,),
     Frame.GRAVITY_1D, ["1", "2"], [9.78, 9.78001], {}),
]


class TestJacobians:
    """specs/05 section 7 criterion 1, applied to every observation equation.

    A sign error here raises nothing and produces a coordinate that is wrong by
    an amount nobody can see, so each equation is differentiated numerically and
    compared.
    """

    @staticmethod
    def _numeric(observation, layout, x):
        def values(v):
            return np.array(
                [row.computed for row in evaluate(observation, layout, np.asarray(v, float))]
            )

        columns = []
        for index in range(layout.size):
            step = 1e-6 * max(abs(float(x[index])), 1.0)
            forward, backward = x.copy(), x.copy()
            forward[index] += step
            backward[index] -= step
            columns.append((values(forward) - values(backward)) / (2 * step))
        return np.column_stack(columns)

    @pytest.mark.parametrize(
        ("observation_type", "stations", "values", "units", "frame", "ids", "x", "extra"),
        JACOBIAN_CASES,
        ids=[case[0].value for case in JACOBIAN_CASES],
    )
    def test_analytic_jacobian_matches_numerical(
        self, observation_type, stations, values, units, frame, ids, x, extra
    ):
        network = Network(id="j")
        for station_id in ids:
            network.add_station(Station(id=station_id))
        observation = Observation(
            id="o",
            type=observation_type,
            stations=stations,
            values=tuple(
                Quantity.from_std_dev(v, 0.001, u)
                for v, u in zip(values, units, strict=True)
            ),
            **extra,
        )
        layout = ParameterLayout.build(network, frame)
        x = np.array(x, dtype=float)

        analytic = np.vstack(
            [row.to_dense(layout.size) for row in evaluate(observation, layout, x)]
        )
        numeric = self._numeric(observation, layout, x)

        scale = max(float(np.max(np.abs(analytic))), 1.0)
        assert float(np.max(np.abs(analytic - numeric))) / scale < 1e-7

    def test_a_direction_differentiates_its_orientation_unknown(self):
        network = Network(id="d")
        for station_id in ("1", "2"):
            network.add_station(Station(id=station_id))
        layout = ParameterLayout.build(
            network, Frame.PLANE_2D, auxiliary={"setup1": ("orientation",)}
        )
        observation = Observation(
            id="o",
            type=ObservationType.DIRECTION,
            stations=("1", "2"),
            values=(Quantity.from_std_dev(1.0, 1e-5, RADIAN),),
            cluster_id="c",
            setup_id="setup1",
        )
        x = np.array([0.0, 0.0, 11.5, 7.3, 0.35])
        row = evaluate(observation, layout, x)[0]
        assert row.partials[layout.column("setup1", "orientation")] == pytest.approx(-1.0)
        assert row.computed == pytest.approx(math.atan2(11.5, 7.3) - 0.35)

    def test_a_vertical_angle_is_the_complement_of_the_zenith_angle(self):
        """The numerical check above cannot see a sign error in the value.

        It differentiates the same function it is checking, so a vertical angle
        computed as ``z`` rather than ``pi/2 - z`` would pass it and put every
        sight on the wrong side of the horizon. This compares the two equations
        against each other on one geometry, which does see it.
        """
        network = Network(id="v")
        for station_id in ("1", "2"):
            network.add_station(Station(id=station_id))
        layout = ParameterLayout.build(network, Frame.SPACE_3D)
        x = np.array([0.0, 0.0, 0.0, 11.5, 0.3, 6.4])

        def computed(observation_type):
            observation = Observation(
                id="o",
                type=observation_type,
                stations=("1", "2"),
                values=(Quantity.from_std_dev(1.0, 1e-5, RADIAN),),
            )
            return evaluate(observation, layout, x)[0]

        zenith = computed(ObservationType.ZENITH_ANGLE)
        vertical = computed(ObservationType.VERTICAL_ANGLE)
        assert vertical.computed == pytest.approx(math.pi / 2.0 - zenith.computed)
        # The sight rises, so the vertical angle is above the horizon.
        assert vertical.computed > 0.0
        for column, partial in zenith.partials.items():
            assert vertical.partials[column] == pytest.approx(-partial)


class TestDatumDefect:
    def test_a_levelling_network_has_one_translation_free(self):
        reference = levelling_loop()
        defect = detect_defect(list(reference.network.observations.values()), Frame.HEIGHT_1D)
        assert defect.components == (DefectComponent.TRANSLATION_U,)

    def test_a_height_observation_removes_the_translation(self):
        reference = levelling_loop()
        observations = list(reference.network.observations.values())
        observations.append(
            Observation(
                id="H",
                type=ObservationType.ORTHOMETRIC_HEIGHT,
                stations=("B",),
                values=(Quantity.from_std_dev(12.5, 0.002, METRE),),
            )
        )
        assert detect_defect(observations, Frame.HEIGHT_1D).size == 0

    def test_distances_fix_scale_but_not_orientation(self):
        network = Network(id="d")
        for station_id in ("A", "B"):
            network.add_station(Station(id=station_id))
        distance = Observation(
            id="d",
            type=ObservationType.HORIZONTAL_DISTANCE,
            stations=("A", "B"),
            values=(Quantity.from_std_dev(100.0, 0.005, METRE),),
        )
        defect = detect_defect([distance], Frame.PLANE_2D)
        assert DefectComponent.SCALE not in defect.components
        assert DefectComponent.ROTATION_U in defect.components

    def test_an_azimuth_fixes_the_rotation(self):
        reference = trilateration()
        defect = detect_defect(list(reference.network.observations.values()), Frame.PLANE_2D)
        assert defect.components == (DefectComponent.TRANSLATION_E, DefectComponent.TRANSLATION_N)

    def test_the_constraint_matrix_has_one_column_per_free_direction(self):
        reference = free_trilateration()
        layout = ParameterLayout.build(reference.network, Frame.PLANE_2D)
        observations = list(reference.network.observations.values())
        defect = detect_defect(observations, Frame.PLANE_2D)
        values = starting_values(
            reference.network, layout, AdjustmentOptions(frame=Frame.PLANE_2D), None
        )
        matrix = constraint_matrix(layout, values, defect)
        assert matrix.shape == (layout.size, defect.size)
        assert np.allclose(np.linalg.norm(matrix, axis=0), 1.0)


class TestRankDiagnosis:
    def test_a_free_levelling_network_names_the_undetermined_combination(self):
        """FR-226: a diagnosis, never a number."""
        reference = levelling_loop()
        network = Network(
            id="free",
            stations={
                sid: Station(id=sid, approx_position=station.approx_position)
                for sid, station in reference.network.stations.items()
            },
            observations=dict(reference.network.observations),
        )
        layout = ParameterLayout.build(network, Frame.HEIGHT_1D)
        values = starting_values(network, layout, AdjustmentOptions(frame=Frame.HEIGHT_1D), None)
        x = np.array([values[s.owner][s.component] for s in layout.slots])
        system = assemble(list(network.observations.values()), network.clusters, layout, x)

        with pytest.raises(ComputationError) as caught:
            solve(system, layout)
        assert caught.value.code == "computation.rank_deficient_normal_matrix"
        assert caught.value.context["deficiency"] == 1
        described = caught.value.context["undetermined"][0]
        for station_id in ("A", "B", "C", "D"):
            assert f"{station_id}.h" in described

    def test_the_null_space_of_a_free_levelling_network_is_a_common_shift(self):
        reference = levelling_loop()
        network = Network(
            id="free",
            stations={
                sid: Station(id=sid, approx_position=station.approx_position)
                for sid, station in reference.network.stations.items()
            },
            observations=dict(reference.network.observations),
        )
        layout = ParameterLayout.build(network, Frame.HEIGHT_1D)
        values = starting_values(network, layout, AdjustmentOptions(frame=Frame.HEIGHT_1D), None)
        x = np.array([values[s.owner][s.component] for s in layout.slots])
        system = assemble(list(network.observations.values()), network.clusters, layout, x)

        findings = diagnose_rank(system.normal_matrix(), layout)
        assert len(findings) == 1
        weights = [weight for _, weight in findings[0].parameters]
        # Every station moves together and by the same amount: 1/sqrt(4).
        assert all(abs(abs(w) - 0.5) < 1e-9 for w in weights)

    def test_a_full_rank_system_reports_no_findings(self):
        reference = levelling_loop()
        run = adjust(reference.network, constrained(Frame.HEIGHT_1D))
        assert diagnose_rank(run.system.normal_matrix(), run.layout) == []


class TestLevellingAdjustment:
    """RD-03.1 -- the network whose answer can be checked entirely by hand."""

    def test_a_loop_misclosure_distributes_equally_with_equal_weights(self):
        """Three equally weighted height differences round a loop share the
        misclosure equally. Closed form, and a strong check on the weighting."""
        network = Network(id="loop", crs="EPSG:31982")
        position = Position(
            values=(Quantity.exact(0.0, METRE), Quantity.exact(0.0, METRE), Quantity.exact(10.0, METRE)),
            system=CoordinateSystem.PROJECTED,
            crs="EPSG:31982",
            height_type=HeightType.ORTHOMETRIC,
        )
        network.add_station(
            Station(
                id="A",
                approx_position=position,
                constraint=ConstraintSpec(
                    mode=ConstraintMode.FIXED, components=frozenset({"up"}), position=position
                ),
            )
        )
        for station_id, height in (("B", 12.0), ("C", 15.5)):
            network.add_station(
                Station(
                    id=station_id,
                    approx_position=Position(
                        values=(
                            Quantity.exact(0.0, METRE),
                            Quantity.exact(0.0, METRE),
                            Quantity.from_std_dev(height, 0.5, METRE),
                        ),
                        system=CoordinateSystem.PROJECTED,
                        crs="EPSG:31982",
                        height_type=HeightType.ORTHOMETRIC,
                    ),
                )
            )
        for observation_id, (origin, target, value) in enumerate(
            [("A", "B", 2.501), ("B", "C", 2.498), ("C", "A", -5.002)]
        ):
            network.add_observation(
                Observation(
                    id=f"L{observation_id}",
                    type=ObservationType.HEIGHT_DIFFERENCE,
                    stations=(origin, target),
                    values=(Quantity.from_std_dev(value, 0.002, METRE),),
                )
            )

        run = adjust(network, constrained(Frame.HEIGHT_1D))

        # Misclosure is -3 mm over three equally weighted lines: +1 mm each.
        assert np.allclose(run.residuals, 0.001, atol=1e-9)
        assert run.degrees_of_freedom == 1
        # v'Pv = 3 * (0.001 / 0.002)^2 = 0.75
        assert run.variance_factor_aposteriori == pytest.approx(0.75)

    def test_the_reference_loop_recovers_the_truth(self):
        reference = levelling_loop()
        run = adjust(reference.network, constrained(Frame.HEIGHT_1D))
        assert run.converged
        # Observation sigma is 2 mm with redundancy; errors should stay well below 1 cm.
        assert reference.max_coordinate_error(run.parameters, run.layout) < 0.01

    def test_redundancy_numbers_sum_to_the_degrees_of_freedom(self):
        """The identity behind data snooping and reliability. It holds for every
        network, which makes it a far stronger check than any single answer."""
        reference = levelling_loop()
        run = adjust(reference.network, constrained(Frame.HEIGHT_1D))
        assert run.redundancy.sum() == pytest.approx(run.degrees_of_freedom, abs=1e-9)


class TestTrilateration:
    """RD-03.2 -- 2D, non-linear, converging from poor approximations."""

    @pytest.fixture(scope="class")
    def run(self):
        return adjust(trilateration().network, constrained(Frame.PLANE_2D))

    def test_it_converges(self, run):
        assert run.converged
        assert run.iterations <= 5
        assert run.max_correction < 1e-4

    def test_it_recovers_the_truth(self, run):
        assert trilateration().max_coordinate_error(run.parameters, run.layout) < 0.02

    def test_redundancy_sums_to_the_degrees_of_freedom(self, run):
        assert run.redundancy.sum() == pytest.approx(run.degrees_of_freedom, abs=1e-9)

    def test_the_sole_orientation_observation_is_uncheckable(self, run):
        """The azimuth is the only thing fixing rotation, so nothing checks it.
        A network can pass every test while containing such an observation, and
        this one is here precisely so that condition is exercised."""
        row = run.system.row_labels.index(("az", ""))
        assert run.redundancy[row] < 0.01

    def test_the_variance_factor_is_near_one(self, run):
        """The observations were generated with exactly the stated sigma, so the
        stochastic model is correct by construction and sigma_0^2 should be
        near 1. A unit error in the weight matrix would show up here at once."""
        assert 0.2 < run.variance_factor_aposteriori < 3.0

    def test_the_parameter_covariance_is_positive_definite(self, run):
        assert np.all(np.linalg.eigvalsh(run.parameter_covariance) > 0)


class TestTriangulateration:
    """RD-03.3 -- angles and distances, mixing radians and metres in one weight matrix."""

    @pytest.fixture(scope="class")
    def run(self):
        return adjust(triangulateration().network, constrained(Frame.PLANE_2D))

    def test_it_converges_and_recovers_the_truth(self, run):
        assert run.converged
        assert triangulateration().max_coordinate_error(run.parameters, run.layout) < 0.05

    def test_redundancy_sums_to_the_degrees_of_freedom(self, run):
        assert run.redundancy.sum() == pytest.approx(run.degrees_of_freedom, abs=1e-9)

    def test_mixed_units_give_a_sane_variance_factor(self, run):
        """A unit confusion between radians and metres would inflate or deflate
        the variance factor by orders of magnitude."""
        assert 0.1 < run.variance_factor_aposteriori < 5.0


class TestFreeNetworkAndDatum:
    """specs/06 section 7 criterion 2."""

    @pytest.fixture(scope="class")
    def free(self):
        return adjust(free_trilateration().network, inner(Frame.PLANE_2D))

    @pytest.fixture(scope="class")
    def fixed(self):
        return adjust(trilateration().network, constrained(Frame.PLANE_2D))

    def test_the_free_solution_converges(self, free):
        assert free.converged
        assert free.method == "bordered"

    def test_free_and_constrained_agree_on_the_residuals(self, free, fixed):
        """The datum choice cannot change how well the observations fit -- only
        where the network sits. Residuals are the sharpest form of that claim."""
        by_label_free = dict(zip(free.system.row_labels, free.residuals, strict=True))
        by_label_fixed = dict(zip(fixed.system.row_labels, fixed.residuals, strict=True))
        for label, residual in by_label_fixed.items():
            assert by_label_free[label] == pytest.approx(residual, abs=1e-9)

    def test_free_and_constrained_agree_on_the_variance_factor(self, free, fixed):
        assert free.variance_factor_aposteriori == pytest.approx(
            fixed.variance_factor_aposteriori, rel=1e-9
        )

    def test_free_and_constrained_agree_on_the_degrees_of_freedom(self, free, fixed):
        assert free.degrees_of_freedom == fixed.degrees_of_freedom

    def test_the_free_solution_differs_only_by_a_datum_transformation(self, free, fixed):
        """The two solutions differ by a similarity transformation and nothing
        else. Fitting one and checking the residual distances are unchanged is
        the geometric statement of that."""
        stations = [s for s in free.layout.station_ids() if s in fixed.layout.station_ids()]
        for first in stations:
            for second in stations:
                if first >= second:
                    continue

                def separation(run, a=first, b=second):
                    ca, cb = run.layout.station_columns(a), run.layout.station_columns(b)
                    return math.dist(
                        (run.parameters[ca["e"]], run.parameters[ca["n"]]),
                        (run.parameters[cb["e"]], run.parameters[cb["n"]]),
                    )

                assert separation(free) == pytest.approx(separation(fixed), abs=1e-6)

    def test_inner_constraints_privilege_no_station(self, free):
        """The trace-minimum condition: the *corrections* sum to zero in each
        component, so the solution sits as close as possible to the approximate
        coordinates rather than being pinned to any one station.

        Measured against the approximate coordinates, not against the truth: an
        inner-constraint solution deliberately does not know where the truth is,
        which is exactly why it is the right choice for deformation analysis.
        """
        reference = free_trilateration()
        approximate = starting_values(
            reference.network, free.layout, inner(Frame.PLANE_2D), None
        )
        for component in ("e", "n"):
            total = sum(
                free.parameters[free.layout.station_columns(station_id)[component]]
                - approximate[station_id][component]
                for station_id in free.layout.station_ids()
            )
            assert abs(total) < 1e-6, component


class TestFailureModes:
    def test_non_convergence_is_reported_not_returned(self):
        """A result that looks like coordinates but is iteration seven of a
        diverging sequence is worse than no result."""
        reference = trilateration()
        with pytest.raises(ComputationError) as caught:
            adjust(
                reference.network,
                AdjustmentOptions(
                    frame=Frame.PLANE_2D,
                    datum=DatumDefinition.CONSTRAINED,
                    convergence=1e-18,
                    max_iterations=2,
                ),
            )
        assert caught.value.code == "computation.adjustment_did_not_converge"
        assert "iterations" in caught.value.context

    def test_an_observation_without_uncertainty_is_refused(self):
        network = Network(id="w", crs="EPSG:31982")
        position = Position(
            values=tuple(Quantity.exact(0.0, METRE) for _ in range(3)),
            system=CoordinateSystem.PROJECTED,
            crs="EPSG:31982",
            height_type=HeightType.ORTHOMETRIC,
        )
        network.add_station(
            Station(
                id="A",
                approx_position=position,
                constraint=ConstraintSpec(
                    mode=ConstraintMode.FIXED, components=frozenset({"up"}), position=position
                ),
            )
        )
        network.add_station(Station(id="B", approx_position=position))
        network.add_observation(
            Observation(
                id="L",
                type=ObservationType.HEIGHT_DIFFERENCE,
                stations=("A", "B"),
                values=(Quantity.exact(1.0, METRE),),
            )
        )
        from geocomp.core.errors import DataError

        with pytest.raises(DataError) as caught:
            adjust(network, constrained(Frame.HEIGHT_1D))
        assert caught.value.code == "data.observation_without_uncertainty"

    def test_a_type_in_the_wrong_dimensionality_is_refused(self):
        network = Network(id="dim")
        for station_id in ("A", "B"):
            network.add_station(Station(id=station_id))
        layout = ParameterLayout.build(network, Frame.HEIGHT_1D)
        observation = Observation(
            id="d",
            type=ObservationType.HORIZONTAL_DISTANCE,
            stations=("A", "B"),
            values=(Quantity.from_std_dev(10.0, 0.01, METRE),),
        )
        with pytest.raises(ValidationError) as caught:
            evaluate(observation, layout, np.zeros(layout.size))
        assert caught.value.code == "validation.observation_wrong_dimensionality"

    def test_missing_approximate_coordinates_are_refused_with_the_station_named(self):
        reference = levelling_loop()
        reference.network.stations["B"] = Station(id="B")
        with pytest.raises(ValidationError) as caught:
            adjust(reference.network, constrained(Frame.HEIGHT_1D))
        assert caught.value.code == "validation.missing_approximate_coordinates"
        assert caught.value.context["station"] == "B"


class TestSolutionAssembly:
    """The boundary phase P6 makes a cross-validation.

    DynAdjust's parser fills the same :class:`Solution`, so anything the
    in-house path leaves empty here is something the visualisation, reporting
    and multi-epoch code would have to special-case per engine.
    """

    @pytest.fixture
    def run(self):
        return adjust(trilateration().network, constrained(Frame.PLANE_2D))

    def _solution(self, run, **kwargs):
        return to_solution(
            run,
            trilateration().network,
            solution_id="s1",
            crs="EPSG:31982",
            epoch=Epoch.from_decimal_year(2026.0),
            datum=DatumDefinition.CONSTRAINED,
            **kwargs,
        )

    def test_every_adjusted_station_carries_an_error_ellipse(self, run):
        """FR-254 asks for the ellipse wherever a station is reported. A
        Solution that carried a covariance but no ellipse would push the
        eigen-decomposition into every consumer."""
        solution = self._solution(run)
        assert solution.adjusted_stations
        for station in solution.adjusted_stations:
            assert station.ellipse is not None
            assert station.ellipse.semi_major >= station.ellipse.semi_minor > 0.0

    def test_the_ellipse_matches_the_station_covariance_block(self, run):
        from geocomp.core.statistics.ellipses import error_ellipse

        solution = self._solution(run)
        for station in solution.adjusted_stations:
            columns = run.layout.station_columns(station.station_id)
            indices = [columns[c] for c in ("e", "n") if c in columns]
            expected = error_ellipse(
                run.parameter_covariance[np.ix_(indices, indices)],
                confidence=0.95,
                degrees_of_freedom=run.degrees_of_freedom,
            )
            assert station.ellipse.semi_major == pytest.approx(expected.semi_major)
            assert station.ellipse.semi_minor == pytest.approx(expected.semi_minor)

    def test_the_confidence_level_reaches_the_ellipse(self, run):
        """A larger confidence must give a larger ellipse; if the parameter were
        ignored the two would come back identical."""
        at_95 = self._solution(run, confidence=0.95).adjusted_stations[0].ellipse
        at_99 = self._solution(run, confidence=0.99).adjusted_stations[0].ellipse
        assert at_99.semi_major > at_95.semi_major
        assert at_99.confidence == 0.99

    def test_the_a_priori_variance_factor_is_recorded_not_assumed(self):
        """The global test compares against it, so a solution that always said
        1.0 would misreport what was actually tested."""
        options = AdjustmentOptions(
            frame=Frame.PLANE_2D, datum=DatumDefinition.CONSTRAINED, variance_factor_apriori=0.25
        )
        run = adjust(trilateration().network, options)
        assert run.variance_factor_apriori == 0.25
        assert self._solution(run).statistics.variance_factor_apriori == 0.25

    def test_one_observation_result_per_design_matrix_row(self, run):
        """Per row, not per observation: a three-component baseline that
        collapsed to one result would hide which component carries the
        residual."""
        results = to_observation_results(run)
        assert len(results) == len(run.system.row_labels)
        assert [r.observation_id for r in results] == [
            label[0] for label in run.system.row_labels
        ]

    def test_observation_results_carry_the_residual_and_redundancy(self, run):
        for row, result in enumerate(to_observation_results(run)):
            assert result.residual == pytest.approx(float(run.residuals[row]))
            assert result.redundancy == pytest.approx(float(run.redundancy[row]))

    def test_statistics_and_reliability_reach_the_results_when_supplied(self, run):
        from geocomp.core.statistics.reliability import reliability
        from geocomp.core.statistics.tests import data_snooping

        snooping = data_snooping(
            run.residuals,
            run.cofactor_residuals,
            run.system.weight,
            run.system.row_labels,
            variance_factor=run.variance_factor_aposteriori,
            degrees_of_freedom=run.degrees_of_freedom,
        )
        report = reliability(
            run.cofactor_residuals,
            run.system.weight,
            run.system.design,
            run.cofactor_parameters,
            run.system.row_labels,
        )
        results = to_observation_results(run, snooping=snooping, reliability=report)

        by_row = {result.row: result for result in report.results}
        for row, result in enumerate(results):
            assert result.standardised_residual == pytest.approx(snooping.statistics[row])
            assert result.minimal_detectable_bias == by_row[row].minimal_detectable_bias
            assert result.external_reliability == by_row[row].external_effect

        # The azimuth is the only observation fixing orientation, so nothing
        # checks it: its MDB is undefined rather than merely large.
        uncheckable = [r for r in results if r.is_uncheckable]
        assert uncheckable
        assert all(r.minimal_detectable_bias is None for r in uncheckable)

    def test_a_flagged_observation_carries_its_w_test_decision(self):
        reference = trilateration(blunder=0.5, blunder_on="d4")
        run = adjust(reference.network, constrained(Frame.PLANE_2D))
        from geocomp.core.statistics.tests import data_snooping

        snooping = data_snooping(
            run.residuals,
            run.cofactor_residuals,
            run.system.weight,
            run.system.row_labels,
            variance_factor=run.variance_factor_aposteriori,
            degrees_of_freedom=run.degrees_of_freedom,
        )
        results = to_observation_results(run, snooping=snooping)
        flagged = [r for r in results if r.w_test is not None and not r.w_test.passed]
        assert [r.observation_id for r in flagged] == ["d4"]
        assert flagged[0].w_test.name.startswith("w-test")

    def test_the_solution_round_trips_through_json(self, run):
        """NFR-007: the document an algorithm writes must read back as the same
        solution, ellipses and per-observation results included."""
        import json

        from geocomp.core.models import Solution
        from geocomp.core.statistics.tests import global_test

        solution = self._solution(
            run,
            observation_results=to_observation_results(run),
            global_test=global_test(run.variance_factor_aposteriori, run.degrees_of_freedom),
        )
        payload = solution.to_dict()
        assert Solution.from_dict(json.loads(json.dumps(payload))).to_dict() == payload


class TestOrientationUnknowns:
    """Direction sets, found under-tested when phase P3 first used them.

    P2 implemented the direction observation equation with an orientation
    unknown, and P2's own tests exercised it only with the unknown declared by
    hand and starting from a value near the truth. Real total-station data does
    neither: the setup id comes from the field book, and the circle's zero is
    wherever the instrument happened to be pointing. Both gaps produced a
    diverging adjustment with a message about convergence that said nothing
    about the cause.
    """

    @staticmethod
    def _network(orientations: dict[str, float]) -> Network:
        """Three stations, two direction sets with the given true orientations.

        Distances fix the shape; the directions are then *readings*, offset from
        the true azimuths by each setup's orientation.
        """
        truth = {"A": (0.0, 0.0), "B": (300.0, 0.0), "C": (150.0, 260.0)}
        network = Network(id="orientation", crs="EPSG:31982")
        for station_id, (easting, northing) in truth.items():
            network.add_station(
                Station(
                    id=station_id,
                    approx_position=Position(
                        values=(
                            Quantity.from_std_dev(easting, 0.5, METRE),
                            Quantity.from_std_dev(northing, 0.5, METRE),
                            Quantity.exact(0.0, METRE),
                        ),
                        system=CoordinateSystem.PROJECTED,
                        crs="EPSG:31982",
                        height_type=HeightType.ORTHOMETRIC,
                    ),
                )
            )

        for origin, targets in (("A", ("B", "C")), ("B", ("A", "C"))):
            ids = []
            for target in targets:
                azimuth = math.atan2(
                    truth[target][0] - truth[origin][0], truth[target][1] - truth[origin][1]
                )
                reading = (azimuth - orientations[origin]) % (2 * math.pi)
                observation_id = f"{origin}-dir-{target}"
                network.add_observation(
                    Observation(
                        id=observation_id,
                        type=ObservationType.DIRECTION,
                        stations=(origin, target),
                        values=(Quantity.from_std_dev(reading, 5e-6, RADIAN),),
                        cluster_id=f"{origin}-set",
                        setup_id=origin,
                    )
                )
                ids.append(observation_id)
            network.add_cluster(
                Cluster(
                    id=f"{origin}-set",
                    kind=ClusterKind.DIRECTION_SET,
                    observation_ids=tuple(ids),
                    covariance=Covariance(
                        matrix=np.diag([5e-6**2, 5e-6**2]),
                        labels=tuple(ids),
                        units=(RADIAN, RADIAN),
                    ),
                )
            )

        for origin, target in (("A", "B"), ("A", "C"), ("B", "C")):
            distance = math.dist(truth[origin], truth[target])
            network.add_observation(
                Observation(
                    id=f"d-{origin}{target}",
                    type=ObservationType.HORIZONTAL_DISTANCE,
                    stations=(origin, target),
                    values=(Quantity.from_std_dev(distance, 0.003, METRE),),
                )
            )
        return network

    @pytest.mark.parametrize("orientation_degrees", [0.0, 37.0, 175.0, 250.0, 359.5])
    def test_a_direction_set_converges_whatever_its_orientation(self, orientation_degrees):
        """The circle's zero is arbitrary. An adjustment that only worked when
        it happened to be near north would be useless on real data."""
        orientation = math.radians(orientation_degrees)
        network = self._network({"A": orientation, "B": orientation / 2.0})
        run = adjust(
            network,
            AdjustmentOptions(frame=Frame.PLANE_2D, datum=DatumDefinition.INNER_CONSTRAINT),
        )
        assert run.converged
        assert run.variance_factor_aposteriori < 5.0

    def test_the_orientation_unknown_is_derived_rather_than_declared(self):
        """A direction without one is always wrong, so requiring the caller to
        declare it is a footgun rather than a choice. Nothing is passed in
        ``auxiliary`` here."""
        network = self._network({"A": math.radians(37.0), "B": math.radians(112.0)})
        run = adjust(
            network,
            AdjustmentOptions(frame=Frame.PLANE_2D, datum=DatumDefinition.INNER_CONSTRAINT),
        )
        assert run.layout.column("A", "orientation") is not None
        assert run.layout.column("B", "orientation") is not None

    def test_the_estimated_orientations_recover_the_ones_that_were_planted(self):
        planted = {"A": math.radians(37.0), "B": math.radians(112.0)}
        network = self._network(planted)
        run = adjust(
            network,
            AdjustmentOptions(frame=Frame.PLANE_2D, datum=DatumDefinition.INNER_CONSTRAINT),
        )
        for station, expected in planted.items():
            column = run.layout.column(station, "orientation")
            estimated = float(run.parameters[column]) % (2 * math.pi)
            assert estimated == pytest.approx(expected, abs=1e-4)

    def test_an_explicitly_declared_orientation_is_not_overridden(self):
        """Two setups sharing one orientation -- both on a pillar, say -- is a
        legitimate model the caller may impose."""
        network = self._network({"A": math.radians(37.0), "B": math.radians(37.0)})
        run = adjust(
            network,
            AdjustmentOptions(
                frame=Frame.PLANE_2D,
                datum=DatumDefinition.INNER_CONSTRAINT,
                auxiliary={"A": ("orientation",)},
            ),
        )
        assert run.layout.column("A", "orientation") is not None


class TestAngularMisclosureWrapping:
    """An angular misclosure is taken the short way round the circle.

    The defect this guards against is silent and severe: a direction read as
    353 degrees against a computed -7 differs by nothing, but the plain
    subtraction says 360, which enters the normal equations as an enormous
    residual. The adjustment then diverges and reports a convergence failure
    that says nothing about the cause.
    """

    @staticmethod
    def _misclosure(observed_degrees: float, computed_degrees: float, unit) -> float:
        from geocomp.core.adjustment.normal_equations import _misclosure

        return _misclosure(
            math.radians(observed_degrees), math.radians(computed_degrees), unit
        )

    @pytest.mark.parametrize(
        ("observed", "computed", "expected"),
        [
            (353.0, -7.0, 0.0),
            (-7.0, 353.0, 0.0),
            (1.0, 359.0, 2.0),
            (359.0, 1.0, -2.0),
            (90.0, 60.0, 30.0),
            (180.0, 0.0, 180.0),
        ],
    )
    def test_an_angular_misclosure_takes_the_short_way(self, observed, computed, expected):
        result = self._misclosure(observed, computed, RADIAN)
        assert math.degrees(result) == pytest.approx(expected, abs=1e-12)

    def test_a_linear_misclosure_is_left_alone(self):
        """Wrapping a distance would be nonsense, and a 6.28 m difference is a
        perfectly ordinary blunder that must survive to the residual."""
        from geocomp.core.adjustment.normal_equations import _misclosure

        assert _misclosure(10.0, 3.0, METRE) == pytest.approx(7.0)
        assert _misclosure(2.0 * math.pi, 0.0, METRE) == pytest.approx(2.0 * math.pi)

    def test_the_wrap_never_exceeds_half_a_turn(self):
        for observed in range(0, 360, 7):
            for computed in range(0, 360, 11):
                result = self._misclosure(float(observed), float(computed), RADIAN)
                assert -math.pi < result <= math.pi + 1e-12
