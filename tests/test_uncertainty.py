# SPDX-License-Identifier: GPL-2.0-or-later
"""Quantity, Covariance and propagation (specs/05).

The acceptance criteria of ``specs/05-uncertainty-and-covariance.md`` section 7
are the organising principle here. The one that matters most is criterion 6:
combining two quantities drawn from the same covariance through the scalar path
must raise. A sign error in a Jacobian or a silently dropped correlation
produces no exception and no obviously silly number -- just a covariance that is
quietly wrong -- so the guards have to be tested as carefully as the arithmetic.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from geocomp.core.differentiation import complex_step_jacobian
from geocomp.core.errors import DataError, ValidationError
from geocomp.core.uncertainty import (
    Covariance,
    Quantity,
    Strategy,
    UncertaintyMode,
    acos,
    asin,
    atan,
    atan2,
    combine_modes,
    cos,
    exp,
    hypot,
    log,
    propagate,
    sin,
    sqrt,
    tan,
)
from geocomp.core.units import Unit

METRE, RADIAN, NONE = Unit.METRE, Unit.RADIAN, Unit.DIMENSIONLESS


class TestConstruction:
    def test_from_std_dev_squares_the_sigma(self):
        q = Quantity.from_std_dev(10.0, 0.02, METRE)
        assert q.variance == pytest.approx(0.0004)
        assert q.std_dev == pytest.approx(0.02)

    def test_exact_has_no_variance(self):
        assert Quantity.exact(2.5, METRE).is_exact

    def test_negative_variance_is_refused(self):
        with pytest.raises(ValidationError) as caught:
            Quantity(1.0, -1.0, METRE)
        assert caught.value.code == "validation.negative_variance"

    def test_rigorous_cannot_carry_strategies(self):
        """A strategy is a record of approximation; a rigorous result has none."""
        with pytest.raises(ValidationError) as caught:
            Quantity(1.0, 0.1, METRE, UncertaintyMode.RIGOROUS, frozenset({Strategy.TYPE_DEFAULT}))
        assert caught.value.code == "validation.rigorous_with_strategies"

    def test_approximate_requires_naming_the_strategy(self):
        """FR-203: a report must be able to say *which* approximation was made."""
        with pytest.raises(ValidationError) as caught:
            Quantity.approximate(1.0, 0.1, METRE)
        assert caught.value.code == "validation.approximate_without_strategy"

    def test_relative_uncertainty_of_zero_is_refused(self):
        with pytest.raises(ValidationError):
            Quantity.from_std_dev(0.0, 0.1, METRE).relative_std_dev()


class TestScalarPropagation:
    """Each case is checked against the analytic formula written out by hand."""

    def test_sum_of_independent_variances(self):
        a = Quantity.from_std_dev(10.0, 0.03, METRE)
        b = Quantity.from_std_dev(4.0, 0.04, METRE)
        assert (a + b).variance == pytest.approx(0.03**2 + 0.04**2)
        assert (a - b).variance == pytest.approx(0.03**2 + 0.04**2)

    def test_difference_adds_variance_it_does_not_cancel(self):
        """A classic error: subtracting two values does not subtract uncertainty."""
        a = Quantity.from_std_dev(10.0, 0.03, METRE)
        assert (a - a.detached()).std_dev == pytest.approx(0.03 * math.sqrt(2))

    def test_scaling_by_a_constant(self):
        a = Quantity.from_std_dev(10.0, 0.03, METRE)
        assert (a * 3.0).std_dev == pytest.approx(0.09)

    def test_product_rule(self):
        x = Quantity.from_std_dev(3.0, 0.01, NONE)
        y = Quantity.from_std_dev(4.0, 0.02, NONE)
        expected = math.sqrt(y.value**2 * x.variance + x.value**2 * y.variance)
        assert (x * y).std_dev == pytest.approx(expected)

    def test_quotient_rule(self):
        x = Quantity.from_std_dev(3.0, 0.01, NONE)
        y = Quantity.from_std_dev(4.0, 0.02, NONE)
        expected = math.sqrt(x.variance / y.value**2 + x.value**2 * y.variance / y.value**4)
        assert (x / y).std_dev == pytest.approx(expected)

    def test_division_by_zero_is_refused(self):
        with pytest.raises(ValidationError):
            Quantity.from_std_dev(1.0, 0.1, NONE) / Quantity.exact(0.0)

    @pytest.mark.parametrize(
        ("function", "derivative", "value", "in_unit"),
        [
            (sin, math.cos, 0.7, RADIAN),
            (cos, lambda x: -math.sin(x), 0.7, RADIAN),
            (tan, lambda x: 1 / math.cos(x) ** 2, 0.7, RADIAN),
            (asin, lambda x: 1 / math.sqrt(1 - x**2), 0.4, NONE),
            (acos, lambda x: -1 / math.sqrt(1 - x**2), 0.4, NONE),
            (atan, lambda x: 1 / (1 + x**2), 0.4, NONE),
            (exp, math.exp, 0.4, NONE),
            (log, lambda x: 1 / x, 2.0, NONE),
            (sqrt, lambda x: 0.5 / math.sqrt(x), 2.0, NONE),
        ],
        ids=lambda item: getattr(item, "__name__", str(item)),
    )
    def test_elementary_function_matches_its_analytic_derivative(
        self, function, derivative, value, in_unit
    ):
        sigma = 1e-4
        result = function(Quantity.from_std_dev(value, sigma, in_unit))
        assert result.std_dev == pytest.approx(abs(derivative(value)) * sigma, rel=1e-12)

    def test_atan2_is_correct_in_every_quadrant(self):
        for y_value, x_value in [(1, 1), (1, -1), (-1, -1), (-1, 1)]:
            y = Quantity.from_std_dev(float(y_value), 0.01, METRE)
            x = Quantity.from_std_dev(float(x_value), 0.01, METRE)
            assert atan2(y, x).value == pytest.approx(math.atan2(y_value, x_value))

    def test_hypot_preserves_the_unit(self):
        result = hypot(Quantity.from_std_dev(3.0, 0.1, METRE), Quantity.from_std_dev(4.0, 0.1, METRE))
        assert result.value == pytest.approx(5.0)
        assert result.unit is METRE


class TestUnitDiscipline:
    def test_adding_different_units_raises(self):
        with pytest.raises(ValidationError) as caught:
            Quantity.from_std_dev(1.0, 0.1, METRE) + Quantity.from_std_dev(1.0, 0.1, RADIAN)
        assert caught.value.code == "validation.incompatible_units"

    def test_compound_units_are_refused_not_invented(self):
        """No square metre: GeoComp refuses rather than assigning a wrong unit."""
        with pytest.raises(ValidationError) as caught:
            Quantity.from_std_dev(2.0, 0.1, METRE) * Quantity.from_std_dev(3.0, 0.1, METRE)
        assert caught.value.code == "validation.compound_unit_not_supported"

    def test_scaling_a_length_keeps_the_length(self):
        assert (Quantity.from_std_dev(2.0, 0.1, METRE) * Quantity.exact(3.0)).unit is METRE

    def test_a_ratio_of_like_units_is_dimensionless(self):
        result = Quantity.from_std_dev(2.0, 0.1, METRE) / Quantity.from_std_dev(4.0, 0.1, METRE)
        assert result.unit is NONE

    def test_trigonometric_functions_require_an_angle(self):
        with pytest.raises(ValidationError):
            sin(Quantity.from_std_dev(1.0, 0.1, METRE))

    def test_inverse_trigonometric_functions_return_an_angle(self):
        assert asin(Quantity.from_std_dev(0.5, 0.01, NONE)).unit is RADIAN

    def test_powers_of_dimensioned_quantities_are_refused(self):
        with pytest.raises(ValidationError) as caught:
            Quantity.from_std_dev(2.0, 0.1, METRE) ** 2
        assert caught.value.code == "validation.power_of_dimensioned_quantity"


class TestModeContagion:
    def test_one_approximate_input_makes_the_result_approximate(self):
        approximate = Quantity.approximate(2.0, 0.01, METRE, Strategy.NOMINAL_PRECISION)
        rigorous = Quantity.from_std_dev(3.0, 0.02, METRE)
        assert (approximate + rigorous).mode is UncertaintyMode.APPROXIMATE

    def test_strategies_are_unioned(self):
        first = Quantity.approximate(2.0, 0.01, METRE, Strategy.NOMINAL_PRECISION)
        second = Quantity.approximate(3.0, 0.02, METRE, Strategy.TYPE_DEFAULT)
        assert (first + second).strategies == {Strategy.NOMINAL_PRECISION, Strategy.TYPE_DEFAULT}

    def test_rigorous_inputs_stay_rigorous(self):
        a = Quantity.from_std_dev(2.0, 0.01, METRE)
        b = Quantity.from_std_dev(3.0, 0.02, METRE)
        assert (a + b).mode is UncertaintyMode.RIGOROUS
        assert not (a + b).strategies

    def test_mode_survives_an_elementary_function(self):
        approximate = Quantity.approximate(0.5, 0.01, RADIAN, Strategy.TYPE_DEFAULT)
        assert sin(approximate).mode is UncertaintyMode.APPROXIMATE

    def test_combine_modes_over_many_operands(self):
        mode, strategies = combine_modes(
            Quantity.from_std_dev(1.0, 0.1, METRE),
            Quantity.approximate(2.0, 0.1, METRE, Strategy.DOMINANT_TERM),
            Quantity.from_std_dev(3.0, 0.1, METRE),
        )
        assert mode is UncertaintyMode.APPROXIMATE
        assert strategies == {Strategy.DOMINANT_TERM}


class TestCovarianceValidation:
    def test_a_non_symmetric_matrix_is_refused_naming_the_offending_pair(self):
        with pytest.raises(DataError) as caught:
            Covariance(np.array([[1.0, 0.5], [0.4, 1.0]]), ("a", "b"), (METRE, METRE))
        assert caught.value.code == "data.covariance_not_symmetric"
        assert caught.value.context["at"] == ["a", "b"]

    def test_a_non_psd_matrix_is_refused(self):
        """An indefinite input covariance would otherwise surface much later as
        a nonsensical adjustment."""
        with pytest.raises(DataError) as caught:
            Covariance(np.array([[1.0, 2.0], [2.0, 1.0]]), ("a", "b"), (METRE, METRE))
        assert caught.value.code == "data.covariance_not_positive_semidefinite"
        assert caught.value.context["smallest_eigenvalue"] < 0

    def test_a_singular_but_psd_matrix_is_accepted(self):
        """Rank deficiency is legitimate -- a perfectly correlated pair, or a
        constrained component with no freedom."""
        Covariance(np.array([[1.0, 1.0], [1.0, 1.0]]), ("a", "b"), (METRE, METRE))

    def test_labels_are_mandatory_and_must_match_the_size(self):
        with pytest.raises(DataError) as caught:
            Covariance(np.eye(3), ("a", "b"), (METRE, METRE))
        assert caught.value.code == "data.covariance_label_count"

    def test_duplicate_labels_are_refused(self):
        with pytest.raises(DataError):
            Covariance(np.eye(2), ("a", "a"), (METRE, METRE))

    def test_unknown_label_lookup_lists_the_valid_ones(self):
        covariance = Covariance(np.eye(2), ("a", "b"), (METRE, METRE))
        with pytest.raises(ValidationError) as caught:
            covariance.index("c")
        assert caught.value.context["expected"] == ["a", "b"]


class TestCorrelationGuard:
    """specs/05 section 3.2 -- the boundary between the scalar and vector paths."""

    @pytest.fixture
    def correlated(self):
        return Covariance(
            np.array([[4.0, 2.0], [2.0, 9.0]]), ("x", "y"), (METRE, METRE)
        )

    def test_quantities_from_one_covariance_share_a_tag(self, correlated):
        x = correlated.quantity("x", 1.0)
        y = correlated.quantity("y", 2.0)
        assert x.covariance_ref == y.covariance_ref is not None

    @pytest.mark.parametrize("operation", ["add", "sub", "mul", "truediv"])
    def test_the_scalar_path_refuses_correlated_operands(self, correlated, operation):
        x = correlated.quantity("x", 1.0)
        y = correlated.quantity("y", 2.0)
        with pytest.raises(ValidationError) as caught:
            getattr(x, f"__{operation}__")(y)
        assert caught.value.code == "validation.correlated_scalar_path"

    def test_hypot_and_atan2_refuse_correlated_operands_too(self, correlated):
        x = correlated.quantity("x", 3.0)
        y = correlated.quantity("y", 4.0)
        for function in (hypot, atan2):
            with pytest.raises(ValidationError):
                function(x, y)

    def test_the_error_says_what_to_do_instead(self, correlated):
        """NFR-006: what failed, why, and what the user can do about it."""
        x, y = correlated.quantity("x", 1.0), correlated.quantity("y", 2.0)
        with pytest.raises(ValidationError) as caught:
            x + y
        guidance = caught.value.context["expected"]
        assert "propagate()" in guidance and "detached()" in guidance

    def test_quantities_from_different_covariances_combine_freely(self):
        first = Covariance(np.eye(1), ("x",), (METRE,)).quantity("x", 1.0)
        second = Covariance(np.diag([4.0]), ("y",), (METRE,)).quantity("y", 2.0)
        assert (first + second).value == pytest.approx(3.0)

    def test_detached_is_the_explicit_escape_hatch(self, correlated):
        x, y = correlated.quantity("x", 1.0), correlated.quantity("y", 2.0)
        result = x.detached().with_strategy(Strategy.INDEPENDENCE_ASSUMED) + y
        assert result.mode is UncertaintyMode.APPROXIMATE
        assert Strategy.INDEPENDENCE_ASSUMED in result.strategies


class TestRigorousPropagation:
    def test_propagation_matches_the_hand_written_formula(self):
        """Reducing a slope distance to horizontal: dh = d sin(z)."""
        d, z = 13.204, math.radians(88.129861)
        sigma_d, sigma_z = 0.003, math.radians(5 / 3600)
        rho = 0.7

        covariance = Covariance(
            np.array(
                [
                    [sigma_d**2, rho * sigma_d * sigma_z],
                    [rho * sigma_d * sigma_z, sigma_z**2],
                ]
            ),
            ("d", "z"),
            (METRE, RADIAN),
        )
        jacobian = np.array([[math.sin(z), d * math.cos(z)]])
        result = propagate(jacobian, covariance, ["dh"], [METRE])

        expected = (
            math.sin(z) ** 2 * sigma_d**2
            + (d * math.cos(z)) ** 2 * sigma_z**2
            + 2 * math.sin(z) * d * math.cos(z) * rho * sigma_d * sigma_z
        )
        assert result.variance("dh") == pytest.approx(expected, rel=1e-14)

    def test_dropping_the_correlation_changes_the_answer(self):
        """The cross term is the reason FR-208 exists. If ignoring correlation
        made no difference, carrying it would not be worth the machinery."""
        d, z = 13.204, math.radians(88.129861)
        sigma_d, sigma_z = 0.003, math.radians(5 / 3600)
        jacobian = np.array([[math.sin(z), d * math.cos(z)]])

        correlated = Covariance(
            np.array([[sigma_d**2, 0.7 * sigma_d * sigma_z], [0.7 * sigma_d * sigma_z, sigma_z**2]]),
            ("d", "z"),
            (METRE, RADIAN),
        )
        independent = Covariance(
            np.diag([sigma_d**2, sigma_z**2]), ("d", "z"), (METRE, RADIAN)
        )

        with_correlation = propagate(jacobian, correlated, ["dh"], [METRE]).variance("dh")
        without = propagate(jacobian, independent, ["dh"], [METRE]).variance("dh")
        assert with_correlation > without

    def test_propagation_composes(self):
        """specs/05 section 2.1: g after f equals the combined propagation, up to
        linearisation error. This is what lets each pre-processing step be an
        independent algorithm without losing rigour across the chain."""
        covariance = Covariance(
            np.array([[4.0, 1.0], [1.0, 9.0]]), ("a", "b"), (METRE, METRE)
        )
        first = np.array([[2.0, 0.0], [0.0, 3.0]])
        second = np.array([[1.0, 1.0]])

        stepwise = propagate(
            second,
            propagate(first, covariance, ["u", "v"], [METRE, METRE]),
            ["w"],
            [METRE],
        )
        combined = propagate(second @ first, covariance, ["w"], [METRE])
        assert stepwise.variance("w") == pytest.approx(combined.variance("w"), rel=1e-14)

    def test_the_result_stays_symmetric_through_a_long_chain(self):
        """Floating point makes A Sigma A^T slightly asymmetric; propagate must
        re-symmetrise or a long chain eventually trips its own validation."""
        rng = np.random.default_rng(20260826)
        size = 6
        root = rng.normal(size=(size, size))
        covariance = Covariance(
            root @ root.T, tuple(f"q{i}" for i in range(size)), (METRE,) * size
        )
        for _ in range(50):
            jacobian = rng.normal(size=(size, size))
            covariance = propagate(
                jacobian, covariance, covariance.labels, covariance.units
            )
        assert np.allclose(covariance.matrix, covariance.matrix.T, atol=0.0)

    def test_a_mismatched_jacobian_is_refused(self):
        covariance = Covariance(np.eye(2), ("a", "b"), (METRE, METRE))
        with pytest.raises(ValidationError) as caught:
            propagate(np.ones((1, 3)), covariance, ["c"], [METRE])
        assert caught.value.code == "validation.jacobian_shape_mismatch"

    def test_output_labels_must_match_the_jacobian_rows(self):
        covariance = Covariance(np.eye(2), ("a", "b"), (METRE, METRE))
        with pytest.raises(ValidationError) as caught:
            propagate(np.ones((2, 2)), covariance, ["only_one"], [METRE])
        assert caught.value.code == "validation.output_label_count"

    def test_a_numeric_derivative_marks_the_result_approximate(self):
        """specs/05 section 2.2: a finite-difference Jacobian is flagged, because
        the derivative itself is approximate."""
        covariance = Covariance(np.eye(2), ("a", "b"), (METRE, METRE))
        result = propagate(
            np.ones((1, 2)),
            covariance,
            ["c"],
            [METRE],
            strategies=[Strategy.NUMERIC_DERIVATIVE],
        )
        assert result.mode is UncertaintyMode.APPROXIMATE
        assert Strategy.NUMERIC_DERIVATIVE in result.strategies


class TestCovarianceOperations:
    def test_sub_preserves_correlations_between_the_kept_components(self):
        full = Covariance(
            np.array([[4.0, 1.0, 0.5], [1.0, 9.0, 2.0], [0.5, 2.0, 16.0]]),
            ("a", "b", "c"),
            (METRE,) * 3,
        )
        part = full.sub(["a", "c"])
        assert part.labels == ("a", "c")
        assert part.matrix[0, 1] == pytest.approx(0.5)

    def test_sub_can_reorder(self):
        full = Covariance(np.array([[4.0, 1.0], [1.0, 9.0]]), ("a", "b"), (METRE, METRE))
        reordered = full.sub(["b", "a"])
        assert reordered.matrix[0, 0] == pytest.approx(9.0)

    def test_correlation_matrix_has_a_unit_diagonal(self):
        covariance = Covariance(np.array([[4.0, 3.0], [3.0, 9.0]]), ("a", "b"), (METRE, METRE))
        correlation = covariance.to_correlation()
        assert np.allclose(np.diag(correlation), 1.0)
        assert correlation[0, 1] == pytest.approx(3.0 / (2.0 * 3.0))

    def test_correlation_of_a_zero_variance_component_is_zero_not_nan(self):
        covariance = Covariance(np.diag([4.0, 0.0]), ("a", "b"), (METRE, METRE))
        assert not np.isnan(covariance.to_correlation()).any()

    def test_from_quantities_builds_the_declared_correlation(self):
        covariance = Covariance.from_quantities(
            {
                "d": Quantity.from_std_dev(10.0, 0.02, METRE),
                "z": Quantity.from_std_dev(1.5, 0.001, RADIAN),
            },
            correlations={("d", "z"): 0.5},
        )
        assert covariance.matrix[0, 1] == pytest.approx(0.5 * 0.02 * 0.001)

    def test_an_out_of_range_correlation_is_refused(self):
        with pytest.raises(ValidationError):
            Covariance.from_quantities(
                {"a": Quantity.from_std_dev(1.0, 0.1, METRE), "b": Quantity.from_std_dev(1.0, 0.1, METRE)},
                correlations={("a", "b"): 1.5},
            )

    def test_quantities_requires_one_value_per_label(self):
        covariance = Covariance(np.eye(2), ("a", "b"), (METRE, METRE))
        with pytest.raises(ValidationError):
            covariance.quantities([1.0])


class TestSerialisation:
    def test_quantity_round_trips_bit_identically(self):
        """NFR-007: values serialise at full precision, never at display precision."""
        original = Quantity.approximate(
            1.2345678901234567, 0.001234567890123, METRE, Strategy.TYPE_DEFAULT
        )
        restored = Quantity.from_dict(original.to_dict())
        assert restored.value == original.value
        assert restored.variance == original.variance
        assert restored.unit is original.unit
        assert restored.mode is original.mode
        assert restored.strategies == original.strategies

    def test_covariance_round_trips_bit_identically(self):
        original = Covariance(
            np.array([[4.0, 1.23456789012345], [1.23456789012345, 9.0]]),
            ("a", "b"),
            (METRE, RADIAN),
        )
        restored = Covariance.from_dict(original.to_dict())
        assert np.array_equal(restored.matrix, original.matrix)
        assert restored.labels == original.labels
        assert restored.units == original.units

    def test_the_covariance_ref_survives_a_round_trip(self):
        """The ref is content-derived, not object identity, so the correlation
        guard keeps working across a save and reload."""
        original = Covariance(np.diag([1.0, 2.0]), ("a", "b"), (METRE, METRE))
        assert Covariance.from_dict(original.to_dict()).ref == original.ref

    def test_enumerations_serialise_by_name_not_ordinal(self):
        payload = Quantity.approximate(1.0, 0.1, METRE, Strategy.DOMINANT_TERM).to_dict()
        assert payload["unit"] == "METRE"
        assert payload["mode"] == "APPROXIMATE"
        assert payload["strategies"] == ["DOMINANT_TERM"]

    def test_a_rigorous_quantity_omits_the_strategies_key(self):
        assert "strategies" not in Quantity.from_std_dev(1.0, 0.1, METRE).to_dict()


class TestJacobianVerification:
    """specs/05 section 7 criterion 1: every analytic Jacobian must agree with
    complex-step differentiation to 1e-9 relative.

    A sign error in a Jacobian produces a plausible-looking wrong uncertainty,
    which is the failure this whole module exists to prevent.
    """

    @pytest.mark.parametrize(
        ("name", "vector_function", "analytic", "point"),
        [
            (
                "slope reduction",
                lambda v: np.array([v[0] * np.sin(v[1]), v[0] * np.cos(v[1])]),
                lambda d, z: np.array(
                    [[math.sin(z), d * math.cos(z)], [math.cos(z), -d * math.sin(z)]]
                ),
                (13.204, math.radians(88.13)),
            ),
            (
                "polar to cartesian",
                lambda v: np.array([v[0] * np.cos(v[1]), v[0] * np.sin(v[1])]),
                lambda r, t: np.array(
                    [[math.cos(t), -r * math.sin(t)], [math.sin(t), r * math.cos(t)]]
                ),
                (250.0, math.radians(37.5)),
            ),
            (
                "height difference",
                lambda v: np.array([v[0] * np.cos(v[1]) + v[2] - v[3]]),
                lambda d, z, hi, hs: np.array([[math.cos(z), -d * math.sin(z), 1.0, -1.0]]),
                (13.204, math.radians(88.13), 1.5, 1.495),
            ),
        ],
        ids=lambda item: item if isinstance(item, str) else "",
    )
    def test_analytic_jacobian_agrees_with_complex_step(
        self, name, vector_function, analytic, point
    ):
        numeric = complex_step_jacobian(vector_function, point)
        expected = analytic(*point)
        assert numeric.shape == expected.shape
        scale = max(float(np.max(np.abs(expected))), 1.0)
        assert float(np.max(np.abs(numeric - expected))) / scale < 1e-9
