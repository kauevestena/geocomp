# SPDX-License-Identifier: GPL-2.0-or-later
"""Variance component estimation: how wrong each technique's weights were (FR-805).

``specs/13-module-integration.md`` section 4.

When observations of several techniques are adjusted together, the relative
weighting between them is an assumption -- each technique's stated precisions
are on their own scale, and nothing guarantees the scales agree. A global test
that fails says *that* the weights are wrong, never *whose*; the usual response
is to inflate everything until it passes, which is how a technique's real
information gets thrown away. This module says whose.

**The estimator is least-squares variance component estimation** (Teunissen and
Amiri-Simkooei, 2008), which under normally distributed errors is the same as
Helmert's and as BIQUE, and whose iterated form converges to REML. For groups
``k`` with a priori covariance blocks ``Q_k`` and ``M = P Q_vv P``::

    N_kl = 1/2 tr(M Q_k M Q_l)        l_k = 1/2 (P v)^T Q_k (P v)
    theta = N^-1 l                     D(theta) = N^-1

where ``theta_k`` multiplies group ``k``'s covariance. Rows that belong to no
group -- a weighted constraint, a geoid prior -- keep their covariance ``Q_0``
as stated, and their expected contribution is taken off the right-hand side,
``l_k -= 1/2 tr(M Q_k M Q_0)``: the same estimator with a known part. It is exact for
correlated observations -- a GNSS baseline's 3x3, a direction set -- which the
simpler ``v^T P v / r`` per group is not, and it states the components' own
covariance rather than leaving the reader to guess how far to trust them. The
components are iterated: each group's covariance is rescaled by its estimate and
the network adjusted again, until every estimate is one; the factors reported
are the products.

**A factor is information about the survey, not a knob** (``specs/13`` section
4): a factor of 4 on a technique's variances says its stated precisions were
optimistic by a factor of 2. The result says it in those words.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass, replace

import numpy as np

from geocomp.core.adjustment.least_squares import AdjustmentOptions, AdjustmentRun, adjust
from geocomp.core.adjustment.normal_equations import CONSTRAINT_ROW_PREFIX
from geocomp.core.errors import ComputationError, ValidationError
from geocomp.core.models import Cluster, Network, Observation
from geocomp.core.uncertainty import Covariance, Quantity

__all__ = [
    "VarianceComponent",
    "VarianceComponents",
    "estimate_variance_components",
    "scale_groups",
]

#: The smallest redundancy a group may carry and still be estimated. Below one
#: the group's residuals hardly depend on its own weights, and an estimate from
#: them is noise with a confident-looking number attached.
MINIMUM_GROUP_REDUNDANCY = 1.0


@dataclass(frozen=True)
class VarianceComponent:
    """One group's estimated variance factor.

    Attributes:
        group: The technique, or whatever the grouping named it.
        factor: Multiplies the group's a priori variances. One means its stated
            precisions were right.
        std_dev: The factor's own standard deviation, from ``D(theta)``.
        redundancy: How much of the network's redundancy the group carries --
            the sum of its observations' redundancy numbers.
        observations: How many observation rows the group holds.
    """

    group: str
    factor: float
    std_dev: float
    redundancy: float
    observations: int

    @property
    def sigma_scale(self) -> float:
        """What the group's standard deviations should have been multiplied by."""
        return math.sqrt(self.factor)

    def is_consistent_with_one(self, z: float = 1.96) -> bool:
        """Whether the stated precisions are compatible with the data."""
        return abs(self.factor - 1.0) <= z * self.std_dev


@dataclass(frozen=True)
class VarianceComponents:
    """The estimated factors, and the adjustment run with them applied.

    Attributes:
        components: One per group, in the order the groups were first met.
        covariance: ``D(theta)`` over the factors, in that order.
        run: The final adjustment, with every group's covariance rescaled.
        network: The rescaled network that run adjusted.
        iterations: How many adjustments it took.
    """

    components: tuple[VarianceComponent, ...]
    covariance: np.ndarray
    run: AdjustmentRun
    network: Network
    iterations: int

    def factor(self, group: str) -> VarianceComponent:
        for component in self.components:
            if component.group == group:
                return component
        raise ValidationError(
            "variance_component_group_unknown",
            received=group,
            expected=[c.group for c in self.components],
        )


