# SPDX-License-Identifier: GPL-2.0-or-later
"""A table of typed cells: the grid a field book is written into (FR-012).

**A cell holds what was typed.** Not a number: the text, exactly, as a paper
field book holds its ink. It is read when it is needed, in the job's
conventions, and a cell that cannot be read is a *problem the table reports*
rather than a refusal to accept the keystroke -- a user half-way through a row
has typed nothing wrong yet. So the grid never rewrites what a user sees, a
value typed to four decimals is still four decimals when the job is reopened,
and a change of convention cannot silently move a decimal point.

Every edit can be undone. A grid without undo is punishing -- a paste one row
too low overwrites a station -- and a field book is small enough that keeping
the table as it was costs nothing, which is the reasoning
:class:`~geocomp.core.preanalysis.session.DesignSession` already rests on.

A block copied from a spreadsheet is pasted as it comes -- rows on lines, cells
between tabs -- and a block copied from here pastes into one (FR-014).
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from enum import Enum

from geocomp.core.errors import GeoCompError, ValidationError
from geocomp.jobs.angles import AngleTyping, parse_typed_angle

__all__ = [
    "CellKind",
    "CellProblem",
    "Column",
    "TypedTable",
    "format_number",
    "parse_integer",
    "parse_number",
]

#: How many edits back a table remembers.
_UNDO_DEPTH = 200


class CellKind(Enum):
    """What a column's cells are read as."""

    NAME = "name"
    TEXT = "text"
    CHOICE = "choice"
    ANGLE = "angle"
    NUMBER = "number"
    INTEGER = "integer"


@dataclass(frozen=True)
class Column:
    """One column of a typed table.

    Attributes:
        key: Stable and English. A job file stores it, so renaming one breaks
            every job saved with it.
        kind: What the cells are read as.
        choices: For :attr:`CellKind.CHOICE`, each accepted value with the
            spellings typed for it: ``{"PD": ("PD", "1", "F1")}``.
        carries: A new row starts with the value of the row above. The occupied
            station and its instrument height are typed once per setup on
            paper, and should be here.
    """

    key: str
    kind: CellKind = CellKind.TEXT
    choices: tuple[tuple[str, tuple[str, ...]], ...] = ()
    carries: bool = False

    def choice(self, text: str) -> str:
        """The accepted value *text* spells, compared without regard to case.

        Raises:
            ValidationError: ``typed_choice_unknown`` for text that spells none.
        """
        typed = text.strip().upper()
        for value, spellings in self.choices:
            if typed in {spelling.upper() for spelling in (value, *spellings)}:
                return value
        raise ValidationError(
            "typed_choice_unknown", received=text, expected=[value for value, _ in self.choices]
        )


@dataclass(frozen=True)
class CellProblem:
    """A cell that cannot be read, and why.

    Returned, not raised, so every bad cell of a table is reported in one pass
    (FR-166's rule for an import, kept for typing).

    Attributes:
        row: The table's row, counted from zero.
        column: The column's key.
        error: The refusal, which the presentation layer words.
    """

    row: int
    column: str
    error: GeoCompError


def parse_number(text: str) -> float:
    """The number *text* types, with a point or a comma for its decimal mark.

    Raises:
        ValidationError: ``typed_number_unreadable``.
    """
    cleaned = text.strip().replace(",", ".")
    try:
        value = float(cleaned)
    except ValueError:
        raise ValidationError("typed_number_unreadable", received=text) from None
    if value != value or value in (float("inf"), float("-inf")):
        raise ValidationError("typed_number_unreadable", received=text)
    return value


def parse_integer(text: str) -> int:
    """The whole number *text* types.

    Raises:
        ValidationError: ``typed_integer_unreadable``.
    """
    try:
        return int(text.strip())
    except ValueError:
        raise ValidationError("typed_integer_unreadable", received=text) from None


def format_number(value: float, decimals: int = 4) -> str:
    """*value* as GeoComp fills a cell with it: a decimal point, and no exponent."""
    return f"{value:.{decimals}f}"


