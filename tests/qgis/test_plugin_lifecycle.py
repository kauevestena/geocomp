# SPDX-License-Identifier: GPL-2.0-or-later
"""The plugin loads, unloads without a trace, and reloads without duplicates (FR-002, FR-003, FR-006).

``specs/15`` criteria 1 and 3, and §1.4's *a specific, tested condition* --
which until the P12c audit no test was. The plugin needs a main window, a
message bar and a map canvas, so it runs in a QGIS of its own with a stand-in
``iface``: the tier's shared application has no GUI, and its registry already
holds the provider, which would hide whether the plugin's own registration and
removal work.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.qgis

REPO_ROOT = Path(__file__).resolve().parents[2]

#: The GeoComp menu, top to bottom: FR-003's eight entries, the separator
#: before the last.
MENU = [
    "geocompMenu_total_station",
    "geocompMenu_level",
    "geocompMenu_gnss",
    "geocompMenu_gravimetry",
    "geocompMenu_integration",
    "geocompMenu_analysis",
    "geocompMenu_project",
    "---",
    "geocompMenuAction_global_settings",
]

SCRIPT = r"""
import json, sys
from qgis.core import QgsApplication
from qgis.gui import QgsMapCanvas, QgsMessageBar
from qgis.PyQt.QtCore import QCoreApplication, QEvent
from qgis.PyQt.QtWidgets import QDockWidget, QMainWindow, QToolBar

app = QgsApplication([], True)
app.initQgis()


class Iface:
    def __init__(self):
        self.window = QMainWindow()
        self.bar = QgsMessageBar()
        self.canvas = QgsMapCanvas()
        self.plugin_menu = []

    def mainWindow(self):
        return self.window

    def messageBar(self):
        return self.bar

    def mapCanvas(self):
        return self.canvas

    def addToolBar(self, name):
        return self.window.addToolBar(name)

    def addDockWidget(self, area, dock):
        self.window.addDockWidget(area, dock)

    def removeDockWidget(self, dock):
        self.window.removeDockWidget(dock)

    def addPluginToMenu(self, name, action):
        self.plugin_menu.append(action)

    def removePluginMenu(self, name, action):
        self.plugin_menu.remove(action)


def settle():
    app.processEvents()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    app.processEvents()


def state(iface):
    bar = iface.window.menuBar()
    menus = [a.menu() for a in bar.actions() if a.menu() is not None]
    ours = [m for m in menus if m.objectName() == "geocompMenu"]
    entries = []
    if ours:
        for action in ours[0].actions():
            if action.isSeparator():
                entries.append("---")
            elif action.menu() is not None:
                entries.append(action.menu().objectName())
            else:
                entries.append(action.objectName())
    window = iface.window
    return {
        "menus": len(ours),
        "entries": entries,
        "toolbars": len([t for t in window.findChildren(QToolBar) if t.parent() is window]),
        "docks": len([d for d in window.findChildren(QDockWidget) if d.parent() is window]),
        "plugin_menu": len(iface.plugin_menu),
        "provider": QgsApplication.processingRegistry().providerById("geocomp") is not None,
        "algorithms": len(
            [a for a in QgsApplication.processingRegistry().algorithms() if a.provider().id() == "geocomp"]
        ),
    }


from geocomp import classFactory

iface = Iface()
before = state(iface)
plugin = classFactory(iface)
plugin.initGui()
loaded = state(iface)
plugin.unload()
settle()
unloaded = state(iface)
again = classFactory(iface)
again.initGui()
reloaded = state(iface)
again.unload()
settle()
print(json.dumps({"before": before, "loaded": loaded, "unloaded": unloaded, "reloaded": reloaded}))
app.exitQgis()
"""


@pytest.fixture(scope="module")
def lifecycle(qgis_app, tmp_path_factory):
    # A profile and an authentication database of its own, so nothing the
    # plugin reads or writes touches a developer's QGIS.
    environment = dict(
        os.environ,
        QT_QPA_PLATFORM="offscreen",
        # This interpreter's own path, so the child finds QGIS where the parent did.
        PYTHONPATH=os.pathsep.join([str(REPO_ROOT), *sys.path]),
        QGIS_CUSTOM_CONFIG_PATH=str(tmp_path_factory.mktemp("qgis-profile")),
        QGIS_AUTH_DB_DIR_PATH=str(tmp_path_factory.mktemp("qgis-auth")),
    )
    completed = subprocess.run(
        [sys.executable, "-c", SCRIPT],
        capture_output=True,
        text=True,
        env=environment,
        timeout=300,
        check=False,
    )
    lines = [line for line in completed.stdout.splitlines() if line.startswith("{")]
    assert completed.returncode == 0 and lines, completed.stderr[-4000:]
    return json.loads(lines[-1])


class TestLoading:
    def test_the_menu_is_on_the_menu_bar_with_its_eight_entries_in_order(self, lifecycle):
        """FR-002 and FR-003: top level, not under Plugins; the separator before
        Global Settings."""
        assert lifecycle["loaded"]["menus"] == 1
        assert lifecycle["loaded"]["entries"] == MENU

    def test_the_provider_toolbar_panels_and_plugin_entries_arrive(self, lifecycle):
        loaded, before = lifecycle["loaded"], lifecycle["before"]
        assert loaded["provider"] and loaded["algorithms"] > 40
        assert loaded["toolbars"] == before["toolbars"] + 1
        # The time series panel and the results panel.
        assert loaded["docks"] == before["docks"] + 2
        assert loaded["plugin_menu"] == 3


class TestUnloading:
    def test_nothing_the_plugin_made_remains(self, lifecycle):
        """FR-006: the menu, the toolbar, the provider, the panels, the entries."""
        assert lifecycle["unloaded"] == lifecycle["before"]


class TestReloading:
    def test_a_second_load_is_the_first_load_again(self, lifecycle):
        """No duplicate menu, toolbar or panel, which is what a development
        reload would show first."""
        assert lifecycle["reloaded"] == lifecycle["loaded"]
