# SPDX-License-Identifier: GPL-2.0-or-later
"""``geocomp:project_install_engine`` -- download, verify and install an engine (FR-301, ADR-0003).

The proposal's "poucos cliques": install QGIS, install the plugin, and the
engines arrive without a command line. Until P12c-6 the manager that does this
(:mod:`geocomp.engines.manager`) existed, had been run by hand on Linux, and was
called by nothing in the plugin. This algorithm is what calls it, and the
*Paths and engines* page of Global Settings opens it.

What it installs is the release **pinned in GeoComp** for this machine's
platform: the archive's SHA-256 is committed in this repository and checked
before anything is extracted, and an archive that does not match is deleted.
It lands in the QGIS profile, is recorded with its version, and is then run to
show that it works here -- an installation that verified and will not start is
reported as a failure, not as success.

**The user states that they understand the licence.** DynAdjust is a separate
program, written by Geoscience Australia and licensed by them (Apache-2.0); it
is downloaded from their release page and GeoComp does not distribute it
(ADR-0003, ``specs/21`` section 7). A required tick box says that the person
installing it has been told so, and an install without it is refused, naming the
box, before anything is downloaded.

**RTKLIB is not offered here.** GeoComp carries its own ``rnx2rtkp`` for Linux
and Windows on x86-64 and for macOS (ADR-0009); on any other system its path is
set in Global Settings.
"""

from __future__ import annotations

from typing import Any

from qgis.core import (
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingOutputFolder,
    QgsProcessingOutputString,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterEnum,
)

from geocomp.algorithms.base import GeoCompAlgorithm
from geocomp.engines.dynadjust.engine import DynAdjustEngine
from geocomp.engines.manager import current_platform, releases_for

__all__ = ["InstallEngineAlgorithm"]

ENGINE = "ENGINE"
ACKNOWLEDGE_LICENCE = "ACKNOWLEDGE_LICENCE"
OUTPUT_DIRECTORY = "OUTPUT_DIRECTORY"
OUTPUT_VERSION = "OUTPUT_VERSION"

#: The engines the manager has a pinned release of, in the order offered.
ENGINES = ("dynadjust",)

#: Where DynAdjust's licence is published, named in the help and in the refusal.
DYNADJUST_REPOSITORY = "https://github.com/GeoscienceAustralia/DynAdjust"


