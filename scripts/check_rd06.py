#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Run the working tree against RD-06's independent NGS coordinates, offline.

Exit 1 means the published-coordinate comparison failed; other errors propagate.
``--verify-inputs`` needs only Python's standard library. Processing additionally
needs NumPy, hatanaka and rnx2rtkp. No old GeoComp checkout is substituted for the
code being developed. See tests/data/rd06/PROVENANCE.md for the unresolved result.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import os
import platform
import re
import subprocess
import sys
import urllib.request
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "tests/data/rd06"
CASES = (
    ("default_001", 1, "GODN", "GODS", False, False),
    ("calibrated_001", 1, "GODN", "GODS", True, False),
    ("calibrated_002", 2, "GODN", "GODS", True, False),
    ("reverse_001", 1, "GODS", "GODN", True, False),
    ("precise_001", 1, "GODN", "GODS", True, True),
)


class AccuracyMismatchError(AssertionError):
    """Only the independent-coordinate discrepancy, never an engine failure."""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_sources(data: Path = DATA, *, include_external: bool = False) -> None:
    for entry in json.loads((data / "source_manifest.json").read_text(encoding="utf-8")):
        if not entry["vendored"] and not include_external:
            continue
        if not entry["vendored"] and not entry["required_for_processing"]:
            continue
        path = data / entry["packaged_path"]
        if entry.get("transformation"):
            original = gzip.decompress(path.read_bytes())
            if hashlib.sha256(original).hexdigest() != entry["sha256"]:
                raise ValueError(f"Original source checksum mismatch: {path}")
        elif sha256(path) != entry["packaged_sha256"]:
            raise ValueError(f"Source checksum mismatch: {path}")


def fetch_sources(data: Path = DATA) -> None:
    """Explicit acquisition only: immutable hashes, bounded reads, atomic writes."""
    for entry in json.loads((data / "source_manifest.json").read_text(encoding="utf-8")):
        path = data / entry["packaged_path"]
        if entry["vendored"] or not entry["required_for_processing"] or path.exists():
            continue
        print(f"Fetching {entry['file']}", flush=True)
        with urllib.request.urlopen(entry["url"], timeout=60) as response:
            original = response.read(entry["bytes"] + 1)
        if len(original) != entry["bytes"] or hashlib.sha256(original).hexdigest() != entry["sha256"]:
            raise ValueError(f"Upstream bytes changed: {entry['file']}; refusing substitution")
        content = gzip.compress(original, mtime=0) if entry.get("transformation") else original
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(path.name + ".part")
        temporary.write_bytes(content)
        temporary.replace(path)
    verify_sources(data, include_external=True)


def official_station(reference: dict, station: str, data: Path = DATA) -> tuple[list, list]:
    """Read the first ITRF2020 ARP block; exclude NAD83, L1PC and monument."""
    entry = reference["stations"][station]
    text = (data / entry["coordinate_sheet"]).read_text(encoding="utf-8").split("NAD_83", 1)[0]
    if "ITRF2020 POSITION (EPOCH 2020.0)" not in text or "Antenna Reference Point(ARP)" not in text:
        raise ValueError("Unexpected coordinate frame, epoch or reference point")
    values = []
    for prefix in ("", "V"):
        vector = []
        for axis in "XYZ":
            match = re.search(r"\|\s+" + prefix + axis + r" =\s*([-\d.]+)", text)
            if match is None:
                raise ValueError(f"Missing official {prefix}{axis} for {station}")
            vector.append(float(match[1]))
        values.append(vector)
    if values != [entry["arp_xyz_m_epoch_2020"], entry["velocity_xyz_m_per_year"]]:
        raise ValueError(f"Reference transcription differs from official sheet: {station}")
    return values[0], values[1]


def load_reference(data: Path = DATA) -> dict:
    verify_sources(data)
    reference = json.loads((data / "reference.json").read_text(encoding="utf-8"))
    for station in reference["stations"]:
        official_station(reference, station, data)
    recorded = reference["recorded_solution"]
    recorded_bytes = gzip.decompress((data / recorded["path"]).read_bytes())
    if hashlib.sha256(recorded_bytes).hexdigest() != recorded["sha256"]:
        raise ValueError("Recorded solution checksum mismatch")
    # This is printed-source precision, not an estimate from the observed error.
    if reference["tolerance_m"] != 0.001:
        raise ValueError("RD-06 must retain the 1 mm printed-precision comparison")
    return reference


