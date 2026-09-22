# SPDX-License-Identifier: GPL-2.0-or-later
"""Compare one dataset processed several ways (FR-359).

``specs/11-module-gnss.md`` section 6. Runs the same session pair under several
elevation masks and presents the solutions side by side with the significance of
each difference, given the covariances.

**The elevation-mask sweep is the parameter worth sweeping first**, and this is
not a guess: it is what attributed RD-06's discrepancy (``specs/22`` §5). Below
25 degrees two independent days of the same 76 m baseline disagreed by 11 mm in
east; at 25 and above they agreed to 0.14 mm. A comparison that only printed the
coordinates would have shown twelve numbers and no finding.

``specs/15`` section 3 lists this operation as one that eventually wants a
custom dialog, to show the comparison interactively. **The algorithm ships
first, and alone**: ADR-0005 says the dialog collects parameters and hands them
to the same algorithm, so the algorithm is what makes the capability real,
scriptable and testable. The dialog is recorded as still to come rather than
implied by this.
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
    QgsProcessingParameterFile,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
)

from geocomp.algorithms.base import GeoCompAlgorithm
from geocomp.algorithms.gnss.common import configured_profile, translate_error
from geocomp.core.errors import GeoCompError
from geocomp.core.techniques.gnss.comparison import DEFAULT_CONFIDENCE, compare_baselines
from geocomp.engines.rtklib import RtklibEngine, RtklibJob
from geocomp.engines.rtklib.baseline import baseline_from_solution
from geocomp.io.gnss_discovery import overlapping_groups, scan_folder

FOLDER = "FOLDER"
MASKS = "MASKS"
CONFIDENCE = "CONFIDENCE"
OUTPUT_CSV = "OUTPUT_CSV"
OUTPUT_JSON = "OUTPUT_JSON"

#: The sweep that attributed RD-06. Straddles the point where the answer stops
#: depending on which satellites were used.
DEFAULT_MASKS = "10,15,20,25,30,35"


class CompareConfigurationsAlgorithm(GeoCompAlgorithm):
    """Process one baseline several ways and compare the results."""

    TR_CONTEXT = "CompareConfigurationsAlgorithm"

    def displayName(self) -> str:
        return self.tr("Compare configurations")

    def shortDescription(self) -> str:
        return self.tr("Process the same data several ways and compare, with significance.")

    def help_body(self) -> str:
        return self.tr(
            "<p>Processes one pair of simultaneously observing sessions at several "
            "elevation masks, and compares the baselines they determine.</p>"
            "<p><b>The comparison is by significance, not by size.</b> A 3 mm "
            "difference is large when both solutions are good to 0.5 mm and "
            "nothing at all when they are good to 5 mm, so each difference is "
            "tested against the combined covariance of the two solutions.</p>"
            "<p>The two runs share their observations, so treating them as "
            "independent overstates the difference's uncertainty and "
            "under-reports significance. That is the conservative direction for "
            "a test whose job is to stop a parameter being called important when "
            "it is not, and the assumption is recorded on the result.</p>"
            "<p>A difference reported as <i>not significant</i> is the "
            "informative answer: it says the parameter changed nothing this data "
            "can resolve.</p>"
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
            QgsProcessingParameterString(
                MASKS, self.tr("Elevation masks to compare (degrees)"), defaultValue=DEFAULT_MASKS
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterNumber(
                CONFIDENCE,
                self.tr("Confidence for the significance test"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=DEFAULT_CONFIDENCE,
                minValue=0.5,
                maxValue=0.999,
            )
        )
        for name, label, filter_text in (
            (OUTPUT_CSV, self.tr("Comparison table"), self.tr("CSV files (*.csv)")),
            (OUTPUT_JSON, self.tr("Comparison"), self.tr("JSON files (*.json)")),
        ):
            self.addParameter(
                QgsProcessingParameterFileDestination(
                    name, label, filter_text, optional=True, createByDefault=True
                )
            )

    def processAlgorithm(
        self,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> dict[str, Any]:
        folder = Path(self.parameterAsFile(parameters, FOLDER, context))
        confidence = self.parameterAsDouble(parameters, CONFIDENCE, context)
        raw = self.parameterAsString(parameters, MASKS, context) or DEFAULT_MASKS
        try:
            masks = [float(piece) for piece in raw.replace(";", ",").split(",") if piece.strip()]
        except ValueError as exc:
            raise QgsProcessingException(
                self.tr("Could not read the elevation masks from %1").replace("%1", raw)
            ) from exc
        if len(masks) < 2:
            raise QgsProcessingException(
                self.tr("Give at least two elevation masks to compare.")
            )

        try:
            scan = scan_folder(folder)
        except GeoCompError as exc:
            raise QgsProcessingException(translate_error(exc)) from exc
        pair = next((g for g in overlapping_groups(scan.sessions) if len(g) == 2), None)
        if pair is None:
            raise QgsProcessingException(
                self.tr(
                    "Comparison needs exactly one pair of simultaneously observing "
                    "sessions in the folder."
                )
            )
        base, rover = sorted(pair, key=lambda s: s.station_id)
        feedback.pushInfo(
            self.tr("Base %1 → rover %2")
            .replace("%1", base.station_id)
            .replace("%2", rover.station_id)
        )

        work_root = Path(tempfile.mkdtemp(prefix="geocomp-compare-"))
        baselines = {}
        for index, mask in enumerate(masks):
            if feedback.isCanceled():
                return {}
            feedback.setProgress(10 + 70 * index // len(masks))
            name = self.tr("mask %1°").replace("%1", f"{mask:g}")
            try:
                result = RtklibEngine().run(
                    RtklibJob(
                        rover=rover,
                        base=base,
                        config=configured_profile(
                            "relative-static", output_format="xyz", elevation_mask=mask
                        ),
                    ),
                    work_dir=work_root / f"mask-{mask:g}",
                )
                baselines[name] = baseline_from_solution(
                    result.solution,
                    base_station=base.station_id,
                    rover_station=rover.station_id,
                )
            except GeoCompError as exc:
                feedback.pushWarning(
                    self.tr("%1 failed: %2")
                    .replace("%1", name)
                    .replace("%2", translate_error(exc))
                )

        if len(baselines) < 2:
            raise QgsProcessingException(
                self.tr("Fewer than two configurations produced a baseline to compare.")
            )

        try:
            comparison = compare_baselines(baselines, confidence=confidence)
        except GeoCompError as exc:
            raise QgsProcessingException(translate_error(exc)) from exc

        for row in comparison.table():
            feedback.pushInfo("  ".join(f"{cell:>12}" for cell in row))
        if not comparison.any_significant:
            feedback.pushInfo(
                self.tr(
                    "No difference is significant at this confidence: over this data, "
                    "the elevation mask changed nothing that can be resolved."
                )
            )

        outputs: dict[str, Any] = {}
        csv_path = self.parameterAsFileOutput(parameters, OUTPUT_CSV, context)
        if csv_path:
            Path(csv_path).write_text(
                "\n".join(",".join(row) for row in comparison.table()) + "\n", encoding="utf-8"
            )
            outputs[OUTPUT_CSV] = csv_path
        json_path = self.parameterAsFileOutput(parameters, OUTPUT_JSON, context)
        if json_path:
            Path(json_path).write_text(
                json.dumps(comparison.to_dict(), indent=2) + "\n", encoding="utf-8"
            )
            outputs[OUTPUT_JSON] = json_path
        feedback.setProgress(100)
        return outputs
