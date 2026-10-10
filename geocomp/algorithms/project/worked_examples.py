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

**The map is not empty when the project opens** (P13-22). Where a dataset's
inputs place its stations -- a network document's approximate positions, a
RINEX header's, a gravity survey's latitude and longitude -- they are written
to ``<dataset>-stations.gpkg`` beside the project, and the project opens on
that layer, labelled, in its CRS. A dataset whose inputs place nothing, as a
levelling loop's do not, has no such layer.
"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from qgis.core import (
    QgsApplication,
    QgsCoordinateReferenceSystem,
    QgsFeature,
    QgsGeometry,
    QgsPalLayerSettings,
    QgsPointXY,
    QgsProcessingModelAlgorithm,
    QgsProcessingModelChildAlgorithm,
    QgsProcessingModelChildDependency,
    QgsProcessingModelChildParameterSource,
    QgsProcessingModelOutput,
    QgsProcessingModelParameter,
    QgsProcessingParameterFile,
    QgsProcessingParameterFileDestination,
    QgsProject,
    QgsReferencedRectangle,
    QgsVectorFileWriter,
    QgsVectorLayer,
    QgsVectorLayerSimpleLabeling,
    QgsXmlUtils,
)
from qgis.PyQt.QtCore import QCoreApplication

from geocomp.algorithms.analysis.common import DATUM_ORDER, FRAME_ORDER
from geocomp.algorithms.gravimetry.network_adjust import DRIFT_MODES
from geocomp.core.adjustment import Frame
from geocomp.core.geodesy.cartesian import cartesian_to_geodetic
from geocomp.core.geodesy.ellipsoid import ELLIPSOIDS
from geocomp.core.models import CoordinateSystem, DatumDefinition, Network
from geocomp.io.gnss_discovery import scan_folder
from geocomp.io.gravimeter_files import read_gravimeter_file

__all__ = ["PLACED", "WORKED", "Step", "build_model", "read_models", "stations_file", "write_project"]

_CONTEXT = "WorkedExamples"

#: The element QGIS's project provider keeps a project's models in.
PROJECT_MODELS = "projectModels"

#: The CRS rd01's walkthrough adjusts in, and so the one its approximate
#: positions are drawn in: the adjusted stations then fall on them.
_RD01_CRS = "EPSG:31982"

#: Longitude and latitude. A RINEX header's or a geocentric document's position
#: is a start, a metre or so out; the datum it is in does not show on a map.
_GEOGRAPHIC = "EPSG:4326"


def _tr(text: str) -> str:
    return QCoreApplication.translate(_CONTEXT, text)


@dataclass(frozen=True)
class Step:
    """One step of a walkthrough, as one child of its model.

    Attributes:
        id: The child's id, which the model's outputs are named by.
        algorithm: The GeoComp algorithm it runs.
        files: Inputs read from an installed file, by name; ``"."`` is the
            dataset's folder itself, and a name ending ``/`` a folder in it.
            Each becomes an input of the model, whose default is that file.
        wires: Inputs taken from an earlier step's output, as ``(step, output)``.
        values: Every other input the walkthrough fills.
        results: Outputs the model exposes. A file is written into ``results``,
            or into :attr:`folder` inside it; a layer is loaded when the model
            finishes.
        folder: The folder inside ``results`` this step's files go to, when
            its files are read back together, as a folder (P13-17).
        reads: Inputs that are a folder inside ``results``, by name: the files
            earlier steps wrote there.
        after: Steps this one runs after. A step reading a folder takes nothing
            from the steps that fill it, so the model is told.
    """

    id: str
    algorithm: str
    files: dict[str, str] = field(default_factory=dict)
    wires: dict[str, tuple[str, str]] = field(default_factory=dict)
    values: dict[str, Any] = field(default_factory=dict)
    results: tuple[str, ...] = ()
    folder: str = ""
    reads: dict[str, str] = field(default_factory=dict)
    after: tuple[str, ...] = ()


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
            values={"DIMENSION": 0, "DATUM": _INNER, "CRS": _RD01_CRS},
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


