# SPDX-License-Identifier: GPL-2.0-or-later
"""``geocomp:levelling_network`` -- adjust a levelling network (FR-504).

``specs/10-module-levelling.md`` section 4.

Reduced lines become ``HEIGHT_DIFFERENCE`` observations and the adjustment core
does the rest. Nothing here reimplements least squares, which is what makes
levelling a cheap second technique rather than a second pipeline.

What is levelling's own is the **weighting decision** and what the report is
about. A reduced line arrives carrying an uncertainty propagated from its staff
readings, which is rigorous and usually optimistic -- it knows nothing of
refraction, staff calibration or a tripod settling. The ``k * sqrt(L)`` and
``k * sqrt(n)`` models are fitted to lines that suffered all three. Both are
offered; neither is chosen silently.

And the report gives the **relative height uncertainty between pairs of
benchmarks**, which ``specs/10`` section 4 names as the 1D analogue of the error
ellipse. It is the number that answers the question a levelling network is
usually built to answer -- how well do we know the height *difference* between
these two marks -- and it is not the difference of their individual
uncertainties, because they are correlated.
"""

from __future__ import annotations

import csv
import math
from typing import Any

from qgis.core import (
    Qgis,
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFile,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
)

from geocomp.algorithms.base import GeoCompAlgorithm
from geocomp.algorithms.levelling.closures import _reduction_from_dict
from geocomp.algorithms.levelling.common import (
    findings_table,
    read_reductions,
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
from geocomp.core.adjustment import Frame, approximate_values
from geocomp.core.adjustment.least_squares import (
    AdjustmentOptions,
    adjust,
    to_observation_results,
    to_solution,
)
from geocomp.core.errors import GeoCompError
from geocomp.core.models import DatumDefinition, Epoch, Provenance
from geocomp.core.settings_def import WEIGHTING_LENGTH, WEIGHTING_SETUPS
from geocomp.core.statistics.reliability import DEFAULT_ALPHA, DEFAULT_BETA, reliability
from geocomp.core.statistics.tests import data_snooping, global_test
from geocomp.core.techniques.levelling import Benchmark, build_network, weighting_for
from geocomp.core.uncertainty import Quantity
from geocomp.core.units import Unit

__all__ = ["LevellingNetworkAlgorithm"]

REDUCTIONS = "REDUCTIONS"
BENCHMARKS = "BENCHMARKS"
WEIGHTING = "WEIGHTING"
SIGMA_PER_KM = "SIGMA_PER_KM"
SIGMA_PER_SETUP = "SIGMA_PER_SETUP"
FREE = "FREE"
CONFIDENCE = "CONFIDENCE"
ALPHA = "ALPHA"
BETA = "BETA"
EPOCH = "EPOCH"
OUTPUT_SOLUTION = "OUTPUT_SOLUTION"
OUTPUT_HTML = "OUTPUT_HTML"
OUTPUT_CSV = "OUTPUT_CSV"
VARIANCE_FACTOR_APOSTERIORI = "VARIANCE_FACTOR_APOSTERIORI"
DEGREES_OF_FREEDOM = "DEGREES_OF_FREEDOM"
GLOBAL_TEST_PASSED = "GLOBAL_TEST_PASSED"
OUTLIER_COUNT = "OUTLIER_COUNT"
WORST_HEIGHT_UNCERTAINTY = "WORST_HEIGHT_UNCERTAINTY"


class LevellingNetworkAlgorithm(GeoCompAlgorithm):
    """Adjust reduced levelling lines as a 1D network."""

    TR_CONTEXT = "LevellingNetworkAlgorithm"

    def displayName(self) -> str:
        return self.tr("Levelling network adjustment")

    def shortDescription(self) -> str:
        return self.tr("Adjust levelling lines as a 1D network, by length or setup weighting.")

    def help_body(self) -> str:
        return self.tr(
            "<p>Adjusts reduced levelling lines as a one-dimensional network: the same "
            "least squares, the same global test, the same data snooping and reliability "
            "as any other GeoComp adjustment.</p>"
            "<p><b>Two weighting models, and the choice is yours.</b> A reduced line "
            "arrives carrying an uncertainty propagated from its staff readings. That "
            "figure is rigorous and usually optimistic: it knows nothing of refraction, of "
            "staff calibration, or of a tripod settling between backsight and foresight. "
            "The <code>k &times; &radic;L</code> and <code>k &times; &radic;n</code> models "
            "are fitted to lines that suffered all three. Length weighting suits long lines "
            "with consistent sight lengths; setup weighting suits short, irregular ones "
            "where the per-setup reading error dominates. Leaving both coefficients at zero "
            "keeps the propagated uncertainty, and the report says which was used.</p>"
            "<p><b>Benchmarks</b> are entered as <code>id=height</code> pairs, separated by "
            "commas or semicolons; add <code>±sigma</code> to hold one with a weight rather "
            "than exactly, for example <code>BM1=100.000, BM2=103.750±0.002</code>. With "
            "none, the network is free, which is often the right thing to adjust first: it "
            "shows the observations' internal consistency without a datum's errors mixed "
            "in.</p>"
            "<p>Mixing orthometric and ellipsoidal heights without a geoid model is "
            "refused. The error would be the geoid undulation &mdash; tens of metres across "
            "much of Brazil &mdash; and the result would look entirely reasonable.</p>"
            "<p><b>The report gives relative height uncertainties between pairs of "
            "benchmarks</b>, which is the 1D analogue of the error ellipse and usually the "
            "number a levelling network was built to produce. It is not the difference of "
            "the two individual uncertainties, because adjusted heights are correlated.</p>"
            "<h3>Parameters</h3>"
            "<p><b>Reduced lines</b> &mdash; the document a reduction produced. "
            "<b>Benchmarks</b> &mdash; as above. <b>Weighting</b>, and the coefficient for "
            "each model (m per root km, m per root setup); zero means that model is not "
            "configured.</p>"
            "<p><b>Free network</b> &mdash; ignore the benchmarks and remove the datum "
            "defect with an inner constraint.</p>"
            "<p><b>Confidence</b>, <b>alpha</b> and <b>beta</b> &mdash; for the global "
            "test, data snooping and the minimal detectable bias.</p>"
            "<h3>Outputs</h3>"
            "<p><b>Solution</b> &mdash; JSON. <b>Report</b> &mdash; HTML. <b>Heights</b> "
            "&mdash; CSV.</p>"
            "<p><b>No map layers.</b> A levelling network has no planimetry: it determines "
            "heights and nothing else, so every station would be drawn at the same point. "
            "Use the network algorithm in the Analysis menu on a network document that "
            "carries coordinates, or wait for the project store that holds both. Scalars: "
            "<code>VARIANCE_FACTOR_APOSTERIORI</code>, <code>DEGREES_OF_FREEDOM</code>, "
            "<code>GLOBAL_TEST_PASSED</code>, <code>OUTLIER_COUNT</code> and "
            "<code>WORST_HEIGHT_UNCERTAINTY</code> in metres.</p>"
        )

    def initAlgorithm(self, config: dict[str, Any] | None = None) -> None:
        self.addParameter(
            QgsProcessingParameterFile(REDUCTIONS, self.tr("Reduced lines"), extension="json")
        )
        self.addParameter(
            QgsProcessingParameterString(
                BENCHMARKS, self.tr("Benchmarks"), defaultValue="", optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                WEIGHTING,
                self.tr("Weighting"),
                options=[self.tr("By line length"), self.tr("By number of setups")],
                defaultValue=0,
            )
        )
        for name, label in (
            (SIGMA_PER_KM, self.tr("Uncertainty per root kilometre (m)")),
            (SIGMA_PER_SETUP, self.tr("Uncertainty per root setup (m)")),
        ):
            self.addParameter(
                QgsProcessingParameterNumber(
                    name,
                    label,
                    type=QgsProcessingParameterNumber.Type.Double,
                    defaultValue=0.0,
                    minValue=0.0,
                    maxValue=1.0,
                )
            )
        self.addParameter(
            QgsProcessingParameterBoolean(FREE, self.tr("Free network"), defaultValue=False)
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
        self.addAdvancedParameter(
            QgsProcessingParameterNumber(
                EPOCH,
                self.tr("Epoch (decimal year)"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=2026.0,
                minValue=1900.0,
                maxValue=2200.0,
            )
        )
        for name, label, filter_text, by_default in (
            (OUTPUT_SOLUTION, self.tr("Solution"), self.tr("GeoComp solution (*.json)"), True),
            (OUTPUT_HTML, self.tr("Report"), self.tr("HTML files (*.html)"), True),
            (OUTPUT_CSV, self.tr("Heights"), self.tr("CSV files (*.csv)"), False),
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
        reductions = [_reduction_from_dict(line) for line in payload]
        free = self.parameterAsBool(parameters, FREE, context)
        benchmarks = (
            []
            if free
            else self._benchmarks(self.parameterAsString(parameters, BENCHMARKS, context))
        )

        mode = (
            WEIGHTING_LENGTH
            if self.parameterAsEnum(parameters, WEIGHTING, context) == 0
            else WEIGHTING_SETUPS
        )
        weighting = weighting_for(
            mode,
            sigma_per_km=self.parameterAsDouble(parameters, SIGMA_PER_KM, context),
            sigma_per_setup=self.parameterAsDouble(parameters, SIGMA_PER_SETUP, context),
        )

        feedback.setProgress(15)
        try:
            built = build_network(
                reductions, benchmarks, network_id="levelling", weighting=weighting
            )
        except GeoCompError as exc:
            from geocomp.services.messages import message_for

            raise QgsProcessingException(message_for(exc)) from exc

        summarise_findings(built.findings, feedback)
        network = built.network

        datum = (
            DatumDefinition.INNER_CONSTRAINT
            if free or not benchmarks
            else DatumDefinition.CONSTRAINED
        )
        confidence = self.parameterAsDouble(parameters, CONFIDENCE, context)
        options = AdjustmentOptions(
            frame=Frame.HEIGHT_1D, datum=datum, confidence=confidence
        )

        feedback.setProgress(30)
        feedback.pushInfo(self.tr("Adjusting…"))
        start = approximate_values(network, Frame.HEIGHT_1D)
        if not start.is_connected:
            raise QgsProcessingException(
                self.tr(
                    "The lines fall into %1 disconnected pieces, so they cannot be adjusted "
                    "as one network whatever the datum. Level between them, or adjust each "
                    "piece separately."
                ).replace("%1", str(start.components))
            )
        try:
            run = adjust(network, options, approximate=start.values)
        except GeoCompError as exc:
            from geocomp.services.messages import message_for

            raise QgsProcessingException(message_for(exc)) from exc

        if feedback.isCanceled():
            return {}

        feedback.setProgress(55)
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
            alpha=self.parameterAsDouble(parameters, ALPHA, context),
            beta=self.parameterAsDouble(parameters, BETA, context),
        )

        solution = to_solution(
            run,
            network,
            solution_id="levelling-adjustment",
            crs=network.crs,
            epoch=Epoch.from_decimal_year(self.parameterAsDouble(parameters, EPOCH, context)),
            datum=datum,
            height_type=built.height_type,
            provenance=self._provenance(built, options, confidence),
            observation_results=to_observation_results(
                run, snooping=snooping, reliability=reliability_report
            ),
            global_test=test,
            confidence=confidence,
        )

        feedback.setProgress(80)
        self._push_summary(run, test, snooping, feedback)
        write_document(
            self.parameterAsFileOutput(parameters, OUTPUT_SOLUTION, context),
            solution.to_dict(),
        )
        relative = self._relative_uncertainties(run, solution)
        self._write_report(parameters, context, built, run, solution, test, snooping, relative)
        self._write_csv(parameters, context, solution)

        feedback.setProgress(100)

        heights = [
            station.position.height.std_dev for station in solution.adjusted_stations
        ]
        return {
            VARIANCE_FACTOR_APOSTERIORI: run.variance_factor_aposteriori,
            DEGREES_OF_FREEDOM: run.degrees_of_freedom,
            GLOBAL_TEST_PASSED: test.passed,
            OUTLIER_COUNT: len(snooping.candidates),
            WORST_HEIGHT_UNCERTAINTY: max(heights) if heights else 0.0,
            OUTPUT_SOLUTION: self.parameterAsFileOutput(parameters, OUTPUT_SOLUTION, context),
            OUTPUT_HTML: self.parameterAsFileOutput(parameters, OUTPUT_HTML, context),
            OUTPUT_CSV: self.parameterAsFileOutput(parameters, OUTPUT_CSV, context),
        }

    # -- inputs ----------------------------------------------------------

    def _benchmarks(self, raw: str) -> list[Benchmark]:
        """Parse ``BM1=100.000, BM2=103.750±0.002`` into benchmarks.

        A plain-text parameter rather than a file because a levelling network is
        usually tied to one or two marks, and asking for a document to hold two
        numbers is friction with no benefit. A file-scale case is the network
        algorithm in the Analysis menu.
        """
        benchmarks: list[Benchmark] = []
        for chunk in raw.replace(";", ",").split(","):
            entry = chunk.strip()
            if not entry:
                continue
            if "=" not in entry:
                raise QgsProcessingException(
                    self.tr(
                        "'%1' is not a benchmark. Write them as id=height, for example "
                        "BM1=100.000, and add a tolerance as BM2=103.750±0.002 to hold one "
                        "with a weight rather than exactly."
                    ).replace("%1", entry)
                )
            station, _, value = entry.partition("=")
            text = value.strip().replace("+/-", "±")
            height_text, _, sigma_text = text.partition("±")
            try:
                height = float(height_text.strip())
                sigma = float(sigma_text.strip()) if sigma_text.strip() else 0.0
            except ValueError:
                raise QgsProcessingException(
                    self.tr("'%1' does not hold a number.").replace("%1", entry)
                ) from None
            benchmarks.append(
                Benchmark(
                    station=station.strip(),
                    height=(
                        Quantity.exact(height, Unit.METRE)
                        if sigma <= 0.0
                        else Quantity.from_std_dev(height, sigma, Unit.METRE)
                    ),
                    fixed=sigma <= 0.0,
                )
            )
        return benchmarks

    def _provenance(self, built, options, confidence) -> Provenance:
        """What was run, so the result can be reproduced (FR-134).

        The resolved values, never the raw parameter dictionary: that dictionary
        carries file paths and could in general carry a credential, which
        provenance must never hold (NFR-010).
        """
        return Provenance.now(
            algorithm_id=self.spec().id,
            source="geocomp:levelling_network",
            qgis_version=Qgis.QGIS_VERSION,
            parameters={
                "frame": options.frame.value,
                "datum": options.datum.value,
                "confidence": confidence,
                "weighting": built.weighting.describe if built.weighting else "propagated",
                "height_type": built.height_type.value,
            },
        )

    # -- outputs ---------------------------------------------------------

    def _relative_uncertainties(self, run, solution) -> list[tuple[str, str, float, float]]:
        """Relative height uncertainty for every pair of adjusted stations.

        The 1D analogue of the relative error ellipse (``specs/10`` section 4):

            var(H_j - H_i) = var(H_i) + var(H_j) - 2 cov(H_i, H_j)

        The covariance term is why this is not the difference of the two
        individual figures, and why it is usually much *smaller* than either --
        two marks at the ends of one well-observed line know their separation
        far better than either knows its own height.
        """
        layout = run.layout
        covariance = run.parameter_covariance
        stations = [
            station_id
            for station_id in layout.station_ids()
            if layout.station_columns(station_id)
        ]

        rows: list[tuple[str, str, float, float]] = []
        for index, first in enumerate(stations):
            column_first = layout.station_columns(first)["h"]
            for second in stations[index + 1 :]:
                column_second = layout.station_columns(second)["h"]
                variance = (
                    covariance[column_first, column_first]
                    + covariance[column_second, column_second]
                    - 2.0 * covariance[column_first, column_second]
                )
                difference = float(
                    run.parameters[column_second] - run.parameters[column_first]
                )
                rows.append((first, second, difference, math.sqrt(max(variance, 0.0))))
        return rows

    def _push_summary(self, run, test, snooping, feedback) -> None:
        feedback.pushInfo(
            self.tr("Degrees of freedom %1; variance factor %2.")
            .replace("%1", str(run.degrees_of_freedom))
            .replace("%2", format_number(run.variance_factor_aposteriori, 4))
        )
        if not test.passed:
            feedback.pushWarning(
                self.tr(
                    "The global test failed. Either the observations disagree with each "
                    "other more than their weights allow, or the weights are wrong — the "
                    "test cannot tell you which."
                )
            )
        for candidate in snooping.candidates:
            feedback.pushWarning(
                self.tr("Outlier candidate: %1 (w = %2).")
                .replace("%1", candidate.observation_id)
                .replace("%2", format_number(candidate.statistic, 2))
            )

    def _write_report(
        self, parameters, context, built, run, solution, test, snooping, relative
    ) -> None:
        path = self.parameterAsFileOutput(parameters, OUTPUT_HTML, context)
        if not path:
            return

        weighting = built.weighting
        summary = render_table(
            [escape(self.tr("Quantity")), escape(self.tr("Value"))],
            [
                [escape(self.tr("Stations")), str(len(solution.adjusted_stations))],
                [escape(self.tr("Observations")), str(len(run.observations))],
                [escape(self.tr("Degrees of freedom")), str(run.degrees_of_freedom)],
                [
                    escape(self.tr("Variance factor")),
                    format_number(run.variance_factor_aposteriori, 5),
                ],
                [
                    escape(self.tr("Global test")),
                    escape(self.tr("passed") if test.passed else self.tr("FAILED")),
                ],
                [escape(self.tr("Datum")), escape(solution.datum_definition.value)],
                [escape(self.tr("Height type")), escape(built.height_type.value)],
                [
                    escape(self.tr("Weighting")),
                    escape(weighting.describe)
                    if weighting
                    else escape(self.tr("propagated from the staff readings")),
                ],
            ],
        )

        heights = render_table(
            [
                escape(self.tr("Station")),
                escape(self.tr("Height (m)")),
                escape(self.tr("Uncertainty (mm)")),
            ],
            [
                [
                    escape(station.station_id),
                    format_number(station.position.height.value, 5),
                    format_number(station.position.height.std_dev * 1000.0, 3),
                ]
                for station in sorted(
                    solution.adjusted_stations, key=lambda s: s.station_id
                )
            ],
        )

        relative_table = render_table(
            [
                escape(self.tr("From")),
                escape(self.tr("To")),
                escape(self.tr("dH (m)")),
                escape(self.tr("Relative uncertainty (mm)")),
            ],
            [
                [
                    escape(first),
                    escape(second),
                    format_number(difference, 5),
                    format_number(sigma * 1000.0, 3),
                ]
                for first, second, difference, sigma in relative
            ],
        )

        body = [
            f"<h2>{escape(self.tr('Summary'))}</h2>",
            summary,
            f"<h2>{escape(self.tr('Adjusted heights'))}</h2>",
            heights,
            f"<h2>{escape(self.tr('Relative height uncertainties'))}</h2>",
            relative_table,
            render_note(
                self.tr(
                    "The relative uncertainty is the 1D analogue of the relative error "
                    "ellipse, and is usually what a levelling network was built to produce. "
                    "It is not the difference of the two individual uncertainties: adjusted "
                    "heights are correlated, and two marks at the ends of one well-observed "
                    "line know their separation far better than either knows its own height."
                ),
                label=self.tr("Why these are not the individual figures"),
            ),
        ]

        if not test.passed:
            body.append(
                render_note(
                    self.tr(
                        "The global test failed. Either the observations disagree more than "
                        "their weights allow, or the weights are wrong — the test cannot "
                        "distinguish the two. A levelling network weighted by propagated "
                        "staff readings routinely fails it, because that model omits "
                        "refraction, staff calibration and settlement."
                    ),
                    label=self.tr("Global test"),
                )
            )
        if snooping.candidates:
            body.append(f"<h2>{escape(self.tr('Outlier candidates'))}</h2>")
            body.append(
                render_table(
                    [
                        escape(self.tr("Observation")),
                        escape(self.tr("w")),
                        escape(self.tr("Critical value")),
                    ],
                    [
                        [
                            escape(candidate.observation_id),
                            format_number(candidate.statistic, 3),
                            format_number(candidate.critical_high, 3),
                        ]
                        for candidate in snooping.candidates
                    ],
                )
            )
            body.append(
                render_note(
                    self.tr(
                        "Candidates, not rejections. GeoComp never removes an observation "
                        "on its own: in a monitoring network the displacement being measured "
                        "is exactly what an automatic outlier remover would delete."
                    ),
                    label=self.tr("Data snooping"),
                )
            )

        body.append(f"<h2>{escape(self.tr('Findings'))}</h2>")
        body.append(findings_table(built.findings))
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(render_document(self.tr("Levelling network adjustment"), body))

    def _write_csv(self, parameters, context, solution) -> None:
        path = self.parameterAsFileOutput(parameters, OUTPUT_CSV, context)
        if not path:
            return
        with open(path, "w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["station", "height_m", "std_dev_m"])
            for station in sorted(solution.adjusted_stations, key=lambda s: s.station_id):
                writer.writerow(
                    [
                        station.station_id,
                        exact(station.position.height.value),
                        exact(station.position.height.std_dev),
                    ]
                )
