# SPDX-License-Identifier: GPL-2.0-or-later
"""Network design simulation and data inspection.

Two capabilities that the archived roadmap conflated under one name
(``specs/archive/README.md`` item 6), and that answer different questions:

* :mod:`~geocomp.core.preanalysis.design` -- **pre-analysis proper** (FR-270).
  What precision would a *planned* network give, before any observation exists?
* :mod:`~geocomp.core.preanalysis.inspection` -- **inspection** (FR-273). What
  is wrong with the data I already have?
"""

from __future__ import annotations

from geocomp.core.preanalysis.design import DesignReport, StationDesign, simulate
from geocomp.core.preanalysis.inspection import Finding, InspectionReport, Severity, inspect

__all__ = [
    "DesignReport",
    "Finding",
    "InspectionReport",
    "Severity",
    "StationDesign",
    "inspect",
    "simulate",
]
