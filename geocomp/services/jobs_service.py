# SPDX-License-Identifier: GPL-2.0-or-later
"""The job each technique's windows are working on (FR-013).

The windows of one technique share one job -- one field book -- as Posição's
*Caderneta*, *Calc. Poligonal* and *Calc. Irradiações* share one. This service
holds it: the current job per technique, New / Open / Save, whether it has
changed since it was saved, and a signal the technique's open windows listen
to, so a row typed in *Field book* is the row *Traverse* computes from without
either window knowing the other exists.

**The QGIS project remembers its jobs.** The path of each technique's job is
written into the project (relative to it, where QGIS stores paths relatively),
and read back when the project is opened, so a surveyor who closes QGIS finds
the field book where it was left.

Nothing here reads or computes a job's content; that is ``geocomp.jobs``.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from qgis.core import QgsProject
from qgis.PyQt.QtCore import QObject, pyqtSignal

from geocomp.core.errors import GeoCompError
from geocomp.jobs import levelling, total_station
from geocomp.jobs.chains import fingerprint
from geocomp.jobs.document import Job
from geocomp.services.logging import log

__all__ = ["TECHNIQUES", "JobsService"]

#: Each technique's way of making an empty job and of opening a saved one.
TECHNIQUES: dict[str, tuple[Callable[[], Job], Callable[[str | Path], Job]]] = {
    total_station.TECHNIQUE: (total_station.new_job, total_station.load_job),
    levelling.TECHNIQUE: (levelling.new_job, levelling.load_job),
}

_PROJECT_SCOPE = "geocomp"


class JobsService(QObject):
    """The current job of each technique.

    Args:
        parent: The Qt parent.
        project: The QGIS project that remembers the jobs. The open one by
            default; a test passes its own.
    """

    #: Another job became the technique's current one: its windows start over.
    replaced = pyqtSignal(str)
    #: The technique's job was edited: its windows look again at what they show.
    edited = pyqtSignal(str)
    #: The technique's job was saved, or its saved state otherwise changed.
    saved = pyqtSignal(str)

    def __init__(self, parent: QObject | None = None, *, project: QgsProject | None = None) -> None:
        super().__init__(parent)
        self._project = project if project is not None else QgsProject.instance()
        self._jobs: dict[str, Job] = {}
        self._as_saved: dict[str, str] = {}
        self._project.readProject.connect(self._project_read)

    def detach(self) -> None:
        """Stop following the project. Called when the plugin unloads (FR-006)."""
        try:
            self._project.readProject.disconnect(self._project_read)
        except (TypeError, RuntimeError):  # already disconnected, or the project is gone
            pass

    # -- the current job --------------------------------------------------

    def job(self, technique: str) -> Job:
        """The technique's current job: an empty, unsaved one until another is made or opened."""
        if technique not in self._jobs:
            self._adopt(technique, TECHNIQUES[technique][0]())
        return self._jobs[technique]

    def is_modified(self, technique: str) -> bool:
        """Whether the job differs from what was last saved, or from the empty job it began as."""
        return _content(self.job(technique)) != self._as_saved[technique]

    def touch(self, technique: str) -> None:
        """Say that the job was edited. Whoever edits it calls this."""
        self.edited.emit(technique)

    def new(self, technique: str) -> Job:
        """Start an empty job. The caller has asked about unsaved changes."""
        self._adopt(technique, TECHNIQUES[technique][0]())
        self._remember(technique)
        self.replaced.emit(technique)
        return self._jobs[technique]

    def open(self, technique: str, path: str | Path) -> Job:
        """Open the job file at *path* as the technique's current job.

        Raises:
            GeoCompError: the technique's refusals for a file that is not its job.
        """
        self._adopt(technique, TECHNIQUES[technique][1](path))
        self._remember(technique)
        self.replaced.emit(technique)
        return self._jobs[technique]

    def save(self, technique: str, path: str | Path | None = None) -> Path:
        """Save the job, to *path* or to where it was last saved.

        Raises:
            StorageError: ``job_not_saved``.
        """
        job = self.job(technique)
        written = job.save(path)
        self._as_saved[technique] = _content(job)
        self._remember(technique)
        self.saved.emit(technique)
        return written

    def _adopt(self, technique: str, job: Job) -> None:
        self._jobs[technique] = job
        self._as_saved[technique] = _content(job)

    # -- the project's memory ----------------------------------------------

    def _remember(self, technique: str) -> None:
        """Write where the technique's job is into the project, or forget it."""
        path = self._jobs[technique].path
        key = f"jobs/{technique}"
        if path is None:
            if self._project.readEntry(_PROJECT_SCOPE, key, "")[0]:
                self._project.removeEntry(_PROJECT_SCOPE, key)
                self._project.setDirty(True)
            return
        stored = self._project.writePath(str(path))
        if self._project.readEntry(_PROJECT_SCOPE, key, "")[0] != stored:
            self._project.writeEntry(_PROJECT_SCOPE, key, stored)
            self._project.setDirty(True)

    def remembered(self, technique: str) -> Path | None:
        """Where the project says the technique's job is, or ``None``."""
        stored = self._project.readEntry(_PROJECT_SCOPE, f"jobs/{technique}", "")[0]
        return Path(self._project.readPath(stored)) if stored else None

    def _project_read(self, *_arguments: object) -> None:
        self.restore()

    def restore(self) -> None:
        """Open the jobs the project remembers, where their files are still there.

        A job with unsaved changes is left alone: the project being opened
        must not cost a field book being typed.
        """
        for technique in TECHNIQUES:
            path = self.remembered(technique)
            if path is None or not path.is_file():
                continue
            if technique in self._jobs and self.is_modified(technique):
                continue
            current = self._jobs.get(technique)
            if current is not None and current.path == path:
                continue
            try:
                self._adopt(technique, TECHNIQUES[technique][1](path))
            except GeoCompError as error:
                log.warning("remembered job not opened", path=str(path), error=str(error))
                continue
            self.replaced.emit(technique)


def _content(job: Job) -> str:
    return fingerprint(job.to_dict())
