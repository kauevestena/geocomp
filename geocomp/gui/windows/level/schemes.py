# SPDX-License-Identifier: GPL-2.0-or-later
"""Level ▸ Equal sights, Equidistant sights and Extreme sights, on the typed book (FR-011).

``specs/15-ui-menu-and-settings.md`` section 7.2; the three schemes of
``specs/10`` section 2. Each window is three steps -- the scheme's options,
**Calculate**, **Results** -- over the one levelling field book:

* **Equal sights** reduces each line as a whole, with the collimation carried
  through the accumulated imbalance; its options are the collimation and the
  sight limits, the level being the field book's.
* **Equidistant sights** combines reciprocal setups, two by two in the book's
  order, from the two banks of an obstacle.
* **Extreme sights** gives each setup's foresights as correlated height
  differences.

Each window says which of the typed setups its scheme will read, as typed:
which pairs, which setups with several foresights. Which of them the
algorithm accepts is the algorithm's to say.
"""

from __future__ import annotations

from typing import Any

from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtWidgets import QLabel, QVBoxLayout, QWidget

from geocomp.core.number_format import localised
from geocomp.gui.windows.level.common import LevelWindow
from geocomp.gui.workbench.parameters import ParameterForm
from geocomp.gui.workbench.window import INFO, Note, Step
from geocomp.jobs import levelling as lv
from geocomp.jobs.chains import Chain

__all__ = ["EqualSightsWindow", "EquidistantSightsWindow", "ExtremeSightsWindow"]

_TR_CONTEXT = "GeoCompLevelWindows"


def _tr(text: str) -> str:
    return QCoreApplication.translate(_TR_CONTEXT, text)


def _millimetres(value: Any) -> str:
    return "" if value is None else localised(f"{float(value) * 1000.0:.1f}") + " mm"


class _SchemeWindow(LevelWindow):
    """One options step over the book, then the run and its results."""

    #: The window, the algorithm and the parameters of it the options step shows.
    WINDOW = ""
    ALGORITHM = ""
    OPTIONS: tuple[str, ...] = ()

    def options_title(self) -> str:
        """The options step's title."""
        return _tr("Options")

    def options_note(self) -> str:
        """What the options step says beneath the form."""
        return ""

    def build(self) -> None:
        """The scheme's options, then the run and its results."""
        page = QWidget(self)
        self.form = ParameterForm(
            self.ALGORITHM,
            self.OPTIONS,
            lambda: self.job.parameters(self.WINDOW),
            parent=page,
        )
        self.form.changed.connect(lambda _name="": self.touch())
        note = QLabel(self.options_note(), page)
        note.setWordWrap(True)
        layout = QVBoxLayout(page)
        layout.addWidget(self.form)
        layout.addWidget(note)
        layout.addStretch(1)
        self.add_step(Step("options", self.options_title(), page, notes=self.scheme_notes))
        self.add_run_steps(_tr("Calculate"), _tr("Results"))

    def scheme_notes(self) -> list[Note]:
        """What the options step's strip says about the book's setups."""
        return []

    def reload_pages(self) -> None:
        """Another job is the current one: show its options."""
        self.form.reload()


class EqualSightsWindow(_SchemeWindow):
    """Reduce each levelling line, the collimation carried through its accumulated imbalance."""

    WINDOW = lv.WINDOW_EQUAL
    ALGORITHM = lv.EQUAL
    OPTIONS = lv.EQUAL_OPTIONS
    REPORT = ("equal", "OUTPUT_HTML")
    TABLE = ("equal", "OUTPUT_CSV")

    def options_title(self) -> str:
        """The collimation and the sight limits."""
        return _tr("Collimation and limits")

    def options_note(self) -> str:
        """Where the level comes from, and what a collimation of zero means."""
        return _tr(
            "These are the algorithm's own parameters. The level is the one chosen in the "
            "Levelling field book window; a collimation given here overrides its profile's, "
            "and zero keeps it."
        )

    def chain(self) -> Chain:
        """The import, then the reduction of each line."""
        return lv.equal_chain(self.book)

    def figures(self, scalars: dict[str, Any]) -> list[tuple[str, str]]:
        """How many lines, the worst imbalance, the largest uncertainty."""
        imbalance = scalars.get("equal.WORST_IMBALANCE")
        return [
            (_tr("Lines reduced"), str(scalars.get("equal.LINE_COUNT", ""))),
            (
                _tr("Largest accumulated imbalance"),
                "" if imbalance is None else localised(f"{float(imbalance):.2f}") + " m",
            ),
            (_tr("Largest standard deviation"), _millimetres(scalars.get("equal.WORST_UNCERTAINTY"))),
        ]


