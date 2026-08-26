# SPDX-License-Identifier: GPL-2.0-or-later
"""Assembling and solving the normal equations.

``specs/06-adjustment-core.md`` sections 2.1 and 2.4.

    N = A^T P A,   u = A^T P l,   x = N^-1 u

**The full weight matrix is used, not its diagonal** (FR-221). A GNSS baseline
contributes a 3x3 block from its cluster covariance; a direction set contributes
its own block. This is a requirement rather than an optimisation: treating a
baseline's three components as independent misstates every statistic that
follows from the adjustment.

The part of this module that earns its keep is :func:`diagnose_rank`. A
rank-deficient network is the normal outcome of a free network, a forgotten
constraint, or a station connected by observations that do not determine it --
and returning a numerically meaningless answer, or a bare "singular matrix",
leaves the user no way forward. Instead the null space is mapped back to the
stations and components it involves, so the message names them (FR-226).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from geocomp.core.adjustment.equations import evaluate
from geocomp.core.adjustment.parameters import ParameterLayout
from geocomp.core.errors import ComputationError, DataError
from geocomp.core.models import Cluster, Observation
from geocomp.core.units import Unit, wrap_to_pi

__all__ = [
    "LinearisedSystem",
    "NullSpaceFinding",
    "SolveResult",
    "assemble",
    "build_weight_matrix",
    "diagnose_rank",
    "solve",
]

#: Below this ratio to the largest, an eigenvalue of the normal matrix counts as
#: zero. Deliberately generous: a datum defect produces eigenvalues around 1e-16
#: relative, while a merely weak network produces 1e-8, and calling the latter
#: singular would refuse to adjust networks that are poor but solvable.
RANK_TOLERANCE = 1e-12


@dataclass
class LinearisedSystem:
    """The linearised system at the current approximate parameters.

    Attributes:
        design: **A**, shape ``(m, n)``.
        misclosure: **l** = observed - computed, shape ``(m,)``.
        weight: **P**, shape ``(m, m)``.
        row_labels: Which observation and component each row came from, so a
            residual can be reported against the observation a user recognises.
    """

    design: np.ndarray
    misclosure: np.ndarray
    weight: np.ndarray
    row_labels: list[tuple[str, str]] = field(default_factory=list)

    @property
    def observation_count(self) -> int:
        return self.design.shape[0]

    @property
    def parameter_count(self) -> int:
        return self.design.shape[1]

    def normal_matrix(self) -> np.ndarray:
        return self.design.T @ self.weight @ self.design

    def normal_vector(self) -> np.ndarray:
        return self.design.T @ self.weight @ self.misclosure


def build_weight_matrix(
    observations: list[Observation],
    clusters: dict[str, Cluster],
    row_labels: list[tuple[str, str]],
) -> np.ndarray:
    """Build **P** = Sigma^-1, block by block.

    Uncorrelated observations contribute 1/sigma^2 on the diagonal. A cluster
    contributes the inverse of its covariance block over exactly its member
    rows, in the cluster's own ordering -- which is why
    :class:`~geocomp.core.models.observation.Cluster` stores that ordering
    explicitly.
    """
    size = len(row_labels)
    weight = np.zeros((size, size))
    row_of = {label: index for index, label in enumerate(row_labels)}
    by_id = {observation.id: observation for observation in observations}
    handled: set[int] = set()

    for cluster in clusters.values():
        members = [oid for oid in cluster.observation_ids if oid in by_id]
        if not members:
            continue

        rows: list[int] = []
        for observation_id in cluster.observation_ids:
            observation = by_id.get(observation_id)
            if observation is None:
                continue
            components = observation.spec.components
            for component in components:
                key = (observation_id, component if len(components) > 1 else "")
                if key in row_of:
                    rows.append(row_of[key])

        if len(rows) != cluster.covariance.size:
            raise DataError(
                "cluster_rows_mismatch",
                cluster=cluster.id,
                rows=len(rows),
                covariance=cluster.covariance.size,
                expected="one active row per covariance component",
            )

        block = np.linalg.inv(cluster.covariance.matrix)
        index = np.array(rows)
        weight[np.ix_(index, index)] = block
        handled.update(rows)

    for observation in observations:
        components = observation.spec.components
        for position, component in enumerate(components):
            key = (observation.id, component if len(components) > 1 else "")
            row = row_of.get(key)
            if row is None or row in handled:
                continue
            variance = observation.values[position].variance
            if variance <= 0.0:
                raise DataError(
                    "observation_without_uncertainty",
                    observation=observation.id,
                    expected=(
                        "a positive variance; GeoComp does not invent a weight, "
                        "because a fabricated one silently corrupts every statistic"
                    ),
                )
            weight[row, row] = 1.0 / variance

    return weight


def _misclosure(observed: float, computed: float, unit: Unit) -> float:
    """``l = observed - computed``, taken the short way round for an angle.

    An angular observation and its computed value can straddle the zero of the
    circle -- a direction read as 353 degrees against a computed -7 -- and the
    plain difference is then 360 degrees where the true discrepancy is nothing.
    That enters the normal equations as an enormous residual and the adjustment
    diverges, reporting a convergence failure that says nothing about the cause.

    Found in phase P3, when total-station direction sets first exercised the
    direction equation with a real circle orientation. Phase P2's networks
    happened to have every angular observation near its computed value, so the
    wrap never arose.
    """
    difference = observed - computed
    return wrap_to_pi(difference) if unit is Unit.RADIAN else difference


def assemble(
    observations: list[Observation],
    clusters: dict[str, Cluster],
    layout: ParameterLayout,
    x: np.ndarray,
) -> LinearisedSystem:
    """Linearise every observation at the current parameters *x*."""
    rows: list[np.ndarray] = []
    misclosure: list[float] = []
    labels: list[tuple[str, str]] = []

    for observation in observations:
        equations = evaluate(observation, layout, x)
        components = observation.spec.components
        units = observation.spec.units
        for position, equation in enumerate(equations):
            rows.append(equation.to_dense(layout.size))
            misclosure.append(
                _misclosure(
                    observation.values[position].value, equation.computed, units[position]
                )
            )
            labels.append((observation.id, equation.component if len(components) > 1 else ""))

    if not rows:
        raise ComputationError(
            "no_observations",
            expected="at least one active observation to adjust",
        )

    return LinearisedSystem(
        design=np.vstack(rows),
        misclosure=np.array(misclosure),
        weight=build_weight_matrix(observations, clusters, labels),
        row_labels=labels,
    )


@dataclass(frozen=True)
class NullSpaceFinding:
    """One undetermined direction in the parameter space.

    Attributes:
        parameters: The unknowns involved, with their weight in the direction,
            largest first. This is what turns "singular matrix" into a sentence
            a surveyor can act on.
        magnitude: The eigenvalue, relative to the largest.
    """

    parameters: list[tuple[str, float]]
    magnitude: float

    def describe(self) -> str:
        involved = ", ".join(f"{label} ({weight:+.2f})" for label, weight in self.parameters[:6])
        more = "" if len(self.parameters) <= 6 else f", and {len(self.parameters) - 6} more"
        return f"undetermined combination of {involved}{more}"


def diagnose_rank(
    normal: np.ndarray, layout: ParameterLayout, *, tolerance: float = RANK_TOLERANCE
) -> list[NullSpaceFinding]:
    """Find the undetermined directions of a singular normal matrix (FR-226).

    Returns an empty list when the system has full rank. Otherwise each finding
    names the unknowns that participate in one undetermined direction, ordered
    by how strongly.

    A pure datum defect shows up here as translations and rotations: in a 2D
    network with no constraints, the two translation directions appear as every
    easting moving together and every northing moving together.
    """
    if normal.size == 0:
        return []

    eigenvalues, eigenvectors = np.linalg.eigh(normal)
    largest = float(np.max(np.abs(eigenvalues)))
    if largest == 0.0:
        return [
            NullSpaceFinding([(label, 1.0) for label in layout.labels()], 0.0)
        ]

    findings: list[NullSpaceFinding] = []
    labels = layout.labels()
    for index, eigenvalue in enumerate(eigenvalues):
        if abs(eigenvalue) / largest > tolerance:
            continue
        vector = eigenvectors[:, index]
        contributions = [
            (labels[position], float(vector[position]))
            for position in np.argsort(-np.abs(vector))
            if abs(float(vector[position])) > 1e-8
        ]
        findings.append(NullSpaceFinding(contributions, float(eigenvalue) / largest))

    return findings


@dataclass
class SolveResult:
    """The solution of one normal system.

    Attributes:
        x: Parameter corrections.
        cofactor: **Q**xx = N^-1, the cofactor matrix of the parameters.
        condition_number: Of the normal matrix; reported so an ill-conditioned
            but solvable system is visible rather than merely survivable.
        rank_deficiency: Zero for a full-rank system.
        method: Which factorisation actually ran.
    """

    x: np.ndarray
    cofactor: np.ndarray
    condition_number: float
    rank_deficiency: int = 0
    method: str = "cholesky"


def solve(
    system: LinearisedSystem,
    layout: ParameterLayout,
    *,
    constraints: np.ndarray | None = None,
) -> SolveResult:
    """Solve the normal equations, with optional datum constraints.

    Args:
        system: The linearised system.
        layout: For naming unknowns in a rank diagnosis.
        constraints: The **G** matrix of an inner- or minimum-constraint
            solution, shape ``(n, d)``. When given, the bordered system

            ``[[N, G], [G^T, 0]] [x; k] = [u; 0]``

            is solved, which is the standard way to impose a trace-minimum
            datum without distorting the network's internal geometry.

    Raises:
        ComputationError: when the system is singular and no constraints were
            supplied. The message names the undetermined unknowns.
    """
    normal = system.normal_matrix()
    vector = system.normal_vector()
    condition = _condition_number(normal)

    if constraints is not None:
        return _solve_bordered(normal, vector, constraints, condition)

    findings = diagnose_rank(normal, layout)
    if findings:
        raise ComputationError(
            "rank_deficient_normal_matrix",
            deficiency=len(findings),
            condition_number=condition,
            undetermined=[finding.describe() for finding in findings],
            expected=(
                "a network with enough constraints to define the datum, or an "
                "inner- or minimum-constraint solution. The listed parameter "
                "combinations are not determined by the observations"
            ),
        )

    try:
        factor = np.linalg.cholesky(normal)
        x = _cholesky_solve(factor, vector)
        cofactor = _cholesky_inverse(factor)
        method = "cholesky"
    except np.linalg.LinAlgError:
        # The normal matrix is positive definite in exact arithmetic whenever
        # the system has full rank, so reaching here means it is badly enough
        # conditioned that Cholesky fails numerically. QR on the weighted design
        # matrix has roughly the square root of the condition number, so it
        # often succeeds where this did.
        return _solve_qr(system, condition)

    return SolveResult(x=x, cofactor=cofactor, condition_number=condition, method=method)


def _condition_number(normal: np.ndarray) -> float:
    if normal.size == 0:
        return float("inf")
    eigenvalues = np.abs(np.linalg.eigvalsh(normal))
    smallest = float(np.min(eigenvalues))
    largest = float(np.max(eigenvalues))
    if smallest == 0.0:
        return float("inf")
    return largest / smallest


def _cholesky_solve(factor: np.ndarray, vector: np.ndarray) -> np.ndarray:
    intermediate = np.linalg.solve(factor, vector)
    return np.linalg.solve(factor.T, intermediate)


def _cholesky_inverse(factor: np.ndarray) -> np.ndarray:
    identity = np.eye(factor.shape[0])
    inverse_factor = np.linalg.solve(factor, identity)
    return inverse_factor.T @ inverse_factor


def _solve_qr(system: LinearisedSystem, condition: float) -> SolveResult:
    """Least squares by QR on the weighted design matrix.

    Numerically better than forming the normal equations, at more cost. Used
    when Cholesky fails, per ``specs/06`` section 2.4.
    """
    root = _weight_square_root(system.weight)
    weighted_design = root @ system.design
    weighted_misclosure = root @ system.misclosure

    q, r = np.linalg.qr(weighted_design)
    x = np.linalg.solve(r, q.T @ weighted_misclosure)
    r_inverse = np.linalg.solve(r, np.eye(r.shape[0]))
    return SolveResult(
        x=x,
        cofactor=r_inverse @ r_inverse.T,
        condition_number=condition,
        method="qr",
    )


def _weight_square_root(weight: np.ndarray) -> np.ndarray:
    """A matrix R with R^T R = P, for the weighted QR formulation."""
    eigenvalues, eigenvectors = np.linalg.eigh(weight)
    eigenvalues = np.clip(eigenvalues, 0.0, None)
    return np.diag(np.sqrt(eigenvalues)) @ eigenvectors.T


def _solve_bordered(
    normal: np.ndarray, vector: np.ndarray, constraints: np.ndarray, condition: float
) -> SolveResult:
    """Solve with datum constraints by bordering the normal matrix."""
    size = normal.shape[0]
    count = constraints.shape[1]

    bordered = np.zeros((size + count, size + count))
    bordered[:size, :size] = normal
    bordered[:size, size:] = constraints
    bordered[size:, :size] = constraints.T

    right = np.zeros(size + count)
    right[:size] = vector

    try:
        solution = np.linalg.solve(bordered, right)
        inverse = np.linalg.inv(bordered)
    except np.linalg.LinAlgError as error:
        raise ComputationError(
            "constrained_system_singular",
            constraints=count,
            expected=(
                "constraints that remove exactly the datum defect; too few leave "
                "the system singular and too many over-constrain it"
            ),
        ) from error

    return SolveResult(
        x=solution[:size],
        # The leading block of the bordered inverse is the constrained cofactor
        # matrix -- the pseudo-inverse of N subject to G^T x = 0.
        cofactor=inverse[:size, :size],
        condition_number=condition,
        rank_deficiency=count,
        method="bordered",
    )
