# SPDX-License-Identifier: GPL-2.0-or-later
"""The engine abstraction: one interface for every external program (FR-303).

``specs/03-architecture.md`` section 3.3 and ``specs/07-engine-dynadjust.md``.

GeoComp drives compiled C++ programs it did not write and cannot debug. Three
things follow, and they are the whole design of this module.

**Every run is recorded, whether it worked or not** (FR-036, FR-304). Command
line, exit code, stdout, stderr, wall time and the engine's own version go into
an :class:`EngineRun`, which reaches provenance and the report. When a user asks
why two runs differ, the answer is usually in the version or the command line,
and neither is recoverable after the fact if it was not captured at the time.

**``prepare`` / ``run`` / ``parse`` are separate** (FR-325). Advanced mode stops
after ``prepare`` so the user can read or edit the generated input, then
continues. A single ``adjust()`` that did all three would make that impossible
without a second code path, and a second code path is how the inspected files
stop being the files that ran.

**Absence is a state, not an exception at the point of use** (FR-306).
:meth:`Engine.detect` returns ``None`` rather than raising, so the UI can ask
"is this available?" and disable an action with an explanation. The exception
exists too -- :class:`EngineAbsentError`, raised by :func:`require` -- for the
code path that has already decided it needs the engine.

**This module imports no Qt.** Process execution, discovery, version parsing and
timeout handling are ordinary Python and are tested as such (NFR-002); only the
*download* needs the QGIS network stack, and it lives in
:mod:`geocomp.engines.manager` behind an injected fetcher for exactly that
reason.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import threading
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from geocomp.core.errors import ComputationError, ValidationError

__all__ = [
    "Engine",
    "EngineAbsentError",
    "EngineRun",
    "EngineVersion",
    "ProgressCallback",
    "discover",
    "require",
    "run_process",
]

#: Called with a line of engine output as it arrives. Engines are chatty and
#: slow; a progress bar that only moves at the end is not progress reporting.
ProgressCallback = Callable[[str], None]

#: How long an engine may run before it is terminated, when the caller states
#: nothing. Ten minutes suits a project-scale network; a continental one is
#: given an explicit limit by the algorithm that launches it (FR-304).
DEFAULT_TIMEOUT = 600.0


@dataclass(frozen=True)
class EngineVersion:
    """What was found, where, and whether it is a version GeoComp has tested.

    Attributes:
        version: The engine's own version string, exactly as it reported it.
            Not normalised: a parser keyed on it must match what the engine
            says, and a "helpful" normalisation is a silent behaviour change.
        tested: Whether *version* falls in the range this GeoComp release was
            validated against. ``False`` is a **warning, not a refusal**
            (FR-302): a user with a newer engine should be told the parsers may
            not match it, not prevented from working.
        source: How it was found -- a configured path, the system ``PATH``, or
            the managed installation. Part of the answer to "why does this
            machine behave differently".
    """

    name: str
    version: str
    path: Path
    tested: bool = True
    source: str = ""
    raw: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "path": str(self.path),
            "tested": self.tested,
            "source": self.source,
        }


@dataclass
class EngineRun:
    """One invocation of one engine program, recorded whole (FR-036, FR-304).

    Kept even when the run failed -- especially then. ``specs/07`` section 7
    requires that an engine failure surfaces the engine's *own* diagnostic
    rather than an exit code, and that is only possible if stderr was captured
    and retained.

    Attributes:
        work_dir: Retained after the run, not cleaned up, so the user can
            reproduce the invocation by hand or attach the inputs to an
            upstream bug report (FR-955).
        timed_out: Distinguished from a non-zero exit, because they mean
            different things: a timeout says nothing about whether the network
            was adjustable, and reporting it as a failure of the adjustment
            would send the user looking in the wrong place.
    """

    program: str
    command: tuple[str, ...]
    exit_code: int
    stdout: str
    stderr: str
    seconds: float
    work_dir: Path
    version: EngineVersion | None = None
    timed_out: bool = False
    environment: dict[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.exit_code == 0 and not self.timed_out

    @property
    def diagnostic(self) -> str:
        """The engine's own message, for a user who must act on it (FR-305).

        stderr first, then stdout: engines that report errors on stdout are
        common enough that taking stderr alone loses the message entirely, and
        an empty error box is the worst possible failure report.
        """
        for stream in (self.stderr, self.stdout):
            text = stream.strip()
            if text:
                return text
        return ""

    def to_dict(self) -> dict[str, Any]:
        """Serialise for provenance. Output is **truncated**, deliberately.

        A DynAdjust run over a large network prints tens of thousands of lines,
        and a provenance record that carries all of them is one nobody opens.
        The retained ``work_dir`` holds the full logs; this is the part a reader
        sees first, which is the beginning and the end -- where the version
        banner and the error are.
        """
        return {
            "program": self.program,
            "command": list(self.command),
            "exit_code": self.exit_code,
            "seconds": self.seconds,
            "timed_out": self.timed_out,
            "work_dir": str(self.work_dir),
            "version": self.version.to_dict() if self.version else None,
            "stdout": _ends(self.stdout),
            "stderr": _ends(self.stderr),
        }


def _ends(text: str, keep: int = 40) -> str:
    lines = text.splitlines()
    if len(lines) <= 2 * keep:
        return text
    omitted = len(lines) - 2 * keep
    return "\n".join(
        [*lines[:keep], f"... {omitted} lines omitted; see the run's work_dir ...", *lines[-keep:]]
    )


class EngineAbsentError(ComputationError):
    """The engine is needed and is not installed (FR-306).

    A :class:`~geocomp.core.errors.ComputationError` rather than a bespoke type
    so it travels the same path as every other failure a user sees, carrying
    the same structured context.
    """


class Engine(Protocol):
    """What every external engine adapter provides (FR-303).

    A protocol rather than a base class: RTKLIB (phase P7) has nothing to
    inherit from DynAdjust, and an abstract base would invite sharing that does
    not exist between two programs whose only similarity is being external.
    """

    name: str

    def detect(self) -> EngineVersion | None:
        """The installed version, or ``None``. Never raises for absence."""
        ...

    def prepare(self, job: Any, work_dir: Path) -> Any:
        """Write the engine's input files. No process is started."""
        ...

    def run(
        self,
        prepared: Any,
        *,
        timeout: float = DEFAULT_TIMEOUT,
        on_progress: ProgressCallback | None = None,
    ) -> list[EngineRun]:
        """Execute the engine, returning one :class:`EngineRun` per program."""
        ...

    def parse(self, runs: list[EngineRun], prepared: Any) -> Any:
        """Turn the engine's output into a :class:`~geocomp.core.models.Solution`."""
        ...


