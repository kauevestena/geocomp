# SPDX-License-Identifier: GPL-2.0-or-later
"""The four project-level algorithms P5 adds, in a running QGIS.

``geocomp:project_export``, ``project_report``, ``project_store`` and
``project_basemap``. The machinery each drives is tested without QGIS in
``tests/test_export.py``, ``tests/test_report_templates.py``,
``tests/test_project_store.py`` and ``tests/test_basemaps.py``; what needs a
runtime, and is therefore here, is that a user can actually reach it: the
algorithm registers, its parameters accept what a previous algorithm wrote, and
the whole chain from an adjustment to a stored, reported, exported result runs.

The chain is the point. Each of these takes a *solution document* written by
another algorithm, so a mismatch between what one writes and what the next reads
is a defect no single-algorithm test can see -- and it is exactly the kind of
defect that only appears when someone tries to use the plugin.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.conftest import requires_qgis

pytestmark = [pytest.mark.qgis, requires_qgis]

PROJECT_IDS = (
    "geocomp:project_export",
    "geocomp:project_report",
    "geocomp:project_store",
    "geocomp:project_basemap",
)


@pytest.fixture(autouse=True, scope="module")
def _registered(geocomp_provider):
    return geocomp_provider


def _algorithm(algorithm_id: str):
    from qgis.core import QgsApplication

    algorithm = QgsApplication.processingRegistry().algorithmById(algorithm_id)
    assert algorithm is not None, f"{algorithm_id} is not registered"
    return algorithm


def _run(algorithm_id: str, parameters: dict):
    from qgis.core import QgsProcessingContext, QgsProcessingFeedback

    algorithm = _algorithm(algorithm_id).create({})
    results, ok = algorithm.run(
        parameters, QgsProcessingContext(), QgsProcessingFeedback(), catchExceptions=False
    )
    assert ok, f"{algorithm_id} reported failure"
    return results


@pytest.fixture(scope="module")
def documents(tmp_path_factory) -> tuple[Path, Path]:
    """An adjusted network and its solution, as the documents on disk.

    Built through the same core the levelling algorithm uses rather than by
    running that algorithm, so a failure here is about *these* algorithms.
    """
    import tests.networks as nets
    from geocomp.core.adjustment import Frame
    from geocomp.core.adjustment.least_squares import (
        AdjustmentOptions,
        adjust,
        to_observation_results,
        to_solution,
    )
    from geocomp.core.models import DatumDefinition, HeightType
    from geocomp.core.models.epoch import Epoch

    reference = nets.levelling_loop()
    run = adjust(
        reference.network,
        AdjustmentOptions(frame=Frame.HEIGHT_1D, datum=DatumDefinition.CONSTRAINED),
    )
    solution = to_solution(
        run,
        reference.network,
        solution_id="p5-chain",
        crs="EPSG:31982",
        epoch=Epoch.from_decimal_year(2026.0),
        datum=DatumDefinition.CONSTRAINED,
        height_type=HeightType.ORTHOMETRIC,
        observation_results=to_observation_results(run),
    )

    folder = tmp_path_factory.mktemp("documents")
    network_path = folder / "network.json"
    solution_path = folder / "solution.json"
    network_path.write_text(json.dumps(reference.network.to_dict()), encoding="utf-8")
    solution_path.write_text(json.dumps(solution.to_dict()), encoding="utf-8")
    return network_path, solution_path


# -- registration ---------------------------------------------------------


@pytest.mark.parametrize("algorithm_id", PROJECT_IDS)
def test_the_algorithm_is_registered(algorithm_id: str) -> None:
    algorithm = _algorithm(algorithm_id)
    assert algorithm.displayName()
    assert algorithm.shortHelpString()


@pytest.mark.parametrize("algorithm_id", PROJECT_IDS)
def test_it_appears_under_the_project_group(algorithm_id: str) -> None:
    assert _algorithm(algorithm_id).groupId() == "project"


# -- export ---------------------------------------------------------------


def test_the_csv_export_writes_the_tables(documents, tmp_path: Path) -> None:
    network_path, solution_path = documents
    folder = tmp_path / "csv"
    results = _run(
        "geocomp:project_export",
        {
            "SOLUTION": str(solution_path),
            "NETWORK": str(network_path),
            "FORMAT": 0,
            "OUTPUT_FOLDER": str(folder),
        },
    )
    written = {Path(name).name for name in results["FILES"]}
    assert {"stations.csv", "adjusted.csv", "residuals.csv", "statistics.csv"} <= written
    assert (folder / "adjusted.csv").read_text(encoding="utf-8").count("\n") > 1


def test_the_spreadsheet_export_writes_one_file(documents, tmp_path: Path) -> None:
    _network_path, solution_path = documents
    target = tmp_path / "solution.xlsx"
    results = _run(
        "geocomp:project_export",
        {"SOLUTION": str(solution_path), "FORMAT": 1, "OUTPUT_WORKBOOK": str(target)},
    )
    assert Path(results["OUTPUT_WORKBOOK"]).exists()
    # A .xlsx is a zip; the magic bytes say the writer produced one rather than
    # a file with the right extension.
    assert target.read_bytes()[:2] == b"PK"


def test_a_network_given_where_a_solution_belongs_says_so(documents, tmp_path: Path) -> None:
    """The two documents sit in the same folder, so this happens."""
    from qgis.core import QgsProcessingException

    network_path, _solution_path = documents
    with pytest.raises(QgsProcessingException) as excinfo:
        _run(
            "geocomp:project_export",
            {
                "SOLUTION": str(network_path),
                "FORMAT": 0,
                "OUTPUT_FOLDER": str(tmp_path / "out"),
            },
        )
    assert "network" in str(excinfo.value).lower()


# -- report ---------------------------------------------------------------


def test_the_report_renders_from_a_solution_document(documents, tmp_path: Path) -> None:
    network_path, solution_path = documents
    target = tmp_path / "report.html"
    results = _run(
        "geocomp:project_report",
        {
            "SOLUTION": str(solution_path),
            "NETWORK": str(network_path),
            "OUTPUT_HTML": str(target),
        },
    )
    html = Path(results["OUTPUT_HTML"]).read_text(encoding="utf-8")
    assert html.startswith("<!doctype html>")
    assert "p5-chain" in html
    assert results["OMITTED"] == []


def test_the_report_is_deterministic(documents, tmp_path: Path) -> None:
    """NFR-007. A report regenerated from a stored solution must not drift."""
    _network_path, solution_path = documents
    first = tmp_path / "a.html"
    second = tmp_path / "b.html"
    for target in (first, second):
        _run(
            "geocomp:project_report",
            {"SOLUTION": str(solution_path), "OUTPUT_HTML": str(target)},
        )
    assert first.read_bytes() == second.read_bytes()


# -- store ----------------------------------------------------------------


def test_the_store_writes_and_reads_back(documents, tmp_path: Path) -> None:
    from geocomp.io.store import open_store

    network_path, solution_path = documents
    target = tmp_path / "project.gpkg"
    results = _run(
        "geocomp:project_store",
        {
            "STORE": str(target),
            "SOLUTION": str(solution_path),
            "NETWORK": str(network_path),
            "PROJECT_ID": "chain",
        },
    )
    assert any("solution p5-chain" in line for line in results["WRITTEN"])

    with open_store(target) as store:
        project = store.read()
        assert project.id == "chain"
        assert "rd03-levelling" in project.networks
        assert [s.id for s in store.read_solutions()] == ["p5-chain"]


def test_a_second_solution_is_added_rather_than_replacing_the_project(
    documents, tmp_path: Path
) -> None:
    """The default, because the opposite mistake cannot be undone."""
    import json as _json

    from geocomp.io.store import open_store

    network_path, solution_path = documents
    target = tmp_path / "two.gpkg"
    _run(
        "geocomp:project_store",
        {"STORE": str(target), "SOLUTION": str(solution_path), "NETWORK": str(network_path)},
    )

    second = tmp_path / "solution2.json"
    payload = _json.loads(solution_path.read_text(encoding="utf-8"))
    payload["id"] = "p5-chain-2"
    second.write_text(_json.dumps(payload), encoding="utf-8")

    _run(
        "geocomp:project_store",
        {"STORE": str(target), "SOLUTION": str(second), "SUPERSEDES": "p5-chain"},
    )

    with open_store(target) as store:
        stored = {s.id: s for s in store.read_solutions()}
        assert set(stored) == {"p5-chain", "p5-chain-2"}
        # Superseded, not deleted: what was believed and when survives.
        assert stored["p5-chain"].superseded_by == "p5-chain-2"
        assert "rd03-levelling" in store.read().networks


def test_neither_document_given_is_refused(tmp_path: Path) -> None:
    from qgis.core import QgsProcessingException

    with pytest.raises(QgsProcessingException):
        _run("geocomp:project_store", {"STORE": str(tmp_path / "empty.gpkg")})


# -- base map -------------------------------------------------------------


def test_the_base_map_algorithm_adds_a_named_service(qgis_app) -> None:
    from qgis.core import QgsProject

    project = QgsProject.instance()
    project.clear()
    try:
        results = _run("geocomp:project_basemap", {"SERVICE": "osm"})
        assert results["OUTCOME"] == "added"
        assert results["SERVICE"] == "osm"
        assert len(project.mapLayers()) == 1
    finally:
        project.clear()


def test_no_configured_default_adds_nothing_rather_than_guessing(qgis_app) -> None:
    """An unset default means do not add one, not "add the first"."""
    from qgis.core import QgsProject

    project = QgsProject.instance()
    project.clear()
    try:
        results = _run("geocomp:project_basemap", {"SERVICE": ""})
        assert results["OUTCOME"] == "none"
        assert not project.mapLayers()
    finally:
        project.clear()


def test_an_unknown_service_names_the_ones_that_exist(qgis_app) -> None:
    from qgis.core import QgsProcessingException

    with pytest.raises(QgsProcessingException) as excinfo:
        _run("geocomp:project_basemap", {"SERVICE": "ortofoto-2023"})
    assert "osm" in str(excinfo.value)
