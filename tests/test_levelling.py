# SPDX-License-Identifier: GPL-2.0-or-later
"""Geometric levelling: the three schemes, closures, weighting and the network.

``specs/10-module-levelling.md`` section 7 lists seven acceptance criteria and
the roadmap's P4 exit adds the shape of each. This module is those criteria made
executable, against RD-04 (``tests/reference_levelling.py``), whose books are
generated from known heights so a recovered height can be compared with the
truth rather than with another computation.
"""

from __future__ import annotations

import dataclasses
import math

import numpy as np
import pytest

import tests.reference_levelling as rd
from geocomp.core.adjustment import (
    DifferenceWeighting,
    ExtentKind,
    Frame,
    approximate_values,
    connected_components,
)
from geocomp.core.adjustment.least_squares import (
    AdjustmentOptions,
    adjust,
    to_observation_results,
    to_solution,
)
from geocomp.core.errors import ValidationError
from geocomp.core.geoid import Coverage, GeoidModel
from geocomp.core.instruments import LevellingClass, LevelProfile, ProfileLibrary
from geocomp.core.instruments.stochastic import (
    SIGHT_DISTANCE,
    STAFF_READING,
    SigmaSource,
    StochasticDefaults,
    resolve_sigma,
)
from geocomp.core.models import DatumDefinition, HeightType
from geocomp.core.models.epoch import Epoch
from geocomp.core.techniques.levelling import (
    Benchmark,
    LevellingLine,
    LevelSetup,
    StaffReading,
    ThreeWireReading,
    build_network,
    build_setup_network,
    empirical_reading_sigma,
    line_closure,
    loop_closure,
    normal_orthometric_correction,
    reduce_line,
    reduce_reciprocal,
    reduce_setup,
    weighting_for,
)
from geocomp.core.uncertainty import Quantity, Strategy, UncertaintyMode
from geocomp.core.units import Unit

METRE = Unit.METRE
MILLIMETRE = 1.0e-3


def _metres(value: float, sigma: float = rd.SIGMA_READING) -> Quantity:
    return Quantity.from_std_dev(value, sigma, METRE)


# -- The instrument and the class ----------------------------------------


class TestTheLevelProfile:
    def test_precision_scales_with_the_square_root_of_the_extent(self):
        level = rd.profile()
        assert level.sigma_for_length(4.0) == pytest.approx(level.sigma_per_km * 2.0)
        assert level.sigma_for_setups(9) == pytest.approx(level.sigma_per_setup * 3.0)

    def test_an_unconfigured_precision_is_none_not_zero(self):
        """A profile that says nothing has not claimed the instrument is perfect."""
        bare = LevelProfile(id="bare")
        assert bare.sigma_for_length(4.0) is None
        assert bare.sigma_for_setups(4) is None
        assert bare.reading_sigma is None

    def test_the_collimation_correction_is_zero_for_a_balanced_setup(self):
        level = rd.profile(collimation=5.0e-4)
        assert level.collimation_correction(0.0).value == 0.0

    def test_the_collimation_correction_opposes_the_imbalance(self):
        """r_true = r_obs - c*d, so dh gains -c * (d_back - d_fore)."""
        level = rd.profile(collimation=2.0e-4)
        assert level.collimation_correction(60.0).value == pytest.approx(-0.012)
        assert level.collimation_correction(-60.0).value == pytest.approx(+0.012)

    def test_an_instrument_that_corrects_itself_is_not_corrected_twice(self):
        level = rd.profile(collimation=2.0e-4, applies_collimation=True)
        assert level.collimation_correction(60.0).value == 0.0

    def test_a_class_without_a_coefficient_states_no_tolerance(self):
        """Not a large tolerance: none. The two are different statements."""
        assert LevellingClass(id="unset").permissible_misclosure(4.0) is None
        assert not LevellingClass(id="unset").has_tolerance

    def test_the_permissible_misclosure_is_k_root_l(self):
        levelling_class = rd.levelling_class(coefficient=0.008)
        assert levelling_class.permissible_misclosure(4.0) == pytest.approx(0.016)

    def test_a_negative_limit_is_refused(self):
        with pytest.raises(ValidationError) as caught:
            LevellingClass(id="bad", tolerance_coefficient=-1.0)
        assert caught.value.code == "validation.levelling_class_negative_limit"

    def test_the_library_resolves_levels_and_refuses_to_invent_one(self):
        library = ProfileLibrary()
        library.add_level(rd.profile())
        assert library.level(None).id == "rd04-level"
        with pytest.raises(ValidationError) as caught:
            ProfileLibrary().level(None)
        assert caught.value.code == "validation.no_level_profile"

    def test_a_class_is_optional_where_a_level_is_not(self):
        """A line with no stated specification still has a misclosure worth seeing."""
        assert ProfileLibrary().levelling_class(None) is None


# -- Three-wire readings --------------------------------------------------


