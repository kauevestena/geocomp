#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Build the GNSS tutorial's files from RD-06's pinned NOAA sources (P13-17).

The tutorial ``geocomp/resources/datasets/ggao-triangle`` is two hours of one
day, 2025-001, at the three GGAO stations GODN, GODE and GODS: midnight, when
the triangle closes, and eleven o'clock, the hour ``specs/22`` section 5.1
found failing ambiguity resolution. Its observation files are derived from
NOAA's published daily files, which ``tests/data/rd06/source_manifest.json``
pins by hash, in exactly two ways and no other:

* **cut** to the hour: the epoch records inside it are copied unmodified, and
  the header's first and last observation times are set to the epochs kept;
* **reduced to GPS and the eight observables** a dual-frequency GPS solution
  reads (C1 P1 L1 S1 C2 P2 L2 S2): every kept value is its sixteen characters
  unchanged.

GeoComp's static profile processes GPS on L1 and L2, so neither changes a
solution: the six ``.pos`` files solved from the full hours and from these are
the same bytes below their headers (``specs/ROADMAP.md`` P13-17). The
navigation file is NOAA's, unchanged.

``tests/test_rd06.py`` rebuilds the files from the sources wherever engine CI
has fetched them and holds the shipped ones to the result, byte for byte.

Usage::

    python3 scripts/check_rd06.py --fetch-inputs --verify-inputs
    python3 scripts/make_ggao_triangle.py [--check]

Needs ``hatanaka`` (``tests/data/rd06/requirements.txt``), as RD-06 does.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SOURCES = REPO / "tests" / "data" / "rd06" / "sources"
DATASET = REPO / "geocomp" / "resources" / "datasets" / "ggao-triangle"

STATIONS = ("godn", "gode", "gods")
#: The hours shipped, GPS time: each folder holds one, from its start to the next.
HOURS = (0, 11)
NAVIGATION = "brdc0010.25n.gz"
KEEP = ("C1", "P1", "L1", "S1", "C2", "P2", "L2", "S2")

_EPOCH = re.compile(
    r"^ (\d\d) ([ \d]\d) ([ \d]\d) ([ \d]\d) ([ \d]\d) ([ \d]\d\.\d{7})  (\d)([ \d]{3})"
)


def folder(hour: int) -> str:
    """The tutorial's folder for *hour*: ``hour-00``, ``hour-11``."""
    return f"hour-{hour:02d}"


def _stamp(match: re.Match, label: str) -> str:
    year = 2000 + int(match[1])
    return (
        f"{year:6d}{int(match[2]):6d}{int(match[3]):6d}{int(match[4]):6d}{int(match[5]):6d}"
        f"{float(match[6]):13.7f}     GPS         {label}"
    )


def cut(text: str, start: float, end: float, source: str) -> str:
    """The epoch records of *text* from *start* to *end* hours, copied unmodified."""
    lines = text.splitlines()
    last_header = next(i for i, line in enumerate(lines) if line[60:73] == "END OF HEADER")
    header, body = lines[: last_header + 1], lines[last_header + 1 :]

    kept: list[str] = []
    inside, first, last = False, None, None
    for line in body:
        match = _EPOCH.match(line)
        if match:
            hours = int(match[4]) + int(match[5]) / 60 + float(match[6]) / 3600
            inside = start <= hours < end
            if inside:
                first = first or match
                last = match
        if inside:
            kept.append(line)
    if first is None or last is None:
        raise ValueError(f"{source} has no epoch from {start} to {end} h")

    out: list[str] = []
    for line in header:
        if line[60:77] == "TIME OF FIRST OBS":
            line = _stamp(first, "TIME OF FIRST OBS")
        elif line[60:76] == "TIME OF LAST OBS":
            line = _stamp(last, "TIME OF LAST OBS")
        elif line[60:73] == "END OF HEADER":
            for note in (
                f"Cut to {start:05.2f}-{end:05.2f} h GPST from {source}",
                "Epoch records copied unmodified; first and last",
                "observation times set to the epochs kept",
            ):
                out.append(f"{note:<60}COMMENT")
        out.append(line)
    return "\n".join(out + kept) + "\n"


