# SPDX-License-Identifier: GPL-2.0-or-later
"""``geocomp:analysis_dynadjust_compare`` -- two solutions of one network.

``specs/07-engine-dynadjust.md`` section 6. This is phase P6's exit criterion
made available to a user: the in-house core and DynAdjust are independent
implementations of the same least-squares problem, so agreement is evidence
about both, and a disagreement is a real finding about one of them.

It compares two solution documents, whatever produced them. Two DynAdjust runs
with different options, or the same network before and after a change to the
stochastic model, compare on the same terms -- the algorithm has no notion of
which engine is which and does not need one, because both fill the same
structure (FR-323).

**Coordinates are compared only when both solutions are in the same frame.**
Differencing a geocentric X against a projected easting produces a number, and
the number means nothing; so a frame mismatch is reported as not compared, with
both frames named, rather than silently done or silently skipped.
"""

from __future__ import annotations

import json
from pathlib import Path
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
from geocomp.core.errors import GeoCompError
from geocomp.core.models.solution import Solution
from geocomp.engines.dynadjust.crossvalidation import compare

__all__ = ["DynAdjustCompareAlgorithm"]

REFERENCE = "REFERENCE"
OTHER = "OTHER"
COORDINATE_TOLERANCE = "COORDINATE_TOLERANCE"
VARIANCE_TOLERANCE = "VARIANCE_TOLERANCE"
OUTPUT_REPORT = "OUTPUT_REPORT"
OUTPUT_JSON = "OUTPUT_JSON"
AGREES = "AGREES"
LARGEST_COORDINATE_DIFFERENCE = "LARGEST_COORDINATE_DIFFERENCE"
LARGEST_RESIDUAL_DIFFERENCE = "LARGEST_RESIDUAL_DIFFERENCE"
DISAGREEMENT_COUNT = "DISAGREEMENT_COUNT"


