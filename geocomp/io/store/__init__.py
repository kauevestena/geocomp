# SPDX-License-Identifier: GPL-2.0-or-later
"""The project store (FR-130 to FR-135).

``specs/17-persistence-and-interoperability.md``, ADR-0006. GeoPackage is the
default and canonical store; PostGIS is its mirror with an identical logical
schema, driven from the same declarations in :mod:`geocomp.io.store.schema`.

**What is built and what is not.** The GeoPackage backend is complete and
tested. The PostGIS backend is *not built*: there is no PostgreSQL server in
this project's environments, so its round-trip acceptance criterion cannot be
demonstrated, and shipping an untested storage backend for the one part of the
system whose job is not losing data would be worse than shipping none. What is
here for it is the shared schema and its physical type mapping, so the two
cannot drift apart before the backend arrives.
"""

from __future__ import annotations

from geocomp.io.store.geopackage import GeoPackageStore, open_store
from geocomp.io.store.schema import SCHEMA, SCHEMA_VERSION, Table, table, table_names

__all__ = [
    "SCHEMA",
    "SCHEMA_VERSION",
    "GeoPackageStore",
    "Table",
    "open_store",
    "table",
    "table_names",
]
