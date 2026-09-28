# SPDX-License-Identifier: GPL-2.0-or-later
"""What a monitoring result draws on the map (``specs/19`` sections 1 and 3).

A displacement is drawn as an arrow from where the first epoch put the station,
at a stated exaggeration, with **its confidence ellipse at the tip** -- so a
reader sees whether zero, the tail, lies inside it (``specs/14`` section 4.1).
A velocity is drawn the same way, as a year's motion. Pure geometry from the
documents of :mod:`geocomp.core.monitoring.document`; the QGIS layers in
:mod:`geocomp.layers.builders` only wrap it.

**One category per station, for the style.** ``alert`` when any of the
station's thresholds was crossed -- whether or not the motion is significant,
because the owner's criterion is not silenced by the survey's (``specs/14``
section 7) -- then ``significant`` or ``not significant``. Three categories and
three symbols, because that is the decision structure (``specs/19`` section 2).

**On a geocentric comparison** the displacement is in each station's east and
north, and the map is the UTM grid of the frame. The two norths differ by the
grid convergence, over a degree at a zone's edge; each station's arrow and
ellipse are turned by it, as the adjustment layers' are.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import Any

from geocomp.core.models import ErrorEllipse
from geocomp.core.visualization.geometry import (
    DrawnEllipse,
    default_exaggeration,
    displacement_arrow,
    ellipse_ring,
)

__all__ = [
    "ALERT",
    "CATEGORIES",
    "DrawnDisplacement",
    "DrawnVelocity",
    "displacement_exaggeration",
    "drawn_displacements",
    "drawn_velocities",
    "station_category",
    "velocity_exaggeration",
]

ALERT = "alert"
SIGNIFICANT = "significant"
NOT_SIGNIFICANT = "not significant"
#: The categories a monitoring layer's style draws, strongest first.
CATEGORIES = (ALERT, SIGNIFICANT, NOT_SIGNIFICANT)

#: The largest arrow spans this fraction of the network's shorter side in the
#: automatic factor: long enough to read a direction, short enough not to cross
#: the neighbouring station.
_TARGET_FRACTION = 0.15


@dataclass(frozen=True)
class DrawnDisplacement:
    """One station's displacement as drawn, and the numbers its feature carries."""

    station: str
    record: dict[str, Any]
    tail: tuple[float, float]
    tip: tuple[float, float]
    ellipse: DrawnEllipse | None
    category: str
    alerts: tuple[str, ...]
    exaggeration: float


@dataclass(frozen=True)
class DrawnVelocity:
    """One station's velocity as drawn: a year's motion, exaggerated."""

    station: str
    record: dict[str, Any]
    tail: tuple[float, float]
    tip: tuple[float, float]
    category: str
    alerts: tuple[str, ...]
    exaggeration: float


def station_category(
    station: str, decision: str | None, alerts: list[dict[str, Any]]
) -> tuple[str, tuple[str, ...]]:
    """The style category of *station*, and the kinds of alert it crossed."""
    crossed = tuple(sorted({a["kind"] for a in alerts if a["station"] == station and a["exceeded"]}))
    if crossed:
        return ALERT, crossed
    return (SIGNIFICANT if decision == SIGNIFICANT else NOT_SIGNIFICANT), crossed


def displacement_exaggeration(document: dict[str, Any]) -> float:
    """A first factor fitted to the network: the largest horizontal
    displacement drawn at a fraction of the network's extent.

    Returns 1 when there is nothing to scale -- no plan, or no motion.
    """
    sizes = [
        d["horizontal_magnitude"]
        for d in document.get("displacements", [])
        if d.get("horizontal_magnitude") and d["station"] in document["display"]["positions"]
    ]
    return _fitted(document["display"]["positions"], sizes)


def velocity_exaggeration(document: dict[str, Any]) -> float:
    """The same for a series: a year's largest horizontal motion."""
    sizes = [s["speed"] for s in document.get("stations", []) if s.get("speed") and _plan_velocity(s)]
    return _fitted(document["display"]["positions"], sizes)


