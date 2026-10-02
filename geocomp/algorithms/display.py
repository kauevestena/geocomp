# SPDX-License-Identifier: GPL-2.0-or-later
"""The configured display format, for the reports (FR-067; phase P12a).

:class:`~geocomp.core.display_format.DisplayFormat` is the formatting, QGIS-free
and tested without QGIS; this resolves it from the four interface settings,
through the run, project and global scopes, when a report is written.
"""

from __future__ import annotations

from geocomp.algorithms.defaults import configured
from geocomp.core.display_format import DisplayFormat

__all__ = ["display_format"]


def display_format() -> DisplayFormat:
    """The display format the interface settings describe, now."""
    return DisplayFormat(
        angle_format=str(configured("interface.angle_format")),
        angle_decimals=int(configured("interface.angle_decimals")),
        coordinate_decimals=int(configured("interface.coordinate_decimals")),
        distance_unit=str(configured("interface.distance_unit")),
    )
