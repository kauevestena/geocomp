# SPDX-License-Identifier: GPL-2.0-or-later
"""``geocomp:analysis_network_inspect`` -- check a network before adjusting it.

FR-273. ``specs/06-adjustment-core.md`` section 5.2.

The problems this catches otherwise surface as a singular normal matrix twenty
seconds into an adjustment, with a message about rank rather than about the two
halves of the network that share no observation. Running it first is cheap; it
needs no adjustment and no approximate coordinates.

**It reports every problem at once rather than stopping at the first** (FR-166).
A network with six disconnected pieces should say so once, not six times across
six runs.

Distinct from pre-analysis, which is design simulation on a network that does
not exist yet -- the archived roadmap conflated the two
(``specs/archive/README.md`` item 6).
"""

from __future__ import annotations

import csv
from typing import Any

from qgis.core import (
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFile,
    QgsProcessingParameterFileDestination,
)

from geocomp.algorithms.analysis.common import (
    escape,
    frame_labels,
    frame_of,
    load_network,
    render_document,
    render_note,
    render_table,
)
from geocomp.algorithms.base import GeoCompAlgorithm
from geocomp.core.preanalysis.inspection import Severity, inspect

__all__ = ["NetworkInspectAlgorithm"]

NETWORK = "NETWORK"
FRAME = "FRAME"
FAIL_ON_BLOCKING = "FAIL_ON_BLOCKING"
OUTPUT_HTML = "OUTPUT_HTML"
OUTPUT_CSV = "OUTPUT_CSV"
CAN_ADJUST = "CAN_ADJUST"
BLOCKING_COUNT = "BLOCKING_COUNT"
WARNING_COUNT = "WARNING_COUNT"
COMPONENT_COUNT = "COMPONENT_COUNT"


