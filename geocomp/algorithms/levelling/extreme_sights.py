# SPDX-License-Identifier: GPL-2.0-or-later
"""``geocomp:levelling_extreme_sights`` -- several foresights from one setup (FR-502).

``specs/10-module-levelling.md`` section 2.3.

The routine case for levelling a set of points from one instrument position. All
the foresights of a setup subtract the same backsight reading, so they are
**correlated**, and the correlation is not a nuisance to be tidied away.

Between two foresighted points the backsight cancels exactly: their height
difference is ``f_i - f_j`` and the backsight never appears. Treating the two as
independent adds twice the backsight variance that is not there, and reports an
uncertainty too *large*. That is the opposite of the usual failure and no less
wrong -- a network can be declared inadequate on the strength of it.
"""

from __future__ import annotations

import csv
import math
from typing import Any

from qgis.core import (
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingParameterBoolean,
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
from geocomp.core.techniques.levelling import reduce_setup

__all__ = ["ExtremeSightsAlgorithm"]

SETUPS = "SETUPS"
PROFILES = "PROFILES"
LEVEL_ID = "LEVEL_ID"
MAX_SIGHT_LENGTH = "MAX_SIGHT_LENGTH"
MAX_SIGHT_IMBALANCE = "MAX_SIGHT_IMBALANCE"
ONLY_MULTIPLE = "ONLY_MULTIPLE"
OUTPUT_DIFFERENCES = "OUTPUT_DIFFERENCES"
OUTPUT_HTML = "OUTPUT_HTML"
OUTPUT_CSV = "OUTPUT_CSV"
SETUP_COUNT = "SETUP_COUNT"
DIFFERENCE_COUNT = "DIFFERENCE_COUNT"
WORST_UNCERTAINTY = "WORST_UNCERTAINTY"


class ExtremeSightsAlgorithm(GeoCompAlgorithm):
    """Height differences from one setup to each of its foresights."""

    TR_CONTEXT = "ExtremeSightsAlgorithm"

    def displayName(self) -> str:
        return self.tr("Extreme sights")

    def shortDescription(self) -> str:
        return self.tr(
            "Several foresights from one setup, kept correlated through the backsight."
        )

    def help_body(self) -> str:
        return self.tr(
            "<p>Reduces each instrument setup to one height difference per foresight, "
            "keeping the <b>full covariance</b> between them.</p>"
            "<p>All the foresights of a setup subtract the same backsight reading, so they "
            "share its error. Between two of them the backsight <b>cancels exactly</b>: "
            "their height difference is one foresight minus the other, and the backsight "
            "does not appear. Treating the two as independent adds twice the backsight "
            "variance that is not there and reports an uncertainty too <b>large</b> "
            "&mdash; which is the opposite of the usual failure, and can have a network "
            "declared inadequate that is in fact fine.</p>"
            "<p>The report gives both: the difference from the backsighted station to each "
            "foresight, and the difference between each pair of foresights computed through "
            "the covariance, next to what treating them independently would have claimed.</p>"
            "<p>The correlation is carried into the output document as a covariance, so a "
            "network adjustment built from these setups keeps it.</p>"
            "<h3>Parameters</h3>"
            "<p><b>Setups</b> &mdash; the document the importer produced. <b>Only setups "
            "with several foresights</b> &mdash; skip the ordinary one-foresight setups, "
            "which have no correlation to show.</p>"
            "<p><b>Instrument profiles</b> and <b>level id</b> &mdash; where the reading "
            "precision comes from. <b>Longest sight</b> and <b>largest imbalance per "
            "setup</b> (m) &mdash; limits; zero disables a check.</p>"
            "<h3>Outputs</h3>"
            "<p><b>Height differences</b> &mdash; JSON with the covariances. <b>Report</b> "
            "&mdash; HTML. <b>Differences</b> &mdash; CSV. Scalars: "
            "<code>SETUP_COUNT</code>, <code>DIFFERENCE_COUNT</code> and "
            "<code>WORST_UNCERTAINTY</code> in metres.</p>"
        )

    def initAlgorithm(self, config: dict[str, Any] | None = None) -> None:
        self.addParameter(
            QgsProcessingParameterFile(SETUPS, self.tr("Setups"), extension="json")
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                ONLY_MULTIPLE,
                self.tr("Only setups with several foresights"),
                defaultValue=True,
            )
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
            (MAX_SIGHT_LENGTH, self.tr("Longest sight (m)"), 500.0),
            (MAX_SIGHT_IMBALANCE, self.tr("Largest imbalance per setup (m)"), 100.0),
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
                OUTPUT_DIFFERENCES,
                self.tr("Height differences"),
                self.tr("GeoComp height differences (*.json)"),
                True,
            ),
            (OUTPUT_HTML, self.tr("Report"), self.tr("HTML files (*.html)"), True),
            (OUTPUT_CSV, self.tr("Differences"), self.tr("CSV files (*.csv)"), False),
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
        only_multiple = self.parameterAsBool(parameters, ONLY_MULTIPLE, context)
        level = level_from_parameters(
            profiles=self.parameterAsFile(parameters, PROFILES, context),
            level_id=self.parameterAsString(parameters, LEVEL_ID, context),
            collimation=0.0,
            collimation_sigma=0.0,
        )

        setups = [
            setup
            for line in lines
            for setup in line.setups
            if setup.is_extreme_sights or not only_multiple
        ]
        if not setups:
            raise QgsProcessingException(
                self.tr(
                    "No setup carries several foresights. Extreme sights is for a setup "
                    "that levelled a group of points at once; clear 'Only setups with "
                    "several foresights' to reduce the ordinary ones too."
                )
            )

        feedback.setProgress(30)
        try:
            reductions = [
                reduce_setup(
                    setup,
                    level,
                    max_sight_length=self.parameterAsDouble(
                        parameters, MAX_SIGHT_LENGTH, context
                    ),
                    max_sight_imbalance=self.parameterAsDouble(
                        parameters, MAX_SIGHT_IMBALANCE, context
                    ),
                )
                for setup in setups
            ]
        except GeoCompError as exc:
            from geocomp.services.messages import message_for

            raise QgsProcessingException(message_for(exc)) from exc

        findings = tuple(f for reduction in reductions for f in reduction.findings)
        blocking, warnings = summarise_findings(findings, feedback)

        feedback.setProgress(70)
        write_document(
            self.parameterAsFileOutput(parameters, OUTPUT_DIFFERENCES, context),
            {
                "kind": "levelling_setup_reductions",
                "level_id": level.id,
                "setups": [
                    {
                        "setup_id": reduction.setup_id,
                        "from_station": reduction.from_station,
                        "to_stations": list(reduction.to_stations),
                        "height_differences": [
                            quantity.to_dict() for quantity in reduction.height_differences
                        ],
                        "covariance": reduction.covariance.to_dict(),
                        "imbalances": list(reduction.imbalances),
                    }
                    for reduction in reductions
                ],
            },
        )
        self._write_report(parameters, context, reductions, findings)
        self._write_csv(parameters, context, reductions)
        feedback.setProgress(100)

        differences = sum(len(r.height_differences) for r in reductions)
        return {
            SETUP_COUNT: len(reductions),
            DIFFERENCE_COUNT: differences,
            WORST_UNCERTAINTY: max(
                quantity.std_dev
                for reduction in reductions
                for quantity in reduction.height_differences
            ),
            OUTPUT_DIFFERENCES: self.parameterAsFileOutput(
                parameters, OUTPUT_DIFFERENCES, context
            ),
            OUTPUT_HTML: self.parameterAsFileOutput(parameters, OUTPUT_HTML, context),
            OUTPUT_CSV: self.parameterAsFileOutput(parameters, OUTPUT_CSV, context),
            "BLOCKING": blocking,
            "WARNINGS": warnings,
        }

    # -- outputs ---------------------------------------------------------

    def _pairs(self, reduction):
        """Every pair of foresights, correlated and as-if-independent."""
        stations = reduction.to_stations
        for index, first in enumerate(stations):
            for second in stations[index + 1 :]:
                correlated = reduction.between_foresights(first, second)
                independent = math.hypot(
                    reduction.height_difference(first).std_dev,
                    reduction.height_difference(second).std_dev,
                )
                yield first, second, correlated, independent

    def _write_report(self, parameters, context, reductions, findings) -> None:
        path = self.parameterAsFileOutput(parameters, OUTPUT_HTML, context)
        if not path:
            return

        body = [f"<h2>{escape(self.tr('Height differences from each setup'))}</h2>"]
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
                        escape(reduction.setup_id),
                        escape(reduction.from_station),
                        escape(station),
                        format_number(reduction.height_difference(station).value, 5),
                        format_number(
                            reduction.height_difference(station).std_dev * 1000.0, 3
                        ),
                    ]
                    for reduction in reductions
                    for station in reduction.to_stations
                ],
            )
        )

        pair_rows = [
            [
                escape(reduction.setup_id),
                escape(first),
                escape(second),
                format_number(correlated.value, 5),
                format_number(correlated.std_dev * 1000.0, 3),
                format_number(independent * 1000.0, 3),
                format_number(
                    (1.0 - correlated.std_dev / independent) * 100.0 if independent else 0.0,
                    1,
                ),
            ]
            for reduction in reductions
            for first, second, correlated, independent in self._pairs(reduction)
        ]
        if pair_rows:
            body.append(
                f"<h2>{escape(self.tr('Differences between foresighted points'))}</h2>"
            )
            body.append(
                render_table(
                    [
                        escape(self.tr("Setup")),
                        escape(self.tr("From")),
                        escape(self.tr("To")),
                        escape(self.tr("dH (m)")),
                        escape(self.tr("Uncertainty (mm)")),
                        escape(self.tr("If treated as independent (mm)")),
                        escape(self.tr("Overstated by (%)")),
                    ],
                    pair_rows,
                )
            )
            body.append(
                render_note(
                    self.tr(
                        "The backsight cancels between two foresights of one setup, so "
                        "these differences are better determined than independent treatment "
                        "would suggest. The last column is how much an independent "
                        "treatment would have overstated the uncertainty by."
                    ),
                    label=self.tr("Why the correlation helps"),
                )
            )

        body.append(f"<h2>{escape(self.tr('Findings'))}</h2>")
        body.append(findings_table(findings))
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(render_document(self.tr("Levelling: extreme sights"), body))

    def _write_csv(self, parameters, context, reductions) -> None:
        path = self.parameterAsFileOutput(parameters, OUTPUT_CSV, context)
        if not path:
            return
        with open(path, "w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["setup", "from", "to", "height_difference_m", "std_dev_m"])
            for reduction in reductions:
                for station in reduction.to_stations:
                    quantity = reduction.height_difference(station)
                    writer.writerow(
                        [
                            reduction.setup_id,
                            reduction.from_station,
                            station,
                            exact(quantity.value),
                            exact(quantity.std_dev),
                        ]
                    )
