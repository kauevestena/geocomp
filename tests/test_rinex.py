# SPDX-License-Identifier: GPL-2.0-or-later
"""``io/rinex.py`` -- reading what a RINEX header actually states (FR-164).

The RINEX 2 files here are RTKLIB's own sample data, unmodified; the RINEX 3
header is transcribed from the published format definition, because nothing in
the RTKLIB tree is RINEX 3 and ``convbin`` -- the tool that would convert one --
aborts with a buffer overflow on RTKLIB's own data at the pinned commit. Both
facts are in ``tests/data/rtklib/PROVENANCE.md``, and the tests below say which
fixture is which rather than letting a transcript pass for a tool's output.
"""

from __future__ import annotations

import gzip
from datetime import UTC, datetime
from pathlib import Path
from typing import ClassVar

import pytest

from geocomp.core.errors import DataError
from geocomp.io.rinex import (
    Compression,
    HeightMethod,
    compression_of,
    read_rinex_header,
)

DATA = Path(__file__).parent / "data" / "rtklib"

#: RTKLIB's sample pair: two stations observing the same hour of 2 April 2005.
BASE = DATA / "07590920.05o"
ROVER = DATA / "30400920.05o"
NAVIGATION = DATA / "brdc_0759.05n.gz"
RINEX3 = DATA / "rinex3-header.rnx"


class TestRinex2Observation:
    """Against RTKLIB's own file, so every expected value below is a fact."""

    @pytest.fixture
    def header(self):
        return read_rinex_header(BASE)

    def test_the_version_and_type_come_from_the_record_not_the_extension(self, header):
        assert header.version == pytest.approx(2.10)
        assert header.file_type == "O"
        assert header.satellite_system == "G"
        assert header.is_observation and not header.is_navigation

    def test_the_marker_is_the_one_in_the_header(self, header):
        """``specs/08`` §4: read the header, do not trust the file name. The
        file is called ``07590920.05o`` and the mark is ``0759`` -- they agree
        here, and session discovery is what reports it when they do not."""
        assert header.marker_name == "0759"

    def test_the_receiver_fields_are_split_by_column(self, header):
        """Three twenty-character fields. Splitting on whitespace turns
        ``TRIMBLE 5700`` into two tokens and shifts the version into the type."""
        assert header.receiver.number == "00000"
        assert header.receiver.type == "TRIMBLE 5700"
        assert header.receiver.version == "1.24"

    def test_the_antenna_type_is_read_and_its_serial_is_empty(self, header):
        """An empty serial is normal and must not pull the type leftwards."""
        assert header.antenna_number == ""
        assert header.antenna_type == "TRM29659.00"

    def test_the_approximate_position_is_a_complete_triple(self, header):
        assert header.approximate_position == pytest.approx(
            (-3976219.5082, 3382372.5671, 3652512.9849)
        )

    def test_the_interval_and_first_epoch_are_read(self, header):
        assert header.interval == pytest.approx(30.0)
        assert header.first_observation == datetime(2005, 4, 2, 0, 0, 0, tzinfo=UTC)
        assert header.time_system == "GPS"

    def test_a_header_without_a_last_epoch_reports_no_span(self, header):
        """``TIME OF LAST OBS`` is optional, and this file omits it. Guessing a
        span from the file size or the interval would be a number nobody
        measured."""
        assert header.last_observation is None
        assert header.span is None

    def test_the_observation_types_are_the_four_the_file_declares(self, header):
        assert header.observation_types == {"": ("L1", "C1", "L2", "P2")}

    def test_the_two_stations_are_different_marks_at_the_same_epoch(self):
        """What makes the pair a baseline rather than two files."""
        base, rover = read_rinex_header(BASE), read_rinex_header(ROVER)
        assert base.marker_name != rover.marker_name
        assert base.first_observation == rover.first_observation
        assert base.interval == rover.interval
        assert base.approximate_position != rover.approximate_position


