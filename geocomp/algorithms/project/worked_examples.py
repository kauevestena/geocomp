# SPDX-License-Identifier: GPL-2.0-or-later
"""Each tutorial's walkthrough as one Processing model, in a QGIS project beside it (FR-952; P13-12).

``specs/20-testing-and-validation.md`` section 8 asks for *worked examples
shipped as QGIS projects a student can open and run*. *Install tutorial
dataset* writes one beside the files it installs: ``<dataset>.qgz``, holding
the walkthrough's chain as a model embedded in the project. Opened in QGIS, the
model is in the toolbox under *Project models*. Its inputs are already the
installed files, its files go to a ``results`` folder beside them, and its map
layers are loaded when it finishes.

The project is written at install time, not shipped: a model's inputs are
absolute paths, and only the installer knows where the files went.

A chain is declared, not derived from the README. Each walkthrough's steps are
held to its README by the tier-3 tests, and the model's children to the same
steps by ``tests/qgis/test_worked_examples.py``, so the two cannot drift apart
without a test saying which.

QGIS embeds a model in a project as the Processing plugin's project provider
does: a ``projectModels`` element under ``qgis``, holding the model's variant
(``processing/modeler/ProjectProvider.py``). :func:`write_project` writes that
element, and :func:`read_models` reads it back the same way.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from qgis.core import (
    QgsApplication,
    QgsProcessingModelAlgorithm,
    QgsProcessingModelChildAlgorithm,
    QgsProcessingModelChildParameterSource,
    QgsProcessingModelOutput,
    QgsProcessingModelParameter,
    QgsProcessingParameterFile,
    QgsProcessingParameterFileDestination,
    QgsProject,
    QgsXmlUtils,
)
from qgis.PyQt.QtCore import QCoreApplication

from geocomp.algorithms.analysis.common import DATUM_ORDER, FRAME_ORDER
from geocomp.algorithms.gravimetry.network_adjust import DRIFT_MODES
from geocomp.core.adjustment import Frame
from geocomp.core.models import DatumDefinition

__all__ = ["WORKED", "Step", "build_model", "read_models", "write_project"]

_CONTEXT = "WorkedExamples"

#: The element QGIS's project provider keeps a project's models in.
PROJECT_MODELS = "projectModels"


def _tr(text: str) -> str:
    return QCoreApplication.translate(_CONTEXT, text)


@dataclass(frozen=True)
class Step:
    """One step of a walkthrough, as one child of its model.

    Attributes:
        id: The child's id, which the model's outputs are named by.
        algorithm: The GeoComp algorithm it runs.
        files: Inputs read from an installed file, by name; ``"."`` is the
            dataset's folder itself. Each becomes an input of the model, whose
            default is that file.
        wires: Inputs taken from an earlier step's output, as ``(step, output)``.
        values: Every other input the walkthrough fills.
        results: Outputs the model exposes. A file is written into ``results``;
            a layer is loaded when the model finishes.
    """

    id: str
    algorithm: str
    files: dict[str, str] = field(default_factory=dict)
    wires: dict[str, tuple[str, str]] = field(default_factory=dict)
    values: dict[str, Any] = field(default_factory=dict)
    results: tuple[str, ...] = ()


_PLANE = FRAME_ORDER.index(Frame.PLANE_2D)
_INNER = DATUM_ORDER.index(DatumDefinition.INNER_CONSTRAINT)
_MINIMUM = DATUM_ORDER.index(DatumDefinition.MINIMUM_CONSTRAINT)
_ADJUSTMENT_LAYERS = (
    "OUTPUT_STATION_LAYER",
    "OUTPUT_ELLIPSE_LAYER",
    "OUTPUT_RESIDUAL_LAYER",
    "OUTPUT_OBSERVATION_LAYER",
    "OUTPUT_CORRECTION_LAYER",
)


def _levelling() -> tuple[Step, ...]:
    return (
        Step(
            "import",
            "geocomp:levelling_import",
            files={"BOOK": "loop.csv", "MAPPING": "mapping.json", "PROFILES": "profiles.json"},
        ),
        Step(
            "reduce",
            "geocomp:levelling_equal_sights",
            files={"PROFILES": "profiles.json"},
            wires={"SETUPS": ("import", "OUTPUT_SETUPS")},
        ),
        Step(
            "closures",
            "geocomp:levelling_closures",
            wires={"REDUCTIONS": ("reduce", "OUTPUT_REDUCTIONS")},
            # 0 is the loop: "Loop" comes first in the mode's options.
            values={"MODE": 0, "TOLERANCE_COEFFICIENT": 0.008},
            results=("OUTPUT_CLOSURES", "OUTPUT_HTML"),
        ),
        Step(
            "network",
            "geocomp:levelling_network",
            wires={"REDUCTIONS": ("reduce", "OUTPUT_REDUCTIONS")},
            values={
                "BENCHMARKS": "BM1=100.000",
                "TOLERANCE_COEFFICIENT": 0.008,
                "SIGMA_PER_KM": 0.0007,
            },
            results=("OUTPUT_SOLUTION", "OUTPUT_HTML"),
        ),
    )


def _monitoring() -> tuple[Step, ...]:
    pillars = "R1,R2,R3,R4"
    adjust = {"FRAME": _PLANE, "DATUM": _MINIMUM, "DATUM_STATIONS": pillars}
    return (
        Step(
            "epoch2025",
            "geocomp:analysis_network_adjust",
            files={"NETWORK": "epoch-2025.json"},
            values=adjust,
        ),
        Step(
            "epoch2026",
            "geocomp:analysis_network_adjust",
            files={"NETWORK": "epoch-2026.json"},
            values=adjust,
        ),
        Step(
            "compare",
            "geocomp:monitoring_compare_epochs",
            files={"THRESHOLDS": "thresholds.csv"},
            wires={
                "FIRST": ("epoch2025", "OUTPUT_SOLUTION"),
                "SECOND": ("epoch2026", "OUTPUT_SOLUTION"),
            },
            values={"REFERENCE": pillars},
            results=(
                "OUTPUT_ANALYSIS",
                "OUTPUT_HTML",
                "OUTPUT_DISPLACEMENT_LAYER",
                "OUTPUT_DISPLACEMENT_ELLIPSE_LAYER",
            ),
        ),
    )


def _gravimetry() -> tuple[Step, ...]:
    joint = DRIFT_MODES.index("joint")
    steps: list[Step] = []
    for name, survey, profiles, known in (
        ("test2", "Test2.txt", "profiles.json", "sta1=50.000"),
        ("test3", "Test3.txt", "profiles.json", "sta1=50.000,sta3=45.000"),
        ("test3calibrated", "Test3.txt", "profiles-calibrated.json", "sta1=50.000,sta3=45.000"),
    ):
        steps.append(
            Step(
                f"{name}reduce",
                "geocomp:gravimetry_preprocess",
                files={"READINGS": survey, "PROFILES": profiles},
                values={"PRECISION_FLOOR": 0.0},
            )
        )
        steps.append(
            Step(
                name,
                "geocomp:gravimetry_network",
                wires={"READINGS": (f"{name}reduce", "OUTPUT_READINGS")},
                values={"KNOWN_GRAVITY": known, "DRIFT_MODE": joint},
                results=("OUTPUT_SOLUTION", "OUTPUT_HTML"),
            )
        )
    return tuple(steps)


def _integration() -> tuple[Step, ...]:
    return tuple(
        Step(
            name,
            "geocomp:integration_gnss_total_station",
            files={"GNSS": "gnss.json", "TOTAL_STATION": "total-station.json"},
            # 0 is ITRF2020, the first of the frames offered.
            values={"FRAME": 0, "FIXED_STATIONS": "CTB1,CTB2", "VARIANCE_COMPONENTS": components},
            results=("OUTPUT_SOLUTION", "OUTPUT_HTML"),
        )
        for name, components in (("stated", False), ("weighed", True))
    )


def _total_station() -> tuple[Step, ...]:
    return (
        Step(
            "import",
            "geocomp:totalstation_import_fieldbook",
            files={"SOURCE": "raw_data.csv", "MAPPING": "mapping.json", "PROFILES": "profiles.json"},
        ),
        Step(
            "preprocess",
            "geocomp:totalstation_preprocess",
            files={"PROFILES": "profiles.json"},
            wires={"READINGS": ("import", "OUTPUT_READINGS")},
            results=("OUTPUT_HTML",),
        ),
        Step(
            "network",
            "geocomp:totalstation_network",
            files={"APPROXIMATE": "approximate.json"},
            wires={"REDUCTIONS": ("preprocess", "OUTPUT_REDUCED")},
            # 0 is 2D, the first dimension offered.
            values={"DIMENSION": 0, "DATUM": _INNER, "CRS": "EPSG:31982"},
            results=("OUTPUT_SOLUTION", "OUTPUT_HTML", *_ADJUSTMENT_LAYERS),
        ),
    )


def _gnss() -> tuple[Step, ...]:
    return (
        Step(
            "static",
            "geocomp:gnss_relative_static",
            files={"FOLDER": "."},
            values={"BASE_STATION": "3040", "ROVER_STATION": "0759"},
            results=("OUTPUT_POS", "OUTPUT_JSON", "OUTPUT_LAYER"),
        ),
    )


#: Each shipped dataset's walkthrough, as the steps its model runs. A step the
#: README describes but GeoComp refuses -- the levelling loop's last, the dam's
#: moved pillar -- is the reader's to try, and is not in the model.
WORKED: dict[str, Callable[[], tuple[Step, ...]]] = {
    "rd01": _total_station,
    "rtklib-sample": _gnss,
    "rd04-loop": _levelling,
    "rd08-dam": _monitoring,
    "rd07-usgs": _gravimetry,
    "combined-curitiba": _integration,
}


def _input_name(file: str) -> str:
    return "FOLDER" if file == "." else re.sub(r"\W+", "_", Path(file).stem).upper()


def build_model(name: str, folder: Path) -> QgsProcessingModelAlgorithm:
    """*name*'s walkthrough as a model, its inputs the files installed in *folder*."""
    registry = QgsApplication.processingRegistry()
    model = QgsProcessingModelAlgorithm(
        _tr("%1 — walkthrough").replace("%1", name), _tr("GeoComp tutorials")
    )
    model.setHelpContent(
        {
            "ALG_DESC": _tr(
                "The walkthrough in this folder's README, as one model: every step it runs, "
                "with the values it gives. Its inputs are the installed files; its files go to "
                "the results folder, and its map layers are loaded when it finishes. The "
                "README explains each result, and the steps it leaves for you to try."
            )
        }
    )

    inputs: set[str] = set()
    for step in WORKED[name]():
        # Created, not the registered instance: its labels are in the language now in use.
        algorithm = registry.algorithmById(step.algorithm).create({})
        definitions = {d.name(): d for d in algorithm.parameterDefinitions()}
        child = QgsProcessingModelChildAlgorithm(step.algorithm)
        child.setChildId(step.id)
        child.setDescription(algorithm.displayName())
        for parameter, file in step.files.items():
            key = _input_name(file)
            if key not in inputs:
                inputs.add(key)
                label = definitions[parameter].description()
                definition = QgsProcessingParameterFile(
                    key,
                    f"{label} — {file}" if file != "." else label,
                    behavior=(
                        QgsProcessingParameterFile.Behavior.Folder
                        if file == "."
                        else QgsProcessingParameterFile.Behavior.File
                    ),
                    defaultValue=str(folder if file == "." else folder / file),
                )
                model.addModelParameter(definition, QgsProcessingModelParameter(key))
            child.addParameterSources(
                parameter, [QgsProcessingModelChildParameterSource.fromModelParameter(key)]
            )
        for parameter, (source, output) in step.wires.items():
            child.addParameterSources(
                parameter, [QgsProcessingModelChildParameterSource.fromChildOutput(source, output)]
            )
        for parameter, value in step.values.items():
            child.addParameterSources(
                parameter, [QgsProcessingModelChildParameterSource.fromStaticValue(value)]
            )
        outputs = {}
        for result in step.results:
            destination = definitions[result]
            label = f"{destination.description()} — {step.id}"
            output = QgsProcessingModelOutput(label)
            output.setChildId(step.id)
            output.setChildOutputName(result)
            # A file goes to results; a layer, given no default, is a temporary one the
            # dialog loads when the model finishes.
            if isinstance(destination, QgsProcessingParameterFileDestination):
                stem = f"{step.id}-{result.removeprefix('OUTPUT_').lower()}"
                output.setDefaultValue(
                    str(folder / "results" / f"{stem}.{destination.defaultFileExtension()}")
                )
            outputs[label] = output
        child.setModelOutputs(outputs)
        model.addChildAlgorithm(child)
    model.updateDestinationParameters()
    return model


