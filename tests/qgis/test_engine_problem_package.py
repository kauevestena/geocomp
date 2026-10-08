# SPDX-License-Identifier: GPL-2.0-or-later
"""*Package an engine problem*, through Processing (FR-955; P12c-48).

The packaging itself is tier 1's (``tests/test_engine_problem_report.py``),
with a real DynAdjust failure in tier 4. This is the algorithm: what it says,
what it returns, and that a folder no engine ran in is refused against the
input it came from.
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

import pytest

from tests.conftest import requires_qgis
from tests.qgis.test_engine_runs import _feedback

pytestmark = [pytest.mark.qgis, requires_qgis]

PACKAGE = "geocomp:project_package_engine_problem"


@pytest.fixture(scope="module", autouse=True)
def _registered(geocomp_provider):
    return geocomp_provider


def _package(folder: Path, destination: Path):
    from qgis.core import QgsApplication, QgsProcessingContext

    algorithm = QgsApplication.processingRegistry().algorithmById(PACKAGE).create({})
    feedback = _feedback()
    results, ok = algorithm.run(
        {"FOLDER": str(folder), "OUTPUT": str(destination)},
        QgsProcessingContext(),
        feedback,
        catchExceptions=False,
    )
    assert ok
    return results, feedback


def test_a_failed_run_is_packaged_and_where_to_report_it_said(tmp_path):
    from geocomp.engines.base import run_process
    from geocomp.engines.report import README, UPSTREAM

    work = tmp_path / "job"
    run_process([sys.executable, "-c", "import sys; sys.exit(2)"], work_dir=work, program="dnaimport")
    results, feedback = _package(work, tmp_path / "report.zip")
    assert results["ENGINE"] == "DynAdjust"
    with zipfile.ZipFile(results["OUTPUT"]) as archive:
        assert README in archive.namelist()
    assert any(UPSTREAM["DynAdjust"] in info for info in feedback.infos), feedback.infos
    assert any("Look inside before you send it" in warning for warning in feedback.warnings)


def test_a_folder_no_engine_ran_in_is_refused_against_its_input(tmp_path):
    from qgis.core import QgsProcessingException

    with pytest.raises(QgsProcessingException, match=r"Working folder: .* holds no record of an engine run"):
        _package(tmp_path, tmp_path / "report.zip")
