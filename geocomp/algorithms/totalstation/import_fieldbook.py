# SPDX-License-Identifier: GPL-2.0-or-later
"""``geocomp:totalstation_import_fieldbook`` -- read a field book (FR-160, FR-166).

``specs/17-persistence-and-interoperability.md`` section 5.1 and ``specs/09``
section 5.

The entry point of the total-station workflow. It reads a CSV field book through
a **saved, reusable mapping**, attaches an uncertainty to every reading, and
writes a document the other algorithms in this group take as input.

**Every bad record is reported and none aborts the run** (FR-166). A field book
with six problems needs one run and produces six rows in the findings table,
each naming its source row -- not six runs each stopping at the next problem.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from qgis.core import (
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterFile,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterNumber,
)

from geocomp.algorithms.base import GeoCompAlgorithm
from geocomp.algorithms.reporting import escape, render_document, render_table
from geocomp.algorithms.totalstation.common import (
    findings_table,
    load_mapping,
    load_profiles,
    stochastic_defaults,
    summarise_findings,
)
from geocomp.core.errors import GeoCompError
from geocomp.io import read_field_book

__all__ = ["ImportFieldBookAlgorithm"]

SOURCE = "SOURCE"
MAPPING = "MAPPING"
PROFILES = "PROFILES"
SIGMA_DIRECTION = "SIGMA_DIRECTION"
SIGMA_ZENITH = "SIGMA_ZENITH"
SIGMA_DISTANCE = "SIGMA_DISTANCE"
FAIL_ON_REJECTED = "FAIL_ON_REJECTED"
OUTPUT_READINGS = "OUTPUT_READINGS"
OUTPUT_HTML = "OUTPUT_HTML"
OUTPUT_FINDINGS = "OUTPUT_FINDINGS"
RECORD_COUNT = "RECORD_COUNT"
SETUP_COUNT = "SETUP_COUNT"
REJECTED_COUNT = "REJECTED_COUNT"


class ImportFieldBookAlgorithm(GeoCompAlgorithm):
    """Read a CSV field book into GeoComp, with a saved field mapping."""

    TR_CONTEXT = "ImportFieldBookAlgorithm"

    def displayName(self) -> str:
        return self.tr("Import field book")

    def shortDescription(self) -> str:
        return self.tr("Read a CSV field book through a saved, reusable field mapping.")

    def help_body(self) -> str:
        return self.tr(
            "<p>Reads a total-station field book from a CSV file and writes a GeoComp "
            "readings document the other Total Station algorithms take as input.</p>"
            "<p><b>The field mapping is a saved, reusable object.</b> The same organisation "
            "imports the same instrument export layout every week, and re-mapping columns by "
            "hand each time is exactly the manual handling this plugin exists to remove. "
            "Leave the mapping empty and GeoComp infers one from the header, which is right "
            "for the layouts it recognises; the report then states every column it mapped, "
            "so an inferred mapping is never silently trusted.</p>"
            "<p><b>Every bad record is reported and none stops the import.</b> A field book "
            "with six problems needs one run and produces six findings, each naming its "
            "source row.</p>"
            "<p>An uncertainty is attached to every reading here, at the boundary, from the "
            "instrument profile or from the per-type defaults below. Where neither supplies "
            "one the import refuses: GeoComp does not invent a standard deviation, because a "
            "fabricated weight silently corrupts every statistic computed from it.</p>"
            "<h3>Parameters</h3>"
            "<p><b>Field book</b> &mdash; the CSV file. <b>Field mapping</b> &mdash; a saved "
            "mapping document (JSON); empty infers one.</p>"
            "<p><b>Instrument profiles</b> &mdash; a profile library (JSON). Empty uses a "
            "generic total station of 2 mm + 2 ppm and 5 arcseconds, and everything computed "
            "from it is marked approximate.</p>"
            "<p><b>Default direction, zenith and distance precision</b> &mdash; used where "
            "the instrument profile supplies none. In radians and metres; 0 means not "
            "configured.</p>"
            "<p><b>Fail if any record was rejected</b> &mdash; when set, a rejected record "
            "stops the algorithm, so a model does not carry on with a partial import.</p>"
            "<h3>Outputs</h3>"
            "<p><b>Readings</b> &mdash; the JSON document. <b>Report</b> &mdash; HTML. "
            "<b>Findings</b> &mdash; CSV, one row per problem. Scalars: "
            "<code>RECORD_COUNT</code>, <code>SETUP_COUNT</code> and "
            "<code>REJECTED_COUNT</code>.</p>"
        )

    def initAlgorithm(self, config: dict[str, Any] | None = None) -> None:
        self.addParameter(
            QgsProcessingParameterFile(SOURCE, self.tr("Field book"), extension="csv")
        )
        self.addParameter(
            QgsProcessingParameterFile(
                MAPPING, self.tr("Field mapping"), extension="json", optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterFile(
                PROFILES, self.tr("Instrument profiles"), extension="json", optional=True
            )
        )
        for name, label, default, maximum in (
            (SIGMA_DIRECTION, self.tr("Default direction precision (rad)"), 0.0, 0.1),
            (SIGMA_ZENITH, self.tr("Default zenith angle precision (rad)"), 0.0, 0.1),
            (SIGMA_DISTANCE, self.tr("Default distance precision (m)"), 0.0, 100.0),
        ):
            self.addAdvancedParameter(
                QgsProcessingParameterNumber(
                    name,
                    label,
                    type=QgsProcessingParameterNumber.Type.Double,
                    defaultValue=default,
                    minValue=0.0,
                    maxValue=maximum,
                )
            )
        self.addAdvancedParameter(
            QgsProcessingParameterBoolean(
                FAIL_ON_REJECTED, self.tr("Fail if any record was rejected"), defaultValue=False
            )
        )
        self.addParameter(
            QgsProcessingParameterFileDestination(
                OUTPUT_READINGS,
                self.tr("Readings"),
                self.tr("GeoComp readings (*.json)"),
                optional=True,
                createByDefault=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterFileDestination(
                OUTPUT_HTML,
                self.tr("Report"),
                self.tr("HTML files (*.html)"),
                optional=True,
                createByDefault=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterFileDestination(
                OUTPUT_FINDINGS,
                self.tr("Findings"),
                self.tr("CSV files (*.csv)"),
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
        source = Path(self.parameterAsFile(parameters, SOURCE, context))
        if not source.is_file():
            raise QgsProcessingException(
                self.tr("The field book '%1' does not exist.").replace("%1", str(source))
            )

        with open(source, encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.reader(handle))
        if not rows:
            raise QgsProcessingException(
                self.tr("The field book '%1' is empty.").replace("%1", str(source))
            )

        mapping = load_mapping(self.parameterAsFile(parameters, MAPPING, context), rows[0])
        library = load_profiles(self.parameterAsFile(parameters, PROFILES, context))
        defaults = stochastic_defaults(
            self.parameterAsDouble(parameters, SIGMA_DIRECTION, context),
            self.parameterAsDouble(parameters, SIGMA_ZENITH, context),
            self.parameterAsDouble(parameters, SIGMA_DISTANCE, context),
        )

        feedback.setProgress(20)
        feedback.pushInfo(
            self.tr("Reading '%1' with mapping '%2'…")
            .replace("%1", source.name)
            .replace("%2", mapping.name)
        )
        try:
            result = read_field_book(rows, mapping, library=library, defaults=defaults)
        except GeoCompError as exc:
            from geocomp.services.messages import message_for

            raise QgsProcessingException(message_for(exc)) from exc

        feedback.setProgress(60)
        summarise_findings(result.findings, feedback)
        feedback.pushInfo(
            self.tr("%1 record(s) read into %2 setup(s); %3 rejected.")
            .replace("%1", str(len(result.records)))
            .replace("%2", str(len(result.setups)))
            .replace("%3", str(len(result.rejected_rows)))
        )
        if result.unrecognised_columns:
            feedback.pushWarning(
                self.tr("Columns not mapped, and therefore not imported: %1").replace(
                    "%1", ", ".join(result.unrecognised_columns)
                )
            )

        outputs = self._write(parameters, context, source, mapping, result)
        feedback.setProgress(100)

        if result.rejected_rows and self.parameterAsBool(parameters, FAIL_ON_REJECTED, context):
            raise QgsProcessingException(
                self.tr("%1 record(s) were rejected; see the findings.").replace(
                    "%1", str(len(result.rejected_rows))
                )
            )

        return {
            RECORD_COUNT: len(result.records),
            SETUP_COUNT: len(result.setups),
            REJECTED_COUNT: len(result.rejected_rows),
            **outputs,
        }

    # -- outputs ---------------------------------------------------------

    def _write(self, parameters, context, source, mapping, result) -> dict[str, Any]:
        readings = self.parameterAsFileOutput(parameters, OUTPUT_READINGS, context)
        if readings:
            with open(readings, "w", encoding="utf-8") as handle:
                json.dump(
                    _readings_document(source, mapping, result),
                    handle,
                    indent=2,
                    sort_keys=True,
                )
                handle.write("\n")

        html_target = self.parameterAsFileOutput(parameters, OUTPUT_HTML, context)
        if html_target:
            with open(html_target, "w", encoding="utf-8") as handle:
                handle.write(self._render(source, mapping, result))

        findings_csv = self.parameterAsFileOutput(parameters, OUTPUT_FINDINGS, context)
        if findings_csv:
            with open(findings_csv, "w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(["code", "severity", "message", "row"])
                for finding in result.findings:
                    writer.writerow(
                        [
                            finding.code,
                            finding.severity.value,
                            finding.message,
                            "" if finding.value is None else int(finding.value),
                        ]
                    )

        return {
            OUTPUT_READINGS: readings,
            OUTPUT_HTML: html_target,
            OUTPUT_FINDINGS: findings_csv,
        }

    def _render(self, source, mapping, result) -> str:
        summary = [
            [escape(self.tr("Field book")), escape(source.name)],
            [escape(self.tr("Field mapping")), escape(mapping.name)],
            [escape(self.tr("Angle format")), escape(mapping.angle_format.value)],
            [escape(self.tr("Rows read")), escape(result.row_count)],
            [escape(self.tr("Records")), escape(len(result.records))],
            [escape(self.tr("Setups")), escape(len(result.setups))],
            [escape(self.tr("Rejected records")), escape(len(result.rejected_rows))],
        ]

        body = [
            f"<h2>{escape(self.tr('Import'))}</h2>",
            render_table([escape(self.tr("Property")), escape(self.tr("Value"))], summary),
            f"<h2>{escape(self.tr('Field mapping used'))}</h2>",
            render_table(
                [
                    escape(self.tr("GeoComp field")),
                    escape(self.tr("Source column")),
                    escape(self.tr("Unit")),
                ],
                [
                    [
                        escape(column.field),
                        escape(
                            column.column
                            or self.tr("(constant %1)").replace("%1", str(column.constant))
                        ),
                        escape(column.unit) or "—",
                    ]
                    for column in sorted(mapping.columns, key=lambda c: c.field)
                ],
            ),
        ]

        if result.unrecognised_columns:
            body.append(
                render_table(
                    [escape(self.tr("Column not mapped"))],
                    [[escape(column)] for column in result.unrecognised_columns],
                )
            )

        body.append(f"<h2>{escape(self.tr('Findings'))}</h2>")
        body.append(findings_table(result.findings))

        return render_document(
            self.tr("Field book import report"),
            body,
            footer=escape(
                self.tr("Generated by GeoComp — geocomp:totalstation_import_fieldbook")
            ),
        )


def _readings_document(source, mapping, result) -> dict[str, Any]:
    """The readings document the rest of the group consumes.

    Setups serialised with their face pairs and singles, each reading carrying
    its own uncertainty. Written rather than passed in memory because
    ``specs/16`` section 9 requires the steps to chain in the modeller, and a
    file is the only thing a modeller can pass between two algorithms.
    """
    return {
        "kind": "geocomp.readings",
        "version": 1,
        "source": source.name,
        "mapping": mapping.to_dict(),
        "setups": [
            {
                "station": setup.station,
                "instrument_height": setup.instrument_height.to_dict(),
                "instrument_id": setup.instrument_id,
                "reflector_id": setup.reflector_id,
                "pairs": [
                    {
                        "direct": _reading_dict(pair.direct),
                        "reverse": _reading_dict(pair.reverse),
                    }
                    for pair in setup.pairs
                ],
                "singles": [_reading_dict(single) for single in setup.singles],
            }
            for setup in result.setups
        ],
    }


def _reading_dict(reading) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "target": reading.target,
        "face": reading.face.value,
        "horizontal": reading.horizontal.to_dict(),
        "zenith": reading.zenith.to_dict(),
        "set_number": reading.set_number,
    }
    if reading.distance is not None:
        payload["distance"] = reading.distance.to_dict()
    if reading.target_height is not None:
        payload["target_height"] = reading.target_height.to_dict()
    if reading.extra:
        payload["extra"] = dict(reading.extra)
    return payload
