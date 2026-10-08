# SPDX-License-Identifier: GPL-2.0-or-later
"""Dilution of precision from the satellite geometry RTKLIB reports (FR-603, P12c-35).

Three kinds of evidence, each independent of GeoComp's own arithmetic:

* every epoch of a real run against **RTKLIB's own ``dops()``**, applied to the
  same status file (``tests/data/rtklib/stat/PROVENANCE.md``);
* a geometry whose DOP is worked by hand below;
* the cases where there is no DOP to give.
"""

from __future__ import annotations

import csv
import gzip
import math
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from geocomp.core.errors import DataError
from geocomp.core.techniques.gnss.quality import (
    DilutionOfPrecision,
    EpochQuality,
    dilution_of_precision,
    summarise,
)
from geocomp.engines.rtklib.read_stat import read_satellite_geometry, to_millisecond

STAT = Path(__file__).resolve().parent / "data" / "rtklib" / "stat"
GPS_EPOCH = datetime(1980, 1, 6, tzinfo=UTC)


@pytest.fixture(scope="module")
def status_file(tmp_path_factory) -> Path:
    path = tmp_path_factory.mktemp("stat") / "relative-static.pos.stat"
    path.write_bytes(gzip.decompress((STAT / "relative-static.pos.stat.gz").read_bytes()))
    return path


@pytest.fixture(scope="module")
def rtklib_dops() -> dict[datetime, dict[str, float]]:
    with (STAT / "relative-static.dops.csv").open(encoding="ascii") as handle:
        return {
            to_millisecond(GPS_EPOCH + timedelta(weeks=int(row["week"]), seconds=float(row["tow"]))): {
                key: float(value) for key, value in row.items() if key not in {"week", "tow"}
            }
            for row in csv.DictReader(handle)
        }


class TestAgainstRtklibsOwnDops:
    def test_every_epoch_is_read(self, status_file, rtklib_dops):
        geometry = read_satellite_geometry(status_file)
        assert set(geometry) == set(rtklib_dops)
        assert len(geometry) == 120

    def test_each_epoch_counts_the_satellites_rtklib_counts(self, status_file, rtklib_dops):
        geometry = read_satellite_geometry(status_file)
        for time, expected in rtklib_dops.items():
            assert len(geometry[time]) == expected["satellites"], time

    def test_each_epochs_dop_is_rtklibs(self, status_file, rtklib_dops):
        """RTKLIB prints six decimals; the comparison allows the last one."""
        geometry = read_satellite_geometry(status_file)
        for time, expected in rtklib_dops.items():
            dop = dilution_of_precision([(s.azimuth, s.elevation) for s in geometry[time]])
            assert dop is not None, time
            assert dop.geometric == pytest.approx(expected["gdop"], abs=1e-6), time
            assert dop.position == pytest.approx(expected["pdop"], abs=1e-6), time
            assert dop.horizontal == pytest.approx(expected["hdop"], abs=1e-6), time
            assert dop.vertical == pytest.approx(expected["vdop"], abs=1e-6), time

    def test_the_session_reports_the_median_and_the_worst_epoch(self, status_file, rtklib_dops):
        geometry = read_satellite_geometry(status_file)
        epochs = [
            EpochQuality(
                time=time,
                status="FIX",
                satellites=len(sightings),
                ratio=3.0,
                age=0.0,
                dop=dilution_of_precision([(s.azimuth, s.elevation) for s in sightings]),
            )
            for time, sightings in sorted(geometry.items())
        ]
        quality = summarise("0759", epochs)
        pdops = sorted(row["pdop"] for row in rtklib_dops.values())
        middle = len(pdops) // 2
        assert quality.dilution_of_precision.position == pytest.approx(
            (pdops[middle - 1] + pdops[middle]) / 2, abs=1e-6
        )
        assert quality.dilution_of_precision_worst.position == pytest.approx(max(pdops), abs=1e-6)
        record = quality.to_dict()
        assert set(record["dilution_of_precision"]) == {"gdop", "pdop", "hdop", "vdop"}
        assert record["dilution_of_precision_worst"]["pdop"] == pytest.approx(max(pdops), abs=1e-6)


