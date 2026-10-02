# SPDX-License-Identifier: GPL-2.0-or-later
"""Switching a project between a GeoPackage and PostGIS (FR-131, FR-132; phase P11).

``specs/17-persistence-and-interoperability.md`` section 4: *two operations,
export a GeoPackage project to a PostGIS schema, and import a PostGIS schema to
a GeoPackage. Both are complete round trips.*

**Each copies, then proves the copy.** The project moves table by table
(:func:`geocomp.io.store.transfer.copy_store`), and both stores are then read
back and compared, every row of every table; the log says how many rows moved
and that the comparison found nothing, or the algorithm fails naming what
differs. A switch of storage is the moment a project is most at risk, so it is
the moment to check rather than to assume.

**Never into a store that holds a project.** Copying into one would mix two
projects; replacing one is a decision made by choosing an empty target, not a
side effect of an export.

**The login is QGIS's.** The database is a connection saved in QGIS, used with
whatever credentials it carries -- an authentication configuration, ideally --
and the log names it by its name and schema, never by a connection string
(NFR-010).
"""

from __future__ import annotations

from typing import Any

from qgis.core import (
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingOutputNumber,
    QgsProcessingOutputString,
    QgsProcessingParameterFile,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterProviderConnection,
    QgsProcessingParameterString,
)
from qgis.PyQt.QtCore import QCoreApplication

from geocomp.algorithms.base import GeoCompAlgorithm
from geocomp.core.cancellation import Cancelled
from geocomp.core.errors import GeoCompError
from geocomp.services.messages import message_for

__all__ = ["ExportToPostgisAlgorithm", "ImportFromPostgisAlgorithm"]

SOURCE = "SOURCE"
DATABASE = "DATABASE"
SCHEMA = "SCHEMA"
OUTPUT = "OUTPUT"
ROWS = "ROWS"
TARGET = "TARGET"


#: The shared body's own words, translated under their own context: through
#: ``self.tr`` they were looked up under each subclass's and never found
#: (found by P12c's audit).
_CONTEXT = "GeoCompPostgis"


def _tr(text: str) -> str:
    return QCoreApplication.translate(_CONTEXT, text)


class _SwitchAlgorithm(GeoCompAlgorithm):
    """What export and import share: the copy, the comparison, the report."""

    def _database_parameters(self) -> None:
        self.addParameter(
            QgsProcessingParameterProviderConnection(
                DATABASE, _tr("PostgreSQL connection"), "postgres"
            )
        )
        self.addParameter(
            QgsProcessingParameterString(SCHEMA, _tr("Schema"), defaultValue="geocomp")
        )

    def _database(self, parameters, context) -> tuple[str, str]:
        connection = self.parameterAsConnectionName(parameters, DATABASE, context)
        schema = (self.parameterAsString(parameters, SCHEMA, context) or "").strip()
        if not connection or not schema:
            raise QgsProcessingException(_tr("Give a PostgreSQL connection and a schema."))
        return connection, schema

    def _copy(self, source, target, feedback: QgsProcessingFeedback) -> int:
        from geocomp.algorithms.transaction import FeedbackCancellation
        from geocomp.io.store.transfer import copy_store

        feedback.pushInfo(
            _tr("Copying %1 to %2").replace("%1", source.location).replace("%2", target.location)
        )
        report = copy_store(source, target, FeedbackCancellation(feedback))
        for name, count in report.rows.items():
            if count:
                feedback.pushInfo(f"  {name}: {count}")
        if not report.identical:
            for line in report.differences[:20]:
                feedback.reportError(line)
            raise QgsProcessingException(
                _tr(
                    "The copy in %1 differs from the original in %2 place(s), listed above. "
                    "Do not use it; delete it and report this."
                )
                .replace("%1", target.location)
                .replace("%2", str(len(report.differences)))
            )
        feedback.pushInfo(
            _tr("%1 rows copied; every table compared identical.").replace(
                "%1", str(report.total)
            )
        )
        return report.total


