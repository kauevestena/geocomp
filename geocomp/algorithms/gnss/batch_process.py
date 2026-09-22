# SPDX-License-Identifier: GPL-2.0-or-later
"""Process a whole campaign, reporting failures rather than stopping (FR-355).

``specs/11-module-gnss.md`` section 2. The requirement's exact words are
"batch processing with progress monitoring and per-session error reporting
**that does not abort the batch**", and the acceptance criterion is that *a
batch with one broken session completes and reports it*.

The logic lives in :func:`geocomp.core.techniques.gnss.batch.run_batch`, which
is QGIS-free and tested without one; this is the Processing surface over it.
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
    QgsProcessingParameterEnum,
    QgsProcessingParameterFile,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterString,
)

from geocomp.algorithms.base import GeoCompAlgorithm
from geocomp.algorithms.gnss.common import configured_profile, translate_error
from geocomp.core.errors import GeoCompError
from geocomp.core.techniques.gnss.batch import run_batch
from geocomp.engines.rtklib import RtklibEngine, RtklibJob
from geocomp.engines.rtklib.baseline import quality_from_solution
from geocomp.io.gnss_discovery import overlapping_groups, scan_folder

FOLDER = "FOLDER"
BASE_STATION = "BASE_STATION"
PROFILE = "PROFILE"
OUTPUT_DIR = "OUTPUT_DIR"
OUTPUT_JSON = "OUTPUT_JSON"

_PROFILES = ("relative-static", "relative-kinematic", "absolute-static", "absolute-kinematic")


class BatchProcessAlgorithm(GeoCompAlgorithm):
    """Process every session in a folder against one base."""

    TR_CONTEXT = "BatchProcessAlgorithm"

    def displayName(self) -> str:
        return self.tr("Batch processing")

    def shortDescription(self) -> str:
        return self.tr("Process every session in a folder; one failure does not stop the rest.")

    def help_body(self) -> str:
        return self.tr(
            "<p>Processes every rover session in a folder against one base "
            "station, with the same configuration.</p>"
            "<p><b>A session that fails does not stop the batch.</b> Each is "
            "attempted, each failure is reported with the reason, and the summary "
            "lists what succeeded, what failed and what ran but produced no "
            "usable solution. A campaign of fifty sessions with one truncated "
            "file finishes and tells you which one it was.</p>"
            "<p>Cancelling stops the batch promptly: the remaining sessions are "
            "not attempted, and what has already run is kept.</p>"
        )

    def initAlgorithm(self, config: dict[str, Any] | None = None) -> None:
        self.addParameter(
            QgsProcessingParameterFile(
                FOLDER,
                self.tr("Folder of RINEX observations"),
                behavior=QgsProcessingParameterFile.Behavior.Folder,
            )
        )
        self.addParameter(
            QgsProcessingParameterString(BASE_STATION, self.tr("Base station"), optional=True)
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                PROFILE,
                self.tr("Processing mode"),
                options=[
                    self.tr("Relative — Static"),
                    self.tr("Relative — Kinematic"),
                    self.tr("Absolute — Static"),
                    self.tr("Absolute — Kinematic"),
                ],
                defaultValue=0,
            )
        )
        self.addParameter(
            QgsProcessingParameterFileDestination(
                OUTPUT_JSON,
                self.tr("Batch report"),
                self.tr("JSON files (*.json)"),
                optional=True,
                createByDefault=True,
            )
        )

    def processAlgorithm(
        self,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> dict[str, Any]:
        folder = Path(self.parameterAsFile(parameters, FOLDER, context))
        base_name = (self.parameterAsString(parameters, BASE_STATION, context) or "").strip()
        profile_name = _PROFILES[self.parameterAsEnum(parameters, PROFILE, context)]
        is_absolute = profile_name.startswith("absolute")

        if is_absolute:
            feedback.pushWarning(self.tr(
                "Absolute (PPP) processing in RTKLIB is limited and typically "
                "decimetre-level. Prefer Relative processing where a base "
                "station is available."
            ))

        try:
            scan = scan_folder(folder)
        except GeoCompError as exc:
            raise QgsProcessingException(translate_error(exc)) from exc
        for path, reason in scan.skipped:
            feedback.pushWarning(
                self.tr("Could not read %1: %2").replace("%1", str(path)).replace("%2", reason)
            )
        if not scan.sessions:
            raise QgsProcessingException(
                self.tr("No RINEX observation sessions were found in %1").replace(
                    "%1", str(folder)
                )
            )

        by_station = {s.station_id: s for s in scan.sessions}
        base = None
        if not is_absolute:
            overlapping = {
                s.station_id
                for group in overlapping_groups(scan.sessions)
                if len(group) >= 2
                for s in group
            }
            if base_name:
                if base_name not in by_station:
                    raise QgsProcessingException(
                        self.tr("No session for base station %1").replace("%1", base_name)
                    )
                base = by_station[base_name]
            elif len(overlapping) == 2:
                base = by_station[sorted(overlapping)[0]]
            else:
                raise QgsProcessingException(
                    self.tr("Name the base station explicitly; the folder holds: %1").replace(
                        "%1", ", ".join(sorted(by_station))
                    )
                )
            feedback.pushInfo(self.tr("Base: %1").replace("%1", base.station_id))

        configuration = configured_profile(profile_name)
        rovers = [s for s in scan.sessions if base is None or s.station_id != base.station_id]
        work_root = Path(tempfile.mkdtemp(prefix="geocomp-batch-"))

        def process(station_id: str):
            session = by_station[station_id]
            kwargs = {"base": base} if base is not None else {}
            result = RtklibEngine().run(
                RtklibJob(rover=session, config=configuration, **kwargs),
                work_dir=work_root / station_id,
            )
            return {
                "station": station_id,
                "quality": quality_from_solution(result.solution, session_id=station_id).to_dict(),
                "solution": str(result.output_file),
            }

        def report(fraction: float | None, code: str | None = None) -> None:
            if fraction is not None:
                feedback.setProgress(int(fraction * 100))

        outcome = run_batch(
            [s.station_id for s in rovers],
            process,
            token=_Feedback(feedback),
            progress=report,
            # An engine that exits cleanly having fixed nothing has not produced
            # a solution worth the name -- specs/08's lesson, applied per row.
            accept=lambda row: row["quality"]["epochs"] > 0,
        )

        for row in outcome.results:
            if row.ok:
                feedback.pushInfo(
                    self.tr("%1: %2 epochs")
                    .replace("%1", row.key)
                    .replace("%2", str(row.value["quality"]["epochs"] if row.value else 0))
                )
            else:
                feedback.pushWarning(
                    self.tr("%1 failed: %2").replace("%1", row.key).replace("%2", row.detail)
                )
        counts = outcome.summary()
        feedback.pushInfo(
            self.tr("%1 succeeded, %2 failed, %3 rejected")
            .replace("%1", str(counts["succeeded"]))
            .replace("%2", str(counts["failed"]))
            .replace("%3", str(counts["rejected"]))
        )

        outputs: dict[str, Any] = {}
        destination = self.parameterAsFileOutput(parameters, OUTPUT_JSON, context)
        if destination:
            Path(destination).write_text(
                json.dumps(
                    {
                        "profile": profile_name,
                        **({"base": base.station_id} if base else {}),
                        **outcome.to_dict(),
                        "sessions": [r.value for r in outcome.succeeded if r.value],
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            outputs[OUTPUT_JSON] = destination
        return outputs


class _Feedback:
    """Adapts a Processing feedback to the core's cancellation protocol.

    The core knows nothing about QGIS (NFR-002), so cancellation crosses the
    boundary as a protocol with one method rather than as a QGIS type.
    """

    __slots__ = ("_feedback",)

    def __init__(self, feedback: QgsProcessingFeedback) -> None:
        self._feedback = feedback

    def is_cancelled(self) -> bool:
        return bool(self._feedback.isCanceled())
