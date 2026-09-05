# SPDX-License-Identifier: GPL-2.0-or-later
"""The shipped RD-01 tutorial dataset (FR-950, FR-952).

``specs/20`` section 3 says RD-01 ships with the plugin as a tutorial, with both
of its defects documented, because a tutorial in which the software catches two
real errors in real data teaches more than one in which nothing is wrong.

A tutorial is a promise about what the software will do, and one whose numbers
have drifted from the code is worse than none: a reader who runs it and gets
something else concludes the software is broken. So the claims are checked here
against the shipped files -- not the repository's working copies -- and the
numbers written in the prose are checked against the constants the reference
tests use.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from geocomp.core.instruments import stochastic
from geocomp.core.instruments.profiles import ProfileLibrary
from geocomp.core.techniques.total_station.pipeline import (
    PreprocessingOptions,
    preprocess_setup,
)
from geocomp.io.fieldbook import read_field_book_csv
from geocomp.io.mapping import FieldMapping
from geocomp.resources import DATASETS_DIR, available_datasets
from tests import reference_rd01 as rd01

RD01 = DATASETS_DIR / "rd01"
FILES = ("README.md", "approximate.json", "mapping.json", "profiles.json", "raw_data.csv")


@pytest.fixture(scope="module")
def readme() -> str:
    return (RD01 / "README.md").read_text(encoding="utf-8")


class TestItShips:
    def test_the_dataset_is_discoverable(self):
        assert "rd01" in available_datasets()

    @pytest.mark.parametrize("name", FILES)
    def test_every_file_the_tutorial_needs_is_there(self, name):
        assert (RD01 / name).is_file()

    def test_nothing_else_is_in_the_folder(self):
        """The installer copies the folder, so a stray file becomes part of
        every user's tutorial."""
        assert sorted(path.name for path in RD01.iterdir()) == sorted(FILES)

    def test_the_shipped_field_book_is_the_reference_one(self):
        """The tutorial and the reference dataset must be the same data. If
        they drift, the tutorial's numbers stop being the tested ones."""
        assert (RD01 / "raw_data.csv").read_bytes() == rd01.RAW.read_bytes()

    def test_every_file_type_in_the_dataset_is_one_the_build_includes(self):
        """The build copies by suffix, and a dataset file with an unlisted one
        would vanish from the package while every test here still passed --
        the algorithm would then report no datasets on a user's machine and
        nowhere else."""
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "geocomp_build", Path(__file__).resolve().parent.parent / "scripts" / "build.py"
        )
        build = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(build)

        suffixes = {path.suffix for path in RD01.iterdir() if path.is_file()}
        assert suffixes <= build.INCLUDE_SUFFIXES
        assert not suffixes & build.EXCLUDE_SUFFIXES

    def test_the_installer_ships_the_whole_folder(self):
        """``available_datasets`` reads the directory rather than a list in
        code, so adding a dataset cannot leave the list behind."""
        assert available_datasets() == sorted(
            path.name for path in DATASETS_DIR.iterdir() if path.is_dir()
        )


class TestTheSupportingDocumentsWork:
    def test_the_mapping_covers_every_column_of_the_field_book(self):
        """FR-160's point is that a mapping is defined once and reused. One
        that does not cover the file it was made for is not reusable."""
        mapping = FieldMapping.from_dict(
            json.loads((RD01 / "mapping.json").read_text(encoding="utf-8"))
        )
        with open(RD01 / "raw_data.csv", encoding="utf-8") as handle:
            header = next(csv.reader(handle))
        mapped = {column.column for column in mapping.columns if column.column}
        assert mapped == set(header)

    def test_the_profile_library_supplies_a_sigma_for_every_reading(self):
        """The import refuses rather than inventing one, so a tutorial shipped
        without a usable profile would fail at step 1."""
        library = ProfileLibrary.from_dict(
            json.loads((RD01 / "profiles.json").read_text(encoding="utf-8"))
        )
        assert library.default_instrument
        instrument = library.instruments[library.default_instrument]
        for kind, value in (
            (stochastic.DIRECTION, 1.0),
            (stochastic.ZENITH_ANGLE, 1.5),
            (stochastic.SLOPE_DISTANCE, 11.5),
        ):
            quantity, source = stochastic.resolve_sigma(kind, value, instrument=instrument)
            assert quantity.std_dev > 0.0, kind
            assert source is not None

    def test_the_approximate_coordinates_name_the_three_stations(self):
        approximate = json.loads((RD01 / "approximate.json").read_text(encoding="utf-8"))
        assert set(approximate) == {"1", "2", "3"}
        assert all(len(values) == 3 for values in approximate.values())


