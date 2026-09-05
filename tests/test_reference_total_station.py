# SPDX-License-Identifier: GPL-2.0-or-later
"""RD-01: the phase P3 acceptance criteria, as tests.

``specs/09-module-total-station.md`` section 7, criteria 1 to 3.

Two of these tests are unusual and deliberately so: they assert that GeoComp
*disagrees* with its own reference dataset's expected output, in two specific
places, and they carry the independent checks that establish which of the two
answers is right. A reference test that could only ever confirm the reference
would have propagated both of RD-01's defects into the production code.
"""

from __future__ import annotations

import math

import pytest

from geocomp.core.adjustment.least_squares import AdjustmentOptions, adjust
from geocomp.core.adjustment.parameters import Frame
from geocomp.core.findings import Severity
from geocomp.core.models import DatumDefinition
from geocomp.core.techniques.total_station import (
    Face,
    FacePair,
    FaceReading,
    preprocess_setup,
    reduce_basic,
    reduce_face_pair,
)
from geocomp.core.uncertainty import Quantity, UncertaintyMode
from geocomp.core.units import Unit
from tests import reference_rd01 as rd01

#: The tolerance the acceptance criterion states. Everything below actually
#: agrees to about 1e-14, which is machine precision for these magnitudes.
TOLERANCE = 1e-9


@pytest.fixture(scope="module")
def expected():
    return rd01.published()


def _reduce(key):
    """Face reduction plus basic reduction for one published record."""
    record = rd01.published()[key]
    reduction = reduce_face_pair(rd01.face_pair(key))
    basic = reduce_basic(
        reduction.distance,
        reduction.zenith,
        Quantity.from_std_dev(record.instrument_height, rd01.SIGMA_HEIGHT, Unit.METRE),
        Quantity.from_std_dev(record.target_height, rd01.SIGMA_HEIGHT, Unit.METRE),
    )
    return reduction, basic, record


class TestReproduction:
    """Acceptance criterion 1: RD-01 reproduces, except where the prototype is wrong."""

    def test_the_dataset_is_present_and_complete(self):
        """Guards every other test here: a missing file would make them vacuous."""
        assert rd01.RAW.is_file() and rd01.PROCESSED.is_file()
        assert len(rd01.published()) == 6
        assert len(rd01.raw_groups()) == 6

    @pytest.mark.parametrize("key", sorted(rd01.published()))
    def test_zenith_distance_and_height_difference_reproduce(self, key):
        """V_corr, DH, DV and dH, to 1e-9. These the prototype got right."""
        _reduction, basic, record = _reduce(key)
        reduction, _basic, _record = _reduce(key)

        assert math.degrees(reduction.zenith.value) == pytest.approx(
            record.zenith_degrees, abs=TOLERANCE
        )
        assert basic.horizontal_distance.value == pytest.approx(
            record.horizontal_distance, abs=TOLERANCE
        )
        assert basic.vertical_component.value == pytest.approx(
            record.vertical_component, abs=TOLERANCE
        )
        assert basic.height_difference.value == pytest.approx(
            record.height_difference, abs=TOLERANCE
        )

    @pytest.mark.parametrize(
        "key", sorted(k for k in rd01.published() if k != rd01.WRONG_DIRECTION_KEY)
    )
    def test_directions_reproduce_everywhere_the_prototype_was_right(self, key):
        reduction, _basic, record = _reduce(key)
        assert math.degrees(reduction.horizontal.value) == pytest.approx(
            record.horizontal_degrees, abs=TOLERANCE
        )

    def test_every_reproduced_value_carries_an_uncertainty(self):
        """The other half of criterion 1: reproducing the numbers is not enough."""
        for key in rd01.published():
            reduction, basic, _record = _reduce(key)
            for quantity in (
                reduction.horizontal,
                reduction.zenith,
                reduction.distance,
                basic.horizontal_distance,
                basic.vertical_component,
                basic.height_difference,
            ):
                assert quantity.std_dev > 0.0, f"{key}: a value with no uncertainty"


