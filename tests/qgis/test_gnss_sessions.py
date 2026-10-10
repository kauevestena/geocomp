# SPDX-License-Identifier: GPL-2.0-or-later
"""A station observed more than once is never guessed between (P13-16).

Until P13-16 the GNSS algorithms kept one session per station, the last the
scan listed, and dropped the others without a word. *Relative — Static* then
processed whichever pair that left, observed together or not; *Batch
processing* keyed every row by station, so a mark observed on two days was
processed twice as the second day and the first was lost. The GNSS tutorial's
walkthrough found it, with two hours of one triangle in one folder.

The folders here are RTKLIB's 2005 pair, with copies moved to the next day:
the same observations, a day later, which is all a second session needs to be.
``rnx2rtkp`` is tier 4; the stand-in answers every run, and what is checked is
which sessions the algorithm handed it.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from tests.qgis.test_engine_runs import RINEX, _feedback, rtklib  # noqa: F401 -- a fixture
from tests.qgis.walkthrough import refusal

pytestmark = pytest.mark.qgis

DAY_ONE = "2005-04-02 00:00/00:59"
DAY_TWO = "2005-04-03 00:00/00:59"


@pytest.fixture(scope="module", autouse=True)
def _registered(geocomp_provider):
    return geocomp_provider


def _next_day(source: Path, folder: Path, *, station: str | None = None, later: bool = True) -> Path:
    """*source* observed a day *later*, and as *station* when one is given."""
    text = source.read_text(encoding="ascii")
    name = source.name
    if later:
        text = text.replace("  2005     4     2", "  2005     4     3")
        text = text.replace("\n 05  4  2 ", "\n 05  4  3 ")
        name = name.replace("0920", "0930")
    if station:
        old = source.name[:4]
        text = text.replace(f"{old:<60}MARKER NAME", f"{station:<60}MARKER NAME")
        name = station + name[4:]
    target = folder / name
    target.write_text(text, encoding="ascii")
    return target


def _folder(tmp_path: Path, *, base: tuple[int, ...], rover: tuple[int, ...]) -> Path:
    """The 2005 pair, base 3040 and rover 0759, on the days named (1 or 2)."""
    folder = tmp_path / "rinex"
    folder.mkdir()
    shutil.copy(RINEX / "brdc_0759.05n.gz", folder)
    for station, days in (("3040", base), ("0759", rover)):
        source = RINEX / f"{station}0920.05o"
        if 1 in days:
            shutil.copy(source, folder)
        if 2 in days:
            _next_day(source, folder)
    return folder


def _relative(folder: Path, out: Path, **extra) -> dict:
    return {
        "FOLDER": str(folder),
        "BASE_STATION": "3040",
        "ROVER_STATION": "0759",
        "OUTPUT_POS": str(out / "solution.pos"),
        "OUTPUT_JSON": str(out / "summary.json"),
        **extra,
    }


def _run(algorithm_id: str, parameters: dict):
    from qgis.core import QgsApplication, QgsProcessingContext

    feedback = _feedback()
    results, ok = QgsApplication.processingRegistry().algorithmById(algorithm_id).create({}).run(
        parameters, QgsProcessingContext(), feedback, catchExceptions=False
    )
    assert ok
    return results, feedback


class TestOneBaseline:
    def test_two_sessions_observed_together_twice_are_refused_and_named(self, rtklib, tmp_path):  # noqa: F811
        engine = rtklib()
        said = refusal(
            "geocomp:gnss_relative_static",
            _relative(_folder(tmp_path, base=(1, 2), rover=(1, 2)), tmp_path),
        )
        assert "observed together 2 times" in said
        assert DAY_ONE in said and DAY_TWO in said
        assert engine.jobs == []

    def test_the_one_pair_that_observed_together_is_the_one_processed_and_said(self, rtklib, tmp_path):  # noqa: F811
        """The rover is there on both days and the base on the second: the
        second day is the baseline. Before, the last session of each station
        was taken, which here happened to be right and in general is not."""
        engine = rtklib()
        _results, feedback = _run(
            "geocomp:gnss_relative_static",
            _relative(_folder(tmp_path, base=(2,), rover=(1, 2)), tmp_path),
        )
        (job,) = engine.jobs
        assert job.base.start == job.rover.start
        assert f"{job.rover.start:%Y-%m-%d %H:%M}" in DAY_TWO
        assert any(DAY_TWO in info and "once" in info for info in feedback.infos)

    def test_the_first_day_is_found_when_it_is_the_one(self, rtklib, tmp_path):  # noqa: F811
        """The case the old dict got wrong: the last session of the rover is
        the day the base did not observe."""
        engine = rtklib()
        _run(
            "geocomp:gnss_relative_static",
            _relative(_folder(tmp_path, base=(1,), rover=(1, 2)), tmp_path),
        )
        (job,) = engine.jobs
        assert f"{job.rover.start:%Y-%m-%d %H:%M}" in DAY_ONE
        assert job.base.start == job.rover.start

    def test_a_base_never_observed_with_the_rover_is_refused(self, rtklib, tmp_path):  # noqa: F811
        """The base observed on the first day, with another receiver; the
        rover on the second, with a third. Each has a partner, and they were
        never partners of each other."""
        engine = rtklib()
        folder = _folder(tmp_path, base=(1,), rover=(2,))
        _next_day(RINEX / "07590920.05o", folder, station="2222", later=False)
        _next_day(RINEX / "30400920.05o", folder, station="1111")
        said = refusal("geocomp:gnss_relative_static", _relative(folder, tmp_path))
        assert "never observed at the same time" in said
        assert engine.jobs == []

    def test_a_station_with_two_sessions_is_refused_by_absolute_processing(self, rtklib, tmp_path):  # noqa: F811
        engine = rtklib()
        said = refusal(
            "geocomp:gnss_absolute_static",
            {
                "FOLDER": str(_folder(tmp_path, base=(), rover=(1, 2))),
                "ROVER_STATION": "0759",
                "OUTPUT_POS": str(tmp_path / "solution.pos"),
                "OUTPUT_JSON": str(tmp_path / "summary.json"),
            },
        )
        assert "has 2 sessions" in said and DAY_ONE in said and DAY_TWO in said
        assert engine.jobs == []


#: Where the 2005 sample's base is said to move, for a database that knows it.
#: The pair's own header position; the velocity is large enough to see in a day.
BASE_XYZ = (-3978242.4348, 3382841.1715, 3649902.7667)
BASE_VELOCITY = (-0.030, 0.020, 0.010)


@pytest.fixture
def base_in_the_database(tmp_path):
    """3040 in a reference-station database, at 2005.0 and moving, for the length of a test."""
    from geocomp.core.models.epoch import Epoch
    from geocomp.core.techniques.gnss.stations import ReferenceStation, StationDatabase
    from geocomp.core.uncertainty import Quantity
    from geocomp.core.units import Unit
    from geocomp.services.settings_service import settings

    stations = StationDatabase()
    stations.add(
        ReferenceStation(
            id="3040",
            position=tuple(Quantity.from_std_dev(v, 0.002, Unit.METRE) for v in BASE_XYZ),
            frame="ITRF2020",
            epoch=Epoch(decimal_year=2005.0),
            velocity_per_year=BASE_VELOCITY,
            source="a test's own",
        )
    )
    path = tmp_path / "stations.json"
    stations.write(path)
    settings.set_global("gnss.reference_station_database", str(path))
    yield
    settings.reset_global("gnss.reference_station_database")


class TestABatch:
    def _batch(self, folder: Path, tmp_path: Path, **extra):
        report = tmp_path / "batch.json"
        _results, feedback = _run(
            "geocomp:gnss_batch",
            {"FOLDER": str(folder), "BASE_STATION": "3040", "OUTPUT_JSON": str(report), **extra},
        )
        return json.loads(report.read_text(encoding="utf-8")), feedback

    def test_each_session_holds_the_base_at_its_own_epoch(self, rtklib, tmp_path, base_in_the_database):  # noqa: F811
        """P13-23: each day's base where its velocity has carried it by that day.

        Until P13-23 every row held the base where the first session put it.
        """
        import numpy as np

        engine = rtklib()
        # 1: the base's own frame, so only its epoch moves it.
        document, _feedback = self._batch(_folder(tmp_path, base=(1, 2), rover=(1, 2)), tmp_path, FRAME=1)
        jobs = sorted(engine.jobs, key=lambda job: job.base.start)
        assert [job.config.base_position_type for job in jobs] == ["xyz", "xyz"]
        records = sorted((row["base_coordinates"] for row in document["sessions"]), key=lambda r: r["epoch"])
        assert [record["session"] for record in records] == [DAY_ONE, DAY_TWO]
        years = records[1]["epoch"] - records[0]["epoch"]
        assert years == pytest.approx(1 / 365, rel=1e-6)
        moved = np.subtract(jobs[1].config.base_position, jobs[0].config.base_position)
        np.testing.assert_allclose(moved, np.multiply(BASE_VELOCITY, years), atol=1e-9)
        for job, record in zip(jobs, records, strict=True):
            assert list(job.config.base_position) == pytest.approx(record["xyz"], abs=1e-9)

    def test_a_base_held_at_its_header_is_said_once(self, rtklib, tmp_path):  # noqa: F811
        """Not in the database: the header holds it whatever the day, and the log says so once."""
        engine = rtklib()
        document, feedback = self._batch(_folder(tmp_path, base=(1, 2), rover=(1, 2)), tmp_path)
        said = [line for line in feedback.infos if "is not in the reference-station database" in line]
        assert len(said) == 1
        assert {job.config.base_position_type for job in engine.jobs} == {"rinexhead"}
        records = [row["base_coordinates"] for row in document["sessions"]]
        assert sorted(record["session"] for record in records) == [DAY_ONE, DAY_TWO]
        assert {record["source"] for record in records} == {"RINEX header"}

    def test_every_session_is_a_row_against_the_base_it_observed_with(self, rtklib, tmp_path):  # noqa: F811
        engine = rtklib()
        document, _feedback = self._batch(_folder(tmp_path, base=(1, 2), rover=(1, 2)), tmp_path)
        assert [row["key"] for row in document["results"]] == [f"0759 {DAY_ONE}", f"0759 {DAY_TWO}"]
        assert document["summary"]["succeeded"] == 2
        assert sorted(job.rover.start for job in engine.jobs) == sorted(
            job.base.start for job in engine.jobs
        )
        assert len({job.rover.start for job in engine.jobs}) == 2

    def test_a_session_the_base_did_not_observe_with_fails_and_says_why(self, rtklib, tmp_path):  # noqa: F811
        engine = rtklib()
        document, feedback = self._batch(_folder(tmp_path, base=(1,), rover=(1, 2)), tmp_path)
        rows = {row["key"]: row for row in document["results"]}
        assert rows[f"0759 {DAY_ONE}"]["outcome"] == "succeeded"
        assert rows[f"0759 {DAY_TWO}"]["outcome"] == "failed"
        assert rows[f"0759 {DAY_TWO}"]["code"] == "computation.gnss_batch_no_base_session"
        assert any("did not observe at the same time" in warning for warning in feedback.warnings)
        (job,) = engine.jobs
        assert job.base.start == job.rover.start

    def test_one_session_per_station_keeps_the_station_as_its_key(self, rtklib, tmp_path):  # noqa: F811
        """A campaign of one session per mark reads as it did before."""
        rtklib()
        document, _feedback = self._batch(_folder(tmp_path, base=(1,), rover=(1,)), tmp_path)
        assert [row["key"] for row in document["results"]] == ["0759"]
