# SPDX-License-Identifier: GPL-2.0-or-later
"""An options form made from an algorithm's own parameters (FR-016).

A window's options *are* its algorithm's parameters, so the form is built from
their definitions:

* the label is the algorithm's, with its unit, translated once;
* the default is the algorithm's -- Global Settings, read when the form is
  made, exactly as a toolbox dialog reads it;
* the range and the choices are the algorithm's;
* a parameter the algorithm hides in Basic mode is hidden here (FR-070).

So there is no second label to translate, no second default to drift, and a
window in Basic mode computes what the same window in Advanced mode computes
with nothing touched (FR-071), for the reason the toolbox does.

**The widgets are GeoComp's own, not QGIS's.** P14a first drew them with
``QgsProcessingGuiRegistry.createParameterWidgetWrapper``, the factory QGIS's
own dialog uses. On QGIS 4.2 for macOS that call ended the process with a
trap, on the GitHub runner, in a plugin as in a bare interpreter, while Linux
and Windows were fine. The windows need five kinds of parameter -- numbers,
choices, switches, text and files -- and drawing those is a few lines each, so
they no longer depend on it. A number is typed into a text field and read as
the grid reads one, with a point or a comma and every digit kept: a spin box
would round a precision of 5e-6 rad to its decimals.

**Only what the user changes is kept.** A value is stored in the job when it
differs from the algorithm's default and removed when it is set back, so a job
says what was chosen, and a parameter never touched is the algorithm's to
decide.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Iterable, MutableMapping
from typing import Any

from qgis.core import (
    NULL,
    QgsApplication,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterDefinition,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFile,
    QgsProcessingParameterNumber,
)
from qgis.PyQt.QtCore import QCoreApplication, pyqtSignal
from qgis.PyQt.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
)

from geocomp.core.errors import GeoCompError
from geocomp.jobs.tables import format_number, parse_integer, parse_number

__all__ = ["ParameterForm"]

_TR_CONTEXT = "GeoCompWorkbench"

#: How a number that cannot be read is shown.
_PROBLEM_STYLE = "QLineEdit { background-color: rgb(250, 205, 205); }"


def _tr(text: str) -> str:
    return QCoreApplication.translate(_TR_CONTEXT, text)


class _Field:
    """One parameter's widget, and how a value goes in and out of it."""

    def __init__(self, form: ParameterForm, definition: QgsProcessingParameterDefinition) -> None:
        self.name = definition.name()
        self.optional = bool(definition.flags() & QgsProcessingParameterDefinition.Flag.FlagOptional)
        self.kind = "text"
        self.minimum: float | None = None
        self.maximum: float | None = None
        self.integer = False
        self.editor: Any = None
        self.browse: QPushButton | None = None
        self.extension = ""
        if isinstance(definition, QgsProcessingParameterNumber):
            self.kind = "number"
            self.integer = definition.dataType() == QgsProcessingParameterNumber.Type.Integer
            self.minimum, self.maximum = definition.minimum(), definition.maximum()
            self.editor = QLineEdit(form)
            self.editor.setPlaceholderText(_tr("not set") if self.optional else "")
            self.widget: QWidget = self.editor
        elif isinstance(definition, QgsProcessingParameterEnum):
            self.kind = "choice"
            self.widget = QComboBox(form)
            self.widget.addItems(list(definition.options()))
        elif isinstance(definition, QgsProcessingParameterBoolean):
            self.kind = "switch"
            self.widget = QCheckBox(form)
        else:
            self.kind = "file" if isinstance(definition, QgsProcessingParameterFile) else "text"
            self.editor = QLineEdit(form)
            self.widget = self.editor
            if self.kind == "file":
                self.widget = QWidget(form)
                row = QHBoxLayout(self.widget)
                row.setContentsMargins(0, 0, 0, 0)
                row.addWidget(self.editor, 1)
                self.browse = QPushButton(_tr("Browse…"), self.widget)
                self.browse.setToolTip(_tr("Choose the file."))
                self.extension = definition.extension()
                row.addWidget(self.browse)
        self.widget.setObjectName(f"geocompParameter_{self.name}")
        self.widget.setToolTip(definition.description())
        self._tip = definition.description()

    def owns(self, widget: Any) -> bool:
        """Whether *widget* is one of this field's own."""
        return widget is not None and any(widget is part for part in (self.widget, self.editor, self.browse))

    # -- the value ---------------------------------------------------------

    def show(self, value: Any) -> None:
        """Put *value* in the widget."""
        if self.kind == "choice":
            self.widget.setCurrentIndex(int(value) if value is not None else 0)
        elif self.kind == "switch":
            self.widget.setChecked(bool(value))
        elif self.kind == "number":
            self.editor.setText("" if value is None else _number_text(value, self.integer))
        else:
            self.editor.setText("" if value is None else str(value))

    def read(self) -> tuple[Any, str]:
        """The value the widget holds, and why it is not one when it cannot be read."""
        if self.kind == "choice":
            return self.widget.currentIndex(), ""
        if self.kind == "switch":
            return self.widget.isChecked(), ""
        text = self.editor.text().strip()
        if self.kind != "number":
            return (text or None), ""
        if not text:
            return None, "" if self.optional else _tr("A value is needed.")
        try:
            value: Any = parse_integer(text) if self.integer else parse_number(text)
        except GeoCompError:
            return None, _tr("Not a whole number.") if self.integer else _tr("Not a number.")
        low = self.minimum if self.minimum is not None and math.isfinite(self.minimum) else None
        high = self.maximum if self.maximum is not None and math.isfinite(self.maximum) else None
        if (low is not None and value < low) or (high is not None and value > high):
            return None, (
                _tr("Between %1 and %2.")
                .replace("%1", _number_text(-math.inf if low is None else low, self.integer))
                .replace("%2", _number_text(math.inf if high is None else high, self.integer))
            )
        return value, ""

    def mark(self, problem: str) -> None:
        """Show that the value typed cannot be used, and why; or that it can."""
        if self.editor is not None and self.kind == "number":
            self.editor.setStyleSheet(_PROBLEM_STYLE if problem else "")
            self.editor.setToolTip(problem or self._tip)


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
        self._fields: dict[str, _Field] = {}
        self._labels: dict[str, QWidget] = {}
        self._defaults: dict[str, Any] = {}
        self._descriptions: dict[str, str] = {}

        layout = QFormLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        registered = QgsApplication.processingRegistry().algorithmById(algorithm_id)
        if registered is None:
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
        # A fresh instance gives what a toolbox dialog opened now would: the
        # defaults of today's Global Settings, and what Basic mode hides. Its
        # definitions are read here, into plain values, and the instance let go.
        fresh = registered.create({})
        for definition in fresh.parameterDefinitions():
            self._defaults[definition.name()] = _plain(definition.defaultValue())
            self._descriptions[definition.name()] = definition.description()
        shown_anyway = frozenset(always)
        for name in names:
            definition = fresh.parameterDefinition(name)
            if definition is None:
                continue
            hidden = bool(definition.flags() & QgsProcessingParameterDefinition.Flag.FlagHidden)
            if hidden and name not in shown_anyway:
                continue
            field = _Field(self, definition)
            # Bound methods, which PyQt holds weakly: a lambda over the form
            # would keep it alive through its own children.
            if field.kind == "choice":
                field.widget.activated.connect(self._edited)
            elif field.kind == "switch":
                field.widget.toggled.connect(self._edited)
            else:
                field.editor.textEdited.connect(self._edited)
            if field.browse is not None:
                field.browse.clicked.connect(self._browse)
            label = QLabel(definition.description(), self)
            layout.addRow(label, field.widget)
            self._fields[name] = field
            self._labels[name] = label
        del fresh
        self.reload()

    # -- reading -----------------------------------------------------------

    @property
    def names(self) -> tuple[str, ...]:
        """The parameters the form shows."""
        return tuple(self._fields)

    def default(self, name: str) -> Any:
        """The algorithm's default for *name*: what a toolbox dialog would start with."""
        return self._defaults.get(name)

    def value(self, name: str) -> Any:
        """What the run will use for *name*: the stored choice, or the algorithm's default."""
        stored = self._stored()
        return stored[name] if stored.get(name) is not None else self.default(name)

    def label(self, name: str) -> str:
        """The algorithm's own label for *name*, with its unit."""
        return self._descriptions.get(name, name)

    def widget(self, name: str) -> QWidget | None:
        """The widget of *name*, or ``None`` when the form does not show it."""
        field = self._fields.get(name)
        return None if field is None else field.widget

    def editor(self, name: str) -> QWidget | None:
        """Where *name* is typed or chosen: the text field of a number or a file, or the widget."""
        field = self._fields.get(name)
        if field is None:
            return None
        return field.editor if field.editor is not None else field.widget

    # -- writing -----------------------------------------------------------

    def reload(self) -> None:
        """Set every widget from the job: it was replaced, or changed elsewhere."""
        self._loading = True
        try:
            for name, field in self._fields.items():
                field.show(self.value(name))
                field.mark("")
        finally:
            self._loading = False

    def set_value(self, name: str, value: Any) -> None:
        """Choose *value* for *name* as though the user had: a point picked on the map."""
        self._store(name, value)
        field = self._fields.get(name)
        if field is not None:
            self._loading = True
            try:
                field.show(self.value(name))
                field.mark("")
            finally:
                self._loading = False
        self.changed.emit(name)

    def set_shown(self, name: str, shown: bool) -> None:
        """Show or hide one parameter's row: it does not apply to what else was chosen."""
        for part in (self._labels.get(name), self.widget(name)):
            if part is not None:
                part.setVisible(shown)

    def _sender_field(self) -> str | None:
        sender = self.sender()
        return next((name for name, field in self._fields.items() if field.owns(sender)), None)

    def _edited(self, *_arguments: Any) -> None:
        name = self._sender_field()
        if name is not None:
            self.field_changed(name)

    def _browse(self, *_arguments: Any) -> None:
        name = self._sender_field()
        if name is None:
            return
        field = self._fields[name]
        pattern = f"*.{field.extension}" if field.extension else "*"
        path, _filter = QFileDialog.getOpenFileName(
            self, self.label(name), field.editor.text(), f"{pattern};;" + _tr("All files (*)")
        )
        if path:
            field.editor.setText(path)
            self.field_changed(name)

    def field_changed(self, name: str) -> None:
        """The user edited *name*'s widget: keep what it now holds, if it can be used."""
        if self._loading or name not in self._fields:
            return
        field = self._fields[name]
        value, problem = field.read()
        field.mark(problem)
        if problem:
            return
        self._store(name, value)
        self.changed.emit(name)

    def _store(self, name: str, value: Any) -> None:
        stored = self._stored()
        if value is None or value == self.default(name):
            stored.pop(name, None)
        else:
            stored[name] = value


def _number_text(value: Any, integer: bool) -> str:
    """A number as a field shows it: every digit, no exponent, a whole number without a point."""
    number = float(value)
    if math.isinf(number):
        return "∞" if number > 0 else "-∞"
    if integer or number.is_integer():
        return str(int(number))
    text = repr(number)
    return format_number(number, 12).rstrip("0").rstrip(".") if "e" in text else text


def _plain(value: Any) -> Any:
    """A parameter value as a job file stores it: ``None`` for nothing, text for a path."""
    if value is None or value == NULL:
        return None
    if isinstance(value, str):
        return value if value.strip() else None
    if isinstance(value, bool | int | float):
        return value
    return str(value)