class TestAGeometryWorkedByHand:
    """A satellite at the zenith and four at 30 degrees, at azimuths 0, 90, 180 and 270.

    With c = cos 30 and s = sin 30 the normal matrix separates: east and north
    each get 2c^2 = 3/2, and up and the clock form [[4s^2 + 1, 4s + 1], [4s + 1, 5]]
    = [[2, 3], [3, 5]], whose inverse is [[5, -3], [-3, 2]] (its determinant is 1).
    So the cofactors are 2/3, 2/3, 5 and 2: HDOP = sqrt(4/3), VDOP = sqrt(5),
    PDOP = sqrt(19/3), GDOP = sqrt(25/3).
    """

    SKY = [(0.0, math.pi / 2)] + [(math.radians(a), math.radians(30.0)) for a in (0, 90, 180, 270)]

    def test_the_four_values(self):
        dop = dilution_of_precision(self.SKY)
        assert dop.horizontal == pytest.approx(math.sqrt(4 / 3), rel=1e-12)
        assert dop.vertical == pytest.approx(math.sqrt(5), rel=1e-12)
        assert dop.position == pytest.approx(math.sqrt(19 / 3), rel=1e-12)
        assert dop.geometric == pytest.approx(math.sqrt(25 / 3), rel=1e-12)

    def test_turning_the_whole_sky_changes_nothing(self):
        turned = [(azimuth + 0.7, elevation) for azimuth, elevation in self.SKY]
        assert dilution_of_precision(turned) == pytest.approx(dilution_of_precision(self.SKY))


class TestWhereThereIsNoDop:
    def test_three_satellites_give_none(self):
        assert dilution_of_precision([(0.0, 1.0), (2.0, 0.5), (4.0, 0.6)]) is None

    def test_a_satellite_at_or_below_the_horizon_does_not_count(self):
        sky = [(0.0, math.pi / 2), (0.0, 0.5), (2.0, 0.5), (4.0, 0.0)]
        assert dilution_of_precision(sky) is None

    def test_the_mask_is_applied(self):
        sky = TestAGeometryWorkedByHand.SKY
        assert dilution_of_precision(sky, elevation_mask=math.radians(29)) is not None
        assert dilution_of_precision(sky, elevation_mask=math.radians(31)) is None

    def test_a_geometry_with_no_inverse_gives_none(self):
        """Four satellites at one point of the sky cannot separate the unknowns."""
        assert dilution_of_precision([(1.0, 0.8)] * 4) is None

    def test_a_session_with_no_geometry_reports_none(self):
        epoch = EpochQuality(time=GPS_EPOCH, status="FIX", satellites=7, ratio=3.0, age=0.0)
        quality = summarise("x", [epoch])
        assert quality.dilution_of_precision is None
        assert quality.dilution_of_precision_worst is None
        assert quality.to_dict()["dilution_of_precision"] is None

    def test_the_value_names_the_four(self):
        dop = DilutionOfPrecision(geometric=3.0, position=2.0, horizontal=1.0, vertical=1.5)
        assert dop.to_dict() == {"gdop": 3.0, "pdop": 2.0, "hdop": 1.0, "vdop": 1.5}


