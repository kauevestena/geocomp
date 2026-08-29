# SPDX-License-Identifier: GPL-2.0-or-later
"""Reading DynAdjust's output files (FR-322, FR-323).

Tier 1: every fixture in ``tests/data/dynadjust/output`` is real ``dnaadjust``
output committed to the repository, so these run wherever Python does and need
no engine.

The cross-checks are the point. A parser test that asserts a number equals the
number in the file it just read proves only that ``float`` works. What these do
instead is check the files *against each other* -- the ``.cor`` corrections
against the ``.adj`` ones, the ``.apu`` covariance rotated into the local frame
against the ``.adj`` standard deviations, the ellipse against the covariance it
was computed from -- because agreement between quantities DynAdjust derived
independently is evidence the right columns were read.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest

from geocomp.core.errors import DataError, ValidationError
from geocomp.core.models.position import CoordinateSystem, HeightType
from geocomp.core.units import Unit
from geocomp.engines.dynadjust.columns import Column, ColumnPlan, take_name
from geocomp.engines.dynadjust.read_output import (
    AngularFormat,
    measurement_angular_format,
    read_adj,
    read_apu,
    read_coordinates,
    read_cor,
    read_measurements,
    read_preamble,
    read_statistics,
    read_xyz,
    station_angular_format,
)

DATA = Path(__file__).parent / "data" / "dynadjust" / "output"


def _first_by_code(rows: list) -> dict:
    """The first row of each type letter. A dict comprehension keeps the last."""
    first: dict = {}
    for row in rows:
        first.setdefault(row.code, row)
    return first

SAMPLE_ADJ = DATA / "sample.adj"
SAMPLE_APU = DATA / "sample.apu"
SAMPLE_COR = DATA / "sample.cor"
SAMPLE_XYZ = DATA / "sample.xyz"
ALT_ADJ = DATA / "alt-flags.adj"
ALT_APU = DATA / "alt-flags.apu"
ANGLES_ADJ = DATA / "angles.adj"


def local_rotation(latitude: float, longitude: float) -> np.ndarray:
    """Cartesian to local e/n/up, the rotation DynAdjust applies internally."""
    sin_lat, cos_lat = math.sin(latitude), math.cos(latitude)
    sin_lon, cos_lon = math.sin(longitude), math.cos(longitude)
    return np.array(
        [
            [-sin_lon, cos_lon, 0.0],
            [-sin_lat * cos_lon, -sin_lat * sin_lon, cos_lat],
            [cos_lat * cos_lon, cos_lat * sin_lon, sin_lat],
        ]
    )


class TestThePreamble:
    def test_it_reports_the_frame_and_epoch_the_file_states(self) -> None:
        preamble = read_preamble(SAMPLE_ADJ.read_text().splitlines())
        assert preamble.reference_frame == "GDA2020"
        assert preamble.epoch is not None
        assert preamble.epoch.instant is not None
        assert preamble.epoch.instant.date().isoformat() == "2020-01-01"
        assert preamble.epoch.label == "01.01.2020"

    def test_a_version_it_has_not_been_checked_against_is_refused(self, tmp_path: Path) -> None:
        """FR-302. Reading an unknown layout produces numbers, not an error."""
        text = SAMPLE_ADJ.read_text().replace("1.4.0, Release", "9.9.0, Release", 1)
        path = tmp_path / "future.adj"
        path.write_text(text)
        with pytest.raises(DataError) as excinfo:
            read_coordinates(path)
        assert excinfo.value.code == "data.dynadjust_unsupported_output_version"
        assert excinfo.value.context["received"] == "9.9.0"

    def test_a_patch_release_is_accepted(self, tmp_path: Path) -> None:
        """The gate is on major.minor: refusing a bug-fix release helps nobody."""
        text = SAMPLE_ADJ.read_text().replace("1.4.0, Release", "1.4.7, Release", 1)
        path = tmp_path / "patch.adj"
        path.write_text(text)
        assert len(read_coordinates(path)[0]) == 11

    def test_a_file_that_is_not_dynadjust_output_is_refused(self, tmp_path: Path) -> None:
        path = tmp_path / "not-an-adj.txt"
        path.write_text("Station  Latitude  Longitude\nBEEC  1.0  2.0\n")
        with pytest.raises(DataError) as excinfo:
            read_coordinates(path)
        assert excinfo.value.code == "data.dynadjust_unsupported_output_version"


class TestTheCoordinateTable:
    def test_the_default_layout_yields_cartesian_positions(self) -> None:
        rows, preamble = read_coordinates(SAMPLE_ADJ)
        assert preamble.coordinate_types == "PLHhXYZ"
        assert len(rows) == 11
        assert rows[0].position.system is CoordinateSystem.CARTESIAN
        assert [q.unit for q in rows[0].position.values] == [Unit.METRE] * 3
        assert rows[0].position.values[0].value == pytest.approx(-4251956.4559)

    def test_the_components_carry_no_uncertainty_of_their_own(self) -> None:
        """SD(e,n,up) are local-frame metres; X, Y and Z are not.

        Attaching one to the other would put a real number on the wrong axis,
        so the position's components are exact and the local figures are kept
        beside them.
        """
        row = read_coordinates(SAMPLE_ADJ)[0][0]
        assert [q.variance for q in row.position.values] == [0.0, 0.0, 0.0]
        assert row.local_sigmas == pytest.approx((0.0049, 0.0051, 0.0136))

    def test_the_constraint_and_description_survive(self) -> None:
        rows, _ = read_coordinates(SAMPLE_ADJ)
        assert rows[0].constraint == "FFF"
        by_id = {row.station_id: row for row in rows}
        assert by_id["380700500"].description == "WHITFIELD PM   50"
        assert by_id["356000780"].description == ""

    def test_corrections_are_absent_rather_than_zero_when_not_requested(self) -> None:
        assert read_coordinates(SAMPLE_ADJ)[0][0].correction is not None
        assert read_coordinates(ALT_ADJ)[0][0].correction is None

    def test_the_xyz_file_carries_the_same_table_as_the_adj(self) -> None:
        """Same writer, same columns -- so one reader, and it must agree."""
        for adj, xyz in zip(read_coordinates(SAMPLE_ADJ)[0], read_xyz(SAMPLE_XYZ), strict=True):
            assert adj.station_id == xyz.station_id
            assert [q.value for q in adj.position.values] == [q.value for q in xyz.position.values]
            assert adj.local_sigmas == xyz.local_sigmas
            assert adj.correction == xyz.correction

    def test_a_different_coordinate_type_string_changes_the_columns(self) -> None:
        """``--stn-coord-types PLH``: three columns where the default has seven."""
        rows, preamble = read_coordinates(ALT_ADJ)
        assert preamble.coordinate_types == "PLH"
        assert rows[0].position.system is CoordinateSystem.GEODETIC
        assert rows[0].position.height_type is HeightType.ORTHOMETRIC
        assert [q.unit for q in rows[0].position.values] == [Unit.RADIAN, Unit.RADIAN, Unit.METRE]

    def test_the_two_runs_agree_on_the_same_station(self) -> None:
        """One in HP notation and cartesian, the other decimal degrees and geodetic.

        They are adjustments of the same network with different print options, so
        the same station must come out at the same place -- which is only true if
        both angular formats were read correctly.
        """
        geodetic = {row.station_id: row for row in read_coordinates(ALT_ADJ)[0]}
        uncertainty = {
            item.station_id: item
            for item in read_apu(SAMPLE_APU, angular_format=AngularFormat.HP)[0]
        }
        for name, row in geodetic.items():
            assert row.position.values[0].value == pytest.approx(
                uncertainty[name].latitude, abs=1e-10
            )
            assert row.position.values[1].value == pytest.approx(
                uncertainty[name].longitude, abs=1e-10
            )


class TestAngularFormats:
    def test_decimal_degrees_are_not_read_as_hp(self) -> None:
        """The trap: both readings are valid HP, and they differ by 0.2 degrees here."""
        row = read_coordinates(ALT_ADJ)[0][0]
        assert math.degrees(row.position.values[0].value) == pytest.approx(-36.552865187)
        # What reading it as HP would have given, for contrast.
        assert math.degrees(row.position.values[0].value) != pytest.approx(-36.9235, abs=1e-3)

    def test_the_format_comes_from_the_recorded_command_line(self) -> None:
        preamble = read_preamble(ALT_ADJ.read_text().splitlines())
        assert preamble.option("angular-stn-type") == "1"
        assert station_angular_format(preamble) is AngularFormat.DEGREES

    def test_a_file_with_no_command_line_and_no_declaration_is_refused(self) -> None:
        """An ``.apu`` records no command line, so it cannot say. It must not guess."""
        preamble = read_preamble(SAMPLE_APU.read_text().splitlines())
        assert preamble.command_line == ""
        with pytest.raises(DataError) as excinfo:
            station_angular_format(preamble)
        assert excinfo.value.code == "data.dynadjust_angular_format_unknown"

    def test_the_apu_still_reads_without_one_and_omits_only_the_angles(self) -> None:
        """Rule 2: what cannot be established is absent, and blocks nothing else."""
        stations, _ = read_apu(SAMPLE_APU)
        assert stations[0].latitude is None
        assert stations[0].longitude is None
        assert stations[0].covariance.matrix[0, 0] == pytest.approx(9.722934021e-05)
        assert stations[0].ellipse.semi_major == pytest.approx(0.0051)

    def test_a_cartesian_table_needs_no_angular_format_at_all(self) -> None:
        """A ``.xyz`` records no command line either, yet is read exactly."""
        assert read_preamble(SAMPLE_XYZ.read_text().splitlines()).command_line == ""
        assert read_xyz(SAMPLE_XYZ)[0].position.system is CoordinateSystem.CARTESIAN

    def test_reading_decimal_degrees_as_hp_is_usually_caught(self) -> None:
        """A partial safety net, worth knowing the shape of.

        HP notation cannot hold minutes of 60 or more, so a decimal-degree value
        whose fraction is 0.60 or greater is refused rather than mis-converted.
        That covers a good share of a real file but is **not** a guarantee:
        ``145.55`` is valid read either way, and would come back wrong. It is a
        reason to declare the format, not a substitute for declaring it.
        """
        with pytest.raises(ValidationError) as excinfo:
            read_apu(ALT_APU, angular_format=AngularFormat.HP)
        assert excinfo.value.code == "validation.hp_angle_minutes_out_of_range"

    def test_degrees_minutes_seconds_with_symbols_is_refused_not_mangled(self) -> None:
        preamble = read_preamble(
            (ALT_ADJ.read_text().replace("--angular-stn-type 1", "--dms-msr-format 1")).splitlines()
        )
        with pytest.raises(DataError) as excinfo:
            measurement_angular_format(preamble)
        assert excinfo.value.code == "data.dynadjust_angular_measurement_format_unsupported"


class TestTheMeasurementTable:
    def test_every_row_is_read(self) -> None:
        rows = read_measurements(SAMPLE_ADJ)
        assert len(rows) == 36
        assert {row.code for row in rows} == {"X", "Y", "G"}

    def test_a_cluster_yields_one_row_per_component(self) -> None:
        rows = [row for row in read_measurements(SAMPLE_ADJ) if row.code == "Y"]
        assert [row.component for row in rows[:3]] == ["X", "Y", "Z"]
        assert rows[0].stations == ("BEEC",)

    def test_the_optional_t_statistic_column_is_found_from_the_header(self) -> None:
        assert read_measurements(SAMPLE_ADJ)[0].t_statistic is None
        assert read_measurements(ALT_ADJ)[0].t_statistic == pytest.approx(-0.99)

    def test_angular_values_are_radians_and_their_corrections_are_too(self) -> None:
        """The two are in *different* formats in the file.

        ``Measured`` is degrees/minutes/seconds; ``Correction`` and the three
        precisions beside it are seconds of arc. Reading the second as the first
        is a factor-of-3600 error on every angular residual.
        """
        rows = _first_by_code(read_measurements(ANGLES_ADJ))
        zenith = rows["V"]
        assert zenith.angular
        assert math.degrees(zenith.measured) == pytest.approx(89 + 53 / 60 + 56.7283 / 3600)
        assert math.degrees(zenith.measured_sigma) * 3600 == pytest.approx(20.0)
        assert abs(math.degrees(zenith.correction) * 3600) < 1.0

    def test_a_linear_measurement_stays_in_metres(self) -> None:
        rows = _first_by_code(read_measurements(ANGLES_ADJ))
        assert not rows["S"].angular
        assert rows["S"].measured == pytest.approx(7523.1230)
        assert rows["L"].measured == pytest.approx(17.6929)

    def test_the_component_decides_angularity_not_the_type(self) -> None:
        """A ``Y`` cluster prints latitude, longitude *and* a height under one type."""
        rows = read_measurements(ANGLES_ADJ)
        assert all(row.component in {"", "X", "Y", "Z"} for row in rows)
        # The three-station horizontal angle has no component letter, so the type
        # decides -- and it is angular.
        angle = next(row for row in rows if row.code == "A")
        assert angle.component == ""
        assert angle.angular
        assert angle.stations == ("BASE", "NORTH", "EAST")

    def test_dimensionless_statistics_are_never_converted(self) -> None:
        angular = next(row for row in read_measurements(ANGLES_ADJ) if row.angular)
        assert abs(angular.n_statistic or 0.0) < 10.0
        assert (angular.pelzer or 0.0) > 0.0

    def test_an_adj_without_the_measurement_table_yields_nothing(self, tmp_path: Path) -> None:
        """``--output-adj-msr`` was not passed. A configuration fact, not a failure."""
        text = SAMPLE_ADJ.read_text()
        path = tmp_path / "no-msr.adj"
        path.write_text(text[: text.index("Adjusted Measurements")])
        assert read_measurements(path) == []


class TestTheStatistics:
    def test_the_summary_is_read(self) -> None:
        statistics = read_statistics(SAMPLE_ADJ)
        assert statistics.n_observations == 36
        assert statistics.n_parameters == 33
        assert statistics.degrees_of_freedom == 3
        assert statistics.converged is True
        assert statistics.iterations == 2

    def test_sigma_zero_is_the_variance_factor_not_its_root(self) -> None:
        """Chi-squared over degrees of freedom, which is what the file's own
        numbers give: 0.41 / 3 = 0.137, printed as 0.138."""
        statistics = read_statistics(SAMPLE_ADJ)
        assert statistics.variance_factor_aposteriori == pytest.approx(0.138)
        assert statistics.variance_factor_aposteriori == pytest.approx(
            0.41 / statistics.degrees_of_freedom, abs=2e-3
        )

    def test_the_chi_square_test_keeps_both_critical_values(self) -> None:
        test = read_statistics(SAMPLE_ADJ).global_test
        assert test is not None
        assert (test.critical_low, test.statistic, test.critical_high) == pytest.approx(
            (0.072, 0.138, 3.116)
        )
        assert test.confidence == pytest.approx(0.95)
        assert test.passed is True

    def test_the_maximum_correction_is_the_largest_component(self) -> None:
        """What DynAdjust compares against ``--iteration-threshold``, not the
        magnitude of the vector it prints."""
        assert read_statistics(SAMPLE_ADJ).max_correction == pytest.approx(4.7e-05)

    def test_a_failure_to_converge_is_not_read_as_success(self) -> None:
        statistics = read_statistics(ANGLES_ADJ)
        assert statistics.converged is False
        assert statistics.global_test is not None
        assert statistics.global_test.passed is False

    def test_a_file_with_no_solution_is_refused(self, tmp_path: Path) -> None:
        text = SAMPLE_ADJ.read_text()
        path = tmp_path / "unfinished.adj"
        path.write_text(text[: text.index("SOLUTION")])
        with pytest.raises(DataError) as excinfo:
            read_statistics(path)
        assert excinfo.value.code == "data.dynadjust_output_has_no_solution"


class TestPositionalUncertainty:
    def test_every_station_gets_its_own_matrix(self) -> None:
        stations, preamble = read_apu(SAMPLE_APU, angular_format=AngularFormat.HP)
        assert len(stations) == 11
        assert preamble.variance_units == "XYZ"
        assert preamble.full_covariance is True
        assert stations[0].covariance.labels == ("211302450.x", "211302450.y", "211302450.z")

    def test_the_own_matrix_is_symmetric(self) -> None:
        """It is written as an upper triangle over three lines. Getting the
        unpacking wrong gives a matrix that is not symmetric, or is symmetric
        about the wrong elements."""
        for station in read_apu(SAMPLE_APU, angular_format=AngularFormat.HP)[0]:
            matrix = station.covariance.matrix
            assert np.allclose(matrix, matrix.T, rtol=0, atol=0)

    def test_the_covariance_reproduces_the_adj_standard_deviations(self) -> None:
        """The strongest check available without a second implementation.

        The ``.apu`` gives a cartesian covariance and the ``.adj`` gives local
        standard deviations; DynAdjust derived them from the same matrix by the
        rotation below. Agreeing to the ``.adj``'s own print precision means the
        right nine numbers were read into the right nine places.
        """
        sigmas = {row.station_id: row.local_sigmas for row in read_coordinates(SAMPLE_ADJ)[0]}
        for station in read_apu(SAMPLE_APU, angular_format=AngularFormat.HP)[0]:
            rotation = local_rotation(station.latitude, station.longitude)
            local = rotation @ station.covariance.matrix @ rotation.T
            assert np.sqrt(np.diag(local)) == pytest.approx(
                np.array(sigmas[station.station_id]), abs=1e-4
            )

    def test_the_ellipse_reproduces_the_covariance_it_came_from(self) -> None:
        for station in read_apu(SAMPLE_APU, angular_format=AngularFormat.HP)[0]:
            rotation = local_rotation(station.latitude, station.longitude)
            local = rotation @ station.covariance.matrix @ rotation.T
            values = np.linalg.eigvalsh(local[:2, :2])
            assert math.sqrt(values[1]) == pytest.approx(station.ellipse.semi_major, abs=1e-4)
            assert math.sqrt(values[0]) == pytest.approx(station.ellipse.semi_minor, abs=1e-4)

    def test_the_orientation_is_hp_even_when_the_coordinates_are_not(self) -> None:
        """``PrintPosUncertainty`` writes ``RadtoDms(azimuth)`` with no branch on
        ``--angular-stn-type``, so the alt-flags file has decimal-degree
        coordinates and an HP orientation in the same row."""
        stations, _ = read_apu(ALT_APU, angular_format=AngularFormat.DEGREES)
        by_id = {station.station_id: station for station in stations}
        assert math.degrees(by_id["324900360"].ellipse.orientation) == pytest.approx(
            79 + 47 / 60 + 24 / 3600, abs=1e-6
        )

    def test_the_cross_covariances_are_read_when_present(self) -> None:
        stations, _ = read_apu(SAMPLE_APU, angular_format=AngularFormat.HP)
        first = stations[0]
        assert len(first.cross) == 10
        assert set(first.cross) == {s.station_id for s in stations[1:]}
        assert first.cross["MYRT"].shape == (3, 3)

    def test_a_cross_block_is_not_forced_symmetric(self) -> None:
        """It is a block of the full matrix, not a variance of anything, so it
        has no reason to be symmetric -- and reading it as a triangle would
        silently make it so."""
        block = read_apu(SAMPLE_APU, angular_format=AngularFormat.HP)[0][0].cross["MYRT"]
        assert not np.allclose(block, block.T, atol=1e-12)

    def test_without_all_covariances_there_are_none(self) -> None:
        stations, preamble = read_apu(ALT_APU, angular_format=AngularFormat.DEGREES)
        assert preamble.full_covariance is False
        assert all(not station.cross for station in stations)

    def test_local_variance_units_are_reported_and_labelled(self) -> None:
        stations, preamble = read_apu(ALT_APU, angular_format=AngularFormat.DEGREES)
        assert preamble.variance_units == "ENU"
        assert stations[0].covariance.labels == ("211302450.e", "211302450.n", "211302450.up")

    def test_local_variances_need_no_rotation_to_match_the_adj(self) -> None:
        """The other half of the rotation test: with ``--output-apu-vcv-units 1``
        the matrix is already local, so its diagonal *is* the ``.adj``'s SDs."""
        sigmas = {row.station_id: row.local_sigmas for row in read_coordinates(ALT_ADJ)[0]}
        for station in read_apu(ALT_APU, angular_format=AngularFormat.DEGREES)[0]:
            assert np.sqrt(np.diag(station.covariance.matrix)) == pytest.approx(
                np.array(sigmas[station.station_id]), abs=1e-4
            )


