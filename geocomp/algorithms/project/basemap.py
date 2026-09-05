# SPDX-License-Identifier: GPL-2.0-or-later
"""``geocomp:project_basemap`` -- add a configured base map (FR-167).

``specs/17-persistence-and-interoperability.md`` section 5.6.

Cartographic context for a network is not decoration. A pre-analysis design is
judged against what the ground actually looks like -- whether a planned station
sits on a road or in a river -- and a set of adjusted coordinates is checked
first by whether the marks land where the surveyor remembers putting them.

**No imagery is bundled and no service is hard-coded.** The catalogue is data:
two openly licensed defaults, replaceable wholesale by a file named in
``basemaps.catalogue``. Nothing is downloaded here; QGIS fetches tiles when it
draws them, and the algorithm neither waits for that nor reports on it.

**What is already in the project is honoured.** A service already present is
reused rather than added a second time, and the base map goes to the bottom of
the layer tree -- above the results it hides what was just computed.
"""

from __future__ import annotations

from typing import Any

from qgis.core import (
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterString,
    QgsProject,
)

from geocomp.algorithms.base import GeoCompAlgorithm
from geocomp.core.errors import GeoCompError

__all__ = ["ProjectBaseMapAlgorithm"]

SERVICE = "SERVICE"
REUSE = "REUSE"

#: Result keys: which service, what happened, and the layer it became.
OUTCOME = "OUTCOME"
LAYER = "LAYER"


class ProjectBaseMapAlgorithm(GeoCompAlgorithm):
    """Adds one configured base map service to the current project."""

    TR_CONTEXT = "ProjectBaseMapAlgorithm"

    def displayName(self) -> str:
        return self.tr("Add base map")

    def shortDescription(self) -> str:
        return self.tr("Add a configured base map service to the project, for context.")

    def help_body(self) -> str:
        return self.tr(
            "<p>Adds one of the configured base map services to the current project, at "
            "the bottom of the layer tree so it does not hide the results.</p>"
            "<p>The services come from the catalogue file named in Global Settings, or "
            "from GeoComp's two openly licensed defaults when none is configured. Nothing "
            "is bundled and nothing is hard-coded: replace the catalogue and the list "
            "changes entirely.</p>"
            "<p>A service already present in the project is reused rather than added "
            "again &mdash; matched on its URL, since a layer's name is yours to change.</p>"
            "<p>Services requiring authentication reference an entry in the QGIS "
            "authentication database. GeoComp never stores a credential itself, and "
            "refuses a service URL with one embedded in it.</p>"
            "<h3>Parameters</h3>"
            "<p><b>Service</b> &mdash; the id of a service in the catalogue. Leave empty "
            "to use the one configured as the default; if none is configured, nothing is "
            "added, rather than a layer you did not ask for.</p>"
        )

    def initAlgorithm(self, config: dict[str, Any] | None = None) -> None:
        self.addParameter(
            QgsProcessingParameterString(
                SERVICE,
                self.tr("Service id (empty for the configured default)"),
                optional=True,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterBoolean(
                REUSE,
                self.tr("Reuse a base map already in the project"),
                defaultValue=True,
            )
        )

    def processAlgorithm(
        self,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> dict[str, Any]:
        from geocomp.core.basemaps import load_catalogue
        from geocomp.layers.basemaps import add_base_map
        from geocomp.services.settings_service import settings

        requested = (self.parameterAsString(parameters, SERVICE, context) or "").strip()
        reuse = self.parameterAsBool(parameters, REUSE, context)

        try:
            catalogue = load_catalogue(settings.value("basemaps.catalogue"))
            service = (
                catalogue.service(requested)
                if requested
                else catalogue.default(settings.value("basemaps.default_service"))
            )
        except GeoCompError as error:
            raise QgsProcessingException(str(error)) from error

        if service is None:
            feedback.pushWarning(
                self.tr(
                    "No base map is configured as the default, so none was added. "
                    "Name a service, or set one in Global Settings; the available ids "
                    "are: "
                )
                + ", ".join(entry.id for entry in catalogue.services)
            )
            return {SERVICE: "", OUTCOME: "none"}

        feedback.setProgress(40)
        layer, outcome = add_base_map(service, QgsProject.instance(), reuse_existing=reuse)

        if outcome == "invalid":
            raise QgsProcessingException(
                self.tr("The base map service could not be loaded: ") + service.url
            )

        feedback.pushInfo(f"{service.name} ({outcome})")
        # The attribution is on the layer's metadata, but a user reading the log
        # after a run should see it too: a base map used without its attribution
        # is a licence breach, and the log is where they are already looking.
        feedback.pushInfo(self.tr("Attribution: ") + service.attribution)
        feedback.setProgress(100)
        return {
            SERVICE: service.id,
            OUTCOME: outcome,
            LAYER: layer.id() if layer is not None else "",
        }