class TestThreeWireReadings:
    def test_the_mean_is_propagated_not_sampled(self):
        """The three wires read different heights by design.

        Their sample spread is the stadia interval -- centimetres -- and using it
        as a precision would report a reading good to half a millimetre as good
        to five centimetres. The regression this guards is a real one that was
        written and caught in phase P4.
        """
        wires = ThreeWireReading(_metres(1.583), _metres(1.421), _metres(1.259))
        assert wires.mean().value == pytest.approx(1.421)
        assert wires.mean().std_dev == pytest.approx(rd.SIGMA_READING / math.sqrt(3.0))

    def test_the_half_sum_residual_is_zero_for_a_consistent_set(self):
        wires = ThreeWireReading(_metres(1.583), _metres(1.421), _metres(1.259))
        assert wires.half_sum_residual == pytest.approx(0.0, abs=1e-12)

    def test_a_misread_wire_is_caught(self):
        wires = ThreeWireReading(_metres(1.583), _metres(1.431), _metres(1.259))
        finding = wires.check(0.002, label="BS")
        assert finding is not None and finding.code == "three_wire_half_sum"

    def test_the_sight_distance_comes_from_the_interval(self):
        wires = ThreeWireReading(_metres(1.583), _metres(1.421), _metres(1.259))
        assert wires.stadia_distance(100.0).value == pytest.approx(32.4)

    def test_wires_out_of_order_are_refused(self):
        with pytest.raises(ValidationError) as caught:
            ThreeWireReading(_metres(1.259), _metres(1.421), _metres(1.583))
        assert caught.value.code == "validation.three_wire_out_of_order"

    def test_the_empirical_sigma_pools_half_sum_residuals(self):
        """var(e) = 1.5 sigma^2, so sigma_hat = sqrt(sum e^2 / 1.5n)."""
        # Shift *both* outer wires the same way: a residual that cancels between
        # them is not a residual at all, which is how the first draft of this
        # test managed to assert nothing.
        sets = [
            ThreeWireReading(_metres(1.5 + e), _metres(1.4), _metres(1.3 + e))
            for e in (0.0006, -0.0006, 0.0006, -0.0006)
        ]
        estimate, dof = empirical_reading_sigma(sets)
        assert dof == 4
        assert estimate == pytest.approx(0.0006 / math.sqrt(1.5), rel=1e-9)

    def test_the_degrees_of_freedom_are_returned_not_buried(self):
        """One set gives one degree of freedom, which is nearly worthless.

        A caller that cannot see the count cannot know that, so the count is
        part of the answer.
        """
        assert empirical_reading_sigma([])[1] == 0
        one = ThreeWireReading(_metres(1.5), _metres(1.4), _metres(1.3))
        assert empirical_reading_sigma([one])[1] == 1


# -- FR-500: equal sights -------------------------------------------------


class TestEqualSights:
    def test_a_balanced_line_recovers_the_truth_exactly(self):
        book = rd.balanced_line()
        reduction = reduce_line(book.line, rd.profile())
        assert reduction.height_difference.value == pytest.approx(book.true_difference, abs=1e-12)

    def test_a_balanced_line_recovers_the_truth_even_with_a_bad_collimation(self):
        """The whole reason equal sights is the preferred method.

        The instrument is 2e-4 rad out of adjustment -- 40 seconds of arc, badly
        out -- and the line is still exact, because the imbalance is zero.
        """
        level = rd.profile(collimation=2.0e-4)
        book = rd.balanced_line(collimation=2.0e-4)
        reduction = reduce_line(book.line, level)
        assert reduction.height_difference.value == pytest.approx(book.true_difference, abs=1e-12)

    def test_a_balanced_line_carries_no_collimation_uncertainty_either(self):
        """Not merely no correction: no *variance* contribution.

        (accumulated imbalance)^2 * var(c) is zero when the imbalance is,
        whatever var(c) is. Summing independently reduced setups would instead
        give sum(imbalance_i^2) * var(c), which is not zero for a line whose
        per-setup imbalances merely cancel.
        """
        careless = rd.profile(collimation=2.0e-4, collimation_sigma=1.0e-4)
        book = rd.balanced_line(collimation=2.0e-4)
        reduction = reduce_line(book.line, careless)
        readings_only = math.sqrt(
            sum(
                setup.backsight.reading.variance + setup.foresights[0].reading.variance
                for setup in book.line.setups
            )
        )
        assert reduction.height_difference.std_dev == pytest.approx(readings_only)
        assert reduction.is_balanced

    def test_cancelling_imbalances_cost_nothing(self):
        """+20 m at one setup and -20 m at the next is a balanced line.

        The per-setup figures are both out of tolerance and the line is not,
        which is exactly the distinction specs/10 section 2.1 draws.
        """
        book = rd.balanced_line(collimation=1.0e-4)
        first, second, third = book.line.setups
        skewed = LevellingLine(
            id="cancelling",
            setups=(
                LevelSetup(
                    id=first.id,
                    backsight=StaffReading(
                        first.backsight.station,
                        first.backsight.reading,
                        _metres(50.0, rd.SIGMA_DISTANCE),
                    ),
                    foresights=(
                        StaffReading(
                            first.foresights[0].station,
                            first.foresights[0].reading,
                            _metres(30.0, rd.SIGMA_DISTANCE),
                        ),
                    ),
                ),
                LevelSetup(
                    id=second.id,
                    backsight=StaffReading(
                        second.backsight.station,
                        second.backsight.reading,
                        _metres(30.0, rd.SIGMA_DISTANCE),
                    ),
                    foresights=(
                        StaffReading(
                            second.foresights[0].station,
                            second.foresights[0].reading,
                            _metres(50.0, rd.SIGMA_DISTANCE),
                        ),
                    ),
                ),
                third,
            ),
        )
        reduction = reduce_line(skewed, rd.profile(collimation=1.0e-4))
        assert reduction.accumulated_imbalance == pytest.approx(0.0)
        assert reduction.is_balanced

    def test_an_imbalanced_line_is_wrong_until_it_is_corrected(self):
        """The correction is worth 12 mm here, and is invisible without distances."""
        book = rd.imbalanced_line(collimation=2.0e-4)
        level = rd.profile(collimation=2.0e-4)
        reduction = reduce_line(book.line, level)

        assert reduction.accumulated_imbalance == pytest.approx(60.0)
        assert reduction.raw_height_difference.value - book.true_difference == pytest.approx(
            0.012
        )
        assert reduction.height_difference.value == pytest.approx(
            book.true_difference, abs=1e-12
        )

    def test_without_the_instrument_the_imbalance_is_reported_not_corrected(self):
        book = rd.imbalanced_line(collimation=2.0e-4)
        reduction = reduce_line(book.line, None)
        assert reduction.collimation is None
        assert reduction.height_difference.value != pytest.approx(book.true_difference)
        codes = {finding.code for finding in reduction.findings}
        assert "level_imbalance_without_instrument" in codes

    def test_the_accumulated_imbalance_is_checked_against_its_limit(self):
        book = rd.imbalanced_line(collimation=2.0e-4)
        reduction = reduce_line(
            book.line, rd.profile(collimation=2.0e-4), max_accumulated_imbalance=5.0
        )
        finding = next(
            f for f in reduction.findings if f.code == "levelling_line_accumulated_imbalance"
        )
        assert finding.value == pytest.approx(60.0)
        assert finding.threshold == pytest.approx(5.0)

    def test_a_discontinuous_line_is_refused_by_name(self):
        book = rd.balanced_line()
        first, _second, third = book.line.setups
        with pytest.raises(ValidationError) as caught:
            LevellingLine(id="broken", setups=(first, third))
        assert caught.value.code == "validation.levelling_line_discontinuous"


