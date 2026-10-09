# SPDX-License-Identifier: GPL-2.0-or-later
"""The integration tutorial, followed as its README says (FR-952; P13-5).

GNSS and a total station adjusted together, the total station having measured
three times worse than it states. The README quotes the log's breakdown by
technique and the report's variance components; both are read here from the
run, and the components are held to the misweighting the survey was built with.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from geocomp.resources import DATASETS_DIR, available_datasets
from tests.conftest import requires_qgis
from tests.qgis.walkthrough import check_names, label, quote, quoted, run, run_logged, steps

pytestmark = [pytest.mark.qgis, requires_qgis]

NAME = "combined-curitiba"
README = DATASETS_DIR / NAME / "README.md"
INSTALL = "geocomp:project_tutorial_dataset"
PRESET = "geocomp:integration_gnss_total_station"
SHIPPED = ("README.es.md", "README.md", "README.pt_BR.md", "gnss.json", "total-station.json")


@pytest.fixture(scope="module", autouse=True)
def _registered(geocomp_provider):
    return geocomp_provider


@pytest.fixture(scope="module")
def readme() -> str:
    return README.read_text(encoding="utf-8")


class TestItNamesWhatTheDialogsShow:
    def test_it_has_two_steps_with_the_preset(self, readme):
        assert [step.algorithm_id for step in steps(readme)] == [PRESET, PRESET]

    def test_every_title_input_and_choice_is_the_dialogs(self, readme):
        check_names(readme)

    def test_the_two_runs_differ_only_in_the_components(self, readme):
        first, second = (dict(step.filled) for step in steps(readme))
        components = label(PRESET, "VARIANCE_COMPONENTS")
        assert (first.pop(components), second.pop(components)) == ("off", "on")
        assert first == second


@pytest.fixture(scope="module")
def folder(tmp_path_factory) -> Path:
    results = run(
        INSTALL,
        {
            "DATASET": available_datasets().index(NAME),
            "DESTINATION": str(tmp_path_factory.mktemp("integration-tutorial")),
        },
    )
    assert results["FILE_COUNT"] == len(SHIPPED)
    return Path(results["OUTPUT_DIRECTORY"])


def _combine(folder: Path, components: bool, tag: str = "") -> tuple[dict, str, dict]:
    import tests.combined_network as field

    results, log = run_logged(
        PRESET,
        {
            "GNSS": str(folder / "gnss.json"),
            "TOTAL_STATION": str(folder / "total-station.json"),
            "FRAME": 0,
            "FIXED_STATIONS": ",".join(field.HELD),
            "VARIANCE_COMPONENTS": components,
            "OUTPUT_SOLUTION": str(folder / f"combined-{components}{tag}.json"),
            "OUTPUT_HTML": str(folder / f"combined-{components}{tag}.html"),
        },
    )
    solution = json.loads(Path(results["OUTPUT_SOLUTION"]).read_text(encoding="utf-8"))
    return results, log, solution


@pytest.fixture(scope="module")
def stated(folder):
    return _combine(folder, False)


@pytest.fixture(scope="module")
def weighed(folder):
    return _combine(folder, True)


class TestFollowingIt:
    def test_it_installs_the_two_networks(self, folder):
        installed = sorted(path.name for path in folder.iterdir() if not path.name.startswith("combined-"))
        assert installed == sorted(SHIPPED)

    def test_the_inputs_are_what_it_says(self, readme, folder):
        gnss = json.loads((folder / "gnss.json").read_text(encoding="utf-8"))
        total_station = json.loads((folder / "total-station.json").read_text(encoding="utf-8"))
        assert (gnss["crs"], gnss["epoch"]["decimal_year"]) == ("ITRF2014", 2020.0)
        from geocomp.core.models import ObservationType

        kinds = {ObservationType[o["type"]] for o in gnss["observations"]}
        assert kinds == {ObservationType.GNSS_BASELINE, ObservationType.ELLIPSOIDAL_HEIGHT}
        assert not total_station.get("crs")
        count = len(total_station["observations"])
        quoted(readme, f"every station it can see, with one more angle and one azimuth: {count} observations")

    def test_step_1_combines_in_itrf2020_and_says_so(self, readme, stated):
        _results, log, solution = stated
        assert solution["crs"] == "ITRF2020"
        line = next(part for part in log.split(". ") if part.startswith("Combined 2 inputs"))
        quoted(readme, f"*{line}.*")

    def test_step_1_fails_and_the_breakdown_points_at_the_total_station(self, readme, stated):
        results, log, _solution = stated
        assert results["DEGREES_OF_FREEDOM"] == 41 and results["GLOBAL_TEST_PASSED"] is False
        quoted(
            readme,
            f"**{results['DEGREES_OF_FREEDOM']} degrees of freedom, and the global test fails**, "
            f"with a variance factor of **{results['VARIANCE_FACTOR_APOSTERIORI']:.2f}**",
        )
        breakdown = quote(readme)
        assert breakdown in log, (breakdown, log)
        quoted(readme, "**6.950 for the total station**, against 1.375 for the GNSS")
        assert "Total station: 44 observation(s), 79.4% of the redundancy, vᵀPv/r 6.950" in log

    def test_step_2_the_components_find_the_misweighting(self, readme, weighed):
        from tests.test_integration import TUTORIAL_NOISE

        results, log, solution = weighed
        components = solution["provenance"]["parameters"]["variance_components"]
        total_station, gnss = components["total_station"], components["gnss"]
        quoted(
            readme,
            f"a component of **{total_station['factor']:.2f} ± {total_station['std_dev']:.2f}** and the GNSS "
            f"**{gnss['factor']:.2f} ± {gnss['std_dev']:.2f}**",
        )
        scale = math.sqrt(total_station["factor"])
        made = f"{TUTORIAL_NOISE:.0f}"
        quoted(readme, f"understated by about **{scale:.1f}** times, where the survey was made with {made}")
        assert abs(total_station["factor"] - TUTORIAL_NOISE**2) < 2 * total_station["std_dev"]
        assert abs(gnss["factor"] - 1.0) < gnss["std_dev"]
        assert results["GLOBAL_TEST_PASSED"] is True
        assert results["VARIANCE_FACTOR_APOSTERIORI"] == pytest.approx(1.0, abs=1e-6)
        share = next(part for part in log.split(". ") if part.startswith("Total station:"))
        quoted(readme, f"from 79.4 % to **{share.split(', ')[1].split('%')[0]} %**")
        html = Path(results["OUTPUT_HTML"]).read_text(encoding="utf-8")
        assert "<h2>Techniques</h2>" in html and "Variance components" in html
        quoted(readme, "The report's *Techniques* section, under *Variance components*")
        assert "not its variance component" in html
        quoted(readme, "it is not yet a variance component")


@pytest.mark.parametrize("language", ("pt_BR", "es"))
class TestInEachLanguage:
    """The translations, held to GeoComp speaking their language (P13-7), as the others' are."""

    def test_every_name_it_uses_is_the_dialogs(self, language):
        from tests.qgis.test_language import _Installed

        translated = (DATASETS_DIR / NAME / f"README.{language}.md").read_text(encoding="utf-8")
        with _Installed(language):
            check_names(translated)
            components = label(PRESET, "VARIANCE_COMPONENTS")
        first, second = (dict(step.filled) for step in steps(translated))
        assert first.pop(components) != second.pop(components)
        assert first == second

    def test_it_quotes_the_log_and_the_report_in_that_language(self, language, folder):
        from geocomp.reports.adjustment import _tr
        from tests.qgis.test_language import _Installed

        translated = (DATASETS_DIR / NAME / f"README.{language}.md").read_text(encoding="utf-8")
        with _Installed(language):
            _results, log, _solution = _combine(folder, False, f"-{language}")
            results, _log, _solution = _combine(folder, True, f"-{language}")
            techniques, components = _tr("Techniques"), _tr("Variance components")
        assert techniques != "Techniques" and components != "Variance components"
        line = next(part for part in log.split(". ") if "(gnss, total_station)" in part)
        quoted(translated, f"*{line}.*")
        assert quote(translated) in log, (quote(translated), log)
        html = Path(results["OUTPUT_HTML"]).read_text(encoding="utf-8")
        assert f"<h2>{techniques}</h2>" in html and components in html
        quoted(translated, f"*{techniques}*")
        quoted(translated, f"*{components}*")
