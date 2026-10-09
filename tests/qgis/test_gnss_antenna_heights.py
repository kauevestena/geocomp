# SPDX-License-Identifier: GPL-2.0-or-later
"""Each station has one antenna height in *Build baselines* (P13-19).

Until P13-19 *Build baselines* reduced every baseline by one base height and
one rover height. In a network a station is the base of one baseline and the
rover of another, so unless the two heights were equal its mark was put in two
places, and every loop through it missed by the difference -- which reads as a
measurement error (specs/11 section 4.2).

The solutions are the GNSS tutorial's midnight triangle as the real engine
solved it (``tests/data/ggao/hour-00``), and the heights are the ones its RINEX
headers state: GODN's antenna reference point 0.0614 m above its mark, GODE's
and GODS's 0.0083 m. GODE is the rover of GODN-GODE and the base of GODE-GODS.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from tests.conftest import REPO_ROOT
from tests.qgis.walkthrough import label, refusal, run_logged

pytestmark = pytest.mark.qgis

ALGORITHM = "geocomp:gnss_build_baselines"
RECORDED = REPO_ROOT / "tests" / "data" / "ggao" / "hour-00"
LEGS = (("GODN", "GODE"), ("GODN", "GODS"), ("GODE", "GODS"))
#: ``ANTENNA: DELTA H/E/N`` in each station's header.
HEADER = {"GODN": 0.0614, "GODE": 0.0083, "GODS": 0.0083}
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


def _vectors(document: dict) -> dict[str, list[float]]:
    return {
        observation["id"].removeprefix("gnss-"): [value["value"] for value in observation["values"]]
        for observation in document["observations"]
    }


class TestEachStationItsOwnHeight:
    def test_the_marks_are_where_each_stations_height_puts_them(self, tmp_path):
        document, _log = _build(tmp_path, STATION_HEIGHTS=_rows(HEADER))
        assert document["antenna_heights"] == HEADER
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
        assert document["antenna_heights"] == HEADER

    def test_names_are_matched_in_upper_case_and_a_decimal_comma_is_read(self, tmp_path):
        document, _log = _build(tmp_path, STATION_HEIGHTS=["godn", "0,0614"])
        assert document["antenna_heights"]["GODN"] == HEADER["GODN"]


class TestOneHeightOrNone:
    def test_with_no_height_nothing_is_reduced(self, tmp_path):
        document, _log = _build(tmp_path)
        assert document["antenna_heights"] == {}
        vectors = _vectors(document)
        for baseline in _baselines():
            assert baseline.antenna_reduction is None
            np.testing.assert_allclose(
                vectors[baseline.id], [c.value for c in baseline.components], atol=1e-9
            )

    def test_once_any_height_is_given_every_baseline_is_reduced(self, tmp_path):
        """GODE-GODS by zero at both ends: a loop of reduced and unreduced legs cannot be closed."""
        document, log = _build(tmp_path, STATION_HEIGHTS=["GODN", "0.0614"])
        assert document["antenna_heights"] == {"GODN": 0.0614, "GODE": 0.0, "GODS": 0.0}
        assert len(document["closures"]) == 1
        assert "could not be closed" not in log


class TestTwoHeightsForOneStationAreRefused:
    def test_the_base_and_rover_heights_on_a_station_at_both_ends(self):
        said = refusal(
            ALGORITHM,
            {"FOLDER": str(RECORDED), "BASE_HEIGHT": HEADER["GODN"], "ROVER_HEIGHT": HEADER["GODE"]},
        )
        assert said.startswith(
            "GODE is the base of GODE-GODS and the rover of GODN-GODE, so it would be reduced by "
            "0.0614 m on one and 0.0083 m on the other"
        ), said
        assert f"Give its height in {label(ALGORITHM, 'STATION_HEIGHTS')}." in said

    def test_what_it_refuses_would_have_missed_by_the_difference(self):
        """The defect P13-19 removes: the loop the old reduction gave."""
        missed = _closure(_baselines({}, base=HEADER["GODN"], rover=HEADER["GODE"])).to_dict()
        closed = _closure(_baselines()).to_dict()
        difference = np.subtract(missed["misclosure_xyz_mm"], closed["misclosure_xyz_mm"])
        assert np.linalg.norm(difference) == pytest.approx((HEADER["GODN"] - HEADER["GODE"]) * 1000, abs=0.01)

    def test_equal_base_and_rover_heights_are_one_height(self, tmp_path):
        document, _log = _build(tmp_path, BASE_HEIGHT=1.5, ROVER_HEIGHT=1.5)
        assert document["antenna_heights"] == dict.fromkeys(HEADER, 1.5)


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
        assert document["antenna_heights"]["GODN"] == 1.0

    def test_a_station_no_baseline_has_is_said(self, tmp_path):
        """In the name it is matched by, which is how a reader finds the one typed wrong."""
        _document, log = _build(tmp_path, STATION_HEIGHTS=["godx", "1.2"])
        assert (
            "No baseline has GODX, so the height given for it in "
            f"{label(ALGORITHM, 'STATION_HEIGHTS')} was not used."
        ) in log