def write_project(name: str, folder: Path, path: Path) -> None:
    """Write a QGIS project at *path* holding *name*'s walkthrough model."""
    (folder / "results").mkdir(exist_ok=True)
    model = build_model(name, folder)
    project = QgsProject()
    project.setTitle(model.name())

    def embed(document) -> None:
        root = document.elementsByTagName("qgis").at(0)
        models = document.createElement(PROJECT_MODELS)
        models.appendChild(QgsXmlUtils.writeVariant(model.toVariant(), document))
        root.appendChild(models)

    project.writeProject.connect(embed)
    if not project.write(str(path)):
        raise OSError(project.error())


def read_models(path: Path) -> list[QgsProcessingModelAlgorithm]:
    """The models a project at *path* holds, read as QGIS's project provider reads them."""
    found: list[QgsProcessingModelAlgorithm] = []

    def collect(document) -> None:
        nodes = document.elementsByTagName(PROJECT_MODELS)
        if not nodes.count():
            return
        children = nodes.at(0).childNodes()
        for index in range(children.count()):
            model = QgsProcessingModelAlgorithm()
            if model.loadVariant(QgsXmlUtils.readVariant(children.at(index).toElement())):
                found.append(model)

    project = QgsProject()
    project.readProject.connect(collect)
    if not project.read(str(path)):
        raise OSError(project.error())
    return found
