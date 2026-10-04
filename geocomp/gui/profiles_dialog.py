# SPDX-License-Identifier: GPL-2.0-or-later
"""The instrument profiles window (FR-061, FR-069; specs/15 §2.2).

A library of named profiles -- total stations, reflectors, levels, levelling
classes, gravimeters -- opened from a file, edited, and saved back: the file an
algorithm's *Instrument profiles* input reads. One tab a kind, each with its list
and its form. Add, duplicate, delete, choose the default, import another
library's profiles, export some of this one's.

What is edited is :mod:`geocomp.core.instruments.editing`'s business, tested
without QGIS: which fields, in which units, and what each operation does to the
library. This window lays it out. Angles are shown in the interface's small-angle
unit (seconds, cc or µrad), small lengths in millimetres, EDM terms in ppm; the
file keeps radians, metres and ratios. A value the profile refuses is refused
here in its own words and nothing is changed.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qgis.PyQt.QtCore import QCoreApplication, Qt
from qgis.PyQt.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

# The profile window's refusals are worded by the templates registered with the
# analysis group; imported here so that the window says them in words whether or
# not the Processing provider has been loaded.
from geocomp.algorithms.analysis import messages as _messages  # noqa: F401
from geocomp.core.errors import GeoCompError
from geocomp.core.instruments.editing import (
    FIELDS,
    KINDS,
    Field,
    add_profile,
    duplicate_profile,
    edited,
    export_profiles,
    import_profiles,
    remove_profile,
    set_default,
    shown,
)
from geocomp.core.instruments.profiles import ProfileLibrary

__all__ = ["ProfileLibraryDialog", "read_library"]

#: What a file that is not a profile library raises when read.
_UNREADABLE = (OSError, ValueError, KeyError, TypeError, AttributeError, GeoCompError)


def read_library(path: str) -> ProfileLibrary:
    """The profile library in the file at *path*.

    Raises:
        DataError: ``profile_library_not_an_object`` when the file holds JSON
            that is not an object -- a list, a number -- and so cannot be a
            library; and whatever the profiles themselves refuse.
    """
    from geocomp.core.errors import DataError

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise DataError("profile_library_not_an_object", path=path)
    return ProfileLibrary.from_dict(payload)

_CONTEXT = "GeoCompProfiles"


def _tr(text: str) -> str:
    return QCoreApplication.translate(_CONTEXT, text)


def _kind_label(kind: str) -> str:
    return {
        "instruments": _tr("Total stations"),
        "reflectors": _tr("Reflectors"),
        "levels": _tr("Levels"),
        "levelling_classes": _tr("Levelling classes"),
        "gravimeters": _tr("Gravimeters"),
    }[kind]


def _field_label(kind: str, field: Field, angle: str) -> str:
    """The field's label, with its unit; *angle* is the small-angle symbol."""
    labels = {
        "name": _tr("Name"),
        "manufacturer": _tr("Manufacturer"),
        "model": _tr("Model"),
        "serial_number": _tr("Serial number"),
        "serial": _tr("Serial number"),
        "calibration_date": _tr("Calibration date"),
        "calibration_reference": _tr("Calibration certificate"),
        "source": _tr("Source document"),
        "collimation": (
            _tr("Line-of-sight tilt (%1)") if kind == "levels" else _tr("Collimation error (%1)")
        ),
        "vertical_index": _tr("Vertical index error (%1)"),
        "trunnion_tilt": _tr("Trunnion axis tilt (%1)"),
        "edm_additive": _tr("EDM additive constant (mm)"),
        "edm_scale": _tr("EDM scale error (ppm)"),
        "cyclic_error_amplitude": _tr("EDM cyclic error amplitude (mm)"),
        "cyclic_error_wavelength": _tr("EDM cyclic error wavelength (m)"),
        "applies_edm_constant": _tr("The instrument applies its EDM constant"),
        "applies_atmospheric": _tr("The instrument applies the atmospheric correction"),
        "atmospheric_model": _tr("Atmospheric model"),
        "reference_refractive_index": _tr("Reference refractive index"),
        "edm.constant": _tr("EDM precision, constant part (mm)"),
        "edm.proportional": _tr("EDM precision, proportional part (ppm)"),
        "edm.scale": _tr("EDM precision, factor on the specification"),
        "sigma_direction": _tr("Direction, one set (%1)"),
        "sigma_zenith": _tr("Zenith angle, one set (%1)"),
        "sigma_zenith_refraction": _tr("Zenith angle, refraction term (%1 per km)"),
        "sigma_instrument_height": _tr("Instrument height (mm)"),
        "sigma_target_height": _tr("Target height (mm)"),
        "additive_constant": _tr("Prism constant (mm)"),
        "applies_internally": _tr("The instrument applies this constant"),
        "applies_collimation": _tr("The level removes its own tilt"),
        "sigma_per_km": _tr("Height difference, per root kilometre (mm)"),
        "sigma_per_setup": _tr("Height difference, per setup (mm)"),
        "sigma_reading": (
            _tr("One reading (µGal)") if kind == "gravimeters" else _tr("One staff reading (mm)")
        ),
        "stadia_factor": _tr("Stadia factor"),
        "sigma_stadia_reading": _tr("One outer-wire reading (mm)"),
        "tolerance_coefficient": _tr("Misclosure tolerance k, in k√L (mm)"),
        "max_sight_length": _tr("Longest sight (m)"),
        "max_sight_imbalance": _tr("Largest imbalance per setup (m)"),
        "max_accumulated_imbalance": _tr("Largest imbalance along a line (m)"),
        "reading_unit": _tr("Readings are"),
        "calibration_factor": _tr("Calibration factor"),
        "applies_tide": _tr("The readings have the tide removed"),
    }
    return labels[field.key].replace("%1", angle)


