# SPDX-License-Identifier: GPL-2.0-or-later
"""Joining DynAdjust's four output files into one Solution (FR-323).

Tier 1. The network comes from the same DynaML files the adjustment was run on,
so these exercise the whole round trip GeoComp performs in practice: write the
input, run the engine, read the output back onto the network that produced it.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from geocomp.core.errors import DataError
from geocomp.core.models.solution import DatumDefinition, SolutionKind
from geocomp.core.uncertainty import UncertaintyMode
from geocomp.engines.dynadjust.read_dynaml import read_dynaml
from geocomp.engines.dynadjust.read_output import AngularFormat, read_apu, read_measurements
from geocomp.engines.dynadjust.solution import (
    adjusted_stations,
    datum_definition,
    printed_rows,
    read_solution,
)

DATA = Path(__file__).parent / "data" / "dynadjust"
OUTPUT = DATA / "output"


@pytest.fixture
def network():
    return read_dynaml(DATA / "sample-stn.xml", DATA / "sample-msr.xml").network


@pytest.fixture
def solution(network):
    return read_solution(
        OUTPUT / "sample.adj",
        network=network,
        apu_path=OUTPUT / "sample.apu",
        cor_path=OUTPUT / "sample.cor",
        angular_format=AngularFormat.HP,
    )


class TestTheAssembledSolution:
    def test_it_is_an_adjustment_of_the_network_it_was_read_against(self, solution, network) -> None:
        assert solution.kind is SolutionKind.ADJUSTMENT
        assert solution.network_id == network.id
        assert solution.crs == "GDA2020"

    def test_it_carries_the_epoch_the_file_states(self, solution) -> None:
        """FR-105: never inferred, and a solution cannot exist without one."""
        assert solution.epoch.instant is not None
        assert solution.epoch.instant.date().isoformat() == "2020-01-01"

    def test_every_station_arrives_with_its_covariance_and_ellipse(self, solution) -> None:
        assert len(solution.adjusted_stations) == 11
        for station in solution.adjusted_stations:
            assert station.covariance is not None
            assert station.covariance.matrix.shape == (3, 3)
            assert station.ellipse is not None
            assert station.positional_uncertainty is not None
            assert station.correction is not None

    def test_the_results_cover_every_printed_component(self, solution) -> None:
        assert len(solution.observation_results) == 36
        assert {result.observation_id for result in solution.observation_results} == {
            row[0] for row in printed_rows(read_dynaml(
                DATA / "sample-stn.xml", DATA / "sample-msr.xml").network)
        }

    def test_the_uncertainty_is_rigorous_not_approximate(self, solution) -> None:
        """FR-203. DynAdjust propagates the full matrix; GeoComp approximated
        nothing, and must not label it as though it had."""
        assert solution.uncertainty_mode is UncertaintyMode.RIGOROUS

    def test_an_all_free_adjustment_defines_no_datum(self, solution) -> None:
        assert solution.datum_definition is DatumDefinition.NONE

    def test_a_held_station_makes_it_constrained(self) -> None:
        rows, _ = __import__(
            "geocomp.engines.dynadjust.read_output", fromlist=["read_coordinates"]
        ).read_coordinates(OUTPUT / "angles.adj")
        assert any("C" in row.constraint for row in rows)
        assert datum_definition(rows) is DatumDefinition.CONSTRAINED


class TestTheParameterCovariance:
    def test_the_full_matrix_is_assembled_when_the_apu_carries_it(self, solution) -> None:
        matrix = solution.parameter_covariance
        assert matrix is not None
        assert matrix.matrix.shape == (33, 33)
        assert matrix.labels[:3] == ("211302450.x", "211302450.y", "211302450.z")

    def test_it_is_positive_definite(self, solution) -> None:
        """The real check on where the cross-blocks went.

        Symmetry is by construction -- the assembler writes the transpose into
        the mirrored block -- so it proves nothing. Positive definiteness does:
        a block placed at the wrong pair, or transposed the wrong way, gives a
        symmetric matrix that is not a covariance.
        """
        eigenvalues = np.linalg.eigvalsh(solution.parameter_covariance.matrix)
        assert eigenvalues.min() > 0.0

    def test_its_diagonal_blocks_are_the_per_station_matrices(self, solution) -> None:
        stations, _ = read_apu(OUTPUT / "sample.apu", angular_format=AngularFormat.HP)
        matrix = solution.parameter_covariance.matrix
        for position, station in enumerate(stations):
            block = matrix[3 * position : 3 * position + 3, 3 * position : 3 * position + 3]
            assert np.array_equal(block, station.covariance.matrix)

    def test_no_full_matrix_is_invented_when_the_apu_lacks_one(self, network) -> None:
        """Assembling a block-diagonal from the per-station blocks would assert
        that every pair of stations is uncorrelated, which is false in every
        adjusted network."""
        solution = read_solution(
            OUTPUT / "sample.adj",
            network=network,
            apu_path=OUTPUT / "sample-no-covariances.apu",
            angular_format=AngularFormat.HP,
        )
        assert solution.parameter_covariance is None
        # The per-station blocks are still there. Only what was never written
        # is missing.
        assert all(
            station.covariance is not None for station in solution.adjusted_stations
        )

    def test_a_local_frame_matrix_is_not_attached_to_cartesian_components(
        self, network
    ) -> None:
        """``--output-apu-vcv-units 1`` gives an e/n/up matrix. The ``.adj``'s
        table here gives latitude, longitude and height. The two do not describe
        each other, so the matrix is not attached to them."""
        solution = read_solution(
            OUTPUT / "alt-flags.adj",
            network=network,
            apu_path=OUTPUT / "alt-flags.apu",
            angular_format=AngularFormat.DEGREES,
        )
        assert all(station.covariance is None for station in solution.adjusted_stations)
        # The ellipse and positional uncertainty are frame-free, so they stay.
        assert all(station.ellipse is not None for station in solution.adjusted_stations)


class TestMatchingObservationsBack:
    def test_a_cluster_is_printed_under_its_own_type_letter(self, network) -> None:
        """The rule that cannot be read off an observation: four baselines in one
        cluster print as ``X``, a lone one as ``G``, though both are baselines."""
        codes = {identifier.split("-")[0]: code for identifier, code, _ in printed_rows(network)}
        assert codes["X0"] == "X"
        assert codes["Y1"] == "Y"
        assert codes["G2"] == "G"

    def test_a_row_that_disagrees_with_its_observation_is_refused(self, network) -> None:
        """Order is used, never trusted. Reversing the rows must not produce
        results quietly attributed to the wrong observations."""
        rows = read_measurements(OUTPUT / "sample.adj")
        from geocomp.engines.dynadjust.read_output import match_observations

        with pytest.raises(DataError) as excinfo:
            match_observations(list(reversed(rows)), network)
        assert excinfo.value.code == "data.dynadjust_measurement_type_mismatch"

    def test_the_wrong_number_of_rows_is_refused(self, network) -> None:
        rows = read_measurements(OUTPUT / "sample.adj")
        from geocomp.engines.dynadjust.read_output import match_observations

        with pytest.raises(DataError) as excinfo:
            match_observations(rows[:-1], network)
        assert excinfo.value.code == "data.dynadjust_measurement_count_mismatch"

    def test_the_residual_is_the_correction_the_engine_reported(self, solution) -> None:
        first = solution.observation_results[0]
        assert first.residual == pytest.approx(-0.0001)
        assert first.standardised_residual == pytest.approx(-0.37)
        assert first.adjusted_value == pytest.approx(-17395.5540)


class TestRefusals:
    def test_an_apu_naming_an_unknown_station_is_refused(self) -> None:
        from geocomp.engines.dynadjust.read_output import read_coordinates

        rows, _ = read_coordinates(OUTPUT / "sample.adj")
        stations, _ = read_apu(OUTPUT / "sample.apu", angular_format=AngularFormat.HP)
        with pytest.raises(DataError) as excinfo:
            adjusted_stations(rows[:-1], stations)
        assert excinfo.value.code == "data.dynadjust_uncertainty_for_an_unknown_station"

    def test_files_from_different_versions_are_refused(self, network, tmp_path: Path) -> None:
        apu = tmp_path / "other.apu"
        apu.write_text(
            (OUTPUT / "sample.apu").read_text().replace("1.4.0, Release", "1.4.9, Release", 1)
        )
        with pytest.raises(DataError) as excinfo:
            read_solution(
                OUTPUT / "sample.adj",
                network=network,
                apu_path=apu,
                angular_format=AngularFormat.HP,
            )
        assert excinfo.value.code == "data.dynadjust_output_versions_disagree"


def test_the_stations_survive_without_an_apu_at_all(network) -> None:
    """A run that was not asked for uncertainties still yields a solution."""
    solution = read_solution(OUTPUT / "sample.adj", network=network, angular_format=AngularFormat.HP)
    assert len(solution.adjusted_stations) == 11
    assert all(station.covariance is None for station in solution.adjusted_stations)
    assert all(station.ellipse is None for station in solution.adjusted_stations)
    assert solution.parameter_covariance is None
    assert len(solution.observation_results) == 36
