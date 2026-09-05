# SPDX-License-Identifier: GPL-2.0-or-later
"""The DynAdjust pipeline: prepare, run, parse (FR-321, FR-325).

``specs/07-engine-dynadjust.md`` section 3. DynAdjust is a suite, not one
program, so a run is a sequence of them over a shared working directory:

.. code-block:: text

    dnaimport  -> dnareftran -> dnageoid -> dnasegment -> dnaadjust
    (always)      (frame or     (ortho-     (large        (always)
                   epoch          metric      networks)
                   differs)       heights)

**Which stages run is decided from the job, and recorded.** ``dnareftran`` when
the target frame or epoch differs from the input's, ``dnageoid`` when
orthometric heights participate, ``dnasegment`` when the station count passes a
threshold. Each decision is kept on the :class:`PreparedJob` with the reason, so
"why did this run take four minutes" and "why is this solution in a different
frame" are answerable from the result rather than from the code.

**``prepare``, ``run`` and ``parse`` are separate** (FR-325). Advanced mode stops
after ``prepare`` so the user can read or edit the generated input, then
continues; nothing in ``prepare`` starts a process, and nothing in ``parse``
needs one.

**GeoComp always states the output options rather than accepting the defaults.**
Two reasons. The parsers need the covariances and corrections, which are off by
default. And the angular format appears nowhere in a ``.xyz`` or ``.apu``
(section 5.1), so the only way those files can be read without guessing is for
the caller to know what it asked for -- which it does, because it asked here.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from geocomp.core.errors import ComputationError, ValidationError
from geocomp.core.geodesy.projection import ProjectionParameters
from geocomp.core.models.epoch import Epoch
from geocomp.core.models.network import Network
from geocomp.core.models.position import HeightType
from geocomp.core.models.solution import Provenance, Solution
from geocomp.engines.base import (
    DEFAULT_TIMEOUT,
    EngineAbsentError,
    EngineRun,
    EngineVersion,
    ProgressCallback,
    discover,
    run_process,
)
from geocomp.engines.dynadjust.dynaml import station_names, write_measurement_file, write_station_file
from geocomp.engines.dynadjust.formats import format_epoch
from geocomp.engines.dynadjust.read_output import (
    SUPPORTED_LAYOUTS,
    AngularFormat,
    printed_rows,
)
from geocomp.engines.dynadjust.solution import read_solution

__all__ = [
    "DynAdjustEngine",
    "DynAdjustJob",
    "PreparedJob",
    "Stage",
    "check_import",
    "dynadjust_epoch",
    "imported_counts",
    "parse_version",
    "plan",
]

#: The programs a pipeline may use, in the order they run.
PROGRAMS = ("dnaimport", "dnareftran", "dnageoid", "dnasegment", "dnaadjust")

#: Above this many stations, segment before adjusting. DynAdjust's own default
#: block size is 500 stations (``dnasegment --max-block-stns``), and a network
#: below that gains nothing from being cut into one block.
SEGMENTATION_THRESHOLD = 500

#: The angular format GeoComp asks for and therefore knows how to read back.
#: HP is DynAdjust's own default; naming it explicitly costs nothing and means
#: a change of default upstream cannot silently change what the parsers read.
ANGULAR_FORMAT = AngularFormat.HP


#: ``dnaadjust --version`` prints a banner; this is the line that names the
#: version, e.g. ``+ Version:      1.4.0, Release with OpenBLAS``.
_VERSION_LINE = re.compile(r"^\+?\s*Version:\s*([^\s,]+)", re.MULTILINE)


def parse_version(text: str, *, path: Path, program: str = "dnaadjust") -> EngineVersion | None:
    """The version out of a ``--version`` banner, or ``None`` if it says none.

    ``tested`` compares ``major.minor`` against the layouts the output parsers
    were checked against, and a mismatch is a **warning, not a refusal**
    (FR-302): a user with a newer DynAdjust should be told the parsers may not
    match it, not stopped from running it. The refusal, when it comes, comes
    from the parser meeting an unfamiliar file -- which is where it can name the
    column that moved.
    """
    match = _VERSION_LINE.search(text)
    if not match:
        return None
    version = match.group(1).strip()
    layout = ".".join(version.split(".")[:2])
    return EngineVersion(
        name=program,
        version=version,
        path=path,
        tested=layout in SUPPORTED_LAYOUTS,
        source="detect",
        raw=text.strip(),
    )


@dataclass(frozen=True)
class Stage:
    """One program of the pipeline, and why it is or is not in it."""

    program: str
    arguments: tuple[str, ...] = ()
    included: bool = True
    #: Why this stage runs, or why it does not. Kept in the provenance, because
    #: "dnareftran did not run" is only useful beside "the frames matched".
    reason: str = ""


@dataclass(frozen=True)
class DynAdjustJob:
    """What to adjust, and in what frame.

    Attributes:
        network: The stations and observations. Its own ``crs`` and ``epoch``
            are the *input* frame.
        target_frame: The frame to adjust in. Defaults to the network's own,
            which is what makes ``dnareftran`` skippable.
        target_epoch: Likewise for the epoch. Never inferred (FR-105): a job
            that names neither adjusts in the frame the data is already in.
        geoid_grid: An NTv2 grid, when orthometric heights participate.
        confidence: For the chi-square test and the positional uncertainties.
        iteration_threshold: Metres. DynAdjust's default is 0.0005.
        maximum_iterations: DynAdjust's default is 10.
        phased: Force the phased adjustment. ``None`` decides from the size.
        segmentation_threshold: Station count above which to segment.
    """

    network: Network
    name: str = "geocomp"
    target_frame: str = ""
    target_epoch: Epoch | None = None
    geoid_grid: str | Path | None = None
    confidence: float = 0.95
    iteration_threshold: float = 0.0005
    maximum_iterations: int = 10
    phased: bool | None = None
    segmentation_threshold: int = SEGMENTATION_THRESHOLD
    #: How to invert the network's projection, when its positions are projected.
    #:
    #: DynAdjust has no way to take a grid coordinate. GeoComp can invert a
    #: Transverse Mercator (``core.geodesy.projection``) but cannot tell *which*
    #: projection a CRS string names -- that needs a projection database
    #: (``specs/07`` section 4.4) -- so the caller states it, or the job is
    #: refused rather than writing an easting where a latitude belongs.
    projection: ProjectionParameters | None = None
    #: ``{station id: N}`` in metres, for a projected network with orthometric
    #: heights. DynaML's LLH height is *h* above the ellipsoid (FR-804).
    geoid_undulations: dict[str, float] = field(default_factory=dict)
    #: Adjust anyway when some observations have no DynAdjust equivalent.
    #:
    #: Off by default, and that is the whole point. Three GeoComp observation
    #: types have no DynAdjust type (specs/07 §4.2): the two gravity ones, and
    #: ``HORIZONTAL_DISTANCE`` -- which is the *dominant* type in a plane
    #: trilateration or traverse. Adjusting what is left gives an answer to a
    #: different network, with a variance factor and residuals that look
    #: entirely healthy, and nothing in the result says which observations were
    #: not in it. Turning this on is a statement that a partial network is what
    #: was wanted; the skipped observations are still reported either way.
    allow_partial: bool = False

    def __post_init__(self) -> None:
        if not self.network.stations:
            raise ValidationError(
                "dynadjust_job_without_stations",
                network=self.network.id,
                expected="a network with at least one station",
            )
        if not 0.0 < self.confidence < 1.0:
            raise ValidationError(
                "dynadjust_confidence_out_of_range",
                received=self.confidence,
                expected="a probability strictly between 0 and 1",
            )
        # FR-105, checked here rather than left to the writer: a job with no
        # frame or no epoch cannot be run, and finding that out after the input
        # files are half written makes the message about the wrong thing.
        if not self.frame or self.epoch is None:
            raise ValidationError(
                "dynadjust_job_frame_or_epoch_missing",
                received={"frame": self.frame, "epoch": str(self.epoch) if self.epoch else ""},
                expected=(
                    "an explicit reference frame and epoch, on the job or on the network. "
                    "GeoComp will not infer either: a frame it guessed is a datum shift "
                    "absorbed into the residuals"
                ),
            )

    @property
    def frame(self) -> str:
        """The frame to adjust in: the target when given, else the input's."""
        return self.target_frame or self.network.crs

    @property
    def epoch(self) -> Epoch | None:
        return self.target_epoch or self.network.epoch


