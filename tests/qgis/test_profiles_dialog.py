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


class TestTheLibraryARunReads:
    """Each technique's page names the library its runs read (P12c-17)."""

    @pytest.fixture
    def settings_window(self, qgis_app):
        from geocomp.gui.settings_dialog import GlobalSettingsDialog

        settings = GlobalSettingsDialog()
        yield settings
        settings.deleteLater()

    @staticmethod
    def _named(settings, key: str) -> str:
        from geocomp.gui.settings_dialog import _editor_value

        return _editor_value(settings._editors[key])

    @staticmethod
    def _name(settings, key: str, path: str) -> None:
        from geocomp.gui.settings_dialog import _set_editor_value

        _set_editor_value(settings._editors[key], path)

    def test_the_page_opens_the_library_it_names(self, settings_window, library_file):
        """As the page shows it, before OK: the window is part of the same edit."""
        self._name(settings_window, "level.profile_library", str(library_file))
        opened = settings_window.open_profiles("levels")
        try:
            assert opened.path == str(library_file)
            assert opened.pages["levels"].current_id() == "level-1"
        finally:
            opened.close()

    def test_a_library_saved_where_none_was_named_is_entered_on_the_page(
        self, settings_window, tmp_path
    ):
        self._name(settings_window, "gravimeter.profile_library", "")
        opened = settings_window.open_profiles("gravimeters")
        assert opened.pages["gravimeters"].add("CG-5")
        path = tmp_path / "gravimeters.json"
        assert opened.save(str(path))
        opened.reject()
        assert self._named(settings_window, "gravimeter.profile_library") == str(path)

    def test_a_library_named_elsewhere_is_left_alone(self, settings_window, library_file, tmp_path):
        """Saved as another file, it is a copy: the page keeps the one it named."""
        self._name(settings_window, "total_station.profile_library", str(library_file))
        opened = settings_window.open_profiles("instruments")
        assert opened.save(str(tmp_path / "copy.json"))
        opened.reject()
        assert self._named(settings_window, "total_station.profile_library") == str(library_file)

    def test_a_named_library_not_yet_written_is_started_there(self, qgis_app, tmp_path):
        from geocomp.gui.profiles_dialog import ProfileLibraryDialog

        path = tmp_path / "later.json"
        dialog = ProfileLibraryDialog(str(path))
        try:
            assert dialog.path == str(path) and dialog.pages["instruments"].list.count() == 0
            assert "does not exist yet" in dialog.status.text()
            assert dialog.pages["instruments"].add("TS-9")
            assert dialog.save()
            assert list(_reload(path).instruments) == ["TS-9"]
        finally:
            dialog.dirty = False
            dialog.deleteLater()

    def test_a_run_given_no_library_reads_the_one_named(self, geocomp_provider, library_file, tmp_path):
        """The field book names no instrument; the named library's default is used."""
        from qgis.core import QgsApplication, QgsProcessingContext, QgsProcessingFeedback

        from geocomp.services.settings_service import settings
        from tests import reference_rd01 as rd01

        with settings.run_overrides({"total_station.profile_library": str(library_file)}):
            algorithm = QgsApplication.processingRegistry().algorithmById(
                "geocomp:totalstation_import_fieldbook"
            ).create({})
            _results, ok = algorithm.run(
                {"SOURCE": str(rd01.RAW), "OUTPUT_READINGS": str(tmp_path / "readings.json")},
                QgsProcessingContext(),
                QgsProcessingFeedback(),
                catchExceptions=False,
            )
        assert ok
        readings = json.loads((tmp_path / "readings.json").read_text(encoding="utf-8"))
        assert {setup["instrument_id"] for setup in readings["setups"]} == {"TS-1"}