class TestCorrections:
    def test_the_corrections_match_the_adj_table(self) -> None:
        """Two files, two writers, one set of numbers."""
        rows = {row.station_id: row for row in read_coordinates(SAMPLE_ADJ)[0]}
        corrections = read_cor(SAMPLE_COR)
        assert len(corrections) == 11
        for correction in corrections:
            expected = rows[correction.station_id].correction
            assert expected is not None
            assert (correction.east, correction.north, correction.up) == pytest.approx(expected)

    def test_its_angles_are_separated_fields_not_hp(self) -> None:
        """The ``.cor`` writes ``84 42 21`` where the ``.adj`` writes
        ``84.4221``. A reader that assumed one format for both divides by 100
        in one of the two files."""
        first = read_cor(SAMPLE_COR)[0]
        assert math.degrees(first.azimuth) == pytest.approx(84 + 42 / 60 + 21 / 3600)
        assert math.degrees(first.vertical_angle) == pytest.approx(89 + 58 / 60 + 39 / 3600)

    def test_a_negative_vertical_angle_keeps_its_sign(self) -> None:
        by_id = {item.station_id: item for item in read_cor(SAMPLE_COR)}
        assert math.degrees(by_id["BNLA"].vertical_angle) == pytest.approx(
            -(80 + 25 / 60 + 58 / 3600)
        )

    def test_the_distance_columns_are_metres(self) -> None:
        first = read_cor(SAMPLE_COR)[0]
        assert first.slope_distance == pytest.approx(9.1344)
        assert first.horizontal_distance == pytest.approx(0.0036)


