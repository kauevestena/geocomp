# SPDX-License-Identifier: GPL-2.0-or-later
"""The decimal separator of a number a person reads (FR-094; phase P12c).

``specs/18`` §5: pt-BR and es write a decimal comma, and the separator must not
be hard-coded. Until P12c every report, table and panel printed a point in
every language. The translated text then read *desvio-padrão 0.0021 m* in
Portuguese, and in a language where the point groups thousands that is a
number a thousand times too large.

**Only what a person reads.** A file is written with a point whatever the
language (FR-095), so nothing here is called on the way to one:
:func:`geocomp.algorithms.reporting.exact` and the engines' writers format for a
machine. What calls this is the two formatters every report goes through --
:func:`geocomp.algorithms.reporting.format_number` and
:class:`~geocomp.core.display_format.DisplayFormat` -- which turn the point of
a number they have just formatted into the locale's separator.

**Where the separator comes from.** The language GeoComp's own words are in,
whatever QGIS's is (``specs/18`` criterion 3): a Portuguese report with English
numbers, or the reverse, would be the inconsistency the override exists to
prevent. The plugin sets it when it installs the catalogue
(:func:`set_display_locale`); a Processing run reads it at its start, so a run
is in one language throughout (:func:`numbers_for`). Thread-safe: the value a
run uses is held in a context variable, which a worker thread has its own of.

**Not built.** Thousands grouping and locale dates: a report still prints
``7395123,4567`` rather than grouping the digits, and dates as ISO 8601.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

__all__ = [
    "SEPARATORS",
    "decimal_separator",
    "localised",
    "localised_if_number",
    "numbers_for",
    "separator_for",
    "set_display_locale",
]

#: The decimal separator of each shipped language.
SEPARATORS = {"en": ".", "pt_BR": ",", "es": ","}

#: A value that is a decimal number and nothing else, as a setting's is stored.
_DECIMAL_NUMBER = re.compile(r"-?\d+\.\d+(?:[eE][-+]?\d+)?")

#: The language the plugin's words are in: set once, when it installs them.
_display_locale = "en"

#: The separator a run in progress uses, when one has set it.
_RUN_SEPARATOR: ContextVar[str | None] = ContextVar("geocomp_decimal_separator", default=None)


def separator_for(locale: str) -> str:
    """The decimal separator of *locale*: a shipped one, or its language's."""
    if locale in SEPARATORS:
        return SEPARATORS[locale]
    language = locale.replace("-", "_").split("_", 1)[0].lower()
    return {"pt": ",", "es": ","}.get(language, ".")


def set_display_locale(locale: str) -> None:
    """The language GeoComp shows its words in, so its numbers agree with them."""
    global _display_locale
    _display_locale = locale


def decimal_separator() -> str:
    """The separator to write now: the run's, if one is in progress, else the display's."""
    separator = _RUN_SEPARATOR.get()
    return separator if separator is not None else separator_for(_display_locale)


@contextmanager
def numbers_for(locale: str | None = None) -> Iterator[None]:
    """Write numbers for *locale* -- by default the display's -- until the block ends."""
    token = _RUN_SEPARATOR.set(separator_for(locale or _display_locale))
    try:
        yield
    finally:
        _RUN_SEPARATOR.reset(token)


def localised(text: str) -> str:
    """*text*, a number just formatted with a point, with the locale's separator.

    Only for a string that is a formatted number, and nothing else: a version
    number or a file name in the same string would be changed too.
    """
    separator = decimal_separator()
    return text if separator == "." else text.replace(".", separator)


def localised_if_number(text: str) -> str:
    """*text* localised when it is a decimal number, and unchanged when it is anything else.

    For a value that arrives as text -- a setting's, recorded in a solution's
    provenance -- where a number and a CRS or a path share one column.
    """
    return localised(text) if _DECIMAL_NUMBER.fullmatch(text.strip()) else text
