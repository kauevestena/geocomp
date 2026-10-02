# SPDX-License-Identifier: GPL-2.0-or-later
"""The combined adjustment behind the four Integration presets (``specs/13`` section 1).

``specs/13`` section 1: *each is a preset over one general combined-adjustment
capability; the presets exist because they carry different defaults, different
validation, and different explanatory material.* This is the capability, as a
Processing algorithm; each preset says which technique networks it takes,
whether it combines in a geocentric frame or locally, and whether a geoid is
required.

**The inputs are network documents** -- what the technique algorithms write:
*Build baselines* for GNSS, *Classical network* for the total station, *Network
adjustment* for levelling (``specs/16`` section 4). Nothing is re-derived here:
the combination takes each technique's network as its producer built it.

**The datum.** A network document leaves its marks free unless its producer
held them, so the presets take *Fixed stations*: each is held where the first
input that places it says it is -- for GNSS, the base's own coordinates from
the processing. In a geocentric combination only a geocentric or geodetic
position can be held; a total-station station held in grid coordinates is
refused by the combination with the reason.

**A projected input** is read through the projection its CRS names, which QGIS
knows and the core does not (``specs/07`` section 4.4): Transverse Mercator
and UTM on a frame GeoComp can transform from. Only starting positions depend
on it.
"""

from __future__ import annotations

import csv
import json
import math
import tempfile
from pathlib import Path
from typing import Any, ClassVar