class TestTheOneHundredAndEightyDegreeError:
    """Acceptance criterion 1's exception, and criterion 2's second half.

    ``specs/09`` section 2.1 previously said the prototype's ``pd_pi_H`` was
    "correct for the RD-01 data, and wrong for pairs that straddle the wrap".
    The first half is false. These tests pin down both the disagreement and the
    evidence for which side of it is right, so that neither can be quietly
    reverted to match the published file.
    """

    def test_geocomp_gives_the_corrected_direction(self):
        reduction, _basic, _record = _reduce(rd01.WRONG_DIRECTION_KEY)
        assert math.degrees(reduction.horizontal.value) == pytest.approx(
            rd01.CORRECT_DEGREES, abs=TOLERANCE
        )

    def test_and_therefore_disagrees_with_the_published_file_by_exactly_half_a_turn(self):
        reduction, _basic, record = _reduce(rd01.WRONG_DIRECTION_KEY)
        difference = math.degrees(reduction.horizontal.value) - record.horizontal_degrees
        assert difference == pytest.approx(180.0, abs=TOLERANCE)

    def test_the_corrected_direction_closes_the_triangle(self):
        """First independent check.

        The three interior angles of a plane triangle sum to 180 degrees. With
        the published direction they sum to 38.24 degrees, which is not a
        misclosure -- it is a different triangle.
        """
        assert self._interior_sum(corrected=True) == pytest.approx(180.0, abs=0.05)
        assert self._interior_sum(corrected=False) == pytest.approx(38.24, abs=0.01)

    def test_the_corrected_direction_agrees_with_the_measured_third_side(self):
        """Second independent check, using no angle but the one in question.

        The law of cosines over the two sides measured from station 1 predicts
        the third side. The published direction predicts 4.43 m against 24.35 m
        measured; the corrected one predicts 24.36 m.
        """
        sides = rd01.triangle_sides()
        measured = sides[frozenset({"2", "3"})]
        b = sides[frozenset({"1", "3"})]
        c = sides[frozenset({"1", "2"})]

        def third_side(angle_degrees: float) -> float:
            return math.sqrt(
                b**2 + c**2 - 2.0 * b * c * math.cos(math.radians(angle_degrees))
            )

        published_angle = self._angle_at_station_one(corrected=False)
        corrected_angle = self._angle_at_station_one(corrected=True)

        assert third_side(corrected_angle) == pytest.approx(measured, abs=0.02)
        assert third_side(published_angle) < 5.0
        assert abs(third_side(published_angle) - measured) > 19.0

    # -- the two independent checks, shared -------------------------------

    @staticmethod
    def _direction(key, *, corrected: bool) -> float:
        """The foresight or backsight direction in degrees, from either source."""
        if corrected:
            reduction, _basic, _record = _reduce(key)
            return math.degrees(reduction.horizontal.value)
        return rd01.published()[key].horizontal_degrees

    @classmethod
    def _angle_at_station_one(cls, *, corrected: bool) -> float:
        """The interior angle at station 1, swept from backsight to foresight."""
        back = cls._direction(("3", "1", "2", "R"), corrected=corrected)
        fore = cls._direction(("3", "1", "2", "V"), corrected=corrected)
        swept = (fore - back) % 360.0
        return min(swept, 360.0 - swept)

    @classmethod
    def _interior_sum(cls, *, corrected: bool) -> float:
        total = cls._angle_at_station_one(corrected=corrected)
        for setup in (("1", "2", "3"), ("2", "3", "1")):
            back = cls._direction((*setup, "R"), corrected=False)
            fore = cls._direction((*setup, "V"), corrected=False)
            swept = (fore - back) % 360.0
            total += min(swept, 360.0 - swept)
        return total


