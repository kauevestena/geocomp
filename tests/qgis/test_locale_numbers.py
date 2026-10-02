# SPDX-License-Identifier: GPL-2.0-or-later
"""Numbers for people in the language's separator, files in a point (specs/18 criteria 5 and 6).

FR-094: a report in Portuguese or Spanish writes a decimal comma. FR-095: no
file does, whatever the language. ``specs/18`` §5 asks for the second as a
test that "writes every output format under a comma-decimal locale and reads
it back under a period-decimal one". These run RD-01's whole chain in English,
then again in Brazilian Portuguese and in Spanish, each time with all of these
set to the language:

* Qt's default locale;
* GeoComp's display language;
* Python's numeric locale, where the system has one to set.

Every file a person does not read must come out the same, and must read back
in English. Every number in every table of a report must change its
separator and nothing else.
"""

from __future__ import annotations

import contextlib
import json
import locale
import re
from pathlib import Path

import pytest

from tests import reference_rd01 as rd01
from tests.conftest import requires_qgis

pytestmark = [pytest.mark.qgis, requires_qgis]

DECIMAL = re.compile(r"^-?\d+\.\d+(e[-+]\d+)?$")
CELL = re.compile(r"<td[^>]*>(.*?)</td>", re.S)


@contextlib.contextmanager
def _everything_in(name: str):
    """Qt's locale, GeoComp's display language, and Python's numbers where it can."""
    from qgis.PyQt.QtCore import QLocale

    from geocomp.core.number_format import set_display_locale

    previous_qt = QLocale()
    previous_python = locale.setlocale(locale.LC_NUMERIC)
    QLocale.setDefault(QLocale(name))
    set_display_locale(name)
    with contextlib.suppress(locale.Error):
        locale.setlocale(locale.LC_NUMERIC, f"{name}.UTF-8")
    try:
        yield
    finally:
        QLocale.setDefault(previous_qt)
        set_display_locale("en")
        locale.setlocale(locale.LC_NUMERIC, previous_python)


def _run(algorithm_id: str, parameters: dict) -> dict:
    from qgis.core import QgsApplication, QgsProcessingContext, QgsProcessingFeedback

    algorithm = QgsApplication.processingRegistry().algorithmById(algorithm_id).create({})
    results, ok = algorithm.run(
        parameters, QgsProcessingContext(), QgsProcessingFeedback(), catchExceptions=False
    )
    assert ok, algorithm_id
    return results


def _chain(directory: Path) -> Path:
    """RD-01 from the field book to a stored project and an export, every output to *directory*."""
    directory.mkdir()
    imported = _run(
        "geocomp:totalstation_import_fieldbook",
        {
            "SOURCE": str(rd01.RAW),
            "SIGMA_DIRECTION": rd01.SIGMA_ANGLE,
            "SIGMA_ZENITH": rd01.SIGMA_ANGLE,
            "SIGMA_DISTANCE": 0.002,
            "OUTPUT_READINGS": str(directory / "readings.json"),
            "OUTPUT_HTML": str(directory / "import.html"),
            "OUTPUT_FINDINGS": str(directory / "findings.csv"),
        },
    )
    reduced = _run(
        "geocomp:totalstation_preprocess",
        {
            "READINGS": imported["OUTPUT_READINGS"],
            "APPLY_ATMOSPHERIC": False,
            "OUTPUT_REDUCED": str(directory / "reduced.json"),
            "OUTPUT_HTML": str(directory / "preprocess.html"),
            "OUTPUT_CSV": str(directory / "reduced.csv"),
        },
    )
    approximate = directory / "approximate.json"
    approximate.write_text(json.dumps(rd01.approximate_coordinates()), encoding="utf-8")
    adjusted = _run(
        "geocomp:totalstation_network",
        {
            "REDUCTIONS": reduced["OUTPUT_REDUCED"],
            "APPROXIMATE": str(approximate),
            "DIMENSION": 0,
            "DATUM": 1,
            "CRS": "EPSG:31982",
            "OUTPUT_NETWORK": str(directory / "network.json"),
            "OUTPUT_SOLUTION": str(directory / "solution.json"),
            "OUTPUT_HTML": str(directory / "network.html"),
            "OUTPUT_STATIONS": str(directory / "stations.csv"),
        },
    )
    _run(
        "geocomp:project_export",
        {
            "SOLUTION": adjusted["OUTPUT_SOLUTION"],
            "FORMAT": 0,
            "OUTPUT_FOLDER": str(directory / "export"),
        },
    )
    _run(
        "geocomp:project_report",
        {"SOLUTION": adjusted["OUTPUT_SOLUTION"], "OUTPUT_HTML": str(directory / "report.html")},
    )
    return directory


