# SPDX-License-Identifier: GPL-2.0-or-later
"""Reading a levelling field book (FR-160, FR-166, FR-095).

``specs/10-module-levelling.md`` section 6. Two layouts, three-wire readings,
and the discipline the total-station importer already holds to: every bad record
is reported and none aborts the import, numbers are locale-independent, and a
reading with no available sigma is refused rather than invented.
"""

from __future__ import annotations

import math

import pytest

import tests.reference_levelling as rd
from geocomp.core.errors import ValidationError
from geocomp.core.instruments import ProfileLibrary, StochasticDefaults
from geocomp.core.instruments.stochastic import STAFF_READING
from geocomp.core.techniques.levelling import reduce_line
from geocomp.core.uncertainty import Strategy
from geocomp.io import ColumnMapping, FieldMapping
from geocomp.io.levelbook import Layout, LevelMapping, read_level_book, read_level_book_csv

THREE_WIRE_ROWS = [
    ["setup", "point", "kind", "up", "mid", "low"],
    ["1", "BM1", "BS", "1.583", "1.421", "1.259"],
    ["1", "TP1", "FS", "1.264", "1.102", "0.940"],
    ["1", "S1", "IS", "2.104", "1.942", "1.780"],
    ["2", "TP1", "BS", "1.700", "1.540", "1.380"],
    ["2", "BM2", "FS", "0.912", "0.752", "0.592"],
]

THREE_WIRE_MAPPING = LevelMapping(
    name="three-wire",
    columns=(
        ColumnMapping("setup", "setup"),
        ColumnMapping("station", "point"),
        ColumnMapping("sight", "kind"),
        ColumnMapping("upper", "up"),
        ColumnMapping("middle", "mid"),
        ColumnMapping("lower", "low"),
    ),
)

SETUP_ROWS = [
    ["linha", "de", "para", "re", "vante", "dist_re", "dist_vante"],
    ["L1", "BM1", "TP1", "1,421", "1,102", "32,4", "32,6"],
    ["L1", "TP1", "BM2", "1,540", "0,752", "30,1", "29,9"],
]

SETUP_MAPPING = LevelMapping(
    name="pt-BR spreadsheet",
    decimal_separator=",",
    columns=(
        ColumnMapping("line", "linha"),
        ColumnMapping("backsight_station", "de"),
        ColumnMapping("foresight_station", "para"),
        ColumnMapping("backsight_reading", "re"),
        ColumnMapping("foresight_reading", "vante"),
        ColumnMapping("backsight_distance", "dist_re"),
        ColumnMapping("foresight_distance", "dist_vante"),
    ),
)


class TestTheLayoutIsWorkedOutNotAskedFor:
    def test_a_row_per_reading_book_is_recognised(self):
        assert THREE_WIRE_MAPPING.layout is Layout.READING

    def test_a_row_per_setup_book_is_recognised(self):
        assert SETUP_MAPPING.layout is Layout.SETUP

    def test_naming_columns_of_both_layouts_is_refused(self):
        """A mapping that declares one layout while naming the other's columns
        produces wrong data quietly, which is the failure worth refusing."""
        mapping = LevelMapping(
            name="both",
            columns=(
                ColumnMapping("station", "a"),
                ColumnMapping("backsight_station", "b"),
            ),
        )
        with pytest.raises(ValidationError) as caught:
            mapping.layout  # noqa: B018 - the property is what raises
        assert caught.value.code == "validation.ambiguous_level_layout"

    def test_a_mapping_naming_neither_is_refused(self):
        mapping = LevelMapping(name="thin", columns=(ColumnMapping("reading", "r"),))
        with pytest.raises(ValidationError) as caught:
            mapping.layout  # noqa: B018
        assert caught.value.code == "validation.unrecognised_level_layout"

    def test_an_incomplete_mapping_names_what_is_missing(self):
        mapping = LevelMapping(
            name="partial",
            columns=(ColumnMapping("station", "point"), ColumnMapping("sight", "kind")),
        )
        assert "setup" in mapping.missing_required()
        assert "reading" in mapping.missing_required()
        with pytest.raises(ValidationError) as caught:
            read_level_book(THREE_WIRE_ROWS, mapping, level=rd.profile())
        assert caught.value.code == "validation.level_mapping_incomplete"

    def test_three_wires_count_as_a_reading(self):
        assert THREE_WIRE_MAPPING.missing_required() == ()

    def test_a_levelling_field_name_is_checked_against_its_own_vocabulary(self):
        with pytest.raises(ValidationError) as caught:
            LevelMapping(name="m", columns=(ColumnMapping("zenith", "Z"),))
        assert caught.value.code == "validation.unknown_level_mapping_field"

    def test_a_total_station_field_name_is_checked_against_its_own(self):
        """The two vocabularies are separate on purpose: a levelling book has no
        zenith angles and a total-station book has no stadia wires."""
        with pytest.raises(ValidationError) as caught:
            FieldMapping(name="m", columns=(ColumnMapping("upper", "U"),))
        assert caught.value.code == "validation.unknown_mapping_field"


