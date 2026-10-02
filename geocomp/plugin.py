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

from qgis.core import QgsApplication
from qgis.PyQt.QtCore import QCoreApplication, QTranslator
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QToolBar

from geocomp.core.number_format import set_display_locale
from geocomp.core.version import __version__
from geocomp.i18n import install_translator, resolve_locale
from geocomp.provider import GeoCompProvider
from geocomp.resources import icon_path

__all__ = ["GeoCompPlugin"]

_TR_CONTEXT = "GeoCompPlugin"


def _tr(text: str) -> str:
    return QCoreApplication.translate(_TR_CONTEXT, text)


class GeoCompPlugin:
    """Lifecycle for the GeoComp plugin.

    Args:
        iface: The ``QgisInterface`` QGIS hands to ``classFactory``.
    """

    def __init__(self, iface) -> None:
        self.iface = iface
        self._provider: GeoCompProvider | None = None
        self._translator: QTranslator | None = None
        self._menu = None
        self._toolbar: QToolBar | None = None
        self._toolbar_actions: list[QAction] = []
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
        """Create the GeoComp toolbar (FR-007).

        Hidden when ``interface.show_toolbar`` is off. Created regardless, so
        toggling the setting does not require a restart.
        """
        from geocomp.services.settings_service import settings

        self._toolbar = self.iface.addToolBar(_tr("GeoComp"))
        self._toolbar.setObjectName("geocompToolbar")

        settings_action = QAction(
            QIcon(icon_path("geocomp.svg")),
            _tr("GeoComp Global Settings"),
            self.iface.mainWindow(),
        )
        settings_action.setObjectName("geocompToolbarSettings")
        settings_action.triggered.connect(self.open_settings)
        self._toolbar.addAction(settings_action)
        self._toolbar_actions.append(settings_action)

        self._toolbar.setVisible(bool(settings.value("interface.show_toolbar")))

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
        """
        from processing import execAlgorithmDialog

        from geocomp.gui.prompts import collect_parameters

        prefilled = collect_parameters(
            algorithm_id, self.iface.mainWindow(), self.iface.mapCanvas()
        )
        if prefilled is None:
            return
        execAlgorithmDialog(algorithm_id, prefilled)

    def open_settings(self) -> None:
        from geocomp.gui.settings_dialog import GlobalSettingsDialog

        dialog = GlobalSettingsDialog(self.iface.mainWindow())
        dialog.exec()
        if self._toolbar is not None:
            from geocomp.services.settings_service import settings

            self._toolbar.setVisible(bool(settings.value("interface.show_toolbar")))

    def open_series_panel(self) -> None:
        if self._series_panel is not None:
            self._series_panel.show()
            self._series_panel.raise_()

    def open_results_panel(self) -> None:
        if self._results_panel is not None:
            self._results_panel.show()
            self._results_panel.raise_()

    def open_about(self) -> None:
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
