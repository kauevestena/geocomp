# SPDX-License-Identifier: GPL-2.0-or-later
"""``geocomp:gravimetry_preprocess`` -- scale, tide and drift (FR-701).

``specs/12-module-gravimetry.md`` section 4.

A gravimeter file -- Scintrex CG-5, ZLS Burris, or a plain CSV -- becomes
readings on the calibrated scale, with the solid-Earth tide removed (once: an
instrument that applied its own keeps it) and reduced to the mark. The drift is
**shown, not applied**: each session's drift as its base readings give it, and
whether its occupations determine it jointly. Removing it is the network's
business, because a drift estimated there with the station values uses every
re-occupation rather than only the base's (FR-702).
"""

from __future__ import annotations

import csv
from typing import Any

from qgis.core import (
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFile,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterNumber,
)

from geocomp.algorithms.base import GeoCompAlgorithm
from geocomp.algorithms.gravimetry.common import (
    DRIFT_DEGREE_KEY,
    PRECISION_FLOOR_KEY,
    TIDE_AMPLIFICATION_KEY,
    TIDE_MODEL_KEY,
    display_decimals,
    display_unit,
    gravimeter_library,
    gravimeter_setting,
    source_name,
    tide_model_from,
    to_display,
    translate_error,
    unit_symbol,
    with_sensor_height,
    write_readings_document,
)
from geocomp.algorithms.reporting import format_number
from geocomp.core.errors import GeoCompError
from geocomp.core.techniques.gravimetry import (
    MODEL_UNCERTAINTY,
    DriftOptions,
    ReductionOptions,
    drift_previews,
    group_occupations,
    reduce_readings,
)
from geocomp.core.units import METRES_PER_SECOND_SQUARED_PER_MGAL as MGAL
from geocomp.io.gravimeter_files import read_gravimeter_file

__all__ = ["GravimetryPreprocessAlgorithm"]

READINGS = "READINGS"
PROFILES = "PROFILES"
PRECISION_FLOOR = "PRECISION_FLOOR"
SENSOR_HEIGHT = "SENSOR_HEIGHT"
SENSOR_HEIGHT_SIGMA = "SENSOR_HEIGHT_SIGMA"
REPLACE_TIDE = "REPLACE_TIDE"
UTC_OFFSET = "UTC_OFFSET"
TIDE_MODEL = "TIDE_MODEL"
AMPLIFICATION = "AMPLIFICATION"
DRIFT_DEGREE = "DRIFT_DEGREE"
OUTPUT_READINGS = "OUTPUT_READINGS"
OUTPUT_CSV = "OUTPUT_CSV"
OUTPUT_DRIFT = "OUTPUT_DRIFT"
READING_COUNT = "READING_COUNT"
OCCUPATION_COUNT = "OCCUPATION_COUNT"
SESSION_COUNT = "SESSION_COUNT"
UNESTIMABLE_SESSIONS = "UNESTIMABLE_SESSIONS"
LARGEST_TIDE = "LARGEST_TIDE"

#: The settings' tide-model values, in the order the enum parameter lists them.
TIDE_MODELS = ("longman_1959", "none")


