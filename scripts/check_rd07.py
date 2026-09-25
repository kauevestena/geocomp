#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""RD-07: GeoComp's gravimetry against a real survey and a published solution.

``specs/22-reference-data-sources.md`` section 5.6 and ``specs/12`` section 8.

Two references, and neither can be committed here:

* **A Scintrex CG-5 survey** (Djougou, Benin, September 2013; Hector and
  Hinderer, *Computers & Geosciences* 2016) whose file records, beside every
  reading, the tide correction the instrument's own firmware applied. GeoComp's
  Longman implementation is compared with all of them.
* **pyGrav's published least-squares solution** for four days of that survey
  -- station values, drifts, a posteriori SD -- from the paper's own test case.
  GeoComp's joint drift adjustment is required to reproduce it.

pyGrav states no licence, and the CG-5 file GSadjust re-hosts under CC0 came
from pyGrav, so GSadjust cannot have waived rights in it. Both are therefore
*fetched*, at pinned commits, and checked against pinned digests -- the way
engine CI treats the ANTEX file -- and never committed. What *is* committed
under ``tests/data/rd07/gsadjust/`` is USGS's own synthetic test data, which is
public domain; this script also proves it is still byte-for-byte USGS's.

**What reproducing pyGrav means, precisely.** pyGrav solves
``(N + S S^T)^-1 A^T P l`` with ``S`` one on every station -- Hwang's datum-free
term, added on top of an absolute observation that already fixes the datum. It
is a pseudo-observation ``sum(g) = 0`` of unit weight in mGal, and it biases
every value slightly (station 1, held at 0 +- 0.001 mGal, comes out at -0.0003).
GeoComp does not add it. So the check is two steps:

1. An independent transcription of pyGrav's model *with* the term reproduces
   the published values within what the rounding of the published inputs
   allows -- times printed to 0.01 day, values and SDs to 0.1 microgal --
   computed by perturbing those inputs within their rounding, not chosen.
2. GeoComp reproduces the same model *without* the term to machine precision.

Usage::

    python3 scripts/check_rd07.py --fetch DIR   # clone, verify, compare
    python3 scripts/check_rd07.py --data DIR    # compare a directory fetched earlier
