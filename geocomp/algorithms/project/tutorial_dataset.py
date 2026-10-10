# SPDX-License-Identifier: GPL-2.0-or-later
"""``geocomp:project_tutorial_dataset`` -- install a shipped dataset (FR-950, FR-952).

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

Two more ship beside it: ``rtklib-sample``, RTKLIB's own baseline for a GNSS
run, and since P13-2 ``rd04-loop``, the levelling tutorial -- a loop with one
spoiled reading, which closes badly, adjusts quietly wrong, and is found only
by the benchmarks; and since P13-3 ``rd08-dam``, the monitoring tutorial -- two
epochs of a structure, one of whose targets moved; and since P13-4
``rd07-usgs``, the gravimetry tutorial -- two of USGS's synthetic surveys, the
first tutorial whose answer someone else published; and since P13-5
``combined-curitiba``, the integration tutorial. The dataset is an enum whose index a saved model keeps, so
the order is :data:`~geocomp.resources.DATASET_ORDER`'s, to which a new
dataset is appended.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from qgis.core import (
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingOutputFile,
    QgsProcessingOutputFolder,
    QgsProcessingOutputNumber,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFile,
)

from geocomp.algorithms.base import GeoCompAlgorithm
from geocomp.algorithms.project.print_layout import _no_threading
from geocomp.algorithms.project.worked_examples import WORKED, write_project
from geocomp.resources import available_datasets, dataset_dir

__all__ = ["TutorialDatasetAlgorithm"]

DATASET = "DATASET"
DESTINATION = "DESTINATION"
OVERWRITE = "OVERWRITE"
OUTPUT_DIRECTORY = "OUTPUT_DIRECTORY"
FILE_COUNT = "FILE_COUNT"
OUTPUT_PROJECT = "OUTPUT_PROJECT"


class TutorialDatasetAlgorithm(GeoCompAlgorithm):
    """Copy a shipped reference dataset to a writable directory."""

    TR_CONTEXT = "TutorialDatasetAlgorithm"

    def displayName(self) -> str:
        return self.tr("Install tutorial dataset")

    def flags(self):
        # It writes a QGIS project, which is built on the main thread.
        return super().flags() | _no_threading()

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
            "<p><b>rd04-loop</b> is a levelling loop of three lines with one foresight "
            "written down 12 mm wrong: the loop's closure detects the error, an adjustment "
            "with one degree of freedom spreads it, and the known heights locate it. "
            "<b>rd08-dam</b> is two epochs of a monitored structure, one of whose targets "
            "moved between them: comparing the epochs finds it, and holding it as a stable "
            "pillar is refused. "
            "<b>rd07-usgs</b> is two of USGS's synthetic gravity surveys, whose truth USGS "
            "published: the first comes back within a few microgal of it, and the second, "
            "from a meter that reads 3 % high, passes every test until a second known value "
            "exposes its scale. "
            "<b>combined-curitiba</b> is GNSS and a total station adjusted together, the "
            "total station having measured three times worse than it states: the "
            "breakdown by technique points at it, and variance components weigh it by "
            "what it measured. "
            "<b>ggao-triangle</b> is three GNSS receivers at NASA's Goddard observatory, over "
            "two hours of one day: the triangle's baselines close to a fraction of a millimetre "
            "in one hour and miss by several in the other, and the loop closure says which hour "
            "to trust. "
            "<b>rtklib-sample</b> is RTKLIB's own base-and-rover pair, for a GNSS run. Each "
            "has its own <code>README.md</code>, in English, Portuguese and Spanish.</p>"
            "<p><b>A worked example to open and run.</b> Beside the files it writes a QGIS "
            "project named after the dataset, holding the walkthrough as one model. Open the "
            "project, and the model is in the Processing toolbox under <i>Project models</i>: "
            "its inputs are the installed files, its files go to a <code>results</code> folder, "
            "and its map layers are loaded when it finishes. A step the README leaves for you "
            "to try, such as one GeoComp refuses, is not in it.</p>"
        ) + self.tr(
            "<p><b>Its map and its print layout.</b> Where the inputs place the stations, the "
            "project opens on them: a layer written beside it, labelled, in the CRS the "
            "walkthrough works in. It also holds a print layout named after the dataset, whose "
            "map and legend follow the project: it shows the stations when the project opens, "
            "and the results beside them once the model has run. A levelling loop places no "
            "station, so its project has neither.</p>"
        ) + self.tr(
            "<h3>Parameters</h3>"
            "<p><b>Dataset</b> &mdash; which shipped dataset to install. <b>Destination "
            "folder</b> &mdash; where to put it; a subfolder named after the dataset is "
            "created inside. <b>Overwrite</b> &mdash; replace files already there, which "
            "is off by default so an edited tutorial file is not lost.</p>"
            "<h3>Outputs</h3>"
            "<p><code>OUTPUT_DIRECTORY</code> &mdash; where the files landed. "
            "<code>FILE_COUNT</code> &mdash; how many were copied. <code>OUTPUT_PROJECT</code> "
            "&mdash; the project, left alone like the files when it is already there and "
            "<b>Overwrite</b> is off.</p>"
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
        self.addOutput(QgsProcessingOutputFolder(OUTPUT_DIRECTORY, self.tr("Installed in")))
        self.addOutput(QgsProcessingOutputNumber(FILE_COUNT, self.tr("Files copied")))
        self.addOutput(QgsProcessingOutputFile(OUTPUT_PROJECT, self.tr("Worked example project")))

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
                    "something you can correct here. Install the plugin again from its "
                    "release archive, and report it if the datasets are still missing."
                )
            )

        name = datasets[self.parameterAsEnum(parameters, DATASET, context)]
        source = dataset_dir(name)
        destination = Path(self.parameterAsFile(parameters, DESTINATION, context))
        if not destination.is_dir():
            raise QgsProcessingException(
                self.tr("The destination folder '%1' does not exist. Create it, or choose "
                        "another.").replace(
                    "%1", str(destination)
                )
            )

        target = destination / name
        target.mkdir(parents=True, exist_ok=True)
        overwrite = self.parameterAsBoolean(parameters, OVERWRITE, context)

        copied = 0
        skipped: list[str] = []
        # Folders too, since P13-17: the GNSS tutorial keeps each hour in its
        # own, because one folder of one station's two hours is refused.
        for path in sorted(source.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(source)
            landing = target / relative
            if landing.exists() and not overwrite:
                skipped.append(relative.as_posix())
                continue
            landing.parent.mkdir(parents=True, exist_ok=True)
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

        project = target / f"{name}.qgz"
        if name in WORKED and (overwrite or not project.exists()):
            write_project(name, target, project)
            feedback.pushInfo(
                self.tr(
                    "%1 is a QGIS project holding the walkthrough as one model. Open it, and "
                    "the model is in the Processing toolbox under Project models, its inputs "
                    "already the installed files."
                ).replace("%1", str(project))
            )

        return {
            OUTPUT_DIRECTORY: str(target),
            FILE_COUNT: copied,
            OUTPUT_PROJECT: str(project) if project.exists() else "",
        }
