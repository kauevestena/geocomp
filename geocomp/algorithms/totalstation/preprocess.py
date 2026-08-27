# SPDX-License-Identifier: GPL-2.0-or-later
"""``geocomp:totalstation_preprocess`` -- the generalised pre-processing chain.

FR-400 to FR-405 and FR-412. ``specs/09-module-total-station.md`` section 2.

    raw readings -> face reduction -> instrument corrections -> atmospheric
      correction -> EDM corrections -> geometric reductions -> observations

Uncertainty is propagated at every stage; no stage produces a bare float.

**The diagnostics are the reason to run this rather than just averaging.** A
face pair carries information the mean throws away -- the collimation, the
vertical index error, and whether the two faces agreed on the distance -- and
RD-01 contains a face-pair distance discrepancy of exactly one metre that
averaging buries silently. Reporting it is what turns a reduction into a check.
"""

from __future__ import annotations

import csv
import json
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
)

from geocomp.algorithms.base import GeoCompAlgorithm
from geocomp.algorithms.reporting import escape, format_number, render_document, render_table
from geocomp.algorithms.totalstation.common import (
    findings_table,
    load_profiles,
    read_readings,
    summarise_findings,
)
from geocomp.core.errors import GeoCompError
from geocomp.core.techniques.total_station import (
    Atmosphere,
    PreprocessingOptions,
    preprocess_setup,
)
from geocomp.core.techniques.total_station.face import DEFAULT_COLLIMATION_TOLERANCE

__all__ = ["PreprocessAlgorithm"]

READINGS = "READINGS"
PROFILES = "PROFILES"
TEMPERATURE = "TEMPERATURE"
PRESSURE = "PRESSURE"
HUMIDITY = "HUMIDITY"
TEMPERATURE_SIGMA = "TEMPERATURE_SIGMA"
PRESSURE_SIGMA = "PRESSURE_SIGMA"
APPLY_ATMOSPHERIC = "APPLY_ATMOSPHERIC"
COLLIMATION_TOLERANCE = "COLLIMATION_TOLERANCE"
DISTANCE_TOLERANCE = "DISTANCE_TOLERANCE"
CORRELATION = "CORRELATION"
OUTPUT_REDUCED = "OUTPUT_REDUCED"
OUTPUT_HTML = "OUTPUT_HTML"
OUTPUT_CSV = "OUTPUT_CSV"
POINTING_COUNT = "POINTING_COUNT"
USABLE_COUNT = "USABLE_COUNT"
BLOCKING_COUNT = "BLOCKING_COUNT"


