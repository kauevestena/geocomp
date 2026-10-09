# SPDX-License-Identifier: GPL-2.0-or-later
"""The gravimetry tutorial, followed as its README says (FR-950, FR-952; P13-4).

The third walkthrough held to the toolbox (:mod:`tests.qgis.walkthrough`), and
the first whose answer is someone else's. USGS published the truth of these
surveys beside them, so the numbers checked here are GeoComp's distance from
that truth, not GeoComp agreeing with itself. The drift and the assumptions the
README quotes are in the run's log, and are read from it.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

import pytest

from geocomp.resources import DATASETS_DIR, available_datasets
from tests import usgs_gravity as usgs
from tests.conftest import requires_qgis
from tests.qgis import walkthrough
from tests.qgis.walkthrough import check_names, flat, option, quoted, run, run_logged, steps

pytestmark = [pytest.mark.qgis, requires_qgis]

NAME = "rd07-usgs"
README = DATASETS_DIR / NAME / "README.md"
INSTALL = "geocomp:project_tutorial_dataset"
SHIPPED = (
    "GSadjust-LICENSE.md",
    "README.es.md",
    "README.md",
    "README.pt_BR.md",
    "Test2.txt",
    "Test3.txt",
    "profiles-calibrated.json",
    "profiles.json",
)
PREPROCESS = "geocomp:gravimetry_preprocess"
NETWORK = "geocomp:gravimetry_network"
JOINT = "Estimated with the station values"
DRIFT = re.compile(r"(\d+\.\d+) ± (\d+\.\d+) mGal per hour")
VF = "VARIANCE_FACTOR_APOSTERIORI"
UNKNOWN = ("sta2", "sta3", "sta4", "sta5")


@pytest.fixture(scope="module", autouse=True)
def _registered(geocomp_provider):
    return geocomp_provider


@pytest.fixture(scope="module")
def readme() -> str:
    return README.read_text(encoding="utf-8")


class TestItNamesWhatTheDialogsShow:
    def test_it_has_three_pairs_of_steps(self, readme):
        assert [step.algorithm_id for step in steps(readme)] == [PREPROCESS, NETWORK] * 3

    def test_every_title_input_and_choice_is_the_dialogs(self, readme):
        check_names(readme)

    def test_the_known_gravity_it_gives_is_usgss_truth(self, readme):
        networks = [step for step in steps(readme) if step.algorithm_id == NETWORK]
        known = [dict(step.filled)["Known gravity (mGal)"] for step in networks]
        for value in known:
            for pair in value.strip("`").split(","):
                station, gravity = pair.split("=")
                assert float(gravity) == usgs.TRUTH[station], pair

    def test_the_truth_it_tabulates_is_usgss(self, readme):
        row = next(line for line in readme.splitlines() if line.startswith("| **Truth**"))
        assert [float(cell) for cell in row.split("|")[2:7]] == list(usgs.TRUTH.values())


@pytest.fixture(scope="module")
def folder(tmp_path_factory) -> Path:
    results = run(
        INSTALL,
        {
            "DATASET": available_datasets().index(NAME),
            "DESTINATION": str(tmp_path_factory.mktemp("gravimetry-tutorial")),
        },
    )
    assert results["FILE_COUNT"] == len(SHIPPED)
    return Path(results["OUTPUT_DIRECTORY"])


def _preprocess(folder: Path, survey: str, profiles: str, name: str) -> tuple[dict, str]:
    return run_logged(
        PREPROCESS,
        {
            "READINGS": str(folder / survey),
            "PROFILES": str(folder / profiles),
            "PRECISION_FLOOR": 0.0,
            "OUTPUT_READINGS": str(folder / name),
        },
    )


def _network(folder: Path, readings: dict, known: str, name: str) -> tuple[dict, str, dict]:
    results, log = run_logged(
        NETWORK,
        {
            "READINGS": readings["OUTPUT_READINGS"],
            "KNOWN_GRAVITY": known,
            "DRIFT_MODE": option(NETWORK, "DRIFT_MODE", JOINT),
            "OUTPUT_SOLUTION": str(folder / f"{name}.json"),
            "OUTPUT_CSV": str(folder / f"{name}.csv"),
        },
    )
    with open(results["OUTPUT_CSV"], encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    gravity = {row["station"]: (float(row["gravity_mgal"]), float(row["sigma_mgal"])) for row in rows}
    return results, log, gravity


def _ugal(mgal: float) -> str:
    return f"{abs(mgal) * 1000:.1f}"


@pytest.fixture(scope="module")
def test2(folder):
    return _preprocess(folder, "Test2.txt", "profiles.json", "test2.json")


@pytest.fixture(scope="module")
def test2_network(folder, test2):
    return _network(folder, test2[0], "sta1=50.000", "test2-network")


@pytest.fixture(scope="module")
def test3(folder):
    return _preprocess(folder, "Test3.txt", "profiles.json", "test3.json")


@pytest.fixture(scope="module")
def test3_calibrated(folder):
    return _preprocess(folder, "Test3.txt", "profiles-calibrated.json", "test3-calibrated.json")


class TestFollowingIt:
    def test_it_installs_the_surveys_their_profiles_and_licence(self, folder):
        assert folder.name == NAME
        assert sorted(path.name for path in folder.iterdir()) == walkthrough.installed(NAME, SHIPPED)

    def test_step_1_reads_one_session_and_says_what_it_assumed(self, readme, test2):
        results, log = test2
        counts = (results["READING_COUNT"], results["OCCUPATION_COUNT"], results["SESSION_COUNT"])
        assert counts == (11, 11, 1)
        quoted(readme, "Eleven readings, eleven occupations, one session.")
        assert "the profile's nominal precision" in log and "times were taken as UTC" in log
        rate, sigma = DRIFT.search(log).groups()
        quoted(readme, f"the base: **{rate} ± {sigma} mGal per hour**")

    def test_step_2_passes_and_estimates_the_drift(self, readme, test2_network):
        results, log, _gravity = test2_network
        assert results["DEGREES_OF_FREEDOM"] == 5 and results["GLOBAL_TEST_PASSED"] is True
        quoted(readme, "**5 degrees of freedom**")
        quoted(readme, f"a variance factor of **{results[VF]:.2f}**")
        rate, sigma = DRIFT.search(log).groups()
        quoted(readme, f"**{rate} ± {sigma} mGal per hour**, against the 0.01 USGS put in")
        assert abs(float(rate) - usgs.CASES["Test2"]["drift_mgal_h"]) < float(sigma)

    def test_step_2_recovers_usgss_truth(self, readme, test2_network):
        _results, _log, gravity = test2_network
        off = {station: gravity[station][0] - usgs.TRUTH[station] for station in UNKNOWN}
        quoted(
            readme,
            f"sta2 is **{_ugal(off['sta2'])} µGal** from its truth, sta3 **{_ugal(off['sta3'])}**, "
            f"sta4 **{_ugal(off['sta4'])}** and sta5 **{_ugal(off['sta5'])}**",
        )
        for station, error in off.items():
            assert abs(error) < gravity[station][1], station
        assert gravity["sta1"] == (usgs.TRUTH["sta1"], 0.0)

    def test_step_4_two_known_values_expose_the_scale(self, readme, folder, test3):
        results, log, _gravity = _network(folder, test3[0], "sta1=50.000,sta3=45.000", "test3-two")
        assert results["GLOBAL_TEST_PASSED"] is False
        assert "The global test failed." in log
        quoted(
            readme,
            f"**The global test fails**, with a variance factor of **{results[VF]:.0f}**",
        )

    def test_step_4_try_this_one_known_value_hides_it(self, readme, folder, test3, test3_calibrated):
        results, _log, gravity = _network(folder, test3[0], "sta1=50.000", "test3-one")
        assert results["GLOBAL_TEST_PASSED"] is True
        quoted(readme, f"with a variance factor of **{results[VF]:.2f}**,")
        sta3 = gravity["sta3"][0]
        error = abs(sta3 - usgs.TRUTH["sta3"]) * 1000
        quoted(readme, f"sta3 comes out at **{sta3:.3f} mGal**, **{error:.0f} µGal** from its truth")
        calibrated, _log, _gravity = _network(folder, test3_calibrated[0], "sta1=50.000", "test3-one-cal")
        shown = f"{results[VF]:.2f}"
        assert f"{calibrated[VF]:.2f}" == shown
        assert calibrated[VF] == pytest.approx(results[VF], rel=1e-9)
        quoted(readme, f"the variance factor is the same, {shown}, to every digit shown")

    def test_step_6_the_calibration_makes_it_consistent_and_right(self, readme, folder, test3_calibrated):
        results, _log, gravity = _network(folder, test3_calibrated[0], "sta1=50.000,sta3=45.000", "test3-cal")
        assert results["GLOBAL_TEST_PASSED"] is True
        quoted(
            readme,
            f"The global test passes, with a variance factor of **{results[VF]:.2f}**",
        )
        worst = max(abs(gravity[station][0] - usgs.TRUTH[station]) for station in ("sta2", "sta4", "sta5"))
        stated = float(re.search(r"within \*\*(\d+\.\d) µGal\*\* of their truth", flat(readme)).group(1))
        assert worst * 1000 <= stated and stated - worst * 1000 < 0.1

    def test_what_to_take_from_it_quotes_the_two_drift_precisions(self, readme, test2, test2_network):
        base = DRIFT.search(test2[1]).group(2)
        joint = DRIFT.search(test2_network[1]).group(2)
        quoted(readme, f"(±{joint} against ±{base} mGal per hour here)")
        assert float(joint) < float(base)


@pytest.mark.parametrize("language", ("pt_BR", "es"))
def test_each_translation_names_what_the_dialogs_show_in_its_language(language):
    """The translations, held to GeoComp speaking their language (P13-7)."""
    from tests.qgis.test_language import _Installed
    from tests.qgis.walkthrough import label

    translated = (DATASETS_DIR / NAME / f"README.{language}.md").read_text(encoding="utf-8")
    with _Installed(language):
        check_names(translated)
        quoted(translated, f"*{label(NETWORK, 'KNOWN_GRAVITY')}*")
