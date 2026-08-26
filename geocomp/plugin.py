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

from geocomp.core.version import __version__
from geocomp.i18n import install_translator
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
        self._build_plugin_menu_entries()

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
            QIcon(icon_path("geocomp.svg")), _tr("GeoComp Global Settings"), self.iface.mainWindow()
        )
        settings_action.setObjectName("geocompToolbarSettings")
        settings_action.triggered.connect(self.open_settings)
        self._toolbar.addAction(settings_action)
        self._toolbar_actions.append(settings_action)

        self._toolbar.setVisible(bool(settings.value("interface.show_toolbar")))

    def _build_plugin_menu_entries(self) -> None:
        """Add the conventional Plugins ▸ GeoComp entries.

        The GeoComp menu itself presents exactly the six technique-oriented
        entries FR-003 specifies, so About lives here instead -- where QGIS
        users already look for it -- rather than becoming a seventh entry that
        would distort the specified structure.
        """
        about = QAction(_tr("About GeoComp…"), self.iface.mainWindow())
        about.setObjectName("geocompPluginMenuAbout")
        about.triggered.connect(self.open_about)
        self.iface.addPluginToMenu("&GeoComp", about)
        self._plugin_menu_actions.append(about)

    # -- actions ---------------------------------------------------------

    def run_algorithm(self, algorithm_id: str) -> None:
        """Open the Processing dialog for *algorithm_id*.

        ADR-0005: menu items launch algorithms; they do not reimplement them.
        """
        from processing import execAlgorithmDialog

        execAlgorithmDialog(algorithm_id, {})

    def open_settings(self) -> None:
        from geocomp.gui.settings_dialog import GlobalSettingsDialog

        dialog = GlobalSettingsDialog(self.iface.mainWindow())
        dialog.exec()
        if self._toolbar is not None:
            from geocomp.services.settings_service import settings

            self._toolbar.setVisible(bool(settings.value("interface.show_toolbar")))

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
