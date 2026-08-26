# SPDX-License-Identifier: GPL-2.0-or-later
"""Run core operations off the GUI thread (FR-008, NFR-004).

``specs/03-architecture.md`` section 3.5 fixes the division: core functions are
synchronous and cancellation-aware through an injected token; only this layer
knows about ``QgsTask``. Two rules follow, and both are enforced by the shape of
this module rather than by convention:

* **No layer or project mutation off the main thread.** A task returns data;
  ``finished`` runs on the main thread and is where layers get created. The
  worker callable is given no QGIS object to mutate.
* **Cancellation is cooperative.** ``QgsTask.isCanceled`` is adapted to the
  core's :class:`~geocomp.core.cancellation.CancellationToken` protocol, so core
  code polls a plain object and stays testable.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Generic, TypeVar

from qgis.core import QgsApplication, QgsTask

from geocomp.core.cancellation import Cancelled
from geocomp.core.errors import GeoCompError
from geocomp.services.logging import log

__all__ = ["GeoCompTask", "TaskCancellation", "run_task"]

T = TypeVar("T")


class TaskCancellation:
    """Adapts ``QgsTask`` cancellation onto the core's token protocol."""

    __slots__ = ("_task",)

    def __init__(self, task: QgsTask) -> None:
        self._task = task

    def is_cancelled(self) -> bool:
        return bool(self._task.isCanceled())


class GeoCompTask(QgsTask, Generic[T]):
    """Runs a synchronous core callable on a background thread.

    Args:
        description: Shown in the QGIS task manager. Already translated by the
            caller -- this layer does not phrase text.
        work: ``work(cancellation, progress) -> T``. Must be pure with respect
            to QGIS: it may not touch layers, the project, or any GUI object.
        on_success: Called on the **main** thread with the result. This is where
            layers are added and the UI is updated.
        on_error: Called on the main thread when *work* raised. Defaults to
            logging the exception.
        on_cancel: Called on the main thread when the user cancelled.
    """

    def __init__(
        self,
        description: str,
        work: Callable[[TaskCancellation, Callable[[float | None, str | None], None]], T],
        *,
        on_success: Callable[[T], None] | None = None,
        on_error: Callable[[BaseException], None] | None = None,
        on_cancel: Callable[[], None] | None = None,
        flags: Any = None,
    ) -> None:
        if flags is None:
            super().__init__(description, QgsTask.Flag.CanCancel)
        else:
            super().__init__(description, flags)
        self._work = work
        self._on_success = on_success
        self._on_error = on_error
        self._on_cancel = on_cancel
        self._result: T | None = None
        self._exception: BaseException | None = None

    def run(self) -> bool:
        """Executed on the worker thread. Returns success."""
        cancellation = TaskCancellation(self)

        def progress(fraction: float | None, message_code: str | None = None) -> None:
            # Determinate where the work is countable, indeterminate otherwise
            # (FR-008). QgsTask expects 0..100.
            if fraction is not None:
                self.setProgress(max(0.0, min(1.0, fraction)) * 100.0)
            if message_code:
                log.debug("task progress", task=self.description(), stage=message_code)

        try:
            self._result = self._work(cancellation, progress)
        except Cancelled:
            return False
        except BaseException as exc:  # noqa: BLE001 - re-raised on the main thread
            self._exception = exc
            return False
        return True

    def finished(self, success: bool) -> None:
        """Executed on the main thread. The only place QGIS state may change."""
        if success:
            if self._on_success is not None:
                self._on_success(self._result)  # type: ignore[arg-type]
            return

        if self._exception is not None:
            if self._on_error is not None:
                self._on_error(self._exception)
            elif isinstance(self._exception, GeoCompError):
                log.exception(self._exception, message=f"task failed: {self.description()}")
            else:
                log.exception(self._exception, message=f"task failed unexpectedly: {self.description()}")
            return

        # No exception and not successful means cancellation.
        if self._on_cancel is not None:
            self._on_cancel()
        else:
            log.info("task cancelled", task=self.description())


def run_task(task: GeoCompTask[Any]) -> GeoCompTask[Any]:
    """Hand *task* to the QGIS task manager and return it.

    The caller must keep a reference: the task manager takes ownership, but
    dropping the Python reference before ``finished`` runs is a known way to
    lose the task to garbage collection.
    """
    QgsApplication.taskManager().addTask(task)
    return task
