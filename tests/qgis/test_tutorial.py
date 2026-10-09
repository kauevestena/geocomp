# SPDX-License-Identifier: GPL-2.0-or-later
"""The tutorial, run the way a user follows it (FR-950, FR-952).

``tests/test_tutorial_dataset.py`` checks the shipped files and the claims the
prose makes, without QGIS. What is left is the part a reader actually does:
install the dataset from the toolbox, then run the three algorithms in order
with the shipped mapping and profiles, and get the numbers the tutorial promised.

That distinction matters. The other tests drive the core with sigmas written
into the test; this one drives the algorithms with the ``profiles.json`` a
reader would pick in the file chooser. A tutorial whose supporting documents do
not work through the dialogs is not a tutorial, however correct the mathematics
underneath it is.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.qgis import walkthrough

pytestmark = pytest.mark.qgis

TUTORIAL_ALGORITHM = "geocomp:project_tutorial_dataset"
NETWORK = "geocomp:totalstation_network"
INNER = "Inner constraint — free network, trace minimum"
MINIMUM = "Minimum constraint — over chosen stations"
CONSTRAINED = "Constrained — hold the stations the network fixes"
README = Path(__file__).resolve().parents[2] / "geocomp" / "resources" / "datasets" / "rd01" / "README.md"
SHIPPED = (
    "README.es.md",
    "README.md",
    "README.pt_BR.md",
    "approximate.json",
    "mapping.json",
    "profiles.json",
    "raw_data.csv",
)


def _algorithm(algorithm_id: str):
    from qgis.core import QgsApplication

    algorithm = QgsApplication.processingRegistry().algorithmById(algorithm_id)
    assert algorithm is not None, f"{algorithm_id} is not registered"
    return algorithm


def _network(workspace: Path, reduced: dict, name: str, *, datum: str, **more) -> dict:
    """Step 3's parameters, as the README fills them, with *datum* chosen by its name."""
    from tests.qgis.walkthrough import option

    return {
        "REDUCTIONS": reduced["OUTPUT_REDUCED"],
        "APPROXIMATE": str(workspace / "approximate.json"),
        "DIMENSION": option(NETWORK, "DIMENSION", "2D — planimetric"),
        "DATUM": option(NETWORK, "DATUM", datum),
        "CRS": "EPSG:31982",
        "OUTPUT_SOLUTION": str(workspace / f"{name}.json"),
        **more,
    }


def _run(algorithm_id: str, parameters: dict):
    from qgis.core import QgsProcessingContext, QgsProcessingFeedback

    algorithm = _algorithm(algorithm_id).create({})
    results, ok = algorithm.run(
        parameters, QgsProcessingContext(), QgsProcessingFeedback(), catchExceptions=False
    )
    assert ok, f"{algorithm_id} reported failure"
    return results


