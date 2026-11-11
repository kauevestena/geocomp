# SPDX-License-Identifier: GPL-2.0-or-later
"""Run a window's chain of algorithms off the GUI thread (FR-011, NFR-004).

ADR-0010: an interactive window computes nothing; it runs registered Processing
algorithms. This is where they are run. A :class:`~geocomp.jobs.chains.Chain`
is resolved into files and parameters, and each step is run as a
``QgsProcessingAlgRunnerTask`` -- the task QGIS's own Processing dialog uses --
one after another, each reading what the one before it wrote.

Three rules, held by the shape of this module:

* **Nothing runs on the GUI thread.** A step is a task in the QGIS task
  manager; what it says arrives through queued Qt signals.
* **A window runs only the algorithms the registry says it runs.** The runner
  is made with those ids and refuses any other, so a window cannot acquire a
  computation without ``geocomp.registry.WINDOWS`` saying so.
* **A refusal is the algorithm's own.** Parameters are checked with the
  algorithm's ``checkParameterValues`` before it runs, exactly as the toolbox
  dialog checks them, and a failure is reported in the words the algorithm
  raised it with -- there is no second wording to drift.

An algorithm is made afresh for each run (``create()``), so its defaults are
the Global Settings of the moment, as a toolbox dialog's are.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from qgis.core import (
    QgsApplication,
    QgsProcessingAlgRunnerTask,
    QgsProcessingContext,
    QgsProcessingFeedback,
)
from qgis.PyQt.QtCore import QCoreApplication, QObject, pyqtSignal

from geocomp.jobs.chains import Chain, ResolvedStep, resolve

__all__ = ["INFO", "PROBLEM", "WARNING", "ChainFeedback", "ChainOutcome", "ChainRunner"]

_TR_CONTEXT = "GeoCompChainRunner"

#: The kinds of line an algorithm says while it runs.
INFO = "info"
WARNING = "warning"
PROBLEM = "problem"


def _tr(text: str) -> str:
    return QCoreApplication.translate(_TR_CONTEXT, text)


class ChainFeedback(QgsProcessingFeedback):
    """What a running algorithm says, carried to the window through queued signals."""

    said = pyqtSignal(str, str)

    def __init__(self) -> None:
        super().__init__()
        #: The last error the algorithm reported: why it failed.
        self.error = ""

    def pushInfo(self, info: str) -> None:  # noqa: N802 -- QGIS interface
        """An ordinary line of the algorithm's log."""
        super().pushInfo(info)
        self.said.emit(INFO, info)

    def pushWarning(self, warning: str) -> None:  # noqa: N802 -- QGIS interface
        """A warning: the run goes on, and the user should see it."""
        super().pushWarning(warning)
        self.said.emit(WARNING, warning)

    def reportError(self, error: str, fatalError: bool = False) -> None:  # noqa: N802, N803 -- QGIS
        """An error: kept as the reason, should the run fail."""
        super().reportError(error, fatalError)
        self.error = error
        self.said.emit(PROBLEM, error)


@dataclass(frozen=True)
class ChainOutcome:
    """How a chain's run ended.

    Attributes:
        succeeded: Every step ran to its end.
        cancelled: The user stopped it.
        failed_step: The key of the step that failed, when one did.
        error: Why, in the algorithm's own words.
        steps: The steps as they were run, with where each file is.
        results: What each step's algorithm returned, by step key: its output
            paths and its scalars.
        log: Every line the algorithms said, as ``(kind, text)``.
    """

    succeeded: bool
    cancelled: bool = False
    failed_step: str = ""
    error: str = ""
    steps: tuple[ResolvedStep, ...] = ()
    results: dict[str, dict[str, Any]] = field(default_factory=dict)
    log: tuple[tuple[str, str], ...] = ()

    def output(self, step: str, name: str) -> Path | None:
        """Where the step *step* wrote its output *name*, when it did."""
        for resolved in self.steps:
            if resolved.key == step and name in resolved.outputs:
                path = resolved.outputs[name]
                return path if path.is_file() else None
        return None


