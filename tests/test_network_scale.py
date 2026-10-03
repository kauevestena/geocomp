# SPDX-License-Identifier: GPL-2.0-or-later
"""Which solver a network gets, and the refusal without SciPy (NFR-008; P12c-4).

``specs/06-adjustment-core.md`` section 2.4 and ADR-0008. Tier 1: nothing here
needs SciPy, because the refusal is exactly what a machine without it must get,
and CI's degraded job runs this file where SciPy is absent.

The sparse path itself, and its agreement with the dense one, is
``tests/test_sparse_adjustment.py``.
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from geocomp.core.adjustment import Frame
from geocomp.core.adjustment import scale as scale_module
from geocomp.core.adjustment.blocks import (
    BlockDiagonal,
    inverse_diagonal,
    product_diagonal,
    quadratic_form,
)
from geocomp.core.adjustment.least_squares import AdjustmentOptions, adjust, to_solution
from geocomp.core.adjustment.normal_equations import assemble, build_weight_matrix, weight_blocks
from geocomp.core.adjustment.scale import (
    AUTO,
    DENSE,
    SPARSE,
    SPARSE_ABOVE,
    choose_solver,
    dense_footprint,
    dense_limit,
    physical_memory,
)
from geocomp.core.adjustment.variance_components import estimate_variance_components
from geocomp.core.errors import ComputationError, ValidationError
from geocomp.core.models import DatumDefinition, Epoch, Provenance
from tests.combined_network import survey
from tests.networks import trilateration

GiB = 1 << 30


def _random_blocks(rng, size: int) -> list[tuple[np.ndarray, np.ndarray]]:
    """Symmetric positive definite blocks of sizes 1 to 3 over scattered rows."""
    order = rng.permutation(size)
    blocks, start = [], 0
    while start < size:
        width = min(int(rng.integers(1, 4)), size - start)
        rows = order[start : start + width]
        root = rng.normal(size=(width, width))
        blocks.append((rows, root @ root.T + width * np.eye(width)))
        start += width
    return blocks


class TestBlockDiagonal:
    @pytest.fixture
    def pair(self):
        rng = np.random.default_rng(8)
        blocks = BlockDiagonal.from_blocks(17, _random_blocks(rng, 17))
        return blocks, blocks.to_dense()

    def test_it_holds_the_matrix_it_was_given(self, pair):
        blocks, dense = pair
        assert np.array_equal(blocks.to_dense(), dense)
        assert np.allclose(dense, dense.T)
        for row in range(17):
            for column in range(17):
                assert blocks[row, column] == dense[row, column]
                assert blocks.holds(row, column) == (dense[row, column] != 0.0)

    def test_its_arithmetic_is_the_dense_arithmetic(self, pair):
        blocks, dense = pair
        vector = np.arange(17.0) - 5.0
        columns = np.random.default_rng(1).normal(size=(17, 4))
        assert np.allclose(blocks @ vector, dense @ vector)
        assert np.allclose(vector @ blocks, vector @ dense)
        assert np.allclose(blocks @ columns, dense @ columns)
        assert np.allclose(blocks.inverse().to_dense(), np.linalg.inv(dense))
        assert np.allclose((blocks @ blocks.inverse()).to_dense(), np.eye(17))
        assert np.allclose((2.5 * blocks).to_dense(), 2.5 * dense)
        assert np.allclose((blocks - blocks.inverse()).to_dense(), dense - np.linalg.inv(dense))
        assert np.allclose(blocks.diagonal(), np.diag(dense))
        index = np.ix_([3, 0, 9], [9, 3])
        assert np.array_equal(blocks[index], dense[index])

    def test_the_helpers_give_one_answer_for_either_form(self, pair):
        blocks, dense = pair
        other = blocks.inverse()
        assert np.allclose(product_diagonal(blocks, other), product_diagonal(dense, other.to_dense()))
        assert np.allclose(product_diagonal(dense, dense), np.diag(dense @ dense))
        assert np.allclose(inverse_diagonal(blocks), inverse_diagonal(dense))
        vector = np.linspace(-1.0, 2.0, 17)
        rows = [1, 4, 5, 11, 16]
        assert quadratic_form(blocks, vector) == pytest.approx(quadratic_form(dense, vector))
        # A block straddling the chosen rows contributes only its part inside them.
        assert quadratic_form(blocks, vector, rows) == pytest.approx(quadratic_form(dense, vector, rows))

    def test_a_row_in_two_blocks_is_refused(self):
        with pytest.raises(ValueError, match="two blocks"):
            BlockDiagonal.from_blocks(3, [(np.array([0, 1]), np.eye(2)), (np.array([1]), np.eye(1))])

    def test_the_weight_matrix_is_its_blocks(self):
        """One source for both paths: the dense P is the blocks laid out, so the two
        cannot weight an observation differently. The combined survey has its
        three baselines in one correlated cluster among single rows."""
        network = survey()
        run = adjust(network, AdjustmentOptions(frame=Frame.GEOCENTRIC_3D, solver=DENSE))
        observations = list(network.active_observations)
        labels = [label for label in run.system.row_labels if not label[0].startswith("constraint:")]
        dense = build_weight_matrix(observations, network.clusters, labels)
        blocks = BlockDiagonal.from_blocks(len(labels), weight_blocks(observations, network.clusters, labels))
        assert np.array_equal(blocks.to_dense(), dense)
        assert max(blocks.groups) == 9, "three correlated baselines, one 9x9 cluster"


class TestTheChoice:
    def test_the_footprint_is_what_the_dense_path_holds(self):
        # Measured in P12c: 3,422 rows and 1,796 parameters (900 stations) peaked
        # at 698 MiB; the estimate errs high, which is the side to err on.
        assert dense_footprint(3422, 1796) / 2**20 == pytest.approx(772.8, abs=0.1)
        assert dense_footprint(39402, 19996) > 70 * GiB

    @pytest.mark.dense_only

    def test_a_small_network_is_dense_and_a_large_one_sparse(self):
        small = choose_solver(AUTO, 342, 196, limit=8 * GiB, scipy=True)
        large = choose_solver(AUTO, 39402, 19996, limit=8 * GiB, scipy=True)
        assert (small.solver, large.solver) == (DENSE, SPARSE)
        assert small.footprint <= SPARSE_ABOVE < large.footprint

    def test_without_scipy_the_dense_path_is_kept_while_it_fits(self):
        middle = choose_solver(AUTO, 6000, 3000, limit=8 * GiB, scipy=False)
        assert middle.footprint > SPARSE_ABOVE
        assert middle.solver == DENSE

    def test_without_scipy_a_network_that_does_not_fit_is_refused_naming_scipy(self):
        with pytest.raises(ComputationError) as caught:
            choose_solver(AUTO, 39402, 19996, limit=8 * GiB, scipy=False)
        assert caught.value.code == "computation.adjustment_needs_scipy"
        context = caught.value.context
        assert "SciPy" in context["expected"] and "DynAdjust" in context["expected"]
        assert context["footprint_mib"] > context["limit_mib"] == 8192

    def test_the_dense_path_asked_for_is_refused_when_it_cannot_be_held(self):
        assert choose_solver(DENSE, 39402, 19996, limit=200 * GiB, scipy=True).solver == DENSE
        with pytest.raises(ComputationError) as caught:
            choose_solver(DENSE, 39402, 19996, limit=8 * GiB, scipy=True)
        assert caught.value.code == "computation.adjustment_too_large_for_dense"

    def test_the_sparse_path_asked_for_needs_scipy(self):
        assert choose_solver(SPARSE, 10, 4, scipy=True).solver == SPARSE
        with pytest.raises(ComputationError) as caught:
            choose_solver(SPARSE, 10, 4, scipy=False)
        assert caught.value.code == "computation.sparse_solver_needs_scipy"

    def test_an_unknown_solver_is_refused(self):
        with pytest.raises(ValidationError):
            choose_solver("cholmod", 10, 4)

    def test_the_machines_memory_is_read_on_every_supported_system(self):
        """NFR-003: Windows, macOS and Linux each have their own call, and CI runs
        this on all three. Unread, the limit falls back to 4 GiB."""
        memory = physical_memory()
        assert memory is not None and memory > GiB
        assert dense_limit() == memory // 2


class TestTheAdjustmentAsks:
    """Through :func:`adjust`, where the choice is made before anything is allocated."""

    @pytest.fixture
    def tiny_machine(self, monkeypatch):
        """Every network is 'large', and the dense path can hold almost nothing."""
        monkeypatch.setattr(scale_module, "SPARSE_ABOVE", 0)
        monkeypatch.setattr(scale_module, "dense_limit", lambda: 1024)
        monkeypatch.setattr(scale_module, "sparse_available", lambda: False)

    def test_without_scipy_it_refuses_before_allocating(self, tiny_machine):
        with pytest.raises(ComputationError) as caught:
            adjust(trilateration().network, AdjustmentOptions(frame=Frame.PLANE_2D))
        assert caught.value.code == "computation.adjustment_needs_scipy"

    def test_within_the_limit_it_stays_dense_without_scipy(self, monkeypatch):
        monkeypatch.setattr(scale_module, "SPARSE_ABOVE", 0)
        monkeypatch.setattr(scale_module, "sparse_available", lambda: False)
        run = adjust(trilateration().network, AdjustmentOptions(frame=Frame.PLANE_2D))
        assert run.solver == DENSE

    def test_variance_components_need_the_dense_path(self, monkeypatch):
        network = survey()
        options = AdjustmentOptions(frame=Frame.GEOCENTRIC_3D)
        with pytest.raises(ComputationError) as caught:
            estimate_variance_components(network, replace(options, solver=SPARSE))
        assert caught.value.code == "computation.variance_components_need_dense"
        # Automatic is dense, whatever the threshold says; and a network the
        # dense path cannot hold is refused by name rather than taken sparsely.
        monkeypatch.setattr(scale_module, "SPARSE_ABOVE", 0)
        monkeypatch.setattr(scale_module, "dense_limit", lambda: 1024)
        with pytest.raises(ComputationError) as caught:
            estimate_variance_components(network, options)
        assert caught.value.code == "computation.adjustment_too_large_for_dense"

    @pytest.mark.dense_only

    def test_the_solution_records_which_path_ran(self):
        reference = trilateration()
        run = adjust(reference.network, AdjustmentOptions(frame=Frame.PLANE_2D))
        solution = to_solution(
            run,
            reference.network,
            solution_id="s",
            crs="LOCAL",
            epoch=Epoch.from_decimal_year(2026.0),
            datum=DatumDefinition.CONSTRAINED,
            provenance=Provenance.now(algorithm_id="test", parameters={"kept": 1}),
        )
        assert solution.provenance.parameters == {"kept": 1, "solver": DENSE}
        assert solution.parameter_covariance is not None


def test_the_dense_assembly_is_unchanged_by_sharing_its_rows():
    """The P12c refactor laid the dense rows out from the shared linearisation;
    the design matrix is the one the equations give, row by row."""
    from geocomp.core.adjustment import evaluate

    reference = trilateration()
    options = AdjustmentOptions(frame=Frame.PLANE_2D)
    run = adjust(reference.network, options)
    x = run.parameters
    system = assemble(list(reference.network.active_observations), reference.network.clusters, run.layout, x)
    rows = [
        equation.to_dense(run.layout.size)
        for observation in reference.network.active_observations
        for equation in evaluate(observation, run.layout, x)
    ]
    assert np.array_equal(system.design, np.vstack(rows))
