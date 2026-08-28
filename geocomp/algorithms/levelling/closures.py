# SPDX-License-Identifier: GPL-2.0-or-later
"""``geocomp:levelling_closures`` -- line and loop closures (FR-503).

``specs/10-module-levelling.md`` section 3: *a levelling result without a closure
check is not a result*.

Three things, and the third is where the thought went. The misclosure; the
comparison against ``k * sqrt(L)``, or no verdict at all when no *k* was
configured; and the classical proportional distribution, with an honest account
of what it can and cannot tell you.
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

from geocomp.algorithms.base import GeoCompAlgorithm
from geocomp.algorithms.levelling.common import (
    findings_table,
    levelling_class_from_parameters,
    read_reductions,
    reduction_from_dict,
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
from geocomp.core.settings_def import WEIGHTING_LENGTH, WEIGHTING_SETUPS
from geocomp.core.techniques.levelling import line_closure, loop_closure
from geocomp.core.uncertainty import Quantity
from geocomp.core.units import Unit

__all__ = ["LevellingClosureAlgorithm"]

REDUCTIONS = "REDUCTIONS"
MODE = "MODE"
KNOWN_DIFFERENCE = "KNOWN_DIFFERENCE"
KNOWN_SIGMA = "KNOWN_SIGMA"
TOLERANCE_COEFFICIENT = "TOLERANCE_COEFFICIENT"
WEIGHTING = "WEIGHTING"
LOOP_ID = "LOOP_ID"
OUTPUT_CLOSURES = "OUTPUT_CLOSURES"
OUTPUT_HTML = "OUTPUT_HTML"
OUTPUT_CSV = "OUTPUT_CSV"
MISCLOSURE = "MISCLOSURE"
PERMISSIBLE = "PERMISSIBLE"
PASSED = "PASSED"

LOOP, LINE = 0, 1


class LevellingClosureAlgorithm(GeoCompAlgorithm):
    """Close a levelling loop on itself, or a line against a known difference."""

    TR_CONTEXT = "LevellingClosureAlgorithm"

    def displayName(self) -> str:
        return self.tr("Closures and tolerances")

    def shortDescription(self) -> str:
        return self.tr("Line and loop misclosure, against a configurable tolerance.")

    def help_body(self) -> str:
        return self.tr(
            "<p>Computes the misclosure of a levelling loop or line and compares it with "
            "the permissible misclosure <code>k &times; &radic;L</code>, with <i>L</i> in "
            "kilometres.</p>"
            "<p><b>With no k configured there is no verdict.</b> The misclosure is still "
            "reported &mdash; it is the number that matters &mdash; but whether it is "
            "acceptable is not, because inventing a tolerance to have something to compare "
            "against would be worse than saying nothing. GeoComp ships no national "
            "tolerance table: <i>k</i> differs by country, by class within a country and by "
            "edition of the standard, and a wrong value does not fail loudly, it quietly "
            "accepts a line that should have been re-run.</p>"
            "<p><b>The distribution across setups comes with a caveat that is part of the "
            "answer.</b> Distributing a misclosure proportionally is the classical "
            "correction and many specifications require it, so it is computed. But "
            "proportional distribution <b>localises nothing</b>: every setup gets its share "
            "whether or not it is where the error entered, so a blunder is smeared evenly "
            "along the line and made harder to find.</p>"
            "<p>So the misclosure is also compared with <b>its own propagated standard "
            "deviation</b>. A small ratio means the line closed as well as its own readings "
            "say it should, and distributing that misclosure is exactly right. A large one "
            "means something happened that the reading precisions do not explain, and "
            "spreading it evenly is the one response guaranteed to hide it &mdash; adjust "
            "the network and let data snooping find it instead. The report says which case "
            "you are in.</p>"
            "<h3>Parameters</h3>"
            "<p><b>Reduced lines</b> &mdash; the document a reduction produced. <b>Mode</b> "
            "&mdash; loop (the lines must chain and return to where they began; a line "
            "entered in the opposite direction is handled from the station ids) or line "
            "(the first line only, against a known height difference).</p>"
            "<p><b>Known height difference</b> and its <b>uncertainty</b> (m) &mdash; from "
            "the two benchmarks' published heights. The uncertainty enters the misclosure's: "
            "a line closed against two third-order marks has not been tested as sharply as "
            "one closed against two first-order marks.</p>"
            "<p><b>Tolerance coefficient k</b> (m per root kilometre) &mdash; zero for no "
            "verdict. <b>Distribute by</b> &mdash; line length or setup count.</p>"
            "<h3>Outputs</h3>"
            "<p><b>Closure</b> &mdash; JSON. <b>Report</b> &mdash; HTML. "
            "<b>Distribution</b> &mdash; CSV. Scalars: <code>MISCLOSURE</code> and "
            "<code>PERMISSIBLE</code> in metres, and <code>PASSED</code> (1, 0, or -1 for "
            "not judged).</p>"
        )

    def initAlgorithm(self, config: dict[str, Any] | None = None) -> None:
        self.addParameter(
            QgsProcessingParameterFile(REDUCTIONS, self.tr("Reduced lines"), extension="json")
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                MODE,
                self.tr("Mode"),
                options=[self.tr("Loop"), self.tr("Line against a known difference")],
                defaultValue=LOOP,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                TOLERANCE_COEFFICIENT,
                self.tr("Tolerance coefficient k (m per root km)"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=0.0,
                minValue=0.0,
                maxValue=1.0,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                KNOWN_DIFFERENCE,
                self.tr("Known height difference (m)"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=0.0,
                minValue=-10000.0,
                maxValue=10000.0,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterNumber(
                KNOWN_SIGMA,
                self.tr("Uncertainty of the known difference (m)"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=0.0,
                minValue=0.0,
                maxValue=10.0,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterEnum(
                WEIGHTING,
                self.tr("Distribute by"),
                options=[self.tr("Line length"), self.tr("Number of setups")],
                defaultValue=0,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterString(
                LOOP_ID, self.tr("Loop name"), defaultValue="loop", optional=True
            )
        )
        for name, label, filter_text, by_default in (
            (OUTPUT_CLOSURES, self.tr("Closure"), self.tr("GeoComp closure (*.json)"), True),
            (OUTPUT_HTML, self.tr("Report"), self.tr("HTML files (*.html)"), True),
            (OUTPUT_CSV, self.tr("Distribution"), self.tr("CSV files (*.csv)"), False),
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
        payload = read_reductions(self.parameterAsFile(parameters, REDUCTIONS, context))
        reductions = [reduction_from_dict(line) for line in payload]
        mode = self.parameterAsEnum(parameters, MODE, context)
        weighting = (
            WEIGHTING_LENGTH
            if self.parameterAsEnum(parameters, WEIGHTING, context) == 0
            else WEIGHTING_SETUPS
        )
        levelling_class = levelling_class_from_parameters(
            coefficient=self.parameterAsDouble(parameters, TOLERANCE_COEFFICIENT, context),
            max_sight_length=0.0,
            max_sight_imbalance=0.0,
            max_accumulated_imbalance=0.0,
        )

        feedback.setProgress(30)
        try:
            if mode == LINE:
                check = line_closure(
                    reductions[0],
                    Quantity.from_std_dev(
                        self.parameterAsDouble(parameters, KNOWN_DIFFERENCE, context),
                        self.parameterAsDouble(parameters, KNOWN_SIGMA, context),
                        Unit.METRE,
                    ),
                    levelling_class=levelling_class,
                    weighting=weighting,
                )
            else:
                check = loop_closure(
                    reductions,
                    loop_id=self.parameterAsString(parameters, LOOP_ID, context) or "loop",
                    levelling_class=levelling_class,
                    weighting=weighting,
                )
        except GeoCompError as exc:
            from geocomp.services.messages import message_for

            raise QgsProcessingException(message_for(exc)) from exc

        blocking, warnings = summarise_findings(check.findings, feedback)
        feedback.pushInfo(
            self.tr("Misclosure %1 mm over %2 km.")
            .replace("%1", format_number(check.misclosure * 1000.0, 2))
            .replace("%2", format_number(check.length_km, 3) if check.length_km else "?")
        )

        feedback.setProgress(70)
        write_document(
            self.parameterAsFileOutput(parameters, OUTPUT_CLOSURES, context),
            {
                "kind": "levelling_closure",
                "closure": {
                    "kind": check.kind,
                    "id": check.id,
                    "misclosure": check.misclosure,
                    "permissible": check.permissible,
                    "passed": check.passed,
                    "standardised": check.standardised,
                    "length_km": check.length_km,
                    "setup_count": check.setup_count,
                    "distribution": [
                        {
                            "setup_id": share.setup_id,
                            "correction": share.correction,
                            "weight": share.weight,
                            "standardised": share.standardised,
                        }
                        for share in check.distribution
                    ],
                },
            },
        )
        self._write_report(parameters, context, check)
        self._write_csv(parameters, context, check)
        feedback.setProgress(100)

        return {
            MISCLOSURE: check.misclosure,
            PERMISSIBLE: check.permissible if check.permissible is not None else -1.0,
            PASSED: -1 if check.passed is None else int(check.passed),
            OUTPUT_CLOSURES: self.parameterAsFileOutput(parameters, OUTPUT_CLOSURES, context),
            OUTPUT_HTML: self.parameterAsFileOutput(parameters, OUTPUT_HTML, context),
            OUTPUT_CSV: self.parameterAsFileOutput(parameters, OUTPUT_CSV, context),
            "BLOCKING": blocking,
            "WARNINGS": warnings,
        }

    def _verdict(self, check) -> str:
        if check.passed is True:
            return self.tr("within tolerance")
        if check.passed is False:
            return self.tr("OUT OF TOLERANCE")
        return self.tr("not judged — no tolerance was configured")

    def _write_report(self, parameters, context, check) -> None:
        path = self.parameterAsFileOutput(parameters, OUTPUT_HTML, context)
        if not path:
            return

        summary = render_table(
            [escape(self.tr("Quantity")), escape(self.tr("Value"))],
            [
                [escape(self.tr("Kind")), escape(check.kind)],
                [escape(self.tr("Misclosure (mm)")), format_number(check.misclosure * 1000.0, 2)],
                [
                    escape(self.tr("Permissible (mm)")),
                    format_number(check.permissible * 1000.0, 2)
                    if check.permissible is not None
                    else "—",
                ],
                [escape(self.tr("Verdict")), escape(self._verdict(check))],
                [
                    escape(self.tr("Length (km)")),
                    format_number(check.length_km, 4) if check.length_km is not None else "—",
                ],
                [escape(self.tr("Setups")), str(check.setup_count)],
                [
                    escape(self.tr("Misclosure over its own uncertainty")),
                    format_number(check.standardised, 2)
                    if check.standardised is not None
                    else "—",
                ],
            ],
        )

        body = [f"<h2>{escape(self.tr('Closure'))}</h2>", summary]
        if check.looks_like_a_blunder:
            body.append(
                render_note(
                    self.tr(
                        "The misclosure is far larger than the readings' own precision "
                        "explains. That is not accumulated random error, so distributing it "
                        "proportionally would spread one mistake evenly along the line and "
                        "make it harder to find. Adjust the network and let data snooping "
                        "locate it."
                    ),
                    label=self.tr("Do not distribute this"),
                )
            )
        else:
            body.append(
                render_note(
                    self.tr(
                        "The misclosure is consistent with the readings' own precision, "
                        "which is the case proportional distribution is correct for."
                    ),
                    label=self.tr("Distribution"),
                )
            )

        body.append(f"<h2>{escape(self.tr('Distribution across setups'))}</h2>")
        body.append(
            render_table(
                [
                    escape(self.tr("Setup")),
                    escape(self.tr("Share")),
                    escape(self.tr("Correction (mm)")),
                    escape(self.tr("Correction over the setup's own uncertainty")),
                ],
                [
                    [
                        escape(share.setup_id),
                        format_number(share.weight, 4),
                        format_number(share.correction * 1000.0, 3),
                        format_number(share.standardised, 2)
                        if share.standardised is not None
                        else "—",
                    ]
                    for share in check.distribution
                ],
            )
        )
        body.append(f"<h2>{escape(self.tr('Findings'))}</h2>")
        body.append(findings_table(check.findings))
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(render_document(self.tr("Levelling: closures"), body))

    def _write_csv(self, parameters, context, check) -> None:
        path = self.parameterAsFileOutput(parameters, OUTPUT_CSV, context)
        if not path:
            return
        with open(path, "w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["setup", "weight", "correction_m", "standardised"])
            for share in check.distribution:
                writer.writerow(
                    [
                        share.setup_id,
                        exact(share.weight),
                        exact(share.correction),
                        exact(share.standardised),
                    ]
                )