class TestReadingAThreeWireBook:
    def test_the_setups_and_the_line_are_assembled(self):
        result = read_level_book(THREE_WIRE_ROWS, THREE_WIRE_MAPPING, level=rd.profile())
        assert [setup.id for setup in result.setups] == ["1", "2"]
        assert len(result.lines) == 1
        assert (result.lines[0].from_station, result.lines[0].to_station) == ("BM1", "BM2")
        assert result.is_clean

    def test_the_sight_distance_comes_from_the_wires(self):
        """Which is what makes the balance check possible on a book that never
        recorded a distance (specs/10 section 6)."""
        result = read_level_book(THREE_WIRE_ROWS, THREE_WIRE_MAPPING, level=rd.profile())
        assert result.setups[0].backsight.distance.value == pytest.approx(32.4)
        assert result.setups[0].has_distances

    def test_the_reading_is_the_mean_of_the_three(self):
        result = read_level_book(THREE_WIRE_ROWS, THREE_WIRE_MAPPING, level=rd.profile())
        reading = result.setups[0].backsight.reading
        assert reading.value == pytest.approx(1.421)
        assert reading.std_dev == pytest.approx(rd.SIGMA_READING / math.sqrt(3.0))

    def test_the_intermediate_sight_becomes_a_second_foresight(self):
        result = read_level_book(THREE_WIRE_ROWS, THREE_WIRE_MAPPING, level=rd.profile())
        assert [sight.station for sight in result.setups[0].foresights] == ["TP1", "S1"]
        assert result.setups[0].is_extreme_sights

    def test_the_line_reduces_to_the_expected_difference(self):
        result = read_level_book(THREE_WIRE_ROWS, THREE_WIRE_MAPPING, level=rd.profile())
        reduction = reduce_line(result.lines[0], rd.profile())
        assert reduction.height_difference.value == pytest.approx(
            (1.421 - 1.102) + (1.540 - 0.752)
        )
        assert [shot.to_station for shot in reduction.side_shots] == ["S1"]

    def test_a_misread_wire_is_a_finding_and_the_import_continues(self):
        rows = [row[:] for row in THREE_WIRE_ROWS]
        rows[2][4] = "1.112"  # middle wire out by 10 mm
        result = read_level_book(rows, THREE_WIRE_MAPPING, level=rd.profile())
        assert "three_wire_half_sum" in {finding.code for finding in result.findings}
        assert len(result.setups) == 2

    def test_wires_out_of_order_are_reported_by_row(self):
        rows = [row[:] for row in THREE_WIRE_ROWS]
        rows[1][3], rows[1][5] = rows[1][5], rows[1][3]
        result = read_level_book(rows, THREE_WIRE_MAPPING, level=rd.profile())
        assert 2 in result.rejected_rows
        assert not result.is_clean


class TestReadingARowPerSetupBook:
    def test_a_comma_decimal_book_reads_identically(self):
        """FR-095: converted once, at the boundary."""
        result = read_level_book(SETUP_ROWS, SETUP_MAPPING, level=rd.profile())
        assert result.setups[0].backsight.reading.value == pytest.approx(1.421)
        assert result.setups[0].backsight.distance.value == pytest.approx(32.4)

    def test_the_imbalance_is_available(self):
        result = read_level_book(SETUP_ROWS, SETUP_MAPPING, level=rd.profile())
        assert result.setups[0].imbalance() == pytest.approx(-0.2)

    def test_the_line_name_groups_the_setups(self):
        result = read_level_book(SETUP_ROWS, SETUP_MAPPING, level=rd.profile())
        assert [line.id for line in result.lines] == ["L1"]
        assert result.lines[0].setup_count == 2

    def test_a_setup_id_is_generated_when_the_book_names_none(self):
        result = read_level_book(SETUP_ROWS, SETUP_MAPPING, level=rd.profile())
        assert all(setup.id.startswith("setup-") for setup in result.setups)


