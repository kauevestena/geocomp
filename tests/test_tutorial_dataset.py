# SPDX-License-Identifier: GPL-2.0-or-later
"""The shipped tutorial datasets (FR-950, FR-952).

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
from geocomp.io.levelbook import LevelMapping, read_level_book_csv
from geocomp.io.mapping import FieldMapping
from geocomp.resources import DATASET_ORDER, DATASETS_DIR, available_datasets
from tests import monitoring_network as monitoring
from tests import reference_levelling as levelling
from tests import reference_rd01 as rd01
from tests import usgs_gravity as usgs

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

    def test_every_shipped_dataset_has_its_origin_and_licence_recorded(self):
        """Every one ships in the plugin ZIP, so every one is redistributed.

        Until P13-3 ``THIRD_PARTY.md``'s table of bundled assets named none of
        them -- including ``rtklib-sample``, under RTKLIB's own licence, which
        had shipped since P12c-27.
        """
        notices = (Path(__file__).resolve().parent.parent / "THIRD_PARTY.md").read_text(encoding="utf-8")
        for name in DATASET_ORDER:
            assert f"| `geocomp/resources/datasets/{name}/` |" in notices, name

    def test_the_installer_offers_every_folder_in_the_published_order(self):
        """``available_datasets`` reads the directory, so a dataset a build left
        out is not offered; it orders what it finds by ``DATASET_ORDER``, because
        a saved model holds the dataset's index.

        Until P13-2 the order was the folders' names sorted, and this test
        asserted exactly that -- which ``rd04-loop`` would have kept passing
        while it moved ``rtklib-sample`` from index 1 to 2. Both directions are
        held: every folder is in the order, and every name in it ships.
        """
        folders = {path.name for path in DATASETS_DIR.iterdir() if path.is_dir()}
        assert set(DATASET_ORDER) == folders
        assert available_datasets() == list(DATASET_ORDER)


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


RTKLIB_SAMPLE = DATASETS_DIR / "rtklib-sample"
RTKLIB_FILES = (
    "07590920.05o",
    "30400920.05o",
    "RTKLIB-license.txt",
    "README.md",
    "brdc_0759.05n.gz",
)


class TestTheGnssSample:
    """The second shipped dataset: RTKLIB's own sample baseline, for a GNSS run."""

    def test_it_is_discoverable_and_sorts_after_rd01(self):
        """The installer's default is the first dataset, and existing tests and
        users mean RD-01 by it."""
        names = available_datasets()
        assert "rtklib-sample" in names
        assert names.index("rd01") < names.index("rtklib-sample")
        assert names[0] == "rd01"

    @pytest.mark.parametrize("name", RTKLIB_FILES)
    def test_every_file_is_there(self, name):
        assert (RTKLIB_SAMPLE / name).is_file()

    def test_nothing_else_is_in_the_folder(self):
        assert sorted(path.name for path in RTKLIB_SAMPLE.iterdir()) == sorted(RTKLIB_FILES)

    @pytest.mark.parametrize("name", ("07590920.05o", "30400920.05o", "brdc_0759.05n.gz"))
    def test_the_data_is_the_repositorys_own_copy_of_rtklibs(self, name):
        """One provenance record covers both copies, so they must not drift."""
        repository = Path(__file__).resolve().parent / "data" / "rtklib" / name
        assert (RTKLIB_SAMPLE / name).read_bytes() == repository.read_bytes()

    def test_the_licence_notice_travels_with_the_data(self):
        text = (RTKLIB_SAMPLE / "RTKLIB-license.txt").read_text(encoding="utf-8")
        assert "BSD 2-clause" in text and "T. Takasu" in text

    def test_the_build_ships_every_file_whatever_its_suffix(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "geocomp_build", Path(__file__).resolve().parent.parent / "scripts" / "build.py"
        )
        build = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(build)

        shipped = {path.name for path in build.collect_files() if RTKLIB_SAMPLE in path.parents}
        assert shipped == set(RTKLIB_FILES)

    def test_the_readme_names_the_stations_the_data_holds(self):
        text = (RTKLIB_SAMPLE / "README.md").read_text(encoding="utf-8")
        assert "3040" in text and "0759" in text
        markers = {
            name: next(
                line[:60].strip()
                for line in (RTKLIB_SAMPLE / name).read_text(encoding="latin-1").splitlines()
                if line.endswith("MARKER NAME")
            )
            for name in ("07590920.05o", "30400920.05o")
        }
        assert markers == {"07590920.05o": "0759", "30400920.05o": "3040"}