class TestTheDistanceBlunder:
    """Acceptance criterion 2: RD-01's 1.000 m face-pair discrepancy is caught."""

    def test_the_blundered_pair_is_flagged(self):
        reduction = reduce_face_pair(rd01.face_pair(rd01.BLUNDER_KEY))
        codes = {finding.code for finding in reduction.findings}
        assert "face_distance_discrepancy" in codes

    def test_it_is_flagged_as_blocking_not_merely_noted(self):
        """The mean of two distances a metre apart is not a measurement of
        anything, so it must not reach an adjustment as though it were."""
        reduction = reduce_face_pair(rd01.face_pair(rd01.BLUNDER_KEY))
        blocking = [f for f in reduction.findings if f.severity is Severity.BLOCKING]
        assert len(blocking) == 1
        assert blocking[0].value == pytest.approx(rd01.BLUNDER_SIZE, abs=1e-9)

    def test_no_other_pair_is_flagged(self):
        """A detector that fires everywhere detects nothing. Every other pair in
        RD-01 agrees between faces to the millimetre."""
        flagged = []
        for key in rd01.published():
            reduction = reduce_face_pair(rd01.face_pair(key))
            if any(f.severity is Severity.BLOCKING for f in reduction.findings):
                flagged.append(key)
        assert flagged == [rd01.BLUNDER_KEY]

    def test_the_prototype_averaged_it_and_the_average_is_in_the_expected_file(self):
        """Documents what the defect actually did, so the test explains itself.

        23.861 m is the mean of 24.361 and 23.361, and it is what
        ``processed_data.csv`` carries.
        """
        record = rd01.published()[rd01.BLUNDER_KEY]
        faces = rd01.raw_groups()[rd01.BLUNDER_KEY]
        direct = float(faces["PD"]["D"])
        reverse = float(faces["PI"]["D"])
        assert direct - reverse == pytest.approx(rd01.BLUNDER_SIZE, abs=1e-9)
        assert record.slope_distance == pytest.approx((direct + reverse) / 2.0, abs=1e-9)

    def test_the_blundered_pointing_does_not_become_an_observation(self):
        """The pipeline reports it and leaves it out, rather than passing a
        known-bad number to an adjustment where it would acquire a residual and
        a standard deviation as though it were real."""
        from geocomp.core.techniques.total_station import to_observations

        result = preprocess_setup(rd01.setups()["3"], rd01.library())
        assert any(
            f.code == "face_distance_discrepancy" for f in result.all_findings
        ), "the pipeline lost the finding the reduction produced"

        observations, _clusters = to_observations(result)
        assert observations, "the clean pointing at this setup should still be there"
        assert len(result.usable) == len(result.pointings) - 1


class TestTheWrapCase:
    """Acceptance criterion 3: PD = 181 degrees with PI = 1 degree returns 181."""

    @staticmethod
    def _pair(direct_degrees: float, reverse_degrees: float) -> FacePair:
        def reading(value: float, face: Face) -> FaceReading:
            return FaceReading(
                target="t",
                face=face,
                horizontal=Quantity.from_std_dev(math.radians(value), 5e-6, Unit.RADIAN),
                zenith=Quantity.from_std_dev(math.radians(90.0), 5e-6, Unit.RADIAN)
                if face is Face.DIRECT
                else Quantity.from_std_dev(math.radians(270.0), 5e-6, Unit.RADIAN),
            )

        return FacePair(reading(direct_degrees, Face.DIRECT), reading(reverse_degrees, Face.REVERSE))

    def test_the_case_the_spec_names(self):
        reduction = reduce_face_pair(self._pair(181.0, 1.0))
        assert math.degrees(reduction.horizontal.value) == pytest.approx(181.0, abs=1e-12)

    def test_the_arithmetic_mean_would_have_given_one_degree(self):
        """States the failure this test exists to prevent, so a future reader
        knows what 181 is being contrasted with."""
        arithmetic = (181.0 + 1.0) / 2.0
        assert arithmetic - 90.0 == pytest.approx(1.0)

    @pytest.mark.parametrize(
        ("direct", "reverse"),
        [(0.0, 180.0), (0.001, 180.001), (359.999, 179.999), (181.0, 1.0), (90.0, 270.0)],
    )
    def test_the_reduction_returns_the_direct_reading_when_the_pair_is_exact(
        self, direct, reverse
    ):
        """With no collimation, the reduced direction *is* the direct reading.
        Across the wrap included -- which is the whole property."""
        reduction = reduce_face_pair(self._pair(direct, reverse))
        assert math.degrees(reduction.horizontal.value) == pytest.approx(direct, abs=1e-12)

    def test_collimation_is_recovered_across_the_wrap(self):
        """A five-arcsecond collimation planted at the discontinuity comes back."""
        planted = 5.0 / 3600.0
        reduction = reduce_face_pair(self._pair(0.0 + planted, 180.0 - planted))
        assert math.degrees(reduction.collimation.value) == pytest.approx(planted, abs=1e-12)


