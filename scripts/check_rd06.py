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
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "tests/data/rd06"
#: name, day, base, rover, calibrated, precise ephemeris.
#:
#: **The accuracy criterion is judged on the GODE cases and not on the GODS
#: ones**, and the reason is in ``reference.json``'s ``antenna_epoch_rule``:
#: GODS's antenna changed on 2020-09-03, after the 2020.0 epoch of the
#: coordinate it is compared against, so its published position describes an
#: instrument the observations are not of. GODS stays in the list unjudged,
#: because one base with two rovers on the same day under the same
#: configuration turns that reading into a controlled experiment rather than an
#: argument: only one of the two rovers can show the effect.
CASES = (
    ("default_gode_001", 1, "GODN", "GODE", False, False),
    ("calibrated_gode_001", 1, "GODN", "GODE", True, False),
    ("calibrated_gode_002", 2, "GODN", "GODE", True, False),
    ("reverse_gode_001", 1, "GODE", "GODN", True, False),
    ("precise_gode_001", 1, "GODN", "GODE", True, True),
    ("calibrated_gods_001", 1, "GODN", "GODS", True, False),
    ("calibrated_gods_002", 2, "GODN", "GODS", True, False),
)


class AccuracyMismatchError(AssertionError):
    """Only the independent-coordinate discrepancy, never an engine failure."""


class UnjudgeableCaseError(AssertionError):
    """The comparison cannot be made, which is not the same as failing it.

    Raised when the case the criterion is judged on was processed with a
    calibration that is not its own antenna's. Reporting that as an accuracy
    result would put a number on a configuration nobody chose.
    """


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


#: The antenna blocks of an IGS site log: "4.1 Antenna Type", its install date
#: and its removal date. "4.x" is the blank template at the end of every log and
#: is skipped by requiring digits.
_ANTENNA_BLOCK = re.compile(
    # ``[^\S\n]*`` and not ``\s*``: under ``re.S`` a plain ``\s*`` crosses the
    # newline, so a log with an *empty* date field lets the match run on and
    # pair this antenna with a later block's dates -- reporting a real antenna
    # against times it was never installed for. Keeping the run-up whitespace
    # on one line makes an empty field read as empty, which
    # :func:`antennas_spanning` then rejects.
    r"^4\.\d+[^\S\n]+Antenna Type[^\S\n]*:[^\S\n]*(?P<type>.+?)[^\S\n]*$.*?"
    r"^[^\S\n]*Date Installed[^\S\n]*:[^\S\n]*(?P<installed>\S*).*?$.*?"
    r"^[^\S\n]*Date Removed[^\S\n]*:[^\S\n]*(?P<removed>\S*).*?$",
    re.S | re.M,
)

#: A site log's dates carry a time ("2020-09-03T00:00Z"); only the day is used,
#: and anything that is not one is not a date at all.
_LOG_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


def _antenna_blocks(text: str) -> list[dict]:
    """Parse section 4 of a site log, in the order the log records it."""
    return [
        {
            "type": match["type"].strip(),
            "installed": match["installed"][:10],
            # The unfilled template reads "(CCYY-MM-DDThh:mmZ)", which is how a
            # log says "still installed".
            "removed": (
                None if not match["removed"] or match["removed"].startswith("(") else match["removed"][:10]
            ),
        }
        for match in _ANTENNA_BLOCK.finditer(text)
    ]


def antennas_spanning(text: str, epoch: str, observed: str) -> set[str]:
    """The antenna types a site log says were on the monument for *both* dates.

    A published coordinate describes the antenna carried while the data behind
    it was collected, so a comparison only means anything when the observations
    are of that same instrument. An antenna spans the interval when it was
    installed on or before *epoch* and was not removed before *observed*.

    The size of the result is the whole diagnosis. **One** type is a station
    worth comparing. **None** means no antenna spans the interval at all --
    GODS read against a 2025 day is exactly this, and it is why that station is
    the counter-case. **More than one** means the hardware changed in between.

    A block whose installation date is missing or malformed is skipped rather
    than guessed at, so the answer errs towards refusing a station.

    Note what is *not* fixed here: *observed* is a free parameter. Reading a
    station against a day adjacent to its coordinate epoch is a different, and
    usually easier, question than reading it against a day five years later --
    see ``specs/22`` section 5.2.
    """
    spanning = set()
    for block in _antenna_blocks(text):
        installed, removed = block["installed"], block["removed"]
        if not _LOG_DATE.fullmatch(installed) or installed > epoch:
            continue
        if removed is not None and removed < observed:
            continue
        spanning.add(block["type"])
    return spanning


def antenna_history(reference: dict, station: str, data: Path = DATA) -> list[dict]:
    """Every antenna the site log records, in the order it records them."""
    entry = reference["stations"][station]
    text = (data / entry["station_log"]).read_text(encoding="utf-8", errors="replace")
    history = _antenna_blocks(text)
    if not history:
        raise ValueError(f"No antenna blocks in the site log for {station}")
    return history


