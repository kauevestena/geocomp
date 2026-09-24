#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Measure how well NGS's published CORS coordinates can be reproduced at all.

RD-06 asks a static relative session to reproduce a published coordinate to
1 mm per component, and has never met it. Until now the reason could not be
separated from the reference case's own defects: GODS's antenna changed after
its coordinate epoch, and GODE's radome has no published calibration, so the
one pair available was never clean.

This answers the question the other way round -- not "is this pair clean?" but
"what does a clean pair do?". It takes **every** short same-antenna CORS pair
that `screen_cors_pairs.py` finds for an observation day beside the 2020.0
coordinate epoch, checks that both antennas *and radomes* are in the ANTEX,
and solves each one on three consecutive days under RD-06's own configuration.

Nothing is selected after solving: every eligible pair is processed and every
result is reported. A pair drops out only for a missing input -- KEN5/KEN6
because KEN6 publishes no ITRF2020 coordinate sheet, so there is no truth to
compare against.

The recorded answer is in ``tests/data/published_coordinates/observed.json``
and `specs/22` section 5.4 reads it. ``--run`` needs an ANTEX, rnx2rtkp, NumPy
and hatanaka; ``--verify-inputs`` needs only the standard library.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

DATA = ROOT / "tests/data/published_coordinates"
DAYS = ("015", "016", "017")
YEAR = 2020
#: Both ends carry this, which is why the pairs are comparable at all: a
#: mixed-antenna baseline is the configuration NGS itself warns about.
ANTENNA = "TRM41249USCG    SCIT"
#: From ``screen_cors_pairs.py`` over all 2886 site logs for 2020 day 015.
#: Base is the lower-numbered station and rover the higher, with no exceptions,
#: so no pair's orientation was chosen after seeing its answer.
PAIRS = (
    ("SHK5", "SHK6"),
    ("DET5", "DET6"),
    ("LEV5", "LEV6"),
    ("BIS5", "BIS6"),
    ("HDF5", "HDF6"),
    ("CHB5", "CHB6"),
    ("AIS5", "AIS6"),
    ("YOU5", "YOU6"),
    ("KEW5", "KEW6"),
    ("MOR5", "MOR6"),
    ("PNB5", "PNB6"),
    ("GUS5", "GUS6"),
    ("ENG5", "ENG6"),
    ("ACU5", "ACU6"),
)
TOLERANCE_MM = 1.0


def manifest() -> list[dict]:
    return json.loads((DATA / "source_manifest.json").read_text())


def observed() -> dict:
    return json.loads((DATA / "observed.json").read_text())


def fetch_inputs(into: Path) -> None:
    """Retrieve each pinned source, refusing any whose bytes moved."""
    into.mkdir(parents=True, exist_ok=True)
    for entry in manifest():
        target = into / entry["file"]
        if not target.is_file():
            print(f"Fetching {entry['file']}")
            with urllib.request.urlopen(entry["url"], timeout=300) as response:
                target.write_bytes(response.read())
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        if digest != entry["sha256"]:
            raise ValueError(f"{entry['file']}: upstream changed; {digest} != {entry['sha256']}")


def published_arp(text: str) -> list[float] | None:
    """The sheet's ITRF2020 epoch-2020.0 ARP, read before the L1 block.

    The sheet prints ARP *and* L1 phase centre; taking the text after the L1
    heading would silently compare against a point 85 mm higher.
    """
    if text.count("L1 Phase Center") != 1:
        return None
    block = text.split("L1 Phase Center", 1)[0].split("NAD_83", 1)[0]
    if "ITRF2020 POSITION (EPOCH 2020.0)" not in block:
        return None
    return [float(re.search(rf"\|\s+{axis} =\s*([-\d.]+)", block)[1]) for axis in "XYZ"]


