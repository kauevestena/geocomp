# SPDX-License-Identifier: GPL-2.0-or-later
"""The monitoring report's pictures, as inline SVG (FR-932; ``specs/19`` section 7.2).

A report is attached to an email or a client deliverable, so its map and its
plots travel inside it: SVG text, no image files, no QGIS canvas. Drawn from
the same documents and the same geometry as the map layers
(:mod:`geocomp.core.visualization.monitoring`), so the picture in the report
and the layer on the map cannot show two different things.

**The exaggeration is stated in the picture itself** (FR-901): an arrow a
centimetre long for a displacement of a millimetre is a misrepresentation
unless the drawing says so, and a report is read away from any legend.

Deterministic (NFR-007): every coordinate is written with fixed decimals, so
the same document draws the same bytes. No text is phrased here -- the caller
passes the translated words, because the core does not phrase
(``specs/18`` section 2).
"""

from __future__ import annotations

import html
import math
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from geocomp.core.number_format import localised
from geocomp.core.visualization.monitoring import ALERT, SIGNIFICANT, drawn_displacements, series_curves

__all__ = ["COLOURS", "MapText", "PlotText", "displacement_map", "series_plot"]

#: The layer styles' colours (Okabe--Ito, colour-vision-deficiency safe), so the
#: report's picture reads like the map.
COLOURS = {ALERT: "#d55e00", SIGNIFICANT: "#0072b2", "not significant": "#787878"}
_REFERENCE = "#333333"

_WIDTH = 640.0
_MARGIN = 36.0


@dataclass(frozen=True)
class MapText:
    """The translated words of the displacement map."""

    caption: str
    legend: dict[str, str]
    reference: str
    obj: str
    scale_unit: str = "m"


@dataclass(frozen=True)
class PlotText:
    """The translated words of one time-series plot."""

    title: str
    x_label: str
    y_label: str
    band: str
    fit: str
    threshold: str
    epochs: dict[float, str] = field(default_factory=dict)


# -- the map -------------------------------------------------------------------


def displacement_map(document: dict[str, Any], *, exaggeration: float, text: MapText) -> str:
    """Every placed station, its arrow and its ellipse, with the factor stated.

    Returns an empty string when the document places nothing -- a heights-only
    comparison with no plan -- rather than an empty frame that looks like a
    failed image.
    """
    drawn = drawn_displacements(document, exaggeration=exaggeration)
    if not drawn:
        return ""
    reference = set(document.get("reference", []))
    points = [d.tail for d in drawn] + [d.tip for d in drawn]
    for d in drawn:
        if d.ellipse is not None:
            points.extend(d.ellipse.ring)
    project, height, scale = _frame(points)

    parts = [_open(_WIDTH, height + 64.0)]
    for d in drawn:
        colour = COLOURS[d.category]
        if d.ellipse is not None:
            ring = " ".join(_xy(project(p)) for p in d.ellipse.ring)
            parts.append(
                f'<polygon points="{ring}" fill="{colour}" fill-opacity="0.12" stroke="{colour}" '
                'stroke-width="1"/>'
            )
    for d in drawn:
        colour = COLOURS[d.category]
        (x1, y1), (x2, y2) = project(d.tail), project(d.tip)
        width = 2.5 if d.category == ALERT else (2.0 if d.category == SIGNIFICANT else 1.2)
        parts.append(_arrow(x1, y1, x2, y2, colour, width))
    for d in drawn:
        x, y = project(d.tail)
        if d.station in reference:
            parts.append(
                f'<polygon points="{_f(x)},{_f(y - 6)} {_f(x - 5.5)},{_f(y + 4)} {_f(x + 5.5)},{_f(y + 4)}" '
                f'fill="{_REFERENCE}"/>'
            )
        else:
            parts.append(f'<circle cx="{_f(x)}" cy="{_f(y)}" r="3.5" fill="#ffffff" stroke="{_REFERENCE}"/>')
        parts.append(
            f'<text x="{_f(x + 7)}" y="{_f(y - 6)}" font-size="11" font-family="sans-serif">'
            f"{_e(d.station)}</text>"
        )
    parts.append(_scale_bar(scale, height, text.scale_unit))
    parts.append(_legend(text, height))
    parts.append("</svg>")
    return "\n".join(parts)


def _frame(points: Sequence[tuple[float, float]]):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    span_x = max(xs) - min(xs) or 1.0
    span_y = max(ys) - min(ys) or 1.0
    inner = _WIDTH - 2 * _MARGIN
    scale = inner / max(span_x, span_y)
    height = span_y * scale + 2 * _MARGIN
    x0, y1 = min(xs), max(ys)

    def project(point: tuple[float, float]) -> tuple[float, float]:
        return _MARGIN + (point[0] - x0) * scale, _MARGIN + (y1 - point[1]) * scale

    return project, height, scale


