# SPDX-License-Identifier: GPL-2.0-or-later
"""Single source of truth for the GeoComp version.

``metadata.txt`` carries the same value; a build-time check asserts they agree
(see ``specs/21-packaging-ci-release-licensing.md`` section 3).
"""

from __future__ import annotations

__all__ = ["VERSION_INFO", "__version__"]

VERSION_INFO = (0, 1, 0)
__version__ = ".".join(str(part) for part in VERSION_INFO)