# -- FR-502: extreme sights -----------------------------------------------


class TestExtremeSights:
    def test_several_foresights_share_the_backsight_variance(self):
        setup, _truth = rd.extreme_sights_setup()
        reduction = reduce_setup(setup, rd.profile())
        off_diagonal = reduction.covariance.matrix[0, 1]
        assert off_diagonal == pytest.approx(setup.backsight.reading.variance)

    def test_each_difference_recovers_its_true_height(self):
        setup, truth = rd.extreme_sights_setup()
        reduction = reduce_setup(setup, rd.profile())
        for station in reduction.to_stations:
            assert reduction.height_difference(station).value == pytest.approx(
                truth[station] - truth["BM1"], abs=1e-12
            )

    def test_the_correlation_makes_a_derived_difference_better_not_worse(self):
        """specs/10 section 7 item 3, and the point of FR-104.

        The difference between two foresighted points is ``f_i - f_j``: the
        backsight cancels exactly. Treating the two as independent adds
        ``2 * sigma_b^2`` that is not there and reports an uncertainty too
        *large* -- the opposite of the usual failure, and no less wrong.
        """
        setup, truth = rd.extreme_sights_setup()
        reduction = reduce_setup(setup, rd.profile())

        correlated = reduction.between_foresights("S1", "S2")
        independent = math.hypot(
            reduction.height_difference("S1").std_dev,
            reduction.height_difference("S2").std_dev,
        )

        assert correlated.value == pytest.approx(truth["S2"] - truth["S1"], abs=1e-12)
        assert correlated.std_dev < independent
        assert correlated.variance == pytest.approx(
            independent**2 - 2.0 * setup.backsight.reading.variance
        )

    def test_the_cluster_reaches_the_adjustment(self):
        setup, _truth = rd.extreme_sights_setup()
        reduction = reduce_setup(setup, rd.profile())
        result = build_setup_network(
            [reduction], [Benchmark("BM1", Quantity.exact(rd.HEIGHTS["BM1"], METRE))]
        )
        assert len(result.network.clusters) == 1
        cluster = next(iter(result.network.clusters.values()))
        assert len(cluster.observation_ids) == 3
        assert cluster.covariance.matrix[0, 1] == pytest.approx(
            setup.backsight.reading.variance
        )

    def test_a_single_foresight_needs_no_cluster(self):
        book = rd.balanced_line()
        reduction = reduce_setup(book.line.setups[0], rd.profile())
        assert not reduction.is_clustered

    def test_a_setup_cannot_sight_the_same_station_twice(self):
        with pytest.raises(ValidationError) as caught:
            LevelSetup(
                id="s",
                backsight=StaffReading("A", _metres(1.5)),
                foresights=(StaffReading("A", _metres(1.2)),),
            )
        assert caught.value.code == "validation.level_setup_repeats_a_station"


# -- FR-501: equidistant (reciprocal) sights ------------------------------


class TestReciprocalSights:
    def test_the_systematic_error_cancels_in_the_mean(self):
        near, far, truth = rd.reciprocal_crossing(refraction=0.012)
        result = reduce_reciprocal(near, far)
        assert result.height_difference.value == pytest.approx(truth, abs=1e-12)

    def test_the_discrepancy_is_twice_the_systematic_error(self):
        near, far, _truth = rd.reciprocal_crossing(refraction=0.012)
        result = reduce_reciprocal(near, far)
        assert abs(result.discrepancy) == pytest.approx(0.024, abs=1e-12)

    def test_the_uncertainty_is_inflated_and_says_so(self):
        near, far, _truth = rd.reciprocal_crossing()
        plain = reduce_reciprocal(near, far, variance_inflation=1.0)
        inflated = reduce_reciprocal(near, far, variance_inflation=2.0)

        assert inflated.height_difference.variance == pytest.approx(
            2.0 * plain.height_difference.variance
        )
        assert inflated.height_difference.mode is UncertaintyMode.APPROXIMATE
        assert Strategy.EMPIRICAL_SCALING in inflated.height_difference.strategies
        assert "reciprocal_variance_inflated" in {f.code for f in inflated.findings}

    def test_declining_to_inflate_is_itself_reported(self):
        near, far, _truth = rd.reciprocal_crossing()
        result = reduce_reciprocal(near, far, variance_inflation=1.0)
        assert "reciprocal_variance_not_inflated" in {f.code for f in result.findings}

    def test_a_large_discrepancy_is_reported(self):
        near, far, _truth = rd.reciprocal_crossing(refraction=0.012)
        result = reduce_reciprocal(near, far, discrepancy_tolerance=0.005)
        assert "reciprocal_determinations_disagree" in {f.code for f in result.findings}

    def test_deflating_the_variance_is_refused(self):
        near, far, _truth = rd.reciprocal_crossing()
        with pytest.raises(ValidationError) as caught:
            reduce_reciprocal(near, far, variance_inflation=0.5)
        assert caught.value.code == "validation.variance_inflation_below_one"

    def test_pairs_that_do_not_describe_one_crossing_are_refused(self):
        near, _far, _truth = rd.reciprocal_crossing()
        with pytest.raises(ValidationError) as caught:
            reduce_reciprocal(near, near)
        assert caught.value.code == "validation.reciprocal_second_pair_reversed"


