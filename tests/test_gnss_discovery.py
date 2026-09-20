# SPDX-License-Identifier: GPL-2.0-or-later
"""``io/gnss_discovery.py`` -- a folder of RINEX into sessions (FR-350, FR-351).

The fixture folder holds RTKLIB's own sample pair, so "two sessions that
overlap" below is a fact about a real 2005 survey rather than about files
written to satisfy this test.
"""

from __future__ import annotations

import gzip
import json
import shutil
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest

from geocomp.core.errors import DataError
from geocomp.io.gnss_discovery import overlapping_groups, scan_folder

DATA = Path(__file__).parent / "data" / "rtklib"
BASE_NAME = "07590920.05o"
ROVER_NAME = "30400920.05o"


@pytest.fixture
def scan():
    return scan_folder(DATA)


def _by_id(scan):
    return {session.id: session for session in scan.sessions}


class TestScanningTheRealFolder:
    def test_every_observation_file_becomes_a_session(self, scan):
        assert {session.id for session in scan.sessions} == {
            BASE_NAME, ROVER_NAME, "rinex3-header.rnx",
        }

    def test_nothing_readable_is_skipped(self, scan):
        """PROVENANCE.md is markdown and is not a candidate; the gzipped
        navigation file is one and reads fine."""
        assert scan.skipped == []
        assert [path.name for path in scan.navigation] == ["brdc_0759.05n.gz"]

    def test_the_station_comes_from_the_header(self, scan):
        sessions = _by_id(scan)
        assert sessions[BASE_NAME].station_id == "0759"
        assert sessions[ROVER_NAME].station_id == "3040"

    def test_the_instrument_fields_are_carried(self, scan):
        session = _by_id(scan)[BASE_NAME]
        assert session.receiver == "TRIMBLE 5700"
        assert session.antenna == "TRM29659.00"
        assert session.interval == pytest.approx(30.0)

    def test_the_antenna_height_says_its_method_is_unstated(self, scan):
        """Not left empty. RINEX states a distance and not how it was measured,
        and "unstated" is a value a later step can act on where "" is an
        absence that looks like nobody filled the form in."""
        session = _by_id(scan)[BASE_NAME]
        assert session.antenna_height is not None
        assert session.antenna_height.value == 0.0
        assert session.antenna_height_method == "unstated"

    def test_the_scan_serialises(self, scan):
        """It reaches provenance and the project store, so it must round-trip
        through JSON like every other model."""
        assert json.loads(json.dumps(scan.to_dict()))["sessions"]


class TestSpans:
    def test_a_missing_last_epoch_is_measured_from_the_file(self, scan):
        """The header omits ``TIME OF LAST OBS``; the session still has an end."""
        session = _by_id(scan)[BASE_NAME]
        assert session.start == datetime(2005, 4, 2, 0, 0, tzinfo=UTC)
        assert session.end is not None
        assert session.end.replace(microsecond=0) == datetime(2005, 4, 2, 0, 59, 30, tzinfo=UTC)
        assert session.duration_seconds == pytest.approx(3570.0, abs=1.0)

    def test_a_session_whose_span_cannot_be_established_says_so(self, tmp_path):
        """A gzipped file cannot be seeked, so its end is an honest unknown --
        and a session with no end cannot be matched with simultaneous ones,
        which the user needs to be told rather than left to infer."""
        path = tmp_path / f"{BASE_NAME}.gz"
        with gzip.open(path, "wt", encoding="ascii") as handle:
            handle.write((DATA / BASE_NAME).read_text(encoding="ascii"))
        result = scan_folder(tmp_path)
        assert result.sessions[0].end is None
        assert any("span is unknown" in reason for _, reason in result.warnings)


