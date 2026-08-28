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
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from geocomp.core.errors import DataError, ValidationError
from geocomp.io.store.schema import SCHEMA_VERSION

__all__ = [
    "MIGRATIONS",
    "MigrationReport",
    "backup_path",
    "check_version",
    "migrate",
    "register",
]


@dataclass
class MigrationReport:
    """What a migration did, so the caller can tell the user."""

    from_version: int
    to_version: int
    backup: Path | None = None
    steps: list[str] = field(default_factory=list)

    @property
    def migrated(self) -> bool:
        return self.from_version != self.to_version


#: ``{target_version: (description, apply)}``. A migration takes the store's
#: connection inside an open transaction and brings it from ``target - 1`` to
#: ``target``.
MIGRATIONS: dict[int, tuple[str, Callable[[sqlite3.Connection], None]]] = {}


def register(
    version: int, description: str
) -> Callable[[Callable[[sqlite3.Connection], None]], Callable[[sqlite3.Connection], None]]:
    """Register the migration that produces *version*."""

    def decorate(
        function: Callable[[sqlite3.Connection], None],
    ) -> Callable[[sqlite3.Connection], None]:
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
    connection: sqlite3.Connection,
    path: Path,
    found: int,
    *,
    take_backup: bool = True,
) -> MigrationReport:
    """Bring a store from *found* up to :data:`SCHEMA_VERSION`.

    The backup is taken **before** the transaction opens and is not removed on
    success: a migration that appeared to work and lost something is exactly the
    case a backup exists for, and it is discovered later.

    Args:
        take_backup: Only a test that has already copied the file sets this
            false. There is no user-facing way to skip the backup.
    """
    check_version(found, path=path)
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
        report.backup = backup_path(path)
        shutil.copy2(path, report.backup)

    with connection:
        for version in range(found + 1, SCHEMA_VERSION + 1):
            description, apply = MIGRATIONS[version]
            apply(connection)
            connection.execute(
                'UPDATE "gc_project" SET schema_version = ?', (version,)
            )
            report.steps.append(f"{version}: {description}")
    return report
