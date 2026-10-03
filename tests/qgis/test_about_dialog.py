# SPDX-License-Identifier: GPL-2.0-or-later
"""The About dialog: GeoComp's licence, the engines' versions and theirs (specs/21 criterion 8)."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.qgis


@pytest.fixture
def body(qgis_app):
    from geocomp.gui.about_dialog import AboutDialog

    dialog = AboutDialog()
    try:
        yield dialog._body()
    finally:
        dialog.deleteLater()


def test_it_states_geocomps_licence(body):
    assert "GNU General Public License" in body


def test_each_engine_with_its_licence_and_what_is_installed(body):
    from geocomp.services.engines import engine_status

    for engine in engine_status():
        assert engine.name in body and engine.licence in body
        if engine.version is None:
            assert "not installed" in body
        else:
            assert engine.version.version in body


def test_it_no_longer_says_the_engines_are_still_to_come(body):
    """It did until P12c, three phases after both had arrived."""
    assert "later development phases" not in body


def test_the_system_report_says_the_same(qgis_app):
    """The report a support request attaches said both engines were "not
    integrated yet" until P12c."""
    from geocomp.algorithms.project.system_report import SystemReportAlgorithm
    from geocomp.services.engines import engine_status

    rows = SystemReportAlgorithm()._collect_engines()
    assert [name for name, _state, _version in rows] == [e.name for e in engine_status()]
    for (_name, state, version), engine in zip(rows, engine_status(), strict=True):
        if engine.version is None:
            assert state == "Not installed" and version == ""
        else:
            assert engine.version.version in version
