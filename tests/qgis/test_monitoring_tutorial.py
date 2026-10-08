# SPDX-License-Identifier: GPL-2.0-or-later
"""The monitoring tutorial, followed as its README says (FR-950, FR-952; P13-3).

The same discipline as the levelling tutorial's test: install ``rd08-dam`` from
the toolbox, fill in each dialog as the README's step says, and compare every
number the README quotes with what the algorithm returned. Each step's title,
every input it fills and every choice it makes from a list are held to the
dialog's own words (:mod:`tests.qgis.walkthrough`).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from geocomp.resources import DATASETS_DIR, available_datasets
from tests import monitoring_network as rd
from tests.conftest import requires_qgis
from tests.qgis.walkthrough import check_names, label, mm, option, quote, quoted, refusal, run, steps

pytestmark = [pytest.mark.qgis, requires_qgis]

NAME = "rd08-dam"
README = DATASETS_DIR / NAME / "README.md"
INSTALL = "geocomp:project_tutorial_dataset"
ADJUST = "geocomp:analysis_network_adjust"
COMPARE = "geocomp:monitoring_compare_epochs"
PILLARS = ",".join(rd.REFERENCE)
PLANE = "2D — planimetric (easting, northing)"
HELD = "Minimum constraint — over chosen stations"
FREE = "Inner constraint — free network, trace minimum"


@pytest.fixture(scope="module", autouse=True)
def _registered(geocomp_provider):
    return geocomp_provider


@pytest.fixture(scope="module")
def readme() -> str:
    return README.read_text(encoding="utf-8")


class TestItNamesWhatTheDialogsShow:
    def test_it_has_three_steps_with_algorithms(self, readme):
        assert [step.algorithm_id for step in steps(readme)] == [ADJUST, ADJUST, COMPARE]

    def test_every_title_input_and_choice_is_the_dialogs(self, readme):
        check_names(readme)

    def test_both_adjustments_are_filled_alike(self, readme):
        first, second = (dict(step.filled) for step in steps(readme)[:2])
        for name in (label(ADJUST, "FRAME"), label(ADJUST, "DATUM"), label(ADJUST, "DATUM_STATIONS")):
            assert first[name] == second[name], name
        assert first[label(ADJUST, "DATUM_STATIONS")] == f"`{PILLARS}`"

    def test_the_menu_it_names_is_where_the_algorithm_is(self, readme):
        from geocomp.gui.menu import menu_label
        from geocomp.registry import ALGORITHMS
        from tests.qgis.walkthrough import algorithm

        spec = next(spec for spec in ALGORITHMS if spec.id == COMPARE)
        quoted(readme, f"*GeoComp ▸ {menu_label(spec.menu)} ▸ {algorithm(COMPARE).displayName()}*")

    def test_the_inputs_it_names_in_passing_are_the_dialogs_too(self, readme):
        quoted(readme, f"giving the **{label(COMPARE, 'REFERENCE')}** as")
        quoted(readme, f"with *{label(ADJUST, 'DATUM')}* at *{FREE}*")
        option(ADJUST, "DATUM", FREE)


@pytest.fixture(scope="module")
def folder(tmp_path_factory) -> Path:
    results = run(
        INSTALL,
        {
            "DATASET": available_datasets().index(NAME),
            "DESTINATION": str(tmp_path_factory.mktemp("monitoring-tutorial")),
        },
    )
    assert results["FILE_COUNT"] == 4
    return Path(results["OUTPUT_DIRECTORY"])


def _adjust(folder: Path, year: int, datum: str = HELD) -> dict:
    parameters = {
        "NETWORK": str(folder / f"epoch-{year}.json"),
        "FRAME": option(ADJUST, "FRAME", PLANE),
        "DATUM": option(ADJUST, "DATUM", datum),
        "OUTPUT_SOLUTION": str(folder / f"solution-{year}-{datum[:5]}.json"),
    }
    if datum == HELD:
        parameters["DATUM_STATIONS"] = PILLARS
    results = run(ADJUST, parameters)
    results["solution"] = json.loads(Path(results["OUTPUT_SOLUTION"]).read_text(encoding="utf-8"))
    return results


def _compare(folder: Path, first: dict, second: dict, name: str, reference: str = PILLARS) -> dict:
    return {
        "FIRST": first["OUTPUT_SOLUTION"],
        "SECOND": second["OUTPUT_SOLUTION"],
        "REFERENCE": reference,
        "THRESHOLDS": str(folder / "thresholds.csv"),
        "OUTPUT_ANALYSIS": str(folder / f"{name}.json"),
        "OUTPUT_HTML": str(folder / f"{name}.html"),
    }


@pytest.fixture(scope="module")
def first(folder) -> dict:
    return _adjust(folder, 2025)


@pytest.fixture(scope="module")
def second(folder) -> dict:
    return _adjust(folder, 2026)


@pytest.fixture(scope="module")
def compared(folder, first, second) -> dict:
    results = run(COMPARE, _compare(folder, first, second, "comparison"))
    results["analysis"] = json.loads(Path(results["OUTPUT_ANALYSIS"]).read_text(encoding="utf-8"))
    results["by_station"] = {entry["station"]: entry for entry in results["analysis"]["displacements"]}
    return results


def _w_tests(adjusted: dict) -> list[dict]:
    return [result["w_test"] for result in adjusted["solution"]["observation_results"]]


class TestFollowingIt:
    def test_it_installs_the_two_epochs_and_the_thresholds(self, folder):
        assert folder.name == NAME
        assert sorted(path.name for path in folder.iterdir()) == [
            "README.md",
            "epoch-2025.json",
            "epoch-2026.json",
            "thresholds.csv",
        ]

    def test_step_1_passes_its_global_test(self, readme, first):
        assert first["DEGREES_OF_FREEDOM"] == 21
        quoted(readme, "**21 degrees of freedom.**")
        assert first["GLOBAL_TEST_PASSED"] is True
        quoted(
            readme,
            f"The global test passes, with an a-posteriori variance factor of "
            f"**{first['VARIANCE_FACTOR_APOSTERIORI']:.2f}**",
        )

    def test_step_1_flags_noise_and_rejects_nothing(self, readme, first):
        tests = _w_tests(first)
        (critical,) = {f"{test['critical_high']:.2f}" for test in tests}
        flagged = [abs(test["statistic"]) for test in tests if not test["passed"]]
        assert first["OUTLIER_COUNT"] == len(flagged)
        quoted(
            readme,
            f"Data snooping lists **{len(flagged)}** observations whose w-test exceeds the critical value "
            f"of {critical}, the largest **{max(flagged):.2f}**.",
        )
        # Nothing rejected: every one of the 36 was adjusted, flagged ones included.
        assert len(tests) == 36 and first["DEGREES_OF_FREEDOM"] == 36 - 2 * 9 + 3
        quoted(readme, "GeoComp rejects none of them")

    def test_step_2_passes_too(self, readme, second):
        assert second["GLOBAL_TEST_PASSED"] is True
        quoted(readme, f"with a variance factor of **{second['VARIANCE_FACTOR_APOSTERIORI']:.2f}**")

    def test_step_3_the_reference_block_is_stable_and_the_network_is_not(self, readme, compared):
        assert compared["REFERENCE_STABLE"] is True
        block = compared["analysis"]["reference_check"]["test"]["test"]
        assert block["passed"] is True
        quoted(
            readme,
            f"Its congruency test gives **{block['statistic']:.2f}** against a critical value of "
            f"**{block['critical_high']:.2f}**",
        )
        whole = compared["analysis"]["global_test"]["test"]
        assert compared["GLOBAL_TEST_PASSED"] is False and whole["passed"] is False
        quoted(
            readme,
            f"The whole network's gives **{whole['statistic']:.2f}** against "
            f"**{whole['critical_high']:.2f}**",
        )

    def test_step_3_finds_o2_and_only_o2(self, readme, compared):
        significant = [name for name, entry in compared["by_station"].items() if entry["significant"]]
        assert significant == ["O2"] and compared["SIGNIFICANT_COUNT"] == 1
        o2 = compared["by_station"]["O2"]
        east, north = o2["values"]
        quoted(
            readme,
            f"**Significant motion at one station: O2**, by **{mm(o2['magnitude'])} mm**, "
            f"{mm(east)} mm east and {mm(-north)} mm south.",
        )
        test = o2["test"]
        quoted(readme, f"Its test gives **{test['statistic']:.1f}** against **{test['critical_high']:.2f}**")

    def test_step_3_the_difference_from_the_truth_is_inside_the_ellipse(self, readme, compared):
        o2 = compared["by_station"]["O2"]
        moved = rd.TUTORIAL_MOTION["O2"]
        true = (moved[0] ** 2 + moved[1] ** 2) ** 0.5
        noise = mm(o2["magnitude"] - true)
        quoted(readme, f"It was moved by {mm(true)} mm; the other {noise} mm is the noise")
        ellipse = o2["ellipse"]
        quoted(readme, f"95 % ellipse of **{mm(ellipse['semi_major'])} by {mm(ellipse['semi_minor'])} mm**")
        error = ((o2["values"][0] - moved[0]) ** 2 + (o2["values"][1] - moved[1]) ** 2) ** 0.5
        assert error < ellipse["semi_minor"]

    def test_step_3_the_largest_other_displacement(self, readme, compared):
        others = {name: compared["by_station"][name] for name in rd.OBJECTS if name != "O2"}
        largest = max(others, key=lambda name: others[name]["magnitude"])
        quoted(readme, f"the largest displacement is {largest}'s **{mm(others[largest]['magnitude'])} mm**")

    def test_step_3_the_alert_is_at_o2_alone(self, readme, compared):
        crossed = sorted({alert["station"] for alert in compared["analysis"]["alerts"] if alert["exceeded"]})
        assert crossed == ["O2"] and compared["ALERT_COUNT"] == 1
        quoted(readme, f"An alert threshold: {mm(rd.TUTORIAL_THRESHOLD, 0)} mm of motion")
        quoted(readme, "The alert threshold is crossed at O2 alone.")

    def test_step_3_try_this_the_epochs_datum_does_not_matter(self, readme, folder, compared):
        epochs = (_adjust(folder, 2025, FREE), _adjust(folder, 2026, FREE))
        free = run(COMPARE, _compare(folder, *epochs, "free"))
        analysis = json.loads(Path(free["OUTPUT_ANALYSIS"]).read_text(encoding="utf-8"))
        for entry in analysis["displacements"]:
            held = compared["by_station"][entry["station"]]
            for a, b in zip(entry["values"], held["values"], strict=True):
                assert a == pytest.approx(b, abs=1e-7), entry["station"]
        quoted(readme, "The displacements come out the same, to the tenth of a micrometre.")

    def test_step_4_a_moved_pillar_is_refused_and_named(self, readme, folder, first, second):
        refused = refusal(COMPARE, _compare(folder, first, second, "refused", reference=f"{PILLARS},O2"))
        quoted(readme, f"`{PILLARS},O2`")
        assert refused.startswith(quote(readme)), refused
        assert "implicates O2" in refused
        assert "The localisation is recorded in:" in refused
        quoted(readme, "and says where it wrote the localisation.")
