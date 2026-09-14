#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Regenerate the ``.pos`` fixtures and check the committed ones match.

``tests/data/rtklib/pos/`` holds real ``rnx2rtkp`` output, and every test of the
solution parser reads it rather than the engine. That is what keeps those tests
tier 1 -- they run wherever Python does. It is also how they go stale: an
RTKLIB that changed a column, or renamed one, would keep passing against a
fixture written by the old one.

This is the guard, and it matters more here than for DynAdjust. The `.pos`
column layout is not documented anywhere GeoComp can cite: it was established by
reading ``src/solution.c`` and running the engine four ways, and one of the
headers is **wrong upstream** (``specs/08`` section 4.1). A parser built on that
reading has to be told the day the reading stops being true.

Usage::

    python3 scripts/check_rtklib_fixtures.py            # check
    python3 scripts/check_rtklib_fixtures.py --write    # accept the new output
"""

from __future__ import annotations

import argparse
import difflib
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "tests" / "data" / "rtklib"
FIXTURES = DATA / "pos"

#: ``rnx2rtkp`` takes the **rover first and the base second**; that order is the
#: interface, not a convention, and reversing it computes a different solution
#: while reporting success. The committed fixtures were produced this way round.
ROVER = "07590920.05o"
BASE = "30400920.05o"
NAVIGATION = "brdc_0759.05n.gz"

#: Lines whose content depends on when and where the run happened rather than
#: on the engine's output format.
VOLATILE = ("% inp file",)


@dataclass(frozen=True)
class Case:
    """One run and the fixture it produces."""

    name: str
    flags: tuple[str, ...]
    note: str


CASES = (
    Case("llh", (), "the default: latitude, longitude, height"),
    Case("llh-dms", ("-g",), "lat/lon as degrees, minutes and seconds -- seven position columns"),
    Case("xyz", ("-e",), "ECEF, whose cross columns pair differently again"),
    Case("enu", ("-a",), "the ENU baseline, a third pairing order"),
    Case("llh-calendar", ("-t",), "a calendar date and time instead of a GPS week"),
)

#: How far two runs' numbers may differ and still count as the same output.
#: Not zero: this compares the output of two builds of a numerical program, and
#: a different libm or a different vectorisation moves the last digits. Far
#: tighter than any error this exists to catch -- a column read from the wrong
#: place is wrong by a factor, not by a part in a million.
RELATIVE_TOLERANCE = 1e-6


def comparable(text: str) -> list[str]:
    return [
        line for line in text.splitlines() if not any(line.startswith(key) for key in VOLATILE)
    ]


def _tokens(line: str) -> list[tuple[int, str]]:
    return [(match.start(), match.group()) for match in re.finditer(r"\S+", line)]


def same_line(committed: str, produced: str) -> bool:
    """Is *produced* the same output as *committed*, allowing arithmetic noise?

    Tokens are compared **with their column positions**, which is what makes
    this a layout check rather than a numbers check: a column that moved,
    widened or was renamed shifts a start position and fails here even when
    every value it holds is unchanged.
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


def run_case(case: Case, work: Path) -> str:
    """Run one case and return its output with the input paths made relative."""
    navigation = work / "nav.05n"
    with subprocess.Popen(
        ["gunzip", "-c", str(DATA / NAVIGATION)], stdout=subprocess.PIPE
    ) as unzip:
        navigation.write_bytes(unzip.stdout.read())

    output = work / f"{case.name}.pos"
    command = [
        "rnx2rtkp", "-p", "3", "-m", "15", *case.flags, "-o", str(output),
        str(DATA / ROVER), str(DATA / BASE), str(navigation),
    ]
    result = subprocess.run(command, cwd=work, capture_output=True, text=True, check=False)
    if result.returncode != 0 or not output.is_file():
        raise SystemExit(
            f"rnx2rtkp failed for case {case.name} ({result.returncode}):\n"
            f"{result.stdout[-2000:]}\n{result.stderr[-2000:]}"
        )
    # The `% inp file` lines name absolute paths on the machine that ran; the
    # committed fixtures carry relative ones, as the DynAdjust fixtures do.
    return re.sub(r"^(% inp file  :) +.*/([^/\n]+)$", r"\1 ./\2", output.read_text(), flags=re.M)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write",
        action="store_true",
        help="overwrite the committed fixtures with what this engine produced",
    )
    arguments = parser.parse_args()

    if shutil.which("rnx2rtkp") is None:
        print("rnx2rtkp is not on PATH; nothing to check.", file=sys.stderr)
        return 0

    version = subprocess.run(
        ["rnx2rtkp", "--version"], capture_output=True, text=True, check=False
    )
    print(f"{version.stdout.strip()}{version.stderr.strip()}")

    failures = 0
    for case in CASES:
        with tempfile.TemporaryDirectory() as directory:
            produced = run_case(case, Path(directory))
        fixture = FIXTURES / f"{case.name}.pos"

        if arguments.write:
            fixture.write_text(produced)
            print(f"  wrote   {fixture.relative_to(ROOT)}")
            continue
        if not fixture.is_file():
            print(f"  MISSING {fixture.relative_to(ROOT)}")
            failures += 1
            continue

        expected, actual = comparable(fixture.read_text()), comparable(produced)
        if len(expected) == len(actual) and all(
            same_line(one, other) for one, other in zip(expected, actual, strict=True)
        ):
            print(f"  ok      {fixture.relative_to(ROOT)}  ({case.note})")
            continue
        failures += 1
        print(f"  DIFFERS {fixture.relative_to(ROOT)}")
        for line in list(
            difflib.unified_diff(
                expected, actual, fromfile="committed", tofile="produced", lineterm="", n=1
            )
        )[:40]:
            print(f"    {line}")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