def estimate_variance_components(
    network: Network,
    options: AdjustmentOptions | None = None,
    *,
    group_of: Callable[[Observation], str] | None = None,
    max_iterations: int = 30,
    tolerance: float = 1.0e-4,
    approximate: dict[str, dict[str, float]] | None = None,
) -> VarianceComponents:
    """Estimate one variance factor per group, iterating to convergence.

    Args:
        group_of: Assigns each observation its group. ``None`` means its technique
            (:func:`~geocomp.core.techniques.integration.techniques.technique_of`);
            grouping by observation type is the other common choice.
        tolerance: Stop when every factor of an iteration is within this of one.

    Raises:
        ValidationError: a cluster whose members fall in different groups -- its
            covariance cannot be rescaled by two factors at once.
        ComputationError: a group with too little redundancy to estimate, a
            negative estimate, or no convergence. Each names the group.
    """
    options = options or AdjustmentOptions()
    group_of = group_of or _by_technique()
    groups = _groups(network, group_of)
    factors = dict.fromkeys(groups, 1.0)
    scaled = network
    iterations = 0
    for iterations in range(1, max_iterations + 1):  # noqa: B007 - reported below
        run = adjust(scaled, options, approximate=approximate)
        estimate, covariance, redundancy, counts = _estimate(run, scaled, groups, group_of)
        for group, value in estimate.items():
            if not value > 0.0:
                raise ComputationError(
                    "variance_component_negative",
                    group=group,
                    received=value,
                    expected=(
                        "a positive variance factor. A negative one means the group's "
                        "residuals are smaller than its model allows for any positive "
                        "scale -- too little redundancy, or a stochastic model that is "
                        "wrong in shape rather than in scale"
                    ),
                )
            factors[group] *= value
        if all(abs(value - 1.0) <= tolerance for value in estimate.values()):
            break
        scaled = scale_groups(network, {g: factors[g] for g in groups}, group_of)
    else:
        raise ComputationError(
            "variance_components_not_converged",
            iterations=max_iterations,
            received={g: factors[g] for g in groups},
            expected="factors that settle; a group with little redundancy can oscillate",
        )

    # At convergence every estimate is one, so D(theta) of the rescaled problem
    # is the covariance of the multipliers on it; carried back to the original
    # scale it multiplies by the factors on both sides.
    scale = np.array([factors[g] for g in groups])
    covariance = covariance * np.outer(scale, scale)
    components = tuple(
        VarianceComponent(
            group=group,
            factor=factors[group],
            std_dev=float(math.sqrt(max(covariance[i, i], 0.0))),
            redundancy=redundancy[group],
            observations=counts[group],
        )
        for i, group in enumerate(groups)
    )
    return VarianceComponents(
        components=components,
        covariance=covariance,
        run=run,
        network=scaled,
        iterations=iterations,
    )


def scale_groups(
    network: Network,
    factors: dict[str, float],
    group_of: Callable[[Observation], str] | None = None,
) -> Network:
    """A copy of *network* with each group's variances multiplied by its factor.

    What the estimator iterates on, and what a user applies once the factors are
    known: the observations keep their values, and every variance -- on the
    observation and in its cluster -- is scaled, so correlations are unchanged.
    """
    group_of = group_of or _by_technique()
    observations = {}
    for identifier, observation in network.observations.items():
        factor = factors.get(group_of(observation), 1.0)
        observations[identifier] = (
            observation
            if factor == 1.0
            else replace(observation, values=tuple(_scaled(v, factor) for v in observation.values))
        )
    clusters = {}
    for identifier, cluster in network.clusters.items():
        members = [network.observations[o] for o in cluster.observation_ids if o in network.observations]
        factor = factors.get(group_of(members[0]), 1.0) if members else 1.0
        clusters[identifier] = cluster if factor == 1.0 else _scaled_cluster(cluster, factor)
    return replace(network, observations=observations, clusters=clusters)


# -- internals ---------------------------------------------------------------


