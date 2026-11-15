# SPDX-License-Identifier: GPL-2.0-or-later
"""The grid a field book is typed into (FR-012, FR-014).

A table view over a :class:`~geocomp.jobs.tables.TypedTable`. The table holds
what was typed and decides what is readable; this draws it and edits it:

* a spare row at the foot is always there to type into, as a paper book always
  has a next line; typing in it adds the row, with what the columns carry;
* a cell that cannot be read is tinted and says why when pointed at -- it is
  never refused while it is being typed;
* a block copied from a spreadsheet is pasted where the cursor is, and the
  selection is copied as one a spreadsheet pastes;
* Enter moves to the next cell and, at the end of a row, to the start of the
  next, which is the order a field book is read aloud in;
* every edit can be undone.

The model takes the column headings from its owner, because a heading states
the convention -- ``Hz (D M S)`` -- and the convention is the job's.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from qgis.PyQt.QtCore import QAbstractTableModel, QCoreApplication, QModelIndex, Qt, pyqtSignal
from qgis.PyQt.QtGui import QBrush, QColor, QKeyEvent, QKeySequence
from qgis.PyQt.QtWidgets import (
    QAbstractItemDelegate,
    QAbstractItemView,
    QApplication,
    QHBoxLayout,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from geocomp.jobs.angles import AngleTyping
from geocomp.jobs.tables import Column, TypedTable
from geocomp.services.messages import message_for

__all__ = ["GridView", "GridWidget", "TypedTableModel"]

_TR_CONTEXT = "GeoCompWorkbench"

#: The tint of a cell that cannot be read. Light enough to read the text through.
_PROBLEM_COLOUR = QColor(250, 205, 205)


def _tr(text: str) -> str:
    return QCoreApplication.translate(_TR_CONTEXT, text)


class TypedTableModel(QAbstractTableModel):
    """A typed table, as Qt's views read and edit one.

    Args:
        table: The table shown.
        heading: Gives a column its translated heading.
        angle_typing: Gives the convention angles are read in, or ``None`` for
            a table without angles.
        parent: The Qt parent.
    """

    #: The table was edited through the model.
    edited = pyqtSignal()

    def __init__(
        self,
        table: TypedTable,
        heading: Callable[[Column], str],
        angle_typing: Callable[[], AngleTyping | None] = lambda: None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._table = table
        self._heading = heading
        self._angle_typing = angle_typing
        self._problems: dict[tuple[int, int], str] = {}
        self._read_problems()

    @property
    def table(self) -> TypedTable:
        """The table shown."""
        return self._table

    def set_table(self, table: TypedTable) -> None:
        """Show another table: the job was replaced."""
        self.beginResetModel()
        self._table = table
        self._read_problems()
        self.endResetModel()

    def reload(self) -> None:
        """Read the table again: it was changed from outside, or its conventions were."""
        self.beginResetModel()
        self._read_problems()
        self.endResetModel()

    def _read_problems(self) -> None:
        self._problems = {
            (problem.row, self._table.index_of(problem.column)): message_for(problem.error)
            for problem in self._table.problems(self._angle_typing())
        }

    # -- what Qt asks ------------------------------------------------------

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: B008 -- Qt's signature
        """The table's rows and the spare one to type into."""
        return 0 if parent.isValid() else self._table.row_count + 1

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: B008 -- Qt's signature
        """One column per column of the table."""
        return 0 if parent.isValid() else len(self._table.columns)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """A cell's text, and for an unreadable one its tint and the reason."""
        if not index.isValid() or index.row() >= self._table.row_count:
            return None
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            return self._table.row(index.row())[index.column()]
        problem = self._problems.get((index.row(), index.column()))
        if problem is not None and role == Qt.ItemDataRole.BackgroundRole:
            return QBrush(_PROBLEM_COLOUR)
        if problem is not None and role == Qt.ItemDataRole.ForegroundRole:
            return QBrush(QColor(60, 0, 0))
        if problem is not None and role == Qt.ItemDataRole.ToolTipRole:
            return problem
        return None

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole
    ) -> Any:
        """A column's heading, and a row's number counted from one."""
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return self._heading(self._table.columns[section])
        return "*" if section >= self._table.row_count else str(section + 1)

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        """Every cell can be selected and typed in."""
        del index
        return (
            Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable
        )

    def setData(self, index: QModelIndex, value: Any, role: int = Qt.ItemDataRole.EditRole) -> bool:
        """Type *value* into a cell; in the spare row, that adds the row first."""
        if not index.isValid() or role != Qt.ItemDataRole.EditRole:
            return False
        text = "" if value is None else str(value)
        row, key = index.row(), self._table.columns[index.column()].key
        if row >= self._table.row_count:
            if not text.strip():
                return False
            self.beginInsertRows(QModelIndex(), row + 1, row + 1)
            self._table.insert_row()
            self.endInsertRows()
        self._table.set_cell(row, key, text.strip())
        self._changed()
        return True

    def _changed(self) -> None:
        self._read_problems()
        if self.rowCount() and self.columnCount():
            self.dataChanged.emit(
                self.index(0, 0), self.index(self.rowCount() - 1, self.columnCount() - 1)
            )
        self.headerDataChanged.emit(Qt.Orientation.Vertical, 0, max(self.rowCount() - 1, 0))
        self.edited.emit()

    # -- edits of more than one cell -----------------------------------------

    def paste(self, index: QModelIndex, block: str) -> None:
        """Paste a spreadsheet block with its top-left cell at *index*."""
        key = self._table.columns[max(index.column(), 0)].key
        self.beginResetModel()
        written = self._table.paste(max(index.row(), 0), key, block)
        self._read_problems()
        self.endResetModel()
        if written != (0, 0):
            self.edited.emit()

    def remove_rows(self, rows: list[int]) -> None:
        """Take whole rows out."""
        self._structural(lambda: self._table.remove_rows(rows))

    def insert_row(self, row: int | None = None) -> int:
        """Add a row at *row*, or at the foot, and return where it went."""
        position: list[int] = []
        self._structural(lambda: position.append(self._table.insert_row(row)))
        return position[0]

    def clear_cells(self, cells: list[tuple[int, int]]) -> None:
        """Empty the cells named by row and column number."""
        keys = [column.key for column in self._table.columns]
        self._structural(
            lambda: self._table.clear_cells(
                (row, keys[column]) for row, column in cells if row < self._table.row_count
            )
        )

    def undo(self) -> None:
        """Undo the table's last edit."""
        self._structural(self._table.undo)

    def redo(self) -> None:
        """Make the table's last undone edit again."""
        self._structural(self._table.redo)

    def _structural(self, edit: Callable[[], object]) -> None:
        before = self._table.revision
        self.beginResetModel()
        edit()
        self._read_problems()
        self.endResetModel()
        if self._table.revision != before:
            self.edited.emit()


