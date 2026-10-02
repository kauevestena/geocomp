# SPDX-License-Identifier: GPL-2.0-or-later
"""The project store (FR-130 to FR-135).

``specs/17-persistence-and-interoperability.md``, ADR-0006. GeoPackage is the
default and canonical store; PostGIS is its mirror with an identical logical
schema, driven from the same declarations in :mod:`geocomp.io.store.schema`.

Since phase P11 both are built: what a store does with a project is written
once, in :mod:`geocomp.io.store.base`; :mod:`~geocomp.io.store.geopackage` and
:mod:`~geocomp.io.store.postgis` supply only what their backend does
differently; and :mod:`~geocomp.io.store.transfer` moves a project between them
table by table, then compares every table to show nothing was lost.
"""

from __future__ import annotations

from geocomp.io.store.base import ProjectStore
from geocomp.io.store.geopackage import GeoPackageStore, open_store
from geocomp.io.store.postgis import PostgisStore, open_postgis_store
from geocomp.io.store.schema import SCHEMA, SCHEMA_VERSION, Table, table, table_names
from geocomp.io.store.transfer import CopyReport, copy_store, differences

__all__ = [
    "SCHEMA",
    "SCHEMA_VERSION",
    "CopyReport",
    "GeoPackageStore",
    "PostgisStore",
    "ProjectStore",
    "Table",
    "copy_store",
    "differences",
    "open_postgis_store",
    "open_store",
    "table",
    "table_names",
]