class TestInstalling:
    def test_the_algorithm_is_registered_and_documented(self, geocomp_provider):
        algorithm = _algorithm(TUTORIAL_ALGORITHM)
        assert algorithm.groupId() == "project"
        assert len(algorithm.shortHelpString()) > 200

    def test_it_is_not_filed_under_a_survey_technique(self, geocomp_provider):
        """Installing a dataset belongs to no technique, and a future levelling
        or GNSS dataset would use the same algorithm.

        It was toolbox-only for that reason from P0 until P5, when the Project
        menu gave it and five others a home. The claim being made is unchanged --
        *not under a technique* -- and it is now asserted directly rather than
        through the absence of a menu placement, which said the same thing only
        while there was nowhere else for it to go.
        """
        from geocomp.registry import ALGORITHMS

        techniques = {"total_station", "level", "gnss", "gravimetry", "integration"}
        spec = next(spec for spec in ALGORITHMS if spec.id == TUTORIAL_ALGORITHM)
        assert spec.menu == "project"
        assert spec.menu not in techniques

    @pytest.fixture(scope="class")
    def installed(self, geocomp_provider, tmp_path_factory) -> Path:
        directory = tmp_path_factory.mktemp("tutorial")
        results = _run(TUTORIAL_ALGORITHM, {"DATASET": 0, "DESTINATION": str(directory)})
        assert results["FILE_COUNT"] == len(SHIPPED)
        return Path(results["OUTPUT_DIRECTORY"])

    def test_every_file_lands_in_a_folder_named_for_the_dataset(self, installed):
        assert installed.name == "rd01"
        assert sorted(path.name for path in installed.iterdir()) == walkthrough.installed("rd01", SHIPPED)

    def test_a_second_install_leaves_edited_files_alone(self, geocomp_provider, tmp_path):
        """Overwrite is off by default. A reader who annotated the tutorial and
        re-ran the installer should not lose the annotations."""
        first = _run(TUTORIAL_ALGORITHM, {"DATASET": 0, "DESTINATION": str(tmp_path)})
        marked = Path(first["OUTPUT_DIRECTORY"]) / "README.md"
        marked.write_text("my notes", encoding="utf-8")

        again = _run(TUTORIAL_ALGORITHM, {"DATASET": 0, "DESTINATION": str(tmp_path)})
        assert again["FILE_COUNT"] == 0
        assert marked.read_text(encoding="utf-8") == "my notes"

    def test_overwriting_is_available_when_asked_for(self, geocomp_provider, tmp_path):
        _run(TUTORIAL_ALGORITHM, {"DATASET": 0, "DESTINATION": str(tmp_path)})
        marked = tmp_path / "rd01" / "README.md"
        marked.write_text("my notes", encoding="utf-8")

        results = _run(
            TUTORIAL_ALGORITHM,
            {"DATASET": 0, "DESTINATION": str(tmp_path), "OVERWRITE": True},
        )
        assert results["FILE_COUNT"] == len(SHIPPED)
        assert marked.read_text(encoding="utf-8") != "my notes"

    def test_a_destination_that_does_not_exist_is_refused_by_name(
        self, geocomp_provider, tmp_path
    ):
        from qgis.core import (
            QgsProcessingContext,
            QgsProcessingException,
            QgsProcessingFeedback,
        )

        missing = tmp_path / "nowhere"
        algorithm = _algorithm(TUTORIAL_ALGORITHM).create({})
        with pytest.raises(QgsProcessingException) as caught:
            algorithm.run(
                {"DATASET": 0, "DESTINATION": str(missing)},
                QgsProcessingContext(),
                QgsProcessingFeedback(),
                catchExceptions=False,
            )
        assert "nowhere" in str(caught.value)


class TestFollowingIt:
    """The three steps, with the shipped mapping and profiles, in order."""

    @pytest.fixture(scope="class")
    def workspace(self, geocomp_provider, tmp_path_factory):
        directory = tmp_path_factory.mktemp("following")
        results = _run(TUTORIAL_ALGORITHM, {"DATASET": 0, "DESTINATION": str(directory)})
        return Path(results["OUTPUT_DIRECTORY"])

    @pytest.fixture(scope="class")
    def imported(self, workspace):
        return _run(
            "geocomp:totalstation_import_fieldbook",
            {
                "SOURCE": str(workspace / "raw_data.csv"),
                "MAPPING": str(workspace / "mapping.json"),
                "PROFILES": str(workspace / "profiles.json"),
                "OUTPUT_READINGS": str(workspace / "readings.json"),
            },
        )

    def test_step_one_reads_everything_the_tutorial_says_it_does(self, imported):
        assert imported["RECORD_COUNT"] == 12
        assert imported["SETUP_COUNT"] == 3
        assert imported["REJECTED_COUNT"] == 0

    @pytest.fixture(scope="class")
    def reduced(self, workspace, imported):
        return _run(
            "geocomp:totalstation_preprocess",
            {
                "READINGS": imported["OUTPUT_READINGS"],
                # The same library as step 1: the readings record which
                # instrument took them, and the reduction needs its constants.
                # Nothing else: until P13-9 this turned the atmospheric
                # correction off, which the README never asks a reader to do.
                "PROFILES": str(workspace / "profiles.json"),
                "OUTPUT_REDUCED": str(workspace / "reduced.json"),
            },
        )

    def test_step_two_blocks_the_one_pointing_the_tutorial_promises(self, reduced):
        assert reduced["POINTING_COUNT"] == 6
        assert reduced["BLOCKING_COUNT"] == 1
        assert reduced["USABLE_COUNT"] == 5

    def test_step_two_says_what_the_tutorial_quotes(self, workspace, imported):
        """Until P13-10 the quote was a paraphrase of an older message, in GeoComp's voice."""
        from tests.qgis.walkthrough import quote, run_logged

        _results, log = run_logged(
            "geocomp:totalstation_preprocess",
            {
                "READINGS": imported["OUTPUT_READINGS"],
                "PROFILES": str(workspace / "profiles.json"),
                "OUTPUT_REDUCED": str(workspace / "reduced-logged.json"),
            },
        )
        readme = README.read_text(encoding="utf-8")
        assert quote(readme) in log, (quote(readme), log)

    @pytest.fixture(scope="class")
    def adjusted(self, workspace, reduced):
        return _run(NETWORK, _network(workspace, reduced, "solution", datum=INNER))

    def test_step_three_fails_its_global_test_as_the_tutorial_warns(self, adjusted):
        """Correctly. The distances disagree by about 15 mm against a claimed
        2 mm, and a reader who was not told would think they had gone wrong."""
        assert adjusted["GLOBAL_TEST_PASSED"] is False
        assert adjusted["DEGREES_OF_FREEDOM"] > 0

    def test_the_solution_holds_all_three_stations(self, adjusted):
        from geocomp.core.models import Solution

        solution = Solution.from_dict(
            json.loads(Path(adjusted["OUTPUT_SOLUTION"]).read_text(encoding="utf-8"))
        )
        assert {station.station_id for station in solution.adjusted_stations} == {"1", "2", "3"}


