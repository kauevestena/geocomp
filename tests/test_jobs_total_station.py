# SPDX-License-Identifier: GPL-2.0-or-later
"""The total-station field book, typed (FR-011, FR-012, FR-014).

**Typed equals imported** is the test that carries the whole of ADR-0010 at
this tier: RD-01's rows typed into a job emit rows and a mapping that the
importer's own reader turns into setups equal, quantity for quantity and to the
last bit, to reading ``topo_test/raw_data.csv`` with RD-01's own mapping. The
window then has nothing to compute and nothing to disagree about.
"""

from __future__ import annotations

import csv
import json
import math

import pytest

from geocomp.core.errors import ValidationError
from geocomp.core.instruments import InstrumentProfile, ProfileLibrary
from geocomp.io import AngleFormat, infer_mapping, read_field_book
from geocomp.jobs import AngleTyping, InputFile, Ref, resolve
from geocomp.jobs import total_station as ts
from tests import reference_rd01 as rd01


def library() -> ProfileLibrary:
    profiles = ProfileLibrary()
    profiles.add_instrument(InstrumentProfile(id="ts"))
    return profiles


def rd01_rows() -> list[list[str]]:
    with open(rd01.RAW, encoding="utf-8") as handle:
        return list(csv.reader(handle))


def typed_rd01(typing: AngleTyping = AngleTyping.DMS) -> ts.TotalStationBook:
    """RD-01 as a surveyor would type it: one row per pointing, angles in *typing*."""
    book = ts.TotalStationBook(ts.new_job("RD-01"))
    book.angle_typing = typing

    def angle(row: dict[str, str], prefix: str) -> str:
        degrees, minutes, seconds = (row[prefix + part] for part in "GMS")
        if typing is AngleTyping.DMS:
            return f"{degrees} {minutes} {seconds}"
        return f"{degrees}.{int(minutes):02d}{int(seconds):02d}"

    with open(rd01.RAW, encoding="utf-8") as handle:
        lines = [
            "\t".join(
                [
                    row["E"],
                    row["hi"],
                    row["R"] if row["vis"] == "R" else row["V"],
                    row["pos"],
                    angle(row, "H"),
                    angle(row, "V"),
                    row["D"],
                    row["hs"],
                ]
            )
            for row in csv.DictReader(handle)
        ]
    book.table.paste(0, "station", "\n".join(lines))
    return book


def imported_rd01():
    rows = rd01_rows()
    return read_field_book(rows, infer_mapping(rows[0]), library=library())


def as_values(result) -> list:
    """Every setup's readings, as plain values and variances, for comparing two imports."""

    def reading(item):
        return (
            item.target,
            item.face,
            (item.horizontal.value, item.horizontal.variance),
            (item.zenith.value, item.zenith.variance),
            None if item.distance is None else (item.distance.value, item.distance.variance),
            None if item.target_height is None else (item.target_height.value, item.target_height.variance),
            item.set_number,
        )

    return [
        (
            setup.station,
            (setup.instrument_height.value, setup.instrument_height.variance),
            [(reading(pair.direct), reading(pair.reverse)) for pair in setup.pairs],
            [reading(single) for single in setup.singles],
        )
        for setup in result.setups
    ]


class TestTypedEqualsImported:
    @pytest.mark.parametrize("typing", [AngleTyping.DMS, AngleTyping.DMS_PACKED])
    def test_rd01_typed_reads_as_rd01_imported_to_the_last_bit(self, typing):
        typed = typed_rd01(typing).read(library=library())
        imported = imported_rd01()
        assert imported.setups, "RD-01 must import, or this compares nothing"
        assert as_values(typed) == as_values(imported)
        assert typed.findings == imported.findings == ()

    def test_the_rows_keep_their_numbers(self):
        """Line n + 1 of the emitted file is row n of the grid, which for a
        book typed in the file's own order is the file's own numbering -- so
        the provenance each reading records is the same too."""
        typed = typed_rd01().read(library=library())
        imported = imported_rd01()
        assert [r.record for s in typed.setups for p in s.pairs for r in (p.direct, p.reverse)] == [
            r.record for s in imported.setups for p in s.pairs for r in (p.direct, p.reverse)
        ]

    def test_the_emitted_mapping_is_the_identity_in_radians(self):
        emission = typed_rd01().emit()
        assert emission.mapping.angle_format is AngleFormat.RADIANS
        assert emission.mapping.unrecognised(list(emission.rows[0])) == ()
        assert emission.mapping.missing_required() == ()
        assert all(column.column == column.field for column in emission.mapping.columns)

    def test_the_csv_and_the_mapping_read_back_as_they_were_emitted(self, tmp_path):
        """Through the files, as the import algorithm receives them."""
        from geocomp.io import FieldMapping, read_field_book_csv

        emission = typed_rd01().emit()
        (tmp_path / "book.csv").write_text(emission.csv_text(), encoding="utf-8")
        mapping = FieldMapping.from_dict(json.loads(emission.mapping_text()))
        through_files = read_field_book_csv(tmp_path / "book.csv", mapping, library=library())
        assert as_values(through_files) == as_values(imported_rd01())


