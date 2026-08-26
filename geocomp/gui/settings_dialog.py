# SPDX-License-Identifier: GPL-2.0-or-later
"""The Global Settings window (FR-060).

The research project asks for *"uma janela onde com menus laterais para cada
tipo de equipamento, onde deverão estar armazenadas constantes e valores
configuráveis"* -- a side menu organised by equipment type. Layout is specified
in ``specs/15-ui-menu-and-settings.md`` section 2: equipment sections first,
then the cross-cutting ones, separated.

The pages are **generated** from :data:`geocomp.core.settings_def.SECTIONS` and
``SETTINGS``, not hand-built. A new setting therefore cannot exist without a UI,
and the dialog cannot show a setting that no longer exists.

Each editor shows the origin scope of its effective value and offers a
per-project override, which is FR-068's requirement that the effective value and
its origin be inspectable.
"""

from __future__ import annotations

from typing import Any

from qgis.PyQt.QtCore import QCoreApplication, Qt
from qgis.PyQt.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from geocomp.core.settings_def import (
    SECTIONS,
    Scope,
    SectionDef,
    SettingDef,
    SettingType,
    settings_in_section,
)

__all__ = ["GlobalSettingsDialog", "section_label", "setting_label"]

_TR_CONTEXT = "GeoCompSettings"


def _tr(text: str) -> str:
    return QCoreApplication.translate(_TR_CONTEXT, text)


def section_label(section_id: str) -> str:
    """Translated label for a settings section."""
    return {
        "total_station": _tr("Total Station"),
        "level": _tr("Level"),
        "gnss": _tr("GNSS"),
        "gravimeter": _tr("Gravimeter"),
        "stochastic": _tr("Stochastic model"),
        "reference_systems": _tr("Reference systems"),
        "paths": _tr("Paths and engines"),
        "interface": _tr("Interface"),
    }.get(section_id, section_id)


def setting_label(key: str) -> str:
    """Translated label for one setting."""
    return {
        "interface.language": _tr("Language"),
        "interface.mode": _tr("Usage mode"),
        "interface.distance_unit": _tr("Distance unit"),
        "interface.angle_format": _tr("Angle format"),
        "interface.coordinate_decimals": _tr("Coordinate decimal places"),
        "interface.angle_decimals": _tr("Angle decimal places"),
        "interface.log_level": _tr("Log verbosity"),
        "interface.show_toolbar": _tr("Show the GeoComp toolbar"),
    }.get(key, key)


def choice_label(key: str, value: str) -> str:
    """Translated label for one choice of a choice setting."""
    return {
        ("interface.language", "system"): _tr("Follow QGIS"),
        ("interface.language", "en"): _tr("English"),
        ("interface.language", "pt_BR"): _tr("Português (Brasil)"),
        ("interface.language", "es"): _tr("Español"),
        ("interface.mode", "basic"): _tr("Basic"),
        ("interface.mode", "advanced"): _tr("Advanced"),
        ("interface.distance_unit", "metre"): _tr("Metre"),
        ("interface.distance_unit", "foot"): _tr("Foot"),
        ("interface.distance_unit", "us_survey_foot"): _tr("US survey foot"),
        ("interface.angle_format", "dms"): _tr("Degrees, minutes, seconds"),
        ("interface.angle_format", "decimal_degrees"): _tr("Decimal degrees"),
        ("interface.angle_format", "gon"): _tr("Gon"),
        ("interface.angle_format", "radian"): _tr("Radian"),
        ("interface.log_level", "debug"): _tr("Debug"),
        ("interface.log_level", "info"): _tr("Information"),
        ("interface.log_level", "warning"): _tr("Warning"),
        ("interface.log_level", "critical"): _tr("Critical"),
    }.get((key, value), value)


def scope_label(scope: Scope) -> str:
    """Translated name of an origin scope, shown beside each value."""
    return {
        Scope.RUN: _tr("this run"),
        Scope.PROJECT: _tr("this project"),
        Scope.GLOBAL: _tr("global"),
        Scope.DEFAULT: _tr("default"),
    }[scope]


