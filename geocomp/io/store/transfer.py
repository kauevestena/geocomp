# SPDX-License-Identifier: GPL-2.0-or-later
"""Switching a project between GeoPackage and PostGIS, losing nothing (FR-132, phase P11).

``specs/17-persistence-and-interoperability.md`` section 4: *two operations,
export a GeoPackage project to a PostGIS schema, and import a PostGIS schema to
a GeoPackage. Both are complete round trips -- a round trip must be lossless,
asserted by a test comparing every table.*

**Table by table, not project by project.** Reading a project into objects and
writing it out again would copy what the domain model knows about, which is
not quite everything a store holds: a run record, a displacement, a revision.
Copying rows copies all of it, and is the operation "identical logical schema"
promises to make possible. Each value crosses as its logical kind -- a boolean
as a boolean, a covariance as its exact bytes, a geometry re-encoded between
the GeoPackage binary and PostGIS's EWKB -- so nothing is converted through
text and nothing is rounded.

**The comparison is part of the operation.** :func:`differences` reads both
stores back as logical values and lists every row that is not identical; the
algorithms run it after every copy and report it, so a round trip that lost
something says so where it happened rather than being discovered a year later.
Floating-point values are compared by their bytes: ``NaN`` equals itself and
``-0.0`` does not equal ``0.0``, because "identical" means identical.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field
from typing import Any

from geocomp.core.cancellation import NULL_CANCELLATION, CancellationToken, Cancelled
from geocomp.core.errors import DataError
from geocomp.io.store.base import SRS_UNDEFINED_CARTESIAN, ProjectStore
from geocomp.io.store.schema import (
    POSTGRES,
    SCHEMA,
    SCHEMA_VERSION,
    SQLITE,
    ColumnKind,
    Table,
    quoted,
)

__all__ = ["CopyReport", "copy_store", "differences", "logical_rows"]

_EWKB_SRID = 0x20000000
#: GeoPackage envelope sizes by the flags' envelope indicator (bits 1-3).
_ENVELOPE = {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}


@dataclass
class CopyReport:
    """What a copy moved, and whether the two stores now agree."""

    rows: dict[str, int] = field(default_factory=dict)
    #: Every row that differs after the copy; empty when the copy is lossless.
    differences: list[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        """The number of rows copied, over every table."""
        return sum(self.rows.values())

    @property
    def identical(self) -> bool:
        """Whether the copy matched the source in every table compared."""
        return not self.differences


def copy_store(
    source: ProjectStore,
    target: ProjectStore,
    cancellation: CancellationToken = NULL_CANCELLATION,
) -> CopyReport:
    """Copy every table of *source* into the empty *target*, then compare them.

    Both must be at the current schema version: a copy is a move between
    backends, not a migration, and an older store is migrated first.

    The rows go in as one transaction, and *cancellation* is asked between
    tables and once more before the commit. A cancelled copy raises
    :class:`~geocomp.core.cancellation.Cancelled` with nothing committed
    (``specs/17`` criterion 6).

    Raises:
        DataError: ``store_copy_target_not_empty`` when *target* already holds
            a project -- copying into it would mix two projects, and replacing
            it is a decision for the user, made by choosing an empty target.
    """
    for store in (source, target):
        if store.schema_version_or_none() not in (None, SCHEMA_VERSION):
            raise DataError(
                "store_schema_older",
                path=store.location,
                received=store.schema_version_or_none(),
                supported=SCHEMA_VERSION,
                expected="a store at the current schema version; migrate it first",
            )
    if target.schema_version_or_none() is not None:
        raise DataError(
            "store_copy_target_not_empty",
            path=target.location,
            expected="an empty store to copy into: a new GeoPackage, or a new schema",
        )

    contents = logical_rows(source)
    report = CopyReport()
    with target._transaction(write=True):
        _defer_foreign_keys(target)
        for entry in SCHEMA:
            if cancellation.is_cancelled():
                raise Cancelled()
            for row in contents[entry.name]:
                target._insert(entry.name, _physical(entry, row, target.backend))
            report.rows[entry.name] = len(contents[entry.name])
        if cancellation.is_cancelled():
            raise Cancelled()
    target.refresh()
    report.differences = differences(source, target, first_rows=contents)
    return report


def logical_rows(store: ProjectStore) -> dict[str, list[dict[str, Any]]]:
    """Every row of every table, as backend-independent values, in key order.

    Geometry is ``(srid, wkb)`` with the undefined SRS as -1 in both backends,
    the WKB without its SRID: the same shape whichever store it came from.
    """
    contents: dict[str, list[dict[str, Any]]] = {}
    with store._transaction(write=False):
        for entry in SCHEMA:
            columns = [quoted(column.name) for column in entry.columns]
            if entry.geometry is not None:
                columns.append(
                    'ST_AsEWKB("geom") AS "geom"' if store.backend == POSTGRES else '"geom"'
                )
            order = ", ".join(quoted(key) for key in entry.primary_key)
            rows = store._execute(
                f"SELECT {', '.join(columns)} FROM {quoted(entry.name)} ORDER BY {order}"
            ).fetchall()
            contents[entry.name] = [_logical(entry, row, store.backend) for row in rows]
    return contents


def differences(
    first: ProjectStore,
    second: ProjectStore,
    *,
    first_rows: dict[str, list[dict[str, Any]]] | None = None,
) -> list[str]:
    """Every difference between two stores' contents, table by table.

    Values are compared by kind: floating point by its bytes, so ``NaN`` equals
    ``NaN`` and ``-0.0`` differs from ``0.0``. *first_rows* spares reading
    *first* again when the caller already has its :func:`logical_rows`.
    """
    left = first_rows if first_rows is not None else logical_rows(first)
    right = logical_rows(second)
    found: list[str] = []
    for entry in SCHEMA:
        a, b = left[entry.name], right[entry.name]
        if len(a) != len(b):
            found.append(f"{entry.name}: {len(a)} rows against {len(b)}")
            continue
        for index, (row_a, row_b) in enumerate(zip(a, b, strict=True)):
            for name in row_a:
                if _key(entry, name, row_a[name]) != _key(entry, name, row_b[name]):
                    key = ", ".join(str(row_a[k]) for k in entry.primary_key)
                    found.append(f"{entry.name}[{key or index}].{name} differs")
    return found


# -- logical values ------------------------------------------------------------


def _logical(entry: Table, row: Any, backend: str) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for index, column in enumerate(entry.columns):
        value = row[index]
        if value is not None:
            if column.kind is ColumnKind.BOOLEAN:
                value = bool(value)
            elif column.kind is ColumnKind.BLOB:
                value = bytes(value)
        values[column.name] = value
    if entry.geometry is not None:
        raw = row[len(entry.columns)]
        if raw is None:
            values["geom"] = None
        elif backend == POSTGRES:
            values["geom"] = _from_ewkb(bytes(raw))
        else:
            values["geom"] = _from_gpkg(bytes(raw))
    return values


def _physical(entry: Table, row: dict[str, Any], backend: str) -> dict[str, Any]:
    values = dict(row)
    if entry.geometry is not None and values.get("geom") is not None:
        srid, wkb = values["geom"]
        values["geom"] = _to_ewkb(srid, wkb) if backend == POSTGRES else _to_gpkg(srid, wkb)
    return values


def _key(entry: Table, name: str, value: Any) -> Any:
    """A value in the form two stores' values are compared in."""
    if value is None or name == "geom":
        return value
    if entry.column(name).kind is ColumnKind.REAL:
        return struct.pack(">d", float(value))
    return value