class TestTheTutorialTellsTheTruth:
    """Every number the prose states, run against the files it ships with."""

    @pytest.fixture(scope="class")
    def imported(self):
        mapping = FieldMapping.from_dict(
            json.loads((RD01 / "mapping.json").read_text(encoding="utf-8"))
        )
        library = ProfileLibrary.from_dict(
            json.loads((RD01 / "profiles.json").read_text(encoding="utf-8"))
        )
        return read_field_book_csv(RD01 / "raw_data.csv", mapping, library=library)

    def test_step_one_reads_twelve_records_into_three_setups(self, imported):
        assert imported.row_count == 12
        assert len(imported.records) == 12
        assert len(imported.setups) == 3
        assert imported.rejected_rows == ()
        assert imported.unrecognised_columns == ()

    @pytest.fixture(scope="class")
    def reduced(self, imported):
        library = ProfileLibrary.from_dict(
            json.loads((RD01 / "profiles.json").read_text(encoding="utf-8"))
        )
        options = PreprocessingOptions(apply_atmospheric=False)
        return [preprocess_setup(setup, library, options=options) for setup in imported.setups]

    def test_step_two_reduces_six_pointings_and_blocks_exactly_one(self, reduced):
        pointings = [pointing for result in reduced for pointing in result.pointings]
        assert len(pointings) == 6
        assert sum(1 for pointing in pointings if not pointing.is_usable) == 1

    def test_the_blocked_pointing_is_the_one_the_tutorial_names(self, readme, reduced):
        """The tutorial names the setup and the target, so getting them the
        wrong way round would send a reader looking at the wrong row."""
        blocked = [
            (result.station, pointing.target)
            for result in reduced
            for pointing in result.pointings
            if not pointing.is_usable
        ]
        assert blocked == [("3", "2")]
        assert "from station 3 to station 2" in readme

    def test_the_blunder_is_the_round_metre_the_tutorial_quotes(self, readme):
        assert "1.000 m" in readme
        assert rd01.BLUNDER_SIZE == pytest.approx(1.000)

    @pytest.mark.parametrize(
        ("quoted", "value"),
        (
            ("199.110", rd01.CORRECT_DEGREES),
            ("19.110", rd01.PUBLISHED_WRONG_DEGREES),
        ),
    )
    def test_the_directions_it_quotes_are_the_tested_ones(self, readme, quoted, value):
        assert quoted in readme
        assert f"{value:.3f}" == quoted

    @pytest.mark.parametrize(
        ("quoted", "in_source"),
        (("38.24", "38.24"), ("4.43", "4.43"), ("24.35", "24.35"), ("15 mm", "15 mm")),
    )
    def test_the_checks_it_cites_are_the_ones_that_exist(self, readme, quoted, in_source):
        """Each of these appears in ``tests/test_reference_total_station.py``,
        where the claim is actually established. The tutorial cites that file
        by name, so the numbers must be the same numbers."""
        source = (
            Path(__file__).resolve().parent / "test_reference_total_station.py"
        ).read_text(encoding="utf-8")
        assert quoted in readme
        assert in_source in source

    def test_it_says_the_network_is_free_and_why(self, readme):
        """RD-01 has no known point and no azimuth, so it can only be adjusted
        with inner or minimum constraints. A tutorial that skipped that would
        leave a reader stuck at the datum parameter."""
        lowered = readme.lower()
        assert "inner" in lowered and "free" in lowered
        assert "azimuth" in lowered

    def test_it_warns_that_the_global_test_fails(self, readme):
        """It does fail, correctly, and a reader who was not told would think
        they had done something wrong."""
        assert "global test fails" in readme.lower()
