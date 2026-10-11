# SPDX-License-Identifier: GPL-2.0-or-later
"""A base logged in several files is joined into one (P13-26).

A receiver that logs a file an hour leaves a rover session overlapped by
several of the base's, and ``rnx2rtkp`` reads one base file. Until P13-26
*Batch processing* refused such a rover session, telling the user to join the
files, and *Relative — Static* refused the pair as observed together twice.
:func:`~geocomp.io.gnss_discovery.join_sessions` joins them.

The files are RTKLIB's 2005 base, 3040, cut in two at 00:30: the first half
and the second, each with its own header, as a receiver logging half-hourly
files would have written them.
"""

from __future__ import annotations

import gzip
import re
import shutil
from pathlib import Path

import pytest

from geocomp.core.errors import DataError
from geocomp.io.gnss_discovery import join_sessions, scan_folder
from geocomp.io.rinex import read_rinex_header
from tests.conftest import requires_rtklib

DATA = Path(__file__).parent / "data" / "rtklib"
BASE = DATA / "30400920.05o"
#: An epoch record of RINEX 2: two-digit year, month, day, hour, minute, seconds.
EPOCH = re.compile(r"^ \d\d [ \d]\d [ \d]\d [ \d]\d [ \d]\d [ \d]\d\.\d{7}  \d")
FIRST_OBS = "  2005     4     2     0     0    0.0000000     GPS         TIME OF FIRST OBS"


def _parts(source: Path) -> tuple[list[str], list[str]]:
    lines = source.read_text(encoding="ascii").splitlines()
    end = next(i for i, line in enumerate(lines) if line[60:].strip() == "END OF HEADER")
    return lines[: end + 1], lines[end + 1 :]


def split(source: Path, folder: Path, *, at: str = " 05  4  2  0 30") -> tuple[Path, Path]:
    """*source* cut in two at the epoch *at*, as ``ssss092a.05o`` and ``ssss092b.05o``."""
    header, body = _parts(source)
    cut = next(i for i, line in enumerate(body) if EPOCH.match(line) and line.startswith(at))
    station = source.name[:4]
    first, second = folder / f"{station}092a.05o", folder / f"{station}092b.05o"
    first.write_text("\n".join([*header, *body[:cut]]) + "\n", encoding="ascii")
    later = [
        line.replace(FIRST_OBS, FIRST_OBS.replace("0     0    0.0", "0    30    0.0")) for line in header
    ]
    second.write_text("\n".join([*later, *body[cut:]]) + "\n", encoding="ascii")
    return first, second


@pytest.fixture
def halves(tmp_path) -> Path:
    folder = tmp_path / "halves"
    folder.mkdir()
    split(BASE, folder)
    shutil.copy(DATA / "brdc_0759.05n.gz", folder)
    return folder


def _sessions(folder: Path):
    return sorted(scan_folder(folder).sessions, key=lambda session: session.start)


