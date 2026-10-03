# SPDX-License-Identifier: GPL-2.0-or-later
"""The sparse path gives the dense path's answer (NFR-008; P12c-4).

ADR-0008: the NumPy path is the reference and defines what "correct" means;
where SciPy is used, the two are tested against each other. These do that for
everything an adjustment reports -- coordinates, the variance factor, each
station's covariance and ellipse, the redundancy numbers, the w-tests, the
minimal detectable biases and the external reliability -- over networks with
held, weighted and free datums, direction sets, a 1D levelling loop and a
geocentric survey with a correlated baseline cluster.

``pytest --sparse`` runs the whole suite with every adjustment on this path;
CI's QGIS job does, so a consumer of the run's matrices that only works on the
dense ones fails there. This file is where the two paths meet directly.

Needs SciPy; skipped without it -- the refusal that a machine without SciPy
gets instead is ``tests/test_network_scale.py``.
"""

from __future__ import annotations

import math
from dataclasses import replace

import numpy as np
import pytest

pytest.importorskip("scipy")

from geocomp.core.adjustment import Frame, sparse
from geocomp.core.adjustment import scale as scale_module
from geocomp.core.adjustment.least_squares import AdjustmentOptions, adjust, to_solution
from geocomp.core.errors import ComputationError
from geocomp.core.models import (
    ConstraintMode,
    ConstraintSpec,
    CoordinateSystem,
    DatumDefinition,
    Epoch,
    Network,
    Observation,
    ObservationType,
    Position,
    Provenance,
    Station,
)
from geocomp.core.monitoring.compare import compare
from geocomp.core.preanalysis import simulate
from geocomp.core.statistics.reliability import reliability
from geocomp.core.statistics.tests import data_snooping
from geocomp.core.uncertainty import Quantity
from geocomp.core.units import Unit
from tests.combined_network import survey
from tests.monitoring_network import epoch as monitoring_epoch
from tests.networks import (
    free_triangulateration,
    free_trilateration,
    levelling_loop,
    triangulateration,
    trilateration,
)


def braced_grid(side: int, *, seed: int = 1) -> Network:
    """A *side* x *side* grid, 100 m apart, every square braced both ways, two
    corners held: the shape of the P12c measurements, small."""
    rng = np.random.default_rng(seed)
    network = Network(id=f"grid-{side}", crs="LOCAL")
    truth = {}
    for i in range(side):
        for j in range(side):
            name = f"P{i}_{j}"
            truth[name] = (1000.0 + 100.0 * j + rng.uniform(-5, 5), 2000.0 + 100.0 * i + rng.uniform(-5, 5))
            held = (i, j) in ((0, 0), (0, 1))
            start = tuple(v + (0.0 if held else rng.uniform(-0.05, 0.05)) for v in truth[name])
            position = Position(
                values=tuple(
                    Quantity.from_std_dev(v, 0.0 if held else 0.5, Unit.METRE) for v in (*start, 0.0)
                ),
                system=CoordinateSystem.PROJECTED,
                crs="LOCAL",
            )
            constraint = (
                ConstraintSpec(
                    mode=ConstraintMode.FIXED,
                    components=frozenset({"easting", "northing"}),
                    position=position,
                )
                if held
                else ConstraintSpec()
            )
            network.add_station(Station(id=name, approx_position=position, constraint=constraint))
    count = 0
    for i in range(side):
        for j in range(side):
            for di, dj in ((0, 1), (1, 0), (1, 1), (1, -1)):
                if 0 <= i + di < side and 0 <= j + dj < side:
                    a, b = f"P{i}_{j}", f"P{i + di}_{j + dj}"
                    count += 1
                    network.add_observation(
                        Observation(
                            id=f"d{count}",
                            type=ObservationType.HORIZONTAL_DISTANCE,
                            stations=(a, b),
                            values=(
                                Quantity.from_std_dev(
                                    math.dist(truth[a], truth[b]) + rng.normal(0, 0.003), 0.003, Unit.METRE
                                ),
                            ),
                        )
                    )
    return network


def _plane(datum=DatumDefinition.CONSTRAINED):
    return AdjustmentOptions(frame=Frame.PLANE_2D, datum=datum)


