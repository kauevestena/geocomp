# SPDX-License-Identifier: GPL-2.0-or-later
"""Every setting can be set from the window that exists to set it (phase P12a).

``specs/15-ui-menu-and-settings.md`` section 2.3, *found in P8b*: the window
built editors for choices, switches and whole numbers only, and showed 36 of 61
settings as *(not editable in this version)* -- every floating-point one, every
path, the CRS. They resolved correctly and could not be set. P12a gives each
type its editor; these tests hold the window to it, and to not storing what the
user did not change.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.qgis


@pytest.fixture
def stored(qgis_app):
    """Every GeoComp global setting as stored, restored afterwards whatever the test wrote."""
    from qgis.core import QgsSettings

    from geocomp.services.settings_service import SETTINGS_PREFIX

    def snapshot() -> dict[str, object]:
        store = QgsSettings()
        return {
            key: store.value(key)
            for key in store.allKeys()
            if key.startswith(f"{SETTINGS_PREFIX}/")
        }

    before = snapshot()
    yield snapshot
    store = QgsSettings()
    for key in set(snapshot()) | set(before):
        if key in before:
            store.setValue(key, before[key])
        else:
            store.remove(key)


@pytest.fixture
def dialog(qgis_app, stored):
    from geocomp.gui.settings_dialog import GlobalSettingsDialog

    window = GlobalSettingsDialog()
    yield window
    window.deleteLater()


def test_every_setting_has_an_editor(dialog):
    from qgis.PyQt.QtWidgets import QLabel

    from geocomp.core.settings_def import SETTINGS

    uneditable = sorted(key for key, editor in dialog._editors.items() if isinstance(editor, QLabel))
    assert not uneditable, f"shown as not editable: {uneditable}"
    assert set(dialog._editors) == {definition.key for definition in SETTINGS}


def test_every_editor_reads_back_exactly_what_it_was_given(dialog):
    """A float shown to twelve digits and read back differs in its last bits."""
    from geocomp.services.settings_service import settings

    values = dialog.values()
    mismatched = sorted(key for key, value in values.items() if value != settings.value(key))
    assert not mismatched, f"the editor does not hold the effective value: {mismatched}"


def test_ok_with_nothing_changed_stores_nothing(dialog, stored):
    before = stored()
    dialog.accept()
    assert stored() == before


def test_a_typed_number_is_saved(dialog):
    from geocomp.services.settings_service import settings

    dialog._editors["total_station.default_temperature_celsius"].setText("31.5")
    dialog.accept()
    assert settings.value("total_station.default_temperature_celsius") == 31.5


def test_scientific_notation_is_a_number(dialog):
    """The traverse tolerance is 1.45e-4 rad; nobody should have to type its zeros."""
    from geocomp.services.settings_service import settings

    dialog._editors["total_station.traverse_angular_tolerance_per_station"].setText("1e-4")
    dialog.accept()
    assert settings.value("total_station.traverse_angular_tolerance_per_station") == 1.0e-4


def test_a_number_out_of_range_is_not_saved_and_is_named(dialog):
    from qgis.PyQt.QtWidgets import QDialog

    from geocomp.services.settings_service import settings

    before = settings.value("stochastic.confidence_level")
    dialog._editors["stochastic.confidence_level"].setText("5")
    dialog.accept()
    assert dialog.result() != QDialog.DialogCode.Accepted
    assert "Confidence" in dialog._error.text()
    assert settings.value("stochastic.confidence_level") == before


def test_a_crs_is_saved_by_its_authority_code(dialog):
    from geocomp.services.settings_service import settings

    dialog._editors["reference_systems.preferred_crs"].set_value("EPSG:31983")
    dialog.accept()
    assert settings.value("reference_systems.preferred_crs") == "EPSG:31983"


def test_a_directory_and_a_text_are_saved(dialog, tmp_path):
    from geocomp.services.settings_service import settings

    dialog._editors["gnss.product_cache"].set_value(str(tmp_path))
    dialog._editors["gnss.product_services"].setText("noaa-ncn, other")
    dialog.accept()
    assert settings.value("gnss.product_cache") == str(tmp_path)
    assert settings.value("gnss.product_services") == "noaa-ncn, other"
