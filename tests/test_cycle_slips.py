# SPDX-License-Identifier: GPL-2.0-or-later
"""Cycle slips and rejected observations, as the engine reports them (specs/11 section 5, P12c-36).

RTKLIB's sample baseline is clean -- no slip, no outlier in 120 epochs -- so the
evidence here is a fault put in where the answer is known: five and three
cycles on G20's two carriers from 00:30, and 500 m on G19's two pseudoranges at
00:45 (``tests/gnss_faults.py``). The engine is asked to find them, and GeoComp
to report what it found where it was put:

* the status file of that run, committed, read in tier 1
  (``tests/data/rtklib/stat/PROVENANCE.md``);
* the same run made live, through the engine wrapper, in tier 4;
* the reader's rules on lines written by hand, for the cases a real run of
  this data does not reach -- a flag on a signal not in use, a counter that
  stays, a counter the engine reset.
"""

from __future__ import annotations

import gzip
import shutil
from datetime import UTC, datetime
from pathlib import Path

import pytest

from geocomp.core.techniques.gnss.quality import EpochQuality, summarise
from geocomp.engines.rtklib.read_stat import read_status
from tests.conftest import requires_rtklib
from tests.gnss_faults import SLIP_AND_OUTLIER, with_faults

DATA = Path(__file__).resolve().parent / "data" / "rtklib"
STAT = DATA / "stat"

#: Where the faults were put: epochs 60 and 90 of the rover file, 30 s apart.
SLIPPED_AT = datetime(2005, 4, 2, 0, 30, tzinfo=UTC)
REJECTED_AT = datetime(2005, 4, 2, 0, 45, tzinfo=UTC)


def _sat(seconds: float, satellite: str, frequency: int, *, valid=1, slip=0, rejected=0) -> str:
    """A ``$SAT`` line in ``outsolstat``'s layout, with the fields read here set."""
    return (
        f"$SAT,1316,{seconds:.3f},{satellite},{frequency},120.0,40.0,0.1,0.0,{valid},45,1,"
        f"{slip},10,0,0,{rejected},0.00,0.000000,0.00000\n"
    )


def _pos(seconds: float) -> str:
    return f"$POS,1316,{seconds:.3f},1,1,2,3,0,0,0\n"


def _read(tmp_path: Path, text: str):
    path = tmp_path / "x.stat"
    path.write_text(text, encoding="ascii")
    return list(read_status(path).values())


@pytest.fixture(scope="module")
def status(tmp_path_factory):
    """The committed status file of the run with the faults in, read."""
    path = tmp_path_factory.mktemp("stat") / "slip-and-outlier.pos.stat"
    path.write_bytes(gzip.decompress((STAT / "slip-and-outlier.pos.stat.gz").read_bytes()))
    return read_status(path)


@pytest.fixture(scope="module")
def live_result(tmp_path_factory):
    """The faults put in now and the engine run through GeoComp's wrapper (tier 4)."""
    from geocomp.engines.rtklib import RtklibEngine, RtklibJob, profile
    from geocomp.io.gnss_discovery import scan_folder

    folder = tmp_path_factory.mktemp("faults")
    rover = (DATA / "07590920.05o").read_text(encoding="ascii")
    (folder / "07590920.05o").write_text(with_faults(rover, SLIP_AND_OUTLIER), encoding="ascii")
    shutil.copy(DATA / "30400920.05o", folder)
    shutil.copy(DATA / "brdc_0759.05n.gz", folder)
    sessions = {session.station_id: session for session in scan_folder(folder).sessions}
    return RtklibEngine().run(
        RtklibJob(rover=sessions["0759"], base=sessions["3040"], config=profile("relative-static")),
        work_dir=tmp_path_factory.mktemp("work"),
    )


class TestTheEngineFoundWhatWasPutThere:
    """The committed status file of the run with the faults in."""

    def test_the_slip_on_both_of_g20s_carriers_at_0030_and_nowhere_else(self, status):
        slips = {time: epoch.slips for time, epoch in status.items() if epoch.slips}
        assert slips == {SLIPPED_AT: ("G20/1", "G20/2")}

    def test_the_outlier_on_both_of_g19s_signals_at_0045_and_nowhere_else(self, status):
        rejections = {time: epoch.rejections for time, epoch in status.items() if epoch.rejections}
        assert rejections == {REJECTED_AT: ("G19/1", "G19/2")}

    def test_every_epoch_is_reported_on(self, status):
        assert len(status) == 120

    def test_the_rejected_satellite_drops_out_of_the_geometry_for_that_epoch(self, status):
        """Rejected, it was not used, so it is not in the DOP either."""
        used = {s.satellite for s in status[REJECTED_AT].sightings}
        assert "G19" not in used
        before = {s.satellite for s in status[datetime(2005, 4, 2, 0, 44, 30, tzinfo=UTC)].sightings}
        assert "G19" in before

    def test_the_clean_run_reports_none_of_either(self, tmp_path):
        path = tmp_path / "clean.stat"
        path.write_bytes(gzip.decompress((STAT / "relative-static.pos.stat.gz").read_bytes()))
        status = read_status(path)
        assert not any(epoch.slips or epoch.rejections for epoch in status.values())


