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
"""

from __future__ import annotations

import json
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
    QgsProcessingParameterString,
)

from geocomp.algorithms.analysis.common import load_network
from geocomp.algorithms.base import GeoCompAlgorithm
from geocomp.core.errors import GeoCompError
from geocomp.core.models import Epoch
from geocomp.engines.base import EngineAbsentError
from geocomp.engines.dynadjust.engine import DynAdjustEngine, DynAdjustJob

__all__ = ["DynAdjustAdjustAlgorithm"]

NETWORK = "NETWORK"
FRAME = "FRAME"
EPOCH = "EPOCH"
GEOID_GRID = "GEOID_GRID"
CONFIDENCE = "CONFIDENCE"
ITERATION_THRESHOLD = "ITERATION_THRESHOLD"
MAX_ITERATIONS = "MAX_ITERATIONS"
SEGMENTATION_THRESHOLD = "SEGMENTATION_THRESHOLD"
ENGINE_DIRECTORY = "ENGINE_DIRECTORY"
TIMEOUT = "TIMEOUT"
KEEP_WORKING_FILES = "KEEP_WORKING_FILES"
OUTPUT_SOLUTION = "OUTPUT_SOLUTION"
OUTPUT_WORK_DIR = "OUTPUT_WORK_DIR"
ENGINE_VERSION = "ENGINE_VERSION"
VARIANCE_FACTOR_APOSTERIORI = "VARIANCE_FACTOR_APOSTERIORI"
DEGREES_OF_FREEDOM = "DEGREES_OF_FREEDOM"
ITERATIONS = "ITERATIONS"
CONVERGED = "CONVERGED"
GLOBAL_TEST_PASSED = "GLOBAL_TEST_PASSED"
ADJUSTMENT_MODE = "ADJUSTMENT_MODE"


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
            "<p><b>Network</b> &mdash; a GeoComp network document (JSON).</p>"
            "<p><b>Reference frame</b> and <b>Reference epoch</b> &mdash; the frame and "
            "epoch to adjust in. Leave them empty to use the network's own. Neither is ever "
            "guessed: a frame GeoComp inferred rather than knew is a datum shift absorbed "
            "into the residuals.</p>"
            "<p><b>Geoid grid</b> &mdash; an NTv2 file, required when the network has "
            "orthometric heights, because the height systems cannot be related without one.</p>"
            "<p><b>Confidence level</b> &mdash; for the chi-square test and the positional "
            "uncertainties. <b>Convergence threshold</b> and <b>Maximum iterations</b> "
            "&mdash; passed to DynAdjust unchanged.</p>"
            "<p><b>Segmentation threshold</b> &mdash; above this many stations the network "
            "is segmented and adjusted in phases, which is rigorous: the block solutions "
            "and their variances equal the simultaneous ones.</p>"
            "<p><b>DynAdjust directory</b> &mdash; where the programs are, when they are not "
            "on the system path. <b>Timeout</b> &mdash; seconds before a stage is abandoned "
            "and its process group killed.</p>"
            "<p><b>Keep the working files</b> &mdash; writes the generated input and the raw "
            "DynAdjust output to a folder instead of a temporary directory. An adjustment "
            "that surprises you is answerable only from the files that produced it.</p>"
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
            QgsProcessingParameterFile(NETWORK, self.tr("Network document"), extension="json")
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
                defaultValue=0.0,
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
        self.addAdvancedParameter(
            QgsProcessingParameterNumber(
                CONFIDENCE,
                self.tr("Confidence level"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=0.95,
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
                self.tr("DynAdjust directory (empty = search the system path)"),
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
        directory = self.parameterAsFile(parameters, ENGINE_DIRECTORY, context)
        engine = DynAdjustEngine(configured_directory=directory or None)

        version = engine.detect()
        if version is None:
            raise QgsProcessingException(
                self.tr(
                    "DynAdjust was not found. Install it and put its programs on the "
                    "system path, or give the directory holding them in the "
                    "'DynAdjust directory' parameter. GeoComp does not bundle it: it is "
                    "a separate program under its own licence."
                )
            )
        if not version.tested:
            feedback.pushWarning(
                self.tr(
                    "DynAdjust %1 has not been checked against this GeoComp release. "
                    "It will be used, but if its output format has changed the result "
                    "may be refused when it is read back."
                ).replace("%1", version.version)
            )
        feedback.pushInfo(
            self.tr("Using DynAdjust %1 from %2.")
            .replace("%1", version.version)
            .replace("%2", str(version.path))
        )

        epoch_year = self.parameterAsDouble(parameters, EPOCH, context)
        job = DynAdjustJob(
            network=network,
            name=network.id or "geocomp",
            target_frame=self.parameterAsString(parameters, FRAME, context).strip(),
            target_epoch=Epoch.from_decimal_year(epoch_year) if epoch_year else None,
            geoid_grid=self.parameterAsFile(parameters, GEOID_GRID, context) or None,
            confidence=self.parameterAsDouble(parameters, CONFIDENCE, context),
            iteration_threshold=self.parameterAsDouble(parameters, ITERATION_THRESHOLD, context),
            maximum_iterations=self.parameterAsInt(parameters, MAX_ITERATIONS, context),
            segmentation_threshold=self.parameterAsInt(
                parameters, SEGMENTATION_THRESHOLD, context
            ),
        )

        keep = self.parameterAsBoolean(parameters, KEEP_WORKING_FILES, context)
        requested = self.parameterAsString(parameters, OUTPUT_WORK_DIR, context)
        with tempfile.TemporaryDirectory(prefix="geocomp-dynadjust-") as temporary:
            work_dir = Path(requested) if (keep and requested) else Path(temporary)
            solution = self._run(job, engine, work_dir, parameters, context, feedback)
            if feedback.isCanceled():
                return {}
            results = self._write(solution, parameters, context)

        statistics = solution.statistics
        return {
            **results,
            OUTPUT_WORK_DIR: str(work_dir) if keep else "",
            ENGINE_VERSION: version.version,
            VARIANCE_FACTOR_APOSTERIORI: statistics.variance_factor_aposteriori,
            DEGREES_OF_FREEDOM: statistics.degrees_of_freedom,
            ITERATIONS: statistics.iterations,
            CONVERGED: statistics.converged,
            GLOBAL_TEST_PASSED: (
                statistics.global_test.passed if statistics.global_test else None
            ),
            ADJUSTMENT_MODE: solution.provenance.parameters["mode"]
            if solution.provenance
            else "",
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
        """Drive the pipeline, turning every engine failure into a user message.

        The three failure kinds are kept apart because the remedies differ: an
        absent program is an installation problem, a refused input is a data
        problem the engine itself describes, and everything else is a GeoComp
        problem.
        """
        try:
            prepared = engine.prepare(job, work_dir)
        except GeoCompError as error:
            raise QgsProcessingException(str(error)) from error

        if prepared.skipped:
            feedback.pushWarning(
                self.tr(
                    "%1 observation(s) have no DynAdjust equivalent and were not "
                    "written: %2"
                )
                .replace("%1", str(len(prepared.skipped)))
                .replace("%2", ", ".join(sorted(prepared.skipped)[:10]))
            )

        running = [stage.program for stage in prepared.included]
        feedback.pushInfo(self.tr("Pipeline: %1").replace("%1", " -> ".join(running)))
        for stage in prepared.stages:
            if not stage.included:
                feedback.pushInfo(
                    self.tr("Skipping %1: %2")
                    .replace("%1", stage.program)
                    .replace("%2", stage.reason)
                )

        timeout = self.parameterAsDouble(parameters, TIMEOUT, context)
        try:
            runs = engine.run(prepared, timeout=timeout, on_progress=feedback.pushConsoleInfo)
        except EngineAbsentError as error:
            raise QgsProcessingException(
                self.tr(
                    "A DynAdjust program the pipeline needs is missing: %1. DynAdjust is "
                    "a suite, and a partial installation fails part way through."
                ).replace("%1", str(error.context.get("program", "")))
            ) from error
        except GeoCompError as error:
            raise QgsProcessingException(str(error)) from error

        feedback.setProgress(80)
        try:
            return engine.parse(runs, prepared)
        except GeoCompError as error:
            raise QgsProcessingException(str(error)) from error

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