CASES = {
    "trilateration, held": (lambda: trilateration().network, _plane()),
    "triangulateration, held": (lambda: triangulateration().network, _plane()),
    "trilateration, free": (
        lambda: free_trilateration().network,
        _plane(DatumDefinition.INNER_CONSTRAINT),
    ),
    "triangulateration, free": (
        lambda: free_triangulateration().network,
        _plane(DatumDefinition.INNER_CONSTRAINT),
    ),
    "levelling loop": (
        lambda: levelling_loop().network,
        AdjustmentOptions(frame=Frame.HEIGHT_1D, datum=DatumDefinition.CONSTRAINED),
    ),
    "geocentric survey, correlated baselines and a direction set": (
        survey,
        AdjustmentOptions(frame=Frame.GEOCENTRIC_3D),
    ),
    "braced grid": (lambda: braced_grid(7), _plane()),
}


def _both(case: str):
    build, options = CASES[case]
    network = build()
    return (
        network,
        adjust(network, replace(options, solver="dense")),
        adjust(network, replace(options, solver="sparse")),
    )


def _statistics(run):
    snooping = data_snooping(
        run.residuals,
        run.cofactor_residuals,
        run.system.weight,
        run.system.row_labels,
        variance_factor=run.variance_factor_aposteriori,
        degrees_of_freedom=run.degrees_of_freedom,
    )
    found = reliability(
        run.cofactor_residuals,
        run.system.weight,
        run.system.design,
        run.cofactor_parameters,
        run.system.row_labels,
    )
    return snooping, found