class TestJoined:
    def test_the_halves_are_two_sessions_until_joined(self, halves):
        first, second = _sessions(halves)
        assert f"{first.start:%H:%M}" == "00:00" and f"{second.start:%H:%M}" == "00:30"

    def test_it_is_the_whole_file_again(self, halves, tmp_path):
        joined = join_sessions(_sessions(halves), tmp_path / "joined")
        header, body = _parts(Path(joined.obs_file))
        original_header, original_body = _parts(BASE)
        assert body == original_body
        # The original's header, and a comment that says what was done.
        assert [line for line in header if "GEOCOMP" not in line] == original_header
        assert "GEOCOMP: JOINED FROM 2 FILES" in header[-2]

    def test_its_session_spans_both(self, halves, tmp_path):
        first, second = _sessions(halves)
        joined = join_sessions([second, first], tmp_path / "joined")
        assert (joined.start, joined.end) == (first.start, second.end)
        assert joined.station_id == "3040"
        assert joined.meta["joined_from"] == ["3040092a.05o", "3040092b.05o"]
        assert joined.nav_files == first.nav_files
        assert Path(joined.obs_file).name == joined.id == "3040-200504020000-joined.05o"

    def test_it_reads_back_as_one_session(self, halves, tmp_path):
        joined = join_sessions(_sessions(halves), tmp_path / "joined")
        header = read_rinex_header(joined.obs_file)
        assert header.marker_name == "3040"
        assert f"{header.first_observation:%H:%M}" == "00:00"

    def test_a_gzipped_file_is_read(self, halves, tmp_path):
        second = halves / "3040092b.05o"
        with gzip.open(halves / "3040092b.05o.gz", "wt", encoding="ascii") as handle:
            handle.write(second.read_text(encoding="ascii"))
        second.unlink()
        joined = join_sessions(_sessions(halves), tmp_path / "joined")
        assert _parts(Path(joined.obs_file))[1] == _parts(BASE)[1]
        assert "compression" not in joined.meta

    def test_the_last_files_time_of_last_obs_is_kept(self, halves, tmp_path):
        record = "  2005     4     2     0    59   29.9960000     GPS         TIME OF LAST OBS"
        second = halves / "3040092b.05o"
        header, body = _parts(second)
        header.insert(-1, record)
        second.write_text("\n".join([*header, *body]) + "\n", encoding="ascii")
        joined = join_sessions(_sessions(halves), tmp_path / "joined")
        assert record in _parts(Path(joined.obs_file))[0]


class TestRefused:
    def _edit(self, path: Path, old: str, new: str) -> None:
        text = path.read_text(encoding="ascii")
        assert old in text
        path.write_text(text.replace(old, new), encoding="ascii")

    def test_two_setups_of_one_station(self, halves, tmp_path):
        """The receiver set up again at another height is two sessions, not one."""
        self._edit(
            halves / "3040092b.05o",
            "        0.0000        0.0000        0.0000                  ANTENNA: DELTA H/E/N",
            "        1.5000        0.0000        0.0000                  ANTENNA: DELTA H/E/N",
        )
        with pytest.raises(DataError) as caught:
            join_sessions(_sessions(halves), tmp_path / "joined")
        assert caught.value.code == "data.gnss_join_setups_differ"
        assert caught.value.context["field"] == "ANTENNA: DELTA H/E/N"

    def test_files_that_record_different_observations(self, halves, tmp_path):
        self._edit(
            halves / "3040092b.05o",
            "     4    L1    C1    L2    P2                              # / TYPES OF OBSERV",
            "     4    L1    C1    L2    C2                              # / TYPES OF OBSERV",
        )
        with pytest.raises(DataError) as caught:
            join_sessions(_sessions(halves), tmp_path / "joined")
        assert caught.value.context["field"] == "# / TYPES OF OBSERV"

    def test_two_stations(self, halves, tmp_path):
        self._edit(
            halves / "3040092b.05o",
            f"{'3040':<60}MARKER NAME",
            f"{'3041':<60}MARKER NAME",
        )
        with pytest.raises(DataError) as caught:
            join_sessions(_sessions(halves), tmp_path / "joined")
        assert caught.value.code == "data.gnss_join_different_stations"

    def test_a_file_whose_observations_cannot_be_read(self, halves, tmp_path):
        from dataclasses import replace

        first, second = _sessions(halves)
        hatanaka = replace(second, obs_file=str(halves / "3040092b.05d"))
        with pytest.raises(DataError) as caught:
            join_sessions([first, hatanaka], tmp_path / "joined")
        assert caught.value.code == "data.rinex_compression_unsupported"