class TestInjectedInstrumentalErrors:
    """Acceptance criterion 4: a synthetic pair with known errors returns them."""

    @staticmethod
    def _pair(true_direction: float, true_zenith: float, collimation: float, index: float):
        """Build a face pair carrying exactly the two errors named.

        Collimation displaces the horizontal reading in opposite senses on the
        two faces; the index error displaces both zenith readings the same way,
        which is why the pair mean cancels the first and the *sum* reveals the
        second.
        """

        def reading(horizontal: float, zenith: float, face: Face) -> FaceReading:
            return FaceReading(
                target="t",
                face=face,
                horizontal=Quantity.from_std_dev(math.radians(horizontal), 5e-6, Unit.RADIAN),
                zenith=Quantity.from_std_dev(math.radians(zenith), 5e-6, Unit.RADIAN),
            )

        return FacePair(
            reading(true_direction + collimation, true_zenith + index, Face.DIRECT),
            reading(true_direction + 180.0 - collimation, 360.0 - true_zenith + index, Face.REVERSE),
        )

    @pytest.mark.parametrize("collimation_arcsec", [0.0, 5.0, -12.5, 60.0])
    @pytest.mark.parametrize("index_arcsec", [0.0, 8.0, -3.0])
    def test_both_errors_are_recovered_and_both_are_cancelled(
        self, collimation_arcsec, index_arcsec
    ):
        collimation = collimation_arcsec / 3600.0
        index = index_arcsec / 3600.0
        reduction = reduce_face_pair(
            self._pair(37.5, 88.25, collimation, index),
            collimation_tolerance=1.0,
        )

        assert math.degrees(reduction.collimation.value) == pytest.approx(
            collimation, abs=1e-11
        )
        assert math.degrees(reduction.vertical_index.value) == pytest.approx(index, abs=1e-11)
        # And the reduced values are free of both.
        assert math.degrees(reduction.horizontal.value) == pytest.approx(37.5, abs=1e-11)
        assert math.degrees(reduction.zenith.value) == pytest.approx(88.25, abs=1e-11)

    def test_a_collimation_beyond_tolerance_is_reported(self):
        reduction = reduce_face_pair(
            self._pair(37.5, 88.25, 60.0 / 3600.0, 0.0),
            collimation_tolerance=math.radians(10.0 / 3600.0),
        )
        codes = {finding.code for finding in reduction.findings}
        assert "collimation_beyond_tolerance" in codes
        # A warning, not blocking: the pair cancelled it, so the result stands.
        assert all(f.severity is not Severity.BLOCKING for f in reduction.findings)


class TestPipelineOverRd01:
    """The whole chain over the real setups, as a Processing algorithm will run it."""

    def test_every_setup_processes(self):
        profiles = rd01.library()
        for station, setup in sorted(rd01.setups().items()):
            result = preprocess_setup(setup, profiles)
            assert result.station == station
            assert len(result.pointings) == 2

    def test_the_uncertainties_are_approximate_and_say_why(self):
        """RD-01 has no stated per-observation sigmas, so the precisions came
        from the instrument profile. FR-203 requires that be visible."""
        result = preprocess_setup(rd01.setups()["1"], rd01.library())
        pointing = result.pointings[0]
        assert pointing.basic is not None
        assert pointing.basic.height_difference.mode is UncertaintyMode.APPROXIMATE
        assert pointing.basic.height_difference.strategies

    def test_the_setup_diagnostics_are_reported(self):
        """The collimation and index error each setup implies, which the mean
        throws away and which this module is required to surface."""
        result = preprocess_setup(rd01.setups()["1"], rd01.library())
        assert result.diagnostics.pair_count == 2
        assert math.isfinite(result.diagnostics.collimation_mean)
        assert result.diagnostics.collimation_spread >= 0.0

    def test_observations_are_produced_with_a_direction_set_cluster(self):
        """Directions from one setup share its unknown orientation, so they must
        arrive as a cluster rather than as independent scalars (FR-104)."""
        from geocomp.core.models import ClusterKind
        from geocomp.core.techniques.total_station import to_observations

        result = preprocess_setup(rd01.setups()["1"], rd01.library())
        observations, clusters = to_observations(result)

        assert observations
        assert len(clusters) == 1
        assert clusters[0].kind is ClusterKind.DIRECTION_SET
        assert len(clusters[0].observation_ids) == 2


