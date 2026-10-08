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
import re
from pathlib import Path

import pytest

from geocomp.resources import DATASETS_DIR, available_datasets
from tests.conftest import requires_qgis

pytestmark = [pytest.mark.qgis, requires_qgis]

NAME = "rd04-loop"
README = DATASETS_DIR / NAME / "README.md"
INSTALL = "geocomp:project_tutorial_dataset"
STEP = re.compile(r"^### \d+\. (?P<title>.+?) — `(?P<id>geocomp:\w+)`$")
FILLED = re.compile(r"^- \*\*(?P<label>.+?)\*\*: ")


@pytest.fixture(scope="module", autouse=True)
def _registered(geocomp_provider):
    return geocomp_provider


@pytest.fixture(scope="module")
def readme() -> str:
    return README.read_text(encoding="utf-8")


def _flat(text: str) -> str:
    """*text* as one line, its block-quote markers gone: what a reader reads, not how it wraps."""
    return " ".join(line.removeprefix(">").strip() for line in text.splitlines() if line.strip())


def _steps(text: str) -> list[tuple[str, str, list[str]]]:
    """Each step with an algorithm: its title, the algorithm's id and the inputs it fills."""
    steps: list[tuple[str, str, list[str]]] = []
    for line in text.splitlines():
        heading = STEP.match(line)
        if heading:
            steps.append((heading["title"], heading["id"], []))
        elif line.startswith("### "):
            steps.append(("", "", []))
        elif steps and (filled := FILLED.match(line)):
            steps[-1][2].append(filled["label"])
    return [step for step in steps if step[1]]


def _algorithm(algorithm_id: str):
    from qgis.core import QgsApplication

    algorithm = QgsApplication.processingRegistry().algorithmById(algorithm_id)
    assert algorithm is not None, f"{algorithm_id} is not registered"
    return algorithm.create({})


def _run(algorithm_id: str, parameters: dict) -> dict:
    from qgis.core import QgsProcessingContext, QgsProcessingFeedback

    results, ok = _algorithm(algorithm_id).run(
        parameters, QgsProcessingContext(), QgsProcessingFeedback(), catchExceptions=False
    )
    assert ok, f"{algorithm_id} reported failure"
    return results


def _refusal(algorithm_id: str, parameters: dict) -> str:
    from qgis.core import QgsProcessingContext, QgsProcessingException, QgsProcessingFeedback

    with pytest.raises(QgsProcessingException) as caught:
        _algorithm(algorithm_id).run(
            parameters, QgsProcessingContext(), QgsProcessingFeedback(), catchExceptions=False
        )
    return _flat(str(caught.value))


def _quoted(readme: str, text: str) -> None:
    assert text in _flat(readme), f"the README does not say {text!r}"


def _label(algorithm_id: str, name: str) -> str:
    algorithm = _algorithm(algorithm_id)  # held: the definition is the algorithm's, and goes with it
    return algorithm.parameterDefinition(name).description()


def _mm(metres: float, places: int = 1) -> str:
    """Millimetres as the README writes them, with a typographic minus."""
    return f"{metres * 1000:.{places}f}".replace("-", "\u2212")


class TestItNamesWhatTheDialogsShow:
    def test_it_has_the_four_steps_with_algorithms(self, readme):
        assert [step[1] for step in _steps(readme)] == [
            "geocomp:levelling_import",
            "geocomp:levelling_equal_sights",
            "geocomp:levelling_closures",
            "geocomp:levelling_network",
        ]

    def test_each_step_is_titled_as_the_toolbox_lists_it(self, readme):
        for title, algorithm_id, _labels in _steps(readme):
            assert title == _algorithm(algorithm_id).displayName(), algorithm_id

    def test_every_input_it_fills_is_one_the_dialog_has(self, readme):
        for _title, algorithm_id, labels in _steps(readme):
            algorithm = _algorithm(algorithm_id)
            offered = {definition.description() for definition in algorithm.parameterDefinitions()}
            assert labels, algorithm_id
            assert set(labels) <= offered, (algorithm_id, set(labels) - offered)

    def test_the_inputs_it_names_in_passing_are_the_dialogs_too(self, readme):
        closures = _algorithm("geocomp:levelling_closures")
        assert "Loop" in closures.parameterDefinition("MODE").options()
        _quoted(readme, "**Mode**: *Loop*")
        network = "geocomp:levelling_network"
        _quoted(readme, f"giving the **{_label(network, 'BENCHMARKS')}** as")
        _quoted(readme, f"turn on *{_label(network, 'ADJUST_FAILING')}*")


