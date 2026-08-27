# SPDX-License-Identifier: GPL-2.0-or-later
"""``geocomp:analysis_network_adjust`` -- adjust a network and test the result.

FR-220…FR-227 and FR-250…FR-255. ``specs/06-adjustment-core.md``.

The Processing face of the in-house least-squares core. It adjusts, then runs
the tests that say whether the adjustment may be believed: the two-sided global
chi-square test on the variance factor, Baarda's w-test on every standardised
residual, and the reliability analysis that says which observations the network
could not check even in principle.

**Nothing is rejected automatically** (FR-255). Data snooping returns
*candidates*; removing an observation is the user's decision, taken with the
evidence in front of them, and re-adjustment after a rejection is a second
explicit run. Automatic iterative rejection deletes real signal, and in
deformation monitoring the real signal is the thing being measured.

Engine-independent by construction: the result is the same
:class:`~geocomp.core.models.Solution` DynAdjust's output will fill in phase P6,
so everything downstream stays engine-blind (FR-323).
"""

from __future__ import annotations

import csv
import json
from typing import Any

from qgis.core import (
    Qgis,
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFile,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
)

from geocomp.algorithms.analysis.common import (
    datum_labels,
    datum_of,
    escape,
    format_number,
    frame_labels,
    frame_of,
    load_network,
    render_document,
    render_note,
    render_table,
    station_list,
)
from geocomp.algorithms.base import GeoCompAlgorithm
from geocomp.algorithms.layer_outputs import (
    add_result_layer_parameters,
    write_result_layers,
)
from geocomp.core.adjustment.least_squares import (
    AdjustmentOptions,
    adjust,
    to_observation_results,
    to_solution,
)
from geocomp.core.errors import GeoCompError
from geocomp.core.models import Epoch, HeightType, Provenance
from geocomp.core.statistics.reliability import DEFAULT_ALPHA, DEFAULT_BETA, reliability
from geocomp.core.statistics.tests import data_snooping, global_test

__all__ = ["NetworkAdjustAlgorithm"]

NETWORK = "NETWORK"
FRAME = "FRAME"
DATUM = "DATUM"
DATUM_STATIONS = "DATUM_STATIONS"
CONFIDENCE = "CONFIDENCE"
VARIANCE_FACTOR = "VARIANCE_FACTOR"
CONVERGENCE = "CONVERGENCE"
MAX_ITERATIONS = "MAX_ITERATIONS"
ALPHA = "ALPHA"
BETA = "BETA"
EPOCH = "EPOCH"
OUTPUT_SOLUTION = "OUTPUT_SOLUTION"
OUTPUT_HTML = "OUTPUT_HTML"
OUTPUT_STATIONS_CSV = "OUTPUT_STATIONS_CSV"
OUTPUT_RESIDUALS_CSV = "OUTPUT_RESIDUALS_CSV"
VARIANCE_FACTOR_APOSTERIORI = "VARIANCE_FACTOR_APOSTERIORI"
DEGREES_OF_FREEDOM = "DEGREES_OF_FREEDOM"
ITERATIONS = "ITERATIONS"
GLOBAL_TEST_PASSED = "GLOBAL_TEST_PASSED"
OUTLIER_COUNT = "OUTLIER_COUNT"
WORST_OUTLIER = "WORST_OUTLIER"
UNCHECKABLE_COUNT = "UNCHECKABLE_COUNT"


