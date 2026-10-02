# SPDX-License-Identifier: GPL-2.0-or-later
"""A saved model runs the whole chain headless, and every way of running gives one answer.

``specs/16`` criterion 5: a model-builder model chaining import, pre-process,
adjust and visualise runs headlessly end to end. Criterion 2: the toolbox, the
modeller, batch mode and PyQGIS give identical results (FR-033). Until P12c
the chain was tested step by step, by a test that fed each output to the next
by hand; no test had built a model, so nothing showed that the outputs are
ones the modeller can wire, nor that a saved model reloads.

The three ways run here are the three execution paths QGIS has:

* **PyQGIS**: ``algorithm.run`` on the main thread.
* **The toolbox and batch dialogs**: a ``QgsProcessingAlgRunnerTask`` on a
  worker thread. That is how QGIS's algorithm dialog runs any algorithm not
  flagged ``NoThreading``, and how the batch dialog runs each row. What the
  dialogs add is widgets that build the parameters, which are QGIS's own.
* **The modeller**: a ``QgsProcessingModelAlgorithm``, saved to a ``.model3``
  file and loaded back, as a user's saved model would be.

RD-01 is the data, because it is what ``specs/09`` criterion 9 asks the menu
to turn into styled layers with ellipses.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from tests import reference_rd01 as rd01
from tests.conftest import requires_qgis
from tests.qgis.conftest import requires_modern_field_api

pytestmark = [pytest.mark.qgis, requires_qgis]

IMPORT = "geocomp:totalstation_import_fieldbook"
PREPROCESS = "geocomp:totalstation_preprocess"
NETWORK = "geocomp:totalstation_network"

#: The parameters each step takes besides the previous step's output and its own
#: destinations: RD-01's stochastic model and datum, as the whole-chain test has them.
IMPORT_SETTINGS = {
    "SIGMA_DIRECTION": rd01.SIGMA_ANGLE,
    "SIGMA_ZENITH": rd01.SIGMA_ANGLE,
    "SIGMA_DISTANCE": 0.002,
}
PREPROCESS_SETTINGS = {"APPLY_ATMOSPHERIC": False}
NETWORK_SETTINGS = {"DIMENSION": 0, "DATUM": 1, "CRS": "EPSG:31982", "EXAGGERATION": 2000.0}

LAYERS = ("OUTPUT_STATION_LAYER", "OUTPUT_ELLIPSE_LAYER", "OUTPUT_RESIDUAL_LAYER")


@pytest.fixture(scope="module")
def approximate(tmp_path_factory) -> str:
    path = tmp_path_factory.mktemp("rd01-approximate") / "approximate.json"
    path.write_text(json.dumps(rd01.approximate_coordinates()), encoding="utf-8")
    return str(path)


def _directly(algorithm_id: str, parameters: dict):
    from qgis.core import QgsApplication, QgsProcessingContext, QgsProcessingFeedback

    algorithm = QgsApplication.processingRegistry().algorithmById(algorithm_id).create({})
    context = QgsProcessingContext()
    results, ok = algorithm.run(parameters, context, QgsProcessingFeedback(), catchExceptions=False)
    assert ok, algorithm_id
    return results, context


def _in_a_task(algorithm_id: str, parameters: dict):
    """As the toolbox dialog runs it: prepared here, run on a worker thread,
    post-processed back on this one."""
    from qgis.core import (
        QgsApplication,
        QgsProcessingAlgRunnerTask,
        QgsProcessingContext,
        QgsProcessingFeedback,
    )
    from qgis.PyQt.QtCore import QCoreApplication

    algorithm = QgsApplication.processingRegistry().algorithmById(algorithm_id)
    context = QgsProcessingContext()
    feedback = QgsProcessingFeedback()
    outcome: dict = {}
    task = QgsProcessingAlgRunnerTask(algorithm, parameters, context, feedback)
    task.executed.connect(lambda ok, results: outcome.update(ok=ok, results=results))
    QgsApplication.taskManager().addTask(task)
    deadline = time.monotonic() + 120.0
    while "ok" not in outcome and time.monotonic() < deadline:
        QCoreApplication.processEvents()
        time.sleep(0.005)
    assert outcome.get("ok"), f"{algorithm_id} did not complete as a task"
    return outcome["results"], context


def _chain(run, directory: Path, approximate: str, *, layers: bool = False):
    directory.mkdir(parents=True, exist_ok=True)
    imported, _ = run(
        IMPORT,
        {
            "SOURCE": str(rd01.RAW),
            **IMPORT_SETTINGS,
            "OUTPUT_READINGS": str(directory / "readings.json"),
        },
    )
    reduced, _ = run(
        PREPROCESS,
        {
            "READINGS": imported["OUTPUT_READINGS"],
            **PREPROCESS_SETTINGS,
            "OUTPUT_REDUCED": str(directory / "reduced.json"),
        },
    )
    parameters = {
        "REDUCTIONS": reduced["OUTPUT_REDUCED"],
        "APPROXIMATE": approximate,
        **NETWORK_SETTINGS,
        "OUTPUT_SOLUTION": str(directory / "solution.json"),
    }
    if layers:
        from qgis.core import QgsProcessing

        parameters.update(dict.fromkeys(LAYERS, QgsProcessing.TEMPORARY_OUTPUT))
    return run(NETWORK, parameters)


def _model(*, layers: bool):
    """Import -> pre-process -> adjust, the solution and, with *layers*, the map as its outputs."""
    from qgis.core import (
        QgsProcessingModelAlgorithm,
        QgsProcessingModelChildAlgorithm,
        QgsProcessingModelChildParameterSource,
        QgsProcessingModelOutput,
        QgsProcessingModelParameter,
        QgsProcessingParameterFile,
    )

    def static(value):
        return [QgsProcessingModelChildParameterSource.fromStaticValue(value)]

    def child(child_id: str, algorithm_id: str, settings: dict, **sources):
        step = QgsProcessingModelChildAlgorithm(algorithm_id)
        step.setChildId(child_id)
        for name, value in settings.items():
            step.addParameterSources(name, static(value))
        for name, source in sources.items():
            step.addParameterSources(name, [source])
        return step

    model = QgsProcessingModelAlgorithm("RD-01 chain", "GeoComp tests")
    for name, label in (("SOURCE", "Field book"), ("APPROXIMATE", "Approximate coordinates")):
        model.addModelParameter(QgsProcessingParameterFile(name, label), QgsProcessingModelParameter(name))

    importing = child(
        "import",
        IMPORT,
        IMPORT_SETTINGS,
        SOURCE=QgsProcessingModelChildParameterSource.fromModelParameter("SOURCE"),
    )
    reducing = child(
        "preprocess",
        PREPROCESS,
        PREPROCESS_SETTINGS,
        READINGS=QgsProcessingModelChildParameterSource.fromChildOutput("import", "OUTPUT_READINGS"),
    )
    adjusting = child(
        "adjust",
        NETWORK,
        NETWORK_SETTINGS,
        REDUCTIONS=QgsProcessingModelChildParameterSource.fromChildOutput("preprocess", "OUTPUT_REDUCED"),
        APPROXIMATE=QgsProcessingModelChildParameterSource.fromModelParameter("APPROXIMATE"),
    )
    outputs = {}
    for name in ("OUTPUT_SOLUTION", *(LAYERS if layers else ())):
        output = QgsProcessingModelOutput(name.lower())
        output.setChildId("adjust")
        output.setChildOutputName(name)
        outputs[name.lower()] = output
    adjusting.setModelOutputs(outputs)

    for step in (importing, reducing, adjusting):
        model.addChildAlgorithm(step)
    model.updateDestinationParameters()
    return model


def _comparable(path: str) -> dict:
    """A solution document without its provenance, which names when and how it was run."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    payload.pop("provenance", None)
    return payload


