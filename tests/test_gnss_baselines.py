# SPDX-License-Identifier: GPL-2.0-or-later
"""Baselines: the frame, the reduction, and the independent set (FR-602, FR-104).

The centrepiece is :class:`TestTheRotationAgreesWithTheEngine`. ``xyz.pos`` and
``enu.pos`` are **one run written twice**, so rotating the ECEF baseline derived
from the first must reproduce the second -- vector and covariance both. That
makes :func:`enu_rotation` evidence rather than assertion, and it is the only
check here that a sign error in the rotation could not survive. It is the same
device ``tests/test_pos_reader.py`` uses on the two formats' covariances.

Everything else follows from three rules the specifications state and nothing
previously enforced: a baseline is ECEF unless it says otherwise, an antenna
height is removed exactly once, and ``n(n-1)/2`` baselines carry ``n-1``
baselines' worth of information.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest

from geocomp.core.adjustment.equations import evaluate
from geocomp.core.adjustment.parameters import Frame, ParameterLayout
from geocomp.core.errors import DataError, ValidationError
from geocomp.core.geodesy.cartesian import ecef_to_enu, enu_rotation, enu_to_ecef
from geocomp.core.models import (
    BaselineFrame,
    ClusterKind,
    Network,
    Observation,
    ObservationType,
    Station,
    baseline_frame,
)
from geocomp.core.techniques.gnss import (
    AntennaOffset,
    Baseline,
    components_from_covariance,
    independent_subset,
    loop_closure,
    reduce_to_marks,
    rotate_baseline_to_local,
    to_cluster,
)
from geocomp.core.uncertainty import Covariance, Quantity, Strategy, UncertaintyMode
from geocomp.core.units import Unit
from geocomp.engines.rtklib.baseline import (
    baseline_from_solution,
    printed_covariance_half_width,
)
from geocomp.engines.rtklib.read_pos import read_pos

POS = Path(__file__).parent / "data" / "rtklib" / "pos"

#: What ``enu.pos``'s final epoch prints, to the 0.1 mm it is written at. The
#: engine computed these independently of the ECEF run; they are the answer the
#: rotation has to reproduce.
ENU_BASELINE = (-953.3367, 3196.2371, -6.3992)
ENU_DEVIATIONS = (0.0007, 0.0009, 0.0025)


@pytest.fixture
def ecef_baseline():
    solution = read_pos(POS / "xyz.pos")
    return baseline_from_solution(solution, base_station="3040", rover_station="0759", baseline_id="b1")


def _space_3d_layout(stations=("a", "b"), cartesian_frame=None):
    """A two-station 3D layout, the smallest thing a baseline equation needs."""
    network = Network(id="n", cartesian_frame=cartesian_frame)
    for name in stations:
        network.add_station(Station(id=name, name=name))
    return ParameterLayout.build(network, Frame.SPACE_3D)


def _baseline_observation(frame=None):
    meta = {} if frame is None else {"baseline_frame": frame}
    return Observation(
        id="o1",
        type=ObservationType.GNSS_BASELINE,
        stations=("a", "b"),
        values=tuple(Quantity.exact(v, Unit.METRE) for v in (1.0, 2.0, 3.0)),
        cluster_id="c",
        meta=meta,
    )


def _synthetic(identifier, base, rover, *, variance=1e-6):
    """A baseline with no engine behind it, for the graph tests."""
    covariance = Covariance(
        matrix=np.eye(3) * variance,
        labels=("x", "y", "z"),
        units=(Unit.METRE,) * 3,
    )
    return Baseline(
        id=identifier,
        base_station=base,
        rover_station=rover,
        components=components_from_covariance((100.0, 200.0, 300.0), covariance),
        covariance=covariance,
        base_horizon=(0.6, 2.4),
        rover_horizon=(0.6, 2.4),
    )


class TestTheRotationAgreesWithTheEngine:
    """``R @ (xyz - ref)`` must be what ``enu.pos`` says, or the rotation is wrong.

    Two files, one solution. Nothing in this class computes the expected answer
    from the code under test.
    """

    def test_the_rotated_vector_reproduces_the_enu_file(self, ecef_baseline):
        rotated = rotate_baseline_to_local(ecef_baseline)
        found = [q.value for q in rotated.components]
        # The residual is the 0.1 mm the inputs were printed at, not slack.
        assert found == pytest.approx(ENU_BASELINE, abs=1e-4)

    def test_the_rotated_covariance_reproduces_the_enu_deviations(self, ecef_baseline):
        rotated = rotate_baseline_to_local(ecef_baseline)
        found = [q.std_dev for q in rotated.components]
        # Every printed digit, which is a stronger statement than it looks:
        # a transposed row of R would change these by tens of percent.
        assert found == pytest.approx(ENU_DEVIATIONS, abs=5e-5)

    def test_the_length_is_the_one_the_enu_file_implies(self, ecef_baseline):
        assert ecef_baseline.length.value == pytest.approx(math.hypot(*ENU_BASELINE), abs=1e-3)

    def test_a_rotation_changes_the_representation_and_not_the_vector(self, ecef_baseline):
        rotated = rotate_baseline_to_local(ecef_baseline)
        assert rotated.length.value == pytest.approx(ecef_baseline.length.value, abs=1e-9)
        assert np.trace(rotated.covariance.matrix) == pytest.approx(
            np.trace(ecef_baseline.covariance.matrix), rel=1e-12
        )

    def test_the_rotation_is_orthonormal_and_right_handed(self):
        rotation = enu_rotation(0.6, 2.4)
        assert np.allclose(rotation @ rotation.T, np.eye(3))
        assert float(np.linalg.det(rotation)) == pytest.approx(1.0)

    def test_east_at_the_equator_and_prime_meridian_is_the_y_axis(self):
        assert ecef_to_enu((0.0, 1.0, 0.0), 0.0, 0.0) == pytest.approx((1.0, 0.0, 0.0))
        assert ecef_to_enu((0.0, 0.0, 1.0), 0.0, 0.0) == pytest.approx((0.0, 1.0, 0.0))
        assert ecef_to_enu((1.0, 0.0, 0.0), 0.0, 0.0) == pytest.approx((0.0, 0.0, 1.0))

    def test_the_inverse_round_trips(self):
        vector = (1234.5, -678.9, 2468.0)
        there = ecef_to_enu(vector, 0.6, 2.4)
        assert enu_to_ecef(there, 0.6, 2.4) == pytest.approx(vector, abs=1e-9)


class TestTheFrameIsDeclaredAndEnforced:
    """The defect P7b exists to close: a baseline with no stated frame.

    The DynaML writer means ECEF and the in-house core means east/north/up, and
    until this phase neither said so. Both now refuse the frame they cannot
    handle -- and one guard without the other would leave the mirror defect
    reachable, so both are tested.
    """

    def test_an_observation_with_no_recorded_frame_is_ecef(self):
        observation = Observation(
            id="o1",
            type=ObservationType.GNSS_BASELINE,
            stations=("a", "b"),
            values=tuple(Quantity.exact(v, Unit.METRE) for v in (1.0, 2.0, 3.0)),
            cluster_id="c",
        )
        assert baseline_frame(observation) is BaselineFrame.ECEF

    def test_an_unrecognised_frame_is_refused_rather_than_defaulted(self):
        observation = Observation(
            id="o1",
            type=ObservationType.GNSS_BASELINE,
            stations=("a", "b"),
            values=tuple(Quantity.exact(v, Unit.METRE) for v in (1.0, 2.0, 3.0)),
            cluster_id="c",
            meta={"baseline_frame": "geocentrik"},
        )
        with pytest.raises(DataError, match="baseline_frame_unknown"):
            baseline_frame(observation)

    def test_the_core_refuses_a_baseline_from_a_different_frame(self):
        """The error that actually exists: mixing, not ECEF-ness.

        ``target[c] - origin[c]`` is correct in any orthogonal 3-frame, so an
        ECEF baseline against ECEF coordinates is right -- which is what
        ``tests/test_dynadjust_crossvalidation.py`` relies on. What is wrong,
        and silent, is an ECEF baseline differenced against projected eastings
        and northings.
        """
        layout = _space_3d_layout(cartesian_frame=BaselineFrame.LOCAL)
        with pytest.raises(ValidationError, match="gnss_baseline_frame_mismatch"):
            evaluate(_baseline_observation("ecef"), layout, np.zeros(layout.size))

    def test_the_core_accepts_a_baseline_in_the_networks_own_frame(self):
        layout = _space_3d_layout(cartesian_frame=BaselineFrame.LOCAL)
        rows = evaluate(_baseline_observation("local"), layout, np.zeros(layout.size))
        assert [row.component for row in rows] == ["dx", "dy", "dz"]

    def test_a_geocentric_network_adjusts_a_geocentric_baseline(self):
        """``Frame.SPACE_3D`` is three orthogonal metres whatever they are called."""
        layout = _space_3d_layout(cartesian_frame=BaselineFrame.ECEF)
        rows = evaluate(_baseline_observation("ecef"), layout, np.zeros(layout.size))
        assert [row.computed for row in rows] == [0.0, 0.0, 0.0]

    def test_a_network_that_states_no_frame_is_not_checked(self):
        """Not a loophole, and the reason is in the equation's docstring: with
        nothing stated there is nothing to compare against, and defaulting
        would refuse the legitimate geocentric case above."""
        layout = _space_3d_layout()
        rows = evaluate(_baseline_observation("ecef"), layout, np.zeros(layout.size))
        assert len(rows) == 3

    def test_rotating_twice_is_refused(self, ecef_baseline):
        once = rotate_baseline_to_local(ecef_baseline)
        with pytest.raises(ValidationError, match="baseline_already_local"):
            rotate_baseline_to_local(once)

    def test_a_cluster_records_the_frame_on_every_member(self, ecef_baseline):
        local = rotate_baseline_to_local(ecef_baseline)
        observations, _ = to_cluster([local], cluster_id="c1")
        assert all(baseline_frame(o) is BaselineFrame.LOCAL for o in observations)

    def test_a_cluster_of_mixed_frames_is_refused(self, ecef_baseline):
        local = rotate_baseline_to_local(ecef_baseline)
        with pytest.raises(DataError, match="baseline_cluster_mixed_frames"):
            to_cluster([ecef_baseline, local], cluster_id="c1")


class TestAntennaHeightIsRemovedOnce:
    """``specs/11`` acceptance criterion 5, which asks for exactly this test."""

    @staticmethod
    def _offsets():
        return (
            AntennaOffset(up=Quantity.from_std_dev(1.500, 0.002, Unit.METRE), method="vertical"),
            AntennaOffset(up=Quantity.from_std_dev(1.200, 0.002, Unit.METRE), method="vertical"),
        )

    def test_the_height_difference_moves_by_the_difference_of_the_offsets(self, ecef_baseline):
        base, rover = self._offsets()
        before = rotate_baseline_to_local(ecef_baseline).components[2].value
        after = rotate_baseline_to_local(reduce_to_marks(ecef_baseline, base, rover)).components[2].value
        # Mark-to-mark is 0.3 m higher than antenna-to-antenna: the base's
        # antenna stood 0.3 m further above its mark than the rover's did.
        assert after - before == pytest.approx(0.300, abs=1e-3)

    def test_both_offsets_uncertainties_reach_the_result(self, ecef_baseline):
        base, rover = self._offsets()
        before = rotate_baseline_to_local(ecef_baseline).components[2]
        after = rotate_baseline_to_local(reduce_to_marks(ecef_baseline, base, rover)).components[2]
        expected = math.sqrt(before.std_dev**2 + 0.002**2 + 0.002**2)
        assert after.std_dev == pytest.approx(expected, rel=1e-6)
        assert after.std_dev > before.std_dev

    def test_a_second_reduction_raises(self, ecef_baseline):
        base, rover = self._offsets()
        once = reduce_to_marks(ecef_baseline, base, rover)
        with pytest.raises(ValidationError, match="antenna_height_already_reduced"):
            reduce_to_marks(once, base, rover)

    def test_the_reduction_is_recorded_on_the_baseline_it_produced(self, ecef_baseline):
        base, rover = self._offsets()
        once = reduce_to_marks(ecef_baseline, base, rover)
        assert ecef_baseline.antenna_reduction is None
        assert once.antenna_reduction is not None
        assert once.antenna_reduction.base.up.value == pytest.approx(1.500)

    def test_a_slant_height_is_refused_rather_than_assumed_vertical(self, ecef_baseline):
        _, rover = self._offsets()
        slant = AntennaOffset(up=Quantity.exact(1.5, Unit.METRE), method="slant")
        with pytest.raises(ValidationError, match="antenna_height_is_slant"):
            reduce_to_marks(ecef_baseline, slant, rover)

    def test_reducing_after_rotating_is_refused(self, ecef_baseline):
        base, rover = self._offsets()
        local = rotate_baseline_to_local(ecef_baseline)
        with pytest.raises(ValidationError, match="antenna_reduction_needs_ecef"):
            reduce_to_marks(local, base, rover)

    def test_each_end_is_rotated_at_its_own_horizon(self, ecef_baseline):
        """Two vertical offsets do not cancel horizontally over a real baseline.

        The local vertical turns by about 0.03 degrees over these 3.3 km, so a
        1.2 m offset at the far end leaves a sub-millimetre horizontal residue.
        Using one horizon for both ends would make this exactly zero -- which
        would look tidier and be wrong.
        """
        base, rover = self._offsets()
        before = rotate_baseline_to_local(ecef_baseline)
        after = rotate_baseline_to_local(reduce_to_marks(ecef_baseline, base, rover))
        north_shift = abs(after.components[1].value - before.components[1].value)
        assert 1e-4 < north_shift < 2e-3


class TestTheIndependentSubset:
    """``n`` stations give ``n(n-1)/2`` baselines and ``n-1`` independent ones."""

    def test_four_stations_give_six_baselines_and_three_independent(self):
        stations = ["a", "b", "c", "d"]
        baselines = [
            _synthetic(f"{first}{second}", first, second)
            for index, first in enumerate(stations)
            for second in stations[index + 1 :]
        ]
        assert len(baselines) == 6
        independent, dependent = independent_subset(baselines)
        assert len(independent) == 3
        assert len(dependent) == 3

    def test_nothing_is_discarded_and_everything_is_marked(self):
        baselines = [_synthetic("ab", "a", "b"), _synthetic("bc", "b", "c"), _synthetic("ac", "a", "c")]
        independent, dependent = independent_subset(baselines)
        assert len(independent) + len(dependent) == len(baselines)
        assert all(b.is_independent is True for b in independent)
        assert all(b.is_independent is False for b in dependent)

    def test_the_independent_set_spans_every_station(self):
        stations = ["a", "b", "c", "d"]
        baselines = [
            _synthetic(f"{first}{second}", first, second)
            for index, first in enumerate(stations)
            for second in stations[index + 1 :]
        ]
        independent, _ = independent_subset(baselines)
        covered = {s for b in independent for s in (b.base_station, b.rover_station)}
        assert covered == set(stations)

    def test_the_better_determined_baseline_is_preferred(self):
        """Not whichever one came first: the spanning tree is chosen by quality."""
        baselines = [
            _synthetic("ab-poor", "a", "b", variance=1e-2),
            _synthetic("bc", "b", "c", variance=1e-6),
            _synthetic("ac-good", "a", "c", variance=1e-8),
        ]
        _, dependent = independent_subset(baselines)
        assert [b.id for b in dependent] == ["ab-poor"]

    def test_two_disconnected_pairs_give_a_forest_not_a_tree(self):
        baselines = [_synthetic("ab", "a", "b"), _synthetic("cd", "c", "d")]
        independent, dependent = independent_subset(baselines)
        assert len(independent) == 2
        assert dependent == []


class TestTheClusterReachesAnAdjustment:
    def test_a_single_baseline_becomes_a_three_by_three_cluster(self, ecef_baseline):
        observations, cluster = to_cluster([ecef_baseline], cluster_id="c1")
        assert len(observations) == 1
        assert cluster.kind is ClusterKind.GNSS_BASELINE
        assert cluster.covariance.size == 3
        assert cluster.covariance.labels == ("m0.x", "m0.y", "m0.z")

    def test_two_baselines_carry_a_six_by_six(self, ecef_baseline):
        second = _synthetic("b2", "3040", "9999")
        observations, cluster = to_cluster([ecef_baseline, second], cluster_id="c1")
        assert cluster.covariance.size == 6
        assert cluster.observation_ids == tuple(o.id for o in observations)

    def test_the_covariance_survives_the_network_validator(self, ecef_baseline):
        observations, cluster = to_cluster([ecef_baseline], cluster_id="c1")
        network = Network(id="n")
        for name in ("3040", "0759"):
            network.add_station(Station(id=name, name=name))
        for observation in observations:
            network.add_observation(observation)
        network.add_cluster(cluster)
        network.require_valid()

    def test_the_off_diagonal_blocks_are_zero_because_nothing_measured_them(self, ecef_baseline):
        """``specs/08`` §8.5: a correlation the engine did not supply is absent,
        not invented. ``rnx2rtkp`` runs one baseline at a time."""
        second = _synthetic("b2", "3040", "9999")
        _, cluster = to_cluster([ecef_baseline, second], cluster_id="c1")
        assert np.allclose(cluster.covariance.matrix[0:3, 3:6], 0.0)

    def test_an_empty_cluster_is_refused(self):
        with pytest.raises(DataError, match="baseline_cluster_empty"):
            to_cluster([], cluster_id="c1")


class TestThePrintedCovarianceIsNotTakenAtFaceValue:
    def test_the_half_width_follows_the_signed_square_root_not_the_printing(self):
        """``dc/dv = 2|v|``, so the covariance's half-width is not ``0.5e-4``.

        Passing the printed half-width straight through would be two orders of
        magnitude too loose and would condition matrices that are indefinite
        for a real reason.
        """
        solution = read_pos(POS / "xyz.pos")
        epoch = solution.last()
        found = printed_covariance_half_width(epoch)
        largest = float(np.max(np.abs(np.sqrt(np.abs(epoch.covariance.matrix)))))
        assert found == pytest.approx(2.0 * largest * 0.5e-4)
        assert found < 1e-5

    def test_the_baseline_covariance_is_positive_semi_definite(self, ecef_baseline):
        eigenvalues = np.linalg.eigvalsh(ecef_baseline.covariance.matrix)
        assert eigenvalues.min() >= -1e-15

    def test_the_off_diagonals_keep_the_sign_the_file_wrote(self, ecef_baseline):
        matrix = ecef_baseline.covariance.matrix
        # xy and zx are printed negative in xyz.pos; yz positive.
        assert matrix[0, 1] < 0
        assert matrix[1, 2] > 0
        assert matrix[2, 0] < 0


class TestTheEngineBridgeRefusesWhatItCannotUse:
    def test_a_non_geocentric_pos_is_refused_by_name(self):
        solution = read_pos(POS / "enu.pos")
        with pytest.raises(DataError, match="pos_not_geocentric"):
            baseline_from_solution(solution, base_station="a", rover_station="b")

    def test_the_last_epoch_is_the_answer_not_the_first(self, ecef_baseline):
        """A static run writes the filter's state every epoch; the early ones
        are a converging filter's guesses, and ``xyz.pos``'s first is a float
        solution two metres out."""
        solution = read_pos(POS / "xyz.pos")
        first = np.asarray(solution.epochs[0].position) - np.asarray(solution.reference_position)
        found = np.array([q.value for q in ecef_baseline.components])
        assert np.linalg.norm(found - first) > 0.1

    def test_the_quality_summary_carries_what_the_run_achieved(self):
        from geocomp.engines.rtklib.baseline import quality_from_solution

        quality = quality_from_solution(read_pos(POS / "xyz.pos"), session_id="0759")
        assert quality.epochs == 120
        assert quality.status_counts == {"FLOAT": 3, "FIXED": 117}
        assert quality.fixed_fraction == pytest.approx(117 / 120)
        assert quality.interval == pytest.approx(30.0)
        assert quality.satellites_least == 5
        assert quality.satellites_most == 7

    def test_dilution_of_precision_is_absent_and_says_so(self):
        """FR-603 names DOP and ``rnx2rtkp`` writes none, in any format. The
        field is ``None`` rather than a covariance-derived substitute wearing
        the name of a different quantity."""
        from geocomp.engines.rtklib.baseline import quality_from_solution

        assert quality_from_solution(read_pos(POS / "xyz.pos")).dilution_of_precision is None


def _leg(identifier, base, rover, vector, *, variance=1e-6, frame=None):
    """A baseline with a chosen vector, for the closure tests."""
    covariance = Covariance(
        matrix=np.eye(3) * variance,
        labels=("e", "n", "u") if frame is BaselineFrame.LOCAL else ("x", "y", "z"),
        units=(Unit.METRE,) * 3,
    )
    return Baseline(
        id=identifier,
        base_station=base,
        rover_station=rover,
        components=components_from_covariance(tuple(vector), covariance),
        covariance=covariance,
        base_horizon=(0.6, 2.4),
        rover_horizon=(0.6, 2.4),
        frame=frame or BaselineFrame.ECEF,
    )


def _triangle(error=(0.0, 0.0, 0.0)):
    """A-B-C-A, with *error* added to the last leg so the loop fails to close."""
    ab = np.array([100.0, 0.0, 0.0])
    bc = np.array([0.0, 200.0, 50.0])
    ca = -(ab + bc) + np.array(error)
    return [
        _leg("ab", "A", "B", ab),
        _leg("bc", "B", "C", bc),
        _leg("ca", "C", "A", ca),
    ]


class TestALoopClosesOnItself:
    """Closure is the one check on a set of baselines that needs no external
    coordinate: it asks whether the measurements agree with each other."""

    def test_a_perfect_triangle_closes_to_zero(self):
        closure = loop_closure(_triangle(), ["A", "B", "C"])
        assert closure.magnitude_m == pytest.approx(0.0, abs=1e-12)
        assert closure.legs == ("ab", "bc", "ca")

    def test_an_error_in_one_leg_is_the_misclosure(self):
        closure = loop_closure(_triangle(error=(0.003, -0.004, 0.012)), ["A", "B", "C"])
        assert [q.value for q in closure.misclosure] == pytest.approx([0.003, -0.004, 0.012])
        assert closure.magnitude_m == pytest.approx(0.013, abs=1e-9)

    def test_a_leg_stored_the_other_way_round_is_negated_not_refused(self):
        """Traversing a baseline against its sense is a negation, not a
        different measurement, so the same physical set must close either way."""
        legs = _triangle()
        legs[1] = _leg("cb", "C", "B", -np.array([0.0, 200.0, 50.0]))
        closure = loop_closure(legs, ["A", "B", "C"])
        assert closure.magnitude_m == pytest.approx(0.0, abs=1e-12)
        assert closure.legs == ("ab", "cb", "ca")

    def test_the_perimeter_gives_a_proportional_figure(self):
        closure = loop_closure(_triangle(error=(0.0, 0.0, 0.01)), ["A", "B", "C"])
        assert closure.perimeter_m == pytest.approx(2 * np.linalg.norm([100.0, 200.0, 50.0]) + 0.0, rel=0.2)
        assert closure.parts_per_million == pytest.approx(1e6 * closure.magnitude_m / closure.perimeter_m)


class TestTheClosureSaysHowWellItKnowsItself:
    def test_the_covariance_is_approximate_and_says_why(self):
        """Legs of one session share satellites and atmosphere, so summing
        their covariances as independent understates the truth. A misclosure
        judged against an over-optimistic sigma looks significant when it is
        not, so the assumption is recorded rather than left to be inferred."""
        closure = loop_closure(_triangle(), ["A", "B", "C"])
        assert closure.covariance.mode is UncertaintyMode.APPROXIMATE
        assert Strategy.INDEPENDENCE_ASSUMED in closure.covariance.strategies

    def test_the_variance_is_the_sum_over_the_legs(self):
        closure = loop_closure(_triangle(), ["A", "B", "C"])
        assert closure.covariance.matrix[0, 0] == pytest.approx(3e-6)


class TestAClosureThatWouldBeMeaninglessIsRefused:
    def test_a_local_frame_leg_is_refused(self):
        """East, north and up at one station are not east, north and up at
        another, so a circuit of local vectors sums three different frames."""
        legs = _triangle()
        legs[0] = _leg("ab", "A", "B", [100.0, 0.0, 0.0], frame=BaselineFrame.LOCAL)
        with pytest.raises(DataError, match="gnss_loop_leg_not_ecef"):
            loop_closure(legs, ["A", "B", "C"])

    def test_a_two_station_circuit_is_refused(self):
        """It retraces one baseline and closes by construction, so it would
        report a perfect closure while checking nothing."""
        with pytest.raises(ValidationError, match="gnss_loop_too_short"):
            loop_closure(_triangle(), ["A", "B"])

    def test_a_repeated_station_is_refused(self):
        with pytest.raises(ValidationError, match="gnss_loop_repeats_a_station"):
            loop_closure(_triangle(), ["A", "B", "A", "C"])

    def test_a_missing_leg_is_refused(self):
        with pytest.raises(ValidationError, match="gnss_loop_leg_missing"):
            loop_closure(_triangle()[:2], ["A", "B", "C"])

    def test_mixing_reduced_and_unreduced_legs_is_refused(self):
        """Such a loop closes by the difference of the antenna heights, which
        looks exactly like a measurement error and is not one."""
        legs = _triangle()
        legs[0] = reduce_to_marks(
            legs[0],
            AntennaOffset(up=Quantity.from_std_dev(1.500, 0.002, Unit.METRE), method="vertical"),
            AntennaOffset(up=Quantity.from_std_dev(1.200, 0.002, Unit.METRE), method="vertical"),
        )
        with pytest.raises(DataError, match="gnss_loop_mixed_antenna_reduction"):
            loop_closure(legs, ["A", "B", "C"])
