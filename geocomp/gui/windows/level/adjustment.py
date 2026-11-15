# SPDX-License-Identifier: GPL-2.0-or-later
"""Level ▸ Closures and tolerances, and Levelling network adjustment (FR-011).

``specs/15-ui-menu-and-settings.md`` section 7.2; ``specs/10`` sections 3 and 4.
Both reduce the typed book's lines by equal sights first, as the toolbox chain
does, and then:

* **Closures and tolerances** -- a loop, or a line against a known height
  difference, judged against ``k·√L``: the closure, the tolerance, **Calculate**,
  **Results**. With no *k* there is no verdict, and the window says so.
* **Levelling network adjustment** -- the **Benchmarks** typed as a table (or a
  free network), the **Weighting**, the **Options**, **Calculate**, **Results**.

The benchmarks are written as the algorithm's own list, ``BM1=100.000,
BM2=103.750±0.002``, each height as typed.
"""

from __future__ import annotations

from typing import Any

from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtWidgets import QLabel, QVBoxLayout, QWidget

from geocomp.core.errors import GeoCompError
from geocomp.core.number_format import localised
from geocomp.gui.windows.level.common import LevelWindow
from geocomp.gui.workbench.grid import GridWidget
from geocomp.gui.workbench.parameters import ParameterForm
from geocomp.gui.workbench.window import INFO, Note, Step
from geocomp.jobs import levelling as lv
from geocomp.jobs.chains import Chain
from geocomp.services.messages import message_for

__all__ = ["ClosuresWindow", "LevelNetworkWindow"]

_TR_CONTEXT = "GeoCompLevelWindows"

#: The closure algorithm's ``MODE`` values, whose order is as permanent as its id.
_LOOP, _AGAINST_KNOWN = 0, 1


def _tr(text: str) -> str:
    return QCoreApplication.translate(_TR_CONTEXT, text)


def _millimetres(value: Any) -> str:
    return "" if value is None else localised(f"{float(value) * 1000.0:.1f}") + " mm"


class ClosuresWindow(LevelWindow):
    """Close the book's lines as a loop, or a line against a known difference."""

    REPORT = ("closures", "OUTPUT_HTML")
    TABLE = ("closures", "OUTPUT_CSV")

    def build(self) -> None:
        """The closure and its tolerance, then the run and its results."""
        page = QWidget(self)
        self.form = ParameterForm(
            lv.CLOSURES, lv.CLOSURE_OPTIONS, self._options, parent=page
        )
        self.form.changed.connect(lambda _name="": self._mode_changed())
        note = QLabel(
            _tr(
                "These are the algorithm's own parameters. The lines are reduced by equal "
                "sights first, with the Equal sights window's collimation and limits. With no "
                "tolerance coefficient the misclosure is reported without a verdict."
            ),
            page,
        )
        note.setWordWrap(True)
        layout = QVBoxLayout(page)
        layout.addWidget(self.form)
        layout.addWidget(note)
        layout.addStretch(1)
        self.add_step(Step("closure", _tr("Closure and tolerance"), page))
        self.add_run_steps(_tr("Calculate"), _tr("Results"))
        self._show_mode()

    def chain(self) -> Chain:
        """The import, the reduction of each line, and the closure."""
        return lv.closures_chain(self.book)

    def _options(self) -> dict[str, Any]:
        return self.job.parameters(lv.WINDOW_CLOSURES)

    def _mode_changed(self) -> None:
        self._show_mode()
        self.touch()

    def _show_mode(self) -> None:
        """The known difference is asked only of a line closed against one; the loop's name, of a loop."""
        against = int(self.form.value("MODE") or 0) == _AGAINST_KNOWN
        for name in ("KNOWN_DIFFERENCE", "KNOWN_SIGMA"):
            self.form.set_shown(name, against)
        self.form.set_shown("LOOP_ID", not against)

    def figures(self, scalars: dict[str, Any]) -> list[tuple[str, str]]:
        """The misclosure, what is permitted, and the verdict -- or that there is none."""
        permissible = scalars.get("closures.PERMISSIBLE")
        passed = scalars.get("closures.PASSED")
        judged = passed is not None and int(passed) >= 0
        return [
            (_tr("Misclosure"), _millimetres(scalars.get("closures.MISCLOSURE"))),
            (
                _tr("Permissible"),
                _millimetres(permissible) if judged else _tr("none: no tolerance coefficient"),
            ),
            (
                _tr("Verdict"),
                ""
                if passed is None
                else _tr("Not judged")
                if not judged
                else _tr("Within tolerance")
                if int(passed)
                else _tr("Out of tolerance: see the report"),
            ),
        ]

    def reload_pages(self) -> None:
        """Another job is the current one: show its options."""
        self.form.reload()
        self._show_mode()