class TestConventions:
    def test_a_vertical_angle_from_the_horizon_is_emitted_as_a_zenith_angle(self):
        book = ts.TotalStationBook(ts.new_job())
        book.vertical = ts.VerticalAngle.ELEVATION
        book.table.paste(0, "station", "E1\t1.5\tP1\tPD\t10 00 00\t1 52 20\t13.204\t1.5")
        record = book.read(library=library()).records[0]
        assert record.zenith == math.pi / 2.0 - math.radians(1 + 52 / 60 + 20 / 3600)

    def test_a_blank_station_is_the_station_of_the_row_above(self):
        book = ts.TotalStationBook(ts.new_job())
        book.table.paste(
            0,
            "station",
            "E1\t1.5\tP1\tPD\t10 00 00\t90 00 00\t10\n"
            "\t\tP2\tPD\t20 00 00\t90 00 00\t10\n"
            "E2\t1.6\tP1\tPD\t30 00 00\t90 00 00\t10\n"
            "\t\tP3\tPD\t40 00 00\t90 00 00\t10",
        )
        assert book.stations() == ("E1", "E2")
        assert book.targets("E1") == ("P1", "P2")
        assert book.targets("E2") == ("P1", "P3")
        assert book.targets() == ("P1", "P2", "P3")
        assert book.point_names() == ("E1", "E2", "P1", "P2", "P3")
        result = book.read(library=library())
        assert [setup.station for setup in result.setups] == ["E1", "E2"]
        assert [setup.instrument_height.value for setup in result.setups] == [1.5, 1.6]

    def test_the_spellings_of_a_face_are_emitted_as_the_importers_tokens(self):
        book = ts.TotalStationBook(ts.new_job())
        book.table.paste(
            0, "station", "E1\t1.5\tP1\tf1\t10 00 00\t90 00 00\t10\nE1\t1.5\tP1\t2\t190 00 00\t270 00 00\t10"
        )
        assert [row[2] for row in book.emit().rows[1:]] == ["PD", "PI"]
        book.table.set_cell(0, "face", "cd")
        book.table.set_cell(1, "face", "CI")
        # The Spanish círculo directo / inverso.
        assert [row[2] for row in book.emit().rows[1:]] == ["PD", "PI"]
        assert len(book.read(library=library()).setups[0].pairs) == 1

    def test_a_decimal_comma_is_read_at_the_boundary(self):
        book = ts.TotalStationBook(ts.new_job())
        book.table.paste(0, "station", "E1\t1,495\tP1\tPD\t10 00 00\t90 00 00\t11,508\t1,5")
        record = book.read(library=library()).records[0]
        assert (record.distance, record.instrument_height, record.target_height) == (11.508, 1.495, 1.5)

    def test_changing_the_convention_reinterprets_and_never_rewrites(self):
        book = ts.TotalStationBook(ts.new_job())
        book.table.paste(0, "station", "E1\t1.5\tP1\tPD\t87.3115\t90.0000\t10")
        before = book.table.to_list()
        book.angle_typing = AngleTyping.DMS_PACKED
        packed = book.read(library=library()).records[0].horizontal
        book.angle_typing = AngleTyping.DECIMAL_DEGREES
        decimal = book.read(library=library()).records[0].horizontal
        assert book.table.to_list() == before
        assert packed == math.radians(87 + 31 / 60 + 15 / 3600)
        assert decimal == math.radians(87.3115)

    def test_a_job_with_a_convention_this_version_does_not_know_falls_back(self):
        job = ts.new_job()
        job.entry["angle_typing"] = "mils"
        job.entry["vertical_angle"] = "nadir"
        book = ts.TotalStationBook(job)
        assert book.angle_typing is AngleTyping.DMS
        assert book.vertical is ts.VerticalAngle.ZENITH