def require_reference_configuration(reference: dict, data: Path = DATA) -> dict:
    """Refuse a comparison whose reference describes a different instrument.

    **This is the guard the 2026-09-23 investigation produced, and the defect it
    exists for was live in this very dataset.** A published coordinate describes
    the antenna that was on the monument while the data behind it was collected.
    GODS's antenna changed on 2020-09-03, eight months after the 2020.0 epoch of
    its published position; NGS's own MYCS3 page says such a change moves a
    coordinate by "a few mm to several centimeters"; and GODN to GODS missed the
    published baseline by 6 to 7 mm in north on all four days tried, while GODN
    to GODE -- whose antenna predates the epoch -- did not.

    Nothing about that is visible in the coordinate sheet, which prints no
    uncertainty and no equipment history. It is visible in the site log, which
    is vendored beside the sheet precisely so this can be checked offline on
    every commit rather than rediscovered.

    A station carrying ``antenna_epoch_exempt`` is the counter-case and is not
    required to pass -- but the guard checks that its exemption is still
    *earned*, so an exemption cannot outlive the defect it was written for.
    """
    epoch = reference["reference_epoch"][:10]
    findings = {}
    for station in sorted(reference["stations"]):
        history = antenna_history(reference, station, data)
        current = [entry for entry in history if entry["removed"] is None]
        if len(current) != 1:
            raise ValueError(
                f"{station}: the site log records {len(current)} current antennas; "
                "one is needed to say which instrument the observations are of"
            )
        declared = reference["stations"][station]
        if current[0]["type"] != declared["antenna_type"]:
            raise ValueError(
                f"{station}: site log says {current[0]['type']!r}, "
                f"reference.json says {declared['antenna_type']!r}"
            )
        if current[0]["installed"] != declared["antenna_installed"]:
            raise ValueError(
                f"{station}: site log installs the antenna on {current[0]['installed']}, "
                f"reference.json says {declared['antenna_installed']}"
            )
        findings[station] = {
            "antenna_type": current[0]["type"],
            "installed": current[0]["installed"],
            "changes_recorded": len(history),
            "predates_coordinate_epoch": current[0]["installed"] <= epoch,
        }
    for station, finding in sorted(findings.items()):
        exempt = reference["stations"][station].get("antenna_epoch_exempt")
        finding["exempt"] = bool(exempt)
        if exempt and finding["predates_coordinate_epoch"]:
            raise ValueError(
                f"{station} is exempted as the counter-case, but its antenna now predates "
                f"the {epoch} coordinate epoch; the exemption no longer describes anything "
                "and should be removed rather than left to excuse a future station"
            )
        if not exempt and not finding["predates_coordinate_epoch"]:
            raise ValueError(
                f"{station}: its antenna was installed on {finding['installed']}, "
                f"after the {epoch} epoch of the coordinate it is compared against; "
                "the published position describes an instrument these observations are not of"
            )
    return findings


def phase_centre_offsets(reference: dict, data: Path = DATA) -> dict:
    """How far each sheet's own two coordinates disagree, needing no engine.

    Each NGS sheet publishes the same monument twice: once at the antenna
    reference point and once at the L1 phase centre. **An L1 offset is vertical
    by construction**, so the two published positions may differ in height and
    must not differ horizontally: two verticals 76 m apart diverge by 1.2e-5
    radians, which turns 85 mm of offset into under a micrometre sideways.

    Whatever horizontal difference the sheet does show is therefore the
    publisher's own inconsistency, measured from the publisher's own numbers
    with nothing assumed. It is the only bound on the reference's uncertainty
    available here: the sheets print no covariance, and the two stations carry
    identical published velocities, so the five-year propagation to the
    observation epoch contributes exactly nothing to the baseline and cannot be
    the cause either.

    It is a *lower* bound. An error common to both of a station's coordinates
    cancels in this difference and leaves no trace on the sheet.
    """
    import numpy as np

    from geocomp.core.geodesy.cartesian import cartesian_to_geodetic, ecef_to_enu
    from geocomp.core.geodesy.ellipsoid import ELLIPSOIDS

    offsets: dict[str, Any] = {}
    origin = reference["stations"]["GODN"]["arp_xyz_m_epoch_2020"]
    latitude, longitude, _ = cartesian_to_geodetic(*origin, ELLIPSOIDS["GRS80"])
    for station, entry in reference["stations"].items():
        text = (data / entry["coordinate_sheet"]).read_text(encoding="utf-8")
        if text.count("L1 Phase Center") != 1:
            raise ValueError(f"Unexpected sheet layout for {station}")
        arp_text, l1_text = text.split("L1 Phase Center", 1)
        positions = []
        for chunk in (arp_text, l1_text):
            block = chunk.split("NAD_83", 1)[0]
            if "ITRF2020 POSITION (EPOCH 2020.0)" not in block:
                raise ValueError(f"Unexpected coordinate frame or epoch for {station}")
            positions.append(
                [float(re.search(r"\|\s+" + axis + r" =\s*([-\d.]+)", block)[1]) for axis in "XYZ"]
            )
        if positions[0] != entry["arp_xyz_m_epoch_2020"]:
            raise ValueError(f"Reference transcription differs from official sheet: {station}")
        east, north, up = (
            v * 1000
            for v in ecef_to_enu(tuple(np.array(positions[1]) - np.array(positions[0])), latitude, longitude)
        )
        offsets[station] = {
            "arp_to_l1pc_enu_mm": [east, north, up],
            "horizontal_inconsistency_mm": math.hypot(east, north),
            "antenna_type": entry["antenna_type"],
        }
    return offsets


