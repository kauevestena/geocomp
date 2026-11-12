# SPDX-License-Identifier: GPL-2.0-or-later
"""The frame the interactive menu windows are built in (ADR-0010, FR-010).

``specs/15-ui-menu-and-settings.md`` section 7. One module per part of a window:

* :mod:`~geocomp.gui.workbench.window` -- the guided, non-modal frame: job bar,
  steps, strip, the run and its results, the canvas hand-back;
* :mod:`~geocomp.gui.workbench.grid` -- the grid a field book is typed into;
* :mod:`~geocomp.gui.workbench.parameters` -- an options form made from an
  algorithm's own parameters;
* :mod:`~geocomp.gui.workbench.run` and :mod:`~geocomp.gui.workbench.results`
  -- running the algorithms, and showing what they wrote;
* :mod:`~geocomp.gui.workbench.sketch` and :mod:`~geocomp.gui.workbench.layers`
  -- the sketch on the map, picking a point from it, and results as a layer.

**Nothing here computes** -- nor does anything in :mod:`geocomp.gui.windows`.
A window writes what was typed as an algorithm's inputs and runs the
algorithm; ``tests/structural/test_windows_compute_nothing.py`` holds it.

Importing this package registers the wording of what a typed job refuses.
"""

from __future__ import annotations

from geocomp.gui.workbench import messages as _messages  # noqa: F401