"""

from __future__ import annotations

import argparse
import hashlib
import math
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from itertools import pairwise
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

VENDORED = REPO_ROOT / "tests" / "data" / "rd07" / "gsadjust"

#: GSadjust's 2.0.0 branch: its master now holds only a pointer to
#: code.usgs.gov, which is not reachable from every environment GeoComp is
#: tested in. Pinned in .github/workflows/reference.yml too.
GSADJUST_URL = "https://github.com/jkennedy-usgs/sgp-gsadjust.git"
GSADJUST_COMMIT = "17bb3ca09f0ea23b6a74c1c44ae0a2c77c64b440"
PYGRAV_URL = "https://github.com/basileh/pyGrav.git"
PYGRAV_COMMIT = "fc39609b6393dd935a8a0417698217bec1879e78"

CG5 = "test_data/field/CG-5/CG-5_TestData.txt"
CG5_SHA256 = "242c109b0011dfd3d3b3252af423a7268b1a0054b18cfaaecc59d09a9ddf3c3d"
PYGRAV_DAYS = {
    "2013-09-15": "05b13f69e311263d474f92ba07618c14bb5f71845858852f7d9579e29364ae5d",
    "2013-09-19": "20186bde486e6724e918b6cac389e0315ab029deb680e414c64e253d5833ccb7",
    "2013-09-21": "adc313bade476391ac234acdb797c1e10c1df6ae29d785f404888e476d267bb7",
    "2013-09-23": "410b2bf5aeee1c959bb29637706cb68c76181c755f177684ee64c252c6d51ba4",
}
PYGRAV_FILE = "test_case/input_data/preprocessed/{day}/LSresults_tot_20150812_1637.dat"
GSADJUST_SYNTHETIC = "test_data/synthetic"

MGAL = 1e-5
UGAL = 1e-8

#: The CG-5 comparison. The firmware prints to 1 microgal; this implementation
#: reproduces it to 0.60 microgal rms and 1.51 at worst, and these bounds are
#: that measurement rounded up to the next half microgal -- a regression guard,
#: not a claim the comparison was made against.
CG5_MAX_UGAL = 2.0
CG5_RMS_UGAL = 0.7
#: GeoComp against the same model computed independently: the arithmetic may
#: differ in order, so a few ulps are allowed and nothing more.
MACHINE_UGAL = 1e-6
#: Perturbations of the printed inputs for the rounding envelope, and its level.
ENVELOPE_SAMPLES = 400
ENVELOPE_PERCENTILE = 95.0


# -- fetching ------------------------------------------------------------


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _clone(url: str, commit: str, paths: list[str], destination: Path) -> None:
    run = lambda *args: subprocess.run(args, check=True, capture_output=True)  # noqa: E731
    run("git", "clone", "--filter=blob:none", "--no-checkout", url, str(destination))
    run("git", "-C", str(destination), "checkout", commit, "--", *paths)


def fetch(into: Path) -> Path:
    """Clone both references at their pinned commits and lay the files out under *into*."""
    into.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as scratch:
        gsadjust = Path(scratch) / "gsadjust"
        pygrav = Path(scratch) / "pygrav"
        _clone(GSADJUST_URL, GSADJUST_COMMIT, [CG5, GSADJUST_SYNTHETIC], gsadjust)
        _clone(PYGRAV_URL, PYGRAV_COMMIT, [PYGRAV_FILE.format(day=d) for d in PYGRAV_DAYS], pygrav)
        (into / "cg5").mkdir(exist_ok=True)
        shutil.copy2(gsadjust / CG5, into / "cg5" / "CG-5_TestData.txt")
        shutil.copytree(gsadjust / GSADJUST_SYNTHETIC, into / "gsadjust", dirs_exist_ok=True)
        for day in PYGRAV_DAYS:
            (into / "pygrav" / day).mkdir(parents=True, exist_ok=True)
            shutil.copy2(pygrav / PYGRAV_FILE.format(day=day), into / "pygrav" / day / "LSresults_tot.dat")
    return into


def verify(data: Path) -> list[str]:
    """Every fetched file is the one pinned, and the vendored ones are still USGS's."""
    problems: list[str] = []
    if _sha256(data / "cg5" / "CG-5_TestData.txt") != CG5_SHA256:
        problems.append("the CG-5 file is not the pinned one")
    for day, digest in PYGRAV_DAYS.items():
        if _sha256(data / "pygrav" / day / "LSresults_tot.dat") != digest:
            problems.append(f"pyGrav's {day} results are not the pinned ones")
    upstream = {p.name: _sha256(p) for p in (data / "gsadjust").iterdir() if p.is_file()}
    vendored = {p.name: _sha256(p) for p in VENDORED.iterdir() if p.is_file()}
    for name, digest in vendored.items():
        if upstream.get(name) != digest:
            problems.append(f"tests/data/rd07/gsadjust/{name} differs from GSadjust's")
    return problems


# -- the CG-5 tide -------------------------------------------------------


@dataclass(frozen=True)
class Cg5Reading:
    station: str
    instant: datetime
    gravity_mgal: float
    sd_mgal: float
    duration_s: int
    tide_mgal: float


@dataclass(frozen=True)
class Cg5Survey:
    latitude_deg: float
    longitude_deg: float
    tide_applied: bool
    readings: tuple[Cg5Reading, ...]