@dataclass(frozen=True)
class PreparedJob:
    """Everything ``prepare`` produced, and the plan ``run`` will follow."""

    job: DynAdjustJob
    work_dir: Path
    station_file: Path
    measurement_file: Path
    stages: tuple[Stage, ...]
    #: GeoComp name -> the name written to the file. Empty when nothing was
    #: renamed; the parsers need it to read a name back out of a fixed-width
    #: column it overflows.
    names: dict[str, str] = field(default_factory=dict)
    skipped: tuple[str, ...] = ()

    @property
    def mode(self) -> str:
        """``"phased"`` or ``"simult"``: the infix DynAdjust puts in its output
        file names, so the files can be found without globbing."""
        adjust = next(stage for stage in self.stages if stage.program == "dnaadjust")
        return "phased" if "--phased-adjustment" in stage_arguments(adjust) else "simult"

    def output(self, suffix: str) -> Path:
        return self.work_dir / f"{self.job.name}.{self.mode}.{suffix}"

    @property
    def included(self) -> tuple[Stage, ...]:
        return tuple(stage for stage in self.stages if stage.included)


def stage_arguments(stage: Stage) -> tuple[str, ...]:
    return stage.arguments


def dynadjust_epoch(epoch: Epoch) -> str:
    """An :class:`Epoch` as DynAdjust's ``dd.mm.yyyy`` (Guide Table B.5).

    The instant wins when there is one, because it says which day. An epoch that
    carries only a decimal year is converted by the same definition
    :meth:`Epoch.from_datetime` uses in reverse -- arithmetic, not a guess --
    and the result is rounded to the day, which is all the format can hold.
    """
    instant = epoch.instant
    if instant is None:
        year = int(epoch.decimal_year)
        start = datetime(year, 1, 1, tzinfo=UTC)
        length = datetime(year + 1, 1, 1, tzinfo=UTC) - start
        instant = start + (epoch.decimal_year - year) * length
    instant = instant.astimezone(UTC)
    return format_epoch(instant.day, instant.month, instant.year)