def _ggao() -> tuple[Step, ...]:
    """Each hour's three sides, then its closure; the solutions of an hour in a folder of their own."""
    steps: list[Step] = []
    for hour in ("00", "11"):
        sides = []
        for base, rover in (("GODN", "GODE"), ("GODN", "GODS"), ("GODE", "GODS")):
            side = f"{base}{rover}{hour}".lower()
            sides.append(side)
            steps.append(
                Step(
                    side,
                    "geocomp:gnss_relative_static",
                    files={"FOLDER": f"hour-{hour}/"},
                    values={"BASE_STATION": base, "ROVER_STATION": rover},
                    results=("OUTPUT_POS",),
                    folder=f"solutions-{hour}",
                )
            )
        steps.append(
            Step(
                f"baselines{hour}",
                "geocomp:gnss_build_baselines",
                reads={"FOLDER": f"solutions-{hour}"},
                results=("OUTPUT_JSON",),
                after=tuple(sides),
            )
        )
    return tuple(steps)


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
    "ggao-triangle": _ggao,
}


#: A station, where an input places it, and the file that does.
Placed = tuple[str, float, float, str]


def _geographic(xyz) -> tuple[float, float]:
    """Longitude and latitude, in degrees, of a geocentric position."""
    latitude, longitude, _height = cartesian_to_geodetic(*(float(v) for v in xyz), ELLIPSOIDS["GRS80"])
    return math.degrees(longitude), math.degrees(latitude)


def _placed_by_network(file: str) -> Callable[[Path], tuple[str, list[Placed]]]:
    """Each station of a network document, at its approximate or held position."""

    def placed(folder: Path) -> tuple[str, list[Placed]]:
        network = Network.from_dict(json.loads((folder / file).read_text(encoding="utf-8")))
        crs, rows = "", []
        for station in network.stations.values():
            position = station.approx_position or station.constraint.position
            if position is None:
                continue
            first, second, _third = (q.value for q in position.values)
            if position.system is CoordinateSystem.PROJECTED:
                crs, x, y = position.crs, first, second
            elif position.system is CoordinateSystem.CARTESIAN:
                crs, (x, y) = _GEOGRAPHIC, _geographic((first, second, _third))
            else:
                crs, x, y = _GEOGRAPHIC, math.degrees(second), math.degrees(first)
            rows.append((station.id, x, y, file))
        return crs, rows

    return placed


def _placed_by_rinex(subfolder: str = "") -> Callable[[Path], tuple[str, list[Placed]]]:
    """Each observing station, at its RINEX header's approximate position."""

    def placed(folder: Path) -> tuple[str, list[Placed]]:
        rows = []
        for session in scan_folder(folder / subfolder).sessions:
            xyz = session.meta.get("approximate_position")
            if xyz:
                rows.append((session.station_id, *_geographic(xyz), Path(session.obs_file).name))
        return _GEOGRAPHIC, rows

    return placed


def _placed_by_gravity(*files: str) -> Callable[[Path], tuple[str, list[Placed]]]:
    """Each surveyed station, where its first reading puts it."""

    def placed(folder: Path) -> tuple[str, list[Placed]]:
        rows, seen = [], set()
        for file in files:
            for reading in read_gravimeter_file(folder / file).readings:
                if reading.station in seen or reading.latitude is None or reading.longitude is None:
                    continue
                seen.add(reading.station)
                rows.append(
                    (reading.station, math.degrees(reading.longitude), math.degrees(reading.latitude), file)
                )
        return _GEOGRAPHIC, rows

    return placed


def _placed_approximately(folder: Path) -> tuple[str, list[Placed]]:
    """rd01's approximate coordinates, station by station."""
    approximate = json.loads((folder / "approximate.json").read_text(encoding="utf-8"))
    return _RD01_CRS, [
        (station, float(east), float(north), "approximate.json")
        for station, (east, north, *_up) in approximate.items()
    ]


#: Where each dataset's inputs place its stations (P13-22). rd04-loop's
#: levelling book places none.
PLACED: dict[str, Callable[[Path], tuple[str, list[Placed]]]] = {
    "rd01": _placed_approximately,
    "rtklib-sample": _placed_by_rinex(),
    "rd08-dam": _placed_by_network("epoch-2025.json"),
    "rd07-usgs": _placed_by_gravity("Test2.txt", "Test3.txt"),
    "combined-curitiba": _placed_by_network("gnss.json"),
    "ggao-triangle": _placed_by_rinex("hour-00"),
}