class TestAntennaDelta:
    def test_the_method_is_unstated_because_rinex_does_not_state_it(self):
        """The point of the field, and the reason it is not defaulted.

        ``ANTENNA: DELTA H/E/N`` is by definition a vertical offset to the
        antenna reference point. If a crew measured a slant height, someone
        reduced it before the file existed and the file does not record that
        they did. ``specs/08`` §4 requires the method be recorded; this reader
        can only record that the file is silent, and the session must supply the
        rest. Defaulting to VERTICAL would be inventing the fact.
        """
        delta = read_rinex_header(BASE).antenna_delta
        assert delta is not None
        assert delta.method is HeightMethod.UNSTATED

    def test_a_zero_delta_is_a_statement_not_an_absence(self):
        """The antenna stood on the mark. That is a measurement, and it is
        different from a file that omits the record."""
        delta = read_rinex_header(BASE).antenna_delta
        assert delta.height.value == 0.0
        assert not delta.is_eccentric

    def test_a_horizontal_offset_is_reported_separately(self):
        """Rare enough that it is either deliberate or a mistake, and either way
        it must not pass unnoticed."""
        delta = read_rinex_header(RINEX3).antenna_delta
        assert delta.height.value == pytest.approx(1.5230)
        assert delta.east.value == pytest.approx(0.0120)
        assert delta.north.value == pytest.approx(-0.0080)
        assert delta.is_eccentric


class TestRinex3:
    """The transcribed fixture. Its value is the *format*, not the numbers."""

    @pytest.fixture
    def header(self):
        return read_rinex_header(RINEX3)

    def test_the_version_is_read_as_three(self, header):
        assert header.version == pytest.approx(3.04)
        assert header.file_type == "O"
        assert header.satellite_system == "M"

    def test_a_marker_name_containing_a_space_survives(self, header):
        """``MARKER NAME`` is one sixty-character field. A reader that splits on
        whitespace returns ``PORTO`` and calls it the station."""
        assert header.marker_name == "PORTO ALEGRE 1"

    def test_the_rinex_3_only_records_are_read(self, header):
        assert header.marker_number == "91234M001"
        assert header.marker_type == "GEODETIC"

    def test_an_antenna_type_with_a_radome_keeps_its_spacing(self, header):
        """``TRM59800.00     SCIS`` is one A20 field: antenna then radome, and
        the gap between them is part of the identifier."""
        assert header.antenna_type == "TRM59800.00     SCIS"

    def test_observation_types_are_per_constellation(self, header):
        assert set(header.observation_types) == {"G", "R"}
        assert header.observation_types["R"] == (
            "C1C", "L1C", "D1C", "S1C", "C2P", "L2P", "D2P", "S2P",
        )

    def test_a_continuation_record_is_not_lost(self, header):
        """Sixteen GPS types: thirteen on the first record and three on the
        second. Dropping the continuation looks like a receiver tracking fewer
        signals than it does."""
        assert len(header.observation_types["G"]) == 16
        assert header.observation_types["G"][-3:] == ("L5Q", "D5Q", "S5Q")

    def test_the_type_list_is_read_at_the_right_stride(self, header):
        """The defect this test exists for, found while writing the fixture.

        RINEX 2 lists observation types six characters apart (``I6, 9(4X,A2)``)
        and RINEX 3 **four** (``A1, 2X, I3, 13(1X,A3)``). Reading a RINEX 3 list
        at stride 6 raises nothing: it returns a shorter list of codes chopped
        across their boundaries, which reads as a file with fewer observables
        rather than as a parser that is wrong. Every code here is three
        characters and every one is a real RINEX 3 observation code.
        """
        for system, codes in header.observation_types.items():
            assert codes, system
            for code in codes:
                assert len(code) == 3, (system, code)
                assert code[0] in "CLDS", code

    def test_the_span_comes_from_both_epoch_records(self, header):
        assert header.first_observation == datetime(2026, 9, 13, 0, 0, tzinfo=UTC)
        assert header.last_observation == datetime(2026, 9, 13, 23, 59, 30, tzinfo=UTC)
        assert header.span == pytest.approx(86370.0)


class TestNavigation:
    def test_a_navigation_file_is_recognised_and_carries_no_marker(self):
        header = read_rinex_header(NAVIGATION)
        assert header.is_navigation and not header.is_observation
        assert header.marker_name == ""
        assert header.observation_types == {}

    def test_a_gzipped_file_is_read_without_being_unpacked_first(self):
        """The only gzipped fixture, and a real file rather than one this
        project compressed for the occasion."""
        header = read_rinex_header(NAVIGATION)
        assert header.compression is Compression.GZIP
        assert header.version == pytest.approx(2.10)


