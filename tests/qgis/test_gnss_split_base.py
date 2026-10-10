# SPDX-License-Identifier: GPL-2.0-or-later
"""A base logged in several files over one rover session is joined (P13-26).

Until P13-26 *Batch processing* refused such a rover session, telling the user
to join the base's files, and *Relative — Static* refused the pair as observed
together twice, listing one rover span twice. Both now join the files and
process one baseline.

RTKLIB's 2005 pair, its base cut in two at 00:30 as a receiver logging
half-hourly would have written it (``tests/test_gnss_join.py``). ``rnx2rtkp``
is tier 4; the stand-in answers every run, and what is checked is the base it
was handed. ``tests/test_rtklib_engine.py`` runs the real engine on the same
halves.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from tests.qgis.test_engine_runs import RINEX, rtklib  # noqa: F401 -- a fixture
from tests.qgis.test_gnss_sessions import _relative, _run
from tests.qgis.walkthrough import refusal
from tests.test_gnss_join import split

pytestmark = pytest.mark.qgis

JOINED = (
    "Base 3040 logged the session 2005-04-02 00:00/00:59 in 2 files, joined into one: "
    "3040092a.05o, 3040092b.05o."
)


@pytest.fixture(scope="module", autouse=True)
def _registered(geocomp_provider):
    return geocomp_provider


@pytest.fixture
def folder(tmp_path) -> Path:
    """The rover's hour, and the base's in two files."""
    folder = tmp_path / "rinex"
    folder.mkdir()
    shutil.copy(RINEX / "brdc_0759.05n.gz", folder)
    shutil.copy(RINEX / "07590920.05o", folder)
    split(RINEX / "30400920.05o", folder)
    return folder


def _set_up_again(folder: Path) -> None:
    """The second half's antenna 1.5 m up: the base set up again, not logged on."""
    second = folder / "3040092b.05o"
    text = second.read_text(encoding="ascii")
    old = "        0.0000        0.0000        0.0000                  ANTENNA: DELTA H/E/N"
    second.write_text(text.replace(old, old.replace("        0.0000", "        1.5000", 1)), encoding="ascii")


def _whole(job) -> None:
    """The job's base is both halves joined: the hour the rover observed."""
    assert Path(job.base.obs_file).name == "3040-200504020000-joined.05o"
    assert f"{job.base.start:%H:%M}/{job.base.end:%H:%M:%S}" == "00:00/00:59:29"
    assert job.base.meta["joined_from"] == ["3040092a.05o", "3040092b.05o"]


class TestRelativeStatic:
    def test_the_base_is_joined_and_one_baseline_processed(self, rtklib, folder, tmp_path):  # noqa: F811
        engine = rtklib()
        _results, feedback = _run("geocomp:gnss_relative_static", _relative(folder, tmp_path))
        (job,) = engine.jobs
        _whole(job)
        assert job.rover.station_id == "0759"
        assert JOINED in feedback.infos

    def test_a_base_set_up_again_is_refused_and_named(self, rtklib, folder, tmp_path):  # noqa: F811
        engine = rtklib()
        _set_up_again(folder)
        said = refusal("geocomp:gnss_relative_static", _relative(folder, tmp_path))
        assert "'3040092a.05o' and '3040092b.05o' cannot be joined into one session" in said
        assert "ANTENNA: DELTA H/E/N" in said
        assert engine.jobs == []


class TestABatch:
    def _batch(self, folder: Path, tmp_path: Path):
        report = tmp_path / "batch.json"
        _results, feedback = _run(
            "geocomp:gnss_batch",
            {"FOLDER": str(folder), "BASE_STATION": "3040", "OUTPUT_JSON": str(report)},
        )
        return json.loads(report.read_text(encoding="utf-8")), feedback

    def test_the_session_runs_against_the_joined_base(self, rtklib, folder, tmp_path):  # noqa: F811
        engine = rtklib()
        document, feedback = self._batch(folder, tmp_path)
        assert document["summary"]["succeeded"] == 1
        (job,) = engine.jobs
        _whole(job)
        assert JOINED in feedback.infos

    def test_two_rovers_share_one_join(self, rtklib, folder, tmp_path):  # noqa: F811
        """A second receiver over the same hour: one join, said once, both rows against it."""
        engine = rtklib()
        text = (RINEX / "07590920.05o").read_text(encoding="ascii")
        (folder / "11110920.05o").write_text(
            text.replace(f"{'0759':<60}MARKER NAME", f"{'1111':<60}MARKER NAME"), encoding="ascii"
        )
        document, feedback = self._batch(folder, tmp_path)
        assert document["summary"]["succeeded"] == 2
        assert {job.base.obs_file for job in engine.jobs} == {engine.jobs[0].base.obs_file}
        assert sum("joined into one" in line for line in feedback.infos) == 1

    def test_a_base_set_up_again_fails_its_row_and_says_why(self, rtklib, folder, tmp_path):  # noqa: F811
        engine = rtklib()
        _set_up_again(folder)
        document, feedback = self._batch(folder, tmp_path)
        (row,) = document["results"]
        assert row["outcome"] == "failed"
        assert row["code"] == "data.gnss_join_setups_differ"
        assert any("cannot be joined into one session" in warning for warning in feedback.warnings)
        assert engine.jobs == []
