# SPDX-License-Identifier: GPL-2.0-or-later
"""The job file: a technique's typed field book, and what was asked of it (FR-013).

``specs/17-persistence-and-interoperability.md`` section 6. One file,
``<name>.gcjob``, in JSON:

* what was typed -- every table, cell for cell, as text;
* the conventions it was typed in, without which the text means nothing;
* for each window that worked on it, the options chosen and an index of the
  results it last produced.

**The job file is the record; the results are not.** What an algorithm wrote --
readings, reductions, reports -- lies in a folder beside the file,
``<name>_results/``, one subfolder per window, and every file in it can be made
again from the job by pressing Calculate. So a job is handed to a colleague as
one file, and a results folder that has gone missing costs a recalculation, not
a survey.

A result is indexed with a **fingerprint** of the inputs that produced it. When
the field book or an option has changed since, the fingerprint no longer matches
and the window says the result is out of date instead of showing a closure that
belongs to an earlier field book.

Saving is atomic: the file is written beside its destination and moved over it,
so a save interrupted half-way leaves the previous job, not half of the new one.
"""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from geocomp.core.errors import StorageError, ValidationError
from geocomp.jobs.tables import Column, TypedTable

__all__ = ["JOB_KIND", "JOB_SUFFIX", "JOB_VERSION", "Job"]

JOB_KIND = "geocomp.job"
JOB_VERSION = 1
JOB_SUFFIX = ".gcjob"


