# SPDX-License-Identifier: GPL-2.0-or-later
"""The worked examples: a QGIS project per tutorial that a student opens and runs (FR-952; P13-12).

*Install tutorial dataset* writes ``<dataset>.qgz`` beside the files, holding
the walkthrough as one model. Each test here does what a student would:
installs the dataset, opens the project (read as QGIS's project provider reads
it), and runs its model with nothing changed. The model must be the README's
steps, and give the numbers the README states.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from geocomp.resources import DATASETS_DIR, available_datasets
from tests.conftest import requires_qgis
from tests.qgis.conftest import requires_modern_field_api
from tests.qgis.walkthrough import quoted, run, steps

pytestmark = [pytest.mark.qgis, requires_qgis]

INSTALL = "geocomp:project_tutorial_dataset"

#: For each dataset, the steps whose results the README quotes: the step's id in
#: the model, the result, and the README's words around it.
STATED = {
    "rd01": (("network", "VARIANCE_FACTOR", "with a variance factor of **{:.2f}**"),),
    "rd04-loop": (
        ("network", "VARIANCE_FACTOR_APOSTERIORI", "a-posteriori variance factor of **{:.0f}**"),
    ),
    "rd08-dam": (
        ("epoch2025", "VARIANCE_FACTOR_APOSTERIORI", "a-posteriori variance factor of **{:.2f}**"),
        ("epoch2026", "VARIANCE_FACTOR_APOSTERIORI", "with a variance factor of **{:.2f}**"),
    ),
    "rd07-usgs": (
        ("test2", "VARIANCE_FACTOR_APOSTERIORI", "passes with a variance factor of **{:.2f}**"),
        ("test3", "VARIANCE_FACTOR_APOSTERIORI", "with a variance factor of **{:.0f}**"),
        ("test3calibrated", "VARIANCE_FACTOR_APOSTERIORI", "with a variance factor of **{:.2f}**"),
    ),
    "combined-curitiba": (
        ("stated", "VARIANCE_FACTOR_APOSTERIORI", "with a variance factor of **{:.2f}**"),
    ),
    "rtklib-sample": (),
}


@pytest.fixture(scope="module", autouse=True)
def _registered(geocomp_provider):
    return geocomp_provider


@pytest.fixture(scope="module", params=sorted(STATED))
def name(request) -> str:
    return request.param


@pytest.fixture(scope="module")
def installed(name, tmp_path_factory) -> tuple[Path, Path]:
    results = run(
        INSTALL,
        {
            "DATASET": available_datasets().index(name),
            "DESTINATION": str(tmp_path_factory.mktemp(f"worked-{name}")),
        },
    )
    return Path(results["OUTPUT_DIRECTORY"]), Path(results["OUTPUT_PROJECT"])


@pytest.fixture(scope="module")
def model(installed):
    from geocomp.algorithms.project.worked_examples import read_models

    _folder, project = installed
    models = read_models(project)
    assert len(models) == 1, models
    return models[0]


def _defaults(model, *, layers: str | None = None) -> dict:
    """The model's own defaults, as its dialog fills them. A layer gets *layers*:
    nothing, or a temporary layer as the dialog's default is."""
    from qgis.core import QgsProcessingDestinationParameter, QgsProcessingParameterFileDestination

    parameters = {}
    for definition in model.parameterDefinitions():
        is_layer = isinstance(definition, QgsProcessingDestinationParameter) and not isinstance(
            definition, QgsProcessingParameterFileDestination
        )
        parameters[definition.name()] = layers if is_layer else definition.defaultValue()
    return parameters


@pytest.fixture(scope="module")
def ran(name, model):
    from qgis.core import QgsProcessingContext, QgsProcessingFeedback

    with pytest.MonkeyPatch.context() as patch:
        if name == "rtklib-sample":
            # rnx2rtkp is tier 4: the solution it gave for this pair stands in.
            from geocomp.services import engines
            from tests.qgis.test_engine_runs import _Rtklib

            patch.setattr(engines, "rtklib_engine", _Rtklib)
        results, ok = model.run(
            _defaults(model), QgsProcessingContext(), QgsProcessingFeedback(), catchExceptions=False
        )
    assert ok
    return results