class TestRowsThatAreNotPointings:
    def test_a_row_holding_only_what_it_carried_is_not_emitted(self):
        """A new row starts with the station and the heights of the row above;
        until something is typed in it, it is not a pointing with its target
        missing."""
        book = typed_rd01()
        book.table.insert_row()
        last = book.table.row_count - 1
        assert book.table.cell(last, "station")
        assert last not in book.pointing_rows()
        assert book.check(library=library()).findings == ()

    def test_a_row_holding_only_a_note_is_not_emitted(self):
        book = typed_rd01()
        row = book.table.insert_row(0)
        book.table.set_cell(row, "note", "morning session")
        assert not any(book.emit().rows[1])
        assert book.check(library=library()).is_usable

    def test_blank_rows_keep_the_numbering(self):
        book = typed_rd01()
        book.table.insert_row(3)
        book.table.clear_cells([(3, column.key) for column in ts.BOOK_COLUMNS])
        emission = book.emit()
        assert not any(emission.rows[4])
        assert emission.rows[5][0]


class TestChecking:
    def test_rd01_is_clean(self):
        check = typed_rd01().check(library=library())
        assert check.is_usable
        assert (check.pointings, check.records, check.setups) == (12, 12, 3)

    def test_an_unreadable_cell_is_a_problem_and_its_row_is_kept_from_the_reader(self):
        book = typed_rd01()
        book.table.set_cell(2, "horizontal", "199.1108")
        check = book.check(library=library())
        assert [(problem.row, problem.column) for problem in check.problems] == [(2, "horizontal")]
        assert check.records == 11
        assert not check.is_usable
        # The reader was not asked about the row, so it does not say a second
        # time, and less exactly, that the row is bad.
        assert not check.blocking

    def test_a_row_the_reader_rejects_is_named_as_the_grid_numbers_it(self):
        book = typed_rd01()
        book.table.set_cell(4, "target", "")
        check = book.check(library=library())
        (finding,) = check.blocking
        assert finding.code == "missing_target"
        assert finding.context["row"] == "6", "the importer counts the heading"
        typed = ts.as_typed(finding)
        assert typed.context["row"] == "5" and typed.value == 5.0
        assert not check.is_usable

    def test_a_finding_that_names_no_row_is_left_as_it_is(self):
        book = typed_rd01()
        for row in range(book.table.row_count):
            book.table.set_cell(row, "instrument_height", "")
        findings = book.check(library=library()).findings
        assert {finding.code for finding in findings} == {"missing_instrument_height"}
        assert all(ts.as_typed(finding) is finding for finding in findings)

    def test_a_book_the_reader_cannot_read_at_all_is_a_refusal_not_a_crash(self):
        """No profile and no default precision: GeoComp does not invent a sigma."""
        check = typed_rd01().check()
        assert check.refusal is not None
        assert not check.is_usable

    def test_an_empty_book_is_not_usable(self):
        assert not ts.TotalStationBook(ts.new_job()).check(library=library()).is_usable


class TestEmissionRefusals:
    def test_a_book_with_an_unreadable_cell_is_not_emitted_in_part(self):
        book = typed_rd01()
        book.table.set_cell(0, "distance", "eleven")
        with pytest.raises(ValidationError) as refusal:
            book.emit()
        assert refusal.value.code == "validation.field_book_cells_unreadable"
        assert refusal.value.context["count"] == 1

    def test_an_empty_book(self):
        with pytest.raises(ValidationError) as refusal:
            ts.TotalStationBook(ts.new_job()).emit()
        assert refusal.value.code == "validation.field_book_empty"


