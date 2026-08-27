# SPDX-License-Identifier: GPL-2.0-or-later
"""The state behind the field-mapping dialog (FR-160).

The dialog itself is a view; every decision it makes is made here, so every
decision is tested here rather than only in a QGIS runtime.

A mapping dialog is where a wrong answer is both expensive and invisible.
Assigning ``hs`` to the horizontal seconds instead of the target height gives a
file that imports cleanly and means something else entirely -- and RD-01's own
header carries both ``HS`` and ``hs``. So the tests are mostly about what the
editor refuses and what it reports, not about what it stores.
"""

from __future__ import annotations

import csv

import pytest

from geocomp.core.findings import Severity
from geocomp.io.mapping import AngleFormat, FieldMapping
from geocomp.io.mapping_editor import MappingEditor, PreviewTable, field_is_required
from tests import reference_rd01 as rd01


def _rd01_preview() -> PreviewTable:
    with open(rd01.RAW, encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))
    return PreviewTable(header=tuple(rows[0]), rows=tuple(tuple(row) for row in rows[1:6]))


@pytest.fixture
def editor() -> MappingEditor:
    return MappingEditor(_rd01_preview())


class TestItStartsFromWhatTheHeaderSays:
    def test_a_recognised_header_arrives_already_mapped(self, editor):
        """A dialog that opened empty would make the common case -- a header
        GeoComp understands -- the most laborious one."""
        assert editor.is_usable
        assert editor.findings() == ()

    def test_case_alone_distinguishes_two_different_fields(self, editor):
        """RD-01 carries HS, the seconds of the horizontal angle, and hs, the
        target height. They differ only by case and mean entirely different
        things."""
        assert editor.column_for("horizontal_seconds") == "HS"
        assert editor.column_for("target_height") == "hs"

    def test_the_angle_format_comes_from_the_header_too(self, editor):
        assert editor.angle_format is AngleFormat.SEXAGESIMAL_TRIPLE

    def test_an_unrecognised_header_leaves_the_required_fields_to_the_user(self):
        editor = MappingEditor(PreviewTable(header=("a", "b", "c"), rows=()))
        codes = {finding.code for finding in editor.findings()}
        assert "required_field_unmapped" in codes
        assert not editor.is_usable


class TestWhatItRefusesToLetPass:
    def test_a_required_field_left_unmapped_blocks(self, editor):
        editor.assign("station", "")
        blocking = [f for f in editor.findings() if f.code == "required_field_unmapped"]
        assert [f.observations for f in blocking] == [("station",)]
        assert not editor.is_usable

    def test_one_column_assigned_to_two_fields_blocks_and_names_both(self, editor):
        """Which of the two the user meant is not something the editor can
        know, so it says so rather than picking."""
        editor.assign("temperature", "hs")
        finding = next(f for f in editor.findings() if f.code == "column_assigned_twice")
        assert finding.severity is Severity.BLOCKING
        assert finding.observations == ("target_height", "temperature")
        assert "hs" in finding.message
        assert not editor.is_usable

    def test_assigning_a_column_does_not_quietly_steal_it(self, editor):
        """Clearing the other field would undo a choice the user made
        deliberately, and they would not see it happen."""
        editor.assign("temperature", "hs")
        assert editor.column_for("target_height") == "hs"
        assert editor.column_for("temperature") == "hs"

    def test_a_mapping_naming_a_column_this_file_lacks_blocks(self, editor):
        """A mapping saved for one instrument's export layout does not fit
        another's, and that has to be visible rather than producing an import
        that reads nothing."""
        editor.assign("temperature", "TEMP_C")
        finding = next(f for f in editor.findings() if f.code == "mapped_column_absent")
        assert finding.severity is Severity.BLOCKING
        assert "TEMP_C" in finding.message

    def test_the_sexagesimal_triple_supplies_the_angle_it_composes(self):
        """``horizontal`` is required, but three columns of degrees, minutes
        and seconds supply it. Marking them all required would be wrong in both
        directions."""
        editor = MappingEditor(_rd01_preview())
        assert editor.column_for("horizontal") == ""
        assert editor.is_usable

    def test_only_the_three_true_requirements_are_marked_required(self):
        required = ("station", "horizontal", "zenith")
        assert all(field_is_required(field) for field in required)
        assert not field_is_required("horizontal_degrees")
        assert not field_is_required("distance")