def _choice_label(value: str) -> str:
    return {
        "counter": _tr("counter units, through a calibration table"),
        "gravity": _tr("gravity"),
    }.get(value, value.replace("_", " ").lower())


def _spin(parent: QWidget) -> QDoubleSpinBox:
    box = QDoubleSpinBox(parent)
    box.setDecimals(6)
    box.setRange(-1.0e9, 1.0e9)
    return box


class _KindPage(QWidget):
    """One kind's list and form."""

    def __init__(self, dialog: ProfileLibraryDialog, kind: str) -> None:
        super().__init__(dialog.tabs)
        self.dialog = dialog
        self.kind = kind
        layout = QHBoxLayout(self)

        left = QVBoxLayout()
        self.list = QListWidget(self)
        self.list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        left.addWidget(self.list)
        self.buttons: dict[str, QPushButton] = {}
        for name, label, slot in (
            ("add", _tr("Add…"), self.add),
            ("duplicate", _tr("Duplicate…"), self.duplicate),
            ("delete", _tr("Delete"), self.delete),
            ("default", _tr("Use as default"), self.make_default),
            ("export", _tr("Export selected…"), self._export),
        ):
            button = QPushButton(label, self)
            button.clicked.connect(lambda _checked=False, slot=slot: slot())
            left.addWidget(button)
            self.buttons[name] = button
        layout.addLayout(left, stretch=1)

        right = QVBoxLayout()
        self.form = QFormLayout()
        self.editors: dict[str, Any] = {}
        angle = dialog.display.small_angle_symbol
        for field in FIELDS[kind]:
            self.editors[field.key] = self._editor(field)
            widget = self.editors[field.key]
            if isinstance(widget, tuple):
                row = QWidget(self)
                row_layout = QHBoxLayout(row)
                row_layout.setContentsMargins(0, 0, 0, 0)
                row_layout.addWidget(widget[0])
                row_layout.addWidget(widget[1])
                widget = row
            self.form.addRow(_field_label(kind, field, angle), widget)
        right.addLayout(self.form)
        self.apply_button = QPushButton(_tr("Apply"), self)
        self.apply_button.clicked.connect(self.apply)
        right.addWidget(self.apply_button)
        right.addStretch(1)
        layout.addLayout(right, stretch=2)

        self.list.currentItemChanged.connect(lambda *_args: self.show_current())

    def _editor(self, field: Field):
        if field.editor == "text":
            return QLineEdit(self)
        if field.editor == "flag":
            return QCheckBox(self)
        if field.editor == "choice":
            box = QComboBox(self)
            for value in field.choices:
                box.addItem(_choice_label(value), value)
            return box
        if field.editor == "number":
            return _spin(self)
        sigma = _spin(self)
        sigma.setMinimum(0.0)
        sigma.setPrefix(_tr("± "))
        sigma.setToolTip(_tr("Its standard deviation, in the same unit"))
        return _spin(self), sigma

    # -- the list ------------------------------------------------------------

    @property
    def profiles(self) -> dict[str, Any]:
        return getattr(self.dialog.library, self.kind)

    def refresh(self, select: str = "") -> None:
        default = getattr(self.dialog.library, next(k.default for k in KINDS if k.key == self.kind))
        self.list.blockSignals(True)
        self.list.clear()
        for profile_id, profile in sorted(self.profiles.items()):
            text = (
                profile_id
                if profile.name in ("", profile_id)
                else _tr("%1 — %2").replace("%1", profile_id).replace("%2", profile.name)
            )
            if profile_id == default:
                text = _tr("%1 (default)").replace("%1", text)
            item = QListWidgetItem(text, self.list)
            item.setData(Qt.ItemDataRole.UserRole, profile_id)
            if profile_id == select:
                self.list.setCurrentItem(item)
        self.list.blockSignals(False)
        if self.list.currentItem() is None and self.list.count():
            self.list.setCurrentRow(0)
        self.show_current()

    def current_id(self) -> str:
        item = self.list.currentItem()
        return str(item.data(Qt.ItemDataRole.UserRole)) if item is not None else ""

    def selected_ids(self) -> list[str]:
        return sorted(str(item.data(Qt.ItemDataRole.UserRole)) for item in self.list.selectedItems())

    # -- the form ------------------------------------------------------------

    def show_current(self) -> None:
        profile_id = self.current_id()
        enabled = bool(profile_id)
        for name in ("duplicate", "delete", "default", "export"):
            self.buttons[name].setEnabled(enabled)
        self.apply_button.setEnabled(enabled)
        if not enabled:
            return
        payload = self.profiles[profile_id].to_dict()
        factor = self.dialog.display.small_angle_factor
        for field in FIELDS[self.kind]:
            value = shown(payload, field, small_angle=factor)
            editor = self.editors[field.key]
            if field.editor == "text":
                editor.setText(value)
            elif field.editor == "flag":
                editor.setChecked(value)
            elif field.editor == "choice":
                editor.setCurrentIndex(max(editor.findData(value), 0))
            elif field.editor == "number":
                editor.setValue(value)
            else:
                editor[0].setValue(value[0])
                editor[1].setValue(value[1])

    def values(self) -> dict[str, Any]:
        """What the form holds, by field, as :func:`edited` takes it."""
        values: dict[str, Any] = {}
        for field in FIELDS[self.kind]:
            editor = self.editors[field.key]
            if field.editor == "text":
                values[field.key] = editor.text()
            elif field.editor == "flag":
                values[field.key] = editor.isChecked()
            elif field.editor == "choice":
                values[field.key] = editor.currentData()
            elif field.editor == "number":
                values[field.key] = editor.value()
            else:
                values[field.key] = (editor[0].value(), editor[1].value())
        return values

    def apply(self) -> bool:
        """Write the form into the current profile; ``False``, said, if it refuses."""
        profile_id = self.current_id()
        if not profile_id:
            return False
        try:
            profile = edited(
                self.kind,
                self.profiles[profile_id].to_dict(),
                self.values(),
                small_angle=self.dialog.display.small_angle_factor,
            )
        except GeoCompError as error:
            self.dialog.say_refused(error)
            return False
        self.profiles[profile_id] = profile
        self.dialog.changed(_tr("%1 updated.").replace("%1", profile_id))
        self.refresh(select=profile_id)
        return True

    # -- operations ----------------------------------------------------------

    def _ask_id(self, title: str, suggestion: str = "") -> str:
        text, ok = QInputDialog.getText(self, title, _tr("Profile id"), text=suggestion)
        return text.strip() if ok else ""

    def add(self, profile_id: str | None = None) -> bool:
        profile_id = profile_id if profile_id is not None else self._ask_id(_tr("New profile"))
        if not profile_id:
            return False
        try:
            add_profile(self.dialog.library, self.kind, profile_id)
        except GeoCompError as error:
            self.dialog.say_refused(error)
            return False
        self.dialog.changed(_tr("%1 added.").replace("%1", profile_id))
        self.refresh(select=profile_id)
        return True

    def duplicate(self, new_id: str | None = None) -> bool:
        source = self.current_id()
        if not source:
            return False
        new_id = new_id if new_id is not None else self._ask_id(_tr("Duplicate profile"), f"{source}-2")
        if not new_id:
            return False
        try:
            duplicate_profile(self.dialog.library, self.kind, source, new_id)
        except GeoCompError as error:
            self.dialog.say_refused(error)
            return False
        self.dialog.changed(_tr("%1 copied to %2.").replace("%1", source).replace("%2", new_id))
        self.refresh(select=new_id)
        return True

    def delete(self) -> bool:
        profile_id = self.current_id()
        if not profile_id:
            return False
        remove_profile(self.dialog.library, self.kind, profile_id)
        self.dialog.changed(_tr("%1 deleted.").replace("%1", profile_id))
        self.refresh()
        return True

    def make_default(self) -> bool:
        profile_id = self.current_id()
        if not profile_id:
            return False
        set_default(self.dialog.library, self.kind, profile_id)
        self.dialog.changed(_tr("%1 is the default.").replace("%1", profile_id))
        self.refresh(select=profile_id)
        return True

    def _export(self) -> None:
        path, _filter = QFileDialog.getSaveFileName(
            self, _tr("Export profiles"), "", _tr("GeoComp instrument profiles (*.json)")
        )
        if path:
            self.dialog.export_file(path, {self.kind: self.selected_ids()})


