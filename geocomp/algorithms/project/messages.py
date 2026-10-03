# SPDX-License-Identifier: GPL-2.0-or-later
"""User-facing wording for what the project store refuses (``specs/17``; phase P11).

Each says what happened and what to do about it (NFR-006). Before P11 the store
algorithm showed these as their codes; the refusals matter more with a shared
PostGIS store, where the most likely one -- someone else saved first -- is
something the user can act on only if they are told it plainly.

None of them names a password or a connection string: a store is named by its
file, or by the QGIS connection's name and the schema (NFR-010).

Importing this module registers the templates; :mod:`geocomp.algorithms.project`
imports it.
"""

from __future__ import annotations

from geocomp.services.messages import MessageTemplate, register_template

__all__ = ["TEMPLATES"]

TEMPLATES: dict[str, MessageTemplate] = {
    # -- the documents the project and monitoring algorithms read (P12c-6) ---
    # Each carries the file's path, so the refusal is said against the input it
    # came from (geocomp.algorithms.inputs). Before P12c-6 none had a template,
    # and a run showed the code and its context instead.
    "data.json_document_unreadable": MessageTemplate(
        "'%1' could not be read as a JSON document (%2). Expected %3.",
        "path",
        "reason",
        "expected",
    ),
    "data.json_document_not_an_object": MessageTemplate(
        "'%1' is not a GeoComp document: its top level is not a JSON object. Expected %2.",
        "path",
        "expected",
    ),
    "data.network_given_where_a_solution_was_expected": MessageTemplate(
        "'%1' is a network document, not a solution: it has stations but no adjusted "
        "stations. Choose the solution an adjustment wrote.",
        "path",
    ),
    "data.solution_document_malformed": MessageTemplate(
        "'%1' is not a solution document as GeoComp writes it (%2).",
        "path",
        "reason",
    ),
    "data.network_document_malformed": MessageTemplate(
        "'%1' is not a network document as GeoComp writes it (%2).",
        "path",
        "reason",
    ),
    "data.project_store_not_found": MessageTemplate(
        "There is no GeoComp project at %1. Check the name, or choose to create it.",
        "path",
    ),
    "data.project_store_not_geocomp": MessageTemplate(
        "%1 is not a GeoComp project store: it holds other tables (%2). GeoComp does "
        "not write into a store it did not create; choose a new file or schema.",
        "path",
        "received",
    ),
    "data.project_store_empty": MessageTemplate(
        "The project store %1 holds no project yet. Save a network or a solution to it first.",
        "path",
    ),
    "data.store_schema_too_new": MessageTemplate(
        "The project store %1 was written by a newer GeoComp (schema %2; this version "
        "reads up to %3). Update the plugin to open it: GeoComp does not read a schema "
        "it does not understand, because what it cannot see would be lost on the next save.",
        "path",
        "received",
        "supported",
    ),
    "data.store_schema_older": MessageTemplate(
        "The project store %1 uses schema %2, older than this version's %3. It can be "
        "migrated, after a backup is taken.",
        "path",
        "received",
        "supported",
    ),
    "data.store_schema_invalid": MessageTemplate(
        "The project store %1 records schema version %2, which no GeoComp wrote. It may "
        "be damaged; restore it from a backup.",
        "path",
        "received",
    ),
    "validation.store_migration_missing": MessageTemplate(
        "A project store at schema %1 cannot be brought forward by this version of "
        "GeoComp: a migration step is missing. Report this; do not edit the store by hand.",
        "received",
    ),
    "data.store_modified_concurrently": MessageTemplate(
        "Someone else saved %1 since you opened it (revision %2 now; you read %3). "
        "Nothing was written. Open the project again and redo your change, so their "
        "save is not overwritten.",
        "path",
        "received",
        "seen",
    ),
    "validation.observation_has_results": MessageTemplate(
        "The observation %1 cannot be deleted: the stored solutions %2 were computed "
        "from it (FR-135). Supersede those solutions first, or keep the observation.",
        "observation",
        "received",
    ),
    "validation.unknown_solution": MessageTemplate(
        "There is no solution %1 in this project store.",
        "solution",
    ),
    "validation.solution_supersedes_itself": MessageTemplate(
        "The solution %1 cannot supersede itself; name the earlier solution it replaces.",
        "solution",
    ),
    "data.store_copy_target_not_empty": MessageTemplate(
        "%1 already holds a project, and copying into it would mix two. Copy into a "
        "new GeoPackage or a new schema.",
        "path",
    ),
    "data.store_geometry_unreadable": MessageTemplate(
        "A geometry in the project store could not be read (it begins %1). The store "
        "may be damaged; the numeric coordinates beside it are the record.",
        "received",
    ),
    "data.postgis_driver_missing": MessageTemplate(
        "PostGIS projects need the psycopg2 Python module, which this QGIS does not "
        "have. Install it into the Python QGIS uses (on Linux, the python3-psycopg2 "
        "package), then restart QGIS.",
    ),
    "data.postgis_connection_failed": MessageTemplate(
        "Could not connect to the PostgreSQL server: %1. Check the connection in the "
        "QGIS browser; its login is the one GeoComp uses.",
        "reason",
    ),
    "data.postgis_connection_unknown": MessageTemplate(
        "There is no PostgreSQL connection named '%1' in QGIS. Add it in the Browser "
        "panel under PostgreSQL, or choose one that exists.",
        "received",
    ),
    "data.postgis_extension_missing": MessageTemplate(
        "The database behind %1 does not have the PostGIS extension. A database "
        "administrator enables it once, with: CREATE EXTENSION postgis",
        "path",
    ),
}

for _code, _template in TEMPLATES.items():
    register_template(_code, _template)
