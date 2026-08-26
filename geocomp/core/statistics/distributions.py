# SPDX-License-Identifier: GPL-2.0-or-later
"""Distribution functions, with a NumPy-only fallback.

``specs/06-adjustment-core.md`` section 4 needs the normal, chi-square, F and
Student t distributions: the global test compares a variance ratio against
chi-square quantiles, data snooping needs normal (or tau) critical values, and
the minimal detectable bias needs a non-centrality parameter.

SciPy provides all of these and is used when it is present. It is **optional**
(``specs/03-architecture.md`` section 3.7, ADR-0008), so this module also
implements every function directly. That fallback is not decoration: the
development container here has no SciPy, so without it nothing statistical could
be computed or tested at all.

Accuracy of the fallback is around 1e-12 relative for the CDFs and 1e-10 for the
quantiles, which is far below any tolerance a geodetic test applies. Both paths
are compared against each other whenever SciPy is available, and both against
published table values regardless.

The algorithms are the standard ones: a rational approximation with a Newton
refinement for the normal quantile; the series and continued-fraction forms of
the regularised incomplete gamma for chi-square; a Lentz continued fraction for
the regularised incomplete beta, which gives F and t.
"""

from __future__ import annotations

import math

from geocomp.core.errors import ValidationError

__all__ = [
    "USING_SCIPY",
    "chi2_cdf",
    "chi2_quantile",
    "f_cdf",
    "f_quantile",
    "non_centrality",
    "normal_cdf",
    "normal_quantile",
    "t_cdf",
    "t_quantile",
]

try:  # pragma: no cover - exercised by whichever environment runs the tests
    from scipy import stats as _scipy_stats

    USING_SCIPY = True
except ImportError:  # pragma: no cover
    _scipy_stats = None
    USING_SCIPY = False

#: Iteration limits for the series and continued fractions below. Generous:
#: convergence is fast, and a runaway loop should be reported rather than spun on.
_MAX_ITERATIONS = 500
_EPSILON = 1e-15
#: Guards the continued fractions against a zero denominator (Lentz's method).
_TINY = 1e-300


# -- normal --------------------------------------------------------------


def normal_cdf(x: float) -> float:
    """Standard normal cumulative distribution."""
    if _scipy_stats is not None:
        return float(_scipy_stats.norm.cdf(x))
    return 0.5 * math.erfc(-x / math.sqrt(2.0))


