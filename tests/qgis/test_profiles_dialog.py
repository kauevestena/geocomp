# SPDX-License-Identifier: GPL-2.0-or-later
"""The instrument profiles window (FR-061, FR-069; specs/15 §2.2).

What is edited and what each operation does is tested without QGIS in
``tests/test_profile_editing.py``. Here, the window: a library opened from the
file an algorithm reads, edited through the form in the units a surveyor reads,
saved back, and reached from Global Settings.
"""

from __future__ import annotations

import json
import math

import pytest

pytestmark = pytest.mark.qgis

ARCSECONDS = 180.0 * 3600.0 / math.pi


@pytest.fixture
def library_file(tmp_path):
    from geocomp.core.instruments.editing import add_profile
    from geocomp.core.instruments.profiles import ProfileLibrary

    library = ProfileLibrary()
    add_profile(library, "instruments", "TS-1")
    add_profile(library, "reflectors", "prism-1")
    add_profile(library, "levels", "level-1")
    path = tmp_path / "profiles.json"
    path.write_text(json.dumps(library.to_dict()), encoding="utf-8")
    return path


@pytest.fixture
def window(qgis_app, library_file):
    from geocomp.gui.profiles_dialog import ProfileLibraryDialog

    dialog = ProfileLibraryDialog(str(library_file))
    yield dialog
    dialog.dirty = False
    dialog.deleteLater()


def _reload(path):
    from geocomp.core.instruments.profiles import ProfileLibrary

    return ProfileLibrary.from_dict(json.loads(path.read_text(encoding="utf-8")))


class TestTheFile:
    def test_every_kind_has_its_tab_and_lists_its_profiles(self, window):
        assert window.tabs.count() == 5
        assert window.pages["instruments"].list.count() == 1
        assert window.pages["levels"].current_id() == "level-1"
        assert window.pages["gravimeters"].list.count() == 0

    def test_an_edit_saved_is_what_a_run_reads(self, window, library_file):
        """Seconds of arc in the form, radians in the file the algorithms read."""
        page = window.pages["instruments"]
        value, sigma = page.editors["vertical_index"]
        value.setValue(12.0)
        sigma.setValue(1.5)
        page.editors["edm_additive"][0].setValue(-17.4)
        page.editors["serial_number"].setText("S-1234")
        assert page.apply()
        assert window.dirty
        assert window.save()
        assert not window.dirty
        stored = _reload(library_file).instruments["TS-1"]
        assert stored.vertical_index.value == pytest.approx(12.0 / ARCSECONDS)
        assert stored.vertical_index.std_dev == pytest.approx(1.5 / ARCSECONDS)
        assert stored.edm_additive.value == pytest.approx(-0.0174)
        assert stored.serial_number == "S-1234"

    def test_a_refused_value_is_said_and_changes_nothing(self, window):
        page = window.pages["instruments"]
        before = window.library.instruments["TS-1"]
        page.editors["sigma_direction"].setValue(-1.0)
        assert not page.apply()
        assert window.library.instruments["TS-1"] is before
        assert "negative" in window.status.text()

    def test_a_file_that_is_not_a_library_is_said(self, window, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("[1, 2]", encoding="utf-8")
        assert not window.open_library(str(bad))
        assert "could not be read" in window.status.text()


class TestTheOperations:
    def test_add_duplicate_default_and_delete(self, window):
        page = window.pages["instruments"]
        assert page.add("TS-2")
        assert page.current_id() == "TS-2"
        assert page.duplicate("TS-3")
        assert page.make_default()
        assert window.library.default_instrument == "TS-3"
        assert page.delete()
        assert set(window.library.instruments) == {"TS-1", "TS-2"}
        assert window.library.default_instrument == ""

    def test_an_id_in_use_is_refused(self, window):
        assert not window.pages["instruments"].add("TS-1")
        assert "already in the library" in window.status.text()

    def test_import_adds_and_keeps_what_is_there(self, window, tmp_path):
        from geocomp.core.instruments.editing import add_profile
        from geocomp.core.instruments.profiles import ProfileLibrary

        other = ProfileLibrary()
        add_profile(other, "instruments", "TS-1")
        add_profile(other, "gravimeters", "CG-5")
        path = tmp_path / "theirs.json"
        path.write_text(json.dumps(other.to_dict()), encoding="utf-8")
        added, kept = window.import_file(str(path))
        assert added == ["gravimeters/CG-5"] and kept == ["instruments/TS-1"]
        assert window.pages["gravimeters"].list.count() == 1
        assert "instruments/TS-1" in window.status.text()

    def test_export_writes_the_selected_profiles_alone(self, window, tmp_path):
        path = tmp_path / "exported.json"
        assert window.export_file(str(path), {"levels": ["level-1"]}) == 1
        exported = _reload(path)
        assert list(exported.levels) == ["level-1"] and exported.instruments == {}

    def test_unsaved_changes_are_asked_about_before_closing(self, window, monkeypatch):
        from geocomp.gui import profiles_dialog

        asked = []
        monkeypatch.setattr(
            profiles_dialog.QMessageBox,
            "question",
            lambda *args: asked.append(args) or profiles_dialog.QMessageBox.StandardButton.No,
        )
        window.pages["levels"].add("level-2")
        window.reject()
        assert asked and window.dirty  # still open, nothing lost


class TestFromGlobalSettings:
    def test_each_technique_page_leads_to_its_tab(self, qgis_app):
        from qgis.PyQt.QtWidgets import QPushButton

        from geocomp.gui.settings_dialog import GlobalSettingsDialog

        settings = GlobalSettingsDialog()
        try:
            for kind in ("instruments", "levels", "gravimeters"):
                assert settings.findChild(QPushButton, f"geocompProfiles_{kind}") is not None
            opened = settings.open_profiles("levels")
            assert opened.tabs.currentWidget() is opened.pages["levels"]
            opened.dirty = False
            opened.close()
        finally:
            settings.deleteLater()