def _needs_geoid(network: Network) -> bool:
    """Do orthometric heights take part? (FR-804)

    Asked of the stations' height types rather than of whether a grid was
    supplied, so a job that needs a geoid and was not given one is a stated
    error instead of a silently ellipsoidal answer.
    """
    return any(
        station.approx_position is not None
        and station.approx_position.height_type is HeightType.ORTHOMETRIC
        for station in network.stations.values()
    )


def plan(job: DynAdjustJob) -> tuple[Stage, ...]:
    """Which programs this job runs, in order, each with its reason.

    Every stage appears, included or not. A pipeline that silently omitted the
    stages it did not need would make a provenance record that cannot answer
    "was this transformed?" -- and "no" and "the question was never asked" are
    different answers.
    """
    network = job.network
    stages: list[Stage] = [
        Stage(
            "dnaimport",
            ("-n", job.name, f"{job.name}-stn.xml", f"{job.name}-msr.xml"),
            reason="always: it validates the input and builds the binary working files",
        )
    ]

    # A transformation needs a frame to transform *from*. An input that states
    # none is not in a different frame -- it is in an unrecorded one, and
    # transforming out of that would apply a shift computed from an assumption
    # (FR-105). So an unstated input frame or epoch means the job's own is taken
    # as a statement of what the data already is, and dnareftran stays out.
    frame_differs = bool(network.crs and job.target_frame and job.target_frame != network.crs)
    epoch_differs = bool(
        network.epoch is not None
        and job.target_epoch is not None
        and job.target_epoch.decimal_year != network.epoch.decimal_year
    )
    reftran: list[str] = ["-n", job.name]
    if frame_differs:
        reftran += ["-r", job.frame]
    if epoch_differs and job.epoch is not None:
        reftran += ["-e", dynadjust_epoch(job.epoch)]

    if frame_differs and epoch_differs:
        reason = (
            f"frame {network.crs} -> {job.frame} and epoch "
            f"{network.epoch} -> {job.epoch}"
        )
    elif frame_differs:
        reason = f"the frame differs: {network.crs} -> {job.frame}"
    elif epoch_differs:
        reason = f"the epoch differs: {network.epoch} -> {job.epoch}"
    elif not network.crs:
        reason = (
            f"the input states no frame, so {job.frame} is taken as the frame it is "
            "already in; transforming out of an unrecorded frame would apply a shift "
            "computed from a guess (FR-105)"
        )
    else:
        reason = "the input is already in the target frame and epoch"
    stages.append(
        Stage("dnareftran", tuple(reftran), included=frame_differs or epoch_differs, reason=reason)
    )

    # Orthometric heights need the separation applied -- but not necessarily by
    # dnageoid. When the job carries per-station undulations the writer has
    # already turned H into h, so the heights DynAdjust receives are ellipsoidal
    # and there is nothing left for this stage to do. Running it anyway would
    # apply the separation twice.
    applied_by_geocomp = bool(job.geoid_undulations)
    geoid = _needs_geoid(network) and not applied_by_geocomp
    stages.append(
        Stage(
            "dnageoid",
            ("-n", job.name, "-g", str(job.geoid_grid), "--convert-stn-hts") if geoid else (),
            included=geoid,
            reason=(
                "orthometric heights take part, so the geoid separation is needed (FR-804)"
                if geoid
                else (
                    "the heights were converted with the undulations the job supplied, "
                    "so they reach DynAdjust ellipsoidal already"
                    if applied_by_geocomp
                    else "every height is ellipsoidal; no geoid is involved"
                )
            ),
        )
    )

    large = len(network.stations) > job.segmentation_threshold
    phased = large if job.phased is None else job.phased
    stages.append(
        Stage(
            "dnasegment",
            ("-n", job.name, "--max-block-stns", str(job.segmentation_threshold)),
            included=phased,
            reason=(
                f"{len(network.stations)} stations, above the threshold of "
                f"{job.segmentation_threshold}"
                if large
                else (
                    "a phased adjustment was asked for"
                    if phased
                    else f"{len(network.stations)} stations adjust simultaneously"
                )
            ),
        )
    )

    adjust = [
        "-n",
        job.name,
        "--phased-adjustment" if phased else "--simultaneous-adjustment",
        "--conf-interval",
        f"{job.confidence * 100:g}",
        "--iteration-threshold",
        f"{job.iteration_threshold:g}",
        "--max-iterations",
        str(job.maximum_iterations),
        # Everything the parsers read. Off by default, every one of them.
        "--output-adj-msr",
        "--output-pos-uncertainty",
        "--output-all-covariances",
        "--output-corrections-file",
        "--stn-corrections",
        # Stated rather than assumed: see the module docstring.
        "--angular-stn-type",
        "0" if ANGULAR_FORMAT is AngularFormat.HP else "1",
        "--output-apu-vcv-units",
        "0",
    ]
    stages.append(
        Stage("dnaadjust", tuple(adjust), reason="always: it is the adjustment")
    )
    return tuple(stages)