# -- FR-503: closures and tolerances --------------------------------------


class TestClosures:
    def test_a_line_within_tolerance_passes(self):
        book = rd.balanced_line(noise=0.0003)
        reduction = reduce_line(book.line, rd.profile())
        check = line_closure(
            reduction,
            Quantity.from_std_dev(book.true_difference, 0.0002, METRE),
            levelling_class=rd.levelling_class(),
        )
        assert check.passed is True
        assert check.was_judged
        assert abs(check.misclosure) < check.permissible

    def test_a_line_out_of_tolerance_fails_and_blocks(self):
        book = rd.balanced_line()
        reduction = reduce_line(book.line, rd.profile())
        check = line_closure(
            reduction,
            Quantity.from_std_dev(book.true_difference + 0.030, 0.0002, METRE),
            levelling_class=rd.levelling_class(),
        )
        assert check.passed is False
        finding = next(f for f in check.findings if f.code == "closure_out_of_tolerance")
        assert finding.is_blocking
        assert finding.value == pytest.approx(0.030, abs=1e-6)

    def test_with_no_tolerance_configured_there_is_no_verdict(self):
        """Three states, not two: a check that reports success when it could not
        test anything is worse than one that admits it."""
        book = rd.balanced_line()
        reduction = reduce_line(book.line, rd.profile())
        check = line_closure(reduction, Quantity.from_std_dev(book.true_difference, 0.0002, METRE))
        assert check.passed is None
        assert not check.was_judged
        assert "closure_not_judged" in {f.code for f in check.findings}

    def test_a_misclosure_consistent_with_its_own_precision_may_be_distributed(self):
        book = rd.balanced_line(noise=0.0003)
        reduction = reduce_line(book.line, rd.profile())
        check = line_closure(
            reduction,
            Quantity.from_std_dev(book.true_difference, 0.0002, METRE),
            levelling_class=rd.levelling_class(),
        )
        assert not check.looks_like_a_blunder
        assert "closure_consistent_with_its_precision" in {f.code for f in check.findings}

    def test_a_misclosure_beyond_it_says_not_to_distribute(self):
        """The judgement that makes the distribution honest.

        Proportional distribution assumes the misclosure is accumulated random
        error. When it is not, spreading it evenly is the one response
        guaranteed to hide where it came from, and GeoComp says so.
        """
        book = rd.balanced_line()
        reduction = reduce_line(book.line, rd.profile())
        check = line_closure(
            reduction,
            Quantity.from_std_dev(book.true_difference + 0.030, 0.0002, METRE),
            levelling_class=rd.levelling_class(),
        )
        assert check.looks_like_a_blunder
        assert "closure_exceeds_its_own_precision" in {f.code for f in check.findings}

    def test_the_distribution_covers_every_setup_and_sums_to_the_misclosure(self):
        book = rd.balanced_line(noise=0.0003)
        reduction = reduce_line(book.line, rd.profile())
        check = line_closure(
            reduction, Quantity.from_std_dev(book.true_difference, 0.0002, METRE)
        )
        assert len(check.distribution) == book.line.setup_count
        assert sum(share.weight for share in check.distribution) == pytest.approx(1.0)
        assert sum(share.correction for share in check.distribution) == pytest.approx(
            -check.misclosure
        )

    def test_a_loop_closes_on_itself(self):
        books, _truth = rd.loop(noise=0.0003)
        reductions = [reduce_line(book.line, rd.profile()) for book in books]
        check = loop_closure(reductions, loop_id="RD04", levelling_class=rd.levelling_class())
        assert check.kind == "loop"
        assert check.setup_count == sum(book.line.setup_count for book in books)
        assert check.passed is True

    def test_a_line_entered_backwards_still_contributes_the_right_sign(self):
        """The sign is worked out from the station ids, never asked for.

        Entering it by hand is where a loop closure goes wrong, and it goes
        wrong by exactly twice the height difference -- which looks like a
        blunder somewhere else entirely.
        """
        books, _truth = rd.loop(noise=0.0003)
        reductions = [reduce_line(book.line, rd.profile()) for book in books]
        forward = loop_closure(reductions, loop_id="f")

        last = reductions[-1]
        reversed_last = dataclasses.replace(
            last,
            line_id=f"{last.line_id}-reversed",
            from_station=last.to_station,
            to_station=last.from_station,
            height_difference=-last.height_difference,
        )
        backward = loop_closure([*reductions[:-1], reversed_last], loop_id="b")
        assert backward.misclosure == pytest.approx(forward.misclosure)

    def test_a_loop_whose_lines_do_not_chain_is_refused(self):
        books, _truth = rd.loop(noise=0.0003)
        reductions = [reduce_line(book.line, rd.profile()) for book in books]
        with pytest.raises(ValidationError) as caught:
            loop_closure([reductions[0], reductions[2], reductions[1]], loop_id="jumbled")
        assert caught.value.code == "validation.loop_discontinuous"

    def test_a_loop_with_a_blunder_fails(self):
        books, _truth = rd.loop(noise=0.0003, blunder=0.040, blunder_on="BM2-BM4")
        reductions = [reduce_line(book.line, rd.profile()) for book in books]
        check = loop_closure(reductions, loop_id="RD04", levelling_class=rd.levelling_class())
        assert check.passed is False
        assert check.looks_like_a_blunder

    def test_a_loop_that_does_not_join_up_is_refused(self):
        books, _truth = rd.loop()
        reductions = [reduce_line(book.line, rd.profile()) for book in books]
        with pytest.raises(ValidationError) as caught:
            loop_closure(reductions[:2], loop_id="open")
        assert caught.value.code == "validation.loop_does_not_close"


