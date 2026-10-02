# SPDX-License-Identifier: GPL-2.0-or-later
"""The PostGIS project store (FR-131, FR-132, FR-133; phase P11).

``specs/17-persistence-and-interoperability.md`` sections 1 to 4 and ADR-0006:
the same logical schema as the GeoPackage, in one PostgreSQL schema per project,
for what a single file is not good at -- shared projects, concurrent users, long
monitoring series. What a store does with a project is
:class:`~geocomp.io.store.base.ProjectStore`'s and is shared with the
GeoPackage; this module supplies only what PostgreSQL does differently.

**Through ``psycopg2``**, the PostgreSQL driver QGIS's own Python tools use.
The store takes a libpq connection string or an open connection, so it is
tested in the fast tier against a real server -- ``tests/test_postgis_store.py``,
whenever ``GEOCOMP_TEST_POSTGRES`` names one -- with no QGIS. Where the driver
is absent the store says so, by name, rather than failing on an import. The
plugin builds the connection string from the QGIS connection registry
(``geocomp/services/postgis.py``), so a password is never something GeoComp asks
for, stores, or writes down (NFR-010); and the string itself is never used as
the store's name in a message, because it may hold one.

**What differs, and why each difference is safe:**

* *Placeholders.* The shared SQL marks parameters with ``?``; here they become
  ``%s``.
* *Upsert.* The same ``INSERT ... ON CONFLICT DO UPDATE`` as SQLite's (the
  shared code writes it); only the geometry's parameter is cast.
* *Geometry.* EWKB, with SRID 0 where the GeoPackage writes -1 (undefined
  cartesian): PostGIS has no negative SRID.
* *Booleans* are ``boolean``, not 0 and 1.
* *Transactions.* The connection runs in autocommit, and the store opens its
  own: a write takes ``SHARE ROW EXCLUSIVE`` on ``gc_project`` so that two saves
  cannot interleave between the revision check and the commit; a read is
  ``REPEATABLE READ``, one consistent snapshot of a project being written by
  someone else.
"""

from __future__ import annotations

import struct
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Any

from geocomp.core.errors import DataError
from geocomp.core.models import ObservationType
from geocomp.io.store.base import ProjectStore
from geocomp.io.store.migrations import check_version, migrate
from geocomp.io.store.schema import (
    POSTGRES,
    SCHEMA,
    SCHEMA_VERSION,
    ColumnKind,
    Table,
    ddl,
    index_ddl,
    quoted,
    view_ddl,
)

__all__ = ["PostgisStore", "backup_schema", "connect", "open_postgis_store"]

#: EWKB's flag for "an SRID follows the type".
EWKB_SRID = 0x20000000


def connect(conninfo: str) -> Any:
    """A ``psycopg2`` connection from a libpq connection string.

    Raises:
        DataError: ``postgis_driver_missing`` when ``psycopg2`` is not
            installed, naming it; ``postgis_connection_failed`` when the server
            refuses -- with the server's reason, which names no password.
    """
    try:
        import psycopg2
    except ImportError as error:
        raise DataError(
            "postgis_driver_missing",
            expected=(
                "the psycopg2 Python module, which QGIS's own database tools use; "
                "install it into the Python QGIS runs (python3-psycopg2 on Linux)"
            ),
        ) from error
    try:
        return psycopg2.connect(conninfo)
    except psycopg2.Error as error:
        raise DataError(
            "postgis_connection_failed",
            reason=_first_line(error),
            expected="a reachable PostgreSQL server and a login it accepts",
        ) from error


def _first_line(error: Exception) -> str:
    return (str(error).strip().splitlines() or [type(error).__name__])[0]


