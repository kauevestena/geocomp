# SPDX-License-Identifier: GPL-2.0-or-later
"""A run writes all of its outputs or none of them (specs/16 §7, criterion 8; specs/17 criterion 6).

``specs/16`` asks that a cancelled run leave no partial output. Until P12c, 13
of the 46 algorithms looked at the cancel button at all, and each of those
returned an empty result from wherever it noticed. Whatever it had written by
then -- a solution document without its report, half of an engine's working
folder, a GeoPackage with some of a project in it -- stayed on disk, and
Processing reported the run as having *completed*.

Checking the button in 46 places would not have fixed that: the check is only
as good as the place it sits, and the next algorithm written would forget it.
So the rule is held in one place, around every algorithm's
``processAlgorithm``. :class:`~geocomp.algorithms.base.GeoCompAlgorithm` wraps
each subclass's method when the class is defined, so no algorithm can opt out
by forgetting. Before the run, every file a destination parameter names is
noted, and copied aside if it exists. Afterwards:

* **not cancelled** -- the copies are dropped, whether the run finished or
  failed. A failure is left as it failed, because several algorithms write a
  refusal before they raise: the document and report saying why the analysis
  was refused are the output a user needs then, not debris to clear away.
* **cancelled** -- every named file is put back as it was: restored from its
  copy, or removed if the run created it. Every entry the run added to a
  destination folder is removed. The run then raises, so Processing reports it
  as not having finished, rather than as a success with no results. Cancelled
  means the feedback says so, whether the algorithm noticed and returned, or
  went on to the end, or failed because its engine was stopped; or a core
  routine raised :class:`~geocomp.core.cancellation.Cancelled`.

**What it does not cover, and why.** A destination that is a database table --
``postgres:``, ``ogr:``, a GeoPackage layer -- belongs to its provider, and the
GeoComp algorithms that write into a database do so inside a transaction of
their own, cancelled before it commits (``project_store``, the PostGIS switches).
A temporary output, which Processing names in its own temporary folder, is
removed when the results name it. A model's children are each a run of their
own: cancelling a model keeps the outputs of the children that had finished.
And an existing file inside a destination *folder* is not copied first, since
an engine's folder can hold gigabytes; a run that overwrites one and is then
cancelled leaves it overwritten. No GeoComp algorithm overwrites one.
"""

from __future__ import annotations

import functools
import shutil
import tempfile
from collections.abc import Callable, Iterable
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from qgis.core import (
    QgsProcessing,
    QgsProcessingException,
    QgsProcessingOutputLayerDefinition,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterFolderDestination,
    QgsProcessingUtils,
)
from qgis.PyQt.QtCore import QCoreApplication

from geocomp.core.cancellation import Cancelled

__all__ = ["FeedbackCancellation", "OutputTransaction", "cancelled_message", "transactional"]

_CONTEXT = "GeoCompAlgorithm"

#: Whether this thread is already inside a run's transaction: a subclass that
#: calls its parent's ``processAlgorithm`` is one run, not two.
_ACTIVE: ContextVar[bool] = ContextVar("geocomp_output_transaction", default=False)

#: A shapefile is several files, and the run that wrote one wrote all of them.
_SHAPEFILE_PARTS = (".shp", ".shx", ".dbf", ".prj", ".cpg", ".qix", ".qmd")


def _tr(text: str) -> str:
    return QCoreApplication.translate(_CONTEXT, text)


def cancelled_message() -> str:
    """What a cancelled run says, wherever it noticed."""
    return _tr("Cancelled. Nothing was written: every output is as it was before the run.")


class FeedbackCancellation:
    """Processing's cancel button, as the token a core routine polls."""

    __slots__ = ("_feedback",)

    def __init__(self, feedback: Any) -> None:
        self._feedback = feedback

    def is_cancelled(self) -> bool:
        """Whether the user has pressed cancel."""
        return _cancelled(self._feedback)


@dataclass
class _File:
    path: Path
    backup: Path | None


@dataclass
class _Folder:
    path: Path
    before: set[str] | None