class TestCompressionDetection:
    @pytest.mark.parametrize(
        ("name", "expected"),
        [
            ("07590920.05o", Compression.NONE),
            ("ABCD1234.rnx", Compression.NONE),
            ("brdc_0759.05n.gz", Compression.GZIP),
            ("07590920.05o.Z", Compression.UNIX_COMPRESS),
            ("session.zip", Compression.ZIP),
            # Hatanaka: a `d` where the short-name type letter goes, or `.crx`.
            ("07590920.05d", Compression.HATANAKA),
            ("ABCD00BRA_R_20260010000_01D_30S_MO.crx", Compression.HATANAKA),
            ("07590920.05d.gz", Compression.HATANAKA_GZIP),
        ],
    )
    def test_the_wrapper_is_named_from_the_suffixes(self, name, expected):
        assert compression_of(name) is expected

    def test_an_observation_file_is_not_mistaken_for_hatanaka(self):
        """``o`` and ``d`` differ by one letter in the same column."""
        assert compression_of("07590920.05o") is Compression.NONE


class TestRefusals:
    def test_a_file_that_is_not_rinex_is_refused_by_name(self, tmp_path):
        path = tmp_path / "notes.txt"
        path.write_text("this is not a RINEX file\n", encoding="ascii")
        with pytest.raises(DataError) as caught:
            read_rinex_header(path)
        assert caught.value.code == "data.rinex_header_missing"
        assert str(path) in caught.value.context["file"]

    def test_an_empty_file_is_refused(self, tmp_path):
        path = tmp_path / "empty.05o"
        path.write_text("", encoding="ascii")
        with pytest.raises(DataError) as caught:
            read_rinex_header(path)
        assert caught.value.code == "data.rinex_file_empty"

    def test_a_header_that_never_ends_is_refused_rather_than_read_whole(self, tmp_path):
        """A truncated or corrupt file must not pull a day of observations into
        memory looking for a record that is not there."""
        path = tmp_path / "runaway.05o"
        first = read_rinex_header(BASE).path.read_text(encoding="ascii").splitlines()[0]
        path.write_text(first + "\n" + "COMMENT".rjust(80) + "\n" * 1, encoding="ascii")
        with pytest.raises(DataError) as caught:
            read_rinex_header(path)
        assert caught.value.code == "data.rinex_header_unterminated"

    @pytest.mark.parametrize("suffix", [".Z", ".zip"])
    def test_a_wrapper_this_reader_cannot_open_says_so(self, tmp_path, suffix):
        """Rather than half-reading it. ``compress(1)`` is not in the standard
        library, and a zip may hold several files -- which is a session
        question, not a header one."""
        path = tmp_path / f"07590920.05o{suffix}"
        path.write_bytes(b"not really compressed")
        with pytest.raises(DataError) as caught:
            read_rinex_header(path)
        assert caught.value.code == "data.rinex_compression_unsupported"
        assert caught.value.context["compression"] in {"unix_compress", "zip"}
        assert "decompress it first" in caught.value.context["expected"]

    def test_a_malformed_version_names_what_was_expected(self, tmp_path):
        path = tmp_path / "bad.05o"
        path.write_text(f"{'x.xx':<60}{'RINEX VERSION / TYPE':<20}\n", encoding="ascii")
        with pytest.raises(DataError) as caught:
            read_rinex_header(path)
        assert caught.value.code == "data.rinex_version_malformed"
        assert "2.11" in caught.value.context["expected"]


class TestOnlyTheHeaderIsRead:
    def test_reading_stops_at_end_of_header(self, tmp_path):
        """A day of 1 s observations is hundreds of megabytes, and discovery
        scans folders of them. Proved by appending a line that would fail if it
        were parsed, after the terminator."""
        path = tmp_path / "trailing.05o"
        text = BASE.read_text(encoding="ascii")
        end = text.index("END OF HEADER") + len("END OF HEADER") + 1
        path.write_text(text[:end] + "\x00 this would not survive being parsed\n", encoding="ascii")
        header = read_rinex_header(path)
        assert header.marker_name == "0759"

    def test_a_gzipped_header_stops_there_too(self, tmp_path):
        path = tmp_path / "trailing.05o.gz"
        text = BASE.read_text(encoding="ascii")
        end = text.index("END OF HEADER") + len("END OF HEADER") + 1
        with gzip.open(path, "wt", encoding="ascii") as handle:
            handle.write(text[:end] + "\x00 not parseable\n")
        assert read_rinex_header(path).marker_name == "0759"


def _record(value: str, label: str) -> str:
    return f"{value:<60}{label:<20}".rstrip() + "\n"


def _rinex2(*records: str) -> str:
    head = _record(f"{2.11:9.2f}".ljust(20) + "OBSERVATION DATA".ljust(20) + "G (GPS)",
                   "RINEX VERSION / TYPE")
    return head + "".join(records) + _record("", "END OF HEADER")


