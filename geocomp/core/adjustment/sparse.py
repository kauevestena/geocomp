# SPDX-License-Identifier: GPL-2.0-or-later
"""The sparse path: networks the dense one cannot hold (NFR-008, ADR-0008).

``specs/06-adjustment-core.md`` section 2.4. Imported only when
:func:`~geocomp.core.adjustment.scale.choose_solver` has chosen it, so SciPy
stays optional: nothing here is reached on a machine without it.

**What is sparse, and what is not.** A geodetic normal matrix couples a
station only to the stations it was observed with, so **N** is sparse and
factorises with little fill under a minimum-degree ordering -- 0.2 s at 10,000
stations, where the dense path would need 77 GB. **A** is held compressed by
row, and **P** as its diagonal blocks (:class:`~geocomp.core.adjustment.blocks.BlockDiagonal`).

The inverse is not sparse, and is never formed. The adjustment needs only
parts of it, all found in one sweep over its columns (:func:`_sweep`):

* each station's own block of **Q**xx -- its covariance, its ellipse;
* the diagonal blocks of **Q**vv = **P**^-1 - **A Q**xx **A**^T over **P**'s
  blocks -- the redundancy numbers, the w-tests and the minimal detectable
  biases need nothing else;
* ``||Q``xx ``A^T P e_i||`` for every row -- the external reliability. Without
  the n x m influence matrix: ``F^T F = P A Q Q A^T P`` and ``Q Q`` is the sum
  over column chunks ``C`` of ``C C^T``, so each row's squared norm is the sum
  over chunks of the squared row of ``P A C``.

Anything else of **Q**xx -- a covariance between two stations -- is solved for
one column at a time when it is asked for (:class:`SparseCofactor`).

**What it does not give.** The full parameter covariance: a solution from this
path carries each station's block and not the matrix between them
(``to_solution``), and a comparison of two epochs says so. Variance component
estimation needs the full **Q**vv and refuses this path by name.
"""

from __future__ import annotations

from collections import OrderedDict

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

from geocomp.core.adjustment.blocks import BlockDiagonal
from geocomp.core.adjustment.normal_equations import (
    RANK_TOLERANCE,
    ROUNDING_TOLERANCE,
    NullSpaceFinding,
    SolveResult,
    _condition_number,
    diagnose_rank,
    linearise,
)
from geocomp.core.adjustment.parameters import ParameterLayout, WeightedConstraint
from geocomp.core.errors import ComputationError
from geocomp.core.models import Cluster, Observation

__all__ = [
    "SparseCofactor",
    "SparseSystem",
    "assemble",
    "solve",
]

#: The fill-reducing ordering. A minimum-degree ordering of N's own pattern:
#: COLAMD, SuperLU's default, filled the 10,000-station factor fifty times
#: over and took 83 s where this takes 0.2 s (measured in P12c).
ORDERING = "MMD_AT_PLUS_A"
#: Partial pivoting is all but switched off -- N is positive definite and its
#: diagonal is the right pivot -- but not quite: a bordered system has zeros on
#: its diagonal, and with no pivoting at all it lost eight digits.
PIVOT_THRESHOLD = 0.01
#: Up to this many parameters the spectrum is examined densely, exactly as the
#: dense path does; beyond it, by Lanczos iteration.
DENSE_EXAMINATION = 2000
#: How many of the smallest eigenvalues the iterative examination looks at.
#: More undetermined directions than this are reported as this many.
EXAMINED = 12
#: Bytes of dense column block one sweep step may hold.
CHUNK_BYTES = 1 << 28
#: Columns of Qxx kept once solved for an off-block entry.
CACHED_COLUMNS = 64


class SparseSystem:
    """The linearised system, held sparsely. The same fields as the dense one."""

    def __init__(self, design, misclosure: np.ndarray, weight: BlockDiagonal, row_labels):
        self.design = design
        self.misclosure = misclosure
        self.weight = weight
        self.row_labels = row_labels

    @property
    def observation_count(self) -> int:
        return self.design.shape[0]

    @property
    def parameter_count(self) -> int:
        return self.design.shape[1]

    def normal_matrix(self):
        normal = self.design.T @ (_sparse(self.weight) @ self.design)
        # Symmetric in exact arithmetic; made so in floating point, which the
        # symmetric ordering and the Lanczos examination both assume.
        return ((normal + normal.T) * 0.5).tocsc()

    def normal_vector(self) -> np.ndarray:
        return self.design.T @ (self.weight @ self.misclosure)