def discover(
    program: str,
    *,
    configured: str | Path | None = None,
    extra_directories: Sequence[Path] = (),
) -> tuple[Path | None, str]:
    """Find *program*, returning its path and how it was found.

    Search order, and it is not arbitrary (ADR-0003 rule 4): **an explicitly
    configured path always wins**, because a user who set one has a reason --
    a system installation, their own build, a specific version they are
    comparing against -- and silently preferring something else would make that
    setting a lie. Then the managed installation directories, then ``PATH``.

    A configured path that does not exist is an **error**, not a fall-through:
    falling back would run a different program than the one named, which is the
    failure mode this order exists to prevent.
    """
    if configured:
        candidate = Path(configured)
        if candidate.is_dir():
            candidate = candidate / program
        if not candidate.exists():
            raise ValidationError(
                "engine_path_not_found",
                program=program,
                received=str(configured),
                expected=(
                    "an existing executable, or no configured path at all. "
                    "GeoComp does not fall back to a different program than the "
                    "one you named"
                ),
            )
        return candidate, "configured"

    for directory in extra_directories:
        candidate = Path(directory) / program
        if candidate.exists():
            return candidate, "managed"

    found = shutil.which(program)
    if found:
        return Path(found), "path"
    return None, "absent"


def require(version: EngineVersion | None, *, engine: str, operation: str) -> EngineVersion:
    """Return *version*, or raise :class:`EngineAbsentError` naming what to do.

    The message is the point. ``specs/07`` section 7 and FR-306 both ask for an
    explanation rather than a failure, and "DynAdjust not found" tells a user
    nothing they can act on.
    """
    if version is not None:
        return version
    raise EngineAbsentError(
        "engine_not_available",
        engine=engine,
        operation=operation,
        expected=(
            f"{engine} installed. Install it from Global Settings > Paths and engines, "
            f"which downloads the pinned release for your platform and verifies it, or "
            f"set the path to an existing installation there. Everything in GeoComp that "
            f"does not need {engine} continues to work without it"
        ),
    )


