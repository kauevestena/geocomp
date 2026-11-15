# SPDX-License-Identifier: GPL-2.0-or-later
"""The GeoComp menu, generated from the registry.

FR-002 and FR-003: a dedicated top-level menu on the QGIS menu bar -- alongside
Project, Edit and View, not buried under Plugins -- presenting seven entries in
order, with a separator before Global Settings, matching
``research_project/fig/menu_estrutura.png``.

The figure shows five technique submenus; **Analysis** is the sixth, added in
phase P2 for the operations that belong to no single technique (network
pre-analysis, inspection, adjustment and its statistics). ``specs/15`` section
1.1 left that placement open and FR-003 is amended rather than contradicted.

ADR-0010: a menu item opens an **interactive window**, in which observations
are typed and which computes only by running registered algorithms. The menu
holds no second implementation, and it is built from :mod:`geocomp.registry` so
that an item cannot point at nothing.

Phase P14 rebuilds the menu group by group. Until a group's windows exist its
items are what ADR-0005 made them: *launchers*, each opening one algorithm's
Processing dialog. The registry says which is which, and the two kinds are
drawn by the same code in the order the registry gives.

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
from qgis.PyQt.QtWidgets import QAction, QMenu, QMenuBar, QWidget

from geocomp.registry import (
    MENU_GROUPS,
    AlgorithmSpec,
    MenuGroup,
    WindowSpec,
    entries_in_menu,
    entries_in_submenu,
    submenus_in_menu,
)
from geocomp.resources import icon_path

__all__ = ["GeoCompMenu", "algorithm_label", "entry_label", "menu_label", "submenu_label"]

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
        "analysis": _tr("Analysis"),
        "project": _tr("Project"),
        "global_settings": _tr("Global Settings…"),
    }.get(menu_id, menu_id)


class GeoCompMenu:
    """Builds and tears down the GeoComp menu bar entry.

    Args:
        parent: Widget owning the created actions, so Qt destroys them with it.
        run_algorithm: Called with an algorithm id when a legacy launcher is chosen.
        open_window: Called with a window's name when a window's item is chosen.
        open_settings: Called when Global Settings is chosen.
    """

    def __init__(
        self,
        parent: QWidget,
        *,
        run_algorithm: Callable[[str], None],
        open_window: Callable[[str], None],
        open_settings: Callable[[], None],
    ) -> None:
        self._parent = parent
        self._run_algorithm = run_algorithm
        self._open_window = open_window
        self._open_settings = open_settings
        self._menu: QMenu | None = None
        self._actions: list[QAction] = []
        self._submenus: list[QMenu] = []

    @property
    def menu(self) -> QMenu | None:
        """The menu, or ``None`` before it is built and after it is removed."""
        return self._menu

    def build(self, menu_bar: QMenuBar) -> QMenu:
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

        specs = entries_in_menu(group.id)

        # A second level, where the group declares one. GNSS is the only group
        # that does, and `specs/11` section 1 draws why: its four modes are two
        # branches of two, and "Static" alone names nothing. Nested entries come
        # first, matching the specification's own figure.
        for nested in submenus_in_menu(group.id):
            branch = QMenu(submenu_label(group.id, nested), submenu)
            branch.setObjectName(f"geocompMenu_{group.id}_{nested}")
            for spec in entries_in_submenu(group.id, nested):
                branch.addAction(self._entry_action(spec))
            submenu.addMenu(branch)
            self._submenus.append(branch)

        for spec in entries_in_submenu(group.id, None):
            submenu.addAction(self._entry_action(spec))

        if not specs:
            submenu.setEnabled(False)
            submenu.setToolTip(_tr("No operations available yet in this version."))

        self._menu.addMenu(submenu)
        self._submenus.append(submenu)

    def _entry_action(self, spec: WindowSpec | AlgorithmSpec) -> QAction:
        """One menu item: a window's, or an algorithm's legacy launcher.

        Factored out when GNSS added a second level, so a nested item and a
        top-level one are built by the same code and cannot drift -- the object
        name in particular, which is what `tests/qgis/` finds items by. A
        window's item carries its name as data and a launcher's its algorithm
        id, so the two can be told apart from outside.
        """
        action = QAction(entry_label(spec), self._parent)
        action.setObjectName(f"geocompMenuAction_{spec.name}")
        if isinstance(spec, WindowSpec):
            action.setData(spec.name)
            action.triggered.connect(
                lambda _checked=False, name=spec.name: self._open_window(name)
            )
        else:
            action.setData(spec.id)
            action.triggered.connect(
                lambda _checked=False, algorithm_id=spec.id: self._run_algorithm(algorithm_id)
            )
        self._actions.append(action)
        return action

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



def submenu_label(menu_id: str, submenu_id: str) -> str:
    """Translated label for a second-level menu entry.

    Only GNSS has one; see ``AlgorithmSpec.submenu`` in :mod:`geocomp.registry`
    for why, and why it stays the exception. An unknown id falls back to its own
    text capitalised rather than raising: a missing label is a cosmetic fault
    and should not stop the menu being built.
    """
    return {
        ("gnss", "absolute"): _tr("Absolute"),
        ("gnss", "relative"): _tr("Relative"),
    }.get((menu_id, submenu_id), submenu_id.replace("_", " ").capitalize())


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


def entry_label(spec: WindowSpec | AlgorithmSpec) -> str:
    """Label for a menu item of either kind.

    A window's is its own (``geocomp.gui.windows.labels``); a launcher's is its
    algorithm's ``displayName()``. A window's item ends with an ellipsis, as an
    item that opens something to work in does.
    """
    if isinstance(spec, WindowSpec):
        from geocomp.gui.windows.labels import window_label

        return window_label(spec.name) + "…"
    return algorithm_label(spec)


def _insert_before_help(menu_bar, menu: QMenu) -> None:
    for action in menu_bar.actions():
        submenu = action.menu()
        if submenu is not None and submenu.objectName() in ("mHelpMenu", "helpMenu"):
            menu_bar.insertMenu(action, menu)
            return
    menu_bar.addMenu(menu)
