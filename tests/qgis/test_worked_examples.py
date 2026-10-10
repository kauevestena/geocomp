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
from contextlib import contextmanager
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
    "ggao-triangle": (),
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


@contextmanager
def _engines_standing_in(name: str):
    """rnx2rtkp is tier 4: the solutions it gave for a GNSS tutorial's pairs stand in."""
    with pytest.MonkeyPatch.context() as patch:
        if name == "rtklib-sample":
            from geocomp.services import engines
            from tests.qgis.test_engine_runs import _Rtklib

            patch.setattr(engines, "rtklib_engine", _Rtklib)
        if name == "ggao-triangle":
            # Each hour's three pairs.
            from geocomp.services import engines
            from tests.qgis.test_gnss_tutorial import _Recorded

            patch.setattr(engines, "rtklib_engine", _Recorded)
        yield


@pytest.fixture(scope="module")
def ran(name, model):
    from qgis.core import QgsProcessingContext, QgsProcessingFeedback

    with _engines_standing_in(name):
        results, ok = model.run(
            _defaults(model), QgsProcessingContext(), QgsProcessingFeedback(), catchExceptions=False
        )
    assert ok
    return results


#: Each dataset's stations as its project's map shows them (P13-22): the CRS,
#: the stations, and where one of them is -- in longitude and latitude where
#: the CRS is geographic, which is what puts a RINEX header's Japan in Japan.
#: rd04-loop's levelling book places no station, and its map is empty.
ON_THE_MAP = {
    "rd01": ("EPSG:31982", {"1", "2", "3"}, ("1", 0.0, 0.0)),
    "rtklib-sample": ("EPSG:4326", {"0759", "3040"}, ("3040", 139.6243, 35.1321)),
    "rd08-dam": (
        "EPSG:31982",
        {"R1", "R2", "R3", "R4", "O1", "O2", "O3", "O4", "O5"},
        ("R1", 675000.0007, 7185000.0270),
    ),
    "rd07-usgs": ("EPSG:4326", {"sta1", "sta2", "sta3", "sta4", "sta5"}, ("sta1", -110.0, 32.5)),
    "combined-curitiba": (
        "EPSG:4326",
        {"CTB1", "CTB2", "M03", "M04", "M05", "M06"},
        ("CTB1", -49.2700, -25.4300),
    ),
    "ggao-triangle": ("EPSG:4326", {"GODN", "GODE", "GODS"}, ("GODN", -76.8271, 39.0212)),
}


def _opened(installed):
    """The installed project, read as QGIS reads it.

    Opened in the test, not by a fixture: pytest keeps a fixture's value on the
    test item until the session ends, and a project still holding a GeoPackage
    layer when QGIS has shut down crashes the interpreter on its way out.
    """
    from qgis.core import QgsProject

    _folder, path = installed
    project = QgsProject()
    assert project.read(str(path)), project.error()
    return project


class TestTheMap:
    """P13-22: the project opens on the stations, before the model has run."""

    def test_it_opens_on_the_stations_the_inputs_place(self, name, installed):
        from geocomp.algorithms.project.worked_examples import stations_file

        folder, _path = installed
        opened = _opened(installed)
        layers = list(opened.mapLayers().values())
        if name not in ON_THE_MAP:
            assert layers == []
            assert not stations_file(name, folder).exists()
            return
        crs, stations, _one = ON_THE_MAP[name]
        (layer,) = layers
        assert layer.isValid()
        # As paths: QGIS writes the source with forward slashes on Windows too.
        assert Path(layer.source().split("|")[0]) == stations_file(name, folder)
        assert layer.crs().authid() == crs == opened.crs().authid()
        assert {feature["station"] for feature in layer.getFeatures()} == stations

    def test_each_station_is_where_its_input_puts_it(self, name, installed):
        if name not in ON_THE_MAP:
            pytest.skip("its inputs place no station")
        _crs, _stations, (station, x, y) = ON_THE_MAP[name]
        opened = _opened(installed)
        (layer,) = opened.mapLayers().values()
        (feature,) = [f for f in layer.getFeatures() if f["station"] == station]
        point = feature.geometry().asPoint()
        assert (point.x(), point.y()) == pytest.approx((x, y), abs=1e-4)

    def test_it_is_labelled_and_opens_on_them(self, name, installed):
        if name not in ON_THE_MAP:
            pytest.skip("its inputs place no station")
        opened = _opened(installed)
        (layer,) = opened.mapLayers().values()
        assert layer.labelsEnabled()
        assert layer.labeling().settings().fieldName == "station"
        view = opened.viewSettings().defaultViewExtent()
        assert view.crs() == layer.crs()
        assert view.contains(layer.extent()) and view.width() > 0 and view.height() > 0