class TestSimultaneity:
    def test_the_pair_that_forms_a_baseline_is_grouped(self, scan):
        """The whole point of the scan: which sessions could form a baseline."""
        groups = overlapping_groups(scan.sessions)
        stations = [sorted(session.station_id for session in group) for group in groups]
        assert ["0759", "3040"] in stations

    def test_a_session_from_another_epoch_stands_alone(self, scan):
        groups = overlapping_groups(scan.sessions)
        assert ["PORTO ALEGRE 1"] in [
            sorted(session.station_id for session in group) for group in groups
        ]

    def test_grouping_is_transitive(self, scan):
        """A overlapping B and B overlapping C is one observing period, even
        where A and C do not themselves overlap: the engine decides which pairs
        within it are worth processing, not this.

        Spans are set explicitly so the three sessions are exactly that shape --
        the fixture pair observes the same hour and would not show it.
        """
        template = _by_id(scan)[BASE_NAME]

        def spanning(name, start_hour, end_hour):
            return replace(
                template,
                id=name,
                station_id=name,
                start=datetime(2005, 4, 2, start_hour, 0, tzinfo=UTC),
                end=datetime(2005, 4, 2, end_hour, 0, tzinfo=UTC),
            )

        first, middle, last = (
            spanning("A", 0, 2), spanning("B", 1, 4), spanning("C", 3, 5),
        )
        assert not first.overlaps(last)
        groups = overlapping_groups((first, middle, last))
        assert len(groups) == 1
        assert {session.id for session in groups[0]} == {"A", "B", "C"}

    def test_sessions_that_merely_touch_do_not_overlap(self, scan):
        """One ending exactly as the next begins share no epoch, so they cannot
        difference to a baseline."""
        template = _by_id(scan)[BASE_NAME]
        noon = datetime(2005, 4, 2, 12, 0, tzinfo=UTC)
        before = replace(template, id="before", start=template.start, end=noon)
        after = replace(template, id="after", start=noon,
                        end=datetime(2005, 4, 2, 13, 0, tzinfo=UTC))
        assert not before.overlaps(after)
        assert len(overlapping_groups((before, after))) == 2

    def test_a_session_with_no_span_is_never_grouped_wrongly(self, scan):
        unknown = replace(_by_id(scan)[BASE_NAME], id="unknown", end=None)
        groups = overlapping_groups((unknown, _by_id(scan)[ROVER_NAME]))
        assert len(groups) == 2


class TestCrossChecks:
    """The header decides and the name is checked against it, never the reverse."""

    def test_a_name_claiming_another_station_is_warned_about(self, tmp_path):
        shutil.copy(DATA / BASE_NAME, tmp_path / "99990920.05o")
        result = scan_folder(tmp_path)
        assert result.sessions[0].station_id == "0759"
        assert any("9999" in reason and "0759" in reason for _, reason in result.warnings)

    def test_a_name_claiming_another_day_is_warned_about(self, tmp_path):
        shutil.copy(DATA / BASE_NAME, tmp_path / "07591230.05o")
        result = scan_folder(tmp_path)
        assert any("2005-05-03" in reason for _, reason in result.warnings)

    def test_agreement_produces_no_warning(self, tmp_path):
        shutil.copy(DATA / BASE_NAME, tmp_path / BASE_NAME)
        result = scan_folder(tmp_path)
        assert not any("header states marker" in reason for _, reason in result.warnings)

    def test_the_name_supplies_the_station_when_the_header_has_no_marker(self, tmp_path):
        """A marker-less observation file is unusual but legal, and the name is
        better than nothing -- recorded in meta so the origin is visible."""
        text = (DATA / BASE_NAME).read_text(encoding="ascii")
        stripped = "\n".join(
            line for line in text.splitlines() if line[60:80].strip() != "MARKER NAME"
        )
        (tmp_path / BASE_NAME).write_text(stripped + "\n", encoding="ascii")
        session = scan_folder(tmp_path).sessions[0]
        assert session.station_id == "0759"
        assert session.meta["name_claims_station"] == "0759"


class TestNavigationPairing:
    def test_pairing_by_date_when_the_names_state_one(self, tmp_path):
        shutil.copy(DATA / BASE_NAME, tmp_path / BASE_NAME)
        with gzip.open(DATA / "brdc_0759.05n.gz", "rt", encoding="ascii") as handle:
            navigation = handle.read()
        (tmp_path / "07590920.05n").write_text(navigation, encoding="ascii")
        (tmp_path / "07591800.05n").write_text(navigation, encoding="ascii")
        session = scan_folder(tmp_path).sessions[0]
        assert [Path(name).name for name in session.nav_files] == ["07590920.05n"]

    def test_a_fallback_pairing_says_it_fell_back(self, scan):
        """``brdc_0759.05n.gz`` follows neither naming convention, so its date
        is unknown and every navigation file is offered instead. Silently
        attaching the wrong day's ephemeris is a solution that converges to the
        wrong place."""
        session = _by_id(scan)[BASE_NAME]
        assert [Path(name).name for name in session.nav_files] == ["brdc_0759.05n.gz"]
        assert any("paired by fallback" in reason for _, reason in scan.warnings)

    def test_no_navigation_is_not_an_error(self, tmp_path):
        shutil.copy(DATA / BASE_NAME, tmp_path / BASE_NAME)
        session = scan_folder(tmp_path).sessions[0]
        assert session.nav_files == ()