def run(into: Path, executable: Path, antex: Path) -> dict:
    import hatanaka
    import numpy as np

    from geocomp.core.geodesy.cartesian import cartesian_to_geodetic, ecef_to_enu
    from geocomp.core.geodesy.ellipsoid import ELLIPSOIDS
    from geocomp.engines.rtklib import RtklibConfig, RtklibEngine, RtklibJob
    from geocomp.io.gnss_discovery import scan_folder

    if ANTENNA not in {
        line[:20].rstrip()
        for line in antex.read_text(errors="replace").splitlines()
        if line[60:].startswith("TYPE / SERIAL NO")
    }:
        raise ValueError(f"{antex.name} has no entry for {ANTENNA!r}; the comparison would be unjudgeable")

    truth = {}
    for station in {s for pair in PAIRS for s in pair}:
        position = published_arp((into / f"{station.lower()}_20.coord.txt").read_text(errors="replace"))
        if position is None:
            raise ValueError(f"{station}: no ITRF2020 ARP in the coordinate sheet")
        truth[station] = np.array(position)

    engine = RtklibEngine(configured=executable)
    by_day: dict[str, dict] = {}
    for day in DAYS:
        inputs = into / f"inputs{day}"
        inputs.mkdir(exist_ok=True)
        for source in sorted(into.glob(f"*{day}0.20d.gz")):
            target = inputs / (source.name[:-4] + "o")
            if not target.is_file():
                target.write_bytes(hatanaka.decompress(source.read_bytes()))
        nav = inputs / f"brdc{day}0.20n"
        if not nav.is_file():
            nav.write_bytes(gzip.decompress((into / f"brdc{day}0.20n.gz").read_bytes()))
        sessions = {s.station_id: s for s in scan_folder(inputs).sessions}
        for base, rover in PAIRS:
            if base not in sessions or rover not in sessions:
                raise ValueError(f"{base}/{rover}: missing observations on day {day}")
            for station in (base, rover):
                if sessions[station].antenna != ANTENNA:
                    raise ValueError(f"{station}: carries {sessions[station].antenna!r}")
            config = RtklibConfig(
                name=f"{base}_{rover}",
                output_format="xyz",
                base_position_type="xyz",
                base_position=tuple(truth[base]),
                # RD-06's calibrated case, unchanged. The ARP deltas are zeroed
                # because the published coordinates are ARP values and the
                # reduction is already in the truth.
                extra={
                    "ant1-antdele": "0",
                    "ant1-antdeln": "0",
                    "ant1-antdelu": "0",
                    "ant2-antdele": "0",
                    "ant2-antdeln": "0",
                    "ant2-antdelu": "0",
                    "pos1-tidecorr": "1",
                    "pos1-dynamics": "off",
                    "ant1-anttype": ANTENNA,
                    "ant2-anttype": ANTENNA,
                    "file-rcvantfile": str(antex),
                    "file-satantfile": str(antex),
                    "pos1-posopt2": "on",
                },
                ephemeris="brdc",
            )
            job = RtklibJob(rover=sessions[rover], base=sessions[base], config=config, timeout=300)
            solution = engine.run(job, work_dir=into / f"runs{day}" / f"{base}_{rover}").solution
            resolved = solution.antennas
            if sorted(resolved.values()) != [ANTENNA, ANTENNA]:
                raise ValueError(f"{base}/{rover} day {day}: engine resolved {resolved}")
            delta = np.array(solution.last().position) - truth[rover]
            lat, lon, _ = cartesian_to_geodetic(*truth[base], ELLIPSOIDS["GRS80"])
            by_day.setdefault(f"{base}-{rover}", {})[day] = {
                "xyz_mm": (delta * 1000).tolist(),
                "enu_mm": (np.array(ecef_to_enu(tuple(delta), lat, lon)) * 1000).tolist(),
            }
    return by_day


def compare(measured: dict, limit: float) -> int:
    """Check a fresh run against the recorded one, component by component.

    The default limit is tight enough that only an identical calibration
    passes. Running against a *different* ANTEX -- NGS's `ngs20.atx` rather
    than the IGS type means this was recorded with -- is a legitimate reason
    for a sub-millimetre departure, so that comparison should raise the limit
    deliberately and say why, rather than leaving the tolerance loose here.
    """
    recorded = {row["pair"]: row for row in observed()["results"]}
    worst, culprit = 0.0, ""
    for pair, days in sorted(measured.items()):
        for day, values in sorted(days.items()):
            was = recorded[pair]["enu_mm_by_day"][day]
            for axis, (got, before) in enumerate(zip(values["enu_mm"], was, strict=True)):
                if abs(got - before) > worst:
                    worst, culprit = abs(got - before), f"{pair} day {day} {'ENU'[axis]}"
    print(f"largest departure from the recorded result: {worst:.4f} mm ({culprit})")
    if worst > limit:
        print(f"that exceeds the {limit:g} mm limit", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, default=ROOT / "build/published-coordinates")
    parser.add_argument("--fetch-inputs", action="store_true")
    parser.add_argument("--verify-inputs", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--engine", type=Path, help="rnx2rtkp; otherwise taken from PATH")
    parser.add_argument("--antex", type=Path, help="igs20.atx or an ANTEX carrying this antenna")
    parser.add_argument(
        "--max-departure-mm",
        type=float,
        default=0.05,
        help="how far a fresh run may sit from the recorded one; raise it only for a "
        "deliberately different ANTEX, and say so",
    )
    args = parser.parse_args()

    if args.fetch_inputs or args.verify_inputs:
        fetch_inputs(args.work)
        print(f"{len(manifest())} sources verified against their pinned digests")
    if not args.run:
        summary = observed()
        print(
            f"recorded: {summary['pairs']} pairs, "
            f"{summary['pairs_passing_1mm_per_component']} within {TOLERANCE_MM:g} mm per component; "
            f"median worst component {summary['median_max_abs_xyz_mm']} mm"
        )
        return 0
    if args.antex is None:
        parser.error("--run needs --antex")
    measured = run(args.work, args.engine or Path("rnx2rtkp"), args.antex)
    return compare(measured, args.max_departure_mm)


if __name__ == "__main__":
    raise SystemExit(main())