def drawn_displacements(document: dict[str, Any], *, exaggeration: float) -> list[DrawnDisplacement]:
    """Every displacement the document places on the map, drawn at *exaggeration*.

    A station without a plan position is left out rather than drawn at the
    origin; a heights-only displacement is drawn as a point-length arrow whose
    attributes carry the vertical motion.
    """
    display = document["display"]
    alerts = document.get("alerts", [])
    drawn: list[DrawnDisplacement] = []
    for record in document.get("displacements", []):
        station = record["station"]
        origin = display["positions"].get(station)
        if origin is None:
            continue
        bearing = display.get("rotations", {}).get(station, 0.0)
        east, north = _plan(record["components"], record["values"])
        shift = _turned(east, north, bearing)
        tail, tip = displacement_arrow(tuple(origin), shift, exaggeration=exaggeration)
        ellipse = None
        if record.get("ellipse"):
            region = ErrorEllipse.from_dict(record["ellipse"])
            region = replace(region, orientation=(region.orientation + bearing) % math.pi)
            ellipse = ellipse_ring(tip, region, exaggeration=exaggeration)
        category, crossed = station_category(station, record.get("decision"), alerts)
        drawn.append(
            DrawnDisplacement(
                station=station,
                record=record,
                tail=tail,
                tip=tip,
                ellipse=ellipse,
                category=category,
                alerts=crossed,
                exaggeration=exaggeration,
            )
        )
    return drawn


def drawn_velocities(document: dict[str, Any], *, exaggeration: float) -> list[DrawnVelocity]:
    """Every velocity the series document places on the map, as a year's motion."""
    display = document["display"]
    alerts = document.get("alerts", [])
    drawn: list[DrawnVelocity] = []
    for record in document.get("stations", []):
        station = record["station"]
        origin = display["positions"].get(station)
        if origin is None or record.get("velocity") is None:
            continue
        bearing = display.get("rotations", {}).get(station, 0.0)
        east, north = _plan(record["components"], record["velocity"])
        shift = _turned(east, north, bearing)
        tail, tip = displacement_arrow(tuple(origin), shift, exaggeration=exaggeration)
        test = record.get("velocity_test")
        decision = None if test is None else (NOT_SIGNIFICANT if test["passed"] else SIGNIFICANT)
        category, crossed = station_category(station, decision, alerts)
        drawn.append(
            DrawnVelocity(
                station=station,
                record=record,
                tail=tail,
                tip=tip,
                category=category,
                alerts=crossed,
                exaggeration=exaggeration,
            )
        )
    return drawn


# -- internals -----------------------------------------------------------------


def _plan(components: list[str], values: list[float]) -> tuple[float, float]:
    if "e" in components and "n" in components:
        return values[components.index("e")], values[components.index("n")]
    return 0.0, 0.0


def _plan_velocity(record: dict[str, Any]) -> bool:
    return "e" in record["components"] and "n" in record["components"] and record.get("velocity") is not None


def _turned(east: float, north: float, bearing: float) -> tuple[float, float]:
    """East and north onto a grid whose north is *bearing* from geodetic north."""
    if bearing == 0.0:
        return east, north
    c, s = math.cos(bearing), math.sin(bearing)
    return east * c + north * s, -east * s + north * c


def _fitted(positions: dict[str, list[float]], sizes: list[float]) -> float:
    if len(positions) < 2 or not sizes or max(sizes) <= 0.0:
        return 1.0
    eastings = [p[0] for p in positions.values()]
    northings = [p[1] for p in positions.values()]
    width, height = max(eastings) - min(eastings), max(northings) - min(northings)
    span = max(width, height)
    if span <= 0.0:
        return 1.0
    width, height = (width or span), (height or span)
    return default_exaggeration((width, height), sizes, target_fraction=_TARGET_FRACTION)
