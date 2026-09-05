# SPDX-License-Identifier: GPL-2.0-or-later
"""Application layer: use-case orchestration.

Sits between the presentation layer (``geocomp.gui``, ``geocomp.algorithms``)
and the QGIS-free core. This is the only layer permitted to know about QGIS
threading, settings storage and logging, and it is where a synchronous core
operation is wrapped into a ``QgsTask`` (``specs/03-architecture.md`` section 1).
"""

from __future__ import annotations