#: ``dnaimport`` reports what it took in, e.g. ``Loaded 36 measurements in 0.002s``.
_LOADED = re.compile(r"Loaded\s+(\d+)\s+(stations?|measurements?)", re.IGNORECASE)


def imported_counts(stdout: str) -> dict[str, int]:
    """What ``dnaimport`` says it loaded, summed over the input files."""
    counts = {"stations": 0, "measurements": 0}
    for number, kind in _LOADED.findall(stdout):
        counts["stations" if kind.lower().startswith("station") else "measurements"] += int(number)
    return counts


def check_import(run: EngineRun, prepared: PreparedJob) -> None:
    """Did ``dnaimport`` take in everything GeoComp wrote?

    **It exits 0 when it could not parse a file at all.** Given a measurement
    file that is not one, it prints ``Warning: some files were not parsed`` and
    ``there are no measurements to process``, and returns success; the failure
    then appears at ``dnaadjust``, or -- when only *part* of a file failed to
    parse -- not at all. That last case is the dangerous one: an adjustment of
    fewer observations than intended, with a variance factor that looks fine.

    So the exit code is not the whole test. GeoComp knows how many stations and
    measurement components it wrote, ``dnaimport`` reports how many it read, and
    a difference is a refusal naming both. Counting rather than matching the
    warning text: the counts are the thing that actually matters, and they do
    not change wording between releases.
    """
    counts = imported_counts(run.stdout)
    if not counts["stations"] and not counts["measurements"]:
        # No count line at all -- an output format this does not recognise.
        # Not a failure on its own; the exit code and the later stages still
        # apply, and refusing here would reject a version over its phrasing.
        return
    expected_stations = len(prepared.job.network.stations)
    expected_measurements = len(printed_rows(prepared.job.network))
    if (
        counts["stations"] != expected_stations
        or counts["measurements"] != expected_measurements
    ):
        raise ComputationError(
            "dynadjust_import_incomplete",
            expected={"stations": expected_stations, "measurements": expected_measurements},
            received=counts,
            diagnostic=run.diagnostic[-2000:],
            hint=(
                "dnaimport reported success but did not take in everything GeoComp "
                "wrote; adjusting the remainder would give a plausible answer to a "
                "different network"
            ),
        )