class OutputTransaction:
    """The files a run's destination parameters name, and how to put them back."""

    def __init__(self, algorithm: Any, parameters: dict[str, Any], context: Any) -> None:
        self._files: list[_File] = []
        self._folders: list[_Folder] = []
        self._backups: Path | None = None
        for definition in algorithm.destinationParameterDefinitions():
            path = _named_path(algorithm, definition, parameters, context)
            if path is None:
                continue
            if isinstance(definition, QgsProcessingParameterFolderDestination):
                before = {entry.name for entry in path.iterdir()} if path.is_dir() else None
                self._folders.append(_Folder(path, before))
                continue
            parts = (
                [path.with_suffix(suffix) for suffix in _SHAPEFILE_PARTS]
                if path.suffix.lower() == ".shp"
                else [path]
            )
            for part in parts:
                self._files.append(_File(part, self._copy_aside(part)))

    def _copy_aside(self, path: Path) -> Path | None:
        if not path.is_file():
            return None
        if self._backups is None:
            self._backups = Path(tempfile.mkdtemp(prefix="geocomp-outputs-"))
        backup = self._backups / f"{len(self._files)}-{path.name}"
        shutil.copy2(path, backup)
        return backup

    def undo(self, results: Iterable[Any] = ()) -> None:
        """Put every named output back as it was before the run."""
        for entry in self._files:
            if entry.backup is not None:
                shutil.copy2(entry.backup, entry.path)
            elif entry.path.is_file():
                entry.path.unlink()
        for folder in self._folders:
            if not folder.path.is_dir():
                continue
            if folder.before is None:
                shutil.rmtree(folder.path, ignore_errors=True)
                continue
            for added in folder.path.iterdir():
                if added.name in folder.before:
                    continue
                if added.is_dir():
                    shutil.rmtree(added, ignore_errors=True)
                else:
                    added.unlink(missing_ok=True)
        _remove_temporary(results)
        self.keep()

    def keep(self) -> None:
        """The run finished: drop the copies."""
        if self._backups is not None:
            shutil.rmtree(self._backups, ignore_errors=True)
            self._backups = None


def _named_path(algorithm: Any, definition: Any, parameters: dict[str, Any], context: Any):
    """The local file a destination names, or ``None`` when it names none."""
    value = parameters.get(definition.name())
    if isinstance(value, QgsProcessingOutputLayerDefinition):
        value = value.sink.staticValue()
    if not isinstance(value, str) or not value or value == QgsProcessing.TEMPORARY_OUTPUT:
        return None
    if isinstance(definition, QgsProcessingParameterFileDestination):
        # The same call the algorithm makes, so a default extension it appends
        # is appended here too.
        resolved = algorithm.parameterAsFileOutput(parameters, definition.name(), context)
        return Path(resolved) if resolved else None
    if isinstance(definition, QgsProcessingParameterFolderDestination):
        return Path(value)
    if isinstance(definition, QgsProcessingParameterFeatureSink):
        # "memory:", "postgres:...", "ogr:..." are the provider's, and a
        # "path|layername=..." is a table inside a file other layers share.
        if "|" in value or (":" in value and not Path(value).is_absolute()):
            return None
        path = Path(value)
        return path if path.suffix else path.with_suffix("." + definition.defaultFileExtension())
    return None


def _remove_temporary(results: Iterable[Any]) -> None:
    """Remove what a cancelled run wrote to Processing's temporary folder."""
    folder = Path(QgsProcessingUtils.tempFolder())
    for value in results:
        if not isinstance(value, str) or not value:
            continue
        path = Path(value)
        if path.is_absolute() and path.is_file() and folder in path.parents:
            path.unlink(missing_ok=True)


def _cancelled(feedback: Any) -> bool:
    return feedback is not None and bool(feedback.isCanceled())


def transactional(process: Callable) -> Callable:
    """Wrap a ``processAlgorithm`` so its run writes everything or nothing."""
    if getattr(process, "_geocomp_transactional", False):
        return process

    @functools.wraps(process)
    def run(self, parameters, context, feedback):
        if _ACTIVE.get():
            return process(self, parameters, context, feedback)
        transaction = OutputTransaction(self, parameters, context)
        token = _ACTIVE.set(True)
        try:
            results = process(self, parameters, context, feedback)
        except Cancelled:
            transaction.undo()
            raise QgsProcessingException(cancelled_message()) from None
        except BaseException:
            if not _cancelled(feedback):
                transaction.keep()
                raise
            transaction.undo()
            raise QgsProcessingException(cancelled_message()) from None
        finally:
            _ACTIVE.reset(token)
        if _cancelled(feedback):
            transaction.undo((results or {}).values())
            raise QgsProcessingException(cancelled_message())
        transaction.keep()
        return results

    run._geocomp_transactional = True
    return run
