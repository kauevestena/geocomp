# SPDX-License-Identifier: GPL-2.0-or-later
"""The QGIS plugin entry point.

Owns the plugin lifecycle: install translations, register the Processing
provider, build the menu and toolbar, and take all of it down again cleanly on
unload (FR-001, FR-002, FR-006, FR-007).

``unload`` matters more than its size suggests. Reloading during development
must leave nothing behind -- a duplicated menu or a stale provider is the most
common way a plugin becomes confusing to work on.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from qgis.core import QgsApplication
from qgis.PyQt.QtCore import QCoreApplication, QTranslator
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QToolBar

from geocomp.core.number_format import set_display_locale
from geocomp.core.version import __version__
from geocomp.i18n import install_translator, resolve_locale
from geocomp.provider import GeoCompProvider
from geocomp.resources import icon_path

if TYPE_CHECKING:
    from qgis.gui import QgisInterface

__all__ = ["GeoCompPlugin"]

_TR_CONTEXT = "GeoCompPlugin"


def _tr(text: str) -> str:
    return QCoreApplication.translate(_TR_CONTEXT, text)


#: The algorithms on the toolbar (specs/15 section 1.3): object name, id, and
#: the QGIS theme icon that says what it does.
TOOLBAR_ALGORITHMS = (
    ("geocompToolbarInspect", "geocomp:analysis_network_inspect", "/mActionIdentify.svg"),
    ("geocompToolbarAdjust", "geocomp:analysis_network_adjust", "/processingAlgorithm.svg"),
    ("geocompToolbarStore", "geocomp:project_store", "/mActionFileSave.svg"),
)


def _theme_icon(name: str) -> QIcon:
    """A QGIS theme icon, or GeoComp's own where this QGIS has no such icon.

    Theme icon names are not an API, and a missing one is an empty button.
    """
    icon = QgsApplication.getThemeIcon(name)
    return QIcon(icon_path("geocomp.svg")) if icon.isNull() else icon


class GeoCompPlugin:
    """Lifecycle for the GeoComp plugin.

    Args:
        iface: The ``QgisInterface`` QGIS hands to ``classFactory``.
    """

    def __init__(self, iface: QgisInterface) -> None:
        self.iface = iface
        self._provider: GeoCompProvider | None = None
        self._translator: QTranslator | None = None
        self._menu = None
        self._toolbar: QToolBar | None = None
        self._toolbar_actions: list[QAction] = []
        self._run_again: QAction | None = None
        self._last_algorithm: str | None = None
        self._plugin_menu_actions: list[QAction] = []
        self._series_panel = None
        self._basemap_offer = None
        self._results_panel = None

    # -- lifecycle -------------------------------------------------------

    def initGui(self) -> None:
        """Called by QGIS once the GUI is available."""
        from geocomp.gui.menu import GeoCompMenu
        from geocomp.services.logging import log
        from geocomp.services.settings_service import settings

        # Translations first: everything built below reads its labels through
        # the translation layer, so installing later would leave the menu in
        # the source language until the next restart (FR-092).
        self._translator = install_translator(_language_override())
        # And the numbers in the language the words came out in: a decimal
        # comma beside English words, or a point beside Portuguese ones, would
        # be the mixture the override exists to prevent (FR-094).
        set_display_locale(
            resolve_locale(_language_override()) if self._translator is not None else "en"
        )

        settings.apply_log_level()
        log.info("GeoComp starting", version=__version__)

        self._provider = GeoCompProvider()
        QgsApplication.processingRegistry().addProvider(self._provider)

        self._menu = GeoCompMenu(
            self.iface.mainWindow(),
            run_algorithm=self.run_algorithm,
            open_settings=self.open_settings,
        )
        self._menu.build(self.iface.mainWindow().menuBar())

        self._build_toolbar()
        self._build_series_panel()
        self._build_results_panel()
        self._build_plugin_menu_entries()
        self._build_basemap_offer()

        log.info("GeoComp ready")

    def unload(self) -> None:
        """Remove every element this plugin created (FR-006)."""
        from geocomp.services.logging import log

        if self._menu is not None:
            self._menu.unload()
            self._menu = None

        for action in self._toolbar_actions:
            action.setParent(None)
            action.deleteLater()
        self._toolbar_actions.clear()
        self._run_again = None

        if self._toolbar is not None:
            self._toolbar.setParent(None)
            self._toolbar.deleteLater()
            self._toolbar = None

        for action in self._plugin_menu_actions:
            self.iface.removePluginMenu("&GeoComp", action)
            action.setParent(None)
            action.deleteLater()
        self._plugin_menu_actions.clear()

        if self._results_panel is not None:
            from geocomp.gui.results_panel import detach_from_project as detach_results

            detach_results(self._results_panel)
            self.iface.removeDockWidget(self._results_panel)
            self._results_panel.setParent(None)
            self._results_panel.deleteLater()
            self._results_panel = None

        if self._basemap_offer is not None:
            self._basemap_offer.unload()
            self._basemap_offer = None

        if self._series_panel is not None:
            from geocomp.gui.time_series_panel import detach_from_project

            detach_from_project(self._series_panel)
            self.iface.removeDockWidget(self._series_panel)
            self._series_panel.setParent(None)
            self._series_panel.deleteLater()
            self._series_panel = None

        if self._provider is not None:
            QgsApplication.processingRegistry().removeProvider(self._provider)
            self._provider = None

        if self._translator is not None:
            QCoreApplication.removeTranslator(self._translator)
            self._translator = None

        log.info("GeoComp unloaded")

    # -- construction ----------------------------------------------------

    def _build_toolbar(self) -> None:
        """Create the GeoComp toolbar (FR-007, specs/15 section 1.3).

        Hidden when ``interface.show_toolbar`` is off. Created regardless, so
        toggling the setting does not require a restart.

        Until P12c-13 it held one action, Global Settings, where specs/15 lists
        the frequent ones: inspecting and adjusting a network, saving to the
        project store, running the last algorithm again and the results panel.
        Each algorithm opens the same dialog its menu item does (ADR-0005).
        """
        from geocomp.services.settings_service import settings

        self._toolbar = self.iface.addToolBar(_tr("GeoComp"))
        self._toolbar.setObjectName("geocompToolbar")
        registry = QgsApplication.processingRegistry()

        for name, algorithm_id, icon in TOOLBAR_ALGORITHMS:
            algorithm = registry.algorithmById(algorithm_id)
            label = algorithm.displayName() if algorithm is not None else algorithm_id
            action = QAction(_theme_icon(icon), label, self.iface.mainWindow())
            action.setObjectName(name)
            action.triggered.connect(
                lambda _checked=False, algorithm_id=algorithm_id: self.run_algorithm(algorithm_id)
            )
            self._add_to_toolbar(action)

        self._run_again = QAction(
            _theme_icon("/mActionRedo.svg"),
            _tr("Run the last GeoComp algorithm again"),
            self.iface.mainWindow(),
        )
        self._run_again.setObjectName("geocompToolbarRunAgain")
        self._run_again.setEnabled(False)
        self._run_again.triggered.connect(self.run_again)
        self._add_to_toolbar(self._run_again)

        results = QAction(
            _theme_icon("/mActionOpenTable.svg"), _tr("Results panel"), self.iface.mainWindow()
        )
        results.setObjectName("geocompToolbarResults")
        results.triggered.connect(self.open_results_panel)
        self._add_to_toolbar(results)

        settings_action = QAction(
            QIcon(icon_path("geocomp.svg")),
            _tr("GeoComp Global Settings"),
            self.iface.mainWindow(),
        )
        settings_action.setObjectName("geocompToolbarSettings")
        settings_action.triggered.connect(self.open_settings)
        self._add_to_toolbar(settings_action)

        self._toolbar.setVisible(bool(settings.value("interface.show_toolbar")))

    def _add_to_toolbar(self, action: QAction) -> None:
        self._toolbar.addAction(action)
        self._toolbar_actions.append(action)

    def _build_series_panel(self) -> None:
        """The time-series panel (FR-903), docked and hidden until wanted.

        It shows itself when a layer written by *Time series and velocities* is
        added to the project, and is reachable from Plugins ▸ GeoComp and from
        QGIS's own panel list at any time.
        """
        from qgis.PyQt.QtCore import Qt

        from geocomp.gui.time_series_panel import TimeSeriesPanel, attach_to_project

        self._series_panel = TimeSeriesPanel(self.iface.mainWindow())
        self.iface.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._series_panel)
        self._series_panel.hide()
        attach_to_project(self._series_panel)

    def _build_basemap_offer(self) -> None:
        """Offer a base map when result layers arrive (FR-167, ``basemaps.offer_on_result_layers``)."""
        from geocomp.gui.basemap_offer import BaseMapOffer

        self._basemap_offer = BaseMapOffer(self.iface.messageBar())

    def _build_results_panel(self) -> None:
        """The results panel (specs/15 section 4), docked and hidden until wanted.

        It lists each run whose result layers reach the project, and links its
        rows to their features on the map -- which it zooms to -- and its
        stations to the time-series panel.
        """
        from qgis.PyQt.QtCore import Qt

        from geocomp.gui.results_panel import ResultsPanel, attach_to_project

        canvas = self.iface.mapCanvas()
        self._results_panel = ResultsPanel(
            self.iface.mainWindow(),
            zoom=canvas.zoomToSelected,
            series_panel=self._series_panel,
        )
        self.iface.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._results_panel)
        self._results_panel.hide()
        attach_to_project(self._results_panel)

    def _build_plugin_menu_entries(self) -> None:
        """Add the conventional Plugins ▸ GeoComp entries.

        The GeoComp menu itself presents exactly the entries FR-003
        specifies -- five survey techniques, Analysis, and Global settings -- so
        About lives here instead, where QGIS users already look for it, rather
        than becoming one more entry that would distort that structure.
        """
        about = QAction(_tr("About GeoComp…"), self.iface.mainWindow())
        about.setObjectName("geocompPluginMenuAbout")
        about.triggered.connect(self.open_about)
        self.iface.addPluginToMenu("&GeoComp", about)
        self._plugin_menu_actions.append(about)

        series = QAction(_tr("Time series panel"), self.iface.mainWindow())
        series.setObjectName("geocompPluginMenuTimeSeries")
        series.triggered.connect(self.open_series_panel)
        self.iface.addPluginToMenu("&GeoComp", series)
        self._plugin_menu_actions.append(series)

        results = QAction(_tr("Results panel"), self.iface.mainWindow())
        results.setObjectName("geocompPluginMenuResults")
        results.triggered.connect(self.open_results_panel)
        self.iface.addPluginToMenu("&GeoComp", results)
        self._plugin_menu_actions.append(results)

    # -- actions ---------------------------------------------------------

    def run_algorithm(self, algorithm_id: str) -> None:
        """Open the Processing dialog for *algorithm_id*.

        ADR-0005: menu items launch algorithms; they do not reimplement them.

        A few algorithms open a custom dialog first, because choosing their
        parameters needs something the generated dialog cannot show -- see
        ``geocomp.registry.CUSTOM_DIALOGS``. What that dialog produces is
        pre-filled into the same Processing dialog every other item opens, so
        there is still one implementation and one set of defaults.

        A cancelled custom dialog stops here. Falling through to the Processing
        dialog would re-prompt for something the user has just declined.

        The toolbar's *run again* repeats whatever was opened last, from the
        menu or the toolbar.
        """
        self._remember(algorithm_id)
        self._open_dialog(algorithm_id)

    def run_again(self) -> None:
        """Open the algorithm last launched from the menu again, if there was one."""
        if self._last_algorithm is not None:
            self.run_algorithm(self._last_algorithm)

    def _remember(self, algorithm_id: str) -> None:
        self._last_algorithm = algorithm_id
        if self._run_again is None:
            return
        algorithm = QgsApplication.processingRegistry().algorithmById(algorithm_id)
        name = algorithm.displayName() if algorithm is not None else algorithm_id
        self._run_again.setEnabled(True)
        self._run_again.setToolTip(_tr("Run again: %1").replace("%1", name))

    def _open_dialog(self, algorithm_id: str) -> None:
        from processing import execAlgorithmDialog

        from geocomp.gui.prompts import collect_parameters

        prefilled = collect_parameters(
            algorithm_id, self.iface.mainWindow(), self.iface.mapCanvas()
        )
        if prefilled is None:
            return
        execAlgorithmDialog(algorithm_id, prefilled)

    def open_settings(self) -> None:
        """Open Global Settings, then apply what changed that needs no restart.

        The toolbar follows its setting, and a change of interface mode refreshes the toolbox
        (``specs/15`` section 3).
        """
        from geocomp.gui.settings_dialog import GlobalSettingsDialog
        from geocomp.services.settings_service import settings

        mode = settings.value("interface.mode")
        dialog = GlobalSettingsDialog(self.iface.mainWindow())
        dialog.exec()
        if self._toolbar is not None:
            self._toolbar.setVisible(bool(settings.value("interface.show_toolbar")))
        # specs/15 section 3: the mode switches without a restart. A dialog
        # builds its algorithm afresh, but the toolbox lists the provider's own.
        if settings.value("interface.mode") != mode and self._provider is not None:
            self._provider.refreshAlgorithms()

    def open_series_panel(self) -> None:
        """Show the time-series panel and bring it to the front."""
        if self._series_panel is not None:
            self._series_panel.show()
            self._series_panel.raise_()

    def open_results_panel(self) -> None:
        """Show the results panel and bring it to the front."""
        if self._results_panel is not None:
            self._results_panel.show()
            self._results_panel.raise_()

    def open_about(self) -> None:
        """Show the About dialog."""
        from geocomp.gui.about_dialog import AboutDialog

        AboutDialog(self.iface.mainWindow()).exec()


def _language_override() -> str | None:
    """Read ``interface.language`` before the settings service is available.

    ``initGui`` installs translations before anything else, so this reads
    ``QgsSettings`` directly rather than depending on a service that has not
    been configured yet.
    """
    from qgis.core import QgsSettings

    from geocomp.services.settings_service import SETTINGS_PREFIX

    value = QgsSettings().value(f"{SETTINGS_PREFIX}/interface.language", None)
    return str(value) if value else None