from qgis.core import (
    Qgis,
    QgsCoordinateReferenceSystem,
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

from geocomp.algorithms.analysis.common import DATUM_ORDER, datum_labels, datum_of, load_network, station_list
from geocomp.algorithms.base import GeoCompAlgorithm
from geocomp.algorithms.defaults import configured, configured_epoch
from geocomp.algorithms.display import display_format
from geocomp.algorithms.layer_outputs import add_result_layer_parameters, write_result_layers
from geocomp.core.errors import GeoCompError, ValidationError
from geocomp.core.geodesy.ellipsoid import ELLIPSOIDS
from geocomp.core.geodesy.frames import FRAME_NAMES, canonical_frame
from geocomp.core.geodesy.projection import ProjectionParameters, utm_parameters
from geocomp.core.models import (
    ConstraintMode,
    ConstraintSpec,
    CoordinateSystem,
    DatumDefinition,
    Epoch,
    Network,
)
from geocomp.core.number_format import localised
from geocomp.core.techniques.integration import GridFrame, Velocity, adjust_combination, combine, route
from geocomp.core.uncertainty import Quantity

__all__ = [
    "GNSS",
    "LEVELLING",
    "TOTAL_STATION",
    "_CombinedAdjustmentAlgorithm",
]

GNSS = "GNSS"
TOTAL_STATION = "TOTAL_STATION"
LEVELLING = "LEVELLING"
READINGS = "READINGS"
KNOWN_GRAVITY = "KNOWN_GRAVITY"
FRAME = "FRAME"
EPOCH = "EPOCH"
VELOCITIES = "VELOCITIES"
GEOID = "GEOID"
GEOID_SIGMA = "GEOID_SIGMA"
FIXED_STATIONS = "FIXED_STATIONS"
DATUM = "DATUM"
ENGINE = "ENGINE"
VARIANCE_COMPONENTS = "VARIANCE_COMPONENTS"
CONFIDENCE = "CONFIDENCE"
OUTPUT_SOLUTION = "OUTPUT_SOLUTION"
OUTPUT_HTML = "OUTPUT_HTML"
OUTPUT_NETWORK = "OUTPUT_NETWORK"
OUTPUT_GRAVITY = "OUTPUT_GRAVITY"
VARIANCE_FACTOR_APOSTERIORI = "VARIANCE_FACTOR_APOSTERIORI"
DEGREES_OF_FREEDOM = "DEGREES_OF_FREEDOM"
GLOBAL_TEST_PASSED = "GLOBAL_TEST_PASSED"
OUTLIER_COUNT = "OUTLIER_COUNT"
ENGINE_USED = "ENGINE_USED"

#: Engine choices; the index is what a saved model stores.
ENGINES = ("in_house", "dynadjust")
_TECHNIQUE_OF_INPUT = {GNSS: "gnss", TOTAL_STATION: "total_station", LEVELLING: "levelling"}


def _stated_epoch() -> str:
    """The stated default epoch as the parameter's text: empty, taking the inputs', when none is."""
    stated = configured_epoch(0.0)
    return str(stated) if stated else ""


class _CombinedAdjustmentAlgorithm(GeoCompAlgorithm):
    """Adjust several techniques' networks together (``specs/13``).

    Subclasses set the class attributes; everything else is shared. They keep
    this ``TR_CONTEXT``, so the strings written here are found at run time under
    the context they were extracted in.
    """

    TR_CONTEXT = "CombinedAdjustmentAlgorithm"

    #: ``(parameter, required)`` for each technique network the preset takes.
    INPUTS: ClassVar[tuple[tuple[str, bool], ...]] = ()
    #: ``True`` geocentric, ``False`` local, ``None`` geocentric when GNSS is given.
    GEOCENTRIC: ClassVar[bool | None] = True
    GEOID_REQUIRED: ClassVar[bool] = False
    GRAVITY: ClassVar[bool] = False
    MINIMUM_TECHNIQUES: ClassVar[int] = 2

    # -- declaration -----------------------------------------------------

    def _input_label(self, name: str) -> str:
        return {
            GNSS: self.tr("GNSS network (from Build baselines)"),
            TOTAL_STATION: self.tr("Total station network (from Classical network)"),
            LEVELLING: self.tr("Levelling network (from Network adjustment)"),
        }[name]

    def common_help(self) -> str:
        return self.tr(
            "<p><b>Inputs</b> are the network documents the technique algorithms write. "
            "Each is combined as its producer built it; stations with the same name in two "
            "inputs are the same mark, which is what ties the techniques together.</p>"
            "<p><b>Fixed stations</b> are held where the first input that places them says "
            "they are &mdash; for GNSS, the base coordinates from the processing.</p>"
            "<p><b>Engine</b>: DynAdjust is used only when it can adjust everything. Gravity, "
            "an observation type it lacks, a local system or orthometric heights keep the "
            "combination in the in-house core, and the report says which and why.</p>"
            "<p>The report has a <i>Techniques</i> section: each technique's share of the "
            "redundancy and of the weighted squares, the variance components when asked "
            "for, the geoid residuals, and every frame transformation applied.</p>"
        )

    def initAlgorithm(self, config: dict[str, Any] | None = None) -> None:
        for name, required in self.INPUTS:
            self.addParameter(
                QgsProcessingParameterFile(
                    name, self._input_label(name), extension="json", optional=not required
                )
            )
        if self.GRAVITY:
            self.addParameter(
                QgsProcessingParameterFile(
                    READINGS,
                    self.tr("Gravity readings (from Gravimetry pre-processing)"),
                    extension="json",
                    optional=True,
                )
            )
            self.addParameter(
                QgsProcessingParameterString(
                    KNOWN_GRAVITY, self.tr("Known gravity (station=mGal[±sigma], ...)"), optional=True
                )
            )
        if self.GEOCENTRIC is not False:
            self.addParameter(
                QgsProcessingParameterEnum(
                    FRAME, self.tr("Frame to combine in"), options=list(FRAME_NAMES), defaultValue=0
                )
            )
        self.addParameter(
            QgsProcessingParameterString(
                EPOCH,
                self.tr("Epoch (decimal year; empty takes the inputs')"),
                defaultValue=_stated_epoch(),
                optional=True,
            )
        )
        if self.GEOCENTRIC is not False:
            self.addParameter(
                QgsProcessingParameterFile(
                    VELOCITIES,
                    self.tr("Station velocities (CSV: station, vx, vy, vz in m/yr)"),
                    extension="csv",
                    optional=True,
                )
            )
            self.addParameter(
                QgsProcessingParameterFile(
                    GEOID,
                    self.tr("Geoid model (GTX or ESRI ASCII grid)"),
                    defaultValue=configured("reference_systems.geoid_model") or None,
                    optional=not self.GEOID_REQUIRED,
                )
            )
            self.addParameter(
                QgsProcessingParameterNumber(
                    GEOID_SIGMA,
                    self.tr("Geoid model uncertainty (m)"),
                    type=QgsProcessingParameterNumber.Type.Double,
                    defaultValue=configured("reference_systems.geoid_sigma"),
                    minValue=0.0,
                    maxValue=10.0,
                )
            )
        self.addParameter(
            QgsProcessingParameterString(
                FIXED_STATIONS, self.tr("Fixed stations (comma-separated)"), optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                DATUM,
                self.tr("Datum definition"),
                options=datum_labels(),
                defaultValue=DATUM_ORDER.index(DatumDefinition.FIXED),
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                ENGINE,
                self.tr("Engine"),
                options=[
                    self.tr("GeoComp in-house core"),
                    self.tr("DynAdjust, when it can adjust everything"),
                ],
                defaultValue=0,
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                VARIANCE_COMPONENTS,
                self.tr("Estimate a variance component per technique"),
                defaultValue=False,
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
        outputs = [
            (OUTPUT_SOLUTION, self.tr("Solution"), self.tr("GeoComp solution (*.json)"), True),
            (OUTPUT_HTML, self.tr("Report"), self.tr("HTML files (*.html)"), True),
            (OUTPUT_NETWORK, self.tr("Combined network"), self.tr("GeoComp network (*.json)"), False),
        ]
        if self.GRAVITY:
            outputs.append(
                (OUTPUT_GRAVITY, self.tr("Gravity solution"), self.tr("GeoComp solution (*.json)"), False)
            )
        for name, label, filter_text, by_default in outputs:
            self.addParameter(
                QgsProcessingParameterFileDestination(
                    name, label, filter_text, optional=True, createByDefault=by_default
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
        inputs = self._inputs(parameters, context)
        gravity = self._gravity(parameters, context) if self.GRAVITY else None
        techniques = {_TECHNIQUE_OF_INPUT[name] for name in inputs} | ({"gravimetry"} if gravity else set())
        if len(techniques) < self.MINIMUM_TECHNIQUES:
            raise QgsProcessingException(
                self.tr(
                    "This combination needs at least %1 techniques and was given %2. Use the "
                    "two-technique combination that matches your inputs."
                )
                .replace("%1", str(self.MINIMUM_TECHNIQUES))
                .replace("%2", str(len(techniques)))
            )
        geocentric = self.GEOCENTRIC if self.GEOCENTRIC is not None else GNSS in inputs
        networks = list(inputs.values())
        epoch = self._epoch(parameters, context, inputs, geocentric)
        fixed = station_list(self.parameterAsString(parameters, FIXED_STATIONS, context)) or []
        networks, unplaced = _held(networks, fixed, geocentric)
        if unplaced:
            raise QgsProcessingException(
                self.tr(
                    "These fixed stations have no position any input could hold them at: %1. In a "
                    "combination with GNSS, a station is held at its GNSS position."
                ).replace("%1", ", ".join(unplaced))
            )
        frame = FRAME_NAMES[self.parameterAsEnum(parameters, FRAME, context)] if geocentric else None
        confidence = self.parameterAsDouble(parameters, CONFIDENCE, context)
        requested = ENGINES[self.parameterAsEnum(parameters, ENGINE, context)]
        datum = datum_of(self.parameterAsEnum(parameters, DATUM, context))
        feedback.setProgress(10)

        try:
            combination = combine(
                networks,
                frame=frame,
                epoch=epoch,
                velocities=self._velocities(parameters, context) if geocentric else None,
                grids=_grids(networks) if geocentric else None,
            )
            feedback.pushInfo(
                self.tr("Combined %1 inputs (%2) in %3; %4 transformation(s) applied.")
                .replace("%1", str(len(combination.inputs)))
                .replace("%2", ", ".join(combination.techniques))
                .replace("%3", combination.frame or self.tr("the inputs' own system"))
                .replace("%4", str(len(combination.transformations)))
            )
            geoid = self._geoid(parameters, context) if geocentric else None
            network = combination.network
            if gravity is not None:
                network = _with(network, gravity.network)
            routing = route(network, requested)
            feedback.pushInfo(
                self.tr("Engine: %1 (%2).").replace("%1", routing.engine).replace("%2", routing.reason)
            )
            feedback.setProgress(30)
            if routing.engine == "dynadjust":
                from geocomp.engines.dynadjust.combination import adjust_with_dynadjust

                with tempfile.TemporaryDirectory(prefix="geocomp-combined-") as work_dir:
                    result = adjust_with_dynadjust(combination, work_dir, confidence=confidence)
            else:
                result = adjust_combination(
                    combination,
                    geoid=geoid,
                    requested_engine=requested,
                    gravity=gravity,
                    estimate_components=self.parameterAsBool(parameters, VARIANCE_COMPONENTS, context),
                    datum=datum,
                    confidence=confidence,
                )
        except GeoCompError as exc:
            from geocomp.services.messages import message_for

            raise QgsProcessingException(message_for(exc)) from exc
        if feedback.isCanceled():
            return {}
        feedback.setProgress(80)

        solution = self._stamped(result.solution, fixed, datum)
        self._summarise(result, feedback)
        outputs = self._write(parameters, context, combination, solution, result, frame, epoch, requested)
        layers = write_result_layers(
            self,
            parameters,
            context,
            solution,
            combination.network,
            feedback=feedback,
            solution_path=self.parameterAsFileOutput(parameters, OUTPUT_SOLUTION, context),
        )
        feedback.setProgress(100)

        statistics = solution.statistics
        test = statistics.global_test
        return {
            VARIANCE_FACTOR_APOSTERIORI: statistics.variance_factor_aposteriori,
            DEGREES_OF_FREEDOM: statistics.degrees_of_freedom,
            GLOBAL_TEST_PASSED: bool(test.passed) if test is not None else False,
            OUTLIER_COUNT: sum(
                1 for r in solution.observation_results if r.w_test is not None and not r.w_test.passed
            ),
            ENGINE_USED: result.routing.engine,
            **outputs,
            **layers,
        }

    # -- inputs ----------------------------------------------------------

    def _inputs(self, parameters, context) -> dict[str, Network]:
        inputs: dict[str, Network] = {}
        for name, _required in self.INPUTS:
            path = self.parameterAsFile(parameters, name, context)
            if path:
                inputs[name] = load_network(path, parameter=name)
        return inputs

    def _epoch(self, parameters, context, inputs: dict[str, Network], geocentric: bool) -> Epoch:
        text = self.parameterAsString(parameters, EPOCH, context).strip()
        if text:
            try:
                return Epoch.from_decimal_year(float(text))
            except (ValueError, GeoCompError):
                raise QgsProcessingException(
                    self.tr("'%1' is not an epoch. Write it as a decimal year, for example 2024.5.").replace(
                        "%1", text
                    )
                ) from None
        # The GNSS input's, in a geocentric combination: its baselines are the
        # positions in a frame, and their epoch is the one that matters.
        ordered = ([inputs[GNSS]] if geocentric and GNSS in inputs else []) + list(inputs.values())
        for network in ordered:
            if network.epoch is not None:
                return network.epoch
        raise QgsProcessingException(
            self.tr(
                "State the epoch of the combination (a decimal year). None of the inputs states "
                "one, and GeoComp does not assume one."
            )
        )

    def _velocities(self, parameters, context) -> dict[str, Velocity]:
        path = self.parameterAsFile(parameters, VELOCITIES, context)
        if not path:
            return {}
        velocities: dict[str, Velocity] = {}
        with open(path, encoding="utf-8", newline="") as handle:
            for number, row in enumerate(csv.reader(handle), start=1):
                cells = [cell.strip() for cell in row]
                if not cells or not cells[0] or cells[0].lower() == "station" or cells[0].startswith("#"):
                    continue
                try:
                    values = [float(cell) for cell in cells[1:]]
                except ValueError:
                    raise QgsProcessingException(
                        self.tr("Line %1 of the velocities file does not hold numbers.").replace(
                            "%1", str(number)
                        )
                    ) from None
                if len(values) not in (3, 6):
                    raise QgsProcessingException(
                        self.tr(
                            "Line %1 of the velocities file has %2 numbers. Write station, vx, vy, "
                            "vz in metres a year, and optionally their three standard deviations."
                        )
                        .replace("%1", str(number))
                        .replace("%2", str(len(values)))
                    )
                covariance = None if len(values) == 3 else _diagonal([v**2 for v in values[3:]])
                velocities[cells[0]] = Velocity(tuple(values[:3]), covariance)
        return velocities

    def _geoid(self, parameters, context):
        path = self.parameterAsFile(parameters, GEOID, context)
        if not path:
            return None
        from geocomp.io.geoid import read_geoid

        # The file's name is the model's id: it is what the report prints and
        # what the provenance keeps, and a path could carry a user's name.
        return read_geoid(
            path, sigma=self.parameterAsDouble(parameters, GEOID_SIGMA, context), id=Path(path).stem
        )

    def _gravity(self, parameters, context):
        path = self.parameterAsFile(parameters, READINGS, context)
        if not path:
            return None
        from geocomp.algorithms.gravimetry.common import read_readings_document
        from geocomp.algorithms.gravimetry.network_adjust import GravimetryNetworkAlgorithm
        from geocomp.core.techniques.gravimetry import build_gravity_network

        reduced, library, _document = read_readings_document(path, parameter=READINGS)
        absolutes, held = GravimetryNetworkAlgorithm()._known(
            self.parameterAsString(parameters, KNOWN_GRAVITY, context)
        )
        try:
            return build_gravity_network(
                reduced,
                library,
                absolutes=absolutes,
                held=held,
                confidence=self.parameterAsDouble(parameters, CONFIDENCE, context),
            )
        except GeoCompError as exc:
            from geocomp.services.messages import message_for

            raise QgsProcessingException(message_for(exc)) from exc

    # -- outputs ---------------------------------------------------------

    def _stamped(self, solution, fixed, datum):
        from dataclasses import replace

        provenance = solution.provenance
        if provenance is None:
            return solution
        return replace(
            solution,
            provenance=replace(
                provenance,
                algorithm_id=self.spec().id,
                qgis_version=Qgis.QGIS_VERSION,
                parameters={**provenance.parameters, "fixed": list(fixed), "datum": datum.value},
            ),
        )

    def _summarise(self, result, feedback) -> None:
        for summary in result.breakdown:
            feedback.pushInfo(
                self.tr("%1: %2 observation(s), %3 of the redundancy, vᵀPv/r %4.")
                .replace("%1", summary.technique)
                .replace("%2", str(summary.observations))
                .replace("%3", localised(f"{100.0 * summary.redundancy_share:.1f}%"))
                .replace(
                    "%4",
                    "—"
                    if summary.variance_factor is None
                    else localised(f"{summary.variance_factor:.3f}"),
                )
            )
        if result.gravity is not None:
            feedback.pushInfo(
                self.tr(
                    "Gravity was adjusted beside the geometry, by the in-house core; its solution "
                    "is written separately."
                )
            )

    def _write(self, parameters, context, combination, solution, result, frame, epoch, requested):
        solution_path = self.parameterAsFileOutput(parameters, OUTPUT_SOLUTION, context)
        _dump(solution_path, solution.to_dict())
        network_path = self.parameterAsFileOutput(parameters, OUTPUT_NETWORK, context)
        _dump(network_path, combination.network.to_dict())
        outputs = {OUTPUT_SOLUTION: solution_path, OUTPUT_NETWORK: network_path}
        if self.GRAVITY:
            gravity_path = self.parameterAsFileOutput(parameters, OUTPUT_GRAVITY, context)
            if result.gravity is not None:
                _dump(gravity_path, result.gravity.solution.to_dict())
            outputs[OUTPUT_GRAVITY] = gravity_path if result.gravity is not None else ""

        html_path = self.parameterAsFileOutput(parameters, OUTPUT_HTML, context)
        if html_path:
            from geocomp.reports import ReportContext, render_adjustment_report

            scope = self.tr("this run")
            html, omitted = render_adjustment_report(
                solution,
                ReportContext(
                    network=combination.network,
                    qgis_version=Qgis.QGIS_VERSION,
                    display=display_format(),
                    parameter_scopes={
                        "integration.frame": (frame or combination.frame or "—", scope),
                        "integration.epoch": (f"{epoch.decimal_year:.4f}", scope),
                        "integration.engine_requested": (requested, scope),
                        "integration.confidence": (
                            str(self.parameterAsDouble(parameters, CONFIDENCE, context)),
                            scope,
                        ),
                    },
                ),
            )
            Path(html_path).write_text(html, encoding="utf-8")
            del omitted
        outputs[OUTPUT_HTML] = html_path
        return outputs


# -- helpers ---------------------------------------------------------------


def _held(networks: list[Network], names: list[str], geocentric: bool) -> tuple[list[Network], list[str]]:
    """Each named station held where the first input that places it says.

    Geocentric: a cartesian or geodetic start. Local: a projected one. An input
    that already holds the station keeps its own hold. Returns the networks and
    the names no input could place.
    """
    from dataclasses import replace

    usable = (
        (CoordinateSystem.CARTESIAN, CoordinateSystem.GEODETIC)
        if geocentric
        else (CoordinateSystem.PROJECTED,)
    )
    remaining = list(names)
    out = [replace(n, stations=dict(n.stations)) for n in networks]
    for name in names:
        for network in out:
            station = network.stations.get(name)
            if station is None:
                continue
            if station.constraint.mode is not ConstraintMode.FREE:
                remaining.remove(name)
                break
            position = station.approx_position
            if position is None or position.system not in usable:
                continue
            exact = replace(
                position,
                values=tuple(Quantity.exact(q.value, q.unit) for q in position.values),
                epoch=position.epoch or network.epoch,
            )
            network.stations[name] = replace(
                station,
                constraint=ConstraintSpec(
                    mode=ConstraintMode.FIXED,
                    components=frozenset(exact.system.component_names),
                    position=exact,
                ),
            )
            remaining.remove(name)
            break
    return out, remaining


def _grids(networks: list[Network]) -> dict[str, GridFrame]:
    """Each projected CRS among the inputs, as the combination reads it."""
    grids: dict[str, GridFrame] = {}
    for network in networks:
        crs = (network.crs or "").strip()
        if not crs or crs.upper() == "LOCAL" or crs in grids:
            continue
        try:
            canonical_frame(crs)
            continue
        except ValidationError:
            pass
        reference = QgsCoordinateReferenceSystem(crs)
        if not reference.isValid() or reference.isGeographic():
            continue
        projection = projection_of(reference.toProj())
        if projection is None:
            continue
        try:
            frame = canonical_frame(reference.geographicCrsAuthId())
        except ValidationError:
            continue
        grids[crs] = GridFrame(frame=frame, projection=projection)
    return grids


def projection_of(proj: str) -> ProjectionParameters | None:
    """A UTM or Transverse Mercator PROJ definition on GRS80, as parameters.

    ``None`` for anything else: the combination then refuses the input by name,
    which is better than placing it with a projection it is not in.
    """
    tokens: dict[str, str] = {}
    for token in proj.split():
        key, _, value = token.lstrip("+").partition("=")
        tokens[key] = value
    # Stated, not defaulted: "+datum=WGS84" names no ellipsoid and is not GRS80.
    if tokens.get("ellps") != "GRS80":
        return None
    ellipsoid = ELLIPSOIDS["GRS80"]
    try:
        if tokens.get("proj") == "utm":
            return utm_parameters(
                int(tokens["zone"]), southern_hemisphere="south" in tokens, ellipsoid=ellipsoid
            )
        if tokens.get("proj") == "tmerc":
            return ProjectionParameters(
                ellipsoid=ellipsoid,
                central_meridian=math.radians(float(tokens.get("lon_0", 0.0))),
                latitude_of_origin=math.radians(float(tokens.get("lat_0", 0.0))),
                scale_factor=float(tokens.get("k", tokens.get("k_0", 1.0))),
                false_easting=float(tokens.get("x_0", 0.0)),
                false_northing=float(tokens.get("y_0", 0.0)),
                name=proj,
            )
    except (KeyError, ValueError, GeoCompError):
        return None
    return None


def _with(network: Network, other: Network) -> Network:
    from dataclasses import replace

    return replace(network, observations={**network.observations, **other.observations})


def _diagonal(values):
    import numpy as np

    return np.diag(values)


def _dump(path: str, payload: dict[str, Any]) -> None:
    if path:
        Path(path).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
