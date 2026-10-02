# SPDX-License-Identifier: GPL-2.0-or-later
"""Schema versioning and forward-only migration (FR-133).

``specs/17-persistence-and-interoperability.md`` section 3.

Two rules, and the asymmetry between them is the whole design:

* Opening a **newer** schema is **refused**. Reading a schema you do not
  understand silently corrupts it -- the columns you know are still there, so
  the read succeeds, and the write back drops everything you did not know
  about. A refusal costs a plugin update; the alternative costs the data.
* Opening an **older** schema is **migrated**, in a transaction, after a backup,
  and the caller is told what changed.

This matters more than the usual versioning ceremony. A monitoring project
accumulates epochs over years and outlives several plugin releases; the store
that cannot be opened is the store whose ten-year displacement series is gone.

**Migrations are forward-only and each is registered with the version it
produces.** There is no down-migration: a downgrade path that is never exercised
is a downgrade path that does not work, and the honest recovery from "I upgraded
and want to go back" is the backup this module took.
"""

from __future__ import annotations

import shutil
import sqlite3
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

from geocomp.core.errors import DataError, ValidationError
from geocomp.io.store.schema import POSTGRES, SCHEMA_VERSION, SQLITE, physical_type, table

__all__ = [
    "MIGRATIONS",
    "MigrationReport",
    "MigrationTarget",
    "SqliteTarget",
    "backup_path",
    "check_version",
    "migrate",
    "register",
]


class MigrationTarget(Protocol):
    """What a migration needs of a store, on either backend (phase P11).

    A migration runs SQL, so it needs to know which dialect it is writing:
    a column added by a migration must have the physical type the schema
    declares on *that* backend, or a migrated store and a new one would differ.
    """

    backend: str

    def execute(self, sql: str) -> Any: ...

    def transaction(self) -> Any: ...


class SqliteTarget:
    """A SQLite connection as a :class:`MigrationTarget`.

    **The transaction is explicit.** In Python's legacy ``sqlite3`` mode an
    ``ALTER TABLE`` does not open a transaction -- only DML does -- so before
    P11 a migration's first ``ALTER`` ran outside the ``with connection:``
    block and committed on its own. Had a later step failed, the store would
    have kept a column its recorded version does not account for, and the
    migration could not simply be run again.
    """

    backend = SQLITE

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def execute(self, sql: str) -> Any:
        return self.connection.execute(sql)

    @contextmanager
    def transaction(self) -> Iterator[None]:
        if self.connection.in_transaction:
            self.connection.commit()
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            yield
        except BaseException:
            self.connection.rollback()
            raise
        self.connection.commit()


@dataclass
class MigrationReport:
    """What a migration did, so the caller can tell the user."""

    from_version: int
    to_version: int
    #: The file a GeoPackage was copied to, or the schema a PostGIS store was.
    backup: Path | str | None = None
    steps: list[str] = field(default_factory=list)

    @property
    def migrated(self) -> bool:
        return self.from_version != self.to_version


#: ``{target_version: (description, apply)}``. A migration takes a
#: :class:`MigrationTarget` inside an open transaction and brings the store from
#: ``target - 1`` to ``target``.
MIGRATIONS: dict[int, tuple[str, Callable[[MigrationTarget], None]]] = {}


def register(
    version: int, description: str
) -> Callable[[Callable[[MigrationTarget], None]], Callable[[MigrationTarget], None]]:
    """Register the migration that produces *version*."""

    def decorate(
        function: Callable[[MigrationTarget], None],
    ) -> Callable[[MigrationTarget], None]:
        if version in MIGRATIONS:
            raise ValueError(f"two migrations claim version {version}")
        if version > SCHEMA_VERSION:
            raise ValueError(
                f"migration to {version} is beyond SCHEMA_VERSION {SCHEMA_VERSION}; "
                "raise the schema version in the same change"
            )
        MIGRATIONS[version] = (description, function)
        return function

    return decorate


# Version 1 is the first released schema, so there is nothing to migrate *to*
# it. The chain begins empty on purpose: an invented migration from a version
# that never existed is a step that has never run against real data.


def check_version(found: int, *, path: Path | None = None) -> None:
    """Raise unless *found* can be opened, migrated or not.

    Raises:
        DataError: ``store_schema_too_new``, naming both versions. This is the
            refusal FR-133 requires, and the message says what to do about it
            rather than only that something is wrong (NFR-006).
    """
    if found > SCHEMA_VERSION:
        raise DataError(
            "store_schema_too_new",
            path=str(path) if path else "",
            received=found,
            supported=SCHEMA_VERSION,
            expected=(
                f"a store written by this version of GeoComp (schema {SCHEMA_VERSION}) "
                "or older. Update the plugin to open this one; GeoComp will not read a "
                "schema it does not understand, because the columns it cannot see would "
                "be dropped the first time it saved"
            ),
        )
    if found < 1:
        raise DataError(
            "store_schema_invalid",
            path=str(path) if path else "",
            received=found,
            expected="a schema version of at least 1",
        )


def backup_path(path: Path, *, now: datetime | None = None) -> Path:
    """Where the pre-migration backup of *path* goes.

    Beside the original, with the timestamp in the name: a backup in a temporary
    directory is a backup the user cannot find when they need it.
    """
    stamp = (now or datetime.now(UTC)).strftime("%Y%m%dT%H%M%SZ")
    return path.with_name(f"{path.stem}.backup-{stamp}{path.suffix}")


