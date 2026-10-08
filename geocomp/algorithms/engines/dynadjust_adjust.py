# SPDX-License-Identifier: GPL-2.0-or-later
"""``geocomp:analysis_dynadjust_adjust`` -- adjust a network with DynAdjust.

FR-320…FR-325. ``specs/07-engine-dynadjust.md``.

The Processing face of the DynAdjust pipeline. It writes the input files, drives
``dnaimport`` through ``dnaadjust``, and parses the output into the **same**
:class:`~geocomp.core.models.Solution` the in-house core produces -- so the
report, the layers, the store and the multi-epoch comparison downstream never
learn which engine ran (FR-323).

**When DynAdjust is absent this fails with a message that says how to get it**,
not with an import error. An engine is an optional dependency by ADR-0003, and
the algorithm still appears in the toolbox so a user can read what it needs.

**The working directory is kept when asked** (FR-325). An adjustment that
surprises its author is answerable only from the files that produced it, and
"re-run it and hope" is not an answer.

**Advanced mode can stop before running, and add options of its own**
(FR-325, FR-070; P12c-21). *Stop after writing the input* writes the input
files and a manifest and returns their folder, to be inspected or edited and
run by *Run a prepared DynAdjust job*. A *DynAdjust configuration* file adds
options to each program after GeoComp's own.
"""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

from qgis.core import (
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterFile,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterFolderDestination,
    QgsProcessingParameterNumber,
    QgsProcessingParameterProviderConnection,
    QgsProcessingParameterString,
)
from qgis.PyQt.QtCore import QCoreApplication

from geocomp.algorithms.analysis.common import load_network
from geocomp.algorithms.base import GeoCompAlgorithm
from geocomp.algorithms.defaults import configured
from geocomp.algorithms.layer_outputs import add_result_layer_parameters, write_result_layers
from geocomp.algorithms.projection import projection_of_crs
from geocomp.core.errors import GeoCompError
from geocomp.core.geodesy.projection import ProjectionParameters
from geocomp.core.models import CoordinateSystem, Epoch, HeightType, Network, Solution
from geocomp.core.number_format import localised
from geocomp.engines.base import EngineAbsentError, EngineVersion
from geocomp.engines.dynadjust.dynaml import written_position
from geocomp.engines.dynadjust.engine import (
    DynAdjustEngine,
    DynAdjustJob,
    PreparedJob,
    read_configuration,
)
from geocomp.services.engines import dynadjust_engine
from geocomp.services.messages import message_for

__all__ = ["DynAdjustAdjustAlgorithm"]

NETWORK = "NETWORK"
STORE = "STORE"
DATABASE = "DATABASE"
SCHEMA = "SCHEMA"
STORED_NETWORK = "STORED_NETWORK"
FRAME = "FRAME"
EPOCH = "EPOCH"
GEOID_GRID = "GEOID_GRID"
GEOID_UNDULATION = "GEOID_UNDULATION"
CONFIDENCE = "CONFIDENCE"
ITERATION_THRESHOLD = "ITERATION_THRESHOLD"
MAX_ITERATIONS = "MAX_ITERATIONS"
SEGMENTATION_THRESHOLD = "SEGMENTATION_THRESHOLD"
ENGINE_DIRECTORY = "ENGINE_DIRECTORY"
TIMEOUT = "TIMEOUT"
KEEP_WORKING_FILES = "KEEP_WORKING_FILES"
CONFIGURATION = "CONFIGURATION"
STOP_BEFORE_RUNNING = "STOP_BEFORE_RUNNING"
OUTPUT_SOLUTION = "OUTPUT_SOLUTION"
OUTPUT_WORK_DIR = "OUTPUT_WORK_DIR"
ENGINE_VERSION = "ENGINE_VERSION"
VARIANCE_FACTOR_APOSTERIORI = "VARIANCE_FACTOR_APOSTERIORI"
DEGREES_OF_FREEDOM = "DEGREES_OF_FREEDOM"
ITERATIONS = "ITERATIONS"
CONVERGED = "CONVERGED"
GLOBAL_TEST_PASSED = "GLOBAL_TEST_PASSED"
ADJUSTMENT_MODE = "ADJUSTMENT_MODE"

