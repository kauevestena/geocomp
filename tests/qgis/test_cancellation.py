# SPDX-License-Identifier: GPL-2.0-or-later
"""A cancelled run leaves no partial output (specs/16 criterion 8; specs/17 criterion 6).

Before P12c, 13 of the 46 algorithms looked at the cancel button, each returned
an empty result from wherever it noticed, and Processing reported success. What
had been written by then stayed. :mod:`geocomp.algorithms.transaction` now holds
the rule around every algorithm. These tests cancel at the worst moment: after
the files are written and before the run returns. A file the run would have
replaced must come back unchanged, and a file it created must be gone.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests import reference_rd01 as rd01
from tests.conftest import requires_qgis

pytestmark = [pytest.mark.qgis, requires_qgis]

BEFORE = '{"written": "before the run"}'


def _feedback(*, at: int | None = None):
    """A feedback cancelled from the start, or once progress reaches *at*."""
    from qgis.core import QgsProcessingFeedback

    class CancelAt(QgsProcessingFeedback):
        def setProgress(self, progress):  # noqa: N802 -- the Qt interface
            super().setProgress(progress)
            if at is not None and progress >= at:
                self.cancel()

    feedback = CancelAt()
    if at is None:
        feedback.cancel()
    return feedback


def _run(algorithm_id: str, parameters: dict, feedback=None):
    from qgis.core import QgsApplication, QgsProcessingContext, QgsProcessingFeedback

    algorithm = QgsApplication.processingRegistry().algorithmById(algorithm_id).create({})
    results, ok = algorithm.run(
        parameters,
        QgsProcessingContext(),
        feedback or QgsProcessingFeedback(),
        catchExceptions=False,
    )
    assert ok
    return results


def _cancelled(algorithm_id: str, parameters: dict, feedback) -> str:
    from qgis.core import QgsProcessingException

    with pytest.raises(QgsProcessingException) as caught:
        _run(algorithm_id, parameters, feedback)
    return str(caught.value)


@pytest.fixture(scope="module")
def reduced(geocomp_provider, tmp_path_factory) -> dict[str, str]:
    """RD-01 imported and reduced, run normally: the inputs the network needs."""
    directory = tmp_path_factory.mktemp("rd01-inputs")
    imported = _run(
        "geocomp:totalstation_import_fieldbook",
        {
            "SOURCE": str(rd01.RAW),
            "SIGMA_DIRECTION": rd01.SIGMA_ANGLE,
            "SIGMA_ZENITH": rd01.SIGMA_ANGLE,
            "SIGMA_DISTANCE": 0.002,
            "OUTPUT_READINGS": str(directory / "readings.json"),
        },
    )
    reduction = _run(
        "geocomp:totalstation_preprocess",
        {
            "READINGS": imported["OUTPUT_READINGS"],
            "APPLY_ATMOSPHERIC": False,
            "OUTPUT_REDUCED": str(directory / "reduced.json"),
        },
    )
    approximate = directory / "approximate.json"
    approximate.write_text(json.dumps(rd01.approximate_coordinates()), encoding="utf-8")
    return {
        "readings": imported["OUTPUT_READINGS"],
        "reduced": reduction["OUTPUT_REDUCED"],
        "approximate": str(approximate),
    }


def test_every_algorithm_runs_inside_the_transaction(geocomp_provider):
    """The rule is applied when a class is defined, so none can be without it."""
    from qgis.core import QgsApplication

    from geocomp.registry import ALGORITHMS

    registry = QgsApplication.processingRegistry()
    outside = [
        spec.id
        for spec in ALGORITHMS
        if not getattr(
            type(registry.algorithmById(spec.id)).processAlgorithm,
            "_geocomp_transactional",
            False,
        )
    ]
    assert len(ALGORITHMS) == 49
    assert not outside


class TestCancelledAfterWriting:
    """The adjustment writes four files and is cancelled as it reports 100%."""

    @pytest.fixture
    def outputs(self, tmp_path) -> dict[str, Path]:
        existing = tmp_path / "solution.json"
        existing.write_text(BEFORE, encoding="utf-8")
        return {
            "OUTPUT_SOLUTION": existing,
            "OUTPUT_NETWORK": tmp_path / "network.json",
            "OUTPUT_HTML": tmp_path / "network.html",
            "OUTPUT_STATIONS": tmp_path / "stations.csv",
        }

    def _parameters(self, reduced, outputs) -> dict:
        return {
            "REDUCTIONS": reduced["reduced"],
            "APPROXIMATE": reduced["approximate"],
            "DIMENSION": 0,
            "DATUM": 1,
            "CRS": "EPSG:31982",
            **{name: str(path) for name, path in outputs.items()},
        }

    def test_a_file_it_replaced_comes_back_and_the_ones_it_made_go(self, reduced, outputs):
        message = _cancelled(
            "geocomp:totalstation_network", self._parameters(reduced, outputs), _feedback(at=100)
        )
        assert "Cancelled" in message
        assert outputs["OUTPUT_SOLUTION"].read_text(encoding="utf-8") == BEFORE
        for name in ("OUTPUT_NETWORK", "OUTPUT_HTML", "OUTPUT_STATIONS"):
            assert not outputs[name].exists(), name

    def test_the_same_run_not_cancelled_writes_everything(self, reduced, outputs):
        """The control: what the cancelled run took away was written."""
        _run("geocomp:totalstation_network", self._parameters(reduced, outputs))
        assert outputs["OUTPUT_SOLUTION"].read_text(encoding="utf-8") != BEFORE
        assert all(path.is_file() for path in outputs.values())


def test_an_algorithm_that_noticed_no_longer_reports_success(reduced, tmp_path):
    """Pre-processing returned an empty result when it saw the button, and
    Processing called that a completed run."""
    target = tmp_path / "reduced.json"
    message = _cancelled(
        "geocomp:totalstation_preprocess",
        {"READINGS": reduced["readings"], "OUTPUT_REDUCED": str(target)},
        _feedback(),
    )
    assert "Cancelled" in message
    assert not target.exists()


def test_a_cancelled_import_leaves_its_target_unchanged(geocomp_provider, tmp_path):
    """specs/17 criterion 6."""
    target = tmp_path / "readings.json"
    target.write_text(BEFORE, encoding="utf-8")
    report = tmp_path / "import.html"
    _cancelled(
        "geocomp:totalstation_import_fieldbook",
        {
            "SOURCE": str(rd01.RAW),
            "SIGMA_DIRECTION": rd01.SIGMA_ANGLE,
            "SIGMA_ZENITH": rd01.SIGMA_ANGLE,
            "SIGMA_DISTANCE": 0.002,
            "OUTPUT_READINGS": str(target),
            "OUTPUT_HTML": str(report),
        },
        _feedback(at=100),
    )
    assert target.read_text(encoding="utf-8") == BEFORE
    assert not report.exists()


def test_a_cancelled_save_leaves_the_project_as_it_was(reduced, tmp_path):
    """Saving a network and its solution into a project that already holds one."""
    from geocomp.io.store import open_store

    directory = tmp_path / "run"
    directory.mkdir()
    solved = _run(
        "geocomp:totalstation_network",
        {
            "REDUCTIONS": reduced["reduced"],
            "APPROXIMATE": reduced["approximate"],
            "DIMENSION": 0,
            "DATUM": 1,
            "CRS": "EPSG:31982",
            "OUTPUT_NETWORK": str(directory / "network.json"),
            "OUTPUT_SOLUTION": str(directory / "solution.json"),
        },
    )
    project = tmp_path / "project.gpkg"
    save = {
        "STORE": str(project),
        "NETWORK": solved["OUTPUT_NETWORK"],
        "SOLUTION": solved["OUTPUT_SOLUTION"],
    }
    _run("geocomp:project_store", save)
    with open_store(project) as store:
        before = (store.revision, [entry.id for entry in store.read_solutions()])

    second = json.loads(Path(solved["OUTPUT_SOLUTION"]).read_text(encoding="utf-8"))
    second["id"] = "the-second-solution"
    again = directory / "second.json"
    again.write_text(json.dumps(second), encoding="utf-8")
    _cancelled("geocomp:project_store", {**save, "SOLUTION": str(again)}, _feedback())

    with open_store(project) as store:
        assert (store.revision, [entry.id for entry in store.read_solutions()]) == before
