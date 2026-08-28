# SPDX-License-Identifier: GPL-2.0-or-later
"""Readers and writers: the boundary between GeoComp and other people's files.

``specs/17-persistence-and-interoperability.md``. The GeoPackage project store
and the *Adjust* format arrive in phase P5; phase P3 starts this package with
the field-book importer, because FR-160's saved field mapping is what makes the
first vertical slice usable on real instrument exports.

Nothing here imports QGIS. It is permitted to (``specs/03`` section 3.7 allows
GDAL and ``qgis.core`` in ``io/`` and above), and it happens not to need it --
which keeps the parsing testable in the fast tier where a malformed field book
is cheapest to reason about.
"""

from __future__ import annotations

from geocomp.io.fieldbook import (
    FieldBookRecord,
    ImportResult,
    read_field_book,
    read_field_book_csv,
)
from geocomp.io.levelbook import (
    Layout,
    LevelBookRecord,
    LevelImportResult,
    LevelMapping,
    read_level_book,
    read_level_book_csv,
)
from geocomp.io.mapping import (
    AngleFormat,
    ColumnMapping,
    FieldMapping,
    infer_mapping,
)

__all__ = [
    "AngleFormat",
    "ColumnMapping",
    "FieldBookRecord",
    "FieldMapping",
    "ImportResult",
    "Layout",
    "LevelBookRecord",
    "LevelImportResult",
    "LevelMapping",
    "infer_mapping",
    "read_field_book",
    "read_field_book_csv",
    "read_level_book",
    "read_level_book_csv",
]
