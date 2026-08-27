# SPDX-License-Identifier: GPL-2.0-or-later
"""``geocomp:project_tutorial_dataset`` -- install RD-01 (FR-950, FR-952).

``specs/20-testing-and-validation.md`` section 3.

RD-01 is the reference dataset for the whole total-station slice, and it ships
inside the plugin so that a user has something to run five minutes after
installing GeoComp. This algorithm copies it somewhere writable, because a
plugin directory usually is not, and because a tutorial that starts "first find
your own data" is not a tutorial.

**The dataset is the tutorial for the same reason it is the reference: it has
two real errors in it.** A 1.000 m transcription blunder in one face pair, which
pre-processing blocks, and a global test that correctly fails because the
distances disagree by more than the instrument profile claims. Software catching
two genuine errors in genuine data teaches more than a clean run does, so the
copied ``README.md`` walks through both rather than around them.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from qgis.core import (
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFile,
)

from geocomp.algorithms.base import GeoCompAlgorithm
from geocomp.resources import available_datasets, dataset_dir

__all__ = ["TutorialDatasetAlgorithm"]

DATASET = "DATASET"
DESTINATION = "DESTINATION"
OVERWRITE = "OVERWRITE"
OUTPUT_DIRECTORY = "OUTPUT_DIRECTORY"
FILE_COUNT = "FILE_COUNT"


class TutorialDatasetAlgorithm(GeoCompAlgorithm):
    """Copy a shipped reference dataset to a writable directory."""

    TR_CONTEXT = "TutorialDatasetAlgorithm"

    def displayName(self) -> str:
        return self.tr("Install tutorial dataset")

    def shortDescription(self) -> str:
        return self.tr(
            "Copy a shipped reference dataset and its tutorial to a folder you choose."
        )

    def help_body(self) -> str:
        return self.tr(
            "<p>Copies a reference dataset that ships with GeoComp into a directory of "
            "your choosing, with its tutorial. The plugin's own directory is usually not "
            "writable, and outputs have to go somewhere.</p>"
            "<p><b>RD-01</b> is the author's own total-station triangle: three stations, "
            "six pointings, each observed on both faces. It is the smallest complete "
            "survey there is and it exercises the entire total-station chain, from field "
            "book to adjusted network.</p>"
            "<p><b>It contains two real errors, and that is the point.</b> One face pair "
            "disagrees by exactly 1.000 m in distance &mdash; a transcription blunder, "
            "which pre-processing blocks rather than averages away. And the network's "
            "global test fails, correctly: the distances disagree between the two ends by "
            "far more than the instrument's stated precision allows. A tutorial in which "
            "nothing is wrong teaches you which buttons to press; this one teaches you "
            "what the software is for.</p>"
            "<p>The copied <code>README.md</code> walks through the whole chain and "
            "explains both, along with why a network with no known point and no azimuth "
            "can only be adjusted with inner constraints.</p>"
            "<h3>Parameters</h3>"
            "<p><b>Dataset</b> &mdash; which shipped dataset to install. <b>Destination "
            "folder</b> &mdash; where to put it; a subfolder named after the dataset is "
            "created inside. <b>Overwrite</b> &mdash; replace files already there, which "
            "is off by default so an edited tutorial file is not lost.</p>"
            "<h3>Outputs</h3>"
            "<p><code>OUTPUT_DIRECTORY</code> &mdash; where the files landed. "
            "<code>FILE_COUNT</code> &mdash; how many were copied.</p>"
        )

    def initAlgorithm(self, config: dict[str, Any] | None = None) -> None:
        datasets = available_datasets()
        self.addParameter(
            QgsProcessingParameterEnum(
                DATASET,
                self.tr("Dataset"),
                options=datasets or [self.tr("(none shipped)")],
                defaultValue=0,
            )
        )
        self.addParameter(
            QgsProcessingParameterFile(
                DESTINATION,
                self.tr("Destination folder"),
                behavior=QgsProcessingParameterFile.Behavior.Folder,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterBoolean(
                OVERWRITE, self.tr("Overwrite existing files"), defaultValue=False
            )
        )

    def processAlgorithm(
        self,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> dict[str, Any]:
        datasets = available_datasets()
        if not datasets:
            raise QgsProcessingException(
                self.tr(
                    "No datasets ship with this build. That means the package was built "
                    "without its resources, which is a packaging fault rather than "
                    "something you can correct here."
                )
            )

        name = datasets[self.parameterAsEnum(parameters, DATASET, context)]
        source = dataset_dir(name)
        destination = Path(self.parameterAsFile(parameters, DESTINATION, context))
        if not destination.is_dir():
            raise QgsProcessingException(
                self.tr("The destination folder '%1' does not exist.").replace(
                    "%1", str(destination)
                )
            )

        target = destination / name
        target.mkdir(parents=True, exist_ok=True)
        overwrite = self.parameterAsBoolean(parameters, OVERWRITE, context)

        copied = 0
        skipped: list[str] = []
        for path in sorted(source.iterdir()):
            if not path.is_file():
                continue
            landing = target / path.name
            if landing.exists() and not overwrite:
                skipped.append(path.name)
                continue
            shutil.copyfile(path, landing)
            copied += 1

        if skipped:
            feedback.pushWarning(
                self.tr(
                    "%1 file(s) were already there and were left alone: %2. Turn on "
                    "Overwrite to replace them."
                )
                .replace("%1", str(len(skipped)))
                .replace("%2", ", ".join(skipped))
            )
        feedback.pushInfo(
            self.tr("%1 file(s) copied to %2.")
            .replace("%1", str(copied))
            .replace("%2", str(target))
        )
        feedback.pushInfo(
            self.tr("Start with README.md there: it walks through the whole chain.")
        )

        return {OUTPUT_DIRECTORY: str(target), FILE_COUNT: copied}
