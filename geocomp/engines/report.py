# SPDX-License-Identifier: GPL-2.0-or-later
"""An engine's failure, packaged for the engine's developers (FR-955; P12c-48).

``specs/20`` section 8: "where a failure is in DynAdjust or RTKLIB, GeoComp
packages the exact inputs, configuration, command line and output that
reproduce it, so the report is actionable." The working folder already holds
the inputs and the configuration, kept on a failure or on request, and since
P12c-48 every run leaves its command, exit code, version and whole output there
too (:func:`geocomp.engines.base.keep_record`). This puts the folder in one zip
with a README a maintainer can read without GeoComp: which engine and version,
what ran in what order and how each run ended, and where the output is.

**In English, whatever the user's language.** It is written for the engines'
developers, not for the user, and both projects work in English.

**Nothing is left out, and the README says so.** The files are the user's
survey and may name folders on their computer; deciding what may be shared is
the user's, so the README asks them to look before they send, rather than
GeoComp guessing what to remove. No credential is in a working folder: GeoComp
fetches products through QGIS's authentication system and writes only the
files (NFR-010).

Imports no Qt.
"""

from __future__ import annotations

import json
import platform
import zipfile
from dataclasses import dataclass
from pathlib import Path

from geocomp.core.errors import ValidationError
from geocomp.engines.base import RUN_RECORD

__all__ = ["README", "UPSTREAM", "ProblemPackage", "package_problem"]

#: The README's name inside the zip.
README = "README-geocomp.txt"

#: Where each engine's developers take reports, as specs/07 and specs/08 cite
#: the projects: DynAdjust's repository, and the RTKLIB build GeoComp ships.
UPSTREAM: dict[str, str] = {
    "DynAdjust": "https://github.com/GeoscienceAustralia/DynAdjust/issues",
    "RTKLIB": "https://github.com/rtklibexplorer/RTKLIB/issues",
}


@dataclass(frozen=True)
class ProblemPackage:
    """What was packaged: the zip, the engine (``""`` when not recognised), its runs and how many files."""

    path: Path
    engine: str
    runs: int
    files: int
    failed: tuple[str, ...]


def _runs(folder: Path) -> list[dict]:
    record = folder / RUN_RECORD
    if not record.is_file():
        raise ValidationError(
            "engine_run_record_missing",
            folder=str(folder),
            expected=(
                f"a working folder an engine ran in since P12c-48, holding {RUN_RECORD}: the one a "
                "DynAdjust or RTKLIB refusal names, or one the run was asked to keep"
            ),
        )
    runs = []
    for line in record.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            runs.append(json.loads(line))
    return runs


def _engine(runs: list[dict]) -> str:
    """``DynAdjust``, ``RTKLIB``, or ``""`` for a program GeoComp does not know as either."""
    programs = {Path(run.get("program", "")).name for run in runs}
    if any(program.startswith("dna") for program in programs):
        return "DynAdjust"
    if any("rnx2rtkp" in program or "rtk" in program for program in programs):
        return "RTKLIB"
    return ""


def _ending(run: dict) -> str:
    if run.get("timed_out"):
        return f"stopped at its time limit after {run.get('seconds', 0.0):.1f} s"
    return f"exit code {run.get('exit_code')} after {run.get('seconds', 0.0):.1f} s"


def _readme(folder: Path, runs: list[dict], engine: str, *, geocomp: str, qgis: str) -> str:
    versions = sorted(
        {
            f"{run['version'].get('name', engine)} {run['version'].get('version', '?')} "
            f"({run['version'].get('path', '')})"
            for run in runs
            if run.get("version")
        }
    )
    lines = [
        f"A problem report prepared by GeoComp {geocomp} (QGIS {qgis}) on {platform.platform()}.",
        "",
        f"Engine: {engine or 'not recognised'}"
        + (f" -- {'; '.join(versions)}" if versions else ", version not recorded"),
    ]
    if engine in UPSTREAM:
        lines.append(f"Reported to: {UPSTREAM[engine]}")
    lines += ["", f"What ran, in order, in {folder}:"]
    for run in runs:
        lines.append(f"  {Path(run.get('program', '')).name}")
        lines.append("    $ " + " ".join(run.get("command", [])))
        lines.append(f"    {_ending(run)}")
    lines += [
        "",
        "Each program's whole output is in geocomp-<program>.stdout.txt and geocomp-<program>.stderr.txt.",
        f"{RUN_RECORD} records each run. The other files are the inputs, the configuration and whatever",
        "the engine wrote, as they stood when this was packaged.",
        "",
        "Before sending: these files are a survey's data, and the commands name folders on the computer",
        "that ran them. Remove what may not be shared; GeoComp has left everything in.",
        "",
    ]
    return "\n".join(lines)


def package_problem(
    folder: str | Path, destination: str | Path, *, geocomp: str = "", qgis: str = ""
) -> ProblemPackage:
    """Zip the working folder *folder* into *destination*, with a README for the engine's developers.

    Raises:
        ValidationError: ``engine_run_record_missing`` for a folder no engine has
            recorded a run in -- not a working folder, or one from before P12c-48.
    """
    folder = Path(folder)
    destination = Path(destination)
    runs = _runs(folder)
    engine = _engine(runs)
    files = sorted(
        path for path in folder.rglob("*") if path.is_file() and path.resolve() != destination.resolve()
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(README, _readme(folder, runs, engine, geocomp=geocomp, qgis=qgis))
        for path in files:
            archive.write(path, path.relative_to(folder).as_posix())
    failed = tuple(
        Path(run.get("program", "")).name
        for run in runs
        if run.get("timed_out") or run.get("exit_code") not in (0, None)
    )
    return ProblemPackage(destination, engine, len(runs), len(files), failed)
