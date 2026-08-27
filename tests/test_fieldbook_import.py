# SPDX-License-Identifier: GPL-2.0-or-later
"""The field-book importer (specs/17 section 5.1: FR-160, FR-166, FR-095).

Three properties carry this module, and each has a test that fails loudly if it
stops holding:

* **A mapping is saveable and reusable.** It round-trips through a document, so
  an organisation can define its instrument's export layout once and distribute
  it.
* **Every bad record is reported and none aborts the import.** A field book with
  six problems needs one run.
* **Numbers parse the same under any locale.** A file written with comma
  decimals reads identically to one written with points.
"""

from __future__ import annotations

import csv
import json
import math

import pytest

from geocomp.core.errors import ValidationError
from geocomp.core.findings import Severity
from geocomp.core.instruments import InstrumentProfile, ProfileLibrary
from geocomp.core.instruments.stochastic import StochasticDefaults
from geocomp.core.techniques.total_station import Face
from geocomp.io import (
    AngleFormat,
    ColumnMapping,
    FieldMapping,
    infer_mapping,
    read_field_book,
    read_field_book_csv,
)
from tests import reference_rd01 as rd01

HEADER = ["R", "E", "V", "pos", "vis", "HG", "HM", "HS", "VG", "VM", "VS", "D", "hs", "hi"]


def library() -> ProfileLibrary:
    profiles = ProfileLibrary()
    profiles.add_instrument(InstrumentProfile(id="ts"))
    return profiles


def rd01_header() -> list[str]:
    with open(rd01.RAW, encoding="utf-8") as handle:
        return next(csv.reader(handle))


class TestMappingInference:
    def test_it_maps_every_column_of_rd01(self):
        header = rd01_header()
        mapping = infer_mapping(header)
        assert mapping.unrecognised(header) == ()
        assert mapping.missing_required() == ()

    def test_it_chooses_the_sexagesimal_triple_for_rd01(self):
        assert infer_mapping(rd01_header()).angle_format is AngleFormat.SEXAGESIMAL_TRIPLE

    def test_it_distinguishes_columns_that_differ_only_by_case(self):
        """RD-01's header carries both ``HS`` (the seconds of the horizontal
        angle) and ``hs`` (the target height). A case-insensitive guess maps one
        to the other's field, leaves a column unrecognised, and the import then
        fails for a reason that looks nothing like the cause."""
        mapping = infer_mapping(rd01_header())
        assert mapping.for_field("horizontal_seconds").column == "HS"
        assert mapping.for_field("target_height").column == "hs"

    def test_a_decimal_layout_is_recognised_as_such(self):
        mapping = infer_mapping(["station", "target", "H", "Z", "D"])
        assert mapping.angle_format is AngleFormat.DECIMAL_DEGREES
        assert mapping.for_field("horizontal").column == "H"

    def test_a_triple_layout_does_not_also_claim_a_decimal_column(self):
        """Both would leave the mapping supplying one field two ways."""
        mapping = infer_mapping([*HEADER, "H"])
        assert mapping.for_field("horizontal") is None
        assert mapping.for_field("horizontal_degrees") is not None

    def test_an_unknown_column_is_reported_not_discarded(self):
        header = [*rd01_header(), "operator_notes"]
        mapping = infer_mapping(header)
        assert mapping.unrecognised(header) == ("operator_notes",)

    def test_an_empty_header_yields_a_mapping_that_says_what_is_missing(self):
        mapping = infer_mapping([])
        assert set(mapping.missing_required()) == {"station", "horizontal", "zenith"}


