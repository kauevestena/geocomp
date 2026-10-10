# SPDX-License-Identifier: GPL-2.0-or-later
"""Each station has one antenna height in *Build baselines* (P13-19).

Until P13-19 *Build baselines* reduced every baseline by one base height and
one rover height. In a network a station is the base of one baseline and the
rover of another, so unless the two heights were equal its mark was put in two
places, and every loop through it missed by the difference -- which reads as a
measurement error (specs/11 section 4.2).

The solutions are the GNSS tutorial's midnight triangle as the real engine
solved it (``tests/data/ggao/hour-00``), and the heights are the ones its RINEX
headers state: GODE's antenna reference point 0.0614 m above its mark, GODN's
and GODS's 0.0083 m. GODE is the rover of GODN-GODE and the base of GODE-GODS.
(P13-19 had GODN's and GODE's the other way round; P13-20, reading the files,
found it.)
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from geocomp.resources import DATASETS_DIR
from tests.conftest import REPO_ROOT
from tests.qgis.walkthrough import label, refusal, run_logged

pytestmark = pytest.mark.qgis

ALGORITHM = "geocomp:gnss_build_baselines"
RECORDED = REPO_ROOT / "tests" / "data" / "ggao" / "hour-00"
#: The observation files those solutions were solved from.
OBSERVED = DATASETS_DIR / "ggao-triangle" / "hour-00"
LEGS = (("GODN", "GODE"), ("GODN", "GODS"), ("GODE", "GODS"))
#: ``ANTENNA: DELTA H/E/N`` in each station's header.
HEADER = {"GODN": 0.0083, "GODE": 0.0614, "GODS": 0.0083}
SIGMA = 0.002


@pytest.fixture(scope="module", autouse=True)
def _registered(geocomp_provider):
    return geocomp_provider


def _build(tmp_path: Path, **extra) -> tuple[dict, str]:
    results, log = run_logged(
        ALGORITHM,
        {
            "FOLDER": str(RECORDED),
            "INDEPENDENT_ONLY": False,  # all three, so each is compared
            "OUTPUT_JSON": str(tmp_path / "baselines.json"),
            **extra,
        },
    )
    return json.loads(Path(results["OUTPUT_JSON"]).read_text(encoding="utf-8")), log


def _rows(heights: dict[str, object]) -> list[str]:
    return [str(cell) for station, height in heights.items() for cell in (station, height)]


def _baselines(heights: dict[str, float] | None = None, *, base: float = 0.0, rover: float = 0.0):
    """The three baselines through the core, each end reduced by *heights* or by its role's."""
    from geocomp.core.techniques.gnss import AntennaOffset, reduce_to_marks
    from geocomp.core.uncertainty import Quantity
    from geocomp.core.units import Unit
    from geocomp.engines.rtklib.baseline import baseline_from_solution
    from geocomp.engines.rtklib.read_pos import read_pos

    def offset(height: float) -> AntennaOffset:
        return AntennaOffset(up=Quantity.from_std_dev(height, SIGMA, Unit.METRE), method="vertical")

    built = []
    for start, end in LEGS:
        baseline = baseline_from_solution(
            read_pos(RECORDED / f"{start}-{end}.pos".lower()), base_station=start, rover_station=end
        )
        if heights is not None:
            baseline = reduce_to_marks(
                baseline, offset(heights.get(start, base)), offset(heights.get(end, rover))
            )
        built.append(baseline)
    return built


def _closure(built):
    from geocomp.core.techniques.gnss import closing_loops, independent_subset, loop_closure

    ((loop, legs),) = closing_loops(*independent_subset(built))
    return loop_closure(legs, loop)


def _by_station(document: dict) -> dict[str, float]:
    """The heights applied, by station, each station's the same on every baseline it is an end of."""
    heights: dict[str, float] = {}
    for ends in document["antenna_heights"].values():
        for station, height in ends.items():
            assert heights.setdefault(station, height) == height, (station, document["antenna_heights"])
    return heights


def _round_the_triangle(built) -> np.ndarray:
    """GODN -> GODE -> GODS -> GODN, in metres, always that way round.

    Not through ``closing_loops``: which baseline it closes with is the
    independent subset's choice, by covariance trace, and the reduced and the
    unreduced sets need not choose alike -- so two sets can be closed in
    opposite directions, and their misclosures not subtracted. (Until P13-21 a
    tie could also go either way on another platform, and on Windows it did.)
    """
    vectors = {b.id: np.array([c.value for c in b.components]) for b in built}
    return vectors["GODN-GODE"] + vectors["GODE-GODS"] - vectors["GODN-GODS"]