class PostgisStore(ProjectStore):
    """A GeoComp project in one PostgreSQL schema."""

    backend = POSTGRES

    def __init__(self, connection: Any, schema: str, label: str) -> None:
        super().__init__(label)
        self.schema = schema
        self._connection = connection
        #: What opening with ``create=True`` made: the schema, or only its
        #: tables in a schema that was there and empty. Kept so that a run
        #: that is cancelled can take away exactly what it made, and no more.
        self.created_schema = False
        self.created_tables = False

    def remove_what_was_created(self) -> None:
        """Drop the schema, or the tables, that opening this store created.

        For an export that was cancelled (``specs/17`` criterion 6): the target
        must be left as it was, and before the run there was no project here.
        Nothing is dropped that this store did not create.
        """
        if self.created_schema:
            self._execute(f"DROP SCHEMA {quoted(self.schema)} CASCADE")
        elif self.created_tables:
            for entry in reversed(SCHEMA):
                self._execute(
                    f"DROP TABLE IF EXISTS {quoted(self.schema)}.{quoted(entry.name)} CASCADE"
                )
        self.created_schema = self.created_tables = False

    @property
    def connection(self) -> Any:
        return self._connection

    def close(self) -> None:
        self._connection.close()

    def tables(self) -> list[str]:
        rows = self._execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = ? AND table_type = 'BASE TABLE' ORDER BY table_name",
            (self.schema,),
        ).fetchall()
        return [row[0] for row in rows]

    # -- the backend hooks -------------------------------------------------

    def _execute(self, sql: str, parameters: Sequence[Any] = ()) -> Any:
        from psycopg2.extras import DictCursor

        cursor = self._connection.cursor(cursor_factory=DictCursor)
        if parameters:
            cursor.execute(sql.replace("%", "%%").replace("?", "%s"), tuple(parameters))
        else:
            cursor.execute(sql)
        return cursor

    def _begin(self, write: bool) -> None:
        if write:
            self._execute("BEGIN")
            self._execute('LOCK TABLE "gc_project" IN SHARE ROW EXCLUSIVE MODE')
        else:
            self._execute("BEGIN ISOLATION LEVEL REPEATABLE READ")

    def _commit(self) -> None:
        self._execute("COMMIT")

    def _rollback(self) -> None:
        self._execute("ROLLBACK")

    def _marker(self, column: str) -> str:
        return "?::geometry" if column == "geom" else "?"

    def _adapt(self, entry: Table, column: str, value: Any) -> Any:
        if value is None or column == "geom":
            return value
        if entry.column(column).kind is ColumnKind.BOOLEAN:
            return bool(value)
        return value

    def _point(self, easting: float, northing: float, srs_id: int) -> bytes:
        return struct.pack("<BIIdd", 1, 1 | EWKB_SRID, _srid(srs_id), easting, northing)

    def _line(self, points: Sequence[tuple[float, float]], srs_id: int) -> bytes:
        body = b"".join(struct.pack("<dd", x, y) for x, y in points)
        return struct.pack("<BIII", 1, 2 | EWKB_SRID, _srid(srs_id), len(points)) + body

    def migration_target(self) -> _Target:
        return _Target(self)


class _Target:
    """A PostGIS store as a :class:`~geocomp.io.store.migrations.MigrationTarget`."""

    backend = POSTGRES

    def __init__(self, store: PostgisStore) -> None:
        self._store = store

    def execute(self, sql: str) -> Any:
        return self._store._execute(sql)

    @contextmanager
    def transaction(self) -> Iterator[None]:
        with self._store._transaction(write=True):
            yield


def _srid(srs_id: int) -> int:
    """PostGIS's SRID for a GeoPackage srs_id: 0 for undefined, never negative."""
    return srs_id if srs_id > 0 else 0


def backup_schema(store: PostgisStore, *, now: datetime | None = None) -> str:
    """Copy every table of the store's schema into a new schema beside it.

    The PostGIS counterpart of the GeoPackage's backup file: before a migration,
    in the same database, with the time in its name, so it is where the user
    looks. Copies the tables as they are, whatever version wrote them -- a
    backup that went through the current schema would not be a backup of the
    old one.
    """
    stamp = (now or datetime.now(UTC)).strftime("%Y%m%dT%H%M%SZ")
    name = f"{store.schema}_backup_{stamp}"[:63]
    with store._transaction(write=False):
        store._execute(f"CREATE SCHEMA {quoted(name)}")
        for table_name in store.tables():
            store._execute(
                f"CREATE TABLE {quoted(name)}.{quoted(table_name)} AS "
                f"TABLE {quoted(store.schema)}.{quoted(table_name)}"
            )
    return name


