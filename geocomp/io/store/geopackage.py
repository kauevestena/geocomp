# SPDX-License-Identifier: GPL-2.0-or-later
"""The GeoPackage project store (FR-130, FR-133, FR-134, FR-135).

``specs/17-persistence-and-interoperability.md`` and ADR-0006: GeoPackage is the
default and canonical store, and PostGIS a mirror with an identical logical
schema. What a store *does* with a project is :class:`~geocomp.io.store.base.ProjectStore`'s,
shared with PostGIS since phase P11; this module is what makes it a GeoPackage.

**Written with the standard library's ``sqlite3``, not GDAL.** A GeoPackage *is*
a SQLite database with a documented set of metadata tables, so nothing here needs
a spatial library -- and the consequence is the point: the store is testable in
the fast tier, on every platform, with no QGIS and no GDAL. Eight of CI's nine
jobs have neither. A GDAL-backed store would have been shorter to write and
untestable in all eight, which for the one part of the system whose whole job is
*not losing data* is the wrong trade.

The file is a valid GeoPackage: the ``GPKG`` application id, the required
``gpkg_spatial_ref_sys`` rows, a ``gpkg_contents`` entry per table, and geometry
in the GeoPackage binary encoding. QGIS opens it and draws the network.

**Geometry is derived, and derived late.** ``specs/17`` section 2 rule 5: the
numeric coordinates are the record and the geometry is a view of them. So it is
computed on write from the authoritative JSON and never read back -- a reader
that took coordinates from the geometry column would be reading a rounded copy
of what sits beside it.
"""

from __future__ import annotations

import sqlite3
import struct
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from geocomp.core.errors import DataError
from geocomp.core.models import ObservationType
from geocomp.io.store.base import SRS_UNDEFINED_CARTESIAN, ProjectStore, _now, srs_of
from geocomp.io.store.migrations import SqliteTarget, check_version, migrate
from geocomp.io.store.schema import (
    SCHEMA,
    SCHEMA_VERSION,
    SQLITE,
    Table,
    ddl,
    index_ddl,
    view_ddl,
)

__all__ = ["GeoPackageStore", "open_store"]

#: ``GPKG`` as a big-endian integer, the GeoPackage application id.
APPLICATION_ID = 0x47504B47
#: GeoPackage 1.4.0, as the specification's ``user_version`` encoding.
USER_VERSION = 10400

SRS_UNDEFINED_GEOGRAPHIC = 0

#: Kept for callers of the pre-P11 name.
_srs_of = srs_of


# -- geometry -------------------------------------------------------------


def _point_blob(easting: float, northing: float, srs_id: int) -> bytes:
    """A GeoPackage POINT: the standard binary header plus little-endian WKB."""
    header = struct.pack("<2sBBi", b"GP", 0, 0b00000001, srs_id)
    wkb = struct.pack("<BIdd", 1, 1, easting, northing)
    return header + wkb


def _line_blob(points: Sequence[tuple[float, float]], srs_id: int) -> bytes:
    header = struct.pack("<2sBBi", b"GP", 0, 0b00000001, srs_id)
    wkb = struct.pack("<BII", 1, 2, len(points))
    for easting, northing in points:
        wkb += struct.pack("<dd", easting, northing)
    return header + wkb


class GeoPackageStore(ProjectStore):
    """A GeoComp project in one GeoPackage file."""

    backend = SQLITE

    def __init__(self, path: str | Path, connection: sqlite3.Connection) -> None:
        super().__init__(str(path))
        self.path = Path(path)
        self._connection = connection

    @property
    def connection(self) -> sqlite3.Connection:
        """The SQLite connection, for the migrations and the tests."""
        return self._connection

    def close(self) -> None:
        """Close the SQLite connection."""
        self._connection.close()

    def tables(self) -> list[str]:
        """The names of the file's tables, sorted."""
        rows = self._connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
        ).fetchall()
        return [row[0] for row in rows]

    # -- the backend hooks -------------------------------------------------

    def _execute(self, sql: str, parameters: Sequence[Any] = ()) -> sqlite3.Cursor:
        return self._connection.execute(sql, tuple(parameters))

    def _begin(self, write: bool) -> None:
        # A write takes SQLite's write lock at once (IMMEDIATE), so the revision
        # read next cannot change before this transaction commits. A read is a
        # deferred transaction: one consistent snapshot, no lock held against
        # writers until the first read.
        if self._connection.in_transaction:
            self._connection.commit()
        self._connection.execute("BEGIN IMMEDIATE" if write else "BEGIN")

    def _commit(self) -> None:
        self._connection.commit()

    def _rollback(self) -> None:
        self._connection.rollback()

    def _point(self, easting: float, northing: float, srs_id: int) -> bytes:
        return _point_blob(easting, northing, srs_id)

    def _line(self, points: Sequence[tuple[float, float]], srs_id: int) -> bytes:
        return _line_blob(points, srs_id)

    def migration_target(self) -> SqliteTarget:
        """What the migrations run against for this store."""
        return SqliteTarget(self._connection)


