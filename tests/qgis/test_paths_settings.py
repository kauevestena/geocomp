# SPDX-License-Identifier: GPL-2.0-or-later
"""Working directories and report templates are Global Settings (FR-066; P12c-46).

Until P12c-46 they were each algorithm's parameters and nothing else: an
engine's working files went to the system's temporary directory unless a run
named a folder, and an organisation's report template had to be chosen on every
run. Both are now settings under *Paths and engines*, and a run that names its
own still wins.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import tests.qgis.test_engine_runs as engine_runs
from tests.conftest import requires_qgis

pytestmark = [pytest.mark.qgis, requires_qgis]


@pytest.fixture(scope="module", autouse=True)
def _registered(geocomp_provider):
    return geocomp_provider


@pytest.fixture
def global_setting():
    """Set a global-only setting for one test, and put it back after."""
    from geocomp.services.settings_service import settings

    touched = []

    def put(key: str, value: str) -> None:
        touched.append(key)
        settings.set_global(key, value)

    yield put
    for key in touched:
        settings.reset_global(key)


def _prepare(store: Path, monkeypatch, **extra) -> dict:
    """DynAdjust stopped before running, on *store*'s network: no program is needed."""
    from qgis.core import QgsApplication, QgsProcessingContext

    from geocomp.algorithms.engines import dynadjust_adjust

    stand_in = engine_runs._NeverDetected()
    monkeypatch.setattr(dynadjust_adjust, "dynadjust_engine", lambda directory=None: stand_in)
    algorithm = QgsApplication.processingRegistry().algorithmById(
        "geocomp:analysis_dynadjust_adjust"
    ).create({})
    results, ok = algorithm.run(
        {"STORE": str(store), "FRAME": "GDA2020", "EPOCH": 2020.0, "STOP_BEFORE_RUNNING": True, **extra},
        QgsProcessingContext(),
        engine_runs._feedback(),
        catchExceptions=False,
    )
    assert ok
    return results


class TestTheWorkingDirectory:
    def test_an_engines_files_go_under_it(self, tmp_path, monkeypatch, global_setting):
        store = engine_runs.TestFromTheProjectStore._store(tmp_path, "sample")
        working = tmp_path / "engines" / "work"
        global_setting("paths.working_directory", str(working))
        job = Path(_prepare(store, monkeypatch)["OUTPUT_WORK_DIR"])
        assert job.parent == working and job.name.startswith("geocomp-dynadjust-")
        assert any(job.glob("*-msr.xml"))

    def test_a_folder_the_run_names_still_wins(self, tmp_path, monkeypatch, global_setting):
        store = engine_runs.TestFromTheProjectStore._store(tmp_path, "sample")
        named = tmp_path / "this-run"
        global_setting("paths.working_directory", str(tmp_path / "engines"))
        job = Path(_prepare(store, monkeypatch, OUTPUT_WORK_DIR=str(named))["OUTPUT_WORK_DIR"])
        assert job == named
        assert not (tmp_path / "engines").exists()

    def test_one_that_cannot_be_written_in_is_refused_by_name(self, tmp_path, monkeypatch, global_setting):
        from qgis.core import QgsProcessingException

        store = engine_runs.TestFromTheProjectStore._store(tmp_path, "sample")
        blocker = tmp_path / "a-file"
        blocker.write_text("not a folder", encoding="utf-8")
        unusable = blocker / "work"
        global_setting("paths.working_directory", str(unusable))
        with pytest.raises(QgsProcessingException, match="set in Global Settings cannot be written in"):
            _prepare(store, monkeypatch)

    def test_empty_is_the_systems_temporary_directory(self, tmp_path, monkeypatch, global_setting):
        import tempfile

        store = engine_runs.TestFromTheProjectStore._store(tmp_path, "sample")
        global_setting("paths.working_directory", "")
        job = Path(_prepare(store, monkeypatch)["OUTPUT_WORK_DIR"])
        assert job.parent == Path(tempfile.gettempdir())


class TestTheReportTemplates:
    """The monitoring report, and the comparison's own, from the organisation's folder."""

    @pytest.fixture
    def organisation(self, tmp_path) -> Path:
        folder = tmp_path / "templates"
        folder.mkdir()
        (folder / "monitoring.html").write_text(
            "<html><body><h1>Acme Monitoring</h1>{{title}}{{displacements}}</body></html>", encoding="utf-8"
        )
        return folder

    @staticmethod
    def _analysis(tmp_path: Path, **outputs) -> dict:
        from tests.monitoring_network import REFERENCE, epoch
        from tests.qgis.test_monitoring_algorithms import COMPARE, _run

        first, second = tmp_path / "first.json", tmp_path / "second.json"
        first.write_text(json.dumps(epoch(2025.0, seed=1).to_dict()), encoding="utf-8")
        moved = epoch(2026.0, moves={"O2": (0.008, -0.006)}, seed=2)
        second.write_text(json.dumps(moved.to_dict()), encoding="utf-8")
        results, _ = _run(
            COMPARE,
            {"FIRST": str(first), "SECOND": str(second), "REFERENCE": ",".join(REFERENCE), **outputs},
        )
        return results

    def test_the_comparisons_report_uses_it(self, tmp_path, organisation, global_setting):
        global_setting("paths.report_templates", str(organisation))
        results = self._analysis(
            tmp_path, OUTPUT_ANALYSIS=str(tmp_path / "a.json"), OUTPUT_HTML=str(tmp_path / "a.html")
        )
        assert "Acme Monitoring" in Path(results["OUTPUT_HTML"]).read_text(encoding="utf-8")

    def test_the_monitoring_report_uses_it_unless_the_run_names_one(
        self, tmp_path, organisation, global_setting
    ):
        from tests.qgis.test_monitoring_algorithms import _run

        self._analysis(tmp_path, OUTPUT_ANALYSIS=str(tmp_path / "a.json"))
        own = tmp_path / "own.html"
        own.write_text("<html><body><h1>This run's</h1>{{title}}</body></html>", encoding="utf-8")
        global_setting("paths.report_templates", str(organisation))
        configured, _ = _run(
            "geocomp:monitoring_report",
            {"ANALYSIS": str(tmp_path / "a.json"), "OUTPUT_HTML": str(tmp_path / "configured.html")},
        )
        named, _ = _run(
            "geocomp:monitoring_report",
            {
                "ANALYSIS": str(tmp_path / "a.json"),
                "TEMPLATE": str(own),
                "OUTPUT_HTML": str(tmp_path / "named.html"),
            },
        )
        assert "Acme Monitoring" in Path(configured["OUTPUT_HTML"]).read_text(encoding="utf-8")
        named_html = Path(named["OUTPUT_HTML"]).read_text(encoding="utf-8")
        assert "This run's" in named_html and "Acme Monitoring" not in named_html

    def test_a_folder_without_the_template_falls_back_to_the_shipped_one(self, tmp_path, global_setting):
        empty = tmp_path / "empty"
        empty.mkdir()
        global_setting("paths.report_templates", str(empty))
        results = self._analysis(
            tmp_path, OUTPUT_ANALYSIS=str(tmp_path / "a.json"), OUTPUT_HTML=str(tmp_path / "a.html")
        )
        html = Path(results["OUTPUT_HTML"]).read_text(encoding="utf-8")
        assert "Displacements" in html and "Acme" not in html
