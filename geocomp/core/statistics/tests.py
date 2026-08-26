# SPDX-License-Identifier: GPL-2.0-or-later
"""The global test and data snooping.

``specs/06-adjustment-core.md`` sections 4.1 and 4.2.

Two rules run through this module, both aimed at preventing confident misuse
rather than at the arithmetic, which is straightforward:

* **Every statistic is reported with its critical value, its confidence level
  and its decision.** A bare pass or fail teaches a student nothing and gives a
  professional nothing to defend.
* **Rejection is never automatic and never silent** (FR-255). This module
  returns *candidates*; the caller decides. In a monitoring network the
  displacement being measured is exactly what an automatic outlier remover
  would delete.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from geocomp.core.models import TestResult
from geocomp.core.statistics.distributions import chi2_quantile, normal_quantile, t_quantile

__all__ = [
    "GLOBAL_TEST_CAUSES",
    "OutlierCandidate",
    "SnoopingReport",
    "data_snooping",
    "global_test",
]

#: What a failed global test can mean. Reported alongside the decision because
#: students and practitioners routinely assume the first and stop there
#: (``specs/06`` section 4.1).
GLOBAL_TEST_CAUSES = (
    "one or more blunders in the observations",
    "an incorrect stochastic model: the a priori precisions are wrong",
    "an incorrect functional model: the observation equations do not describe "
    "what was measured",
)


def global_test(
    variance_factor_aposteriori: float,
    degrees_of_freedom: int,
    *,
    variance_factor_apriori: float = 1.0,
    confidence: float = 0.95,
) -> TestResult:
    """The chi-square test on the variance factor (FR-250).

    **Two-sided by design.** An unexpectedly *small* variance factor means the a
    priori precisions were pessimistic -- the survey was better than claimed, or
    the weights were too generous -- and that is information, not a pass. A
    one-sided test throws it away.

    The statistic is ``dof * sigma_hat^2 / sigma_0^2``, compared against the
    chi-square quantiles at ``(1 - confidence) / 2`` and
    ``1 - (1 - confidence) / 2``.
    """
    if degrees_of_freedom < 1:
        return TestResult(
            name="global",
            statistic=float("nan"),
            confidence=confidence,
            passed=True,
            note=(
                "no redundancy: with zero degrees of freedom the observations fit "
                "exactly by construction and there is nothing to test"
            ),
        )

    statistic = degrees_of_freedom * variance_factor_aposteriori / variance_factor_apriori
    alpha = 1.0 - confidence
    lower = chi2_quantile(alpha / 2.0, degrees_of_freedom)
    upper = chi2_quantile(1.0 - alpha / 2.0, degrees_of_freedom)
    passed = lower <= statistic <= upper

    if passed:
        note = ""
    elif statistic > upper:
        note = "variance factor too large. Possible causes: " + "; ".join(GLOBAL_TEST_CAUSES)
    else:
        note = (
            "variance factor too small: the a priori precisions appear pessimistic, "
            "so the observations agree better than the stochastic model claimed. "
            "This is not a failure of the survey, but the reported uncertainties "
            "are likely too large"
        )

    return TestResult(
        name="global",
        statistic=statistic,
        critical_low=lower,
        critical_high=upper,
        confidence=confidence,
        passed=passed,
        note=note,
    )


@dataclass(frozen=True)
class OutlierCandidate:
    """One observation whose standardised residual exceeds the critical value.

    A *candidate*, deliberately: the caller decides, and the decision is
    recorded and reversible (FR-255).
    """

    row: int
    observation_id: str
    component: str
    residual: float
    residual_std_dev: float
    statistic: float
    critical_value: float
    redundancy: float

    @property
    def is_uncheckable(self) -> bool:
        return self.redundancy < 0.01

    def to_test_result(self, confidence: float, distribution: str) -> TestResult:
        return TestResult(
            name=f"w-test ({distribution})",
            statistic=self.statistic,
            critical_high=self.critical_value,
            confidence=confidence,
            passed=self.statistic <= self.critical_value,
        )


@dataclass(frozen=True)
class SnoopingReport:
    """The outcome of data snooping over a whole adjustment.

    Attributes:
        candidates: Every row exceeding the critical value, worst first.
        uncheckable: Rows whose redundancy is so low that no blunder in them
            could be detected. **Reported prominently**: a network full of these
            can pass every test and still be wrong (``specs/06`` section 4.2).
        distribution: ``"normal"`` when sigma_0 is known, ``"tau"`` when it was
            estimated from the adjustment. Which was used must be stated.
        multiple_exceedances: True when more than one row exceeds the critical
            value, in which case the single-outlier assumption behind the test
            does not hold and the candidates cannot be read as a ranking.
    """

    candidates: tuple[OutlierCandidate, ...]
    uncheckable: tuple[OutlierCandidate, ...]
    statistics: dict[int, float]
    critical_value: float
    confidence: float
    distribution: str

    @property
    def multiple_exceedances(self) -> bool:
        return len(self.candidates) > 1

    @property
    def worst(self) -> OutlierCandidate | None:
        return self.candidates[0] if self.candidates else None

    def note(self) -> str:
        if not self.candidates:
            return ""
        if self.multiple_exceedances:
            return (
                f"{len(self.candidates)} observations exceed the critical value. "
                "Data snooping locates one outlier at a time, and multiple "
                "simultaneous blunders can mask each other, so this list is not a "
                "ranking: investigate the largest, decide, re-adjust, and test again"
            )
        return "one observation exceeds the critical value"


def data_snooping(
    residuals: np.ndarray,
    cofactor_residuals: np.ndarray,
    weight: np.ndarray,
    row_labels: list[tuple[str, str]],
    *,
    variance_factor: float = 1.0,
    degrees_of_freedom: int = 0,
    confidence: float = 0.95,
    sigma_known: bool = False,
) -> SnoopingReport:
    """Baarda's w-test on the standardised residuals (FR-251).

        w_i = |v_i| / sigma_{v_i},   sigma_{v_i} = sigma_0 * sqrt(q_{v_i})

    Args:
        residuals: **v**.
        cofactor_residuals: **Q**vv, whose diagonal gives ``q_{v_i}``.
        weight: **P**, for the redundancy numbers ``r_i = (Qvv P)_ii``.
        row_labels: Observation id and component per row.
        variance_factor: The a posteriori sigma_0^2, used when it was estimated.
        sigma_known: Whether sigma_0 is known a priori. When it is not, the tau
            distribution replaces the normal, and the report says so -- required
            by ``specs/06`` section 4.2.

    Returns:
        A :class:`SnoopingReport`. Nothing is rejected here.
    """
    sigma_zero = 1.0 if sigma_known else float(np.sqrt(max(variance_factor, 0.0)))
    redundancy = np.diag(cofactor_residuals @ weight)
    diagonal = np.diag(cofactor_residuals)

    if sigma_known or degrees_of_freedom < 1:
        critical = normal_quantile(1.0 - (1.0 - confidence) / 2.0)
        distribution = "normal"
    else:
        critical = _tau_critical(confidence, degrees_of_freedom)
        distribution = "tau"

    candidates: list[OutlierCandidate] = []
    uncheckable: list[OutlierCandidate] = []
    statistics: dict[int, float] = {}

    for row, (observation_id, component) in enumerate(row_labels):
        q = float(diagonal[row])
        r = float(redundancy[row])
        std_dev = sigma_zero * np.sqrt(max(q, 0.0))
        statistic = abs(float(residuals[row])) / std_dev if std_dev > 0.0 else 0.0
        statistics[row] = statistic

        entry = OutlierCandidate(
            row=row,
            observation_id=observation_id,
            component=component,
            residual=float(residuals[row]),
            residual_std_dev=float(std_dev),
            statistic=statistic,
            critical_value=critical,
            redundancy=r,
        )
        if entry.is_uncheckable:
            uncheckable.append(entry)
        elif statistic > critical:
            candidates.append(entry)

    candidates.sort(key=lambda item: -item.statistic)
    return SnoopingReport(
        candidates=tuple(candidates),
        uncheckable=tuple(uncheckable),
        statistics=statistics,
        critical_value=critical,
        confidence=confidence,
        distribution=distribution,
    )


def _tau_critical(confidence: float, degrees_of_freedom: int) -> float:
    """Critical value of the tau distribution.

    Tau relates to Student t on ``dof - 1`` degrees of freedom by

        tau = t * sqrt(dof) / sqrt(dof - 1 + t^2)

    It is the correct distribution when sigma_0 is estimated from the same
    adjustment that produced the residuals, because the statistic and its
    denominator are then not independent -- which the normal distribution
    assumes.
    """
    if degrees_of_freedom <= 1:
        # With one degree of freedom tau degenerates; fall back to the normal,
        # which is conservative here, and the report names the distribution used.
        return normal_quantile(1.0 - (1.0 - confidence) / 2.0)
    t_value = t_quantile(1.0 - (1.0 - confidence) / 2.0, degrees_of_freedom - 1)
    return t_value * np.sqrt(degrees_of_freedom) / np.sqrt(
        degrees_of_freedom - 1 + t_value * t_value
    )
