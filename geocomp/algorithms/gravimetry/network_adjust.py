# SPDX-License-Identifier: GPL-2.0-or-later
"""``geocomp:gravimetry_network`` -- adjust a gravimetric network (FR-700, FR-702).

``specs/12-module-gravimetry.md`` section 5.

The reduced readings *Pre-processing* wrote become gravity differences, the
drift is estimated with the station values (or was fitted to a base first, if
the user chose that), and absolute values enter weighted. Everything numerical
is :func:`~geocomp.core.techniques.gravimetry.adjust_gravity_network`, which is
the in-house core; this module turns parameters into its inputs and its result
into a solution, a report, a CSV and two layers.

**What the report is about.** A gravity network is small and weakly redundant,
so the questions that matter are which observations nothing checks, what the
datum is, and how each session's drift was treated. Those come first, and the
uncheckable observations are listed by name even when every test passes.
"""

from __future__ import annotations

import csv
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
from geocomp.algorithms.gravimetry.common import (
    DRIFT_DEGREE_KEY,
    DRIFT_MODE_KEY,
    display_decimals,
    display_unit,
    gravimeter_setting,
    gravity_label,
    read_readings_document,
    to_display,
    translate_error,
    unit_symbol,
)
from geocomp.algorithms.layer_outputs import (
    LINE_SOURCE_TYPE,
    POINT_SOURCE_TYPE,
    write_styled_sink,
)
from geocomp.algorithms.levelling.common import write_document
from geocomp.algorithms.reporting import (
    escape,
    format_number,
    render_document,
    render_note,
    render_table,
)
from geocomp.core.errors import GeoCompError
from geocomp.core.models import ObservationType, Provenance
from geocomp.core.statistics.reliability import DEFAULT_ALPHA, DEFAULT_BETA
from geocomp.core.techniques.gravimetry import (
    AbsoluteGravity,
    DriftMode,
    DriftOptions,
    DriftTreatment,
    adjust_gravity_network,
    build_gravity_network,
)
from geocomp.core.uncertainty import Quantity
from geocomp.core.units import METRES_PER_SECOND_SQUARED_PER_MGAL as MGAL
from geocomp.core.units import Unit

__all__ = ["GravimetryNetworkAlgorithm"]

READINGS = "READINGS"
KNOWN_GRAVITY = "KNOWN_GRAVITY"
DRIFT_MODE = "DRIFT_MODE"
DRIFT_DEGREE = "DRIFT_DEGREE"
CORRELATED = "CORRELATED"
CONFIDENCE = "CONFIDENCE"
ALPHA = "ALPHA"
BETA = "BETA"
OUTPUT_SOLUTION = "OUTPUT_SOLUTION"
OUTPUT_HTML = "OUTPUT_HTML"
OUTPUT_CSV = "OUTPUT_CSV"
OUTPUT_STATIONS = "OUTPUT_STATIONS"
OUTPUT_DIFFERENCES = "OUTPUT_DIFFERENCES"
VARIANCE_FACTOR_APOSTERIORI = "VARIANCE_FACTOR_APOSTERIORI"
DEGREES_OF_FREEDOM = "DEGREES_OF_FREEDOM"
GLOBAL_TEST_PASSED = "GLOBAL_TEST_PASSED"
OUTLIER_COUNT = "OUTLIER_COUNT"
UNCHECKABLE_COUNT = "UNCHECKABLE_COUNT"
DATUM_DEFECT = "DATUM_DEFECT"

#: The settings' drift-mode values, in the order the enum parameter lists them.
DRIFT_MODES = ("joint", "pre_corrected")