def _arrow(x1: float, y1: float, x2: float, y2: float, colour: str, width: float) -> str:
    length = math.hypot(x2 - x1, y2 - y1)
    line = (
        f'<line x1="{_f(x1)}" y1="{_f(y1)}" x2="{_f(x2)}" y2="{_f(y2)}" stroke="{colour}" '
        f'stroke-width="{width:g}" stroke-linecap="round"/>'
    )
    if length < 1.0:
        return line
    ux, uy = (x2 - x1) / length, (y2 - y1) / length
    head = min(9.0, 0.4 * length) + width
    left = (x2 - head * ux - 0.45 * head * uy, y2 - head * uy + 0.45 * head * ux)
    right = (x2 - head * ux + 0.45 * head * uy, y2 - head * uy - 0.45 * head * ux)
    return line + (
        f'\n<polygon points="{_f(x2)},{_f(y2)} {_xy(left)} {_xy(right)}" fill="{colour}"/>'
    )


def _scale_bar(scale: float, height: float, unit: str) -> str:
    """A bar of a round true length, so distances on the map can be read."""
    target = (_WIDTH - 2 * _MARGIN) / 5.0 / scale
    length = _nice(target)
    pixels = length * scale
    y = height + 14.0
    return (
        f'<line x1="{_f(_MARGIN)}" y1="{_f(y)}" x2="{_f(_MARGIN + pixels)}" y2="{_f(y)}" '
        'stroke="#000000" stroke-width="2"/>\n'
        f'<text x="{_f(_MARGIN)}" y="{_f(y + 14)}" font-size="11" font-family="sans-serif">'
        f"{_e(f'{length:g} {unit}')}</text>"
    )


def _legend(text: MapText, height: float) -> str:
    x = _MARGIN + 140.0
    y = height + 12.0
    parts = []
    for category in (ALERT, SIGNIFICANT, "not significant"):
        label = text.legend.get(category)
        if not label:
            continue
        parts.append(
            f'<line x1="{_f(x)}" y1="{_f(y - 4)}" x2="{_f(x + 16)}" y2="{_f(y - 4)}" '
            f'stroke="{COLOURS[category]}" stroke-width="2.5"/>'
            f'<text x="{_f(x + 20)}" y="{_f(y)}" font-size="11" font-family="sans-serif">{_e(label)}</text>'
        )
        x += 20.0 + 7.0 * len(label) + 12.0
    parts.append(
        f'<text x="{_f(_MARGIN + 140.0)}" y="{_f(y + 18)}" font-size="11" font-family="sans-serif">'
        f"&#9650; {_e(text.reference)}   &#9675; {_e(text.obj)}   {_e(text.caption)}</text>"
    )
    return "\n".join(parts)


# -- a series --------------------------------------------------------------------


