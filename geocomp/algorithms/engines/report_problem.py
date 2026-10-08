# SPDX-License-Identifier: GPL-2.0-or-later
"""``geocomp:project_package_engine_problem`` -- an engine's failure, for its developers (FR-955).

``specs/20`` section 8, ``specs/21`` section 4. A DynAdjust or RTKLIB run that
fails keeps its working folder and names it; this puts that folder in one zip
with a README the engine's developers can read without GeoComp, so the report
a user files is one a maintainer can reproduce. The work is
:func:`geocomp.engines.report.package_problem`; this is its Processing face.
"""

from __future__ import annotations

from typing import Any

from qgis.core import (
    Qgis,
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingOutputString,
    QgsProcessingParameterFile,
    QgsProcessingParameterFileDestination,
)

from geocomp.algorithms.base import GeoCompAlgorithm
from geocomp.core.errors import GeoCompError
from geocomp.core.version import __version__
from geocomp.engines.report import UPSTREAM, package_problem

__all__ = ["PackageEngineProblemAlgorithm"]

FOLDER = "FOLDER"
OUTPUT = "OUTPUT"
ENGINE = "ENGINE"


class PackageEngineProblemAlgorithm(GeoCompAlgorithm):
    """Zips an engine's working folder with a README for the engine's developers."""

    TR_CONTEXT = "PackageEngineProblemAlgorithm"

    def displayName(self) -> str:
        return self.tr("Package an engine problem")

    def shortDescription(self) -> str:
        return self.tr(
            "Put a failed DynAdjust or RTKLIB run's folder in one file for the engine's developers."
        )

    def help_body(self) -> str:
        return self.tr(
            "<p>When DynAdjust or RTKLIB fails, GeoComp keeps the folder it ran in and names "
            "it in the refusal. That folder holds what reproduces the failure: the input GeoComp "
            "wrote, the configuration, each command that ran, how it ended, and everything the "
            "engine printed. This puts all of it in one zip file, with a README in English for "
            "the engine's developers saying which engine and version ran, the commands in order "
            "and how each ended, and where to report it.</p>"
            "<h3>Parameters</h3>"
            "<p><b>Working folder</b> &mdash; the folder the refusal named, or one the run was "
            "asked to keep. <b>Package</b> &mdash; the zip file to write.</p>"
            "<p><b>Look before you send.</b> The files are your survey's data, and the commands "
            "name folders on this computer. Nothing is removed for you: remove what may not be "
            "shared. No password or key is ever in a working folder; downloads go through "
            "QGIS's authentication system.</p>"
        )

    def initAlgorithm(self, config: dict[str, Any] | None = None) -> None:
        self.addParameter(
            QgsProcessingParameterFile(
                FOLDER, self.tr("Working folder"), behavior=QgsProcessingParameterFile.Folder
            )
        )
        self.addParameter(
            QgsProcessingParameterFileDestination(
                OUTPUT, self.tr("Package"), fileFilter=self.tr("Zip archives (*.zip)")
            )
        )
        self.addOutput(QgsProcessingOutputString(ENGINE, self.tr("Engine")))

    def processAlgorithm(
        self,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> dict[str, Any]:
        from geocomp.services.messages import message_for

        folder = self.parameterAsFile(parameters, FOLDER, context)
        destination = self.parameterAsFileOutput(parameters, OUTPUT, context)
        try:
            package = package_problem(
                folder, destination, geocomp=__version__, qgis=Qgis.QGIS_VERSION
            )
        except GeoCompError as error:
            raise QgsProcessingException(self.about_input(FOLDER, message_for(error))) from error
        feedback.pushInfo(
            self.tr("%1 runs and %2 files from %3 are in %4.")
            .replace("%1", str(package.runs))
            .replace("%2", str(package.files))
            .replace("%3", package.engine or self.tr("an engine GeoComp does not recognise"))
            .replace("%4", str(package.path))
        )
        if package.engine in UPSTREAM:
            feedback.pushInfo(
                self.tr("Report it at %1, attaching the package.").replace("%1", UPSTREAM[package.engine])
            )
        feedback.pushWarning(
            self.tr(
                "Look inside before you send it: the files are your survey's data and name folders "
                "on this computer. Remove what may not be shared."
            )
        )
        return {OUTPUT: str(package.path), ENGINE: package.engine}
