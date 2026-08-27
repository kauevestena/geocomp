# SPDX-License-Identifier: GPL-2.0-or-later
"""``geocomp:totalstation_trig_levelling`` -- trigonometric levelling (FR-410).

``specs/09-module-total-station.md`` section 4.5.

Height differences from zenith angles and slope distances, with curvature and
refraction applied and the instrument and target heights accounted for.

**Leap-frog changes the error model, not just the arithmetic.** With the
instrument set between two targets, the instrument height cancels exactly -- it
never has to be measured -- and the refraction largely cancels because both
sights pass through the same air at the same moment and therefore share one
coefficient. That shared coefficient is carried through a single Jacobian, so
the cancellation appears in the uncertainty and not only in the value. Treating
the two sights as independent would give a standard deviation several times too
large.
"""

from __future__ import annotations

import csv
import json
from typing import Any

from qgis.core import (
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFile,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterNumber,
)

from geocomp.algorithms.base import GeoCompAlgorithm
from geocomp.algorithms.reporting import (
    escape,
    format_number,
    render_document,
    render_note,
    render_table,
)
from geocomp.algorithms.totalstation.common import findings_table, read_reductions
from geocomp.core.errors import GeoCompError
from geocomp.core.techniques.total_station import (
    Sight,
    leapfrog_height_difference,
    radial_height_difference,
)
from geocomp.core.techniques.total_station.reductions import DEFAULT_EARTH_RADIUS
from geocomp.core.uncertainty import Quantity
from geocomp.core.units import Unit

__all__ = ["TrigonometricLevellingAlgorithm"]

REDUCTIONS = "REDUCTIONS"
MODE = "MODE"
INSTRUMENT_HEIGHT = "INSTRUMENT_HEIGHT"
TARGET_HEIGHT = "TARGET_HEIGHT"
REFRACTION = "REFRACTION"
REFRACTION_SIGMA = "REFRACTION_SIGMA"
EARTH_RADIUS = "EARTH_RADIUS"
IMBALANCE_TOLERANCE = "IMBALANCE_TOLERANCE"
OUTPUT_HEIGHTS = "OUTPUT_HEIGHTS"
OUTPUT_HTML = "OUTPUT_HTML"
OUTPUT_CSV = "OUTPUT_CSV"
RESULT_COUNT = "RESULT_COUNT"
WORST_UNCERTAINTY = "WORST_UNCERTAINTY"

RADIAL, LEAPFROG = 0, 1


