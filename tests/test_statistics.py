# SPDX-License-Identifier: GPL-2.0-or-later
"""Statistical validation, reliability, ellipses and pre-analysis (specs/06 sections 4 and 5).

Includes the two P2 exit criteria that carry the most weight:

* a blunder at 2 x MDB is located in the correct observation on the first pass,
  with no false positive elsewhere (RD-09);
* design simulation reproduces the covariance the full adjustment produces.

Both are tested against a **known truth** rather than against another
computation, which is the only way to distinguish "agrees with itself" from
"is right".
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from geocomp.core.adjustment import Frame
from geocomp.core.adjustment.least_squares import AdjustmentOptions, adjust
from geocomp.core.errors import ValidationError
from geocomp.core.models import DatumDefinition, Network, Observation, ObservationType, Station
from geocomp.core.preanalysis import inspect, simulate
from geocomp.core.preanalysis.inspection import Severity
from geocomp.core.statistics import USING_SCIPY
from geocomp.core.statistics.distributions import (
    chi2_cdf,
    chi2_quantile,
    f_quantile,
    non_centrality,
    normal_cdf,
    normal_quantile,
    t_quantile,
)
from geocomp.core.statistics.ellipses import (
    confidence_scale,
    error_ellipse,
    positional_uncertainty,
    relative_ellipse,
)
from geocomp.core.statistics.reliability import reliability
from geocomp.core.statistics.tests import data_snooping, global_test
from geocomp.core.uncertainty import Quantity
from geocomp.core.units import Unit
from tests.networks import levelling_loop, trilateration

METRE = Unit.METRE


def constrained(frame: Frame) -> AdjustmentOptions:
    return AdjustmentOptions(frame=frame, datum=DatumDefinition.CONSTRAINED)


class TestDistributions:
    """Against published table values. The NumPy-only fallback is what runs
    here, since this container has no SciPy -- so these also prove the fallback
    is real rather than assumed (ADR-0008)."""

    @pytest.mark.parametrize(
        ("probability", "expected"),
        [(0.975, 1.959964), (0.995, 2.575829), (0.9995, 3.290527), (0.80, 0.841621)],
    )
    def test_normal_quantiles(self, probability, expected):
        assert normal_quantile(probability) == pytest.approx(expected, abs=1e-6)

    @pytest.mark.parametrize(
        ("probability", "dof", "expected"),
        [
            (0.95, 1, 3.8415), (0.95, 10, 18.3070), (0.95, 30, 43.7730),
            (0.05, 10, 3.9403), (0.99, 5, 15.0863), (0.025, 20, 9.5908),
            (0.975, 20, 34.1696),
        ],
    )
    def test_chi_square_quantiles(self, probability, dof, expected):
        assert chi2_quantile(probability, dof) == pytest.approx(expected, abs=1e-4)

    @pytest.mark.parametrize(
        ("probability", "df1", "df2", "expected"),
        [(0.95, 2, 10, 4.1028), (0.95, 3, 20, 3.0984), (0.95, 1, 1, 161.4476), (0.99, 5, 15, 4.5556)],
    )
    def test_f_quantiles(self, probability, df1, df2, expected):
        assert f_quantile(probability, df1, df2) == pytest.approx(expected, abs=1e-3)

    @pytest.mark.parametrize(
        ("probability", "dof", "expected"),
        [(0.975, 10, 2.2281), (0.975, 30, 2.0423), (0.995, 5, 4.0321), (0.975, 1, 12.7062)],
    )
    def test_student_t_quantiles(self, probability, dof, expected):
        assert t_quantile(probability, dof) == pytest.approx(expected, abs=1e-4)

    def test_the_classic_geodetic_non_centrality(self):
        """delta_0 = 4.13 at alpha = 0.001, beta = 0.20 (specs/06 section 4.3)."""
        assert non_centrality(0.001, 0.20) == pytest.approx(4.13, abs=0.005)

    def test_quantiles_and_cdfs_are_inverse(self):
        for probability in (0.01, 0.25, 0.5, 0.9, 0.999):
            assert normal_cdf(normal_quantile(probability)) == pytest.approx(probability, abs=1e-9)
            assert chi2_cdf(chi2_quantile(probability, 7), 7) == pytest.approx(probability, abs=1e-9)

    def test_invalid_probabilities_are_refused(self):
        for bad in (0.0, 1.0, -0.5, 1.5):
            with pytest.raises(ValidationError):
                normal_quantile(bad)

    def test_zero_degrees_of_freedom_is_refused(self):
        with pytest.raises(ValidationError) as caught:
            chi2_quantile(0.95, 0)
        assert "no test to apply" in caught.value.context["expected"]

    @pytest.mark.skipif(not USING_SCIPY, reason="SciPy not installed in this environment")
    def test_the_two_paths_agree_where_scipy_exists(self):  # pragma: no cover
        """ADR-0008: SciPy is a speed path, not a different answer."""
        from scipy import stats

        for probability in (0.025, 0.5, 0.975):
            assert normal_quantile(probability) == pytest.approx(
                float(stats.norm.ppf(probability)), rel=1e-10
            )


class TestGlobalTest:
    def test_a_correct_stochastic_model_passes(self):
        result = global_test(1.0, 10)
        assert result.passed
        assert result.critical_low < result.statistic < result.critical_high

    def test_an_inflated_variance_factor_fails_and_lists_the_causes(self):
        """specs/06 section 4.1: rejection is not automatically a blunder, and
        students routinely assume it is."""
        result = global_test(3.0, 10)
        assert not result.passed
        assert "blunders" in result.note
        assert "stochastic model" in result.note
        assert "functional model" in result.note

    def test_a_deflated_variance_factor_also_fails_and_says_why(self):
        """The test is two-sided by design: pessimistic a priori precisions are
        information, not a pass."""
        result = global_test(0.15, 10)
        assert not result.passed
        assert "pessimistic" in result.note

    def test_zero_redundancy_has_nothing_to_test(self):
        result = global_test(1.0, 0)
        assert result.passed
        assert "no redundancy" in result.note

    def test_the_statistic_carries_both_critical_values(self):
        """specs/06 section 7: never a bare pass or fail."""
        result = global_test(1.0, 10)
        assert result.critical_low is not None
        assert result.critical_high is not None
        assert result.confidence == 0.95


class TestDataSnooping:
    """RD-09 -- detection tested against an injected blunder of known size."""

    @staticmethod
    def _mdb(run, observation_id):
        report = reliability(
            run.cofactor_residuals,
            run.system.weight,
            run.system.design,
            run.cofactor_parameters,
            run.system.row_labels,
        )
        return report.by_observation()[observation_id].minimal_detectable_bias

    def test_a_clean_network_yields_no_candidates(self):
        run = adjust(trilateration().network, constrained(Frame.PLANE_2D))
        report = data_snooping(
            run.residuals,
            run.cofactor_residuals,
            run.system.weight,
            run.system.row_labels,
            variance_factor=run.variance_factor_aposteriori,
            degrees_of_freedom=run.degrees_of_freedom,
        )
        assert report.candidates == ()

    def test_a_blunder_at_twice_the_mdb_is_located_on_the_first_pass(self):
        """The P2 exit criterion. The blunder is injected at a known place with
        a known size, so 'located it' means located *the right one*."""
        clean = adjust(trilateration().network, constrained(Frame.PLANE_2D))
        size = 2.0 * self._mdb(clean, "d4")

        blundered = adjust(
            trilateration(blunder=size, blunder_on="d4").network, constrained(Frame.PLANE_2D)
        )
        report = data_snooping(
            blundered.residuals,
            blundered.cofactor_residuals,
            blundered.system.weight,
            blundered.system.row_labels,
            variance_factor=blundered.variance_factor_aposteriori,
            degrees_of_freedom=blundered.degrees_of_freedom,
        )

        assert report.worst is not None
        assert report.worst.observation_id == "d4"
        assert [c.observation_id for c in report.candidates] == ["d4"]

    def test_a_blunder_fails_the_global_test(self):
        clean = adjust(trilateration().network, constrained(Frame.PLANE_2D))
        size = 2.0 * self._mdb(clean, "d4")
        blundered = adjust(
            trilateration(blunder=size, blunder_on="d4").network, constrained(Frame.PLANE_2D)
        )
        assert not global_test(
            blundered.variance_factor_aposteriori, blundered.degrees_of_freedom
        ).passed

    def test_the_distribution_used_is_reported(self):
        """specs/06 section 4.2: which variant was applied must be stated,
        because the estimated-sigma case deflates every statistic."""
        run = adjust(trilateration().network, constrained(Frame.PLANE_2D))
        estimated = data_snooping(
            run.residuals, run.cofactor_residuals, run.system.weight, run.system.row_labels,
            variance_factor=run.variance_factor_aposteriori,
            degrees_of_freedom=run.degrees_of_freedom, sigma_known=False,
        )
        known = data_snooping(
            run.residuals, run.cofactor_residuals, run.system.weight, run.system.row_labels,
            degrees_of_freedom=run.degrees_of_freedom, sigma_known=True,
        )
        assert estimated.distribution == "tau"
        assert known.distribution == "normal"

    def test_uncheckable_observations_are_separated_from_candidates(self):
        """An observation with no redundancy cannot be an outlier candidate,
        because nothing checks it -- reporting it as clean would be misleading."""
        run = adjust(trilateration().network, constrained(Frame.PLANE_2D))
        report = data_snooping(
            run.residuals, run.cofactor_residuals, run.system.weight, run.system.row_labels,
            variance_factor=run.variance_factor_aposteriori,
            degrees_of_freedom=run.degrees_of_freedom,
        )
        assert [u.observation_id for u in report.uncheckable] == ["az"]

    def test_multiple_exceedances_are_flagged_as_not_a_ranking(self):
        clean = adjust(trilateration().network, constrained(Frame.PLANE_2D))
        size = 10.0 * self._mdb(clean, "d4")
        blundered = adjust(
            trilateration(blunder=size, blunder_on="d4").network, constrained(Frame.PLANE_2D)
        )
        report = data_snooping(
            blundered.residuals, blundered.cofactor_residuals, blundered.system.weight,
            blundered.system.row_labels, degrees_of_freedom=blundered.degrees_of_freedom,
            sigma_known=True,
        )
        if report.multiple_exceedances:
            assert "not a ranking" in report.note()


class TestReliability:
    @pytest.fixture(scope="class")
    def report(self):
        run = adjust(trilateration().network, constrained(Frame.PLANE_2D))
        return reliability(
            run.cofactor_residuals,
            run.system.weight,
            run.system.design,
            run.cofactor_parameters,
            run.system.row_labels,
        )

    def test_it_uses_the_classic_non_centrality(self, report):
        assert report.non_centrality == pytest.approx(4.13, abs=0.005)

    def test_an_uncheckable_observation_has_no_finite_mdb(self, report):
        """At zero redundancy the MDB is infinite. Reporting None is honest;
        a very large number would invite comparison with the finite ones."""
        uncheckable = report.by_observation()["az"]
        assert uncheckable.is_uncheckable
        assert uncheckable.minimal_detectable_bias is None

    def test_checkable_observations_have_a_finite_mdb(self, report):
        finite = [r for r in report.results if not r.is_uncheckable]
        assert finite
        assert all(r.minimal_detectable_bias > 0 for r in finite)

    def test_the_mdb_grows_as_redundancy_falls(self, report):
        """MDB = delta_0 * sigma / sqrt(r): less checkable means a bigger blunder
        can hide."""
        finite = sorted(
            (r for r in report.results if not r.is_uncheckable), key=lambda r: r.redundancy
        )
        scaled = [r.minimal_detectable_bias * math.sqrt(r.redundancy) / r.std_dev for r in finite]
        assert all(value == pytest.approx(report.non_centrality, rel=1e-9) for value in scaled)

    def test_external_reliability_is_reported_alongside_internal(self, report):
        """specs/06 section 4.3: the MDB alone is the less useful half."""
        for result in report.results:
            if result.minimal_detectable_bias is not None:
                assert result.external_effect is not None

    def test_the_report_warns_about_uncheckable_observations(self, report):
        assert "uncheckable" in report.note()


class TestEllipses:
    def test_the_classic_two_dimensional_scale_factor(self):
        assert confidence_scale(0.95) == pytest.approx(2.4477, abs=1e-4)

    def test_the_f_scaling_exceeds_the_chi_square_scaling(self):
        """The variance factor was estimated, so the region must be larger."""
        assert confidence_scale(0.95, degrees_of_freedom=10) > confidence_scale(0.95)

    def test_the_f_scaling_approaches_chi_square_as_redundancy_grows(self):
        assert confidence_scale(0.95, degrees_of_freedom=5000) == pytest.approx(
            confidence_scale(0.95), rel=1e-3
        )

    def test_the_axes_are_the_eigenvalues(self):
        covariance = np.array([[4e-4, 1e-4], [1e-4, 1e-4]])
        ellipse = error_ellipse(covariance, confidence=None)
        eigenvalues = np.sort(np.linalg.eigvalsh(covariance))[::-1]
        assert ellipse.semi_major == pytest.approx(math.sqrt(eigenvalues[0]))
        assert ellipse.semi_minor == pytest.approx(math.sqrt(eigenvalues[1]))

    def test_a_circular_covariance_gives_a_circle(self):
        ellipse = error_ellipse(np.diag([4e-4, 4e-4]), confidence=None)
        assert ellipse.semi_major == pytest.approx(ellipse.semi_minor)

    def test_a_three_by_three_covariance_yields_a_vertical_axis(self):
        ellipse = error_ellipse(np.diag([4e-4, 1e-4, 9e-4]), confidence=None)
        assert ellipse.semi_vertical == pytest.approx(0.03)

    def test_a_wrong_shape_is_refused(self):
        with pytest.raises(ValidationError) as caught:
            error_ellipse(np.eye(4))
        assert caught.value.code == "validation.ellipse_wrong_dimension"

    def test_the_relative_ellipse_uses_the_cross_covariance(self):
        """Two stations determined by the same observations are correlated, and
        ignoring that overstates the baseline uncertainty -- often by a lot,
        which is why a network can look poor absolutely and be excellent
        relatively."""
        rho, variance = 0.9, 4e-4
        covariance = variance * rho
        joint = np.array(
            [
                [variance, 0.0, covariance, 0.0],
                [0.0, variance, 0.0, covariance],
                [covariance, 0.0, variance, 0.0],
                [0.0, covariance, 0.0, variance],
            ]
        )
        correlated = relative_ellipse(joint, [0, 1], [2, 3], confidence=None)
        independent = relative_ellipse(
            np.diag(np.diag(joint)), [0, 1], [2, 3], confidence=None
        )
        assert correlated.semi_major < independent.semi_major
        # sqrt(2(1-rho)) vs sqrt(2): a factor of sqrt(1-rho) = 0.316 here.
        assert correlated.semi_major / independent.semi_major == pytest.approx(
            math.sqrt(1 - rho), rel=1e-9
        )

    def test_mismatched_station_dimensions_are_refused(self):
        with pytest.raises(ValidationError):
            relative_ellipse(np.eye(4), [0, 1], [2])

    def test_positional_uncertainty_is_the_semi_major_axis(self):
        covariance = np.array([[4e-4, 1e-4], [1e-4, 1e-4]])
        assert positional_uncertainty(covariance, confidence=0.95) == pytest.approx(
            error_ellipse(covariance, confidence=0.95).semi_major
        )


class TestPreAnalysis:
    """FR-270, FR-271 -- design simulation, and the criterion that it agrees
    with the adjustment."""

    def test_design_reproduces_the_adjustment_covariance(self):
        """The P2 exit criterion.

        Evaluated at the *adjusted* coordinates, where the two must agree to
        machine precision. Evaluated at the approximate coordinates they differ
        by the linearisation, which the next test measures rather than hides.
        """
        reference = trilateration()
        run = adjust(reference.network, constrained(Frame.PLANE_2D))

        adjusted = {
            station_id: {
                component: float(run.parameters[column])
                for component, column in run.layout.station_columns(station_id).items()
            }
            for station_id in run.layout.station_ids()
        }
        for station_id in reference.network.stations:
            if station_id not in adjusted:
                adjusted[station_id] = {"e": 0.0, "n": 0.0}

        at_solution = trilateration()
        for station_id, values in adjusted.items():
            station = at_solution.network.stations[station_id]
            if station.constraint.is_free:
                from geocomp.core.models import Position

                at_solution.network.stations[station_id] = Station(
                    id=station_id,
                    approx_position=Position(
                        values=(
                            Quantity.from_std_dev(values["e"], 0.5, METRE),
                            Quantity.from_std_dev(values["n"], 0.5, METRE),
                            Quantity.from_std_dev(0.0, 0.5, METRE),
                        ),
                        system=station.approx_position.system,
                        crs=station.approx_position.crs,
                        height_type=station.approx_position.height_type,
                    ),
                    constraint=station.constraint,
                )

        design = simulate(
            at_solution.network, frame=Frame.PLANE_2D, datum=DatumDefinition.CONSTRAINED
        )

        for station in design.stations:
            columns = run.layout.station_columns(station.station_id)
            indices = [columns["e"], columns["n"]]
            expected = positional_uncertainty(
                run.cofactor_parameters[np.ix_(indices, indices)],
                confidence=0.95,
                degrees_of_freedom=run.degrees_of_freedom,
            )
            assert station.positional_uncertainty == pytest.approx(expected, rel=1e-10)

    def test_design_at_approximate_coordinates_agrees_to_linearisation_error(self):
        """The same comparison from the *approximate* coordinates, which is the
        situation a real design is in: nobody has observed the network, so the
        only geometry available is approximate.

        The two then differ, and the size of the difference is not arbitrary.
        **A** depends on the geometry through direction cosines, so an error of
        *e* in a coordinate perturbs them by roughly *e/s* over a baseline of
        length *s*. Here the approximate coordinates are off by |(0.3, -0.2)| =
        0.36 m and the shortest baseline is A-E at 750 m, which bounds the
        discrepancy at about 4.8e-4. Anything materially larger would mean the
        design path is doing something other than linearising elsewhere.

        The test asserts the bound *and* that the agreement is not exact,
        because a design that silently became exact here would mean it had
        stopped using the coordinates it was given.
        """
        offset = math.hypot(0.3, 0.2)
        shortest_baseline = 750.0
        bound = offset / shortest_baseline

        reference = trilateration()
        run = adjust(reference.network, constrained(Frame.PLANE_2D))
        design = simulate(
            trilateration().network, frame=Frame.PLANE_2D, datum=DatumDefinition.CONSTRAINED
        )

        discrepancies = []
        for station in design.stations:
            columns = run.layout.station_columns(station.station_id)
            indices = [columns["e"], columns["n"]]
            expected = positional_uncertainty(
                run.cofactor_parameters[np.ix_(indices, indices)],
                confidence=0.95,
                degrees_of_freedom=run.degrees_of_freedom,
            )
            discrepancies.append(abs(station.positional_uncertainty - expected) / expected)

        assert max(discrepancies) < bound
        assert max(discrepancies) > 1e-6

    def test_a_design_reports_its_redundancy_and_defect(self):
        design = simulate(
            trilateration().network, frame=Frame.PLANE_2D, datum=DatumDefinition.CONSTRAINED
        )
        assert design.degrees_of_freedom == design.observation_count - design.parameter_count
        assert "translation" in design.defect_description

    def test_a_design_reports_expected_reliability_not_only_precision(self):
        """A design can be precise and still unable to detect a blunder
        anywhere; reporting only precision gives half the answer."""
        design = simulate(
            trilateration().network, frame=Frame.PLANE_2D, datum=DatumDefinition.CONSTRAINED
        )
        assert design.reliability.results
        assert design.reliability.uncheckable

    def test_the_worst_station_is_identifiable(self):
        design = simulate(
            trilateration().network, frame=Frame.PLANE_2D, datum=DatumDefinition.CONSTRAINED
        )
        worst = design.worst_station()
        assert worst is not None
        assert all(
            worst.positional_uncertainty >= s.positional_uncertainty for s in design.stations
        )

    def test_meets_answers_the_design_question(self):
        design = simulate(
            trilateration().network, frame=Frame.PLANE_2D, datum=DatumDefinition.CONSTRAINED
        )
        worst = design.worst_station().positional_uncertainty
        assert design.meets(worst * 1.01)
        assert not design.meets(worst * 0.99)

    def test_an_inner_constraint_design_needs_no_fixed_station(self):
        """The point of pre-analysis: judge a network before deciding where to
        pin it."""
        from tests.networks import free_trilateration

        design = simulate(
            free_trilateration().network,
            frame=Frame.PLANE_2D,
            datum=DatumDefinition.INNER_CONSTRAINT,
        )
        assert design.stations


class TestInspection:
    """FR-273 -- distinct from pre-analysis (specs/archive/README.md item 6)."""

    def test_a_sound_network_produces_no_findings(self):
        report = inspect(trilateration().network, frame=Frame.PLANE_2D)
        assert report.findings == ()
        assert report.can_adjust
        assert report.is_connected

    def test_a_disconnected_network_is_blocking(self):
        reference = levelling_loop()
        reference.network.add_station(Station(id="X"))
        reference.network.add_station(Station(id="Y"))
        reference.network.add_observation(
            Observation(
                id="far",
                type=ObservationType.HEIGHT_DIFFERENCE,
                stations=("X", "Y"),
                values=(Quantity.from_std_dev(1.0, 0.002, METRE),),
            )
        )
        report = inspect(reference.network, frame=Frame.HEIGHT_1D)
        assert not report.is_connected
        assert not report.can_adjust
        assert any(f.code == "network_not_connected" for f in report.blocking)

    def test_an_isolated_station_is_blocking(self):
        reference = levelling_loop()
        reference.network.add_station(Station(id="Z"))
        report = inspect(reference.network, frame=Frame.HEIGHT_1D)
        codes = {f.code for f in report.blocking}
        assert "isolated_stations" in codes

    def test_repeated_observations_are_information_not_an_error(self):
        """Repeated measurements are good practice; a duplicated import is not.
        Surfacing them without calling either wrong is the useful behaviour."""
        reference = levelling_loop()
        original = reference.network.observations["L0"]
        reference.network.add_observation(
            Observation(
                id="L0-repeat",
                type=original.type,
                stations=original.stations,
                values=original.values,
            )
        )
        report = inspect(reference.network, frame=Frame.HEIGHT_1D)
        repeated = [f for f in report.findings if f.code == "repeated_observations"]
        assert repeated
        assert repeated[0].severity is Severity.INFO
        assert report.can_adjust

    def test_missing_approximate_coordinates_are_a_warning(self):
        reference = levelling_loop()
        reference.network.stations["B"] = Station(id="B")
        report = inspect(reference.network, frame=Frame.HEIGHT_1D)
        assert any(f.code == "missing_approximate_coordinates" for f in report.warnings)

    def test_a_dimensionality_mismatch_is_blocking(self):
        network = Network(id="dim", crs="EPSG:31982")
        for station_id in ("A", "B"):
            network.add_station(Station(id=station_id))
        network.add_observation(
            Observation(
                id="d",
                type=ObservationType.HORIZONTAL_DISTANCE,
                stations=("A", "B"),
                values=(Quantity.from_std_dev(10.0, 0.01, METRE),),
            )
        )
        report = inspect(network, frame=Frame.HEIGHT_1D)
        assert any(f.code == "wrong_dimensionality" for f in report.blocking)

    def test_an_empty_network_is_blocking(self):
        report = inspect(Network(id="empty"), frame=Frame.PLANE_2D)
        assert any(f.code == "no_active_observations" for f in report.blocking)

    def test_referential_problems_are_reported(self):
        network = Network(id="bad", crs="EPSG:31982")
        network.add_station(Station(id="A"))
        network.add_observation(
            Observation(
                id="d",
                type=ObservationType.HEIGHT_DIFFERENCE,
                stations=("A", "ghost"),
                values=(Quantity.from_std_dev(1.0, 0.002, METRE),),
            )
        )
        report = inspect(network, frame=Frame.HEIGHT_1D)
        assert any(f.code == "referential_integrity" for f in report.blocking)