class TestRinex2Continuations:
    """More than nine observation types, which is an ordinary file.

    RTKLIB's sample declares four, so the continuation path had no fixture. A
    dual-frequency receiver with code, phase, Doppler and SNR passes nine
    easily, and a reader that drops the second record reports the file as
    carrying fewer observables than it does.
    """

    TYPES: ClassVar[list[str]] = [
        "C1", "L1", "D1", "S1", "P2", "L2", "D2", "S2", "C5", "L5", "D5", "S5",
    ]

    def _header(self, tmp_path, *, label_continuation: bool) -> Path:
        first = f"{len(self.TYPES):6d}" + "".join(f"{code:>6}" for code in self.TYPES[:9])
        rest = " " * 6 + "".join(f"{code:>6}" for code in self.TYPES[9:])
        path = tmp_path / "many.11o"
        path.write_text(
            _rinex2(
                _record("MANY", "MARKER NAME"),
                _record(first, "# / TYPES OF OBSERV"),
                _record(rest, "# / TYPES OF OBSERV" if label_continuation else ""),
            ),
            encoding="ascii",
        )
        return path

    @pytest.mark.parametrize("label_continuation", [True, False])
    def test_a_continuation_record_is_read_either_way(self, tmp_path, label_continuation):
        """RINEX 2.11 repeats the label on the continuation; earlier versions
        leave it blank. Both spellings are in the wild and both must work."""
        header = read_rinex_header(self._header(tmp_path, label_continuation=label_continuation))
        assert header.observation_types[""] == tuple(self.TYPES)

    def test_the_list_is_read_at_six_characters_not_four(self, tmp_path):
        """The other half of the stride defect: reading a RINEX 2 list at the
        RINEX 3 stride splits every two-character code across a boundary."""
        header = read_rinex_header(self._header(tmp_path, label_continuation=True))
        assert all(2 <= len(code) <= 3 for code in header.observation_types[""])
        assert "C1" in header.observation_types[""]


class TestMalformedFieldsAreSkippedNotGuessed:
    """A field this reader cannot make sense of is left absent.

    The alternative -- a zero, a default, or a partial triple -- is a number
    nobody measured travelling into a baseline.
    """

    def test_an_unreadable_interval_is_absent(self, tmp_path):
        path = tmp_path / "bad.11o"
        path.write_text(_rinex2(_record("      x.x", "INTERVAL")), encoding="ascii")
        assert read_rinex_header(path).interval is None

    def test_a_partial_position_is_no_position(self, tmp_path):
        """Two of three coordinates is not a position."""
        path = tmp_path / "bad.11o"
        path.write_text(
            _rinex2(_record(f"{1.0:14.4f}{2.0:14.4f}", "APPROX POSITION XYZ")), encoding="ascii"
        )
        assert read_rinex_header(path).approximate_position is None

    def test_a_partial_antenna_delta_is_no_delta(self, tmp_path):
        path = tmp_path / "bad.11o"
        path.write_text(
            _rinex2(_record(f"{1.5:14.4f}", "ANTENNA: DELTA H/E/N")), encoding="ascii"
        )
        assert read_rinex_header(path).antenna_delta is None

    @pytest.mark.parametrize(
        "value",
        [
            "  2005     4    xx     0     0    0.0000000     GPS",
            "  2005     4     2     0     0        x.xx      GPS",
            "  2005    13    42     0     0    0.0000000     GPS",
        ],
        ids=["non-numeric-day", "non-numeric-seconds", "impossible-date"],
    )
    def test_an_unreadable_first_epoch_is_absent_but_the_time_system_survives(
        self, tmp_path, value
    ):
        path = tmp_path / "bad.11o"
        path.write_text(_rinex2(_record(value, "TIME OF FIRST OBS")), encoding="ascii")
        header = read_rinex_header(path)
        assert header.first_observation is None
        assert header.time_system == "GPS"

    def test_a_last_epoch_supplies_the_time_system_when_the_first_did_not(self, tmp_path):
        path = tmp_path / "only-last.11o"
        path.write_text(
            _rinex2(_record("  2005     4     2    23    59   30.0000000     GLO",
                            "TIME OF LAST OBS")),
            encoding="ascii",
        )
        header = read_rinex_header(path)
        assert header.time_system == "GLO"
        assert header.first_observation is None
        assert header.span is None
