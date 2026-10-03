# SPDX-License-Identifier: GPL-2.0-or-later
"""The public functions of ``core/`` that nothing else in the suite reached (specs/20 criterion 6).

``scripts/check_coverage.py`` runs after the suite under ``coverage`` and lists
every public function and method of ``core/`` whose body no test executes. Its
first run, in P12c-6, found 49 -- serialisation round trips, properties and
profile helpers that the code uses but no test had called, and a few that
nothing calls yet. Each is held here to what its docstring says it does, so the
check can then insist on none.

Some of them were worth more than the number: ``RejectionRecord`` had never been
written and read back, so the record a rejected observation carries -- why, by
which test, at what statistic -- was unverified across the one boundary that
matters for it.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta

import numpy as np
import pytest

from geocomp.core.errors import ValidationError
from geocomp.core.uncertainty import Quantity, Strategy, UncertaintyMode
from geocomp.core.units import Unit


class TestTheAdjustmentCore:
    def test_a_block_diagonal_transposes_block_by_block(self):
        from geocomp.core.adjustment.blocks import BlockDiagonal

        blocks = BlockDiagonal.from_blocks(
            4,
            [
                (np.array([0, 2]), np.array([[1.0, 2.0], [3.0, 4.0]])),
                (np.array([1]), [[5.0]]),
                (np.array([3]), [[6.0]]),
            ],
        )
        assert np.array_equal(blocks.T.to_dense(), blocks.to_dense().T)

    def test_a_systems_parameter_count_is_its_layouts(self):
        from geocomp.core.adjustment import Frame
        from geocomp.core.adjustment.least_squares import AdjustmentOptions, adjust
        from tests.networks import trilateration

        run = adjust(trilateration().network, AdjustmentOptions(frame=Frame.PLANE_2D))
        assert run.system.parameter_count == run.layout.size == run.system.design.shape[1]

    def test_a_difference_weighting_round_trips(self):
        from geocomp.core.adjustment.weighting import DifferenceWeighting, ExtentKind

        weighting = DifferenceWeighting(
            kind=ExtentKind.LENGTH, coefficient=0.002, extent_label="km", strategy=Strategy.NOMINAL_PRECISION
        )
        assert DifferenceWeighting.from_dict(weighting.to_dict()) == weighting


class TestTheEllipsoid:
    """Closed forms rather than printed values: at the equator the mean radius
    of curvature is the semi-minor axis, and at a pole it is a^2/b."""

    @pytest.fixture
    def grs80(self):
        from geocomp.core.geodesy.ellipsoid import ellipsoid_by_name

        return ellipsoid_by_name("GRS80")

    def test_the_mean_radius_is_the_iugg_arithmetic_mean(self, grs80):
        a, b = grs80.semi_major_axis, grs80.semi_minor_axis
        assert grs80.mean_radius == pytest.approx((2.0 * a + b) / 3.0, rel=1e-15)
        assert b < grs80.mean_radius < a

    def test_the_gaussian_radius_at_the_equator_and_the_pole(self, grs80):
        a, b = grs80.semi_major_axis, grs80.semi_minor_axis
        assert grs80.gaussian_radius(0.0) == pytest.approx(b, rel=1e-12)
        assert grs80.gaussian_radius(math.pi / 2.0) == pytest.approx(a * a / b, rel=1e-12)


class TestInstrumentProfiles:
    @pytest.fixture
    def total_station(self):
        from geocomp.core.instruments.profiles import EdmSpecification, InstrumentProfile

        return InstrumentProfile(
            id="ts",
            sigma_direction=1.0e-5,
            sigma_zenith=2.0e-5,
            sigma_zenith_refraction=1.0e-8,
            edm=EdmSpecification(constant=0.002, proportional=2.0e-6),
            sigma_instrument_height=0.001,
            sigma_target_height=0.002,
        )

    def test_a_mean_of_sets_improves_as_the_root_of_their_number(self):
        from geocomp.core.instruments.profiles import angular_specification

        single = angular_specification(4.0e-5)
        four = angular_specification(4.0e-5, sets=4)
        assert single.value == four.value == 0.0
        assert four.std_dev == pytest.approx(single.std_dev / 2.0)
        assert single.mode is UncertaintyMode.RIGOROUS
        named = angular_specification(4.0e-5, strategies=(Strategy.NOMINAL_PRECISION,))
        assert named.mode is UncertaintyMode.APPROXIMATE and Strategy.NOMINAL_PRECISION in named.strategies
        with pytest.raises(ValidationError):
            angular_specification(4.0e-5, sets=0)

    def test_each_reading_carries_the_profiles_precision(self, total_station):
        direction = total_station.direction_quantity(1.0, sets=4)
        assert direction.std_dev == pytest.approx(1.0e-5 / 2.0)
        assert direction.unit is Unit.RADIAN and Strategy.NOMINAL_PRECISION in direction.strategies
        zenith = total_station.zenith_quantity(1.5, 1000.0)
        assert zenith.std_dev == pytest.approx(2.0e-5 + 1.0e-8 * 1000.0)
        distance = total_station.distance_quantity(500.0)
        assert distance.std_dev == pytest.approx(0.002 + 2.0e-6 * 500.0)
        assert distance.unit is Unit.METRE
        assert total_station.instrument_height_quantity(1.5).std_dev == pytest.approx(0.001)
        assert total_station.target_height_quantity(1.7).std_dev == pytest.approx(0.002)

    def test_a_staff_reading_needs_the_levels_precision(self):
        from geocomp.core.instruments.level import LevelProfile

        reading = LevelProfile(id="lv", sigma_reading=0.0003).reading_quantity(1.234)
        assert reading.value == 1.234 and reading.std_dev == pytest.approx(0.0003)
        assert Strategy.NOMINAL_PRECISION in reading.strategies
        with pytest.raises(ValidationError) as caught:
            LevelProfile(id="bare").reading_quantity(1.0)
        assert caught.value.code == "validation.level_without_reading_sigma"

    def test_a_levelling_class_round_trips_and_omits_what_is_empty(self):
        from geocomp.core.instruments.level import LevellingClass

        full = LevellingClass(
            id="first",
            name="First order",
            tolerance_coefficient=0.004,
            max_sight_length=50.0,
            max_sight_imbalance=1.0,
            max_accumulated_imbalance=3.0,
            source="IBGE",
        )
        assert LevellingClass.from_dict(full.to_dict()) == full
        bare = LevellingClass(id="bare")
        assert "name" not in bare.to_dict() and "source" not in bare.to_dict()
        assert LevellingClass.from_dict(bare.to_dict()) == bare

    def test_a_gravimeters_label_is_its_name_or_its_id(self):
        from geocomp.core.instruments.gravimeter import GravimeterProfile

        assert GravimeterProfile(id="g1", name="CG-5 #42").label == "CG-5 #42"
        assert GravimeterProfile(id="g1").label == "g1"

    def test_the_library_adds_a_class_once_and_replaces_a_recalibrated_profile(self, total_station):
        from dataclasses import replace

        from geocomp.core.instruments.gravimeter import GravimeterProfile
        from geocomp.core.instruments.level import LevellingClass, LevelProfile
        from geocomp.core.instruments.profiles import ProfileLibrary

        library = ProfileLibrary()
        library.add_levelling_class(LevellingClass(id="first"))
        assert library.default_levelling_class == "first"
        library.add_levelling_class(LevellingClass(id="second"))
        assert library.default_levelling_class == "first", "the first added stays the default"
        with pytest.raises(ValidationError):
            library.add_levelling_class(LevellingClass(id="first"))

        library.replace_instrument(total_station)
        library.replace_instrument(replace(total_station, sigma_direction=5.0e-6))
        assert library.instruments["ts"].sigma_direction == 5.0e-6
        library.replace_level(LevelProfile(id="lv", sigma_reading=0.001))
        library.replace_level(LevelProfile(id="lv", sigma_reading=0.0005))
        assert library.levels["lv"].sigma_reading == 0.0005
        library.replace_gravimeter(GravimeterProfile(id="g", name="before"))
        library.replace_gravimeter(GravimeterProfile(id="g", name="recalibrated"))
        assert library.gravimeters["g"].name == "recalibrated"


class TestTheModels:
    def test_each_type_has_its_spec(self):
        from geocomp.core.models.observation import OBSERVATION_TYPES, ObservationType, observation_type_spec

        for kind in ObservationType:
            assert observation_type_spec(kind) is OBSERVATION_TYPES[kind]

    def test_a_rejection_record_round_trips_with_its_evidence(self):
        from geocomp.core.models.observation import RejectionRecord

        record = RejectionRecord(
            reason="blunder located by data snooping",
            test="w-test (tau)",
            statistic=4.2,
            critical_value=3.3,
            at=datetime(2026, 10, 3, 12, 0, tzinfo=UTC),
            by="surveyor",
        )
        back = RejectionRecord.from_dict(record.to_dict())
        assert back == record
        bare = RejectionRecord(reason="obstructed sight")
        assert bare.to_dict() == {"reason": "obstructed sight"}
        assert RejectionRecord.from_dict(bare.to_dict()) == bare

    def test_a_positions_standard_deviations(self):
        from geocomp.core.models import CoordinateSystem, Position

        position = Position(
            values=(
                Quantity.from_std_dev(1.0, 0.01, Unit.METRE),
                Quantity.from_std_dev(2.0, 0.02, Unit.METRE),
                Quantity.from_std_dev(3.0, 0.03, Unit.METRE),
            ),
            system=CoordinateSystem.PROJECTED,
            crs="LOCAL",
        )
        assert position.std_devs() == pytest.approx((0.01, 0.02, 0.03))

    def test_a_quantity_knows_whether_it_is_rigorous(self):
        assert Quantity.from_std_dev(1.0, 0.1, Unit.METRE).is_rigorous
        assert not Quantity.approximate(1.0, 0.1, Unit.METRE, Strategy.NOMINAL_PRECISION).is_rigorous

    def test_settings_name_their_translation_keys(self):
        from geocomp.core.settings_def import SECTIONS, SETTINGS

        setting = SETTINGS[0]
        assert setting.label_code == f"setting.{setting.key}.label"
        assert setting.help_code == f"setting.{setting.key}.help"
        assert SECTIONS[0].label_code == f"settings.section.{SECTIONS[0].id}.label"

    def test_a_basemap_catalogue_round_trips(self):
        from geocomp.core.basemaps import DEFAULT_SERVICES, BaseMapCatalogue

        catalogue = BaseMapCatalogue(services=DEFAULT_SERVICES)
        assert BaseMapCatalogue.from_dict(catalogue.to_dict()).to_dict() == catalogue.to_dict()


class TestGnss:
    def test_an_antenna_is_eccentric_when_it_is_offset_horizontally(self):
        from geocomp.core.techniques.gnss.baselines import AntennaOffset, AntennaReduction

        centred = AntennaOffset(up=Quantity.from_std_dev(1.5, 0.001, Unit.METRE))
        offset = AntennaOffset(
            up=Quantity.from_std_dev(1.5, 0.001, Unit.METRE),
            east=Quantity.from_std_dev(0.2, 0.001, Unit.METRE),
        )
        assert not centred.is_eccentric and offset.is_eccentric
        assert not AntennaReduction(base=centred, rover=centred).is_eccentric
        assert AntennaReduction(base=centred, rover=offset).is_eccentric

    def test_a_batch_says_which_succeeded(self):
        from geocomp.core.techniques.gnss.batch import BatchOutcome, BatchReport, BatchResult

        report = BatchReport(
            results=(
                BatchResult(key="a", outcome=BatchOutcome.SUCCEEDED, value=1),
                BatchResult(key="b", outcome=BatchOutcome.FAILED, code="engine.failed"),
            )
        )
        assert [r.key for r in report.succeeded] == ["a"]
        assert [r.ok for r in report.results] == [True, False]

    def test_a_sessions_duration_and_whether_it_is_wholly_fixed(self):
        from geocomp.core.techniques.gnss.quality import SessionQuality

        start = datetime(2025, 1, 1, tzinfo=UTC)

        def quality(fixed: float, *, epochs: int = 120, end=start + timedelta(hours=1)):
            return SessionQuality(
                session_id="s",
                epochs=epochs,
                status_counts={},
                fixed_fraction=fixed,
                satellites_least=7,
                satellites_most=9,
                ratio_best=10.0,
                ratio_median=5.0,
                start=start,
                end=end,
            )

        assert quality(1.0).duration_seconds == 3600.0
        assert quality(1.0, end=None).duration_seconds is None
        assert quality(1.0).is_wholly_fixed
        assert not quality(0.95).is_wholly_fixed
        assert not quality(1.0, epochs=0).is_wholly_fixed


class TestGravimetry:
    def test_a_reduced_reading_is_tide_free(self):
        from geocomp.core.techniques.gravimetry.readings import reduce_readings
        from geocomp.core.techniques.gravimetry.tides import TIDE_SYSTEM
        from tests.test_gravimetry_readings import _library, _reading

        (reduced,) = reduce_readings([_reading()], _library())
        assert reduced.tide_system == TIDE_SYSTEM == "tide-free"


class TestLevelling:
    @staticmethod
    def _reading(station: str, value: float, distance: float = 30.0):
        from geocomp.core.techniques.levelling.readings import StaffReading

        return StaffReading(
            station=station,
            reading=Quantity.from_std_dev(value, 0.0003, Unit.METRE),
            distance=Quantity.from_std_dev(distance, 0.1, Unit.METRE),
        )

    def test_a_line_names_its_stations_in_order_side_shots_included(self):
        from geocomp.core.techniques.levelling.line import LevellingLine
        from geocomp.core.techniques.levelling.readings import LevelSetup

        line = LevellingLine(
            id="L1",
            setups=(
                LevelSetup(
                    id="s1", backsight=self._reading("A", 1.5), foresights=(self._reading("T1", 1.2),)
                ),
                LevelSetup(
                    id="s2",
                    backsight=self._reading("T1", 1.4),
                    foresights=(self._reading("B", 1.1), self._reading("side", 0.9)),
                ),
            ),
        )
        assert line.stations == ("A", "T1", "B", "side")

    def test_a_reversed_line_is_the_same_difference_negated(self):
        from geocomp.core.techniques.levelling.line import (
            LevellingLine,
            reduce_line,
            reverse_height_difference,
        )
        from geocomp.core.techniques.levelling.readings import LevelSetup

        reduction = reduce_line(
            LevellingLine(
                id="L1",
                setups=(
                    LevelSetup(
                        id="s1", backsight=self._reading("A", 1.5), foresights=(self._reading("B", 1.2),)
                    ),
                ),
            )
        )
        back = reverse_height_difference(reduction)
        assert back.value == pytest.approx(-reduction.height_difference.value)
        assert back.variance == pytest.approx(reduction.height_difference.variance)

    def test_a_three_wire_set_round_trips_and_gives_a_staff_reading(self):
        from geocomp.core.techniques.levelling.readings import StaffReading, ThreeWireReading

        wires = ThreeWireReading(
            upper=Quantity.from_std_dev(1.650, 0.0005, Unit.METRE),
            middle=Quantity.from_std_dev(1.500, 0.0005, Unit.METRE),
            lower=Quantity.from_std_dev(1.350, 0.0005, Unit.METRE),
        )
        assert ThreeWireReading.from_dict(wires.to_dict()) == wires
        reading = StaffReading.from_three_wire("B", wires)
        assert reading.station == "B" and reading.three_wire == wires
        assert reading.reading.value == pytest.approx(wires.mean().value)
        assert reading.distance.value == pytest.approx(100.0 * (1.650 - 1.350))

    def test_a_setup_is_approximate_when_any_reading_is(self):
        from geocomp.core.techniques.levelling.readings import LevelSetup, StaffReading

        rigorous = LevelSetup(
            id="s", backsight=self._reading("A", 1.5), foresights=(self._reading("B", 1.2),)
        )
        assert rigorous.mode is UncertaintyMode.RIGOROUS
        nominal = StaffReading(
            station="B", reading=Quantity.approximate(1.2, 0.001, Unit.METRE, Strategy.NOMINAL_PRECISION)
        )
        assert LevelSetup(id="s", backsight=self._reading("A", 1.5), foresights=(nominal,)).mode is (
            UncertaintyMode.APPROXIMATE
        )


class TestTotalStation:
    @staticmethod
    def _face_reading(target: str, face, *, distance: float | None = 100.0):
        from geocomp.core.techniques.total_station.readings import FaceReading

        return FaceReading(
            target=target,
            face=face,
            horizontal=Quantity.from_std_dev(0.5, 1e-5, Unit.RADIAN),
            zenith=Quantity.from_std_dev(1.5, 1e-5, Unit.RADIAN),
            distance=None if distance is None else Quantity.from_std_dev(distance, 0.002, Unit.METRE),
        )

    def test_faces_pairs_and_setups(self):
        from geocomp.core.techniques.total_station.readings import Face, FacePair, Setup

        assert Face.DIRECT.is_direct and not Face.REVERSE.is_direct
        pair = FacePair(
            direct=self._face_reading("B", Face.DIRECT), reverse=self._face_reading("B", Face.REVERSE)
        )
        angles_only = FacePair(
            direct=self._face_reading("C", Face.DIRECT, distance=None),
            reverse=self._face_reading("C", Face.REVERSE, distance=None),
        )
        assert pair.has_distance and not angles_only.has_distance
        height = Quantity.from_std_dev(1.5, 0.001, Unit.METRE)
        setup = Setup(station="A", instrument_height=height, pairs=(pair, angles_only, pair))
        assert setup.targets == ("B", "C")
        assert not setup.is_empty and Setup(station="A", instrument_height=height).is_empty

    def test_a_face_reduction_names_its_blunder_candidates(self):
        from geocomp.core.findings import Finding, Severity
        from geocomp.core.techniques.total_station.face import FaceReduction

        def reduction(*findings):
            angle = Quantity.from_std_dev(0.5, 1e-5, Unit.RADIAN)
            return FaceReduction(
                target="B",
                horizontal=angle,
                zenith=angle,
                distance=None,
                collimation=angle,
                vertical_index=angle,
                findings=findings,
            )

        blocking = Finding(code="face_disagreement", severity=Severity.BLOCKING, message="faces disagree")
        warning = Finding(code="large_collimation", severity=Severity.WARNING, message="large c")
        assert reduction().is_clean and not reduction().blunder_candidates
        mixed = reduction(blocking, warning)
        assert not mixed.is_clean and mixed.blunder_candidates == (blocking,)