class TestOpeningAReadingsDocument:
    def document(self) -> dict:
        """What ``geocomp:totalstation_import_fieldbook`` writes for RD-01."""
        result = imported_rd01()

        def reading(item) -> dict:
            return {
                "target": item.target,
                "face": item.face.value,
                "horizontal": item.horizontal.to_dict(),
                "zenith": item.zenith.to_dict(),
                "distance": item.distance.to_dict(),
                "target_height": item.target_height.to_dict(),
                "set_number": item.set_number,
                "record": item.record,
            }

        return {
            "kind": "geocomp.readings",
            "version": 1,
            "setups": [
                {
                    "station": setup.station,
                    "instrument_height": setup.instrument_height.to_dict(),
                    "pairs": [
                        {"direct": reading(pair.direct), "reverse": reading(pair.reverse)}
                        for pair in setup.pairs
                    ],
                    "singles": [reading(single) for single in setup.singles],
                }
                for setup in result.setups
            ],
        }

    @pytest.mark.parametrize("typing", list(AngleTyping))
    def test_the_document_opens_into_the_same_setups(self, typing):
        book = ts.TotalStationBook(ts.new_job())
        book.angle_typing = typing
        assert book.fill_from_readings(self.document()) == 12
        reopened = as_values(book.read(library=library()))
        original = as_values(imported_rd01())
        assert json.dumps(reopened, default=str) != "" and len(reopened) == len(original)
        for (station, height, pairs, _singles), (station_, height_, pairs_, _s) in zip(
            reopened, original, strict=True
        ):
            assert (station, height) == (station_, height_)
            for typed, imported in zip(pairs, pairs_, strict=True):
                for one, other in zip(typed, imported, strict=True):
                    assert one[:2] == other[:2]
                    assert one[2][0] == pytest.approx(other[2][0], abs=5e-10)
                    assert one[3][0] == pytest.approx(other[3][0], abs=5e-10)
                    assert one[4:] == other[4:], "distances and heights are written with every digit"

    def test_the_rows_come_in_the_order_of_the_source(self):
        book = ts.TotalStationBook(ts.new_job())
        book.fill_from_readings(self.document())
        typed = typed_rd01()
        for row in range(12):
            for key in ("station", "target", "face"):
                assert book.table.cell(row, key) == typed.table.cell(row, key)

    def test_opening_is_one_edit_that_can_be_undone(self):
        book = typed_rd01()
        before = book.table.to_list()
        book.fill_from_readings({"kind": "geocomp.readings", "setups": []})
        assert book.table.row_count == 0
        book.table.undo()
        assert book.table.to_list() == before

    def test_a_document_of_another_kind_is_refused(self):
        with pytest.raises(ValidationError) as refusal:
            ts.TotalStationBook(ts.new_job()).fill_from_readings(
                {"kind": "geocomp.reductions"}, source="x.json"
            )
        assert refusal.value.code == "validation.readings_document_not_readings"

    def test_a_malformed_document_is_refused_and_the_book_kept(self):
        book = typed_rd01()
        before = book.table.to_list()
        with pytest.raises(ValidationError) as refusal:
            book.fill_from_readings({"kind": "geocomp.readings", "setups": [{"station": "1"}]})
        assert refusal.value.code == "validation.readings_document_malformed"
        assert book.table.to_list() == before


class TestKnownPoints:
    def book(self) -> ts.TotalStationBook:
        book = typed_rd01()
        book.points.paste(0, "name", "1\t1000\t5000,5\t100\n3\t1011.508\t5000\t100.2")
        return book

    def test_the_points_are_read_in_metres(self):
        assert self.book().known_stations() == {
            "1": (1000.0, 5000.5, 100.0),
            "3": (1011.508, 5000.0, 100.2),
        }

    @pytest.mark.parametrize(
        ("edit", "code"),
        [
            ((0, "easting", "east"), "validation.known_points_unreadable"),
            ((0, "height", ""), "validation.known_point_incomplete"),
            ((1, "name", "1"), "validation.known_point_repeated"),
        ],
    )
    def test_what_is_wrong_with_them_is_refused(self, edit, code):
        book = self.book()
        book.points.set_cell(*edit)
        with pytest.raises(ValidationError) as refusal:
            book.known_stations()
        assert refusal.value.code == code

    def test_no_point_at_all_is_refused(self):
        with pytest.raises(ValidationError) as refusal:
            typed_rd01().known_stations()
        assert refusal.value.code == "validation.known_points_missing"

    def test_a_point_written_by_a_window_replaces_the_row_of_its_name(self):
        book = self.book()
        assert book.set_point("3", 1011.5, 5000.25, None, origin="map") == 1
        assert book.points.row(1) == ("3", "1011.5", "5000.25", "", "map")
        assert book.set_point("7", 1.0e-7, 2.0, 3.0) == 2
        assert book.points.cell(2, "easting") == "0.0000001"
        book.points.undo()
        assert book.points.row_count == 2

    def test_orientations_are_emitted_in_degrees(self):
        book = self.book()
        book.orientations.paste(0, "station", "2\t45 30 00")
        assert book.given_orientations() == {"2": pytest.approx(45.5, abs=1e-12)}
        book.orientations.set_cell(0, "azimuth", "")
        with pytest.raises(ValidationError) as refusal:
            book.given_orientations()
        assert refusal.value.code == "validation.orientation_incomplete"


