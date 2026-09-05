# SPDX-License-Identifier: GPL-2.0-or-later
"""``geocomp:project_export`` -- a solution as CSV or a spreadsheet (FR-162).

``specs/17-persistence-and-interoperability.md`` section 5.1.

An adjustment produces numbers people then work with elsewhere: a report to a
client, a comparison against the previous epoch, a column of heights pasted into
a setting-out sheet. Making them retype those numbers out of an HTML report is
how transcription errors enter a survey, which is a category of error the whole
project exists to eliminate.

**Five tables, and only the ones with content.** Stations, observations,
adjusted values, residuals and statistics. An empty ``residuals.csv`` beside a
network that was never adjusted invites the reader to conclude the residuals
were zero, so it is not written.

**`.xlsx` needs `openpyxl`, and GeoComp does not** (``specs/03`` section 3.7):
the workbook is written directly as its OPC zip, so the format works in a bare
QGIS install. What the format does *not* do is carry uncertainty better than CSV
does -- both write the same columns -- so the choice is about who reads it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qgis.core import (
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFile,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterFolderDestination,
)

from geocomp.algorithms.base import GeoCompAlgorithm
from geocomp.algorithms.project.common import read_network, read_solution
from geocomp.core.errors import GeoCompError
from geocomp.io.tabular import SHEETS, write_csv, write_workbook

__all__ = ["ProjectExportAlgorithm"]

SOLUTION = "SOLUTION"
NETWORK = "NETWORK"
FORMAT = "FORMAT"
OUTPUT_FOLDER = "OUTPUT_FOLDER"
OUTPUT_WORKBOOK = "OUTPUT_WORKBOOK"

#: Result keys. Declared as constants like the parameters, because a
#: caller in the model builder reads a result by name exactly as it sets a
#: parameter by name, and tests/structural/test_tier3_parameter_names.py
#: checks both sides against these declarations.
FILES = "FILES"
TABLES = "TABLES"

FORMAT_CSV = 0
FORMAT_XLSX = 1


class ProjectExportAlgorithm(GeoCompAlgorithm):
    """Writes a solution's tables as CSV files or one spreadsheet."""

    TR_CONTEXT = "ProjectExportAlgorithm"

    def displayName(self) -> str:
        return self.tr("Export solution tables")

    def shortDescription(self) -> str:
        return self.tr("Write stations, observations, adjusted values, residuals and statistics.")

    def help_body(self) -> str:
        return self.tr(
            "<p>Writes the five tables of an adjustment: stations, observations, adjusted "
            "values, residuals and statistics. Only tables with content are written &mdash; "
            "an empty residuals table beside an unadjusted network would invite the reader "
            "to conclude the residuals were zero.</p>"
            "<p>Every uncertainty is exported beside its value, and every value is written "
            "to full precision, so a figure read back into another tool is the figure "
            "GeoComp computed rather than a rounded version of it.</p>"
            "<h3>Parameters</h3>"
            "<p><b>Solution</b> &mdash; a solution document written by an adjustment "
            "algorithm.</p>"
            "<p><b>Network</b> &mdash; optional. Supplying it adds the station and "
            "observation tables, which describe what was adjusted rather than what came "
            "out; without it only the adjusted values, residuals and statistics are "
            "written.</p>"
            "<p><b>Format</b> &mdash; one CSV per table, or a single spreadsheet holding "
            "all of them.</p>"
        )

    def initAlgorithm(self, config: dict[str, Any] | None = None) -> None:
        self.addParameter(
            QgsProcessingParameterFile(
                SOLUTION,
                self.tr("Solution document"),
                extension="json",
            )
        )
        self.addParameter(
            QgsProcessingParameterFile(
                NETWORK,
                self.tr("Network document (optional)"),
                extension="json",
                optional=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                FORMAT,
                self.tr("Format"),
                options=[self.tr("One CSV per table"), self.tr("One spreadsheet (.xlsx)")],
                defaultValue=FORMAT_CSV,
            )
        )
        self.addParameter(
            QgsProcessingParameterFolderDestination(
                OUTPUT_FOLDER,
                self.tr("Folder for the CSV files"),
                optional=True,
                createByDefault=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterFileDestination(
                OUTPUT_WORKBOOK,
                self.tr("Spreadsheet"),
                self.tr("Excel workbooks (*.xlsx)"),
                optional=True,
                createByDefault=False,
            )
        )

    def processAlgorithm(
        self,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> dict[str, Any]:
        try:
            solution = read_solution(self.parameterAsFile(parameters, SOLUTION, context))
            network = read_network(self.parameterAsFile(parameters, NETWORK, context))
        except GeoCompError as error:
            raise QgsProcessingException(str(error)) from error

        chosen = self.parameterAsEnum(parameters, FORMAT, context)
        feedback.setProgress(20)

        if chosen == FORMAT_XLSX:
            target = self.parameterAsFileOutput(parameters, OUTPUT_WORKBOOK, context)
            if not target:
                raise QgsProcessingException(
                    self.tr("Choose a destination spreadsheet, or export as CSV instead.")
                )
            written = self._workbook(target, network, solution, feedback)
            return {OUTPUT_WORKBOOK: str(written), TABLES: _named(solution, network)}

        folder = self.parameterAsString(parameters, OUTPUT_FOLDER, context)
        if not folder:
            raise QgsProcessingException(
                self.tr("Choose a destination folder for the CSV files.")
            )
        paths = self._csv(folder, network, solution, feedback)
        return {OUTPUT_FOLDER: folder, FILES: [str(path) for path in paths]}

    # -- the two formats --------------------------------------------------

    def _csv(self, folder: str, network, solution, feedback) -> list[Path]:
        Path(folder).mkdir(parents=True, exist_ok=True)
        try:
            paths = write_csv(folder, network=network, solution=solution)
        except GeoCompError as error:
            raise QgsProcessingException(str(error)) from error
        for path in paths:
            feedback.pushInfo(path.name)
        if not paths:
            feedback.pushWarning(
                self.tr(
                    "Nothing was written: the solution and network carry no rows for any "
                    "table. An empty file would say the tables were empty, which is a "
                    "different claim."
                )
            )
        feedback.setProgress(100)
        return paths

    def _workbook(self, target: str, network, solution, feedback) -> Path:
        try:
            path = write_workbook(target, network=network, solution=solution)
        except GeoCompError as error:
            raise QgsProcessingException(str(error)) from error
        feedback.pushInfo(path.name)
        feedback.setProgress(100)
        return path


def _named(solution, network) -> list[str]:
    """The sheets that had content, for the algorithm's result dictionary."""
    from geocomp.io.tabular import sheet_rows

    present = []
    for sheet in SHEETS:
        _headers, rows = sheet_rows(sheet.name, network, solution)
        if rows:
            present.append(sheet.name)
    return present