@pytest.fixture(scope="module")
def by_pyqgis(geocomp_provider, approximate, tmp_path_factory):
    return _chain(_directly, tmp_path_factory.mktemp("pyqgis"), approximate)


@pytest.fixture(scope="module")
def by_task(geocomp_provider, approximate, tmp_path_factory):
    return _chain(_in_a_task, tmp_path_factory.mktemp("task"), approximate)


def _saved(directory: Path, *, layers: bool):
    from qgis.core import QgsProcessingModelAlgorithm

    path = directory / "rd01_chain.model3"
    assert _model(layers=layers).toFile(str(path))
    loaded = QgsProcessingModelAlgorithm()
    assert loaded.fromFile(str(path))
    return loaded


def _run_model(model, directory: Path, approximate: str, *, layers: bool):
    from qgis.core import QgsProcessing, QgsProcessingContext, QgsProcessingFeedback

    parameters = {
        "SOURCE": str(rd01.RAW),
        "APPROXIMATE": approximate,
        "adjust:output_solution": str(directory / "solution.json"),
    }
    if layers:
        for name in LAYERS:
            parameters[f"adjust:{name.lower()}"] = QgsProcessing.TEMPORARY_OUTPUT
    context = QgsProcessingContext()
    results, ok = model.run(parameters, context, QgsProcessingFeedback(), catchExceptions=False)
    assert ok
    return results, context


@pytest.fixture(scope="module")
def saved_model(geocomp_provider, tmp_path_factory):
    return _saved(tmp_path_factory.mktemp("model"), layers=False)


@pytest.fixture(scope="module")
def by_model(saved_model, approximate, tmp_path_factory):
    return _run_model(saved_model, tmp_path_factory.mktemp("model-run"), approximate, layers=False)


