# SPDX-License-Identifier: GPL-2.0-or-later
"""``geocomp:analysis_network_preanalysis`` -- judge a network before observing it.

FR-270, FR-271. ``specs/06-adjustment-core.md`` section 5.1.

    Sigma_x = sigma_0^2 (A^T P A)^-1

**A** depends only on the geometry of the planned network and **P** only on the
assumed precisions, so the expected precision of a network can be computed
before anyone goes to the field. That is the whole value of pre-analysis: a
design that cannot meet its specification costs a few seconds to discover here
and a field campaign to discover later.

**On FR-272.** The requirement also asks that a design be edited on the QGIS
canvas and re-evaluated in a loop. That dialog is deferred to the phase that can
verify it in a running QGIS; this algorithm delivers the mathematics and the
non-interactive route, which is what a model or a script needs anyway.
``specs/ROADMAP.md`` records the re-planning rather than leaving it implied.
"""

from __future__ import annotations

import csv
from typing import Any

from qgis.core import (
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFile,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
)

from geocomp.algorithms.analysis.common import (
    datum_labels,
    datum_of,
    escape,
    format_number,
    frame_labels,
    frame_of,
    load_network,
    render_document,
    render_note,
    render_table,
    station_list,
)
from geocomp.algorithms.base import GeoCompAlgorithm
from geocomp.core.errors import GeoCompError
from geocomp.core.preanalysis.design import simulate
from geocomp.core.statistics.reliability import DEFAULT_ALPHA, DEFAULT_BETA

__all__ = ["NetworkPreAnalysisAlgorithm"]

NETWORK = "NETWORK"
FRAME = "FRAME"
DATUM = "DATUM"
DATUM_STATIONS = "DATUM_STATIONS"
TOLERANCE = "TOLERANCE"
CONFIDENCE = "CONFIDENCE"
VARIANCE_FACTOR = "VARIANCE_FACTOR"
ALPHA = "ALPHA"
BETA = "BETA"
OUTPUT_HTML = "OUTPUT_HTML"
OUTPUT_CSV = "OUTPUT_CSV"
MEETS_TOLERANCE = "MEETS_TOLERANCE"
WORST_STATION = "WORST_STATION"
WORST_UNCERTAINTY = "WORST_UNCERTAINTY"
DEGREES_OF_FREEDOM = "DEGREES_OF_FREEDOM"
UNCHECKABLE_COUNT = "UNCHECKABLE_COUNT"