class GravimetryPreprocessAlgorithm(GeoCompAlgorithm):
    """Scale, de-tide and reduce a gravimeter file, and preview each session's drift."""

    TR_CONTEXT = "GravimetryPreprocessAlgorithm"

    def displayName(self) -> str:
        return self.tr("Pre-processing (scale, tide, drift)")

    def shortDescription(self) -> str:
        return self.tr(
            "Read a gravimeter file, apply its calibration, remove the tide, and show each "
            "session's drift."
        )

    def help_body(self) -> str:
        return self.tr(
            "<p>Reads a relative gravimeter file and reduces every reading: through the "
            "instrument's <b>calibration</b>, with the <b>solid-Earth tide</b> removed, and "
            "to the <b>mark</b>. The result is a document the network adjustment reads.</p>"
            "<p><b>Formats.</b> A Scintrex CG-5 text export, whose header gives the "
            "location, the clock's GMT difference and whether the instrument removed the tide "
            "itself; a ZLS Burris export; or a CSV with the columns <code>station</code>, "
            "<code>time</code> (ISO 8601 with its UTC offset) and <code>reading_mgal</code>, "
            "and optionally <code>sd_mgal</code>, <code>instrument</code>, "
            "<code>session</code>, <code>latitude_deg</code>, <code>longitude_deg</code>, "
            "<code>height_m</code>, <code>sensor_height_m</code> and "
            "<code>tide_applied</code>. The format is recognised from the content.</p>"
            "<p><b>The tide is removed once.</b> An instrument that applied its own "
            "correction keeps it. Ask for GeoComp's instead and the instrument's is added "
            "back first; that needs the file's times in UTC, and GeoComp settles which way a "
            "CG-5's GMT difference runs by comparing the instrument's tide with its own "
            "under both readings. Longman's model agrees with ETERNA to about 1.5 µGal, and "
            "that figure is carried as the tide's uncertainty.</p>"
            "<p><b>Drift is shown here and estimated in the network.</b> For each session "
            "the log and the drift table give the drift its base readings show, and whether "
            "the session's re-occupations let the network estimate it jointly with the "
            "station values. Nothing is subtracted from the readings.</p>"
            "<h3>Parameters</h3>"
            "<p><b>Gravimeter file</b>. <b>Gravimeter profiles</b> &mdash; a profile library "
            "whose gravimeters carry each instrument's calibration table and factor, "
            "keyed by the instrument name the file uses (for a CG-5, <code>CG-5</code> and "
            "its serial number, e.g. <code>CG-5 40236</code>). Without one, each "
            "instrument's own scale is used, and the result is labelled approximate for "
            "it.</p>"
            "<p><b>Precision floor</b> (mGal) &mdash; added in quadrature to each reading's "
            "own precision, for what that figure knows nothing of: tilt, temperature, "
            "transport. A CG-5's precision is <code>SD / &radic;DUR</code>; a Burris states "
            "none and takes the floor alone. Zero adds nothing.</p>"
            "<p><b>Sensor height</b> (m) &mdash; above the mark, for readings that do not "
            "carry their own. Left empty, readings are taken to refer to the mark, and the "
            "notes say so: an absolute value quoted at the mark and readings taken 20 cm "
            "above it differ by about 60 µGal.</p>"
            "<p><b>Replace the instrument's tide</b> &mdash; as above. <b>UTC offset</b> "
            "(hours, advanced) &mdash; the file's local time minus UTC, when it should not be "
            "inferred.</p>"
            "<p>The tide model, the gravimetric factor and the drift degree default to the "
            "Gravimeter settings.</p>"
            "<h3>Outputs</h3>"
            "<p><b>Reduced readings</b> &mdash; JSON, in SI, with the profiles the readings "
            "were reduced with. <b>Corrections</b> &mdash; CSV, one row per reading, in the "
            "display unit. <b>Drift</b> &mdash; CSV, one row per session; the coefficients "
            "are per hour to the power of the degree. Scalars: <code>READING_COUNT</code>, "
            "<code>OCCUPATION_COUNT</code>, <code>SESSION_COUNT</code>, "
            "<code>UNESTIMABLE_SESSIONS</code> (sessions whose drift the network cannot "
            "estimate jointly) and <code>LARGEST_TIDE</code> in m/s².</p>"
        )

    def initAlgorithm(self, config: dict[str, Any] | None = None) -> None:
        self.addParameter(
            QgsProcessingParameterFile(READINGS, self.tr("Gravimeter file"))
        )
        self.addParameter(
            QgsProcessingParameterFile(
                PROFILES, self.tr("Gravimeter profiles"), extension="json", optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                PRECISION_FLOOR,
                self.tr("Precision floor (mGal)"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=float(gravimeter_setting(PRECISION_FLOOR_KEY)) / MGAL,
                minValue=0.0,
                maxValue=1.0,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                SENSOR_HEIGHT,
                self.tr("Sensor height above the mark (m)"),
                type=QgsProcessingParameterNumber.Type.Double,
                optional=True,
                minValue=0.0,
                maxValue=5.0,
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                REPLACE_TIDE,
                self.tr("Replace the instrument's tide correction with GeoComp's"),
                defaultValue=False,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterNumber(
                SENSOR_HEIGHT_SIGMA,
                self.tr("Sensor height standard deviation (m)"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=0.0,
                minValue=0.0,
                maxValue=0.5,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterNumber(
                UTC_OFFSET,
                self.tr("Local time minus UTC (hours)"),
                type=QgsProcessingParameterNumber.Type.Double,
                optional=True,
                minValue=-14.0,
                maxValue=14.0,
            )
        )
        configured = gravimeter_setting(TIDE_MODEL_KEY)
        self.addAdvancedParameter(
            QgsProcessingParameterEnum(
                TIDE_MODEL,
                self.tr("Tide model"),
                options=[
                    self.tr("Longman (1959)"),
                    self.tr("None (every instrument applies its own)"),
                ],
                defaultValue=TIDE_MODELS.index(configured) if configured in TIDE_MODELS else 0,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterNumber(
                AMPLIFICATION,
                self.tr("Gravimetric factor (tide amplification)"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=float(gravimeter_setting(TIDE_AMPLIFICATION_KEY)),
                minValue=1.0,
                maxValue=1.3,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterNumber(
                DRIFT_DEGREE,
                self.tr("Drift polynomial degree"),
                type=QgsProcessingParameterNumber.Type.Integer,
                defaultValue=int(gravimeter_setting(DRIFT_DEGREE_KEY)),
                minValue=1,
                maxValue=3,
            )
        )
        for name, label, filter_text, by_default in (
            (
                OUTPUT_READINGS,
                self.tr("Reduced readings"),
                self.tr("GeoComp gravity readings (*.json)"),
                True,
            ),
            (OUTPUT_CSV, self.tr("Corrections"), self.tr("CSV files (*.csv)"), True),
            (OUTPUT_DRIFT, self.tr("Drift"), self.tr("CSV files (*.csv)"), False),
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
        path = self.parameterAsFile(parameters, READINGS, context)
        floor = self.parameterAsDouble(parameters, PRECISION_FLOOR, context) * MGAL
        replace_tide = self.parameterAsBool(parameters, REPLACE_TIDE, context)
        offset = (
            None
            if parameters.get(UTC_OFFSET) in (None, "")
            else self.parameterAsDouble(parameters, UTC_OFFSET, context)
        )
        height = (
            None
            if parameters.get(SENSOR_HEIGHT) in (None, "")
            else self.parameterAsDouble(parameters, SENSOR_HEIGHT, context)
        )
        height_sigma = self.parameterAsDouble(parameters, SENSOR_HEIGHT_SIGMA, context)
        tide_value = TIDE_MODELS[self.parameterAsEnum(parameters, TIDE_MODEL, context)]
        amplification = self.parameterAsDouble(parameters, AMPLIFICATION, context)
        degree = self.parameterAsInt(parameters, DRIFT_DEGREE, context)

        try:
            loaded = read_gravimeter_file(
                path,
                additive_sigma=floor,
                replace_tide=replace_tide,
                utc_offset_hours=offset,
            )
        except GeoCompError as exc:
            raise QgsProcessingException(translate_error(exc)) from exc
        feedback.setProgress(20)

        notes = list(loaded.notes)
        library = gravimeter_library(
            self.parameterAsFile(parameters, PROFILES, context),
            loaded.instruments,
            floor,
            notes,
        )
        readings = with_sensor_height(loaded.readings, height, height_sigma)
        options = ReductionOptions(
            tide_model=tide_model_from(tide_value), amplification=amplification
        )
        drift = DriftOptions(degree=degree)
        try:
            reduced = reduce_readings(readings, library, options)
            previews = drift_previews(reduced, drift)
            occupations = group_occupations(reduced)
        except GeoCompError as exc:
            raise QgsProcessingException(translate_error(exc)) from exc
        if feedback.isCanceled():
            return {}
        feedback.setProgress(60)

        unit = display_unit()
        for note in notes:
            feedback.pushInfo(note)
        unestimable = self._push_drift(previews, unit, feedback)

        write_readings_document(
            self.parameterAsFileOutput(parameters, OUTPUT_READINGS, context),
            reduced=reduced,
            library=library,
            source=source_name(path),
            file_format=loaded.format.value,
            reduction={
                "tide_model": tide_value,
                "amplification": amplification,
                "tide_uncertainty": MODEL_UNCERTAINTY if tide_value != "none" else 0.0,
                "precision_floor": floor,
                "replace_tide": replace_tide,
                "utc_offset_hours": offset,
                "sensor_height": height,
                "sensor_height_sigma": height_sigma if height is not None else None,
                "drift_degree": degree,
            },
            notes=notes,
        )
        self._write_corrections(parameters, context, reduced, unit)
        self._write_drift(parameters, context, previews, unit, degree)
        feedback.setProgress(100)

        tides = [abs(item.tide.value) for item in reduced if item.tide is not None]
        return {
            READING_COUNT: len(reduced),
            OCCUPATION_COUNT: len(occupations),
            SESSION_COUNT: len(previews),
            UNESTIMABLE_SESSIONS: unestimable,
            LARGEST_TIDE: max(tides) if tides else 0.0,
            OUTPUT_READINGS: self.parameterAsFileOutput(parameters, OUTPUT_READINGS, context),
            OUTPUT_CSV: self.parameterAsFileOutput(parameters, OUTPUT_CSV, context),
            OUTPUT_DRIFT: self.parameterAsFileOutput(parameters, OUTPUT_DRIFT, context),
        }

    # -- outputs ---------------------------------------------------------

    def _push_drift(self, previews, unit, feedback) -> int:
        """Say what each session's drift looks like; return how many cannot be estimated."""
        unestimable = 0
        decimals = display_decimals(unit) + 1
        for preview in previews:
            if preview.estimate is not None:
                rate = preview.estimate.coefficients[0]
                feedback.pushInfo(
                    self.tr("Session %1: %2 ± %3 %4 per hour from %5 readings of %6.")
                    .replace("%1", preview.session)
                    .replace("%2", format_number(to_display(rate.value, unit), decimals))
                    .replace("%3", format_number(to_display(rate.std_dev, unit), decimals))
                    .replace("%4", unit_symbol(unit))
                    .replace("%5", str(preview.base_occupations))
                    .replace("%6", preview.base_station)
                )
            if not preview.estimable:
                unestimable += 1
                feedback.pushWarning(
                    self.tr(
                        "Session %1 re-occupies no station at enough different times: the "
                        "network cannot estimate its drift with the station values. "
                        "Pre-correct it from a base, or re-occupy a station."
                    ).replace("%1", preview.session)
                )
        return unestimable

    def _write_corrections(self, parameters, context, reduced, unit) -> None:
        path = self.parameterAsFileOutput(parameters, OUTPUT_CSV, context)
        if not path:
            return
        decimals = display_decimals(unit) + 2
        symbol = unit_symbol(unit).replace("µ", "u").lower()

        def shown(value: float | None) -> str:
            return "" if value is None else f"{to_display(value, unit):.{decimals}f}"

        with open(path, "w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                [
                    "reading",
                    "station",
                    "session",
                    "instrument",
                    "time_utc",
                    f"scaled_{symbol}",
                    f"tide_{symbol}",
                    f"to_mark_{symbol}",
                    f"reduced_{symbol}",
                    f"sigma_{symbol}",
                    "uncertainty",
                ]
            )
            for item in reduced:
                tide = item.tide.value if item.tide is not None else None
                to_mark = item.to_mark.value if item.to_mark is not None else None
                scaled = item.gravity.value - (tide or 0.0) - (to_mark or 0.0)
                writer.writerow(
                    [
                        item.reading.id,
                        item.reading.station,
                        item.reading.session,
                        item.reading.instrument,
                        item.reading.instant.isoformat(),
                        shown(scaled),
                        shown(tide),
                        shown(to_mark),
                        shown(item.gravity.value),
                        shown(item.gravity.std_dev),
                        item.gravity.mode.value,
                    ]
                )

    def _write_drift(self, parameters, context, previews, unit, degree) -> None:
        path = self.parameterAsFileOutput(parameters, OUTPUT_DRIFT, context)
        if not path:
            return
        decimals = display_decimals(unit) + 2
        symbol = unit_symbol(unit).replace("µ", "u").lower()
        coefficient_columns = []
        for power in range(1, degree + 1):
            coefficient_columns += [f"c{power}_{symbol}", f"c{power}_sigma_{symbol}"]
        with open(path, "w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                [
                    "session",
                    "instrument",
                    "occupations",
                    "estimable_jointly",
                    "base_station",
                    "base_occupations",
                    *coefficient_columns,
                    "base_residuals_pass",
                ]
            )
            for preview in previews:
                estimate = preview.estimate
                values: list[str] = []
                for power in range(degree):
                    if estimate is None:
                        values += ["", ""]
                        continue
                    coefficient = estimate.coefficients[power]
                    values += [
                        f"{to_display(coefficient.value, unit):.{decimals}f}",
                        f"{to_display(coefficient.std_dev, unit):.{decimals}f}",
                    ]
                verified = "" if estimate is None or estimate.verified is None else estimate.verified
                writer.writerow(
                    [
                        preview.session,
                        preview.instrument,
                        preview.occupations,
                        preview.estimable,
                        preview.base_station,
                        preview.base_occupations,
                        *values,
                        verified,
                    ]
                )
