# SPDX-License-Identifier: GPL-2.0-or-later
"""Styled QGIS layers built from adjustment results (FR-900, FR-905).

Separate from :mod:`geocomp.algorithms` because a layer is not an algorithm
output: the same builders serve the Processing algorithms, the future
pre-analysis dialog and anything else that has a :class:`Solution` to show.

The geometry these build is computed in :mod:`geocomp.core.visualization`,
which has no QGIS in it and can therefore be checked against closed-form
values without one.
"""

from __future__ import annotations

from geocomp.layers.builders import (
    correction_layer,
    ellipse_layer,
    exaggeration_label,
    observation_layer,
    residual_layer,
    station_layer,
)
from geocomp.layers.styles import STYLE_DIR, apply_style, style_path

__all__ = [
    "STYLE_DIR",
    "apply_style",
    "correction_layer",
    "ellipse_layer",
    "exaggeration_label",
    "observation_layer",
    "residual_layer",
    "station_layer",
    "style_path",
]
