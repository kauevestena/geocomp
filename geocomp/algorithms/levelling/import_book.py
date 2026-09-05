# SPDX-License-Identifier: GPL-2.0-or-later
"""``geocomp:levelling_import`` -- read a levelling field book (FR-160).

``specs/10-module-levelling.md`` section 6.

Two layouts and three-wire readings, with the layout worked out from the mapped
columns rather than asked for. Every bad record is reported and none aborts the
import (FR-166): a book with six bad rows needs one run.
"""

from __future__ import annotations

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
from geocomp.algorithms.levelling.common import (
    findings_table,
    level_from_parameters,
    load_json,
    setup_to_dict,
    staff_defaults,
    summarise_findings,
    write_document,
)
from geocomp.algorithms.reporting import escape, render_document, render_note, render_table
from geocomp.core.errors import GeoCompError
from geocomp.io.levelbook import LevelMapping, read_level_book_csv

__all__ = ["ImportLevelBookAlgorithm"]

BOOK = "BOOK"
MAPPING = "MAPPING"
PROFILES = "PROFILES"
LEVEL_ID = "LEVEL_ID"
SIGMA_READING = "SIGMA_READING"
STADIA_FACTOR = "STADIA_FACTOR"
OUTPUT_SETUPS = "OUTPUT_SETUPS"
OUTPUT_HTML = "OUTPUT_HTML"
SETUP_COUNT = "SETUP_COUNT"
LINE_COUNT = "LINE_COUNT"
REJECTED_ROWS = "REJECTED_ROWS"


