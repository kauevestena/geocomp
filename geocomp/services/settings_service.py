# SPDX-License-Identifier: GPL-2.0-or-later
"""Layered settings storage and resolution against QGIS (FR-060, FR-067, FR-068).

The resolution *rule* lives in :mod:`geocomp.core.settings_resolution`, where it
is testable without QGIS. This module supplies the storage each scope reads
from:

* **Global** -- ``QgsSettings`` under a ``GeoComp/`` prefix. Follows the user
  across projects.
* **Project** -- the QGIS project's own entry store in P0, moving to the GeoComp
  project store (GeoPackage or PostGIS) when that exists in P5. Project-scope
  values travel with the data, so a project handed to a colleague carries the
  constants it was computed with.
* **Run** -- values supplied for a single algorithm run; held in memory.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from qgis.core import QgsProject, QgsSettings

from geocomp.core.errors import ValidationError
from geocomp.core.settings_def import SETTINGS, Scope, SettingDef, setting
from geocomp.core.settings_resolution import ResolvedSetting, resolve
from geocomp.services.logging import LogLevel, log

__all__ = ["SettingsService", "settings"]

#: Prefix for every GeoComp key inside ``QgsSettings``.
SETTINGS_PREFIX = "GeoComp"

#: Scope under which project-level values are stored in the QGIS project file.
PROJECT_ENTRY_SCOPE = "GeoComp"


class SettingsService:
    """Reads and writes GeoComp settings across the three settable scopes."""

    def __init__(self) -> None:
        self._run_overrides: dict[str, Any] = {}

    # -- readers ---------------------------------------------------------

    def _read_global(self, key: str) -> Any:
        definition = setting(key)
        stored = QgsSettings().value(f"{SETTINGS_PREFIX}/{key}", None)
        return _coerce(definition, stored)

    def _read_project(self, key: str) -> Any:
        definition = setting(key)
        project = QgsProject.instance()
        if project is None:
            return None
        stored, ok = project.readEntry(PROJECT_ENTRY_SCOPE, key)
        if not ok or stored == "":
            return None
        return _coerce(definition, stored)

    def _read_run(self, key: str) -> Any:
        return self._run_overrides.get(key)

    def _readers(self) -> dict[Scope, Any]:
        return {
            Scope.RUN: self._read_run,
            Scope.PROJECT: self._read_project,
            Scope.GLOBAL: self._read_global,
        }

    # -- public interface ------------------------------------------------

    def resolve(self, key: str) -> ResolvedSetting:
        """Return the effective value of *key* together with its origin scope.

        The origin is what the Global Settings dialog shows next to each value,
        and what provenance records alongside a result (FR-134).
        """
        return resolve(key, self._readers())

    def value(self, key: str) -> Any:
        """Return the effective value of *key*."""
        return self.resolve(key).value

    def set_global(self, key: str, value: Any) -> None:
        """Write *value* at global scope, validating it first."""
        definition = self._checked(key, value, Scope.GLOBAL)
        QgsSettings().setValue(f"{SETTINGS_PREFIX}/{definition.key}", value)

    def set_project(self, key: str, value: Any) -> None:
        """Write *value* at project scope."""
        definition = self._checked(key, value, Scope.PROJECT)
        project = QgsProject.instance()
        if project is None:
            raise ValidationError("no_project_open", key=key)
        project.writeEntry(PROJECT_ENTRY_SCOPE, definition.key, _to_storage(value))

    def clear_project(self, key: str) -> None:
        """Remove the project-scope override for *key*, if any."""
        project = QgsProject.instance()
        if project is not None:
            project.removeEntry(PROJECT_ENTRY_SCOPE, key)

    def reset_global(self, key: str) -> None:
        """Remove the global value for *key*, restoring the built-in default."""
        QgsSettings().remove(f"{SETTINGS_PREFIX}/{key}")

    @contextmanager
    def run_overrides(self, values: dict[str, Any]) -> Iterator[None]:
        """Apply run-scope overrides for the duration of the block.

        Used by algorithms so a parameter supplied for one run takes precedence
        without being written anywhere. Restores the previous state on exit,
        including on exception -- a failed run must not leak its parameters into
        the next one.
        """
        for key, value in values.items():
            self._checked(key, value, Scope.RUN)
        previous = dict(self._run_overrides)
        self._run_overrides.update(values)
        try:
            yield
        finally:
            self._run_overrides = previous

    def all_resolved(self) -> dict[str, ResolvedSetting]:
        """Resolve every declared setting. Used by the settings dialog and diagnostics."""
        readers = self._readers()
        return {definition.key: resolve(definition.key, readers) for definition in SETTINGS}

    def apply_log_level(self) -> None:
        """Push ``interface.log_level`` into the process logger."""
        log.set_threshold(LogLevel.from_setting(self.value("interface.log_level")))

    # -- internals -------------------------------------------------------

    def _checked(self, key: str, value: Any, scope: Scope) -> SettingDef:
        definition = setting(key)
        if scope not in definition.scopes:
            raise ValidationError(
                "setting_scope_not_allowed",
                key=key,
                scope=scope.value,
                expected=sorted(s.value for s in definition.scopes),
            )
        definition.validate(value)
        return definition


def _to_storage(value: Any) -> str:
    """Project entries are strings; booleans need an unambiguous form."""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _coerce(definition: SettingDef, stored: Any) -> Any:
    """Convert a stored value back to the declared type.

    ``QgsSettings`` and project entries return strings on some platforms and
    native types on others, so the type is restored from the declaration rather
    than trusted. A value that cannot be coerced is logged and treated as unset,
    letting resolution fall through to the next scope instead of failing.
    """
    from geocomp.core.settings_def import SettingType

    if stored is None or stored == "":
        return None
    try:
        if definition.type is SettingType.BOOL:
            if isinstance(stored, bool):
                return stored
            return str(stored).strip().lower() in ("true", "1", "yes")
        if definition.type is SettingType.INT:
            return int(stored)
        if definition.type is SettingType.FLOAT:
            return float(stored)
        return str(stored)
    except (TypeError, ValueError):
        log.warning("ignoring unreadable setting value", key=definition.key, stored=stored)
        return None


#: Process-wide settings service.
settings = SettingsService()
