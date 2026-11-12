# SPDX-License-Identifier: GPL-2.0-or-later
"""What a window shows of a run's results (FR-017).

Three things, and all three are the algorithm's:

* the **figures** it returned -- a misclosure, a count, a verdict -- under the
  window's own labels;
* the **report** it wrote, shown as it wrote it: the same HTML a toolbox run
  produces, in the display format and the language of the moment, so there is
  one presentation of a traverse and not a window's and a report's;
* the **table** it wrote, copied to the clipboard as a block a spreadsheet
  pastes -- the route back out of GeoComp that pasting is the route in.

A result made from an earlier field book is not shown as though it were of
this one: the view says it is out of date, and what it shows is greyed.
"""

from __future__ import annotations

import csv
from collections.abc import Callable, Sequence
from pathlib import Path

from qgis.PyQt.QtCore import QCoreApplication, Qt, QUrl
from qgis.PyQt.QtGui import QDesktopServices
from qgis.PyQt.QtWidgets import (
    QApplication,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

__all__ = ["ResultsView"]

_TR_CONTEXT = "GeoCompWorkbench"


def _tr(text: str) -> str:
    return QCoreApplication.translate(_TR_CONTEXT, text)


class ResultsView(QWidget):
    """The figures, the report and the table of a window's last run.

    Args:
        parent: The Qt parent.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._report: Path | None = None
        self._table: Path | None = None
        self._figures: list[tuple[QLabel, QLabel]] = []

        self.notice = QLabel(self)
        self.notice.setObjectName("geocompResultsNotice")
        self.notice.setWordWrap(True)
        self._summary = QFormLayout()
        self.report = QTextBrowser(self)
        self.report.setObjectName("geocompResultsReport")
        self.report.setOpenExternalLinks(True)

        self.open_button = QPushButton(_tr("Open report"), self)
        self.open_button.setToolTip(_tr("Open the report in your browser, to print or keep."))
        self.copy_button = QPushButton(_tr("Copy table"), self)
        self.copy_button.setToolTip(
            _tr("Copy the results table, with every digit, to paste into a spreadsheet.")
        )
        self.folder_button = QPushButton(_tr("Open results folder"), self)
        self.open_button.clicked.connect(self.open_report)
        self.copy_button.clicked.connect(self.copy_table)
        self.folder_button.clicked.connect(self.open_folder)
        self.actions = QHBoxLayout()
        for button in (self.open_button, self.copy_button, self.folder_button):
            self.actions.addWidget(button)
        self.actions.addStretch(1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.notice)
        layout.addLayout(self._summary)
        layout.addWidget(self.report, 1)
        layout.addLayout(self.actions)
        self.clear(_tr("Not calculated yet."))

    def add_action(self, label: str, run: Callable[[], None], tip: str = "") -> QPushButton:
        """Add a button of the window's own beside the standard ones."""
        button = QPushButton(label, self)
        button.setToolTip(tip)
        button.clicked.connect(lambda _checked=False: run())
        self.actions.insertWidget(self.actions.count() - 1, button)
        return button

    # -- showing -----------------------------------------------------------

    def clear(self, notice: str) -> None:
        """Show nothing, and say why: not calculated yet, or the results are gone."""
        self._report = self._table = None
        self._set_figures(())
        self.report.clear()
        self.notice.setText(notice)
        self.notice.setVisible(True)
        self._enable(False)

    def show_results(
        self,
        figures: Sequence[tuple[str, str]],
        *,
        report: Path | None,
        table: Path | None = None,
        stale: bool = False,
    ) -> None:
        """Show a run's figures, report and table.

        Args:
            figures: Each figure as its label and its value, both ready to read.
            report: The HTML report the algorithm wrote.
            table: The CSV the algorithm wrote, for *Copy table*.
            stale: The results are of an earlier state of the job. They are
                shown greyed, under a notice that says so.
        """
        self._report, self._table = report, table
        self._set_figures(figures)
        if report is not None and report.is_file():
            self.report.setHtml(report.read_text(encoding="utf-8"))
        else:
            self.report.clear()
        self.notice.setVisible(stale)
        if stale:
            self.notice.setText(
                _tr(
                    "These results are of an earlier state of the job: the field book or an "
                    "option has changed since. Calculate again."
                )
            )
        self.report.setEnabled(not stale)
        for label, value in self._figures:
            label.setEnabled(not stale)
            value.setEnabled(not stale)
        self._enable(True)

    def figures(self) -> dict[str, str]:
        """The figures shown, by label. What a test, or a screen reader, reads."""
        return {label.text(): value.text() for label, value in self._figures}

    def _set_figures(self, figures: Sequence[tuple[str, str]]) -> None:
        while self._summary.rowCount():
            self._summary.removeRow(0)
        self._figures = []
        for name, text in figures:
            label, value = QLabel(name, self), QLabel(text, self)
            value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self._summary.addRow(label, value)
            self._figures.append((label, value))

    def _enable(self, shown: bool) -> None:
        self.open_button.setEnabled(shown and self._report is not None)
        self.copy_button.setEnabled(shown and self._table is not None)
        self.folder_button.setEnabled(shown and self._report is not None)

    # -- the buttons -------------------------------------------------------

    def open_report(self) -> None:
        """Open the report in the system's browser."""
        if self._report is not None:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self._report)))

    def open_folder(self) -> None:
        """Open the folder the results are in."""
        if self._report is not None:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self._report.parent)))

    def table_block(self) -> str:
        """The results table as a block a spreadsheet pastes: tabs and lines."""
        if self._table is None or not self._table.is_file():
            return ""
        with open(self._table, encoding="utf-8", newline="") as handle:
            return "\n".join("\t".join(row) for row in csv.reader(handle))

    def copy_table(self) -> None:
        """Copy the results table to the clipboard."""
        QApplication.clipboard().setText(self.table_block())
