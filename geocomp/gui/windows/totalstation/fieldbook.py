# SPDX-License-Identifier: GPL-2.0-or-later
"""Total Station ▸ Field book: where the observations are typed (FR-012, FR-014).

``specs/15-ui-menu-and-settings.md`` section 7.2. Four steps:

1. **Job and instrument** -- the job's name and CRS, the conventions the book is typed in,
   and the instrument: the profile library and the default precisions, which
   are the import algorithm's own parameters.
2. **Field book** -- the grid. One row per pointing; typed, pasted from a
   spreadsheet, or opened from the readings document the toolbox's *Import
   field book* wrote. What is wrong with a row is said beneath the grid as it
   is typed, by the importer's own reader.
3. **Check** -- runs ``geocomp:totalstation_import_fieldbook`` on the book.
4. **Report** -- the report it wrote.

The other Total Station windows compute from the book typed here.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qgis.core import QgsCoordinateReferenceSystem
from qgis.gui import QgsProjectionSelectionWidget
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from geocomp.core.errors import GeoCompError, ValidationError
from geocomp.gui.windows.totalstation.common import (
    TotalStationWindow,
    typing_label,
    vertical_label,
)
from geocomp.gui.workbench.grid import GridWidget
from geocomp.gui.workbench.parameters import ParameterForm
from geocomp.gui.workbench.window import Note, Step
from geocomp.jobs import total_station as ts
from geocomp.jobs.angles import AngleTyping
from geocomp.jobs.chains import Chain
from geocomp.services.messages import message_for

__all__ = ["FieldBookWindow"]

_TR_CONTEXT = "GeoCompTotalStationWindows"


def _tr(text: str) -> str:
    return QCoreApplication.translate(_TR_CONTEXT, text)


class FieldBookWindow(TotalStationWindow):
    """The total-station field book: set up, typed and checked."""

    NEEDS_USABLE_BOOK = False
    REPORT = ("import", "OUTPUT_HTML")
    TABLE = ("import", "OUTPUT_FINDINGS")

    def build(self) -> None:
        """The job and the instrument, the grid, and the import that checks it."""
        self.add_step(Step("setup", _tr("Job and instrument"), self._setup_page()))
        self.add_step(
            Step(
                "field_book",
                _tr("Field book"),
                self._grid_page(),
                problem=lambda: self.book_problem(rejected_rows_block=False),
                notes=self.book_notes,
            )
        )
        self.add_run_steps(_tr("Check"), _tr("Report"))
        self._load_setup()

    def action_label(self) -> str:
        """The run is a check of the book, and is called one."""
        return _tr("Check the field book")

    def chain(self) -> Chain:
        """The import, on the typed book."""
        return ts.import_chain(self.book)

    def figures(self, scalars: dict[str, Any]) -> list[tuple[str, str]]:
        """What the import counted."""
        return [
            (_tr("Records read"), str(scalars.get("import.RECORD_COUNT", ""))),
            (_tr("Setups"), str(scalars.get("import.SETUP_COUNT", ""))),
            (_tr("Rejected records"), str(scalars.get("import.REJECTED_COUNT", ""))),
        ]

    # -- step 1: setup ---------------------------------------------------------

    def _setup_page(self) -> QWidget:
        page = QWidget(self)
        self.name_edit = QLineEdit(page)
        self.name_edit.setObjectName("geocompJobName")
        self.name_edit.setPlaceholderText(_tr("What you call this survey"))
        self.crs_widget = QgsProjectionSelectionWidget(page)
        self.crs_widget.setObjectName("geocompJobCrs")
        self.crs_widget.setOptionVisible(QgsProjectionSelectionWidget.CrsOption.CrsNotSet, True)
        self.crs_widget.setNotSetText(_tr("No CRS: a local plane"))
        self.typing_combo = QComboBox(page)
        self.typing_combo.setObjectName("geocompAngleTyping")
        for typing in AngleTyping:
            self.typing_combo.addItem(typing_label(typing), typing.value)
        self.vertical_combo = QComboBox(page)
        self.vertical_combo.setObjectName("geocompVerticalAngle")
        for vertical in ts.VerticalAngle:
            self.vertical_combo.addItem(vertical_label(vertical), vertical.value)
        convention_note = QLabel(
            _tr(
                "A change of convention does not rewrite what is typed: the cells are read "
                "again in the new one, and any that no longer reads is marked."
            ),
            page,
        )
        convention_note.setWordWrap(True)
        self.import_form = ParameterForm(
            ts.IMPORT,
            ts.IMPORT_OPTIONS,
            lambda: self.job.parameters(ts.WINDOW_FIELD_BOOK),
            parent=page,
        )
        instrument_note = QLabel(
            _tr(
                "The instrument's precisions weight every reading. Without a profile library, "
                "a generic total station is assumed and the results are marked approximate."
            ),
            page,
        )
        instrument_note.setWordWrap(True)

        form = QFormLayout()
        form.addRow(_tr("Job name"), self.name_edit)
        form.addRow(_tr("Coordinate reference system"), self.crs_widget)
        form.addRow(_tr("Angles are typed as"), self.typing_combo)
        form.addRow(_tr("The vertical circle reads"), self.vertical_combo)
        layout = QVBoxLayout(page)
        layout.addLayout(form)
        layout.addWidget(convention_note)
        layout.addWidget(self.import_form)
        layout.addWidget(instrument_note)
        layout.addStretch(1)

        self.name_edit.editingFinished.connect(self._setup_changed)
        self.crs_widget.crsChanged.connect(lambda _crs=None: self._setup_changed())
        self.typing_combo.currentIndexChanged.connect(lambda _index=0: self._setup_changed())
        self.vertical_combo.currentIndexChanged.connect(lambda _index=0: self._setup_changed())
        self.import_form.changed.connect(lambda _name="": self.touch())
        return page

    def _load_setup(self) -> None:
        """Set the first step's widgets from the job."""
        self._loading = True
        try:
            job, book = self.job, self.book
            self.name_edit.setText(job.name)
            self.crs_widget.setCrs(
                QgsCoordinateReferenceSystem(job.crs) if job.crs else QgsCoordinateReferenceSystem()
            )
            self.typing_combo.setCurrentIndex(self.typing_combo.findData(book.angle_typing.value))
            self.vertical_combo.setCurrentIndex(self.vertical_combo.findData(book.vertical.value))
            self.import_form.reload()
        finally:
            self._loading = False

    def _setup_changed(self) -> None:
        if getattr(self, "_loading", False):
            return
        job, book = self.job, self.book
        crs = self.crs_widget.crs()
        before = (job.name, job.crs, dict(job.entry))
        job.name = self.name_edit.text().strip()
        job.crs = crs.authid() if crs.isValid() else ""
        book.angle_typing = AngleTyping(self.typing_combo.currentData())
        book.vertical = ts.VerticalAngle(self.vertical_combo.currentData())
        if (job.name, job.crs, dict(job.entry)) != before:
            # The headings state the convention, and the cells are read in it.
            self.grid.reload()
            self.touch()

    # -- step 2: the grid --------------------------------------------------------

    def _grid_page(self) -> QWidget:
        self.grid = GridWidget(
            self.book.table, self.heading, lambda: self.book.angle_typing, self
        )
        self.grid.edited.connect(self.touch)
        self.open_readings_button = QPushButton(_tr("Open readings document…"), self.grid)
        self.open_readings_button.setToolTip(
            _tr(
                "Fill the grid from the readings document the toolbox's Import field book "
                "wrote. It replaces what is in the grid; Undo brings it back."
            )
        )
        self.open_readings_button.clicked.connect(lambda _checked=False: self.open_readings())
        self.grid.buttons.insertWidget(self.grid.buttons.count() - 1, self.open_readings_button)
        return self.grid

    def open_readings(self) -> None:
        """Ask for a readings document and open it into the grid."""
        path, _filter = QFileDialog.getOpenFileName(
            self, _tr("Open readings document"), "", _tr("GeoComp readings (*.json)")
        )
        if path:
            self.open_readings_file(path)

    def open_readings_file(self, path: str | Path) -> bool:
        """Fill the grid from the readings document at *path*. Returns whether it was one."""
        try:
            try:
                document = json.loads(Path(path).read_text(encoding="utf-8"))
            except (OSError, ValueError) as error:
                raise ValidationError(
                    "readings_document_malformed", path=str(path), reason=str(error)
                ) from error
            self.book.fill_from_readings(document, source=str(path))
        except GeoCompError as error:
            self.say(message_for(error))
            return False
        self.grid.reload()
        self.touch()
        return True

    def note_chosen(self, note: Note) -> None:
        """Go to the row a line of the strip is about."""
        if note.table == ts.FIELD_BOOK and note.row is not None:
            column = self.book.table.index_of(note.column) if note.column else 0
            self.grid.select_row(note.row, column)

    def reload_pages(self) -> None:
        """Another job is the current one: show its book and its setup."""
        self.grid.set_table(self.book.table)
        self._load_setup()

    def refresh(self) -> None:
        """Also re-read the grid when the book was changed from another window."""
        if hasattr(self, "grid") and self.grid.model.table is not self.book.table:
            self.grid.set_table(self.book.table)
        super().refresh()
