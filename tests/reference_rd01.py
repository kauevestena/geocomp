# SPDX-License-Identifier: GPL-2.0-or-later
"""RD-01: the project author's own total-station triangle.

``specs/20-testing-and-validation.md`` section 3. Unlike RD-02 and RD-03, this
one is **real field data** -- three stations, three setups, face pairs, recorded
in ``topo_test/raw_data.csv`` -- and its expected output
``topo_test/processed_data.csv`` was produced by the prototype notebook that
seeded this module.

**It carries two known defects, and both are the point.**

1. A **1.000 m face-pair distance discrepancy** on the ``2,3,1`` backsight,
   where every other pair in the file agrees to the millimetre. Almost certainly
   a transcription error in the raw data. The prototype averages the two faces
   to 23.861 m and that value propagates into the expected output.

2. A **180 degree error** in one reduced direction, caused by the prototype's
   arithmetic-mean face reduction. ``specs/09`` section 2.1 previously claimed
   that reduction was "correct for the RD-01 data"; implementing the circular
   form and comparing showed it is not.

This module holds the data and the expected values so both the reference test
and any later tutorial material read from one place.
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path

from geocomp.core.instruments import InstrumentProfile, ProfileLibrary
from geocomp.core.techniques.total_station import Face, FacePair, FaceReading, Setup
from geocomp.core.uncertainty import Quantity
from geocomp.core.units import Unit

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW = REPO_ROOT / "topo_test" / "raw_data.csv"
PROCESSED = REPO_ROOT / "topo_test" / "processed_data.csv"

#: The setup and target where the prototype's face reduction is 180 degrees out.
#: Keyed by (backsight, occupied, foresight, which-was-sighted), matching the
#: raw file's own grouping.
WRONG_DIRECTION_KEY = ("3", "1", "2", "V")

#: What the prototype published there, and what the circular reduction gives.
PUBLISHED_WRONG_DEGREES = 19.110138888888883
CORRECT_DEGREES = 199.11013888888888

#: The face pair whose two distances differ by a metre.
BLUNDER_KEY = ("2", "3", "1", "R")
BLUNDER_SIZE = 1.000

#: Nominal precisions for the reduction. RD-01 records no instrument, so these
#: are a plausible modern total station; they affect the *uncertainties* the
#: pipeline attaches and not one of the values it must reproduce, which is
#: exactly the separation the reproduction test relies on.
SIGMA_ANGLE = 5.0e-6
SIGMA_DISTANCE = 0.002
SIGMA_HEIGHT = 0.001


@dataclass(frozen=True)
class Rd01Record:
    """One reduced pointing as the prototype published it."""

    key: tuple[str, str, str, str]
    horizontal_degrees: float
    zenith_degrees: float
    horizontal_distance: float
    vertical_component: float
    height_difference: float
    instrument_height: float
    target_height: float
    slope_distance: float


def _decimal_degrees(row: dict[str, str], prefix: str) -> float:
    return (
        float(row[prefix + "G"])
        + float(row[prefix + "M"]) / 60.0
        + float(row[prefix + "S"]) / 3600.0
    )


def raw_groups() -> dict[tuple[str, str, str, str], dict[str, dict[str, str]]]:
    """The raw file, grouped into face pairs the way the prototype grouped it."""
    groups: dict[tuple[str, str, str, str], dict[str, dict[str, str]]] = {}
    with open(RAW, encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            key = (row["R"], row["E"], row["V"], row["vis"])
            groups.setdefault(key, {})[row["pos"]] = row
    return groups


def published() -> dict[tuple[str, str, str, str], Rd01Record]:
    """``processed_data.csv``, keyed the same way."""
    records: dict[tuple[str, str, str, str], Rd01Record] = {}
    raw = raw_groups()
    with open(PROCESSED, encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            key = (row["R"], row["E"], row["V"], row["vis"])
            records[key] = Rd01Record(
                key=key,
                horizontal_degrees=float(row["H_corr"]) % 360.0,
                zenith_degrees=float(row["V_corr"]),
                horizontal_distance=float(row["DH"]),
                vertical_component=float(row["DV"]),
                height_difference=float(row["dH"]),
                instrument_height=float(row["hi"]),
                target_height=float(row["hs"]),
                slope_distance=float(row["D"]),
            )
            assert key in raw, f"{key} is in the processed file but not the raw one"
    return records


def face_pair(key: tuple[str, str, str, str]) -> FacePair:
    """Build a :class:`FacePair` from the raw file, with nominal precisions."""
    faces = raw_groups()[key]
    target = key[0] if key[3] == "R" else key[2]

    def reading(row: dict[str, str], face: Face) -> FaceReading:
        return FaceReading(
            target=target,
            face=face,
            horizontal=Quantity.from_std_dev(
                math.radians(_decimal_degrees(row, "H")), SIGMA_ANGLE, Unit.RADIAN
            ),
            zenith=Quantity.from_std_dev(
                math.radians(_decimal_degrees(row, "V")), SIGMA_ANGLE, Unit.RADIAN
            ),
            distance=Quantity.from_std_dev(float(row["D"]), SIGMA_DISTANCE, Unit.METRE),
            target_height=Quantity.from_std_dev(float(row["hs"]), SIGMA_HEIGHT, Unit.METRE),
        )

    return FacePair(reading(faces["PD"], Face.DIRECT), reading(faces["PI"], Face.REVERSE))


def setups() -> dict[str, Setup]:
    """The three instrument stations, each with its two face pairs."""
    by_station: dict[str, Setup] = {}
    for key in raw_groups():
        _backsight, occupied, _foresight, _which = key
        if occupied not in by_station:
            row = next(iter(raw_groups()[key].values()))
            by_station[occupied] = Setup(
                station=occupied,
                instrument_height=Quantity.from_std_dev(
                    float(row["hi"]), SIGMA_HEIGHT, Unit.METRE
                ),
                instrument_id="rd01",
            )
        by_station[occupied].pairs.append(face_pair(key))
    return by_station


def library() -> ProfileLibrary:
    """A profile library matching the nominal precisions used above."""
    profiles = ProfileLibrary()
    profiles.add_instrument(
        InstrumentProfile(
            id="rd01",
            name="RD-01 nominal total station",
            sigma_direction=SIGMA_ANGLE,
            sigma_zenith=SIGMA_ANGLE,
            sigma_instrument_height=SIGMA_HEIGHT,
            sigma_target_height=SIGMA_HEIGHT,
        )
    )
    return profiles


def triangle_sides() -> dict[frozenset[str], float]:
    """Horizontal distances between the three stations, as published.

    Each side was measured twice, once from each end; this takes the mean of
    the two, except for the side carrying the 1.000 m blunder, where the
    single clean measurement is used.
    """
    records = published()
    sides: dict[frozenset[str], list[float]] = {}
    for key, record in records.items():
        backsight, occupied, foresight, which = key
        other = backsight if which == "R" else foresight
        if key == BLUNDER_KEY:
            continue
        sides.setdefault(frozenset({occupied, other}), []).append(record.horizontal_distance)
    return {pair: sum(values) / len(values) for pair, values in sides.items()}