class GridView(QTableView):
    """The table view of a grid: a spreadsheet's keys, over a typed table."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ContiguousSelection)
        self.setEditTriggers(
            QAbstractItemView.EditTrigger.AnyKeyPressed
            | QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.EditKeyPressed
        )
        self.setTabKeyNavigation(True)
        self.horizontalHeader().setStretchLastSection(True)

    def grid_model(self) -> TypedTableModel:
        """The typed model the view shows."""
        return self.model()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Paste, copy, clear, undo and redo, and Enter to the next cell."""
        if event.matches(QKeySequence.StandardKey.Paste):
            self.paste()
        elif event.matches(QKeySequence.StandardKey.Copy):
            self.copy()
        elif event.matches(QKeySequence.StandardKey.Undo):
            self.grid_model().undo()
        elif event.matches(QKeySequence.StandardKey.Redo):
            self.grid_model().redo()
        elif event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self.clear_selection()
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.advance()
        else:
            super().keyPressEvent(event)

    def closeEditor(self, editor: QWidget, hint: QAbstractItemDelegate.EndEditHint) -> None:
        """After Enter in a cell, go on to the next one."""
        super().closeEditor(editor, hint)
        if hint == QAbstractItemDelegate.EndEditHint.SubmitModelCache:
            self.advance()

    def advance(self) -> None:
        """Move to the next cell: rightwards, then to the start of the next row."""
        index = self.currentIndex()
        if not index.isValid():
            return
        model = self.model()
        row, column = index.row(), index.column() + 1
        if column >= model.columnCount():
            row, column = row + 1, 0
        if row < model.rowCount():
            self.setCurrentIndex(model.index(row, column))

    def paste(self) -> None:
        """Paste the clipboard's block at the current cell."""
        index = self.currentIndex()
        self.grid_model().paste(
            index if index.isValid() else self.model().index(0, 0), QApplication.clipboard().text()
        )

    def copy(self) -> None:
        """Copy the selected cells, or the whole table when nothing is selected."""
        table = self.grid_model().table
        selected = self.selectedIndexes()
        if not selected:
            QApplication.clipboard().setText(table.copy())
            return
        rows = sorted({index.row() for index in selected})
        columns = sorted({index.column() for index in selected})
        QApplication.clipboard().setText(
            table.copy(rows, [table.columns[column].key for column in columns])
        )

    def clear_selection(self) -> None:
        """Empty the selected cells."""
        self.grid_model().clear_cells(
            [(index.row(), index.column()) for index in self.selectedIndexes()]
        )

    def selected_rows(self) -> list[int]:
        """The table rows the selection touches, the spare row left out."""
        count = self.grid_model().table.row_count
        rows = {index.row() for index in self.selectedIndexes()}
        if not rows and self.currentIndex().isValid():
            rows = {self.currentIndex().row()}
        return sorted(row for row in rows if row < count)


