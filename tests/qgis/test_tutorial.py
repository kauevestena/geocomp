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

pytestmark = pytest.mark.qgis

TUTORIAL_ALGORITHM = "geocomp:project_tutorial_dataset"


def _algorithm(algorithm_id: str):
    from qgis.core import QgsApplication

    algorithm = QgsApplication.processingRegistry().algorithmById(algorithm_id)
    assert algorithm is not None, f"{algorithm_id} is not registered"
    return algorithm


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
        assert results["FILE_COUNT"] == 5
        return Path(results["OUTPUT_DIRECTORY"])

    def test_every_file_lands_in_a_folder_named_for_the_dataset(self, installed):
        assert installed.name == "rd01"
        assert sorted(path.name for path in installed.iterdir()) == [
            "README.md",
            "approximate.json",
            "mapping.json",
            "profiles.json",
            "raw_data.csv",
        ]

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
        assert results["FILE_COUNT"] == 5
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
                "PROFILES": str(workspace / "profiles.json"),
                "APPLY_ATMOSPHERIC": False,
                "OUTPUT_REDUCED": str(workspace / "reduced.json"),
            },
        )

    def test_step_two_blocks_the_one_pointing_the_tutorial_promises(self, reduced):
        assert reduced["POINTING_COUNT"] == 6
        assert reduced["BLOCKING_COUNT"] == 1
        assert reduced["USABLE_COUNT"] == 5

    @pytest.fixture(scope="class")
    def adjusted(self, workspace, reduced):
        return _run(
            "geocomp:totalstation_network",
            {
                "REDUCTIONS": reduced["OUTPUT_REDUCED"],
                "APPROXIMATE": str(workspace / "approximate.json"),
                "DIMENSION": 0,
                "DATUM": 1,
                "CRS": "EPSG:31982",
                "OUTPUT_SOLUTION": str(workspace / "solution.json"),
            },
        )

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
