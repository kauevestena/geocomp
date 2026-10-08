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
from dataclasses import dataclass
from typing import Any

from qgis.core import (
    Qgis,
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterEnum,
    QgsProcessingParameterField,
    QgsProcessingParameterFile,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
    QgsProcessingParameterVectorLayer,
    QgsWkbTypes,
)

from geocomp.algorithms.analysis.common import (
    DATUM_ORDER,
    datum_labels,
    datum_of,
    station_list,
)
from geocomp.algorithms.base import GeoCompAlgorithm
from geocomp.algorithms.defaults import (
    configured,
    configured_epoch,
    recorded_epoch,
    run_epoch,
)
from geocomp.algorithms.display import display_format
from geocomp.algorithms.labels import defect_words
from geocomp.algorithms.layer_outputs import (
    add_result_layer_parameters,
    write_result_layers,
)
from geocomp.algorithms.layer_sources import file_or_layer, point_type, stations_of_layer
from geocomp.algorithms.reporting import (
    escape,
    exact,
    format_number,
    global_test_failed,
    no_redundancy,
    render_document,
    render_note,
    render_table,
)
from geocomp.algorithms.totalstation.common import (
    document_source,
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
from geocomp.core.models import DatumDefinition, HeightType, Provenance
from geocomp.core.preanalysis import inspect
from geocomp.core.statistics.reliability import reliability
from geocomp.core.statistics.tests import data_snooping, global_test
from geocomp.core.techniques.total_station import build_network
from geocomp.core.techniques.total_station.grid import GridReduction, reduce_distances_to_grid
from geocomp.core.uncertainty import Quantity
from geocomp.core.units import Unit
from geocomp.io.tabular import read_coordinates
from geocomp.services.messages import finding_text, message_for

__all__ = ["ClassicalNetworkAlgorithm"]

REDUCTIONS = "REDUCTIONS"
APPROXIMATE = "APPROXIMATE"
APPROXIMATE_LAYER = "APPROXIMATE_LAYER"
STATION_FIELD = "STATION_FIELD"
HEIGHT_FIELD = "HEIGHT_FIELD"
DIMENSION = "DIMENSION"
DATUM = "DATUM"
FIXED_STATIONS = "FIXED_STATIONS"
CONFIDENCE = "CONFIDENCE"
EPOCH = "EPOCH"
CRS = "CRS"
REDUCE_TO_GRID = "REDUCE_TO_GRID"
GEOID_UNDULATION = "GEOID_UNDULATION"
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


@dataclass(frozen=True)
class _GridOutcome:
    """What became of the reduction to the grid, for the summary, the report and
    the provenance: every distance it reduced, or why it reduced none."""

    records: tuple[GridReduction, ...] = ()
    reason: str = ""
    #: In words, translated where it was said.
    said: str = ""

    @property
    def applied(self) -> bool:
        return bool(self.records)

    def provenance(self, undulation: float) -> dict[str, Any]:
        if not self.applied:
            return {"applied": False, "reason": self.reason}
        ppm = [record.parts_per_million for record in self.records]
        return {
            "applied": True,
            "distances": len(self.records),
            "geoid_undulation": undulation,
            "ppm": [min(ppm), max(ppm)],
        }


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
            "<code>[easting, northing, up]</code>, or a CSV or .xlsx table with a station, "
            "its easting, its northing and its height on each row. Required, not derived: "
            "the linearised model needs a point to linearise about, and a traverse or a "
            "resection is how a surveyor obtains one.</p>"
            "<p><b>Approximate coordinates, as a point layer of the project</b> &mdash; the "
            "alternative to the file: each point a station, named by the <b>field naming "
            "each station</b>, its height from the <b>field holding each station's "
            "height</b> or, with none named, from the point's Z. A layer in another CRS is "
            "carried into the network's, horizontally; the heights are kept as given. Give "
            "the file or the layer, not both.</p>"
            "<p><b>Dimension</b> &mdash; which of 2D, 3D and 1D to adjust in. It decides "
            "which reduced quantities become observations: a 2D adjustment takes directions "
            "and horizontal distances, a 3D one takes directions, zenith angles and slope "
            "distances. Emitting all of them would use the same measurement twice.</p>"
            "<p><b>Datum definition</b> &mdash; how the datum defect is removed. <b>Fixed "
            "stations</b> &mdash; comma-separated; their approximate coordinates are held "
            "exactly.</p>"
            "<p><b>Confidence level</b>, <b>reference epoch</b> and <b>CRS</b> &mdash; "
            "recorded on the solution.</p>"
            "<p><b>Reduce measured distances to the grid</b> &mdash; a total station "
            "measures a distance on the ground, and a plane adjustment computes one from "
            "grid coordinates. On a projected CRS the two differ by the reduction to the "
            "ellipsoid, about 157 ppm for each kilometre of height, and by the projection's "
            "scale factor, on UTM from &minus;400 ppm at the central meridian to about "
            "+1000 ppm at a zone's edge. In a 2D adjustment each horizontal distance is "
            "reduced by both, at the mean height of its ends and the scale factor of its "
            "line, and the report states the range applied. Coordinates that lie outside "
            "the area the CRS is defined for are read as a local plane and are not "
            "reduced; neither is a network in a CRS that is not projected.</p>"
            "<p><b>Geoid undulation N</b> (m) &mdash; the approximate heights are "
            "orthometric, and the reduction to the ellipsoid needs ellipsoidal ones, "
            "<i>h = H + N</i>. Each 10 m of N left out is 1.6 ppm.</p>"
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
                APPROXIMATE,
                self.tr("Approximate coordinates"),
                fileFilter=self.tr("Coordinates (*.json *.csv *.xlsx);;All files (*)"),
                optional=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                APPROXIMATE_LAYER,
                self.tr("Approximate coordinates, as a point layer of the project"),
                types=[point_type()],
                optional=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                STATION_FIELD,
                self.tr("Field naming each station"),
                parentLayerParameterName=APPROXIMATE_LAYER,
                optional=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                HEIGHT_FIELD,
                self.tr("Field holding each station's height (the points' Z when none)"),
                parentLayerParameterName=APPROXIMATE_LAYER,
                optional=True,
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
                defaultValue=configured("stochastic.confidence_level"),
                minValue=0.5,
                maxValue=0.9999,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterNumber(
                EPOCH,
                self.tr("Reference epoch, decimal year (0 = the network's own)"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=configured_epoch(0.0),
            )
        )
        # Required, and not advanced. It was both, which was incoherent: the
        # model refuses to build a position without a CRS ("GeoComp does not
        # infer one"), so declaring the parameter optional promised something
        # the algorithm could not deliver and failed deep inside instead, with
        # a message about a position rather than about the empty field.
        self.addParameter(
            QgsProcessingParameterString(
                CRS,
                self.tr("CRS authority code, e.g. EPSG:31982"),
                defaultValue=configured("reference_systems.preferred_crs"),
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                REDUCE_TO_GRID,
                self.tr("Reduce measured distances to the grid"),
                defaultValue=True,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterNumber(
                GEOID_UNDULATION,
                self.tr("Geoid undulation N (m)"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=0.0,
                minValue=-150.0,
                maxValue=150.0,
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
        dimension = _DIMENSIONS[self.parameterAsEnum(parameters, DIMENSION, context)]
        results = read_reductions(
            self.parameterAsFile(parameters, REDUCTIONS, context), needs_heights=dimension == 3
        )
        datum = datum_of(self.parameterAsEnum(parameters, DATUM, context))
        fixed_names = station_list(self.parameterAsString(parameters, FIXED_STATIONS, context))
        crs = self.parameterAsString(parameters, CRS, context).strip()
        if not crs:
            raise QgsProcessingException(
                self.tr(
                    "A CRS authority code is required, for example 'EPSG:31982'. GeoComp "
                    "does not infer one: the adjusted coordinates are meaningless without "
                    "knowing what they are coordinates in, and a guess would be recorded "
                    "on the solution as though it had been chosen. Give one; for a local "
                    "survey with no datum, use the projected CRS of the area it sits in."
                )
            )
        confidence = self.parameterAsDouble(parameters, CONFIDENCE, context)
        approximate = self._approximate(parameters, context, crs, feedback)

        missing = sorted(set(fixed_names or ()) - set(approximate))
        if missing:
            raise QgsProcessingException(
                self.tr("These fixed stations have no approximate coordinates; add them: "
                        "%1").replace(
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
            source_file=document_source(
                self.parameterAsFile(parameters, REDUCTIONS, context), parameter=REDUCTIONS
            ),
        )
        undulation = self.parameterAsDouble(parameters, GEOID_UNDULATION, context)
        network, grid = self._to_grid(
            network,
            crs,
            dimension=dimension,
            wanted=self.parameterAsBool(parameters, REDUCE_TO_GRID, context),
            undulation=undulation,
            context=context,
            feedback=feedback,
        )

        frame = _FRAMES[dimension]
        report = inspect(network, frame=frame)
        blocking = report.blocking
        for finding in report.findings:
            line = f"[{finding.code}] {finding_text(finding)}"
            if finding.is_blocking:
                feedback.pushWarning(line)
            else:
                feedback.pushInfo(line)
        if blocking:
            raise QgsProcessingException(
                self.tr("The network cannot be adjusted; correct these first: %1").replace(
                    "%1", "; ".join(finding_text(f) for f in blocking)
                )
            )

        feedback.setProgress(40)
        feedback.pushInfo(self.tr("Adjusting…"))
        options = AdjustmentOptions(frame=frame, datum=datum, confidence=confidence)
        try:
            run = adjust(network, options)
        except GeoCompError as exc:
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
            alpha=float(configured("stochastic.outlier_alpha")),
            beta=float(configured("stochastic.outlier_beta")),
        )

        self._push_summary(run, test, snooping, feedback)

        epoch, epoch_origin = run_epoch(
            self.parameterAsDouble(parameters, EPOCH, context), network, 2000.0
        )
        solution = recorded_epoch(
            to_solution(
                run,
                network,
                solution_id=f"{network.id}-adjustment",
                crs=crs,
                epoch=epoch,
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
                        "grid_reduction": grid.provenance(undulation),
                    },
                ),
                observation_results=to_observation_results(
                    run, snooping=snooping, reliability=reliability_report
                ),
                global_test=test,
                confidence=confidence,
            ),
            epoch_origin,
            feedback,
        )

        feedback.setProgress(90)
        outputs = self._write(
            parameters, context, network, solution, run, test, snooping, report, grid
        )
        layers = write_result_layers(
            self,
            parameters,
            context,
            solution,
            network,
            feedback=feedback,
            solution_path=self.parameterAsFileOutput(parameters, OUTPUT_SOLUTION, context),
        )
        feedback.setProgress(100)

        return {
            DEGREES_OF_FREEDOM: run.degrees_of_freedom,
            VARIANCE_FACTOR: run.variance_factor_aposteriori,
            GLOBAL_TEST_PASSED: test.passed if test.tested else None,
            OUTLIER_COUNT: len(snooping.candidates),
            **outputs,
            **layers,
        }

    # -- inputs ----------------------------------------------------------

    def _approximate(
        self, parameters, context, crs: str, feedback
    ) -> dict[str, tuple[float, float, float]]:
        """The stations to linearise about, from the file or the point layer -- exactly one (FR-320)."""
        path, layer = file_or_layer(
            self, parameters, context, file=APPROXIMATE, layer=APPROXIMATE_LAYER
        )
        if layer is None:
            return self._approximate_file(path)
        name_field = self.parameterAsString(parameters, STATION_FIELD, context)
        height_field = self.parameterAsString(parameters, HEIGHT_FIELD, context)
        if not name_field:
            raise QgsProcessingException(
                self.about_input(
                    STATION_FIELD,
                    self.tr("Name the field of '%1' that holds each station's name.").replace(
                        "%1", layer.name()
                    ),
                )
            )
        if not height_field and not QgsWkbTypes.hasZ(layer.wkbType()):
            raise QgsProcessingException(
                self.about_input(
                    HEIGHT_FIELD,
                    self.tr("The points of '%1' have no Z. Name the field that holds each "
                            "station's height.").replace("%1", layer.name()),
                )
            )
        return stations_of_layer(
            layer,
            name_field=name_field,
            height_field=height_field,
            crs=crs,
            context=context,
            feedback=feedback,
        )

    def _approximate_file(self, path: str) -> dict[str, tuple[float, float, float]]:
        if path.lower().endswith((".csv", ".xlsx")):
            # FR-160: stations from a table as well as observations from a book.
            try:
                return read_coordinates(path)
            except GeoCompError as exc:
                raise QgsProcessingException(message_for(exc)) from exc
        payload = load_json(path, parameter=APPROXIMATE)
        coordinates: dict[str, tuple[float, float, float]] = {}
        for station, values in payload.items():
            try:
                easting, northing, up = (float(v) for v in values)
            except (TypeError, ValueError) as exc:
                raise QgsProcessingException(
                    self.tr(
                        "Approximate coordinates for station '%1' are not three numbers. "
                        "Give three numbers: easting, northing and height."
                    ).replace("%1", str(station))
                ) from exc
            coordinates[str(station)] = (easting, northing, up)
        if not coordinates:
            raise QgsProcessingException(
                self.tr("The approximate coordinates document is empty. Add its entries, "
                        "or choose another document.")
            )
        return coordinates

    # -- feedback --------------------------------------------------------

    def _to_grid(
        self, network, crs_code, *, dimension, wanted, undulation, context, feedback
    ) -> tuple[Any, _GridOutcome]:
        """Carry the measured distances to the grid of the CRS, if it has one (FR-405).

        The scale factor is QGIS's, from the CRS at a point: ``core`` reduces,
        and the projection is QGIS's business. Coordinates outside the area the
        CRS is defined for are a local plane -- which is what RD-01 is, in
        EPSG:31982 -- and are left as they are, saying so.
        """
        from qgis.core import (
            QgsCoordinateReferenceSystem,
            QgsCoordinateTransform,
            QgsCsException,
            QgsPoint,
            QgsPointXY,
        )

        def not_reduced(reason: str, note: str) -> tuple[Any, _GridOutcome]:
            feedback.pushInfo(note)
            return network, _GridOutcome(reason=reason, said=note)

        if not wanted:
            return not_reduced("not_asked", self.tr("No: the reduction was turned off."))
        if dimension != 2:
            return not_reduced(
                "not_planimetric",
                self.tr(
                    "No: distances are reduced to the grid in a 2D adjustment only, and this "
                    "one is not 2D."
                ),
            )
        crs = QgsCoordinateReferenceSystem(crs_code)
        if not crs.isValid() or crs.isGeographic():
            return not_reduced(
                "not_projected",
                self.tr("No: %1 is not a projected CRS, so there is no grid to reduce to.").replace(
                    "%1", crs_code
                ),
            )
        to_geographic = QgsCoordinateTransform(
            crs, crs.toGeographicCrs(), context.transformContext()
        )
        area = crs.bounds()
        outside = []
        for station in sorted(network.stations.values(), key=lambda item: item.id):
            position = station.approx_position
            if position is None:
                continue
            try:
                point = to_geographic.transform(
                    QgsPointXY(position.values[0].value, position.values[1].value)
                )
            except QgsCsException:
                outside.append(station.id)
                continue
            if not area.isEmpty() and not area.contains(point):
                outside.append(station.id)
        if outside:
            note = (
                self.tr(
                    "No: these stations lie outside the area %1 is defined for, so the "
                    "coordinates are read as a local plane: %2."
                )
                .replace("%1", crs_code)
                .replace("%2", ", ".join(outside))
            )
            feedback.pushWarning(note)
            return network, _GridOutcome(reason="outside_area", said=note)

        def scale_factor(easting: float, northing: float) -> float:
            point = to_geographic.transform(QgsPointXY(easting, northing))
            factors = crs.factors(QgsPoint(point.x(), point.y()))
            if not factors.isValid():
                raise QgsProcessingException(
                    self.tr("QGIS gives no scale factor for %1 at %2, %3. Check that the "
                            "coordinates are inside the CRS's area of use.")
                    .replace("%1", crs_code)
                    .replace("%2", format_number(easting, 3))
                    .replace("%3", format_number(northing, 3))
                )
            if abs(factors.meridionalScale() - factors.parallelScale()) > 1e-8:
                raise QgsProcessingException(
                    self.tr(
                        "%1 is not a conformal projection: its scale differs between the "
                        "meridian and the parallel, so a distance's reduction would depend on "
                        "its direction. Adjust in a conformal projection, such as UTM, or turn "
                        "the reduction off."
                    ).replace("%1", crs_code)
                )
            return factors.meridionalScale()

        try:
            reduced, records = reduce_distances_to_grid(
                network,
                scale_factor=scale_factor,
                undulation=Quantity.exact(undulation, Unit.METRE),
            )
        except GeoCompError as exc:
            raise QgsProcessingException(message_for(exc)) from exc
        if not records:
            return not_reduced("no_distances", self.tr("No: the network has no distance to reduce."))
        ppm = [record.parts_per_million for record in records]
        note = (
            self.tr("%1 distance(s), from %2 to %3 ppm.")
            .replace("%1", str(len(records)))
            .replace("%2", format_number(min(ppm), 1))
            .replace("%3", format_number(max(ppm), 1))
        )
        feedback.pushInfo(self.tr("Reduced to the grid: %1").replace("%1", note))
        return reduced, _GridOutcome(records=records, said=note)

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
        if not test.tested:
            feedback.pushWarning(no_redundancy())
        elif test.passed:
            feedback.pushInfo(self.tr("The global test passes."))
        else:
            feedback.pushWarning(global_test_failed(test))
        if snooping.candidates:
            feedback.pushWarning(
                self.tr(
                    "%1 observation(s) exceed the w-test critical value; none was rejected."
                ).replace("%1", str(len(snooping.candidates)))
            )

    # -- outputs ---------------------------------------------------------

    def _write(
        self, parameters, context, network, solution, run, test, snooping, inspection, grid
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
                handle.write(
                    self._render(network, solution, run, test, snooping, inspection, grid)
                )

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
                        + [exact(q.value) for q in values]
                        + [exact(q.std_dev) for q in values]
                        + (
                            [
                                exact(ellipse.semi_major),
                                exact(ellipse.semi_minor),
                                exact(ellipse.orientation),
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

    def _render(self, network, solution, run, test, snooping, inspection, grid) -> str:
        summary = [
            [escape(self.tr("Network")), escape(network.id)],
            [escape(self.tr("Stations")), escape(len(network.stations))],
            [escape(self.tr("Observations")), escape(len(network.observations))],
            [escape(self.tr("Datum defect")), escape(defect_words(run.defect))],
            [escape(self.tr("Degrees of freedom")), escape(run.degrees_of_freedom)],
            [escape(self.tr("Iterations")), escape(run.iterations)],
            [
                escape(self.tr("Variance factor")),
                format_number(run.variance_factor_aposteriori),
            ],
            [escape(self.tr("Distances reduced to the grid")), escape(grid.said)],
        ]

        shown = display_format()
        rows = []
        for station in solution.adjusted_stations:
            values = station.position.values
            ellipse = station.ellipse
            rows.append(
                [
                    escape(station.station_id),
                    shown.coordinate(values[0].value),
                    shown.coordinate(values[1].value),
                    shown.coordinate(values[2].value),
                    format_number(values[0].std_dev * 1000.0, 2),
                    format_number(values[1].std_dev * 1000.0, 2),
                    format_number(ellipse.semi_major * 1000.0, 2) if ellipse else "—",
                ]
            )

        verdict_class = "pass" if test.passed and test.tested else "fail"
        verdict = (
            no_redundancy()
            if not test.tested
            else self.tr("The global test passes.")
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
        if test.tested and not test.passed:
            body.append(render_note(global_test_failed(test)))

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