class TestChains:
    def book(self) -> ts.TotalStationBook:
        book = typed_rd01()
        book.points.paste(0, "name", "1\t1000\t5000\t100")
        return book

    def test_each_window_runs_the_algorithms_before_it_and_its_own(self):
        book = self.book()
        assert ts.import_chain(book).algorithms == (ts.IMPORT,)
        assert ts.preprocess_chain(book).algorithms == (ts.IMPORT, ts.PREPROCESS)
        assert ts.traverse_chain(book).algorithms == (ts.IMPORT, ts.PREPROCESS, ts.TRAVERSE)
        assert ts.radiation_chain(book).algorithms == (ts.IMPORT, ts.PREPROCESS, ts.RADIATION)

    def test_each_step_reads_what_the_one_before_it_wrote(self, tmp_path):
        steps = resolve(ts.radiation_chain(self.book()), tmp_path)
        by_key = {step.key: step for step in steps}
        assert by_key["preprocess"].parameters["READINGS"] == str(by_key["import"].outputs["OUTPUT_READINGS"])
        assert by_key["radiation"].parameters["REDUCTIONS"] == str(
            by_key["preprocess"].outputs["OUTPUT_REDUCED"]
        )
        stations = json.loads((tmp_path / "radiation" / "stations.json").read_text(encoding="utf-8"))
        assert stations == {"1": [1000.0, 5000.0, 100.0]}
        assert "ORIENTATIONS" not in by_key["radiation"].parameters

    def test_the_typed_book_is_the_import_steps_source(self, tmp_path):
        book = self.book()
        (step,) = ts.import_chain(book).steps
        assert isinstance(step.parameters["SOURCE"], InputFile)
        assert step.parameters["SOURCE"].text == book.emit().csv_text()
        assert step.parameters["MAPPING"].text == book.emit().mapping_text()

    def test_only_what_the_user_set_is_passed_and_the_rest_is_the_algorithms_default(self):
        book = self.book()
        book.job.parameters(ts.WINDOW_FIELD_BOOK).update(
            {"PROFILES": "/tmp/lib.json", "SOURCE": "/etc/passwd"}
        )
        book.job.parameters(ts.WINDOW_TRAVERSE).update({"ROUTE": "1,2,3,1", "BACKSIGHT": "3", "KIND": 0})
        chain = ts.traverse_chain(book)
        imported, preprocess, traverse = chain.steps
        assert imported.parameters["PROFILES"] == "/tmp/lib.json"
        assert isinstance(imported.parameters["SOURCE"], InputFile), "a job cannot redirect the source"
        assert preprocess.parameters == {
            "PROFILES": "/tmp/lib.json",
            "READINGS": Ref("import", "OUTPUT_READINGS"),
        }
        assert traverse.parameters == {
            "ROUTE": "1,2,3,1",
            "BACKSIGHT": "3",
            "KIND": 0,
            "REDUCTIONS": Ref("preprocess", "OUTPUT_REDUCED"),
        }

    def test_the_fingerprint_follows_the_book_and_the_options(self):
        book = self.book()
        first = ts.traverse_chain(book).fingerprint()
        assert ts.traverse_chain(book).fingerprint() == first
        book.job.parameters(ts.WINDOW_TRAVERSE)["KIND"] = 2
        second = ts.traverse_chain(book).fingerprint()
        book.table.set_cell(0, "distance", "11.509")
        third = ts.traverse_chain(book).fingerprint()
        assert len({first, second, third}) == 3

    def test_a_chain_is_not_built_from_a_book_that_cannot_be_read(self):
        book = self.book()
        book.table.set_cell(0, "horizontal", "0.5")
        with pytest.raises(ValidationError):
            ts.preprocess_chain(book)