def read_cg5(path: Path) -> Cg5Survey:
    """The header's location, GMT offset and tide flag, and every reading."""
    text = path.read_text(encoding="latin-1")

    def header(label: str) -> str:
        found = re.search(rf"^/\s*{re.escape(label)}\s*(.+)$", text, re.M)
        if found is None:
            raise ValueError(f"CG-5 header has no {label!r}")
        return found.group(1).strip()

    def angle(value: str) -> float:
        number, hemisphere = value.split()
        return float(number) * (-1.0 if hemisphere in ("S", "W") else 1.0)

    latitude = angle(header("LAT:"))
    longitude = angle(header("LONG:"))
    offset = timedelta(hours=float(header("GMT DIFF.:")))
    tide_applied = header("Tide Correction:").upper().startswith("Y")
    readings = []
    for line in text.splitlines():
        fields = line.split()
        if len(fields) != 15 or not fields[0][0].isdigit():
            continue
        local = datetime.strptime(f"{fields[14]} {fields[11]}", "%Y/%m/%d %H:%M:%S")
        readings.append(
            Cg5Reading(
                station=str(int(float(fields[1]))),
                instant=(local - offset).replace(tzinfo=UTC),
                gravity_mgal=float(fields[3]),
                sd_mgal=float(fields[4]),
                duration_s=int(fields[9]),
                tide_mgal=float(fields[8]),
            )
        )
    return Cg5Survey(latitude, longitude, tide_applied, tuple(readings))


@dataclass(frozen=True)
class TideComparison:
    readings: int
    mean_ugal: float
    rms_ugal: float
    max_ugal: float

    @property
    def passed(self) -> bool:
        return self.max_ugal <= CG5_MAX_UGAL and self.rms_ugal <= CG5_RMS_UGAL


def compare_cg5_tide(survey: Cg5Survey) -> TideComparison:
    """GeoComp's Longman correction against the one the firmware recorded."""
    from geocomp.core.techniques.gravimetry.tides import tidal_correction

    latitude = math.radians(survey.latitude_deg)
    longitude = math.radians(survey.longitude_deg)
    misfit = [
        reading.tide_mgal * MGAL - tidal_correction(reading.instant, latitude, longitude, 0.0).value
        for reading in survey.readings
    ]
    return TideComparison(
        readings=len(misfit),
        mean_ugal=sum(misfit) / len(misfit) / UGAL,
        rms_ugal=math.sqrt(sum(m * m for m in misfit) / len(misfit)) / UGAL,
        max_ugal=max(abs(m) for m in misfit) / UGAL,
    )


# -- pyGrav's published solution ------------------------------------------


@dataclass(frozen=True)
class PublishedDay:
    """One day of pyGrav's test case: its inputs as printed, and its results."""

    day: str
    loops: tuple[tuple[tuple[str, float, float, float], ...], ...]
    stations: dict[str, float]
    drifts: tuple[float, ...]
    sd_aposteriori: float


def read_pygrav(day: str, path: Path) -> PublishedDay:
    """``Observations (weighted means)`` per loop, and ``Final results``."""
    text = path.read_text(encoding="latin-1")
    inputs = text.split("Relative observations:")[0]
    results = text.split("Final results")[1]
    loops = []
    for block in re.split(r"Loop: \d+", inputs)[1:]:
        rows = [line.split() for line in block.strip().splitlines() if re.match(r"^\d{4}\s", line)]
        loops.append(tuple((str(int(r[0])), float(r[1]), float(r[2]), float(r[4])) for r in rows))
    stations = {
        m.group(1): float(m.group(2))
        for m in re.finditer(r"^(\d+)\s+(-?\d+\.\d+)\s+(\d+\.\d+)$", results.split("Drift values")[0], re.M)
    }
    drifts = tuple(float(x) for x in re.findall(r"Degree 1:\s+(-?\d+\.\d+)", results))
    sd = float(re.search(r"SD a posteriori:\s+([\d.]+)", text).group(1))  # type: ignore[union-attr]
    return PublishedDay(day, tuple(loops), stations, drifts, sd)