class DynAdjustCompareAlgorithm(GeoCompAlgorithm):
    """Compare two solutions of one network, quantity by quantity."""

    TR_CONTEXT = "DynAdjustCompareAlgorithm"

    def displayName(self) -> str:
        return self.tr("Compare two solutions")

    def shortDescription(self) -> str:
        return self.tr(
            "Cross-validate two adjustments of the same network, whichever engines produced them."
        )

    def help_body(self) -> str:
        return self.tr(
            "<p>Compares two solution documents of the same network and reports, quantity "
            "by quantity, where they agree and where they do not.</p>"
            "<p>Its first purpose is cross-validating GeoComp's own least-squares core "
            "against <b>DynAdjust</b>: two independent implementations of the same problem, "
            "so agreement is evidence about both and a disagreement is a real finding about "
            "one of them. It is not limited to that. Any two solutions compare on the same "
            "terms &mdash; the same network adjusted with a different stochastic model, or "
            "before and after an observation was rejected &mdash; because every engine "
            "fills the same structure.</p>"
            "<h3>What is compared</h3>"
            "<p><b>Degrees of freedom, observation count and parameter count</b> must match "
            "<i>exactly</i>. They are properties of the model rather than of the arithmetic, "
            "so a difference means the two solved different problems &mdash; and comparing "
            "residuals after that would be meaningless.</p>"
            "<p><b>The variance factor</b> is compared relatively, because an absolute "
            "tolerance is wrong at both ends: it is a large error on a variance factor of "
            "0.001 and negligible on one of 100.</p>"
            "<p><b>Coordinates</b>, per station, as the largest difference over the three "
            "components &mdash; but only when both solutions are in the same frame. "
            "Differencing a geocentric X against a projected easting produces a number, and "
            "the number means nothing, so a frame mismatch is reported as <i>not compared</i> "
            "with both frames named.</p>"
            "<p><b>Residuals</b>, per observation. These move before the coordinates do: a "
            "sign error in a Jacobian or a dropped correlation between the components of a "
            "GNSS baseline shows here first.</p>"
            "<p>A quantity that could not be compared does <b>not</b> count as a "
            "disagreement. Absence of evidence is not evidence, and treating it as such "
            "would make an unconvertible frame look like a defect in an engine.</p>"
            "<h3>Parameters</h3>"
            "<p><b>Reference solution</b> and <b>Other solution</b> &mdash; JSON documents. "
            "The comparison is symmetric; the names decide only which column is which.</p>"
            "<p><b>Coordinate tolerance</b> &mdash; metres. The default of 0.1 mm is far "
            "below any observation's precision and far above the last-digit differences two "
            "orderings of the same arithmetic produce.</p>"
            "<p><b>Variance factor tolerance</b> &mdash; relative. The default of 1% "
            "accommodates DynAdjust printing sigma-nought to three decimals.</p>"
            "<h3>Outputs</h3>"
            "<p><b>Report</b> &mdash; plain text, one line per quantity. <b>Differences</b> "
            "&mdash; JSON, per station and per observation, for a plot or a spreadsheet.</p>"
            "<p>Scalar outputs: <code>AGREES</code>, "
            "<code>LARGEST_COORDINATE_DIFFERENCE</code>, "
            "<code>LARGEST_RESIDUAL_DIFFERENCE</code> and "
            "<code>DISAGREEMENT_COUNT</code>.</p>"
        )

    # -- parameters ------------------------------------------------------

    def initAlgorithm(self, config: dict[str, Any] | None = None) -> None:
        self.addParameter(
            QgsProcessingParameterFile(
                REFERENCE, self.tr("Reference solution"), extension="json"
            )
        )
        self.addParameter(
            QgsProcessingParameterFile(OTHER, self.tr("Other solution"), extension="json")
        )
        self.addAdvancedParameter(
            QgsProcessingParameterNumber(
                COORDINATE_TOLERANCE,
                self.tr("Coordinate tolerance (m)"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=1e-4,
                minValue=0.0,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterNumber(
                VARIANCE_TOLERANCE,
                self.tr("Variance factor tolerance (relative)"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=1e-2,
                minValue=0.0,
            )
        )
        self.addParameter(
            QgsProcessingParameterFileDestination(
                OUTPUT_REPORT,
                self.tr("Comparison report"),
                fileFilter="Text (*.txt)",
                optional=True,
                createByDefault=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterFileDestination(
                OUTPUT_JSON,
                self.tr("Differences"),
                fileFilter="JSON (*.json)",
                optional=True,
                createByDefault=False,
            )
        )

    # -- execution -------------------------------------------------------

    def processAlgorithm(
        self,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> dict[str, Any]:
        reference = self._load(self.parameterAsFile(parameters, REFERENCE, context), REFERENCE)
        other = self._load(self.parameterAsFile(parameters, OTHER, context), OTHER)

        if reference.network_id != other.network_id:
            feedback.pushWarning(
                self.tr(
                    "The two solutions name different networks (%1 and %2). Comparing "
                    "them is only meaningful if they are in fact the same network under "
                    "two names."
                )
                .replace("%1", reference.network_id)
                .replace("%2", other.network_id)
            )

        result = compare(
            reference,
            other,
            coordinate_tolerance=self.parameterAsDouble(
                parameters, COORDINATE_TOLERANCE, context
            ),
            variance_tolerance=self.parameterAsDouble(parameters, VARIANCE_TOLERANCE, context),
        )

        summary = result.summary()
        for line in summary.splitlines():
            feedback.pushInfo(line)
        if not result.agrees:
            feedback.pushWarning(
                self.tr("%1 quantity/quantities disagree.").replace(
                    "%1", str(len(result.disagreements))
                )
            )

        report_target = self.parameterAsFileOutput(parameters, OUTPUT_REPORT, context)
        if report_target:
            Path(report_target).write_text(summary + "\n", encoding="utf-8")

        json_target = self.parameterAsFileOutput(parameters, OUTPUT_JSON, context)
        if json_target:
            payload = {
                "reference": result.reference_id,
                "other": result.other_id,
                "agrees": result.agrees,
                "quantities": [
                    {
                        "quantity": item.quantity,
                        "reference": item.reference,
                        "other": item.other,
                        "agrees": item.agrees,
                        "not_compared": item.not_compared,
                    }
                    for item in result.agreements
                ],
                "coordinate_differences": result.coordinate_differences,
                "residual_differences": result.residual_differences,
            }
            with open(json_target, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2, sort_keys=True)
                handle.write("\n")

        residuals = result.residual_differences.values()
        return {
            OUTPUT_REPORT: report_target,
            OUTPUT_JSON: json_target,
            AGREES: result.agrees,
            LARGEST_COORDINATE_DIFFERENCE: result.largest_coordinate_difference,
            LARGEST_RESIDUAL_DIFFERENCE: max(residuals) if residuals else None,
            DISAGREEMENT_COUNT: len(result.disagreements),
        }

    def _load(self, path: str, parameter: str) -> Solution:
        """Read a solution document, failing with a message that names it."""
        if not path:
            raise QgsProcessingException(
                self.tr("No solution document was given for parameter '%1'.").replace(
                    "%1", parameter
                )
            )
        source = Path(path)
        if not source.is_file():
            raise QgsProcessingException(
                self.tr("The solution document '%1' does not exist.").replace("%1", str(source))
            )
        try:
            payload = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise QgsProcessingException(
                self.tr("'%1' could not be read as JSON: %2")
                .replace("%1", str(source))
                .replace("%2", str(error))
            ) from error
        try:
            return Solution.from_dict(payload)
        except (GeoCompError, KeyError, TypeError, ValueError) as error:
            raise QgsProcessingException(
                self.tr("'%1' is not a GeoComp solution document: %2")
                .replace("%1", str(source))
                .replace("%2", str(error))
            ) from error
