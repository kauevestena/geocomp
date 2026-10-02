# SPDX-License-Identifier: GPL-2.0-or-later
"""``geocomp:project_store`` -- save a network and its solution (FR-130, FR-131, FR-134).

``specs/17-persistence-and-interoperability.md`` sections 2 to 4.

A JSON document beside a report is enough to hand a result to someone. It is not
enough to *keep* one: a monitoring project accumulates epochs over years, needs
to know which observations produced which solution, and must refuse to delete
the ones a stored result depends on (FR-135). That is a database's job, and the
GeoPackage store is where it is done.

**Adding to an existing store rather than replacing it is the default**, because
the opposite mistake is unrecoverable: a user who meant to add this epoch's
solution to last year's project and instead replaced it has lost the project.
Replacing is available and says what it does.

**Superseding, not deleting.** A solution recomputed with better data does not
remove the one it replaces; it is recorded as superseding it, so the record of
what was believed and when survives (FR-135). Monitoring is exactly the case
where the earlier answer matters after it stops being the current one.

**A GeoPackage or a PostGIS schema** (phase P11). The same project, the same
tables, in one file or in a shared database reached through a QGIS connection.
The second is where two people can save to one project at once, so a save that
finds someone else's save since the store was read is refused -- and the
message says what to do -- rather than overwriting it.
"""

from __future__ import annotations

from typing import Any

from qgis.core import (
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterFile,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterProviderConnection,
    QgsProcessingParameterString,
)

from geocomp.algorithms.base import GeoCompAlgorithm
from geocomp.algorithms.project.common import read_network, read_solution
from geocomp.core.errors import GeoCompError
from geocomp.core.models import Project
from geocomp.services.messages import message_for

__all__ = ["ProjectStoreAlgorithm"]

STORE = "STORE"
DATABASE = "DATABASE"
SCHEMA = "SCHEMA"
SOLUTION = "SOLUTION"
NETWORK = "NETWORK"
PROJECT_ID = "PROJECT_ID"
SUPERSEDES = "SUPERSEDES"
REPLACE = "REPLACE"

#: Result key: what was written, in the order it was written.
WRITTEN = "WRITTEN"