class EquidistantSightsWindow(_SchemeWindow):
    """Combine reciprocal setups across an obstacle, two by two."""

    WINDOW = lv.WINDOW_EQUIDISTANT
    ALGORITHM = lv.EQUIDISTANT
    OPTIONS = lv.EQUIDISTANT_OPTIONS
    REPORT = ("equidistant", "OUTPUT_HTML")
    TABLE = ("equidistant", "OUTPUT_CSV")

    def options_title(self) -> str:
        """The crossing's uncertainty model and tolerance."""
        return _tr("Crossing")

    def options_note(self) -> str:
        """How the setups are paired."""
        return _tr(
            "The setups are paired in the book's order: the first with the second, the third "
            "with the fourth, each pair one setup from each bank. Refraction over water is "
            "why the uncertainty is inflated."
        )

    def chain(self) -> Chain:
        """The import, then the reciprocal crossings."""
        return lv.equidistant_chain(self.book)

    def scheme_notes(self) -> list[Note]:
        """The pairs the book's setups make, as typed."""
        names = list(self.book.setups())
        if len(names) % 2:
            return [
                Note(
                    INFO,
                    _tr(
                        "The book has %1 setup(s): an odd number, so one has no partner from "
                        "the other bank."
                    ).replace("%1", str(len(names))),
                )
            ]
        pairs = [f"{first} ↔ {second}" for first, second in zip(names[0::2], names[1::2], strict=True)]
        return [Note(INFO, _tr("Crossings, as typed: %1.").replace("%1", "; ".join(pairs)))] if pairs else []

    def figures(self, scalars: dict[str, Any]) -> list[tuple[str, str]]:
        """How many crossings, and the largest discrepancy between the two banks."""
        return [
            (_tr("Crossings"), str(scalars.get("equidistant.CROSSING_COUNT", ""))),
            (_tr("Largest discrepancy"), _millimetres(scalars.get("equidistant.WORST_DISCREPANCY"))),
        ]


class ExtremeSightsWindow(_SchemeWindow):
    """Each setup's foresights as height differences correlated through the shared backsight."""

    WINDOW = lv.WINDOW_EXTREME
    ALGORITHM = lv.EXTREME
    OPTIONS = lv.EXTREME_OPTIONS
    REPORT = ("extreme", "OUTPUT_HTML")
    TABLE = ("extreme", "OUTPUT_CSV")

    def options_note(self) -> str:
        """Where the level comes from."""
        return _tr(
            "These are the algorithm's own parameters. The level is the one chosen in the "
            "Levelling field book window."
        )

    def chain(self) -> Chain:
        """The import, then each setup's correlated differences."""
        return lv.extreme_chain(self.book)

    def scheme_notes(self) -> list[Note]:
        """The setups with several foresights, as typed."""
        several = [
            name
            for name, sights in self.book.setups().items()
            if sum(1 for kind, _station in sights if kind in ("FS", "IS")) > 1
        ]
        if not several:
            return [
                Note(
                    INFO,
                    _tr(
                        "No setup of the book has several foresights. Extreme sights is for a "
                        "setup that read several points from one backsight."
                    ),
                )
            ]
        return [
            Note(
                INFO,
                _tr("Setups with several foresights, as typed: %1.").replace("%1", ", ".join(several)),
            )
        ]

    def figures(self, scalars: dict[str, Any]) -> list[tuple[str, str]]:
        """How many setups and differences, and the largest uncertainty."""
        return [
            (_tr("Setups"), str(scalars.get("extreme.SETUP_COUNT", ""))),
            (_tr("Height differences"), str(scalars.get("extreme.DIFFERENCE_COUNT", ""))),
            (_tr("Largest standard deviation"), _millimetres(scalars.get("extreme.WORST_UNCERTAINTY"))),
        ]