class NetworkInspectAlgorithm(GeoCompAlgorithm):
    """Connectivity, isolated stations, duplicates and missing coordinates."""

    TR_CONTEXT = "NetworkInspectAlgorithm"

    def displayName(self) -> str:
        return self.tr("Inspect network")

    def shortDescription(self) -> str:
        return self.tr("Check a network for the problems that block or distort an adjustment.")

    def help_body(self) -> str:
        return self.tr(
            "<p>Checks a geodetic network for the problems that stop an adjustment or make "
            "its result mean something other than what the user expects: stations that take "
            "part in no observation, a network that falls into disconnected pieces each with "
            "its own datum, observation types the in-house adjustment does not implement, "
            "observations that cannot contribute to the chosen dimensionality, repeated "
            "observations, and missing approximate coordinates.</p>"
            "<p>Findings are graded. <b>Blocking</b> means the adjustment cannot run. "
            "<b>Warning</b> means it can, but the result may not mean what you expect. "
            "<b>Information</b> is worth seeing and is not a problem.</p>"
            "<p>Every finding is reported in one pass, so a network with several problems "
            "needs one run rather than one run per problem.</p>"
            "<h3>Parameters</h3>"
            "<p><b>Network</b> &mdash; a GeoComp network document (JSON).</p>"
            "<p><b>Coordinate frame</b> &mdash; which of 1D, 2D and 3D the network is to be "
            "adjusted in. It decides which observations can contribute and how many "
            "observations a station needs.</p>"
            "<p><b>Fail if the network cannot be adjusted</b> &mdash; when set, a blocking "
            "finding stops the algorithm, so a model that chains inspect into adjust does "
            "not proceed on a network that cannot be adjusted. When unset, the algorithm "
            "always succeeds and reports its findings, which is what an interactive check "
            "wants.</p>"
            "<p><b>Report</b> &mdash; destination HTML file. <b>Findings table</b> &mdash; "
            "destination CSV, one row per finding, for use in a model or a spreadsheet.</p>"
            "<h3>Outputs</h3>"
            "<p><code>CAN_ADJUST</code> (boolean), <code>BLOCKING_COUNT</code>, "
            "<code>WARNING_COUNT</code> and <code>COMPONENT_COUNT</code> &mdash; the number "
            "of connected pieces, which is 1 for a network that hangs together.</p>"
        )

    def initAlgorithm(self, config: dict[str, Any] | None = None) -> None:
        self.addParameter(
            QgsProcessingParameterFile(
                NETWORK,
                self.tr("Network document"),
                extension="json",
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                FRAME,
                self.tr("Coordinate frame"),
                options=frame_labels(),
                defaultValue=0,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterBoolean(
                FAIL_ON_BLOCKING,
                self.tr("Fail if the network cannot be adjusted"),
                defaultValue=False,
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
                self.tr("Findings table"),
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

        feedback.setProgress(20)
        feedback.pushInfo(
            self.tr("Inspecting network '%1'…").replace(
                "%1", network.id or self.tr("(unnamed)")
            )
        )
        report = inspect(network, frame=frame)

        feedback.setProgress(60)
        self._push_findings(report, feedback)

        html_target = self.parameterAsFileOutput(parameters, OUTPUT_HTML, context)
        if html_target:
            with open(html_target, "w", encoding="utf-8") as handle:
                handle.write(self._render(network, frame, report))

        csv_target = self.parameterAsFileOutput(parameters, OUTPUT_CSV, context)
        if csv_target:
            self._write_csv(csv_target, report)

        feedback.setProgress(100)

        if not report.can_adjust and self.parameterAsBool(
            parameters, FAIL_ON_BLOCKING, context
        ):
            from qgis.core import QgsProcessingException

            raise QgsProcessingException(
                self.tr(
                    "The network has %1 blocking problem(s) and cannot be adjusted."
                ).replace("%1", str(len(report.blocking)))
            )

        return {
            CAN_ADJUST: report.can_adjust,
            BLOCKING_COUNT: len(report.blocking),
            WARNING_COUNT: len(report.warnings),
            COMPONENT_COUNT: len(report.components),
            OUTPUT_HTML: html_target,
            OUTPUT_CSV: csv_target,
        }

    # -- feedback --------------------------------------------------------

    def _push_findings(self, report, feedback: QgsProcessingFeedback) -> None:
        """Blocking findings as warnings, the rest as information.

        A blocking finding goes through ``pushWarning`` so it is visible in the
        log even when the run is allowed to succeed; silently returning
        ``CAN_ADJUST = false`` would let a model proceed on a network nobody
        looked at.
        """
        for finding in report.findings:
            line = f"[{finding.code}] {finding.message}"
            if finding.severity is Severity.BLOCKING:
                feedback.pushWarning(line)
            else:
                feedback.pushInfo(line)

        if not report.findings:
            feedback.pushInfo(self.tr("No problems found."))

        feedback.pushInfo(
            self.tr("%1 station(s), %2 observation(s), %3 active.")
            .replace("%1", str(report.station_count))
            .replace("%2", str(report.observation_count))
            .replace("%3", str(report.active_observation_count))
        )

    # -- outputs ---------------------------------------------------------

    def _write_csv(self, path: str, report) -> None:
        with open(path, "w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["code", "severity", "message", "stations", "observations"])
            for finding in report.findings:
                writer.writerow(
                    [
                        finding.code,
                        finding.severity.value,
                        finding.message,
                        " ".join(finding.stations),
                        " ".join(finding.observations),
                    ]
                )

    def _render(self, network, frame, report) -> str:
        severity_labels = {
            Severity.BLOCKING: (self.tr("Blocking"), "blocking"),
            Severity.WARNING: (self.tr("Warning"), "warning"),
            Severity.INFO: (self.tr("Information"), ""),
        }

        summary_rows = [
            [escape(self.tr("Network")), escape(network.id or "—")],
            [escape(self.tr("Coordinate frame")), escape(frame.value)],
            [escape(self.tr("Stations")), escape(report.station_count)],
            [escape(self.tr("Observations")), escape(report.observation_count)],
            [escape(self.tr("Active observations")), escape(report.active_observation_count)],
            [escape(self.tr("Connected pieces")), escape(len(report.components))],
        ]

        if report.can_adjust:
            verdict = f'<p class="pass">{escape(self.tr("The network can be adjusted."))}</p>'
        else:
            message = self.tr("The network cannot be adjusted as it stands.")
            verdict = f'<p class="fail">{escape(message)}</p>'

        body = [
            f"<h2>{escape(self.tr('Summary'))}</h2>",
            render_table([escape(self.tr("Property")), escape(self.tr("Value"))], summary_rows),
            verdict,
            f"<h2>{escape(self.tr('Findings'))}</h2>",
        ]

        if report.findings:
            rows = []
            for finding in report.findings:
                label, css = severity_labels[finding.severity]
                marker = f'<span class="{css}">{escape(label)}</span>' if css else escape(label)
                rows.append(
                    [
                        marker,
                        f"<code>{escape(finding.code)}</code>",
                        escape(finding.message),
                        escape(", ".join(finding.stations + finding.observations)) or "—",
                    ]
                )
            body.append(
                render_table(
                    [
                        escape(self.tr("Severity")),
                        escape(self.tr("Code")),
                        escape(self.tr("Finding")),
                        escape(self.tr("Involves")),
                    ],
                    rows,
                )
            )
        else:
            body.append(f"<p>{escape(self.tr('No problems found.'))}</p>")

        if not report.is_connected:
            pieces = [
                [escape(index + 1), escape(len(members)), escape(", ".join(members))]
                for index, members in enumerate(report.components)
            ]
            body.extend(
                [
                    f"<h2>{escape(self.tr('Connected pieces'))}</h2>",
                    render_note(
                        self.tr(
                            "Each piece has its own datum. They cannot be adjusted together "
                            "until an observation joins them."
                        )
                    ),
                    render_table(
                        [
                            escape(self.tr("Piece")),
                            escape(self.tr("Stations")),
                            escape(self.tr("Members")),
                        ],
                        pieces,
                    ),
                ]
            )

        return render_document(
            self.tr("Network inspection report"),
            body,
            footer=escape(self.tr("Generated by GeoComp — geocomp:analysis_network_inspect")),
        )