class TestUnreadableFiles:
    def test_a_bad_file_is_reported_and_the_scan_continues(self, tmp_path):
        """FR-166. A scan that quietly drops what it cannot open reports a
        campaign as smaller than it was, and the missing session looks like a
        field failure rather than a software one."""
        shutil.copy(DATA / BASE_NAME, tmp_path / BASE_NAME)
        (tmp_path / "30400920.05o").write_text("this is not RINEX\n", encoding="ascii")
        result = scan_folder(tmp_path)
        assert [session.id for session in result.sessions] == [BASE_NAME]
        assert len(result.skipped) == 1
        name, reason = result.skipped[0]
        assert "30400920.05o" in name
        assert "rinex_header_missing" in reason

    def test_files_that_are_not_rinex_at_all_are_passed_over_silently(self, tmp_path):
        """Different from skipped: a project folder holds shapefiles and notes,
        and listing them as failures would bury the ones that matter."""
        shutil.copy(DATA / BASE_NAME, tmp_path / BASE_NAME)
        (tmp_path / "notes.txt").write_text("hello\n", encoding="ascii")
        (tmp_path / "site.shp").write_bytes(b"\x00\x01")
        result = scan_folder(tmp_path)
        assert result.skipped == []
        assert len(result.sessions) == 1


class TestTheFolderItself:
    def test_an_empty_folder_is_an_empty_scan_not_an_error(self, tmp_path):
        result = scan_folder(tmp_path)
        assert result.sessions == () and result.skipped == []

    def test_a_path_that_is_not_a_directory_is_refused(self, tmp_path):
        path = tmp_path / "file.txt"
        path.write_text("x", encoding="ascii")
        with pytest.raises(DataError) as caught:
            scan_folder(path)
        assert caught.value.code == "data.gnss_scan_not_a_directory"

    def test_recursion_is_opt_in(self, tmp_path):
        (tmp_path / "day1").mkdir()
        shutil.copy(DATA / BASE_NAME, tmp_path / "day1" / BASE_NAME)
        assert scan_folder(tmp_path).sessions == ()
        assert len(scan_folder(tmp_path, recursive=True).sessions) == 1


class TestMetadata:
    def test_what_the_header_said_is_kept(self, scan):
        meta = _by_id(scan)[BASE_NAME].meta
        assert meta["rinex_version"] == pytest.approx(2.10)
        assert meta["observation_types"][""] == ["L1", "C1", "L2", "P2"]
        assert meta["time_system"] == "GPS"
        assert meta["approximate_position"][0] == pytest.approx(-3976219.5082)

    def test_an_eccentric_antenna_is_recorded(self, scan):
        assert _by_id(scan)["rinex3-header.rnx"].meta["antenna_eccentricity"] == [0.012, -0.008]

    def test_a_hatanaka_file_is_flagged_as_needing_decompression(self, tmp_path):
        """The header reads but the observations do not, and ``rnx2rtkp`` wants
        them -- saying so here is cheaper than a failed run later."""
        shutil.copy(DATA / BASE_NAME, tmp_path / "07590920.05d")
        session = scan_folder(tmp_path).sessions[0]
        assert session.meta["needs_crx2rnx"] is True


class TestOtherRinexTypes:
    def test_a_file_that_is_neither_observation_nor_navigation_is_reported(self, tmp_path):
        """A meteorological file is legal RINEX and is not a session. Reporting
        it beats dropping it: a user who pointed at the wrong folder should be
        told what was there."""
        path = tmp_path / "0759092a.05m"
        path.write_text(
            f"{2.11:9.2f}".ljust(20).ljust(60) + f"{'RINEX VERSION / TYPE':<20}\n",
            encoding="ascii",
        )
        # Column 21 carries the file type; 'M' is meteorological.
        text = path.read_text(encoding="ascii").splitlines()[0]
        path.write_text(
            text[:20] + "M" + text[21:] + "\n" + f"{'':<60}{'END OF HEADER':<20}\n",
            encoding="ascii",
        )
        result = scan_folder(tmp_path)
        assert result.sessions == ()
        assert len(result.skipped) == 1
        assert "neither observation nor navigation" in result.skipped[0][1]