def official_position(reference: dict, station: str, day: int) -> list[float]:
    entry = reference["stations"][station]
    epoch = date(2025, 1, 1) + timedelta(days=day - 1)
    years = ((epoch - date(2020, 1, 1)).days + 0.5) / reference["year_days"]
    return [x + years * v for x, v in zip(
        entry["arp_xyz_m_epoch_2020"], entry["velocity_xyz_m_per_year"], strict=True
    )]


def measure_solution(solution, reference: dict, case: tuple) -> dict:
    import numpy as np

    from geocomp.core.geodesy.cartesian import cartesian_to_geodetic, enu_rotation
    from geocomp.core.geodesy.ellipsoid import ELLIPSOIDS
    from geocomp.engines.rtklib.baseline import baseline_from_solution

    name, day, base, rover, _calibrated, _precise = case
    base_xyz = np.array(official_position(reference, base, day))
    expected = np.array(official_position(reference, rover, day))
    baseline = baseline_from_solution(solution, base_station=base, rover_station=rover)
    last = solution.last()  # Same final-epoch policy as the development code.
    delta = np.array(last.position) - expected
    lat, lon, _ = cartesian_to_geodetic(*expected, ELLIPSOIDS["GRS80"])
    enu = enu_rotation(lat, lon) @ delta
    # PosSolution stores GPST calendar labels with a UTC tzinfo; do not apply
    # a UTC/GPST conversion to those labels when checking the epoch sequence.
    start = datetime(2025, 1, 1, tzinfo=UTC) + timedelta(days=day - 1)
    complete = len(solution.epochs) == 2880 and all(
        epoch.time == start + timedelta(seconds=30 * i) for i, epoch in enumerate(solution.epochs)
    )
    return {
        "case": name, "base": base, "rover": rover, "day": f"2025-{day:03d}",
        "official_base_arp_xyz_m": base_xyz.tolist(), "official_rover_arp_xyz_m": expected.tolist(),
        "computed_rover_arp_xyz_m": list(last.position), "difference_xyz_m": delta.tolist(),
        "difference_enu_m": enu.tolist(), "error_3d_m": float(np.linalg.norm(delta)),
        "computed_baseline_xyz_m": [q.value for q in baseline.components],
        "expected_baseline_xyz_m": (expected - base_xyz).tolist(),
        "covariance_xyz_m2": baseline.covariance.matrix.tolist(),
        "formal_sigma_xyz_m": np.sqrt(np.diag(baseline.covariance.matrix)).tolist(),
        "epochs": len(solution.epochs), "last_epoch": last.time.isoformat(),
        "fixed_fraction": solution.fixed_fraction, "last_status": last.status.name,
        "last_satellites": last.satellites, "last_ratio": last.ratio,
        "tolerance_m": reference["tolerance_m"],
        "passes_strict_xyz_comparison": bool(np.all(np.abs(delta) <= reference["tolerance_m"])),
        "full_day_and_fixed": complete and last.is_ambiguity_fixed,
    }


def require_accuracy(metrics: dict, reference: dict) -> None:
    delta = metrics["difference_xyz_m"]
    if len(delta) != 3 or not all(math.isfinite(x) for x in delta):
        raise ValueError("Invalid coordinate differences")
    if any(abs(x) > reference["tolerance_m"] for x in delta):
        raise AccuracyMismatchError(
            f"{metrics['case']}: RD-06 published-coordinate criterion UNMET; "
            f"XYZ error (mm) = {[round(x * 1000, 4) for x in delta]}; "
            f"limit = {reference['tolerance_m'] * 1000:g} mm per component"
        )


def require_processing(summary: dict) -> None:
    for metrics in summary["cases"]:
        for check in ("full_day_and_fixed", "repeat_pos_bit_identical"):
            if not metrics[check]:
                raise RuntimeError(f"{metrics['case']}: {check} failed; see retained evidence")



