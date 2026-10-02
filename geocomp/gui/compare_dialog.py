# SPDX-License-Identifier: GPL-2.0-or-later
"""The multi-epoch comparison's compatibility check, before the run (FR-831).

``specs/15`` section 3 lists multi-epoch comparison among the few menu items
that open a dialog of their own: the compatibility findings have to be seen
*before* the user commits to an analysis. Two epochs in different frames, or
processed by different engines, or with a station one of them lacks, are
comparable -- but the user should decide to compare them knowing it, not learn
it from a log line afterwards. Two that cannot be compared are refused here,
with the reason, instead of after the parameters have been filled in.

**The dialog does not compare.** It runs the same ``compare`` the algorithm
runs, shows what it found, and hands the two files to
``geocomp:monitoring_compare_epochs`` (ADR-0005): the analysis a user acts on
comes from the algorithm, whichever way it was reached.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from qgis.gui import QgsFileWidget
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from geocomp.core.errors import GeoCompError
from geocomp.core.number_format import localised

__all__ = ["Compatibility", "CompatibilityDialog", "check_compatibility"]

_TR_CONTEXT = "GeoCompCompareDialog"


def _tr(text: str) -> str:
    return QCoreApplication.translate(_TR_CONTEXT, text)


@dataclass
class Compatibility:
    """What the check found: whether the epochs compare, and what to show."""

    comparable: bool
    lines: list[str] = field(default_factory=list)


def check_compatibility(first_path: str, second_path: str) -> Compatibility:
    """Read both solutions and compare them as the algorithm will."""
    from geocomp.algorithms.project.common import read_solution
    from geocomp.core.monitoring import compare
    from geocomp.reports.monitoring import describe_finding
    from geocomp.services.messages import message_for

    try:
        first, second = read_solution(first_path), read_solution(second_path)
        comparison = compare(first, second)
    except GeoCompError as error:
        return Compatibility(False, [_tr("Not comparable: %1").replace("%1", message_for(error))])
    lines = []
    for solution in (first, second):
        lines.append(
            _tr("%1 — epoch %2, %3, datum %4")
            .replace("%1", solution.id)
            .replace("%2", localised(f"{solution.epoch.decimal_year:.4f}"))
            .replace("%3", solution.crs)
            .replace("%4", solution.datum_definition.value)
        )
    lines.append(
        _tr("%1 stations in both epochs.").replace("%1", str(len(comparison.stations)))
    )
    for record in comparison.transformations:
        lines.append(
            _tr("Transformed from %1 to %2, accuracy %3 mm, common to every station.")
            .replace("%1", record.source)
            .replace("%2", record.target)
            .replace("%3", localised(f"{1000.0 * record.accuracy:.1f}"))
        )
    lines.extend(describe_finding(finding.to_dict()) for finding in comparison.findings)
    if comparison.strategies:
        lines.append(
            _tr(
                "The epochs will be taken as independent: the displacements' uncertainty is "
                "overstated if they share reference stations or products."
            )
        )
    return Compatibility(True, lines)


class CompatibilityDialog(QDialog):
    """Choose the two epochs, see what the comparison will find, then proceed."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(_tr("Compare two epochs"))
        self.first = QgsFileWidget(self)
        self.second = QgsFileWidget(self)
        for widget in (self.first, self.second):
            widget.setFilter(_tr("GeoComp solution (*.json)"))
            widget.fileChanged.connect(self.check)
        self.report = QTextBrowser(self)
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        form = QFormLayout()
        form.addRow(_tr("First epoch"), self.first)
        form.addRow(_tr("Second epoch"), self.second)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.report)
        layout.addWidget(self.buttons)
        self.result_of_check = Compatibility(False)
        self.check()

    def check(self, *_args) -> None:
        first, second = self.first.filePath(), self.second.filePath()
        if not first or not second:
            self.result_of_check = Compatibility(False, [_tr("Choose both epochs' solutions.")])
        else:
            self.result_of_check = check_compatibility(first, second)
        self.report.setPlainText("\n".join(self.result_of_check.lines))
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(self.result_of_check.comparable)

    def parameters(self) -> dict[str, str]:
        return {"FIRST": self.first.filePath(), "SECOND": self.second.filePath()}
