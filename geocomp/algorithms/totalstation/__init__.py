# SPDX-License-Identifier: GPL-2.0-or-later
"""Total station algorithms: the first end-to-end vertical slice.

``specs/09-module-total-station.md`` section 1. One algorithm per menu item, so
the whole chain -- import, pre-process, compute, adjust -- can be assembled in
the graphical modeller with no scripting (FR-005, FR-033).

Each of these orchestrates and renders; none computes anything geodetic
(``specs/16`` section 7). The mathematics is in
:mod:`geocomp.core.techniques.total_station`, which is what lets it be tested
without a QGIS runtime.
"""

from __future__ import annotations

from geocomp.algorithms.analysis import messages as _messages  # noqa: F401
