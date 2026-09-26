# SPDX-License-Identifier: GPL-2.0-or-later
"""Gravimetry Processing algorithms (FR-700 to FR-703).

``specs/12-module-gravimetry.md`` section 2: two menu entries, in the order of
the work. *Pre-processing* reads a gravimeter's file, applies the scale, the
tide and the reduction to the mark, and says what each session's drift looks
like; *Gravimetric network adjustment* estimates the drift with the station
values and adjusts. Both are thin surfaces over
:mod:`geocomp.core.techniques.gravimetry`, so the mathematics stays testable
without QGIS (ADR-0005).
"""

from geocomp.algorithms.gravimetry import messages as _messages  # noqa: F401
