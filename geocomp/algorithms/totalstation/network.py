# SPDX-License-Identifier: GPL-2.0-or-later
"""``geocomp:totalstation_network`` -- classical networks (FR-409).

``specs/09-module-total-station.md`` section 4.4.

Triangulation, trilateration and triangulateration are **not three algorithms**:
they are one adjustment over three different observation sets. Which one a
survey is depends on what was measured, not on what the user picks from a menu,
so this takes the reduced pointings and adjusts whatever they contain.

It builds the network *and* adjusts it, because that is what the menu item
means to a surveyor. The network document is written out as well, so the chain
``pre-process -> build -> inspect -> adjust`` from ``specs/16`` section 9 stays
assemblable in the modeller with the Analysis algorithms.

Free and constrained solutions are both available (FR-222) -- precisely the
*"redes livres e amarradas"* comparison the research project names as a
pedagogical goal.
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
    DATUM_ORDER,
    datum_labels,
    datum_of,
    station_list,
)
from geocomp.algorithms.base import GeoCompAlgorithm
from geocomp.algorithms.layer_outputs import (
    add_result_layer_parameters,
    write_result_layers,
)
from geocomp.algorithms.reporting import (
    escape,
    format_number,
    render_document,
    render_note,
    render_table,
)
from geocomp.algorithms.totalstation.common import (
    findings_table,
    load_json,
    read_reductions,
)
from geocomp.core.adjustment.least_squares import (
    AdjustmentOptions,
    adjust,
    to_observation_results,
    to_solution,
)
from geocomp.core.adjustment.parameters import Frame
from geocomp.core.errors import GeoCompError
from geocomp.core.models import DatumDefinition, Epoch, HeightType, Provenance
from geocomp.core.preanalysis import inspect
from geocomp.core.statistics.reliability import DEFAULT_ALPHA, DEFAULT_BETA, reliability
from geocomp.core.statistics.tests import data_snooping, global_test
from geocomp.core.techniques.total_station import build_network

__all__ = ["ClassicalNetworkAlgorithm"]

REDUCTIONS = "REDUCTIONS"
APPROXIMATE = "APPROXIMATE"
DIMENSION = "DIMENSION"
DATUM = "DATUM"
FIXED_STATIONS = "FIXED_STATIONS"
CONFIDENCE = "CONFIDENCE"
EPOCH = "EPOCH"
CRS = "CRS"
OUTPUT_NETWORK = "OUTPUT_NETWORK"
OUTPUT_SOLUTION = "OUTPUT_SOLUTION"
OUTPUT_HTML = "OUTPUT_HTML"
OUTPUT_STATIONS = "OUTPUT_STATIONS"
DEGREES_OF_FREEDOM = "DEGREES_OF_FREEDOM"
VARIANCE_FACTOR = "VARIANCE_FACTOR"
GLOBAL_TEST_PASSED = "GLOBAL_TEST_PASSED"
OUTLIER_COUNT = "OUTLIER_COUNT"

#: Dimension choices. The index is stored in saved models, so the order is as
#: permanent as an algorithm id.
_DIMENSIONS = (2, 3, 1)
_FRAMES = {1: Frame.HEIGHT_1D, 2: Frame.PLANE_2D, 3: Frame.SPACE_3D}


class ClassicalNetworkAlgorithm(GeoCompAlgorithm):
    """Build a network from reduced pointings and adjust it by least squares."""

    TR_CONTEXT = "ClassicalNetworkAlgorithm"

    def displayName(self) -> str:
        return self.tr("Classical network")

    def shortDescription(self) -> str:
        return self.tr(
            "Build a triangulation, trilateration or triangulateration network from "
            "reduced pointings and adjust it."
        )

    def help_body(self) -> str:
        return self.tr(
            "<p>Assembles the reduced pointings into a geodetic network and adjusts it by "
            "least squares, with the global test, data snooping and reliability analysis.</p>"
            "<p><b>Triangulation, trilateration and triangulateration are not three "
            "different computations.</b> They are one adjustment over three different "
            "observation sets, and which one a survey is depends on what was measured. This "
            "algorithm adjusts whatever the pointings contain.</p>"
            "<p>Free and constrained solutions are both available, which is the comparison "
            "between <i>redes livres</i> and <i>redes amarradas</i> the research project "
            "names as a teaching goal. A free network is adjusted with inner constraints and "
            "is the honest choice when nothing external orients or positions the survey.</p>"
            "<p>The network document is written out as well as the solution, so the chain "
            "<i>pre-process &rarr; build &rarr; inspect &rarr; adjust</i> can be assembled in "
            "the graphical modeller using the Analysis algorithms.</p>"
            "<p><b>No observation is rejected automatically.</b> Data snooping reports "
            "candidates and the decision is yours.</p>"
            "<h3>Parameters</h3>"
            "<p><b>Reduced observations</b> &mdash; the document Generalised pre-processing "
            "produced.</p>"
            "<p><b>Approximate coordinates</b> &mdash; a JSON object mapping each station to "
            "<code>[easting, northing, up]</code>. Required, not derived: the linearised "
            "model needs a point to linearise about, and a traverse or a resection is how a "
            "surveyor obtains one.</p>"
            "<p><b>Dimension</b> &mdash; which of 2D, 3D and 1D to adjust in. It decides "
            "which reduced quantities become observations: a 2D adjustment takes directions "
            "and horizontal distances, a 3D one takes directions, zenith angles and slope "
            "distances. Emitting all of them would use the same measurement twice.</p>"
            "<p><b>Datum definition</b> &mdash; how the datum defect is removed. <b>Fixed "
            "stations</b> &mdash; comma-separated; their approximate coordinates are held "
            "exactly.</p>"
            "<p><b>Confidence level</b>, <b>reference epoch</b> and <b>CRS</b> &mdash; "
            "recorded on the solution.</p>"
            "<h3>Outputs</h3>"
            "<p><b>Network</b> and <b>Solution</b> &mdash; JSON documents; the first feeds "
            "the Analysis algorithms, the second holds the adjusted coordinates with their "
            "full covariance and provenance. <b>Report</b> &mdash; HTML. <b>Adjusted "
            "stations</b> &mdash; CSV. Scalars: <code>DEGREES_OF_FREEDOM</code>, "
            "<code>VARIANCE_FACTOR</code>, <code>GLOBAL_TEST_PASSED</code> and "
            "<code>OUTLIER_COUNT</code>.</p>"
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

    def initAlgorithm(self, config: dict[str, Any] | None = None) -> None:
        self.addParameter(
            QgsProcessingParameterFile(
                REDUCTIONS, self.tr("Reduced observations"), extension="json"
            )
        )
        self.addParameter(
            QgsProcessingParameterFile(
                APPROXIMATE, self.tr("Approximate coordinates"), extension="json"
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                DIMENSION,
                self.tr("Dimension"),
                options=[self.tr("2D — planimetric"), self.tr("3D"), self.tr("1D — heights")],
                defaultValue=0,
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                DATUM,
                self.tr("Datum definition"),
                options=datum_labels(),
                defaultValue=DATUM_ORDER.index(DatumDefinition.INNER_CONSTRAINT),
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                FIXED_STATIONS,
                self.tr("Fixed stations (comma-separated)"),
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
                EPOCH,
                self.tr("Reference epoch (decimal year)"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=2000.0,
            )
        )
        # Required, and not advanced. It was both, which was incoherent: the
        # model refuses to build a position without a CRS ("GeoComp does not
        # infer one"), so declaring the parameter optional promised something
        # the algorithm could not deliver and failed deep inside instead, with
        # a message about a position rather than about the empty field.
        self.addParameter(
            QgsProcessingParameterString(
                CRS, self.tr("CRS authority code, e.g. EPSG:31982"), defaultValue=""
            )
        )
        for name, label, filter_text, by_default in (
            (OUTPUT_NETWORK, self.tr("Network"), self.tr("GeoComp network (*.json)"), True),
            (OUTPUT_SOLUTION, self.tr("Solution"), self.tr("GeoComp solution (*.json)"), True),
            (OUTPUT_HTML, self.tr("Report"), self.tr("HTML files (*.html)"), True),
            (
                OUTPUT_STATIONS,
                self.tr("Adjusted stations"),
                self.tr("CSV files (*.csv)"),
                False,
            ),
        ):
            self.addParameter(
                QgsProcessingParameterFileDestination(
                    name, label, filter_text, optional=True, createByDefault=by_default
                )
            )

        add_result_layer_parameters(self)

    def processAlgorithm(
        self,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> dict[str, Any]:
        results = read_reductions(self.parameterAsFile(parameters, REDUCTIONS, context))
        approximate = self._approximate(self.parameterAsFile(parameters, APPROXIMATE, context))

        dimension = _DIMENSIONS[self.parameterAsEnum(parameters, DIMENSION, context)]
        datum = datum_of(self.parameterAsEnum(parameters, DATUM, context))
        fixed_names = station_list(self.parameterAsString(parameters, FIXED_STATIONS, context))
        crs = self.parameterAsString(parameters, CRS, context).strip()
        if not crs:
            raise QgsProcessingException(
                self.tr(
                    "A CRS authority code is required, for example 'EPSG:31982'. GeoComp "
                    "does not infer one: the adjusted coordinates are meaningless without "
                    "knowing what they are coordinates in, and a guess would be recorded "
                    "on the solution as though it had been chosen. For a local survey with "
                    "no datum, use the projected CRS of the area it sits in."
                )
            )
        confidence = self.parameterAsDouble(parameters, CONFIDENCE, context)

        missing = sorted(set(fixed_names or ()) - set(approximate))
        if missing:
            raise QgsProcessingException(
                self.tr("These fixed stations have no approximate coordinates: %1").replace(
                    "%1", ", ".join(missing)
                )
            )

        feedback.setProgress(15)
        network = build_network(
            results,
            approximate,
            crs=crs,
            dimension=dimension,
            fixed={name: approximate[name] for name in (fixed_names or ())},
        )

        frame = _FRAMES[dimension]
        report = inspect(network, frame=frame)
        blocking = report.blocking
        for finding in report.findings:
            line = f"[{finding.code}] {finding.message}"
            if finding.is_blocking:
                feedback.pushWarning(line)
            else:
                feedback.pushInfo(line)
        if blocking:
            raise QgsProcessingException(
                self.tr("The network cannot be adjusted: %1").replace(
                    "%1", "; ".join(f.message for f in blocking)
                )
            )

        feedback.setProgress(40)
        feedback.pushInfo(self.tr("Adjusting…"))
        options = AdjustmentOptions(frame=frame, datum=datum, confidence=confidence)
        try:
            run = adjust(network, options)
        except GeoCompError as exc:
            from geocomp.services.messages import message_for

            raise QgsProcessingException(message_for(exc)) from exc

        feedback.setProgress(70)
        test = global_test(
            run.variance_factor_aposteriori, run.degrees_of_freedom, confidence=confidence
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
            alpha=DEFAULT_ALPHA,
            beta=DEFAULT_BETA,
        )

        self._push_summary(run, test, snooping, feedback)

        solution = to_solution(
            run,
            network,
            solution_id=f"{network.id}-adjustment",
            crs=crs,
            epoch=Epoch.from_decimal_year(self.parameterAsDouble(parameters, EPOCH, context)),
            datum=datum,
            height_type=HeightType.ORTHOMETRIC if dimension == 1 else HeightType.NONE,
            provenance=Provenance.now(
                algorithm_id=self.spec().id,
                source=self.spec().id,
                qgis_version=Qgis.QGIS_VERSION,
                parameters={
                    "dimension": dimension,
                    "datum": datum.value,
                    "fixed": list(fixed_names or ()),
                    "confidence": confidence,
                },
            ),
            observation_results=to_observation_results(
                run, snooping=snooping, reliability=reliability_report
            ),
            global_test=test,
            confidence=confidence,
        )

        feedback.setProgress(90)
        outputs = self._write(
            parameters, context, network, solution, run, test, snooping, report
        )
        layers = write_result_layers(
            self, parameters, context, solution, network, feedback=feedback
        )
        feedback.setProgress(100)

        return {
            DEGREES_OF_FREEDOM: run.degrees_of_freedom,
            VARIANCE_FACTOR: run.variance_factor_aposteriori,
            GLOBAL_TEST_PASSED: test.passed,
            OUTLIER_COUNT: len(snooping.candidates),
            **outputs,
            **layers,
        }

    # -- inputs ----------------------------------------------------------

    def _approximate(self, path: str) -> dict[str, tuple[float, float, float]]:
        payload = load_json(path, parameter=APPROXIMATE)
        coordinates: dict[str, tuple[float, float, float]] = {}
        for station, values in payload.items():
            try:
                easting, northing, up = (float(v) for v in values)
            except (TypeError, ValueError) as exc:
                raise QgsProcessingException(
                    self.tr(
                        "Approximate coordinates for station '%1' are not three numbers."
                    ).replace("%1", str(station))
                ) from exc
            coordinates[str(station)] = (easting, northing, up)
        if not coordinates:
            raise QgsProcessingException(
                self.tr("The approximate coordinates document is empty.")
            )
        return coordinates

    # -- feedback --------------------------------------------------------

    def _push_summary(self, run, test, snooping, feedback) -> None:
        feedback.pushInfo(
            self.tr("Converged in %1 iteration(s); %2 degree(s) of freedom.")
            .replace("%1", str(run.iterations))
            .replace("%2", str(run.degrees_of_freedom))
        )
        feedback.pushInfo(
            self.tr("Variance factor %1.").replace(
                "%1", format_number(run.variance_factor_aposteriori)
            )
        )
        if test.passed:
            feedback.pushInfo(self.tr("The global test passes."))
        else:
            feedback.pushWarning(self.tr("The global test fails: %1").replace("%1", test.note))
        if snooping.candidates:
            feedback.pushWarning(
                self.tr(
                    "%1 observation(s) exceed the w-test critical value; none was rejected."
                ).replace("%1", str(len(snooping.candidates)))
            )

    # -- outputs ---------------------------------------------------------

    def _write(
        self, parameters, context, network, solution, run, test, snooping, inspection
    ) -> dict[str, Any]:
        network_path = self.parameterAsFileOutput(parameters, OUTPUT_NETWORK, context)
        if network_path:
            with open(network_path, "w", encoding="utf-8") as handle:
                json.dump(network.to_dict(), handle, indent=2, sort_keys=True)
                handle.write("\n")

        solution_path = self.parameterAsFileOutput(parameters, OUTPUT_SOLUTION, context)
        if solution_path:
            with open(solution_path, "w", encoding="utf-8") as handle:
                json.dump(solution.to_dict(), handle, indent=2, sort_keys=True)
                handle.write("\n")

        html_path = self.parameterAsFileOutput(parameters, OUTPUT_HTML, context)
        if html_path:
            with open(html_path, "w", encoding="utf-8") as handle:
                handle.write(self._render(network, solution, run, test, snooping, inspection))

        stations_path = self.parameterAsFileOutput(parameters, OUTPUT_STATIONS, context)
        if stations_path:
            with open(stations_path, "w", encoding="utf-8", newline="") as handle:
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
                        + [repr(q.value) for q in values]
                        + [repr(q.std_dev) for q in values]
                        + (
                            [
                                repr(ellipse.semi_major),
                                repr(ellipse.semi_minor),
                                repr(ellipse.orientation),
                            ]
                            if ellipse
                            else ["", "", ""]
                        )
                    )

        return {
            OUTPUT_NETWORK: network_path,
            OUTPUT_SOLUTION: solution_path,
            OUTPUT_HTML: html_path,
            OUTPUT_STATIONS: stations_path,
        }

    def _render(self, network, solution, run, test, snooping, inspection) -> str:
        summary = [
            [escape(self.tr("Network")), escape(network.id)],
            [escape(self.tr("Stations")), escape(len(network.stations))],
            [escape(self.tr("Observations")), escape(len(network.observations))],
            [escape(self.tr("Datum defect")), escape(run.defect.describe())],
            [escape(self.tr("Degrees of freedom")), escape(run.degrees_of_freedom)],
            [escape(self.tr("Iterations")), escape(run.iterations)],
            [
                escape(self.tr("Variance factor")),
                format_number(run.variance_factor_aposteriori),
            ],
        ]

        rows = []
        for station in solution.adjusted_stations:
            values = station.position.values
            ellipse = station.ellipse
            rows.append(
                [
                    escape(station.station_id),
                    format_number(values[0].value),
                    format_number(values[1].value),
                    format_number(values[2].value),
                    format_number(values[0].std_dev * 1000.0, 2),
                    format_number(values[1].std_dev * 1000.0, 2),
                    format_number(ellipse.semi_major * 1000.0, 2) if ellipse else "—",
                ]
            )

        verdict_class = "pass" if test.passed else "fail"
        verdict = (
            self.tr("The global test passes.")
            if test.passed
            else self.tr("The global test fails.")
        )

        body = [
            f"<h2>{escape(self.tr('Network'))}</h2>",
            render_table([escape(self.tr("Property")), escape(self.tr("Value"))], summary),
            f"<h2>{escape(self.tr('Adjusted stations'))}</h2>",
            render_table(
                [
                    escape(self.tr("Station")),
                    escape(self.tr("X (m)")),
                    escape(self.tr("Y (m)")),
                    escape(self.tr("Z (m)")),
                    escape(self.tr("Std dev X (mm)")),
                    escape(self.tr("Std dev Y (mm)")),
                    escape(self.tr("Semi-major (mm)")),
                ],
                rows,
            ),
            f"<h2>{escape(self.tr('Global test'))}</h2>",
            f'<p class="{verdict_class}">{escape(verdict)}</p>',
            render_table(
                [escape(self.tr("Quantity")), escape(self.tr("Value"))],
                [
                    [escape(self.tr("Statistic")), format_number(test.statistic)],
                    [escape(self.tr("Lower critical value")), format_number(test.critical_low)],
                    [
                        escape(self.tr("Upper critical value")),
                        format_number(test.critical_high),
                    ],
                ],
            ),
        ]
        if test.note:
            body.append(render_note(test.note))

        body.append(f"<h2>{escape(self.tr('Data snooping'))}</h2>")
        body.append(
            render_note(
                self.tr(
                    "Observations exceeding the critical value are candidates, not "
                    "rejections. Nothing has been removed."
                )
            )
        )
        body.append(
            render_table(
                [
                    escape(self.tr("Observation")),
                    escape(self.tr("Standardised residual")),
                    escape(self.tr("Critical value")),
                    escape(self.tr("Redundancy")),
                ],
                [
                    [
                        escape(candidate.observation_id),
                        format_number(candidate.statistic, 3),
                        format_number(candidate.critical_value, 3),
                        format_number(candidate.redundancy, 3),
                    ]
                    for candidate in snooping.candidates
                ]
                or [["—", "—", "—", "—"]],
            )
        )

        body.append(f"<h2>{escape(self.tr('Inspection'))}</h2>")
        body.append(findings_table(inspection.findings))

        return render_document(
            self.tr("Classical network report"),
            body,
            footer=escape(self.tr("Generated by GeoComp — geocomp:totalstation_network")),
        )
