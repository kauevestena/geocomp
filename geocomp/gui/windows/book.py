# SPDX-License-Identifier: GPL-2.0-or-later
"""What every window over a typed field book shares: the book, read once, and its notes.

Every window of a technique works from the same typed field book, and each
needs to know the same thing about it before it can do anything: whether it
can be read. :class:`BookWindow` asks once per state of the job -- with the
importer's own reader and the options the import algorithm would be run with --
and a technique's windows show what it found. The Total Station windows were
the first (P14a); the Level windows (P14c) are the second, and this is what
they have in common.

A computation window does not let its algorithms loose on a book with a row
the importer rejects: the toolbox carries on past a rejected record because a
file is what it is, but a typed row is one keystroke from being right, and a
reduction computed around a missing reading is not what anyone meant.
"""

from __future__ import annotations

from typing import Any

from qgis.core import NULL, QgsApplication
from qgis.PyQt.QtCore import QCoreApplication

from geocomp.core.findings import Finding
from geocomp.gui.workbench.window import BLOCKING, INFO, WARNING, Note, Workbench
from geocomp.jobs.chains import fingerprint
from geocomp.jobs.tables import CellProblem, Column
from geocomp.services.messages import finding_text, message_for

__all__ = ["BookWindow"]

_TR_CONTEXT = "GeoCompWindows"


def _tr(text: str) -> str:
    return QCoreApplication.translate(_TR_CONTEXT, text)


class BookWindow(Workbench):
    """A window over a technique's typed field book.

    A technique says, as class attributes, where its book is typed and how it
    is imported, and implements :meth:`read_book`, :meth:`typed_finding` and
    :meth:`heading`.
    """

    #: Whether the window computes from the field book, and so needs it usable.
    NEEDS_USABLE_BOOK = True
    #: The window the book is typed in.
    FIELD_BOOK_WINDOW = ""
    #: The job's table that is the book.
    FIELD_BOOK_TABLE = "field_book"
    #: The import algorithm, and the options of it the field-book window sets.
    IMPORT_ALGORITHM = ""
    IMPORT_OPTIONS: tuple[str, ...] = ()

    def __init__(self, *arguments: Any, **options: Any) -> None:
        self._checked: tuple[str, Any, str] | None = None
        super().__init__(*arguments, **options)

    # -- what a technique says -----------------------------------------------

    def read_book(self, options: dict[str, Any]) -> tuple[Any, str]:
        """Read the book as the import would with *options*: the check, and why its
        instrument could not be resolved, or ``""``.

        The check has ``problems``, ``findings``, ``refusal``, ``entries`` and
        ``blocking``.
        """
        raise NotImplementedError

    def typed_finding(self, finding: Finding) -> tuple[Finding, int | None]:
        """*finding* numbered as the grid numbers rows, and the grid row it is about, from zero."""
        raise NotImplementedError

    def heading(self, column: Column) -> str:
        """A column's heading in the job's conventions."""
        raise NotImplementedError

    # -- the banner ----------------------------------------------------------

    def banner_action(self) -> None:
        """Bring the field-book window forward."""
        self.open_field_book()

    def open_field_book(self) -> None:
        """Bring the field-book window forward, to put right what it shows."""
        if self._open_window is not None:
            self._open_window(self.FIELD_BOOK_WINDOW)

    # -- the field book, read once per state of the job ----------------------

    def import_option(self, name: str) -> Any:
        """What the import will be run with for *name*: the job's choice, or the algorithm's default."""
        chosen = self.job.parameters(self.FIELD_BOOK_WINDOW).get(name)
        if chosen is not None:
            return chosen
        registered = QgsApplication.processingRegistry().algorithmById(self.IMPORT_ALGORITHM)
        if registered is None:
            return None
        # Made afresh, so the default is Global Settings' of the moment, and
        # held while it is read: the definition belongs to the instance.
        algorithm = registered.create({})
        definition = algorithm.parameterDefinition(name)
        value = None if definition is None else definition.defaultValue()
        return None if value is None or value == NULL else value

    def book_check(self) -> tuple[Any, str]:
        """What reading the field book finds, and why its instrument could not be resolved.

        Read with the importer's own reader and what the import algorithm would
        be given -- so what is shown before a run is what the run will find.
        Kept until the job changes.
        """
        job = self.job
        options = {name: self.import_option(name) for name in self.IMPORT_OPTIONS}
        state = fingerprint(
            [id(job), job.tables[self.FIELD_BOOK_TABLE].revision, dict(job.entry), options]
        )
        if self._checked is not None and self._checked[0] == state:
            return self._checked[1], self._checked[2]
        check, refusal = self.read_book(options)
        self._checked = (state, check, refusal)
        return check, refusal

    def book_problem(self, *, rejected_rows_block: bool) -> str:
        """Why the field book cannot be computed from, in one sentence, or ``""``."""
        check, refusal = self.book_check()
        if refusal:
            return refusal
        if check.entries == 0:
            return _tr(
                "The field book is empty. Type the observations in its grid, or paste them "
                "from a spreadsheet."
            )
        if check.problems:
            return _tr("%1 cell(s) of the field book cannot be read. Correct the cells marked.").replace(
                "%1", str(len(check.problems))
            )
        if check.refusal is not None:
            return message_for(check.refusal)
        if rejected_rows_block and check.blocking:
            return _tr(
                "%1 row(s) of the field book are rejected. Correct them: each is named below."
            ).replace("%1", str(len(check.blocking)))
        return ""

    def precondition(self) -> str:
        """A computation window needs a field book that can be computed from."""
        if not self.NEEDS_USABLE_BOOK:
            return ""
        problem = self.book_problem(rejected_rows_block=True)
        if not problem:
            return ""
        from geocomp.gui.windows.labels import window_label

        return (
            _tr("%1 Put it right in the %2 window.")
            .replace("%1", problem)
            .replace("%2", window_label(self.FIELD_BOOK_WINDOW))
        )

    def book_notes(self) -> list[Note]:
        """Every problem and finding of the field book, each leading to its row."""
        check, _refusal = self.book_check()
        notes = [self.cell_note(self.FIELD_BOOK_TABLE, problem) for problem in check.problems]
        for finding in check.findings:
            typed, row = self.typed_finding(finding)
            notes.append(
                Note(
                    {"blocking": BLOCKING, "warning": WARNING}.get(finding.severity.value, INFO),
                    finding_text(typed),
                    table=self.FIELD_BOOK_TABLE,
                    row=row,
                )
            )
        return notes

    def cell_note(self, table: str, problem: CellProblem) -> Note:
        """A cell that cannot be read, as a line of the strip naming its row and column."""
        column = self.job.tables[table].column(problem.column)
        return Note(
            BLOCKING,
            _tr("Row %1, %2: %3")
            .replace("%1", str(problem.row + 1))
            .replace("%2", self.heading(column))
            .replace("%3", message_for(problem.error)),
            table=table,
            row=problem.row,
            column=problem.column,
        )