LOOP = DATASETS_DIR / "rd04-loop"
LOOP_FILES = ("README.es.md", "README.md", "README.pt_BR.md", "loop.csv", "mapping.json", "profiles.json")


def _build_module():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "geocomp_build", Path(__file__).resolve().parent.parent / "scripts" / "build.py"
    )
    build = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build)
    return build


class TestTheLevellingLoop:
    """The third: RD-04's loop with one spoiled reading, the levelling tutorial (P13-2).

    The README's numbers are checked by following it through the algorithms, in
    ``tests/qgis/test_levelling_tutorial.py``. What is checked here is that the
    files are the ones the reference generator makes, so the tutorial and the
    tested data cannot drift apart.
    """

    def test_it_is_offered_after_the_two_before_it(self):
        """Appended: the datasets already published keep their indices."""
        assert available_datasets().index("rd04-loop") == 2

    def test_nothing_else_is_in_the_folder(self):
        assert sorted(path.name for path in LOOP.iterdir()) == sorted(LOOP_FILES)

    def test_the_field_book_is_the_generators(self):
        with open(LOOP / "loop.csv", encoding="utf-8", newline="") as handle:
            assert list(csv.reader(handle)) == levelling.tutorial_rows()

    def test_the_blunder_is_where_the_readme_says(self):
        """12 mm on one foresight of BM2-BM4: the generator's, and the README's."""
        assert levelling.TUTORIAL_LOOP["blunder_on"] == "BM2-BM4"
        assert levelling.TUTORIAL_LOOP["blunder"] == pytest.approx(0.012)
        readme = (LOOP / "README.md").read_text(encoding="utf-8")
        assert "One foresight on the line BM2 to BM4\nwas written down 12 mm wrong." in readme

    def test_the_heights_it_was_made_from_are_the_ones_it_states(self):
        readme = (LOOP / "README.md").read_text(encoding="utf-8")
        stated = ", ".join(f"{name} {levelling.HEIGHTS[name]:.3f} m" for name in ("BM1", "BM2", "BM4"))
        assert stated in " ".join(readme.split())

    def test_the_profiles_are_the_reference_level(self):
        library = ProfileLibrary.from_dict(json.loads((LOOP / "profiles.json").read_text(encoding="utf-8")))
        reference = ProfileLibrary()
        reference.add_level(levelling.profile())
        assert library.to_dict() == reference.to_dict()
        assert library.default_level == levelling.profile().id

    def test_the_mapping_covers_every_column(self):
        mapping = LevelMapping.from_dict(json.loads((LOOP / "mapping.json").read_text(encoding="utf-8")))
        mapped = {column.column for column in mapping.columns if column.column}
        assert mapped == set(levelling.TUTORIAL_COLUMNS)

    def test_the_book_reads_with_its_own_mapping_and_profiles(self):
        """Step 1 of the README, without QGIS: no row rejected, no column left over."""
        mapping = LevelMapping.from_dict(json.loads((LOOP / "mapping.json").read_text(encoding="utf-8")))
        library = ProfileLibrary.from_dict(json.loads((LOOP / "profiles.json").read_text(encoding="utf-8")))
        result = read_level_book_csv(LOOP / "loop.csv", mapping, library=library)
        assert (len(result.setups), len(result.lines)) == (10, 3)
        assert result.rejected_rows == ()
        assert [line.id for line in result.lines] == ["BM1-BM2", "BM2-BM4", "BM4-BM1"]

    def test_the_build_ships_every_file(self):
        build = _build_module()
        shipped = {path.name for path in build.collect_files() if LOOP in path.parents}
        assert shipped == set(LOOP_FILES)