class ExportToPostgisAlgorithm(_SwitchAlgorithm):
    """A GeoPackage project into a new PostGIS schema."""

    TR_CONTEXT = "ExportToPostgisAlgorithm"

    def displayName(self) -> str:
        return self.tr("Export project to PostGIS")

    def shortDescription(self) -> str:
        return self.tr("Copy a GeoPackage project into a PostGIS schema, and check the copy.")

    def help_body(self) -> str:
        return self.tr(
            "<p>Copies every table of a GeoComp GeoPackage into a schema of a PostGIS "
            "database, for a project that several people work on or that grows large. "
            "Nothing is converted through text: coordinates, covariances and their "
            "provenance arrive exactly as they were.</p>"
            "<p>Both stores are then compared, every row of every table, and the log says "
            "so. The schema must be new or empty; an existing project is never "
            "overwritten. The database is reached through a connection saved in QGIS, "
            "with its login, and must have the PostGIS extension.</p>"
            "<p>An older GeoPackage is migrated first, after a backup.</p>"
        )

    def initAlgorithm(self, config: dict[str, Any] | None = None) -> None:
        self.addParameter(
            QgsProcessingParameterFile(SOURCE, self.tr("GeoComp GeoPackage"), extension="gpkg")
        )
        self._database_parameters()
        self.addOutput(QgsProcessingOutputNumber(ROWS, self.tr("Rows copied")))
        self.addOutput(QgsProcessingOutputString(TARGET, self.tr("Project store")))

    def processAlgorithm(
        self,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> dict[str, Any]:
        from geocomp.io.store import open_store
        from geocomp.services.postgis import open_database_store

        path = self.parameterAsFile(parameters, SOURCE, context)
        connection, schema = self._database(parameters, context)
        try:
            with open_store(path, migrate_older=True) as source:
                with open_database_store(connection, schema, create=True) as target:
                    try:
                        rows = self._copy(source, target, feedback)
                    except Cancelled:
                        # The rows were rolled back; what opening the target
                        # made goes too, so the database is as it was.
                        target.remove_what_was_created()
                        raise
                    location = target.location
        except GeoCompError as error:
            raise QgsProcessingException(message_for(error)) from error
        feedback.setProgress(100)
        return {ROWS: rows, TARGET: location}


class ImportFromPostgisAlgorithm(_SwitchAlgorithm):
    """A PostGIS project into a new GeoPackage."""

    TR_CONTEXT = "ImportFromPostgisAlgorithm"

    def displayName(self) -> str:
        return self.tr("Import project from PostGIS")

    def shortDescription(self) -> str:
        return self.tr("Copy a PostGIS project into a new GeoPackage, and check the copy.")

    def help_body(self) -> str:
        return self.tr(
            "<p>Copies every table of a GeoComp project in a PostGIS schema into a "
            "GeoPackage: for work away from the database, for a copy to send, or to keep a "
            "monitoring project's state at a date.</p>"
            "<p>Both stores are then compared, every row of every table, and the log says "
            "so. The GeoPackage must be new; an existing project is never overwritten.</p>"
        )

    def initAlgorithm(self, config: dict[str, Any] | None = None) -> None:
        self._database_parameters()
        self.addParameter(
            QgsProcessingParameterFileDestination(
                OUTPUT, self.tr("GeoPackage"), self.tr("GeoPackage (*.gpkg)")
            )
        )
        self.addOutput(QgsProcessingOutputNumber(ROWS, self.tr("Rows copied")))

    def processAlgorithm(
        self,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> dict[str, Any]:
        from geocomp.io.store import open_store
        from geocomp.services.postgis import open_database_store

        connection, schema = self._database(parameters, context)
        path = self.parameterAsFileOutput(parameters, OUTPUT, context)
        try:
            with open_database_store(connection, schema, migrate_older=True) as source:
                with open_store(path, create=True) as target:
                    rows = self._copy(source, target, feedback)
        except GeoCompError as error:
            raise QgsProcessingException(message_for(error)) from error
        feedback.setProgress(100)
        return {OUTPUT: path, ROWS: rows}