class TestMappingDocument:
    def test_a_mapping_round_trips_through_json(self):
        """FR-160's whole point: saved by name, reused, distributed."""
        mapping = infer_mapping(rd01_header(), name="Leica TS15 export")
        payload = json.loads(json.dumps(mapping.to_dict()))
        assert FieldMapping.from_dict(payload).to_dict() == mapping.to_dict()

    def test_a_mapping_needs_a_name(self):
        with pytest.raises(ValidationError) as caught:
            FieldMapping(name="  ")
        assert caught.value.code == "validation.mapping_without_name"

    def test_a_field_cannot_be_mapped_twice(self):
        with pytest.raises(ValidationError) as caught:
            FieldMapping(
                name="m",
                columns=(
                    ColumnMapping("distance", column="D1"),
                    ColumnMapping("distance", column="D2"),
                ),
            )
        assert caught.value.code == "validation.duplicate_mapped_field"

    def test_a_column_mapping_needs_a_source(self):
        with pytest.raises(ValidationError) as caught:
            ColumnMapping("distance")
        assert caught.value.code == "validation.mapping_without_source"

    def test_an_unknown_field_is_refused(self):
        with pytest.raises(ValidationError) as caught:
            ColumnMapping("wingspan", column="W")
        assert caught.value.code == "validation.unknown_mapping_field"

    def test_a_constant_supplies_a_value_for_every_row(self):
        """Instrument height written once on the cover of a field book rather
        than on every line is the routine case."""
        mapping = FieldMapping(
            name="m",
            angle_format=AngleFormat.DECIMAL_DEGREES,
            columns=(
                ColumnMapping("station", column="E"),
                ColumnMapping("target", column="V"),
                ColumnMapping("horizontal", column="H"),
                ColumnMapping("zenith", column="Z"),
                ColumnMapping("instrument_height", constant="1.550"),
            ),
        )
        result = read_field_book(
            [["E", "V", "H", "Z"], ["A", "B", "0", "90"]], mapping, library=library()
        )
        assert result.setups[0].instrument_height.value == pytest.approx(1.550)


class TestLocaleIndependentNumbers:
    """FR-095: a file is portable between users whatever their locale."""

    @staticmethod
    def _mapping(separator: str) -> FieldMapping:
        return FieldMapping(
            name="m",
            angle_format=AngleFormat.DECIMAL_DEGREES,
            decimal_separator=separator,
            columns=(
                ColumnMapping("station", column="E"),
                ColumnMapping("target", column="V"),
                ColumnMapping("horizontal", column="H"),
                ColumnMapping("zenith", column="Z"),
                ColumnMapping("distance", column="D"),
            ),
        )

    def test_a_comma_decimal_file_reads_like_a_point_decimal_one(self):
        comma = read_field_book(
            [["E", "V", "H", "Z", "D"], ["A", "B", "0", "90", "11,508"]],
            self._mapping(","),
            library=library(),
        )
        point = read_field_book(
            [["E", "V", "H", "Z", "D"], ["A", "B", "0", "90", "11.508"]],
            self._mapping("."),
            library=library(),
        )
        assert comma.records[0].distance == pytest.approx(point.records[0].distance)

    def test_auto_decides_per_value(self):
        mapping = self._mapping("auto")
        assert mapping.parse_number("11,508") == pytest.approx(11.508)
        assert mapping.parse_number("11.508") == pytest.approx(11.508)

    def test_a_source_unit_is_converted_once_at_the_boundary(self):
        mapping = FieldMapping(
            name="m",
            angle_format=AngleFormat.DECIMAL_DEGREES,
            columns=(
                ColumnMapping("station", column="E"),
                ColumnMapping("target", column="V"),
                ColumnMapping("horizontal", column="H"),
                ColumnMapping("zenith", column="Z"),
                ColumnMapping("distance", column="D", unit="ft"),
            ),
        )
        result = read_field_book(
            [["E", "V", "H", "Z", "D"], ["A", "B", "0", "90", "100"]],
            mapping,
            library=library(),
        )
        assert result.records[0].distance == pytest.approx(30.48)

    def test_an_unknown_decimal_separator_is_refused(self):
        with pytest.raises(ValidationError) as caught:
            FieldMapping(name="m", decimal_separator=";")
        assert caught.value.code == "validation.unknown_decimal_separator"