def _by_technique() -> Callable[[Observation], str]:
    """The default grouping, imported when used: the integration package
    imports this module, so importing it back at load time is a cycle."""
    from geocomp.core.techniques.integration.techniques import technique_of

    return technique_of


def _groups(network: Network, group_of) -> list[str]:
    groups: list[str] = []
    for observation in network.active_observations:
        group = group_of(observation)
        if group not in groups:
            groups.append(group)
    for cluster in network.clusters.values():
        members = {
            group_of(network.observations[o])
            for o in cluster.observation_ids
            if o in network.observations
        }
        if len(members) > 1:
            raise ValidationError(
                "variance_component_cluster_split",
                cluster=cluster.id,
                received=sorted(members),
                expected=(
                    "every member of a correlated cluster in one group; a covariance "
                    "cannot be rescaled by two factors at once"
                ),
            )
    return groups


def _estimate(run: AdjustmentRun, network: Network, groups: list[str], group_of):
    weight = run.system.weight
    covariance = np.linalg.inv(weight)
    # Only the covariance within a group belongs to it; P is block-diagonal by
    # cluster and no cluster straddles two groups, so this loses nothing. A
    # constraint row is no observation's and no group's: it is the known part.
    row_group = [
        None
        if observation_id.startswith(CONSTRAINT_ROW_PREFIX)
        else group_of(network.observations[observation_id])
        for observation_id, _ in run.system.row_labels
    ]
    index = {group: [i for i, g in enumerate(row_group) if g == group] for group in groups}
    blocks = {}
    for group, rows in index.items():
        block = np.zeros_like(covariance)
        block[np.ix_(rows, rows)] = covariance[np.ix_(rows, rows)]
        blocks[group] = block
    known_rows = [i for i, g in enumerate(row_group) if g is None]
    known = np.zeros_like(covariance)
    known[np.ix_(known_rows, known_rows)] = covariance[np.ix_(known_rows, known_rows)]

    m = weight @ run.cofactor_residuals @ weight
    pv = weight @ run.residuals
    size = len(groups)
    normal = np.zeros((size, size))
    right = np.zeros(size)
    for k, first in enumerate(groups):
        mq = m @ blocks[first]
        right[k] = 0.5 * float(pv @ blocks[first] @ pv)
        if known_rows:
            right[k] -= 0.5 * float(np.trace(mq @ m @ known))
        for j, second in enumerate(groups[k:], start=k):
            normal[k, j] = normal[j, k] = 0.5 * float(np.trace(mq @ m @ blocks[second]))

    redundancy_numbers = np.diag(run.cofactor_residuals @ weight)
    redundancy = {group: float(sum(redundancy_numbers[i] for i in rows)) for group, rows in index.items()}
    for group, value in redundancy.items():
        if value < MINIMUM_GROUP_REDUNDANCY:
            raise ComputationError(
                "variance_component_unestimable",
                group=group,
                received=round(value, 3),
                expected=(
                    f"a redundancy of at least {MINIMUM_GROUP_REDUNDANCY:g} in the group; "
                    "with less, its residuals barely depend on its own weights and a "
                    "factor estimated from them would be noise. Fix its weights "
                    "instead, or merge it with another group"
                ),
            )
    try:
        inverse = np.linalg.inv(normal)
    except np.linalg.LinAlgError as error:
        raise ComputationError(
            "variance_components_singular",
            received=groups,
            expected="groups the residuals can tell apart",
        ) from error
    estimate = inverse @ right
    counts = {group: len(rows) for group, rows in index.items()}
    return dict(zip(groups, (float(v) for v in estimate), strict=True)), inverse, redundancy, counts


def _scaled(quantity: Quantity, factor: float) -> Quantity:
    return Quantity(
        value=quantity.value,
        variance=quantity.variance * factor,
        unit=quantity.unit,
        mode=quantity.mode,
        strategies=quantity.strategies,
    )


def _scaled_cluster(cluster: Cluster, factor: float) -> Cluster:
    covariance = cluster.covariance
    return replace(
        cluster,
        covariance=Covariance(
            matrix=np.asarray(covariance.matrix) * factor,
            labels=covariance.labels,
            units=covariance.units,
            mode=covariance.mode,
            strategies=covariance.strategies,
        ),
    )
