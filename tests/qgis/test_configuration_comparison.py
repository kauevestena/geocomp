# SPDX-License-Identifier: GPL-2.0-or-later
"""Configurations compared side by side (FR-359, P12c-43).

``geocomp:gnss_compare_configurations`` run end to end against a stand-in for
``rnx2rtkp`` that answers every configuration with the committed solution: the
baselines are the same, so every difference is zero and nothing is significant,
which is what lets these tests read the report's shape rather than RTKLIB's
numbers. The comparison's arithmetic is tier 1's (``tests/test_gnss_comparison.py``).
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from tests.conftest import requires_qgis
from tests.qgis.test_engine_runs import RINEX, _feedback, _Rtklib
from tests.qgis.test_language import _Installed

pytestmark = [pytest.mark.qgis, requires_qgis]


@pytest.fixture(scope="module", autouse=True)
def _registered(geocomp_provider):
    return geocomp_provider


@pytest.fixture
def engine(monkeypatch):
    """The stand-in for ``rnx2rtkp``, answering every configuration with the same solution."""
    from geocomp.services import engines

    stand_in = _Rtklib()
    monkeypatch.setattr(engines, "rtklib_engine", lambda: stand_in)
    return stand_in


def _compare(tmp_path: Path, **extra):
    from qgis.core import QgsApplication, QgsProcessingContext

    folder = tmp_path / "rinex"
    folder.mkdir()
    for path in RINEX.iterdir():
        if path.is_file() and path.suffix != ".md":
            shutil.copy(path, folder)
    out = tmp_path / "out"
    out.mkdir()
    parameters = {
        "FOLDER": str(folder),
        "OUTPUT_HTML": str(out / "comparison.html"),
        "OUTPUT_CSV": str(out / "comparison.csv"),
        "OUTPUT_JSON": str(out / "comparison.json"),
        **extra,
    }
    algorithm = QgsApplication.processingRegistry().algorithmById(
        "geocomp:gnss_compare_configurations"
    ).create({})
    feedback = _feedback()
    results, ok = algorithm.run(parameters, QgsProcessingContext(), feedback, catchExceptions=False)
    assert ok
    return results, feedback, out


def _configuration(tmp_path: Path, name: str, text: str) -> str:
    path = tmp_path / f"{name}.conf"
    path.write_text(text, encoding="utf-8")
    return str(path)


class TestTheMasksSweep:
    def test_each_mask_is_a_configuration_run(self, engine, tmp_path):
        _compare(tmp_path, MASKS="15,25")
        assert [job.config.elevation_mask for job in engine.jobs] == [15.0, 25.0]

    def test_the_report_puts_them_side_by_side_the_reference_first(self, engine, tmp_path):
        results, _feedback, _out = _compare(tmp_path, MASKS="15,25")
        html = Path(results["OUTPUT_HTML"]).read_text(encoding="utf-8")
        assert "Side by side" in html
        assert html.index("mask 15° (reference)") < html.index("mask 25°")
        for row in ("Elevation mask (°)", "Difference in 3D (mm)", "Fixed epochs (%)", "Cycle slips"):
            assert row in html
        assert "not significant" in html and "No difference is significant at 95% confidence" in html

    def test_the_document_records_what_each_set_and_how_it_ran(self, engine, tmp_path):
        _results, _feedback, out = _compare(tmp_path, MASKS="15,25")
        document = json.loads((out / "comparison.json").read_text(encoding="utf-8"))
        assert document["configurations"] == {
            "mask 15°": {"elevation_mask": 15.0},
            "mask 25°": {"elevation_mask": 25.0},
        }
        assert set(document["quality"]) == {"mask 15°", "mask 25°"}
        assert document["quality"]["mask 25°"]["epochs"] > 0

    def test_the_log_says_it_in_words(self, engine, tmp_path):
        """Until P12c-43 the log showed the export's rows, header and "yes"/"no" in English."""
        _results, feedback, _out = _compare(tmp_path, MASKS="15,25")
        assert any(
            info.startswith("mask 25°: 0.0 mm in 3D from mask 15°") and info.endswith("not significant.")
            for info in feedback.infos
        ), feedback.infos
        # The export's own header, "configuration  dX mm ... significant", is not the log's.
        assert not any("dX mm" in info for info in feedback.infos)


class TestConfigurationFiles:
    def test_each_file_is_a_configuration_named_by_it(self, engine, tmp_path):
        low = _configuration(tmp_path, "low", "pos1-elmask = 10\n")
        high = _configuration(tmp_path, "high", "pos1-elmask = 20\npos2-arlockcnt = 5\n")
        results, _feedback, out = _compare(tmp_path, CONFIGURATIONS=[low, high])
        assert [job.config.elevation_mask for job in engine.jobs] == [10.0, 20.0]
        assert engine.jobs[1].config.extra["pos2-arlockcnt"] == "5"
        html = Path(results["OUTPUT_HTML"]).read_text(encoding="utf-8")
        assert html.index("low (reference)") < html.index(">high<")
        document = json.loads((out / "comparison.json").read_text(encoding="utf-8"))
        assert document["configurations"]["high"] == {
            "elevation_mask": 20.0,
            "file": high,
            "options": {"pos1-elmask": "20", "pos2-arlockcnt": "5"},
        }

    def test_one_file_alone_is_refused_against_its_input(self, engine, tmp_path):
        from qgis.core import QgsProcessingException
        only = _configuration(tmp_path, "only", "pos1-elmask = 10\n")
        with pytest.raises(QgsProcessingException, match="at least two configuration files"):
            _compare(tmp_path, CONFIGURATIONS=[only])


def test_the_report_speaks_the_language(engine, tmp_path):
    with _Installed("pt_BR") as catalogue:
        results, _feedback, _out = _compare(tmp_path, MASKS="15,25")
    html = Path(results["OUTPUT_HTML"]).read_text(encoding="utf-8")
    words = catalogue["GeoCompGnssComparison"]
    assert words["Side by side"] in html and "Side by side" not in html