def stations_file(name: str, folder: Path) -> Path:
    """Where *name*'s stations are written, beside its project."""
    return folder / f"{name}-stations.gpkg"


def _input_name(file: str) -> str:
    return "FOLDER" if file == "." else re.sub(r"\W+", "_", Path(file.rstrip("/")).stem).upper()


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
                is_folder = file == "." or file.endswith("/")
                definition = QgsProcessingParameterFile(
                    key,
                    f"{label} — {file.rstrip('/')}" if file != "." else label,
                    behavior=(
                        QgsProcessingParameterFile.Behavior.Folder
                        if is_folder
                        else QgsProcessingParameterFile.Behavior.File
                    ),
                    defaultValue=str(folder if file == "." else folder / file.rstrip("/")),
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
        for parameter, read in step.reads.items():
            child.addParameterSources(
                parameter,
                [QgsProcessingModelChildParameterSource.fromStaticValue(str(folder / "results" / read))],
            )
        if step.after:
            child.setDependencies([QgsProcessingModelChildDependency(earlier) for earlier in step.after])
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
                    str(folder / "results" / step.folder / f"{stem}.{destination.defaultFileExtension()}")
                )
            outputs[label] = output
        child.setModelOutputs(outputs)
        model.addChildAlgorithm(child)
    model.updateDestinationParameters()
    return model


def write_project(name: str, folder: Path, path: Path) -> None:
    """Write a QGIS project at *path* holding *name*'s walkthrough model."""
    (folder / "results").mkdir(exist_ok=True)
    for step in WORKED[name]():
        if step.folder:
            (folder / "results" / step.folder).mkdir(exist_ok=True)
    model = build_model(name, folder)
    project = QgsProject()
    project.setTitle(model.name())
    if name in PLACED:
        _add_stations(project, stations_file(name, folder), *PLACED[name](folder))

    def embed(document) -> None:
        root = document.elementsByTagName("qgis").at(0)
        models = document.createElement(PROJECT_MODELS)
        models.appendChild(QgsXmlUtils.writeVariant(model.toVariant(), document))
        root.appendChild(models)

    project.writeProject.connect(embed)
    if not project.write(str(path)):
        raise OSError(project.error())


def _add_stations(project: QgsProject, path: Path, crs: str, rows: list[Placed]) -> None:
    """Write *rows* to a GeoPackage at *path*, and open *project* on it, labelled.

    Built as a memory layer and written out, rather than field by field: a
    memory layer's URI names its fields as text, which every QGIS the tests
    run on reads alike.
    """
    reference = QgsCoordinateReferenceSystem(crs)
    memory = QgsVectorLayer(
        f"Point?crs={crs}&field=station:string&field=source:string", "stations", "memory"
    )
    features = []
    for station, x, y, source in rows:
        feature = QgsFeature(memory.fields())
        feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(x, y)))
        feature.setAttributes([station, source])
        features.append(feature)
    memory.dataProvider().addFeatures(features)
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = "GPKG"
    options.layerName = "stations"
    written = QgsVectorFileWriter.writeAsVectorFormatV3(
        memory, str(path), project.transformContext(), options
    )
    if written[0] != QgsVectorFileWriter.WriterError.NoError:
        raise OSError(written[1])

    layer = QgsVectorLayer(
        f"{path}|layername=stations", _tr("Stations, where the inputs place them"), "ogr"
    )
    labels = QgsPalLayerSettings()
    labels.fieldName = "station"
    layer.setLabeling(QgsVectorLayerSimpleLabeling(labels))
    layer.setLabelsEnabled(True)
    project.addMapLayer(layer)
    project.setCrs(reference)
    # A project written here has no canvas to remember an extent, so QGIS is
    # told where to open: the stations, with a margin, or a little round one.
    extent = layer.extent()
    extent.grow(max(extent.width(), extent.height()) * 0.2 or (0.01 if reference.isGeographic() else 50.0))
    project.viewSettings().setDefaultViewExtent(QgsReferencedRectangle(extent, reference))


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
