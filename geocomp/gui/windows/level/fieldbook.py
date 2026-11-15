# SPDX-License-Identifier: GPL-2.0-or-later
"""Level ▸ Levelling field book: where the staff readings are typed (FR-012, FR-014).

``specs/15-ui-menu-and-settings.md`` section 7.2. Four steps:

1. **Job and instrument** -- the job's name, and the level: the profile
   library, the level's id, the default staff-reading precision and the stadia
   factor, which are the import algorithm's own parameters.
2. **Levelling field book** -- the grid. One row per staff reading, as a
   *caderneta de nivelamento* is kept: a backsight opens a setup, its
   foresights and intermediate sights follow. What is wrong with a row is said
   beneath the grid as it is typed, by the importer's own reader.
3. **Check** -- runs ``geocomp:levelling_import`` on the book.
4. **Report** -- the report it wrote.

The other Level windows compute from the book typed here.
"""

from __future__ import annotations

from typing import Any

from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtWidgets import QFormLayout, QLabel, QLineEdit, QVBoxLayout, QWidget

from geocomp.gui.windows.level.common import LevelWindow
from geocomp.gui.workbench.grid import GridWidget
from geocomp.gui.workbench.parameters import ParameterForm
from geocomp.gui.workbench.window import Note, Step
from geocomp.jobs import levelling as lv
from geocomp.jobs.chains import Chain

__all__ = ["LevelFieldBookWindow"]

_TR_CONTEXT = "GeoCompLevelWindows"


def _tr(text: str) -> str:
    return QCoreApplication.translate(_TR_CONTEXT, text)


class LevelFieldBookWindow(LevelWindow):
    """The levelling field book: the level, the readings, and the import that checks them."""

    NEEDS_USABLE_BOOK = False
    REPORT = ("import", "OUTPUT_HTML")

    def build(self) -> None:
        """The job and the level, the grid, and the import that checks it."""
        self.add_step(Step("setup", _tr("Job and instrument"), self._setup_page()))
        self.add_step(
            Step(
                "field_book",
                _tr("Levelling field book"),
                self._grid_page(),
                problem=lambda: self.book_problem(rejected_rows_block=False),
                notes=self.book_notes,
            )
        )
        self.add_run_steps(_tr("Check"), _tr("Report"))
        self._load_setup()

    def action_label(self) -> str:
        """The run is a check of the book, and is called one."""
        return _tr("Check the levelling field book")

    def chain(self) -> Chain:
        """The import, on the typed book."""
        return lv.import_chain(self.book)

    def figures(self, scalars: dict[str, Any]) -> list[tuple[str, str]]:
        """What the import counted."""
        return [
            (_tr("Setups"), str(scalars.get("import.SETUP_COUNT", ""))),
            (_tr("Lines"), str(scalars.get("import.LINE_COUNT", ""))),
            (_tr("Rejected rows"), str(scalars.get("import.REJECTED_ROWS", ""))),
        ]

    # -- step 1: the job and the level ---------------------------------------------

    def _setup_page(self) -> QWidget:
        page = QWidget(self)
        self.name_edit = QLineEdit(page)
        self.name_edit.setObjectName("geocompJobName")
        self.name_edit.setPlaceholderText(_tr("What you call this levelling"))
        self.import_form = ParameterForm(
            lv.IMPORT,
            lv.IMPORT_OPTIONS,
            lambda: self.job.parameters(lv.WINDOW_FIELD_BOOK),
            parent=page,
        )
        note = QLabel(
            _tr(
                "The level's reading precision weights every reading. Without a profile "
                "library a generic level is assumed, and the report says so. The level chosen "
                "here is the one every Level window reduces with."
            ),
            page,
        )
        note.setWordWrap(True)
        form = QFormLayout()
        form.addRow(_tr("Job name"), self.name_edit)
        layout = QVBoxLayout(page)
        layout.addLayout(form)
        layout.addWidget(self.import_form)
        layout.addWidget(note)
        layout.addStretch(1)
        self.name_edit.editingFinished.connect(self._name_changed)
        self.import_form.changed.connect(lambda _name="": self.touch())
        return page

    def _load_setup(self) -> None:
        self.name_edit.setText(self.job.name)
        self.import_form.reload()

    def _name_changed(self) -> None:
        name = self.name_edit.text().strip()
        if name != self.job.name:
            self.job.name = name
            self.touch()

    # -- step 2: the grid ----------------------------------------------------------

    def _grid_page(self) -> QWidget:
        page = QWidget(self)
        self.grid = GridWidget(self.book.table, self.heading, parent=page)
        self.grid.edited.connect(self._edited)
        note = QLabel(
            _tr(
                "A backsight opens a setup, and the foresights and intermediate sights below "
                "it belong to it; a setup left unnamed is numbered in order. A line left blank "
                "is the line above. Type the upper and lower wires on every row, or on none: "
                "a book with one is read as three wires throughout."
            ),
            page,
        )
        note.setWordWrap(True)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.grid, 1)
        layout.addWidget(note)
        self._wires_shown = self.book.three_wire
        return page

    def _edited(self) -> None:
        # The reading column is the middle wire in a book of three, and says so.
        wires = self.book.three_wire
        if wires != self._wires_shown:
            self._wires_shown = wires
            self.grid.reload()
        self.touch()

    def note_chosen(self, note: Note) -> None:
        """Go to the row a line of the strip is about."""
        if note.table == lv.FIELD_BOOK and note.row is not None:
            column = self.book.table.index_of(note.column) if note.column else 0
            self.grid.select_row(note.row, column)

    def reload_pages(self) -> None:
        """Another job is the current one: show its book and its level."""
        self.grid.set_table(self.book.table)
        self._load_setup()

    def refresh(self) -> None:
        """Also re-read the grid when the book was changed from another window."""
        if hasattr(self, "grid") and self.grid.model.table is not self.book.table:
            self.grid.set_table(self.book.table)
        super().refresh()