def _sparse(blocks: BlockDiagonal):
    rows, columns, values = [], [], []
    for index, matrices in blocks.groups.values():
        size = index.shape[1]
        rows.append(np.repeat(index, size, axis=1).ravel())
        columns.append(np.tile(index, (1, size)).ravel())
        values.append(matrices.ravel())
    if not rows:
        return sp.csr_matrix(blocks.shape)
    return sp.csr_matrix(
        (np.concatenate(values), (np.concatenate(rows), np.concatenate(columns))), shape=blocks.shape
    )


def assemble(
    observations: list[Observation],
    clusters: dict[str, Cluster],
    layout: ParameterLayout,
    x: np.ndarray,
    *,
    weighted: list[WeightedConstraint] | None = None,
) -> SparseSystem:
    """:func:`~geocomp.core.adjustment.normal_equations.assemble`, held sparsely."""
    rows = linearise(observations, clusters, layout, x, weighted=weighted)
    counts = np.fromiter((len(p) for p in rows.partials), dtype=np.intp, count=rows.size)
    pointers = np.concatenate(([0], np.cumsum(counts)))
    total = int(pointers[-1])
    columns = np.fromiter((c for p in rows.partials for c in p), dtype=np.intp, count=total)
    values = np.fromiter((v for p in rows.partials for v in p.values()), dtype=float, count=total)
    design = sp.csr_matrix((values, columns, pointers), shape=(rows.size, layout.size))
    design.sort_indices()
    return SparseSystem(
        design=design,
        misclosure=np.array(rows.misclosure),
        weight=BlockDiagonal.from_blocks(rows.size, rows.weight_blocks),
        row_labels=rows.labels,
    )


class _Factor:
    """**N**, or **N** bordered by the datum constraints, factorised once."""

    def __init__(self, normal, constraints: np.ndarray | None):
        self.size = normal.shape[0]
        self.border = 0 if constraints is None else constraints.shape[1]
        if constraints is None:
            self.matrix = normal.tocsc()
        else:
            border = sp.csc_matrix(constraints)
            self.matrix = sp.bmat([[normal, border], [border.T, None]], format="csc")
        self._norm = float(abs(self.matrix).sum(axis=1).max()) if self.matrix.nnz else 0.0
        self._lu = spla.splu(
            self.matrix,
            permc_spec=ORDERING,
            diag_pivot_thresh=PIVOT_THRESHOLD,
            options={"SymmetricMode": True},
        )

    def solve(self, right: np.ndarray, *, refine: bool = False) -> np.ndarray:
        """The parameter part of the solution for *right*, a vector or columns."""
        padded = right
        if self.border:
            shape = (self.border, *right.shape[1:])
            padded = np.concatenate((right, np.zeros(shape)))
        solution = self._lu.solve(padded)
        if refine:
            # One step of iterative refinement, and a check that the result
            # solves the system at all: a normwise backward error, which a
            # stable factorisation keeps near the rounding error whatever the
            # condition, and a failed one does not.
            solution = solution + self._lu.solve(padded - self.matrix @ solution)
            residual = np.abs(padded - self.matrix @ solution).max()
            scale = self._norm * np.abs(solution).max() + np.abs(padded).max()
            if not np.isfinite(residual) or residual > 1e-8 * max(scale, 1e-300):
                raise np.linalg.LinAlgError("the factorisation does not solve the system")
        return solution[: self.size]


def _spectrum(normal, layout: ParameterLayout) -> tuple[list[NullSpaceFinding], float]:
    """The undetermined directions and the condition number of **N**.

    Densely, exactly as the dense path, while that is cheap; beyond it the
    largest eigenvalue by Lanczos and the smallest by shift-invert Lanczos on
    this module's own factorisation -- SciPy's default would refactorise with
    the ordering that took 83 s.
    """
    size = normal.shape[0]
    if size <= DENSE_EXAMINATION:
        dense = normal.toarray()
        return diagnose_rank(dense, layout), _condition_number(dense)
    try:
        largest = float(spla.eigsh(normal, k=1, which="LA", return_eigenvectors=False, tol=1e-6)[0])
        if largest <= 0.0:
            return [NullSpaceFinding([(label, 1.0) for label in layout.labels()], 0.0)], float("inf")
        shift = largest * 1e-10
        shifted = _Factor(normal + shift * sp.identity(size, format="csc"), None)
        inverse = spla.LinearOperator(normal.shape, matvec=shifted.solve, dtype=float)
        values, vectors = spla.eigsh(
            normal, k=min(EXAMINED, size - 2), sigma=-shift, which="LM", OPinv=inverse
        )
    except (spla.ArpackNoConvergence, RuntimeError):
        return [], float("nan")

    labels = layout.labels()
    findings: list[NullSpaceFinding] = []
    for index in np.argsort(values):
        value = float(values[index])
        if abs(value) / largest > RANK_TOLERANCE:
            continue
        vector = vectors[:, index]
        order = np.argsort(-np.abs(vector))
        contributions = [
            (labels[position], float(vector[position]))
            for position in order
            if abs(float(vector[position])) > 1e-8
        ]
        findings.append(NullSpaceFinding(contributions, value / largest))
    smallest = float(np.min(np.abs(values)))
    return findings, (largest / smallest if smallest > 0.0 else float("inf"))


