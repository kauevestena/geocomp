# SPDX-License-Identifier: GPL-2.0-or-later
"""Base class for every GeoComp Processing algorithm.

Fixes the conventions of ``specs/16-processing-provider.md`` in one place so
that twenty algorithms behave like one plugin: identity derived from the
registry, translation, Basic/Advanced parameter gating, and the rule that
``processAlgorithm`` orchestrates but contains no geodetic mathematics.

**FR-071 is the invariant that matters here.** A parameter hidden in Basic mode
takes exactly the value it would take as the Advanced default: gating changes
what is *shown*, never what is *computed*. Without that, a Basic-mode result
would be a cheaper approximation a professional could not defend, which would
defeat the "modo comercial" framing the research project gives it.
"""

from __future__ import annotations

from typing import Any

from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterDefinition,
)
from qgis.PyQt.QtCore import QCoreApplication

from geocomp.core.settings_def import MODE_ADVANCED
from geocomp.registry import ALGORITHMS, AlgorithmSpec

__all__ = ["GeoCompAlgorithm"]

_BY_CLASS: dict[str, AlgorithmSpec] = {spec.class_name: spec for spec in ALGORITHMS}


class GeoCompAlgorithm(QgsProcessingAlgorithm):
    """Common behaviour for GeoComp algorithms.

    Subclasses implement :meth:`initAlgorithm` and :meth:`processAlgorithm`, and
    are declared in :mod:`geocomp.registry`; identity, group and menu placement
    come from that declaration rather than being restated here, so the two can
    never disagree.
    """

    #: Translation context. One per algorithm keeps Linguist navigable.
    TR_CONTEXT = "GeoCompAlgorithm"

    @classmethod
    def spec(cls) -> AlgorithmSpec:
        """The registry entry for this class."""
        try:
            return _BY_CLASS[cls.__name__]
        except KeyError:  # pragma: no cover - caught by the parity test first
            raise RuntimeError(
                f"{cls.__name__} is not declared in geocomp.registry.ALGORITHMS"
            ) from None

    # -- identity (specs/16 section 3) -----------------------------------

    def name(self) -> str:
        """Stable, never translated. Saved models and scripts store this."""
        return self.spec().name

    def group(self) -> str:
        return self.tr(_group_label(self.spec().group))

    def groupId(self) -> str:
        return self.spec().group

    def createInstance(self) -> GeoCompAlgorithm:
        return type(self)()

    def tr(self, text: str) -> str:
        return QCoreApplication.translate(self.TR_CONTEXT, text)

    # -- Basic / Advanced gating (FR-070, FR-071) ------------------------

    def is_advanced_mode(self) -> bool:
        """Whether the user is in Advanced mode.

        Read through the settings service so the run, project and global scopes
        all apply (FR-068).
        """
        from geocomp.services.settings_service import settings

        return settings.value("interface.mode") == MODE_ADVANCED

    def addAdvancedParameter(self, parameter: QgsProcessingParameterDefinition) -> None:
        """Add *parameter* flagged as advanced.

        Advanced parameters are collapsed in Basic mode rather than removed, so
        the value used is the parameter's own default in both modes. That is
        what makes FR-071 hold structurally rather than by discipline: there is
        one default, not a Basic one and an Advanced one.
        """
        parameter.setFlags(
            parameter.flags() | QgsProcessingParameterDefinition.Flag.FlagAdvanced
        )
        self.addParameter(parameter)

    # -- help (specs/16 section 8) ---------------------------------------

    def shortHelpString(self) -> str:
        """Every algorithm documents what it does and every parameter with units.

        Subclasses override :meth:`help_body`; this wraps it with the
        requirement reference so a reader can find the specification.
        """
        body = self.help_body().strip()
        spec = self.spec()
        return f"{body}\n\n<p><i>{self.tr('Requirement')}: {spec.requirement}</i></p>"

    def help_body(self) -> str:
        """The algorithm's help text. Subclasses must override."""
        raise NotImplementedError

    def displayName(self) -> str:  # pragma: no cover - trivial, overridden
        raise NotImplementedError

    def initAlgorithm(self, config: dict[str, Any] | None = None) -> None:  # pragma: no cover
        raise NotImplementedError


def _group_label(group_id: str) -> str:
    """Source strings for the Processing group names.

    Written as literals so the translation extractor sees them; the mapping is
    keyed by the stable group ids declared in :mod:`geocomp.registry`.
    """
    return {
        "totalstation": "Total Station",
        "levelling": "Level",
        "gnss": "GNSS",
        "gravimetry": "Gravimetry",
        "integration": "Integration",
        "analysis": "Analysis",
        "monitoring": "Monitoring",
        "project": "Project and data",
        "visualization": "Visualisation and reporting",
    }.get(group_id, group_id)
