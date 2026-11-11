# SPDX-License-Identifier: GPL-2.0-or-later
"""An options form made from an algorithm's own parameters (FR-016).

A window's options *are* its algorithm's parameters, so the form is built from
their definitions with the widgets QGIS's own Processing dialog builds from
them (``QgsProcessingGuiRegistry.createParameterWidgetWrapper``):

* the label is the algorithm's, with its unit, translated once;
* the default is the algorithm's -- Global Settings, read when the form is
  made, exactly as a toolbox dialog reads it;
* the range is the algorithm's;
* a parameter the algorithm hides in Basic mode is hidden here (FR-070).

So there is no second label to translate, no second default to drift, and a
window in Basic mode computes what the same window in Advanced mode computes
with nothing touched (FR-071), for the reason the toolbox does.

**Only what the user changes is kept.** A value is stored in the job when it
differs from the algorithm's default and removed when it is set back, so a job
says what was chosen, and a parameter never touched is the algorithm's to
decide.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, MutableMapping
from typing import Any

from qgis.core import (
    NULL,
    QgsApplication,
    QgsProcessingContext,
    QgsProcessingParameterDefinition,
)
from qgis.gui import QgsGui, QgsProcessingGui
from qgis.PyQt.QtCore import QCoreApplication, pyqtSignal
from qgis.PyQt.QtWidgets import QFormLayout, QLabel, QWidget

__all__ = ["ParameterForm"]

_TR_CONTEXT = "GeoCompWorkbench"


def _tr(text: str) -> str:
    return QCoreApplication.translate(_TR_CONTEXT, text)


class ParameterForm(QWidget):
    """Widgets for some of an algorithm's parameters, kept in step with a job.

    Args:
        algorithm_id: The algorithm whose parameters these are.
        names: Which parameters, in the order they are shown.
        stored: Gives the mapping the chosen values are kept in: the window's
            parameters in the current job. Asked each time, because the job
            can be replaced under an open window.
        always: Parameters shown even where the algorithm hides them in Basic
            mode, because the window cannot be used without them: the closing
            coordinates of a connected traverse.
        parent: The Qt parent.
    """

    #: The user changed a parameter: its name.
    changed = pyqtSignal(str)

    def __init__(
        self,
        algorithm_id: str,
        names: Iterable[str],
        stored: Callable[[], MutableMapping[str, Any]],
        *,
        always: Iterable[str] = (),
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._stored = stored
        self._loading = False
        self._wrappers: dict[str, Any] = {}
        self._labels: dict[str, QWidget] = {}
        # Kept: the definitions belong to the algorithm, the widgets to the context.
        self._context = QgsProcessingContext()
        registered = QgsApplication.processingRegistry().algorithmById(algorithm_id)
        self._algorithm = registered.create({}) if registered is not None else None

        layout = QFormLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        if self._algorithm is None:
            layout.addRow(
                QLabel(
                    _tr(
                        "The algorithm %1 is not available. Enable the GeoComp provider in the "
                        "Processing options."
                    ).replace("%1", algorithm_id),
                    self,
                )
            )
            return
        shown_anyway = frozenset(always)
        for name in names:
            definition = self._algorithm.parameterDefinition(name)
            if definition is None:
                continue
            hidden = bool(definition.flags() & QgsProcessingParameterDefinition.Flag.FlagHidden)
            if hidden and name not in shown_anyway:
                continue
            wrapper = QgsGui.processingGuiRegistry().createParameterWidgetWrapper(
                definition, QgsProcessingGui.WidgetType.Standard
            )
            if wrapper is None:
                continue
            widget = wrapper.createWrappedWidget(self._context)
            widget.setObjectName(f"geocompParameter_{name}")
            label = wrapper.createWrappedLabel() or QLabel(definition.description(), self)
            widget.setToolTip(definition.description())
            layout.addRow(label, widget)
            self._wrappers[name] = wrapper
            self._labels[name] = label
            wrapper.widgetValueHasChanged.connect(
                lambda _wrapper=None, name=name: self._widget_changed(name)
            )
        self.reload()

    # -- reading -----------------------------------------------------------

    @property
    def names(self) -> tuple[str, ...]:
        """The parameters the form shows."""
        return tuple(self._wrappers)

    def default(self, name: str) -> Any:
        """The algorithm's default for *name*: what a toolbox dialog would start with."""
        if self._algorithm is None:
            return None
        definition = self._algorithm.parameterDefinition(name)
        return None if definition is None else _plain(definition.defaultValue())

    def value(self, name: str) -> Any:
        """What the run will use for *name*: the stored choice, or the algorithm's default."""
        stored = self._stored()
        return stored[name] if stored.get(name) is not None else self.default(name)

    def label(self, name: str) -> str:
        """The algorithm's own label for *name*, with its unit."""
        if self._algorithm is None:
            return name
        definition = self._algorithm.parameterDefinition(name)
        return name if definition is None else definition.description()

    def widget(self, name: str) -> QWidget | None:
        """The widget of *name*, or ``None`` when the form does not show it."""
        wrapper = self._wrappers.get(name)
        return None if wrapper is None else wrapper.wrappedWidget()

    # -- writing -----------------------------------------------------------

    def reload(self) -> None:
        """Set every widget from the job: it was replaced, or changed elsewhere."""
        self._loading = True
        try:
            for name, wrapper in self._wrappers.items():
                wrapper.setParameterValue(self.value(name), self._context)
        finally:
            self._loading = False

    def set_value(self, name: str, value: Any) -> None:
        """Choose *value* for *name* as though the user had: a point picked on the map."""
        self._store(name, value)
        wrapper = self._wrappers.get(name)
        if wrapper is not None:
            self._loading = True
            try:
                wrapper.setParameterValue(self.value(name), self._context)
            finally:
                self._loading = False
        self.changed.emit(name)

    def set_shown(self, name: str, shown: bool) -> None:
        """Show or hide one parameter's row: it does not apply to what else was chosen."""
        for part in (self._labels.get(name), self.widget(name)):
            if part is not None:
                part.setVisible(shown)

    def _widget_changed(self, name: str) -> None:
        if self._loading:
            return
        self._store(name, _plain(self._wrappers[name].parameterValue()))
        self.changed.emit(name)

    def _store(self, name: str, value: Any) -> None:
        stored = self._stored()
        if value is None or value == self.default(name):
            stored.pop(name, None)
        else:
            stored[name] = value


def _plain(value: Any) -> Any:
    """A parameter value as a job file stores it: ``None`` for nothing, text for a path."""
    if value is None or value == NULL:
        return None
    if isinstance(value, str):
        return value if value.strip() else None
    if isinstance(value, bool | int | float):
        return value
    return str(value)
