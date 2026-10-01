# SPDX-License-Identifier: GPL-2.0-or-later
"""``geocomp:monitoring_report`` -- the monitoring report from saved results (FR-932).

``specs/19`` section 7.2. Separate from the algorithms that produce the
documents, as the adjustment report is from the adjustments: the report is
built from the comparison and series documents **and nothing else**, so one
rendered next year from the saved files says what it said on the day, and a
monitoring programme can render its report with its own template without
running anything again.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qgis.core import (
    Qgis,
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingParameterFile,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterNumber,
)

from geocomp.algorithms.base import GeoCompAlgorithm
from geocomp.algorithms.monitoring.common import fail, read_document
from geocomp.core.errors import GeoCompError
from geocomp.core.monitoring import read_comparison_document, read_series_document

__all__ = ["MonitoringReportAlgorithm"]

ANALYSIS = "ANALYSIS"
SERIES = "SERIES"
TEMPLATE = "TEMPLATE"
EXAGGERATION = "EXAGGERATION"
OUTPUT_HTML = "OUTPUT_HTML"
OMITTED = "OMITTED"


class MonitoringReportAlgorithm(GeoCompAlgorithm):
    """Renders the monitoring report from saved monitoring documents."""

    TR_CONTEXT = "MonitoringReportAlgorithm"

    def displayName(self) -> str:
        return self.tr("Monitoring report")

    def shortDescription(self) -> str:
        return self.tr("Render the monitoring report from a comparison, a series, or both.")

    def help_body(self) -> str:
        return self.tr(
            "<p>Renders the monitoring report: the epochs and every transformation applied, the "
            "reference block's test and its localisation, the displacements with their "
            "significance decisions, a displacement map, the deformation, the alerts, and the "
            "time series and velocities.</p>"
            "<p>Built from the documents <i>Compare two epochs</i> and <i>Time series and "
            "velocities</i> write, and nothing else, so it renders the same report from the "
            "saved files at any later date.</p>"
            "<p>Three sections are placed even by a template that leaves them out: the "
            "uncertainty mode with the direction of its bias, the compatibility findings and "
            "transformations, and the reference block's test. Every decision in the report "
            "rests on them.</p>"
            "<h3>Parameters</h3>"
            "<p><b>Analysis document</b> and <b>Series document</b> &mdash; at least one.</p>"
            "<p><b>Report template</b> &mdash; optional HTML template (FR-931).</p>"
        )

    def initAlgorithm(self, config: dict[str, Any] | None = None) -> None:
        self.addParameter(
            QgsProcessingParameterFile(
                ANALYSIS, self.tr("Analysis document (Compare two epochs)"), extension="json", optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterFile(
                SERIES,
                self.tr("Series document (Time series and velocities)"),
                extension="json",
                optional=True,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterFile(
                TEMPLATE, self.tr("Report template (optional)"), extension="html", optional=True
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterNumber(
                EXAGGERATION,
                self.tr("Exaggeration of the map (0 = from the network's extent)"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=0.0,
                minValue=0.0,
                maxValue=1.0e9,
            )
        )
        self.addParameter(
            QgsProcessingParameterFileDestination(
                OUTPUT_HTML,
                self.tr("Monitoring report"),
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
        from geocomp.reports.monitoring import MonitoringReportContext, render_monitoring_report

        analysis_path = self.parameterAsFile(parameters, ANALYSIS, context)
        series_path = self.parameterAsFile(parameters, SERIES, context)
        if not analysis_path and not series_path:
            raise QgsProcessingException(
                self.tr("Give an analysis document, a series document, or both.")
            )
        comparison = read_document(analysis_path, read_comparison_document) if analysis_path else None
        series = read_document(series_path, read_series_document) if series_path else None
        template = self.parameterAsFile(parameters, TEMPLATE, context) or ""
        try:
            html, omitted = render_monitoring_report(
                comparison,
                series,
                MonitoringReportContext(
                    qgis_version=Qgis.QGIS_VERSION,
                    template_directory=str(Path(template).parent) if template else "",
                    template_name=Path(template).name if template else "monitoring.html",
                    exaggeration=self.parameterAsDouble(parameters, EXAGGERATION, context),
                ),
            )
        except GeoCompError as error:
            raise fail(error) from error
        if omitted:
            feedback.pushWarning(self.tr("The template places no: ") + ", ".join(omitted))
        target = self.parameterAsFileOutput(parameters, OUTPUT_HTML, context)
        if target:
            Path(target).write_text(html, encoding="utf-8")
            feedback.pushInfo(self.tr("Report written."))
        return {OUTPUT_HTML: target, OMITTED: omitted}