class TestWhatItReportsWithoutBlocking:
    def test_an_unmapped_column_is_mentioned_and_not_fatal(self, editor):
        """A column nobody mapped is either a field the user forgot or one
        GeoComp does not understand. Worth saying, not worth stopping for."""
        editor.assign("target_height", "")
        finding = next(f for f in editor.findings() if f.code == "column_unmapped")
        assert finding.severity is Severity.INFO
        assert "hs" in finding.message
        assert editor.is_usable

    def test_every_problem_is_reported_at_once(self, editor):
        """A user fixing a mapping wants the whole list. Revealing them one at
        a time turns one pass into five."""
        editor.assign("station", "")
        editor.assign("temperature", "hs")
        codes = {finding.code for finding in editor.findings()}
        assert {"required_field_unmapped", "column_assigned_twice"} <= codes

    def test_the_worst_problems_come_first(self, editor):
        editor.assign("station", "")
        editor.assign("distance", "")
        severities = [finding.severity.rank for finding in editor.findings()]
        assert severities == sorted(severities, reverse=True)


class TestConstants:
    def test_a_constant_serves_a_quantity_recorded_once(self, editor):
        editor.set_constant("temperature", 21.5)
        assert editor.constant_for("temperature") == 21.5
        assert editor.is_usable

    def test_a_constant_and_a_column_are_mutually_exclusive(self, editor):
        """A field cannot have both, and letting it would leave which one wins
        to whichever code path ran last."""
        editor.set_constant("target_height", 1.5)
        assert editor.column_for("target_height") == ""
        editor.assign("target_height", "hs")
        assert editor.constant_for("target_height") is None

    def test_clearing_a_column_keeps_a_constant_that_was_there_first(self, editor):
        editor.set_constant("pressure", 1013.25)
        editor.assign("pressure", "")
        assert editor.constant_for("pressure") == 1013.25


class TestTheResult:
    def test_the_mapping_round_trips_through_its_own_file_format(self, editor):
        mapping = editor.mapping()
        assert FieldMapping.from_dict(mapping.to_dict()).to_dict() == mapping.to_dict()

    def test_it_imports_rd01_exactly_as_the_inferred_mapping_does(self, editor):
        """The dialog's job is to reproduce, by hand, what inference does
        automatically. If the two disagree on a header inference understands,
        one of them is wrong."""
        from geocomp.io.mapping import infer_mapping

        inferred = infer_mapping(list(editor.preview.header))
        assert editor.mapping().to_dict()["columns"] == inferred.to_dict()["columns"]

    def test_the_column_order_does_not_depend_on_the_order_of_editing(self):
        """Two people who make the same choices must produce the same file, or
        a distributed mapping generates spurious diffs."""
        first = MappingEditor(_rd01_preview())
        second = MappingEditor(_rd01_preview())
        for field in ("distance", "face", "station"):
            first.assign(field, first.column_for(field))
        for field in ("station", "face", "distance"):
            second.assign(field, second.column_for(field))
        assert first.mapping().to_dict() == second.mapping().to_dict()

    def test_loading_a_saved_mapping_replaces_the_whole_state(self, editor):
        saved = FieldMapping.from_dict(
            {
                "name": "other",
                "columns": [
                    {"field": "station", "column": "E"},
                    {"field": "horizontal", "column": "HG"},
                    {"field": "zenith", "column": "VG"},
                ],
                "angle_format": "DECIMAL_DEGREES",
                "decimal_separator": ",",
            }
        )
        editor.load(saved)
        assert editor.angle_format is AngleFormat.DECIMAL_DEGREES
        assert editor.decimal_separator == ","
        assert editor.column_for("horizontal_seconds") == ""
        assert editor.column_for("horizontal") == "HG"

    def test_an_unknown_field_is_refused_rather_than_stored(self, editor):
        with pytest.raises(KeyError):
            editor.assign("elevation_angle", "VG")


class TestThePreview:
    def test_a_column_shows_the_values_under_it(self, editor):
        """The whole reason this dialog exists: a combo box offering HS and hs
        says nothing, and the values under them say everything."""
        assert editor.preview.column("hs")[0] == "1.5"
        assert editor.preview.column("HS")[0] == "0"

    def test_a_column_the_file_does_not_have_previews_as_nothing(self, editor):
        assert editor.preview.column("TEMP_C") == ()

    def test_a_short_row_does_not_break_the_preview(self):
        preview = PreviewTable(header=("a", "b", "c"), rows=(("1", "2"),))
        assert preview.column("c") == ("",)