class TrigonometricLevellingAlgorithm(GeoCompAlgorithm):
    """Height differences from zenith angles and slope distances."""

    TR_CONTEXT = "TrigonometricLevellingAlgorithm"

    def displayName(self) -> str:
        return self.tr("Trigonometric levelling")

    def shortDescription(self) -> str:
        return self.tr(
            "Height differences from zenith angles and distances, radial or leap-frog."
        )

    def help_body(self) -> str:
        return self.tr(
            "<p>Computes height differences from the reduced zenith angles and slope "
            "distances, with the curvature-and-refraction correction applied and its "
            "uncertainty propagated. On a 100 m sight the correction is 0.7 mm; at 1 km it "
            "is 68 mm; at 5 km it is 1.7 m.</p>"
            "<p><b>Radial</b> computes a height difference from the occupied station to each "
            "target it sighted. The instrument height, the target height and the refraction "
            "all contribute in full.</p>"
            "<p><b>Leap-frog</b> takes each setup that sighted exactly two targets as a free "
            "station between them, and produces one height difference from the first to the "
            "second. Two things then cancel. The <b>instrument height cancels exactly</b> and "
            "never has to be measured, which removes what is routinely the dominant error in "
            "a short trigonometric height. And the <b>refraction largely cancels</b>, because "
            "both sights pass through the same air at the same moment and share one "
            "coefficient &mdash; a shared dependence carried through a single Jacobian, so "
            "the cancellation shows in the uncertainty and not only in the value. With "
            "balanced sights the refraction uncertainty leaves the result entirely.</p>"
            "<p>How much cancels depends on how equal the two sights are, which the surveyor "
            "controls by where they stand, so an imbalanced pair is reported along with the "
            "fraction of the refraction uncertainty that survived.</p>"
            "<h3>Parameters</h3>"
            "<p><b>Reduced observations</b> &mdash; the document Generalised pre-processing "
            "produced. <b>Mode</b> &mdash; radial or leap-frog.</p>"
            "<p><b>Instrument height</b> and <b>target height</b> (m) &mdash; used in radial "
            "mode where the readings do not carry their own. Ignored in leap-frog mode, "
            "where the instrument height cancels.</p>"
            "<p><b>Refraction coefficient</b> and its <b>uncertainty</b> &mdash; "
            "dimensionless. The coefficient is poorly known and varies through the day, and "
            "it is the dominant error source on long sights, which is why its uncertainty is "
            "an input rather than an assumption.</p>"
            "<p><b>Earth radius</b> (m) and <b>sight imbalance tolerance</b> (as a fraction "
            "of the longer sight).</p>"
            "<h3>Outputs</h3>"
            "<p><b>Height differences</b> &mdash; JSON. <b>Report</b> &mdash; HTML. "
            "<b>Differences</b> &mdash; CSV. Scalars: <code>RESULT_COUNT</code> and "
            "<code>WORST_UNCERTAINTY</code> in metres.</p>"
        )

    def initAlgorithm(self, config: dict[str, Any] | None = None) -> None:
        self.addParameter(
            QgsProcessingParameterFile(
                REDUCTIONS, self.tr("Reduced observations"), extension="json"
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                MODE,
                self.tr("Mode"),
                options=[self.tr("Radial"), self.tr("Leap-frog")],
                defaultValue=RADIAL,
            )
        )
        for name, label, default in (
            (INSTRUMENT_HEIGHT, self.tr("Instrument height (m)"), 1.500),
            (TARGET_HEIGHT, self.tr("Target height (m)"), 1.500),
        ):
            self.addParameter(
                QgsProcessingParameterNumber(
                    name,
                    label,
                    type=QgsProcessingParameterNumber.Type.Double,
                    defaultValue=default,
                    minValue=0.0,
                    maxValue=100.0,
                )
            )
        self.addParameter(
            QgsProcessingParameterNumber(
                REFRACTION,
                self.tr("Refraction coefficient"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=0.13,
                minValue=-1.0,
                maxValue=1.0,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterNumber(
                REFRACTION_SIGMA,
                self.tr("Refraction coefficient uncertainty"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=0.05,
                minValue=0.0,
                maxValue=1.0,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterNumber(
                EARTH_RADIUS,
                self.tr("Earth radius (m)"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=DEFAULT_EARTH_RADIUS,
                minValue=1.0e6,
                maxValue=1.0e8,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterNumber(
                IMBALANCE_TOLERANCE,
                self.tr("Sight imbalance tolerance"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=0.05,
                minValue=0.0,
                maxValue=1.0,
            )
        )
        for name, label, filter_text, by_default in (
            (
                OUTPUT_HEIGHTS,
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
        results = read_reductions(self.parameterAsFile(parameters, REDUCTIONS, context))
        mode = self.parameterAsEnum(parameters, MODE, context)
        coefficient = Quantity.from_std_dev(
            self.parameterAsDouble(parameters, REFRACTION, context),
            self.parameterAsDouble(parameters, REFRACTION_SIGMA, context),
            Unit.DIMENSIONLESS,
        )
        radius = self.parameterAsDouble(parameters, EARTH_RADIUS, context)

        feedback.setProgress(25)
        try:
            if mode == LEAPFROG:
                rows, findings = self._leapfrog(
                    parameters, context, results, coefficient, radius
                )
            else:
                rows, findings = self._radial(parameters, context, results, coefficient, radius)
        except GeoCompError as exc:
            from geocomp.services.messages import message_for

            raise QgsProcessingException(message_for(exc)) from exc

        if not rows:
            raise QgsProcessingException(
                self.tr(
                    "No height difference could be computed. Radial mode needs pointings "
                    "with a distance; leap-frog mode needs setups that sighted exactly two "
                    "targets."
                )
            )

        for finding in findings:
            feedback.pushWarning(f"[{finding.code}] {finding.message}")
        feedback.pushInfo(
            self.tr("%1 height difference(s) computed.").replace("%1", str(len(rows)))
        )

        feedback.setProgress(80)
        outputs = self._write(parameters, context, rows, findings, mode)
        feedback.setProgress(100)

        return {
            RESULT_COUNT: len(rows),
            WORST_UNCERTAINTY: max(row["difference"].std_dev for row in rows),
            **outputs,
        }

    # -- the two modes ---------------------------------------------------

    def _radial(self, parameters, context, results, coefficient, radius):
        instrument_height = Quantity.from_std_dev(
            self.parameterAsDouble(parameters, INSTRUMENT_HEIGHT, context), 0.001, Unit.METRE
        )
        default_target = Quantity.from_std_dev(
            self.parameterAsDouble(parameters, TARGET_HEIGHT, context), 0.001, Unit.METRE
        )

        rows = []
        for result in results:
            for pointing in result.usable:
                if pointing.reduction.distance is None:
                    continue
                sight = Sight(
                    station=pointing.target,
                    zenith=pointing.reduction.zenith,
                    distance=pointing.reduction.distance,
                    target_height=default_target,
                )
                rows.append(
                    {
                        "from": result.station,
                        "to": pointing.target,
                        "difference": radial_height_difference(
                            sight,
                            instrument_height,
                            refraction_coefficient=coefficient,
                            earth_radius=radius,
                        ),
                        "imbalance": None,
                        "cancellation": None,
                    }
                )
        return rows, ()

    def _leapfrog(self, parameters, context, results, coefficient, radius):
        tolerance = self.parameterAsDouble(parameters, IMBALANCE_TOLERANCE, context)
        target_height = Quantity.from_std_dev(
            self.parameterAsDouble(parameters, TARGET_HEIGHT, context), 0.001, Unit.METRE
        )

        rows = []
        findings = []
        for result in results:
            usable = [p for p in result.usable if p.reduction.distance is not None]
            if len(usable) != 2:
                continue
            backward, forward = usable
            outcome = leapfrog_height_difference(
                Sight(
                    station=backward.target,
                    zenith=backward.reduction.zenith,
                    distance=backward.reduction.distance,
                    target_height=target_height,
                ),
                Sight(
                    station=forward.target,
                    zenith=forward.reduction.zenith,
                    distance=forward.reduction.distance,
                    target_height=target_height,
                ),
                refraction_coefficient=coefficient,
                earth_radius=radius,
                imbalance_tolerance=tolerance,
            )
            findings.extend(outcome.findings)
            rows.append(
                {
                    "from": backward.target,
                    "to": forward.target,
                    "difference": outcome.height_difference,
                    "imbalance": outcome.sight_imbalance,
                    "cancellation": outcome.refraction_cancellation,
                }
            )
        return rows, tuple(findings)

    # -- outputs ---------------------------------------------------------

    def _write(self, parameters, context, rows, findings, mode) -> dict[str, Any]:
        heights = self.parameterAsFileOutput(parameters, OUTPUT_HEIGHTS, context)
        if heights:
            with open(heights, "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "kind": "geocomp.height_differences",
                        "version": 1,
                        "mode": "leapfrog" if mode == LEAPFROG else "radial",
                        "differences": [
                            {
                                "from": row["from"],
                                "to": row["to"],
                                "value": row["difference"].to_dict(),
                            }
                            for row in rows
                        ],
                    },
                    handle,
                    indent=2,
                    sort_keys=True,
                )
                handle.write("\n")

        html_target = self.parameterAsFileOutput(parameters, OUTPUT_HTML, context)
        if html_target:
            with open(html_target, "w", encoding="utf-8") as handle:
                handle.write(self._render(rows, findings, mode))

        csv_target = self.parameterAsFileOutput(parameters, OUTPUT_CSV, context)
        if csv_target:
            with open(csv_target, "w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(
                    [
                        "from",
                        "to",
                        "height_difference",
                        "sigma",
                        "sight_imbalance",
                        "refraction_surviving",
                    ]
                )
                for row in rows:
                    writer.writerow(
                        [
                            row["from"],
                            row["to"],
                            repr(row["difference"].value),
                            repr(row["difference"].std_dev),
                            "" if row["imbalance"] is None else repr(row["imbalance"]),
                            "" if row["cancellation"] is None else repr(row["cancellation"]),
                        ]
                    )

        return {OUTPUT_HEIGHTS: heights, OUTPUT_HTML: html_target, OUTPUT_CSV: csv_target}

    def _render(self, rows, findings, mode) -> str:
        headers = [
            escape(self.tr("From")),
            escape(self.tr("To")),
            escape(self.tr("Height difference (m)")),
            escape(self.tr("Std dev (mm)")),
        ]
        if mode == LEAPFROG:
            headers.extend(
                [
                    escape(self.tr("Sight imbalance (m)")),
                    escape(self.tr("Refraction surviving")),
                ]
            )

        table_rows = []
        for row in rows:
            cells = [
                escape(row["from"]),
                escape(row["to"]),
                format_number(row["difference"].value, 4),
                format_number(row["difference"].std_dev * 1000.0, 2),
            ]
            if mode == LEAPFROG:
                cells.extend(
                    [
                        format_number(row["imbalance"], 2),
                        format_number(row["cancellation"], 3),
                    ]
                )
            table_rows.append(cells)

        body = [
            f"<h2>{escape(self.tr('Height differences'))}</h2>",
            render_table(headers, table_rows),
        ]
        if mode == LEAPFROG:
            body.append(
                render_note(
                    self.tr(
                        "'Refraction surviving' is the fraction of the refraction "
                        "uncertainty the method did not remove: 0 means the two sights were "
                        "equal and it cancelled entirely, 1 means it did not cancel at all. "
                        "It depends only on the two sight lengths, which is what makes it "
                        "something the surveyor controls."
                    )
                )
            )
        body.append(f"<h2>{escape(self.tr('Findings'))}</h2>")
        body.append(findings_table(tuple(findings)))

        return render_document(
            self.tr("Trigonometric levelling report"),
            body,
            footer=escape(
                self.tr("Generated by GeoComp — geocomp:totalstation_trig_levelling")
            ),
        )
