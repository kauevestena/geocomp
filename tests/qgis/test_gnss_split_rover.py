# SPDX-License-Identifier: GPL-2.0-or-later
"""A rover logged in several files is one session (P13-29).

A receiver logging hourly leaves a morning's occupation in several files.
Until P13-29 each was a session of its own: *Relative — Static* refused the pair
as observed together twice, the absolute modes refused the station as having
two sessions, and *Batch processing* made a row of each hour. Files that follow
one another and were recorded one way are now one session.

RTKLIB's 2005 pair, its rover cut in two at 00:30 (``tests/test_gnss_join.py``).
``rnx2rtkp`` is tier 4; the stand-in answers every run, and what is checked is
the rover it was handed.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from tests.qgis.test_engine_runs import RINEX, rtklib  # noqa: F401 -- a fixture
from tests.qgis.test_gnss_sessions import DAY_ONE, DAY_TWO, _next_day, _relative, _run
from tests.test_gnss_join import split

pytestmark = pytest.mark.qgis

JOINED = (
    "0759 logged 2005-04-02 00:00/00:59 in 2 files, one after another, joined into one session: "
    "0759092a.05o, 0759092b.05o."
)


@pytest.fixture(scope="module", autouse=True)
def _registered(geocomp_provider):
    return geocomp_provider


@pytest.fixture
def folder(tmp_path) -> Path:
    """The base's hour, and the rover's in two files."""
    folder = tmp_path / "rinex"
    folder.mkdir()
    shutil.copy(RINEX / "brdc_0759.05n.gz", folder)
    shutil.copy(RINEX / "30400920.05o", folder)
    split(RINEX / "07590920.05o", folder)
    return folder


def _whole(job) -> None:
    assert Path(job.rover.obs_file).name == "0759-200504020000-joined.05o"
    assert f"{job.rover.start:%H:%M}/{job.rover.end:%H:%M}" == "00:00/00:59"


class TestOneSession:
    def test_relative_static_processes_the_hour_once(self, rtklib, folder, tmp_path):  # noqa: F811
        """Before: refused, the pair observed together twice."""
        engine = rtklib()
        _results, feedback = _run("geocomp:gnss_relative_static", _relative(folder, tmp_path))
        (job,) = engine.jobs
        _whole(job)
        assert job.base.station_id == "3040"
        assert JOINED in feedback.infos

    def test_absolute_static_processes_the_hour_once(self, rtklib, folder, tmp_path):  # noqa: F811
        """Before: refused, the station having two sessions."""
        engine = rtklib()
        _run(
            "geocomp:gnss_absolute_static",
            {
                "FOLDER": str(folder),
                "ROVER_STATION": "0759",
                "OUTPUT_POS": str(tmp_path / "solution.pos"),
                "OUTPUT_JSON": str(tmp_path / "summary.json"),
            },
        )
        (job,) = engine.jobs
        _whole(job)

    def test_a_batch_makes_one_row_of_it(self, rtklib, folder, tmp_path):  # noqa: F811
        """Before: a row an hour, keyed by span."""
        engine = rtklib()
        report = tmp_path / "batch.json"
        _results, feedback = _run(
            "geocomp:gnss_batch",
            {"FOLDER": str(folder), "BASE_STATION": "3040", "OUTPUT_JSON": str(report)},
        )
        document = json.loads(report.read_text(encoding="utf-8"))
        assert [row["key"] for row in document["results"]] == ["0759"]
        (job,) = engine.jobs
        _whole(job)
        assert JOINED in feedback.infos

    def test_another_day_is_still_another_row(self, rtklib, folder, tmp_path):  # noqa: F811
        engine = rtklib()
        _next_day(RINEX / "30400920.05o", folder)
        _next_day(RINEX / "07590920.05o", folder)
        report = tmp_path / "batch.json"
        _run(
            "geocomp:gnss_batch",
            {"FOLDER": str(folder), "BASE_STATION": "3040", "OUTPUT_JSON": str(report)},
        )
        document = json.loads(report.read_text(encoding="utf-8"))
        assert [row["key"] for row in document["results"]] == [f"0759 {DAY_ONE}", f"0759 {DAY_TWO}"]
        first, second = sorted(engine.jobs, key=lambda job: job.rover.start)
        _whole(first)
        assert Path(second.rover.obs_file).name == "07590930.05o"
