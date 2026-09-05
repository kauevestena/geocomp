# SPDX-License-Identifier: GPL-2.0-or-later
"""Tier-3 tests: the parts that need a real QGIS runtime.

``specs/20-testing-and-validation.md`` section 1. Everything here skips when
QGIS is not importable, so a contributor without it still gets tiers 1 and 2 in
full; CI's ``qgis integration`` job is where these actually run.
"""