class InstallEngineAlgorithm(GeoCompAlgorithm):
    """Installs the pinned release of an engine into the QGIS profile."""

    TR_CONTEXT = "InstallEngineAlgorithm"

    def displayName(self) -> str:
        return self.tr("Install an engine")

    def shortDescription(self) -> str:
        return self.tr("Download, verify and install DynAdjust for this computer.")

    def help_body(self) -> str:
        return self.tr(
            "<p>Downloads the DynAdjust release GeoComp was tested with, for this computer's "
            "operating system, from Geoscience Australia's release page. Before anything is "
            "extracted the download is checked against the SHA-256 digest recorded in GeoComp; "
            "a download that does not match is deleted and nothing is installed.</p>"
            "<p>The programs go into GeoComp's folder in the QGIS profile, so no administrator "
            "rights are needed and removing the profile removes them. The version is recorded, "
            "and the installed program is run once to show that it works on this computer.</p>"
            "<p>The download uses QGIS's network settings, including its proxy.</p>"
            "<p><b>Licence.</b> DynAdjust is a separate program by Geoscience Australia, under "
            "the Apache-2.0 licence (see its repository, %1). GeoComp does not distribute it: "
            "it is downloaded from the authors' release page. Tick the box to say you "
            "understand this; without it nothing is downloaded.</p>"
            "<p>A DynAdjust directory set in Global Settings, under Paths and engines, is still "
            "used in preference to this installation; clear it to use this one.</p>"
            "<p><b>RTKLIB</b> is not installed here. GeoComp carries its own "
            "<code>rnx2rtkp</code> for Linux and Windows on x86-64 and for macOS; on any "
            "other system, give the path to one in Global Settings.</p>"
        ).replace("%1", DYNADJUST_REPOSITORY)

    def initAlgorithm(self, config: dict[str, Any] | None = None) -> None:
        self.addParameter(
            QgsProcessingParameterEnum(
                ENGINE,
                self.tr("Engine"),
                options=[self.tr("DynAdjust")],
                defaultValue=0,
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                ACKNOWLEDGE_LICENCE,
                self.tr("I understand that DynAdjust is a separate program under its own licence"),
                defaultValue=False,
            )
        )
        self.addOutput(QgsProcessingOutputFolder(OUTPUT_DIRECTORY, self.tr("Installed in")))
        self.addOutput(QgsProcessingOutputString(OUTPUT_VERSION, self.tr("Version installed")))

    def processAlgorithm(
        self,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> dict[str, Any]:
        from geocomp.services.engines import configured_path, install_engine

        engine = ENGINES[self.parameterAsEnum(parameters, ENGINE, context)]
        if not self.parameterAsBoolean(parameters, ACKNOWLEDGE_LICENCE, context):
            raise QgsProcessingException(
                self.tr(
                    "Tick \u201c%1\u201d to install DynAdjust. It is a separate program by "
                    "Geoscience Australia, under the Apache-2.0 licence (%2), downloaded from "
                    "their release page; GeoComp does not distribute it. Nothing was downloaded."
                )
                .replace("%1", self.parameterDefinition(ACKNOWLEDGE_LICENCE).description())
                .replace("%2", DYNADJUST_REPOSITORY)
            )
        feedback.pushInfo(
            self.tr(
                "You confirmed that you understand DynAdjust is a separate program under its "
                "own licence, Apache-2.0 (%1)."
            ).replace("%1", DYNADJUST_REPOSITORY)
        )
        platform = current_platform()
        releases = releases_for(engine, platform)
        if releases:
            feedback.pushInfo(
                self.tr("Downloading DynAdjust %1 for %2 from %3")
                .replace("%1", releases[0].version)
                .replace("%2", platform)
                .replace("%3", releases[0].url)
            )
        installation = install_engine(engine, feedback=feedback)
        if feedback.isCanceled():
            return {}
        feedback.setProgress(80)
        feedback.pushInfo(
            self.tr("Verified against the SHA-256 recorded in GeoComp (%1) and installed in %2.")
            .replace("%1", installation.sha256)
            .replace("%2", str(installation.directory))
        )

        # The installation itself, not whatever the algorithms would find first:
        # a configured directory or a program on the path would answer for it.
        found = DynAdjustEngine(extra_directories=(installation.directory,)).detect()
        if found is None or installation.directory not in found.path.parents:
            raise QgsProcessingException(
                self.tr(
                    "DynAdjust %1 was downloaded, verified and installed in %2, but it does "
                    "not run on this computer. Install DynAdjust another way and give its "
                    "directory in Global Settings, under Paths and engines."
                )
                .replace("%1", installation.version)
                .replace("%2", str(installation.directory))
            )
        feedback.pushInfo(
            self.tr("DynAdjust %1 runs: %2.").replace("%1", found.version).replace("%2", str(found.path))
        )
        if found.version != installation.version:
            feedback.pushWarning(
                self.tr("The program reports version %1 although release %2 was installed.")
                .replace("%1", found.version)
                .replace("%2", installation.version)
            )
        if configured := configured_path(engine):
            feedback.pushWarning(
                self.tr(
                    "A DynAdjust directory is set in Global Settings (%1), and the algorithms "
                    "will keep using it. Clear it to use this installation."
                ).replace("%1", configured)
            )
        feedback.setProgress(100)
        return {OUTPUT_DIRECTORY: str(installation.directory), OUTPUT_VERSION: installation.version}
