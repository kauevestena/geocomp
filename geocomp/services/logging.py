# SPDX-License-Identifier: GPL-2.0-or-later
"""Diagnostics into the QGIS message log, under a ``GeoComp`` tab (FR-009).

Verbosity comes from ``interface.log_level`` (specs/15 section 2.1).

Log text is developer-facing and deliberately **not** translated: it exists to
be searched, pasted into a bug report, and read by whoever is debugging, and a
log that changes language with the UI is far harder to support. User-facing
messages are a separate concern -- see :mod:`geocomp.services.messages`.
"""

from __future__ import annotations

import traceback
from enum import IntEnum
from typing import Any

from qgis.core import Qgis, QgsMessageLog

from geocomp.core.errors import GeoCompError

__all__ = ["GeoCompLog", "LogLevel", "log"]

#: The tab the messages appear under in the QGIS log panel.
LOG_TAG = "GeoComp"


class LogLevel(IntEnum):
    """Ordered so that a threshold comparison is a plain ``>=``."""

    DEBUG = 10
    INFO = 20
    WARNING = 30
    CRITICAL = 40

    @classmethod
    def from_setting(cls, value: str) -> LogLevel:
        """Map an ``interface.log_level`` choice onto a level.

        An unrecognised value yields ``INFO`` rather than raising: failing to
        log because the log level is misconfigured would be an unhelpful way to
        lose the message that explains the misconfiguration.
        """
        return {
            "debug": cls.DEBUG,
            "info": cls.INFO,
            "warning": cls.WARNING,
            "critical": cls.CRITICAL,
        }.get(str(value).lower(), cls.INFO)

    @property
    def qgis_level(self) -> Qgis.MessageLevel:
        return {
            LogLevel.DEBUG: Qgis.MessageLevel.Info,
            LogLevel.INFO: Qgis.MessageLevel.Info,
            LogLevel.WARNING: Qgis.MessageLevel.Warning,
            LogLevel.CRITICAL: Qgis.MessageLevel.Critical,
        }[self]


class GeoCompLog:
    """Thin, testable wrapper over ``QgsMessageLog``."""

    def __init__(self, threshold: LogLevel = LogLevel.INFO) -> None:
        self._threshold = threshold

    @property
    def threshold(self) -> LogLevel:
        return self._threshold

    def set_threshold(self, threshold: LogLevel) -> None:
        self._threshold = threshold

    def _emit(self, level: LogLevel, message: str) -> None:
        if level < self._threshold:
            return
        prefix = "" if level is not LogLevel.DEBUG else "[debug] "
        QgsMessageLog.logMessage(f"{prefix}{message}", LOG_TAG, level.qgis_level)

    def debug(self, message: str, **context: Any) -> None:
        self._emit(LogLevel.DEBUG, _with_context(message, context))

    def info(self, message: str, **context: Any) -> None:
        self._emit(LogLevel.INFO, _with_context(message, context))

    def warning(self, message: str, **context: Any) -> None:
        self._emit(LogLevel.WARNING, _with_context(message, context))

    def critical(self, message: str, **context: Any) -> None:
        self._emit(LogLevel.CRITICAL, _with_context(message, context))

    def exception(self, exc: BaseException, *, message: str = "unhandled exception") -> None:
        """Log an exception with its traceback.

        A :class:`~geocomp.core.errors.GeoCompError` logs its structured code
        and context, which is what makes a failure searchable later.
        """
        if isinstance(exc, GeoCompError):
            self._emit(LogLevel.CRITICAL, _with_context(message, exc.to_dict()))
        else:
            self._emit(LogLevel.CRITICAL, f"{message}: {type(exc).__name__}: {exc}")
        self._emit(LogLevel.DEBUG, "".join(traceback.format_exception(exc)).rstrip())


def _with_context(message: str, context: dict[str, Any]) -> str:
    if not context:
        return message
    detail = " ".join(f"{key}={value!r}" for key, value in sorted(context.items()))
    return f"{message} | {detail}"


#: Process-wide logger. Its threshold is set from settings during plugin
#: start-up and whenever the setting changes.
log = GeoCompLog()
