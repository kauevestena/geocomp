# SPDX-License-Identifier: GPL-2.0-or-later
"""Which solver a network gets, and the refusal when neither can take it (NFR-008).

``specs/06-adjustment-core.md`` section 2.4; ``adr/0008-scipy-and-network-scale.md``.

The dense path holds **A**, **P**, **N**, **Q**xx and the residual cofactor
**Q**vv as full arrays. For m rows and n parameters that is, measured in P12c
on grid networks up to 900 stations (``specs/06`` section 2.4 has the table),

    8 * (6 m^2 + 4 m n + 2 n^2) bytes

-- the m^2 terms dominate, because every observation is a row and **Q**vv is
m x m. A 10,000-station plane network is 40,000 rows: 77 GB. Nothing about that
is a tuning problem, and before P12c the dense path simply tried, and a large
network exhausted memory with nothing to say why.

So the choice is made before anything is allocated:

* **auto**, the default -- dense while the footprint is under
  :data:`SPARSE_ABOVE`; beyond it, sparse when SciPy is importable; without
  SciPy, dense while the machine can hold it, and a refusal naming SciPy when
  it cannot.
* **dense** -- the reference path, forced; refused if it cannot be held.
  Variance component estimation needs it (``variance_components.py``).
* **sparse** -- forced, for testing the sparse path on small networks.

The choice depends on the network and on the machine's memory, never on what
happens to be free at the moment, so one network on one machine always gets
the same solver; the solution records which it was.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass

from geocomp.core.errors import ComputationError, ValidationError

__all__ = [
    "AUTO",
    "DENSE",
    "SOLVERS",
    "SPARSE",
    "SPARSE_ABOVE",
    "SolverChoice",
    "choose_solver",
    "dense_footprint",
    "dense_limit",
    "physical_memory",
    "sparse_available",
]

AUTO = "auto"
DENSE = "dense"
SPARSE = "sparse"
SOLVERS = (AUTO, DENSE, SPARSE)

#: Dense footprint beyond which, with SciPy present, the sparse path is taken.
#: 1 GiB is about 1,050 stations of a braced plane grid, adjusted densely in
#: some 20 seconds; the sparse path takes a fraction of one. Below it the dense
#: path is kept because it carries the full parameter covariance into the
#: solution, which a comparison of epochs uses (``core/monitoring/compare.py``).
SPARSE_ABOVE = 1 << 30

#: What the dense path is allowed when the machine's memory cannot be read.
_UNKNOWN_MEMORY_LIMIT = 4 << 30


@dataclass(frozen=True)
class SolverChoice:
    """Which path a network takes, and the size that decided it."""

    solver: str
    footprint: int
    rows: int
    parameters: int


def dense_footprint(rows: int, parameters: int) -> int:
    """Bytes the dense path holds at its peak, for *rows* x *parameters*."""
    m, n = int(rows), int(parameters)
    return 8 * (6 * m * m + 4 * m * n + 2 * n * n)


def physical_memory() -> int | None:
    """The machine's physical memory in bytes, or ``None`` where it cannot be read."""
    if sys.platform == "win32":
        return _windows_memory()
    try:
        pages = os.sysconf("SC_PHYS_PAGES")
        page = os.sysconf("SC_PAGE_SIZE")
    except (AttributeError, ValueError, OSError):
        return None
    if pages <= 0 or page <= 0:
        return None
    return int(pages) * int(page)


def _windows_memory() -> int | None:
    import ctypes

    class _Status(ctypes.Structure):
        _fields_ = [
            ("dwLength", ctypes.c_ulong),
            ("dwMemoryLoad", ctypes.c_ulong),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]

    status = _Status()
    status.dwLength = ctypes.sizeof(_Status)
    try:
        ok = ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
    except (AttributeError, OSError):
        return None
    return int(status.ullTotalPhys) if ok and status.ullTotalPhys else None


def dense_limit() -> int:
    """The largest dense footprint this machine is asked to hold: half its memory.

    Half, because QGIS, its layers and the operating system are using the rest,
    and the footprint is an estimate.
    """
    memory = physical_memory()
    return memory // 2 if memory else _UNKNOWN_MEMORY_LIMIT


def sparse_available() -> bool:
    """Whether SciPy's sparse factorisation can be imported."""
    try:
        import scipy.sparse.linalg  # noqa: F401
    except ImportError:
        return False
    return True


def choose_solver(
    requested: str,
    rows: int,
    parameters: int,
    *,
    sparse_above: int | None = None,
    limit: int | None = None,
    scipy: bool | None = None,
) -> SolverChoice:
    """Decide the path for a system of *rows* x *parameters*, before allocating it.

    Args:
        requested: ``"auto"``, ``"dense"`` or ``"sparse"``.
        sparse_above, limit, scipy: For tests; by default :data:`SPARSE_ABOVE`,
            :func:`dense_limit` and :func:`sparse_available`.

    Raises:
        ComputationError: ``adjustment_needs_scipy`` when the network is too
            large for the dense path and SciPy is absent;
            ``adjustment_too_large_for_dense`` when the dense path was asked
            for and cannot be held; ``sparse_solver_needs_scipy`` when the
            sparse path was asked for without SciPy.
    """
    if requested not in SOLVERS:
        raise ValidationError("unknown_solver", received=requested, expected=list(SOLVERS))
    footprint = dense_footprint(rows, parameters)
    sparse_above = SPARSE_ABOVE if sparse_above is None else sparse_above
    limit = dense_limit() if limit is None else limit
    scipy = sparse_available() if scipy is None else scipy

    def chosen(solver: str) -> SolverChoice:
        return SolverChoice(solver=solver, footprint=footprint, rows=rows, parameters=parameters)

    if requested == SPARSE:
        if not scipy:
            raise ComputationError(
                "sparse_solver_needs_scipy",
                expected="SciPy (scipy.sparse) installed in QGIS's Python, for the sparse path",
            )
        return chosen(SPARSE)
    if requested == DENSE:
        if footprint > limit:
            raise ComputationError(
                "adjustment_too_large_for_dense",
                rows=rows,
                parameters=parameters,
                footprint_mib=round(footprint / 2**20),
                limit_mib=round(limit / 2**20),
                expected=(
                    "a network small enough to hold densely; this computation has no "
                    "sparse form, so a network this large cannot be given it"
                ),
            )
        return chosen(DENSE)
    if footprint <= sparse_above:
        return chosen(DENSE)
    if scipy:
        return chosen(SPARSE)
    if footprint <= limit:
        return chosen(DENSE)
    raise ComputationError(
        "adjustment_needs_scipy",
        rows=rows,
        parameters=parameters,
        footprint_mib=round(footprint / 2**20),
        limit_mib=round(limit / 2**20),
        expected=(
            "SciPy installed in QGIS's Python: a network this large is adjusted with a "
            "sparse factorisation, which SciPy provides, and held densely it would need "
            "more memory than this machine has. Beyond about 10,000 stations, adjust it "
            "with DynAdjust's segmentation instead"
        ),
    )
