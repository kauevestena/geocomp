# SPDX-License-Identifier: GPL-2.0-or-later
"""``geocomp:levelling_equal_sights`` -- reduce levelling lines (FR-500).

``specs/10-module-levelling.md`` section 2.1.

Equal sight lengths cancel, to first order, the collimation error of the
instrument and the effects of curvature and refraction. **The number that
decides how much actually cancelled is the imbalance accumulated over the line,
not the imbalance of any one setup**: per-setup imbalances of opposite sign
cancel each other, and it is their sum that multiplies the collimation.

A line is therefore reduced as a whole, with the collimation carried through one
shared column. The consequence is worth stating: on a balanced line the
collimation contributes neither a correction nor an *uncertainty*, whatever its
value and whatever its own uncertainty. That is the mathematical form of "equal
sights is the preferred method".
"""

from __future__ import annotations

import csv
from typing import Any

from qgis.core import (
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingParameterFile,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
)

from geocomp.algorithms.base import GeoCompAlgorithm
from geocomp.algorithms.levelling.common import (
    findings_table,
    level_from_parameters,
    read_lines,
    reduction_to_dict,
    summarise_findings,
    write_document,
)
from geocomp.algorithms.reporting import (
    escape,
    exact,
    format_number,
    render_document,
    render_note,
    render_table,
)
from geocomp.core.errors import GeoCompError
from geocomp.core.techniques.levelling import reduce_line

__all__ = ["EqualSightsAlgorithm"]

SETUPS = "SETUPS"
PROFILES = "PROFILES"
LEVEL_ID = "LEVEL_ID"
COLLIMATION = "COLLIMATION"
COLLIMATION_SIGMA = "COLLIMATION_SIGMA"
MAX_SIGHT_LENGTH = "MAX_SIGHT_LENGTH"
MAX_SIGHT_IMBALANCE = "MAX_SIGHT_IMBALANCE"
MAX_ACCUMULATED_IMBALANCE = "MAX_ACCUMULATED_IMBALANCE"
OUTPUT_REDUCTIONS = "OUTPUT_REDUCTIONS"
OUTPUT_HTML = "OUTPUT_HTML"
OUTPUT_CSV = "OUTPUT_CSV"
LINE_COUNT = "LINE_COUNT"
WORST_IMBALANCE = "WORST_IMBALANCE"
WORST_UNCERTAINTY = "WORST_UNCERTAINTY"