class TestNothingIsInvented:
    def test_a_reading_with_no_available_sigma_is_refused(self):
        """Reported as a blocking finding rather than raised, per FR-166 -- the
        import still tells you about every other row."""
        result = read_level_book(SETUP_ROWS, SETUP_MAPPING)
        assert not result.is_clean
        assert "missing_stochastic_model" in {finding.code for finding in result.findings}
        assert result.setups == ()

    def test_a_type_default_satisfies_it(self):
        result = read_level_book(
            SETUP_ROWS,
            SETUP_MAPPING,
            defaults=StochasticDefaults().with_default(STAFF_READING, 0.0008),
        )
        assert result.is_clean
        assert result.setups[0].backsight.reading.std_dev == pytest.approx(0.0008)

    def test_a_sight_distance_falls_back_to_its_recorded_precision(self):
        """The one place a sigma may come from the digits themselves.

        A sight distance's uncertainty reaches the answer only multiplied by a
        collimation of order 1e-4, and the digits an observer wrote are real
        information. specs/05 section 2.3.
        """
        result = read_level_book(
            SETUP_ROWS,
            SETUP_MAPPING,
            defaults=StochasticDefaults().with_default(STAFF_READING, 0.0008),
        )
        distance = result.setups[0].backsight.distance
        assert distance.value == pytest.approx(32.4)
        assert distance.std_dev == pytest.approx(0.05 / math.sqrt(3.0))
        assert Strategy.RECORDED_PRECISION in distance.strategies

    def test_a_staff_reading_never_falls_back_that_way(self):
        """Its sigma becomes an adjustment weight, so it still refuses."""
        result = read_level_book(SETUP_ROWS, SETUP_MAPPING)
        assert "missing_stochastic_model" in {finding.code for finding in result.findings}

    def test_more_digits_means_a_smaller_implied_sigma(self):
        rows = [row[:] for row in SETUP_ROWS]
        rows[1][5] = "32,400"
        result = read_level_book(
            rows,
            SETUP_MAPPING,
            defaults=StochasticDefaults().with_default(STAFF_READING, 0.0008),
        )
        assert result.setups[0].backsight.distance.std_dev == pytest.approx(
            0.0005 / math.sqrt(3.0)
        )

    def test_the_level_profile_wins_over_the_mapping_stadia_factor(self):
        """An instrument constant belongs to the instrument."""
        mapping = LevelMapping(
            name="wrong-factor",
            stadia_factor=50.0,
            columns=THREE_WIRE_MAPPING.columns,
        )
        result = read_level_book(THREE_WIRE_ROWS, mapping, level=rd.profile())
        assert result.setups[0].backsight.distance.value == pytest.approx(32.4)


class TestEveryProblemIsReported:
    def test_several_bad_rows_produce_several_findings_in_one_run(self):
        rows = [
            ["setup", "point", "kind", "reading"],
            ["1", "BM1", "BS", "1.421"],
            ["1", "TP1", "WHAT", "1.102"],
            ["2", "TP1", "BS", "not a number"],
            ["3", "TP1", "BS", "1.540"],
        ]
        mapping = LevelMapping(
            name="plain",
            columns=(
                ColumnMapping("setup", "setup"),
                ColumnMapping("station", "point"),
                ColumnMapping("sight", "kind"),
                ColumnMapping("reading", "reading"),
            ),
        )
        result = read_level_book(rows, mapping, level=rd.profile())
        codes = {finding.code for finding in result.findings}
        assert "level_unknown_sight" in codes
        assert "level_unreadable_number" in codes
        assert "level_setup_malformed" in codes
        assert len(result.rejected_rows) >= 2

    def test_unrecognised_columns_are_reported_not_discarded(self):
        rows = [row[:] for row in THREE_WIRE_ROWS]
        rows[0].append("observador")
        for row in rows[1:]:
            row.append("KV")
        result = read_level_book(rows, THREE_WIRE_MAPPING, level=rd.profile())
        assert result.unrecognised_columns == ("observador",)

    def test_the_row_count_lets_a_ui_say_how_many_of_how_many(self):
        result = read_level_book(THREE_WIRE_ROWS, THREE_WIRE_MAPPING, level=rd.profile())
        assert result.row_count == 5


class TestTheCsvPath:
    def test_a_file_is_read_and_a_missing_one_is_refused(self, tmp_path):
        path = tmp_path / "book.csv"
        path.write_text(
            "\n".join(",".join(row) for row in THREE_WIRE_ROWS) + "\n", encoding="utf-8"
        )
        result = read_level_book_csv(path, THREE_WIRE_MAPPING, level=rd.profile())
        assert [setup.id for setup in result.setups] == ["1", "2"]

        with pytest.raises(ValidationError) as caught:
            read_level_book_csv(tmp_path / "absent.csv", THREE_WIRE_MAPPING)
        assert caught.value.code == "validation.field_book_not_found"

    def test_a_byte_order_mark_does_not_hide_the_first_column(self, tmp_path):
        path = tmp_path / "bom.csv"
        path.write_text(
            "\n".join(",".join(row) for row in THREE_WIRE_ROWS) + "\n", encoding="utf-8-sig"
        )
        result = read_level_book_csv(path, THREE_WIRE_MAPPING, level=rd.profile())
        assert result.unrecognised_columns == ()


class TestTheMappingIsSaveable:
    def test_a_round_trip_preserves_everything(self):
        restored = LevelMapping.from_dict(THREE_WIRE_MAPPING.to_dict())
        assert restored == THREE_WIRE_MAPPING

    def test_the_library_resolves_the_level_named_on_a_row(self):
        library = ProfileLibrary()
        library.add_level(rd.profile())
        rows = [row[:] for row in THREE_WIRE_ROWS]
        rows[0].append("instrumento")
        for row in rows[1:]:
            row.append("rd04-level")
        mapping = LevelMapping(
            name="with-level",
            columns=(*THREE_WIRE_MAPPING.columns, ColumnMapping("level_id", "instrumento")),
        )
        result = read_level_book(rows, mapping, library=library)
        assert result.setups[0].level_id == "rd04-level"
        assert result.is_clean