class TestItNamesWhatTheDialogsShow:
    """Held to the dialogs since P13-9, as the later walkthroughs were from the start.

    Doing it found four names that were not the dialog's -- *Source* for *Field
    book*, *CRS* for its full label, and the dimension and datum written as
    words rather than chosen from the list -- and a *Try this* that GeoComp
    refused.
    """

    @pytest.fixture(scope="class")
    def readme(self) -> str:
        return README.read_text(encoding="utf-8")

    def test_every_title_input_and_choice_is_the_dialogs(self, geocomp_provider, readme):
        from tests.qgis.walkthrough import check_names, steps

        assert [step.algorithm_id for step in steps(readme)] == [
            "geocomp:totalstation_import_fieldbook",
            "geocomp:totalstation_preprocess",
            NETWORK,
        ]
        check_names(readme)

    def test_the_try_this_names_the_dialogs_inputs_and_choices(self, geocomp_provider, readme):
        from tests.qgis.walkthrough import label, quoted

        for name in ("DATUM", "DATUM_STATIONS", "FIXED_STATIONS"):
            quoted(readme, f"**{label(NETWORK, name)}**")
        for choice in (MINIMUM, CONSTRAINED):
            quoted(readme, f"*{choice}*")


class TestTheNetworkIsFree:
    """What the README's section on the datum says happens, happens."""

    @pytest.fixture(scope="class")
    def workspace(self, geocomp_provider, tmp_path_factory):
        directory = str(tmp_path_factory.mktemp("free"))
        results = _run(TUTORIAL_ALGORITHM, {"DATASET": 0, "DESTINATION": directory})
        return Path(results["OUTPUT_DIRECTORY"])

    @pytest.fixture(scope="class")
    def reduced(self, workspace):
        readings = _run(
            "geocomp:totalstation_import_fieldbook",
            {
                "SOURCE": str(workspace / "raw_data.csv"),
                "MAPPING": str(workspace / "mapping.json"),
                "PROFILES": str(workspace / "profiles.json"),
                "OUTPUT_READINGS": str(workspace / "readings.json"),
            },
        )
        return _run(
            "geocomp:totalstation_preprocess",
            {
                "READINGS": readings["OUTPUT_READINGS"],
                "PROFILES": str(workspace / "profiles.json"),
                "OUTPUT_REDUCED": str(workspace / "reduced.json"),
            },
        )

    @pytest.fixture(scope="class")
    def free(self, workspace, reduced):
        return _run(NETWORK, _network(workspace, reduced, "inner", datum=INNER))

    @pytest.fixture(scope="class")
    def chosen(self, workspace, reduced):
        """Over stations 1 and 2: station 2 is due north of 1, so the datum fixes
        both eastings exactly, and their variance is zero. Rounding made one
        -2e-24 m^2, refused as a negative variance until P13-9."""
        return _run(
            NETWORK, _network(workspace, reduced, "minimum", datum=MINIMUM, DATUM_STATIONS="1,2")
        )

    def test_step_3_has_the_degrees_of_freedom_and_variance_factor_it_quotes(self, free):
        from tests.qgis.walkthrough import quoted

        readme = README.read_text(encoding="utf-8")
        quoted(readme, f"**{free['DEGREES_OF_FREEDOM']} degrees of freedom**")
        quoted(readme, f"variance factor of **{free['VARIANCE_FACTOR']:.2f}**")

    def test_two_stations_as_the_datum_change_only_the_coordinates(self, free, chosen):
        from tests.qgis.walkthrough import quoted

        readme = README.read_text(encoding="utf-8")
        assert chosen["DEGREES_OF_FREEDOM"] == free["DEGREES_OF_FREEDOM"]
        assert chosen["VARIANCE_FACTOR"] == pytest.approx(free["VARIANCE_FACTOR"], rel=1e-9)
        quoted(
            readme,
            f"The residuals, the {chosen['DEGREES_OF_FREEDOM']} degrees of freedom and the "
            f"variance factor of {chosen['VARIANCE_FACTOR']:.2f} are the same",
        )
        residuals = [
            json.loads(Path(result["OUTPUT_SOLUTION"]).read_text(encoding="utf-8"))["observation_results"]
            for result in (free, chosen)
        ]
        assert [r["residual"] for r in residuals[1]] == pytest.approx(
            [r["residual"] for r in residuals[0]], abs=1e-9
        )
        positions = [
            {
                station["station_id"]: station["position"]
                for station in json.loads(Path(result["OUTPUT_SOLUTION"]).read_text(encoding="utf-8"))[
                    "adjusted_stations"
                ]
            }
            for result in (free, chosen)
        ]
        assert positions[0] != positions[1]

    def test_holding_station_1_as_well_is_refused(self, workspace, reduced):
        from tests.qgis.walkthrough import refusal

        said = refusal(
            NETWORK,
            _network(
                workspace, reduced, "both", datum=MINIMUM, DATUM_STATIONS="1,2", FIXED_STATIONS="1"
            ),
        )
        assert "These stations are held" in said and "remove it twice" in said, said

    def test_station_1_alone_leaves_the_rotation(self, workspace, reduced):
        from tests.qgis.walkthrough import refusal

        said = refusal(
            NETWORK, _network(workspace, reduced, "one", datum=CONSTRAINED, FIXED_STATIONS="1")
        )
        assert "does not determine 1 combination" in said and "orientation" in said, said