# -- FR-504: weighting ----------------------------------------------------


class TestWeighting:
    def test_the_model_is_k_root_extent(self):
        weighting = DifferenceWeighting(ExtentKind.LENGTH, 0.0007, METRE, "km")
        assert weighting.sigma(4.0) == pytest.approx(0.0014)
        assert weighting.apply(2.5, 4.0).std_dev == pytest.approx(0.0014)

    def test_a_uniform_model_ignores_the_extent(self):
        weighting = DifferenceWeighting(ExtentKind.NONE, 0.002, METRE)
        assert weighting.sigma(99.0) == pytest.approx(0.002)

    def test_the_same_module_weights_a_gravity_difference(self):
        """ADR-0002, Amendment 1, made executable in the weighting too.

        A gravimeter's drift accumulates with elapsed time. That this module
        expresses it without change is the evidence that it is shared machinery
        rather than levelling code with a general-sounding name.
        """
        drift = DifferenceWeighting(
            ExtentKind.DURATION, 2.0e-8, Unit.ACCELERATION, "hours"
        )
        weighted = drift.apply(1.2e-5, 4.0)
        assert weighted.unit is Unit.ACCELERATION
        assert weighted.std_dev == pytest.approx(4.0e-8)

    def test_a_unit_it_cannot_weight_is_refused(self):
        with pytest.raises(ValidationError) as caught:
            DifferenceWeighting(ExtentKind.LENGTH, 1.0, Unit.RADIAN)
        assert caught.value.code == "validation.weighting_unsupported_unit"

    def test_a_zero_coefficient_is_refused(self):
        with pytest.raises(ValidationError) as caught:
            DifferenceWeighting(ExtentKind.LENGTH, 0.0, METRE)
        assert caught.value.code == "validation.weighting_coefficient_not_positive"

    def test_an_unconfigured_coefficient_gives_no_weighting_rather_than_the_other_one(self):
        """Substituting the model the user did not choose would weight the
        network by a figure they never saw."""
        assert weighting_for("length", sigma_per_setup=0.0003) is None
        assert weighting_for("setups", sigma_per_km=0.0007) is None
        assert weighting_for("length", sigma_per_km=0.0007) is not None

    def test_an_unknown_mode_is_refused(self):
        with pytest.raises(ValidationError) as caught:
            weighting_for("vibes", sigma_per_km=0.001)
        assert caught.value.code == "validation.unknown_weighting_mode"


# -- The network ----------------------------------------------------------


def _adjusted(result, *, datum=DatumDefinition.CONSTRAINED):
    start = approximate_values(result.network, Frame.HEIGHT_1D)
    run = adjust(
        result.network,
        AdjustmentOptions(frame=Frame.HEIGHT_1D, datum=datum),
        approximate=start.values,
    )
    solution = to_solution(
        run,
        result.network,
        solution_id="rd04",
        crs="LOCAL",
        epoch=Epoch.from_decimal_year(2026.0),
        datum=datum,
        height_type=HeightType.ORTHOMETRIC,
        observation_results=to_observation_results(run),
    )
    return run, solution


def _heights(solution) -> dict[str, float]:
    return {
        station.station_id: station.position.height.value
        for station in solution.adjusted_stations
    }