class TestTheLayout:
    """P13-24: a print layout of the map as it stands -- the stations, and the results once loaded."""

    def test_it_holds_one_named_after_the_dataset(self, name, installed):
        from geocomp.algorithms.project.worked_examples import layout_name

        opened = _opened(installed)
        layouts = opened.layoutManager().printLayouts()
        if name not in ON_THE_MAP:
            assert layouts == []
            return
        (layout,) = layouts
        assert layout.name() == layout_name(name)
        assert layout.itemById("title").text() == layout_name(name)
        assert opened.crs().authid() in layout.itemById("footer").text()
        assert "exaggerated" in layout.itemById("notes").text()

    def test_its_map_draws_the_project_at_the_stations(self, name, installed):
        if name not in ON_THE_MAP:
            pytest.skip("its inputs place no station")
        opened = _opened(installed)
        (layout,) = opened.layoutManager().printLayouts()
        (stations,) = opened.mapLayers().values()
        drawing = layout.itemById("map")
        # No layers of its own: it draws what the project shows.
        assert drawing.layers() == [] and not drawing.keepLayerSet()
        assert not drawing.followVisibilityPreset()
        assert [layer.id() for layer in drawing.layersToRender()] == [stations.id()]
        assert drawing.crs() == stations.crs()
        assert drawing.extent().contains(stations.extent())

    def test_a_layer_loaded_later_is_drawn_and_listed(self, name, installed):
        """What the model's result layers do when it finishes and they are loaded."""
        from qgis.core import QgsVectorLayer

        if name not in ON_THE_MAP:
            pytest.skip("its inputs place no station")
        opened = _opened(installed)
        (layout,) = opened.layoutManager().printLayouts()
        (stations,) = opened.mapLayers().values()
        result = QgsVectorLayer(f"Point?crs={stations.crs().authid()}", "a result", "memory")
        opened.addMapLayer(result)
        drawing = layout.itemById("map")
        assert {stations.id(), result.id()} <= {layer.id() for layer in drawing.layersToRender()}
        legend = layout.itemById("legend")
        assert legend.linkedMap() == drawing
        assert {stations.id(), result.id()} <= set(legend.model().rootGroup().findLayerIds())


def test_the_installers_help_names_every_dataset():
    """Found by P13-24: the help named every tutorial but the GNSS one, which P13-17 added."""
    from geocomp.algorithms.project.tutorial_dataset import TutorialDatasetAlgorithm

    algorithm = TutorialDatasetAlgorithm()
    body = algorithm.help_body()
    for name in available_datasets():
        assert f"<b>{ {'rd01': 'RD-01'}.get(name, name) }</b>" in body, name
    assert "print layout" in body


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
            # Or a folder inside it, where a later step reads them back together.
            assert folder / "results" in (path.parent, path.parent.parent) and path.is_file(), path

    def test_the_gnss_tutorial_closes_its_two_loops_as_the_readme_states(self, name, ran):
        if name != "ggao-triangle":
            pytest.skip("the GNSS tutorial's own check")
        readme = (DATASETS_DIR / name / "README.md").read_text(encoding="utf-8")
        children = ran["CHILD_RESULTS"]
        midnight, eleven = (
            json.loads(Path(children[f"baselines{hour}"]["OUTPUT_JSON"]).read_text(encoding="utf-8"))
            for hour in ("00", "11")
        )
        quoted(readme, f"**The triangle closes to {midnight['closures'][0]['magnitude_mm']:.2f} mm.**")
        quoted(readme, f"**The triangle misses by {eleven['closures'][0]['magnitude_mm']:.2f} mm**")
        # Each hour's three sides, and only those: the folders keep the hours apart.
        assert len(midnight["observations"]) == len(eleven["observations"]) == 2
        assert midnight["dependent"] and eleven["dependent"]

    def test_the_gnss_sample_gives_its_epochs(self, name, installed, ran):
        if name != "rtklib-sample":
            pytest.skip("the GNSS sample's own check")
        folder, _project = installed
        quality = json.loads((folder / "results" / "static-json.json").read_text(encoding="utf-8"))
        assert "120" in json.dumps(quality)


#: How many result layers each model loads when it finishes (P13-24). The
#: gravity tutorial's is the calibrated run's, and the integration tutorial's
#: the weighed one's: the runs the walkthroughs end on.
DRAWN = {
    "rd01": 5,
    "rtklib-sample": 1,
    "rd04-loop": 0,
    "rd08-dam": 2,
    "rd07-usgs": 2,
    "combined-curitiba": 5,
    "ggao-triangle": 2,
}


@requires_modern_field_api
def test_its_model_draws_its_results_into_the_layout(name, installed, model):
    """The layers a student sees when it finishes, temporary as the dialog makes them and
    loaded as it loads them: each has features, and the layout draws and lists them."""
    from qgis.core import (
        QgsProcessing,
        QgsProcessingContext,
        QgsProcessingDestinationParameter,
        QgsProcessingFeedback,
        QgsProcessingParameterFileDestination,
        QgsProcessingUtils,
    )

    opened = _opened(installed)
    context = QgsProcessingContext()
    context.setProject(opened)
    with _engines_standing_in(name):
        outcome, ok = model.run(
            _defaults(model, layers=QgsProcessing.TEMPORARY_OUTPUT),
            context,
            QgsProcessingFeedback(),
            catchExceptions=False,
        )
    assert ok
    drawn = [
        definition.name()
        for definition in model.parameterDefinitions()
        if isinstance(definition, QgsProcessingDestinationParameter)
        and not isinstance(definition, QgsProcessingParameterFileDestination)
    ]
    assert len(drawn) == DRAWN[name], drawn
    results = []
    for key in drawn:
        layer = QgsProcessingUtils.mapLayerFromString(outcome[key], context)
        assert layer is not None and layer.featureCount() > 0, key
        context.temporaryLayerStore().takeMapLayer(layer)
        opened.addMapLayer(layer)
        results.append(layer.id())
    if name not in ON_THE_MAP:
        assert opened.layoutManager().printLayouts() == []
        return
    (layout,) = opened.layoutManager().printLayouts()
    assert set(results) <= {layer.id() for layer in layout.itemById("map").layersToRender()}
    assert set(results) <= set(layout.itemById("legend").model().rootGroup().findLayerIds())