class ChainRunner(QObject):
    """Runs one chain at a time, in the background.

    Args:
        allowed: The ids of the algorithms this runner may run: those of its
            window's :class:`~geocomp.registry.WindowSpec`.
        parent: The Qt parent, so the runner dies with its window.
    """

    #: A step is about to run: its key, its number from one, and how many there are.
    step_started = pyqtSignal(str, int, int)
    #: Progress of the whole chain, from 0 to 100.
    progressed = pyqtSignal(float)
    #: A line an algorithm said: its kind and its text.
    said = pyqtSignal(str, str)
    #: The run ended, with its :class:`ChainOutcome`.
    finished = pyqtSignal(object)

    def __init__(self, allowed: Iterable[str], parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._allowed = frozenset(allowed)
        self._steps: tuple[ResolvedStep, ...] = ()
        self._index = 0
        self._results: dict[str, dict[str, Any]] = {}
        self._log: list[tuple[str, str]] = []
        self._task = None
        self._context: QgsProcessingContext | None = None
        self._feedback: ChainFeedback | None = None
        self._cancelled = False

    @property
    def is_running(self) -> bool:
        """Whether a chain is running, or stopping."""
        return self._task is not None

    def run(self, chain: Chain, folder: str | Path) -> None:
        """Place *chain*'s files under *folder* and run its steps in order.

        Returns at once; :attr:`finished` reports how it ended. A run asked for
        while another is going is ignored.

        Raises:
            ValueError: for a chain naming an algorithm this runner was not
                made to run. A programming error, and it must not be a silent
                one: it is the rule that a window computes nothing.
        """
        if self.is_running:
            return
        stray = [algorithm for algorithm in chain.algorithms if algorithm not in self._allowed]
        if stray:
            raise ValueError(
                f"the chain names {stray!r}, which this window does not declare in the registry"
            )
        self._steps = resolve(chain, folder)
        # What a previous run left must not be read as this one's.
        for step in self._steps:
            for path in step.outputs.values():
                path.unlink(missing_ok=True)
        self._index = 0
        self._results = {}
        self._log = []
        self._cancelled = False
        self._start_step()

    def cancel(self) -> None:
        """Ask the running step to stop. :attr:`finished` still reports the end."""
        if not self.is_running:
            return
        self._cancelled = True
        if self._feedback is not None:
            self._feedback.cancel()
        self._task.cancel()

    # -- one step --------------------------------------------------------

    def _start_step(self) -> None:
        step = self._steps[self._index]
        self.step_started.emit(step.key, self._index + 1, len(self._steps))
        registered = QgsApplication.processingRegistry().algorithmById(step.algorithm)
        if registered is None:
            self._end(
                failed=step.key,
                error=_tr(
                    "The algorithm %1 is not available. Enable the GeoComp provider in the "
                    "Processing options."
                ).replace("%1", step.algorithm),
            )
            return
        algorithm = registered.create({})
        self._context = QgsProcessingContext()
        self._feedback = ChainFeedback()
        self._feedback.said.connect(self._said)
        self._feedback.progressChanged.connect(self._step_progressed)
        accepted, message = algorithm.checkParameterValues(step.parameters, self._context)
        if not accepted:
            self._end(failed=step.key, error=message)
            return
        self._task = QgsProcessingAlgRunnerTask(
            algorithm, step.parameters, self._context, self._feedback
        )
        self._task.executed.connect(self._step_finished)
        QgsApplication.taskManager().addTask(self._task)

    def _said(self, kind: str, text: str) -> None:
        self._log.append((kind, text))
        self.said.emit(kind, text)

    def _step_progressed(self, percent: float) -> None:
        self.progressed.emit((self._index + percent / 100.0) / max(len(self._steps), 1) * 100.0)

    def _step_finished(self, successful: bool, results: dict) -> None:
        step = self._steps[self._index]
        error = self._feedback.error if self._feedback is not None else ""
        self._task = None
        if self._cancelled:
            self._end(cancelled=True)
            return
        if not successful:
            self._end(
                failed=step.key,
                error=error or _tr("The algorithm stopped without saying why. See the log."),
            )
            return
        self._results[step.key] = dict(results)
        self._index += 1
        if self._index < len(self._steps):
            self.progressed.emit(self._index / len(self._steps) * 100.0)
            self._start_step()
        else:
            self.progressed.emit(100.0)
            self._end()

    def _end(self, *, failed: str = "", error: str = "", cancelled: bool = False) -> None:
        self._task = None
        self.finished.emit(
            ChainOutcome(
                succeeded=not failed and not cancelled,
                cancelled=cancelled,
                failed_step=failed,
                error=error,
                steps=self._steps,
                results=dict(self._results),
                log=tuple(self._log),
            )
        )
