# SPDX-License-Identifier: GPL-2.0-or-later
"""``geocomp:analysis_dynadjust_run_prepared`` -- run a job prepared earlier.

FR-325 and FR-070 (P12c-21). ``specs/07-engine-dynadjust.md`` section 3.

*Adjust network (DynAdjust)* with *Stop after writing the input* writes the
input files, the plan and a manifest to a folder and stops. This runs what is
in that folder now -- the files as GeoComp wrote them, or as the user edited
them -- and reads the result back into the same Solution. Which files were
edited is found from the digests the manifest kept and recorded in the
solution's provenance: a result from hand-edited input is not the network's
result alone, and the record says so.

The folder is the user's and is never removed.
"""

from __future__ import annotations

import json
from typing import Any

from qgis.core import (
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingParameterFile,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterNumber,
)

from geocomp.algorithms.base import GeoCompAlgorithm
from geocomp.algorithms.engines.dynadjust_adjust import (
    ENGINE_DIRECTORY,
    OUTPUT_SOLUTION,
    TIMEOUT,
    detect,
    figures,
    report_plan,
    run_and_read,
)
from geocomp.algorithms.layer_outputs import add_result_layer_parameters, write_result_layers
from geocomp.core.errors import GeoCompError
from geocomp.engines.dynadjust.engine import load_prepared
from geocomp.services.engines import dynadjust_engine
from geocomp.services.messages import message_for

__all__ = ["DynAdjustRunPreparedAlgorithm"]

PREPARED = "PREPARED"
EDITED_INPUTS = "EDITED_INPUTS"

class DynAdjustRunPreparedAlgorithm(GeoCompAlgorithm):
    """Run the DynAdjust input a stopped *Adjust network (DynAdjust)* wrote."""

    TR_CONTEXT = "DynAdjustRunPreparedAlgorithm"

    def displayName(self) -> str:
        return self.tr("Run a prepared DynAdjust job")

    def shortDescription(self) -> str:
        return self.tr(
            "Run the DynAdjust input prepared earlier, as written or as edited, and read the "
            "result back."
        )

    def help_body(self) -> str:
        return self.tr(
            "<p>Runs a DynAdjust job that <b>Adjust network (DynAdjust)</b> prepared with "
            "<b>Stop after writing the input</b>, and reads the result back into the same "
            "solution GeoComp's own adjustment produces.</p>"
            "<p>Between the two you may inspect the input files in the folder, and edit "
            "them: a measurement's variance to scale, a station to constrain, an option "
            "DynAdjust offers that GeoComp does not. They are run as they are now. GeoComp "
            "compares each with what it wrote, and the solution's provenance names the files "
            "that were edited, because a result from edited input is not the network's "
            "alone.</p>"
            "<p>To leave a measurement out, set its <code>Ignore</code> to <code>*</code>: "
            "on the measurement, or on one direction of a direction set. It is set aside in "
            "the solution, as though you had set it aside in GeoComp. Do not add or remove "
            "measurements: the result is matched to the network measurement by measurement, "
            "in the order GeoComp wrote them, and a file with a different set is refused.</p>"
            "<p>Do not rename or remove the files, and do not edit the job file GeoComp "
            "wrote beside them: it is how the result is read back.</p>"
            "<h3>Parameters</h3>"
            "<p><b>Prepared folder</b> &mdash; the working-files folder the stopped run "
            "returned. <b>DynAdjust directory</b> and <b>Timeout</b> &mdash; as for Adjust "
            "network (DynAdjust).</p>"
            "<h3>Outputs</h3>"
            "<p><b>Solution</b> &mdash; JSON, as Adjust network (DynAdjust) writes it. The "
            "scalar outputs are the same, with <code>EDITED_INPUTS</code>: the input files "
            "that were edited, or nothing.</p>"
        )

    def initAlgorithm(self, config: dict[str, Any] | None = None) -> None:
        self.addParameter(
            QgsProcessingParameterFile(
                PREPARED,
                self.tr("Prepared folder"),
                behavior=QgsProcessingParameterFile.Folder,
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
        self.addParameter(
            QgsProcessingParameterFileDestination(
                OUTPUT_SOLUTION,
                self.tr("Solution"),
                fileFilter="JSON (*.json)",
                optional=True,
                createByDefault=True,
            )
        )
        add_result_layer_parameters(self)

    def processAlgorithm(
        self,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> dict[str, Any]:
        folder = self.parameterAsFile(parameters, PREPARED, context)
        try:
            prepared = load_prepared(folder)
        except GeoCompError as error:
            raise QgsProcessingException(self.about_input(PREPARED, message_for(error))) from error
        if prepared.edited:
            feedback.pushWarning(
                self.tr(
                    "These input files were edited after GeoComp wrote them: %1. They are "
                    "run as they are, and the solution records that they were edited."
                ).replace("%1", ", ".join(prepared.edited))
            )
        if prepared.ignored:
            feedback.pushInfo(
                self.tr("Flagged Ignore in the input, and set aside in the solution: %1.").replace(
                    "%1", ", ".join(prepared.ignored)
                )
            )

        engine = dynadjust_engine(self.parameterAsFile(parameters, ENGINE_DIRECTORY, context))
        version = detect(engine, feedback)
        report_plan(prepared, feedback)
        solution = run_and_read(
            engine, prepared, self.parameterAsDouble(parameters, TIMEOUT, context), feedback
        )
        if feedback.isCanceled():
            return {}

        target = self.parameterAsFileOutput(parameters, OUTPUT_SOLUTION, context)
        if target:
            with open(target, "w", encoding="utf-8") as handle:
                json.dump(solution.to_dict(), handle, indent=2, sort_keys=True)
                handle.write("\n")
        results: dict[str, Any] = {OUTPUT_SOLUTION: target}
        results.update(
            write_result_layers(
                self,
                parameters,
                context,
                solution,
                prepared.adjusted_network,
                feedback=feedback,
                solution_path=target or "",
            )
        )
        return {
            **results,
            **figures(solution, version.version),
            EDITED_INPUTS: ", ".join(prepared.edited),
        }