class TestTheWholeSliceOverRd01:
    """Import to adjustment, on real data, with no external engine.

    Phase P3's stated goal in ``specs/ROADMAP.md``. Everything from the raw
    field book to an adjusted network with statistics runs here, in a test with
    no QGIS and no DynAdjust -- which is the claim the phase makes.
    """

    @staticmethod
    def _network(dimension: int = 2, fixed=None):
        from geocomp.core.techniques.total_station import build_network

        profiles = rd01.library()
        results = [
            preprocess_setup(setup, profiles)
            for _station, setup in sorted(rd01.setups().items())
        ]
        return build_network(
            results,
            rd01.approximate_coordinates(),
            crs="EPSG:31982",
            dimension=dimension,
            fixed=fixed,
        )

    def test_the_network_assembles_and_passes_inspection(self):
        from geocomp.core.preanalysis import inspect

        network = self._network()
        report = inspect(network, frame=Frame.PLANE_2D)
        assert report.can_adjust
        assert not report.blocking

    def test_the_blundered_pointing_is_absent_from_the_network(self):
        """It was reported at reduction and never became an observation."""
        network = self._network()
        assert not any("3-hd-2" == o for o in network.observations)

    def test_rd01_is_a_free_network_and_the_datum_defect_says_so(self):
        """Distances give shape and scale; directions give the angles within
        each setup. Nothing in RD-01 gives orientation or position, so the
        defect is two translations and a rotation -- and a constrained solution
        is impossible without an external azimuth. Worth pinning down, because
        it is a property of the dataset rather than of the software."""
        from geocomp.core.adjustment.datum import detect_defect

        network = self._network()
        defect = detect_defect(list(network.observations.values()), Frame.PLANE_2D)
        assert defect.size == 3
        assert "rotation" in defect.describe()

    def test_it_adjusts_with_inner_constraints(self):
        network = self._network()
        run = adjust(
            network,
            AdjustmentOptions(
                frame=Frame.PLANE_2D, datum=DatumDefinition.INNER_CONSTRAINT
            ),
        )
        assert run.converged
        assert run.degrees_of_freedom == 4
        assert run.method == "bordered"

    def test_the_adjusted_shape_matches_the_measured_one(self):
        """The check that the adjustment did something meaningful: the sides it
        produces must agree with the distances that went in, to the few
        millimetres RD-01's own consistency allows."""
        network = self._network()
        run = adjust(
            network,
            AdjustmentOptions(
                frame=Frame.PLANE_2D, datum=DatumDefinition.INNER_CONSTRAINT
            ),
        )
        coordinates = {
            station: (
                float(run.parameters[run.layout.station_columns(station)["e"]]),
                float(run.parameters[run.layout.station_columns(station)["n"]]),
            )
            for station in run.layout.station_ids()
            if run.layout.station_columns(station)
        }
        for pair, measured in rd01.triangle_sides().items():
            first, second = sorted(pair)
            adjusted = math.dist(coordinates[first], coordinates[second])
            assert adjusted == pytest.approx(measured, abs=0.02)

    def test_the_global_test_fails_and_that_is_the_right_answer(self):
        """RD-01's distances disagree between stations by about 15 mm, and the
        nominal precisions assumed here are 2 mm. A global test that passed
        would mean it was not testing anything."""
        from geocomp.core.statistics.tests import global_test

        network = self._network()
        run = adjust(
            network,
            AdjustmentOptions(
                frame=Frame.PLANE_2D, datum=DatumDefinition.INNER_CONSTRAINT
            ),
        )
        result = global_test(run.variance_factor_aposteriori, run.degrees_of_freedom)
        assert not result.passed
        assert result.statistic > result.critical_high
        assert "too large" in result.note

    def test_the_residuals_are_the_size_the_data_justifies(self):
        """Distance residuals of a centimetre or so, direction residuals of a
        few arcseconds. Anything much larger would mean the reduction or the
        network assembly had gone wrong rather than the data being ordinary."""
        network = self._network()
        run = adjust(
            network,
            AdjustmentOptions(
                frame=Frame.PLANE_2D, datum=DatumDefinition.INNER_CONSTRAINT
            ),
        )
        for (observation_id, _component), residual in zip(
            run.system.row_labels, run.residuals, strict=True
        ):
            if "-hd-" in observation_id:
                assert abs(residual) < 0.05, f"{observation_id}: {residual:.4f} m"
            else:
                assert abs(math.degrees(residual) * 3600.0) < 60.0