class TestReadingRd01:
    @pytest.fixture(scope="class")
    def result(self):
        return read_field_book_csv(rd01.RAW, infer_mapping(rd01_header()), library=library())

    def test_every_row_is_read(self, result):
        assert result.row_count == 12
        assert len(result.records) == 12
        assert result.is_clean

    def test_the_three_setups_are_recovered_with_their_face_pairs(self, result):
        setups = {setup.station: setup for setup in result.setups}
        assert set(setups) == {"1", "2", "3"}
        for setup in setups.values():
            assert len(setup.pairs) == 2
            assert not setup.singles

    def test_the_sighted_column_decides_which_station_was_targeted(self, result):
        """RD-01 gives a backsight and a foresight per row and a ``vis`` column
        saying which of the two that row reads."""
        setups = {setup.station: setup for setup in result.setups}
        assert {pair.target for pair in setups["1"].pairs} == {"2", "3"}

    def test_the_instrument_height_comes_from_the_rows(self, result):
        setups = {setup.station: setup for setup in result.setups}
        assert setups["1"].instrument_height.value == pytest.approx(1.495)
        assert setups["2"].instrument_height.value == pytest.approx(1.533)

    def test_the_angles_are_radians_composed_from_the_triple(self, result):
        first = result.records[0]
        assert math.degrees(first.horizontal) == pytest.approx(0.0)
        assert math.degrees(first.zenith) == pytest.approx(90 + 59 / 60 + 48 / 3600)

    def test_every_reading_carries_an_uncertainty(self, result):
        """Attached here, at the boundary. A reading that reached the domain
        model without one could still find its way into an adjustment."""
        for setup in result.setups:
            for pair in setup.pairs:
                for reading in (pair.direct, pair.reverse):
                    assert reading.horizontal.std_dev > 0.0
                    assert reading.zenith.std_dev > 0.0
                    assert reading.distance.std_dev > 0.0

    def test_the_imported_setups_reduce_to_the_same_values_as_the_hand_built_ones(
        self, result
    ):
        """The importer and the reference module must agree, or one of them is
        wrong and the reference tests would not notice."""
        from geocomp.core.techniques.total_station import preprocess_setup

        profiles = rd01.library()
        imported = {setup.station: setup for setup in result.setups}
        for station, built in rd01.setups().items():
            from_file = preprocess_setup(imported[station], library())
            from_code = preprocess_setup(built, profiles)
            by_target = {p.target: p for p in from_code.pointings}
            for pointing in from_file.pointings:
                expected = by_target[pointing.target]
                assert pointing.reduction.horizontal.value == pytest.approx(
                    expected.reduction.horizontal.value, abs=1e-12
                )
                assert pointing.reduction.zenith.value == pytest.approx(
                    expected.reduction.zenith.value, abs=1e-12
                )

    def test_without_a_stochastic_model_the_import_refuses(self):
        """GeoComp does not invent a sigma, and the boundary is where that has
        to hold: a reading imported without one is a reading that could reach an
        adjustment unweighted."""
        with pytest.raises(ValidationError) as caught:
            read_field_book_csv(rd01.RAW, infer_mapping(rd01_header()))
        assert caught.value.code == "validation.missing_stochastic_model"

    def test_type_defaults_are_enough_when_there_is_no_instrument(self):
        defaults = (
            StochasticDefaults()
            .with_default("direction", 1e-5)
            .with_default("zenith_angle", 1e-5)
            .with_default("slope_distance", 0.003)
            .with_default("target_height", 0.001)
            .with_default("instrument_height", 0.001)
        )
        result = read_field_book_csv(
            rd01.RAW, infer_mapping(rd01_header()), defaults=defaults
        )
        assert len(result.setups) == 3