class ProfileLibraryDialog(QDialog):
    """The instrument profiles window."""

    def __init__(self, path: str = "", parent: QWidget | None = None, *, kind: str = "") -> None:
        super().__init__(parent)
        from geocomp.algorithms.display import display_format

        self.setWindowTitle(_tr("GeoComp instrument profiles"))
        self.setObjectName("geocompProfiles")
        self.display = display_format()
        self.library = ProfileLibrary()
        self.path = ""
        self.dirty = False

        layout = QVBoxLayout(self)
        bar = QHBoxLayout()
        self.file_label = QLabel(self)
        bar.addWidget(self.file_label, stretch=1)
        for label, slot in (
            (_tr("New"), self.new),
            (_tr("Open…"), self._open),
            (_tr("Import…"), self._import),
            (_tr("Save"), self._save),
            (_tr("Save as…"), self._save_as),
        ):
            button = QPushButton(label, self)
            button.clicked.connect(lambda _checked=False, slot=slot: slot())
            bar.addWidget(button)
        layout.addLayout(bar)

        self.tabs = QTabWidget(self)
        self.pages: dict[str, _KindPage] = {}
        for each in KINDS:
            page = _KindPage(self, each.key)
            self.pages[each.key] = page
            self.tabs.addTab(page, _kind_label(each.key))
        layout.addWidget(self.tabs)
        self.status = QLabel(self)
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, self)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if path and Path(path).exists():
            self.open_library(path)
        else:
            # A library named in the settings but not written yet: it is
            # started empty, and Save writes it where it is named.
            self.path = path
            self._show_library()
            if path:
                self.status.setText(
                    _tr("%1 does not exist yet. It is written there when saved.").replace("%1", path)
                )
        if kind in self.pages:
            self.tabs.setCurrentWidget(self.pages[kind])

    # -- the file --------------------------------------------------------------

    def new(self) -> None:
        """Start an empty library, asking first if this one has unsaved changes."""
        if not self._may_discard():
            return
        self.library, self.path, self.dirty = ProfileLibrary(), "", False
        self._show_library()

    def open_library(self, path: str) -> bool:
        """Read the library at *path*; ``False``, said, if it cannot be read."""
        try:
            library = read_library(path)
        except _UNREADABLE as error:
            from geocomp.services.messages import reason_for

            self.status.setText(
                _tr("%1 could not be read as instrument profiles: %2")
                .replace("%1", path)
                .replace("%2", reason_for(error))
            )
            return False
        self.library, self.path, self.dirty = library, path, False
        self._show_library()
        return True

    def save(self, path: str = "") -> bool:
        """Write the library to *path*, or to the file it came from; ``False`` with neither."""
        path = path or self.path
        if not path:
            return False
        Path(path).write_text(
            json.dumps(self.library.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        self.path, self.dirty = path, False
        self._show_file()
        self.status.setText(_tr("Saved to %1.").replace("%1", path))
        return True

    def import_file(self, path: str) -> tuple[list[str], list[str]]:
        """Add the profiles in the library at *path*; those whose id is taken are left."""
        try:
            other = read_library(path)
        except _UNREADABLE as error:
            from geocomp.services.messages import reason_for

            self.status.setText(
                _tr("%1 could not be read as instrument profiles: %2")
                .replace("%1", path)
                .replace("%2", reason_for(error))
            )
            return [], []
        added, kept = import_profiles(self.library, other)
        message = _tr("%1 profile(s) imported.").replace("%1", str(len(added)))
        if kept:
            message = (
                _tr("%1 profile(s) imported. Already in the library, and not replaced: %2.")
                .replace("%1", str(len(added)))
                .replace("%2", ", ".join(kept))
            )
        if added:
            self.dirty = True
        self._show_library()
        self.status.setText(message)
        return added, kept

    def export_file(self, path: str, chosen: dict[str, list[str]]) -> int:
        """Write the *chosen* profiles to *path* as a library of their own."""
        exported = export_profiles(self.library, chosen)
        Path(path).write_text(
            json.dumps(exported.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        count = sum(len(ids) for ids in chosen.values())
        self.status.setText(
            _tr("%1 profile(s) exported to %2.").replace("%1", str(count)).replace("%2", path)
        )
        return count

    # -- what the pages report ------------------------------------------------

    def changed(self, message: str) -> None:
        """A page changed the library: mark it unsaved and say what was done."""
        self.dirty = True
        self._show_file()
        self.status.setText(message)

    def say_refused(self, error: GeoCompError) -> None:
        """Say why an edit or an operation was refused, in words."""
        from geocomp.services.messages import message_for

        self.status.setText(message_for(error))

    def _show_library(self) -> None:
        for page in self.pages.values():
            page.refresh()
        self._show_file()

    def _show_file(self) -> None:
        name = self.path or _tr("(not saved)")
        self.file_label.setText(name + (" *" if self.dirty else ""))

    # -- the buttons -----------------------------------------------------------

    def _open(self) -> None:
        if not self._may_discard():
            return
        path, _filter = QFileDialog.getOpenFileName(
            self, _tr("Open instrument profiles"), "", _tr("GeoComp instrument profiles (*.json)")
        )
        if path:
            self.open_library(path)

    def _import(self) -> None:
        path, _filter = QFileDialog.getOpenFileName(
            self, _tr("Import profiles"), "", _tr("GeoComp instrument profiles (*.json)")
        )
        if path:
            self.import_file(path)

    def _save(self) -> None:
        if not self.save():
            self._save_as()

    def _save_as(self) -> None:
        path, _filter = QFileDialog.getSaveFileName(
            self, _tr("Save instrument profiles"), "", _tr("GeoComp instrument profiles (*.json)")
        )
        if path:
            self.save(path)

    def _may_discard(self) -> bool:
        if not self.dirty:
            return True
        answer = QMessageBox.question(
            self,
            _tr("Unsaved changes"),
            _tr("The profiles have changes that are not saved. Discard them?"),
        )
        return answer == QMessageBox.StandardButton.Yes

    def reject(self) -> None:
        """Close, asking first if the library has unsaved changes."""
        if self._may_discard():
            super().reject()