class NetworkAdjustAlgorithm(GeoCompAlgorithm):
    """Least-squares network adjustment with its full statistical treatment."""

    TR_CONTEXT = "NetworkAdjustAlgorithm"

    def displayName(self) -> str:
        return self.tr("Adjust network")

    def shortDescription(self) -> str:
        return self.tr(
            "Least-squares adjustment with the global test, data snooping and reliability."
        )

    def help_body(self) -> str:
        return self.tr(
            "<p>Adjusts a geodetic network by least squares using the parametric model, "
            "iterating the linearised solution to convergence, and reports the adjusted "
            "coordinates with their full covariance matrix, the residuals, and the "
            "statistical tests that say whether the result may be believed.</p>"
            "<p>1D, 2D and 3D networks are all supported, free or constrained. The weight "
            "matrix is built from the observation covariances, including correlations "
            "between the observations of a correlated cluster such as a GNSS baseline.</p>"
            "<p><b>Non-convergence is reported as a failure</b>, never returned as a result. "
            "A set of coordinates that is really iteration seven of a diverging sequence is "
            "worse than no result, because nothing about it says so.</p>"
            "<p><b>No observation is rejected automatically.</b> Data snooping reports "
            "candidates and the decision is yours; re-adjusting after removing one is a "
            "second, explicit run. Automatic iterative rejection deletes real signal, which "
            "in deformation monitoring is the very thing being measured.</p>"
            "<h3>Parameters</h3>"
            "<p><b>Network</b> &mdash; a GeoComp network document (JSON).</p>"
            "<p><b>Coordinate frame</b> &mdash; 1D, 2D or 3D. It decides which parameters "
            "exist and which observations can contribute.</p>"
            "<p><b>Datum definition</b> &mdash; how the datum defect is removed. "
            "<i>Constrained</i> and <i>Fixed</i> hold the stations the network declares as "
            "constrained. <i>Inner constraint</i> gives a free network whose solution is the "
            "trace minimum over all stations. <i>Minimum constraint</i> does the same over "
            "the chosen stations, which is what a deformation analysis needs: holding a "
            "station that has itself moved spreads its motion across the network.</p>"
            "<p><b>Datum stations</b> &mdash; comma-separated; empty means all of them.</p>"
            "<p><b>Confidence level</b> &mdash; for the global test, the w-test and the error "
            "ellipses, between 0 and 1.</p>"
            "<p><b>A priori variance factor</b> &mdash; the assumed sigma-nought squared the "
            "global test compares against.</p>"
            "<p><b>Convergence threshold</b> &mdash; the largest parameter correction "
            "accepted as converged, in metres. <b>Maximum iterations</b> &mdash; after which "
            "non-convergence is reported.</p>"
            "<p><b>Significance</b> and <b>Type II error</b> &mdash; alpha and beta for the "
            "minimal detectable bias.</p>"
            "<p><b>Reference epoch</b> &mdash; the decimal year the coordinates refer to. It "
            "is recorded on the solution because comparing two epochs is only meaningful "
            "when both say which they are.</p>"
            "<h3>Outputs</h3>"
            "<p><b>Solution</b> &mdash; a JSON document holding the adjusted coordinates, the "
            "full covariance matrix, the per-observation results and the provenance. It is "
            "the same structure an external engine's result fills, so everything downstream "
            "is engine-independent.</p>"
            "<p><b>Report</b> &mdash; HTML. <b>Adjusted stations</b> and <b>Residuals</b> "
            "&mdash; CSV tables for a spreadsheet or a model.</p>"
            "<p>Scalar outputs: <code>VARIANCE_FACTOR_APOSTERIORI</code>, "
            "<code>DEGREES_OF_FREEDOM</code>, <code>ITERATIONS</code>, "
            "<code>GLOBAL_TEST_PASSED</code>, <code>OUTLIER_COUNT</code>, "
            "<code>WORST_OUTLIER</code> and <code>UNCHECKABLE_COUNT</code>.</p>"
            "<p><b>Result layers</b> &mdash; five optional map layers, arriving styled "
            "and ready to read (FR-905): adjusted stations sized by their positional "
            "uncertainty, error ellipses, observations coloured by what the w-test "
            "decided about them, the measured network by observation type, and the "
            "coordinate correction vectors. None is created unless asked for, so an "
            "adjustment run to feed another algorithm writes nothing extra.</p>"
            "<p><b>Ellipse exaggeration</b> &mdash; real ellipses are invisible at map "
            "scale, so they are drawn enlarged. Leave it at 0 and a factor is fitted to "
            "the network's own extent. Whatever factor is used is stated in the layer's "
            "name, which is what reaches the legend: an unstated exaggeration turns a "
            "quality visualisation into a misrepresentation.</p>"
        )

    # -- parameters ------------------------------------------------------

    def initAlgorithm(self, config: dict[str, Any] | None = None) -> None:
        self.addParameter(
            QgsProcessingParameterFile(NETWORK, self.tr("Network document"), extension="json")
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                FRAME, self.tr("Coordinate frame"), options=frame_labels(), defaultValue=0
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                DATUM, self.tr("Datum definition"), options=datum_labels(), defaultValue=0
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterString(
                DATUM_STATIONS,
                self.tr("Datum stations (comma-separated; empty = all)"),
                defaultValue="",
                optional=True,
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
        self.addAdvancedParameter(
            QgsProcessingParameterNumber(
                VARIANCE_FACTOR,
                self.tr("A priori variance factor"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=1.0,
                minValue=1e-12,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterNumber(
                CONVERGENCE,
                self.tr("Convergence threshold (m)"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=1e-4,
                minValue=1e-12,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterNumber(
                MAX_ITERATIONS,
                self.tr("Maximum iterations"),
                type=QgsProcessingParameterNumber.Type.Integer,
                defaultValue=20,
                minValue=1,
                maxValue=1000,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterNumber(
                ALPHA,
                self.tr("Significance for the minimal detectable bias"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=DEFAULT_ALPHA,
                minValue=1e-6,
                maxValue=0.5,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterNumber(
                BETA,
                self.tr("Type II error for the minimal detectable bias"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=DEFAULT_BETA,
                minValue=1e-6,
                maxValue=0.9,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterNumber(
                EPOCH,
                self.tr("Reference epoch (decimal year)"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=2000.0,
            )
        )
        self.addParameter(
            QgsProcessingParameterFileDestination(
                OUTPUT_SOLUTION,
                self.tr("Solution"),
                self.tr("GeoComp solution (*.json)"),
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
                OUTPUT_STATIONS_CSV,
                self.tr("Adjusted stations (table)"),
                self.tr("CSV files (*.csv)"),
                optional=True,
                createByDefault=False,
            )
        )
        self.addParameter(
            QgsProcessingParameterFileDestination(
                OUTPUT_RESIDUALS_CSV,
                self.tr("Residuals (table)"),
                self.tr("CSV files (*.csv)"),
                optional=True,
                createByDefault=False,
            )
        )
        add_result_layer_parameters(self)

    # -- execution -------------------------------------------------------

    def processAlgorithm(
        self,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> dict[str, Any]:
        network = load_network(
            self.parameterAsFile(parameters, NETWORK, context), parameter=NETWORK
        )
        confidence = self.parameterAsDouble(parameters, CONFIDENCE, context)
        alpha = self.parameterAsDouble(parameters, ALPHA, context)
        beta = self.parameterAsDouble(parameters, BETA, context)
        options = AdjustmentOptions(
            frame=frame_of(self.parameterAsEnum(parameters, FRAME, context)),
            datum=datum_of(self.parameterAsEnum(parameters, DATUM, context)),
            datum_stations=station_list(
                self.parameterAsString(parameters, DATUM_STATIONS, context)
            ),
            variance_factor_apriori=self.parameterAsDouble(
                parameters, VARIANCE_FACTOR, context
            ),
            convergence=self.parameterAsDouble(parameters, CONVERGENCE, context),
            max_iterations=self.parameterAsInt(parameters, MAX_ITERATIONS, context),
            confidence=confidence,
        )

        feedback.setProgress(10)
        feedback.pushInfo(self.tr("Adjusting…"))
        run = self._adjust(network, options)

        if feedback.isCanceled():
            return {}

        feedback.setProgress(55)
        feedback.pushInfo(
            self.tr("Converged in %1 iteration(s); largest correction %2 m.")
            .replace("%1", str(run.iterations))
            .replace("%2", format_number(run.max_correction, 6))
        )

        test = global_test(
            run.variance_factor_aposteriori,
            run.degrees_of_freedom,
            variance_factor_apriori=options.variance_factor_apriori,
            confidence=confidence,
        )
        snooping = data_snooping(
            run.residuals,
            run.cofactor_residuals,
            run.system.weight,
            run.system.row_labels,
            variance_factor=run.variance_factor_aposteriori,
            degrees_of_freedom=run.degrees_of_freedom,
            confidence=confidence,
        )
        reliability_report = reliability(
            run.cofactor_residuals,
            run.system.weight,
            run.system.design,
            run.cofactor_parameters,
            run.system.row_labels,
            alpha=alpha,
            beta=beta,
        )

        feedback.setProgress(75)
        self._push_summary(run, test, snooping, reliability_report, feedback)

        solution = to_solution(
            run,
            network,
            solution_id=f"{network.id or 'network'}-adjustment",
            crs=network.crs,
            epoch=Epoch.from_decimal_year(self.parameterAsDouble(parameters, EPOCH, context)),
            datum=options.datum,
            height_type=(
                HeightType.ORTHOMETRIC if options.frame.dimension == 1 else HeightType.NONE
            ),
            provenance=self._provenance(parameters, options, confidence, alpha, beta),
            observation_results=to_observation_results(
                run, snooping=snooping, reliability=reliability_report
            ),
            global_test=test,
            confidence=confidence,
        )

        feedback.setProgress(90)
        outputs = self._write_outputs(
            parameters,
            context,
            network,
            options,
            run,
            solution,
            test,
            snooping,
            reliability_report,
            confidence,
        )

        layers = write_result_layers(
            self, parameters, context, solution, network, feedback=feedback
        )

        feedback.setProgress(100)
        worst = snooping.worst
        return {
            VARIANCE_FACTOR_APOSTERIORI: run.variance_factor_aposteriori,
            DEGREES_OF_FREEDOM: run.degrees_of_freedom,
            ITERATIONS: run.iterations,
            GLOBAL_TEST_PASSED: test.passed,
            OUTLIER_COUNT: len(snooping.candidates),
            WORST_OUTLIER: worst.observation_id if worst else "",
            UNCHECKABLE_COUNT: len(reliability_report.uncheckable),
            **outputs,
            **layers,
        }

    def _adjust(self, network, options):
        """Run the adjustment, turning a core error into a Processing failure.

        A rank diagnosis names the stations and components involved
        (FR-226); passing it through as the message is the whole point of
        producing one.
        """
        try:
            return adjust(network, options)
        except GeoCompError as exc:
            from geocomp.services.messages import message_for

            raise QgsProcessingException(message_for(exc)) from exc

    def _provenance(self, parameters, options, confidence, alpha, beta) -> Provenance:
        """Record what was run, so the result can be reproduced (FR-134).

        Deliberately records the *resolved* option values rather than the raw
        parameter dictionary: the raw dictionary carries file paths and, in
        general, could carry a credential, which provenance must never hold
        (NFR-010).
        """
        return Provenance.now(
            algorithm_id=self.spec().id,
            source="geocomp:analysis_network_adjust",
            qgis_version=Qgis.QGIS_VERSION,
            parameters={
                "frame": options.frame.value,
                "datum": options.datum.value,
                "datum_stations": list(options.datum_stations or ()),
                "variance_factor_apriori": options.variance_factor_apriori,
                "convergence": options.convergence,
                "max_iterations": options.max_iterations,
                "confidence": confidence,
                "alpha": alpha,
                "beta": beta,
            },
        )

    # -- feedback --------------------------------------------------------

    def _push_summary(self, run, test, snooping, reliability_report, feedback) -> None:
        feedback.pushInfo(
            self.tr("Variance factor %1 on %2 degree(s) of freedom.")
            .replace("%1", format_number(run.variance_factor_aposteriori))
            .replace("%2", str(run.degrees_of_freedom))
        )
        feedback.pushInfo(
            self.tr("Datum defect: %1 (removed by: %2).")
            .replace("%1", run.defect.describe())
            .replace("%2", run.method)
        )

        if test.passed:
            feedback.pushInfo(self.tr("The global test passes."))
        else:
            feedback.pushWarning(self.tr("The global test fails: %1").replace("%1", test.note))

        if snooping.candidates:
            feedback.pushWarning(
                self.tr("%1 observation(s) exceed the w-test critical value.").replace(
                    "%1", str(len(snooping.candidates))
                )
            )
            note = snooping.note()
            if note:
                feedback.pushWarning(note)
            feedback.pushInfo(
                self.tr("Nothing has been rejected: removing an observation is your decision.")
            )
        else:
            feedback.pushInfo(self.tr("No observation exceeds the w-test critical value."))

        note = reliability_report.note()
        if note:
            feedback.pushWarning(note)

    # -- outputs ---------------------------------------------------------

    def _write_outputs(
        self,
        parameters,
        context,
        network,
        options,
        run,
        solution,
        test,
        snooping,
        reliability_report,
        confidence,
    ) -> dict[str, Any]:
        solution_target = self.parameterAsFileOutput(parameters, OUTPUT_SOLUTION, context)
        if solution_target:
            with open(solution_target, "w", encoding="utf-8") as handle:
                json.dump(solution.to_dict(), handle, indent=2, sort_keys=True)
                handle.write("\n")

        html_target = self.parameterAsFileOutput(parameters, OUTPUT_HTML, context)
        if html_target:
            with open(html_target, "w", encoding="utf-8") as handle:
                handle.write(
                    self._render(
                        network,
                        options,
                        run,
                        solution,
                        test,
                        snooping,
                        reliability_report,
                        confidence,
                    )
                )

        stations_target = self.parameterAsFileOutput(parameters, OUTPUT_STATIONS_CSV, context)
        if stations_target:
            self._write_stations_csv(stations_target, solution)

        residuals_target = self.parameterAsFileOutput(parameters, OUTPUT_RESIDUALS_CSV, context)
        if residuals_target:
            self._write_residuals_csv(residuals_target, run, snooping, reliability_report)

        return {
            OUTPUT_SOLUTION: solution_target,
            OUTPUT_HTML: html_target,
            OUTPUT_STATIONS_CSV: stations_target,
            OUTPUT_RESIDUALS_CSV: residuals_target,
        }

    def _write_stations_csv(self, path: str, solution) -> None:
        """``repr`` rather than a rounded string: a CSV is machine input.

        Rounding here would silently degrade a value someone re-imports, and
        the report is where a human-readable number belongs.
        """
        with open(path, "w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                [
                    "station",
                    "x",
                    "y",
                    "z",
                    "sigma_x",
                    "sigma_y",
                    "sigma_z",
                    "semi_major",
                    "semi_minor",
                    "azimuth_rad",
                ]
            )
            for station in solution.adjusted_stations:
                values = station.position.values
                ellipse = station.ellipse
                writer.writerow(
                    [station.station_id]
                    + [repr(quantity.value) for quantity in values]
                    + [repr(quantity.std_dev) for quantity in values]
                    + (
                        [
                            repr(ellipse.semi_major),
                            repr(ellipse.semi_minor),
                            repr(ellipse.azimuth),
                        ]
                        if ellipse
                        else ["", "", ""]
                    )
                )

    def _write_residuals_csv(self, path: str, run, snooping, reliability_report) -> None:
        by_row = {result.row: result for result in reliability_report.results}
        with open(path, "w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                [
                    "observation",
                    "component",
                    "residual",
                    "standardised_residual",
                    "redundancy",
                    "minimal_detectable_bias",
                    "external_effect",
                    "flagged",
                ]
            )
            flagged = {candidate.row for candidate in snooping.candidates}
            for row, (observation_id, component) in enumerate(run.system.row_labels):
                result = by_row.get(row)
                writer.writerow(
                    [
                        observation_id,
                        component,
                        repr(float(run.residuals[row])),
                        repr(snooping.statistics.get(row, float("nan"))),
                        repr(float(run.redundancy[row])),
                        repr(result.minimal_detectable_bias) if result else "",
                        repr(result.external_effect) if result else "",
                        "yes" if row in flagged else "no",
                    ]
                )

    # -- report ----------------------------------------------------------

    def _render(
        self, network, options, run, solution, test, snooping, reliability_report, confidence
    ) -> str:
        body = [
            f"<h2>{escape(self.tr('Adjustment'))}</h2>",
            render_table(
                [escape(self.tr("Property")), escape(self.tr("Value"))],
                self._summary_rows(network, options, run, confidence),
            ),
            f"<h2>{escape(self.tr('Global test'))}</h2>",
            self._global_test_block(test),
            f"<h2>{escape(self.tr('Adjusted stations'))}</h2>",
            self._stations_table(solution),
            f"<h2>{escape(self.tr('Residuals and data snooping'))}</h2>",
            render_note(
                self.tr(
                    "Observations exceeding the critical value are candidates, not "
                    "rejections. Nothing has been removed: investigate the largest, decide, "
                    "re-adjust, and test again."
                )
            ),
            self._residuals_table(run, snooping, reliability_report),
        ]

        note = snooping.note()
        if note:
            body.append(render_note(note, label=self.tr("Data snooping")))

        note = reliability_report.note()
        if note:
            body.append(render_note(note, label=self.tr("Reliability")))

        return render_document(
            self.tr("Network adjustment report"),
            body,
            footer=escape(self.tr("Generated by GeoComp — geocomp:analysis_network_adjust")),
        )

    def _summary_rows(self, network, options, run, confidence) -> list[list[str]]:
        return [
            [escape(self.tr("Network")), escape(network.id or "—")],
            [escape(self.tr("Coordinate frame")), escape(options.frame.value)],
            [escape(self.tr("Datum definition")), escape(options.datum.value)],
            [escape(self.tr("Datum defect")), escape(run.defect.describe())],
            [escape(self.tr("Solving method")), escape(run.method)],
            [escape(self.tr("Observation equations")), escape(run.system.observation_count)],
            [escape(self.tr("Parameters")), escape(run.layout.size)],
            [escape(self.tr("Degrees of freedom")), escape(run.degrees_of_freedom)],
            [escape(self.tr("Iterations")), escape(run.iterations)],
            [
                escape(self.tr("Largest final correction (m)")),
                format_number(run.max_correction, 6),
            ],
            [
                escape(self.tr("A posteriori variance factor")),
                format_number(run.variance_factor_aposteriori),
            ],
            [escape(self.tr("Condition number")), format_number(run.condition_number, 2)],
            [escape(self.tr("Confidence level")), format_number(confidence, 3)],
        ]

    def _global_test_block(self, test) -> str:
        rows = [
            [escape(self.tr("Statistic")), format_number(test.statistic)],
            [escape(self.tr("Lower critical value")), format_number(test.critical_low)],
            [escape(self.tr("Upper critical value")), format_number(test.critical_high)],
            [
                escape(self.tr("Decision")),
                (
                    f'<span class="pass">{escape(self.tr("Passes"))}</span>'
                    if test.passed
                    else f'<span class="fail">{escape(self.tr("Fails"))}</span>'
                ),
            ],
        ]
        block = render_table([escape(self.tr("Quantity")), escape(self.tr("Value"))], rows)
        if test.note:
            block += render_note(test.note)
        return block

    def _stations_table(self, solution) -> str:
        rows = []
        for station in solution.adjusted_stations:
            values = station.position.values
            ellipse = station.ellipse
            rows.append(
                [
                    escape(station.station_id),
                    format_number(values[0].value, 4),
                    format_number(values[1].value, 4),
                    format_number(values[2].value, 4),
                    format_number(values[0].std_dev, 5),
                    format_number(values[1].std_dev, 5),
                    format_number(values[2].std_dev, 5),
                    format_number(ellipse.semi_major, 5) if ellipse else "—",
                    format_number(ellipse.semi_minor, 5) if ellipse else "—",
                ]
            )
        return render_table(
            [
                escape(self.tr("Station")),
                escape(self.tr("X (m)")),
                escape(self.tr("Y (m)")),
                escape(self.tr("Z (m)")),
                escape(self.tr("Std dev X (m)")),
                escape(self.tr("Std dev Y (m)")),
                escape(self.tr("Std dev Z (m)")),
                escape(self.tr("Semi-major (m)")),
                escape(self.tr("Semi-minor (m)")),
            ],
            rows,
        )

    def _residuals_table(self, run, snooping, reliability_report) -> str:
        by_row = {result.row: result for result in reliability_report.results}
        flagged = {candidate.row for candidate in snooping.candidates}
        rows = []
        for row, (observation_id, component) in enumerate(run.system.row_labels):
            result = by_row.get(row)
            statistic = snooping.statistics.get(row)
            marker = (
                f'<span class="fail">{escape(self.tr("candidate"))}</span>'
                if row in flagged
                else ""
            )
            if result is not None and result.is_uncheckable:
                marker = f'<span class="warning">{escape(self.tr("uncheckable"))}</span>'
            rows.append(
                [
                    escape(observation_id),
                    escape(component),
                    format_number(float(run.residuals[row]), 5),
                    format_number(statistic, 3),
                    format_number(float(run.redundancy[row]), 3),
                    format_number(result.minimal_detectable_bias) if result else "—",
                    format_number(result.external_effect) if result else "—",
                    marker or "—",
                ]
            )
        return render_table(
            [
                escape(self.tr("Observation")),
                escape(self.tr("Component")),
                escape(self.tr("Residual")),
                escape(self.tr("Standardised residual")),
                escape(self.tr("Redundancy")),
                escape(self.tr("Minimal detectable bias")),
                escape(self.tr("External effect")),
                escape(self.tr("Flag")),
            ],
            rows,
        )
