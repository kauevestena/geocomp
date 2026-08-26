# SPDX-License-Identifier: GPL-2.0-or-later
"""Pure-Python geodetic core.

Nothing in this package may import ``qgis`` or ``PyQt``. The rule is specified
in ``specs/03-architecture.md`` section 1 (NFR-002) and enforced by
``tests/structural/test_no_qgis_in_core.py``.

Two consequences worth stating where they will be read:

* The core raises exceptions carrying structured, machine-readable context; it
  never composes a user-facing sentence. Rendering a translated message is the
  presentation layer's job (``specs/18-i18n-and-profiles.md`` section 2).
* The core is synchronous and knows nothing about ``QgsTask``. Long operations
  accept a :class:`~geocomp.core.cancellation.CancellationToken` and a progress
  callback instead (``specs/03-architecture.md`` section 3.5).
"""

from __future__ import annotations

from geocomp.core.version import __version__

__all__ = ["__version__"]