def gps_only(text: str) -> str:
    """GPS and :data:`KEEP` from a RINEX 2.11 file, every kept value unchanged."""
    lines = text.splitlines()
    last_header = next(i for i, line in enumerate(lines) if line[60:73] == "END OF HEADER")
    header, body = lines[: last_header + 1], lines[last_header + 1 :]

    types: list[str] = []
    for line in header:
        if line[60:79] == "# / TYPES OF OBSERV":
            types += line[6:60].split()
    missing = [code for code in KEEP if code not in types]
    if missing:
        raise ValueError(f"the file has no {', '.join(missing)}")
    columns = [types.index(code) for code in KEEP]
    per_satellite = (len(types) + 4) // 5

    out: list[str] = []
    written = False
    for line in header:
        if line[60:79] == "# / TYPES OF OBSERV":
            if not written:
                fields = "".join(f"{code:>6}" for code in KEEP)
                out.append(f"{len(KEEP):6d}{fields:<54}# / TYPES OF OBSERV")
                written = True
            continue
        if line[60:73] == "END OF HEADER":
            for note in (
                f"GPS only, observables {' '.join(KEEP)} kept",
                "from the published file; values copied unchanged",
            ):
                out.append(f"{note:<60}COMMENT")
        out.append(line)

    index = 0
    while index < len(body):
        line = body[index]
        match = _EPOCH.match(line)
        if not match or int(match[7]) not in (0, 1):
            raise ValueError(f"not an observation epoch: {line!r}")
        count = int(match[8])
        listed = line[32:68]
        index += 1
        while len(listed) < 3 * count:
            listed += body[index][32:68]
            index += 1
        kept: list[tuple[str, list[str]]] = []
        for number in range(count):
            name = listed[3 * number : 3 * number + 3]
            record = "".join(body[index + k].ljust(80)[:80] for k in range(per_satellite))
            index += per_satellite
            if name.startswith("G"):
                kept.append((name, [record[16 * c : 16 * c + 16] for c in columns]))
        names = "".join(name for name, _values in kept)
        chunks = [names[k : k + 36] for k in range(0, len(names), 36)] or [""]
        out.append((line[:28] + f"{match[7]}{len(kept):3d}" + chunks[0].ljust(36) + line[68:80]).rstrip())
        out.extend((" " * 32 + chunk).rstrip() for chunk in chunks[1:])
        for _name, values in kept:
            for k in range(0, len(values), 5):
                out.append("".join(values[k : k + 5]).rstrip())
    return "\n".join(out) + "\n"


def build(sources: Path = SOURCES) -> dict[str, bytes]:
    """Every file the tutorial's two folders hold, by path inside the dataset."""
    import hatanaka

    files: dict[str, bytes] = {}
    navigation = (sources / NAVIGATION).read_bytes()
    for station in STATIONS:
        name = f"{station}0010.25"
        daily = hatanaka.decompress((sources / f"{name}d.gz").read_bytes()).decode("ascii")
        for hour in HOURS:
            text = gps_only(cut(daily, hour, hour + 1, f"{name}o"))
            files[f"{folder(hour)}/{name}o"] = text.encode("ascii")
    for hour in HOURS:
        files[f"{folder(hour)}/{NAVIGATION}"] = navigation
    return files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--sources", type=Path, default=SOURCES)
    parser.add_argument("--output", type=Path, default=DATASET)
    parser.add_argument("--check", action="store_true", help="compare with --output; write nothing")
    arguments = parser.parse_args(argv)

    files = build(arguments.sources)
    differing = []
    for relative, data in sorted(files.items()):
        target = arguments.output / relative
        if arguments.check:
            if not target.is_file() or target.read_bytes() != data:
                differing.append(relative)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        print(f"{relative}: {len(data)} bytes")
    if differing:
        print("Differ from the sources: " + ", ".join(differing), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
