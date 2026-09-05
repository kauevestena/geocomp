# SPDX-License-Identifier: GPL-2.0-or-later
"""Rendering the HTML reports every GeoComp algorithm produces.

Extracted from ``geocomp.algorithms.analysis.common`` in phase P3, when the
total-station algorithms needed the same helpers: three groups producing three
sets of reports that looked like three different plugins would be worse than one
shared stylesheet and one table helper.

Rendering lives here rather than in ``core/`` because phrasing is a presentation
concern -- ``core`` cannot import Qt at all (NFR-002), so it cannot translate a
heading (``specs/18`` section 2).
"""

from __future__ import annotations

import html
import math
from typing import Any

from qgis.PyQt.QtCore import QCoreApplication

__all__ = [
    "escape",
    "format_number",
    "render_document",
    "render_findings",
    "render_note",
    "render_table",
]

_CONTEXT = "GeoCompReport"


def _tr(text: str) -> str:
    return QCoreApplication.translate(_CONTEXT, text)


def escape(value: Any) -> str:
    return html.escape(str(value))


def exact(value: Any) -> str:
    """A number written to full precision, for a machine to read back.

    ``repr`` was used for this and is wrong: under NumPy 2 the repr of a
    ``np.float64`` is ``"np.float64(1.93e-06)"``, not ``"1.93e-06"``, so every
    CSV written from an adjustment -- which is NumPy throughout -- became
    unreadable by anything that parses numbers. NumPy 1 printed the bare value,
    so the same code produced two different files depending on a version nobody
    had pinned.

    Converting to a built-in ``float`` first fixes both halves: full round-trip
    precision, and one output regardless of what the value arrived as. ``None``
    is the empty cell, which is what a CSV reader expects for "no value" rather
    than the string "None".
    """
    if value is None:
        return ""
    return repr(float(value))


def format_number(value: Any, decimals: int = 4) -> str:
    """Format a number for a report, without inventing precision.

    ``None`` renders as an em dash rather than "None", and a non-finite value
    says so: an MDB of infinity means the observation is uncheckable, and
    printing ``inf`` in a column of millimetres reads as a bug rather than as
    the fact it is.
    """
    if value is None:
        return "—"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return escape(value)
    if math.isnan(number):
        return _tr("not defined")
    if math.isinf(number):
        return "∞" if number > 0 else "-∞"
    if number != 0.0 and (abs(number) < 10.0**-decimals or abs(number) >= 1.0e6):
        return f"{number:.{decimals}e}"
    return f"{number:.{decimals}f}"


def render_note(text: str, *, label: str = "") -> str:
    """A call-out box for something the reader must not skim past.

    Used for the things a table cannot say -- that the pieces of a disconnected
    network each carry their own datum, that an uncheckable observation makes
    the passing tests say nothing about it.
    """
    prefix = f"<b>{escape(label)}</b>: " if label else ""
    return f'<div class="note">{prefix}{escape(text)}</div>'


def render_table(headers: list[str], rows: list[list[str]], *, css_class: str = "") -> str:
    """An HTML table whose cells are already escaped by the caller.

    Cells arrive escaped rather than being escaped here because several columns
    carry deliberate markup -- a highlighted decision, a unit superscript -- and
    a helper that escaped everything would force those callers to work around it.
    """
    attribute = f' class="{css_class}"' if css_class else ""
    parts = [f"<table{attribute}>", "<tr>"]
    parts.extend(f"<th>{header}</th>" for header in headers)
    parts.append("</tr>")
    for row in rows:
        parts.append("<tr>")
        parts.extend(f"<td>{cell}</td>" for cell in row)
        parts.append("</tr>")
    parts.append("</table>")
    return "\n".join(parts)


#: One stylesheet for every GeoComp report, so three algorithms produce three
#: reports that look like one plugin's.
_STYLE = (
    "body{font-family:sans-serif;margin:2rem;line-height:1.5;max-width:60rem}"
    "table{border-collapse:collapse;margin-bottom:1.5rem;width:100%}"
    "th,td{border:1px solid #ccc;padding:.35rem .6rem;text-align:left;vertical-align:top}"
    "th{background:#f2f2f2}"
    "td.num{text-align:right;font-variant-numeric:tabular-nums}"
    "code{font-family:monospace}"
    ".pass{color:#14611f;font-weight:bold}"
    ".fail{color:#8a1207;font-weight:bold}"
    ".blocking{color:#8a1207;font-weight:bold}"
    ".warning{color:#8a5000;font-weight:bold}"
    ".note{background:#f7f7f2;border-left:4px solid #999;padding:.6rem 1rem;margin:1rem 0}"
    "footer{margin-top:2rem;color:#555;font-size:.9em}"
)


def render_document(title: str, body: list[str], *, footer: str = "") -> str:
    """Wrap report *body* fragments in a complete, self-contained HTML document.

    Self-contained deliberately: a report is attached to an email or a client
    deliverable, and one that needs a stylesheet from the plugin directory
    arrives unstyled (``specs/19`` section 7).
    """
    parts = [
        "<!doctype html>",
        '<html><head><meta charset="utf-8">',
        f"<title>{escape(title)}</title>",
        f"<style>{_STYLE}</style></head><body>",
        f"<h1>{escape(title)}</h1>",
    ]
    parts.extend(body)
    if footer:
        parts.append(f"<footer>{footer}</footer>")
    parts.append("</body></html>")
    return "\n".join(parts)


def render_findings(rows: list[tuple[str, str, str, str]], headers: list[str]) -> str:
    """A findings table, with the severity column already marked up.

    Rows arrive as ``(severity markup, code, message, involves)``. Separate from
    :func:`render_table` only so every algorithm's findings table has the same
    columns in the same order -- a user reading two GeoComp reports should not
    have to re-learn the layout.
    """
    return render_table([escape(h) for h in headers], [list(row) for row in rows])
