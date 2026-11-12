# SPDX-License-Identifier: GPL-2.0-or-later
"""Total Station ▸ Trigonometric levelling, on the typed field book (FR-011, FR-017).

``specs/15-ui-menu-and-settings.md`` section 7.2. Three steps:

1. **Mode and refraction** -- radial or leap-frog, the heights, the refraction
   coefficient and its uncertainty: the parameters of
   ``geocomp:totalstation_trig_levelling``, as its own dialog shows them, with
   the instrument height hidden in leap-frog mode, where it cancels.
2. **Calculate** -- runs the import, the pre-processing and the levelling.
3. **Results** -- the height differences with their standard deviations, the
   algorithm's report and its table.

**The heights are the algorithm's two parameters, not the field book's.** The
algorithm takes one instrument height and one target height for the whole run,
and does not read those typed in the book. The window says so where they are
set, rather than letting the grid suggest otherwise.
"""

from __future__ import annotations

from typing import Any

from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtWidgets import QLabel, QVBoxLayout, QWidget

from geocomp.core.number_format import localised
from geocomp.gui.windows.totalstation.common import TotalStationWindow
from geocomp.gui.workbench.parameters import ParameterForm
from geocomp.gui.workbench.window import INFO, Note, Step
from geocomp.jobs import total_station as ts
from geocomp.jobs.chains import Chain

__all__ = ["TrigLevellingWindow"]

_TR_CONTEXT = "GeoCompTotalStationWindows"

#: The algorithm's ``MODE`` values, whose order is as permanent as its id.
_RADIAL, _LEAPFROG = 0, 1


def _tr(text: str) -> str:
    return QCoreApplication.translate(_TR_CONTEXT, text)


class TrigLevellingWindow(TotalStationWindow):
    """Height differences from the typed field book's zenith angles and distances."""

    REPORT = ("levelling", "OUTPUT_HTML")
    TABLE = ("levelling", "OUTPUT_CSV")

    def build(self) -> None:
        """The mode and the refraction, then the run and its results."""
        page = QWidget(self)
        self.form = ParameterForm(
            ts.TRIG_LEVELLING, ts.TRIG_LEVELLING_OPTIONS, self._options, parent=page
        )
        self.form.changed.connect(lambda _name="": self._mode_changed())
        note = QLabel(
            _tr(
                "These are the algorithm's own parameters and defaults. It takes one instrument "
                "height and one target height for the whole field book, those set here, and "
                "does not read the heights typed in the book's rows. In leap-frog mode the "
                "instrument height cancels and is not asked."
            ),
            page,
        )
        note.setWordWrap(True)
        layout = QVBoxLayout(page)
        layout.addWidget(self.form)
        layout.addWidget(note)
        layout.addStretch(1)
        self.add_step(Step("mode", _tr("Mode and refraction"), page, notes=self._mode_notes))
        self.add_run_steps(_tr("Calculate"), _tr("Results"))
        self._show_mode()

    def chain(self) -> Chain:
        """The import, the pre-processing, and the height differences."""
        return ts.trig_levelling_chain(self.book)

    def _options(self) -> dict[str, Any]:
        return self.job.parameters(ts.WINDOW_TRIG_LEVELLING)

    def mode(self) -> int:
        """Radial or leap-frog, as the algorithm's ``MODE`` parameter numbers them."""
        return int(self.form.value("MODE") or 0)

    def _mode_changed(self) -> None:
        self._show_mode()
        self.touch()

    def _show_mode(self) -> None:
        self.form.set_shown("INSTRUMENT_HEIGHT", self.mode() != _LEAPFROG)

    def _mode_notes(self) -> list[Note]:
        """Which setups leap-frog reads: those that sighted exactly two points, as typed."""
        if self.mode() != _LEAPFROG:
            return []
        book = self.book
        pairs = [
            (station, book.targets(station))
            for station in book.stations()
            if len(book.targets(station)) == 2
        ]
        if not pairs:
            return [
                Note(
                    INFO,
                    _tr(
                        "No setup of the field book sighted exactly two points, which is what "
                        "leap-frog reads. Choose Radial, or add the second sight."
                    ),
                )
            ]
        return [
            Note(
                INFO,
                _tr("Leap-frog reads %1 setup(s), from the first point sighted to the second: %2.")
                .replace("%1", str(len(pairs)))
                .replace(
                    "%2",
                    "; ".join(f"{station} ({first} → {second})" for station, (first, second) in pairs),
                ),
            )
        ]

    # -- results ---------------------------------------------------------------------

    def figures(self, scalars: dict[str, Any]) -> list[tuple[str, str]]:
        """How many height differences, and the largest uncertainty among them."""
        worst = scalars.get("levelling.WORST_UNCERTAINTY")
        return [
            (_tr("Height differences"), str(scalars.get("levelling.RESULT_COUNT", ""))),
            (
                _tr("Largest standard deviation"),
                "" if worst is None else localised(f"{float(worst) * 1000.0:.1f}") + " mm",
            ),
        ]

    def draw(self) -> None:
        """The known points, for orientation on the map: a height difference has no place of its own."""
        for easting, northing in self.placed_points().values():
            self.sketch.add_point(easting, northing)

    def reload_pages(self) -> None:
        """Another job is the current one: show its options."""
        self.form.reload()
        self._show_mode()