def series_plot(
    record: dict[str, Any],
    component: str,
    *,
    band_factor: float,
    thresholds: Sequence[float] = (),
    text: PlotText,
) -> str:
    """One station's offsets in one component across the epochs, in millimetres.

    Each epoch's offset with its band (``band_factor`` sigma, which the caller
    states in ``text.band``), the fitted line, and any alert limit as a dashed
    line at plus and minus its value.
    """
    (curve,) = series_curves({"stations": [record]}, [record["station"]], component, band_factor=band_factor)
    epochs, values = list(curve.epochs), list(curve.values)
    sigmas = [h - v for h, v in zip(curve.high, curve.values, strict=True)]
    limits = [1000.0 * t for t in thresholds]
    low = min([v - s for v, s in zip(values, sigmas, strict=True)] + [-t for t in limits] + [0.0])
    high = max([v + s for v, s in zip(values, sigmas, strict=True)] + limits + [0.0])
    pad = 0.08 * (high - low or 1.0)
    low, high = low - pad, high + pad
    t0, t1 = min(epochs), max(epochs)
    span_t = (t1 - t0) or 1.0
    width, height = _WIDTH, 240.0
    left, right, top, bottom = 58.0, 16.0, 26.0, 40.0

    def px(t: float) -> float:
        return left + (t - t0) / span_t * (width - left - right)

    def py(v: float) -> float:
        return top + (high - v) / (high - low) * (height - top - bottom)

    parts = [_open(width, height)]
    parts.append(
        f'<text x="{_f(left)}" y="16" font-size="12" font-weight="bold" font-family="sans-serif">'
        f"{_e(text.title)}</text>"
    )
    # axes and ticks
    parts.append(
        f'<line x1="{_f(left)}" y1="{_f(top)}" x2="{_f(left)}" y2="{_f(height - bottom)}" stroke="#000"/>'
        f'<line x1="{_f(left)}" y1="{_f(height - bottom)}" x2="{_f(width - right)}" '
        f'y2="{_f(height - bottom)}" stroke="#000"/>'
    )
    for tick in _ticks(low, high):
        y = py(tick)
        parts.append(
            f'<line x1="{_f(left - 4)}" y1="{_f(y)}" x2="{_f(width - right)}" y2="{_f(y)}" '
            'stroke="#dddddd"/>'
            f'<text x="{_f(left - 6)}" y="{_f(y + 4)}" font-size="10" text-anchor="end" '
            f'font-family="sans-serif">{tick:g}</text>'
        )
    for epoch in sorted(set(epochs)):
        x = px(epoch)
        label = text.epochs.get(epoch, localised(f"{epoch:.2f}"))
        parts.append(
            f'<text x="{_f(x)}" y="{_f(height - bottom + 14)}" font-size="10" text-anchor="middle" '
            f'font-family="sans-serif">{_e(label)}</text>'
        )
    parts.append(
        f'<text x="{_f((left + width - right) / 2)}" y="{_f(height - 6)}" font-size="10" '
        f'text-anchor="middle" font-family="sans-serif">{_e(text.x_label)}</text>'
        f'<text x="12" y="{_f((top + height - bottom) / 2)}" font-size="10" text-anchor="middle" '
        f'font-family="sans-serif" transform="rotate(-90 12 {_f((top + height - bottom) / 2)})">'
        f"{_e(text.y_label)}</text>"
    )
    # zero, thresholds, band, fit, points
    parts.append(
        f'<line x1="{_f(left)}" y1="{_f(py(0.0))}" x2="{_f(width - right)}" y2="{_f(py(0.0))}" '
        'stroke="#999999"/>'
    )
    for limit in limits:
        for value in (limit, -limit):
            parts.append(
                f'<line x1="{_f(left)}" y1="{_f(py(value))}" x2="{_f(width - right)}" '
                f'y2="{_f(py(value))}" stroke="{COLOURS[ALERT]}" stroke-dasharray="6 4"/>'
            )
    upper = [(px(t), py(v + s)) for t, v, s in zip(epochs, values, sigmas, strict=True)]
    lower = [(px(t), py(v - s)) for t, v, s in zip(epochs, values, sigmas, strict=True)]
    band = " ".join(_xy(p) for p in upper + lower[::-1])
    parts.append(
        f'<polygon points="{band}" fill="{COLOURS[SIGNIFICANT]}" fill-opacity="0.15" stroke="none"/>'
    )
    if curve.fit is not None:
        (ta, a), (tb, b) = curve.fit
        parts.append(
            f'<line x1="{_f(px(ta))}" y1="{_f(py(a))}" x2="{_f(px(tb))}" y2="{_f(py(b))}" '
            f'stroke="{COLOURS[SIGNIFICANT]}" stroke-dasharray="3 3" stroke-width="1.5"/>'
        )
    for t, v, s in zip(epochs, values, sigmas, strict=True):
        x = px(t)
        parts.append(
            f'<line x1="{_f(x)}" y1="{_f(py(v - s))}" x2="{_f(x)}" y2="{_f(py(v + s))}" '
            f'stroke="{COLOURS[SIGNIFICANT]}"/>'
            f'<circle cx="{_f(x)}" cy="{_f(py(v))}" r="3" fill="{COLOURS[SIGNIFICANT]}"/>'
        )
    legend = f"{text.band} · {text.fit}" + (f" · {text.threshold}" if limits else "")
    parts.append(
        f'<text x="{_f(width - right)}" y="16" font-size="10" text-anchor="end" '
        f'font-family="sans-serif">{_e(legend)}</text>'
    )
    parts.append("</svg>")
    return "\n".join(parts)


def _ticks(low: float, high: float) -> list[float]:
    step = _nice((high - low) / 5.0)
    first = math.ceil(low / step) * step
    ticks = []
    value = first
    while value <= high + 1e-12:
        ticks.append(round(value, 10))
        value += step
    return ticks


# -- helpers ----------------------------------------------------------------------


def _nice(value: float) -> float:
    """The largest 1-2-5 x 10^n not above *value*, of any size: a scale bar or an
    axis step reads as a round number whether it is 200 m or 0.5 mm."""
    if not value > 0.0 or not math.isfinite(value):
        return 1.0
    decade = 10.0 ** math.floor(math.log10(value))
    for step in (5.0, 2.0, 1.0):
        if step * decade <= value * (1.0 + 1e-12):
            return step * decade
    return decade


def _open(width: float, height: float) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{_f(width)}" height="{_f(height)}" '
        f'viewBox="0 0 {_f(width)} {_f(height)}">'
    )


def _f(value: float) -> str:
    return f"{value:.2f}"


def _xy(point: tuple[float, float]) -> str:
    return f"{_f(point[0])},{_f(point[1])}"


def _e(text: str) -> str:
    return html.escape(str(text))
