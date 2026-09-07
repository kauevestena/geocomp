# SPDX-License-Identifier: GPL-2.0-or-later
"""The numerical derivatives of ``specs/05`` section 2.2.

This file exists because a pre-P7 review found the module it tests to be 40%
covered and five of its six public functions to have no caller anywhere --
neither in ``geocomp/`` nor in the suite. Only ``complex_step_jacobian`` was
used, by two Jacobian checks; ``tests/test_adjustment.py`` needed the *other*
method and had inlined its own copy rather than importing this one.

That matters more than a coverage number. The module is the instrument every
analytic Jacobian in the project is measured against, and an instrument nobody
checks is not evidence. The tests below therefore do two things: exercise the
public surface, and verify the claim the module's own docstring makes for
choosing the complex step -- that it is accurate where a difference is not.
"""

from __future__ import annotations

import cmath
import math

import numpy as np
import pytest

from geocomp.core.differentiation import (
    DEFAULT_COMPLEX_STEP,
    central_difference,
    central_difference_jacobian,
    complex_step,
    complex_step_jacobian,
    is_complex_safe,
    numeric_jacobian,
)


def _analytic(x: float) -> float:
    """d/dx of ``exp(x) / sqrt(sin(x)^3 + cos(x)^3)``.

    Squire and Trapp's test function for the complex step, and the standard one:
    it is smooth, its derivative is nowhere near its value in magnitude, and the
    subtractive cancellation that limits a difference is easy to see in it.
    """
    s, c = math.sin(x), math.cos(x)
    denominator = math.sqrt(s**3 + c**3)
    return math.exp(x) * (
        1.0 / denominator
        - 1.5 * (s**2 * c - c**2 * s) / denominator**3
    )


def _f(x):
    trig = cmath.sin if isinstance(x, complex) else math.sin
    cos = cmath.cos if isinstance(x, complex) else math.cos
    root = cmath.sqrt if isinstance(x, complex) else math.sqrt
    exp = cmath.exp if isinstance(x, complex) else math.exp
    return exp(x) / root(trig(x) ** 3 + cos(x) ** 3)


class TestScalarDerivatives:
    def test_the_complex_step_is_accurate_to_machine_precision(self):
        x = 0.7
        assert complex_step(_f, x) == pytest.approx(_analytic(x), rel=1e-14)

    def test_a_central_difference_is_accurate_to_about_ten_digits(self):
        x = 0.7
        assert central_difference(_f, x) == pytest.approx(_analytic(x), rel=1e-9)

    def test_the_complex_step_is_the_more_accurate_of_the_two(self):
        """The module's justification, checked rather than asserted.

        ``differentiation.py`` explains at length why the complex step is worth
        having: a difference cancels two nearly equal numbers and cannot beat
        about ``sqrt(eps)``, while the complex step has no subtraction at all.
        If that ever stopped being true the module would have no reason to
        exist, so it is measured here.
        """
        x = 0.7
        truth = _analytic(x)
        stepped = abs(complex_step(_f, x) - truth)
        differenced = abs(central_difference(_f, x) - truth)
        assert stepped < differenced
        # Not marginally: the difference loses at least four orders of magnitude.
        assert stepped < differenced * 1e-4

    def test_a_smaller_step_does_not_help_a_difference(self):
        """Which is the failure the complex step exists to avoid.

        Shrinking *h* trades truncation error for cancellation. Below the
        optimum the error grows again, and a caller tuning *h* downwards to get
        a better answer gets a worse one with no indication.
        """
        x = 0.7
        truth = _analytic(x)
        at_optimum = abs(central_difference(_f, x) - truth)
        far_too_small = abs(central_difference(_f, x, step=1e-13) - truth)
        assert far_too_small > at_optimum

    def test_a_function_that_cannot_take_a_complex_argument_is_reported(self):
        """Rather than silently degrading: a caller that asked for machine
        precision should learn it is not getting it."""
        with pytest.raises(TypeError, match="complex-safe"):
            complex_step(lambda x: math.sin(x), 0.5)

    def test_the_default_step_is_far_below_the_square_root_of_epsilon(self):
        """The property that makes the step size a non-decision."""
        assert DEFAULT_COMPLEX_STEP < math.sqrt(float(np.finfo(float).eps)) * 1e-8


class TestJacobians:
    @staticmethod
    def _map(v):
        x, y = v[0], v[1]
        return [x * x * y, x + 3.0 * y, x * y * y]

    @staticmethod
    def _truth(x, y):
        return np.array([[2.0 * x * y, x * x], [1.0, 3.0], [y * y, 2.0 * x * y]])

    def test_the_complex_step_jacobian_has_the_right_shape_and_values(self):
        jacobian = complex_step_jacobian(self._map, [2.0, 5.0])
        assert jacobian.shape == (3, 2)
        assert jacobian == pytest.approx(self._truth(2.0, 5.0), rel=1e-13)

    def test_the_central_difference_jacobian_agrees(self):
        jacobian = central_difference_jacobian(self._map, [2.0, 5.0])
        assert jacobian.shape == (3, 2)
        assert jacobian == pytest.approx(self._truth(2.0, 5.0), rel=1e-8)

    def test_an_explicit_step_is_used_for_every_column(self):
        jacobian = central_difference_jacobian(self._map, [2.0, 5.0], step=1e-5)
        assert jacobian == pytest.approx(self._truth(2.0, 5.0), rel=1e-8)


class TestChoosingTheMethod:
    def test_a_complex_safe_function_is_recognised(self):
        assert is_complex_safe(lambda v: [v[0] * v[0]], [3.0])

    def test_a_complex_safe_scalar_function_is_recognised(self):
        assert is_complex_safe(lambda x: x * x, 3.0)

    def test_a_math_module_function_is_not(self):
        assert not is_complex_safe(lambda x: math.sin(x), 0.5)

    def test_a_function_returning_a_real_from_a_complex_input_is_not(self):
        """``np.abs`` of a complex number is real, so the imaginary part the
        method depends on is gone. Accepting the argument is not the test."""
        assert not is_complex_safe(lambda v: np.abs(np.asarray(v)), [3.0])

    def test_numeric_jacobian_takes_the_accurate_method_when_it_can(self):
        jacobian, method = numeric_jacobian(TestJacobians._map, [2.0, 5.0])
        assert method == "complex_step"
        assert jacobian == pytest.approx(TestJacobians._truth(2.0, 5.0), rel=1e-13)

    def test_numeric_jacobian_falls_back_and_says_so(self):
        """The flag is the point (``specs/05`` section 2.2): a caller recording
        an approximate derivative has to be told the derivative was approximate,
        and a returned Jacobian carries no sign of which method produced it."""

        def not_complex_safe(v):
            return [math.hypot(float(np.real(v[0])), float(np.real(v[1])))]

        jacobian, method = numeric_jacobian(not_complex_safe, [3.0, 4.0])
        assert method == "central_difference"
        assert jacobian == pytest.approx(np.array([[0.6, 0.8]]), rel=1e-7)

    def test_the_accurate_method_can_be_declined(self):
        _, method = numeric_jacobian(
            TestJacobians._map, [2.0, 5.0], prefer_complex_step=False
        )
        assert method == "central_difference"