class Job:
    """One technique's field book and what its windows were asked.

    Args:
        technique: Which technique's job it is: ``total_station``. A job is
            opened by the windows of its own technique only.
        tables: The typed tables, by name, each with its columns. A technique
            declares them; :meth:`from_dict` fills them from the file.
        name: What the user calls it.
        crs: The CRS its coordinates are in, as an authority id, or empty for
            a local plane -- a survey with no datum is a real one.
        entry: The conventions the tables were typed in, by name.
    """

    def __init__(
        self,
        technique: str,
        tables: Mapping[str, TypedTable],
        *,
        name: str = "",
        crs: str = "",
        entry: Mapping[str, str] | None = None,
    ) -> None:
        self.technique = technique
        self.tables: dict[str, TypedTable] = dict(tables)
        self.name = name
        self.crs = crs
        self.entry: dict[str, str] = dict(entry or {})
        #: Per window: ``parameters`` chosen, ``state`` of its own steps, and the last ``result``.
        self.windows: dict[str, dict[str, Any]] = {}
        #: Where the job is saved, or ``None`` for one that never was.
        self.path: Path | None = None

    # -- per window ------------------------------------------------------

    def window(self, name: str) -> dict[str, Any]:
        """The record of the window *name*, made empty the first time it is asked for."""
        return self.windows.setdefault(name, {"parameters": {}, "state": {}})

    def parameters(self, window: str) -> dict[str, Any]:
        """The options the window *window* was given, by parameter name."""
        return self.window(window).setdefault("parameters", {})

    def state(self, window: str) -> dict[str, Any]:
        """What the window *window* keeps of its own steps: a route, a choice."""
        return self.window(window).setdefault("state", {})

    def result(self, window: str) -> dict[str, Any] | None:
        """The index of the window's last result, or ``None`` when it never ran."""
        return self.window(window).get("result")

    def record_result(
        self,
        window: str,
        *,
        fingerprint: str,
        outputs: Mapping[str, str],
        scalars: Mapping[str, Any],
        log: Sequence[str] = (),
    ) -> None:
        """Index what the window *window* just produced.

        Args:
            fingerprint: Of the inputs that produced it.
            outputs: Each output file, by ``step.OUTPUT``, relative to the
                window's results folder.
            scalars: The numbers and verdicts the algorithms returned.
            log: What the algorithms said while running.
        """
        self.window(window)["result"] = {
            "fingerprint": fingerprint,
            "outputs": dict(outputs),
            "scalars": dict(scalars),
            "log": list(log),
        }

    def is_current(self, window: str, fingerprint: str) -> bool:
        """Whether the window's last result was produced by the inputs *fingerprint* names."""
        result = self.result(window)
        return result is not None and result.get("fingerprint") == fingerprint

    # -- where things are ------------------------------------------------

    @property
    def results_directory(self) -> Path | None:
        """The folder beside the job file that holds its results, or ``None`` for an unsaved job."""
        if self.path is None:
            return None
        return self.path.with_name(f"{self.path.stem}_results")

    # -- the file --------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """The job as its file stores it."""
        return {
            "kind": JOB_KIND,
            "version": JOB_VERSION,
            "technique": self.technique,
            "name": self.name,
            "crs": self.crs,
            "entry": dict(self.entry),
            "tables": {
                name: {
                    "columns": [column.key for column in table.columns],
                    "rows": table.to_list(),
                }
                for name, table in self.tables.items()
            },
            "windows": self.windows,
        }

    @classmethod
    def from_dict(
        cls, payload: Mapping[str, Any], columns: Mapping[str, Sequence[Column]], *, source: str = ""
    ) -> Job:
        """Read a job back from its stored form.

        Args:
            payload: The file's content.
            columns: The technique's tables and their columns. A table is
                filled by column *key*, so a job saved before a column was
                added, or with its columns in another order, still opens.
            source: The file's path, for the refusals to name.

        Raises:
            ValidationError: ``job_file_not_a_job`` for a document of another
                kind, ``job_file_newer`` for one a later GeoComp saved.
        """
        if not isinstance(payload, Mapping) or payload.get("kind") != JOB_KIND:
            raise ValidationError("job_file_not_a_job", path=source)
        version = payload.get("version")
        if not isinstance(version, int) or version > JOB_VERSION:
            raise ValidationError(
                "job_file_newer", path=source, version=version, supported=JOB_VERSION
            )
        stored = payload.get("tables") or {}
        tables = {
            name: TypedTable(declared, _by_key(stored.get(name) or {}, declared))
            for name, declared in columns.items()
        }
        job = cls(
            str(payload.get("technique") or ""),
            tables,
            name=str(payload.get("name") or ""),
            crs=str(payload.get("crs") or ""),
            entry={str(key): str(value) for key, value in (payload.get("entry") or {}).items()},
        )
        windows = payload.get("windows") or {}
        job.windows = {str(name): dict(record) for name, record in windows.items()}
        return job

    @classmethod
    def load(cls, path: str | Path, columns: Mapping[str, Sequence[Column]]) -> Job:
        """Open the job file at *path*.

        Raises:
            ValidationError: ``job_file_unreadable`` for a file that is missing
                or is not JSON, and :meth:`from_dict`'s refusals.
        """
        source = Path(path)
        try:
            payload = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise ValidationError("job_file_unreadable", path=str(source), reason=str(error)) from error
        job = cls.from_dict(payload, columns, source=str(source))
        job.path = source
        return job

    def save(self, path: str | Path | None = None) -> Path:
        """Write the job to *path*, or to where it was last saved.

        Raises:
            StorageError: ``job_not_saved`` when the file cannot be written, or
                when no path is given and the job has none.
        """
        target = Path(path) if path is not None else self.path
        if target is None:
            raise StorageError("job_not_saved", path="", reason="no path")
        if target.suffix != JOB_SUFFIX:
            target = target.with_name(target.name + JOB_SUFFIX)
        text = json.dumps(self.to_dict(), indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            handle, temporary = tempfile.mkstemp(prefix=target.name, suffix=".tmp", dir=target.parent)
            try:
                with os.fdopen(handle, "w", encoding="utf-8") as stream:
                    stream.write(text)
                os.replace(temporary, target)
            except OSError:
                Path(temporary).unlink(missing_ok=True)
                raise
        except OSError as error:
            raise StorageError("job_not_saved", path=str(target), reason=str(error)) from error
        self.path = target
        return target


def _by_key(stored: Mapping[str, Any], declared: Sequence[Column]) -> list[list[str]]:
    """A stored table's rows, each cell under the declared column of its key."""
    keys = [str(key) for key in stored.get("columns") or ()]
    rows = []
    for row in stored.get("rows") or ():
        cells = dict(zip(keys, (str(cell) for cell in row), strict=False))
        rows.append([cells.get(column.key, "") for column in declared])
    return rows