class TestStationNames:
    def test_a_short_name_needs_no_help(self) -> None:
        assert take_name("BEEC                FFF   -36.20").name == "BEEC"

    def test_a_name_that_fills_its_column_is_refused_rather_than_split(self) -> None:
        """``std::setw`` pads but never truncates, so a 21-character name runs
        into the constraint field with no separator at all."""
        with pytest.raises(DataError) as excinfo:
            take_name("A STATION WITH SPACESCCC   -36.33")
        assert excinfo.value.code == "data.dynadjust_station_name_fills_its_column"

    def test_the_known_names_resolve_it(self) -> None:
        resolution = take_name(
            "A STATION WITH SPACESCCC   -36.33",
            known={"A STATION WITH SPACES", "BEEC"},
        )
        assert resolution.name == "A STATION WITH SPACES"
        assert resolution.resolved is True

    def test_the_longest_match_wins(self) -> None:
        """``BEEC`` must not shadow ``BEECROFT``."""
        assert (
            take_name("BEECROFT            FFF", known={"BEEC", "BEECROFT"}).name == "BEECROFT"
        )

    def test_a_name_not_in_the_known_set_is_refused(self) -> None:
        with pytest.raises(DataError) as excinfo:
            take_name("MYRT                FFF", known={"BEEC"})
        assert excinfo.value.code == "data.dynadjust_unknown_station_in_output"

    def test_the_known_names_do_not_change_an_ordinary_file(self) -> None:
        plain = read_coordinates(SAMPLE_ADJ)[0]
        names = {row.station_id for row in plain}
        with_names = read_coordinates(SAMPLE_ADJ, known=names)[0]
        assert [row.station_id for row in with_names] == [row.station_id for row in plain]
        assert [row.local_sigmas for row in with_names] == [row.local_sigmas for row in plain]


