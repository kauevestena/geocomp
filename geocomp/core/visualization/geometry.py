# SPDX-License-Identifier: GPL-2.0-or-later
"""Map geometry for adjustment results (FR-900, FR-901).

``specs/19-visualization.md`` sections 1 and 3.

Real error ellipses are invisible: a 5 mm semi-axis on a 1:5000 map is a
micron. Everything drawn from an adjustment is therefore exaggerated, and
``specs/19`` calls stating that exaggeration **the single most important rule
in the document** -- an unstated one turns a quality visualisation into a
misrepresentation.

That rule is enforced here by the signatures. ``exaggeration`` is a required
keyword argument of every function that produces map geometry: there is no
default to fall through, so a call site cannot omit it by accident, and the
factor a layer states in its legend is necessarily the factor its geometry was
drawn with.

The module is pure geometry with no QGIS in it, so the vertices can be checked
against closed-form values here rather than only inside a QGIS runtime.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from geocomp.core.errors import ValidationError
from geocomp.core.models import ErrorEllipse

__all__ = [
    "DEFAULT_VERTEX_COUNT",
    "DrawnEllipse",
    "default_exaggeration",
    "displacement_arrow",
    "ellipse_ring",
    "nice_factor",
    "scale_reference_ring",
]

#: Enough that the curve reads as a curve at any sensible zoom, and few enough
#: that a thousand-station network stays a usable layer.
DEFAULT_VERTEX_COUNT = 72


@dataclass(frozen=True)
class DrawnEllipse:
    """An ellipse as drawn: its ring, and everything needed to read it.

    The confidence level and the exaggeration travel with the vertices rather
    than beside them, because a ring on its own is not interpretable and the
    two numbers are exactly what the legend has to state.
    """

    ring: tuple[tuple[float, float], ...]
    exaggeration: float
    confidence: float
    semi_major: float
    semi_minor: float
    orientation: float

    @property
    def is_exaggerated(self) -> bool:
        return self.exaggeration != 1.0


def ellipse_ring(
    centre: tuple[float, float],
    ellipse: ErrorEllipse,
    *,
    exaggeration: float,
    vertices: int = DEFAULT_VERTEX_COUNT,
) -> DrawnEllipse:
    """The closed ring of an error ellipse, drawn about *centre*.

    ``ellipse.orientation`` is an azimuth from north, clockwise, as the rest of
    GeoComp reports it, so the semi-major axis points along ``(sin a, cos a)``
    in (easting, northing) and the semi-minor along the perpendicular
    ``(cos a, -sin a)``.

    Args:
        exaggeration: The factor the semi-axes are multiplied by. Required, and
            required to be stated wherever the result is drawn.
        vertices: Points around the ellipse. The returned ring repeats the
            first as its last, so it is closed.
    """
    _check_exaggeration(exaggeration)
    if vertices < 8:
        raise ValidationError(
            "ellipse_too_few_vertices",
            received=vertices,
            expected="at least 8 vertices, or the ring reads as a polygon rather than "
            "an ellipse",
        )

    east, north = centre
    azimuth = ellipse.orientation
    sin_a, cos_a = math.sin(azimuth), math.cos(azimuth)
    semi_major = ellipse.semi_major * exaggeration
    semi_minor = ellipse.semi_minor * exaggeration

    ring = []
    for index in range(vertices):
        angle = math.tau * index / vertices
        along = semi_major * math.cos(angle)
        across = semi_minor * math.sin(angle)
        ring.append(
            (
                east + along * sin_a + across * cos_a,
                north + along * cos_a - across * sin_a,
            )
        )
    ring.append(ring[0])

    return DrawnEllipse(
        ring=tuple(ring),
        exaggeration=exaggeration,
        confidence=ellipse.confidence,
        semi_major=ellipse.semi_major,
        semi_minor=ellipse.semi_minor,
        orientation=ellipse.orientation,
    )


def scale_reference_ring(
    centre: tuple[float, float],
    true_radius: float,
    *,
    exaggeration: float,
    vertices: int = DEFAULT_VERTEX_COUNT,
) -> DrawnEllipse:
    """A circle of a stated true size, drawn at the same exaggeration (FR-901 §6).

    This is what makes an exaggerated map readable rather than merely honest: a
    reader who is told the factor still has to do arithmetic, whereas a circle
    labelled "10 mm" next to the network is read directly.
    """
    if true_radius <= 0.0:
        raise ValidationError(
            "scale_reference_not_positive",
            received=true_radius,
            expected="a positive true radius, in the coordinate system's units",
        )
    reference = ErrorEllipse(
        semi_major=true_radius, semi_minor=true_radius, orientation=0.0, confidence=1.0
    )
    return ellipse_ring(centre, reference, exaggeration=exaggeration, vertices=vertices)


def displacement_arrow(
    origin: tuple[float, float],
    displacement: tuple[float, float],
    *,
    exaggeration: float,
) -> tuple[tuple[float, float], tuple[float, float]]:
    """The drawn line of a residual or displacement vector.

    Returns the origin and the exaggerated tip. Vectors carry the same
    treatment as ellipses (``specs/19`` section 3): a displacement drawn at an
    unstated scale is the same misrepresentation as an ellipse drawn at one.
    """
    _check_exaggeration(exaggeration)
    east, north = origin
    return (
        (east, north),
        (east + displacement[0] * exaggeration, north + displacement[1] * exaggeration),
    )


def default_exaggeration(
    extent: tuple[float, float],
    sizes: list[float] | tuple[float, ...],
    *,
    target_fraction: float = 0.05,
) -> float:
    """A first exaggeration that makes the largest ellipse visible (FR-901 §3).

    Chosen so the biggest thing drawn spans about *target_fraction* of the
    shorter side of the map extent, then rounded down to a 1-2-5 value: a
    legend reading "x500" is read at a glance, and "x487.3" is not.

    Rounding **down** rather than to the nearest keeps the drawn size at or
    under the target, so the first view never has ellipses running off the
    edge of the extent that produced the factor.

    Returns 1.0 -- never less -- when the ellipses are already large enough to
    see. Shrinking them would understate the uncertainty, which is the failure
    this whole module exists to prevent.

    Args:
        extent: Width and height of the map extent, in the layer's units.
        sizes: Semi-major axes, in the same units. Their maximum sets the factor.
    """
    width, height = extent
    if width <= 0.0 or height <= 0.0:
        raise ValidationError(
            "extent_not_positive",
            received=[width, height],
            expected="a map extent with a positive width and height",
        )
    if not 0.0 < target_fraction <= 1.0:
        raise ValidationError(
            "target_fraction_out_of_range",
            received=target_fraction,
            expected="a fraction of the extent greater than 0 and at most 1",
        )

    largest = max((abs(size) for size in sizes), default=0.0)
    if largest <= 0.0:
        # Every ellipse has collapsed to a point, which happens in a design
        # study with no observations yet. There is nothing to scale.
        return 1.0

    raw = target_fraction * min(width, height) / (2.0 * largest)
    return nice_factor(raw) if raw > 1.0 else 1.0


def nice_factor(value: float) -> float:
    """The largest 1-2-5 x 10^n value not exceeding *value*, at least 1.

    Legends are read, not computed with. The 1-2-5 sequence is the one every
    scale bar and axis tick already uses, so an exaggeration expressed in it
    looks like a scale rather than like a residue of some calculation.
    """
    if value < 1.0:
        return 1.0
    if math.isinf(value):
        raise ValidationError(
            "exaggeration_not_finite",
            received=value,
            expected="a finite factor; an infinite one means the ellipses have no size",
        )
    decade = 10.0 ** math.floor(math.log10(value))
    for step in (5.0, 2.0, 1.0):
        candidate = step * decade
        if candidate <= value:
            return candidate
    return decade


def _check_exaggeration(exaggeration: float) -> None:
    if not math.isfinite(exaggeration) or exaggeration <= 0.0:
        raise ValidationError(
            "exaggeration_not_positive",
            received=exaggeration,
            expected="a positive, finite exaggeration factor. It is required rather "
            "than defaulted because every drawn result must state the factor it "
            "was drawn with (FR-901)",
        )