class TestPlanePoints:
    """P14b: a resection or an intersection reads points that need no height."""

    def test_a_point_without_a_height_is_placed(self):
        book = typed_rd01()
        book.points.paste(0, "name", "1\t1000\t5000,5\n3\t1011.508\t5000\t100.2")
        assert book.known_positions() == {"1": (1000.0, 5000.5), "3": (1011.508, 5000.0)}
        with pytest.raises(ValidationError) as refusal:
            book.known_stations()
        assert refusal.value.code == "validation.known_point_incomplete", "3D still needs it"

    @pytest.mark.parametrize(
        ("cells", "code"),
        [
            ("1\t1000", "validation.known_point_unplaced"),
            ("1\teast\t5000", "validation.known_points_unreadable"),
            ("1\t1\t2\n1\t3\t4", "validation.known_point_repeated"),
            ("", "validation.known_points_missing"),
        ],
    )
    def test_what_is_wrong_with_them_is_refused(self, cells, code):
        book = typed_rd01()
        book.points.paste(0, "name", cells)
        with pytest.raises(ValidationError) as refusal:
            book.known_positions()
        assert refusal.value.code == code

    def test_sightings_are_read_in_the_jobs_convention_into_degrees(self):
        book = typed_rd01(AngleTyping.DMS_PACKED)
        book.sightings.paste(0, "station", "A\t57.5924\nB\t300.0112")
        assert book.observed_azimuths() == {
            "A": pytest.approx(57.99, abs=1e-12),
            "B": pytest.approx(300.02, abs=1e-12),
        }

    @pytest.mark.parametrize(
        ("cells", "code"),
        [
            ("A\t57 59 24\nA\t300 01 12", "validation.sighting_repeated"),
            ("A", "validation.sighting_incomplete"),
            ("A\t57.99", "validation.sightings_unreadable"),
        ],
    )
    def test_what_is_wrong_with_the_sightings_is_refused(self, cells, code):
        book = typed_rd01()
        book.sightings.paste(0, "station", cells)
        with pytest.raises(ValidationError) as refusal:
            book.observed_azimuths()
        assert refusal.value.code == code

    def test_a_job_saved_before_the_sightings_opens_with_them_empty(self, tmp_path):
        book = typed_rd01()
        stored = book.job.to_dict()
        del stored["tables"][ts.SIGHTINGS]
        path = tmp_path / "older.gcjob"
        path.write_text(json.dumps(stored), encoding="utf-8")
        reopened = ts.TotalStationBook(ts.load_job(path))
        assert reopened.sightings.to_list() == []
        assert reopened.table.to_list() == book.table.to_list()


