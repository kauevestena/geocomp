# SPDX-License-Identifier: GPL-2.0-or-later
"""Map geometry for adjustment results, with no QGIS in it.

The layers themselves are built in :mod:`geocomp.layers`, which needs QGIS.
What can be computed and checked without it -- the vertices of an ellipse, the
tip of a vector, the exaggeration a first view should use -- lives here.
"""

from __future__ import annotations

from geocomp.core.visualization.geometry import (
    DEFAULT_VERTEX_COUNT,
    DrawnEllipse,
    default_exaggeration,
    displacement_arrow,
    ellipse_ring,
    nice_factor,
    scale_reference_ring,
)

__all__ = [
    "DEFAULT_VERTEX_COUNT",
    "DrawnEllipse",
    "default_exaggeration",
    "displacement_arrow",
    "ellipse_ring",
    "nice_factor",
    "scale_reference_ring",
]