class GravimetryNetworkAlgorithm(GeoCompAlgorithm):
    """Adjust reduced gravity readings as a network, drift included."""

    TR_CONTEXT = "GravimetryNetworkAlgorithm"

    def displayName(self) -> str:
        return self.tr("Gravimetric network adjustment")

    def shortDescription(self) -> str:
        return self.tr(
            "Adjust relative and absolute gravity as a network, with each session's drift."
        )

    def help_body(self) -> str:
        return self.tr(
            "<p>Adjusts the readings <i>Pre-processing (scale, tide, drift)</i> reduced: "
            "each session's occupations become gravity differences, absolute values enter "
            "weighted, and the result goes through the same global test, data snooping and "
            "reliability analysis as any other GeoComp adjustment.</p>"
            "<p><b>Drift.</b> Estimated with the station values by default, one polynomial "
            "per session: every re-occupation informs it, not only a base station's. "
            "<i>Fitted to base readings first</i> is the classical field method, kept for "
            "comparison and for sessions that re-occupy nothing but their base. The "
            "differences carry their exact covariance either way: successive differences "
            "share an occupation and are correlated, and the calibration factor's "
            "uncertainty is common to every reading of an instrument.</p>"
            "<p><b>Known gravity</b> is entered as <code>station=value</code> pairs in mGal, "
            "separated by commas or semicolons. With <code>±sigma</code> the value is an "
            "absolute determination and is weighted by its uncertainty, for example "
            "<code>RG26=979197.5759±0.0106</code>; without it the station is held exactly, "
            "which makes it the datum and every uncertainty relative to it. With none, the "
            "network is adjusted with an inner constraint and every value is relative to "
            "their mean; the report says which.</p>"
            "<p><b>A value must refer to the mark.</b> Give the pre-processing a sensor "
            "height, or readings taken 20 cm above the mark will differ from an absolute "
            "value quoted at it by about 60 µGal.</p>"
            "<p><b>Uncheckable observations are listed by name.</b> A gravity network is "
            "small and weakly redundant, and a difference with a redundancy near zero can "
            "hide a blunder no test will find. A lone absolute value is always one. The "
            "report lists them and the layers draw them in a colour of their own.</p>"
            "<h3>Parameters</h3>"
            "<p><b>Reduced readings</b> &mdash; the document pre-processing wrote. "
            "<b>Known gravity</b> &mdash; as above. <b>Drift treatment</b> and <b>drift "
            "degree</b> default to the Gravimeter settings.</p>"
            "<p><b>Carry the correlation between differences</b> (advanced) &mdash; on by "
            "default. Off reproduces MCGravi and pyGrav, which treat the differences as "
            "independent, and the result records the assumption. <b>Confidence</b>, "
            "<b>alpha</b> and <b>beta</b> &mdash; for the tests.</p>"
            "<h3>Outputs</h3>"
            "<p><b>Solution</b> &mdash; JSON, in m/s². <b>Report</b> &mdash; HTML. "
            "<b>Gravity</b> &mdash; CSV. <b>Gravity stations</b> and <b>Gravity "
            "differences</b> &mdash; layers, located where the readings were taken; values "
            "in the display unit of the Gravimeter settings, which a column names. Scalars: "
            "<code>VARIANCE_FACTOR_APOSTERIORI</code>, <code>DEGREES_OF_FREEDOM</code>, "
            "<code>GLOBAL_TEST_PASSED</code>, <code>OUTLIER_COUNT</code>, "
            "<code>UNCHECKABLE_COUNT</code> and <code>DATUM_DEFECT</code> (of the relative "
            "observations alone).</p>"
        )

    def initAlgorithm(self, config: dict[str, Any] | None = None) -> None:
        self.addParameter(
            QgsProcessingParameterFile(READINGS, self.tr("Reduced readings"), extension="json")
        )
        self.addParameter(
            QgsProcessingParameterString(
                KNOWN_GRAVITY, self.tr("Known gravity (mGal)"), defaultValue="", optional=True
            )
        )
        configured = gravimeter_setting(DRIFT_MODE_KEY)
        self.addParameter(
            QgsProcessingParameterEnum(
                DRIFT_MODE,
                self.tr("Drift treatment"),
                options=[
                    self.tr("Estimated with the station values"),
                    self.tr("Fitted to base readings first"),
                ],
                defaultValue=DRIFT_MODES.index(configured) if configured in DRIFT_MODES else 0,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                DRIFT_DEGREE,
                self.tr("Drift polynomial degree"),
                type=QgsProcessingParameterNumber.Type.Integer,
                defaultValue=int(gravimeter_setting(DRIFT_DEGREE_KEY)),
                minValue=1,
                maxValue=3,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterBoolean(
                CORRELATED,
                self.tr("Carry the correlation between differences"),
                defaultValue=True,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterNumber(
                CONFIDENCE,
                self.tr("Confidence level"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=0.95,
                minValue=0.5,
                maxValue=0.9999,
            )
        )
        for name, label, default in (
            (ALPHA, self.tr("Data snooping significance (alpha)"), DEFAULT_ALPHA),
            (BETA, self.tr("Data snooping type II error rate (beta)"), DEFAULT_BETA),
        ):
            self.addAdvancedParameter(
                QgsProcessingParameterNumber(
                    name,
                    label,
                    type=QgsProcessingParameterNumber.Type.Double,
                    defaultValue=default,
                    minValue=1.0e-6,
                    maxValue=0.9,
                )
            )
        for name, label, filter_text, by_default in (
            (OUTPUT_SOLUTION, self.tr("Solution"), self.tr("GeoComp solution (*.json)"), True),
            (OUTPUT_HTML, self.tr("Report"), self.tr("HTML files (*.html)"), True),
            (OUTPUT_CSV, self.tr("Gravity"), self.tr("CSV files (*.csv)"), False),
        ):
            self.addParameter(
                QgsProcessingParameterFileDestination(
                    name, label, filter_text, optional=True, createByDefault=by_default
                )
            )
        for name, label, kind in (
            (OUTPUT_STATIONS, self.tr("Gravity stations"), POINT_SOURCE_TYPE),
            (OUTPUT_DIFFERENCES, self.tr("Gravity differences"), LINE_SOURCE_TYPE),
        ):
            self.addParameter(
                QgsProcessingParameterFeatureSink(
                    name, label, type=kind, optional=True, createByDefault=True
                )
            )

    def processAlgorithm(
        self,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> dict[str, Any]:
        path = self.parameterAsFile(parameters, READINGS, context)
        reduced, library, document = read_readings_document(path)
        absolutes, held = self._known(self.parameterAsString(parameters, KNOWN_GRAVITY, context))
        mode = DRIFT_MODES[self.parameterAsEnum(parameters, DRIFT_MODE, context)]
        options = DriftOptions(
            mode=DriftMode.JOINT if mode == "joint" else DriftMode.PRE_CORRECTED,
            degree=self.parameterAsInt(parameters, DRIFT_DEGREE, context),
            correlated=self.parameterAsBool(parameters, CORRELATED, context),
        )
        confidence = self.parameterAsDouble(parameters, CONFIDENCE, context)
        feedback.setProgress(10)

        try:
            built = build_gravity_network(
                reduced,
                library,
                absolutes=absolutes,
                held=held,
                drift=options,
                confidence=confidence,
            )
            feedback.setProgress(30)
            feedback.pushInfo(self.tr("Adjusting…"))
            result = adjust_gravity_network(
                built,
                confidence=confidence,
                alpha=self.parameterAsDouble(parameters, ALPHA, context),
                beta=self.parameterAsDouble(parameters, BETA, context),
                provenance=self._provenance(document, options, confidence, absolutes, held),
            )
        except GeoCompError as exc:
            raise QgsProcessingException(translate_error(exc)) from exc
        if feedback.isCanceled():
            return {}
        feedback.setProgress(70)

        unit = display_unit()
        notes = [*document.get("notes", ()), *result.notes]
        self._push_summary(result, unit, feedback)
        solution = result.solution
        write_document(
            self.parameterAsFileOutput(parameters, OUTPUT_SOLUTION, context),
            solution.to_dict(),
        )
        self._write_report(parameters, context, built, result, unit, notes, document)
        self._write_csv(parameters, context, result, built.network, unit)

        from geocomp.layers.builders import (
            gravity_difference_features,
            gravity_station_features,
        )

        crs = QgsCoordinateReferenceSystem(built.network.crs)
        outputs: dict[str, Any] = {}
        outputs[OUTPUT_STATIONS] = write_styled_sink(
            self,
            parameters,
            context,
            OUTPUT_STATIONS,
            style="gravity_stations",
            geometry=QgsWkbTypes.Type.Point,
            crs=crs,
            features=lambda: gravity_station_features(solution, built.network, unit=unit),
            layer_name=self.tr("Gravity stations (%1)").replace("%1", unit_symbol(unit)),
        )
        outputs[OUTPUT_DIFFERENCES] = write_styled_sink(
            self,
            parameters,
            context,
            OUTPUT_DIFFERENCES,
            style="gravity_differences",
            geometry=QgsWkbTypes.Type.LineString,
            crs=crs,
            features=lambda: gravity_difference_features(solution, built.network, unit=unit),
            layer_name=self.tr("Gravity differences (%1)").replace("%1", unit_symbol(unit)),
        )
        feedback.setProgress(100)

        run = result.run
        candidates = [
            r
            for r in solution.observation_results
            if r.w_test is not None and not r.w_test.passed and not r.is_uncheckable
        ]
        test = solution.statistics.global_test
        outputs.update(
            {
                VARIANCE_FACTOR_APOSTERIORI: run.variance_factor_aposteriori,
                DEGREES_OF_FREEDOM: run.degrees_of_freedom,
                GLOBAL_TEST_PASSED: bool(test.passed) if test is not None else False,
                OUTLIER_COUNT: len(candidates),
                UNCHECKABLE_COUNT: len(result.uncheckable),
                DATUM_DEFECT: result.datum.defect,
                OUTPUT_SOLUTION: self.parameterAsFileOutput(parameters, OUTPUT_SOLUTION, context),
                OUTPUT_HTML: self.parameterAsFileOutput(parameters, OUTPUT_HTML, context),
                OUTPUT_CSV: self.parameterAsFileOutput(parameters, OUTPUT_CSV, context),
            }
        )
        return outputs

    # -- inputs ----------------------------------------------------------

    def _known(self, raw: str) -> tuple[list[AbsoluteGravity], dict[str, Quantity]]:
        """Parse ``A=979197.5759±0.0106, B=979100.0`` into absolute and held values.

        A plain-text parameter rather than a file for the reason the levelling
        benchmarks are one: a gravity network is tied to one or two absolute
        sites, and a document to hold two numbers is friction with no benefit.
        """
        absolutes: list[AbsoluteGravity] = []
        held: dict[str, Quantity] = {}
        for chunk in raw.replace(";", ",").split(","):
            entry = chunk.strip()
            if not entry:
                continue
            if "=" not in entry:
                raise QgsProcessingException(
                    self.tr(
                        "'%1' is not a known gravity. Write it as station=value in mGal, "
                        "for example RG26=979197.5759, and add ±sigma to weight it as an "
                        "absolute determination rather than hold it."
                    ).replace("%1", entry)
                )
            station, _, value = entry.partition("=")
            station = station.strip()
            text = value.strip().replace("+/-", "±")
            gravity_text, _, sigma_text = text.partition("±")
            try:
                gravity = float(gravity_text.strip()) * MGAL
                sigma = float(sigma_text.strip()) * MGAL if sigma_text.strip() else 0.0
            except ValueError:
                raise QgsProcessingException(
                    self.tr("'%1' does not hold a number.").replace("%1", entry)
                ) from None
            if station in held or any(a.station == station for a in absolutes):
                raise QgsProcessingException(
                    self.tr("The station '%1' is given a known gravity twice.").replace(
                        "%1", station
                    )
                )
            if sigma > 0.0:
                absolutes.append(
                    AbsoluteGravity(
                        id=station,
                        station=station,
                        value=Quantity.from_std_dev(gravity, sigma, Unit.ACCELERATION),
                        source="entered on the algorithm's parameters",
                    )
                )
            else:
                held[station] = Quantity.exact(gravity, Unit.ACCELERATION)
        return absolutes, held

    def _provenance(self, document, options, confidence, absolutes, held) -> Provenance:
        """What was run, so the result can be reproduced (FR-134).

        The resolved values and the known gravity by station, never the raw
        parameter dictionary, which carries file paths (NFR-010).
        """
        return Provenance.now(
            algorithm_id=self.spec().id,
            source="geocomp:gravimetry_network",
            qgis_version=Qgis.QGIS_VERSION,
            parameters={
                "readings_source": document.get("source", ""),
                "reduction": document.get("reduction", {}),
                "drift_mode": options.mode.value,
                "drift_degree": options.degree,
                "drift_time_scale_s": options.time_scale,
                "correlated": options.correlated,
                "confidence": confidence,
                "absolute": {a.station: [a.value.value, a.value.std_dev] for a in absolutes},
                "held": {station: value.value for station, value in held.items()},
            },
        )

    # -- outputs ---------------------------------------------------------

    def _push_summary(self, result, unit, feedback) -> None:
        run = result.run
        feedback.pushInfo(
            self.tr("Degrees of freedom %1; variance factor %2.")
            .replace("%1", str(run.degrees_of_freedom))
            .replace("%2", format_number(run.variance_factor_aposteriori, 4))
        )
        feedback.pushInfo(
            self.tr("Datum: %1.").replace("%1", result.datum.removed_by)
        )
        test = result.solution.statistics.global_test
        if test is not None and not test.passed:
            feedback.pushWarning(
                self.tr(
                    "The global test failed. Either the observations disagree with each "
                    "other more than their weights allow, or the weights are wrong — the "
                    "test cannot tell you which."
                )
            )
        for observation in result.uncheckable:
            feedback.pushWarning(
                self.tr("Uncheckable: %1. No blunder in it could be detected.").replace(
                    "%1", observation
                )
            )
        for candidate in result.solution.observation_results:
            if candidate.w_test is not None and not candidate.w_test.passed:
                feedback.pushWarning(
                    self.tr("Outlier candidate: %1 (w = %2).")
                    .replace("%1", candidate.observation_id)
                    .replace("%2", format_number(candidate.standardised_residual, 2))
                )
        decimals = display_decimals(unit) + 1
        for session, drift in sorted(result.drift.items()):
            rate = drift.coefficients[0]
            feedback.pushInfo(
                self.tr("Drift of %1: %2 ± %3 %4 per hour.")
                .replace("%1", session)
                .replace("%2", format_number(to_display(rate.value, unit), decimals))
                .replace("%3", format_number(to_display(rate.std_dev, unit), decimals))
                .replace("%4", unit_symbol(unit))
            )

    def _write_report(self, parameters, context, built, result, unit, notes, document) -> None:
        path = self.parameterAsFileOutput(parameters, OUTPUT_HTML, context)
        if not path:
            return
        solution = result.solution
        run = result.run
        network = built.network
        decimals = display_decimals(unit)
        test = solution.statistics.global_test

        def shown(value: float | None, extra: int = 0) -> str:
            return format_number(None if value is None else to_display(value, unit), decimals + extra)

        summary = render_table(
            [escape(self.tr("Quantity")), escape(self.tr("Value"))],
            [
                [escape(self.tr("Stations")), str(len(network.stations))],
                [escape(self.tr("Readings")), str(len(document.get("readings", ())))],
                [escape(self.tr("Occupations")), str(len(built.occupations))],
                [escape(self.tr("Sessions")), str(len(built.sessions))],
                [escape(self.tr("Observations")), str(len(run.observations))],
                [escape(self.tr("Degrees of freedom")), str(run.degrees_of_freedom)],
                [
                    escape(self.tr("Variance factor")),
                    format_number(run.variance_factor_aposteriori, 5),
                ],
                [
                    escape(self.tr("Global test")),
                    escape(
                        self.tr("not computed")
                        if test is None
                        else self.tr("passed")
                        if test.passed
                        else self.tr("FAILED")
                    ),
                ],
                [
                    escape(self.tr("Datum defect of the differences")),
                    str(result.datum.defect),
                ],
                [escape(self.tr("Datum")), escape(result.datum.removed_by)],
                [escape(self.tr("Uncertainty")), escape(self._mode(solution))],
                [escape(self.tr("Tide system")), escape(result.tide_system)],
            ],
        )

        roles = self._roles(result, network)
        gravity_rows = []
        for station in sorted(solution.adjusted_stations, key=lambda s: s.station_id):
            if station.gravity is None:
                continue
            gravity_rows.append(
                [
                    escape(station.station_id),
                    shown(station.gravity.value),
                    shown(station.gravity.std_dev, 1),
                    escape(roles.get(station.station_id, "")),
                ]
            )
        for station in sorted(network.stations.values(), key=lambda s: s.id):
            gravity = station.constraint.gravity
            if gravity is None or any(
                s.station_id == station.id for s in solution.adjusted_stations
            ):
                continue
            gravity_rows.append(
                [escape(station.id), shown(gravity.value), "—", escape(self.tr("held"))]
            )
        gravity_table = render_table(
            [
                escape(self.tr("Station")),
                escape(gravity_label(self.tr("Gravity"), unit)),
                escape(gravity_label(self.tr("sigma"), unit)),
                escape(self.tr("Determined by")),
            ],
            gravity_rows,
        )

        drift_rows = []
        for session in sorted(built.sessions):
            report = built.sessions[session]
            drift = result.drift.get(session)
            coefficients = (
                "; ".join(
                    f"{shown(c.value, 1)} ± {shown(c.std_dev, 1)}" for c in drift.coefficients
                )
                if drift is not None
                else "—"
            )
            verified = (
                "—"
                if drift is None or drift.verified is None
                else self.tr("passed")
                if drift.verified
                else self.tr("FAILED")
            )
            drift_rows.append(
                [
                    escape(session),
                    escape(report.instrument),
                    escape(
                        self.tr("estimated with the station values")
                        if report.treatment is DriftTreatment.JOINT
                        else self.tr("fitted to base %1 first").replace(
                            "%1", report.base_station or ""
                        )
                    ),
                    str(report.occupations),
                    coefficients,
                    escape(verified),
                ]
            )
        drift_table = render_table(
            [
                escape(self.tr("Session")),
                escape(self.tr("Instrument")),
                escape(self.tr("Treatment")),
                escape(self.tr("Occupations")),
                escape(
                    self.tr("Drift per hour, then per hour², … (%1)").replace(
                        "%1", unit_symbol(unit)
                    )
                ),
                escape(self.tr("Base residuals")),
            ],
            drift_rows,
        )

        differences = []
        for index, observation_result in enumerate(solution.observation_results):
            observation = network.observations.get(observation_result.observation_id)
            test_result = observation_result.w_test
            if observation_result.is_uncheckable:
                decision = f'<span class="blocking">{escape(self.tr("not testable"))}</span>'
            elif test_result is None:
                decision = "—"
            elif test_result.passed:
                decision = escape(self.tr("accepted"))
            else:
                decision = f'<span class="warning">{escape(self.tr("CANDIDATE"))}</span>'
            differences.append(
                [
                    str(index),
                    escape(observation_result.observation_id),
                    escape(" → ".join(observation.stations) if observation else ""),
                    shown(observation.values[0].value if observation else None, 1),
                    shown(observation_result.residual, 1),
                    format_number(observation_result.standardised_residual, 3),
                    format_number(observation_result.redundancy, 3),
                    shown(observation_result.minimal_detectable_bias, 1),
                    decision,
                ]
            )
        observation_table = render_table(
            [
                escape(self.tr("Row")),
                escape(self.tr("Observation")),
                escape(self.tr("Stations")),
                escape(gravity_label(self.tr("Value"), unit)),
                escape(gravity_label(self.tr("Residual"), unit)),
                escape(self.tr("w")),
                escape(self.tr("Redundancy")),
                escape(gravity_label(self.tr("MDB"), unit)),
                escape(self.tr("w-test")),
            ],
            differences,
        )

        body = [
            f"<h2>{escape(self.tr('Summary'))}</h2>",
            summary,
        ]
        if result.uncheckable:
            body.append(f"<h2>{escape(self.tr('Uncheckable observations'))}</h2>")
            body.append(
                render_note(
                    self.tr(
                        "No blunder in these could be detected, whatever the tests below "
                        "say: %1. A lone absolute value and a station reached by one "
                        "difference are the usual cases. Re-observe or add a connection "
                        "to make them checkable."
                    ).replace("%1", ", ".join(result.uncheckable)),
                    label=self.tr("Not testable"),
                )
            )
        body += [
            f"<h2>{escape(self.tr('Adjusted gravity'))}</h2>",
            gravity_table,
            f"<h2>{escape(self.tr('Drift'))}</h2>",
            drift_table,
            f"<h2>{escape(self.tr('Observations'))}</h2>",
            observation_table,
        ]
        if test is not None and not test.passed:
            body.append(
                render_note(
                    self.tr(
                        "The global test failed. Either the observations disagree more than "
                        "their weights allow, or the weights are wrong — the test cannot "
                        "distinguish the two. A reading's own standard error knows nothing "
                        "of tilt, temperature or transport; a precision floor in "
                        "pre-processing is the usual remedy, and the report of the run that "
                        "used one says so."
                    ),
                    label=self.tr("Global test"),
                )
            )
        body.append(
            render_note(
                self.tr(
                    "Candidates, not rejections. GeoComp never removes an observation on "
                    "its own: in a monitoring network the change being measured is exactly "
                    "what an automatic outlier remover would delete."
                ),
                label=self.tr("Data snooping"),
            )
        )
        if notes:
            body.append(f"<h2>{escape(self.tr('Notes'))}</h2>")
            body.append("<ul>" + "".join(f"<li>{escape(note)}</li>" for note in notes) + "</ul>")
        body.append(
            render_note(
                self.tr(
                    "Values are shown in %1, as the Gravimeter settings ask. The solution "
                    "stores m/s²."
                ).replace("%1", unit_symbol(unit)),
                label=self.tr("Units"),
            )
        )
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(render_document(self.tr("Gravimetric network adjustment"), body))

    def _mode(self, solution) -> str:
        """Rigorous, or approximate and why (FR-203): the strategies by name."""
        from geocomp.core.uncertainty import UncertaintyMode

        if solution.uncertainty_mode is UncertaintyMode.RIGOROUS:
            return self.tr("rigorous")
        strategies = sorted(s.value for s in solution.parameter_covariance.strategies)
        return self.tr("approximate: %1").replace("%1", ", ".join(strategies) or "—")

    def _roles(self, result, network) -> dict[str, str]:
        absolute = {
            observation.stations[0]
            for observation in network.observations.values()
            if observation.type is ObservationType.GRAVITY
        }
        roles = {}
        for station in network.stations.values():
            if station.constraint.gravity is not None:
                roles[station.id] = self.tr("held")
            elif station.id in absolute:
                roles[station.id] = self.tr("absolute value and differences")
            else:
                roles[station.id] = self.tr("differences")
        return roles

    def _write_csv(self, parameters, context, result, network, unit) -> None:
        path = self.parameterAsFileOutput(parameters, OUTPUT_CSV, context)
        if not path:
            return
        decimals = display_decimals(unit) + 2
        symbol = unit_symbol(unit).replace("µ", "u").lower()
        roles = self._roles(result, network)
        with open(path, "w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                [
                    "station",
                    f"gravity_{symbol}",
                    f"sigma_{symbol}",
                    "gravity_m_s2",
                    "sigma_m_s2",
                    "determined_by",
                    "uncertainty",
                ]
            )
            rows = [
                (s.station_id, s.gravity.value, s.gravity.std_dev, s.gravity.mode.value)
                for s in result.solution.adjusted_stations
                if s.gravity is not None
            ]
            adjusted = {row[0] for row in rows}
            rows += [
                (s.id, s.constraint.gravity.value, 0.0, s.constraint.gravity.mode.value)
                for s in network.stations.values()
                if s.constraint.gravity is not None and s.id not in adjusted
            ]
            for station, value, sigma, mode in sorted(rows):
                writer.writerow(
                    [
                        station,
                        f"{to_display(value, unit):.{decimals}f}",
                        f"{to_display(sigma, unit):.{decimals}f}",
                        repr(value),
                        repr(sigma),
                        roles.get(station, ""),
                        mode,
                    ]
                )