class TestFollowingIt:
    """Install, then the five steps in order, each step's output the next one's input."""

    @pytest.fixture(scope="class")
    def folder(self, tmp_path_factory) -> Path:
        results = _run(
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
        return _run(
            "geocomp:levelling_import",
            {
                "BOOK": str(folder / "loop.csv"),
                "MAPPING": str(folder / "mapping.json"),
                "PROFILES": str(folder / "profiles.json"),
                "OUTPUT_SETUPS": str(folder / "setups.json"),
            },
        )

    def test_step_1_reads_ten_setups_in_three_lines(self, readme, imported):
        _quoted(readme, "Ten setups in three lines, no row rejected.")
        assert (imported["SETUP_COUNT"], imported["LINE_COUNT"]) == (10, 3)
        assert imported["REJECTED_ROWS"] == 0

    @pytest.fixture(scope="class")
    def reduced(self, folder, imported) -> dict:
        return _run(
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
        _quoted(readme, f"the worst line, BM2 to BM4, carries {_mm(reduced['WORST_UNCERTAINTY'])} mm")
        lines = json.loads(Path(reduced["OUTPUT_REDUCTIONS"]).read_text(encoding="utf-8"))["lines"]
        worst = max(lines, key=lambda line: line["height_difference"]["variance"])
        assert (worst["from_station"], worst["to_station"]) == ("BM2", "BM4")

    def _closure(self, folder, reduced, coefficient: float) -> dict:
        return _run(
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
        _quoted(
            readme,
            f"They sum to **{_mm(closure['MISCLOSURE'])} mm**, against a permissible "
            f"**{_mm(closure['PERMISSIBLE'])} mm**",
        )
        length = (closure["PERMISSIBLE"] / 0.008) ** 2
        _quoted(readme, f"for the loop's {length:.2f} km. **The loop fails.**")

    def test_step_3_without_a_tolerance_there_is_no_verdict(self, readme, folder, reduced):
        judged = self._closure(folder, reduced, 0.008)
        unjudged = self._closure(folder, reduced, 0.0)
        assert unjudged["MISCLOSURE"] == judged["MISCLOSURE"]
        assert unjudged["PASSED"] == -1
        _quoted(readme, "there is no verdict, neither passed nor failed")

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
        results = _run("geocomp:levelling_network", self._network(folder, reduced, "BM1=100.000", "bm1"))
        results["solution"] = json.loads(Path(results["OUTPUT_SOLUTION"]).read_text(encoding="utf-8"))
        return results

    def test_step_4_one_degree_of_freedom_and_a_failed_global_test(self, readme, held_at_bm1):
        assert held_at_bm1["DEGREES_OF_FREEDOM"] == 1
        _quoted(readme, "**one degree of freedom.**")
        assert held_at_bm1["GLOBAL_TEST_PASSED"] is False
        _quoted(
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
        _quoted(readme, f"every one of them scores **{score}**, below the critical value of {critical},")
        _quoted(readme, "so **no outlier is named.**")

    def test_step_4_the_residuals_are_shared_by_length(self, readme, held_at_bm1):
        residuals = {
            result["observation_id"]: _mm(abs(result["residual"]))
            for result in held_at_bm1["solution"]["observation_results"]
        }
        _quoted(
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
        _quoted(readme, f"BM2 comes out at {height:.4f} m")
        _quoted(readme, f"**{_mm(abs(height - HEIGHTS['BM2']))} mm** from where it is")
        _quoted(readme, f"BM2 {HEIGHTS['BM2']:.3f} m")

    def test_step_5_the_benchmarks_find_the_line(self, readme, folder, reduced):
        from tests.reference_levelling import HEIGHTS

        benchmarks = ",".join(f"{name}={HEIGHTS[name]:.3f}" for name in ("BM1", "BM2", "BM4"))
        _quoted(readme, f"`{benchmarks}`")
        refusal = _refusal("geocomp:levelling_network", self._network(folder, reduced, benchmarks, "all"))
        quote = _flat("\n".join(line for line in readme.splitlines() if line.startswith(">")))
        assert quote == refusal
        assert "BM2-BM4" in refusal

    def test_step_5_acknowledged_it_refuses_again_for_another_reason(self, readme, folder, reduced):
        from tests.reference_levelling import HEIGHTS

        benchmarks = ",".join(f"{name}={HEIGHTS[name]:.3f}" for name in ("BM1", "BM2", "BM4"))
        refusal = _refusal(
            "geocomp:levelling_network",
            self._network(folder, reduced, benchmarks, "acknowledged", ADJUST_FAILING=True),
        )
        assert "BM2-BM4" not in refusal
        _quoted(readme, "with all three benchmarks held there is nothing left to estimate")
        assert "held fixed, so there is nothing to estimate" in refusal, refusal