def solve(
    system: SparseSystem,
    layout: ParameterLayout,
    *,
    constraints: np.ndarray | None = None,
    examine: bool = True,
    statistics: bool = False,
) -> SolveResult:
    """:func:`~geocomp.core.adjustment.normal_equations.solve`, by sparse LU.

    Args:
        examine: Look for undetermined directions and the condition number.
            The adjustment examines its first and its final system: the rank of
            a network does not change between iterations, and each examination
            is a few hundred solves.
        statistics: Sweep the inverse for the cofactor blocks, **Q**vv and the
            influence norms (:class:`SparseCofactor`). Only the final system.

    Raises:
        ComputationError: as the dense path does, with the same codes.
    """
    normal = system.normal_matrix()
    vector = system.normal_vector()
    findings, condition = _spectrum(normal, layout) if examine else ([], float("nan"))

    if constraints is None and findings:
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
        factor = _Factor(normal, constraints)
        x = factor.solve(vector, refine=True)
    except (RuntimeError, np.linalg.LinAlgError) as error:
        if constraints is not None:
            raise ComputationError(
                "constrained_system_singular",
                constraints=constraints.shape[1],
                expected=(
                    "constraints that remove exactly the datum defect; too few leave "
                    "the system singular and too many over-constrain it"
                ),
            ) from error
        raise ComputationError(
            "rank_deficient_normal_matrix",
            deficiency=max(len(findings), 1),
            condition_number=condition,
            undetermined=[finding.describe() for finding in findings]
            or ["the factorisation found the normal matrix singular"],
            expected=(
                "a network with enough constraints to define the datum, or an "
                "inner- or minimum-constraint solution"
            ),
        ) from error

    cofactor = _sweep(factor, layout, system) if statistics else None
    return SolveResult(
        x=x,
        cofactor=cofactor,
        condition_number=condition,
        rank_deficiency=0 if constraints is None else constraints.shape[1],
        method="sparse-bordered" if constraints is not None else "sparse-lu",
    )


class SparseCofactor:
    """**Q**xx where the adjustment needs it, and the rest on request.

    Indexed like the dense array it replaces -- ``q[i, j]``,
    ``q[np.ix_(rows, columns)]``, ``q.diagonal()``, ``sigma2 * q`` -- so the
    code that reads a station's covariance does not learn which path ran. An
    entry within one owner's block (a station's components, a setup's
    orientation, a session's drift) was found by the sweep; any other is the
    entry of a column solved for when first asked and kept for a while.

    Attributes:
        residuals: **Q**vv's diagonal blocks over **P**'s, as a
            :class:`BlockDiagonal`.
        influence_norms: ``||Q A^T P e_i||`` per row, at this scale.
    """

    def __init__(
        self,
        blocks: BlockDiagonal,
        factor: _Factor,
        residuals: BlockDiagonal,
        influence: np.ndarray,
        *,
        scale: float = 1.0,
        cache: OrderedDict | None = None,
    ):
        self.blocks = blocks
        self.residuals = residuals
        self._factor = factor
        self._influence = influence
        self.scale = float(scale)
        self._cache = cache if cache is not None else OrderedDict()

    @property
    def shape(self) -> tuple[int, int]:
        return self.blocks.shape

    @property
    def influence_norms(self) -> np.ndarray:
        return self.scale * self._influence

    def diagonal(self) -> np.ndarray:
        return self.scale * self.blocks.diagonal()

    def __mul__(self, factor: float) -> SparseCofactor:
        if not np.isscalar(factor):
            return NotImplemented
        return SparseCofactor(
            self.blocks,
            self._factor,
            self.residuals,
            self._influence,
            scale=self.scale * float(factor),
            cache=self._cache,
        )

    __rmul__ = __mul__
    __array_ufunc__ = None

    def __getitem__(self, key):
        rows, columns = key
        if np.isscalar(rows) and np.isscalar(columns):
            return self._entry(int(rows), int(columns))
        rows, columns = np.broadcast_arrays(
            np.asarray(rows, dtype=np.intp), np.asarray(columns, dtype=np.intp)
        )
        out = np.empty(rows.shape)
        for index in np.ndindex(rows.shape):
            out[index] = self._entry(int(rows[index]), int(columns[index]))
        return out

    def _entry(self, row: int, column: int) -> float:
        if self.blocks.holds(row, column):
            return self.scale * self.blocks.entry(row, column)
        return self.scale * float(self._column(column)[row])

    def _column(self, column: int) -> np.ndarray:
        found = self._cache.get(column)
        if found is None:
            unit = np.zeros(self.blocks.size)
            unit[column] = 1.0
            found = self._factor.solve(unit)
            self._cache[column] = found
            if len(self._cache) > CACHED_COLUMNS:
                self._cache.popitem(last=False)
        else:
            self._cache.move_to_end(column)
        return found


