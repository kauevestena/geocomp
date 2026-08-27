# SPDX-License-Identifier: GPL-2.0-or-later
"""The field-mapping dialog, built and driven in a real QGIS (FR-160).

Every decision the dialog makes is made by ``MappingEditor`` and tested without
QGIS in ``tests/test_mapping_editor.py``. What only a Qt runtime can answer is
whether the widgets are built, whether they show the data the dialog exists to
show, and whether editing one actually reaches the editor underneath -- a combo
box wired to nothing looks identical to one wired correctly until someone uses
it.
"""

from __future__ import annotations

import json

import pytest

from tests import reference_rd01 as rd01

pytestmark = pytest.mark.qgis


@pytest.fixture
def dialog(qgis_app):
    from geocomp.gui.mapping_dialog import FieldMappingDialog

    widget = FieldMappingDialog(str(rd01.RAW))
    yield widget
    widget.deleteLater()


class TestItShowsTheDataItExistsToShow:
    def test_the_preview_holds_the_head_of_the_file(self, dialog):
        """The whole reason this dialog is not the generated one: a combo box
        offering HS and hs says nothing, and the values under them say
        everything."""
        assert dialog.editor.preview.header
        assert dialog.editor.preview.column("hs")[0] == "1.5"
        assert dialog.editor.preview.column("HS")[0] == "0"

    def test_the_preview_widget_has_a_column_per_source_column(self, dialog):
        from qgis.PyQt.QtWidgets import QTableWidget

        table = dialog.findChild(QTableWidget, "geocompMappingPreview")
        assert table is not None
        assert table.columnCount() == len(dialog.editor.preview.header)
        assert table.rowCount() == len(dialog.editor.preview.rows)

    def test_the_preview_is_read_only(self, dialog):
        """It is context, not input. An editable preview would suggest the
        source file could be corrected here, which it cannot."""
        from qgis.PyQt.QtWidgets import QTableWidget

        table = dialog.findChild(QTableWidget, "geocompMappingPreview")
        assert table.editTriggers() == QTableWidget.EditTrigger.NoEditTriggers


class TestTheWidgetsAreWiredToTheEditor:
    def test_every_field_has_a_combo_box(self, dialog):
        from qgis.PyQt.QtWidgets import QComboBox

        from geocomp.io.mapping import FIELDS

        for field in FIELDS:
            combo = dialog.findChild(QComboBox, f"geocompMappingColumn_{field}")
            assert combo is not None, field

    def test_an_inferred_header_arrives_already_selected(self, dialog):
        from qgis.PyQt.QtWidgets import QComboBox

        combo = dialog.findChild(QComboBox, "geocompMappingColumn_target_height")
        assert combo.currentText() == "hs"

    def test_changing_a_combo_box_reaches_the_editor(self, dialog):
        """A combo wired to nothing looks identical to one wired correctly."""
        from qgis.PyQt.QtWidgets import QComboBox

        combo = dialog.findChild(QComboBox, "geocompMappingColumn_temperature")
        combo.setCurrentText("hs")
        assert dialog.editor.column_for("temperature") == "hs"

    def test_a_conflict_disables_ok_and_says_why(self, dialog):
        """One column cannot be two fields, and importing it as both would
        double-count the measurement."""
        from qgis.PyQt.QtWidgets import QComboBox, QDialogButtonBox, QLabel

        combo = dialog.findChild(QComboBox, "geocompMappingColumn_temperature")
        combo.setCurrentText("hs")

        findings = dialog.findChild(QLabel, "geocompMappingFindings")
        assert "hs" in findings.text()
        buttons = dialog.findChild(QDialogButtonBox)
        assert not buttons.button(QDialogButtonBox.StandardButton.Ok).isEnabled()

    def test_clearing_a_required_field_disables_ok(self, dialog):
        from qgis.PyQt.QtWidgets import QComboBox, QDialogButtonBox

        dialog.findChild(QComboBox, "geocompMappingColumn_station").setCurrentText("")
        buttons = dialog.findChild(QDialogButtonBox)
        assert not buttons.button(QDialogButtonBox.StandardButton.Ok).isEnabled()

    def test_a_recognised_header_starts_ready_to_accept(self, dialog):
        from qgis.PyQt.QtWidgets import QDialogButtonBox

        buttons = dialog.findChild(QDialogButtonBox)
        assert buttons.button(QDialogButtonBox.StandardButton.Ok).isEnabled()

    def test_the_angle_format_reaches_the_editor(self, dialog):
        from qgis.PyQt.QtWidgets import QComboBox

        from geocomp.io.mapping import AngleFormat

        combo = dialog.findChild(QComboBox, "geocompMappingAngleFormat")
        assert combo.currentData() == AngleFormat.SEXAGESIMAL_TRIPLE.name
        combo.setCurrentIndex(combo.findData(AngleFormat.GON.name))
        assert dialog.editor.angle_format is AngleFormat.GON


class TestWhatItHandsOn:
    def test_the_mapping_it_produces_imports_rd01(self, dialog):
        """End of the line: the dialog's output has to be a mapping the
        importer accepts, or the feature is decorative."""
        from geocomp.io.fieldbook import read_field_book_csv

        result = read_field_book_csv(rd01.RAW, dialog.mapping(), library=rd01.library())
        assert result.row_count == 12
        assert len(result.setups) == 3

    def test_the_mapping_round_trips_through_a_file(self, dialog, tmp_path):
        from geocomp.io.mapping import FieldMapping

        path = tmp_path / "mapping.json"
        path.write_text(json.dumps(dialog.mapping().to_dict()), encoding="utf-8")
        reloaded = FieldMapping.from_dict(json.loads(path.read_text(encoding="utf-8")))
        assert reloaded.to_dict() == dialog.mapping().to_dict()


class TestTheDispatcher:
    def test_the_import_algorithm_is_the_one_with_a_custom_dialog(self, qgis_app):
        from geocomp.gui.prompts import has_custom_dialog

        assert has_custom_dialog("geocomp:totalstation_import_fieldbook")
        assert not has_custom_dialog("geocomp:totalstation_network")

    def test_an_algorithm_without_one_collects_nothing_and_does_not_cancel(self, qgis_app):
        """An empty mapping, not ``None``: the caller passes the result
        straight through, and ``None`` means the user declined."""
        from geocomp.gui.prompts import collect_parameters

        assert collect_parameters("geocomp:totalstation_network") == {}
