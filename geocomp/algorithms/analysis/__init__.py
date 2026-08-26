# SPDX-License-Identifier: GPL-2.0-or-later
"""Analysis algorithms: inspection, pre-analysis and adjustment.

The Processing face of :mod:`geocomp.core.adjustment`,
:mod:`geocomp.core.statistics` and :mod:`geocomp.core.preanalysis`. Every module
here orchestrates and renders; none of them computes anything geodetic
(``specs/16`` section 7), which is what keeps the mathematics testable without a
QGIS runtime.
"""

from __future__ import annotations

# Registering phase P2's error wording on import, so that any algorithm in this
# package can raise a core error and have it reach the user as a sentence.
from geocomp.algorithms.analysis import messages as _messages  # noqa: F401
