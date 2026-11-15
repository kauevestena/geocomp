# SPDX-License-Identifier: GPL-2.0-or-later
"""What the Level windows share: the levelling field book's reading and its headings.

The book is read once per state of the job by
:class:`~geocomp.gui.windows.book.BookWindow`, as the total-station book is.
What is levelling's own is here: the level and the staff-reading precision the
import resolves from its parameters, as the import does, and the headings.
"""

from __future__ import annotations

from typing import Any

from qgis.core import QgsProcessingException
from qgis.PyQt.QtCore import QCoreApplication

from geocomp.algorithms.levelling.common import level_from_parameters, staff_defaults
from geocomp.core.findings import Finding
from geocomp.gui.windows.book import BookWindow
from geocomp.jobs import levelling as lv
from geocomp.jobs.tables import Column

__all__ = ["LevelWindow", "level_heading"]

_TR_CONTEXT = "GeoCompLevelWindows"


def _tr(text: str) -> str:
    return QCoreApplication.translate(_TR_CONTEXT, text)


def level_heading(column: Column, *, three_wire: bool = False) -> str:
    """A levelling grid column's heading, stating its unit or the tokens it takes."""
    headings = {
        "line": _tr("Line"),
        "setup": _tr("Setup"),
        "station": _tr("Station"),
        "sight": _tr("Sight (BS / FS / IS)"),
        "reading": _tr("Middle wire (m)") if three_wire else _tr("Reading (m)"),
        "upper": _tr("Upper wire (m)"),
        "lower": _tr("Lower wire (m)"),
        "distance": _tr("Sight distance (m)"),
        "note": _tr("Note"),
        "name": _tr("Benchmark"),
        "height": _tr("Height (m)"),
        "sigma": _tr("Standard deviation (m)"),
    }
    return headings.get(column.key, column.key)


class LevelWindow(BookWindow):
    """A window over the levelling job."""

    FIELD_BOOK_WINDOW = lv.WINDOW_FIELD_BOOK
    FIELD_BOOK_TABLE = lv.FIELD_BOOK
    IMPORT_ALGORITHM = lv.IMPORT
    IMPORT_OPTIONS = lv.IMPORT_OPTIONS

    def banner_action_label(self) -> str:
        """A problem with the book is put right in the Levelling field book window."""
        return _tr("Open the levelling field book")

    @property
    def book(self) -> lv.LevellingBook:
        """The current job, read as a levelling field book."""
        return lv.LevellingBook(self.job)

    def heading(self, column: Column) -> str:
        """A column's heading; the reading is the middle wire in a book of three."""
        return level_heading(column, three_wire=self.book.three_wire)

    def read_book(self, options: dict[str, Any]) -> tuple[lv.LevelCheck, str]:
        """The book as the import reads it, with the level and the precision it resolves."""
        refusal = ""
        level = None
        try:
            level = level_from_parameters(
                profiles=str(options.get("PROFILES") or ""),
                level_id=str(options.get("LEVEL_ID") or ""),
                collimation=0.0,
                collimation_sigma=0.0,
            )
        except QgsProcessingException as error:
            refusal = str(error)
        check = self.book.check(
            level=level,
            defaults=staff_defaults(float(options.get("SIGMA_READING") or 0.0)),
            stadia_factor=float(options.get("STADIA_FACTOR") or 100.0),
        )
        return check, refusal

    def typed_finding(self, finding: Finding) -> tuple[Finding, int | None]:
        """The finding renumbered for the grid, and its row counted from zero."""
        return lv.as_typed(finding)
