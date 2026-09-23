#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Find CORS station pairs a published-coordinate comparison could be judged on.

RD-06 needs a short baseline whose two stations each carried **one** antenna
from the epoch of their published coordinate through to the day observed. The
first screen behind ``specs/22`` section 5.2 fixed the observation day at 2025
day 001 and concluded that GGAO's 65 m baseline was the shortest clean one in
the network. That conclusion was a property of the day, not of the network: the
observation day is a free parameter, and moving it next to the coordinate epoch
changes the answer. This script makes that claim reproducible instead of
remembered, and it is why section 5.2 now states the screen's day.

It needs no engine and no network. Feed it a directory of CORS site logs, the
list of stations with observations on the day of interest, and optionally an
ANTEX file to test whether each antenna's *radome* is calibrated too -- the
defect that made GODE unjudgeable. The station list comes from the mirror's own
directory listing; ``--fetch-available`` will retrieve it, and is the only part
that touches the network.

Positions come from each log's approximate ITRF coordinates, which are good to
the millimetre and far beyond what choosing a pair needs. A shortlist is not a
decision: the chosen pair's ARP still comes from its published coordinate sheet.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.check_rd06 import antennas_spanning  # noqa: E402

MIRROR = "https://noaa-cors-pds.s3.amazonaws.com"
_XYZ = re.compile(r"([XYZ]) coordinate \(m\)\s*:\s*(-?[\d.]+)")


def approximate_position(text: str) -> tuple[float, float, float] | None:
    """The log's section 2 ITRF position, or None when it does not carry one.

    Section 3 onwards repeats coordinate-looking fields, so only the text before
    the receiver section is searched.
    """
    found = dict(_XYZ.findall(text.split("3.   GNSS Receiver")[0]))
    if set(found) != {"X", "Y", "Z"}:
        return None
    return tuple(float(found[axis]) for axis in "XYZ")


def antex_entries(path: Path) -> set[str]:
    """Every antenna+radome key an ANTEX file calibrates.

    The key is the first 20 columns -- antenna code *and* radome code -- because
    that is what ``searchpcv`` matches on and what NGS keys its calibrations by.
    Matching on the antenna alone is the substitution that made RD-06's judged
    case unjudgeable; see ``specs/08`` section 7.5.
    """
    return {
        line[:20].rstrip()
        for line in path.read_text(errors="replace").splitlines()
        if line[60:].startswith("TYPE / SERIAL NO")
    }


def fetch_available(year: int, day: int) -> list[str]:
    """Station IDs with RINEX on the mirror for *year* and day-of-year *day*."""
    prefix = f"rinex/{year}/{day:03d}/"
    pattern = re.compile(rf"<Prefix>{re.escape(prefix)}([a-z0-9]+)/</Prefix>")
    stations: list[str] = []
    token = ""
    while True:
        url = f"{MIRROR}/?list-type=2&delimiter=/&prefix={prefix}&max-keys=1000"
        if token:
            url += f"&continuation-token={urllib.parse.quote(token, safe='')}"
        with urllib.request.urlopen(url, timeout=120) as response:
            body = response.read().decode("utf-8", "replace")
        stations += pattern.findall(body)
        following = re.search(r"<NextContinuationToken>([^<]+)</", body)
        if following is None:
            return sorted(set(stations))
        token = following.group(1)


def eligible_stations(
    logs: Path, available: set[str], epoch: str, observed: str, atx: set[str] | None
) -> dict[str, dict]:
    """Stations carrying exactly one antenna across ``epoch`` to ``observed``."""
    stations: dict[str, dict] = {}
    for path in sorted(logs.glob("*.log.txt")):
        name = path.name.split(".")[0].upper()
        if available and name not in available:
            continue
        text = path.read_text(errors="replace")
        position = approximate_position(text)
        if position is None:
            continue
        spanning = antennas_spanning(text, epoch, observed)
        if len(spanning) != 1:
            continue
        antenna = spanning.pop()
        stations[name] = {
            "xyz": position,
            "antenna": antenna,
            "calibrated": None if atx is None else antenna in atx,
        }
    return stations


def pairs_within(stations: dict[str, dict], shortest: float, longest: float) -> list[tuple]:
    """Every station pair whose separation falls in the requested range."""
    names = sorted(stations)
    found = []
    for index, first in enumerate(names):
        for second in names[index + 1 :]:
            span = math.dist(stations[first]["xyz"], stations[second]["xyz"])
            if shortest <= span <= longest:
                found.append((span, first, second))
    return sorted(found)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--logs", type=Path, required=True, help="directory of CORS site logs")
    parser.add_argument("--available", type=Path, help="file of station IDs with data that day")
    parser.add_argument("--fetch-available", metavar="YEAR/DAY", help="list them from the mirror")
    parser.add_argument("--epoch", default="2020-01-01", help="epoch of the published coordinates")
    parser.add_argument("--observed", required=True, help="the day to be processed, YYYY-MM-DD")
    parser.add_argument("--shortest", type=float, default=10.0, help="metres")
    parser.add_argument("--longest", type=float, default=5000.0, help="metres")
    parser.add_argument("--antex", type=Path, help="require antenna *and* radome to be in this file")
    parser.add_argument("--same-type", action="store_true", help="only pairs sharing an antenna")
    parser.add_argument("--json", type=Path, help="write the full result here")
    args = parser.parse_args()

    available: set[str] = set()
    if args.fetch_available:
        year, day = args.fetch_available.split("/")
        available = {name.upper() for name in fetch_available(int(year), int(day))}
    elif args.available:
        available = {line.strip().upper() for line in args.available.read_text().split()}

    atx = antex_entries(args.antex) if args.antex else None
    stations = eligible_stations(args.logs, available, args.epoch, args.observed, atx)
    if atx is not None:
        stations = {k: v for k, v in stations.items() if v["calibrated"]}
    found = pairs_within(stations, args.shortest, args.longest)
    if args.same_type:
        found = [p for p in found if stations[p[1]]["antenna"] == stations[p[2]]["antenna"]]

    print(f"site logs read from {args.logs}")
    if available:
        print(f"stations with observations on {args.observed}: {len(available)}")
    print(f"one antenna spanning {args.epoch} to {args.observed}: {len(stations)}")
    if atx is not None:
        print(f"  ... restricted to antenna+radome in {args.antex.name} ({len(atx)} entries)")
    print(f"pairs between {args.shortest:g} m and {args.longest:g} m: {len(found)}\n")
    for span, first, second in found:
        mark = "same" if stations[first]["antenna"] == stations[second]["antenna"] else "MIXED"
        print(
            f"  {span:9.1f} m  {first}/{second}  {mark:5}  "
            f"{stations[first]['antenna']} | {stations[second]['antenna']}"
        )
    if args.json:
        args.json.write_text(json.dumps({"stations": stations, "pairs": found}, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