DAM = DATASETS_DIR / "rd08-dam"
DAM_FILES = (
    "README.es.md",
    "README.md",
    "README.pt_BR.md",
    "epoch-2025.json",
    "epoch-2026.json",
    "thresholds.csv",
)


class TestTheMonitoredDam:
    """The fourth: RD-08's synthetic two epochs, the monitoring tutorial (P13-3).

    As for the loop, the README's numbers are checked by following it, in
    ``tests/qgis/test_monitoring_tutorial.py``; here, that the files are the
    generator's and ship.
    """

    def test_it_is_offered_after_the_three_before_it(self):
        assert available_datasets().index("rd08-dam") == 3

    def test_nothing_else_is_in_the_folder(self):
        assert sorted(path.name for path in DAM.iterdir()) == sorted(DAM_FILES)

    @pytest.mark.parametrize("name", sorted(monitoring.TUTORIAL_EPOCHS))
    def test_each_epoch_is_the_generators(self, name):
        """To a nanometre rather than byte for byte: the distances are computed,
        and the last bit of a computed float is not promised across platforms."""
        from geocomp.core.models import Network

        shipped = Network.from_dict(json.loads((DAM / name).read_text(encoding="utf-8")))
        made = monitoring.tutorial_networks()[name]
        assert shipped.epoch == made.epoch and shipped.epoch is not None
        assert shipped.crs == made.crs
        assert set(shipped.stations) == set(made.stations) == set(monitoring.LAYOUT)
        for station in made.stations.values():
            values = shipped.stations[station.id].approx_position.values
            for a, b in zip(values, station.approx_position.values, strict=True):
                assert a.value == pytest.approx(b.value, abs=1e-9)
        assert list(shipped.observations) == list(made.observations)
        for a, b in zip(shipped.observations.values(), made.observations.values(), strict=True):
            assert a.values[0].value == pytest.approx(b.values[0].value, abs=1e-9)
            assert a.values[0].std_dev == pytest.approx(monitoring.SIGMA)

    def test_the_thresholds_are_the_generators(self):
        assert (DAM / "thresholds.csv").read_text(encoding="utf-8") == monitoring.tutorial_thresholds()

    def test_the_motion_is_where_the_readme_says(self):
        readme = " ".join((DAM / "README.md").read_text(encoding="utf-8").split())
        (station, (east, north)), = monitoring.TUTORIAL_MOTION.items()
        assert north < 0 < east
        assert f"**{station} moved {east * 1000:.0f} mm east and {-north * 1000:.0f} mm south.**" in readme

    def test_the_build_ships_every_file(self):
        build = _build_module()
        shipped = {path.name for path in build.collect_files() if DAM in path.parents}
        assert shipped == set(DAM_FILES)


GRAVITY = DATASETS_DIR / "rd07-usgs"
GRAVITY_FILES = (
    "GSadjust-LICENSE.md",
    "README.es.md",
    "README.md",
    "README.pt_BR.md",
    "Test2.txt",
    "Test3.txt",
    "profiles-calibrated.json",
    "profiles.json",
)