class TestTheModel:
    def test_it_is_three_steps_wired_output_to_input(self, saved_model):
        steps = saved_model.childAlgorithms()
        assert {step.algorithmId() for step in steps.values()} == {IMPORT, PREPROCESS, NETWORK}
        assert set(saved_model.dependsOnChildAlgorithms("adjust")) == {"import", "preprocess"}

    def test_the_saved_model_adjusts_the_field_book(self, by_model):
        from geocomp.core.models import Solution

        results, _context = by_model
        solution = Solution.from_dict(
            json.loads(Path(results["adjust:output_solution"]).read_text(encoding="utf-8"))
        )
        assert len(solution.adjusted_stations) == 3

    @requires_modern_field_api
    def test_the_saved_model_runs_headless_to_the_map(self, approximate, tmp_path):
        """Criterion 5, all of it: from the field book to the solution and its layers."""
        from qgis.core import QgsProcessingUtils

        model = _saved(tmp_path, layers=True)
        results, context = _run_model(model, tmp_path, approximate, layers=True)
        assert Path(results["adjust:output_solution"]).is_file()
        for name in LAYERS:
            layer = QgsProcessingUtils.mapLayerFromString(results[f"adjust:{name.lower()}"], context)
            assert layer is not None and layer.featureCount() > 0, name


class TestEveryWayGivesOneAnswer:
    """Criterion 2: the solution is the same document, provenance aside, however it was run."""

    def test_the_toolbox_path_gives_what_pyqgis_gives(self, by_pyqgis, by_task):
        assert _comparable(by_task[0]["OUTPUT_SOLUTION"]) == _comparable(by_pyqgis[0]["OUTPUT_SOLUTION"])

    def test_the_model_gives_what_pyqgis_gives(self, by_pyqgis, by_model):
        assert _comparable(by_model[0]["adjust:output_solution"]) == _comparable(
            by_pyqgis[0]["OUTPUT_SOLUTION"]
        )

    def test_the_provenance_names_the_same_algorithm(self, by_pyqgis, by_task, by_model):
        names = {
            json.loads(Path(path).read_text(encoding="utf-8"))["provenance"]["algorithm_id"]
            for path in (
                by_pyqgis[0]["OUTPUT_SOLUTION"],
                by_task[0]["OUTPUT_SOLUTION"],
                by_model[0]["adjust:output_solution"],
            )
        }
        assert names == {NETWORK}


@requires_modern_field_api
class TestRd01ArrivesAsStyledLayers:
    """``specs/09`` criterion 9: RD-01, run as the menu runs it, gives styled
    layers with an ellipse for every station."""

    @pytest.fixture(scope="class")
    def layers(self, geocomp_provider, approximate, tmp_path_factory):
        from qgis.core import QgsProcessingFeedback, QgsProcessingUtils

        directory = tmp_path_factory.mktemp("task-layers")
        results, context = _chain(_in_a_task, directory, approximate, layers=True)
        produced = {}
        for name in LAYERS:
            layer = QgsProcessingUtils.mapLayerFromString(results[name], context)
            assert layer is not None, f"{name} produced no layer"
            details = context.layerToLoadOnCompletionDetails(results[name])
            details.postProcessor().postProcessLayer(layer, context, QgsProcessingFeedback())
            produced[name] = layer
        # Yielded, not returned: the layers live in the context's temporary
        # store, which deletes them when the context goes, and this frame is
        # what keeps the context until the class's tests are done.
        yield produced

    def test_every_station_has_its_ellipse(self, layers):
        assert layers["OUTPUT_ELLIPSE_LAYER"].featureCount() == 3
        assert layers["OUTPUT_STATION_LAYER"].featureCount() == 3

    def test_the_ellipse_layer_states_its_exaggeration(self, layers):
        assert "2000" in layers["OUTPUT_ELLIPSE_LAYER"].name()

    @pytest.mark.parametrize(
        ("output", "style"),
        [
            ("OUTPUT_STATION_LAYER", "stations"),
            ("OUTPUT_ELLIPSE_LAYER", "ellipses"),
            ("OUTPUT_RESIDUAL_LAYER", "residuals"),
        ],
    )
    def test_each_layer_draws_with_its_shipped_style(self, layers, output, style):
        from qgis.core import QgsVectorLayer

        from geocomp.layers.builders import LAYER_GEOMETRY, fields_for
        from geocomp.layers.styles import style_path

        reference = QgsVectorLayer(f"{LAYER_GEOMETRY[style]}?crs=EPSG:31982", style, "memory")
        reference.dataProvider().addAttributes(list(fields_for(style)))
        reference.updateFields()
        _message, ok = reference.loadNamedStyle(str(style_path(style)))
        assert ok
        assert layers[output].renderer().dump() == reference.renderer().dump()