class TestPerRecordErrors:
    """FR-166: report every problem, abort on none."""

    @staticmethod
    def _mapping() -> FieldMapping:
        return FieldMapping(
            name="m",
            angle_format=AngleFormat.DECIMAL_DEGREES,
            columns=(
                ColumnMapping("station", column="E"),
                ColumnMapping("target", column="V"),
                ColumnMapping("horizontal", column="H"),
                ColumnMapping("zenith", column="Z"),
                ColumnMapping("distance", column="D"),
            ),
        )

    def test_six_bad_rows_produce_six_findings_in_one_run(self):
        rows = [["E", "V", "H", "Z", "D"]]
        rows.extend([["A", "B", "not a number", "90", "10"] for _ in range(6)])
        rows.append(["A", "C", "12", "90", "10"])

        result = read_field_book(rows, self._mapping(), library=library())
        blocking = [f for f in result.findings if f.severity is Severity.BLOCKING]
        assert len(blocking) == 6
        assert len(result.records) == 1, "the good row still came through"
        assert result.rejected_rows == (2, 3, 4, 5, 6, 7)

    def test_each_finding_names_its_row(self):
        rows = [["E", "V", "H", "Z", "D"], ["A", "B", "0", "90", "10"], ["", "C", "0", "90", "10"]]
        result = read_field_book(rows, self._mapping(), library=library())
        blocking = [f for f in result.findings if f.severity is Severity.BLOCKING]
        assert len(blocking) == 1
        assert "row 3" in blocking[0].message
        assert blocking[0].code == "missing_station"

    def test_a_blank_row_is_skipped_silently(self):
        """Trailing blank lines are an artefact of every export, not an error."""
        rows = [["E", "V", "H", "Z", "D"], ["A", "B", "0", "90", "10"], ["", "", "", "", ""]]
        result = read_field_book(rows, self._mapping(), library=library())
        assert result.is_clean
        assert len(result.records) == 1

    def test_a_mapping_that_cannot_work_raises_rather_than_reporting(self):
        """A missing required field is a problem with the import definition, not
        with the data, and reporting it per row would repeat it a thousand
        times."""
        mapping = FieldMapping(
            name="m",
            angle_format=AngleFormat.DECIMAL_DEGREES,
            columns=(ColumnMapping("station", column="E"),),
        )
        with pytest.raises(ValidationError) as caught:
            read_field_book([["E"], ["A"]], mapping, library=library())
        assert caught.value.code == "validation.mapping_missing_required_fields"

    def test_minutes_above_sixty_are_caught_rather_than_silently_folded(self):
        """A decimal angle in a triple-format column reads as 12 degrees 50
        minutes when it means 12.5 degrees -- and produces a plausible wrong
        answer, which is exactly the class of error worth refusing."""
        mapping = FieldMapping(
            name="m",
            columns=(
                ColumnMapping("station", column="E"),
                ColumnMapping("target", column="V"),
                ColumnMapping("horizontal_degrees", column="HG"),
                ColumnMapping("horizontal_minutes", column="HM"),
                ColumnMapping("horizontal_seconds", column="HS"),
                ColumnMapping("zenith_degrees", column="VG"),
                ColumnMapping("zenith_minutes", column="VM"),
                ColumnMapping("zenith_seconds", column="VS"),
            ),
        )
        rows = [
            ["E", "V", "HG", "HM", "HS", "VG", "VM", "VS"],
            ["A", "B", "12", "75", "0", "90", "0", "0"],
        ]
        result = read_field_book(rows, mapping, library=library())
        assert "sexagesimal_out_of_range" in {f.code for f in result.findings}

    def test_an_unknown_face_token_is_reported_with_what_was_expected(self):
        mapping = FieldMapping(
            name="m",
            angle_format=AngleFormat.DECIMAL_DEGREES,
            columns=(
                ColumnMapping("station", column="E"),
                ColumnMapping("target", column="V"),
                ColumnMapping("face", column="pos"),
                ColumnMapping("horizontal", column="H"),
                ColumnMapping("zenith", column="Z"),
            ),
        )
        rows = [["E", "V", "pos", "H", "Z"], ["A", "B", "F1", "0", "90"]]
        result = read_field_book(rows, mapping, library=library())
        unknown = [f for f in result.findings if f.code == "unknown_face_value"]
        assert len(unknown) == 1
        assert "PD" in unknown[0].message

    def test_the_face_tokens_are_configurable(self):
        """Because a Leica export says F1 and F2 where RD-01 says PD and PI."""
        mapping = FieldMapping(
            name="m",
            angle_format=AngleFormat.DECIMAL_DEGREES,
            face_values={"F1": "direct", "F2": "reverse"},
            columns=(
                ColumnMapping("station", column="E"),
                ColumnMapping("target", column="V"),
                ColumnMapping("face", column="pos"),
                ColumnMapping("horizontal", column="H"),
                ColumnMapping("zenith", column="Z"),
            ),
        )
        rows = [
            ["E", "V", "pos", "H", "Z"],
            ["A", "B", "F1", "0", "90"],
            ["A", "B", "F2", "180", "270"],
        ]
        result = read_field_book(rows, mapping, library=library())
        assert result.is_clean
        assert len(result.setups[0].pairs) == 1

    def test_a_pointing_with_no_opposite_face_becomes_a_single(self):
        """Still a measurement, just one the instrument's constants must correct
        rather than the pair cancelling them."""
        mapping = self._mapping()
        rows = [["E", "V", "H", "Z", "D"], ["A", "B", "0", "90", "10"]]
        result = read_field_book(rows, mapping, library=library())
        assert len(result.setups[0].singles) == 1
        assert result.setups[0].singles[0].face is Face.DIRECT

    def test_a_repeated_face_in_one_set_is_reported_and_the_first_kept(self):
        mapping = FieldMapping(
            name="m",
            angle_format=AngleFormat.DECIMAL_DEGREES,
            columns=(
                ColumnMapping("station", column="E"),
                ColumnMapping("target", column="V"),
                ColumnMapping("face", column="pos"),
                ColumnMapping("horizontal", column="H"),
                ColumnMapping("zenith", column="Z"),
            ),
        )
        rows = [
            ["E", "V", "pos", "H", "Z"],
            ["A", "B", "PD", "0", "90"],
            ["A", "B", "PD", "0.001", "90"],
        ]
        result = read_field_book(rows, mapping, library=library())
        repeated = [f for f in result.findings if f.code == "repeated_face"]
        assert len(repeated) == 1
        assert repeated[0].severity is Severity.WARNING
        assert "row 3" in repeated[0].message
        assert len(result.setups[0].singles) == 1

    def test_a_missing_instrument_height_is_a_warning_not_a_refusal(self):
        """Zero is right for a leap-frog setup, and wrong everywhere else, so it
        is assumed and said rather than either refused or hidden."""
        result = read_field_book(
            [["E", "V", "H", "Z", "D"], ["A", "B", "0", "90", "10"]],
            self._mapping(),
            library=library(),
        )
        assert "missing_instrument_height" in {f.code for f in result.findings}
        assert all(f.severity is not Severity.BLOCKING for f in result.findings)

    def test_unrecognised_columns_are_carried_on_the_record(self):
        """Never silently discarded: a column GeoComp does not understand may
        still be the one the surveyor needs beside the observation."""
        rows = [
            ["E", "V", "H", "Z", "D", "operator"],
            ["A", "B", "0", "90", "10", "KV"],
        ]
        result = read_field_book(rows, self._mapping(), library=library())
        assert result.unrecognised_columns == ("operator",)
        assert result.records[0].extra == {"operator": "KV"}