class TestTheNetwork:
    def _loop_network(self, weighting=None):
        books, truth = rd.loop(noise=0.0003)
        reductions = [reduce_line(book.line, rd.profile()) for book in books]
        result = build_network(
            reductions,
            [Benchmark("BM1", Quantity.exact(rd.HEIGHTS["BM1"], METRE))],
            weighting=weighting,
        )
        return result, truth

    def test_turning_points_are_not_stations(self):
        """A turning point existed for four minutes and has no mark.

        Putting it in the network adds one parameter and one observation --
        no redundancy, no effect, and a solution cluttered with points that
        cannot be checked.
        """
        result, _truth = self._loop_network()
        assert result.network.station_ids() == {"BM1", "BM2", "BM4"}
        assert len(result.network.observations) == 3

    def test_the_adjustment_recovers_the_true_heights(self):
        result, truth = self._loop_network(weighting_for("length", sigma_per_km=0.0007))
        _run, solution = _adjusted(result)
        heights = _heights(solution)
        for station in ("BM2", "BM4"):
            assert heights[station] == pytest.approx(truth[station], abs=MILLIMETRE)

    def test_the_height_lands_in_the_height_component(self):
        """Phase P2 wrote a 1D solution into the *easting* slot.

        Every levelling result therefore reported a height of zero, and nothing
        in the suite noticed because no test read a 1D solution through its
        Position. See Frame.position_components.
        """
        result, truth = self._loop_network()
        _run, solution = _adjusted(result)
        station = next(s for s in solution.adjusted_stations if s.station_id == "BM2")
        assert station.position.height.value == pytest.approx(truth["BM2"], abs=MILLIMETRE)
        assert station.position.values[0].value == 0.0

    def test_length_and_setup_weighting_agree_on_the_heights(self):
        """specs/10 section 7 item 4.

        RD-04's loop varies its sight length between lines on purpose: with a
        constant sight length the two models are proportional to each other and
        agree trivially. Here they are genuinely different weight matrices, and
        they still agree to well inside the noise.
        """
        by_length, truth = self._loop_network(weighting_for("length", sigma_per_km=0.0007))
        by_setups, _ = self._loop_network(weighting_for("setups", sigma_per_setup=0.0003))

        first = _heights(_adjusted(by_length)[1])
        second = _heights(_adjusted(by_setups)[1])
        assert first.keys() == second.keys()
        for station in first:
            assert first[station] == pytest.approx(second[station], abs=MILLIMETRE)
            assert first[station] == pytest.approx(truth[station], abs=MILLIMETRE)

    def test_the_two_weightings_are_genuinely_different(self):
        """Guards the test above: if the weights happened to be proportional it
        would pass while comparing nothing."""
        by_length, _ = self._loop_network(weighting_for("length", sigma_per_km=0.0007))
        by_setups, _ = self._loop_network(weighting_for("setups", sigma_per_setup=0.0003))

        def ratios(result):
            values = [
                observation.value.std_dev
                for _, observation in sorted(result.network.observations.items())
            ]
            return [value / values[0] for value in values]

        assert ratios(by_length) != pytest.approx(ratios(by_setups))

    def test_the_weighting_choice_is_recorded(self):
        result, _truth = self._loop_network(weighting_for("length", sigma_per_km=0.0007))
        assert result.meta["weighting"]["kind"] == "LENGTH"
        assert "levelling_weighted_by_model" in {f.code for f in result.findings}

    def test_falling_back_to_the_propagated_uncertainty_is_recorded_too(self):
        result, _truth = self._loop_network(None)
        assert result.meta["weighting"] is None
        assert "levelling_weighted_by_propagation" in {f.code for f in result.findings}

    def test_a_free_network_has_one_datum_defect(self):
        books, _truth = rd.loop(noise=0.0003)
        reductions = [reduce_line(book.line, rd.profile()) for book in books]
        result = build_network(reductions, [])
        run, _solution = _adjusted(result, datum=DatumDefinition.INNER_CONSTRAINT)
        assert run.defect.size == 1
        assert "levelling_network_is_free" in {f.code for f in result.findings}

    def test_starting_values_are_derived_by_walking_the_differences(self):
        result, truth = self._loop_network()
        start = approximate_values(result.network, Frame.HEIGHT_1D)
        assert start.is_connected
        assert start.floating == frozenset()
        for station, values in start.values.items():
            assert values["h"] == pytest.approx(truth[station], abs=0.01)

    def test_a_network_with_nothing_known_floats_and_says_so(self):
        books, _truth = rd.loop(noise=0.0003)
        reductions = [reduce_line(book.line, rd.profile()) for book in books]
        result = build_network(reductions, [])
        start = approximate_values(result.network, Frame.HEIGHT_1D)
        assert start.floating and not start.anchored

    def test_disconnected_pieces_are_named_before_the_matrix_is_formed(self):
        books, _truth = rd.loop(noise=0.0003)
        reductions = [reduce_line(book.line, rd.profile()) for book in books]
        result = build_network(reductions[:1], [])
        setup, _ = rd.extreme_sights_setup()
        far = build_setup_network([reduce_setup(setup, rd.profile())], [])
        for station in far.network.stations.values():
            if station.id not in result.network.stations:
                result.network.add_station(station)
        pieces = connected_components(result.network, Frame.HEIGHT_1D)
        assert len(pieces) > 1

    def test_a_benchmark_the_levelling_never_reached_is_refused(self):
        books, _truth = rd.loop()
        reductions = [reduce_line(book.line, rd.profile()) for book in books]
        with pytest.raises(ValidationError) as caught:
            build_network(reductions, [Benchmark("NOWHERE", Quantity.exact(1.0, METRE))])
        assert caught.value.code == "validation.benchmark_not_in_network"

    def test_length_weighting_refuses_a_line_of_unknown_length(self):
        setups = tuple(
            LevelSetup(
                id=setup.id,
                backsight=StaffReading(setup.backsight.station, setup.backsight.reading),
                foresights=(
                    StaffReading(
                        setup.foresights[0].station, setup.foresights[0].reading
                    ),
                ),
            )
            for setup in rd.balanced_line().line.setups
        )
        reduction = reduce_line(LevellingLine(id="nodist", setups=setups), rd.profile())
        assert reduction.length_km is None
        with pytest.raises(ValidationError) as caught:
            build_network(
                [reduction],
                [],
                weighting=weighting_for("length", sigma_per_km=0.0007),
            )
        assert caught.value.code == "validation.line_length_unknown"


# -- FR-802, FR-804: height systems --------------------------------------


def _flat_geoid(undulation: float) -> GeoidModel:
    """A constant-undulation grid over southern Brazil.

    Constant on purpose: the point of these tests is the conversion and its
    bookkeeping, and a constant makes the expected height exact, so a failure
    means the conversion is wrong rather than that the interpolation moved.
    :mod:`tests.test_geoid` is where the interpolation itself is tested.
    """
    return GeoidModel(
        id="TEST-GEOID",
        values=np.full((3, 3), undulation),
        coverage=Coverage(
            south=math.radians(-27.0),
            north=math.radians(-23.0),
            west=math.radians(-52.0),
            east=math.radians(-48.0),
        ),
        sigma=0.03,
    )


