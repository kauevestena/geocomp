# SPDX-License-Identifier: GPL-2.0-or-later
"""The levelling tutorial, followed as its README says (FR-950, FR-952; P13-2).

``tests/test_tutorial_dataset.py`` checks the shipped files without QGIS. This
does what a reader does: installs ``rd04-loop`` from the toolbox, fills in each
dialog as the README's step says, and gets the numbers the README quotes --
every one of them, read out of the README and compared with what the algorithm
returned, so a change that moves a number fails here rather than in front of a
student.

The README names the dialogs too: each step's title, and the label of every
input it tells the reader to fill. As first written it called two of them by
names they do not have ("Reductions" for *Reduced lines*, "Network adjustment"
for *Levelling network adjustment*), which a reader searching the toolbox would
not have found. So the labels are checked against the dialogs as well.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from geocomp.resources import DATASETS_DIR, available_datasets
from tests.conftest import requires_qgis
from tests.qgis.walkthrough import check_names, label, mm, quote, quoted, refusal, run, steps

pytestmark = [pytest.mark.qgis, requires_qgis]

NAME = "rd04-loop"
README = DATASETS_DIR / NAME / "README.md"
INSTALL = "geocomp:project_tutorial_dataset"


@pytest.fixture(scope="module", autouse=True)
def _registered(geocomp_provider):
    return geocomp_provider


@pytest.fixture(scope="module")
def readme() -> str:
    return README.read_text(encoding="utf-8")


class TestItNamesWhatTheDialogsShow:
    def test_it_has_the_four_steps_with_algorithms(self, readme):
        assert [step.algorithm_id for step in steps(readme)] == [
            "geocomp:levelling_import",
            "geocomp:levelling_equal_sights",
            "geocomp:levelling_closures",
            "geocomp:levelling_network",
        ]

    def test_every_title_input_and_choice_is_the_dialogs(self, readme):
        check_names(readme)

    def test_the_inputs_it_names_in_passing_are_the_dialogs_too(self, readme):
        network = "geocomp:levelling_network"
        quoted(readme, f"giving the **{label(network, 'BENCHMARKS')}** as")
        quoted(readme, f"turn on *{label(network, 'ADJUST_FAILING')}*")


class TestFollowingIt:
    """Install, then the five steps in order, each step's output the next one's input."""

    @pytest.fixture(scope="class")
    def folder(self, tmp_path_factory) -> Path:
        results = run(
            INSTALL,
            {
                "DATASET": available_datasets().index(NAME),
                "DESTINATION": str(tmp_path_factory.mktemp("levelling-tutorial")),
            },
        )
        assert results["FILE_COUNT"] == 4
        return Path(results["OUTPUT_DIRECTORY"])

    def test_it_installs_into_a_folder_of_its_own(self, folder):
        assert folder.name == NAME
        assert sorted(path.name for path in folder.iterdir()) == [
            "README.md",
            "loop.csv",
            "mapping.json",
            "profiles.json",
        ]

    @pytest.fixture(scope="class")
    def imported(self, folder) -> dict:
        return run(
            "geocomp:levelling_import",
            {
                "BOOK": str(folder / "loop.csv"),
                "MAPPING": str(folder / "mapping.json"),
                "PROFILES": str(folder / "profiles.json"),
                "OUTPUT_SETUPS": str(folder / "setups.json"),
            },
        )

    def test_step_1_reads_ten_setups_in_three_lines(self, readme, imported):
        quoted(readme, "Ten setups in three lines, no row rejected.")
        assert (imported["SETUP_COUNT"], imported["LINE_COUNT"]) == (10, 3)
        assert imported["REJECTED_ROWS"] == 0

    @pytest.fixture(scope="class")
    def reduced(self, folder, imported) -> dict:
        return run(
            "geocomp:levelling_equal_sights",
            {
                "SETUPS": imported["OUTPUT_SETUPS"],
                "PROFILES": str(folder / "profiles.json"),
                "OUTPUT_REDUCTIONS": str(folder / "reduced.json"),
            },
        )

    def test_step_2_balances_every_line_and_quotes_the_worst(self, readme, reduced):
        assert reduced["LINE_COUNT"] == 3
        assert reduced["WORST_IMBALANCE"] == pytest.approx(0.0, abs=1e-9)
        quoted(readme, f"the worst line, BM2 to BM4, carries {mm(reduced['WORST_UNCERTAINTY'])} mm")
        lines = json.loads(Path(reduced["OUTPUT_REDUCTIONS"]).read_text(encoding="utf-8"))["lines"]
        worst = max(lines, key=lambda line: line["height_difference"]["variance"])
        assert (worst["from_station"], worst["to_station"]) == ("BM2", "BM4")

    def _closure(self, folder, reduced, coefficient: float) -> dict:
        return run(
            "geocomp:levelling_closures",
            {
                "REDUCTIONS": reduced["OUTPUT_REDUCTIONS"],
                "MODE": 0,
                "TOLERANCE_COEFFICIENT": coefficient,
                "OUTPUT_CLOSURES": str(folder / f"closure-{coefficient}.json"),
            },
        )

    def test_step_3_the_loop_fails_by_what_it_says(self, readme, folder, reduced):
        closure = self._closure(folder, reduced, 0.008)
        assert closure["PASSED"] == 0
        quoted(
            readme,
            f"They sum to **{mm(closure['MISCLOSURE'])} mm**, against a permissible "
            f"**{mm(closure['PERMISSIBLE'])} mm**",
        )
        length = (closure["PERMISSIBLE"] / 0.008) ** 2
        quoted(readme, f"for the loop's {length:.2f} km. **The loop fails.**")

    def test_step_3_without_a_tolerance_there_is_no_verdict(self, readme, folder, reduced):
        judged = self._closure(folder, reduced, 0.008)
        unjudged = self._closure(folder, reduced, 0.0)
        assert unjudged["MISCLOSURE"] == judged["MISCLOSURE"]
        assert unjudged["PASSED"] == -1
        quoted(readme, "there is no verdict, neither passed nor failed")

    def _network(self, folder, reduced, benchmarks: str, name: str, **extra) -> dict:
        return {
            "REDUCTIONS": reduced["OUTPUT_REDUCTIONS"],
            "BENCHMARKS": benchmarks,
            "TOLERANCE_COEFFICIENT": 0.008,
            "SIGMA_PER_KM": 0.0007,
            "OUTPUT_SOLUTION": str(folder / f"{name}.json"),
            "OUTPUT_CSV": str(folder / f"{name}.csv"),
            **extra,
        }

    @pytest.fixture(scope="class")
    def held_at_bm1(self, folder, reduced) -> dict:
        results = run("geocomp:levelling_network", self._network(folder, reduced, "BM1=100.000", "bm1"))
        results["solution"] = json.loads(Path(results["OUTPUT_SOLUTION"]).read_text(encoding="utf-8"))
        return results

    def test_step_4_one_degree_of_freedom_and_a_failed_global_test(self, readme, held_at_bm1):
        assert held_at_bm1["DEGREES_OF_FREEDOM"] == 1
        quoted(readme, "**one degree of freedom.**")
        assert held_at_bm1["GLOBAL_TEST_PASSED"] is False
        quoted(
            readme,
            f"The global test fails, with an a-posteriori variance factor of "
            f"**{held_at_bm1['VARIANCE_FACTOR_APOSTERIORI']:.0f}**",
        )

    def test_step_4_every_line_scores_the_same_and_none_is_named(self, readme, held_at_bm1):
        assert held_at_bm1["OUTLIER_COUNT"] == 0
        tests = [result["w_test"] for result in held_at_bm1["solution"]["observation_results"]]
        assert len(tests) == 3
        scores = {f"{abs(test['statistic']):.2f}" for test in tests}
        (critical,) = {f"{test['critical_high']:.2f}" for test in tests}
        assert len(scores) == 1
        score = scores.pop()
        quoted(readme, f"every one of them scores **{score}**, below the critical value of {critical},")
        quoted(readme, "so **no outlier is named.**")

    def test_step_4_the_residuals_are_shared_by_length(self, readme, held_at_bm1):
        residuals = {
            result["observation_id"]: mm(abs(result["residual"]))
            for result in held_at_bm1["solution"]["observation_results"]
        }
        quoted(
            readme,
            f"{residuals['BM1-BM2']} mm on BM1 to BM2, {residuals['BM2-BM4']} mm on BM2 to BM4, "
            f"{residuals['BM4-BM1']} mm on BM4 back to BM1",
        )

    def test_step_4_the_height_is_wrong_by_what_it_says(self, readme, held_at_bm1):
        from tests.reference_levelling import HEIGHTS

        height = next(
            float(row.split(",")[1])
            for row in Path(held_at_bm1["OUTPUT_CSV"]).read_text(encoding="utf-8").splitlines()[1:]
            if row.split(",")[0] == "BM2"
        )
        quoted(readme, f"BM2 comes out at {height:.4f} m")
        quoted(readme, f"**{mm(abs(height - HEIGHTS['BM2']))} mm** from where it is")
        quoted(readme, f"BM2 {HEIGHTS['BM2']:.3f} m")

    def test_step_5_the_benchmarks_find_the_line(self, readme, folder, reduced):
        from tests.reference_levelling import HEIGHTS

        benchmarks = ",".join(f"{name}={HEIGHTS[name]:.3f}" for name in ("BM1", "BM2", "BM4"))
        quoted(readme, f"`{benchmarks}`")
        refused = refusal("geocomp:levelling_network", self._network(folder, reduced, benchmarks, "all"))
        assert quote(readme) == refused
        assert "BM2-BM4" in refused

    def test_step_5_acknowledged_it_refuses_again_for_another_reason(self, readme, folder, reduced):
        from tests.reference_levelling import HEIGHTS

        benchmarks = ",".join(f"{name}={HEIGHTS[name]:.3f}" for name in ("BM1", "BM2", "BM4"))
        refused = refusal(
            "geocomp:levelling_network",
            self._network(folder, reduced, benchmarks, "acknowledged", ADJUST_FAILING=True),
        )
        assert "BM2-BM4" not in refused
        quoted(readme, "with all three benchmarks held there is nothing left to estimate")
        assert "held fixed, so there is nothing to estimate" in refused, refused
