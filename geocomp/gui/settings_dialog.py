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

from qgis.PyQt.QtCore import QCoreApplication, QLocale, Qt
from qgis.PyQt.QtGui import QDoubleValidator
from qgis.PyQt.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
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

__all__ = [
    "CrsEditor",
    "FloatEditor",
    "GlobalSettingsDialog",
    "PathEditor",
    "TextEditor",
    "section_label",
    "setting_label",
]

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
        "basemaps": _tr("Base maps"),
        "interface": _tr("Interface"),
    }.get(section_id, section_id)


def setting_label(key: str) -> str:
    """Translated label for one setting.

    Every declared setting must appear here:
    ``tests/structural/test_settings_labels.py`` checks the correspondence, so a
    new setting cannot reach the dialog showing its raw dotted key. Phases P3
    and P4 both added settings, and P4 added the check after finding that P3's
    seventeen were rendering as ``total_station.atmospheric_model``.
    """
    return {
        # -- Total Station (P3) ------------------------------------------
        "total_station.atmospheric_model": _tr("Atmospheric model"),
        "total_station.default_temperature_celsius": _tr("Default temperature (degrees Celsius)"),
        "total_station.default_pressure_hpa": _tr("Default pressure (hPa)"),
        "total_station.default_humidity_percent": _tr("Default relative humidity (%)"),
        "total_station.default_temperature_sigma": _tr(
            "Uncertainty of the default temperature (degrees Celsius)"
        ),
        "total_station.default_pressure_sigma_hpa": _tr("Uncertainty of the default pressure (hPa)"),
        "total_station.refraction_coefficient": _tr("Coefficient of refraction (k)"),
        "total_station.refraction_coefficient_sigma": _tr("Uncertainty of k"),
        "total_station.face_distance_tolerance": _tr(
            "Face-pair distance tolerance (m; 0 = from the instrument's EDM)"
        ),
        "total_station.collimation_tolerance": _tr("Collimation tolerance (rad)"),
        "total_station.traverse_adjustment": _tr("Traverse adjustment method"),
        "total_station.traverse_relative_precision": _tr("Required relative precision (1:N)"),
        "total_station.traverse_angular_tolerance_per_station": _tr(
            "Angular tolerance per station (rad)"
        ),
        # -- Level (P4) --------------------------------------------------
        "level.weighting": _tr("Height-difference weighting"),
        "level.tolerance_coefficient": _tr("Permissible misclosure k, in m per root kilometre"),
        "level.max_sight_length": _tr("Longest permitted sight (m)"),
        "level.max_sight_imbalance": _tr("Largest permitted imbalance per setup (m)"),
        "level.max_accumulated_imbalance": _tr("Largest permitted imbalance per line (m)"),
        # -- GNSS (P7c) ---------------------------------------------------
        "gnss.product_directory": _tr("Precise product directory"),
        "gnss.antenna_file": _tr("Antenna calibration file (ANTEX)"),
        "gnss.reference_station_database": _tr("Reference station database"),
        "gnss.elevation_mask": _tr("Elevation mask (degrees)"),
        "gnss.ephemeris": _tr("Ephemeris source"),
        "gnss.ionosphere": _tr("Ionospheric correction"),
        "gnss.troposphere": _tr("Tropospheric correction"),
        "gnss.ambiguity_threshold": _tr("Ambiguity ratio threshold"),
        "gnss.independent_baselines_only": _tr("Use only the independent baseline subset"),
        # -- GNSS products (P10c) -----------------------------------------
        "gnss.product_services": _tr("Download services, in priority order (empty: never download)"),
        "gnss.service_definitions": _tr("Additional download services (JSON)"),
        "gnss.product_cache": _tr("Product cache (empty: the QGIS profile's folder)"),
        "gnss.product_fallback": _tr("Use rapid orbits where final ones are not yet published"),
        # -- Gravimeter (P8b) ---------------------------------------------
        "gravimeter.tide_model": _tr("Solid-Earth tide model"),
        "gravimeter.tide_amplification": _tr("Gravimetric factor (tide amplification)"),
        "gravimeter.drift_mode": _tr("Drift treatment"),
        "gravimeter.drift_degree": _tr("Drift polynomial degree"),
        "gravimeter.precision_floor": _tr(
            "Reading precision floor, added in quadrature (m/s²)"
        ),
        "gravimeter.display_unit": _tr("Gravity display unit"),
        "level.reciprocal_variance_inflation": _tr(
            "Variance inflation for reciprocal sights"
        ),
        "level.apply_orthometric_correction": _tr("Apply orthometric corrections"),
        "level.adjust_failing_lines": _tr("Adjust lines that failed their tolerance"),
        # -- Reference systems (P5) --------------------------------------
        "reference_systems.preferred_crs": _tr("Preferred coordinate reference system"),
        "reference_systems.default_epoch": _tr("Default reference epoch"),
        "reference_systems.geoid_model": _tr("Default geoid model file"),
        "reference_systems.geoid_sigma": _tr("Stated accuracy of the geoid model (m)"),
        # -- Base maps (P5) ----------------------------------------------
        "basemaps.offer_on_result_layers": _tr("Offer a base map when adding result layers"),
        "basemaps.default_service": _tr("Base map to offer"),
        "basemaps.catalogue": _tr("Base map catalogue file"),
        "basemaps.reuse_existing_layer": _tr("Use a base map already in the project, if there is one"),
        # -- Stochastic model (P3) ---------------------------------------
        "stochastic.default_sigma_direction": _tr("Default direction standard deviation (rad)"),
        "stochastic.default_sigma_zenith_angle": _tr("Default zenith-angle standard deviation (rad)"),
        "stochastic.default_sigma_slope_distance": _tr("Default slope-distance standard deviation (m)"),
        "stochastic.outlier_alpha": _tr("Outlier test significance level"),
        "stochastic.outlier_beta": _tr("Outlier test type II error rate"),
        "stochastic.confidence_level": _tr("Confidence level"),
        # -- Interface (P0) ----------------------------------------------
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
        ("total_station.atmospheric_model", "barrell_sears"): _tr("Barrell and Sears"),
        ("total_station.atmospheric_model", "leica"): _tr("Leica"),
        ("total_station.atmospheric_model", "trimble"): _tr("Trimble"),
        # GNSS choice values are RTKLIB's own vocabulary (IONOPT and TRPOPT in
        # its `src/options.c`), so the stored value is what the engine reads and
        # only the label is translated.
        ("gnss.ephemeris", "brdc"): _tr("Broadcast"),
        ("gnss.ephemeris", "precise"): _tr("Precise (IGS products)"),
        ("gnss.ionosphere", "off"): _tr("None"),
        ("gnss.ionosphere", "brdc"): _tr("Broadcast model"),
        ("gnss.ionosphere", "sbas"): _tr("SBAS"),
        ("gnss.ionosphere", "dual-freq"): _tr("Dual-frequency (ionosphere-free)"),
        ("gnss.ionosphere", "est-stec"): _tr("Estimated (STEC)"),
        ("gnss.ionosphere", "ionex-tec"): _tr("IONEX map"),
        ("gnss.troposphere", "off"): _tr("None"),
        ("gnss.troposphere", "saas"): _tr("Saastamoinen"),
        ("gnss.troposphere", "sbas"): _tr("SBAS"),
        ("gnss.troposphere", "est-ztd"): _tr("Estimated zenith delay"),
        ("gnss.troposphere", "est-ztdgrad"): _tr("Estimated zenith delay with gradients"),
        ("total_station.traverse_adjustment", "compass"): _tr("Compass (Bowditch) rule"),
        ("total_station.traverse_adjustment", "transit"): _tr("Transit rule"),
        ("total_station.traverse_adjustment", "none"): _tr(
            "None: report the misclosure only (least squares is Network adjustment)"
        ),
        ("level.weighting", "length"): _tr("Proportional to line length"),
        ("level.weighting", "setups"): _tr("Proportional to the number of setups"),
        ("gravimeter.tide_model", "longman_1959"): _tr("Longman (1959)"),
        ("gravimeter.tide_model", "none"): _tr("None (every instrument applies its own)"),
        ("gravimeter.drift_mode", "joint"): _tr("Estimated with the station values"),
        ("gravimeter.drift_mode", "pre_corrected"): _tr("Fitted to base readings first"),
        ("gravimeter.display_unit", "mgal"): _tr("mGal"),
        ("gravimeter.display_unit", "ugal"): _tr("µGal"),
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
        #: "This project", for each setting a project may override (FR-068).
        self._overrides: dict[str, QCheckBox] = {}

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

        # Where a value that cannot be saved is named. Not a message box: the
        # dialog stays open with the field still showing what was typed.
        self._error = QLabel("", self)
        self._error.setObjectName("geocompSettingsError")
        self._error.setWordWrap(True)
        self._error.setStyleSheet("color: #b00020;")
        self._error.hide()

        layout = QVBoxLayout(self)
        layout.addLayout(body)
        layout.addWidget(self._error)
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
                if Scope.PROJECT in definition.scopes:
                    override = QCheckBox(_tr("this project"), row)
                    override.setObjectName(f"geocompOverride_{definition.key}")
                    override.setToolTip(
                        _tr(
                            "Override for this project: the value is saved in the project, "
                            "travels with it, and applies to it alone."
                        )
                    )
                    override.toggled.connect(
                        lambda checked, key=definition.key: self._override_toggled(key, checked)
                    )
                    self._overrides[definition.key] = override
                    row_layout.addWidget(override)
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
        if definition.type is SettingType.FLOAT:
            return FloatEditor(definition, parent)
        if definition.type is SettingType.STRING:
            return TextEditor(parent)
        if definition.type in (SettingType.PATH, SettingType.DIRECTORY):
            return PathEditor(definition, parent)
        if definition.type is SettingType.CRS:
            return CrsEditor(parent)
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
            override = self._overrides.get(key)
            if override is not None:
                override.blockSignals(True)
                override.setChecked(item.scope is Scope.PROJECT)
                override.blockSignals(False)
            self._show_origin(key, item.scope)

    def _show_origin(self, key: str, scope: Scope) -> None:
        origin = self._origins[key]
        origin.setText(_tr("from %1").replace("%1", scope_label(scope)))
        origin.setToolTip(
            _tr("Settings resolve in the order: this run, this project, global, default.")
        )

    def _override_toggled(self, key: str, checked: bool) -> None:
        """Checked: the value shown becomes this project's. Unchecked: the value
        that applies without the override is shown, global or default."""
        from geocomp.services.settings_service import settings

        if checked:
            self._show_origin(key, Scope.PROJECT)
            return
        outside = settings.resolve_outside_project(key)
        _set_editor_value(self._editors[key], outside.value)
        self._show_origin(key, outside.scope)

    def values(self) -> dict[str, Any]:
        """Current editor values, keyed by setting."""
        return {key: _editor_value(editor) for key, editor in self._editors.items()}

    def _restore_defaults(self) -> None:
        from geocomp.core.settings_def import setting

        for key, editor in self._editors.items():
            _set_editor_value(editor, setting(key).default)

    def accept(self) -> None:
        """Write each value to its scope, then close.

        A row marked *this project* is saved in the project and leaves the
        global value alone; an unmarked one clears any project override and is
        saved globally. Until P12c the window wrote every row globally,
        including a value it had loaded from a project override -- so pressing
        OK in one project made its override every other project's global value.

        A global value equal to the built-in default is *cleared* rather than
        written, so the stored configuration stays small and a later change of
        default reaches users who never expressed a preference.
        """
        from geocomp.core.errors import GeoCompError
        from geocomp.core.settings_def import setting
        from geocomp.services.logging import log
        from geocomp.services.settings_service import settings

        unreadable = [
            setting_label(key)
            for key, editor in self._editors.items()
            if isinstance(editor, FloatEditor) and not editor.is_acceptable()
        ]
        if unreadable:
            self._error.setText(
                _tr("Not saved: these values are not numbers within their range: %1.").replace(
                    "%1", ", ".join(unreadable)
                )
            )
            self._error.show()
            return

        for key, value in self.values().items():
            definition = setting(key)
            override = self._overrides.get(key)
            try:
                current = settings.resolve(key)
                if override is not None and override.isChecked():
                    if current.scope is not Scope.PROJECT or current.value != value:
                        settings.set_project(key, value)
                    continue
                if current.scope is Scope.PROJECT:
                    settings.clear_project(key)
                if Scope.GLOBAL not in definition.scopes:
                    continue
                if value == definition.default:
                    settings.reset_global(key)
                else:
                    settings.set_global(key, value)
            except GeoCompError as exc:
                log.exception(exc, message="could not save setting")

        settings.apply_log_level()
        super().accept()


class FloatEditor(QLineEdit):
    """A real number of any magnitude, in the user's locale, within its declared range.

    Not a spin box. A spin box shows a fixed number of decimals, and the
    floating-point settings span eight orders of magnitude -- an angular
    tolerance of 1.45e-4 rad and a pressure of 1013.25 hPa -- so a fixed count
    either hides the first as zero or pads the second with noise. A box that
    takes ``1.45e-4`` as typed, and says so when a value is out of range, is the
    honest editor for both.
    """

    def __init__(self, definition: SettingDef, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        validator = QDoubleValidator(self)
        validator.setLocale(_locale())
        validator.setNotation(QDoubleValidator.Notation.ScientificNotation)
        if definition.minimum is not None:
            validator.setBottom(float(definition.minimum))
        if definition.maximum is not None:
            validator.setTop(float(definition.maximum))
        self.setValidator(validator)
        if definition.minimum is not None and definition.maximum is not None:
            self.setToolTip(
                _tr("From %1 to %2.")
                .replace("%1", _number(definition.minimum))
                .replace("%2", _number(definition.maximum))
            )

    def set_value(self, value: Any) -> None:
        self.setText(_number(value))

    def value(self) -> float | None:
        number, ok = _locale().toDouble(self.text().strip())
        return float(number) if ok else None

    def is_acceptable(self) -> bool:
        return self.hasAcceptableInput() and self.value() is not None


class TextEditor(QLineEdit):
    """A free-text setting: a service id, a list of ids."""

    def set_value(self, value: Any) -> None:
        self.setText("" if value is None else str(value))

    def value(self) -> str:
        return self.text().strip()


def _storage_mode(name: str) -> Any:
    from qgis.gui import QgsFileWidget

    modes = getattr(QgsFileWidget, "StorageMode", QgsFileWidget)
    return getattr(modes, name)


class PathEditor(QWidget):
    """A file or a directory, chosen with QGIS's own picker."""

    def __init__(self, definition: SettingDef, parent: QWidget | None = None) -> None:
        from qgis.gui import QgsFileWidget

        super().__init__(parent)
        self._picker = QgsFileWidget(self)
        self._picker.setStorageMode(
            _storage_mode(
                "GetDirectory" if definition.type is SettingType.DIRECTORY else "GetFile"
            )
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._picker)

    def set_value(self, value: Any) -> None:
        self._picker.setFilePath("" if value is None else str(value))

    def value(self) -> str:
        return (self._picker.filePath() or "").strip()


class CrsEditor(QWidget):
    """A CRS, chosen with QGIS's selector, stored as its authority code.

    "Not set" is a choice the selector offers, because it is the default:
    GeoComp does not assume a CRS (``specs/15`` section 2.1).
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        from qgis.gui import QgsProjectionSelectionWidget

        super().__init__(parent)
        self._selector = QgsProjectionSelectionWidget(self)
        options = getattr(QgsProjectionSelectionWidget, "CrsOption", QgsProjectionSelectionWidget)
        self._selector.setOptionVisible(options.CrsNotSet, True)
        self._selector.setNotSetText(_tr("Not set — each run states its CRS"))
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._selector)

    def set_value(self, value: Any) -> None:
        from qgis.core import QgsCoordinateReferenceSystem

        self._selector.setCrs(QgsCoordinateReferenceSystem(str(value or "")))

    def value(self) -> str:
        crs = self._selector.crs()
        return crs.authid() if crs.isValid() else ""


def _locale() -> QLocale:
    """The user's locale for numbers, without group separators: ``1013.25``, ``1013,25``."""
    locale = QLocale()
    locale.setNumberOptions(QLocale.NumberOption.OmitGroupSeparator)
    return locale


def _number(value: Any) -> str:
    """The shortest text that reads back as exactly *value*.

    Exactly, because OK writes every value that differs from its default: a
    default shown to twelve digits and read back would differ in its last bits,
    and every press of OK would store an override nobody made.
    """
    shortest = getattr(QLocale, "FloatingPointPrecisionOption", QLocale).FloatingPointShortest
    return _locale().toString(float(value), "g", shortest)


def _set_editor_value(editor: QWidget, value: Any) -> None:
    if hasattr(editor, "set_value"):
        editor.set_value(value)
    elif isinstance(editor, QComboBox):
        index = editor.findData(value)
        editor.setCurrentIndex(index if index >= 0 else 0)
    elif isinstance(editor, QCheckBox):
        editor.setChecked(bool(value))
    elif isinstance(editor, QSpinBox):
        editor.setValue(int(value))


def _editor_value(editor: QWidget) -> Any:
    if hasattr(editor, "value") and not isinstance(editor, QSpinBox):
        return editor.value()
    if isinstance(editor, QComboBox):
        return editor.currentData()
    if isinstance(editor, QCheckBox):
        return editor.isChecked()
    if isinstance(editor, QSpinBox):
        return editor.value()
    return None
