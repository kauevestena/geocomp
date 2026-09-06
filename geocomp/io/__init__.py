# SPDX-License-Identifier: GPL-2.0-or-later
"""Readers and writers: the boundary between GeoComp and other people's files.

``specs/17-persistence-and-interoperability.md``. Phase P3 starts this package
with the field-book importer, because FR-160's saved field mapping is what makes
the first vertical slice usable on real instrument exports; the GeoPackage
project store follows in P5, and the *Adjust* format (FR-161) once an example
file finally existed to write a reader against -- it was re-planned out of three
phases for want of one.

Nothing here imports QGIS. It is permitted to (``specs/03`` section 3.7 allows
GDAL and ``qgis.core`` in ``io/`` and above), and it happens not to need it --
which keeps the parsing testable in the fast tier where a malformed field book
is cheapest to reason about.
"""

from __future__ import annotations

from geocomp.io.adjust import AdjustReport, read_adjust, write_adjust
from geocomp.io.fieldbook import (
    FieldBookRecord,
    ImportResult,
    read_field_book,
    read_field_book_csv,
)
from geocomp.io.krumm import KrummReport, read_krumm
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
    "AdjustReport",
    "AngleFormat",
    "ColumnMapping",
    "FieldBookRecord",
    "FieldMapping",
    "ImportResult",
    "KrummReport",
    "Layout",
    "LevelBookRecord",
    "LevelImportResult",
    "LevelMapping",
    "infer_mapping",
    "read_adjust",
    "read_field_book",
    "read_field_book_csv",
    "read_krumm",
    "read_level_book",
    "read_level_book_csv",
    "write_adjust",
]