def load_reference(data: Path = DATA) -> dict:
    verify_sources(data)
    reference = json.loads((data / "reference.json").read_text(encoding="utf-8"))
    for station in reference["stations"]:
        official_station(reference, station, data)
    require_reference_configuration(reference, data)
    # Each expected baseline is the difference of the two transcribed positions,
    # recomputed rather than trusted: a transcription that is right in the
    # stations block and stale in the baseline would be invisible otherwise.
    base = reference["stations"]["GODN"]["arp_xyz_m_epoch_2020"]
    for rover in ("GODE", "GODS"):
        expected = reference[f"expected_baseline_GODN_to_{rover}_m"]
        vector = [
            round(b - a, 4)
            for a, b in zip(base, reference["stations"][rover]["arp_xyz_m_epoch_2020"], strict=True)
        ]
        if [round(v, 4) for v in expected] != vector:
            raise ValueError(f"expected_baseline_GODN_to_{rover}_m is not the published difference")
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
    return [
        x + years * v
        for x, v in zip(entry["arp_xyz_m_epoch_2020"], entry["velocity_xyz_m_per_year"], strict=True)
    ]


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
        "case": name,
        "base": base,
        "rover": rover,
        "day": f"2025-{day:03d}",
        "official_base_arp_xyz_m": base_xyz.tolist(),
        "official_rover_arp_xyz_m": expected.tolist(),
        "computed_rover_arp_xyz_m": list(last.position),
        "difference_xyz_m": delta.tolist(),
        "difference_enu_m": enu.tolist(),
        "error_3d_m": float(np.linalg.norm(delta)),
        "computed_baseline_xyz_m": [q.value for q in baseline.components],
        "expected_baseline_xyz_m": (expected - base_xyz).tolist(),
        "covariance_xyz_m2": baseline.covariance.matrix.tolist(),
        "formal_sigma_xyz_m": np.sqrt(np.diag(baseline.covariance.matrix)).tolist(),
        "epochs": len(solution.epochs),
        "last_epoch": last.time.isoformat(),
        "fixed_fraction": solution.fixed_fraction,
        "last_status": last.status.name,
        "last_satellites": last.satellites,
        "last_ratio": last.ratio,
        "tolerance_m": reference["tolerance_m"],
        "passes_strict_xyz_comparison": bool(np.all(np.abs(delta) <= reference["tolerance_m"])),
        "full_day_and_fixed": complete and last.is_ambiguity_fixed,
        "resolved_antennas": {str(k): v for k, v in solution.antennas.items()},
        "antenna_calibration": _calibration_status(solution, reference, case),
    }


#: What the engine's ANTEX lookup actually did, worst case across the two
#: receivers. ``None`` for an uncalibrated run, where the question does not
#: arise. The three outcomes are genuinely different and were collapsed into a
#: bool until engine CI produced the third one on real data.
EXACT = "exact"
RADOME_SUBSTITUTED = "radome_substituted"
UNCALIBRATED = "none"


def _calibration_status(solution, reference: dict, case: tuple) -> str | None:
    """What the engine's antenna lookup did, per ``specs/08`` section 7.5.

    ``rnx2rtkp`` looks the configured antenna up in the ANTEX and, on a miss,
    **clears the name and processes on with no calibration for that receiver**;
    the warning goes to a trace file that is off by default. Before that, it
    retries the match **without the radome**, which succeeds against a different
    calibration. The engine's own header is the only evidence either happened,
    because it writes back the entry it *matched* rather than the one it was
    given.

    The two outcomes are not equally bad and must not be reported as one:

    * ``none`` -- no calibration at all. The case is meaningless and refused.
    * ``radome_substituted`` -- a real calibration of the same antenna under a
      different dome. NGS states its calibrations are keyed by *antenna code
      plus radome code*, so this is a genuine confound rather than a formality,
      and a case carrying it cannot be judged for accuracy. It is recorded and
      the run continues, because the evidence is worth more than the abort.
    """
    _, _, base, rover, calibrated, _ = case
    if not calibrated:
        return None
    status = EXACT
    for index, station in ((1, rover), (2, base)):
        wanted = reference["stations"][station]["antenna_type"].split()
        got = solution.antennas.get(index, "").split()
        if not got:
            return UNCALIBRATED
        if got != wanted:
            # Same antenna, different dome: `searchpcv`'s second pass matches on
            # the antenna code alone.
            if got[:1] != wanted[:1]:
                return UNCALIBRATED
            status = RADOME_SUBSTITUTED
    return status


def accuracy_case(results: list[dict], reference: dict) -> dict:
    """The one case the criterion is judged on, found by name rather than index.

    It used to be ``results[1]``. Adding the counter-case to ``CASES`` would
    have moved that index silently and judged a different baseline while
    reporting the same thing.
    """
    for metrics in results:
        if metrics["case"] == reference["accuracy_case"]:
            return metrics
    raise ValueError(f"{reference['accuracy_case']} is not among the cases that ran")


def require_exact_calibration(metrics: dict) -> None:
    """The judged case must carry its own antennas' calibration, not a near one."""
    if metrics["antenna_calibration"] == RADOME_SUBSTITUTED:
        raise UnjudgeableCaseError(
            f"{metrics['case']}: the ANTEX has no entry for this station's antenna *and "
            f"radome*, so the engine calibrated it with another dome's pattern. It resolved "
            f"{metrics['resolved_antennas']}. NGS keys its calibrations by antenna code plus "
            "radome code and uses them in the products this comparison is against, so the "
            "substitution is a confound, not a formality. See specs/22 section 5.2"
        )


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
        # No calibration at all is a processing error: the case is labelled
        # calibrated and is not. A substituted radome is a real calibration of
        # the same antenna and is recorded instead, because it disqualifies the
        # case from being *judged* rather than from being evidence.
        if metrics["antenna_calibration"] == UNCALIBRATED:
            raise RuntimeError(
                f"{metrics['case']}: the ANTEX had no entry for an antenna it was given, so "
                f"the engine applied no calibration and said nothing. It resolved "
                f"{metrics['resolved_antennas']}. See specs/08 section 7.5"
            )


