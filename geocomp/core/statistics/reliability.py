# SPDX-License-Identifier: GPL-2.0-or-later
"""Internal and external reliability.

``specs/06-adjustment-core.md`` section 4.3, from Baarda's theory.

Two questions, and the second is the one that decides whether the first
matters:

* **Internal reliability** -- *how large a blunder could be hiding in this
  observation without me noticing?* The minimal detectable bias,
  ``MDB_i = delta_0 * sigma_i / sqrt(r_i)``.
* **External reliability** -- *and would it matter?* The effect on the adjusted
  coordinates of an undetected blunder at exactly the MDB.

An observation with a large MDB but negligible external effect is not a
problem. One with a modest MDB and a large external effect is. Reporting only
the first, as many packages do, gives the user the less useful half.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from geocomp.core.statistics.distributions import non_centrality

__all__ = [
    "DEFAULT_ALPHA",
    "DEFAULT_BETA",
    "ReliabilityReport",
    "ReliabilityResult",
    "reliability",
]

#: The geodetic defaults (``specs/06`` section 4.3): significance 0.001 and
#: power 0.80, giving the familiar delta_0 = 4.13.
DEFAULT_ALPHA = 0.001
DEFAULT_BETA = 0.20

#: Below this redundancy an observation is treated as uncheckable. Not a
#: threshold to tune: at r = 0 the MDB is infinite, and anything near it means
#: the network simply cannot see a blunder in that observation.
UNCHECKABLE_REDUNDANCY = 0.01


@dataclass(frozen=True)
class ReliabilityResult:
    """Reliability of one observation."""

    row: int
    observation_id: str
    component: str
    redundancy: float
    std_dev: float
    minimal_detectable_bias: float | None
    external_effect: float | None

    @property
    def is_uncheckable(self) -> bool:
        return self.redundancy < UNCHECKABLE_REDUNDANCY


@dataclass(frozen=True)
class ReliabilityReport:
    """Reliability across a whole adjustment."""

    results: tuple[ReliabilityResult, ...]
    non_centrality: float
    alpha: float
    beta: float

    @property
    def uncheckable(self) -> tuple[ReliabilityResult, ...]:
        return tuple(result for result in self.results if result.is_uncheckable)

    def by_observation(self) -> dict[str, ReliabilityResult]:
        return {result.observation_id: result for result in self.results}

    def note(self) -> str:
        count = len(self.uncheckable)
        if not count:
            return ""
        return (
            f"{count} observation(s) have effectively no redundancy and are "
            "uncheckable: no blunder in them is detectable at all. A network can "
            "pass every statistical test while containing them, so treat the "
            "passing tests as saying nothing about those observations"
        )


def reliability(
    cofactor_residuals: np.ndarray,
    weight: np.ndarray,
    design: np.ndarray,
    cofactor_parameters: np.ndarray,
    row_labels: list[tuple[str, str]],
    *,
    alpha: float = DEFAULT_ALPHA,
    beta: float = DEFAULT_BETA,
) -> ReliabilityReport:
    """Compute internal and external reliability per observation.

    Args:
        cofactor_residuals: **Q**vv.
        weight: **P**.
        design: **A**, for the external effect.
        cofactor_parameters: **Q**xx, likewise.
        row_labels: Observation id and component per row.
        alpha: Two-sided significance of the test the MDB is defined against.
        beta: Type II error; power is ``1 - beta``.

    The external effect is the norm of the coordinate shift a blunder of one
    MDB would produce:

        dx_i = Qxx A^T P e_i * MDB_i
    """
    delta_zero = non_centrality(alpha, beta)
    redundancy = np.diag(cofactor_residuals @ weight)
    variances = np.diag(np.linalg.inv(weight))

    influence = cofactor_parameters @ design.T @ weight

    results: list[ReliabilityResult] = []
    for row, (observation_id, component) in enumerate(row_labels):
        r = float(redundancy[row])
        sigma = float(np.sqrt(max(variances[row], 0.0)))

        if r < UNCHECKABLE_REDUNDANCY:
            # The MDB is infinite in the limit; reporting None is honest, where
            # a very large number would invite comparison with the finite ones.
            mdb = None
            external = None
        else:
            mdb = delta_zero * sigma / np.sqrt(r)
            external = float(np.linalg.norm(influence[:, row] * mdb))

        results.append(
            ReliabilityResult(
                row=row,
                observation_id=observation_id,
                component=component,
                redundancy=r,
                std_dev=sigma,
                minimal_detectable_bias=mdb,
                external_effect=external,
            )
        )

    return ReliabilityReport(
        results=tuple(results), non_centrality=delta_zero, alpha=alpha, beta=beta
    )
