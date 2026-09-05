# SPDX-License-Identifier: GPL-2.0-or-later
"""Layered settings resolution (FR-068).

``specs/15-ui-menu-and-settings.md`` section 2.3: a value resolves
``run parameter -> project -> global -> built-in default``, and the effective
value together with **the scope it came from** must be inspectable.

The resolution rule lives here, in the QGIS-free core, so it can be tested
exhaustively without a QGIS runtime. ``geocomp.services.settings_service``
supplies the actual scope readers -- ``QgsSettings`` for global, the project
store for project scope.

Tracking the origin is not decoration. It is what makes a result explicable
months later: without it a shared instrument constant can silently differ
between two projects, which is precisely the class of operational error the
research project set out to reduce.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from geocomp.core.errors import ValidationError
from geocomp.core.settings_def import Scope, SettingDef, setting

__all__ = ["ResolvedSetting", "ScopeReader", "resolve", "resolve_value"]

#: Reads one scope. Returns the value, or ``None`` when that scope does not set
#: this key. A scope that legitimately stores ``None`` must not use this
#: protocol -- no GeoComp setting does, and the resolver treats ``None`` as
#: "unset" throughout.
ScopeReader = Callable[[str], Any]


@dataclass(frozen=True)
class ResolvedSetting:
    """An effective value together with where it came from."""

    key: str
    value: Any
    scope: Scope
    #: Every scope that supplied a value, highest precedence first. Lets the UI
    #: show "overridden for this project (global value: X)".
    overridden: tuple[tuple[Scope, Any], ...] = ()

    @property
    def is_default(self) -> bool:
        return self.scope is Scope.DEFAULT

    @property
    def is_overridden(self) -> bool:
        """True when a higher-precedence scope shadowed a lower one."""
        return len(self.overridden) > 1


def resolve(
    key: str,
    readers: Mapping[Scope, ScopeReader],
    *,
    definition: SettingDef | None = None,
    validate: bool = True,
) -> ResolvedSetting:
    """Resolve *key* through the scope chain.

    Args:
        key: The setting key.
        readers: A reader per scope. Missing scopes are skipped, so a caller
            with no project open simply omits ``Scope.PROJECT``.
        definition: The setting definition; looked up from *key* when omitted.
        validate: Validate each candidate value against its definition. A value
            that fails is **skipped with the failure recorded**, not raised:
            a corrupt entry in one scope must not make the setting
            unreadable, and falling through to the next scope is the behaviour
            that keeps the plugin usable.

    Returns:
        The effective value and its origin.

    Raises:
        ValidationError: only if the built-in default itself is invalid, which
            is a programming error in the declaration.
    """
    definition = definition or setting(key)
    found: list[tuple[Scope, Any]] = []

    for scope in Scope:
        if scope is Scope.DEFAULT:
            continue
        if scope not in definition.scopes:
            continue
        reader = readers.get(scope)
        if reader is None:
            continue
        value = reader(key)
        if value is None:
            continue
        if validate:
            try:
                definition.validate(value)
            except ValidationError:
                # Skip the bad value and fall through. The caller logs it; see
                # geocomp.services.settings_service.
                continue
        found.append((scope, value))

    if found:
        scope, value = found[0]
        return ResolvedSetting(key=key, value=value, scope=scope, overridden=tuple(found))

    definition.validate(definition.default)
    return ResolvedSetting(
        key=key,
        value=definition.default,
        scope=Scope.DEFAULT,
        overridden=((Scope.DEFAULT, definition.default),),
    )


def resolve_value(key: str, readers: Mapping[Scope, ScopeReader], **kwargs: Any) -> Any:
    """Convenience wrapper returning only the effective value."""
    return resolve(key, readers, **kwargs).value