#: The context of the helpers both DynAdjust algorithms share. A fixed one,
#: not the calling algorithm's: Qt looks a string up in the context it is
#: translated in, and the second algorithm has none of these.
_CONTEXT = "DynAdjustAdjustAlgorithm"


def _tr(text: str) -> str:
    return QCoreApplication.translate(_CONTEXT, text)


#: Refusals of the configuration file itself, which name it as the input at fault.
_CONFIGURATION_CODES = frozenset(
    {
        "data.dynadjust_configuration_unreadable",
        "validation.dynadjust_configuration_invalid",
        "validation.dynadjust_configuration_unknown_program",
        "validation.dynadjust_option_reserved",
    }
)


class DynAdjustAdjustAlgorithm(GeoCompAlgorithm):
    """Network adjustment by DynAdjust, into GeoComp's own Solution."""

    TR_CONTEXT = "DynAdjustAdjustAlgorithm"

    def displayName(self) -> str:
        return self.tr("Adjust network (DynAdjust)")

    def shortDescription(self) -> str:
        return self.tr(
            "Adjust a network with Geoscience Australia's DynAdjust and read the result back."
        )

    def help_body(self) -> str:
        return self.tr(
            "<p>Adjusts a geodetic network using <b>DynAdjust</b>, Geoscience Australia's "
            "least-squares suite, and reads its output back into the same solution "
            "structure GeoComp's own adjustment produces. Everything downstream &mdash; "
            "reports, map layers, storage, multi-epoch comparison &mdash; works the same "
            "way whichever engine produced the result.</p>"
            "<p><b>DynAdjust must be installed separately.</b> It is not bundled: it is a "
            "large native program under a different licence, and shipping a copy inside a "
            "QGIS plugin would make GeoComp responsible for its build. If it is not found, "
            "this algorithm says so and names what is missing.</p>"
            "<p>DynAdjust is a suite, not one program. This runs, in order, "
            "<code>dnaimport</code>, then <code>dnareftran</code> if the target frame or "
            "epoch differs from the network's, then <code>dnageoid</code> if orthometric "
            "heights take part, then <code>dnasegment</code> for a network too large to "
            "adjust in one piece, then <code>dnaadjust</code>. Which stages ran, and why "
            "each other one did not, is recorded in the solution's provenance.</p>"
            "<h3>Parameters</h3>"
            "<p><b>Network</b> &mdash; a GeoComp network document (JSON). Or, instead, a "
            "<b>project store</b>: a GeoPackage, or a schema of a PostgreSQL connection, "
            "with the id of the <b>network in the store</b> (empty: its only network). The "
            "store is read and never changed.</p>"
            "<p><b>Reference frame</b> and <b>Reference epoch</b> &mdash; the frame and "
            "epoch to adjust in. Leave them empty to use the network's own. Neither is ever "
            "guessed: a frame GeoComp inferred rather than knew is a datum shift absorbed "
            "into the residuals.</p>"
            "<p><b>Geoid grid</b> &mdash; an NTv2 file, required when the network has "
            "orthometric heights, because the height systems cannot be related without one.</p>"
            "<p><b>A network in a projected CRS</b>, as a <i>Classical network</i> is, reaches "
            "DynAdjust as latitude and longitude: the projection is read from the network's "
            "CRS, which must be UTM or Transverse Mercator on GRS80. Its orthometric heights "
            "need the <b>geoid undulation N</b> (m) instead of a grid: GeoComp converts each, "
            "<i>h = H + N</i>, with that one N, and <code>dnageoid</code> does not run. One N "
            "suits a network the geoid barely slopes across. Give the grid or the undulation, "
            "not both.</p>"
            "<p><b>Confidence level</b> &mdash; for the chi-square test and the positional "
            "uncertainties. <b>Convergence threshold</b> and <b>Maximum iterations</b> "
            "&mdash; passed to DynAdjust unchanged.</p>"
            "<p><b>Segmentation threshold</b> &mdash; above this many stations the network "
            "is segmented and adjusted in phases, which is rigorous: the block solutions "
            "and their variances equal the simultaneous ones.</p>"
            "<p><b>DynAdjust directory</b> &mdash; where the programs are, for this run. "
            "Empty, GeoComp uses the directory set in Global Settings under Paths and "
            "engines, then its own installation (Project &rsaquo; Install an engine), then "
            "the system path. <b>Timeout</b> &mdash; seconds before a stage is abandoned "
            "and its process group killed.</p>"
            "<p><b>Keep the working files</b> &mdash; writes the generated input and the raw "
            "DynAdjust output to a folder instead of a temporary directory. An adjustment "
            "that surprises you is answerable only from the files that produced it.</p>"
            "<p><b>DynAdjust configuration</b> &mdash; a JSON file of options of your own for "
            "each program, added after GeoComp's: "
            "<code>{\"dnaadjust\": [\"--free-stn-sd\", \"10\"]}</code>. The options GeoComp "
            "sets itself, such as the confidence or the output files, are refused: each has a "
            "parameter here, and GeoComp reads the output back by them. The options are "
            "recorded in the solution's provenance.</p>"
            "<p><b>Stop after writing the input</b> &mdash; writes the input files and the "
            "plan to the working-files folder and stops, without running DynAdjust, which "
            "need not even be installed. Inspect or edit the files there, then run them with "
            "<b>Run a prepared DynAdjust job</b>. Which files were edited is recorded in the "
            "result.</p>"
            "<h3>Outputs</h3>"
            "<p><b>Solution</b> &mdash; JSON: adjusted coordinates, the full variance matrix, "
            "per-observation residuals, the statistics, and the provenance recording every "
            "command line that ran.</p>"
            "<p>Scalar outputs: <code>ENGINE_VERSION</code>, "
            "<code>VARIANCE_FACTOR_APOSTERIORI</code>, <code>DEGREES_OF_FREEDOM</code>, "
            "<code>ITERATIONS</code>, <code>CONVERGED</code>, "
            "<code>GLOBAL_TEST_PASSED</code> and <code>ADJUSTMENT_MODE</code>.</p>"
        )

    # -- parameters ------------------------------------------------------

    def initAlgorithm(self, config: dict[str, Any] | None = None) -> None:
        self.addParameter(
            QgsProcessingParameterFile(
                NETWORK, self.tr("Network document"), extension="json", optional=True
            )
        )
        # FR-320 (P12c-24): or straight from a project store, as Save to project
        # store writes one -- no network document in between.
        self.addParameter(
            QgsProcessingParameterFile(
                STORE,
                self.tr("Or a project store (GeoPackage)"),
                fileFilter=self.tr("GeoPackage (*.gpkg)"),
                optional=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterProviderConnection(
                DATABASE,
                self.tr("Or a PostgreSQL connection holding the project store"),
                "postgres",
                optional=True,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterString(
                SCHEMA, self.tr("Schema of the project store"), defaultValue="geocomp", optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                STORED_NETWORK,
                self.tr("Network in the store (empty: its only network)"),
                defaultValue="",
                optional=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                FRAME,
                self.tr("Reference frame (empty = the network's own)"),
                defaultValue="",
                optional=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                EPOCH,
                self.tr("Reference epoch, decimal year (0 = the network's own)"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=configured("reference_systems.default_epoch"),
                optional=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterFile(
                GEOID_GRID,
                self.tr("Geoid grid (NTv2), for orthometric heights"),
                optional=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                GEOID_UNDULATION,
                self.tr("Geoid undulation N (m), for the orthometric heights of a projected network"),
                type=QgsProcessingParameterNumber.Double,
                optional=True,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterNumber(
                CONFIDENCE,
                self.tr("Confidence level"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=configured("stochastic.confidence_level"),
                minValue=0.5,
                maxValue=0.9999,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterNumber(
                ITERATION_THRESHOLD,
                self.tr("Convergence threshold (m)"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=0.0005,
                minValue=1e-9,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterNumber(
                MAX_ITERATIONS,
                self.tr("Maximum iterations"),
                defaultValue=10,
                minValue=1,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterNumber(
                SEGMENTATION_THRESHOLD,
                self.tr("Segment above this many stations"),
                defaultValue=500,
                minValue=1,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterFile(
                ENGINE_DIRECTORY,
                self.tr(
                    "DynAdjust directory (empty: Global Settings, then GeoComp's "
                    "installation, then the system path)"
                ),
                behavior=QgsProcessingParameterFile.Folder,
                optional=True,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterNumber(
                TIMEOUT,
                self.tr("Timeout per stage (s)"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=1800.0,
                minValue=1.0,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterBoolean(
                KEEP_WORKING_FILES,
                self.tr("Keep the generated input and raw output"),
                defaultValue=False,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterFile(
                CONFIGURATION,
                self.tr("DynAdjust configuration (JSON: options per program)"),
                extension="json",
                optional=True,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterBoolean(
                STOP_BEFORE_RUNNING,
                self.tr("Stop after writing the input, to inspect or edit it"),
                defaultValue=False,
            )
        )
        self.addParameter(
            QgsProcessingParameterFileDestination(
                OUTPUT_SOLUTION,
                self.tr("Solution"),
                fileFilter="JSON (*.json)",
                optional=True,
                createByDefault=True,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterFolderDestination(
                OUTPUT_WORK_DIR,
                self.tr("Working files"),
                optional=True,
                createByDefault=False,
            )
        )
        # FR-324: the same result layers the in-house adjustment offers, from
        # the same Solution. Until P12c-13 a DynAdjust adjustment wrote its
        # solution document and no layer.
        add_result_layer_parameters(self)

    # -- execution -------------------------------------------------------

    def processAlgorithm(
        self,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> dict[str, Any]:
        network = self._network(parameters, context)
        directory = self.parameterAsFile(parameters, ENGINE_DIRECTORY, context)
        engine = dynadjust_engine(directory)
        stop = self.parameterAsBoolean(parameters, STOP_BEFORE_RUNNING, context)
        # A run that will use DynAdjust looks for it first, as it always has: a
        # machine without it is told so before anything about the network. One
        # that stops after writing the input runs nothing and needs none.
        version = None if stop else detect(engine, feedback)

        epoch_year = self.parameterAsDouble(parameters, EPOCH, context)
        configuration = self.parameterAsFile(parameters, CONFIGURATION, context)
        geoid_grid = self.parameterAsFile(parameters, GEOID_GRID, context) or None
        undulations = self._undulations(network, parameters, context, geoid_grid, feedback)
        try:
            job = DynAdjustJob(
                network=network,
                name=network.id or "geocomp",
                target_frame=self.parameterAsString(parameters, FRAME, context).strip(),
                target_epoch=Epoch.from_decimal_year(epoch_year) if epoch_year else None,
                geoid_grid=geoid_grid,
                projection=_projection(network),
                geoid_undulations=undulations,
                confidence=self.parameterAsDouble(parameters, CONFIDENCE, context),
                iteration_threshold=self.parameterAsDouble(
                    parameters, ITERATION_THRESHOLD, context
                ),
                maximum_iterations=self.parameterAsInt(parameters, MAX_ITERATIONS, context),
                segmentation_threshold=self.parameterAsInt(
                    parameters, SEGMENTATION_THRESHOLD, context
                ),
                extra_arguments=read_configuration(configuration) if configuration else {},
            )
        except GeoCompError as error:
            message = message_for(error)
            if error.code in _CONFIGURATION_CODES:
                message = self.about_input(CONFIGURATION, message)
            raise QgsProcessingException(message) from error

        if version is None:
            return self._prepare_only(job, engine, parameters, context, feedback)

        keep = self.parameterAsBoolean(parameters, KEEP_WORKING_FILES, context)
        requested = self.parameterAsString(parameters, OUTPUT_WORK_DIR, context)
        work_dir = (
            Path(requested)
            if (keep and requested)
            else Path(tempfile.mkdtemp(prefix="geocomp-dynadjust-"))
        )
        # Removed afterwards unless the user keeps it -- or unless the refusal
        # names it. specs/07 section 7 retains the working directory when a
        # stage times out or fails, so the user can see what DynAdjust was given
        # and what it wrote. Until P12c-11 the refusal propagated out of a
        # TemporaryDirectory block, which deleted the files it pointed at.
        retain = keep
        try:
            solution = self._run(job, engine, work_dir, parameters, context, feedback)
            if feedback.isCanceled():
                return {}
            results = self._write(solution, parameters, context)
            results.update(
                write_result_layers(
                    self,
                    parameters,
                    context,
                    solution,
                    network,
                    feedback=feedback,
                    solution_path=results.get(OUTPUT_SOLUTION) or "",
                )
            )
        except QgsProcessingException as failure:
            retain = retain or _names_working_files(failure)
            raise
        finally:
            if not retain:
                shutil.rmtree(work_dir, ignore_errors=True)

        return {
            **results,
            OUTPUT_WORK_DIR: str(work_dir) if keep else "",
            **figures(solution, version.version),
        }

    def _network(self, parameters: dict[str, Any], context: QgsProcessingContext) -> Network:
        """The network to adjust: from a document, or from a project store (FR-320).

        Exactly one source. The store is opened as it is -- never created, never
        migrated -- because reading an input must not change it.
        """
        document = self.parameterAsFile(parameters, NETWORK, context)
        store = self.parameterAsFile(parameters, STORE, context)
        connection = self.parameterAsConnectionName(parameters, DATABASE, context)
        if sum(bool(value) for value in (document, store, connection)) != 1:
            labels = [
                self.parameterDefinition(name).description() for name in (NETWORK, STORE, DATABASE)
            ]
            raise QgsProcessingException(
                self.tr("Give exactly one network to adjust, from one of: %1.").replace(
                    "%1", "; ".join(labels)
                )
            )
        if document:
            return load_network(document, parameter=NETWORK)

        from geocomp.algorithms.project.common import stored_network

        source = STORE if store else DATABASE
        try:
            if store:
                from geocomp.io.store import open_store

                opened = open_store(store)
                label = store
            else:
                from geocomp.services.postgis import open_database_store, store_label

                schema = (self.parameterAsString(parameters, SCHEMA, context) or "geocomp").strip()
                opened = open_database_store(connection, schema)
                label = store_label(connection, schema)
            try:
                project = opened.read()
            finally:
                opened.close()
            return stored_network(
                project, label, (self.parameterAsString(parameters, STORED_NETWORK, context) or "").strip()
            )
        except GeoCompError as error:
            raise QgsProcessingException(self.about_input(source, message_for(error))) from error

    def _undulations(
        self,
        network: Network,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        geoid_grid: str | None,
        feedback: QgsProcessingFeedback,
    ) -> dict[str, float]:
        """The undulation given, for each station whose orthometric height is on a grid coordinate.

        Empty when none was given. The writer turns those stations' *H* into
        the *h* DynaML's ``LLH`` height means, which is ``dnageoid``'s work
        done by GeoComp -- so a grid as well is refused: one would apply the
        separation and the other leave it out (P12c-45).
        """
        given = parameters.get(GEOID_UNDULATION)
        if given is None or given == "":
            return {}
        if geoid_grid:
            raise QgsProcessingException(
                self.tr(
                    "A geoid grid and a geoid undulation were both given. Give one of them: "
                    "the grid for geodetic coordinates, the undulation for a projected network."
                )
            )
        undulation = self.parameterAsDouble(parameters, GEOID_UNDULATION, context)
        stations = {
            station.id: undulation
            for station in network.stations.values()
            if (position := written_position(station)) is not None
            and position.system is CoordinateSystem.PROJECTED
            and position.height_type is HeightType.ORTHOMETRIC
        }
        if not stations:
            feedback.pushInfo(
                self.tr("The geoid undulation is not used: no station has an orthometric height on "
                        "projected coordinates.")
            )
        else:
            feedback.pushInfo(
                self.tr("The heights of %1 station(s) are made ellipsoidal with N = %2 m.")
                .replace("%1", str(len(stations)))
                .replace("%2", localised(f"{undulation:.3f}"))
            )
        return stations

    def _prepare_only(
        self,
        job: DynAdjustJob,
        engine: DynAdjustEngine,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> dict[str, Any]:
        """Write the input and the plan, and stop (FR-325). No program is run,
        so DynAdjust need not be installed on the machine that prepares."""
        requested = self.parameterAsString(parameters, OUTPUT_WORK_DIR, context)
        work_dir = Path(requested) if requested else Path(tempfile.mkdtemp(prefix="geocomp-dynadjust-"))
        try:
            prepared = engine.prepare(job, work_dir)
        except GeoCompError as error:
            raise QgsProcessingException(message_for(error)) from error
        report_plan(prepared, feedback)
        feedback.pushInfo(
            self.tr(
                "Stopped before running DynAdjust. The input is in %1: %2 and %3. Inspect or "
                "edit them there, then run Run a prepared DynAdjust job on that folder."
            )
            .replace("%1", str(work_dir))
            .replace("%2", prepared.station_file.name)
            .replace("%3", prepared.measurement_file.name)
        )
        return {
            OUTPUT_SOLUTION: None,
            OUTPUT_WORK_DIR: str(work_dir),
            ENGINE_VERSION: "",
            VARIANCE_FACTOR_APOSTERIORI: None,
            DEGREES_OF_FREEDOM: None,
            ITERATIONS: None,
            CONVERGED: None,
            GLOBAL_TEST_PASSED: None,
            ADJUSTMENT_MODE: prepared.mode,
        }

    def _run(
        self,
        job: DynAdjustJob,
        engine: DynAdjustEngine,
        work_dir: Path,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ):
        """Prepare, run and read the job, every engine failure said in words."""
        try:
            prepared = engine.prepare(job, work_dir)
        except GeoCompError as error:
            raise QgsProcessingException(message_for(error)) from error
        report_plan(prepared, feedback)
        return run_and_read(
            engine, prepared, self.parameterAsDouble(parameters, TIMEOUT, context), feedback
        )

    def _write(
        self,
        solution,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
    ) -> dict[str, Any]:
        target = self.parameterAsFileOutput(parameters, OUTPUT_SOLUTION, context)
        if target:
            with open(target, "w", encoding="utf-8") as handle:
                json.dump(solution.to_dict(), handle, indent=2, sort_keys=True)
                handle.write("\n")
        return {OUTPUT_SOLUTION: target}


def _projection(network: Network) -> ProjectionParameters | None:
    """The projection of *network*'s grid coordinates, read from their CRS by QGIS (P12c-45).

    ``None`` for a network with none, one whose projected stations are in more
    than one CRS, or a projection GeoComp cannot invert: the DynaML writer then
    refuses each projected station by name, as it did before any was read.
    """
    systems = {
        position.crs or ""
        for station in network.stations.values()
        if (position := written_position(station)) is not None
        and position.system is CoordinateSystem.PROJECTED
    }
    if len(systems) != 1:
        return None
    return projection_of_crs(systems.pop())


def detect(engine: DynAdjustEngine, feedback: QgsProcessingFeedback) -> EngineVersion:
    """The installed DynAdjust, said in the log, or a refusal that says how to get it."""
    version = engine.detect()
    if version is None:
        raise QgsProcessingException(
            _tr(
                "DynAdjust was not found. Install it with Project > Install an engine, "
                "or give the directory holding its programs in Global Settings under "
                "Paths and engines, or in the 'DynAdjust directory' parameter. GeoComp "
                "does not bundle it: it is a separate program under its own licence."
            )
        )
    if not version.tested:
        feedback.pushWarning(
            _tr(
                "DynAdjust %1 has not been checked against this GeoComp release. "
                "It will be used, but if its output format has changed the result "
                "may be refused when it is read back."
            ).replace("%1", version.version)
        )
    feedback.pushInfo(
        _tr("Using DynAdjust %1 from %2.")
        .replace("%1", version.version)
        .replace("%2", str(version.path))
    )
    return version


def report_plan(prepared: PreparedJob, feedback: QgsProcessingFeedback) -> None:
    """Say what was left out, what will run, and why each other stage will not."""
    if prepared.skipped:
        feedback.pushWarning(
            _tr(
                "%1 observation(s) have no DynAdjust equivalent and were not written: %2"
            )
            .replace("%1", str(len(prepared.skipped)))
            # The ids: each reason is the core's English (P12c-45; it raised
            # TypeError, joining the pairs, until a skip first reached here).
            .replace("%2", ", ".join(sorted(identifier for identifier, _reason in prepared.skipped)[:10]))
        )
    running = [stage.program for stage in prepared.included]
    feedback.pushInfo(_tr("Pipeline: %1").replace("%1", " -> ".join(running)))
    for stage in prepared.stages:
        if not stage.included:
            feedback.pushInfo(skipped_stage(stage))


def skipped_stage(stage) -> str:
    """Why *stage* is left out of the pipeline, in words (P12c-42).

    The stage's ``reason`` says it in English for the provenance; until P12c-42
    that sentence was shown as it stood. A job prepared by an older release has
    no code, and is said without the why.
    """
    context = stage.context
    sentences = {
        "already_in_target": _tr("Skipping %1: the input is already in the target frame and epoch."),
        "input_states_no_frame": _tr(
            "Skipping %1: the input states no frame, so %2 is taken as the frame it is already "
            "in; transforming out of an unrecorded frame would apply a shift computed from a guess."
        ).replace("%2", str(context.get("frame", ""))),
        "undulations_applied": _tr(
            "Skipping %1: the heights were converted with the job's own geoid undulations, so "
            "they reach DynAdjust ellipsoidal already."
        ),
        "all_ellipsoidal": _tr("Skipping %1: every height is ellipsoidal; no geoid is involved."),
        "simultaneous": _tr("Skipping %1: %2 stations adjust simultaneously.").replace(
            "%2", str(context.get("stations", ""))
        ),
    }
    return sentences.get(stage.code, _tr("Skipping %1.")).replace("%1", stage.program)


def run_and_read(
    engine: DynAdjustEngine,
    prepared: PreparedJob,
    timeout: float,
    feedback: QgsProcessingFeedback,
) -> Solution:
    """Run the planned stages and read the result, each failure said in words.

    The three failure kinds are kept apart because the remedies differ: an
    absent program is an installation problem, a refused input is a data
    problem the engine itself describes, and everything else is a GeoComp
    problem.
    """
    try:
        runs = engine.run(prepared, timeout=timeout, on_progress=feedback.pushConsoleInfo)
    except EngineAbsentError as error:
        raise QgsProcessingException(
            _tr(
                "A DynAdjust program the pipeline needs is missing: %1. DynAdjust is a "
                "suite, and a partial installation fails part way through. Install "
                "DynAdjust again with the Install an engine algorithm."
            ).replace("%1", str(error.context.get("program", "")))
        ) from error
    except GeoCompError as error:
        raise QgsProcessingException(message_for(error)) from error

    feedback.setProgress(80)
    try:
        return engine.parse(runs, prepared)
    except GeoCompError as error:
        raise QgsProcessingException(message_for(error)) from error


def figures(solution: Solution, version: str) -> dict[str, Any]:
    """The scalar outputs both DynAdjust algorithms return."""
    statistics = solution.statistics
    return {
        ENGINE_VERSION: version,
        VARIANCE_FACTOR_APOSTERIORI: statistics.variance_factor_aposteriori,
        DEGREES_OF_FREEDOM: statistics.degrees_of_freedom,
        ITERATIONS: statistics.iterations,
        CONVERGED: statistics.converged,
        GLOBAL_TEST_PASSED: statistics.global_test.passed if statistics.global_test else None,
        ADJUSTMENT_MODE: solution.provenance.parameters["mode"] if solution.provenance else "",
    }


def _names_working_files(failure: BaseException) -> bool:
    """Whether the refusal points the user at the working directory."""
    cause = failure.__cause__
    return isinstance(cause, GeoCompError) and "work_dir" in cause.context