class TestTheUsgsSurveys:
    """The fifth: two of USGS's synthetic surveys, the gravimetry tutorial (P13-4).

    The first tutorial dataset that is someone else's, with a truth someone else
    published; ``tests/qgis/test_gravimetry_tutorial.py`` follows it.
    """

    def test_it_is_offered_after_the_four_before_it(self):
        assert available_datasets().index("rd07-usgs") == 4

    def test_nothing_else_is_in_the_folder(self):
        assert sorted(path.name for path in GRAVITY.iterdir()) == sorted(GRAVITY_FILES)

    @pytest.mark.parametrize("survey", usgs.TUTORIAL_SURVEYS)
    def test_each_survey_is_the_vendored_copy_byte_for_byte(self, survey):
        """``tests/data/rd07/PROVENANCE.md`` pins the vendored copies to USGS's
        commit by SHA-256, so the shipped ones are pinned through them."""
        name = f"{survey}.txt"
        assert (GRAVITY / name).read_bytes() == (usgs.DATA / name).read_bytes()

    @pytest.mark.parametrize(
        ("name", "calibrated"), (("profiles.json", False), ("profiles-calibrated.json", True))
    )
    def test_the_profiles_are_the_generators(self, name, calibrated):
        shipped = ProfileLibrary.from_dict(json.loads((GRAVITY / name).read_text(encoding="utf-8")))
        assert shipped.to_dict() == usgs.tutorial_profiles(calibrated=calibrated).to_dict()

    def test_the_calibration_undoes_test_3s_stated_scale(self):
        library = ProfileLibrary.from_dict(
            json.loads((GRAVITY / "profiles-calibrated.json").read_text(encoding="utf-8"))
        )
        (meter,) = library.gravimeters.values()
        stated = usgs.CASES["Test3"]["calibration"]["B44"]
        assert meter.calibration_factor.value * stated == pytest.approx(1.0, abs=1e-15)
        assert usgs.CASES["Test2"]["calibration"]["B44"] == 1.0

    def test_the_licence_travels_with_the_surveys(self):
        text = " ".join((GRAVITY / "GSadjust-LICENSE.md").read_text(encoding="utf-8").split())
        assert "CC0 1.0 Universal" in text and "United States Geological Survey" in text

    def test_the_build_ships_every_file(self):
        build = _build_module()
        shipped = {path.name for path in build.collect_files() if GRAVITY in path.parents}
        assert shipped == set(GRAVITY_FILES)


COMBINED = DATASETS_DIR / "combined-curitiba"
COMBINED_FILES = ("README.es.md", "README.md", "README.pt_BR.md", "gnss.json", "total-station.json")


class TestTheCombinedSurvey:
    """The sixth: GNSS and a total station that overstated its precision, the integration tutorial (P13-5)."""

    def test_it_is_offered_last(self):
        assert available_datasets().index("combined-curitiba") == 5

    def test_nothing_else_is_in_the_folder(self):
        assert sorted(path.name for path in COMBINED.iterdir()) == sorted(COMBINED_FILES)

    @pytest.mark.parametrize("name", ("gnss.json", "total-station.json"))
    def test_each_network_is_the_generators(self, name):
        """To a nanometre, as RD-08's: the values are computed, and the GNSS
        noise comes through a Cholesky factor."""
        from geocomp.core.models import Network
        from tests.test_integration import tutorial_inputs

        shipped = Network.from_dict(json.loads((COMBINED / name).read_text(encoding="utf-8")))
        made = tutorial_inputs()[name]
        assert (shipped.crs, shipped.epoch) == (made.crs, made.epoch)
        assert list(shipped.observations) == list(made.observations)
        for a, b in zip(shipped.observations.values(), made.observations.values(), strict=True):
            assert a.type is b.type
            for x, y in zip(a.values, b.values, strict=True):
                assert x.value == pytest.approx(y.value, abs=1e-9)
                assert x.variance == pytest.approx(y.variance, rel=1e-12)

    def test_the_total_station_states_less_than_it_measured(self):
        """The tutorial's premise, held to the generator: drawn with three times
        the standard deviations it states."""
        from tests import combined_network as field
        from tests.test_integration import TUTORIAL_NOISE

        shipped = json.loads((COMBINED / "total-station.json").read_text(encoding="utf-8"))
        distances = [o for o in shipped["observations"] if o["type"] == "SLOPE_DISTANCE"]
        assert distances
        for observation in distances:
            assert observation["values"][0]["variance"] == pytest.approx(field.SIGMA_DISTANCE**2)
        assert TUTORIAL_NOISE == 3.0

    def test_the_build_ships_every_file(self):
        build = _build_module()
        shipped = {path.name for path in build.collect_files() if COMBINED in path.parents}
        assert shipped == set(COMBINED_FILES)
