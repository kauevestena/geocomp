# SPDX-License-Identifier: GPL-2.0-or-later
"""The typed table a field-book grid edits (FR-012, FR-014).

A cell holds what was typed, an unreadable cell is a problem the table reports
rather than a keystroke it refuses, every edit can be undone, and a block copied
from a spreadsheet pastes as it comes.
"""

from __future__ import annotations

import pytest

from geocomp.core.errors import ValidationError
from geocomp.jobs import (
    AngleTyping,
    CellKind,
    Column,
    TypedTable,
    format_number,
    parse_integer,
    parse_number,
)

COLUMNS = (
    Column("station", CellKind.NAME, carries=True),
    Column("target", CellKind.NAME),
    Column("face", CellKind.CHOICE, choices=(("PD", ("1", "F1")), ("PI", ("2", "F2")))),
    Column("angle", CellKind.ANGLE),
    Column("distance", CellKind.NUMBER),
    Column("set", CellKind.INTEGER),
)


def table(*rows) -> TypedTable:
    return TypedTable(COLUMNS, rows)


class TestCells:
    def test_a_cell_holds_what_was_typed(self):
        grid = table(["1", "2", "PD", "87 31 15", "11,5080", ""])
        assert grid.cell(0, "distance") == "11,5080"
        assert grid.row(0) == ("1", "2", "PD", "87 31 15", "11,5080", "")

    def test_a_short_row_is_filled_and_a_long_one_cut(self):
        grid = table(["1"], ["1", "2", "PD", "0", "1", "1", "extra"])
        assert grid.row(0) == ("1", "", "", "", "", "")
        assert len(grid.row(1)) == len(COLUMNS)

    def test_blank_rows_are_not_filled_rows(self):
        grid = table(["1", "2", "", "", "", ""], ["", " ", "", "", "", ""], ["3", "", "", "", "", ""])
        assert grid.filled_rows() == (0, 2)
        assert grid.is_blank(1)


class TestEditing:
    def test_a_new_row_carries_what_the_column_carries(self):
        grid = table(["E1", "P1", "PD", "0", "10", ""])
        position = grid.insert_row()
        assert position == 1
        assert grid.row(1) == ("E1", "", "", "", "", "")

    def test_a_row_inserted_first_carries_nothing(self):
        grid = table(["E1", "P1", "", "", "", ""])
        grid.insert_row(0)
        assert grid.is_blank(0)

    def test_rows_are_removed_whichever_order_they_are_named_in(self):
        grid = table(["a"], ["b"], ["c"], ["d"])
        grid.remove_rows([0, 2, 99])
        assert [grid.cell(row, "station") for row in range(grid.row_count)] == ["b", "d"]

    def test_clearing_cells_is_one_edit(self):
        grid = table(["a", "b", "", "", "", ""])
        grid.clear_cells([(0, "station"), (0, "target")])
        assert grid.is_blank(0)
        grid.undo()
        assert grid.row(0)[:2] == ("a", "b")

    def test_typing_what_was_there_records_nothing(self):
        grid = table(["a"])
        revision = grid.revision
        grid.set_cell(0, "station", "a")
        assert grid.revision == revision
        assert not grid.can_undo


class TestUndo:
    def test_every_edit_can_be_undone_and_made_again(self):
        grid = table(["a"])
        grid.set_cell(0, "station", "b")
        grid.insert_row()
        grid.set_cell(1, "target", "t")
        assert grid.undo() and grid.undo() and grid.undo()
        assert grid.to_list() == [["a", "", "", "", "", ""]]
        assert not grid.undo()
        assert grid.redo() and grid.redo() and grid.redo()
        assert grid.cell(1, "target") == "t"
        assert not grid.redo()

    def test_a_new_edit_ends_the_redo_branch(self):
        grid = table(["a"])
        grid.set_cell(0, "station", "b")
        grid.undo()
        grid.set_cell(0, "station", "c")
        assert not grid.can_redo

    def test_the_revision_counts_every_change_undo_included(self):
        grid = table(["a"])
        before = grid.revision
        grid.set_cell(0, "station", "b")
        grid.undo()
        assert grid.revision == before + 2