def _owner_blocks(layout: ParameterLayout) -> BlockDiagonal:
    columns: dict[str, list[int]] = {}
    for index, slot in enumerate(layout.slots):
        columns.setdefault(slot.owner, []).append(index)
    return BlockDiagonal.from_blocks(
        layout.size, ((np.array(c), np.zeros((len(c), len(c)))) for c in columns.values())
    )


def _sweep(factor: _Factor, layout: ParameterLayout, system: SparseSystem) -> SparseCofactor:
    """One pass over **Q**xx's columns, keeping what the statistics need."""
    n, m = layout.size, system.observation_count
    owners = _owner_blocks(layout)
    owner = {s: np.zeros_like(matrices) for s, (_rows, matrices) in owners.groups.items()}
    weight = system.weight
    product = {s: np.zeros_like(matrices) for s, (_rows, matrices) in weight.groups.items()}
    squares = np.zeros(m)
    design_by_column = system.design.tocsc()
    chunk = int(max(16, min(512, CHUNK_BYTES // (8 * (2 * n + 2 * m)))))

    for start in range(0, n, chunk):
        stop = min(n, start + chunk)
        width = stop - start
        identity = np.zeros((n, width))
        identity[np.arange(start, stop), np.arange(width)] = 1.0
        columns = factor.solve(identity)  # Qxx[:, start:stop]

        # Each owner's block: the rows of the owner of every column here.
        here = np.arange(start, stop)
        sizes, blocks, positions = owners.locate(here)
        for size, (rows, _matrices) in owners.groups.items():
            chosen = sizes == size
            if not chosen.any():
                continue
            block, position = blocks[chosen], positions[chosen]
            owner[size][block, :, position] = columns[rows[block], (here[chosen] - start)[:, None]]

        # A Qxx[:, chunk]: the influence norms, and A Qxx A^T over P's blocks.
        applied = system.design @ columns
        weighted = weight @ applied
        squares += np.einsum("ij,ij->i", weighted, weighted)
        part = design_by_column[:, start:stop].tocoo()
        sizes, blocks, positions = weight.locate(part.row)
        for size, (rows, _matrices) in weight.groups.items():
            chosen = sizes == size
            if not chosen.any():
                continue
            block, position = blocks[chosen], positions[chosen]
            contribution = part.data[chosen][:, None] * applied[rows[block], part.col[chosen][:, None]]
            np.add.at(
                product[size], (block[:, None], np.arange(size)[None, :], position[:, None]), contribution
            )

    # Qvv = P^-1 - A Qxx A^T, over P's blocks; both made exactly symmetric.
    residuals = (weight.inverse() - weight.like(product)).symmetrised()
    return SparseCofactor(
        _zero_rounded(owners.like(owner).symmetrised()), factor, residuals, np.sqrt(squares)
    )


def _zero_rounded(blocks: BlockDiagonal) -> BlockDiagonal:
    """The blocks with each variance rounding took below zero set to zero, as the dense path's
    :func:`~geocomp.core.adjustment.normal_equations.zero_rounded_variances` does."""
    diagonal = blocks.diagonal()
    scale = float(np.max(np.abs(diagonal))) if diagonal.size else 0.0
    matrices = {}
    for size, (_rows, block) in blocks.groups.items():
        variances = np.diagonal(block, axis1=1, axis2=2)
        which, position = np.nonzero((variances < 0.0) & (variances >= -ROUNDING_TOLERANCE * scale))
        block = block.copy()
        block[which, position, :] = 0.0
        block[which, :, position] = 0.0
        matrices[size] = block
    return blocks.like(matrices)