def _vectors(document: dict) -> dict[str, list[float]]:
    return {
        observation["id"].removeprefix("gnss-"): [value["value"] for value in observation["values"]]
        for observation in document["observations"]
    }


class TestEachStationItsOwnHeight:
    def test_the_marks_are_where_each_stations_height_puts_them(self, tmp_path):
        document, _log = _build(tmp_path, STATION_HEIGHTS=_rows(HEADER))
        assert _by_station(document) == HEADER
        vectors = _vectors(document)
        for baseline in _baselines(HEADER):
            np.testing.assert_allclose(
                vectors[baseline.id], [c.value for c in baseline.components], atol=1e-9
            )

    def test_the_loop_closes_as_it_did_between_the_antennas(self, tmp_path):
        """One height a station puts its mark in one place, so the loop is unchanged."""
        document, _log = _build(tmp_path, STATION_HEIGHTS=_rows(HEADER))
        (record,) = document["closures"]
        assert record["magnitude_mm"] == pytest.approx(_closure(_baselines()).magnitude_m * 1000, abs=1e-3)

    def test_a_station_not_listed_takes_its_ends_height(self, tmp_path):
        """GODN is only ever the base and GODS only ever the rover; GODE, both, is listed."""
        document, _log = _build(
            tmp_path, BASE_HEIGHT=HEADER["GODN"], ROVER_HEIGHT=HEADER["GODS"],
            STATION_HEIGHTS=_rows({"GODE": HEADER["GODE"]}),
        )
        assert _by_station(document) == HEADER

    def test_names_are_matched_in_upper_case_and_a_decimal_comma_is_read(self, tmp_path):
        document, _log = _build(tmp_path, STATION_HEIGHTS=["godn", "0,0083"])
        assert _by_station(document)["GODN"] == HEADER["GODN"]


class TestOneHeightOrNone:
    def test_with_no_height_nothing_is_reduced(self, tmp_path):
        document, _log = _build(tmp_path)
        assert _by_station(document) == {}
        vectors = _vectors(document)
        for baseline in _baselines():
            assert baseline.antenna_reduction is None
            np.testing.assert_allclose(
                vectors[baseline.id], [c.value for c in baseline.components], atol=1e-9
            )

    def test_once_any_height_is_given_every_baseline_is_reduced(self, tmp_path):
        """GODE-GODS by zero at both ends: a loop of reduced and unreduced legs cannot be closed."""
        document, log = _build(tmp_path, STATION_HEIGHTS=["GODN", "0.0614"])
        assert _by_station(document) == {"GODN": 0.0614, "GODE": 0.0, "GODS": 0.0}
        assert len(document["closures"]) == 1
        assert "could not be closed" not in log


class TestTwoHeightsForOneStationAreRefused:
    def test_the_base_and_rover_heights_on_a_station_at_both_ends(self):
        said = refusal(
            ALGORITHM,
            {"FOLDER": str(RECORDED), "BASE_HEIGHT": HEADER["GODE"], "ROVER_HEIGHT": HEADER["GODS"]},
        )
        assert said.startswith(
            "GODE is the base of GODE-GODS and the rover of GODN-GODE, so it would be reduced by "
            "0.0614 m on one and 0.0083 m on the other"
        ), said
        assert f"Give its height in {label(ALGORITHM, 'STATION_HEIGHTS')}." in said

    def test_what_it_refuses_would_have_missed_by_the_difference(self):
        """The defect P13-19 removes: the loop the old reduction gave."""
        missed = _round_the_triangle(_baselines({}, base=HEADER["GODE"], rover=HEADER["GODS"]))
        closed = _round_the_triangle(_baselines())
        assert np.linalg.norm(missed - closed) == pytest.approx(HEADER["GODE"] - HEADER["GODS"], abs=1e-6)

    def test_equal_base_and_rover_heights_are_one_height(self, tmp_path):
        document, _log = _build(tmp_path, BASE_HEIGHT=1.5, ROVER_HEIGHT=1.5)
        assert _by_station(document) == dict.fromkeys(HEADER, 1.5)


