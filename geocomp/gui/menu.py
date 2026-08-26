# SPDX-License-Identifier: GPL-2.0-or-later
"""The GeoComp menu, generated from the algorithm registry.

FR-002 and FR-003: a dedicated top-level menu on the QGIS menu bar -- alongside
Project, Edit and View, not buried under Plugins -- presenting six entries in
order, with a separator before Global Settings, matching
``research_project/fig/menu_estrutura.png``.

ADR-0005: the menu is a *launcher*. Every item runs a Processing algorithm; the
menu holds no second implementation, and it is built from
:mod:`geocomp.registry` so that an item cannot point at nothing and an algorithm
cannot go unreachable.

Technique submenus with no algorithms yet are shown **disabled rather than
hidden**. A user who opens the menu should be able to see that Gravimetry is
planned, not be left wondering whether it exists; and a phase that adds its
first algorithm needs no menu change.
"""

from __future__ import annotations

from collections.abc import Callable

from qgis.core import QgsApplication
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMenu, QWidget

from geocomp.registry import MENU_GROUPS, AlgorithmSpec, MenuGroup, algorithms_in_menu
from geocomp.resources import icon_path

__all__ = ["GeoCompMenu", "algorithm_label", "menu_label"]

_TR_CONTEXT = "GeoCompMenu"


def _tr(text: str) -> str:
    return QCoreApplication.translate(_TR_CONTEXT, text)


def menu_label(menu_id: str) -> str:
    """Translated label for a menu group.

    Source strings are literals so the extractor finds them, keyed by the stable
    ids in :mod:`geocomp.registry`.

    The fourth group is **Gravimetry**, not "Gravimeter": the research project's
    prose says *Gravímetro* while ``fig/menu_estrutura.png`` says *Gravimetria*.
    The figure wins, because every other group is named for a technique rather
    than an instrument (recorded in ``specs/00-glossary.md``).
    """
    return {
        "total_station": _tr("Total Station"),
        "level": _tr("Level"),
        "gnss": _tr("GNSS"),
        "gravimetry": _tr("Gravimetry"),
        "integration": _tr("Integration"),
        "global_settings": _tr("Global Settings…"),
    }.get(menu_id, menu_id)


class GeoCompMenu:
    """Builds and tears down the GeoComp menu bar entry.

    Args:
        parent: Widget owning the created actions, so Qt destroys them with it.
        run_algorithm: Called with an algorithm id when a menu item is chosen.
        open_settings: Called when Global Settings is chosen.
    """

    def __init__(
        self,
        parent: QWidget,
        *,
        run_algorithm: Callable[[str], None],
        open_settings: Callable[[], None],
    ) -> None:
        self._parent = parent
        self._run_algorithm = run_algorithm
        self._open_settings = open_settings
        self._menu: QMenu | None = None
        self._actions: list[QAction] = []
        self._submenus: list[QMenu] = []

    @property
    def menu(self) -> QMenu | None:
        return self._menu

    def build(self, menu_bar) -> QMenu:
        """Create the menu and insert it into *menu_bar*.

        Inserted before the Help menu when one is found, so GeoComp sits among
        the application menus rather than after Help.
        """
        self._menu = QMenu(_tr("&GeoComp"), self._parent)
        self._menu.setObjectName("geocompMenu")
        self._menu.setIcon(QIcon(icon_path("geocomp.svg")))

        for group in MENU_GROUPS:
            if group.separator_before:
                self._menu.addSeparator()
            if group.is_action:
                self._add_leaf_action(group)
            else:
                self._add_submenu(group)

        _insert_before_help(menu_bar, self._menu)
        return self._menu

    def _add_leaf_action(self, group: MenuGroup) -> None:
        assert self._menu is not None
        action = QAction(menu_label(group.id), self._parent)
        action.setObjectName(f"geocompMenuAction_{group.id}")
        if group.id == "global_settings":
            action.triggered.connect(self._open_settings)
        self._menu.addAction(action)
        self._actions.append(action)

    def _add_submenu(self, group: MenuGroup) -> None:
        assert self._menu is not None
        submenu = QMenu(menu_label(group.id), self._menu)
        submenu.setObjectName(f"geocompMenu_{group.id}")

        specs = algorithms_in_menu(group.id)
        for spec in specs:
            action = QAction(algorithm_label(spec), self._parent)
            action.setObjectName(f"geocompMenuAction_{spec.name}")
            action.setData(spec.id)
            action.triggered.connect(
                lambda _checked=False, algorithm_id=spec.id: self._run_algorithm(algorithm_id)
            )
            submenu.addAction(action)
            self._actions.append(action)

        if not specs:
            submenu.setEnabled(False)
            submenu.setToolTip(_tr("No operations available yet in this version."))

        self._menu.addMenu(submenu)
        self._submenus.append(submenu)

    def unload(self) -> None:
        """Remove every element this class created (FR-006).

        Reloading the plugin during development must not leave a second GeoComp
        menu behind, which is why actions and submenus are tracked explicitly
        rather than relying on parent destruction.
        """
        for action in self._actions:
            action.setParent(None)
            action.deleteLater()
        self._actions.clear()

        for submenu in self._submenus:
            submenu.setParent(None)
            submenu.deleteLater()
        self._submenus.clear()

        if self._menu is not None:
            menu_bar = self._menu.parentWidget()
            if menu_bar is not None and hasattr(menu_bar, "removeAction"):
                menu_bar.removeAction(self._menu.menuAction())
            self._menu.setParent(None)
            self._menu.deleteLater()
            self._menu = None


def algorithm_label(spec: AlgorithmSpec) -> str:
    """Label for a menu item, taken from the algorithm's own ``displayName()``.

    The authoritative, translated label lives on the algorithm class. It is
    resolved through the Processing registry rather than by importing the class
    here, so the menu does not instantiate every algorithm just to draw itself,
    and so the label a user sees in the menu is by construction the one they see
    in the toolbox.

    ``plugin.initGui`` registers the provider before building the menu, so the
    lookup succeeds in normal operation. The derived fallback covers the case
    where an algorithm failed to load -- ``GeoCompProvider.loadAlgorithms``
    deliberately keeps going when one module is broken, and a readable menu
    entry is better than a crash while building the menu.
    """
    algorithm = QgsApplication.processingRegistry().algorithmById(spec.id)
    if algorithm is not None:
        return algorithm.displayName()
    return spec.operation.replace("_", " ").capitalize()


def _insert_before_help(menu_bar, menu: QMenu) -> None:
    for action in menu_bar.actions():
        submenu = action.menu()
        if submenu is not None and submenu.objectName() in ("mHelpMenu", "helpMenu"):
            menu_bar.insertMenu(action, menu)
            return
    menu_bar.addMenu(menu)