class TestReadingTheStatusFile:
    def test_only_the_first_frequency_of_valid_satellites_counts(self, tmp_path):
        path = tmp_path / "x.stat"
        path.write_text(
            "$POS,1316,518400.000,2,1,2,3,0,0,0\n"
            "$SAT,1316,518400.000,G07,1,298.1,16.2,1.2,0.0,1,0,0,0,0,0,0,0,0,0,0\n"
            "$SAT,1316,518400.000,G07,2,298.1,16.2,1.2,0.0,1,0,0,0,0,0,0,0,0,0,0\n"
            "$SAT,1316,518400.000,G08,1,242.9,20.1,1.2,0.0,0,0,0,0,0,0,0,0,0,0,0\n",
            encoding="ascii",
        )
        geometry = read_satellite_geometry(path)
        (sightings,) = geometry.values()
        assert [s.satellite for s in sightings] == ["G07"]
        assert sightings[0].azimuth == pytest.approx(math.radians(298.1))
        assert sightings[0].elevation == pytest.approx(math.radians(16.2))

    def test_an_epoch_with_no_valid_satellite_is_kept_empty(self, tmp_path):
        path = tmp_path / "x.stat"
        path.write_text(
            "$SAT,1316,518400.000,G08,1,242.9,20.1,1.2,0.0,0,0,0,0,0,0,0,0,0,0,0\n", encoding="ascii"
        )
        assert list(read_satellite_geometry(path).values()) == [()]

    def test_a_combined_solutions_backward_pass_is_not_read_again(self, tmp_path):
        """Forward blocks in time order, then backward ones in reverse -- the
        first of which is for the epoch the forward pass ended on."""

        def block(seconds: int, satellites: tuple[str, ...]) -> str:
            return f"$POS,1316,{seconds}.000,1,1,2,3,0,0,0\n" + "".join(
                f"$SAT,1316,{seconds}.000,{satellite},1,{10.0 * n},40.0,0.1,0.0,1,0,0,0,0,0,0,0,0,0,0\n"
                for n, satellite in enumerate(satellites)
            )

        forward, backward = ("G07", "G08"), ("G07", "G08", "G11")
        path = tmp_path / "x.stat"
        path.write_text(
            block(518400, forward) + block(518430, forward)
            + block(518430, backward) + block(518400, backward),
            encoding="ascii",
        )
        geometry = read_satellite_geometry(path)
        assert [[s.satellite for s in sightings] for sightings in geometry.values()] == [
            ["G07", "G08"],
            ["G07", "G08"],
        ]

    @pytest.mark.parametrize(
        "line",
        [
            "$SAT,1316,518400.000,G07,1,298.1\n",
            "$SAT,1316,noon,G07,1,298.1,16.2,1.2,0.0,1\n",
            "$POS,1316,noon,2,1,2,3,0,0,0\n",
        ],
    )
    def test_a_line_that_cannot_be_read_is_refused_naming_it(self, tmp_path, line):
        path = tmp_path / "x.stat"
        path.write_text("$POS,1316,518400.000,2,1,2,3,0,0,0\n" + line, encoding="ascii")
        with pytest.raises(DataError) as caught:
            read_satellite_geometry(path)
        assert caught.value.code == "data.rtklib_status_malformed"
        assert caught.value.context["line"] == 2

    def test_times_agree_with_the_solution_to_the_millisecond(self):
        early = datetime(2005, 4, 2, 0, 0, 29, 999_999, tzinfo=UTC)
        assert to_millisecond(early) == datetime(2005, 4, 2, 0, 0, 30, tzinfo=UTC)
        assert to_millisecond(datetime(2005, 4, 2, 0, 0, 30, 400, tzinfo=UTC)).microsecond == 0


class TestItReachesTheTrajectoryAndTheSummary:
    """The engine bridge: a solution that carries its run's geometry gives each
    trajectory point, and the session summary, RTKLIB's DOP."""

    @pytest.fixture
    def solution(self, status_file):
        from geocomp.engines.rtklib.read_pos import read_pos

        solution = read_pos(Path(__file__).resolve().parent / "data" / "rtklib" / "pos" / "xyz.pos")
        solution.geometry = read_satellite_geometry(status_file)
        return solution

    def test_each_point_carries_its_epochs_dop(self, solution, rtklib_dops):
        from geocomp.engines.rtklib.trajectory import trajectory_from_solution

        points = trajectory_from_solution(solution)
        assert len(points) == 120
        for point in points:
            expected = rtklib_dops[to_millisecond(point.quality.time)]
            assert point.quality.dop.position == pytest.approx(expected["pdop"], abs=1e-6)
            assert point.quality.dop.vertical == pytest.approx(expected["vdop"], abs=1e-6)

    def test_the_session_summary_carries_the_worst_epoch(self, solution, rtklib_dops):
        from geocomp.engines.rtklib.baseline import quality_from_solution

        quality = quality_from_solution(solution, session_id="0759")
        worst = max(row["pdop"] for row in rtklib_dops.values())
        assert quality.dilution_of_precision_worst.position == pytest.approx(worst, abs=1e-6)

    def test_a_calendar_time_solution_finds_the_same_epochs(self, status_file, rtklib_dops):
        """``-t`` writes dates instead of GPS weeks; the epochs must still meet."""
        from geocomp.engines.rtklib.read_pos import read_pos

        solution = read_pos(
            Path(__file__).resolve().parent / "data" / "rtklib" / "pos" / "llh-calendar.pos"
        )
        solution.geometry = read_satellite_geometry(status_file)
        assert all(solution.dop_at(epoch.time) is not None for epoch in solution.epochs)