class TestClipboard:
    def test_a_spreadsheet_block_is_pasted_as_it_comes(self):
        grid = table()
        written = grid.paste(0, "station", "1\t2\tPD\t0 00 00\t11,508\r\n1\t3\tPD\t199 06 38\t13,204\r\n")
        assert written == (2, 5)
        assert grid.row_count == 2
        assert grid.cell(1, "angle") == "199 06 38"

    def test_a_block_pasted_part_way_across_stays_inside_the_table(self):
        grid = table(["1", "", "", "", "", ""])
        grid.paste(0, "distance", "11.5\t1\tbeyond")
        assert grid.row(0) == ("1", "", "", "", "11.5", "1")

    def test_a_paste_is_one_edit(self):
        grid = table(["keep", "", "", "", "", ""])
        grid.paste(0, "station", "a\tb\nc\td")
        grid.undo()
        assert grid.to_list() == [["keep", "", "", "", "", ""]]

    def test_an_empty_clipboard_writes_nothing(self):
        grid = table()
        assert grid.paste(0, "station", "\n\n") == (0, 0)
        assert not grid.can_undo

    def test_what_is_copied_pastes_back(self):
        grid = table(["1", "2", "PD", "0 00 00", "11.508", "1"], ["1", "3", "PI", "19 06 35", "13.204", "1"])
        other = table()
        other.paste(0, "station", grid.copy())
        assert other.to_list() == grid.to_list()

    def test_part_of_the_table_is_copied_by_rows_and_columns(self):
        grid = table(["1", "2"], ["1", "3"], ["2", "1"])
        assert grid.copy(rows=[2, 0], keys=["target"]) == "2\n1"


class TestProblems:
    def test_every_unreadable_cell_is_reported_in_one_pass(self):
        grid = table(
            ["1", "2", "PD", "87 31 15", "11.508", "1"],
            ["1", "3", "XX", "87.5", "eleven", "one"],
        )
        problems = grid.problems(AngleTyping.DMS)
        assert [(problem.row, problem.column) for problem in problems] == [
            (1, "face"),
            (1, "angle"),
            (1, "distance"),
            (1, "set"),
        ]
        assert [problem.error.code for problem in problems] == [
            "validation.typed_choice_unknown",
            "validation.typed_angle_fraction_misplaced",
            "validation.typed_number_unreadable",
            "validation.typed_integer_unreadable",
        ]

    def test_an_empty_cell_is_not_a_problem(self):
        assert table(["1", "2", "", "", "", ""]).problems(AngleTyping.DMS) == ()

    def test_a_blank_row_is_not_read(self):
        assert table(["", "", "", "", "", ""]).problems(AngleTyping.DMS) == ()

    def test_a_change_of_convention_changes_what_is_a_problem(self):
        grid = table(["1", "2", "", "87.5", "", ""])
        assert grid.problems(AngleTyping.DMS)
        assert not grid.problems(AngleTyping.DECIMAL_DEGREES)


class TestChoices:
    def test_a_spelling_is_read_without_regard_to_case(self):
        face = COLUMNS[2]
        assert face.choice("pd") == "PD"
        assert face.choice(" f2 ") == "PI"

    def test_an_unknown_spelling_names_what_is_accepted(self):
        with pytest.raises(ValidationError) as refusal:
            COLUMNS[2].choice("left")
        assert refusal.value.context["expected"] == ["PD", "PI"]


class TestNumbers:
    def test_a_comma_is_a_decimal_mark(self):
        assert parse_number("11,508") == 11.508
        assert parse_number(" 11.508 ") == 11.508

    @pytest.mark.parametrize("text", ["", "abc", "1,234.5", "nan", "inf"])
    def test_what_is_not_a_number_is_refused(self, text):
        with pytest.raises(ValidationError) as refusal:
            parse_number(text)
        assert refusal.value.code == "validation.typed_number_unreadable"

    def test_whole_numbers(self):
        assert parse_integer(" 2 ") == 2
        with pytest.raises(ValidationError):
            parse_integer("2.0")

    def test_a_number_is_written_without_an_exponent(self):
        assert format_number(0.00001234, 6) == "0.000012"