def _prepare_sessions(work: Path, data: Path, reference: dict) -> dict:
    """Decompress both days into *work* and discover their sessions.

    Shared by :func:`run_all` and :func:`sweep_elevation_mask` so the two see
    exactly the same inputs: a sweep that prepared its data differently would
    not be comparable with the cases it is meant to explain.
    """
    import hatanaka

    from geocomp.io.gnss_discovery import overlapping_groups, scan_folder

    sources = data / "sources"
    sessions_by_day = {}
    for day in (1, 2):
        inputs = work / f"inputs_{day:03d}"
        inputs.mkdir(parents=True, exist_ok=True)
        for station in ("godn", "gods"):
            name = f"{station}{day:03d}0.25"
            target = inputs / f"{name}o"
            if not target.is_file():
                target.write_bytes(hatanaka.decompress((sources / f"{name}d.gz").read_bytes()))
        nav = f"brdc{day:03d}0.25n"
        if not (inputs / nav).is_file():
            (inputs / nav).write_bytes(gzip.decompress((sources / f"{nav}.gz").read_bytes()))
        scan = scan_folder(inputs)
        if scan.skipped or scan.warnings or len(scan.sessions) != 2:
            raise ValueError(f"Session discovery was not clean: {scan}")
        if len(overlapping_groups(scan.sessions)) != 1:
            raise ValueError("Sessions did not overlap")
        sessions_by_day[day] = {session.station_id: session for session in scan.sessions}
        for station, session in sessions_by_day[day].items():
            if session.antenna != reference["stations"][station]["antenna_type"]:
                raise ValueError(f"Unexpected antenna: {station}: {session.antenna}")
    return sessions_by_day

#: Elevation masks the diagnostic sweep uses. Chosen to straddle the point where
#: the two days stop disagreeing: below 25 degrees they differ by up to 11 mm in
#: east, at and above it they agree to a fifth of a millimetre.
SWEEP_MASKS = (10.0, 15.0, 20.0, 25.0, 30.0, 35.0)