@pytest.mark.parametrize("language", ("pt_BR", "es"))
class TestInEachLanguage:
    """The translations, held to GeoComp speaking their language (P13-10), as the others' are."""

    def test_every_name_it_uses_is_the_dialogs(self, geocomp_provider, language):
        from tests.qgis.test_language import _Installed
        from tests.qgis.walkthrough import algorithm, check_names, label, option, quoted

        translated = README.with_name(f"README.{language}.md").read_text(encoding="utf-8")
        # By their English names, before the language changes.
        indices = [option(NETWORK, "DATUM", choice) for choice in (MINIMUM, CONSTRAINED)]
        with _Installed(language):
            check_names(translated)
            for name in ("DATUM", "DATUM_STATIONS", "FIXED_STATIONS"):
                quoted(translated, f"**{label(NETWORK, name)}**")
            network = algorithm(NETWORK)  # held: the definition is the algorithm's
            choices = [network.parameterDefinition("DATUM").options()[index] for index in indices]
        for choice in choices:
            quoted(translated, f"*{choice}*")

    def test_it_quotes_step_two_in_that_language(self, geocomp_provider, language, tmp_path):
        from tests.qgis.test_language import _Installed
        from tests.qgis.walkthrough import quote, run, run_logged

        translated = README.with_name(f"README.{language}.md").read_text(encoding="utf-8")
        installed = run(TUTORIAL_ALGORITHM, {"DATASET": 0, "DESTINATION": str(tmp_path)})
        folder = Path(installed["OUTPUT_DIRECTORY"])
        readings = run(
            "geocomp:totalstation_import_fieldbook",
            {
                "SOURCE": str(folder / "raw_data.csv"),
                "MAPPING": str(folder / "mapping.json"),
                "PROFILES": str(folder / "profiles.json"),
                "OUTPUT_READINGS": str(folder / "readings.json"),
            },
        )
        with _Installed(language):
            _results, log = run_logged(
                "geocomp:totalstation_preprocess",
                {
                    "READINGS": readings["OUTPUT_READINGS"],
                    "PROFILES": str(folder / "profiles.json"),
                    "OUTPUT_REDUCED": str(folder / "reduced.json"),
                },
            )
        assert quote(translated) in log, (quote(translated), log)