class TestTheTable:
    @pytest.mark.parametrize(
        "rows",
        (["GODN", "abc"], ["", "1.5"], ["GODN", ""], ["GODN", "11"], ["GODN", "-1"]),
        ids=("not-a-number", "no-station", "no-height", "too-high", "negative"),
    )
    def test_a_row_that_is_not_a_station_and_a_height_is_refused(self, rows):
        said = refusal(ALGORITHM, {"FOLDER": str(RECORDED), "STATION_HEIGHTS": rows})
        assert said.startswith(f"{label(ALGORITHM, 'STATION_HEIGHTS')}: The row "), said
        assert "is not a station and an antenna height from 0 to 10 m. Correct it, or clear the row." in said

    def test_two_heights_for_one_station_are_refused(self):
        said = refusal(
            ALGORITHM, {"FOLDER": str(RECORDED), "STATION_HEIGHTS": ["GODN", "1", "godn", "2"]}
        )
        assert said.endswith("GODN is given two heights, 1 m and 2 m. Give it one."), said

    def test_the_same_height_twice_and_an_empty_row_are_fine(self, tmp_path):
        document, _log = _build(tmp_path, STATION_HEIGHTS=["GODN", "1", "", "", "GODN", "1.0"])
        assert _by_station(document)["GODN"] == 1.0

    def test_a_station_no_baseline_has_is_said(self, tmp_path):
        """In the name it is matched by, which is how a reader finds the one typed wrong."""
        _document, log = _build(tmp_path, STATION_HEIGHTS=["godx", "1.2"])
        assert (
            "No baseline has GODX, so the height given for it in "
            f"{label(ALGORITHM, 'STATION_HEIGHTS')} was not used."
        ) in log


def _solved_beside_their_files(folder: Path) -> Path:
    """The recorded solutions with the observation files they name, in one folder.

    The recorded solutions name their inputs by file name alone, so a file is
    found beside the solution -- the case of folders moved together.
    """
    folder.mkdir(parents=True, exist_ok=True)
    for source in (*RECORDED.glob("*.pos"), *OBSERVED.glob("*.25o")):
        (folder / source.name).write_bytes(source.read_bytes())
    return folder


def _restate(observation: Path, east: float = 0.0, north: float = 0.0, *, height: float | None = None,
             drop: bool = False) -> None:
    """Rewrite *observation*'s ``ANTENNA: DELTA H/E/N``, or drop it."""
    lines = []
    for line in observation.read_text(encoding="ascii").splitlines(keepends=True):
        if line[60:80].rstrip() == "ANTENNA: DELTA H/E/N":
            if drop:
                continue
            up = float(line[:14]) if height is None else height
            line = f"{up:14.4f}{east:14.4f}{north:14.4f}{'':18}ANTENNA: DELTA H/E/N\n"
        lines.append(line)
    observation.write_text("".join(lines), encoding="ascii")


def _from_files(folder: Path, tmp_path: Path, **extra) -> tuple[dict, str]:
    results, log = run_logged(
        ALGORITHM,
        {
            "FOLDER": str(folder),
            "INDEPENDENT_ONLY": False,
            "HEIGHTS_FROM_FILES": True,
            "OUTPUT_JSON": str(tmp_path / f"{folder.name}.json"),
            **extra,
        },
    )
    return json.loads(Path(results["OUTPUT_JSON"]).read_text(encoding="utf-8")), log


