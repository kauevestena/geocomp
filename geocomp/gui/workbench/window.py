# SPDX-License-Identifier: GPL-2.0-or-later
"""The guided workbench: the frame every interactive menu window is built in (FR-010).

``specs/15-ui-menu-and-settings.md`` section 7.1. A window that is not modal --
the map stays usable beside it -- with:

* a **job bar**: the job being worked on, New, Open, Save;
* a numbered **list of steps** on the left. A step unlocks when the ones before
  it are complete, and any unlocked step can be gone back to: a guide, not a
  wizard that forgets what it was told;
* the current step's **page**;
* a **strip** beneath it that says what is wrong with what is typed, each line
  leading to the cell it is about;
* **Back** and **Next**.

**A window computes nothing** (ADR-0010). What it can do with what was typed is
:meth:`Workbench.chain`: declare the algorithms to run on it. The frame runs
them in the background, keeps what they wrote beside the job, and shows a
result only as the result of the inputs that produced it -- a closure computed
from an earlier field book is marked out of date, never shown as current.

A subclass adds its steps in :meth:`Workbench.build` and says which chain it
runs, which figures it shows and what it draws on the map. Everything else --
the job, the run, the results folder, the canvas hand-back -- is here, once.
"""

from __future__ import annotations

import contextlib
import math
import shutil
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from qgis.core import QgsApplication, QgsProcessingUtils
from qgis.gui import QgsMapCanvas
from qgis.PyQt.QtCore import QCoreApplication, Qt, QTimer, pyqtSignal
from qgis.PyQt.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from geocomp.core.errors import GeoCompError
from geocomp.gui.workbench.results import ResultsView
from geocomp.gui.workbench.run import RunPage
from geocomp.gui.workbench.sketch import CanvasSketch, PointPickTool
from geocomp.jobs.chains import Chain
from geocomp.jobs.document import JOB_SUFFIX, Job
from geocomp.registry import WindowSpec
from geocomp.services.chain_runner import ChainOutcome, ChainRunner
from geocomp.services.jobs_service import JobsService
from geocomp.services.messages import message_for

__all__ = ["BLOCKING", "INFO", "WARNING", "Note", "Step", "Workbench"]

_TR_CONTEXT = "GeoCompWorkbench"

#: How much a note matters, on the scale findings use.
BLOCKING = "blocking"
WARNING = "warning"
INFO = "info"

#: What a step is for. An input step is complete when what it asks is given; the
#: run step when a current result exists; the results step shows one.
INPUT = "input"
RUN = "run"
RESULTS = "results"

#: The states a step is shown in.
LOCKED = "locked"
READY = "ready"
DONE = "done"
STALE = "stale"

_MARKS = {DONE: "  ✓", STALE: "  ↻"}
_NOTE_MARKS = {BLOCKING: "✖  ", WARNING: "⚠  ", INFO: ""}

#: How long after the last edit a window looks again at what it shows, and how
#: long after that it calculates again by itself.
_REFRESH_MS = 150
_RECALCULATE_MS = 1200


def _tr(text: str) -> str:
    return QCoreApplication.translate(_TR_CONTEXT, text)


@dataclass(frozen=True)
class Note:
    """One line of the strip: something wrong, or worth knowing, about what is typed.

    Attributes:
        severity: :data:`BLOCKING`, :data:`WARNING` or :data:`INFO`.
        text: The translated sentence.
        table: The job's table it is about, when it is about a cell or a row.
        row: The row, counted from zero.
        column: The column's key.
    """

    severity: str
    text: str
    table: str = ""
    row: int | None = None
    column: str = ""


@dataclass
class Step:
    """One step of a window.

    Attributes:
        key: Stable and English; a job file may name it.
        title: Translated.
        page: The widget the step shows.
        problem: Says why the step is not complete, or ``""`` when it is. The
            steps after an incomplete input step stay locked.
        notes: What the strip shows while the step is the current one.
        role: :data:`INPUT`, :data:`RUN` or :data:`RESULTS`.
    """

    key: str
    title: str
    page: QWidget
    problem: Callable[[], str] = lambda: ""
    notes: Callable[[], Sequence[Note]] = lambda: ()
    role: str = INPUT
    state: str = field(default=READY, init=False)


