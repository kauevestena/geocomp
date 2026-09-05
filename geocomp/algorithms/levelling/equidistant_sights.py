# SPDX-License-Identifier: GPL-2.0-or-later
"""``geocomp:levelling_equidistant_sights`` -- crossing an obstacle (FR-501).

``specs/10-module-levelling.md`` section 2.2.

The scheme for crossing a river, where an equal-sight setup is impossible. Each
bank observes both staves; what does not cancel geometrically cancels by
symmetry instead, because the long sight's error enters the two determinations
with opposite sign.

**The uncertainty is deliberately conservative and says so.** Refraction across
water varies rapidly and asymmetrically, and the two reciprocal observations were
not simultaneous, so the symmetry the method relies on holds only approximately.
The propagated variance is multiplied by a configurable factor and the result is
marked as an empirical scaling, which carries into every report that uses it.
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
)

from geocomp.algorithms.base import GeoCompAlgorithm
from geocomp.algorithms.levelling.common import (
    findings_table,
    read_lines,
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
from geocomp.core.techniques.levelling import reduce_reciprocal
from geocomp.core.techniques.levelling.schemes import ReciprocalPair

__all__ = ["EquidistantSightsAlgorithm"]

SETUPS = "SETUPS"
INFLATION = "INFLATION"
DISCREPANCY_TOLERANCE = "DISCREPANCY_TOLERANCE"
OUTPUT_DIFFERENCES = "OUTPUT_DIFFERENCES"
OUTPUT_HTML = "OUTPUT_HTML"
OUTPUT_CSV = "OUTPUT_CSV"
CROSSING_COUNT = "CROSSING_COUNT"
WORST_DISCREPANCY = "WORST_DISCREPANCY"


class EquidistantSightsAlgorithm(GeoCompAlgorithm):
    """Reciprocal observations from both banks of an obstacle."""

    TR_CONTEXT = "EquidistantSightsAlgorithm"

    def displayName(self) -> str:
        return self.tr("Equidistant sights")

    def shortDescription(self) -> str:
        return self.tr("Reciprocal levelling across an obstacle, from both banks.")

    def help_body(self) -> str:
        return self.tr(
            "<p>Combines reciprocal observations across an obstacle &mdash; a river is the "
            "case the proposal names &mdash; where an equal-sight setup is impossible.</p>"
            "<p>Each bank's instrument reads the staff on its own side over a short sight "
            "and the staff across the water over a long one. The long sight carries almost "
            "all of the error, and it enters the two determinations with <b>opposite "
            "sign</b>, so it cancels in their mean. That cancellation is the method.</p>"
            "<p><b>The uncertainty is deliberately more conservative than for equal "
            "sights.</b> Refraction over water varies rapidly and asymmetrically, and the "
            "two observations were not simultaneous, so the symmetry the method relies on "
            "holds only approximately. The propagated variance is multiplied by the "
            "inflation factor and the result is marked as an empirical scaling, which "
            "follows it into every report. Setting the factor to one is allowed and is "
            "reported as a warning, because it claims the two observations saw identical "
            "air.</p>"
            "<p>The two determinations' <b>discrepancy</b> is reported. Its expected value "
            "is zero; a large one says the refraction changed between them, which is "
            "precisely the assumption the method makes, so it is shown rather than averaged "
            "away.</p>"
            "<h3>Input layout</h3>"
            "<p>Each crossing is <b>two setups</b> in the imported book, each with one "
            "backsight (the near staff) and one foresight (the far staff), and the second "
            "setup observes the same two stations the other way round. Setups are paired in "
            "the order they appear.</p>"
            "<h3>Parameters</h3>"
            "<p><b>Setups</b> &mdash; the document the importer produced. <b>Variance "
            "inflation</b> &mdash; at least one. <b>Discrepancy tolerance</b> (m) &mdash; "
            "above which the two banks' disagreement is reported; zero disables it.</p>"
            "<h3>Outputs</h3>"
            "<p><b>Height differences</b> &mdash; JSON. <b>Report</b> &mdash; HTML. "
            "<b>Crossings</b> &mdash; CSV. Scalars: <code>CROSSING_COUNT</code> and "
            "<code>WORST_DISCREPANCY</code> in metres.</p>"
        )

    def initAlgorithm(self, config: dict[str, Any] | None = None) -> None:
        self.addParameter(
            QgsProcessingParameterFile(SETUPS, self.tr("Setups"), extension="json")
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                INFLATION,
                self.tr("Variance inflation"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=2.0,
                minValue=1.0,
                maxValue=100.0,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                DISCREPANCY_TOLERANCE,
                self.tr("Discrepancy tolerance (m)"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=0.005,
                minValue=0.0,
                maxValue=10.0,
            )
        )
        for name, label, filter_text, by_default in (
            (
                OUTPUT_DIFFERENCES,
                self.tr("Height differences"),
                self.tr("GeoComp height differences (*.json)"),
                True,
            ),
            (OUTPUT_HTML, self.tr("Report"), self.tr("HTML files (*.html)"), True),
            (OUTPUT_CSV, self.tr("Crossings"), self.tr("CSV files (*.csv)"), False),
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
        setups = [setup for line in lines for setup in line.setups]
        if len(setups) < 2 or len(setups) % 2:
            raise QgsProcessingException(
                self.tr(
                    "A reciprocal crossing is two setups, one from each bank, so the book "
                    "must hold an even number of at least two. It holds %1."
                ).replace("%1", str(len(setups)))
            )
        for setup in setups:
            if setup.is_extreme_sights:
                raise QgsProcessingException(
                    self.tr(
                        "Setup '%1' carries several foresights. A reciprocal crossing has "
                        "one near staff and one far staff per bank."
                    ).replace("%1", setup.id)
                )

        inflation = self.parameterAsDouble(parameters, INFLATION, context)
        tolerance = self.parameterAsDouble(parameters, DISCREPANCY_TOLERANCE, context)

        feedback.setProgress(30)
        results = []
        try:
            for first, second in zip(setups[0::2], setups[1::2], strict=True):
                results.append(
                    reduce_reciprocal(
                        ReciprocalPair(
                            setup_id=first.id,
                            near=first.backsight,
                            far=first.foresights[0],
                        ),
                        ReciprocalPair(
                            setup_id=second.id,
                            near=second.backsight,
                            far=second.foresights[0],
                        ),
                        variance_inflation=inflation,
                        discrepancy_tolerance=tolerance,
                    )
                )
        except GeoCompError as exc:
            from geocomp.services.messages import message_for

            raise QgsProcessingException(message_for(exc)) from exc

        findings = tuple(f for result in results for f in result.findings)
        blocking, warnings = summarise_findings(findings, feedback)

        feedback.setProgress(70)
        write_document(
            self.parameterAsFileOutput(parameters, OUTPUT_DIFFERENCES, context),
            {
                "kind": "levelling_reciprocal",
                "inflation": inflation,
                "crossings": [
                    {
                        "from_station": result.from_station,
                        "to_station": result.to_station,
                        "height_difference": result.height_difference.to_dict(),
                        "forward": result.forward.to_dict(),
                        "reverse": result.reverse.to_dict(),
                        "discrepancy": result.discrepancy,
                        "inflation": result.inflation,
                    }
                    for result in results
                ],
            },
        )
        self._write_report(parameters, context, results, findings, inflation)
        self._write_csv(parameters, context, results)
        feedback.setProgress(100)

        return {
            CROSSING_COUNT: len(results),
            WORST_DISCREPANCY: max(abs(result.discrepancy) for result in results),
            OUTPUT_DIFFERENCES: self.parameterAsFileOutput(
                parameters, OUTPUT_DIFFERENCES, context
            ),
            OUTPUT_HTML: self.parameterAsFileOutput(parameters, OUTPUT_HTML, context),
            OUTPUT_CSV: self.parameterAsFileOutput(parameters, OUTPUT_CSV, context),
            "BLOCKING": blocking,
            "WARNINGS": warnings,
        }

    def _write_report(self, parameters, context, results, findings, inflation) -> None:
        path = self.parameterAsFileOutput(parameters, OUTPUT_HTML, context)
        if not path:
            return

        body = [
            f"<h2>{escape(self.tr('Crossings'))}</h2>",
            render_table(
                [
                    escape(self.tr("From")),
                    escape(self.tr("To")),
                    escape(self.tr("From the near bank (m)")),
                    escape(self.tr("From the far bank (m)")),
                    escape(self.tr("Mean dH (m)")),
                    escape(self.tr("Discrepancy (mm)")),
                    escape(self.tr("Uncertainty (mm)")),
                ],
                [
                    [
                        escape(result.from_station),
                        escape(result.to_station),
                        format_number(result.forward.value, 5),
                        format_number(result.reverse.value, 5),
                        format_number(result.height_difference.value, 5),
                        format_number(result.discrepancy * 1000.0, 2),
                        format_number(result.height_difference.std_dev * 1000.0, 3),
                    ]
                    for result in results
                ],
            ),
            render_note(
                self.tr(
                    "The variance was multiplied by %1 and the result marked as an "
                    "empirical scaling. Refraction over water varies rapidly and "
                    "asymmetrically, and the two reciprocal observations were not "
                    "simultaneous."
                ).replace("%1", format_number(inflation, 2)),
                label=self.tr("Uncertainty model"),
            ),
            render_note(
                self.tr(
                    "The discrepancy is the two banks' disagreement. Its expected value is "
                    "zero; a large one says the refraction changed between the two "
                    "observations, which is the assumption the method rests on."
                ),
                label=self.tr("Discrepancy"),
            ),
            f"<h2>{escape(self.tr('Findings'))}</h2>",
            findings_table(findings),
        ]
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(render_document(self.tr("Levelling: equidistant sights"), body))

    def _write_csv(self, parameters, context, results) -> None:
        path = self.parameterAsFileOutput(parameters, OUTPUT_CSV, context)
        if not path:
            return
        with open(path, "w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                [
                    "from",
                    "to",
                    "forward_m",
                    "reverse_m",
                    "height_difference_m",
                    "discrepancy_m",
                    "std_dev_m",
                    "variance_inflation",
                ]
            )
            for result in results:
                writer.writerow(
                    [
                        result.from_station,
                        result.to_station,
                        exact(result.forward.value),
                        exact(result.reverse.value),
                        exact(result.height_difference.value),
                        exact(result.discrepancy),
                        exact(result.height_difference.std_dev),
                        exact(result.inflation),
                    ]
                )