class TestHeightSystems:
    def _reductions(self):
        books, _truth = rd.loop(noise=0.0003)
        return [reduce_line(book.line, rd.profile()) for book in books]

    def test_mixing_height_types_raises(self):
        """specs/10 section 7 item 6, and the P4 exit criterion.

        Wrong by the geoid undulation -- tens of metres across much of Brazil --
        and the result looks entirely reasonable. So it is a refusal, not a
        warning.
        """
        with pytest.raises(ValidationError) as caught:
            build_network(
                self._reductions(),
                [
                    Benchmark("BM1", Quantity.exact(100.0, METRE)),
                    Benchmark(
                        "BM2",
                        Quantity.exact(103.75, METRE),
                        height_type=HeightType.ELLIPSOIDAL,
                    ),
                ],
            )
        assert caught.value.code == "validation.mixed_height_types"

    def test_naming_a_geoid_model_without_its_grid_is_still_refused(self):
        """A name records which model was used; it cannot compute an undulation.

        Accepting the name as permission to mix would record a conversion that
        never happened -- the worst of both, since the heights would be wrong
        *and* the record would say they had been corrected.
        """
        with pytest.raises(ValidationError) as caught:
            build_network(
                self._reductions(),
                [
                    Benchmark("BM1", Quantity.exact(100.0, METRE)),
                    Benchmark(
                        "BM2",
                        Quantity.exact(103.75, METRE),
                        height_type=HeightType.ELLIPSOIDAL,
                    ),
                ],
                geoid_model="MAPGEO2015",
            )
        assert caught.value.code == "validation.geoid_model_named_without_grid"

    def test_a_geoid_model_resolves_the_mixture(self):
        """FR-804: with the grid, the mixture is converted rather than refused.

        The ellipsoidal benchmark is brought onto the orthometric system the
        levelled differences already measure, and the network is built.
        """
        result = build_network(
            self._reductions(),
            [
                Benchmark("BM1", Quantity.exact(100.0, METRE)),
                Benchmark(
                    "BM2",
                    _metres(103.75 + 12.0, 0.02),
                    height_type=HeightType.ELLIPSOIDAL,
                    latitude=math.radians(-25.0),
                    longitude=math.radians(-50.0),
                ),
            ],
            geoid=_flat_geoid(12.0),
        )
        assert result.height_type is HeightType.ORTHOMETRIC
        assert result.meta["geoid_model"] == "TEST-GEOID"
        height = result.network.stations["BM2"].constraint.position.height
        assert height.value == pytest.approx(103.75)
        # The geoid's own uncertainty is in the converted height (FR-204): the
        # benchmark's 20 mm and the model's 30 mm, in quadrature.
        assert height.std_dev == pytest.approx(math.hypot(0.02, 0.03))

    def test_the_conversion_is_reported_not_silent(self):
        """A height that changed by twelve metres is not a detail to swallow."""
        result = build_network(
            self._reductions(),
            [
                Benchmark("BM1", Quantity.exact(100.0, METRE)),
                Benchmark(
                    "BM2",
                    _metres(115.75, 0.02),
                    height_type=HeightType.ELLIPSOIDAL,
                    latitude=math.radians(-25.0),
                    longitude=math.radians(-50.0),
                ),
            ],
            geoid=_flat_geoid(12.0),
        )
        converted = [f for f in result.findings if f.code == "height_converted_through_geoid"]
        assert len(converted) == 1
        assert converted[0].stations == ("BM2",)
        assert converted[0].value == pytest.approx(12.0)
        # The message carries the size of the change, because "converted" without
        # the twelve metres is a line a reader skims past.
        assert "12.0000" in converted[0].message

    def test_a_benchmark_needing_conversion_without_a_position_is_refused(self):
        """An undulation is a function of position; there is no default point."""
        with pytest.raises(ValidationError) as caught:
            build_network(
                self._reductions(),
                [
                    Benchmark("BM1", Quantity.exact(100.0, METRE)),
                    Benchmark(
                        "BM2",
                        _metres(115.75, 0.02),
                        height_type=HeightType.ELLIPSOIDAL,
                    ),
                ],
                geoid=_flat_geoid(12.0),
            )
        assert caught.value.code == "validation.benchmark_without_position"

    def test_a_geoid_model_is_not_applied_when_nothing_needs_it(self):
        """One height type throughout: no conversion, and no finding claiming one."""
        result = build_network(
            self._reductions(),
            [
                Benchmark("BM1", Quantity.exact(100.0, METRE)),
                Benchmark("BM2", Quantity.exact(103.75, METRE)),
            ],
            geoid=_flat_geoid(12.0),
        )
        assert result.height_type is HeightType.ORTHOMETRIC
        assert not [f for f in result.findings if f.code == "height_converted_through_geoid"]
        assert result.network.stations["BM2"].constraint.position.height.value == pytest.approx(103.75)

    def test_one_height_type_throughout_is_fine(self):
        result = build_network(
            self._reductions(),
            [
                Benchmark("BM1", Quantity.exact(100.0, METRE)),
                Benchmark("BM2", Quantity.exact(103.75, METRE)),
            ],
        )
        assert result.height_type is HeightType.ORTHOMETRIC

    def test_a_benchmark_without_a_height_type_is_refused(self):
        with pytest.raises(ValidationError) as caught:
            Benchmark("BM1", Quantity.exact(100.0, METRE), height_type=HeightType.NONE)
        assert caught.value.code == "validation.benchmark_without_height_type"

    def test_a_weighted_benchmark_needs_an_uncertainty(self):
        with pytest.raises(ValidationError) as caught:
            Benchmark("BM1", Quantity.exact(100.0, METRE), fixed=False)
        assert caught.value.code == "validation.weighted_benchmark_without_uncertainty"


