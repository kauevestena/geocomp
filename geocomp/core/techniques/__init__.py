# SPDX-License-Identifier: GPL-2.0-or-later
"""Technique modules: the instrument-level mathematics of each survey method.

``specs/03-architecture.md``. One package per technique, each built on
:mod:`geocomp.core.uncertainty`, :mod:`geocomp.core.adjustment` and
:mod:`geocomp.core.statistics`, and none of them importing QGIS.

**Every public function here returns an uncertainty-bearing type** (FR-200),
which ``tests/structural/test_no_bare_geodetic_floats.py`` enforces rather than
trusts.
"""
