# SPDX-License-Identifier: GPL-2.0-or-later
"""GNSS Processing algorithms (FR-600, FR-601, FR-602, FR-604, FR-355, FR-359).

``specs/11-module-gnss.md``. One module per menu leaf, plus the shared plumbing
in :mod:`geocomp.algorithms.gnss.common`. Each is a thin Processing surface over
:mod:`geocomp.core.techniques.gnss` and :mod:`geocomp.engines.rtklib`, so the
mathematics stays testable without QGIS (ADR-0005).
"""
