# SPDX-License-Identifier: GPL-2.0-or-later
"""Things worth telling the user about, graded by how much they matter.

Introduced in phase P3 by moving :class:`Severity` and :class:`Finding` out of
:mod:`geocomp.core.preanalysis.inspection`, where phase P2 first needed them.
Network inspection and total-station pre-processing both produce findings, and
two severity scales that meant slightly different things by "warning" would be
worse than one shared scale.

**Findings are returned, not raised.** An importer, an inspection or a
pre-processing run must be able to report every problem at once rather than
stopping at the first (FR-166): a field book with six bad records should need one
run, not six.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

__all__ = ["Finding", "Severity", "worst_severity"]


class Severity(Enum):
    """How much a finding matters.

    ``BLOCKING`` means the computation cannot proceed; ``WARNING`` means it can
    but the result may not mean what the user expects; ``INFO`` is worth seeing
    and is not a problem. The distinction is what lets a UI offer "run anyway"
    honestly.
    """

    BLOCKING = "blocking"
    WARNING = "warning"
    INFO = "info"

    @property
    def rank(self) -> int:
        """Higher is more serious, for sorting and comparison."""
        return {Severity.INFO: 0, Severity.WARNING: 1, Severity.BLOCKING: 2}[self]


@dataclass(frozen=True)
class Finding:
    """One thing worth telling the user about.

    Attributes:
        code: Stable, machine-readable, ``lower_snake_case``. A UI filters and
            a test asserts on this; the message is for a human and may be
            reworded without breaking either.
        message: Developer-facing English. The presentation layer may replace it
            with a translated rendering keyed by ``code``, exactly as
            :mod:`geocomp.services.messages` does for errors.
        stations / observations: What the finding is about, so a map can
            highlight it.
        value / threshold: The measured quantity and what it was compared
            against, where the finding came from a tolerance. Present so a
            report can say *how far* out of tolerance, not just that it was.
    """

    code: str
    severity: Severity
    message: str
    stations: tuple[str, ...] = ()
    observations: tuple[str, ...] = ()
    value: float | None = None
    threshold: float | None = None

    @property
    def is_blocking(self) -> bool:
        return self.severity is Severity.BLOCKING


def worst_severity(findings: tuple[Finding, ...] | list[Finding]) -> Severity | None:
    """The most serious severity present, or ``None`` for no findings."""
    if not findings:
        return None
    return max((finding.severity for finding in findings), key=lambda s: s.rank)
