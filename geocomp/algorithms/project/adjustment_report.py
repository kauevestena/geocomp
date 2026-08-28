# SPDX-License-Identifier: GPL-2.0-or-later
"""``geocomp:project_report`` -- the adjustment report (FR-930, FR-931).

``specs/19-visualization.md`` section 7.

Separate from the algorithms that produce a solution, and deliberately: the
report is built from a :class:`~geocomp.core.models.Solution` **and nothing
else**, which is what makes one report render an in-house adjustment and a
DynAdjust run alike (phase P6 fills the same structure). An algorithm that
rendered its own report inside itself would have to be written again for every
engine.

It is also what makes a report reproducible from a stored result. A solution
read back out of a project store a year later renders the same report it did on
the day, because nothing in the rendering reads the clock or the environment
(NFR-007).

**The omitted sections are an output, not a warning to swallow.** A custom
template that leaves out reliability is making an editorial choice; the
algorithm names what was left out so the choice is visible to whoever receives
the report.
"""

from __future__ import annotations

from typing import Any

from qgis.core import (
    Qgis,
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingParameterFile,
    QgsProcessingParameterFileDestination,
)

from geocomp.algorithms.base import GeoCompAlgorithm
from geocomp.algorithms.project.common import read_network, read_solution
from geocomp.core.errors import GeoCompError

__all__ = ["ProjectReportAlgorithm"]

SOLUTION = "SOLUTION"
NETWORK = "NETWORK"
TEMPLATE = "TEMPLATE"
OUTPUT_HTML = "OUTPUT_HTML"

#: Result key: the sections the template did not place.
OMITTED = "OMITTED"


class ProjectReportAlgorithm(GeoCompAlgorithm):
    """Renders the adjustment report from a stored solution."""

    TR_CONTEXT = "ProjectReportAlgorithm"

    def displayName(self) -> str:
        return self.tr("Adjustment report")

    def shortDescription(self) -> str:
        return self.tr("Render the full adjustment report from a solution document.")

    def help_body(self) -> str:
        return self.tr(
            "<p>Renders the complete adjustment report: identification, inputs, effective "
            "parameters and where each came from, adjusted coordinates, statistics, "
            "observation results, reliability, error ellipses, provenance and software "
            "versions.</p>"
            "<p>Built from the solution alone, so it renders a solution read back out of a "
            "project store exactly as it rendered on the day it was computed. Nothing in "
            "it reads the clock.</p>"
            "<p>Three things are never omitted whatever a template does with the rest: the "
            "uncertainty mode and the strategies behind it, the provenance with its input "
            "digests, and the uncheckable observations. Presenting an approximate figure "
            "as a rigorously propagated one misrepresents the survey, and monitoring "
            "decisions are made on these numbers.</p>"
            "<h3>Parameters</h3>"
            "<p><b>Solution</b> &mdash; a solution document written by an adjustment "
            "algorithm.</p>"
            "<p><b>Network</b> &mdash; optional. Adds the observation descriptions the "
            "solution does not carry, so the observation results table names stations "
            "rather than only observation ids.</p>"
            "<p><b>Template</b> &mdash; optional HTML template (FR-931). Sections it does "
            "not place are listed in the log, because leaving one out is an editorial "
            "choice that should be visible.</p>"
        )

    def initAlgorithm(self, config: dict[str, Any] | None = None) -> None:
        self.addParameter(
            QgsProcessingParameterFile(
                SOLUTION, self.tr("Solution document"), extension="json"
            )
        )
        self.addParameter(
            QgsProcessingParameterFile(
                NETWORK,
                self.tr("Network document (optional)"),
                extension="json",
                optional=True,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterFile(
                TEMPLATE,
                self.tr("Report template (optional)"),
                extension="html",
                optional=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterFileDestination(
                OUTPUT_HTML,
                self.tr("Report"),
                self.tr("HTML files (*.html)"),
                optional=True,
                createByDefault=True,
            )
        )

    def processAlgorithm(
        self,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> dict[str, Any]:
        from pathlib import Path

        from geocomp.reports import ReportContext, render_adjustment_report

        try:
            solution = read_solution(self.parameterAsFile(parameters, SOLUTION, context))
            network = read_network(self.parameterAsFile(parameters, NETWORK, context))
        except GeoCompError as error:
            raise QgsProcessingException(str(error)) from error

        feedback.setProgress(30)
        template = self.parameterAsFile(parameters, TEMPLATE, context) or ""
        report_context = ReportContext(
            network=network,
            qgis_version=Qgis.QGIS_VERSION,
            parameter_scopes=self._scopes(feedback),
            template_directory=str(Path(template).parent) if template else "",
            template_name=Path(template).name if template else "adjustment.html",
        )

        try:
            html, omitted = render_adjustment_report(solution, report_context)
        except GeoCompError as error:
            raise QgsProcessingException(str(error)) from error

        feedback.setProgress(80)
        if omitted:
            feedback.pushWarning(
                self.tr("The template places no: ") + ", ".join(omitted)
            )

        target = self.parameterAsFileOutput(parameters, OUTPUT_HTML, context)
        if target:
            Path(target).write_text(html, encoding="utf-8")
            feedback.pushInfo(self.tr("Report written."))

        feedback.setProgress(100)
        return {OUTPUT_HTML: target, OMITTED: omitted}

    def _scopes(self, feedback: QgsProcessingFeedback) -> dict[str, tuple[Any, str]]:
        """Every effective setting and the scope it came from (FR-068).

        In the report because "confidence 0.99" and "confidence 0.99, from this
        project" are different statements to somebody reproducing the run. A
        settings read that fails is logged and skipped rather than aborting: a
        report missing one row of its parameter table is far better than no
        report at all.
        """
        from geocomp.services.settings_service import settings

        try:
            resolved = settings.all_resolved()
        except Exception as error:  # noqa: BLE001 - never lose a report over a settings read
            feedback.pushDebugInfo(f"settings unavailable: {error}")
            return {}
        return {key: (item.value, item.scope.value) for key, item in resolved.items()}
