# SPDX-License-Identifier: GPL-2.0-or-later
"""A combined adjustment, reported per technique (``specs/13`` section 6, criterion 7).

"The adjustment passed" is much less use than "the adjustment passed, and the
levelling is carrying almost none of the redundancy". This splits an
adjustment's residuals, redundancy and weighted squares by the technique each
row came from, so each technique's contribution -- and its own apparent variance
factor -- is visible rather than averaged away.

The split is exact, not an approximation: the weight matrix is block-diagonal
by cluster and no cluster straddles two techniques, so each technique's share of
``v^T P v`` is ``v_k^T P_kk v_k`` and the shares sum to the whole; redundancy
numbers are per row and sum to the degrees of freedom. Rows that are no
technique's -- a weighted benchmark, a geoid prior -- are reported as their own
groups, ``constraints`` and ``geoid``, because they carry redundancy too and a
breakdown that dropped them would not add up.

A technique's ``v^T P v / r`` is **not** its variance component. It is the
quick reading; :mod:`~geocomp.core.adjustment.variance_components` estimates
the components properly, accounting for how each group's residuals depend on
the others' weights.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from geocomp.core.adjustment.blocks import quadratic_form
from geocomp.core.adjustment.least_squares import AdjustmentRun
from geocomp.core.adjustment.normal_equations import CONSTRAINT_ROW_PREFIX
from geocomp.core.adjustment.undulations import GEOID_OWNER_PREFIX
from geocomp.core.models import Network
from geocomp.core.statistics.reliability import UNCHECKABLE_REDUNDANCY
from geocomp.core.techniques.integration.techniques import technique_of

__all__ = ["CONSTRAINTS", "GEOID", "TechniqueSummary", "technique_breakdown"]

#: The group of a weighted constraint's rows.
CONSTRAINTS = "constraints"
#: The group of the geoid priors' rows.
GEOID = "geoid"


@dataclass(frozen=True)
class TechniqueSummary:
    """One technique's part in a combined adjustment.

    Attributes:
        rows: Design-matrix rows -- a baseline is three.
        observations: Distinct observations behind them.
        redundancy: The sum of the rows' redundancy numbers: how much of the
            network's checking this technique carries.
        redundancy_share: That as a fraction of the degrees of freedom.
        weighted_squares: Its part of ``v^T P v``.
        variance_factor: ``weighted_squares / redundancy``, or ``None`` below a
            redundancy of one, where it would be noise.
        largest_standardised: The largest ``|w|`` among its rows.
        uncheckable: Observations with a row whose redundancy number is below
            :data:`~geocomp.core.statistics.reliability.UNCHECKABLE_REDUNDANCY`
            -- no blunder in them could be detected at all.
    """

    technique: str
    rows: int
    observations: int
    redundancy: float
    redundancy_share: float
    weighted_squares: float
    variance_factor: float | None
    largest_standardised: float | None
    uncheckable: tuple[str, ...]


def _group(label: str, network: Network) -> str:
    if label.startswith(f"{CONSTRAINT_ROW_PREFIX}{GEOID_OWNER_PREFIX}"):
        return GEOID
    if label.startswith(CONSTRAINT_ROW_PREFIX):
        return CONSTRAINTS
    return technique_of(network.observations[label])


def technique_breakdown(run: AdjustmentRun, network: Network) -> tuple[TechniqueSummary, ...]:
    """Every technique's summary, in the order its rows first appear."""
    labels = run.system.row_labels
    groups = [_group(label, network) for label, _ in labels]
    order = list(dict.fromkeys(groups))
    weight = run.system.weight
    residuals = run.residuals
    sigma0_squared = run.variance_factor_apriori
    dof = run.degrees_of_freedom

    summaries: list[TechniqueSummary] = []
    for group in order:
        rows = [i for i, g in enumerate(groups) if g == group]
        squares = quadratic_form(weight, residuals, rows)
        redundancy = float(sum(run.redundancy[i] for i in rows))
        standardised = [
            abs(residuals[i]) / math.sqrt(sigma0_squared * run.cofactor_residuals[i, i])
            for i in rows
            if run.redundancy[i] >= UNCHECKABLE_REDUNDANCY and run.cofactor_residuals[i, i] > 0
        ]
        uncheckable = tuple(
            dict.fromkeys(labels[i][0] for i in rows if run.redundancy[i] < UNCHECKABLE_REDUNDANCY)
        )
        summaries.append(
            TechniqueSummary(
                technique=group,
                rows=len(rows),
                observations=len({labels[i][0] for i in rows}),
                redundancy=redundancy,
                redundancy_share=redundancy / dof if dof > 0 else float("nan"),
                weighted_squares=squares,
                variance_factor=squares / redundancy if redundancy >= 1.0 else None,
                largest_standardised=max(standardised) if standardised else None,
                uncheckable=uncheckable,
            )
        )
    return tuple(summaries)