def open_postgis_store(
    connection: Any,
    schema: str,
    *,
    create: bool = False,
    migrate_older: bool = False,
    label: str = "",
) -> PostgisStore:
    """Open a GeoComp project in a PostgreSQL schema, optionally creating or migrating it.

    Args:
        connection: A libpq connection string, or an open ``psycopg2``
            connection, which the store takes over (and closes).
        schema: The schema the project lives in: one project, one schema.
        create: Create the schema and its tables when absent, or initialise an
            empty schema. Never overwrites: a schema holding a project is opened.
        migrate_older: Bring an older schema version forward, after a backup.
        label: How the store is named in messages. Never the connection string,
            which may hold a password (NFR-010).

    Raises:
        DataError: ``postgis_extension_missing`` when the database lacks
            PostGIS; ``project_store_not_found``, ``project_store_not_geocomp``,
            ``store_schema_too_new`` and ``store_schema_older`` as
            :func:`geocomp.io.store.open_store` raises them.
    """
    if isinstance(connection, str):
        connection = connect(connection)
    connection.autocommit = True
    store = PostgisStore(connection, schema, label or f"PostGIS schema {schema}")
    try:
        _prepare(store, create=create)
        found = store.schema_version_or_none()
        if found is None and not create:
            raise DataError(
                "project_store_empty",
                path=store.location,
                expected="a store holding a project row",
            )
        if found is not None:
            check_version(found)
            if found < SCHEMA_VERSION:
                if not migrate_older:
                    raise DataError(
                        "store_schema_older",
                        path=store.location,
                        received=found,
                        supported=SCHEMA_VERSION,
                        expected=(
                            "an up-to-date store, or migrate_older=True to bring it forward. "
                            "A backup is taken first and the caller is told what changed"
                        ),
                    )
                store.migration = migrate(
                    store.migration_target(),
                    store.location,
                    found,
                    backup=lambda: backup_schema(store),
                )
        store.refresh()
    except BaseException:
        connection.close()
        raise
    return store


def _prepare(store: PostgisStore, *, create: bool) -> None:
    """Check the database, find or create the schema, and point the session at it."""
    extension = store._execute(
        "SELECT n.nspname FROM pg_extension AS e "
        "JOIN pg_namespace AS n ON n.oid = e.extnamespace WHERE e.extname = 'postgis'"
    ).fetchone()
    if extension is None:
        raise DataError(
            "postgis_extension_missing",
            path=store.location,
            expected=(
                "a database with the PostGIS extension. An administrator enables it "
                "once, with: CREATE EXTENSION postgis"
            ),
        )
    exists = store._execute(
        "SELECT 1 FROM information_schema.schemata WHERE schema_name = ?", (store.schema,)
    ).fetchone()
    if exists is None and not create:
        raise DataError(
            "project_store_not_found",
            path=store.location,
            expected="an existing GeoComp schema, or create=True",
        )
    if exists is None:
        store._execute(f"CREATE SCHEMA {quoted(store.schema)}")
        store.created_schema = True
    # Unqualified names resolve to the project's schema; PostGIS's functions
    # and types to wherever the extension lives.
    store._execute(f"SET search_path TO {quoted(store.schema)}, {quoted(extension[0])}")

    names = set(store.tables())
    if not names:
        if not create:
            raise DataError(
                "project_store_not_found",
                path=store.location,
                expected="a schema holding a GeoComp project, or create=True",
            )
        _initialise(store)
        store.created_tables = True
        return
    missing = sorted({entry.name for entry in SCHEMA} - names)
    if missing:
        raise DataError(
            "project_store_not_geocomp",
            path=store.location,
            received=sorted(names)[:10],
            expected=f"a GeoComp store; these tables are missing: {', '.join(missing[:5])}",
        )


def _initialise(store: PostgisStore) -> None:
    """Create the logical schema's tables, indexes and views, in one transaction."""
    with store._transaction(write=False):
        for entry in SCHEMA:
            store._execute(ddl(entry, POSTGRES))
            for statement in index_ddl(entry, POSTGRES):
                store._execute(statement)
        for statement in view_ddl([kind.name for kind in ObservationType], POSTGRES):
            store._execute(statement)
