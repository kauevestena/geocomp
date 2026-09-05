# SPDX-License-Identifier: GPL-2.0-or-later
"""The GeoComp Processing provider (FR-030).

Algorithms come from :mod:`geocomp.registry`, which the menu reads too, so the
toolbox and the menu cannot drift apart (ADR-0005).
"""

from __future__ import annotations

import importlib

from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtGui import QIcon

from geocomp.core.version import __version__
from geocomp.registry import ALGORITHMS, PROVIDER_ID, AlgorithmSpec
from geocomp.resources import icon_path
from geocomp.services.logging import log

__all__ = ["GeoCompProvider"]


class GeoCompProvider(QgsProcessingProvider):
    """Registers GeoComp's algorithms with the QGIS Processing framework."""

    def id(self) -> str:
        """Stable provider id. Saved models and scripts store it (FR-032)."""
        return PROVIDER_ID

    def name(self) -> str:
        return self.tr("GeoComp")

    def longName(self) -> str:
        return f"{self.name()} {__version__}"

    def icon(self) -> QIcon:
        return QIcon(icon_path("geocomp.svg"))

    def versionInfo(self) -> str:
        return __version__

    def tr(self, text: str) -> str:
        return QCoreApplication.translate("GeoCompProvider", text)

    def loadAlgorithms(self) -> None:
        """Instantiate and add every registered algorithm.

        One algorithm failing to import must not take the whole provider down:
        the rest stay available and the failure is logged with its cause. A
        provider that vanishes because of one bad module is far harder to
        diagnose than a provider missing one entry.
        """
        for spec in ALGORITHMS:
            algorithm = self._instantiate(spec)
            if algorithm is not None:
                self.addAlgorithm(algorithm)

    def _instantiate(self, spec: AlgorithmSpec):
        try:
            module = importlib.import_module(spec.module)
            return getattr(module, spec.class_name)()
        except Exception as exc:  # noqa: BLE001 - deliberately broad, see docstring
            log.critical(
                "could not load algorithm",
                algorithm=spec.id,
                module=spec.module,
                cls=spec.class_name,
                error=f"{type(exc).__name__}: {exc}",
            )
            return None