class GlobalSettingsDialog(QDialog):
    """Side-menu settings dialog, generated from the setting declarations."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("geocompSettingsDialog")
        self.setWindowTitle(_tr("GeoComp — Global Settings"))
        self.resize(760, 520)

        self._editors: dict[str, QWidget] = {}
        self._origins: dict[str, QLabel] = {}

        self._sidebar = QListWidget(self)
        self._sidebar.setObjectName("geocompSettingsSidebar")
        self._sidebar.setMaximumWidth(200)
        self._pages = QStackedWidget(self)

        for section in sorted(SECTIONS, key=lambda item: item.order):
            self._add_section(section)

        self._sidebar.currentRowChanged.connect(self._pages.setCurrentIndex)
        if self._sidebar.count():
            self._sidebar.setCurrentRow(0)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.RestoreDefaults,
            self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.StandardButton.RestoreDefaults).clicked.connect(
            self._restore_defaults
        )

        body = QHBoxLayout()
        body.addWidget(self._sidebar)
        body.addWidget(self._pages, stretch=1)

        layout = QVBoxLayout(self)
        layout.addLayout(body)
        layout.addWidget(buttons)

        self._load()

    # -- construction ----------------------------------------------------

    def _add_section(self, section: SectionDef) -> None:
        item = QListWidgetItem(section_label(section.id))
        item.setData(Qt.ItemDataRole.UserRole, section.id)
        self._sidebar.addItem(item)

        page = QWidget(self._pages)
        page.setObjectName(f"geocompSettingsPage_{section.id}")
        form = QFormLayout(page)

        definitions = settings_in_section(section.id)
        if not definitions:
            # A declared-but-unpopulated section: honest about what is coming
            # rather than an empty pane the user has to interpret.
            placeholder = QLabel(
                _tr(
                    "No settings in this section yet. They are added by the "
                    "development phase that implements this equipment type."
                ),
                page,
            )
            placeholder.setWordWrap(True)
            placeholder.setEnabled(False)
            form.addRow(placeholder)
        else:
            for definition in definitions:
                editor = self._build_editor(definition, page)
                origin = QLabel("", page)
                origin.setEnabled(False)
                self._editors[definition.key] = editor
                self._origins[definition.key] = origin

                row = QWidget(page)
                row_layout = QHBoxLayout(row)
                row_layout.setContentsMargins(0, 0, 0, 0)
                row_layout.addWidget(editor, stretch=1)
                row_layout.addWidget(origin)
                form.addRow(setting_label(definition.key), row)

        self._pages.addWidget(page)

    def _build_editor(self, definition: SettingDef, parent: QWidget) -> QWidget:
        if definition.type is SettingType.CHOICE:
            combo = QComboBox(parent)
            for value in definition.choices or ():
                combo.addItem(choice_label(definition.key, value), value)
            return combo
        if definition.type is SettingType.BOOL:
            return QCheckBox("", parent)
        if definition.type is SettingType.INT:
            spin = QSpinBox(parent)
            spin.setMinimum(int(definition.minimum) if definition.minimum is not None else -(2**31))
            spin.setMaximum(int(definition.maximum) if definition.maximum is not None else 2**31 - 1)
            return spin
        label = QLabel(_tr("(not editable in this version)"), parent)
        label.setEnabled(False)
        return label

    # -- values ----------------------------------------------------------

    def _load(self) -> None:
        from geocomp.services.settings_service import settings

        resolved = settings.all_resolved()
        for key, editor in self._editors.items():
            item = resolved.get(key)
            if item is None:  # pragma: no cover - defensive
                continue
            _set_editor_value(editor, item.value)
            origin = self._origins[key]
            origin.setText(_tr("from %1").replace("%1", scope_label(item.scope)))
            origin.setToolTip(
                _tr("Settings resolve in the order: this run, this project, global, default.")
            )

    def values(self) -> dict[str, Any]:
        """Current editor values, keyed by setting."""
        return {key: _editor_value(editor) for key, editor in self._editors.items()}

    def _restore_defaults(self) -> None:
        from geocomp.core.settings_def import setting

        for key, editor in self._editors.items():
            _set_editor_value(editor, setting(key).default)

    def accept(self) -> None:
        """Write changed values at global scope, then close.

        A value equal to the built-in default is *cleared* rather than written,
        so the stored configuration stays small and a later change of default
        reaches users who never expressed a preference.
        """
        from geocomp.core.errors import GeoCompError
        from geocomp.core.settings_def import setting
        from geocomp.services.logging import log
        from geocomp.services.settings_service import settings

        for key, value in self.values().items():
            definition = setting(key)
            if Scope.GLOBAL not in definition.scopes:
                continue
            try:
                if value == definition.default:
                    settings.reset_global(key)
                else:
                    settings.set_global(key, value)
            except GeoCompError as exc:
                log.exception(exc, message="could not save setting")

        settings.apply_log_level()
        super().accept()


def _set_editor_value(editor: QWidget, value: Any) -> None:
    if isinstance(editor, QComboBox):
        index = editor.findData(value)
        editor.setCurrentIndex(index if index >= 0 else 0)
    elif isinstance(editor, QCheckBox):
        editor.setChecked(bool(value))
    elif isinstance(editor, QSpinBox):
        editor.setValue(int(value))


def _editor_value(editor: QWidget) -> Any:
    if isinstance(editor, QComboBox):
        return editor.currentData()
    if isinstance(editor, QCheckBox):
        return editor.isChecked()
    if isinstance(editor, QSpinBox):
        return editor.value()
    return None