class GridWidget(QWidget):
    """A grid with its buttons: what a step that takes a table shows.

    Args:
        table: The table typed into.
        heading: Gives a column its translated heading.
        angle_typing: Gives the convention angles are read in, or ``None``.
        parent: The Qt parent.
    """

    #: The table was edited.
    edited = pyqtSignal()

    def __init__(
        self,
        table: TypedTable,
        heading: Callable[[Column], str],
        angle_typing: Callable[[], AngleTyping | None] = lambda: None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.model = TypedTableModel(table, heading, angle_typing, self)
        self.model.edited.connect(self.edited)
        self.model.edited.connect(self._refresh_buttons)
        self.view = GridView(self)
        self.view.setModel(self.model)

        self.add_button = QPushButton(_tr("Add row"), self)
        self.add_button.setToolTip(
            _tr("Add a row below the current one. It starts with the station and heights above.")
        )
        self.remove_button = QPushButton(_tr("Delete rows"), self)
        self.paste_button = QPushButton(_tr("Paste"), self)
        self.paste_button.setToolTip(
            _tr("Paste a block copied from a spreadsheet, starting at the current cell.")
        )
        self.copy_button = QPushButton(_tr("Copy"), self)
        self.undo_button = QPushButton(_tr("Undo"), self)
        self.redo_button = QPushButton(_tr("Redo"), self)
        self.add_button.clicked.connect(self.add_row)
        self.remove_button.clicked.connect(self.remove_selected_rows)
        self.paste_button.clicked.connect(self.view.paste)
        self.copy_button.clicked.connect(self.view.copy)
        self.undo_button.clicked.connect(self.model.undo)
        self.redo_button.clicked.connect(self.model.redo)

        self.buttons = QHBoxLayout()
        for button in (
            self.add_button,
            self.remove_button,
            self.paste_button,
            self.copy_button,
            self.undo_button,
            self.redo_button,
        ):
            self.buttons.addWidget(button)
        self.buttons.addStretch(1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(self.buttons)
        layout.addWidget(self.view, 1)
        self._refresh_buttons()

    def set_table(self, table: TypedTable) -> None:
        """Show another table: the job was replaced."""
        self.model.set_table(table)
        self._refresh_buttons()

    def reload(self) -> None:
        """Read the table again after a change made elsewhere."""
        self.model.reload()
        self._refresh_buttons()

    def add_row(self) -> None:
        """Add a row below the current one and put the cursor in it."""
        current = self.view.currentIndex()
        count = self.model.table.row_count
        below = min(current.row() + 1, count) if current.isValid() else count
        row = self.model.insert_row(below)
        self.view.setCurrentIndex(self.model.index(row, 0))

    def remove_selected_rows(self) -> None:
        """Delete the rows the selection touches."""
        self.model.remove_rows(self.view.selected_rows())

    def select_row(self, row: int, column: int = 0) -> None:
        """Put the cursor on a cell and bring it into view: a finding was chosen."""
        index = self.model.index(row, column)
        if index.isValid():
            self.view.setCurrentIndex(index)
            self.view.scrollTo(index)
            self.view.setFocus()

    def current_row(self) -> int:
        """The row the cursor is in, or the spare row when it is nowhere."""
        index = self.view.currentIndex()
        return index.row() if index.isValid() else self.model.table.row_count

    def _refresh_buttons(self) -> None:
        self.undo_button.setEnabled(self.model.table.can_undo)
        self.redo_button.setEnabled(self.model.table.can_redo)
