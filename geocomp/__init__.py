# SPDX-License-Identifier: GPL-2.0-or-later
"""GeoComp -- a QGIS framework for geodetic network processing and adjustment.

Copyright (C) 2026 Kauê de Moraes Vestena and the GeoComp contributors.

This program is free software; you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation; either version 2 of the License, or (at your option) any later
version. See the LICENSE file at the repository root.
"""

from __future__ import annotations

from geocomp.core.version import __version__

__all__ = ["__version__", "classFactory"]


def classFactory(iface):
    """Entry point QGIS calls to instantiate the plugin.

    Imported lazily so that merely importing this package -- which the build
    script and the tests do -- does not require a QGIS runtime.
    """
    from geocomp.plugin import GeoCompPlugin

    return GeoCompPlugin(iface)
