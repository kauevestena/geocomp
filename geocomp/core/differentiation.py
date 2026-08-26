# SPDX-License-Identifier: GPL-2.0-or-later
"""Numerical Jacobians.

``specs/05-uncertainty-and-covariance.md`` section 2.2 ranks three ways to
obtain the design matrix **A** = df/dx, in order of preference:

1. **Analytic**, hand-derived and unit-tested. The default, and what every
   standard geodetic transformation uses.
2. **Complex-step**, accurate to machine precision. Used to *verify* the
   analytic derivatives.
3. **Central differences**, the fallback for functions that are not
   complex-safe. Flagged in the result, because the derivative is approximate.

The verification step is the point of this module. A sign error in a Jacobian
produces a plausible-looking, wrong uncertainty -- no exception, no obviously
silly number, just a covariance that is quietly incorrect. The specification
therefore requires every analytic Jacobian to have a test comparing it against
one of the numerical methods here.

## Why complex-step

A central difference computes ``(f(x+h) - f(x-h)) / 2h``. The subtraction of two
nearly equal numbers loses precision as *h* shrinks, while truncation error
grows as *h* grows; the best achievable accuracy is around ``sqrt(eps)``, about
1e-8 relative.

The complex step evaluates ``Im(f(x + ih)) / h``. For a real-analytic *f* this
has no subtraction of nearly equal quantities at all, so *h* can be made
arbitrarily small -- 1e-20 -- and the result is accurate to machine precision
with no step-size tuning. It requires only that *f* be implemented with
complex-safe operations: ``math.sin`` will not do, ``cmath.sin`` or the NumPy
equivalent will.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

import numpy as np

__all__ = [
    "DEFAULT_COMPLEX_STEP",
    "central_difference",
    "central_difference_jacobian",
    "complex_step",
    "complex_step_jacobian",
    "is_complex_safe",
    "numeric_jacobian",
]

#: Small enough that the truncation error is far below machine epsilon, large
#: enough to stay clear of denormal underflow.
DEFAULT_COMPLEX_STEP = 1e-20


def complex_step(
    function: Callable[[complex], complex], x: float, step: float = DEFAULT_COMPLEX_STEP
) -> float:
    """Derivative of a scalar, real-analytic *function* at *x*.

    *function* must be implemented with complex-safe operations.

    Raises:
        TypeError: if *function* cannot accept a complex argument -- reported
            plainly rather than silently degrading to a less accurate method,
            because a caller that asked for machine precision should learn it
            is not getting it.
    """
    try:
        value = function(complex(x, step))
    except TypeError as error:
        raise TypeError(
            "complex_step requires a complex-safe function; use cmath or numpy "
            "rather than the math module, or fall back to central_difference"
        ) from error
    return float(np.imag(value)) / step


def central_difference(
    function: Callable[[float], float], x: float, step: float | None = None
) -> float:
    """Derivative of *function* at *x* by central differences.

    The step defaults to ``eps**(1/3) * max(|x|, 1)``, which balances truncation
    against round-off for a second-order scheme. Accuracy is roughly 1e-10
    relative at best -- adequate as a fallback, not as a reference.
    """
    if step is None:
        step = float(np.finfo(float).eps) ** (1.0 / 3.0) * max(abs(x), 1.0)
    return (function(x + step) - function(x - step)) / (2.0 * step)


def complex_step_jacobian(
    function: Callable[[Sequence[complex]], Sequence[complex]],
    x: Sequence[float],
    step: float = DEFAULT_COMPLEX_STEP,
) -> np.ndarray:
    """Jacobian of a vector function by the complex step, shape ``(m, n)``."""
    x = np.asarray(x, dtype=float)
    columns: list[np.ndarray] = []
    for index in range(x.size):
        perturbed = x.astype(complex)
        perturbed[index] += 1j * step
        columns.append(np.imag(np.asarray(function(perturbed), dtype=complex)) / step)
    return np.column_stack(columns)


def central_difference_jacobian(
    function: Callable[[Sequence[float]], Sequence[float]],
    x: Sequence[float],
    step: float | None = None,
) -> np.ndarray:
    """Jacobian of a vector function by central differences, shape ``(m, n)``."""
    x = np.asarray(x, dtype=float)
    eps_cube_root = float(np.finfo(float).eps) ** (1.0 / 3.0)
    columns: list[np.ndarray] = []
    for index in range(x.size):
        h = step if step is not None else eps_cube_root * max(abs(float(x[index])), 1.0)
        forward, backward = x.copy(), x.copy()
        forward[index] += h
        backward[index] -= h
        columns.append(
            (
                np.asarray(function(forward), dtype=float)
                - np.asarray(function(backward), dtype=float)
            )
            / (2.0 * h)
        )
    return np.column_stack(columns)


def is_complex_safe(function: Callable, x: Sequence[float] | float) -> bool:
    """Whether *function* survives a complex argument.

    Lets a caller choose the accurate method when it is available and the
    fallback when it is not, without the choice being a guess.
    """
    try:
        probe = complex(float(x), 1e-30) if np.isscalar(x) else np.asarray(x, dtype=complex)
        result = function(probe)
        return bool(np.iscomplexobj(np.asarray(result)))
    except (TypeError, ValueError, AttributeError):
        return False


def numeric_jacobian(
    function: Callable,
    x: Sequence[float],
    *,
    prefer_complex_step: bool = True,
) -> tuple[np.ndarray, str]:
    """Jacobian of *function* at *x*, with the method actually used.

    Returns:
        ``(jacobian, method)`` where *method* is ``"complex_step"`` or
        ``"central_difference"``. The method is returned rather than hidden so
        the caller can record that a derivative was approximate -- which
        ``specs/05`` section 2.2 requires to be flagged.
    """
    if prefer_complex_step and is_complex_safe(function, x):
        return complex_step_jacobian(function, x), "complex_step"
    return central_difference_jacobian(function, x), "central_difference"
