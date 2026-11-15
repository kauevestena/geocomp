# SPDX-License-Identifier: GPL-2.0-or-later
"""Jobs: what a user typed into an interactive window, kept in a file (FR-012, FR-013).

``specs/15-ui-menu-and-settings.md`` section 7 and ADR-0010. The GeoComp menu
opens interactive windows in which observations are typed; the Processing
toolbox keeps every algorithm as the route for files. This package is the part
of the first that has no window in it:

* how a typed angle or number is read (:mod:`~geocomp.jobs.angles`,
  :mod:`~geocomp.jobs.tables`);
* the job file a field book is saved in (:mod:`~geocomp.jobs.document`);
* each technique's field book, and how it becomes the very inputs that
  technique's algorithms read (:mod:`~geocomp.jobs.total_station`);
* the chain of algorithms a window runs (:mod:`~geocomp.jobs.chains`).

**Nothing here computes a survey.** A job turns typed text into an algorithm's
inputs and reads the algorithm's outputs back; the reductions, the closures and
the adjustments are the algorithms', which is what makes the menu and the
toolbox give the same answer by construction (FR-011). The package may read
:mod:`geocomp.core`'s models and units and :mod:`geocomp.io`'s readers, and
nothing of the mathematics; ``tests/structural/test_windows_compute_nothing.py``
holds it to that.

**No QGIS and no Qt**, for the reason ``core/`` has none: what a typed row means
is tested in a plain interpreter, in milliseconds
(``tests/structural/test_no_qgis_in_core.py``).
"""

from __future__ import annotations

from geocomp.jobs.angles import AngleTyping, format_typed_angle, parse_typed_angle
from geocomp.jobs.chains import Chain, ChainStep, InputFile, Ref, ResolvedStep, fingerprint, resolve
from geocomp.jobs.document import JOB_KIND, JOB_SUFFIX, JOB_VERSION, Job
from geocomp.jobs.tables import (
    CellKind,
    CellProblem,
    Column,
    TypedTable,
    format_number,
    parse_integer,
    parse_number,
)

__all__ = [
    "JOB_KIND",
    "JOB_SUFFIX",
    "JOB_VERSION",
    "AngleTyping",
    "CellKind",
    "CellProblem",
    "Chain",
    "ChainStep",
    "Column",
    "InputFile",
    "Job",
    "Ref",
    "ResolvedStep",
    "TypedTable",
    "fingerprint",
    "format_number",
    "format_typed_angle",
    "parse_integer",
    "parse_number",
    "parse_typed_angle",
    "resolve",
]
