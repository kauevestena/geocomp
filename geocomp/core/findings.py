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

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from geocomp.core.errors import GeoCompError

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
        message: Developer-facing English, for logs and tests. It is never
            what the user reads: :func:`geocomp.services.messages.finding_text`
            words the finding from ``code`` and ``context``, exactly as
            :func:`~geocomp.services.messages.message_for` words an error
            (``specs/18`` section 2). Until P12c-8 every report and panel
            showed this sentence, in English, whatever the language.
        stations / observations: What the finding is about, so a map can
            highlight it.
        value / threshold: The measured quantity and what it was compared
            against, where the finding came from a tolerance. Present so a
            report can say *how far* out of tolerance, not just that it was.
        context: The values the finding's template interpolates, keyed as the
            template names them. A number in it is already written for the
            reader -- rounded, in the unit the sentence states, and in the
            display locale's separator (FR-094) -- because the template only
            places it.
        error: The refusal the finding reports, when it reports one: a field
            book's bad row or setup, or a design the arithmetic refused. The
            template then says it through ``reason``, so the refusal reaches
            the reader in words and never as its developer diagnostic.
        wording: The template the finding is worded by, when it is not its
            code's. A refusal reported per row, setup or line keeps the
            refusal's code, which filters and tests use, and is worded by the
            frame it is reported in -- "Row %1: %2" -- with the refusal's own
            words as the second part.
    """

    code: str
    severity: Severity
    message: str
    stations: tuple[str, ...] = ()
    observations: tuple[str, ...] = ()
    value: float | None = None
    threshold: float | None = None
    context: Mapping[str, Any] = field(default_factory=dict, compare=False)
    error: GeoCompError | None = field(default=None, compare=False, repr=False)
    wording: str = field(default="", compare=False, repr=False)

    @property
    def template_code(self) -> str:
        """The key of the template that words this finding: ``finding.<wording or code>``."""
        return f"finding.{self.wording or self.code}"

    @property
    def is_blocking(self) -> bool:
        """Whether this finding stops the adjustment from running."""
        return self.severity is Severity.BLOCKING


def worst_severity(findings: tuple[Finding, ...] | list[Finding]) -> Severity | None:
    """The most serious severity present, or ``None`` for no findings."""
    if not findings:
        return None
    return max((finding.severity for finding in findings), key=lambda s: s.rank)