@pytest.fixture(scope="module")
def english(geocomp_provider, tmp_path_factory):
    return _chain(tmp_path_factory.mktemp("locale-en") / "run")


@pytest.fixture(scope="module", params=["pt_BR", "es"])
def runs(request, english, tmp_path_factory):
    """English, and the same chain in a language that writes a decimal comma."""
    with _everything_in(request.param):
        other = _chain(tmp_path_factory.mktemp(f"locale-{request.param}") / "run")
    return english, other


def _files(directory: Path) -> dict[str, Path]:
    return {
        str(path.relative_to(directory)): path for path in sorted(directory.rglob("*")) if path.is_file()
    }


def _without_provenance(payload):
    if isinstance(payload, dict):
        return {k: _without_provenance(v) for k, v in payload.items() if k != "provenance"}
    if isinstance(payload, list):
        return [_without_provenance(v) for v in payload]
    return payload


class TestFilesKeepAPoint:
    """FR-095, specs/18 criterion 5."""

    def test_every_file_a_person_does_not_read_is_the_same(self, runs):
        english, portuguese = runs
        ours, theirs = _files(english), _files(portuguese)
        assert ours.keys() == theirs.keys()
        compared = 0
        for name, path in ours.items():
            if path.suffix == ".html":
                continue
            if path.suffix == ".json":
                assert _without_provenance(
                    json.loads(theirs[name].read_text(encoding="utf-8"))
                ) == _without_provenance(json.loads(path.read_text(encoding="utf-8"))), name
            else:
                assert theirs[name].read_bytes() == path.read_bytes(), name
            compared += 1
        assert compared >= 8, "the chain wrote fewer files than it should"

    def test_what_was_written_in_portuguese_reads_back_in_english(self, runs):
        from geocomp.core.models import Solution

        english, portuguese = runs
        solution = Solution.from_dict(
            json.loads((portuguese / "solution.json").read_text(encoding="utf-8"))
        )
        reference = Solution.from_dict(
            json.loads((english / "solution.json").read_text(encoding="utf-8"))
        )
        def coordinates(found):
            return [[q.value for q in s.position.values] for s in found.adjusted_stations]

        assert coordinates(solution) == coordinates(reference)


class TestReportsUseTheComma:
    """FR-094, specs/18 criterion 6 and specs/19 criterion 7."""

    @pytest.mark.parametrize("report", ["import.html", "preprocess.html", "network.html", "report.html"])
    def test_every_number_in_every_table_changes_its_separator_and_nothing_else(
        self, runs, report
    ):
        english, portuguese = runs
        ours = CELL.findall((english / report).read_text(encoding="utf-8"))
        theirs = CELL.findall((portuguese / report).read_text(encoding="utf-8"))
        assert len(ours) == len(theirs)
        numbers = 0
        for a, b in zip(ours, theirs, strict=True):
            if DECIMAL.match(a.strip()):
                assert b.strip() == a.strip().replace(".", ","), (a, b)
                numbers += 1
        assert numbers > 0 or report == "import.html"

    def test_the_english_report_still_has_points(self, english):
        cells = CELL.findall((english / "network.html").read_text(encoding="utf-8"))
        assert any(DECIMAL.match(cell.strip()) for cell in cells)