# -- Orthometric corrections ----------------------------------------------


class TestOrthometricCorrections:
    def test_the_magnitude_matches_the_documented_case(self):
        """One degree of latitude at 1000 m: 81 mm. Stated in the module
        docstring so a reader can judge when to bother, and asserted here so the
        statement cannot rot."""
        result = normal_orthometric_correction(
            _metres(120.0, 0.003),
            latitude_from=math.radians(-30.0),
            latitude_to=math.radians(-31.0),
            height_from=1000.0,
            height_to=1000.0,
        )
        assert abs(result.millimetres) == pytest.approx(81.0, abs=1.0)

    def test_it_is_negative_going_poleward_in_either_hemisphere(self):
        def correction(from_lat: float, to_lat: float) -> float:
            return normal_orthometric_correction(
                _metres(1.0, 0.001),
                latitude_from=math.radians(from_lat),
                latitude_to=math.radians(to_lat),
                height_from=1000.0,
                height_to=1000.0,
            ).correction.value

        assert correction(30.0, 31.0) < 0.0
        assert correction(-30.0, -31.0) < 0.0
        assert correction(31.0, 30.0) > 0.0

    def test_a_negligible_correction_says_it_is_negligible(self):
        result = normal_orthometric_correction(
            _metres(1.0, 0.001),
            latitude_from=math.radians(-25.4),
            latitude_to=math.radians(-25.4001),
            height_from=100.0,
            height_to=100.0,
        )
        assert result.is_negligible
        assert "orthometric_correction_negligible" in {f.code for f in result.findings}

    def test_the_uncertainty_is_marked_as_a_stand_in(self):
        """The dominant error is the normality assumption, which no propagation
        of the inputs can express. Saying so is FR-203's whole job."""
        result = normal_orthometric_correction(
            _metres(120.0, 0.003),
            latitude_from=math.radians(-30.0),
            latitude_to=math.radians(-31.0),
            height_from=1000.0,
            height_to=1000.0,
        )
        assert result.correction.mode is UncertaintyMode.APPROXIMATE
        assert Strategy.DOMINANT_TERM in result.correction.strategies

    def test_an_impossible_latitude_is_refused(self):
        with pytest.raises(ValidationError) as caught:
            normal_orthometric_correction(
                _metres(1.0, 0.001),
                latitude_from=4.0,
                latitude_to=0.0,
                height_from=0.0,
                height_to=0.0,
            )
        assert caught.value.code == "validation.latitude_out_of_range"


# -- The stochastic model -------------------------------------------------


class TestTheStochasticModel:
    def test_a_staff_reading_takes_its_sigma_from_the_level(self):
        quantity, source = resolve_sigma(STAFF_READING, 1.4321, level=rd.profile())
        assert source is SigmaSource.INSTRUMENT
        assert quantity.std_dev == pytest.approx(rd.SIGMA_READING)

    def test_a_stadia_distance_propagates_two_wire_readings(self):
        quantity, _source = resolve_sigma(SIGHT_DISTANCE, 32.4, level=rd.profile())
        assert quantity.std_dev == pytest.approx(100.0 * rd.SIGMA_READING * math.sqrt(2.0))

    def test_a_height_difference_is_not_weighted_from_the_level_profile(self):
        """It is weighted by line length or setup count, and neither is derivable
        from the height difference itself. Answering with some other sigma would
        answer a question this function was not asked."""
        with pytest.raises(ValidationError) as caught:
            resolve_sigma("height_difference", 2.5, level=rd.profile())
        assert caught.value.code == "validation.missing_stochastic_model"

    def test_the_precedence_still_prefers_a_stated_sigma(self):
        quantity, source = resolve_sigma(
            STAFF_READING, 1.4321, stated=0.0009, level=rd.profile()
        )
        assert source is SigmaSource.STATED
        assert quantity.std_dev == pytest.approx(0.0009)

    def test_with_nothing_configured_it_refuses(self):
        with pytest.raises(ValidationError) as caught:
            resolve_sigma(STAFF_READING, 1.4321)
        assert caught.value.code == "validation.missing_stochastic_model"

    def test_a_type_default_is_the_last_resort(self):
        quantity, source = resolve_sigma(
            STAFF_READING,
            1.4321,
            defaults=StochasticDefaults().with_default(STAFF_READING, 0.0008),
        )
        assert source is SigmaSource.TYPE_DEFAULT
        assert quantity.std_dev == pytest.approx(0.0008)


# -- FR-505: every output carries an uncertainty --------------------------


class TestEveryOutputCarriesAnUncertainty:
    def test_every_levelling_result_is_a_quantity_with_a_variance(self):
        book = rd.balanced_line(noise=0.0003)
        reduction = reduce_line(book.line, rd.profile())
        setup, _ = rd.extreme_sights_setup()
        near, far, _ = rd.reciprocal_crossing()

        results = [
            reduction.height_difference,
            reduction.raw_height_difference,
            *reduce_setup(setup, rd.profile()).height_differences,
            reduce_reciprocal(near, far).height_difference,
        ]
        for quantity in results:
            assert isinstance(quantity, Quantity)
            assert quantity.unit is METRE
            assert quantity.variance > 0.0
            assert quantity.mode in (UncertaintyMode.RIGOROUS, UncertaintyMode.APPROXIMATE)

    def test_the_covariance_of_a_setup_is_positive_semidefinite(self):
        setup, _ = rd.extreme_sights_setup()
        matrix = reduce_setup(setup, rd.profile()).covariance.matrix
        assert np.all(np.linalg.eigvalsh(matrix) > -1e-15)
