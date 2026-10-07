# SPDX-License-Identifier: GPL-2.0-or-later
"""Block-diagonal matrices, and the diagonals the statistics read (NFR-008).

``specs/06-adjustment-core.md`` section 2.4. The weight matrix **P** is block
diagonal by construction -- a cluster's inverse covariance, or one row's
1/sigma^2 -- and held densely it is the largest thing the adjustment allocates:
m x m for m observations, 12 GB at 40,000 rows. The sparse path
(:mod:`geocomp.core.adjustment.sparse`) holds it, and the matching diagonal
blocks of the residual cofactor **Q**vv, as :class:`BlockDiagonal` instead.

The statistics need only diagonals -- the redundancy numbers are
``diag(Qvv P)``, a residual's variance is ``diag(Qvv)``, an observation's is
``diag(P^-1)`` -- so they are written against the helpers here, which take
either a dense array or a :class:`BlockDiagonal` and give the same numbers.
NumPy only: the dense path, which is the reference, goes through them too.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

import numpy as np

__all__ = [
    "BlockDiagonal",
    "inverse_diagonal",
    "product_diagonal",
    "quadratic_form",
]


class BlockDiagonal:
    """A square matrix that is zero outside blocks on its diagonal.

    A block is a set of rows, not necessarily contiguous -- a GNSS baseline's
    three rows sit wherever the assembly put them -- and its matrix over those
    rows. Blocks are grouped by size so each operation is one batched NumPy
    call per size rather than one Python call per block: forty thousand 1x1
    blocks are one array of forty thousand numbers.

    Every row belongs to exactly one block; a row no block names is a row of
    zeros.
    """

    #: NumPy defers ``vector @ blocks`` to :meth:`__rmatmul__` rather than
    #: trying to turn this into an array of objects.
    __array_ufunc__ = None

    def __init__(self, size: int, groups: dict[int, tuple[np.ndarray, np.ndarray]]):
        self.size = int(size)
        #: ``{block size: (rows (k, s), matrices (k, s, s))}``.
        self.groups = {
            s: (np.asarray(rows, dtype=np.intp), np.asarray(matrices, dtype=float))
            for s, (rows, matrices) in groups.items()
            if len(rows)
        }
        self._size_of = np.zeros(self.size, dtype=np.intp)
        self._block_of = np.zeros(self.size, dtype=np.intp)
        self._position_of = np.zeros(self.size, dtype=np.intp)
        for s, (rows, _matrices) in self.groups.items():
            if np.any(self._size_of[rows.ravel()]):
                raise ValueError("a row belongs to two blocks")
            self._size_of[rows] = s
            self._block_of[rows] = np.arange(len(rows))[:, None]
            self._position_of[rows] = np.arange(s)[None, :]
        #: The 1x1 blocks as a diagonal, zero on every other row.
        self._singles = np.zeros(self.size)
        if 1 in self.groups:
            rows, matrices = self.groups[1]
            self._singles[rows[:, 0]] = matrices[:, 0, 0]

    @classmethod
    def from_blocks(cls, size: int, blocks: Iterable[tuple[np.ndarray, np.ndarray]]) -> BlockDiagonal:
        """From ``(rows, matrix)`` pairs, as ``normal_equations.weight_blocks`` gives them."""
        by_size: dict[int, tuple[list[np.ndarray], list[np.ndarray]]] = {}
        for rows, matrix in blocks:
            rows = np.asarray(rows, dtype=np.intp).ravel()
            entry = by_size.setdefault(len(rows), ([], []))
            entry[0].append(rows)
            entry[1].append(np.asarray(matrix, dtype=float).reshape(len(rows), len(rows)))
        return cls(size, {s: (np.array(rows), np.array(matrices)) for s, (rows, matrices) in by_size.items()})

    # -- shape and structure ----------------------------------------------------

    @property
    def shape(self) -> tuple[int, int]:
        """``(size, size)``, as an array's."""
        return (self.size, self.size)

    def same_structure(self, other: BlockDiagonal) -> bool:
        """Whether *other* has blocks of the same sizes over the same rows."""
        return (
            self.size == other.size
            and self.groups.keys() == other.groups.keys()
            and all(np.array_equal(rows, other.groups[s][0]) for s, (rows, _m) in self.groups.items())
        )

    def like(self, matrices: dict[int, np.ndarray]) -> BlockDiagonal:
        """The same blocks over the same rows, holding *matrices* (keyed by size)."""
        return BlockDiagonal(self.size, {s: (self.groups[s][0], matrices[s]) for s in self.groups})

    def locate(self, rows: Sequence[int] | np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """For each of *rows*: its block's size, the block's index among blocks
        of that size, and the row's position within the block."""
        rows = np.asarray(rows, dtype=np.intp)
        return self._size_of[rows], self._block_of[rows], self._position_of[rows]

    def holds(self, row: int, column: int) -> bool:
        """Whether entry (*row*, *column*) lies within a block."""
        size = self._size_of[row]
        return bool(size and size == self._size_of[column] and self._block_of[row] == self._block_of[column])

    def symmetrised(self) -> BlockDiagonal:
        """``(B + B^T) / 2``: what floating point took from a symmetric matrix, restored."""
        return self.like({s: (m + np.swapaxes(m, 1, 2)) * 0.5 for s, (_r, m) in self.groups.items()})

    def to_dense(self) -> np.ndarray:
        """The full matrix, zeros and all: for tests and small systems, not for the sparse path."""
        dense = np.zeros(self.shape)
        for rows, matrices in self.groups.values():
            dense[rows[:, :, None], rows[:, None, :]] = matrices
        return dense

    # -- arithmetic -------------------------------------------------------------

    def diagonal(self) -> np.ndarray:
        """The main diagonal, as a dense vector."""
        out = np.zeros(self.size)
        for rows, matrices in self.groups.values():
            out[rows] = np.diagonal(matrices, axis1=1, axis2=2)
        return out

    def inverse(self) -> BlockDiagonal:
        """The inverse, block by block, in the same structure."""
        return self.like({s: np.linalg.inv(matrices) for s, (_r, matrices) in self.groups.items()})

    def transpose(self) -> BlockDiagonal:
        """The transpose, block by block, in the same structure."""
        return self.like({s: np.swapaxes(matrices, 1, 2) for s, (_r, matrices) in self.groups.items()})

    @property
    def T(self) -> BlockDiagonal:  # noqa: N802 -- NumPy's spelling
        """The transpose, spelled as NumPy spells it."""
        return self.transpose()

    def __mul__(self, factor: float) -> BlockDiagonal:
        if not np.isscalar(factor):
            return NotImplemented
        return self.like({s: matrices * factor for s, (_r, matrices) in self.groups.items()})

    __rmul__ = __mul__

    def __sub__(self, other: BlockDiagonal) -> BlockDiagonal:
        if not isinstance(other, BlockDiagonal) or not self.same_structure(other):
            return NotImplemented
        return self.like({s: matrices - other.groups[s][1] for s, (_r, matrices) in self.groups.items()})

    def __matmul__(self, other):
        if isinstance(other, BlockDiagonal):
            if not self.same_structure(other):
                raise ValueError("block-diagonal product needs one block structure")
            return self.like({s: matrices @ other.groups[s][1] for s, (_r, matrices) in self.groups.items()})
        other = np.asarray(other, dtype=float)
        # The common case, a row on its own, is a scale, not a product: one pass
        # over every row, with the rows of larger blocks then overwritten. At
        # 40,000 rows an einsum over all of them spent 15 s of one sweep here.
        out = self._singles[:, None] * other if other.ndim == 2 else self._singles * other
        for rows, matrices in self.groups.values():
            if rows.shape[1] == 1:
                continue
            if other.ndim == 1:
                out[rows] = (matrices @ other[rows][:, :, None])[:, :, 0]
            else:
                # rows (k, s), matrices (k, s, s), other[rows] (k, s, c): one
                # product per block, batched.
                out[rows] = matrices @ other[rows]
        return out

    def __rmatmul__(self, other):
        # x @ B = (B^T x)^T, which for a vector is the same vector.
        other = np.asarray(other, dtype=float)
        if other.ndim == 1:
            return self.transpose() @ other
        return (self.transpose() @ other.T).T

    def __getitem__(self, key):
        rows, columns = key
        if np.isscalar(rows) and np.isscalar(columns):
            return self.entry(int(rows), int(columns))
        rows = np.asarray(rows, dtype=np.intp)
        columns = np.asarray(columns, dtype=np.intp)
        rows, columns = np.broadcast_arrays(rows, columns)
        out = np.zeros(rows.shape)
        for index in np.ndindex(rows.shape):
            out[index] = self.entry(int(rows[index]), int(columns[index]))
        return out

    def entry(self, row: int, column: int) -> float:
        """The element at (*row*, *column*): zero outside the blocks."""
        if not self.holds(row, column):
            return 0.0
        matrices = self.groups[int(self._size_of[row])][1]
        return float(matrices[self._block_of[row], self._position_of[row], self._position_of[column]])

    def quadratic(self, vector: np.ndarray, rows: Sequence[int] | np.ndarray | None = None) -> float:
        """``v_R^T B_RR v_R``: over all rows, or over the rows *R* only."""
        vector = np.asarray(vector, dtype=float)
        if rows is not None:
            kept = np.zeros(self.size)
            kept[np.asarray(rows, dtype=np.intp)] = 1.0
            # Zeroing the others leaves exactly the terms within R: a block
            # straddling R contributes only its part inside.
            vector = vector * kept
        return float(vector @ (self @ vector))


def product_diagonal(first: np.ndarray | BlockDiagonal, second: np.ndarray | BlockDiagonal) -> np.ndarray:
    """``diag(first @ second)``, without forming the product.

    For dense arrays this is O(m^2) where the product is O(m^3) -- at 3,400
    rows the difference between a moment and forty billion multiplications.
    """
    if isinstance(first, BlockDiagonal):
        return (first @ second).diagonal()
    return np.einsum("ij,ji->i", first, second)


def inverse_diagonal(matrix: np.ndarray | BlockDiagonal) -> np.ndarray:
    """``diag(matrix^-1)``: each observation's variance from **P**."""
    if isinstance(matrix, BlockDiagonal):
        return matrix.inverse().diagonal()
    return np.diag(np.linalg.inv(matrix))


def quadratic_form(
    matrix: np.ndarray | BlockDiagonal,
    vector: np.ndarray,
    rows: Sequence[int] | np.ndarray | None = None,
) -> float:
    """``v_R^T M_RR v_R``, for a dense **P** or a block-diagonal one."""
    if isinstance(matrix, BlockDiagonal):
        return matrix.quadratic(vector, rows)
    vector = np.asarray(vector, dtype=float)
    if rows is None:
        return float(vector @ matrix @ vector)
    rows = np.asarray(rows, dtype=np.intp)
    return float(vector[rows] @ matrix[np.ix_(rows, rows)] @ vector[rows])
