# SPDX-License-Identifier: GPL-2.0-or-later
"""The GNSS sample, followed as its README says (P13-11).

``rnx2rtkp`` is tier 4, so the run here answers with the solution RTKLIB-EX
``2.5.1`` gave for this very pair, committed in ``tests/data/rtklib/pos``: the
algorithm, its log, its quality summary and its layer are GeoComp's own, and the
engine's output is the real one. ``tests/test_rtklib_engine.py`` runs the
engine itself, and checks the same 120 epochs and 117 fixed.

Holding the README to the dialogs found it stale: the log line it quoted, that
the navigation file was *paired by fallback*, had been reworded in P12c-41, and
the installer was not where it said.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from geocomp.resources import DATASETS_DIR, available_datasets
from tests.conftest import requires_qgis
from tests.qgis.walkthrough import algorithm, check_names, quoted, quotes, run, run_logged, steps

pytestmark = [pytest.mark.qgis, requires_qgis]

NAME = "rtklib-sample"
README = DATASETS_DIR / NAME / "README.md"
INSTALL = "geocomp:project_tutorial_dataset"
STATIC = "geocomp:gnss_relative_static"
SHIPPED = (
    "07590920.05o",
    "30400920.05o",
    "README.es.md",
    "README.md",
    "README.pt_BR.md",
    "RTKLIB-license.txt",
    "brdc_0759.05n.gz",
)
SUMMARY = re.compile(r"(\d+) epochs, ([\d.]+)% with resolved ambiguities")


@pytest.fixture(scope="module", autouse=True)
def _registered(geocomp_provider):
    return geocomp_provider


@pytest.fixture(scope="module")
def readme() -> str:
    return README.read_text(encoding="utf-8")


def _menu(algorithm_id: str) -> str:
    from geocomp.gui.menu import menu_label
    from geocomp.registry import ALGORITHMS

    spec = next(spec for spec in ALGORITHMS if spec.id == algorithm_id)
    return f"GeoComp ▸ {menu_label(spec.menu)}"


def _follow(folder: Path, language: str | None = None) -> tuple[str, dict]:
    """Step 2 with the engine standing in, in *language* when one is given."""
    from geocomp.services import engines
    from tests.qgis.test_engine_runs import _Rtklib

    out = folder.parent / f"out-{language or 'en'}"
    out.mkdir()
    parameters = {
        "FOLDER": str(folder),
        "BASE_STATION": "3040",
        "ROVER_STATION": "0759",
        "OUTPUT_POS": str(out / "solution.pos"),
        "OUTPUT_JSON": str(out / "quality.json"),
    }
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(engines, "rtklib_engine", _Rtklib)
        if language:
            from tests.qgis.test_language import _Installed

            with _Installed(language):
                _results, log = run_logged(STATIC, parameters)
        else:
            _results, log = run_logged(STATIC, parameters)
    return log, json.loads((out / "quality.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def folder(tmp_path_factory) -> Path:
    results = run(
        INSTALL,
        {
            "DATASET": available_datasets().index(NAME),
            "DESTINATION": str(tmp_path_factory.mktemp("gnss-sample")),
        },
    )
    assert results["FILE_COUNT"] == len(SHIPPED)
    return Path(results["OUTPUT_DIRECTORY"])


@pytest.fixture(scope="module")
def followed(folder):
    return _follow(folder)


class TestItNamesWhatTheDialogsShow:
    def test_it_has_the_two_steps(self, readme):
        assert [step.algorithm_id for step in steps(readme)] == [INSTALL, STATIC]

    def test_every_title_input_and_choice_is_the_dialogs(self, readme):
        check_names(readme)

    def test_it_says_where_each_is_in_the_menu(self, readme):
        quoted(readme, f"*{_menu(INSTALL)}*")
        quoted(readme, f"*{_menu(STATIC)} ▸ {algorithm(STATIC).displayName()}*")


class TestFollowingIt:
    def test_it_installs_the_session_and_its_licence(self, folder):
        assert sorted(path.name for path in folder.iterdir()) == sorted(SHIPPED)

    def test_the_log_says_what_it_quotes(self, readme, followed):
        log, _quality = followed
        said = quotes(readme)
        assert len(said) == 3
        for quote in said:
            assert quote in log, (quote, log)

    def test_the_epochs_are_the_ones_it_states(self, readme, followed):
        log, quality = followed
        epochs, percent = SUMMARY.search(log).groups()
        assert f"{epochs} epochs, {percent}% with resolved ambiguities" in quotes(readme)
        fixed = round(int(epochs) * float(percent) / 100)
        quoted(readme, f"**{epochs} epochs** over the first hour")
        quoted(readme, f"**{fixed} of them with the ambiguities fixed** and three float")
        assert int(epochs) - fixed == 3
        assert json.dumps(quality)  # the summary was written

    def test_it_names_the_engine_it_used(self, readme, followed):
        log, _quality = followed
        assert "Using RTKLIB-EX 2.5.1 from" in log
        quoted(readme, "*Using RTKLIB-EX* `2.5.1`")


@pytest.mark.parametrize("language", ("pt_BR", "es"))
class TestInEachLanguage:
    """The translations, held to GeoComp speaking their language (P13-11), as the others' are."""

    def test_every_name_it_uses_is_the_dialogs(self, language):
        from tests.qgis.test_language import _Installed

        translated = README.with_name(f"README.{language}.md").read_text(encoding="utf-8")
        with _Installed(language):
            check_names(translated)
            quoted(translated, f"*{_menu(INSTALL)}*")
            quoted(translated, f"*{_menu(STATIC)} ▸ {algorithm(STATIC).displayName()}*")

    def test_it_quotes_the_log_in_that_language(self, language, folder):
        translated = README.with_name(f"README.{language}.md").read_text(encoding="utf-8")
        log, _quality = _follow(folder, language)
        said = quotes(translated)
        assert len(said) == 3
        for quote in said:
            assert quote in log, (quote, log)