class ProjectStoreAlgorithm(GeoCompAlgorithm):
    """Writes a network and a solution into a GeoComp GeoPackage project store."""

    TR_CONTEXT = "ProjectStoreAlgorithm"

    def displayName(self) -> str:
        return self.tr("Save to project store")

    def shortDescription(self) -> str:
        return self.tr(
            "Write a network and its solution into a GeoComp project: a GeoPackage or "
            "a PostGIS schema."
        )

    def help_body(self) -> str:
        return self.tr(
            "<p>Writes a network, a solution, or both into a GeoComp project store: a "
            "GeoPackage holding networks, observations, sessions, settings, solutions and "
            "their provenance, with the covariances stored so that they reload "
            "bit-identically.</p>"
            "<p>By default the solution is <b>added</b> to whatever the store already "
            "holds, because the opposite mistake cannot be undone: replacing a project "
            "that was meant to be added to loses it. Replacing is available and says so.</p>"
            "<p>A store already holding solutions computed from these observations will "
            "refuse to have them deleted (FR-135). To record that a new solution replaces "
            "an older one, name the older one under <i>Supersedes</i>: it is kept and "
            "marked, because in monitoring the earlier answer still matters after it stops "
            "being the current one.</p>"
            "<h3>Parameters</h3>"
            "<p><b>Project store</b> &mdash; the GeoPackage to write to. It is created if "
            "it does not exist; an older schema version is migrated after a backup, and a "
            "newer one is refused.</p>"
            "<p><b>PostgreSQL connection</b> and <b>Schema</b> &mdash; instead of a "
            "GeoPackage, a project in a PostGIS database, through a connection saved in "
            "QGIS and its login. Give one or the other. If someone else saves to the same "
            "project while you work, your save is refused rather than overwriting theirs; "
            "open the project again and redo the change.</p>"
            "<p><b>Solution</b> and <b>Network</b> &mdash; documents written by earlier "
            "algorithms. At least one is required.</p>"
        )

    def initAlgorithm(self, config: dict[str, Any] | None = None) -> None:
        self.addParameter(
            QgsProcessingParameterFileDestination(
                STORE,
                self.tr("Project store"),
                self.tr("GeoPackage (*.gpkg)"),
                optional=True,
                createByDefault=False,
            )
        )
        self.addParameter(
            QgsProcessingParameterProviderConnection(
                DATABASE,
                self.tr("PostgreSQL connection (instead of a GeoPackage)"),
                "postgres",
                optional=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                SCHEMA, self.tr("Schema"), defaultValue="geocomp", optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterFile(
                SOLUTION,
                self.tr("Solution document (optional)"),
                extension="json",
                optional=True,
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
            QgsProcessingParameterString(
                PROJECT_ID,
                self.tr("Project id"),
                defaultValue="geocomp",
                optional=True,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterString(
                SUPERSEDES,
                self.tr("Id of the solution this one replaces (optional)"),
                optional=True,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterBoolean(
                REPLACE,
                self.tr("Replace everything in the store rather than adding"),
                defaultValue=False,
            )
        )

    def processAlgorithm(
        self,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> dict[str, Any]:
        from geocomp.io.store import open_store

        solution_path = self.parameterAsFile(parameters, SOLUTION, context)
        network_path = self.parameterAsFile(parameters, NETWORK, context)
        if not solution_path and not network_path:
            raise QgsProcessingException(
                self.tr("Give a solution document, a network document, or both.")
            )

        try:
            solution = read_solution(solution_path) if solution_path else None
            network = read_network(network_path)
        except GeoCompError as error:
            raise QgsProcessingException(str(error)) from error

        target = self.parameterAsFileOutput(parameters, STORE, context)
        connection = self.parameterAsConnectionName(parameters, DATABASE, context)
        schema = (self.parameterAsString(parameters, SCHEMA, context) or "geocomp").strip()
        if bool(target) == bool(connection):
            raise QgsProcessingException(
                self.tr("Give either a GeoPackage or a PostgreSQL connection to save to.")
            )
        replace = self.parameterAsBool(parameters, REPLACE, context)
        supersedes = (self.parameterAsString(parameters, SUPERSEDES, context) or "").strip()
        project_id = (
            self.parameterAsString(parameters, PROJECT_ID, context) or "geocomp"
        ).strip()

        feedback.setProgress(20)
        try:
            if connection:
                from geocomp.services.postgis import open_database_store

                store = open_database_store(
                    connection, schema, create=True, migrate_older=True
                )
            else:
                store = open_store(target, create=True, migrate_older=True)
        except GeoCompError as error:
            raise QgsProcessingException(message_for(error)) from error
        if store.migration is not None and store.migration.migrated:
            feedback.pushInfo(
                self.tr("Migrated %1 from schema %2 to %3; the backup is %4")
                .replace("%1", store.location)
                .replace("%2", str(store.migration.from_version))
                .replace("%3", str(store.migration.to_version))
                .replace("%4", str(store.migration.backup))
            )

        written: list[str] = []
        try:
            with store:
                self._write(
                    store,
                    project_id=project_id,
                    network=network,
                    solution=solution,
                    replace=replace,
                    supersedes=supersedes,
                    written=written,
                    feedback=feedback,
                )
        except GeoCompError as error:
            raise QgsProcessingException(message_for(error)) from error

        feedback.setProgress(100)
        if connection:
            return {DATABASE: store.location, WRITTEN: written}
        return {STORE: target, WRITTEN: written}

    def _write(
        self,
        store,
        *,
        project_id: str,
        network,
        solution,
        replace: bool,
        supersedes: str,
        written: list[str],
        feedback: QgsProcessingFeedback,
    ) -> None:
        from geocomp.core.errors import DataError

        project: Project | None = None
        if not replace:
            try:
                project = store.read()
            except DataError:
                # An empty or new store. Not an error: the first write to a new
                # project store is the ordinary case, and reporting it as one
                # would train the user to ignore the message that matters.
                project = None

        first_write = project is None
        if project is None:
            project = Project(id=project_id, name=project_id)
        if network is not None:
            project.networks[network.id] = network
            written.append(f"network {network.id}")

        # Only rewrite the project when there is something new in it. Writing it
        # unconditionally cost nothing visible but did real damage: `write`
        # replaces, so adding this epoch's solution to last year's project
        # deleted last year's -- the store looked healthy and had lost the
        # answers. `keep_solutions` covers the case where a network *is* being
        # added to a store that already holds results.
        if replace or first_write or network is not None:
            store.write(project, keep_solutions=not replace and not first_write)
        feedback.setProgress(60)

        if solution is not None:
            store.write_solution(solution)
            written.append(f"solution {solution.id}")
            if supersedes:
                store.supersede_solution(supersedes, solution.id)
                written.append(f"{supersedes} superseded by {solution.id}")
                feedback.pushInfo(
                    self.tr(
                        "The superseded solution is kept, not deleted: what was believed "
                        "and when is part of a monitoring record."
                    )
                )

        for line in written:
            feedback.pushInfo(line)
