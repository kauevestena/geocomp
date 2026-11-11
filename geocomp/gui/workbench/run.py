# SPDX-License-Identifier: GPL-2.0-or-later
"""The step that runs a window's algorithms, and shows them running (FR-011).

A button, a progress bar, what the algorithms say while they run, and -- so
that nothing a window does is a mystery -- **the equivalent toolbox run**: the
algorithms it ran, in order, with the parameters it gave each, as lines a user
can paste into the QGIS Python console. A window computes nothing; this is
where that can be checked by anyone, without reading the code.

The page asks for a run and is told how it goes. It does not run anything:
:class:`geocomp.gui.workbench.window.Workbench` owns the runner.
"""

from __future__ import annotations

import json
from pathlib import Path

from qgis.PyQt.QtCore import QCoreApplication, pyqtSignal
from qgis.PyQt.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from geocomp.jobs.chains import ResolvedStep
from geocomp.services.chain_runner import PROBLEM, WARNING, ChainOutcome

__all__ = ["RunPage", "equivalent_run"]

_TR_CONTEXT = "GeoCompWorkbench"


def _tr(text: str) -> str:
    return QCoreApplication.translate(_TR_CONTEXT, text)


def equivalent_run(
    steps: tuple[ResolvedStep, ...], moved: tuple[Path, Path] | None = None
) -> str:
    """The run as Python a user can paste into the QGIS console: one call per algorithm.

    *moved* is the folder the run wrote in and where its files are now, so the
    paths shown are those of the files that exist.
    """
    lines = ["import processing", ""]
    for step in steps:
        parameters = json.dumps(step.parameters, indent=4, ensure_ascii=False, default=str)
        if moved is not None:
            parameters = parameters.replace(
                json.dumps(str(moved[0]))[1:-1], json.dumps(str(moved[1]))[1:-1]
            )
        parameters = (
            parameters.replace(": true", ": True")
            .replace(": false", ": False")
            .replace(": null", ": None")
        )
        lines.append(f'processing.run("{step.algorithm}", {parameters})')
        lines.append("")
    return "\n".join(lines)


class RunPage(QWidget):
    """Calculate, cancel, progress, the log, and the equivalent toolbox run.

    Args:
        action: The label of the button that starts the run, already translated.
        parent: The Qt parent.
    """

    #: The user asked for a run.
    calculate_requested = pyqtSignal()
    #: The user asked the run to stop.
    cancel_requested = pyqtSignal()

    def __init__(self, action: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.calculate_button = QPushButton(action, self)
        self.calculate_button.setObjectName("geocompCalculate")
        self.calculate_button.setDefault(True)
        self.cancel_button = QPushButton(_tr("Cancel"), self)
        self.cancel_button.setEnabled(False)
        self.automatic = QCheckBox(_tr("Calculate again when the data changes"), self)
        self.automatic.setToolTip(
            _tr(
                "Once calculated, the algorithms are run again a moment after the field book or "
                "an option changes, so the results shown are always those of what is typed."
            )
        )
        self.automatic.setChecked(True)
        self.progress = QProgressBar(self)
        self.progress.setRange(0, 100)
        self.status = QLabel(_tr("Not calculated yet."), self)
        self.status.setObjectName("geocompRunStatus")
        self.status.setWordWrap(True)
        self.log = QPlainTextEdit(self)
        self.log.setReadOnly(True)
        self.equivalent = QPlainTextEdit(self)
        self.equivalent.setReadOnly(True)
        self.equivalent.setPlaceholderText(
            _tr("After a run: the algorithms it ran and the parameters it gave them.")
        )
        self.tabs = QTabWidget(self)
        self.tabs.addTab(self.log, _tr("Log"))
        self.tabs.addTab(self.equivalent, _tr("Equivalent toolbox run"))

        self.calculate_button.clicked.connect(self.calculate_requested)
        self.cancel_button.clicked.connect(self.cancel_requested)

        buttons = QHBoxLayout()
        buttons.addWidget(self.calculate_button)
        buttons.addWidget(self.cancel_button)
        buttons.addWidget(self.automatic)
        buttons.addStretch(1)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(buttons)
        layout.addWidget(self.progress)
        layout.addWidget(self.status)
        layout.addWidget(self.tabs, 1)

    def set_ready(self, ready: bool, reason: str = "") -> None:
        """Whether a run can be asked for, and the reason it cannot."""
        self.calculate_button.setEnabled(ready)
        self.calculate_button.setToolTip(reason)

    def started(self) -> None:
        """A run began."""
        self.calculate_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.progress.setValue(0)
        self.log.clear()
        self.status.setText(_tr("Calculating…"))

    def step_started(self, label: str, number: int, count: int) -> None:
        """One of the chain's algorithms is about to run."""
        self.status.setText(
            _tr("Running %1 (%2 of %3)…")
            .replace("%1", label)
            .replace("%2", str(number))
            .replace("%3", str(count))
        )
        self.log.appendPlainText(f"— {label} —")

    def progressed(self, percent: float) -> None:
        """The chain is *percent* done."""
        self.progress.setValue(round(percent))

    def said(self, kind: str, text: str) -> None:
        """An algorithm said a line."""
        mark = {WARNING: "⚠ ", PROBLEM: "✖ "}.get(kind, "")
        self.log.appendPlainText(mark + text)

    def ended(self, outcome: ChainOutcome, moved: tuple[Path, Path] | None = None) -> None:
        """The run ended; say how, in the algorithm's own words when it failed.

        *moved* is the folder the run wrote in and where its files were put.
        """
        self.calculate_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.equivalent.setPlainText(equivalent_run(outcome.steps, moved))
        if outcome.cancelled:
            self.status.setText(_tr("Cancelled. Nothing was changed."))
        elif outcome.succeeded:
            self.progress.setValue(100)
            self.status.setText(_tr("Calculated."))
        else:
            self.status.setText(outcome.error)

    def set_status(self, text: str) -> None:
        """Say where the step stands when nothing is running."""
        self.status.setText(text)