def sweep_elevation_mask(
    output: Path, executable: Path, reference: dict, data: Path = DATA,
    *, calibrated: bool = True, masks: tuple[float, ...] = SWEEP_MASKS,
) -> dict:
    """Separate the low-elevation error from whatever is under it.

    A coordinate-reference error is invariant under the elevation mask; a
    multipath or antenna phase-centre error is not, because raising the mask
    discards exactly the observations that carry it. Running both days across a
    range of masks therefore splits the discrepancy into a part that depends on
    which satellites were used and a part that does not -- which is what
    ``specs/22`` section 5 needs in order to attribute it.

    Returns a summary with one row per (day, mask), each carrying the local
    east/north/up error so the two components are readable directly.
    """
    import numpy as np

    from geocomp.core.geodesy.cartesian import cartesian_to_geodetic, ecef_to_enu
    from geocomp.core.geodesy.ellipsoid import ELLIPSOIDS
    from geocomp.engines.rtklib import RtklibConfig, RtklibEngine, RtklibJob
    from geocomp.engines.rtklib.baseline import baseline_from_solution

    work = output.resolve()
    work.mkdir(parents=True, exist_ok=True)
    engine = RtklibEngine(configured=executable)
    sessions_by_day = _prepare_sessions(work, data, reference)
    antenna_file = work / "ngs20.atx" if calibrated else None
    if calibrated and not antenna_file.is_file():
        raise FileNotFoundError(
            f"{antenna_file} is required for a calibrated sweep; run --fetch-inputs, "
            "or pass calibrated=False to sweep the uncalibrated configuration"
        )

    expected = np.array(reference["expected_baseline_GODN_to_GODS_m"])
    origin = reference["stations"]["GODN"]["arp_xyz_m_epoch_2020"]
    latitude, longitude, _ = cartesian_to_geodetic(*origin, ELLIPSOIDS["GRS80"])

    rows = []
    for day in (1, 2):
        for mask in masks:
            extra = {
                "ant1-antdele": "0", "ant1-antdeln": "0", "ant1-antdelu": "0",
                "ant2-antdele": "0", "ant2-antdeln": "0", "ant2-antdelu": "0",
                "pos1-tidecorr": "1", "pos1-dynamics": "off",
            }
            if calibrated:
                extra |= {
                    "ant1-anttype": reference["stations"]["GODS"]["antenna_type"],
                    "ant2-anttype": reference["stations"]["GODN"]["antenna_type"],
                    "file-rcvantfile": str(antenna_file),
                    "file-satantfile": str(antenna_file),
                    "pos1-posopt2": "on",
                }
            config = RtklibConfig(
                name=f"sweep_{day:03d}_{mask:g}", output_format="xyz",
                base_position_type="xyz", elevation_mask=mask,
                base_position=tuple(official_position(reference, "GODN", day)),
                extra=extra,
            )
            job = RtklibJob(rover=sessions_by_day[day]["GODS"],
                            base=sessions_by_day[day]["GODN"],
                            config=config, timeout=600)
            result = engine.run(job, work_dir=work / config.name)
            baseline = baseline_from_solution(
                result.solution, base_station="GODN", rover_station="GODS"
            )
            error = np.array([q.value for q in baseline.components]) - expected
            east, north, up = (v * 1000 for v in ecef_to_enu(tuple(error), latitude, longitude))
            rows.append({
                "day": day, "elevation_mask_deg": mask, "calibrated": calibrated,
                "error_enu_mm": [east, north, up],
                "horizontal_mm": math.hypot(east, north),
                "error_3d_mm": math.sqrt(east * east + north * north + up * up),
                "fixed_fraction": result.solution.fixed_fraction,
            })
            print(f"day {day:03d} mask {mask:4g} deg: "
                  f"E {east:7.3f}  N {north:7.3f}  U {up:7.3f}  "
                  f"3D {rows[-1]['error_3d_mm']:6.3f} mm", flush=True)

    summary = {"dataset_id": reference["dataset_id"], "calibrated": calibrated, "rows": rows}
    (work / "sweep.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def run_all(output: Path, executable: Path, reference: dict, data: Path = DATA) -> dict:
    verify_sources(data, include_external=True)
    import hatanaka
    import numpy as np

    from geocomp.engines.rtklib import RtklibConfig, RtklibEngine, RtklibJob

    work = output.resolve()
    work.mkdir(parents=True, exist_ok=True)
    engine = RtklibEngine(configured=executable)
    sources = data / "sources"
    antenna_file = work / "ngs20.atx"
    antenna_file.write_bytes(gzip.decompress((sources / "ngs20.atx.gz").read_bytes()))
    sessions_by_day = _prepare_sessions(work, data, reference)
    orbit_name = "IGS0OPSFIN_20250010000_01D_15M_ORB.SP3"
    orbit = work / orbit_name
    orbit.write_bytes(gzip.decompress((sources / f"{orbit_name}.gz").read_bytes()))
    if "IGS20" not in orbit.read_text(encoding="ascii").splitlines()[0]:
        raise ValueError("Precise orbit frame differs from IGS20")
    results = []
    for case in CASES:
        name, day, base, rover, calibrated, precise = case
        extra = {}
        if calibrated:
            extra = {
                "ant1-anttype": reference["stations"][rover]["antenna_type"],
                "ant2-anttype": reference["stations"][base]["antenna_type"],
                "ant1-antdele": "0", "ant1-antdeln": "0", "ant1-antdelu": "0",
                "ant2-antdele": "0", "ant2-antdeln": "0", "ant2-antdelu": "0",
                "file-rcvantfile": str(antenna_file), "file-satantfile": str(antenna_file),
                "pos1-posopt2": "on", "pos1-tidecorr": "1", "pos1-dynamics": "off",
            }
        config = RtklibConfig(
            name=name, output_format="xyz", base_position_type="xyz",
            base_position=tuple(official_position(reference, base, day)), extra=extra,
            ephemeris="precise" if precise else "brdc",
        )
        # ARP truth: no second mark-to-ARP reduction. Rover truth is never input.
        settings = config.settings()
        if settings["ant1-postype"] != "single" or any(f"ant1-pos{i}" in settings for i in (1, 2, 3)):
            raise ValueError("The reference rover coordinates must not enter the estimator")
        job = RtklibJob(
            rover=sessions_by_day[day][rover], base=sessions_by_day[day][base],
            config=config, products=(str(orbit),) if precise else (), timeout=300,
        )
        directory = work / name
        result = engine.run(job, work_dir=directory)
        first_hash = sha256(result.output_file)
        metrics = measure_solution(result.solution, reference, case)
        # Preserve the first result even if the repeat fails or differs.
        (directory / "first.pos").write_bytes(result.output_file.read_bytes())
        (directory / "stdout.txt").write_text(result.run.stdout, encoding="utf-8")
        (directory / "stderr.txt").write_text(result.run.stderr, encoding="utf-8")
        (directory / "command.json").write_text(json.dumps(list(result.run.command), indent=2) + "\n")
        repeat = engine.run(job, work_dir=directory)
        records = [line for line in (directory / "first.pos").read_text().splitlines()
                   if line.strip() and not line.startswith("%")]
        metrics.update({
            "repeat_pos_bit_identical": first_hash == sha256(repeat.output_file),
            "pos_sha256": first_hash,
            "solution_records_sha256": hashlib.sha256(("\n".join(records) + "\n").encode()).hexdigest(),
            "seconds_first_run": result.run.seconds,
        })
        (directory / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
        results.append(metrics)
        print(f"{name}: XYZ error (mm) {[round(x * 1000, 4) for x in metrics['difference_xyz_m']]}, "
              f"strict pass={metrics['passes_strict_xyz_comparison']}, "
              f"repeat={metrics['repeat_pos_bit_identical']}", flush=True)
    version = engine.version()
    summary = {
        "dataset_id": reference["dataset_id"],
        "geocomp_commit": subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                                                   text=True).strip(),
        "geocomp_worktree_status": subprocess.check_output(
            ["git", "-C", str(ROOT), "status", "--porcelain"], text=True),
        "expected_rtklib_commit": reference["rtklib_commit"],
        "build_declared_rtklib_commit": os.environ.get("RTKLIB_COMMIT"),
        "engine_version": version.raw, "engine_binary_sha256": sha256(executable),
        "python": sys.version, "platform": platform.platform(), "numpy": np.__version__,
        "hatanaka": hatanaka.__version__, "cases": results,
        "accuracy_criterion_met": all(results[1][key] for key in (
            "passes_strict_xyz_comparison", "full_day_and_fixed", "repeat_pos_bit_identical")),
    }
    (work / "metrics.json").write_text(json.dumps(summary, indent=2) + "\n")
    require_processing(summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "build/rd06")
    parser.add_argument("--engine", type=Path, help="rnx2rtkp executable; otherwise use PATH")
    parser.add_argument(
        "--fetch-inputs", action="store_true", help="Download missing inputs and verify hashes"
    )
    parser.add_argument(
        "--verify-inputs", action="store_true", help="Verify frozen sources without an engine"
    )
    parser.add_argument(
        "--sweep", action="store_true",
        help="Diagnostic: solve both days across a range of elevation masks and report "
             "the east/north/up error of each, instead of running the five cases",
    )
    parser.add_argument(
        "--sweep-uncalibrated", action="store_true",
        help="Sweep without the antenna calibration. The only sweep available where the "
             "NGS ANTEX host is unreachable; the uncalibrated day-001 result sits 0.2 mm "
             "from the calibrated one, so it still attributes a millimetre-level error",
    )
    args = parser.parse_args()
    if args.fetch_inputs:
        fetch_sources()
    reference = load_reference()
    if args.verify_inputs:
        print("RD-06 vendored sources and coordinate transcription verified; accuracy NOT evaluated")
        return 0
    sys.path.insert(0, str(ROOT))
    from geocomp.engines.base import require
    from geocomp.engines.rtklib import RtklibEngine

    version = require(RtklibEngine(configured=args.engine).version(), engine="rnx2rtkp", operation="RD-06")
    if args.sweep or args.sweep_uncalibrated:
        sweep_elevation_mask(
            args.output, version.path, reference, calibrated=not args.sweep_uncalibrated
        )
        return 0
    summary = run_all(args.output, version.path, reference)
    try:
        require_accuracy(summary["cases"][1], reference)
    except AccuracyMismatchError as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
