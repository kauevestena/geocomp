# SPDX-License-Identifier: GPL-2.0-or-later
"""``geocomp:monitoring_time_series`` -- where each station has been, and how fast
it is going (``specs/14`` sections 6 and 7; FR-836 to FR-838).

Any number of epochs of one network: every station's offset from the first
epoch with that epoch's own uncertainty, referred to the reference block, and a
velocity per station by weighted least squares with its covariance and its
test. Written as a series document, a CSV of plottable rows, a velocity layer
and the monitoring report's series sections; the velocity layer carries the
series document's path, so the time-series panel shows a station's series when
it is selected on the map (FR-903).

**The block is tested at every epoch.** Each epoch is referred to the reference
block by an S-transformation, which is only right if the block held still; a
velocity measured against a pillar that moved in the third year is the pillar's
velocity, spread over the network. So each epoch's block is tested against the
first's, and the run refuses at the first epoch where it fails, naming it and
the stations -- as the two-epoch comparison does.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from qgis.core import (
    Qgis,
    QgsCoordinateReferenceSystem,
    QgsProcessing,
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFile,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterMultipleLayers,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
    QgsWkbTypes,
)

from geocomp.algorithms.base import GeoCompAlgorithm
from geocomp.algorithms.defaults import configured
from geocomp.algorithms.layer_outputs import LINE_SOURCE_TYPE, write_styled_sink
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
    check_reference,
    compare,
    default_datum,
    evaluate_alerts,
    series,
    series_document,
)
from geocomp.core.monitoring.document import SERIES_PROPERTY
from geocomp.core.number_format import localised
from geocomp.core.visualization.monitoring import velocity_exaggeration

__all__ = ["SERIES_PROPERTY", "MonitoringTimeSeriesAlgorithm"]

SOLUTIONS = "SOLUTIONS"
NETWORK = "NETWORK"
REFERENCE = "REFERENCE"
DATUM = "DATUM"
CONFIDENCE = "CONFIDENCE"
THRESHOLDS = "THRESHOLDS"
EXAGGERATION = "EXAGGERATION"
OUTPUT_SERIES = "OUTPUT_SERIES"
OUTPUT_CSV = "OUTPUT_CSV"
OUTPUT_HTML = "OUTPUT_HTML"
OUTPUT_VELOCITY_LAYER = "OUTPUT_VELOCITY_LAYER"
STATION_COUNT = "STATION_COUNT"
EPOCH_COUNT = "EPOCH_COUNT"
MOVING_COUNT = "MOVING_COUNT"
ALERT_COUNT = "ALERT_COUNT"



def _file_type() -> Any:
    """``QgsProcessingParameterMultipleLayers``'s file type, as QGIS 3 and 4 spell it."""
    if hasattr(Qgis, "ProcessingSourceType"):
        return Qgis.ProcessingSourceType.File
    return QgsProcessing.TypeFile