class PreprocessAlgorithm(GeoCompAlgorithm):
    """Reduce raw field-book readings to corrected observations."""

    TR_CONTEXT = "PreprocessAlgorithm"

    def displayName(self) -> str:
        return self.tr("Generalised pre-processing")

    def shortDescription(self) -> str:
        return self.tr(
            "Reduce face pairs, apply the instrument, atmospheric and EDM corrections, "
            "and report what the pairs revealed."
        )

    def help_body(self) -> str:
        return self.tr(
            "<p>Takes the readings produced by Import field book and runs the whole "
            "pre-processing chain: face reduction, instrument corrections, the "
            "first-velocity atmospheric correction, the EDM corrections, and the basic "
            "reductions to a horizontal distance and a height difference.</p>"
            "<p>Every stage propagates covariance, so each result carries an uncertainty "
            "rather than a bare number. The distance and the zenith angle of one pointing "
            "are correlated through the common sighting, and that correlation is kept.</p>"
            "<p><b>The diagnostics are the reason to run this rather than just averaging the "
            "two faces.</b> A face pair reveals the horizontal collimation, the vertical "
            "index error and whether the two faces agreed on the distance. A pair whose "
            "distances disagree beyond the instrument's own precision is flagged as blocking "
            "and left out of the observations: the mean of two distances a metre apart is "
            "not a measurement of anything, and passing it on would let a known-bad number "
            "acquire a residual as though it were real.</p>"
            "<p>Corrections the instrument already applied are not applied again. Applying a "
            "prism constant twice is a silent error of twice the constant, and nothing "
            "downstream can detect it.</p>"
            "<h3>Parameters</h3>"
            "<p><b>Readings</b> &mdash; the document Import field book produced. "
            "<b>Instrument profiles</b> &mdash; a profile library (JSON); empty uses a generic "
            "total station.</p>"
            "<p><b>Temperature</b> (&deg;C), <b>pressure</b> (hPa) and <b>relative humidity</b> "
            "(%) &mdash; the conditions the distances were measured in. Their uncertainties "
            "propagate: a &plusmn; 2 &deg;C error is about &plusmn; 2 ppm, which is 2 mm over a "
            "kilometre and nothing at all over twenty metres. The propagation makes that "
            "visible instead of assumed.</p>"
            "<p><b>Apply the atmospheric correction</b> &mdash; unset it to skip the stage "
            "entirely, which is a legitimate choice on short sights and one worth making "
            "explicitly.</p>"
            "<p><b>Collimation tolerance</b> (rad) and <b>face distance tolerance</b> (m) "
            "&mdash; beyond these a pair is reported. A distance tolerance of 0 derives it "
            "from the instrument's own EDM specification, which is the right threshold.</p>"
            "<p><b>Distance/zenith correlation</b> &mdash; between -1 and 1, or -2 for "
            "unknown. Unknown is recorded as an assumption rather than silently treated as "
            "zero, and the result is marked approximate.</p>"
            "<h3>Outputs</h3>"
            "<p><b>Reduced observations</b> &mdash; a JSON document. <b>Report</b> &mdash; "
            "HTML, with the per-pair diagnostics. <b>Reductions</b> &mdash; CSV. Scalars: "
            "<code>POINTING_COUNT</code>, <code>USABLE_COUNT</code> and "
            "<code>BLOCKING_COUNT</code>.</p>"
        )

    def initAlgorithm(self, config: dict[str, Any] | None = None) -> None:
        self.addParameter(
            QgsProcessingParameterFile(READINGS, self.tr("Readings"), extension="json")
        )
        self.addParameter(
            QgsProcessingParameterFile(
                PROFILES, self.tr("Instrument profiles"), extension="json", optional=True
            )
        )
        for name, label, default, minimum, maximum in (
            (TEMPERATURE, self.tr("Temperature (°C)"), 20.0, -90.0, 60.0),
            (PRESSURE, self.tr("Pressure (hPa)"), 1013.25, 100.0, 1100.0),
            (HUMIDITY, self.tr("Relative humidity (%)"), 60.0, 0.0, 100.0),
        ):
            self.addParameter(
                QgsProcessingParameterNumber(
                    name,
                    label,
                    type=QgsProcessingParameterNumber.Type.Double,
                    defaultValue=default,
                    minValue=minimum,
                    maxValue=maximum,
                )
            )
        self.addAdvancedParameter(
            QgsProcessingParameterNumber(
                TEMPERATURE_SIGMA,
                self.tr("Temperature uncertainty (°C)"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=5.0,
                minValue=0.0,
                maxValue=50.0,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterNumber(
                PRESSURE_SIGMA,
                self.tr("Pressure uncertainty (hPa)"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=10.0,
                minValue=0.0,
                maxValue=200.0,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterBoolean(
                APPLY_ATMOSPHERIC, self.tr("Apply the atmospheric correction"), defaultValue=True
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterNumber(
                COLLIMATION_TOLERANCE,
                self.tr("Collimation tolerance (rad)"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=DEFAULT_COLLIMATION_TOLERANCE,
                minValue=0.0,
                maxValue=0.1,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterNumber(
                DISTANCE_TOLERANCE,
                self.tr("Face distance tolerance (m, 0 = from the instrument)"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=0.0,
                minValue=0.0,
                maxValue=10.0,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterNumber(
                CORRELATION,
                self.tr("Distance/zenith correlation (-2 = unknown)"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=-2.0,
                minValue=-2.0,
                maxValue=1.0,
            )
        )
        self.addParameter(
            QgsProcessingParameterFileDestination(
                OUTPUT_REDUCED,
                self.tr("Reduced observations"),
                self.tr("GeoComp reductions (*.json)"),
                optional=True,
                createByDefault=True,
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
                self.tr("Reductions"),
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
        setups = read_readings(self.parameterAsFile(parameters, READINGS, context))
        library = load_profiles(self.parameterAsFile(parameters, PROFILES, context))

        correlation = self.parameterAsDouble(parameters, CORRELATION, context)
        options = PreprocessingOptions(
            collimation_tolerance=self.parameterAsDouble(
                parameters, COLLIMATION_TOLERANCE, context
            ),
            distance_tolerance=(
                self.parameterAsDouble(parameters, DISTANCE_TOLERANCE, context) or None
            ),
            distance_zenith_correlation=None if correlation < -1.0 else correlation,
            apply_atmospheric=self.parameterAsBool(parameters, APPLY_ATMOSPHERIC, context),
        )
        atmosphere = self._atmosphere(parameters, context) if options.apply_atmospheric else None

        results = []
        for index, setup in enumerate(setups, start=1):
            if feedback.isCanceled():
                return {}
            feedback.pushInfo(
                self.tr("Reducing station %1…").replace("%1", setup.station)
            )
            try:
                results.append(
                    preprocess_setup(setup, library, atmosphere=atmosphere, options=options)
                )
            except GeoCompError as exc:
                from geocomp.services.messages import message_for

                raise QgsProcessingException(message_for(exc)) from exc
            feedback.setProgress(70.0 * index / len(setups))

        findings = tuple(f for result in results for f in result.all_findings)
        blocking, _warnings = summarise_findings(findings, feedback)

        pointings = sum(len(result.pointings) for result in results)
        usable = sum(len(result.usable) for result in results)
        feedback.pushInfo(
            self.tr("%1 pointing(s) reduced, %2 usable.")
            .replace("%1", str(pointings))
            .replace("%2", str(usable))
        )

        feedback.setProgress(85)
        outputs = self._write(parameters, context, results, findings, options)
        feedback.setProgress(100)

        return {
            POINTING_COUNT: pointings,
            USABLE_COUNT: usable,
            BLOCKING_COUNT: blocking,
            **outputs,
        }

    def _atmosphere(self, parameters, context) -> Atmosphere:
        return Atmosphere.from_field_units(
            self.parameterAsDouble(parameters, TEMPERATURE, context),
            self.parameterAsDouble(parameters, PRESSURE, context),
            self.parameterAsDouble(parameters, HUMIDITY, context),
            temperature_sigma=self.parameterAsDouble(parameters, TEMPERATURE_SIGMA, context),
            pressure_sigma_hpa=self.parameterAsDouble(parameters, PRESSURE_SIGMA, context),
            # Humidity contributes under one part per million across its whole
            # range, so a generous uncertainty on it costs nothing and saves
            # asking the user for a figure they rarely have.
            humidity_sigma_percent=20.0,
        )

    # -- outputs ---------------------------------------------------------

    def _write(self, parameters, context, results, findings, options) -> dict[str, Any]:
        reduced = self.parameterAsFileOutput(parameters, OUTPUT_REDUCED, context)
        if reduced:
            with open(reduced, "w", encoding="utf-8") as handle:
                json.dump(_reductions_document(results), handle, indent=2, sort_keys=True)
                handle.write("\n")

        html_target = self.parameterAsFileOutput(parameters, OUTPUT_HTML, context)
        if html_target:
            with open(html_target, "w", encoding="utf-8") as handle:
                handle.write(self._render(results, findings, options))

        csv_target = self.parameterAsFileOutput(parameters, OUTPUT_CSV, context)
        if csv_target:
            with open(csv_target, "w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(
                    [
                        "station", "target", "horizontal_rad", "zenith_rad", "slope_distance",
                        "horizontal_distance", "height_difference", "collimation_rad",
                        "vertical_index_rad", "face_distance_difference", "usable",
                    ]
                )
                for result in results:
                    for pointing in result.pointings:
                        basic = pointing.basic
                        writer.writerow(
                            [
                                result.station,
                                pointing.target,
                                repr(pointing.reduction.horizontal.value),
                                repr(pointing.reduction.zenith.value),
                                repr(pointing.reduction.distance.value)
                                if pointing.reduction.distance
                                else "",
                                repr(basic.horizontal_distance.value) if basic else "",
                                repr(basic.height_difference.value) if basic else "",
                                repr(pointing.reduction.collimation.value),
                                repr(pointing.reduction.vertical_index.value),
                                repr(pointing.reduction.distance_difference)
                                if pointing.reduction.distance_difference is not None
                                else "",
                                "yes" if pointing.is_usable else "no",
                            ]
                        )

        return {OUTPUT_REDUCED: reduced, OUTPUT_HTML: html_target, OUTPUT_CSV: csv_target}

    def _render(self, results, findings, options) -> str:
        body = [f"<h2>{escape(self.tr('Reduced pointings'))}</h2>"]
        rows = []
        for result in results:
            for pointing in result.pointings:
                basic = pointing.basic
                rows.append(
                    [
                        escape(result.station),
                        escape(pointing.target),
                        format_number(math.degrees(pointing.reduction.horizontal.value), 6),
                        format_number(math.degrees(pointing.reduction.zenith.value), 6),
                        format_number(basic.horizontal_distance.value, 4) if basic else "—",
                        format_number(basic.horizontal_distance.std_dev * 1000.0, 2)
                        if basic
                        else "—",
                        format_number(basic.height_difference.value, 4) if basic else "—",
                        escape(self.tr("yes") if pointing.is_usable else self.tr("no")),
                    ]
                )
        body.append(
            render_table(
                [
                    escape(self.tr("Station")),
                    escape(self.tr("Target")),
                    escape(self.tr("Direction (°)")),
                    escape(self.tr("Zenith (°)")),
                    escape(self.tr("Horizontal distance (m)")),
                    escape(self.tr("Std dev (mm)")),
                    escape(self.tr("Height difference (m)")),
                    escape(self.tr("Usable")),
                ],
                rows,
            )
        )

        body.append(f"<h2>{escape(self.tr('Instrumental diagnostics'))}</h2>")
        body.append(
            render_table(
                [
                    escape(self.tr("Station")),
                    escape(self.tr("Face pairs")),
                    escape(self.tr("Mean collimation (\")")),
                    escape(self.tr("Collimation spread (\")")),
                    escape(self.tr("Mean index error (\")")),
                ],
                [
                    [
                        escape(result.station),
                        escape(result.diagnostics.pair_count),
                        format_number(
                            math.degrees(result.diagnostics.collimation_mean) * 3600.0, 2
                        ),
                        format_number(
                            math.degrees(result.diagnostics.collimation_spread) * 3600.0, 2
                        ),
                        format_number(
                            math.degrees(result.diagnostics.vertical_index_mean) * 3600.0, 2
                        ),
                    ]
                    for result in results
                ],
            )
        )

        if options.distance_zenith_correlation is None:
            from geocomp.algorithms.reporting import render_note

            body.append(
                render_note(
                    self.tr(
                        "The correlation between each distance and its zenith angle was not "
                        "supplied, so they were treated as independent and the results are "
                        "marked approximate."
                    )
                )
            )

        body.append(f"<h2>{escape(self.tr('Findings'))}</h2>")
        body.append(findings_table(findings))

        return render_document(
            self.tr("Pre-processing report"),
            body,
            footer=escape(self.tr("Generated by GeoComp — geocomp:totalstation_preprocess")),
        )


def _reductions_document(results) -> dict[str, Any]:
    """Reduced pointings, for the network algorithm to consume."""
    return {
        "kind": "geocomp.reductions",
        "version": 1,
        "setups": [
            {
                "station": result.station,
                "pointings": [
                    {
                        "target": pointing.target,
                        "horizontal": pointing.reduction.horizontal.to_dict(),
                        "zenith": pointing.reduction.zenith.to_dict(),
                        "distance": (
                            pointing.reduction.distance.to_dict()
                            if pointing.reduction.distance
                            else None
                        ),
                        "horizontal_distance": (
                            pointing.basic.horizontal_distance.to_dict()
                            if pointing.basic
                            else None
                        ),
                        "height_difference": (
                            pointing.basic.height_difference.to_dict()
                            if pointing.basic
                            else None
                        ),
                        "usable": pointing.is_usable,
                    }
                    for pointing in result.pointings
                ],
            }
            for result in results
        ],
    }