class TestSkipRowsAndOtherLayouts:
    def test_a_title_block_before_the_header_is_skipped(self):
        mapping = FieldMapping(
            name="m",
            angle_format=AngleFormat.DECIMAL_DEGREES,
            skip_rows=2,
            columns=(
                ColumnMapping("station", column="E"),
                ColumnMapping("target", column="V"),
                ColumnMapping("horizontal", column="H"),
                ColumnMapping("zenith", column="Z"),
            ),
        )
        rows = [
            ["Levantamento topografico"],
            ["Data: 2026-08-27"],
            ["E", "V", "H", "Z"],
            ["A", "B", "0", "90"],
        ]
        result = read_field_book(rows, mapping, library=library())
        assert result.is_clean
        assert len(result.records) == 1

    def test_a_sexagesimal_text_column_is_parsed(self):
        mapping = FieldMapping(
            name="m",
            angle_format=AngleFormat.SEXAGESIMAL_TEXT,
            columns=(
                ColumnMapping("station", column="E"),
                ColumnMapping("target", column="V"),
                ColumnMapping("horizontal", column="H"),
                ColumnMapping("zenith", column="Z"),
            ),
        )
        rows = [["E", "V", "H", "Z"], ["A", "B", "179 59 56", "269 00 09"]]
        result = read_field_book(rows, mapping, library=library())
        assert result.is_clean
        assert math.degrees(result.records[0].horizontal) == pytest.approx(
            179 + 59 / 60 + 56 / 3600
        )

    def test_a_gon_column_is_converted(self):
        mapping = FieldMapping(
            name="m",
            angle_format=AngleFormat.GON,
            columns=(
                ColumnMapping("station", column="E"),
                ColumnMapping("target", column="V"),
                ColumnMapping("horizontal", column="H"),
                ColumnMapping("zenith", column="Z"),
            ),
        )
        rows = [["E", "V", "H", "Z"], ["A", "B", "100", "100"]]
        result = read_field_book(rows, mapping, library=library())
        assert math.degrees(result.records[0].horizontal) == pytest.approx(90.0)

    def test_a_missing_file_is_refused_by_name(self, tmp_path):
        with pytest.raises(ValidationError) as caught:
            read_field_book_csv(tmp_path / "nope.csv", infer_mapping(HEADER))
        assert caught.value.code == "validation.field_book_not_found"

    def test_a_byte_order_mark_does_not_break_the_first_column(self, tmp_path):
        """Instrument software and spreadsheet exporters routinely emit one, and
        it turns the first mapped column into an unrecognised one."""
        path = tmp_path / "bom.csv"
        path.write_text("E,V,H,Z\nA,B,0,90\n", encoding="utf-8-sig")
        mapping = FieldMapping(
            name="m",
            angle_format=AngleFormat.DECIMAL_DEGREES,
            columns=(
                ColumnMapping("station", column="E"),
                ColumnMapping("target", column="V"),
                ColumnMapping("horizontal", column="H"),
                ColumnMapping("zenith", column="Z"),
            ),
        )
        result = read_field_book_csv(path, mapping, library=library())
        assert result.is_clean
        assert result.unrecognised_columns == ()
