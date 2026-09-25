# SPDX-License-Identifier: GPL-2.0-or-later
"""Running ``rnx2rtkp`` (FR-355, FR-302, FR-304, FR-306, FR-036).

``specs/08-engine-rtklib.md``. The process handling is not repeated here:
:mod:`geocomp.engines.base` already launches engines, captures everything a run
produced, distinguishes a timeout from a failure, and reports an absent engine
as something the user can act on. It was written engine-agnostic in P6 and
needed no change for a second engine, which is the test of whether an
abstraction was one.

What is here is what is specific to this engine: which programs it is, how it
states its version, how a job becomes a command line, and how a failure is
told apart from a run that produced no solution.

**A run that exits zero may still have solved nothing.** ``rnx2rtkp`` reports
missing ephemerides, unusable observations and an empty overlap on stderr and
still exits successfully, leaving a ``.pos`` with a header and no records. So
success is judged on the *solution*, not on the exit code -- the same lesson
``specs/07`` section 4.3 records for ``dnaimport``, learned again here.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from geocomp.core.errors import ComputationError, EngineError
from geocomp.core.models import GnssSession
from geocomp.engines.base import (
    DEFAULT_TIMEOUT,
    EngineRun,
    EngineVersion,
    ProgressCallback,
    discover,
    run_process,
)
from geocomp.engines.rtklib.config import RtklibConfig, profile, write_config
from geocomp.engines.rtklib.read_pos import PosSolution, read_pos

__all__ = [
    "PROGRAM",
    "RtklibEngine",
    "RtklibJob",
    "RtklibResult",
    "command_line",
    "parse_version",
    "program_filenames",
]

#: The one program this adapter runs. RTKLIB is a suite, but post-processing a
#: session is ``rnx2rtkp`` alone -- unlike DynAdjust, where a job is a pipeline
#: of five programs.
PROGRAM = "rnx2rtkp"

#: Versions whose ``.pos`` layout the parser was written against. Outside this
#: range is a **warning, not a refusal** (FR-302): a user with a newer engine
#: should be told the parsers may not match it, not prevented from working.
TESTED_VERSIONS = ("2.4.3", "2.5.1")


def program_filenames(program: str = PROGRAM) -> tuple[str, ...]:
    """What the executable may be called. Windows appends ``.exe``."""
    return (program, f"{program}.exe")


_VERSION = re.compile(r"RTKLIB\s+(?:(?P<distribution>[A-Za-z]+)\s+)?(?P<version>[0-9][0-9.]*\w*)")


def parse_version(text: str, *, path: Path) -> EngineVersion | None:
    """Read ``rnx2rtkp --version``.

    RTKLIB-EX prints ``rnx2rtkp RTKLIB EX 2.5.1`` and Takasu's original prints
    its version without a distribution word. Both are recorded whole: FR-302
    asks which distribution produced a result, and the two forks' behaviour can
    differ even at the same nominal version.
    """
    match = _VERSION.search(text)
    if match is None:
        return None
    distribution = match.group("distribution") or ""
    version = match.group("version")
    return EngineVersion(
        name=f"RTKLIB{f'-{distribution}' if distribution else ''}",
        version=version,
        path=path,
        tested=version in TESTED_VERSIONS,
        source="",
        raw=text.strip(),
    )


@dataclass(frozen=True)
class RtklibJob:
    """One ``rnx2rtkp`` invocation, as data.

    Attributes:
        rover: The session being positioned.
        base: The reference session. Required for every relative mode and
            forbidden for the absolute ones -- passing a base to a PPP run is
            not an error RTKLIB reports, it simply ignores it, and a user who
            thought they were processing a baseline would get a PPP solution
            labelled as one.
        products: Positional product inputs, such as precise ephemeris and clock files. Supplied by the
            caller; **GeoComp does not download them in this phase** -- see
            ``specs/22`` section 5 and the P7 entry in the roadmap. ANTEX is
            configured through ``file-rcvantfile`` / ``file-satantfile`` in
            ``config.extra``; rnx2rtkp does not load positional ANTEX inputs.
        window: Process only the epochs inside ``(start, end)``, **inclusive at
            both ends** -- ``-te`` selects the epoch landing on the bound, so
            two consecutive windows written from the same instant share it.
            ``None`` processes everything the files hold, which is the ordinary
            case: a window is for solving part of a session, as the RD-06
            repeatability experiment does when it splits a day into hours.

            **These are GPST calendar labels, not UTC ones.** ``rnx2rtkp``
            builds its comparison time with ``epoch2time`` and compares it
            against observation times, which are GPST; so is ``TIME OF FIRST
            OBS`` in a GPS RINEX header, and so are the labels
            :class:`~geocomp.engines.rtklib.read_pos.PosSolution` reads back.
            All four carry ``tzinfo=UTC`` for arithmetic and ordering and none
            of them is UTC -- converting one would move it by the leap seconds
            and silently select the wrong epochs.
    """

    rover: GnssSession
    base: GnssSession | None = None
    config: RtklibConfig = field(default_factory=lambda: profile("relative-static"))
    products: tuple[str, ...] = ()
    timeout: float = DEFAULT_TIMEOUT
    window: tuple[datetime, datetime] | None = None

    def __post_init__(self) -> None:
        if self.config.mode.is_relative and self.base is None:
            raise ComputationError(
                "rtklib_relative_mode_needs_a_base",
                mode=self.config.mode.value,
                rover=self.rover.id,
                expected="a base session; a relative mode differences two receivers",
            )
        if not self.config.mode.is_relative and self.base is not None:
            raise ComputationError(
                "rtklib_absolute_mode_takes_no_base",
                mode=self.config.mode.value,
                base=self.base.id,
                expected=(
                    "no base session; rnx2rtkp ignores one in an absolute mode rather "
                    "than refusing it, so a baseline would silently become a PPP solution"
                ),
            )
        if self.base is not None and not self.rover.overlaps(self.base):
            raise ComputationError(
                "rtklib_sessions_do_not_overlap",
                rover=self.rover.id,
                base=self.base.id,
                expected="two sessions observing simultaneously; they share no epoch",
            )
        self._check_window()

    def _check_window(self) -> None:
        """Refuse a window that selects nothing, rather than solving nothing.

        Both failures reach the user identically otherwise: ``rnx2rtkp`` exits
        zero, writes a header and no records, and the adapter reports "the
        engine produced no solution" -- which sends the reader to the
        observations when the fault is in the two numbers they passed.
        """
        if self.window is None:
            return
        start, end = self.window
        if start.tzinfo is None or end.tzinfo is None:
            raise ComputationError(
                "rtklib_window_is_not_timezone_aware",
                window=f"{start.isoformat()}/{end.isoformat()}",
                expected=(
                    "both bounds carrying tzinfo=UTC, the convention every time in this "
                    "project uses -- a naive bound cannot be compared against the session's "
                    "own times, and Python raises a TypeError rather than saying so"
                ),
            )
        if end <= start:
            raise ComputationError(
                "rtklib_window_ends_before_it_starts",
                start=start.isoformat(),
                end=end.isoformat(),
                expected="a window whose end is after its start",
            )
        for session in (self.rover, self.base):
            if session is None or session.start is None or session.end is None:
                continue
            if start >= session.end or end <= session.start:
                raise ComputationError(
                    "rtklib_window_outside_the_session",
                    session=session.id,
                    window=f"{start.isoformat()}/{end.isoformat()}",
                    observed=f"{session.start.isoformat()}/{session.end.isoformat()}",
                    expected=(
                        "a window overlapping the observations; these are GPST "
                        "labels on both sides, so do not convert either to UTC"
                    ),
                )

    def input_files(self) -> tuple[str, ...]:
        """Inputs in the order ``rnx2rtkp`` reads them.

        **Rover first, then base**: the order is the interface, not a
        convention, and reversing it computes the baseline backwards while
        reporting success.
        """
        files = [self.rover.obs_file]
        if self.base is not None:
            files.append(self.base.obs_file)
        files.extend(self.rover.nav_files)
        if self.base is not None:
            files.extend(name for name in self.base.nav_files if name not in files)
        files.extend(self.products)
        return tuple(files)


@dataclass(frozen=True)
class RtklibResult:
    """What one job produced: the run, the solution, and where to look."""

    run: EngineRun
    solution: PosSolution
    config_file: Path
    output_file: Path

    @property
    def ok(self) -> bool:
        return self.run.ok and bool(self.solution.epochs)

    def to_dict(self) -> dict[str, Any]:
        return {
            "command": list(self.run.command),
            "exit_code": self.run.exit_code,
            "seconds": self.run.seconds,
            "config_file": str(self.config_file),
            "solution": self.solution.to_dict(),
        }


def _window_flags(window: tuple[datetime, datetime] | None) -> tuple[str, ...]:
    """``-ts`` and ``-te``, which have no configuration-file equivalent.

    ``rnx2rtkp`` reads each as two arguments -- ``y/m/d`` then ``h:m:s`` -- and
    parses them with ``sscanf("%lf/%lf/%lf")``, so an ISO ``2025-01-01`` is
    read as the year alone and the window silently becomes the year 2025 from
    January the first: not an error, just every epoch selected.
    """
    if window is None:
        return ()
    flags: list[str] = []
    for flag, moment in zip(("-ts", "-te"), window, strict=True):
        flags += [flag, moment.strftime("%Y/%m/%d"), moment.strftime("%H:%M:%S.%f")[:-3]]
    return tuple(flags)


def command_line(
    executable: Path, job: RtklibJob, *, config_file: Path, output_file: Path
) -> tuple[str, ...]:
    """The command for *job*.

    Only four flags, plus the time window where the job sets one: ``-k`` for
    the configuration, ``-o`` for the output, ``-ts``/``-te`` for the window,
    and the inputs. Everything else is in the file, per ``specs/08`` section 2
    -- which is what makes a run reproducible from something the user can read.
    The window is a flag because it has no configuration-file key; it is
    recorded in provenance through the command line, which is stored whole.

    **Every input path is made absolute here.** The process runs in the working
    directory, not in the caller's, so a relative path that was correct when the
    session was discovered resolves to nothing by the time the engine opens it
    -- and ``rnx2rtkp`` reports that as ``error : no obs data``, which sounds
    like a problem with the observations rather than with where they were
    looked for.
    """
    return (
        str(executable),
        "-k", str(Path(config_file).resolve()),
        "-o", str(Path(output_file).resolve()),
        *_window_flags(job.window),
        *(str(Path(name).resolve()) for name in job.input_files()),
    )


class RtklibEngine:
    """The ``rnx2rtkp`` adapter.

    Args:
        configured: An explicitly configured executable path, which always wins
            over the managed installation and over ``PATH`` (ADR-0003 rule 4).
    """

    name = "rtklib"

    def __init__(self, *, configured: str | Path | None = None) -> None:
        self._configured = configured
        self._version: EngineVersion | None = None

    def locate(self) -> tuple[Path | None, str]:
        for candidate in program_filenames():
            path, source = discover(candidate, configured=self._configured)
            if path is not None:
                return path, source
        return None, "not found"

    @property
    def available(self) -> bool:
        """Whether the engine is present. GNSS processing is disabled with an
        explanation rather than failing mid-run when it is not (FR-306)."""
        return self.locate()[0] is not None

    def version(self) -> EngineVersion | None:
        if self._version is not None:
            return self._version
        path, source = self.locate()
        if path is None:
            return None
        run = run_process(
            [str(path), "--version"], work_dir=path.parent, program=PROGRAM, timeout=30.0
        )
        # The version goes to stderr in some builds and stdout in others, so
        # both are searched rather than one being assumed.
        parsed = parse_version(f"{run.stdout}\n{run.stderr}", path=path)
        if parsed is not None:
            self._version = EngineVersion(
                name=parsed.name,
                version=parsed.version,
                path=parsed.path,
                tested=parsed.tested,
                source=source,
                raw=parsed.raw,
            )
        return self._version

    def run(
        self,
        job: RtklibJob,
        *,
        work_dir: str | Path,
        on_progress: ProgressCallback | None = None,
    ) -> RtklibResult:
        """Run *job* in *work_dir* and parse what it produced.

        The working directory is **retained**, as ``EngineRun`` requires: the
        configuration, the command line and the engine's own output are what a
        user reproduces a run from or attaches to a bug report (FR-955).

        Raises:
            EngineAbsentError: if ``rnx2rtkp`` cannot be found (FR-306).
            EngineError: if the run failed, or if it succeeded and solved
                nothing -- with the engine's own message, not an exit code.
        """
        from geocomp.engines.base import require

        work_dir = Path(work_dir)
        work_dir.mkdir(parents=True, exist_ok=True)
        version = require(self.version(), engine=PROGRAM, operation="GNSS processing")

        config_file = write_config(job.config, work_dir / "rnx2rtkp.conf")
        output_file = work_dir / f"{job.rover.id}.pos"
        command = command_line(
            version.path, job, config_file=config_file, output_file=output_file
        )
        run = run_process(
            command,
            work_dir=work_dir,
            program=PROGRAM,
            timeout=job.timeout,
            on_progress=on_progress,
            version=version,
        )

        if not run.ok:
            raise EngineError(
                "rtklib_run_failed",
                engine=PROGRAM,
                exit_code=run.exit_code,
                timed_out=run.timed_out,
                command=" ".join(run.command),
                message=_diagnostic(run),
                work_dir=str(work_dir),
            )
        if not output_file.is_file():
            raise EngineError(
                "rtklib_wrote_no_output",
                engine=PROGRAM,
                command=" ".join(run.command),
                message=_diagnostic(run),
                work_dir=str(work_dir),
                expected=f"a solution file at {output_file.name}",
            )

        solution = read_pos(output_file)
        if not solution.epochs:
            # Exit zero and nothing solved. The engine says why on stderr, and
            # relaying that beats reporting a successful run with no answer.
            raise EngineError(
                "rtklib_produced_no_solution",
                engine=PROGRAM,
                rover=job.rover.id,
                base=job.base.id if job.base else "",
                message=_diagnostic(run),
                work_dir=str(work_dir),
                expected=(
                    "at least one solution epoch; the run exited zero, which for this "
                    "engine does not mean it solved anything"
                ),
            )
        return RtklibResult(
            run=run, solution=solution, config_file=config_file, output_file=output_file
        )


def _diagnostic(run: EngineRun) -> str:
    """The engine's own last word, which is what the user needs.

    ``specs/08`` section 9 requires a failure to surface the engine's message
    rather than an exit code. ``rnx2rtkp`` writes progress to stderr too, so the
    last non-progress line is taken -- the progress lines are carriage-returned
    over each other and say nothing about why a run failed.
    """
    lines = [
        line.strip()
        for line in f"{run.stderr}\n{run.stdout}".replace("\r", "\n").splitlines()
        if line.strip() and not line.strip().startswith("processing :")
    ]
    return lines[-1] if lines else f"exit code {run.exit_code}"
