# SPDX-License-Identifier: GPL-2.0-or-later
"""Reports (FR-930 to FR-932).

``specs/19-visualization.md`` section 7. Built from a
:class:`~geocomp.core.models.Solution` and nothing else, which is what makes one
report render an in-house adjustment and a DynAdjust run alike.

Template-driven (FR-931, FR-066), translated (FR-090), and deterministic
(NFR-007) -- nothing here reads the clock.
"""

from __future__ import annotations

from geocomp.reports.adjustment import (
    ReportContext,
    build_sections,
    render_adjustment_report,
)
from geocomp.reports.templates import Template, load_template, render

__all__ = [
    "ReportContext",
    "Template",
    "build_sections",
    "load_template",
    "render",
    "render_adjustment_report",
]
