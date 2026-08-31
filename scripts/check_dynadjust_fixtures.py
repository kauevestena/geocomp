#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Regenerate the DynAdjust output fixtures and check the committed ones match.

``tests/data/dynadjust/output`` holds real ``dnaadjust`` output, and every test
of the output parsers reads it rather than the engine. That is what keeps those
tests tier 1 -- they run wherever Python does. It is also how they go stale: a
DynAdjust that changed a column would keep passing against a fixture written by
the old one.

This is the guard. Given a DynAdjust on ``PATH`` it runs the same commands the
fixtures were made with and compares the result to what is committed, ignoring
only the lines that cannot help but differ: the timestamp, the build stamp, and
the paths. A difference anywhere else is a layout change, and it should fail
loudly the day it appears rather than the day someone trusts a wrong number.

Usage::

    python3 scripts/check_dynadjust_fixtures.py            # check
    python3 scripts/check_dynadjust_fixtures.py --write    # accept the new output
"""

from __future__ import annotations

import argparse
import difflib
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INPUTS = ROOT / "tests" / "data" / "dynadjust"
FIXTURES = INPUTS / "output"

#: Lines whose content depends on when, where and how fast the run happened
#: rather than on the engine's output format. Dropped before comparing.
#: ``Elapsed time`` and ``Total time`` are wall-clock measurements of a
#: sub-millisecond adjustment, so they differ between two runs of the *same*
#: binary on the same data -- keeping them would make this check fail always,
#: which is the same as not having it.
VOLATILE = (
    "Build:",
    "File created:",
    "File name:",
    "Input files:",
    "Command line arguments:",
    "Elapsed time",
    "Total time",
)


@dataclass(frozen=True)
class Case:
    """One ``dnaadjust`` run and the fixtures it produces."""

    name: str
    station_file: str
    measurement_file: str
    options: tuple[str, ...]
    #: fixture stem -> produced suffix, e.g. ``{"sample": ("adj", "apu")}``
    outputs: tuple[str, ...]
    prefix: str = ""
    extra: dict[str, str] = field(default_factory=dict)


CASES = (
    Case(
        name="sample",
        station_file="sample-stn.xml",
        measurement_file="sample-msr.xml",
        options=(
            "--output-adj-msr",
            "--output-pos-uncertainty",
            "--output-all-covariances",
            "--output-corrections-file",
            "--stn-corrections",
        ),
        outputs=("adj", "apu", "cor", "xyz"),
    ),
    Case(
        name="sample-no-covariances",
        station_file="sample-stn.xml",
        measurement_file="sample-msr.xml",
        options=("--output-adj-msr", "--output-pos-uncertainty", "--stn-corrections"),
        outputs=("apu",),
    ),
    Case(
        name="alt-flags",
        station_file="sample-stn.xml",
        measurement_file="sample-msr.xml",
        options=(
            "--output-adj-msr",
            "--output-tstat-adj-msr",
            "--output-pos-uncertainty",
            "--output-apu-vcv-units",
            "1",
            "--stn-coord-types",
            "PLH",
            "--angular-stn-type",
            "1",
        ),
        outputs=("adj", "apu", "xyz"),
    ),
    Case(
        name="angles",
        station_file="output/angles-stn.xml",
        measurement_file="output/angles-msr.xml",
        options=(
            "--output-adj-msr",
            "--output-pos-uncertainty",
            "--output-corrections-file",
            "--stn-corrections",
        ),
        outputs=("adj", "apu", "cor", "xyz"),
    ),
)


def sanitise(text: str) -> str:
    """Rewrite the absolute paths the engine records to relative ones.

    The same rewrite the committed fixtures had applied, so the two are
    comparable; nothing else is touched.
    """
    lines = []
    for line in text.splitlines():
        label = line[:35].strip()
        if label in {"File name:", "Input files:"}:
            line = line[:35] + re.sub(r"^.*/", "./", line[35:].strip())
        elif not label and re.match(r"^\s+/.*\.(xml|stn|msr)\s*$", line):
            line = " " * 35 + re.sub(r"^.*/", "./", line.strip())
        lines.append(line)
    return "\n".join(lines) + "\n"


#: How far two runs' numbers may differ and still count as the same output.
#:
#: Not zero, and the reason matters. This check asks whether the *layout*
#: changed, and it compares the output of two builds of a numerical program:
#: a different OpenBLAS, or the same one vectorising differently on another
#: CPU, moves the last digits of a matrix inverse. An ill-conditioned station
#: amplifies that -- in the ``angles`` fixture, whose ``HILL`` is barely
#: determined, the variances differ in the eleventh significant figure between
#: this machine and a CI runner.
#:
#: 1e-6 is far tighter than any error this check exists to catch. A column read
#: from the wrong place, a unit taken as degrees instead of HP, a correction
#: read as an angle rather than seconds of arc: all are wrong by a factor, not
#: by a part in a million.
RELATIVE_TOLERANCE = 1e-6


def comparable(text: str) -> list[str]:
    """Drop the lines that cannot help but differ between two runs."""
    return [
        line for line in text.splitlines() if not any(line.startswith(key) for key in VOLATILE)
    ]


def _tokens(line: str) -> list[tuple[int, str]]:
    """Each whitespace-separated token with the column it starts at."""
    return [(match.start(), match.group()) for match in re.finditer(r"\S+", line)]


def same_line(committed: str, produced: str) -> bool:
    """Is *produced* the same output as *committed*, allowing for arithmetic noise?

    Identical text passes at once. Otherwise both lines are tokenised **with
    their column positions**, and the line passes only if every token starts at
    the same column and either matches exactly or is a number within
    :data:`RELATIVE_TOLERANCE`.

    Keeping the column positions in the comparison is what makes this a layout
    check rather than a numbers check: a column that moved, widened or was
    renamed shifts a start position and fails here, even when every value it
    holds is unchanged.
    """
    if committed == produced:
        return True
    left, right = _tokens(committed), _tokens(produced)
    if len(left) != len(right):
        return False
    for (column, expected), (other_column, actual) in zip(left, right, strict=True):
        if column != other_column:
            return False
        if expected == actual:
            continue
        try:
            first, second = float(expected), float(actual)
        except ValueError:
            return False
        scale = max(abs(first), abs(second))
        if scale and abs(first - second) / scale > RELATIVE_TOLERANCE:
            return False
        if not scale and first != second:
            return False
    return True


def run_case(case: Case, work: Path) -> dict[str, str]:
    """Run one case in *work* and return its sanitised outputs by suffix."""
    for name in (case.station_file, case.measurement_file):
        shutil.copy(INPUTS / name, work / Path(name).name)

    network = "fixture"
    commands = [
        ["dnaimport", "-n", network, Path(case.station_file).name, Path(case.measurement_file).name],
        ["dnaadjust", "-n", network, *case.options],
    ]
    for command in commands:
        result = subprocess.run(command, cwd=work, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise SystemExit(
                f"{command[0]} failed for case {case.name} "
                f"({result.returncode}):\n{result.stdout[-2000:]}\n{result.stderr[-2000:]}"
            )

    produced: dict[str, str] = {}
    for suffix in case.outputs:
        path = work / f"{network}.simult.{suffix}"
        if not path.is_file():
            raise SystemExit(f"case {case.name}: dnaadjust wrote no .{suffix}")
        produced[suffix] = sanitise(path.read_text())
    return produced


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write",
        action="store_true",
        help="overwrite the committed fixtures with what this engine produced",
    )
    arguments = parser.parse_args()

    if shutil.which("dnaadjust") is None:
        print("dnaadjust is not on PATH; nothing to check.", file=sys.stderr)
        return 0

    version = subprocess.run(
        ["dnaadjust", "--version"], capture_output=True, text=True, check=False
    ).stdout
    print(next((line for line in version.splitlines() if "Version:" in line), version[:80]).strip())

    failures = 0
    for case in CASES:
        with tempfile.TemporaryDirectory() as directory:
            produced = run_case(case, Path(directory))
        for suffix, text in produced.items():
            fixture = FIXTURES / f"{case.name}.{suffix}"
            if arguments.write:
                fixture.write_text(text)
                print(f"  wrote {fixture.relative_to(ROOT)}")
                continue
            if not fixture.is_file():
                print(f"  MISSING {fixture.relative_to(ROOT)}")
                failures += 1
                continue
            expected, actual = comparable(fixture.read_text()), comparable(text)
            if len(expected) == len(actual) and all(
                same_line(one, other) for one, other in zip(expected, actual, strict=True)
            ):
                print(f"  ok      {fixture.relative_to(ROOT)}")
                continue
            failures += 1
            print(f"  DIFFERS {fixture.relative_to(ROOT)}")
            diff = difflib.unified_diff(
                expected, actual, fromfile="committed", tofile="produced", lineterm="", n=1
            )
            for line in list(diff)[:40]:
                print(f"    {line}")

    if failures:
        print(
            f"\n{failures} fixture(s) no longer match this DynAdjust. Either the engine's "
            "output layout changed -- in which case the parsers need looking at, not just "
            "the fixtures -- or the fixtures were made with a different build.",
            file=sys.stderr,
        )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