def _initialise(connection: sqlite3.Connection) -> None:
    """Make an empty SQLite file into a valid, empty GeoPackage."""
    connection.execute(f"PRAGMA application_id = {APPLICATION_ID}")
    connection.execute(f"PRAGMA user_version = {USER_VERSION}")
    connection.execute("PRAGMA foreign_keys = ON")

    connection.execute(
        """
        CREATE TABLE gpkg_spatial_ref_sys (
            srs_name TEXT NOT NULL,
            srs_id INTEGER NOT NULL PRIMARY KEY,
            organization TEXT NOT NULL,
            organization_coordsys_id INTEGER NOT NULL,
            definition TEXT NOT NULL,
            description TEXT
        )
        """
    )
    connection.executemany(
        "INSERT INTO gpkg_spatial_ref_sys VALUES (?, ?, ?, ?, ?, ?)",
        [
            ("Undefined cartesian SRS", -1, "NONE", -1, "undefined", None),
            ("Undefined geographic SRS", 0, "NONE", 0, "undefined", None),
            (
                "WGS 84 geodetic",
                4326,
                "EPSG",
                4326,
                'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],'
                'PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]]',
                None,
            ),
        ],
    )
    connection.execute(
        """
        CREATE TABLE gpkg_contents (
            table_name TEXT NOT NULL PRIMARY KEY,
            data_type TEXT NOT NULL,
            identifier TEXT UNIQUE,
            description TEXT DEFAULT '',
            last_change TEXT NOT NULL,
            min_x DOUBLE, min_y DOUBLE, max_x DOUBLE, max_y DOUBLE,
            srs_id INTEGER,
            CONSTRAINT fk_gc_r_srs_id FOREIGN KEY (srs_id)
                REFERENCES gpkg_spatial_ref_sys(srs_id)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE gpkg_geometry_columns (
            table_name TEXT NOT NULL,
            column_name TEXT NOT NULL,
            geometry_type_name TEXT NOT NULL,
            srs_id INTEGER NOT NULL,
            z TINYINT NOT NULL,
            m TINYINT NOT NULL,
            CONSTRAINT pk_geom_cols PRIMARY KEY (table_name, column_name)
        )
        """
    )

    for entry in SCHEMA:
        connection.execute(ddl(entry))
        for statement in index_ddl(entry):
            connection.execute(statement)
        _register(connection, entry)

    for statement in view_ddl([kind.name for kind in ObservationType]):
        connection.execute(statement)


def _register(connection: sqlite3.Connection, entry: Table) -> None:
    """Announce a table in the GeoPackage metadata."""
    data_type = "features" if entry.geometry is not None else "attributes"
    connection.execute(
        "INSERT INTO gpkg_contents "
        "(table_name, data_type, identifier, description, last_change, srs_id) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (
            entry.name,
            data_type,
            entry.name,
            entry.note.split(".")[0] if entry.note else "",
            _now(),
            SRS_UNDEFINED_CARTESIAN if entry.geometry is not None else None,
        ),
    )
    if entry.geometry is not None:
        connection.execute(
            "INSERT INTO gpkg_geometry_columns VALUES (?, ?, ?, ?, ?, ?)",
            (entry.name, "geom", entry.geometry.value, SRS_UNDEFINED_CARTESIAN, 0, 0),
        )


def open_store(
    path: str | Path, *, create: bool = False, migrate_older: bool = False
) -> GeoPackageStore:
    """Open a GeoComp GeoPackage, optionally creating or migrating it.

    Args:
        path: The file.
        create: Create it when it does not exist. Never overwrites: opening an
            existing file always opens it.
        migrate_older: Bring an older schema forward, after a backup. Off by
            default because migrating is a decision the user makes, and a
            library that silently rewrote the file it was asked to read would be
            taking it for them.

    Raises:
        DataError: ``project_store_not_found`` when the file is absent and
            *create* is false; ``project_store_not_geocomp`` when the file is a
            database but not one of ours; ``store_schema_too_new`` when it was
            written by a newer GeoComp; ``store_schema_older`` when it needs a
            migration that was not asked for.
    """
    target = Path(path)
    exists = target.is_file()
    if not exists and not create:
        raise DataError(
            "project_store_not_found",
            path=str(target),
            expected="an existing GeoComp GeoPackage, or create=True",
        )

    connection = sqlite3.connect(target)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    if not exists:
        with connection:
            _initialise(connection)
        return GeoPackageStore(target, connection)

    names = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    missing = sorted({entry.name for entry in SCHEMA} - names)
    if missing:
        connection.close()
        raise DataError(
            "project_store_not_geocomp",
            path=str(target),
            received=sorted(names)[:10],
            expected=f"a GeoComp store; these tables are missing: {', '.join(missing[:5])}",
        )

    store = GeoPackageStore(target, connection)
    found = store.schema_version
    try:
        check_version(found, path=target)
    except DataError:
        connection.close()
        raise

    if found < SCHEMA_VERSION:
        if not migrate_older:
            connection.close()
            raise DataError(
                "store_schema_older",
                path=str(target),
                received=found,
                supported=SCHEMA_VERSION,
                expected=(
                    "an up-to-date store, or migrate_older=True to bring it forward. "
                    "A backup is taken first and the caller is told what changed"
                ),
            )
        store.migration = migrate(connection, target, found)
    # What this store object has seen: the next save compares against it.
    store.refresh()
    return store