class TestTheTwoPathsAgree:
    @pytest.fixture(scope="class", params=list(CASES))
    def case(self, request):
        return request.param

    @pytest.fixture(scope="class")
    def runs(self, case):
        return _both(case)

    def test_the_sparse_path_ran(self, case, runs):
        _network, dense, sparse_run = runs
        assert (dense.solver, sparse_run.solver) == ("dense", "sparse")
        assert sparse_run.method.startswith("sparse-")
        assert dense.method.endswith("bordered") == sparse_run.method.endswith("bordered")

    def test_coordinates_and_the_variance_factor(self, case, runs):
        _network, dense, sparse_run = runs
        assert sparse_run.degrees_of_freedom == dense.degrees_of_freedom
        np.testing.assert_allclose(sparse_run.parameters, dense.parameters, rtol=1e-12, atol=1e-9)
        np.testing.assert_allclose(sparse_run.residuals, dense.residuals, rtol=0, atol=1e-9)
        assert sparse_run.variance_factor_aposteriori == pytest.approx(
            dense.variance_factor_aposteriori, rel=1e-8
        )
        if dense.condition_number < 1e12:
            assert sparse_run.condition_number == pytest.approx(dense.condition_number, rel=1e-6)
        else:
            # A free network's N is singular, and both paths report the ratio of
            # its largest eigenvalue to a rounding error: enormous, and noise.
            assert sparse_run.condition_number > 1e12

    def test_each_owners_covariance_block(self, case, runs):
        _network, dense, sparse_run = runs
        scale = np.abs(np.diag(dense.cofactor_parameters)).max()
        np.testing.assert_allclose(
            sparse_run.cofactor_parameters.diagonal(),
            np.diag(dense.cofactor_parameters),
            rtol=0,
            atol=1e-9 * scale,
        )
        for station in dense.layout.station_ids():
            columns = list(dense.layout.station_columns(station).values())
            index = np.ix_(columns, columns)
            np.testing.assert_allclose(
                sparse_run.parameter_covariance[index],
                dense.parameter_covariance[index],
                rtol=0,
                atol=1e-9 * scale * dense.variance_factor_aposteriori,
            )

    def test_an_entry_between_two_owners_is_solved_for(self, case, runs):
        _network, dense, sparse_run = runs
        size = dense.layout.size
        scale = np.abs(np.diag(dense.cofactor_parameters)).max()
        for i, j in ((0, size - 1), (size // 2, 0), (size - 1, size // 3)):
            assert sparse_run.cofactor_parameters[i, j] == pytest.approx(
                dense.cofactor_parameters[i, j], abs=1e-9 * scale
            )

    def test_the_residual_cofactor_and_the_redundancy(self, case, runs):
        _network, dense, sparse_run = runs
        np.testing.assert_allclose(sparse_run.redundancy, dense.redundancy, rtol=0, atol=1e-9)
        assert float(np.sum(sparse_run.redundancy)) == pytest.approx(dense.degrees_of_freedom, abs=1e-8)
        scale = np.abs(np.diag(dense.cofactor_residuals)).max()
        np.testing.assert_allclose(
            sparse_run.cofactor_residuals.diagonal(),
            np.diag(dense.cofactor_residuals),
            rtol=0,
            atol=1e-9 * scale,
        )
        # Within each block of P, all of it -- a baseline's 3x3, not only its diagonal.
        blocks = sparse_run.cofactor_residuals
        for rows, matrices in blocks.groups.values():
            for index, block in zip(rows, matrices, strict=True):
                np.testing.assert_allclose(
                    block, dense.cofactor_residuals[np.ix_(index, index)], rtol=0, atol=1e-9 * scale
                )

    def test_the_w_tests_and_the_reliability(self, case, runs):
        _network, dense, sparse_run = runs
        (snooping_dense, reliability_dense), (snooping_sparse, reliability_sparse) = (
            _statistics(dense),
            _statistics(sparse_run),
        )
        assert snooping_sparse.statistics.keys() == snooping_dense.statistics.keys()
        for row, statistic in snooping_dense.statistics.items():
            # Absolute below 1e-6: a residual of a rounding error's size has a
            # w of a rounding error's size, and its digits are noise on both paths.
            assert snooping_sparse.statistics[row] == pytest.approx(statistic, rel=1e-7, abs=1e-6)
        for ours, theirs in zip(reliability_sparse.results, reliability_dense.results, strict=True):
            if theirs.minimal_detectable_bias is None:
                assert ours.minimal_detectable_bias is None
                continue
            assert ours.minimal_detectable_bias == pytest.approx(theirs.minimal_detectable_bias, rel=1e-7)
            assert ours.external_effect == pytest.approx(theirs.external_effect, rel=1e-6, abs=1e-12)

    def test_the_solution_and_its_ellipses(self, case, runs):
        network, dense, sparse_run = runs
        _build, options = CASES[case]

        def solution(run):
            return to_solution(
                run,
                network,
                solution_id=run.solver,
                crs="LOCAL",
                epoch=Epoch.from_decimal_year(2026.0),
                datum=options.datum,
                provenance=Provenance.now(algorithm_id="test"),
            )

        ours, theirs = solution(sparse_run), solution(dense)
        assert ours.parameter_covariance is None, "the full matrix is never formed, nor stood in for"
        assert theirs.parameter_covariance is not None
        assert ours.provenance.parameters["solver"] == "sparse"
        assert ours.statistics.n_constraints == theirs.statistics.n_constraints
        for a, b in zip(ours.adjusted_stations, theirs.adjusted_stations, strict=True):
            assert a.station_id == b.station_id
            if b.ellipse is not None:
                assert a.ellipse.semi_major == pytest.approx(b.ellipse.semi_major, rel=1e-8)
                assert a.ellipse.semi_minor == pytest.approx(b.ellipse.semi_minor, rel=1e-7, abs=1e-12)
            np.testing.assert_allclose(a.covariance.matrix, b.covariance.matrix, rtol=1e-8, atol=1e-15)


class TestTheSweep:
    """The inverse is found column chunk by column chunk; nothing may depend on where they fall."""

    def test_many_chunks_give_the_answer_one_does(self, monkeypatch):
        network = braced_grid(6)
        dense = adjust(network, replace(_plane(), solver="dense"))
        monkeypatch.setattr(sparse, "CHUNK_BYTES", 1)  # 16 columns a chunk, the floor
        many = adjust(network, replace(_plane(), solver="sparse"))
        assert many.layout.size > 3 * 16
        np.testing.assert_allclose(many.redundancy, dense.redundancy, rtol=0, atol=1e-9)
        np.testing.assert_allclose(
            many.cofactor_parameters.diagonal(), np.diag(dense.cofactor_parameters), rtol=1e-9
        )
        _, found = _statistics(many)
        _, expected = _statistics(dense)
        for ours, theirs in zip(found.results, expected.results, strict=True):
            assert ours.external_effect == pytest.approx(theirs.external_effect, rel=1e-6)

    def test_a_short_column_cache_still_gives_every_entry(self, monkeypatch):
        monkeypatch.setattr(sparse, "CACHED_COLUMNS", 2)
        network = trilateration().network
        dense = adjust(network, replace(_plane(), solver="dense"))
        run = adjust(network, replace(_plane(), solver="sparse"))
        size = run.layout.size
        for i in range(size):
            for j in range(size):
                assert run.cofactor_parameters[i, j] == pytest.approx(
                    dense.cofactor_parameters[i, j], abs=1e-12
                )


class TestAnUndeterminedNetwork:
    """FR-226 on the sparse path: the diagnosis, not a factorisation error."""

    @pytest.mark.parametrize("examined", ["densely", "by Lanczos iteration"])
    def test_it_names_the_undetermined_directions(self, monkeypatch, examined):
        if examined != "densely":
            monkeypatch.setattr(sparse, "DENSE_EXAMINATION", 0)
        network = free_trilateration().network
        with pytest.raises(ComputationError) as dense:
            adjust(network, replace(_plane(), solver="dense"))
        with pytest.raises(ComputationError) as ours:
            adjust(network, replace(_plane(), solver="sparse"))
        assert ours.value.code == dense.value.code == "computation.rank_deficient_normal_matrix"
        # Two: the network's azimuth fixes its rotation and leaves the two
        # translations. Each path may name a different basis of that plane.
        assert ours.value.context["deficiency"] == dense.value.context["deficiency"] == 2
        assert all("undetermined combination of" in text for text in ours.value.context["undetermined"])

    def test_by_lanczos_the_condition_number_is_the_dense_one(self, monkeypatch):
        monkeypatch.setattr(sparse, "DENSE_EXAMINATION", 0)
        network = braced_grid(5)
        dense = adjust(network, replace(_plane(), solver="dense"))
        run = adjust(network, replace(_plane(), solver="sparse"))
        assert run.condition_number == pytest.approx(dense.condition_number, rel=1e-6)


class TestTheAutomaticChoice:
    @pytest.fixture
    def everything_is_large(self, monkeypatch):
        monkeypatch.setattr(scale_module, "SPARSE_ABOVE", -1)

    def test_a_network_past_the_threshold_is_adjusted_sparsely(self, everything_is_large):
        run = adjust(braced_grid(4), _plane())
        assert run.solver == "sparse"

    def test_a_design_is_simulated_on_the_same_path(self, monkeypatch):
        network = trilateration().network
        dense = simulate(network, frame=Frame.PLANE_2D)
        monkeypatch.setattr(scale_module, "SPARSE_ABOVE", -1)
        ours = simulate(network, frame=Frame.PLANE_2D)
        for a, b in zip(ours.stations, dense.stations, strict=True):
            assert a.ellipse.semi_major == pytest.approx(b.ellipse.semi_major, rel=1e-8)
            assert a.positional_uncertainty == pytest.approx(b.positional_uncertainty, rel=1e-8)
        for a, b in zip(ours.reliability.results, dense.reliability.results, strict=True):
            assert a.redundancy == pytest.approx(b.redundancy, abs=1e-9)
            if b.external_effect is not None:
                assert a.external_effect == pytest.approx(b.external_effect, rel=1e-6)

    def test_a_comparison_of_two_sparse_epochs_says_what_they_lack(self, monkeypatch):
        """The displacements are the dense path's; the stations of one epoch are
        taken as uncorrelated, and the comparison says so rather than leaving a
        correlation silently out."""

        def epochs():
            return monitoring_epoch(2025.0), monitoring_epoch(2026.0, moves={"R3": (0.015, 0.010)}, seed=3)

        dense = compare(*epochs())
        monkeypatch.setattr(scale_module, "SPARSE_ABOVE", -1)
        first, second = epochs()
        assert first.parameter_covariance is None
        comparison = compare(first, second)
        np.testing.assert_allclose(comparison.difference, dense.difference, rtol=0, atol=1e-9)
        codes = {finding.code: finding for finding in comparison.findings}
        assert codes["station_blocks_only"].context["solutions"] == [first.id, second.id]
        assert "uncorrelated" in str(codes["station_blocks_only"])

    @pytest.mark.dense_only

    def test_a_comparison_of_two_dense_epochs_has_no_such_finding(self):
        comparison = compare(monitoring_epoch(2025.0), monitoring_epoch(2026.0, seed=3))
        assert "station_blocks_only" not in {finding.code for finding in comparison.findings}
