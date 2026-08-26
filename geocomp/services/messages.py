# SPDX-License-Identifier: GPL-2.0-or-later
"""Turn a structured core error into a translated, user-facing message.

The core raises errors carrying a stable ``code`` and a ``context`` mapping and
never phrases a sentence (``specs/18-i18n-and-profiles.md`` section 2). This
module owns the phrasing, which is why it lives in the presentation-facing
service layer where ``QCoreApplication.translate`` is available.

NFR-006 requires a message to say **what failed, why, and what the user can do
about it**. Each template below is written to do all three; a template that only
restates the code is not finished.
"""

from __future__ import annotations

from typing import Any

from qgis.PyQt.QtCore import QCoreApplication

from geocomp.core.errors import GeoCompError

__all__ = ["MessageTemplate", "message_for", "register_template"]

_CONTEXT = "GeoCompMessages"


class MessageTemplate:
    """A translatable template plus the context keys it interpolates."""

    __slots__ = ("keys", "source")

    def __init__(self, source: str, *keys: str) -> None:
        self.source = source
        self.keys = keys

    def render(self, context: dict[str, Any]) -> str:
        text = QCoreApplication.translate(_CONTEXT, self.source)
        for index, key in enumerate(self.keys, start=1):
            text = text.replace(f"%{index}", _format(context.get(key)))
        return text


def _format(value: Any) -> str:
    if value is None:
        return QCoreApplication.translate(_CONTEXT, "(not set)")
    if isinstance(value, (list, tuple)):
        return ", ".join(str(item) for item in value)
    return str(value)


#: Code -> template. Keyed by the full namespaced code from
#: :class:`~geocomp.core.errors.GeoCompError`.
_TEMPLATES: dict[str, MessageTemplate] = {
    "validation.setting_not_a_choice": MessageTemplate(
        "The setting '%1' cannot be set to '%2'. Permitted values are: %3.",
        "key",
        "received",
        "expected",
    ),
    "validation.setting_wrong_type": MessageTemplate(
        "The setting '%1' expects a value of type %2, but received %3. "
        "Correct it in Global Settings, or restore the default.",
        "key",
        "expected",
        "received",
    ),
    "validation.setting_below_minimum": MessageTemplate(
        "The setting '%1' cannot be less than %2 (received %3).",
        "key",
        "minimum",
        "received",
    ),
    "validation.setting_above_maximum": MessageTemplate(
        "The setting '%1' cannot be greater than %2 (received %3).",
        "key",
        "maximum",
        "received",
    ),
    "engine.not_installed": MessageTemplate(
        "The '%1' engine is required for this operation but is not installed. "
        "Install it from Global Settings, under Paths and engines.",
        "engine",
    ),
}


def register_template(code: str, template: MessageTemplate) -> None:
    """Register a template for *code*.

    Later phases register their own rather than growing this module into a
    catalogue of every error in the project.
    """
    _TEMPLATES[code] = template


def message_for(error: GeoCompError) -> str:
    """Return the translated, user-facing message for *error*.

    Falls back to a generic message that still carries the code, so an
    unregistered error is reportable rather than opaque. A missing template is a
    gap to fill, not a reason to show the user nothing.
    """
    template = _TEMPLATES.get(error.code)
    if template is not None:
        return template.render(error.context)
    return QCoreApplication.translate(
        _CONTEXT,
        "GeoComp could not complete the operation (%1). "
        "See the GeoComp tab of the Log Messages panel for details.",
    ).replace("%1", error.code)