class MonitoringTimeSeriesAlgorithm(GeoCompAlgorithm):
    """A station's series across epochs, and its velocity (FR-836, FR-838)."""

    TR_CONTEXT = "MonitoringTimeSeriesAlgorithm"

    def displayName(self) -> str:
        return self.tr("Time series and velocities")

    def shortDescription(self) -> str:
        return self.tr("Every station's offsets across the epochs, and its velocity.")

    def help_body(self) -> str:
        return self.tr(
            "<p>Follows every station through any number of epochs: its offset from the first "
            "epoch with each epoch's own uncertainty, and its velocity by weighted least "
            "squares, with the velocity's uncertainty and a test of whether it differs from "
            "zero.</p>"
            "<p>Every epoch is referred to the <b>reference stations</b> by an "
            "S-transformation, and their congruency with the first epoch is tested at every "
            "epoch: a velocity measured against a pillar that moved is the pillar's. The run "
            "refuses at the first epoch where the block fails, and names it. Leave the field "
            "empty to take the stations marked REFERENCE in the network document; with none "
            "there either, the epochs are taken in their own datums, which is right only if "
            "they were all held the same way.</p>"
            "<p>The velocity layer is tied to its series: select a station on it and the "
            "time-series panel plots that station.</p>"
            "<p>The epochs are taken as independent, and the result is marked approximate.</p>"
            "<h3>Parameters</h3>"
            "<p><b>Solutions</b> &mdash; two or more solution documents of the same network, in "
            "any order; they are sorted by epoch.</p>"
            "<p><b>Alert thresholds</b> &mdash; a CSV file of <code>kind, limit, stations, "
            "group</code>; a <i>velocity</i> row sets a limit in metres a year on the "
            "horizontal speed, or the vertical rate of a heights-only series.</p>"
            "<p><b>Exaggeration</b> &mdash; the factor a year's motion is drawn at; 0 fits it "
            "to the network.</p>"
        )

    def initAlgorithm(self, config: dict[str, Any] | None = None) -> None:
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                SOLUTIONS, self.tr("Solutions, one per epoch"), layerType=_file_type()
            )
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
            QgsProcessingParameterEnum(
                DATUM, self.tr("Datum of the offsets"), options=datum_labels(), defaultValue=0
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
            QgsProcessingParameterFile(
                THRESHOLDS, self.tr("Alert thresholds (CSV)"), extension="csv", optional=True
            )
        )
        for name, label, filter_text in (
            (OUTPUT_SERIES, self.tr("Series document"), self.tr("GeoComp monitoring document (*.json)")),
            (OUTPUT_CSV, self.tr("Series table"), self.tr("CSV files (*.csv)")),
            (OUTPUT_HTML, self.tr("Monitoring report"), self.tr("HTML files (*.html)")),
        ):
            self.addParameter(
                QgsProcessingParameterFileDestination(
                    name, label, filter_text, optional=True, createByDefault=True
                )
            )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                OUTPUT_VELOCITY_LAYER,
                self.tr("Velocities (layer)"),
                type=LINE_SOURCE_TYPE,
                optional=True,
                createByDefault=True,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterNumber(
                EXAGGERATION,
                self.tr("Exaggeration of a year's motion (0 = from the network's extent)"),
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
        paths = self.parameterAsFileList(parameters, SOLUTIONS, context)
        solutions = sorted(read_solutions(paths), key=lambda s: s.epoch.decimal_year)
        if len(solutions) < 2:
            raise QgsProcessingException(
                self.tr("A series needs two epochs at least; %1 was given.").replace(
                    "%1", str(len(solutions))
                )
            )
        network = read_optional_network(self.parameterAsFile(parameters, NETWORK, context))
        reference, _objects = roles(
            network, self.parameterAsString(parameters, REFERENCE, context), "", required=False
        )
        confidence = self.parameterAsDouble(parameters, CONFIDENCE, context)
        thresholds = read_thresholds(self.parameterAsFile(parameters, THRESHOLDS, context))
        chosen = datum_of(self.parameterAsEnum(parameters, DATUM, context))
        feedback.setProgress(10)

        try:
            datum = chosen or default_datum(compare(solutions[0], solutions[1]))
            if reference:
                self._check_blocks(solutions, reference, datum, confidence, feedback)
            else:
                feedback.pushWarning(
                    self.tr(
                        "No reference stations: each epoch is taken in its own datum, which is right "
                        "only if every epoch was held the same way."
                    )
                )
            stations = series(
                solutions, reference=reference or None, datum=datum, confidence=confidence
            )
        except GeoCompError as error:
            raise fail(error) from error
        feedback.setProgress(60)

        alerts = evaluate_alerts(thresholds, series=stations)
        document = series_document(
            stations,
            solutions,
            reference=reference or None,
            datum=datum,
            confidence=confidence,
            thresholds=thresholds,
            alerts=alerts,
            network=network,
        )
        moving = [
            s["station"]
            for s in document["stations"]
            if s["velocity_test"] and not s["velocity_test"]["passed"]
        ]
        feedback.pushInfo(
            self.tr("%1 stations over %2 epochs; velocity significant at: %3.")
            .replace("%1", str(len(document["stations"])))
            .replace("%2", str(len(solutions)))
            .replace("%3", ", ".join(moving) or self.tr("none"))
        )
        crossed = sorted({a["station"] for a in document["alerts"] if a["exceeded"]})
        if crossed:
            feedback.pushWarning(
                self.tr("Velocity thresholds crossed at: %1.").replace("%1", ", ".join(crossed))
            )

        outputs = self._write(parameters, context, document, stations)
        outputs.update(self._layer(parameters, context, document, outputs[OUTPUT_SERIES], feedback))
        feedback.setProgress(100)
        return {
            STATION_COUNT: len(document["stations"]),
            EPOCH_COUNT: len(solutions),
            MOVING_COUNT: len(moving),
            ALERT_COUNT: len(crossed),
            **outputs,
        }

    def _check_blocks(self, solutions, reference, datum, confidence, feedback) -> None:
        """The block's congruency between the first epoch and every later one."""
        from geocomp.services.messages import message_for

        first = solutions[0]
        for later in solutions[1:]:
            comparison = compare(first, later)
            present = [s for s in reference if s in comparison.stations]
            check = check_reference(comparison, present, datum=datum, confidence=confidence)
            if not check.passed:
                error = ValidationError(
                    "monitoring_reference_block_unstable",
                    stations=list(check.implicated),
                    statistic=round(check.test.test.statistic, 4),
                    critical=round(check.test.test.critical_high or 0.0, 4),
                    stable=list(check.stable),
                )
                raise QgsProcessingException(
                    self.tr("At the epoch of '%1' (%2): ")
                    .replace("%1", later.id)
                    .replace("%2", localised(f"{later.epoch.decimal_year:.4f}"))
                    + message_for(error)
                )
            feedback.pushInfo(
                self.tr("Reference block congruent between %1 and %2.")
                .replace("%1", localised(f"{first.epoch.decimal_year:.4f}"))
                .replace("%2", localised(f"{later.epoch.decimal_year:.4f}"))
            )

    def _write(self, parameters, context, document, stations) -> dict[str, Any]:
        from geocomp.reports.monitoring import MonitoringReportContext, render_monitoring_report

        series_path = write_json(self.parameterAsFileOutput(parameters, OUTPUT_SERIES, context), document)
        csv_path = self.parameterAsFileOutput(parameters, OUTPUT_CSV, context)
        if csv_path:
            fields = ("station", "solution", "epoch", "component", "offset", "std_dev")
            with open(csv_path, "w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                for station in stations:
                    writer.writerows(station.to_rows())
        html_path = self.parameterAsFileOutput(parameters, OUTPUT_HTML, context)
        if html_path:
            html, _omitted = render_monitoring_report(
                None, document, MonitoringReportContext(qgis_version=Qgis.QGIS_VERSION)
            )
            Path(html_path).write_text(html, encoding="utf-8")
        return {OUTPUT_SERIES: series_path, OUTPUT_CSV: csv_path, OUTPUT_HTML: html_path}

    def _layer(self, parameters, context, document, series_path, feedback) -> dict[str, Any]:
        from geocomp.layers.builders import velocity_features, velocity_layer_name

        requested = self.parameterAsDouble(parameters, EXAGGERATION, context)
        factor = requested or velocity_exaggeration(document)
        if not document["display"]["positions"]:
            feedback.pushWarning(
                self.tr(
                    "The stations have no plan position, so nothing is drawn on the map. Give the "
                    "network document to place a heights-only network's stations."
                )
            )
        return {
            OUTPUT_VELOCITY_LAYER: write_styled_sink(
                self,
                parameters,
                context,
                OUTPUT_VELOCITY_LAYER,
                style="velocities",
                geometry=QgsWkbTypes.Type.LineString,
                crs=QgsCoordinateReferenceSystem(document["display"]["crs"]),
                features=lambda: velocity_features(document, exaggeration=factor),
                layer_name=velocity_layer_name(exaggeration=factor),
                properties={SERIES_PROPERTY: str(Path(series_path).resolve())} if series_path else None,
            )
        }