@requires_rtklib
class TestTheEngineReadsTheWhole:
    """Tier 4: ``rnx2rtkp`` given the joined base solves the baseline it solves from the unsplit file."""

    def test_the_baseline_is_the_one_the_unsplit_file_gives(self, halves, tmp_path):
        from geocomp.engines.rtklib import RtklibEngine, RtklibJob, profile

        whole = {session.station_id: session for session in scan_folder(DATA).sessions}
        joined = join_sessions(_sessions(halves), tmp_path / "joined")
        solutions = [
            RtklibEngine()
            .run(
                RtklibJob(rover=whole["0759"], base=base, config=profile("relative-static")),
                work_dir=tmp_path / name,
            )
            .solution
            for name, base in (("whole", whole["3040"]), ("joined", joined))
        ]
        unsplit, split_then_joined = solutions
        assert len(split_then_joined.epochs) == len(unsplit.epochs) == 120
        # Not close: the same. The engine reads the joined file as the original.
        assert [(e.time, e.position, e.is_ambiguity_fixed) for e in split_then_joined.epochs] == [
            (e.time, e.position, e.is_ambiguity_fixed) for e in unsplit.epochs
        ]


class TestOccupations:
    """P13-29: which of one station's files are one occupation, to be joined."""

    def _halves(self, halves):
        from geocomp.io.gnss_discovery import occupations

        first, second = _sessions(halves)
        return first, second, occupations

    def test_files_that_follow_one_another_are_one(self, halves):
        first, second, occupations = self._halves(halves)
        assert occupations([second, first]) == [(first, second)]

    def test_a_gap_of_more_than_two_intervals_is_two(self, halves):
        from dataclasses import replace
        from datetime import timedelta

        first, second, occupations = self._halves(halves)
        # The files state a 30 s interval, so a minute is allowed and a second more is not.
        later = replace(second, start=first.end + timedelta(seconds=61), end=second.end + timedelta(hours=1))
        assert occupations([first, later]) == [(first,), (later,)]
        just = replace(second, start=first.end + timedelta(seconds=60))
        assert occupations([first, just]) == [(first, just)]

    def test_another_day_is_another_occupation(self, halves):
        from dataclasses import replace
        from datetime import timedelta

        first, second, occupations = self._halves(halves)
        tomorrow = replace(second, start=second.start + timedelta(days=1), end=second.end + timedelta(days=1))
        assert occupations([first, tomorrow]) == [(first,), (tomorrow,)]

    def test_another_setup_is_another_occupation(self, halves):
        from dataclasses import replace

        from geocomp.core.uncertainty import Quantity
        from geocomp.core.units import Unit

        first, second, occupations = self._halves(halves)
        raised = replace(second, antenna_height=Quantity.exact(1.5, Unit.METRE))
        assert occupations([first, raised]) == [(first,), (raised,)]

    def test_a_file_with_no_span_is_its_own(self, halves):
        from dataclasses import replace

        first, second, occupations = self._halves(halves)
        unknown = replace(second, start=None, end=None)
        assert occupations([unknown, first]) == [(first,), (unknown,)]


@requires_rtklib
class TestTheEngineReadsTheWholeRover:
    """Tier 4: the rover's hour, cut in two and joined, is solved as the hour was (P13-29)."""

    def test_the_baseline_is_the_one_the_unsplit_rover_gives(self, tmp_path):
        from geocomp.engines.rtklib import RtklibEngine, RtklibJob, profile

        folder = tmp_path / "rover"
        folder.mkdir()
        split(DATA / "07590920.05o", folder)
        shutil.copy(DATA / "brdc_0759.05n.gz", folder)
        whole = {session.station_id: session for session in scan_folder(DATA).sessions}
        joined = join_sessions(_sessions(folder), tmp_path / "joined")
        unsplit, split_then_joined = (
            RtklibEngine()
            .run(
                RtklibJob(rover=rover, base=whole["3040"], config=profile("relative-static")),
                work_dir=tmp_path / name,
            )
            .solution
            for name, rover in (("whole", whole["0759"]), ("joined", joined))
        )
        assert len(split_then_joined.epochs) == len(unsplit.epochs) == 120
        assert [(e.time, e.position, e.is_ambiguity_fixed) for e in split_then_joined.epochs] == [
            (e.time, e.position, e.is_ambiguity_fixed) for e in unsplit.epochs
        ]