class LevelNetworkWindow(LevelWindow):
    """Adjust the book's reduced lines as a height network, held to its benchmarks."""

    REPORT = ("network", "OUTPUT_HTML")
    TABLE = ("network", "OUTPUT_CSV")

    def build(self) -> None:
        """Benchmarks, weighting and options, then the run and its results."""
        self.add_step(
            Step(
                "benchmarks",
                _tr("Benchmarks"),
                self._benchmarks_page(),
                problem=self._benchmarks_problem,
                notes=self._benchmarks_notes,
            )
        )
        self.add_step(Step("weighting", _tr("Weighting"), self._form_page(
            ("WEIGHTING", "SIGMA_PER_KM", "SIGMA_PER_SETUP"),
            _tr(
                "A reduced line carries the uncertainty propagated from its readings. A "
                "coefficient per root kilometre or per root setup replaces it with the model "
                "of the weighting chosen; zero keeps the propagated one."
            ),
            "weighting_form",
        )))
        self.add_step(
            Step(
                "options",
                _tr("Options"),
                self._form_page(
                    (
                        "VARIANCE_COMPONENTS",
                        "CONFIDENCE",
                        "ALPHA",
                        "BETA",
                        "TOLERANCE_COEFFICIENT",
                        "ADJUST_FAILING",
                        "ORTHOMETRIC",
                        "EPOCH",
                    ),
                    _tr(
                        "These are the algorithm's own parameters. The lines are reduced by "
                        "equal sights first, with the Equal sights window's collimation and "
                        "limits."
                    ),
                    "options_form",
                ),
                problem=self._options_problem,
            )
        )
        self.add_run_steps(_tr("Calculate"), _tr("Results"))

    def chain(self) -> Chain:
        """The import, the reduction of each line, and the adjustment."""
        return lv.network_chain(self.book)

    def _options(self) -> dict[str, Any]:
        return self.job.parameters(lv.WINDOW_NETWORK)

    def _form_page(self, names: tuple[str, ...], text: str, attribute: str) -> QWidget:
        page = QWidget(self)
        form = ParameterForm(lv.NETWORK, names, self._options, parent=page)
        form.changed.connect(lambda _name="": self.touch())
        setattr(self, attribute, form)
        note = QLabel(text, page)
        note.setWordWrap(True)
        layout = QVBoxLayout(page)
        layout.addWidget(form)
        layout.addWidget(note)
        layout.addStretch(1)
        return page

    # -- step 1: the benchmarks ------------------------------------------------------

    def _benchmarks_page(self) -> QWidget:
        page = QWidget(self)
        self.free_form = ParameterForm(lv.NETWORK, ("FREE",), self._options, parent=page)
        self.free_form.changed.connect(lambda _name="": self._free_changed())
        self.benchmarks_grid = GridWidget(self.book.benchmarks, self.heading, parent=page)
        self.benchmarks_grid.edited.connect(self.touch)
        note = QLabel(
            _tr(
                "A benchmark with no standard deviation is held exactly; one with a standard "
                "deviation is held with that weight. A free network ignores them, and shows "
                "the readings' own consistency without a datum's errors mixed in."
            ),
            page,
        )
        note.setWordWrap(True)
        layout = QVBoxLayout(page)
        layout.addWidget(self.free_form)
        layout.addWidget(self.benchmarks_grid, 1)
        layout.addWidget(note)
        self._show_free()
        return page

    def is_free(self) -> bool:
        """Whether the network is adjusted free, its benchmarks ignored."""
        return bool(self.free_form.value("FREE"))

    def _free_changed(self) -> None:
        self._show_free()
        self.touch()

    def _show_free(self) -> None:
        self.benchmarks_grid.setEnabled(not self.is_free())

    def _benchmarks_problem(self) -> str:
        if self.is_free():
            return ""
        try:
            known = self.book.known_benchmarks()
        except GeoCompError as error:
            return message_for(error)
        if not known:
            return _tr("Give at least one benchmark's height, or adjust the network free.")
        return ""

    def _benchmarks_notes(self) -> list[Note]:
        notes = [
            self.cell_note(lv.BENCHMARKS, problem) for problem in self.book.benchmarks.problems()
        ]
        if self.is_free():
            return notes
        try:
            known = self.book.known_benchmarks()
        except GeoCompError:
            return notes
        stations = set(self.book.stations())
        absent = [name for name in known if name not in stations]
        if absent:
            notes.append(
                Note(
                    INFO,
                    _tr("Not read in the field book, so holding nothing: %1.").replace(
                        "%1", ", ".join(absent)
                    ),
                )
            )
        return notes

    def note_chosen(self, note: Note) -> None:
        """Go to the benchmark a line of the strip is about."""
        if note.table == lv.BENCHMARKS and note.row is not None:
            table = self.job.tables[lv.BENCHMARKS]
            self.benchmarks_grid.select_row(
                note.row, table.index_of(note.column) if note.column else 0
            )

    # -- step 3: options -------------------------------------------------------------

    def _options_problem(self) -> str:
        if self.options_form.value("ORTHOMETRIC"):
            return _tr(
                "The normal orthometric correction needs each station's latitude, from a layer "
                "of their positions, which this window does not take. Turn it off here, or run "
                "Levelling network adjustment from the toolbox with that layer."
            )
        return ""

    # -- results ---------------------------------------------------------------------

    def figures(self, scalars: dict[str, Any]) -> list[tuple[str, str]]:
        """The global test, the variance factor, the redundancy, outliers and the worst height."""
        variance = scalars.get("network.VARIANCE_FACTOR_APOSTERIORI")
        passed = scalars.get("network.GLOBAL_TEST_PASSED")
        return [
            (
                _tr("Global test"),
                _tr("Not tested: no redundancy")
                if passed is None
                else _tr("Passes")
                if passed
                else _tr("Fails: see the report"),
            ),
            (
                _tr("Variance factor"),
                "" if variance is None else localised(f"{float(variance):.3f}"),
            ),
            (_tr("Degrees of freedom"), str(scalars.get("network.DEGREES_OF_FREEDOM", ""))),
            (_tr("Outlier candidates"), str(scalars.get("network.OUTLIER_COUNT", ""))),
            (
                _tr("Largest height standard deviation"),
                _millimetres(scalars.get("network.WORST_HEIGHT_UNCERTAINTY")),
            ),
        ]

    def reload_pages(self) -> None:
        """Another job is the current one: show its benchmarks and options."""
        self.benchmarks_grid.set_table(self.book.benchmarks)
        for form in (self.free_form, self.weighting_form, self.options_form):
            form.reload()
        self._show_free()

    def refresh(self) -> None:
        """Also re-read the benchmarks."""
        if hasattr(self, "benchmarks_grid"):
            self.benchmarks_grid.reload()
        super().refresh()