class DynAdjustEngine:
    """The DynAdjust adapter (FR-303).

    Holds no state beyond how to find the programs, so one instance serves any
    number of jobs and two jobs cannot interfere through it.
    """

    name = "dynadjust"

    def __init__(
        self,
        *,
        configured_directory: str | Path | None = None,
        extra_directories: tuple[Path, ...] = (),
    ) -> None:
        self._configured = Path(configured_directory) if configured_directory else None
        self._extra = extra_directories

    def locate(self, program: str) -> Path:
        """Where *program* is, or a refusal naming what to install.

        Raises :class:`~geocomp.engines.base.EngineAbsentError` rather than
        returning ``None``: by the time a stage needs a program, absence is a
        failure of this run and not a fact to be handled inline.
        """
        configured = self._configured / program if self._configured else None
        path, _ = discover(program, configured=configured, extra_directories=self._extra)
        if path is None:
            raise EngineAbsentError(
                "dynadjust_program_not_found",
                program=program,
                engine=self.name,
                hint="install DynAdjust, or set the engine directory in the settings",
            )
        return path

    def detect(self) -> EngineVersion | None:
        """The installed version, or ``None``. Never raises for absence."""
        try:
            path = self.locate("dnaadjust")
        except EngineAbsentError:
            return None
        try:
            run = run_process([str(path), "--version"], work_dir=Path.cwd(), program="dnaadjust")
        except (OSError, ComputationError):
            return None
        return parse_version(run.stdout, path=path)

    def prepare(self, job: DynAdjustJob, work_dir: str | Path) -> PreparedJob:
        """Write the input files and settle the plan. No process is started."""
        work_dir = Path(work_dir)
        work_dir.mkdir(parents=True, exist_ok=True)

        stages = plan(job)
        geoid_stage = next(stage for stage in stages if stage.program == "dnageoid")
        # Per-station undulations are a geoid model too, in a coarser form: the
        # writer uses them to turn H into the h DynaML's LLH height means, which
        # is the same job dnageoid does from a grid. Requiring the grid as well
        # would refuse a network whose height systems are already related.
        if geoid_stage.included and not (job.geoid_grid or job.geoid_undulations):
            raise ValidationError(
                "dynadjust_geoid_grid_required",
                network=job.network.id,
                expected=(
                    "a geoid grid, or per-station undulations; orthometric heights "
                    "take part in this network"
                ),
                hint="FR-804: the height systems cannot be related without one",
            )

        epoch = dynadjust_epoch(job.epoch) if job.epoch is not None else ""
        names = station_names(job.network)
        station_file = work_dir / f"{job.name}-stn.xml"
        measurement_file = work_dir / f"{job.name}-msr.xml"
        write_station_file(
            job.network,
            station_file,
            frame=job.frame,
            epoch=epoch,
            names=names,
            projection=job.projection,
            undulations=job.geoid_undulations or None,
        )
        document = write_measurement_file(
            job.network, measurement_file, frame=job.frame, epoch=epoch, names=names
        )
        skipped = tuple(document.skipped)
        if skipped and not job.allow_partial:
            kinds = sorted({reason for _, reason in skipped})
            raise ValidationError(
                "dynadjust_network_would_be_partial",
                network=job.network.id,
                skipped=len(skipped),
                of=len(job.network.observations),
                reasons=kinds[:5],
                expected="a network every observation of which DynAdjust can represent",
                hint=(
                    "adjusting the remainder answers a different question, with a "
                    "variance factor that looks healthy and nothing in the result "
                    "saying what was left out; set allow_partial to accept that"
                ),
            )
        return PreparedJob(
            job=job,
            work_dir=work_dir,
            station_file=station_file,
            measurement_file=measurement_file,
            stages=stages,
            names=names,
            skipped=skipped,
        )

    def run(
        self,
        prepared: PreparedJob,
        *,
        timeout: float = DEFAULT_TIMEOUT,
        on_progress: ProgressCallback | None = None,
    ) -> list[EngineRun]:
        """Execute the planned stages, one :class:`EngineRun` each.

        Stops at the first failure and raises, with that stage's own stderr in
        the message: DynAdjust's import diagnostics name the station and the
        line, and are more use to a surveyor than anything GeoComp could write
        about them (FR-305). The runs completed so far travel on the error, so a
        caller can still show what happened before the failure.
        """
        version = self.detect()
        runs: list[EngineRun] = []
        for stage in prepared.included:
            path = self.locate(stage.program)
            run = run_process(
                [str(path), *stage.arguments],
                work_dir=prepared.work_dir,
                program=stage.program,
                timeout=timeout,
                on_progress=on_progress,
                version=version,
            )
            runs.append(run)
            if run.exit_code == 0 and stage.program == "dnaimport":
                check_import(run, prepared)
            if run.exit_code != 0:
                raise ComputationError(
                    "dynadjust_stage_failed",
                    program=stage.program,
                    exit_code=run.exit_code,
                    # ``diagnostic`` already prefers stderr and falls back to
                    # stdout; the tail keeps a long build log out of the message.
                    diagnostic=run.diagnostic[-2000:],
                    completed=[completed.program for completed in runs[:-1]],
                )
        return runs

    def parse(self, runs: list[EngineRun], prepared: PreparedJob) -> Solution:
        """Read the outputs back into a :class:`Solution` (FR-322, FR-323).

        The ``.apu`` and ``.cor`` are passed only when they exist. They always
        should -- ``plan`` asks for both -- but a stage that was interrupted can
        leave one missing, and a clear "no covariances" beats a stack trace.
        """
        adjust = prepared.output("adj")
        if not adjust.is_file():
            raise ComputationError(
                "dynadjust_output_missing",
                expected=str(adjust),
                hint="dnaadjust reported success but wrote no adjustment file",
            )
        uncertainty = prepared.output("apu")
        corrections = prepared.output("cor")
        return read_solution(
            adjust,
            network=prepared.job.network,
            apu_path=uncertainty if uncertainty.is_file() else None,
            cor_path=corrections if corrections.is_file() else None,
            angular_format=ANGULAR_FORMAT,
            provenance=provenance(runs, prepared),
        )

    def adjust(
        self,
        job: DynAdjustJob,
        work_dir: str | Path,
        *,
        timeout: float = DEFAULT_TIMEOUT,
        on_progress: ProgressCallback | None = None,
    ) -> Solution:
        """The whole pipeline, for callers that do not need to stop in between."""
        prepared = self.prepare(job, work_dir)
        runs = self.run(prepared, timeout=timeout, on_progress=on_progress)
        return self.parse(runs, prepared)


def provenance(runs: list[EngineRun], prepared: PreparedJob) -> Provenance:
    """What was run, in what order, and with which stages left out and why.

    NFR-010: the command lines are recorded, and they carry no credential --
    DynAdjust takes none. The *reasons* are recorded beside the stages because a
    provenance that lists only what ran cannot distinguish a transformation that
    was unnecessary from one that was forgotten.
    """
    version = next((run.version for run in runs if run.version is not None), None)
    return Provenance.now(
        source="dynadjust",
        engine="dynadjust",
        engine_version=version.version if version else "",
        command_line=" && ".join(" ".join(run.command) for run in runs),
        exit_code=next((run.exit_code for run in runs if run.exit_code != 0), 0),
        parameters={
            "mode": prepared.mode,
            "frame": prepared.job.frame,
            "confidence": prepared.job.confidence,
            "iteration_threshold": prepared.job.iteration_threshold,
            "stages": [
                {"program": stage.program, "ran": stage.included, "reason": stage.reason}
                for stage in prepared.stages
            ],
            "skipped_observations": list(prepared.skipped),
        },
        input_ids=(prepared.job.network.id,),
    )
