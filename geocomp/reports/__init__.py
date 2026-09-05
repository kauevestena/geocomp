# SPDX-License-Identifier: GPL-2.0-or-later
"""Reports (FR-930 to FR-932).

``specs/19-visualization.md`` section 7. Built from a
:class:`~geocomp.core.models.Solution` and nothing else, which is what makes one
report render an in-house adjustment and a DynAdjust run alike.

Template-driven (FR-931, FR-066), translated (FR-090), and deterministic
(NFR-007) -- nothing here reads the clock.

**Why the re-exports are lazy.** :mod:`geocomp.reports.templates` is pure Python
and belongs to tier 1; :mod:`geocomp.reports.adjustment` renders translated
headings and so imports Qt. Re-exporting both eagerly meant that importing the
package -- which importing ``templates`` does -- pulled Qt in, and every tier-1
test of the template engine failed to collect in the seven CI jobs that have no
QGIS. The names below are therefore resolved on first access, so the two tiers
stay separable while the package's interface stays one list.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from geocomp.reports.templates import Template, load_template, render

if TYPE_CHECKING:
    from geocomp.reports.adjustment import (
        ReportContext,
        build_sections,
        render_adjustment_report,
    )

__all__ = [
    "ReportContext",
    "Template",
    "build_sections",
    "load_template",
    "render",
    "render_adjustment_report",
]

#: The names that live in the Qt-dependent module, resolved on demand.
_DEFERRED = {"ReportContext", "build_sections", "render_adjustment_report"}


def __getattr__(name: str) -> Any:
    if name in _DEFERRED:
        from geocomp.reports import adjustment

        return getattr(adjustment, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(__all__)