def normal_quantile(p: float) -> float:
    """Standard normal quantile (inverse CDF).

    Rational approximation followed by one Newton step against
    :func:`normal_cdf`, which takes the accuracy from about 1e-9 to machine
    precision. Worth the extra line: this value becomes a critical value that a
    user compares a test statistic against.
    """
    _check_probability(p, "normal_quantile")
    if _scipy_stats is not None:
        return float(_scipy_stats.norm.ppf(p))

    # Acklam's rational approximation.
    a = (-3.969683028665376e01, 2.209460984245205e02, -2.759285104469687e02,
         1.383577518672690e02, -3.066479806614716e01, 2.506628277459239e00)
    b = (-5.447609879822406e01, 1.615858368580409e02, -1.556989798598866e02,
         6.680131188771972e01, -1.328068155288572e01)
    c = (-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e00,
         -2.549732539343734e00, 4.374664141464968e00, 2.938163982698783e00)
    d = (7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e00,
         3.754408661907416e00)

    low, high = 0.02425, 1.0 - 0.02425
    if p < low:
        q = math.sqrt(-2.0 * math.log(p))
        x = (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / (
            (((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0
        )
    elif p <= high:
        q = p - 0.5
        r = q * q
        x = (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / (
            ((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1.0
        )
    else:
        q = math.sqrt(-2.0 * math.log(1.0 - p))
        x = -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / (
            (((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0
        )

    # One Newton step: f(x) = Phi(x) - p, f'(x) = phi(x).
    density = math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)
    if density > 0.0:
        x -= (normal_cdf(x) - p) / density
    return x


# -- incomplete gamma, and chi-square ------------------------------------


def _lower_gamma_regularised(a: float, x: float) -> float:
    """Regularised lower incomplete gamma P(a, x).

    Series expansion below the crossover and the continued fraction above it;
    each converges quickly on its own side and slowly on the other.
    """
    if x < 0.0 or a <= 0.0:
        raise ValidationError("incomplete_gamma_domain", a=a, x=x)
    if x == 0.0:
        return 0.0
    if x < a + 1.0:
        return _gamma_series(a, x)
    return 1.0 - _gamma_continued_fraction(a, x)


def _gamma_series(a: float, x: float) -> float:
    log_gamma = math.lgamma(a)
    term = 1.0 / a
    total = term
    n = a
    for _ in range(_MAX_ITERATIONS):
        n += 1.0
        term *= x / n
        total += term
        if abs(term) < abs(total) * _EPSILON:
            break
    return total * math.exp(-x + a * math.log(x) - log_gamma)


def _gamma_continued_fraction(a: float, x: float) -> float:
    """Q(a, x) by the modified Lentz algorithm."""
    log_gamma = math.lgamma(a)
    b = x + 1.0 - a
    c = 1.0 / _TINY
    d = 1.0 / b
    h = d
    for i in range(1, _MAX_ITERATIONS + 1):
        an = -i * (i - a)
        b += 2.0
        d = an * d + b
        if abs(d) < _TINY:
            d = _TINY
        c = b + an / c
        if abs(c) < _TINY:
            c = _TINY
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < _EPSILON:
            break
    return math.exp(-x + a * math.log(x) - log_gamma) * h


def chi2_cdf(x: float, degrees_of_freedom: int) -> float:
    """Chi-square cumulative distribution."""
    _check_degrees_of_freedom(degrees_of_freedom, "chi2_cdf")
    if x <= 0.0:
        return 0.0
    if _scipy_stats is not None:
        return float(_scipy_stats.chi2.cdf(x, degrees_of_freedom))
    return _lower_gamma_regularised(degrees_of_freedom / 2.0, x / 2.0)


def chi2_quantile(p: float, degrees_of_freedom: int) -> float:
    """Chi-square quantile.

    Used for both bounds of the global test, which is two-sided: an
    unexpectedly *small* variance factor means the a priori precisions were
    pessimistic, and that is information rather than a pass
    (``specs/06`` section 4.1).
    """
    _check_probability(p, "chi2_quantile")
    _check_degrees_of_freedom(degrees_of_freedom, "chi2_quantile")
    if _scipy_stats is not None:
        return float(_scipy_stats.chi2.ppf(p, degrees_of_freedom))
    return _invert_cdf(
        lambda x: chi2_cdf(x, degrees_of_freedom),
        p,
        # Wilson-Hilferty gives a good starting bracket.
        guess=degrees_of_freedom
        * (1.0 - 2.0 / (9.0 * degrees_of_freedom)
           + normal_quantile(p) * math.sqrt(2.0 / (9.0 * degrees_of_freedom))) ** 3,
    )


# -- incomplete beta, and F and t ----------------------------------------


def _incomplete_beta(a: float, b: float, x: float) -> float:
    """Regularised incomplete beta I_x(a, b)."""
    if x < 0.0 or x > 1.0:
        raise ValidationError("incomplete_beta_domain", a=a, b=b, x=x)
    if x in (0.0, 1.0):
        return x
    front = math.exp(
        math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
        + a * math.log(x) + b * math.log(1.0 - x)
    )
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _beta_continued_fraction(a, b, x) / a
    return 1.0 - front * _beta_continued_fraction(b, a, 1.0 - x) / b


def _beta_continued_fraction(a: float, b: float, x: float) -> float:
    """Lentz continued fraction for the incomplete beta."""
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < _TINY:
        d = _TINY
    d = 1.0 / d
    h = d
    for m in range(1, _MAX_ITERATIONS + 1):
        m2 = 2 * m
        # Even step.
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < _TINY:
            d = _TINY
        c = 1.0 + aa / c
        if abs(c) < _TINY:
            c = _TINY
        d = 1.0 / d
        h *= d * c
        # Odd step.
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < _TINY:
            d = _TINY
        c = 1.0 + aa / c
        if abs(c) < _TINY:
            c = _TINY
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < _EPSILON:
            break
    return h


def f_cdf(x: float, df1: int, df2: int) -> float:
    """F cumulative distribution."""
    _check_degrees_of_freedom(df1, "f_cdf")
    _check_degrees_of_freedom(df2, "f_cdf")
    if x <= 0.0:
        return 0.0
    if _scipy_stats is not None:
        return float(_scipy_stats.f.cdf(x, df1, df2))
    return _incomplete_beta(df1 / 2.0, df2 / 2.0, df1 * x / (df1 * x + df2))


def f_quantile(p: float, df1: int, df2: int) -> float:
    """F quantile. Used for confidence ellipses (``specs/06`` section 4.4)."""
    _check_probability(p, "f_quantile")
    _check_degrees_of_freedom(df1, "f_quantile")
    _check_degrees_of_freedom(df2, "f_quantile")
    if _scipy_stats is not None:
        return float(_scipy_stats.f.ppf(p, df1, df2))
    return _invert_cdf(lambda x: f_cdf(x, df1, df2), p, guess=1.0)


def t_cdf(x: float, degrees_of_freedom: int) -> float:
    """Student t cumulative distribution."""
    _check_degrees_of_freedom(degrees_of_freedom, "t_cdf")
    if _scipy_stats is not None:
        return float(_scipy_stats.t.cdf(x, degrees_of_freedom))
    half = _incomplete_beta(
        degrees_of_freedom / 2.0, 0.5, degrees_of_freedom / (degrees_of_freedom + x * x)
    ) / 2.0
    return 1.0 - half if x > 0.0 else half


def t_quantile(p: float, degrees_of_freedom: int) -> float:
    """Student t quantile.

    Data snooping uses the tau distribution when the variance factor is
    estimated rather than known; tau derives from t, and reporting which variant
    was applied is required by ``specs/06`` section 4.2.
    """
    _check_probability(p, "t_quantile")
    _check_degrees_of_freedom(degrees_of_freedom, "t_quantile")
    if _scipy_stats is not None:
        return float(_scipy_stats.t.ppf(p, degrees_of_freedom))
    return _invert_cdf(
        lambda x: t_cdf(x, degrees_of_freedom),
        p,
        guess=normal_quantile(p),
        lower=-1e6,
    )


# -- reliability ---------------------------------------------------------


def non_centrality(alpha: float = 0.001, beta: float = 0.20) -> float:
    """The non-centrality parameter delta_0 for the minimal detectable bias.

    ``specs/06`` section 4.3: MDB_i = delta_0 * sigma_i / sqrt(r_i), where
    delta_0 is the shift a one-dimensional test with two-sided significance
    *alpha* must experience to be rejected with power ``1 - beta``.

    For the one-dimensional case this is the classical

        delta_0 = z_{1 - alpha/2} + z_{1 - beta}

    which at the geodetic defaults alpha = 0.001, beta = 0.20 gives the familiar
    delta_0 = 4.13.

    Args:
        alpha: Two-sided significance (Type I error).
        beta: Type II error; the power is ``1 - beta``.
    """
    _check_probability(alpha, "non_centrality", exclusive=True)
    _check_probability(beta, "non_centrality", exclusive=True)
    return normal_quantile(1.0 - alpha / 2.0) + normal_quantile(1.0 - beta)


# -- shared helpers ------------------------------------------------------


def _check_probability(p: float, operation: str, *, exclusive: bool = False) -> None:
    if not math.isfinite(p) or p <= 0.0 or p >= 1.0:
        raise ValidationError(
            "probability_out_of_range",
            operation=operation,
            received=p,
            expected="a probability strictly between 0 and 1" if exclusive else "0 < p < 1",
        )


def _check_degrees_of_freedom(value: int, operation: str) -> None:
    if value < 1:
        raise ValidationError(
            "degrees_of_freedom_out_of_range",
            operation=operation,
            received=value,
            expected="at least 1; a network with no redundancy has no test to apply",
        )


def _invert_cdf(
    cdf,
    p: float,
    *,
    guess: float,
    lower: float = 0.0,
    upper: float | None = None,
) -> float:
    """Invert a monotone CDF by bracketing and bisection.

    Bisection rather than Newton: it needs no derivative, cannot diverge, and
    the cost is irrelevant here -- these are called once per adjustment, not
    once per observation.
    """
    if upper is None:
        upper = max(guess * 4.0, 1.0)
        while cdf(upper) < p and upper < 1e12:
            upper *= 2.0
    while lower > -1e12 and cdf(lower) > p:
        lower *= 2.0 if lower != 0.0 else 1.0

    for _ in range(200):
        middle = 0.5 * (lower + upper)
        if cdf(middle) < p:
            lower = middle
        else:
            upper = middle
        if upper - lower < 1e-12 * max(abs(upper), 1.0):
            break
    return 0.5 * (lower + upper)