class NetworkPreAnalysisAlgorithm(GeoCompAlgorithm):
    """Expected precision and reliability of a *planned* network."""

    TR_CONTEXT = "NetworkPreAnalysisAlgorithm"

    def displayName(self) -> str:
        return self.tr("Pre-analyse network design")

    def shortDescription(self) -> str:
        return self.tr(
            "Compute the precision and reliability a planned network would achieve, "
            "before any observation exists."
        )

    def help_body(self) -> str:
        return self.tr(
            "<p>Computes what a <i>planned</i> network would achieve. The covariance of the "
            "adjusted coordinates depends only on the geometry of the planned observations "
            "and on their assumed precisions, so it can be computed before the first "
            "observation is made.</p>"
            "<p>The planned observations therefore need only a type, the stations they "
            "connect, and an assumed standard deviation. Any values they carry are ignored, "
            "which is why the simulation is exact rather than an approximation.</p>"
            "<p>Two things are reported, and both matter. <b>Precision</b> &mdash; the "
            "expected error ellipse and positional uncertainty of each station. "
            "<b>Reliability</b> &mdash; the smallest blunder the design could detect in each "
            "observation, and the effect on the coordinates of one that slipped through. A "
            "design can be precise and still unable to detect a blunder anywhere, so "
            "reporting precision alone gives half the answer.</p>"
            "<p>By default the datum is defined by inner constraints, because a design "
            "should be judged on its own geometry rather than through the distortion a "
            "particular fixed station imposes.</p>"
            "<h3>Parameters</h3>"
            "<p><b>Network</b> &mdash; a GeoComp network document (JSON) describing the "
            "planned stations and observations.</p>"
            "<p><b>Coordinate frame</b> &mdash; 1D, 2D or 3D.</p>"
            "<p><b>Datum definition</b> &mdash; how the datum defect is removed. "
            "<b>Datum stations</b> &mdash; for a minimum-constraint solution, the "
            "comma-separated stations the datum is defined on; empty means all of them.</p>"
            "<p><b>Required positional uncertainty</b> &mdash; the specification the design "
            "must meet, in metres, at the stated confidence level. Leave at 0 to report "
            "without judging.</p>"
            "<p><b>Confidence level</b> &mdash; for the error ellipses, between 0 and 1. "
            "<b>A priori variance factor</b> &mdash; the assumed sigma-nought squared. "
            "<b>Significance</b> and <b>Type II error</b> &mdash; alpha and beta for the "
            "minimal detectable bias; the geodetic defaults 0.001 and 0.20 give the "
            "familiar non-centrality 4.13.</p>"
            "<h3>Outputs</h3>"
            "<p><code>MEETS_TOLERANCE</code>, <code>WORST_STATION</code>, "
            "<code>WORST_UNCERTAINTY</code> in metres, <code>DEGREES_OF_FREEDOM</code> and "
            "<code>UNCHECKABLE_COUNT</code> &mdash; observations no blunder in which could "
            "ever be detected.</p>"
        )

    def initAlgorithm(self, config: dict[str, Any] | None = None) -> None:
        self.addParameter(
            QgsProcessingParameterFile(
                NETWORK, self.tr("Planned network document"), extension="json"
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                FRAME, self.tr("Coordinate frame"), options=frame_labels(), defaultValue=0
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                DATUM,
                self.tr("Datum definition"),
                options=datum_labels(),
                defaultValue=1,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                TOLERANCE,
                self.tr("Required positional uncertainty (m, 0 = do not judge)"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=0.0,
                minValue=0.0,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterString(
                DATUM_STATIONS,
                self.tr("Datum stations (comma-separated; empty = all)"),
                defaultValue="",
                optional=True,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterNumber(
                CONFIDENCE,
                self.tr("Confidence level"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=0.95,
                minValue=0.5,
                maxValue=0.9999,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterNumber(
                VARIANCE_FACTOR,
                self.tr("A priori variance factor"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=1.0,
                minValue=1e-12,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterNumber(
                ALPHA,
                self.tr("Significance for the minimal detectable bias"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=DEFAULT_ALPHA,
                minValue=1e-6,
                maxValue=0.5,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterNumber(
                BETA,
                self.tr("Type II error for the minimal detectable bias"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=DEFAULT_BETA,
                minValue=1e-6,
                maxValue=0.9,
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
        self.addParameter(
            QgsProcessingParameterFileDestination(
                OUTPUT_CSV,
                self.tr("Expected station precision (table)"),
                self.tr("CSV files (*.csv)"),
                optional=True,
                createByDefault=False,
            )
        )

    def processAlgorithm(
        self,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> dict[str, Any]:
        network = load_network(
            self.parameterAsFile(parameters, NETWORK, context), parameter=NETWORK
        )
        frame = frame_of(self.parameterAsEnum(parameters, FRAME, context))
        datum = datum_of(self.parameterAsEnum(parameters, DATUM, context))
        datum_stations = station_list(self.parameterAsString(parameters, DATUM_STATIONS, context))
        tolerance = self.parameterAsDouble(parameters, TOLERANCE, context)
        confidence = self.parameterAsDouble(parameters, CONFIDENCE, context)
        variance_factor = self.parameterAsDouble(parameters, VARIANCE_FACTOR, context)
        alpha = self.parameterAsDouble(parameters, ALPHA, context)
        beta = self.parameterAsDouble(parameters, BETA, context)

        feedback.setProgress(15)
        feedback.pushInfo(self.tr("Simulating the design…"))
        try:
            design = simulate(
                network,
                frame=frame,
                datum=datum,
                datum_stations=datum_stations,
                confidence=confidence,
                variance_factor=variance_factor,
                alpha=alpha,
                beta=beta,
            )
        except GeoCompError as exc:
            from geocomp.services.messages import message_for

            raise QgsProcessingException(message_for(exc)) from exc

        feedback.setProgress(70)
        worst = design.worst_station()
        meets = design.meets(tolerance) if tolerance > 0.0 else True

        self._push_summary(design, worst, tolerance, meets, feedback)

        html_target = self.parameterAsFileOutput(parameters, OUTPUT_HTML, context)
        if html_target:
            with open(html_target, "w", encoding="utf-8") as handle:
                handle.write(
                    self._render(network, frame, datum, design, confidence, tolerance, meets)
                )

        csv_target = self.parameterAsFileOutput(parameters, OUTPUT_CSV, context)
        if csv_target:
            self._write_csv(csv_target, design)

        feedback.setProgress(100)
        return {
            MEETS_TOLERANCE: meets,
            WORST_STATION: worst.station_id if worst else "",
            WORST_UNCERTAINTY: worst.positional_uncertainty if worst else 0.0,
            DEGREES_OF_FREEDOM: design.degrees_of_freedom,
            UNCHECKABLE_COUNT: len(design.reliability.uncheckable),
            OUTPUT_HTML: html_target,
            OUTPUT_CSV: csv_target,
        }

    # -- feedback --------------------------------------------------------

    def _push_summary(self, design, worst, tolerance, meets, feedback) -> None:
        feedback.pushInfo(
            self.tr("Redundancy: %1 (%2 observations, %3 parameters).")
            .replace("%1", str(design.degrees_of_freedom))
            .replace("%2", str(design.observation_count))
            .replace("%3", str(design.parameter_count))
        )
        feedback.pushInfo(self.tr("Datum defect: %1").replace("%1", design.defect_description))

        if worst is not None:
            feedback.pushInfo(
                self.tr("Worst station: %1 at %2 m.")
                .replace("%1", worst.station_id)
                .replace("%2", format_number(worst.positional_uncertainty))
            )

        if tolerance > 0.0 and not meets:
            feedback.pushWarning(
                self.tr("The design does not meet the required %1 m.").replace(
                    "%1", format_number(tolerance)
                )
            )

        note = design.reliability.note()
        if note:
            feedback.pushWarning(note)

    # -- outputs ---------------------------------------------------------

    def _write_csv(self, path: str, design) -> None:
        with open(path, "w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                ["station", "positional_uncertainty", "semi_major", "semi_minor", "azimuth_rad"]
            )
            for station in design.stations:
                writer.writerow(
                    [
                        station.station_id,
                        repr(station.positional_uncertainty),
                        repr(station.ellipse.semi_major),
                        repr(station.ellipse.semi_minor),
                        repr(station.ellipse.orientation),
                    ]
                )

    def _render(self, network, frame, datum, design, confidence, tolerance, meets) -> str:
        summary_rows = [
            [escape(self.tr("Network")), escape(network.id or "—")],
            [escape(self.tr("Coordinate frame")), escape(frame.value)],
            [escape(self.tr("Datum definition")), escape(datum.value)],
            [escape(self.tr("Datum defect")), escape(design.defect_description)],
            [escape(self.tr("Planned observations")), escape(design.observation_count)],
            [escape(self.tr("Parameters")), escape(design.parameter_count)],
            [escape(self.tr("Degrees of freedom")), escape(design.degrees_of_freedom)],
            [escape(self.tr("Confidence level")), escape(format_number(confidence, 3))],
        ]

        body = [
            f"<h2>{escape(self.tr('Design'))}</h2>",
            render_table([escape(self.tr("Property")), escape(self.tr("Value"))], summary_rows),
        ]

        if tolerance > 0.0:
            css = "pass" if meets else "fail"
            text = (
                self.tr("Every station meets the required %1 m.")
                if meets
                else self.tr("At least one station does not meet the required %1 m.")
            ).replace("%1", format_number(tolerance))
            body.append(f'<p class="{css}">{escape(text)}</p>')

        body.append(f"<h2>{escape(self.tr('Expected precision'))}</h2>")
        body.append(
            render_table(
                [
                    escape(self.tr("Station")),
                    escape(self.tr("Positional uncertainty (m)")),
                    escape(self.tr("Semi-major (m)")),
                    escape(self.tr("Semi-minor (m)")),
                    escape(self.tr("Azimuth (rad)")),
                ],
                [
                    [
                        escape(station.station_id),
                        f'<span class="num">{format_number(station.positional_uncertainty)}</span>',
                        format_number(station.ellipse.semi_major),
                        format_number(station.ellipse.semi_minor),
                        format_number(station.ellipse.orientation),
                    ]
                    for station in design.stations
                ],
            )
        )

        body.append(f"<h2>{escape(self.tr('Expected reliability'))}</h2>")
        body.append(
            render_note(
                self.tr(
                    "The minimal detectable bias is the smallest blunder the design could "
                    "find in an observation, at the stated significance and power."
                )
            )
        )
        body.append(
            render_table(
                [
                    escape(self.tr("Observation")),
                    escape(self.tr("Component")),
                    escape(self.tr("Redundancy")),
                    escape(self.tr("Minimal detectable bias")),
                    escape(self.tr("External effect (m)")),
                ],
                [
                    [
                        escape(result.observation_id),
                        escape(result.component),
                        format_number(result.redundancy, 3),
                        format_number(result.minimal_detectable_bias),
                        format_number(result.external_effect),
                    ]
                    for result in design.reliability.results
                ],
            )
        )

        note = design.reliability.note()
        if note:
            body.append(render_note(note, label=self.tr("Warning")))

        return render_document(
            self.tr("Network pre-analysis report"),
            body,
            footer=escape(self.tr("Generated by GeoComp — geocomp:analysis_network_preanalysis")),
        )
