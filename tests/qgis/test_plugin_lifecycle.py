# SPDX-License-Identifier: GPL-2.0-or-later
"""The plugin loads, unloads without a trace, and reloads without duplicates (FR-002, FR-003, FR-006).

Since P14a it also opens the menu's windows (FR-010): one of each, brought
forward when chosen again, and every one of them gone -- with its sketch and
its hold on the map canvas -- when the plugin unloads.

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

#: The Total Station submenu: eight windows where eight launchers stood, in the
#: same order -- four built in P14a, four in P14b.
TOTAL_STATION = [
    ("geocompMenuAction_totalstation_fieldbook", "totalstation_fieldbook"),
    ("geocompMenuAction_totalstation_preprocess", "totalstation_preprocess"),
    ("geocompMenuAction_totalstation_traverse", "totalstation_traverse"),
    ("geocompMenuAction_totalstation_resection", "totalstation_resection"),
    ("geocompMenuAction_totalstation_intersection", "totalstation_intersection"),
    ("geocompMenuAction_totalstation_network", "totalstation_network"),
    ("geocompMenuAction_totalstation_trig_levelling", "totalstation_trig_levelling"),
    ("geocompMenuAction_totalstation_radiation", "totalstation_radiation"),
]

#: The toolbar, left to right: specs/15 section 1.3's frequent actions.
TOOLBAR = [
    "geocompToolbarInspect",
    "geocompToolbarAdjust",
    "geocompToolbarStore",
    "geocompToolbarRunAgain",
    "geocompToolbarResults",
    "geocompToolbarSettings",
]

SCRIPT = r"""
import faulthandler, json, signal, sys
faulthandler.enable()
if hasattr(faulthandler, "register") and hasattr(signal, "SIGTRAP"):
    faulthandler.register(signal.SIGTRAP, all_threads=True, chain=True)
from qgis.core import QgsApplication
from qgis.gui import QgsMapCanvas, QgsMessageBar
from qgis.PyQt.QtCore import QCoreApplication, QEvent
from qgis.PyQt.QtWidgets import QDialog, QDockWidget, QMainWindow, QMenu, QToolBar

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
    toolbars = [t for t in window.findChildren(QToolBar) if t.objectName() == "geocompToolbar"]
    return {
        "menus": len(ours),
        "entries": entries,
        "toolbar": [a.objectName() for t in toolbars for a in t.actions()],
        "toolbars": len([t for t in window.findChildren(QToolBar) if t.parent() is window]),
        "docks": len([d for d in window.findChildren(QDockWidget) if d.parent() is window]),
        "plugin_menu": len(iface.plugin_menu),
        "provider": QgsApplication.processingRegistry().providerById("geocomp") is not None,
        "algorithms": len(
            [a for a in QgsApplication.processingRegistry().algorithms() if a.provider().id() == "geocomp"]
        ),
        "windows": sorted(
            d.objectName() for d in window.findChildren(QDialog)
            if d.objectName().startswith("geocompWindow_")
        ),
        "canvas_items": len(iface.canvas.scene().items()),
    }


from geocomp import classFactory

iface = Iface()
before = state(iface)
plugin = classFactory(iface)
plugin.initGui()
loaded = state(iface)

# The toolbar's actions, with the dialog replaced by a record of what it opened.
opened = []
plugin._open_dialog = opened.append
(bar,) = [t for t in iface.window.findChildren(QToolBar) if t.objectName() == "geocompToolbar"]
actions = {a.objectName(): a for a in bar.actions()}
again = actions["geocompToolbarRunAgain"]
toolbar = {"again_before": again.isEnabled()}
actions["geocompToolbarInspect"].trigger()
toolbar["again_after"] = again.isEnabled()
toolbar["again_tip"] = again.toolTip()
again.trigger()
actions["geocompToolbarAdjust"].trigger()
again.trigger()
toolbar["opened"] = list(opened)

# The menu's Total Station items: windows and launchers, told apart by their data.
(station_menu,) = [
    m for m in iface.window.findChildren(QMenu) if m.objectName() == "geocompMenu_total_station"
]
items = {a.objectName(): a for a in station_menu.actions()}
windows = {
    "items": [[a.objectName(), a.data()] for a in station_menu.actions()],
    "labels": [a.text() for a in station_menu.actions()],
}
items["geocompMenuAction_totalstation_fieldbook"].trigger()
items["geocompMenuAction_totalstation_traverse"].trigger()
items["geocompMenuAction_totalstation_fieldbook"].trigger()
settle()
windows["open"] = sorted(plugin._windows.open_windows)
windows["shown"] = state(iface)["windows"]
windows["again_tip"] = again.toolTip()
windows["modal"] = [
    w.isModal() for w in iface.window.findChildren(QDialog) if w.objectName().startswith("geocompWindow_")
]
plugin_menu = {a.objectName(): a for a in iface.plugin_menu}
windows["plugin_menu"] = sorted(plugin_menu)
plugin_menu["geocompPluginMenuImportFieldBook"].trigger()
windows["preview_opened"] = opened[-1]