class TestTheRulesOnLinesWrittenByHand:
    def test_a_slip_is_the_flags_first_bit_on_a_signal_in_use(self, tmp_path):
        (epoch,) = _read(
            tmp_path,
            _pos(0)
            + _sat(0, "G07", 1, slip=1)
            + _sat(0, "G08", 1, slip=3)  # a slip and a half-cycle ambiguity
            + _sat(0, "G11", 1, slip=2),  # a half-cycle ambiguity alone is not a slip
        )
        assert epoch.slips == ("G07/1", "G08/1")

    def test_a_flag_left_on_a_signal_not_in_use_is_not_a_slip(self, tmp_path):
        """RTKLIB clears the flags only for satellites both receivers observe:
        one the base has lost keeps its last flag, on lines flagged not valid."""
        epochs = _read(
            tmp_path,
            _pos(0) + _sat(0, "G07", 1, slip=1)
            + _pos(30) + _sat(30, "G07", 1, slip=1, valid=0)
            + _pos(60) + _sat(60, "G07", 1, slip=1, valid=0),
        )
        assert [epoch.slips for epoch in epochs] == [("G07/1",), (), ()]

    def test_a_rejection_is_the_counter_changing_to_something_other_than_zero(self, tmp_path):
        epochs = _read(
            tmp_path,
            _pos(0) + _sat(0, "G07", 1, rejected=0)
            + _pos(30) + _sat(30, "G07", 1, rejected=3, valid=0)  # three passes, one signal
            + _pos(60) + _sat(60, "G07", 1, rejected=0)  # reset by the engine: no rejection
            + _pos(90) + _sat(90, "G07", 1, rejected=1, valid=0)
            + _pos(120) + _sat(120, "G07", 1, rejected=1),  # unchanged: no new rejection
        )
        assert [epoch.rejections for epoch in epochs] == [(), ("G07/1",), (), ("G07/1",), ()]

    def test_each_signal_keeps_its_own_counter(self, tmp_path):
        epochs = _read(
            tmp_path,
            _pos(0) + _sat(0, "G07", 1, rejected=1) + _sat(0, "G07", 2, rejected=0)
            + _pos(30) + _sat(30, "G07", 1, rejected=1) + _sat(30, "G07", 2, rejected=1),
        )
        assert [epoch.rejections for epoch in epochs] == [("G07/1",), ("G07/2",)]

    def test_a_combined_solutions_backward_pass_does_not_count_again(self, tmp_path):
        epochs = _read(
            tmp_path,
            _pos(0) + _sat(0, "G07", 1, slip=1, rejected=1)
            + _pos(30) + _sat(30, "G07", 1)
            + _pos(30) + _sat(30, "G07", 1, slip=1, rejected=2)
            + _pos(0) + _sat(0, "G07", 1, slip=1, rejected=1),
        )
        assert [(epoch.slips, epoch.rejections) for epoch in epochs] == [
            (("G07/1",), ("G07/1",)),
            ((), ()),
        ]


class TestTheSessionSummary:
    @staticmethod
    def _epoch(seconds: int, slips=None, rejections=None) -> EpochQuality:
        return EpochQuality(
            time=datetime(2005, 4, 2, 0, 0, seconds, tzinfo=UTC),
            status="FIX",
            satellites=7,
            ratio=10.0,
            age=0.0,
            slips=slips,
            rejections=rejections,
        )

    def test_it_counts_signals_and_names_their_satellites(self):
        quality = summarise(
            "0759",
            [
                self._epoch(0, ("G20/1", "G20/2"), ()),
                self._epoch(30, ("G07/1",), ("G19/1", "G19/2")),
                self._epoch(59, (), ()),
            ],
        )
        assert (quality.cycle_slips, quality.rejections) == (3, 2)
        assert quality.satellites_slipped == ("G07", "G20")
        assert quality.satellites_rejected == ("G19",)
        summary = quality.to_dict()
        assert summary["cycle_slips"] == 3
        assert summary["satellites_rejected"] == ["G19"]

    def test_a_clean_session_reports_zero(self):
        quality = summarise("0759", [self._epoch(0, (), ()), self._epoch(30, (), ())])
        assert (quality.cycle_slips, quality.rejections) == (0, 0)

    def test_a_session_the_engine_said_nothing_about_reports_none_not_zero(self):
        quality = summarise("0759", [self._epoch(0), self._epoch(30)])
        assert (quality.cycle_slips, quality.rejections) == (None, None)
        assert quality.to_dict()["cycle_slips"] is None


@requires_rtklib
class TestALiveRunFindsThem:
    """Tier 4: the faults put in now, the engine run through GeoComp's wrapper."""
    def test_the_session_reports_one_slip_and_one_outlier_each_on_two_signals(self, live_result):
        from geocomp.engines.rtklib.baseline import quality_from_solution

        quality = quality_from_solution(live_result.solution, session_id="0759")
        assert (quality.cycle_slips, quality.satellites_slipped) == (2, ("G20",))
        assert (quality.rejections, quality.satellites_rejected) == (2, ("G19",))

    def test_the_trajectory_carries_them_at_their_epochs(self, live_result):
        from geocomp.engines.rtklib.trajectory import trajectory_from_solution

        points = {
            point.quality.time: point.quality
            for point in trajectory_from_solution(live_result.solution)
        }
        assert points[SLIPPED_AT].slips == ("G20/1", "G20/2")
        assert points[REJECTED_AT].rejections == ("G19/1", "G19/2")
        quiet = [q for time, q in points.items() if time not in (SLIPPED_AT, REJECTED_AT)]
        assert all(q.slips == () and q.rejections == () for q in quiet)