def pygrav_model(loops, *, sst: bool) -> tuple[dict[str, float], tuple[float, ...], float]:
    """pyGrav's ``calculateSimpleDiff`` and ``lsInversion``, transcribed.

    Successive differences within each loop, weighted ``1 / (sd_i^2 + sd_j^2)``
    as independent; one degree-1 drift per loop, in mGal per day; station 1
    observed as ``0 +- 0.001`` mGal; and, when *sst*, ``S S^T`` added to the
    normal matrix. Returns station values, drifts and the a posteriori SD.
    """
    stations = sorted({row[0] for loop in loops for row in loop}, key=int)
    column = {s: i for i, s in enumerate(stations)}
    ns, nl = len(stations), len(loops)
    rows, observed, weights = [], [], []
    for k, loop in enumerate(loops):
        for (a, ga, sa, ta), (b, gb, sb, tb) in pairwise(loop):
            row = np.zeros(ns + nl)
            row[column[a]] -= 1.0
            row[column[b]] += 1.0
            row[ns + k] = tb - ta
            rows.append(row)
            observed.append(gb - ga)
            weights.append(1.0 / (sa**2 + sb**2))
    row = np.zeros(ns + nl)
    row[column["1"]] = 1.0
    rows.append(row)
    observed.append(0.0)
    weights.append(1.0 / 0.001**2)
    design, observed, weights = np.array(rows), np.array(observed), np.array(weights)
    normal = design.T @ (weights[:, None] * design)
    if sst:
        s = np.zeros(ns + nl)
        s[:ns] = 1.0
        normal = normal + np.outer(s, s)
    x = np.linalg.solve(normal, design.T @ (weights * observed))
    v = design @ x - observed
    dof = len(observed) - design.shape[1]
    return (
        {s: float(x[column[s]]) for s in stations},
        tuple(float(d) for d in x[ns:]),
        math.sqrt(float(v @ (weights * v)) / dof),
    )


def rounding_envelope(day: PublishedDay, *, seed: int = 7) -> float:
    """How far the printed inputs' rounding alone can move pyGrav's station values.

    Every input is perturbed uniformly within its printed half-digit -- 0.05
    microgal for a value or an SD, 0.005 day for a time -- keeping a reading
    shared between two loops identical in both, and the model re-solved. The
    returned figure is the chosen percentile of the largest station change, in
    mGal: a published value further from GeoComp's than this is not explained
    by the printing.
    """
    rng = np.random.default_rng(seed)
    base, _, _ = pygrav_model(day.loops, sst=True)
    spread = []
    for _ in range(ENVELOPE_SAMPLES):
        loops = []
        for loop in day.loops:
            loops.append(
                [
                    (
                        s,
                        g + rng.uniform(-5e-5, 5e-5),
                        max(sd + rng.uniform(-5e-5, 5e-5), 1e-5),
                        t + rng.uniform(-5e-3, 5e-3),
                    )
                    for s, g, sd, t in loop
                ]
            )
        for earlier, later in pairwise(loops):
            later[0] = earlier[-1]
        moved, _, _ = pygrav_model(loops, sst=True)
        spread.append(max(abs(moved[s] - base[s]) for s in base))
    return float(np.percentile(spread, ENVELOPE_PERCENTILE))


def geocomp_solution(day: PublishedDay):
    """The same day through GeoComp's gravimetry, configured as pyGrav was.

    Independent differences (``correlated=False``), a degree-1 drift per loop
    in days, station 1 observed as ``0 +- 0.001`` mGal. Each loop is a session;
    the reading two loops share is given to both, as pyGrav does.
    """
    from geocomp.core.instruments import GravimeterProfile, ProfileLibrary
    from geocomp.core.techniques.gravimetry import (
        AbsoluteGravity,
        DriftMode,
        DriftOptions,
        GravityReading,
        adjust_gravity_network,
        build_gravity_network,
        reduce_readings,
    )
    from geocomp.core.uncertainty import Quantity
    from geocomp.core.units import Unit

    library = ProfileLibrary()
    library.add_gravimeter(GravimeterProfile(id="CG-5 9379", model="Scintrex CG-5"))
    origin = datetime(2013, 1, 1, tzinfo=UTC)
    readings = []
    for k, loop in enumerate(day.loops, start=1):
        for n, (station, gravity, sd, datenum) in enumerate(loop):
            readings.append(
                GravityReading(
                    id=f"{day.day}/{k}/{n}",
                    station=station,
                    instant=origin + timedelta(days=datenum - 735000.0),
                    value=Quantity.from_std_dev(gravity * MGAL, sd * MGAL, Unit.ACCELERATION),
                    instrument="CG-5 9379",
                    session=f"{day.day}/loop {k}",
                    latitude=math.radians(9.7),
                    longitude=math.radians(1.6),
                    tide_applied=True,
                )
            )
    built = build_gravity_network(
        reduce_readings(readings, library),
        library,
        absolutes=[
            AbsoluteGravity("pyGrav datum", "1", Quantity.from_std_dev(0.0, 0.001 * MGAL, Unit.ACCELERATION))
        ],
        drift=DriftOptions(mode=DriftMode.JOINT, degree=1, time_scale=86400.0, correlated=False),
    )
    return adjust_gravity_network(built)