class TestTheProject:
    def test_the_installer_writes_it_beside_the_files(self, name, installed):
        folder, project = installed
        assert project == folder / f"{name}.qgz" and project.is_file()
        assert (folder / "results").is_dir()

    def test_it_holds_the_walkthrough_and_nothing_else(self, name, model):
        assert name in model.name()

    def test_its_steps_are_the_readmes(self, name, model):
        """The README's steps, less installing the dataset, which the reader has done."""
        from geocomp.algorithms.project.worked_examples import WORKED

        readme = (DATASETS_DIR / name / "README.md").read_text(encoding="utf-8")
        walked = [step.algorithm_id for step in steps(readme) if step.algorithm_id != INSTALL]
        declared = WORKED[name]()
        assert [step.algorithm for step in declared] == walked
        children = model.childAlgorithms()
        assert sorted(children) == sorted(step.id for step in declared)
        assert {child: children[child].algorithmId() for child in children} == {
            step.id: step.algorithm for step in declared
        }

    def test_its_inputs_are_the_installed_files(self, installed, model):
        from qgis.core import QgsProcessingParameterFile

        folder, _project = installed
        inputs = [d for d in model.parameterDefinitions() if isinstance(d, QgsProcessingParameterFile)]
        assert inputs
        for definition in inputs:
            assert Path(definition.defaultValue()).exists(), definition.name()
            assert Path(definition.defaultValue()).parent in (folder, folder.parent)


class TestRunningIt:
    def test_it_runs_as_opened_to_the_numbers_the_readme_states(self, name, ran):
        readme = (DATASETS_DIR / name / "README.md").read_text(encoding="utf-8")
        children = ran["CHILD_RESULTS"]
        for step, result, words in STATED[name]:
            quoted(readme, words.format(children[step][result]))

    def test_its_files_land_in_results(self, installed, ran):
        folder, _project = installed
        written = [
            Path(value)
            for key, value in ran.items()
            if ":" in key and isinstance(value, str) and value
        ]
        assert written
        for path in written:
            assert path.parent == folder / "results" and path.is_file(), path

    def test_the_gnss_sample_gives_its_epochs(self, name, installed, ran):
        if name != "rtklib-sample":
            pytest.skip("the GNSS sample's own check")
        folder, _project = installed
        quality = json.loads((folder / "results" / "static-json.json").read_text(encoding="utf-8"))
        assert "120" in json.dumps(quality)


@requires_modern_field_api
def test_rd01s_model_draws_its_map(tmp_path):
    """The layers a student sees when it finishes: the adjustment's, temporary as the dialog makes them."""
    from qgis.core import (
        QgsProcessing,
        QgsProcessingContext,
        QgsProcessingFeedback,
        QgsProcessingUtils,
    )

    from geocomp.algorithms.project.worked_examples import read_models

    results = run(INSTALL, {"DATASET": available_datasets().index("rd01"), "DESTINATION": str(tmp_path)})
    (model,) = read_models(Path(results["OUTPUT_PROJECT"]))
    context = QgsProcessingContext()
    outcome, ok = model.run(
        _defaults(model, layers=QgsProcessing.TEMPORARY_OUTPUT),
        context,
        QgsProcessingFeedback(),
        catchExceptions=False,
    )
    assert ok
    # The outputs are named by their labels, which end in "(layer)" for a map layer.
    layers = {key: value for key, value in outcome.items() if "(layer)" in key}
    assert len(layers) == 5, sorted(outcome)
    for key, value in layers.items():
        layer = QgsProcessingUtils.mapLayerFromString(value, context)
        assert layer is not None and layer.featureCount() > 0, key