plugin.unload()
settle()
unloaded = state(iface)
again = classFactory(iface)
again.initGui()
reloaded = state(iface)
again.unload()
settle()
states = {"before": before, "loaded": loaded, "unloaded": unloaded, "reloaded": reloaded}
print(json.dumps({**states, "toolbar": toolbar, "windows": windows}))
app.exitQgis()
"""


@pytest.fixture(scope="module")
def lifecycle(qgis_app, tmp_path_factory, request):
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
    if completed.returncode != 0 or not lines:
        # Straight to the log as well, with capturing off: a later crash of the
        # suite would take the assertion's message with it.
        capture = request.config.pluginmanager.getplugin("capturemanager")
        with capture.global_and_fixture_disabled():
            sys.stderr.write(
                f"plugin lifecycle subprocess exited {completed.returncode}:\n"
                f"{completed.stderr[-4000:]}\n"
            )
            sys.stderr.flush()
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
        # About, the two panels, and the field-book import with its mapping preview.
        assert loaded["plugin_menu"] == 4


class TestTheToolbar:
    def test_it_holds_the_frequent_actions(self, lifecycle):
        """specs/15 section 1.3. Until P12c-13 it held Global Settings alone."""
        assert lifecycle["loaded"]["toolbar"] == TOOLBAR

    def test_its_algorithms_open_their_dialogs(self, lifecycle):
        opened = lifecycle["toolbar"]["opened"]
        assert opened[0] == "geocomp:analysis_network_inspect"
        assert opened[2] == "geocomp:analysis_network_adjust"

    def test_run_again_repeats_what_was_opened_last(self, lifecycle):
        toolbar = lifecycle["toolbar"]
        assert not toolbar["again_before"], "nothing has run yet"
        assert toolbar["again_after"]
        assert toolbar["opened"] == [
            "geocomp:analysis_network_inspect",
            "geocomp:analysis_network_inspect",
            "geocomp:analysis_network_adjust",
            "geocomp:analysis_network_adjust",
        ]
        assert "Inspect" in toolbar["again_tip"]


class TestTheWindows:
    """ADR-0010: the menu's items are windows, opened by the plugin."""

    def test_the_total_station_items_are_windows_where_they_were_rebuilt(self, lifecycle):
        assert lifecycle["windows"]["items"] == [list(item) for item in TOTAL_STATION]

    def test_a_window_item_says_it_opens_something(self, lifecycle):
        labels = lifecycle["windows"]["labels"]
        assert labels[0] == "Field book…"
        assert labels[2] == "Traverse…"

    def test_one_of_each_is_open_and_it_does_not_block_the_map(self, lifecycle):
        windows = lifecycle["windows"]
        assert windows["open"] == ["totalstation_fieldbook", "totalstation_traverse"]
        assert windows["shown"] == [
            "geocompWindow_totalstation_fieldbook",
            "geocompWindow_totalstation_traverse",
        ]
        assert windows["modal"] == [False, False]

    def test_run_again_opens_the_last_window_again(self, lifecycle):
        assert "Field book" in lifecycle["windows"]["again_tip"]

    def test_the_field_book_file_route_keeps_its_mapping_preview(self, lifecycle):
        """FR-160's preview is reached from Plugins ▸ GeoComp once the menu's
        item is the typed field book."""
        windows = lifecycle["windows"]
        assert "geocompPluginMenuImportFieldBook" in windows["plugin_menu"]
        assert windows["preview_opened"] == "geocomp:totalstation_import_fieldbook"

    def test_no_window_outlives_the_plugin(self, lifecycle):
        assert lifecycle["unloaded"]["windows"] == []
        assert lifecycle["unloaded"]["canvas_items"] == lifecycle["before"]["canvas_items"]


class TestUnloading:
    def test_nothing_the_plugin_made_remains(self, lifecycle):
        """FR-006: the menu, the toolbar, the provider, the panels, the entries."""
        assert lifecycle["unloaded"] == lifecycle["before"]


class TestReloading:
    def test_a_second_load_is_the_first_load_again(self, lifecycle):
        """No duplicate menu, toolbar or panel, which is what a development
        reload would show first."""
        assert lifecycle["reloaded"] == lifecycle["loaded"]