class TestTheP14bChains:
    def book(self) -> ts.TotalStationBook:
        book = typed_rd01()
        book.points.paste(0, "name", "1\t1000\t5000\t100\n2\t1010\t5000\n3\t1011.508\t5000\t100.2")
        return book

    def test_each_window_runs_what_it_declares(self):
        book = self.book()
        book.job.parameters(ts.WINDOW_RESECTION)["STATION"] = "1"
        book.sightings.paste(0, "station", "1\t45 00 00\n3\t315 00 00")
        assert ts.resection_chain(book).algorithms == (ts.IMPORT, ts.PREPROCESS, ts.RESECTION)
        assert ts.intersection_chain(book).algorithms == (ts.INTERSECTION,)
        assert ts.trig_levelling_chain(book).algorithms == (ts.IMPORT, ts.PREPROCESS, ts.TRIG_LEVELLING)
        book.points.set_cell(1, "height", "100.1")
        assert ts.network_chain(book).algorithms == (ts.IMPORT, ts.PREPROCESS, ts.NETWORK)

    def test_a_resection_is_given_the_known_points_but_the_station_it_fixes(self, tmp_path):
        book = self.book()
        with pytest.raises(ValidationError) as refusal:
            ts.resection_chain(book)
        assert refusal.value.code == "validation.resection_no_station"
        book.job.parameters(ts.WINDOW_RESECTION).update({"STATION": " 1 ", "APPROX_EASTING": 999.0})
        steps = {step.key: step for step in resolve(ts.resection_chain(book), tmp_path)}
        resection = steps["resection"]
        assert resection.parameters["STATION"] == "1"
        assert resection.parameters["APPROX_EASTING"] == 999.0
        assert resection.parameters["REDUCTIONS"] == str(steps["preprocess"].outputs["OUTPUT_REDUCED"])
        known = json.loads((tmp_path / "resection" / "known.json").read_text(encoding="utf-8"))
        assert known == {"2": [1010.0, 5000.0], "3": [1011.508, 5000.0]}

    def test_an_intersection_places_each_sighting_at_its_station(self, tmp_path):
        book = self.book()
        book.sightings.paste(0, "station", "1\t45 00 00\n3\t315 00 00")
        book.job.parameters(ts.WINDOW_INTERSECTION)["TARGET"] = "P9"
        (step,) = resolve(ts.intersection_chain(book), tmp_path)
        assert step.parameters["TARGET"] == "P9"
        assert "REDUCTIONS" not in step.parameters, "the field book is not read"
        document = json.loads((tmp_path / "intersection" / "sightings.json").read_text(encoding="utf-8"))
        assert document == {
            "1": {"position": [1000.0, 5000.0], "azimuth": 45.0},
            "3": {"position": [1011.508, 5000.0], "azimuth": 315.0},
        }

    def test_a_sighting_from_a_station_with_no_coordinates_is_refused(self):
        book = self.book()
        book.sightings.paste(0, "station", "1\t45 00 00\n9\t315 00 00")
        with pytest.raises(ValidationError) as refusal:
            ts.intersection_chain(book)
        assert refusal.value.code == "validation.sighting_station_unknown"

    def test_a_network_is_given_the_known_points_and_the_jobs_crs(self, tmp_path):
        book = self.book()
        book.points.set_cell(1, "height", "100.1")
        book.job.crs = "EPSG:31982"
        steps = {step.key: step for step in resolve(ts.network_chain(book), tmp_path)}
        network = steps["network"]
        assert network.parameters["CRS"] == "EPSG:31982"
        approximate = json.loads((tmp_path / "network" / "approximate.json").read_text(encoding="utf-8"))
        assert approximate["2"] == [1010.0, 5000.0, 100.1]
        for name, file_name in ts.NETWORK_LAYERS:
            assert network.parameters[name] == str(tmp_path / "network" / file_name)
        book.job.parameters(ts.WINDOW_NETWORK)["CRS"] = "EPSG:31983"
        assert ts.network_chain(book).steps[-1].parameters["CRS"] == "EPSG:31983"
        book.job.crs = ""
        del book.job.parameters(ts.WINDOW_NETWORK)["CRS"]
        assert "CRS" not in ts.network_chain(book).steps[-1].parameters, "the algorithm's default"

    @pytest.mark.parametrize(
        ("datum", "given"),
        [
            (None, set()),
            (ts.DATUM_INNER, set()),
            (ts.DATUM_CONSTRAINED, {"FIXED_STATIONS"}),
            (ts.DATUM_FIXED, {"FIXED_STATIONS"}),
            (ts.DATUM_MINIMUM, {"DATUM_STATIONS"}),
        ],
    )
    def test_a_network_is_given_only_the_stations_its_datum_reads(self, datum, given):
        book = self.book()
        book.points.set_cell(1, "height", "100.1")
        options = book.job.parameters(ts.WINDOW_NETWORK)
        options.update({"FIXED_STATIONS": "1,3", "DATUM_STATIONS": "1,2"})
        if datum is not None:
            options["DATUM"] = datum
        parameters = ts.network_chain(book).steps[-1].parameters
        assert {"FIXED_STATIONS", "DATUM_STATIONS"} & set(parameters) == given
        assert options["FIXED_STATIONS"] == "1,3", "kept for when that datum is chosen again"

    def test_the_trig_levelling_chain_passes_what_the_user_set(self):
        book = self.book()
        book.job.parameters(ts.WINDOW_TRIG_LEVELLING).update({"MODE": 1, "SOURCE": "/x"})
        levelling = ts.trig_levelling_chain(book).steps[-1]
        assert levelling.parameters == {"MODE": 1, "REDUCTIONS": Ref("preprocess", "OUTPUT_REDUCED")}


class TestJobs:
    def test_a_job_reopens_with_its_tables_and_conventions(self, tmp_path):
        book = typed_rd01(AngleTyping.DMS_PACKED)
        book.points.paste(0, "name", "1\t1000\t5000\t100")
        path = book.job.save(tmp_path / "rd01")
        reopened = ts.TotalStationBook(ts.load_job(path))
        assert reopened.angle_typing is AngleTyping.DMS_PACKED
        assert reopened.table.to_list() == book.table.to_list()
        assert as_values(reopened.read(library=library())) == as_values(imported_rd01())

    def test_the_job_of_another_technique_is_refused(self, tmp_path):
        job = ts.new_job()
        job.technique = "level"
        path = job.save(tmp_path / "level")
        with pytest.raises(ValidationError) as refusal:
            ts.load_job(path)
        assert refusal.value.code == "validation.job_other_technique"