class TypedTable:
    """Rows of typed cells under fixed columns, edited with undo.

    Args:
        columns: The columns, in order.
        rows: The cells to start with. A short row is filled out with empty
            cells and a long one cut, so a table read from an older job file
            still fits its columns.
    """

    def __init__(self, columns: Sequence[Column], rows: Iterable[Sequence[str]] = ()) -> None:
        self.columns: tuple[Column, ...] = tuple(columns)
        self._keys = [column.key for column in self.columns]
        self._rows: list[list[str]] = [self._fitted(row) for row in rows]
        self._undo: list[list[list[str]]] = []
        self._redo: list[list[list[str]]] = []
        #: Counts every change, so a window can tell whether what it showed is still what is there.
        self.revision = 0

    # -- reading ---------------------------------------------------------

    @property
    def row_count(self) -> int:
        """How many rows the table has, blank ones included."""
        return len(self._rows)

    def column(self, key: str) -> Column:
        """The column of that key."""
        return self.columns[self._keys.index(key)]

    def index_of(self, key: str) -> int:
        """Where the column of that key stands, counted from zero."""
        return self._keys.index(key)

    def cell(self, row: int, key: str) -> str:
        """What was typed in the cell, stripped of the spaces around it."""
        return self._rows[row][self._keys.index(key)].strip()

    def row(self, row: int) -> tuple[str, ...]:
        """One row's cells, as typed."""
        return tuple(self._rows[row])

    def is_blank(self, row: int) -> bool:
        """Whether nothing was typed anywhere in the row."""
        return not any(cell.strip() for cell in self._rows[row])

    def filled_rows(self) -> tuple[int, ...]:
        """The rows that hold something, in order."""
        return tuple(index for index in range(len(self._rows)) if not self.is_blank(index))

    def to_list(self) -> list[list[str]]:
        """Every row, as a job file stores the table."""
        return [list(row) for row in self._rows]

    # -- editing ---------------------------------------------------------

    def set_cell(self, row: int, key: str, text: str) -> None:
        """Type *text* into a cell. Nothing is recorded when it is what was there."""
        column = self._keys.index(key)
        if self._rows[row][column] == text:
            return
        self._checkpoint()
        self._rows[row][column] = text

    def insert_row(self, index: int | None = None) -> int:
        """Add a row at *index*, or at the end, and return where it went.

        Its carrying columns start with the value of the row above.
        """
        position = len(self._rows) if index is None else max(0, min(index, len(self._rows)))
        above = self._rows[position - 1] if position > 0 else None
        self._checkpoint()
        self._rows.insert(
            position,
            [
                above[number] if above is not None and column.carries else ""
                for number, column in enumerate(self.columns)
            ],
        )
        return position

    def remove_rows(self, rows: Iterable[int]) -> None:
        """Take rows out, whichever order they are named in."""
        doomed = sorted({row for row in rows if 0 <= row < len(self._rows)}, reverse=True)
        if not doomed:
            return
        self._checkpoint()
        for row in doomed:
            del self._rows[row]

    def clear_cells(self, cells: Iterable[tuple[int, str]]) -> None:
        """Empty each ``(row, column key)`` named, as one edit."""
        targets = [(row, self._keys.index(key)) for row, key in cells if 0 <= row < len(self._rows)]
        if not any(self._rows[row][column] for row, column in targets):
            return
        self._checkpoint()
        for row, column in targets:
            self._rows[row][column] = ""

    def paste(self, row: int, key: str, block: str) -> tuple[int, int]:
        """Paste a block copied from a spreadsheet, its top-left cell at ``(row, key)``.

        Rows are lines and cells stand between tabs. The table grows to take
        the block's rows; cells that would fall to the right of the last
        column are left out. Returns how many rows and columns were written.
        """
        lines = [line.rstrip("\r") for line in block.split("\n")]
        while lines and not lines[-1].strip():
            lines.pop()
        if not lines:
            return 0, 0
        first = self._keys.index(key)
        room = len(self.columns) - first
        cells = [line.split("\t")[:room] for line in lines]
        self._checkpoint()
        while len(self._rows) < row + len(cells):
            self._rows.append([""] * len(self.columns))
        for offset, values in enumerate(cells):
            for column, value in enumerate(values, start=first):
                self._rows[row + offset][column] = value.strip()
        return len(cells), max(len(values) for values in cells)

    def copy(self, rows: Iterable[int] | None = None, keys: Sequence[str] | None = None) -> str:
        """The rows named, or all of them, as a block a spreadsheet pastes: tabs and lines."""
        chosen = range(len(self._rows)) if rows is None else sorted(set(rows))
        columns = range(len(self.columns)) if keys is None else [self._keys.index(key) for key in keys]
        return "\n".join(
            "\t".join(self._rows[row][column] for column in columns)
            for row in chosen
            if 0 <= row < len(self._rows)
        )

    def replace(self, rows: Iterable[Sequence[str]]) -> None:
        """Put other rows in the table's place, as one edit that can be undone."""
        self._checkpoint()
        self._rows = [self._fitted(row) for row in rows]

    # -- undo ------------------------------------------------------------

    @property
    def can_undo(self) -> bool:
        """Whether there is an edit to undo."""
        return bool(self._undo)

    @property
    def can_redo(self) -> bool:
        """Whether an undone edit can be made again."""
        return bool(self._redo)

    def undo(self) -> bool:
        """Undo the last edit. Returns whether there was one."""
        if not self._undo:
            return False
        self._redo.append(self.to_list())
        self._rows = self._undo.pop()
        self.revision += 1
        return True

    def redo(self) -> bool:
        """Make the last undone edit again. Returns whether there was one."""
        if not self._redo:
            return False
        self._undo.append(self.to_list())
        self._rows = self._redo.pop()
        self.revision += 1
        return True

    def _checkpoint(self) -> None:
        self._undo.append(self.to_list())
        del self._undo[:-_UNDO_DEPTH]
        # A new edit ends the redo branch, as it does in the design session.
        self._redo.clear()
        self.revision += 1

    # -- checking --------------------------------------------------------

    def problems(self, angle_typing: AngleTyping | None = None) -> tuple[CellProblem, ...]:
        """Every cell of a filled row that cannot be read as its column's kind.

        An empty cell is not one: whether a value is *needed* depends on what
        the row is for, which the technique's own reader decides and reports.
        """
        found: list[CellProblem] = []
        for row in self.filled_rows():
            for number, column in enumerate(self.columns):
                text = self._rows[row][number].strip()
                if not text:
                    continue
                try:
                    self._read(column, text, angle_typing)
                except GeoCompError as error:
                    found.append(CellProblem(row=row, column=column.key, error=error))
        return tuple(found)

    @staticmethod
    def _read(column: Column, text: str, angle_typing: AngleTyping | None) -> object:
        if column.kind is CellKind.NUMBER:
            return parse_number(text)
        if column.kind is CellKind.INTEGER:
            return parse_integer(text)
        if column.kind is CellKind.CHOICE:
            return column.choice(text)
        if column.kind is CellKind.ANGLE and angle_typing is not None:
            return parse_typed_angle(text, angle_typing)
        return text

    def _fitted(self, row: Sequence[str]) -> list[str]:
        cells = [str(cell) for cell in row][: len(self.columns)]
        return cells + [""] * (len(self.columns) - len(cells))