class ImportLevelBookAlgorithm(GeoCompAlgorithm):
    """Read a levelling field book into setups and lines."""

    TR_CONTEXT = "ImportLevelBookAlgorithm"

    def displayName(self) -> str:
        return self.tr("Import levelling field book")

    def shortDescription(self) -> str:
        return self.tr("Read a CSV levelling book into setups and lines, with findings.")

    def help_body(self) -> str:
        return self.tr(
            "<p>Reads a levelling field book and assembles it into instrument setups and "
            "lines, attaching an uncertainty to every reading.</p>"
            "<p><b>Two layouts are recognised</b>, and which one a file is in is worked out "
            "from the columns the mapping names rather than asked for. One row per setup, "
            "backsight and foresight side by side, is what a spreadsheet naturally produces. "
            "One row per reading, each carrying a setup identifier, is what an instrument "
            "exports &mdash; and the only layout that can express a setup with several "
            "foresights at all.</p>"
            "<p><b>Three-wire readings</b> may replace a single reading in either layout. "
            "They buy the sight distance for free by stadia, which is what makes the "
            "sight-balance check possible on a book that never recorded a distance, and a "
            "half-sum check that catches a misread wire.</p>"
            "<p>Numbers are read locale-independently: a comma decimal separator is handled "
            "here, at the boundary, and never again.</p>"
            "<h3>Parameters</h3>"
            "<p><b>Field book</b> &mdash; the CSV. <b>Field mapping</b> &mdash; a saved "
            "mapping document describing the layout.</p>"
            "<p><b>Instrument profiles</b> and <b>level id</b> &mdash; where the reading "
            "precision comes from. With neither, a generic level is assumed and the report "
            "says so.</p>"
            "<p><b>Default staff-reading uncertainty</b> (m) &mdash; the last resort before "
            "refusing. Zero means not configured; GeoComp does not invent a sigma, because "
            "a fabricated weight corrupts every statistic computed from it.</p>"
            "<p><b>Stadia factor</b> &mdash; used only when three wires are read and no "
            "level profile is available.</p>"
            "<h3>Outputs</h3>"
            "<p><b>Setups</b> &mdash; JSON, the input to the reduction algorithms. "
            "<b>Report</b> &mdash; HTML. Scalars: <code>SETUP_COUNT</code>, "
            "<code>LINE_COUNT</code> and <code>REJECTED_ROWS</code>.</p>"
        )

    def initAlgorithm(self, config: dict[str, Any] | None = None) -> None:
        self.addParameter(
            QgsProcessingParameterFile(BOOK, self.tr("Field book"), extension="csv")
        )
        self.addParameter(
            QgsProcessingParameterFile(
                MAPPING, self.tr("Field mapping"), extension="json"
            )
        )
        self.addParameter(
            QgsProcessingParameterFile(
                PROFILES, self.tr("Instrument profiles"), extension="json", optional=True
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterString(
                LEVEL_ID, self.tr("Level id"), defaultValue="", optional=True
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterNumber(
                SIGMA_READING,
                self.tr("Default staff-reading uncertainty (m)"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=0.0,
                minValue=0.0,
                maxValue=1.0,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterNumber(
                STADIA_FACTOR,
                self.tr("Stadia factor"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=100.0,
                minValue=1.0,
                maxValue=1000.0,
            )
        )
        for name, label, filter_text, by_default in (
            (OUTPUT_SETUPS, self.tr("Setups"), self.tr("GeoComp setups (*.json)"), True),
            (OUTPUT_HTML, self.tr("Report"), self.tr("HTML files (*.html)"), True),
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
        book = self.parameterAsFile(parameters, BOOK, context)
        mapping = self._mapping(
            self.parameterAsFile(parameters, MAPPING, context),
            self.parameterAsDouble(parameters, STADIA_FACTOR, context),
        )
        level = level_from_parameters(
            profiles=self.parameterAsFile(parameters, PROFILES, context),
            level_id=self.parameterAsString(parameters, LEVEL_ID, context),
            collimation=0.0,
            collimation_sigma=0.0,
        )
        defaults = staff_defaults(
            self.parameterAsDouble(parameters, SIGMA_READING, context)
        )

        feedback.setProgress(20)
        try:
            result = read_level_book_csv(book, mapping, level=level, defaults=defaults)
        except GeoCompError as exc:
            from geocomp.services.messages import message_for

            raise QgsProcessingException(message_for(exc)) from exc

        feedback.setProgress(60)
        blocking, warnings = summarise_findings(result.findings, feedback)
        if not result.setups:
            raise QgsProcessingException(
                self.tr(
                    "No usable setup was read. Every row was rejected; the report lists "
                    "why, row by row."
                )
            )

        feedback.pushInfo(
            self.tr("%1 setup(s) in %2 line(s).")
            .replace("%1", str(len(result.setups)))
            .replace("%2", str(len(result.lines)))
        )

        write_document(
            self.parameterAsFileOutput(parameters, OUTPUT_SETUPS, context),
            {
                "kind": "levelling_setups",
                "level_id": level.id,
                "lines": [
                    {
                        "id": line.id,
                        "setups": [setup_to_dict(setup) for setup in line.setups],
                    }
                    for line in result.lines
                ],
            },
        )
        self._write_report(parameters, context, result, level, mapping)
        feedback.setProgress(100)

        return {
            SETUP_COUNT: len(result.setups),
            LINE_COUNT: len(result.lines),
            REJECTED_ROWS: len(result.rejected_rows),
            OUTPUT_SETUPS: self.parameterAsFileOutput(parameters, OUTPUT_SETUPS, context),
            OUTPUT_HTML: self.parameterAsFileOutput(parameters, OUTPUT_HTML, context),
            "BLOCKING": blocking,
            "WARNINGS": warnings,
        }

    def _mapping(self, path: str, stadia_factor: float) -> LevelMapping:
        try:
            payload = load_json(path, parameter=MAPPING)
            payload.setdefault("stadia_factor", stadia_factor)
            return LevelMapping.from_dict(payload)
        except (GeoCompError, KeyError, TypeError, ValueError) as exc:
            raise QgsProcessingException(
                self.tr("'%1' could not be read as a levelling field mapping: %2")
                .replace("%1", path)
                .replace("%2", str(exc))
            ) from exc

    def _write_report(self, parameters, context, result, level, mapping) -> None:
        path = self.parameterAsFileOutput(parameters, OUTPUT_HTML, context)
        if not path:
            return

        summary = render_table(
            [escape(self.tr("Quantity")), escape(self.tr("Value"))],
            [
                [escape(self.tr("Layout")), escape(mapping.layout.value)],
                [escape(self.tr("Rows read")), str(result.row_count)],
                [escape(self.tr("Setups assembled")), str(len(result.setups))],
                [escape(self.tr("Lines assembled")), str(len(result.lines))],
                [escape(self.tr("Rows rejected")), str(len(result.rejected_rows))],
                [escape(self.tr("Level profile")), escape(level.label)],
            ],
        )
        lines = render_table(
            [
                escape(self.tr("Line")),
                escape(self.tr("From")),
                escape(self.tr("To")),
                escape(self.tr("Setups")),
                escape(self.tr("Distances recorded")),
            ],
            [
                [
                    escape(line.id),
                    escape(line.from_station),
                    escape(line.to_station),
                    str(line.setup_count),
                    escape(self.tr("yes") if line.has_distances else self.tr("no")),
                ]
                for line in result.lines
            ],
        )

        body = [
            f"<h2>{escape(self.tr('Summary'))}</h2>",
            summary,
            f"<h2>{escape(self.tr('Lines'))}</h2>",
            lines,
            f"<h2>{escape(self.tr('Findings'))}</h2>",
            findings_table(result.findings),
        ]
        if result.unrecognised_columns:
            body.append(
                render_note(
                    self.tr(
                        "These source columns were not mapped and were ignored: %1"
                    ).replace("%1", ", ".join(result.unrecognised_columns)),
                    label=self.tr("Unmapped columns"),
                )
            )
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(
                render_document(self.tr("Levelling field book import"), body)
            )

