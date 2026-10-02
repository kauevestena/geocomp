# SPDX-License-Identifier: GPL-2.0-or-later
"""``geocomp:monitoring_compare_epochs`` -- has it moved, and am I sure? (``specs/14``)

Two solutions of the same network, compared the way ``specs/14`` section 8 lays
out: compatibility checked and refused by name where a systematic difference
would pass for motion (FR-831), frames transformed with the transformation's own
uncertainty (FR-832), the reference block tested (FR-835), every displacement
with its covariance (FR-833) tested (FR-834), the global congruency test and the
strain (FR-836), and the project's alert thresholds (FR-837).

**When the reference block has moved, the analysis refuses** -- after writing
the analysis document and the report, which hold every localisation step and
the stations implicated, because that record is what the user needs to decide
which pillars to trust at the next run. A run that went on to report
displacements against a moved block would spread the block's motion over every
other station and call it deformation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qgis.core import (
    Qgis,
    QgsCoordinateReferenceSystem,
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFile,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
    QgsWkbTypes,
)

from geocomp.algorithms.base import GeoCompAlgorithm
from geocomp.algorithms.defaults import configured
from geocomp.algorithms.layer_outputs import LINE_SOURCE_TYPE, POLYGON_SOURCE_TYPE, write_styled_sink
from geocomp.algorithms.monitoring.common import (
    datum_labels,
    datum_of,
    fail,
    read_optional_network,
    read_solutions,
    read_thresholds,
    roles,
    write_json,
)
from geocomp.core.errors import GeoCompError, ValidationError
from geocomp.core.monitoring import (
    analyse,
    check_reference,
    compare,
    comparison_document,
    default_datum,
    evaluate_alerts,
    refused_document,
    strain,
)
from geocomp.core.number_format import localised
from geocomp.core.visualization.monitoring import displacement_exaggeration

__all__ = ["MonitoringCompareEpochsAlgorithm"]

FIRST = "FIRST"
SECOND = "SECOND"
NETWORK = "NETWORK"
REFERENCE = "REFERENCE"
OBJECTS = "OBJECTS"
DATUM = "DATUM"
CONFIDENCE = "CONFIDENCE"
STRAIN = "STRAIN"
THRESHOLDS = "THRESHOLDS"
EXAGGERATION = "EXAGGERATION"
OUTPUT_ANALYSIS = "OUTPUT_ANALYSIS"
OUTPUT_HTML = "OUTPUT_HTML"
OUTPUT_DISPLACEMENT_LAYER = "OUTPUT_DISPLACEMENT_LAYER"
OUTPUT_DISPLACEMENT_ELLIPSE_LAYER = "OUTPUT_DISPLACEMENT_ELLIPSE_LAYER"
REFERENCE_STABLE = "REFERENCE_STABLE"
GLOBAL_TEST_PASSED = "GLOBAL_TEST_PASSED"
SIGNIFICANT_COUNT = "SIGNIFICANT_COUNT"
ALERT_COUNT = "ALERT_COUNT"


class MonitoringCompareEpochsAlgorithm(GeoCompAlgorithm):
    """Two epochs compared for motion (FR-831 to FR-837)."""

    TR_CONTEXT = "MonitoringCompareEpochsAlgorithm"

    def displayName(self) -> str:
        return self.tr("Compare two epochs")

    def shortDescription(self) -> str:
        return self.tr("Displacements between two epochs, tested against the reference block.")

    def help_body(self) -> str:
        return self.tr(
            "<p>Compares two solutions of the same network and says which stations moved, by "
            "how much, and with what confidence.</p>"
            "<p>Before anything is differenced, the epochs are checked: a solution without an "
            "epoch, heights of different types or geoid models, a free datum against a held "
            "one, and two projections are refused by name, because each would put a "
            "systematic difference into every displacement. Geocentric solutions in different "
            "frames are transformed, and the transformation's own uncertainty is carried.</p>"
            "<p>The <b>reference stations</b> are the pillars assumed stable. Their congruency "
            "is tested first; if they moved relative to one another, the analysis names the "
            "stations and <b>refuses</b> to report displacements against them, after writing "
            "the report with every localisation step. Leave the field empty to take the "
            "stations marked REFERENCE in the network document.</p>"
            "<p>Every displacement is tested against its own covariance and reported as "
            "<i>significant</i> or <i>not significant</i> with its value, never as zero. "
            "Without the covariance between the epochs, they are taken as independent and the "
            "result says so, and which way that errs.</p>"
            "<h3>Parameters</h3>"
            "<p><b>First / second epoch</b> &mdash; solution documents written by an adjustment "
            "algorithm.</p>"
            "<p><b>Network document</b> &mdash; optional; where the monitoring roles are read "
            "from, and where a heights-only network's stations are placed on the map.</p>"
            "<p><b>Datum of the displacements</b> &mdash; what the reference block fixes: "
            "translation (heights, geocentric), translation and rotation (a plan), or a "
            "similarity.</p>"
            "<p><b>Alert thresholds</b> &mdash; a CSV file of <code>kind, limit, stations, "
            "group</code>: kind is magnitude, horizontal, vertical or significance; limits in "
            "metres; stations separated by spaces or semicolons, empty for all. A station over "
            "its limit is flagged whether or not its motion is significant.</p>"
            "<p><b>Exaggeration</b> &mdash; the factor the arrows and ellipses are drawn at, "
            "stated in the layer names; 0 fits it to the network.</p>"
        )

    def initAlgorithm(self, config: dict[str, Any] | None = None) -> None:
        self.addParameter(
            QgsProcessingParameterFile(FIRST, self.tr("First epoch (solution)"), extension="json")
        )
        self.addParameter(
            QgsProcessingParameterFile(SECOND, self.tr("Second epoch (solution)"), extension="json")
        )
        self.addParameter(
            QgsProcessingParameterFile(
                NETWORK, self.tr("Network document (monitoring roles)"), extension="json", optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                REFERENCE, self.tr("Reference stations (comma-separated)"), optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                OBJECTS, self.tr("Object stations (comma-separated; empty for all others)"), optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                DATUM, self.tr("Datum of the displacements"), options=datum_labels(), defaultValue=0
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                CONFIDENCE,
                self.tr("Confidence level"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=configured("stochastic.confidence_level"),
                minValue=0.5,
                maxValue=0.9999,
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                STRAIN, self.tr("Separate rigid-body motion from strain"), defaultValue=True
            )
        )
        self.addParameter(
            QgsProcessingParameterFile(
                THRESHOLDS, self.tr("Alert thresholds (CSV)"), extension="csv", optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterFileDestination(
                OUTPUT_ANALYSIS,
                self.tr("Analysis document"),
                self.tr("GeoComp monitoring document (*.json)"),
                optional=True,
                createByDefault=True,
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
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                OUTPUT_DISPLACEMENT_LAYER,
                self.tr("Displacements (layer)"),
                type=LINE_SOURCE_TYPE,
                optional=True,
                createByDefault=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                OUTPUT_DISPLACEMENT_ELLIPSE_LAYER,
                self.tr("Displacement ellipses (layer)"),
                type=POLYGON_SOURCE_TYPE,
                optional=True,
                createByDefault=True,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterNumber(
                EXAGGERATION,
                self.tr("Exaggeration of arrows and ellipses (0 = from the network's extent)"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=0.0,
                minValue=0.0,
                maxValue=1.0e9,
            )
        )

    def processAlgorithm(
        self,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> dict[str, Any]:
        from geocomp.reports.monitoring import describe_finding

        first, second = read_solutions(
            [
                self.parameterAsFile(parameters, FIRST, context),
                self.parameterAsFile(parameters, SECOND, context),
            ]
        )
        network = read_optional_network(self.parameterAsFile(parameters, NETWORK, context))
        reference, objects = roles(
            network,
            self.parameterAsString(parameters, REFERENCE, context),
            self.parameterAsString(parameters, OBJECTS, context),
        )
        confidence = self.parameterAsDouble(parameters, CONFIDENCE, context)
        thresholds = read_thresholds(self.parameterAsFile(parameters, THRESHOLDS, context))
        feedback.setProgress(10)

        try:
            comparison = compare(first, second)
        except GeoCompError as error:
            raise fail(error) from error
        for finding in comparison.findings:
            feedback.pushWarning(describe_finding(finding.to_dict()))
        for record in comparison.transformations:
            feedback.pushInfo(
                self.tr("Transformed %1 at %2 into %3, accuracy %4 mm, common to every station.")
                .replace("%1", record.source)
                .replace("%2", localised(f"{record.source_epoch:.4f}"))
                .replace("%3", record.target)
                .replace("%4", localised(f"{1000.0 * record.accuracy:.1f}"))
            )
        datum = datum_of(self.parameterAsEnum(parameters, DATUM, context)) or default_datum(comparison)
        feedback.setProgress(30)

        try:
            check = check_reference(comparison, reference, datum=datum, confidence=confidence)
        except GeoCompError as error:
            raise fail(error) from error
        if not check.passed:
            document = refused_document(
                comparison,
                check,
                first,
                second,
                reference=reference,
                datum=datum,
                confidence=confidence,
                network=network,
            )
            outputs = self._write(parameters, context, document)
            raise self._refusal(check, outputs)

        try:
            analysis = analyse(comparison, reference, objects=objects, datum=datum, confidence=confidence)
        except GeoCompError as error:
            raise fail(error) from error
        feedback.setProgress(60)

        strained, note = None, "not_requested"
        if self.parameterAsBool(parameters, STRAIN, context):
            try:
                strained = strain(analysis)
            except ValidationError as error:
                note = error.code.split(".")[-1]
                feedback.pushInfo(self.tr("Strain was not computed: the object points do not span an area."))
        alerts = evaluate_alerts(thresholds, displacements=analysis.displacements)
        document = comparison_document(
            analysis,
            first,
            second,
            strain=strained,
            strain_note="" if strained is not None else note,
            thresholds=thresholds,
            alerts=alerts,
            network=network,
        )
        self._summarise(document, feedback)
        feedback.setProgress(80)

        outputs = self._write(parameters, context, document)
        outputs.update(self._layers(parameters, context, document, feedback))
        feedback.setProgress(100)
        return {
            REFERENCE_STABLE: True,
            GLOBAL_TEST_PASSED: bool(document["global_test"]["passed"]),
            SIGNIFICANT_COUNT: sum(1 for d in document["displacements"] if d["significant"]),
            ALERT_COUNT: len({a["station"] for a in document["alerts"] if a["exceeded"]}),
            **outputs,
        }

    # -- outputs -----------------------------------------------------------

    def _write(self, parameters, context, document) -> dict[str, Any]:
        from geocomp.reports.monitoring import MonitoringReportContext, render_monitoring_report

        analysis_path = write_json(self.parameterAsFileOutput(parameters, OUTPUT_ANALYSIS, context), document)
        html_path = self.parameterAsFileOutput(parameters, OUTPUT_HTML, context)
        if html_path:
            html, _omitted = render_monitoring_report(
                document,
                None,
                MonitoringReportContext(
                    qgis_version=Qgis.QGIS_VERSION,
                    exaggeration=self.parameterAsDouble(parameters, EXAGGERATION, context),
                ),
            )
            Path(html_path).write_text(html, encoding="utf-8")
        return {OUTPUT_ANALYSIS: analysis_path, OUTPUT_HTML: html_path}

    def _layers(self, parameters, context, document, feedback) -> dict[str, Any]:
        from geocomp.layers.builders import (
            displacement_ellipse_features,
            displacement_ellipse_layer_name,
            displacement_features,
            displacement_layer_name,
        )

        requested = self.parameterAsDouble(parameters, EXAGGERATION, context)
        factor = requested or displacement_exaggeration(document)
        if not document["display"]["positions"]:
            feedback.pushWarning(
                self.tr(
                    "The stations have no plan position, so nothing is drawn on the map. Give the "
                    "network document to place a heights-only network's stations."
                )
            )
        else:
            feedback.pushInfo(
                self.tr("Arrows and ellipses are drawn exaggerated %1x.").replace("%1", f"{factor:g}")
            )
        crs = QgsCoordinateReferenceSystem(document["display"]["crs"])
        return {
            OUTPUT_DISPLACEMENT_LAYER: write_styled_sink(
                self,
                parameters,
                context,
                OUTPUT_DISPLACEMENT_LAYER,
                style="displacements",
                geometry=QgsWkbTypes.Type.LineString,
                crs=crs,
                features=lambda: displacement_features(document, exaggeration=factor),
                layer_name=displacement_layer_name(document, exaggeration=factor),
            ),
            OUTPUT_DISPLACEMENT_ELLIPSE_LAYER: write_styled_sink(
                self,
                parameters,
                context,
                OUTPUT_DISPLACEMENT_ELLIPSE_LAYER,
                style="displacement_ellipses",
                geometry=QgsWkbTypes.Type.Polygon,
                crs=crs,
                features=lambda: displacement_ellipse_features(document, exaggeration=factor),
                layer_name=displacement_ellipse_layer_name(document, exaggeration=factor),
            ),
        }

    def _summarise(self, document, feedback) -> None:
        moved = [d["station"] for d in document["displacements"] if d["significant"]]
        feedback.pushInfo(
            self.tr("Significant motion at %1 of %2 stations: %3.")
            .replace("%1", str(len(moved)))
            .replace("%2", str(len(document["displacements"])))
            .replace("%3", ", ".join(moved) or self.tr("none"))
        )
        crossed = sorted({a["station"] for a in document["alerts"] if a["exceeded"]})
        if crossed:
            feedback.pushWarning(
                self.tr("Alert thresholds crossed at: %1.").replace("%1", ", ".join(crossed))
            )
        if document["mode"] != "rigorous":
            feedback.pushWarning(
                self.tr(
                    "The epochs were taken as independent; the displacements' uncertainty is "
                    "overstated if they share reference stations or products, so real motion may be "
                    "reported not significant."
                )
            )

    def _refusal(self, check, outputs) -> QgsProcessingException:
        from geocomp.services.messages import message_for

        error = ValidationError(
            "monitoring_reference_block_unstable",
            stations=list(check.implicated),
            statistic=round(check.test.test.statistic, 4),
            critical=round(check.test.test.critical_high or 0.0, 4),
            stable=list(check.stable),
        )
        written = [path for path in (outputs[OUTPUT_HTML], outputs[OUTPUT_ANALYSIS]) if path]
        text = message_for(error)
        if written:
            text += " " + self.tr("The localisation is recorded in: %1").replace("%1", ", ".join(written))
        return QgsProcessingException(text)