@dataclass(frozen=True)
class DayComparison:
    day: str
    model_vs_published_ugal: float
    envelope_ugal: float
    geocomp_vs_model_ugal: float
    geocomp_vs_published_ugal: float
    sst_effect_ugal: float
    sd_aposteriori: float
    published_sd_aposteriori: float

    @property
    def passed(self) -> bool:
        return (
            self.model_vs_published_ugal <= self.envelope_ugal
            and self.geocomp_vs_model_ugal <= MACHINE_UGAL
        )


def compare_pygrav(day: PublishedDay) -> DayComparison:
    with_sst, _, _ = pygrav_model(day.loops, sst=True)
    without, _, _ = pygrav_model(day.loops, sst=False)
    result = geocomp_solution(day)
    geocomp = {s: result.gravity(s).value / MGAL for s in without}
    return DayComparison(
        day=day.day,
        model_vs_published_ugal=max(abs(with_sst[s] - day.stations[s]) for s in day.stations) * 1000,
        envelope_ugal=rounding_envelope(day) * 1000,
        geocomp_vs_model_ugal=max(abs(geocomp[s] - without[s]) for s in without) * 1000,
        geocomp_vs_published_ugal=max(abs(geocomp[s] - day.stations[s]) for s in day.stations) * 1000,
        sst_effect_ugal=max(abs(with_sst[s] - without[s]) for s in without) * 1000,
        sd_aposteriori=math.sqrt(result.run.variance_factor_aposteriori),
        published_sd_aposteriori=day.sd_aposteriori,
    )


# -- entry point ----------------------------------------------------------


def run(data: Path) -> int:
    failures = [f"PROVENANCE: {p}" for p in verify(data)]

    survey = read_cg5(data / "cg5" / "CG-5_TestData.txt")
    tide = compare_cg5_tide(survey)
    print(
        f"CG-5 tide, {tide.readings} readings: mean {tide.mean_ugal:+.3f}, rms {tide.rms_ugal:.3f}, "
        f"worst {tide.max_ugal:.3f} microgal (bounds {CG5_RMS_UGAL} rms, {CG5_MAX_UGAL} worst)"
    )
    if not survey.tide_applied:
        failures.append("the CG-5 file says its tide correction was off; nothing to compare")
    if not tide.passed:
        failures.append("CG-5 tide outside its bounds")

    for day in PYGRAV_DAYS:
        comparison = compare_pygrav(read_pygrav(day, data / "pygrav" / day / "LSresults_tot.dat"))
        print(
            f"pyGrav {day}: model {comparison.model_vs_published_ugal:.3f} microgal from published "
            f"(rounding allows {comparison.envelope_ugal:.3f}); "
            f"GeoComp {comparison.geocomp_vs_model_ugal:.2e} from the model without S S^T, "
            f"{comparison.geocomp_vs_published_ugal:.3f} from published, "
            f"of which S S^T is {comparison.sst_effect_ugal:.3f}; "
            f"SD a posteriori {comparison.sd_aposteriori:.4f} "
            f"(published {comparison.published_sd_aposteriori:.4f}, with S S^T)"
        )
        if not comparison.passed:
            failures.append(f"pyGrav {day} not reproduced")

    for failure in failures:
        print(f"FAIL: {failure}")
    return 1 if failures else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--fetch", type=Path, help="clone the references into this directory")
    source.add_argument("--data", type=Path, help="a directory an earlier --fetch filled")
    args = parser.parse_args(argv)
    data = fetch(args.fetch.resolve()) if args.fetch else args.data.resolve()
    return run(data)


if __name__ == "__main__":
    sys.exit(main())