#: The days the frozen bundle carries. Both are processed by every diagnostic,
#: because a single day cannot tell a constant error from a varying one.
DAYS = (1, 2)


def _prepare_sessions(work: Path, data: Path, reference: dict, *, days: tuple[int, ...] = DAYS) -> dict:
    """Decompress each day into *work* and discover its sessions.

    Shared by :func:`run_all`, :func:`sweep_elevation_mask` and
    :func:`measure_repeatability` so all three see exactly the same inputs: a
    diagnostic that prepared its data differently would not be comparable with
    the cases it is meant to explain.
    """
    import hatanaka

    from geocomp.io.gnss_discovery import overlapping_groups, scan_folder

    sources = data / "sources"
    stations = sorted(reference["stations"])
    sessions_by_day = {}
    for day in days:
        inputs = work / f"inputs_{day:03d}"
        inputs.mkdir(parents=True, exist_ok=True)
        for station in stations:
            name = f"{station.lower()}{day:03d}0.25"
            target = inputs / f"{name}o"
            if not target.is_file():
                target.write_bytes(hatanaka.decompress((sources / f"{name}d.gz").read_bytes()))
        nav = f"brdc{day:03d}0.25n"
        if not (inputs / nav).is_file():
            (inputs / nav).write_bytes(gzip.decompress((sources / f"{nav}.gz").read_bytes()))
        scan = scan_folder(inputs)
        if scan.skipped or scan.warnings or len(scan.sessions) != len(stations):
            raise ValueError(f"Session discovery was not clean: {scan}")
        if len(overlapping_groups(scan.sessions)) != 1:
            raise ValueError("Sessions did not overlap")
        sessions_by_day[day] = {session.station_id: session for session in scan.sessions}
        if sorted(sessions_by_day[day]) != stations:
            raise ValueError(f"Discovered {sorted(sessions_by_day[day])}, expected {stations}")
        for station, session in sessions_by_day[day].items():
            if session.antenna != reference["stations"][station]["antenna_type"]:
                raise ValueError(f"Unexpected antenna: {station}: {session.antenna}")
    return sessions_by_day


#: Elevation masks the diagnostic sweep uses. Chosen to straddle the point where
#: the two days stop disagreeing: below 25 degrees they differ by up to 11 mm in
#: east, at and above it they agree to a fifth of a millimetre.
SWEEP_MASKS = (10.0, 15.0, 20.0, 25.0, 30.0, 35.0)

#: Sub-session lengths in hours, for the repeatability measurement. The full day
#: is included so that the answer RD-06 is judged on comes out of the *same* code
#: path as the sub-sessions it is compared against; the halves, quarters and hours
#: below it give 2, 4 and 24 solutions a day. A single length measures a number,
#: several measure a trend, and the trend is what a full-day tolerance has to be
#: extrapolated along.
REPEATABILITY_SPANS = (24, 12, 6, 1)


def _antenna_file(work: Path, data: Path) -> Path:
    """Decompress the NGS calibration, refusing to silently run without it."""
    archive = data / "sources" / "ngs20.atx.gz"
    if not archive.is_file():
        raise FileNotFoundError(
            f"{archive} is required for a calibrated run; fetch it with --fetch-inputs, "
            "or use --sweep-uncalibrated / --repeatability-uncalibrated where "
            "geodesy.noaa.gov is unreachable"
        )
    antenna_file = work / "ngs20.atx"
    antenna_file.write_bytes(gzip.decompress(archive.read_bytes()))
    return antenna_file


def _processing_options(
    reference: dict, *, base: str, rover: str, calibrated: bool, antenna_file: Path | None
) -> dict[str, str]:
    """The options every diagnostic shares, so their results are comparable.

    The sweep and the repeatability measurement answer different questions
    about the same discrepancy; if they configured the engine differently,
    neither could be read against the other. The antenna deltas are zeroed
    because the reference coordinates are ARP values -- the reduction is
    already in the truth, and applying it again would be the FR-602 double
    reduction this project refuses elsewhere.

    ``ant1`` is the **rover** and ``ant2`` the base, which is the order
    ``rnx2rtkp`` reads its two observation files in. Naming the two antennas
    from the station they belong to rather than hard-coding a pair is what lets
    the accuracy case and the counter-case share this function: getting the two
    the wrong way round applies each antenna's calibration at the other end,
    which is a few millimetres and looks like an ordinary result.
    """
    extra = {
        "ant1-antdele": "0",
        "ant1-antdeln": "0",
        "ant1-antdelu": "0",
        "ant2-antdele": "0",
        "ant2-antdeln": "0",
        "ant2-antdelu": "0",
        "pos1-tidecorr": "1",
        "pos1-dynamics": "off",
    }
    if calibrated:
        if antenna_file is None:
            raise ValueError("A calibrated run needs an antenna file")
        extra |= {
            "ant1-anttype": reference["stations"][rover]["antenna_type"],
            "ant2-anttype": reference["stations"][base]["antenna_type"],
            "file-rcvantfile": str(antenna_file),
            "file-satantfile": str(antenna_file),
            "pos1-posopt2": "on",
        }
    return extra


