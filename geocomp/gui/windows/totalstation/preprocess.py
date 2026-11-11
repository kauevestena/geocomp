# SPDX-License-Identifier: GPL-2.0-or-later
"""Total Station ▸ Generalised pre-processing, on the typed field book (FR-011).

``specs/15-ui-menu-and-settings.md`` section 7.2. Three steps:

1. **Conditions and tolerances** -- the atmosphere the distances were measured
   in and the tolerances the face pairs are held to: the parameters of
   ``geocomp:totalstation_preprocess``, as its own dialog shows them.
2. **Calculate** -- runs the import and then the pre-processing of what it read.
3. **Results** -- the pointings reduced and the report the algorithm wrote,
   with each face pair's diagnostics and every finding.

Nothing is asked about the observations: they are the job's field book.
"""

from __future__ import annotations

from typing import Any

from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtWidgets import QLabel, QVBoxLayout, QWidget

from geocomp.gui.windows.totalstation.common import TotalStationWindow
from geocomp.gui.workbench.parameters import ParameterForm
from geocomp.gui.workbench.window import Step
from geocomp.jobs import total_station as ts
from geocomp.jobs.chains import Chain

__all__ = ["PreprocessWindow"]

_TR_CONTEXT = "GeoCompTotalStationWindows"


def _tr(text: str) -> str:
    return QCoreApplication.translate(_TR_CONTEXT, text)


class PreprocessWindow(TotalStationWindow):
    """Reduce the typed field book: face pairs, corrections, and what does not agree."""

    REPORT = ("preprocess", "OUTPUT_HTML")
    TABLE = ("preprocess", "OUTPUT_CSV")

    def build(self) -> None:
        """The conditions, then the run and its results."""
        page = QWidget(self)
        self.form = ParameterForm(
            ts.PREPROCESS,
            ts.PREPROCESS_OPTIONS,
            lambda: self.job.parameters(ts.WINDOW_PREPROCESS),
            parent=page,
        )
        self.form.changed.connect(lambda _name="": self.touch())
        note = QLabel(
            _tr(
                "These are the algorithm's own parameters and defaults. The observations are "
                "the job's field book; the instrument is the one chosen in the Field book window."
            ),
            page,
        )
        note.setWordWrap(True)
        layout = QVBoxLayout(page)
        layout.addWidget(self.form)
        layout.addWidget(note)
        layout.addStretch(1)
        self.add_step(Step("conditions", _tr("Conditions and tolerances"), page))
        self.add_run_steps(_tr("Calculate"), _tr("Results"))

    def chain(self) -> Chain:
        """The import, then the pre-processing of what it read."""
        return ts.preprocess_chain(self.book)

    def figures(self, scalars: dict[str, Any]) -> list[tuple[str, str]]:
        """What the pre-processing counted."""
        return [
            (_tr("Pointings reduced"), str(scalars.get("preprocess.POINTING_COUNT", ""))),
            (_tr("Usable pointings"), str(scalars.get("preprocess.USABLE_COUNT", ""))),
            (_tr("Blocking findings"), str(scalars.get("preprocess.BLOCKING_COUNT", ""))),
        ]

    def reload_pages(self) -> None:
        """Another job is the current one: show its options."""
        self.form.reload()