def migrate(
    connection: sqlite3.Connection | MigrationTarget,
    path: Path | str,
    found: int,
    *,
    take_backup: bool = True,
    backup: Callable[[], Path | str] | None = None,
) -> MigrationReport:
    """Bring a store from *found* up to :data:`SCHEMA_VERSION`.

    The backup is taken **before** the transaction opens and is not removed on
    success: a migration that appeared to work and lost something is exactly the
    case a backup exists for, and it is discovered later.

    Args:
        connection: A GeoPackage's SQLite connection, or any
            :class:`MigrationTarget` -- a PostGIS store is one.
        path: The GeoPackage, or the label a PostGIS store is named by.
        take_backup: Only a test that has already copied the file sets this
            false. There is no user-facing way to skip the backup.
        backup: How to take the backup when it is not a file copy: a PostGIS
            store copies its schema (:func:`geocomp.io.store.postgis.backup_schema`).
            Returns where the backup went.
    """
    target: MigrationTarget = (
        SqliteTarget(connection) if isinstance(connection, sqlite3.Connection) else connection
    )
    check_version(found, path=Path(path) if target.backend == SQLITE else None)
    report = MigrationReport(from_version=found, to_version=SCHEMA_VERSION)
    if found == SCHEMA_VERSION:
        return report

    missing = [
        version
        for version in range(found + 1, SCHEMA_VERSION + 1)
        if version not in MIGRATIONS
    ]
    if missing:
        raise ValidationError(
            "store_migration_missing",
            received=found,
            expected=(
                f"a migration for each of schema versions {missing}. The store cannot "
                "be brought forward without one, and GeoComp will not guess at the "
                "difference"
            ),
        )

    if take_backup:
        if backup is not None:
            report.backup = backup()
        else:
            report.backup = backup_path(Path(path))
            shutil.copy2(path, report.backup)

    with target.transaction():
        for version in range(found + 1, SCHEMA_VERSION + 1):
            description, apply = MIGRATIONS[version]
            apply(target)
            target.execute(f'UPDATE "gc_project" SET schema_version = {int(version)}')
            report.steps.append(f"{version}: {description}")
    return report


def _add_column(target: MigrationTarget, table_name: str, column_name: str) -> None:
    """``ALTER TABLE ... ADD COLUMN`` with the type the schema declares on this backend."""
    kind = table(table_name).column(column_name).kind
    target.execute(
        f'ALTER TABLE "{table_name}" ADD COLUMN "{column_name}" {physical_type(kind, target.backend)}'
    )


@register(2, "gc_observation gains instrument_height and target_height")
def _setup_heights(target: MigrationTarget) -> None:
    """Carry a sight's instrument and target heights (specs/09 section 2.5).

    A slope distance or zenith angle measured trunnion-axis to reflector needs
    both heights in the observation equation; before this they could not be
    stored at all, so a store written by schema 1 simply has none and the two
    columns are added empty. Nothing is back-filled, and nothing can be: a
    height GeoComp never had is not zero, it is absent, and writing zero would
    turn "we do not know" into "the instrument stood on the mark".

    This is the schema's first migration, which makes it the first exercise of
    the machinery as well as of itself.
    """
    for column in ("instrument_height", "target_height"):
        _add_column(target, "gc_observation", column)


@register(3, "gc_adjusted_station gains gravity")
def _adjusted_gravity(target: MigrationTarget) -> None:
    """Carry a gravity solution's adjusted value (specs/12 section 5).

    Before phase P8 a gravity solution could not be written at all -- its value
    had nowhere to go but a position's ``up`` slot, which refuses an
    acceleration -- so no schema 2 store holds one, and the column is added
    empty. As with the setup heights, nothing is back-filled.
    """
    _add_column(target, "gc_adjusted_station", "gravity")


@register(4, "gc_project gains revision; gc_network_member gains ordinal")
def _revision_and_order(target: MigrationTarget) -> None:
    """Concurrent saves detected, and a network's order kept (phase P11).

    ``revision`` starts at 0 in a migrated store. ``ordinal`` is filled from
    the order the old store implied: SQLite's ``rowid``, which is the order the
    members were written in, so a migrated network reads back in the order it
    always did. In PostgreSQL there is no such order to recover -- no PostGIS
    store older than schema 4 was ever written -- so the physical order is the
    best that exists, and it is used.
    """
    _add_column(target, "gc_project", "revision")
    _add_column(target, "gc_network_member", "ordinal")
    target.execute('UPDATE "gc_project" SET "revision" = 0')
    if target.backend == POSTGRES:
        target.execute(
            'UPDATE "gc_network_member" AS m SET "ordinal" = r.n '
            'FROM (SELECT ctid, row_number() OVER (ORDER BY ctid) AS n FROM "gc_network_member") AS r '
            "WHERE m.ctid = r.ctid"
        )
    else:
        target.execute('UPDATE "gc_network_member" SET "ordinal" = rowid')


@register(5, "gc_provenance gains strategies")
def _provenance_strategies(target: MigrationTarget) -> None:
    """Name the approximations a result rests on in its provenance (FR-203; P12c).

    The audit of P12c found the provenance recorded an approximate solution's
    mode and not which approximations made it so. The column is added empty and
    nothing is back-filled here: a stored solution's strategies are in its
    covariance, and :class:`~geocomp.core.models.Solution` puts them in its
    provenance as it is read.
    """
    _add_column(target, "gc_provenance", "strategies")
