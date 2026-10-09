# SPDX-License-Identifier: GPL-2.0-or-later
"""The GNSS tutorial's data, and the numbers its README states (P13-17).

``geocomp/resources/datasets/ggao-triangle`` is two hours of NOAA's files for
GODN, GODE and GODS on 2025-001, each observation file cut to the hour and
reduced to GPS and eight observables, every value unchanged
(``scripts/make_ggao_triangle.py``). What is held here:

* what ships, and that its notice travels with it;
* that the navigation file is NOAA's, by the digest RD-06's manifest pins, and
  that the observation files are what the script makes from NOAA's, wherever
  the sources have been fetched (engine CI fetches them);
* that each hour is one session per station, all three together;
* that the recorded solutions ``tests/data/ggao`` holds close the two loops by
  what the README says, here, without QGIS or the engine;
* and, at tier 4, that the engine gives those solutions from the shipped files.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

from geocomp.resources import DATASETS_DIR
from tests.conftest import REPO_ROOT, requires_rtklib

DATASET = DATASETS_DIR / "ggao-triangle"
RECORDED = REPO_ROOT / "tests" / "data" / "ggao"
SOURCES = REPO_ROOT / "tests" / "data" / "rd06" / "sources"
HOURS = {"hour-00": 0, "hour-11": 11}
LEGS = (("GODN", "GODE"), ("GODN", "GODS"), ("GODE", "GODS"))
TOP = ("NOTICE.md", "README.es.md", "README.md", "README.pt_BR.md")
IN_EACH_HOUR = ("brdc0010.25n.gz", "gode0010.25o", "godn0010.25o", "gods0010.25o")


def _readme() -> str:
    return " ".join((DATASET / "README.md").read_text(encoding="utf-8").split())


def _recorded(hour: str, base: str, rover: str):
    from geocomp.engines.rtklib.read_pos import read_pos

    return read_pos(RECORDED / hour / f"{base}-{rover}.pos".lower())


def _closure(solutions: dict):
    from geocomp.core.techniques.gnss import closing_loops, independent_subset, loop_closure
    from geocomp.engines.rtklib.baseline import baseline_from_solution

    built = [
        baseline_from_solution(solution, base_station=base, rover_station=rover)
        for (base, rover), solution in solutions.items()
    ]
    independent, dependent = independent_subset(built)
    ((loop, legs),) = closing_loops(independent, dependent)
    return loop_closure(legs, loop)


def _over(closure) -> str:
    return f"over {closure.perimeter_m:.1f} m of baselines ({closure.parts_per_million:.2f} ppm)"


class TestWhatShips:
    def test_the_top_folder_and_each_hour_hold_what_they_should(self):
        assert sorted(path.name for path in DATASET.iterdir() if path.is_file()) == list(TOP)
        assert sorted(path.name for path in DATASET.iterdir() if path.is_dir()) == sorted(HOURS)
        for hour in HOURS:
            assert sorted(path.name for path in (DATASET / hour).iterdir()) == list(IN_EACH_HOUR)

    def test_the_build_ships_both_hours(self):
        spec = importlib.util.spec_from_file_location("geocomp_build", REPO_ROOT / "scripts" / "build.py")
        build = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(build)
        shipped = {
            path.relative_to(DATASET).as_posix() for path in build.collect_files() if DATASET in path.parents
        }
        assert shipped == {*TOP, *(f"{hour}/{name}" for hour in HOURS for name in IN_EACH_HOUR)}

    def test_the_notice_attributes_the_data_and_says_what_was_changed(self):
        notice = " ".join((DATASET / "NOTICE.md").read_text(encoding="utf-8").split())
        for words in ("National Geodetic Survey", "NASA Goddard", "registry.opendata.aws/noaa-ncn",
                      "cut to one hour", "reduced to GPS", "scripts/make_ggao_triangle.py"):
            assert words in notice, words
        assert "| `geocomp/resources/datasets/ggao-triangle/` |" in (REPO_ROOT / "THIRD_PARTY.md").read_text(
            encoding="utf-8"
        )

    def test_the_navigation_file_is_noaas_by_the_pinned_digest(self):
        manifest = json.loads((REPO_ROOT / "tests" / "data" / "rd06" / "source_manifest.json").read_text())
        pinned = next(entry["sha256"] for entry in manifest if entry["url"].endswith("/brdc0010.25n.gz"))
        for hour in HOURS:
            assert hashlib.sha256((DATASET / hour / "brdc0010.25n.gz").read_bytes()).hexdigest() == pinned

    @pytest.mark.parametrize("hour", sorted(HOURS))
    @pytest.mark.parametrize("station", ("godn", "gode", "gods"))
    def test_each_file_says_how_it_was_made(self, hour, station):
        header = (DATASET / hour / f"{station}0010.25o").read_text(encoding="ascii").split("END OF HEADER")[0]
        start = HOURS[hour]
        assert f"Cut to {start:05.2f}-{start + 1:05.2f} h GPST from {station}0010.25o" in header
        assert "GPS only, observables C1 P1 L1 S1 C2 P2 L2 S2 kept" in header


class TestEachHourIsOneSessionPerStation:
    @pytest.mark.parametrize("hour", sorted(HOURS))
    def test_three_stations_observing_together_for_the_hour(self, hour):
        from geocomp.io.gnss_discovery import overlapping_groups, scan_folder

        scan = scan_folder(DATASET / hour)
        assert not scan.skipped
        assert sorted(session.station_id for session in scan.sessions) == ["GODE", "GODN", "GODS"]
        (group,) = overlapping_groups(scan.sessions)
        assert len(group) == 3
        for session in scan.sessions:
            assert (session.start.hour, session.start.minute) == (HOURS[hour], 0)
            assert (session.end.hour, session.end.minute, session.end.second) == (HOURS[hour], 59, 30)


class TestTheNumbersTheReadmeStates:
    """From the recorded solutions, through the same core *Build baselines* uses."""

    def test_midnight_closes_to_what_it_says(self):
        closure = _closure({leg: _recorded("hour-00", *leg) for leg in LEGS})
        assert f"**The triangle closes to {closure.magnitude_m * 1000:.2f} mm.**" in _readme()
        assert _over(closure) in _readme()

    def test_eleven_misses_by_what_it_says(self):
        closure = _closure({leg: _recorded("hour-11", *leg) for leg in LEGS})
        assert f"**The triangle misses by {closure.magnitude_m * 1000:.2f} mm**" in _readme()
        assert _over(closure) in _readme()

    def test_the_recorded_solutions_are_of_the_shipped_files(self):
        for hour in HOURS:
            for base, rover in LEGS:
                solution = _recorded(hour, base, rover)
                assert [Path(name).name for name in solution.inputs] == [
                    f"{rover.lower()}0010.25o",
                    f"{base.lower()}0010.25o",
                    "brdc0010.25n.gz",
                ]


class TestRebuiltFromNoaasFiles:
    """Wherever ``scripts/check_rd06.py --fetch-inputs`` has run, as engine CI does."""

    def test_the_observation_files_are_what_the_script_makes(self):
        if importlib.util.find_spec("hatanaka") is None or not (SOURCES / "godn0010.25d.gz").is_file():
            pytest.skip("needs RD-06's sources (scripts/check_rd06.py --fetch-inputs) and hatanaka")
        script = REPO_ROOT / "scripts" / "make_ggao_triangle.py"
        spec = importlib.util.spec_from_file_location("make_ggao", script)
        make = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(make)
        for relative, data in make.build(SOURCES).items():
            assert (DATASET / relative).read_bytes() == data, relative


@requires_rtklib
class TestTheTutorialAgainstTheRealEngine:
    """Tier 4: the engine, on the shipped files, gives the recorded solutions."""

    @pytest.mark.parametrize("hour", sorted(HOURS))
    def test_each_side_is_the_recorded_solution(self, hour, tmp_path):
        from geocomp.engines.rtklib import RtklibEngine, RtklibJob
        from geocomp.engines.rtklib.config import profile
        from geocomp.io.gnss_discovery import scan_folder

        sessions = {session.station_id: session for session in scan_folder(DATASET / hour).sessions}
        solved = {}
        for base, rover in LEGS:
            result = RtklibEngine().run(
                RtklibJob(rover=sessions[rover], base=sessions[base], config=profile("relative-static")),
                work_dir=tmp_path / f"{base}-{rover}",
            )
            recorded = _recorded(hour, base, rover)
            assert [e.is_ambiguity_fixed for e in result.solution.epochs] == [
                e.is_ambiguity_fixed for e in recorded.epochs
            ]
            np.testing.assert_allclose(result.solution.last().position, recorded.last().position, atol=1e-4)
            solved[base, rover] = result.solution
        assert _closure(solved).magnitude_m == pytest.approx(
            _closure({leg: _recorded(hour, *leg) for leg in LEGS}).magnitude_m, abs=1e-5
        )