class Workbench(QDialog):
    """A guided, non-modal window over one technique's job.

    Args:
        spec: The window's declaration in the registry: its name, its
            technique, and the only algorithms it may run.
        jobs: Holds the technique's current job, shared with its other windows.
        canvas: The map canvas, or ``None`` where there is none.
        parent: The Qt parent, the QGIS main window.
        open_window: Opens another menu window by name: *Traverse* sends the
            user to *Field book* when the book has a problem.
        is_last_open: Whether this is the only open window of its technique,
            which is when closing it asks about unsaved changes.
    """

    #: The window closed: its name.
    closed = pyqtSignal(str)

    def __init__(
        self,
        spec: WindowSpec,
        jobs: JobsService,
        canvas: QgsMapCanvas | None = None,
        parent: QWidget | None = None,
        *,
        open_window: Callable[[str], None] | None = None,
        is_last_open: Callable[[], bool] = lambda: True,
    ) -> None:
        super().__init__(parent)
        self.spec = spec
        self.jobs = jobs
        self.canvas = canvas
        self.steps: list[Step] = []
        self.runner = ChainRunner(spec.algorithm_ids, self)
        self.sketch = CanvasSketch(canvas, lambda: self.job.crs)
        self.last_outcome: ChainOutcome | None = None
        self._open_window = open_window
        self._is_last_open = is_last_open
        self._running: tuple[Chain, Path] | None = None
        #: The inputs of the last run that failed: not run again by itself, or a
        #: failing chain would be retried every time the timer fired.
        self._failed: str | None = None
        self._shown_result: tuple[Any, ...] | None = None
        self._folder_seen: Path | None = None
        self._pick_tool: PointPickTool | None = None
        self._previous_tool = None
        self._picked: Callable[[float, float], None] | None = None
        self._closing = False

        self.setObjectName(f"geocompWindow_{spec.name}")
        self.setModal(False)
        self.setWindowModality(Qt.WindowModality.NonModal)
        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowType.WindowMinimizeButtonHint
            | Qt.WindowType.WindowMaximizeButtonHint
        )
        self.resize(1000, 660)

        self.run_page = RunPage(self.action_label(), self)
        self.results = ResultsView(self)
        self._build_frame()
        self.build()

        self._refresh_timer = QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.setInterval(_REFRESH_MS)
        self._refresh_timer.timeout.connect(self.refresh)
        self._recalculate_timer = QTimer(self)
        self._recalculate_timer.setSingleShot(True)
        self._recalculate_timer.setInterval(_RECALCULATE_MS)
        self._recalculate_timer.timeout.connect(self._recalculate)

        self.run_page.calculate_requested.connect(self.calculate)
        self.run_page.cancel_requested.connect(self.runner.cancel)
        self.runner.step_started.connect(self._step_started)
        self.runner.progressed.connect(self.run_page.progressed)
        self.runner.said.connect(self.run_page.said)
        self.runner.finished.connect(self._run_finished)
        self.jobs.edited.connect(self._job_edited)
        self.jobs.replaced.connect(self._job_replaced)
        self.jobs.saved.connect(self._job_saved)

        self.go_to(0)
        self.refresh()

    # -- what a subclass says -------------------------------------------------

    def build(self) -> None:
        """Add the window's steps, with :meth:`add_step`. A subclass overrides this."""

    def chain(self) -> Chain:
        """The algorithms to run on what is typed, declared as data.

        Raises:
            GeoCompError: when what is typed cannot be run on yet. The window
                shows the refusal in its words.
        """
        raise NotImplementedError

    def precondition(self) -> str:
        """Why the window cannot calculate for a reason outside its own steps, or ``""``.

        A computation window says here that the field book it works from has a
        problem, which is put right in another window.
        """
        return ""

    def figures(self, scalars: dict[str, Any]) -> list[tuple[str, str]]:
        """The figures to show of a run, from what its algorithms returned.

        *scalars* is keyed ``step.NAME``. Each figure is a translated label
        and a value ready to read.
        """
        del scalars
        return []

    #: The run's report and table, as ``(step key, output name)``.
    REPORT: tuple[str, str] = ("", "OUTPUT_HTML")
    TABLE: tuple[str, str] | None = None

    def draw(self) -> None:
        """Draw the window's sketch on the map. Called after the sketch is cleared."""

    def reload_pages(self) -> None:
        """Point the pages at the job again: another became the current one."""

    def note_chosen(self, note: Note) -> None:
        """The user chose a line of the strip: take them to what it is about."""

    def after_run(self, outcome: ChainOutcome) -> None:
        """A run just succeeded and is recorded: a subclass may act on what it wrote."""

    def action_label(self) -> str:
        """The translated label of the button that runs the chain."""
        return _tr("Calculate")

    def banner_action_label(self) -> str:
        """The label of the button beside :meth:`precondition`'s banner, or ``""`` for none."""
        return ""

    def banner_action(self) -> None:
        """What the banner's button does: take the user to where the problem is put right."""

    # -- the job ---------------------------------------------------------------

    @property
    def technique(self) -> str:
        """The technique whose job the window works on."""
        return self.spec.technique

    @property
    def job(self) -> Job:
        """The technique's current job."""
        return self.jobs.job(self.technique)

    def touch(self) -> None:
        """Say the job was edited here, so every window of the technique looks again."""
        self.jobs.touch(self.technique)

    def results_folder(self) -> Path:
        """Where this window's results are written.

        Beside a saved job, in ``<name>_results/<window>``; for a job not yet
        saved, in the session's temporary folder, from which they are carried
        over when it is.
        """
        saved = self.job.results_directory
        if saved is not None:
            return saved / self.spec.name
        return Path(QgsProcessingUtils.tempFolder()) / "geocomp_jobs" / self.technique / self.spec.name

    # -- the frame --------------------------------------------------------------

    def _build_frame(self) -> None:
        self._job_label = QLabel(self)
        self._job_label.setObjectName("geocompJobLabel")
        self._job_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        job_bar = QHBoxLayout()
        job_bar.addWidget(self._job_label, 1)
        for label, tip, action in (
            (_tr("New job"), _tr("Start an empty job."), self.new_job),
            (_tr("Open job…"), _tr("Open a saved job file."), self.open_job),
            (_tr("Save"), _tr("Save the job to its file."), self.save_job),
            (_tr("Save as…"), _tr("Save the job to another file."), self.save_job_as),
        ):
            button = QPushButton(label, self)
            button.setToolTip(tip)
            button.setAutoDefault(False)
            button.clicked.connect(lambda _checked=False, action=action: action())
            job_bar.addWidget(button)

        self.step_list = QListWidget(self)
        self.step_list.setObjectName("geocompSteps")
        self.step_list.setMaximumWidth(250)
        self.step_list.currentRowChanged.connect(self._step_chosen)

        self._title = QLabel(self)
        font = self._title.font()
        font.setBold(True)
        font.setPointSizeF(font.pointSizeF() * 1.2)
        self._title.setFont(font)
        self.banner = QLabel(self)
        self.banner.setObjectName("geocompBanner")
        self.banner.setWordWrap(True)
        self.banner.setVisible(False)
        self.banner_button = QPushButton(self.banner_action_label(), self)
        self.banner_button.setVisible(False)
        self.banner_button.setAutoDefault(False)
        self.banner_button.clicked.connect(lambda _checked=False: self.banner_action())
        banner_row = QHBoxLayout()
        banner_row.addWidget(self.banner, 1)
        banner_row.addWidget(self.banner_button)
        self.pages = QStackedWidget(self)
        self.strip = QListWidget(self)
        self.strip.setObjectName("geocompNotes")
        self.strip.setMaximumHeight(120)
        self.strip.itemClicked.connect(self._note_clicked)

        right = QWidget(self)
        column = QVBoxLayout(right)
        column.setContentsMargins(0, 0, 0, 0)
        column.addWidget(self._title)
        column.addLayout(banner_row)
        column.addWidget(self.pages, 1)
        column.addWidget(self.strip)

        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.addWidget(self.step_list)
        splitter.addWidget(right)
        splitter.setStretchFactor(1, 1)

        self.back_button = QPushButton(_tr("Back"), self)
        self.next_button = QPushButton(_tr("Next"), self)
        self.close_button = QPushButton(_tr("Close"), self)
        for button in (self.back_button, self.next_button, self.close_button):
            button.setAutoDefault(False)
        self.back_button.clicked.connect(lambda _checked=False: self.go_to(self.current - 1))
        self.next_button.clicked.connect(lambda _checked=False: self.go_to(self.current + 1))
        self.close_button.clicked.connect(lambda _checked=False: self.close())
        navigation = QHBoxLayout()
        navigation.addStretch(1)
        navigation.addWidget(self.back_button)
        navigation.addWidget(self.next_button)
        navigation.addWidget(self.close_button)

        layout = QVBoxLayout(self)
        layout.addLayout(job_bar)
        layout.addWidget(splitter, 1)
        layout.addLayout(navigation)

    def add_step(self, step: Step) -> Step:
        """Add a step after those already there."""
        self.steps.append(step)
        self.pages.addWidget(step.page)
        self.step_list.addItem("")
        return step

    def add_run_steps(self, run_title: str, results_title: str) -> None:
        """Add the two steps every computation ends with: run the algorithms, see the results."""
        self.add_step(Step("calculate", run_title, self.run_page, role=RUN))
        self.add_step(Step("results", results_title, self.results, role=RESULTS))

    # -- moving between steps -----------------------------------------------------

    @property
    def current(self) -> int:
        """The number of the step shown, counted from zero."""
        return self.pages.currentIndex()

    def step(self, key: str) -> Step:
        """The step of that key."""
        return next(step for step in self.steps if step.key == key)

    def go_to(self, number: int | str) -> bool:
        """Show a step, by number or key. Returns whether it was unlocked and is shown."""
        if isinstance(number, str):
            number = next(i for i, step in enumerate(self.steps) if step.key == number)
        if not 0 <= number < len(self.steps) or self.steps[number].state == LOCKED:
            return False
        self.pages.setCurrentIndex(number)
        self.step_list.blockSignals(True)
        self.step_list.setCurrentRow(number)
        self.step_list.blockSignals(False)
        self._show_current()
        return True

    def _step_chosen(self, row: int) -> None:
        if row >= 0 and not self.go_to(row):
            self.step_list.blockSignals(True)
            self.step_list.setCurrentRow(self.current)
            self.step_list.blockSignals(False)

    def _show_current(self) -> None:
        if not self.steps:
            return
        step = self.steps[self.current]
        self._title.setText(step.title)
        self.back_button.setEnabled(self.current > 0)
        following = self.current + 1
        self.next_button.setEnabled(
            following < len(self.steps) and self.steps[following].state != LOCKED
        )
        self.strip.clear()
        notes = list(step.notes())
        problem = step.problem() if step.role == INPUT else ""
        if problem and not any(note.severity == BLOCKING for note in notes):
            notes.insert(0, Note(BLOCKING, problem))
        for note in notes:
            item = QListWidgetItem(_NOTE_MARKS.get(note.severity, "") + note.text, self.strip)
            item.setData(Qt.ItemDataRole.UserRole, note)
            item.setToolTip(note.text)
        self.strip.setVisible(bool(notes))

    def _note_clicked(self, item: QListWidgetItem) -> None:
        note = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(note, Note):
            self.note_chosen(note)

    def notes_shown(self) -> list[Note]:
        """The notes in the strip, in order."""
        return [
            self.strip.item(row).data(Qt.ItemDataRole.UserRole) for row in range(self.strip.count())
        ]

    # -- looking again at what is typed ---------------------------------------------

    def schedule_refresh(self) -> None:
        """Look again shortly: several edits in a row cost one look."""
        self._refresh_timer.start()

    def _job_edited(self, technique: str) -> None:
        if technique == self.technique and not self._closing:
            self.schedule_refresh()

    def _job_replaced(self, technique: str) -> None:
        if technique != self.technique or self._closing:
            return
        self._shown_result = None
        self.reload_pages()
        self.refresh()
        self.go_to(0)

    def _job_saved(self, technique: str) -> None:
        if technique != self.technique or self._closing:
            return
        self._carry_results()
        self.refresh()

    def _carry_results(self) -> None:
        """Take results made before the job had a file to where they now belong."""
        target = self.results_folder()
        seen = self._folder_seen
        if seen is not None and seen != target and seen.is_dir() and not target.exists():
            try:
                shutil.copytree(seen, target)
            except OSError:
                # They can be made again from the job; that is what the job file is for.
                return

    def fingerprint(self) -> str | None:
        """What identifies the inputs of a run as they stand, or ``None`` while they cannot be run."""
        try:
            return self.chain().fingerprint()
        except GeoCompError:
            return None

    def refresh(self) -> None:
        """Work out each step's state from the job as it stands, and show it."""
        if self._closing:
            return
        self._refresh_timer.stop()
        blocked = self.precondition()
        ready = not blocked
        result = self.job.result(self.spec.name)
        current = False
        marked = None
        for step in self.steps:
            if step.role == INPUT:
                complete = not step.problem()
                step.state = LOCKED if not ready and step is not self.steps[0] else (
                    DONE if complete else READY
                )
                ready = ready and complete
            elif step.role == RUN:
                marked = self.fingerprint() if ready else None
                current = (
                    marked is not None
                    and self.job.is_current(self.spec.name, marked)
                    and self._report_path() is not None
                )
                step.state = LOCKED if not ready else DONE if current else (
                    STALE if result is not None else READY
                )
                self.run_page.set_ready(
                    ready and not self.runner.is_running, blocked or self._first_problem()
                )
            else:
                has_files = result is not None and self._report_path() is not None
                step.state = LOCKED if not has_files else DONE if current else STALE
        self._folder_seen = self.results_folder()
        self._show_states()
        self._show_banner(blocked)
        self._show_results(result, stale=not current)
        self._show_job()
        self._show_current()
        self.sketch.clear()
        self.draw()
        if (
            result is not None
            and ready
            and not current
            and marked is not None
            and marked != self._failed
            and self.run_page.automatic.isChecked()
            and not self.runner.is_running
        ):
            self._recalculate_timer.start()
        else:
            self._recalculate_timer.stop()

    def _first_problem(self) -> str:
        return next(
            (problem for step in self.steps if step.role == INPUT and (problem := step.problem())), ""
        )

    def _show_states(self) -> None:
        for number, step in enumerate(self.steps):
            item = self.step_list.item(number)
            item.setText(f"{number + 1}.  {step.title}{_MARKS.get(step.state, '')}")
            flags = Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
            item.setFlags(Qt.ItemFlag.NoItemFlags if step.state == LOCKED else flags)
            item.setToolTip(
                {
                    LOCKED: _tr("Complete the steps before this one first."),
                    STALE: _tr("Out of date: the job changed since this was calculated."),
                }.get(step.state, "")
            )
        if self.steps and self.steps[self.current].state == LOCKED:
            self.go_to(max(i for i, step in enumerate(self.steps) if step.state != LOCKED))

    def _show_banner(self, blocked: str) -> None:
        self.banner.setText(blocked)
        self.banner.setVisible(bool(blocked))
        self.banner_button.setVisible(bool(blocked) and bool(self.banner_button.text()))

    def _show_job(self) -> None:
        job = self.job
        name = job.name or (job.path.stem if job.path is not None else _tr("untitled job"))
        where = str(job.path) if job.path is not None else _tr("not saved yet")
        mark = " *" if self.jobs.is_modified(self.technique) else ""
        self._job_label.setText(f"{name}{mark} — {where}")
        self.setWindowTitle(f"{self.window_label()} — {name}{mark}")

    def window_label(self) -> str:
        """The window's translated name, as its menu item gives it."""
        from geocomp.gui.windows.labels import window_label

        return window_label(self.spec.name)

    # -- running ---------------------------------------------------------------------

    def calculate(self) -> bool:
        """Run the window's chain on what is typed. Returns whether a run began."""
        if self.runner.is_running:
            return False
        blocked = self.precondition() or self._first_problem()
        if blocked:
            self.run_page.set_status(blocked)
            return False
        try:
            chain = self.chain()
        except GeoCompError as error:
            self.run_page.set_status(message_for(error))
            return False
        self._recalculate_timer.stop()
        # Into a folder of its own, moved into place only when every step has
        # succeeded: a run that fails must not take the last good result with it.
        folder = self._staging_folder()
        shutil.rmtree(folder, ignore_errors=True)
        self._running = (chain, folder)
        self.run_page.started()
        self.runner.run(chain, folder)
        return True

    def _staging_folder(self) -> Path:
        final = self.results_folder()
        return final.with_name(f".{final.name}.running")

    def _put_in_place(self, staging: Path) -> str:
        """Make a successful run's folder the results folder. Returns why it could not, or ``""``."""
        final = self.results_folder()
        for leftover in final.parent.glob(f".{final.name}.*.replaced"):
            shutil.rmtree(leftover, ignore_errors=True)
        # The last result is moved aside whole, not deleted file by file: on
        # Windows a file held open -- a report in a browser, a table in a
        # spreadsheet -- stops the move before anything is lost, where a
        # deletion would stop half way and leave half a result.
        replaced = final.with_name(f".{final.name}.{time.time_ns()}.replaced")
        try:
            if final.exists():
                final.rename(replaced)
        except OSError as error:
            return str(error)
        try:
            try:
                staging.rename(final)
            except OSError:
                # A file still open in the folder -- a layer GDAL has not let
                # go of -- stops a folder being moved on Windows, not copied.
                shutil.copytree(staging, final)
                shutil.rmtree(staging, ignore_errors=True)
        except OSError as error:
            shutil.rmtree(final, ignore_errors=True)
            if replaced.exists():
                with contextlib.suppress(OSError):
                    replaced.rename(final)
            return str(error)
        shutil.rmtree(replaced, ignore_errors=True)
        return ""

    def _recalculate(self) -> None:
        if self.run_page.automatic.isChecked() and not self._closing:
            self.calculate()

    def _step_started(self, key: str, number: int, count: int) -> None:
        label = key
        if self._running is not None:
            algorithm_id = next(
                (step.algorithm for step in self._running[0].steps if step.key == key), ""
            )
            registered = QgsApplication.processingRegistry().algorithmById(algorithm_id)
            label = registered.displayName() if registered is not None else key
        self.run_page.step_started(label, number, count)

    def _run_finished(self, outcome: ChainOutcome) -> None:
        self.last_outcome = outcome
        running, self._running = self._running, None
        if self._closing:
            return
        if not outcome.succeeded or running is None:
            self.run_page.ended(outcome)
            if running is not None:
                shutil.rmtree(running[1], ignore_errors=True)
                if not outcome.cancelled:
                    self._failed = running[0].fingerprint()
            self.refresh()
            return
        chain, folder = running
        # Indexed before the folder is moved, relative to it, so the same in its new place.
        outputs = {
            f"{step.key}.{name}": str(path.relative_to(folder))
            for step in outcome.steps
            for name, path in step.outputs.items()
            if path.is_file()
        }
        problem = self._put_in_place(folder)
        if problem:
            self.run_page.ended(outcome)
            self.run_page.set_status(
                _tr("Calculated, but the results could not be put in %1 (%2). Check that the folder "
                    "is not open in another program, and calculate again.")
                .replace("%1", str(self.results_folder()))
                .replace("%2", problem)
            )
            self.refresh()
            return
        self.run_page.ended(outcome, moved=(folder, self.results_folder()))
        self._failed = None
        self.job.record_result(
            self.spec.name,
            fingerprint=chain.fingerprint(),
            outputs=outputs,
            scalars={
                f"{key}.{name}": _storable(value)
                for key, results in outcome.results.items()
                for name, value in results.items()
                if isinstance(value, bool | int | float)
            },
            log=[text for _kind, text in outcome.log],
        )
        self._shown_result = None
        self.after_run(outcome)
        self.touch()
        self.refresh()
        if self.steps[self.current].role == RUN:
            self.go_to(next(i for i, step in enumerate(self.steps) if step.role == RESULTS))

    # -- results -----------------------------------------------------------------------

    def output_path(self, step: str, name: str) -> Path | None:
        """Where the last recorded run wrote the output *name* of *step*, if the file is there."""
        result = self.job.result(self.spec.name)
        if result is None:
            return None
        relative = result.get("outputs", {}).get(f"{step}.{name}")
        if not relative:
            return None
        path = self.results_folder() / relative
        return path if path.is_file() else None

    def scalars(self) -> dict[str, Any]:
        """What the last recorded run's algorithms returned, keyed ``step.NAME``."""
        result = self.job.result(self.spec.name)
        return {} if result is None else dict(result.get("scalars", {}))

    def _report_path(self) -> Path | None:
        return self.output_path(*self.REPORT)

    def _show_results(self, result: dict[str, Any] | None, *, stale: bool) -> None:
        report = self._report_path()
        shown = (
            None if result is None else result.get("fingerprint"),
            stale,
            report,
            None if report is None else report.stat().st_mtime_ns,
        )
        if shown == self._shown_result:
            return
        self._shown_result = shown
        if result is None:
            self.results.clear(_tr("Not calculated yet."))
        elif report is None:
            self.results.clear(
                _tr(
                    "The files of the last calculation are no longer there. Calculate again: "
                    "everything a window writes can be made again from the job."
                )
            )
        else:
            table = None if self.TABLE is None else self.output_path(*self.TABLE)
            self.results.show_results(
                self.figures(self.scalars()), report=report, table=table, stale=stale
            )

    # -- the job bar ---------------------------------------------------------------------

    def new_job(self) -> None:
        """Start an empty job, after asking about unsaved changes."""
        if self._settle_changes():
            self.jobs.new(self.technique)

    def open_job(self) -> None:
        """Ask for a job file and open it."""
        if not self._settle_changes():
            return
        path, _filter = QFileDialog.getOpenFileName(
            self, _tr("Open job"), "", _tr("GeoComp jobs (*%1)").replace("%1", JOB_SUFFIX)
        )
        if path:
            self.open_job_file(path)

    def open_job_file(self, path: str | Path) -> bool:
        """Open the job file at *path*. A file that is not a job is refused in words."""
        try:
            self.jobs.open(self.technique, path)
        except GeoCompError as error:
            self.say(message_for(error))
            return False
        return True

    def save_job(self) -> bool:
        """Save the job to its file, asking for one the first time."""
        if self.job.path is None:
            return self.save_job_as()
        return self.save_job_to(None)

    def save_job_as(self) -> bool:
        """Ask where to save the job, and save it there."""
        path, _filter = QFileDialog.getSaveFileName(
            self, _tr("Save job"), "", _tr("GeoComp jobs (*%1)").replace("%1", JOB_SUFFIX)
        )
        return bool(path) and self.save_job_to(path)

    def save_job_to(self, path: str | Path | None) -> bool:
        """Save the job to *path*, or to its own file. A failure is said in words."""
        try:
            self.jobs.save(self.technique, path)
        except GeoCompError as error:
            self.say(message_for(error))
            return False
        return True

    def say(self, text: str) -> None:
        """Tell the user something that needs acknowledging: a file refused, a save failed."""
        QMessageBox.warning(self, self.window_label(), text)

    def ask_to_save(self) -> str:
        """Ask what to do with unsaved changes: ``"save"``, ``"keep"`` or ``"cancel"``."""
        answer = QMessageBox.question(
            self,
            self.window_label(),
            _tr(
                "The job has changes that are not saved. Save them now? Unsaved, the job stays "
                "open until QGIS closes."
            ),
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
        )
        if answer == QMessageBox.StandardButton.Save:
            return "save"
        return "keep" if answer == QMessageBox.StandardButton.Discard else "cancel"

    def _settle_changes(self) -> bool:
        """Whether to go on with something that leaves the job behind."""
        if not self.jobs.is_modified(self.technique):
            return True
        answer = self.ask_to_save()
        if answer == "save":
            return self.save_job()
        return answer == "keep"

    # -- the map -------------------------------------------------------------------------

    def pick_point(self, picked: Callable[[float, float], None]) -> bool:
        """Lend the canvas a tool for one click, and give *picked* the point in the job's CRS.

        Returns whether there is a canvas to click on. The canvas has its
        previous tool back after the click, or when the window closes.
        """
        if self.canvas is None:
            return False
        self._release_canvas()
        self._previous_tool = self.canvas.mapTool()
        self._pick_tool = PointPickTool(self.canvas)
        self._pick_tool.picked.connect(self._point_picked)
        self._picked = picked
        self.canvas.setMapTool(self._pick_tool)
        return True

    def _point_picked(self, x: float, y: float) -> None:
        from qgis.core import QgsPointXY

        picked, self._picked = self._picked, None
        self._release_canvas()
        carried = self.sketch.from_map(QgsPointXY(x, y))
        if picked is not None and carried is not None:
            picked(*carried)
        self.raise_()
        self.activateWindow()

    def _release_canvas(self) -> None:
        """Give the canvas back the tool it had before a point was being picked."""
        tool, self._pick_tool = self._pick_tool, None
        if tool is None or self.canvas is None:
            return
        if self.canvas.mapTool() is tool:
            if self._previous_tool is None:
                # ``setMapTool(None)`` leaves the current tool where it is.
                self.canvas.unsetMapTool(tool)
            else:
                self.canvas.setMapTool(self._previous_tool)
        self._previous_tool = None

    @property
    def is_picking(self) -> bool:
        """Whether the canvas is lent a tool for a click."""
        return self._pick_tool is not None

    # -- closing -------------------------------------------------------------------------

    def reject(self) -> None:
        """Close, after asking about unsaved changes when this is the technique's last window."""
        if self._is_last_open() and not self._settle_changes():
            return
        super().reject()

    def close_now(self) -> None:
        """Close without asking: the plugin is unloading (FR-006)."""
        self.done(0)

    def done(self, result: int) -> None:
        """Give the canvas back, take the sketch off the map and stop what is running."""
        if not self._closing:
            self._closing = True
            self._refresh_timer.stop()
            self._recalculate_timer.stop()
            self.runner.cancel()
            self._release_canvas()
            self.sketch.clear()
            for signal, slot in (
                (self.jobs.edited, self._job_edited),
                (self.jobs.replaced, self._job_replaced),
                (self.jobs.saved, self._job_saved),
            ):
                try:
                    signal.disconnect(slot)
                except (TypeError, RuntimeError):  # already disconnected
                    pass
            self.closed.emit(self.spec.name)
        super().done(result)


def _storable(value: Any) -> Any:
    """A scalar as a job file keeps it: a number that is not finite is kept as its name."""
    if isinstance(value, float) and not math.isfinite(value):
        return repr(value)
    return value