def sweep_elevation_mask(
    output: Path,
    executable: Path,
    reference: dict,
    data: Path = DATA,
    *,
    calibrated: bool = True,
    masks: tuple[float, ...] = SWEEP_MASKS,
    base: str = "GODN",
    rover: str = "GODS",
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

    # Decompressed here rather than assumed present. The first version of this
    # expected `run_all` to have left the file behind, which it does -- in *its*
    # output directory, not the sweep's. Under `continue-on-error` that surfaced
    # as a step which "succeeded" in two seconds having done nothing, which is
    # the failure mode this whole script exists to refuse elsewhere.
    antenna_file = _antenna_file(work, data) if calibrated else None

    expected = np.array(reference[f"expected_baseline_{base}_to_{rover}_m"])
    origin = reference["stations"][base]["arp_xyz_m_epoch_2020"]
    latitude, longitude, _ = cartesian_to_geodetic(*origin, ELLIPSOIDS["GRS80"])

    extra = _processing_options(
        reference, base=base, rover=rover, calibrated=calibrated, antenna_file=antenna_file
    )
    rows = []
    for day in DAYS:
        for mask in masks:
            config = RtklibConfig(
                name=f"sweep_{rover.lower()}_{day:03d}_{mask:g}",
                output_format="xyz",
                base_position_type="xyz",
                elevation_mask=mask,
                base_position=tuple(official_position(reference, base, day)),
                extra=extra,
            )
            job = RtklibJob(
                rover=sessions_by_day[day][rover], base=sessions_by_day[day][base], config=config, timeout=600
            )
            result = engine.run(job, work_dir=work / config.name)
            baseline = baseline_from_solution(result.solution, base_station=base, rover_station=rover)
            error = np.array([q.value for q in baseline.components]) - expected
            east, north, up = (v * 1000 for v in ecef_to_enu(tuple(error), latitude, longitude))
            rows.append(
                {
                    "day": day,
                    "baseline": f"{base}-{rover}",
                    "elevation_mask_deg": mask,
                    "calibrated": calibrated,
                    "error_enu_mm": [east, north, up],
                    "horizontal_mm": math.hypot(east, north),
                    "error_3d_mm": math.sqrt(east * east + north * north + up * up),
                    "fixed_fraction": result.solution.fixed_fraction,
                }
            )
            print(
                f"day {day:03d} mask {mask:4g} deg: "
                f"E {east:7.3f}  N {north:7.3f}  U {up:7.3f}  "
                f"3D {rows[-1]['error_3d_mm']:6.3f} mm",
                flush=True,
            )

    summary = {
        "dataset_id": reference["dataset_id"],
        "baseline": f"{base}-{rover}",
        "calibrated": calibrated,
        "rows": rows,
    }
    (work / "sweep.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def measure_repeatability(
    output: Path,
    executable: Path,
    reference: dict,
    data: Path = DATA,
    *,
    calibrated: bool = True,
    mask: float = 15.0,
    spans: tuple[int, ...] = REPEATABILITY_SPANS,
    base: str = "GODN",
    rover: str = "GODE",
) -> dict:
    """Solve the same baseline from sub-sessions, and report how much it moves.

    **Why this and not the two full days.** Day 001 and day 002 agree to a
    fifth of a millimetre at a high mask, and it is tempting to read that as
    the estimator's uncertainty. It is not. GPS geometry repeats every sidereal
    day, so two consecutive days see nearly the same satellites in nearly the
    same places, and any error driven by geometry -- multipath, residual phase
    centre variation -- repeats with them. Their agreement bounds the
    *day-to-day change* in that error, not the error. Splitting a day into
    hours breaks the repetition: each hour has a different sky, so the scatter
    across hours exposes exactly what the day-to-day comparison conceals.

    The scatter is reported about the mean of the sub-sessions, which is
    *precision*, separately from the mean's own distance to the published
    coordinates, which is *accuracy*. Conflating them is how a tolerance ends
    up describing neither.
    """
    import numpy as np

    from geocomp.core.geodesy.cartesian import (
        cartesian_to_geodetic,
        ecef_to_enu,
        ecef_to_enu_covariance,
    )
    from geocomp.core.geodesy.ellipsoid import ELLIPSOIDS
    from geocomp.engines.rtklib import RtklibConfig, RtklibEngine, RtklibJob
    from geocomp.engines.rtklib.baseline import baseline_from_solution

    work = output.resolve()
    work.mkdir(parents=True, exist_ok=True)
    engine = RtklibEngine(configured=executable)
    sessions_by_day = _prepare_sessions(work, data, reference)
    antenna_file = _antenna_file(work, data) if calibrated else None
    extra = _processing_options(
        reference, base=base, rover=rover, calibrated=calibrated, antenna_file=antenna_file
    )

    expected = np.array(reference[f"expected_baseline_{base}_to_{rover}_m"])
    origin = reference["stations"][base]["arp_xyz_m_epoch_2020"]
    latitude, longitude, _ = cartesian_to_geodetic(*origin, ELLIPSOIDS["GRS80"])
    interval = timedelta(seconds=30)

    rows = []
    for day in DAYS:
        midnight = datetime(2025, 1, 1, tzinfo=UTC) + timedelta(days=day - 1)
        for span in spans:
            for index in range(24 // span):
                start = midnight + timedelta(hours=span * index)
                # One interval short of the next window's start: rnx2rtkp's
                # `-te` is inclusive, so the naive bound would put the boundary
                # epoch in both windows and correlate neighbours slightly.
                end = start + timedelta(hours=span) - interval
                config = RtklibConfig(
                    name=f"rep_{rover.lower()}_{day:03d}_{span:02d}h_{index:02d}",
                    output_format="xyz",
                    base_position_type="xyz",
                    elevation_mask=mask,
                    base_position=tuple(official_position(reference, base, day)),
                    extra=extra,
                )
                job = RtklibJob(
                    rover=sessions_by_day[day][rover],
                    base=sessions_by_day[day][base],
                    config=config,
                    window=(start, end),
                    timeout=600,
                )
                result = engine.run(job, work_dir=work / config.name)
                solution = result.solution
                if len(solution.epochs) != span * 120:
                    raise RuntimeError(
                        f"{config.name}: {len(solution.epochs)} epochs, expected {span * 120}; "
                        "a short sub-session would bias the scatter rather than show itself"
                    )
                baseline = baseline_from_solution(solution, base_station=base, rover_station=rover)
                error = np.array([q.value for q in baseline.components]) - expected
                east, north, up = (v * 1000 for v in ecef_to_enu(tuple(error), latitude, longitude))
                # The formal uncertainty is recorded beside the error so the two
                # can be read against each other. A wrong integer fix is not a
                # large residual -- it is a different, confidently held answer --
                # so whether the engine's own covariance grows when the answer is
                # metres out is a question the data has to settle, not an
                # assumption a rejection rule can be built on.
                # Rotate the covariance, not the standard deviations. Three
                # sigmas are not a vector; ``R`` applied to them would produce
                # three plausible numbers that are not anyone's uncertainty.
                formal_enu = (
                    np.sqrt(np.diag(ecef_to_enu_covariance(baseline.covariance, latitude, longitude).matrix))
                    * 1000
                ).tolist()
                last = solution.last()
                rows.append(
                    {
                        "day": day,
                        "baseline": f"{base}-{rover}",
                        "span_hours": span,
                        "index": index,
                        "start": start.isoformat(),
                        "end": end.isoformat(),
                        "elevation_mask_deg": mask,
                        "calibrated": calibrated,
                        "error_enu_mm": [east, north, up],
                        "error_3d_mm": math.sqrt(east * east + north * north + up * up),
                        "formal_sigma_enu_mm": formal_enu,
                        "epochs": len(solution.epochs),
                        "fixed_fraction": solution.fixed_fraction,
                        "last_status": last.status.name,
                        "last_ratio": last.ratio,
                        "ambiguity_fixed": last.is_ambiguity_fixed,
                    }
                )
                print(
                    f"day {day:03d} {span:2d} h #{index:02d} "
                    f"{start:%H:%M}: E {east:8.3f}  N {north:8.3f}  U {up:8.3f}  "
                    f"fixed {solution.fixed_fraction:5.3f}  ratio {last.ratio:5.1f}  "
                    f"sigma3D {math.sqrt(sum(v * v for v in formal_enu)):6.3f} mm",
                    flush=True,
                )

    summary = {
        "dataset_id": reference["dataset_id"],
        "baseline": f"{base}-{rover}",
        "calibrated": calibrated,
        "elevation_mask_deg": mask,
        "spans_hours": list(spans),
        "rows": rows,
        "statistics": _repeatability_statistics(rows, spans),
    }
    (work / "repeatability.json").write_text(json.dumps(summary, indent=2) + "\n")
    _print_repeatability(summary)
    return summary


def _repeatability_statistics(rows: list[dict], spans: tuple[int, ...]) -> dict:
    """Scatter about the mean, per component, per session length.

    Three quantities are kept apart because conflating any two of them is how a
    tolerance ends up describing nothing:

    * the **mean** error of a session length -- accuracy, the distance to the
      published coordinates;
    * the **scatter** about that mean -- precision, how much the answer moves;
    * the **robust** scatter, which is the same statistic computed so that one
      wrongly fixed solution cannot set it.

    ``ddof=1``: these are samples of a process, not a population, and with four
    six-hour solutions a day the difference is not cosmetic. A session length
    with one solution per day has no within-day scatter, and that is reported as
    absent rather than as zero.

    Nothing is discarded. ``outliers`` names the solutions sitting more than
    five robust scales from the median so a reader can see what the two
    statistics disagree about, and both are reported either way.
    """
    import numpy as np

    statistics: dict[str, Any] = {"per_span": {}}
    for span in spans:
        selected = [row for row in rows if row["span_hours"] == span]
        if not selected:
            continue
        errors = np.array([row["error_enu_mm"] for row in selected])
        per_day: dict[int, dict] = {}
        for day in sorted({row["day"] for row in selected}):
            day_errors = np.array([row["error_enu_mm"] for row in selected if row["day"] == day])
            per_day[day] = {
                "solutions": len(day_errors),
                "mean_enu_mm": day_errors.mean(axis=0).tolist(),
                "sigma_enu_mm": (day_errors.std(axis=0, ddof=1).tolist() if len(day_errors) > 1 else None),
            }
        entry: dict[str, Any] = {
            "solutions": len(selected),
            "mean_enu_mm": errors.mean(axis=0).tolist(),
            "median_enu_mm": np.median(errors, axis=0).tolist(),
            "worst_error_3d_mm": float(np.linalg.norm(errors, axis=1).max()),
            "min_fixed_fraction": min(row["fixed_fraction"] for row in selected),
            "mean_formal_sigma_enu_mm": np.array([row["formal_sigma_enu_mm"] for row in selected])
            .mean(axis=0)
            .tolist(),
            "per_day": per_day,
        }
        entry["sigma_enu_mm"] = errors.std(axis=0, ddof=1).tolist() if len(selected) > 1 else None
        # Scatter about each day's own mean: a day-to-day offset is a different
        # quantity from within-day repeatability and must not inflate it.
        degrees = len(selected) - len(per_day)
        if degrees > 0:
            residuals = np.vstack(
                [
                    np.array([row["error_enu_mm"] for row in selected if row["day"] == day])
                    - per_day[day]["mean_enu_mm"]
                    for day in per_day
                ]
            )
            within = np.sqrt((residuals**2).sum(axis=0) / degrees)
            entry["sigma_within_day_enu_mm"] = within.tolist()
            entry["sigma_within_day_3d_mm"] = float(np.linalg.norm(within))
        else:
            entry["sigma_within_day_enu_mm"] = None
            entry["sigma_within_day_3d_mm"] = None
        # 1.4826 turns a median absolute deviation into a standard deviation for
        # a normal sample; it is the scale a single wrong fix cannot move.
        deviations = np.abs(errors - np.median(errors, axis=0))
        robust = 1.4826 * np.median(deviations, axis=0)
        entry["robust_sigma_enu_mm"] = robust.tolist()
        entry["robust_sigma_3d_mm"] = float(np.linalg.norm(robust))
        scale = np.where(robust > 0, robust, np.inf)
        entry["outliers"] = [
            {
                "start": row["start"],
                "error_enu_mm": row["error_enu_mm"],
                "fixed_fraction": row["fixed_fraction"],
                "last_ratio": row["last_ratio"],
                "formal_sigma_enu_mm": row["formal_sigma_enu_mm"],
            }
            for row, deviation in zip(selected, deviations, strict=True)
            if bool(np.any(deviation > 5 * scale))
        ]
        statistics["per_span"][span] = entry

    fitted = [
        span
        for span in sorted(statistics["per_span"])
        if statistics["per_span"][span]["sigma_within_day_enu_mm"] is not None
    ]
    if len(fitted) >= 2:
        statistics["scaling"] = _scaling(statistics["per_span"], fitted)
        statistics["robust_scaling"] = _scaling(statistics["per_span"], fitted, key="robust_sigma_enu_mm")
    return statistics


def _scaling(per_span: dict, spans: list[int], *, key: str = "sigma_within_day_enu_mm") -> dict:
    """Fit ``sigma(T) = a * T ** -p`` through the session lengths, in log-log.

    ``p = 0.5`` is what averaging white noise gives. A smaller exponent means
    the scatter has a floor a longer session does not remove, and that floor is
    the part a full-day tolerance has to carry.

    **This is an extrapolation and is labelled one.** ``residual_log10`` is the
    largest distance from the fitted line; with only two lengths it is zero
    because two points determine a line, and a zero there is not agreement.
    """
    import numpy as np

    lengths = np.log10(np.array(spans, dtype=float))
    sigmas = np.log10(np.array([per_span[span][key] for span in spans]))
    exponents, intercepts, residuals = [], [], []
    for component in range(3):
        slope, intercept = np.polyfit(lengths, sigmas[:, component], 1)
        exponents.append(-slope)
        intercepts.append(intercept)
        residuals.append(float(np.abs(sigmas[:, component] - (slope * lengths + intercept)).max()))
    predicted = [
        float(10 ** (intercepts[component] - exponents[component] * np.log10(24.0))) for component in range(3)
    ]
    return {
        "from": key,
        "spans_hours": spans,
        "exponent_enu": exponents,
        "white_noise_exponent": 0.5,
        "residual_log10": residuals,
        "extrapolated_24h_sigma_enu_mm": predicted,
        "points": len(spans),
    }


def _print_repeatability(summary: dict) -> None:
    print(
        f"\n--- RD-06 sub-session repeatability, {summary['baseline']} "
        f"(mask {summary['elevation_mask_deg']:g} deg, "
        f"{'calibrated' if summary['calibrated'] else 'uncalibrated'}) ---"
    )
    for span, values in sorted(summary["statistics"]["per_span"].items(), reverse=True):
        mean = values["mean_enu_mm"]
        robust = values["robust_sigma_enu_mm"]
        within = values["sigma_within_day_enu_mm"]
        shown = (
            "  ---  ---  ---" if within is None else (f"{within[0]:6.3f} {within[1]:6.3f} {within[2]:6.3f}")
        )
        print(
            f"{span:2} h x {values['solutions']:2}: "
            f"mean E {mean[0]:7.3f} N {mean[1]:7.3f} U {mean[2]:7.3f} | "
            f"sigma {shown} | robust {robust[0]:6.3f} {robust[1]:6.3f} {robust[2]:6.3f} | "
            f"{len(values['outliers'])} outlier(s)"
        )
    for name in ("scaling", "robust_scaling"):
        scaling = summary["statistics"].get(name)
        if not scaling:
            continue
        exponent = scaling["exponent_enu"]
        extrapolated = scaling["extrapolated_24h_sigma_enu_mm"]
        print(
            f"{name}: exponent E {exponent[0]:.3f} N {exponent[1]:.3f} U {exponent[2]:.3f} "
            f"(white noise 0.5); 24 h sigma E {extrapolated[0]:.3f} "
            f"N {extrapolated[1]:.3f} U {extrapolated[2]:.3f} mm"
        )


def run_all(output: Path, executable: Path, reference: dict, data: Path = DATA) -> dict:
    verify_sources(data, include_external=True)
    import hatanaka
    import numpy as np

    from geocomp.engines.rtklib import RtklibConfig, RtklibEngine, RtklibJob

    work = output.resolve()
    work.mkdir(parents=True, exist_ok=True)
    engine = RtklibEngine(configured=executable)
    sources = data / "sources"
    antenna_file = _antenna_file(work, data)
    sessions_by_day = _prepare_sessions(work, data, reference)
    orbit_name = "IGS0OPSFIN_20250010000_01D_15M_ORB.SP3"
    orbit = work / orbit_name
    orbit.write_bytes(gzip.decompress((sources / f"{orbit_name}.gz").read_bytes()))
    if "IGS20" not in orbit.read_text(encoding="ascii").splitlines()[0]:
        raise ValueError("Precise orbit frame differs from IGS20")
    results = []
    for case in CASES:
        name, day, base, rover, calibrated, precise = case
        # The same options the two diagnostics use, so a case and the sweep or
        # repeatability run that explains it are the same configuration.
        extra = (
            _processing_options(
                reference,
                base=base,
                rover=rover,
                calibrated=calibrated,
                antenna_file=antenna_file,
            )
            if calibrated
            else _processing_options(
                reference,
                base=base,
                rover=rover,
                calibrated=False,
                antenna_file=None,
            )
        )
        config = RtklibConfig(
            name=name,
            output_format="xyz",
            base_position_type="xyz",
            base_position=tuple(official_position(reference, base, day)),
            extra=extra,
            ephemeris="precise" if precise else "brdc",
        )
        # ARP truth: no second mark-to-ARP reduction. Rover truth is never input.
        settings = config.settings()
        if settings["ant1-postype"] != "single" or any(f"ant1-pos{i}" in settings for i in (1, 2, 3)):
            raise ValueError("The reference rover coordinates must not enter the estimator")
        job = RtklibJob(
            rover=sessions_by_day[day][rover],
            base=sessions_by_day[day][base],
            config=config,
            products=(str(orbit),) if precise else (),
            timeout=300,
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
        records = [
            line
            for line in (directory / "first.pos").read_text().splitlines()
            if line.strip() and not line.startswith("%")
        ]
        metrics.update(
            {
                "repeat_pos_bit_identical": first_hash == sha256(repeat.output_file),
                "pos_sha256": first_hash,
                "solution_records_sha256": hashlib.sha256(("\n".join(records) + "\n").encode()).hexdigest(),
                "seconds_first_run": result.run.seconds,
            }
        )
        (directory / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
        results.append(metrics)
        print(
            f"{name}: XYZ error (mm) {[round(x * 1000, 4) for x in metrics['difference_xyz_m']]}, "
            f"strict pass={metrics['passes_strict_xyz_comparison']}, "
            f"repeat={metrics['repeat_pos_bit_identical']}",
            flush=True,
        )
    version = engine.version()
    summary = {
        "dataset_id": reference["dataset_id"],
        "geocomp_commit": subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
        ).strip(),
        "geocomp_worktree_status": subprocess.check_output(
            ["git", "-C", str(ROOT), "status", "--porcelain"], text=True
        ),
        "expected_rtklib_commit": reference["rtklib_commit"],
        "build_declared_rtklib_commit": os.environ.get("RTKLIB_COMMIT"),
        "engine_version": version.raw,
        "engine_binary_sha256": sha256(executable),
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "hatanaka": hatanaka.__version__,
        "cases": results,
        "accuracy_case": reference["accuracy_case"],
        "counter_case": reference["counter_case"],
        "accuracy_criterion_met": all(
            accuracy_case(results, reference)[key]
            for key in ("passes_strict_xyz_comparison", "full_day_and_fixed", "repeat_pos_bit_identical")
        ),
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
        "--sweep",
        action="store_true",
        help="Diagnostic: solve both days across a range of elevation masks and report "
        "the east/north/up error of each, instead of running the cases",
    )
    parser.add_argument(
        "--sweep-uncalibrated",
        action="store_true",
        help="Sweep without the antenna calibration. The only sweep available where the "
        "NGS ANTEX host is unreachable; the uncalibrated day-001 result sits 0.2 mm "
        "from the calibrated one, so it still attributes a millimetre-level error",
    )
    parser.add_argument(
        "--repeatability",
        action="store_true",
        help="Diagnostic: solve both days whole and from 12 h, 6 h and 1 h sub-sessions, "
        "reporting how far the answer moves. Sub-daily because GPS geometry repeats "
        "every sidereal day, so two whole days conceal exactly the error this exposes",
    )
    parser.add_argument(
        "--repeatability-uncalibrated",
        action="store_true",
        help="The repeatability measurement without the antenna calibration, for the "
        "environments where the NGS ANTEX host is unreachable",
    )
    parser.add_argument(
        "--mask",
        type=float,
        default=15.0,
        help="Elevation mask for --repeatability, in degrees. The default is the one "
        "GeoComp ships, so the scatter describes the configuration a user runs",
    )
    parser.add_argument(
        "--rover",
        choices=("GODE", "GODS"),
        help="Which rover the diagnostics solve against GODN. The defaults differ on "
        "purpose: --repeatability measures GODE, the baseline the criterion is judged "
        "on, and --sweep explains GODS, the counter-case it was written for",
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
            args.output,
            version.path,
            reference,
            calibrated=not args.sweep_uncalibrated,
            **({"rover": args.rover} if args.rover else {}),
        )
        return 0
    if args.repeatability or args.repeatability_uncalibrated:
        measure_repeatability(
            args.output,
            version.path,
            reference,
            calibrated=not args.repeatability_uncalibrated,
            mask=args.mask,
            **({"rover": args.rover} if args.rover else {}),
        )
        return 0
    summary = run_all(args.output, version.path, reference)
    try:
        require_accuracy(accuracy_case(summary["cases"], reference), reference)
    except AccuracyMismatchError as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