class EqualSightsAlgorithm(GeoCompAlgorithm):
    """Reduce levelling lines, with the sight-balance check and collimation."""

    TR_CONTEXT = "EqualSightsAlgorithm"

    def displayName(self) -> str:
        return self.tr("Equal sights")

    def shortDescription(self) -> str:
        return self.tr(
            "Reduce levelling lines to height differences, with the balance check."
        )

    def help_body(self) -> str:
        return self.tr(
            "<p>Reduces each levelling line to one height difference between its two end "
            "marks, propagating the uncertainty of every staff reading.</p>"
            "<p><b>Equal sights is the preferred method</b> because equal backsight and "
            "foresight lengths cancel, to first order, the instrument's collimation error "
            "and the effects of curvature and refraction. GeoComp checks the balance and "
            "reports the <b>accumulated</b> imbalance, which is the figure that actually "
            "matters: imbalances of opposite sign at successive setups cancel each other, "
            "and it is their sum that multiplies the collimation.</p>"
            "<p>The line is reduced as a whole, with the collimation carried once rather "
            "than per setup. So on a balanced line the collimation contributes neither a "
            "correction nor an uncertainty &mdash; whatever its value, and whatever its own "
            "uncertainty. On an imbalanced line it contributes both, and the report shows "
            "the raw and corrected differences side by side.</p>"
            "<p>A setup carrying more than one foresight has its extra points reported as "
            "side shots. They are correlated with each other through the shared backsight; "
            "use <b>Extreme sights</b> when that correlation matters.</p>"
            "<h3>Parameters</h3>"
            "<p><b>Setups</b> &mdash; the document the importer produced.</p>"
            "<p><b>Instrument profiles</b>, <b>level id</b>, <b>collimation</b> (rad) and "
            "its <b>uncertainty</b> &mdash; where the two-peg test result comes from. A "
            "collimation given here overrides the profile's, because a test done this "
            "morning beats a profile written last year. With no collimation at all, no "
            "correction is applied and the imbalance is reported instead.</p>"
            "<p><b>Longest sight</b>, <b>largest imbalance per setup</b> and <b>largest "
            "imbalance per line</b> (m) &mdash; limits from the specification the work is "
            "under. Zero disables a check.</p>"
            "<h3>Outputs</h3>"
            "<p><b>Reduced lines</b> &mdash; JSON, the input to Closures and to Network "
            "adjustment. <b>Report</b> &mdash; HTML. <b>Lines</b> &mdash; CSV. Scalars: "
            "<code>LINE_COUNT</code>, <code>WORST_IMBALANCE</code> and "
            "<code>WORST_UNCERTAINTY</code> in metres.</p>"
        )

    def initAlgorithm(self, config: dict[str, Any] | None = None) -> None:
        self.addParameter(
            QgsProcessingParameterFile(SETUPS, self.tr("Setups"), extension="json")
        )
        self.addParameter(
            QgsProcessingParameterFile(
                PROFILES, self.tr("Instrument profiles"), extension="json", optional=True
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterString(
                LEVEL_ID, self.tr("Level id"), defaultValue="", optional=True
            )
        )
        for name, label, maximum in (
            (COLLIMATION, self.tr("Collimation (rad)"), 0.01),
            (COLLIMATION_SIGMA, self.tr("Collimation uncertainty (rad)"), 0.01),
        ):
            self.addAdvancedParameter(
                QgsProcessingParameterNumber(
                    name,
                    label,
                    type=QgsProcessingParameterNumber.Type.Double,
                    defaultValue=0.0,
                    minValue=-maximum if name == COLLIMATION else 0.0,
                    maxValue=maximum,
                )
            )
        for name, label, maximum in (
            (MAX_SIGHT_LENGTH, self.tr("Longest sight (m)"), 500.0),
            (MAX_SIGHT_IMBALANCE, self.tr("Largest imbalance per setup (m)"), 100.0),
            (MAX_ACCUMULATED_IMBALANCE, self.tr("Largest imbalance per line (m)"), 1000.0),
        ):
            self.addParameter(
                QgsProcessingParameterNumber(
                    name,
                    label,
                    type=QgsProcessingParameterNumber.Type.Double,
                    defaultValue=0.0,
                    minValue=0.0,
                    maxValue=maximum,
                )
            )
        for name, label, filter_text, by_default in (
            (
                OUTPUT_REDUCTIONS,
                self.tr("Reduced lines"),
                self.tr("GeoComp levelling reductions (*.json)"),
                True,
            ),
            (OUTPUT_HTML, self.tr("Report"), self.tr("HTML files (*.html)"), True),
            (OUTPUT_CSV, self.tr("Lines"), self.tr("CSV files (*.csv)"), False),
        ):
            self.addParameter(
                QgsProcessingParameterFileDestination(
                    name, label, filter_text, optional=True, createByDefault=by_default
                )
            )

    def processAlgorithm(
        self,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> dict[str, Any]:
        lines = read_lines(self.parameterAsFile(parameters, SETUPS, context))
        level = level_from_parameters(
            profiles=self.parameterAsFile(parameters, PROFILES, context),
            level_id=self.parameterAsString(parameters, LEVEL_ID, context),
            collimation=self.parameterAsDouble(parameters, COLLIMATION, context),
            collimation_sigma=self.parameterAsDouble(parameters, COLLIMATION_SIGMA, context),
        )
        limits = {
            "max_sight_length": self.parameterAsDouble(
                parameters, MAX_SIGHT_LENGTH, context
            ),
            "max_sight_imbalance": self.parameterAsDouble(
                parameters, MAX_SIGHT_IMBALANCE, context
            ),
            "max_accumulated_imbalance": self.parameterAsDouble(
                parameters, MAX_ACCUMULATED_IMBALANCE, context
            ),
        }

        feedback.setProgress(20)
        try:
            reductions = [reduce_line(line, level, **limits) for line in lines]
        except GeoCompError as exc:
            from geocomp.services.messages import message_for

            raise QgsProcessingException(message_for(exc)) from exc

        findings = tuple(f for reduction in reductions for f in reduction.findings)
        blocking, warnings = summarise_findings(findings, feedback)

        feedback.setProgress(70)
        write_document(
            self.parameterAsFileOutput(parameters, OUTPUT_REDUCTIONS, context),
            {
                "kind": "levelling_reductions",
                "level_id": level.id,
                "lines": [reduction_to_dict(reduction) for reduction in reductions],
            },
        )
        self._write_report(parameters, context, reductions, findings, level)
        self._write_csv(parameters, context, reductions)
        feedback.setProgress(100)

        imbalances = [
            abs(reduction.accumulated_imbalance)
            for reduction in reductions
            if reduction.accumulated_imbalance is not None
        ]
        return {
            LINE_COUNT: len(reductions),
            WORST_IMBALANCE: max(imbalances) if imbalances else 0.0,
            WORST_UNCERTAINTY: max(
                reduction.height_difference.std_dev for reduction in reductions
            ),
            OUTPUT_REDUCTIONS: self.parameterAsFileOutput(
                parameters, OUTPUT_REDUCTIONS, context
            ),
            OUTPUT_HTML: self.parameterAsFileOutput(parameters, OUTPUT_HTML, context),
            OUTPUT_CSV: self.parameterAsFileOutput(parameters, OUTPUT_CSV, context),
            "BLOCKING": blocking,
            "WARNINGS": warnings,
        }

    # -- outputs ---------------------------------------------------------

    def _rows(self, reductions) -> list[list[str]]:
        rows = []
        for reduction in reductions:
            imbalance = reduction.accumulated_imbalance
            correction = reduction.collimation
            rows.append(
                [
                    escape(reduction.line_id),
                    escape(reduction.from_station),
                    escape(reduction.to_station),
                    str(reduction.setup_count),
                    format_number(reduction.length_km, 4)
                    if reduction.length_km is not None
                    else "—",
                    format_number(imbalance, 2) if imbalance is not None else "—",
                    format_number(reduction.raw_height_difference.value, 5),
                    format_number(correction.value * 1000.0, 3) if correction else "—",
                    format_number(reduction.height_difference.value, 5),
                    format_number(reduction.height_difference.std_dev * 1000.0, 3),
                ]
            )
        return rows

    def _write_report(self, parameters, context, reductions, findings, level) -> None:
        path = self.parameterAsFileOutput(parameters, OUTPUT_HTML, context)
        if not path:
            return

        table = render_table(
            [
                escape(self.tr("Line")),
                escape(self.tr("From")),
                escape(self.tr("To")),
                escape(self.tr("Setups")),
                escape(self.tr("Length (km)")),
                escape(self.tr("Accumulated imbalance (m)")),
                escape(self.tr("Raw dH (m)")),
                escape(self.tr("Collimation (mm)")),
                escape(self.tr("dH (m)")),
                escape(self.tr("Uncertainty (mm)")),
            ],
            self._rows(reductions),
        )

        balanced = [reduction for reduction in reductions if reduction.is_balanced]
        body = [
            f"<h2>{escape(self.tr('Reduced lines'))}</h2>",
            table,
            render_note(
                self.tr(
                    "Reduced with level profile '%1'. The collimation is carried once over "
                    "each whole line, so a balanced line takes neither a correction nor an "
                    "uncertainty from it."
                ).replace("%1", level.label),
                label=self.tr("Instrument"),
            ),
        ]
        if balanced:
            body.append(
                render_note(
                    self.tr(
                        "%1 line(s) are exactly balanced. On those the collimation error "
                        "does not enter the result at all, whatever its value."
                    ).replace("%1", str(len(balanced))),
                    label=self.tr("Balance"),
                )
            )

        side_shots = [
            shot for reduction in reductions for shot in reduction.side_shots
        ]
        if side_shots:
            body.append(f"<h2>{escape(self.tr('Side shots'))}</h2>")
            body.append(
                render_table(
                    [
                        escape(self.tr("Setup")),
                        escape(self.tr("From")),
                        escape(self.tr("To")),
                        escape(self.tr("dH (m)")),
                        escape(self.tr("Uncertainty (mm)")),
                    ],
                    [
                        [
                            escape(shot.setup_id),
                            escape(shot.from_station),
                            escape(shot.to_station),
                            format_number(shot.height_difference.value, 5),
                            format_number(shot.height_difference.std_dev * 1000.0, 3),
                        ]
                        for shot in side_shots
                    ],
                )
            )
            body.append(
                render_note(
                    self.tr(
                        "Side shots are levelled from a line's setup without the line "
                        "passing through them. A point observed once has no redundancy, so "
                        "it is not adjusted; use Extreme sights when the correlation "
                        "between several such points matters."
                    ),
                    label=self.tr("Side shots"),
                )
            )

        body.append(f"<h2>{escape(self.tr('Findings'))}</h2>")
        body.append(findings_table(findings))
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(render_document(self.tr("Levelling: equal sights"), body))

    def _write_csv(self, parameters, context, reductions) -> None:
        path = self.parameterAsFileOutput(parameters, OUTPUT_CSV, context)
        if not path:
            return
        with open(path, "w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                [
                    "line",
                    "from",
                    "to",
                    "setups",
                    "length_km",
                    "accumulated_imbalance_m",
                    "raw_height_difference_m",
                    "collimation_correction_m",
                    "height_difference_m",
                    "std_dev_m",
                ]
            )
            for reduction in reductions:
                writer.writerow(
                    [
                        reduction.line_id,
                        reduction.from_station,
                        reduction.to_station,
                        reduction.setup_count,
                        exact(reduction.length_km),
                        exact(reduction.accumulated_imbalance),
                        exact(reduction.raw_height_difference.value),
                        exact(reduction.collimation.value if reduction.collimation else None),
                        exact(reduction.height_difference.value),
                        exact(reduction.height_difference.std_dev),
                    ]
                )