def _defer_foreign_keys(store: ProjectStore) -> None:
    """Check references at commit, so a solution can precede the one superseding it."""
    if store.backend == POSTGRES:
        store._execute("SET CONSTRAINTS ALL DEFERRED")
    elif store.backend == SQLITE:
        store._execute("PRAGMA defer_foreign_keys = ON")


# -- geometry encodings ----------------------------------------------------------


def _from_gpkg(blob: bytes) -> tuple[int, bytes]:
    """``(srs_id, wkb)`` from a GeoPackage geometry blob."""
    if blob[:2] != b"GP":
        raise DataError(
            "store_geometry_unreadable",
            received=blob[:8].hex(),
            expected="a GeoPackage geometry, beginning GP",
        )
    flags = blob[3]
    order = "<" if flags & 1 else ">"
    (srs_id,) = struct.unpack(order + "i", blob[4:8])
    start = 8 + _ENVELOPE.get((flags >> 1) & 0b111, 0)
    return (srs_id if srs_id > 0 else SRS_UNDEFINED_CARTESIAN), blob[start:]


def _to_gpkg(srid: int, wkb: bytes) -> bytes:
    return struct.pack("<2sBBi", b"GP", 0, 0b00000001, srid) + wkb


def _from_ewkb(ewkb: bytes) -> tuple[int, bytes]:
    """``(srid, wkb)`` from PostGIS EWKB: the SRID taken out, the type flag cleared."""
    order = "<" if ewkb[0] == 1 else ">"
    (kind,) = struct.unpack(order + "I", ewkb[1:5])
    if kind & _EWKB_SRID:
        (srid,) = struct.unpack(order + "I", ewkb[5:9])
        rest = ewkb[9:]
    else:
        srid, rest = 0, ewkb[5:]
    wkb = ewkb[:1] + struct.pack(order + "I", kind & ~_EWKB_SRID) + rest
    return (srid if srid > 0 else SRS_UNDEFINED_CARTESIAN), wkb


def _to_ewkb(srid: int, wkb: bytes) -> bytes:
    order = "<" if wkb[0] == 1 else ">"
    (kind,) = struct.unpack(order + "I", wkb[1:5])
    return (
        wkb[:1]
        + struct.pack(order + "II", kind | _EWKB_SRID, srid if srid > 0 else 0)
        + wkb[5:]
    )
