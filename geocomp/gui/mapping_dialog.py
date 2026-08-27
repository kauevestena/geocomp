# SPDX-License-Identifier: GPL-2.0-or-later
"""The field-mapping dialog (FR-160).

``specs/15-ui-menu-and-settings.md`` section 3 lists this among the few
operations the standard Processing dialog cannot serve, and gives the reason:
mapping columns needs a preview of the data they contain. A combo box offering
``HS`` and ``hs`` tells a user nothing; a preview showing ``48`` under one and
``1.500`` under the other tells them everything.

The dialog is a **view**. Every decision -- which fields are unmapped, which
column got assigned twice, whether the result can be used -- is made by
:class:`~geocomp.io.mapping_editor.MappingEditor`, which has no Qt in it and is
tested without QGIS. What lives here is layout, signals, and the file chooser.

A saved mapping is the point of the feature rather than a convenience on top of
it: an organisation defines its instrument's export layout once and distributes
the file, and nobody re-maps columns every week (``specs/17`` section 5.1).
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from qgis.PyQt.QtCore import QCoreApplication, Qt
from qgis.PyQt.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from geocomp.core.findings import Severity
from geocomp.io.mapping import FIELDS, AngleFormat, FieldMapping
from geocomp.io.mapping_editor import (
    PREVIEW_ROWS,
    MappingEditor,
    PreviewTable,
    field_is_required,
)

__all__ = ["FieldMappingDialog", "angle_format_label", "field_label", "read_preview"]

_TR_CONTEXT = "GeoCompMapping"

#: Severity to a foreground colour name. Kept to three so the table reads as
#: the same three-way decision the findings themselves are.
_SEVERITY_COLOURS = {
    Severity.BLOCKING: "#d55e00",
    Severity.WARNING: "#e69f00",
    Severity.INFO: "#666666",
}


def _tr(text: str) -> str:
    return QCoreApplication.translate(_TR_CONTEXT, text)


def field_label(field: str) -> str:
    """The human name of a mapping field, translated (FR-090)."""
    labels = {
        "station": _tr("Occupied station"),
        "backsight": _tr("Backsight station"),
        "foresight": _tr("Foresight station"),
        "target": _tr("Target"),
        "face": _tr("Face"),
        "sighted": _tr("Sighted (backsight or foresight)"),
        "horizontal": _tr("Horizontal direction"),
        "horizontal_degrees": _tr("Horizontal degrees"),
        "horizontal_minutes": _tr("Horizontal minutes"),
        "horizontal_seconds": _tr("Horizontal seconds"),
        "zenith": _tr("Zenith angle"),
        "zenith_degrees": _tr("Zenith degrees"),
        "zenith_minutes": _tr("Zenith minutes"),
        "zenith_seconds": _tr("Zenith seconds"),
        "distance": _tr("Slope distance"),
        "instrument_height": _tr("Instrument height"),
        "target_height": _tr("Target height"),
        "temperature": _tr("Temperature"),
        "pressure": _tr("Pressure"),
        "humidity": _tr("Relative humidity"),
        "set_number": _tr("Set number"),
        "instrument_id": _tr("Instrument"),
        "reflector_id": _tr("Reflector"),
    }
    return labels.get(field, field)


def angle_format_label(value: AngleFormat) -> str:
    labels = {
        AngleFormat.DECIMAL_DEGREES: _tr("Decimal degrees"),
        AngleFormat.SEXAGESIMAL_TRIPLE: _tr("Degrees, minutes and seconds in three columns"),
        AngleFormat.SEXAGESIMAL_STRING: _tr("Degrees, minutes and seconds in one column"),
        AngleFormat.GON: _tr("Gon"),
        AngleFormat.RADIANS: _tr("Radians"),
    }
    return labels.get(value, value.name)


def read_preview(path: str | Path, *, rows: int = PREVIEW_ROWS) -> PreviewTable:
    """The header and first rows of a CSV, for the preview pane.

    Reads only what it shows. A field book can be large, and a dialog that
    loaded all of it to display twelve rows would stall on opening.
    """
    with open(path, encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        try:
            header = next(reader)
        except StopIteration:
            return PreviewTable(header=(), rows=())
        collected = []
        for index, row in enumerate(reader):
            if index >= rows:
                break
            collected.append(tuple(row))
    return PreviewTable(header=tuple(header), rows=tuple(collected))


class FieldMappingDialog(QDialog):
    """Map source columns onto GeoComp fields, against a preview of the data."""

    def __init__(
        self,
        source: str | Path,
        mapping: FieldMapping | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("geocompMappingDialog")
        self.setWindowTitle(_tr("GeoComp — Field mapping"))
        self.resize(900, 640)

        self.source = Path(source)
        self.editor = MappingEditor(read_preview(source), mapping)
        self._columns: dict[str, QComboBox] = {}
        self._constants: dict[str, QDoubleSpinBox] = {}

        layout = QVBoxLayout(self)
        layout.addWidget(self._preview_group())
        layout.addWidget(self._fields_group(), stretch=1)
        layout.addWidget(self._format_group())
        layout.addWidget(self._findings_group())

        self._buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        load = QPushButton(_tr("Load mapping…"), self)
        load.setObjectName("geocompMappingLoad")
        load.clicked.connect(self._load_mapping)
        save = QPushButton(_tr("Save mapping…"), self)
        save.setObjectName("geocompMappingSave")
        save.clicked.connect(self._save_mapping)
        self._buttons.addButton(load, QDialogButtonBox.ButtonRole.ActionRole)
        self._buttons.addButton(save, QDialogButtonBox.ButtonRole.ActionRole)
        self._buttons.accepted.connect(self.accept)
        self._buttons.rejected.connect(self.reject)
        layout.addWidget(self._buttons)

        self._refresh()

    # -- construction ----------------------------------------------------

    def _preview_group(self) -> QGroupBox:
        group = QGroupBox(_tr("Source: %1").replace("%1", self.source.name), self)
        header = self.editor.preview.header
        table = QTableWidget(len(self.editor.preview.rows), len(header), group)
        table.setObjectName("geocompMappingPreview")
        table.setHorizontalHeaderLabels(list(header))
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setMaximumHeight(180)
        for row_index, row in enumerate(self.editor.preview.rows):
            for column_index in range(len(header)):
                value = row[column_index] if column_index < len(row) else ""
                table.setItem(row_index, column_index, QTableWidgetItem(value))
        layout = QVBoxLayout(group)
        layout.addWidget(table)
        return group

    def _fields_group(self) -> QGroupBox:
        group = QGroupBox(_tr("Fields"), self)
        form = QFormLayout(group)
        choices = ["", *self.editor.preview.header]

        for field in FIELDS:
            combo = QComboBox(group)
            combo.setObjectName(f"geocompMappingColumn_{field}")
            combo.addItems(choices)
            current = self.editor.column_for(field)
            if current and current not in choices:
                # A loaded mapping naming a column this file lacks. Kept
                # visible rather than silently reset: the findings pane says
                # what is wrong, and clearing it would hide the mismatch.
                combo.addItem(current)
            combo.setCurrentText(current)
            combo.currentTextChanged.connect(
                lambda text, name=field: self._on_column_changed(name, text)
            )

            constant = QDoubleSpinBox(group)
            constant.setObjectName(f"geocompMappingConstant_{field}")
            constant.setDecimals(4)
            constant.setRange(-1.0e9, 1.0e9)
            constant.setSpecialValueText(_tr("(none)"))
            constant.setMinimum(-1.0e9)
            constant.setValue(self.editor.constant_for(field) or -1.0e9)
            constant.setToolTip(
                _tr("One value for every row, for a quantity that was recorded once.")
            )
            constant.valueChanged.connect(
                lambda value, name=field: self._on_constant_changed(name, value)
            )

            row = QHBoxLayout()
            row.addWidget(combo, stretch=2)
            row.addWidget(constant, stretch=1)
            holder = QWidget(group)
            holder.setLayout(row)

            label = field_label(field)
            if field_is_required(field):
                label = _tr("%1 (required)").replace("%1", label)
            form.addRow(label, holder)

            self._columns[field] = combo
            self._constants[field] = constant

        return group

    def _format_group(self) -> QGroupBox:
        group = QGroupBox(_tr("Format"), self)
        form = QFormLayout(group)

        self._angle_format = QComboBox(group)
        self._angle_format.setObjectName("geocompMappingAngleFormat")
        for value in AngleFormat:
            self._angle_format.addItem(angle_format_label(value), value.name)
        self._angle_format.setCurrentIndex(
            self._angle_format.findData(self.editor.angle_format.name)
        )
        self._angle_format.currentIndexChanged.connect(self._on_format_changed)

        self._separator = QComboBox(group)
        self._separator.setObjectName("geocompMappingSeparator")
        for value, label in (
            ("auto", _tr("Detect automatically")),
            (".", _tr("Point")),
            (",", _tr("Comma")),
        ):
            self._separator.addItem(label, value)
        self._separator.setCurrentIndex(self._separator.findData(self.editor.decimal_separator))
        self._separator.currentIndexChanged.connect(self._on_format_changed)

        form.addRow(_tr("Angle format"), self._angle_format)
        form.addRow(_tr("Decimal separator"), self._separator)
        return group

    def _findings_group(self) -> QGroupBox:
        group = QGroupBox(_tr("Problems"), self)
        self._findings = QLabel(group)
        self._findings.setObjectName("geocompMappingFindings")
        self._findings.setWordWrap(True)
        self._findings.setTextFormat(Qt.TextFormat.RichText)
        layout = QVBoxLayout(group)
        layout.addWidget(self._findings)
        return group

    # -- signals ---------------------------------------------------------

    def _on_column_changed(self, field: str, text: str) -> None:
        self.editor.assign(field, text)
        self._refresh()

    def _on_constant_changed(self, field: str, value: float) -> None:
        self.editor.set_constant(field, None if value <= -1.0e9 else value)
        self._refresh()

    def _on_format_changed(self) -> None:
        self.editor.angle_format = AngleFormat[self._angle_format.currentData()]
        self.editor.decimal_separator = self._separator.currentData()
        self._refresh()

    def _refresh(self) -> None:
        """Re-read the editor and repaint. Called after every change, because
        a problems pane that lagged one edit behind would be worse than none."""
        findings = self.editor.findings()
        if not findings:
            self._findings.setText(
                f"<span style='color:{_SEVERITY_COLOURS[Severity.INFO]}'>"
                + _tr("Nothing to fix.")
                + "</span>"
            )
        else:
            self._findings.setText(
                "<br>".join(
                    f"<span style='color:{_SEVERITY_COLOURS[finding.severity]}'>"
                    f"{finding.message}</span>"
                    for finding in findings
                )
            )
        self._buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(
            self.editor.is_usable
        )

    # -- files -----------------------------------------------------------

    def _load_mapping(self) -> None:
        path, _filter = QFileDialog.getOpenFileName(
            self, _tr("Load mapping"), "", _tr("GeoComp field mapping (*.json)")
        )
        if not path:
            return
        try:
            payload = json.loads(Path(path).read_text(encoding="utf-8"))
            self.editor.load(FieldMapping.from_dict(payload))
        except (OSError, ValueError, KeyError) as exc:
            QMessageBox.warning(
                self,
                _tr("Mapping not loaded"),
                _tr("'%1' could not be read as a field mapping: %2")
                .replace("%1", path)
                .replace("%2", str(exc)),
            )
            return
        self._reload_widgets()

    def _save_mapping(self) -> None:
        """Saving is allowed even when the mapping is incomplete.

        Half a mapping is worth keeping -- a user interrupted partway through a
        forty-column export should not have to start again -- and the findings
        pane, not the save button, is what says whether it is usable.
        """
        path, _filter = QFileDialog.getSaveFileName(
            self, _tr("Save mapping"), "", _tr("GeoComp field mapping (*.json)")
        )
        if not path:
            return
        target = Path(path)
        if not target.suffix:
            target = target.with_suffix(".json")
        self.editor.name = target.stem
        try:
            target.write_text(
                json.dumps(self.editor.mapping().to_dict(), indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        except OSError as exc:
            QMessageBox.warning(
                self,
                _tr("Mapping not saved"),
                _tr("'%1' could not be written: %2")
                .replace("%1", str(target))
                .replace("%2", str(exc)),
            )

    def _reload_widgets(self) -> None:
        """Push the editor's state back into the widgets after a load."""
        for field, combo in self._columns.items():
            combo.blockSignals(True)
            column = self.editor.column_for(field)
            if column and combo.findText(column) < 0:
                combo.addItem(column)
            combo.setCurrentText(column)
            combo.blockSignals(False)
        for field, spin in self._constants.items():
            spin.blockSignals(True)
            spin.setValue(self.editor.constant_for(field) or -1.0e9)
            spin.blockSignals(False)
        self._angle_format.blockSignals(True)
        self._angle_format.setCurrentIndex(
            self._angle_format.findData(self.editor.angle_format.name)
        )
        self._angle_format.blockSignals(False)
        self._separator.blockSignals(True)
        self._separator.setCurrentIndex(self._separator.findData(self.editor.decimal_separator))
        self._separator.blockSignals(False)
        self._refresh()

    # -- result ----------------------------------------------------------

    def mapping(self) -> FieldMapping:
        """The mapping the user built. Valid only after :meth:`accept`."""
        return self.editor.mapping()
