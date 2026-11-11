# SPDX-License-Identifier: GPL-2.0-or-later
"""The interactive windows of the GeoComp menu (ADR-0010, FR-010).

One module per window, under a package per technique. Which windows exist,
where each lives and which algorithms it runs is declared in
:data:`geocomp.registry.WINDOWS`; this package opens them.

:class:`WindowManager` is what the plugin holds. A window is imported when it
is first opened -- not when the plugin loads, so a window with a fault costs
its own menu item and nothing else -- and there is one of each at a time: an
item chosen again brings its window forward.
"""

from __future__ import annotations

import importlib
from typing import Any

from qgis.PyQt.QtWidgets import QWidget

from geocomp.registry import window_named
from geocomp.services.jobs_service import JobsService

__all__ = ["WindowManager"]


class WindowManager:
    """Opens the menu's windows, keeps one of each, and closes them all on unload.

    Args:
        parent: The QGIS main window, which the windows float over.
        canvas: The map canvas the windows sketch on and pick from, or ``None``.
        jobs: The job service the windows share; one is made when none is given.
    """

    def __init__(
        self, parent: QWidget | None, canvas: Any = None, jobs: JobsService | None = None
    ) -> None:
        self._parent = parent
        self._canvas = canvas
        self.jobs = jobs if jobs is not None else JobsService()
        self._open: dict[str, QWidget] = {}

    @property
    def open_windows(self) -> tuple[str, ...]:
        """The names of the windows that are open."""
        return tuple(self._open)

    def window(self, name: str) -> QWidget | None:
        """The open window of that name, or ``None``."""
        return self._open.get(name)

    def open(self, name: str) -> QWidget:
        """Open the window *name*, or bring it forward when it is already open.

        Raises:
            KeyError: for a name the registry does not declare.
        """
        window = self._open.get(name)
        if window is None:
            spec = window_named(name)
            if spec is None:
                raise KeyError(name)
            window_class = getattr(importlib.import_module(spec.module), spec.class_name)
            window = window_class(
                spec,
                self.jobs,
                self._canvas,
                self._parent,
                open_window=self.open,
                is_last_open=lambda technique=spec.technique: self._count(technique) <= 1,
            )
            window.closed.connect(self._closed)
            self._open[name] = window
        window.show()
        window.raise_()
        window.activateWindow()
        return window

    def _count(self, technique: str) -> int:
        return sum(1 for window in self._open.values() if window.spec.technique == technique)

    def _closed(self, name: str) -> None:
        window = self._open.pop(name, None)
        if window is not None:
            window.deleteLater()

    def close_all(self) -> None:
        """Close every window without asking, and stop following the project (FR-006)."""
        for window in list(self._open.values()):
            window.close_now()
        self._open.clear()
        self.jobs.detach()
