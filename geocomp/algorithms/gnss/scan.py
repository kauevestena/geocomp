# SPDX-License-Identifier: GPL-2.0-or-later
"""Scan a folder into GNSS sessions (FR-351, FR-166).

``specs/11-module-gnss.md`` section 2, first arrow. The operation that makes
every other GNSS algorithm possible, and the one that decides what a "session"
is: the file headers, not the file names.

**Every file it could not read is reported** (FR-166). A scan that quietly
skipped a truncated observation file would report a campaign as smaller than it
is, and the missing session would be discovered — if at all — when somebody
wondered why a baseline was absent.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qgis.core import (
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingParameterFile,
    QgsProcessingParameterFileDestination,
)

from geocomp.algorithms.base import GeoCompAlgorithm
from geocomp.algorithms.gnss.common import translate_error
from geocomp.core.errors import GeoCompError
from geocomp.io.gnss_discovery import overlapping_groups, scan_folder

FOLDER = "FOLDER"
OUTPUT_JSON = "OUTPUT_JSON"


class ScanSessionsAlgorithm(GeoCompAlgorithm):
    """Discover the observation sessions in a folder of RINEX."""

    TR_CONTEXT = "ScanSessionsAlgorithm"

    def displayName(self) -> str:
        return self.tr("Scan sessions")

    def shortDescription(self) -> str:
        return self.tr("Discover GNSS sessions in a folder, from the RINEX headers.")

    def help_body(self) -> str:
        return self.tr(
            "<p>Reads the header of every RINEX observation file in a folder and "
            "reports the sessions it found: station, receiver, antenna, start and "
            "end, sampling interval, and the navigation files paired with each.</p>"
            "<p><b>The header decides, not the file name.</b> A file named for one "
            "station whose header names another is reported as a mismatch rather "
            "than silently resolved either way.</p>"
            "<p>Groups sessions by simultaneity, since only sessions that actually "
            "overlap in time can form a baseline, and lists every file it could "
            "not read rather than stopping at the first.</p>"
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
            QgsProcessingParameterFileDestination(
                OUTPUT_JSON,
                self.tr("Sessions"),
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
        try:
            scan = scan_folder(folder)
        except GeoCompError as exc:
            raise QgsProcessingException(translate_error(exc)) from exc

        feedback.setProgress(60)
        for path, reason in scan.skipped:
            feedback.pushWarning(
                self.tr("Could not read %1: %2").replace("%1", str(path)).replace("%2", reason)
            )
        for path, reason in scan.warnings:
            feedback.pushWarning(
                self.tr("%1: %2").replace("%1", str(path)).replace("%2", reason)
            )

        groups = overlapping_groups(scan.sessions)
        feedback.pushInfo(
            self.tr("%1 session(s), %2 simultaneous group(s), %3 unreadable file(s)")
            .replace("%1", str(len(scan.sessions)))
            .replace("%2", str(len(groups)))
            .replace("%3", str(len(scan.skipped)))
        )
        for session in scan.sessions:
            feedback.pushInfo(
                self.tr("  %1: %2 to %3")
                .replace("%1", session.station_id)
                .replace("%2", session.start.isoformat() if session.start else "?")
                .replace("%3", session.end.isoformat() if session.end else "?")
            )

        outputs: dict[str, Any] = {}
        destination = self.parameterAsFileOutput(parameters, OUTPUT_JSON, context)
        if destination:
            Path(destination).write_text(
                json.dumps(
                    {
                        **scan.to_dict(),
                        "simultaneous_groups": [
                            [s.station_id for s in group] for group in groups
                        ],
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            outputs[OUTPUT_JSON] = destination
        feedback.setProgress(100)
        return outputs