class TestTheColumnPlan:
    def test_a_plan_reproduces_the_header_it_describes(self) -> None:
        """The plans are built from the widths in DynAdjust's own headers, so
        this is what proves the transcription right."""
        header = next(
            line for line in SAMPLE_ADJ.read_text().splitlines() if line.startswith("M Station 1")
        )
        from geocomp.engines.dynadjust.read_output import measurement_plan

        assert measurement_plan(header).header().rstrip() == header.rstrip()

    def test_an_unrecognised_header_is_refused_with_both_versions(self, tmp_path: Path) -> None:
        text = SAMPLE_ADJ.read_text().replace("      SD(e)", "     SD(E) ", 1)
        path = tmp_path / "moved.adj"
        path.write_text(text)
        with pytest.raises(DataError) as excinfo:
            read_coordinates(path)
        assert excinfo.value.code == "data.dynadjust_unrecognised_output_layout"
        assert "SD(e)" in excinfo.value.context["expected"]

    def test_a_short_row_reads_its_trailing_columns_as_absent(self) -> None:
        plan = ColumnPlan((Column("A", 4, "l"), Column("B", 4), Column("C", 4)))
        assert plan.fields("ab    12") == ("ab", "12", "")


def test_read_adj_returns_the_four_parts_of_one_file() -> None:
    rows, measurements, statistics, preamble = read_adj(SAMPLE_ADJ)
    assert len(rows) == 11
    assert len(measurements) == 36
    assert statistics.degrees_of_freedom == 3
    assert preamble.version == "1.4.0"