def run_process(
    command: Sequence[str],
    *,
    work_dir: Path,
    program: str = "",
    timeout: float = DEFAULT_TIMEOUT,
    on_progress: ProgressCallback | None = None,
    version: EngineVersion | None = None,
    environment: dict[str, str] | None = None,
) -> EngineRun:
    """Run one engine program to completion, capturing everything (FR-304).

    Output is read **line by line while the process runs**, not collected at the
    end, so ``on_progress`` can report and a cancelled task can stop promptly.
    Collecting at the end is simpler and gives a progress bar that jumps from
    zero to done, which for a ten-minute adjustment is no progress bar at all.

    On timeout the **process group** is killed, not just the process: DynAdjust
    is a suite that starts helpers, and killing the parent alone leaves children
    holding the working directory and the CPU.
    """
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

    merged = dict(os.environ)
    merged.update(environment or {})

    started = time.monotonic()
    collected: list[str] = []
    errors: list[str] = []

    # start_new_session gives the child its own process group, which is what
    # makes killing the group possible below. Without it, killpg would signal
    # GeoComp's own group -- that is, QGIS.
    process = subprocess.Popen(
        [str(part) for part in command],
        cwd=str(work_dir),
        env=merged,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        start_new_session=True,
    )

    # **Both streams are drained on their own threads, and the timeout is
    # enforced by waiting on the process, not by checking the clock between
    # lines.** Reading in the main loop and testing the elapsed time after each
    # line looks equivalent and is not: an engine that prints one line and then
    # hangs blocks in the read forever, so the timeout never fires -- which is
    # precisely the case a timeout exists for. It was written that way first and
    # a thirty-second test caught it.
    #
    # Two threads rather than one because draining stdout in the main thread
    # while stderr fills its own pipe deadlocks as soon as the engine writes
    # more than a pipe buffer of diagnostics, and DynAdjust writes a lot.
    def drain(stream: Any, sink: list[str], report: bool) -> None:
        try:
            for line in stream:
                sink.append(line)
                if report and on_progress is not None:
                    on_progress(line.rstrip("\n"))
        except (ValueError, OSError):  # pragma: no cover - stream closed under us on kill
            pass

    readers = [
        threading.Thread(target=drain, args=(process.stdout, collected, True), daemon=True),
        threading.Thread(target=drain, args=(process.stderr, errors, False), daemon=True),
    ]
    for reader in readers:
        reader.start()

    timed_out = False
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        _terminate(process)
    finally:
        for reader in readers:
            reader.join(timeout=5.0)
        for stream in (process.stdout, process.stderr):
            if stream is not None:
                stream.close()

    return EngineRun(
        program=program or Path(command[0]).name,
        command=tuple(str(part) for part in command),
        exit_code=process.returncode if process.returncode is not None else -1,
        stdout="".join(collected),
        stderr="".join(errors),
        seconds=time.monotonic() - started,
        work_dir=work_dir,
        version=version,
        timed_out=timed_out,
        environment=dict(environment or {}),
    )


def _terminate(process: subprocess.Popen) -> None:
    """Kill the process group, politely then not.

    SIGTERM first so the engine can close its files -- a half-written binary
    working file left behind is a file the next run reads as valid.
    """
    import signal

    try:
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
    except (ProcessLookupError, PermissionError, AttributeError):
        process.terminate()
    try:
        process.wait(timeout=5.0)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        except (ProcessLookupError, PermissionError, AttributeError):
            process.kill()