class TestFromTheObservationFiles:
    """P13-20: each end's height as its session's observation file states it."""

    def test_each_end_is_reduced_by_its_files_height(self, tmp_path):
        document, _log = _from_files(_solved_beside_their_files(tmp_path / "in"), tmp_path)
        assert document["antenna_heights_from_files"] is True
        assert document["antenna_heights"] == {
            "GODE-GODS": {"GODE": 0.0614, "GODS": 0.0083},
            "GODN-GODE": {"GODN": 0.0083, "GODE": 0.0614},
            "GODN-GODS": {"GODN": 0.0083, "GODS": 0.0083},
        }
        vectors = _vectors(document)
        for baseline in _baselines(HEADER):
            np.testing.assert_allclose(
                vectors[baseline.id], [c.value for c in baseline.components], atol=1e-9
            )

    def test_it_says_what_a_rinex_height_is_and_is_not(self, tmp_path):
        _document, log = _from_files(_solved_beside_their_files(tmp_path / "in"), tmp_path)
        assert (
            "Each height read from an observation file is taken as the vertical height of the "
            "antenna reference point above the mark"
        ) in log
        assert "check the heights against the field book." in log

    def test_a_listed_station_is_given_its_listed_height(self, tmp_path):
        document, _log = _from_files(
            _solved_beside_their_files(tmp_path / "in"), tmp_path, STATION_HEIGHTS=["GODN", "1.5"]
        )
        assert _by_station(document) == {**HEADER, "GODN": 1.5}

    def test_each_session_is_its_own_file(self, tmp_path):
        """As two setups would be: GODE-GODS names another GODE file, at another height."""
        folder = _solved_beside_their_files(tmp_path / "in")
        other = folder / "gode0011.25o"
        other.write_bytes((folder / "gode0010.25o").read_bytes())
        _restate(other, height=0.5)
        solution = folder / "gode-gods.pos"
        solution.write_text(
            solution.read_text(encoding="ascii").replace("gode0010.25o", "gode0011.25o"), encoding="ascii"
        )
        document, _log = _from_files(folder, tmp_path)
        assert document["antenna_heights"]["GODE-GODS"]["GODE"] == 0.5
        assert document["antenna_heights"]["GODN-GODE"]["GODE"] == 0.0614

    def test_an_eccentric_antenna_is_said_and_reduced(self, tmp_path):
        folder = _solved_beside_their_files(tmp_path / "in")
        _restate(folder / "gods0010.25o", east=0.0100, north=-0.0200)
        centred, _log = _from_files(_solved_beside_their_files(tmp_path / "centred"), tmp_path)
        off, log = _from_files(folder, tmp_path)
        assert "GODS's antenna stood 0.01 m east and -0.02 m north of its mark, as gods0010.25o states" in log
        moved = np.subtract(_vectors(off)["GODN-GODS"], _vectors(centred)["GODN-GODS"])
        assert np.linalg.norm(moved) == pytest.approx(np.hypot(0.01, 0.02), abs=1e-9)

    def test_a_file_that_is_not_there_is_refused(self, tmp_path):
        folder = _solved_beside_their_files(tmp_path / "in")
        (folder / "gods0010.25o").unlink()
        said = refusal(ALGORITHM, {"FOLDER": str(folder), "HEIGHTS_FROM_FILES": True})
        assert said.startswith(
            "The solution names gods0010.25o as the observation file of GODS, and it is not there "
            "or beside the solution."
        ), said
        assert f"give GODS's height in {label(ALGORITHM, 'STATION_HEIGHTS')}." in said

    def test_a_file_that_states_no_height_is_refused(self, tmp_path):
        folder = _solved_beside_their_files(tmp_path / "in")
        _restate(folder / "godn0010.25o", drop=True)
        said = refusal(ALGORITHM, {"FOLDER": str(folder), "HEIGHTS_FROM_FILES": True})
        assert said == (
            "godn0010.25o states no antenna height. "
            f"Give GODN's height in {label(ALGORITHM, 'STATION_HEIGHTS')}."
        ), said

    def test_a_listed_station_needs_no_file(self, tmp_path):
        folder = _solved_beside_their_files(tmp_path / "in")
        (folder / "gods0010.25o").unlink()
        document, _log = _from_files(folder, tmp_path, STATION_HEIGHTS=["GODS", "0.0083"])
        assert _by_station(document) == HEADER

    def test_the_base_and_rover_heights_are_not_used_and_it_says_so(self, tmp_path):
        """Every end is a file's or a listed height, so they cannot give a station two."""
        document, log = _from_files(
            _solved_beside_their_files(tmp_path / "in"), tmp_path, BASE_HEIGHT=1.0, ROVER_HEIGHT=2.0
        )
        assert _by_station(document) == HEADER
        assert (
            f"{label(ALGORITHM, 'BASE_HEIGHT')} and {label(ALGORITHM, 'ROVER_HEIGHT')} are not used"
        ) in log

    def test_a_relative_name_is_looked_for_only_beside_the_solution(self, tmp_path, monkeypatch):
        """Not in whatever folder QGIS was started in, where another file of that name may be."""
        folder = _solved_beside_their_files(tmp_path / "in")
        elsewhere = tmp_path / "elsewhere"
        elsewhere.mkdir()
        (elsewhere / "gods0010.25o").write_bytes((folder / "gods0010.25o").read_bytes())
        _restate(elsewhere / "gods0010.25o", height=9.0)
        monkeypatch.chdir(elsewhere)
        document, _log = _from_files(folder, tmp_path)
        assert _by_station(document)["GODS"] == HEADER["GODS"]
