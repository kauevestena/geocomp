# SPDX-License-Identifier: GPL-2.0-or-later
"""Multi-epoch comparison and deformation analysis (``specs/14``, phase P10a).

Every criterion of ``specs/14`` section 9 that synthetic data can decide,
against ``tests/monitoring_network.py``: a structure measured at several
epochs, each epoch adjusted by the core as a free network from its own
starting coordinates, with motion injected into the truth at known stations.
Criterion 3 -- a *published* worked example -- waits on one being supplied
(``specs/22`` §5.3), and is not claimed here.
"""

from __future__ import annotations

import math
from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pytest

from geocomp.core.errors import ValidationError
from geocomp.core.geodesy.frames import transform_point
from geocomp.core.models import (
    AdjustedStation,
    AdjustmentStatistics,
    CoordinateSystem,
    DatumDefinition,
    Epoch,
    HeightType,
    Position,
    Solution,
    SolutionKind,
)
from geocomp.core.monitoring import (
    NOT_SIGNIFICANT,
    SIGNIFICANT,
    AlertKind,
    AlertThreshold,
    analyse,
    check_reference,
    compare,
    evaluate_alerts,
    series,
    strain,
)
from geocomp.core.uncertainty import Covariance, Quantity, Strategy, UncertaintyMode
from geocomp.core.units import Unit

from .monitoring_network import LAYOUT, OBJECTS, REFERENCE, epoch

CONFIDENCE = 0.99


@pytest.fixture(scope="module")
def stable():
    return epoch(2025.0, seed=1)


@pytest.fixture(scope="module")
def moved():
    """O2 moved 10 mm, 8 east and 6 south; nothing else."""
    return epoch(2026.0, moves={"O2": (0.008, -0.006)}, seed=2)


@pytest.fixture(scope="module")
def analysis(stable, moved):
    return analyse(compare(stable, moved), REFERENCE, confidence=CONFIDENCE)


# -- criterion 4: a known displacement ------------------------------------------


class TestCriterion4InjectedDisplacement:
    def test_it_is_recovered_within_its_uncertainty(self, analysis):
        displacement = analysis.displacement("O2")
        for value, truth, sigma in zip(
            displacement.values, (0.008, -0.006), displacement.std_devs, strict=True
        ):
            assert abs(value - truth) < 3.0 * sigma

    def test_it_is_significant(self, analysis):
        assert analysis.displacement("O2").decision == SIGNIFICANT
        assert not analysis.displacement("O2").horizontal.passed

    def test_no_other_station_is_flagged(self, analysis):
        assert analysis.significant == ("O2",)

    def test_the_reference_block_passes_and_the_network_as_a_whole_does_not(self, analysis):
        assert analysis.reference_check.passed
        assert not analysis.global_test.passed

    def test_the_two_epochs_datums_are_not_mistaken_for_motion(self, stable, moved):
        """Each epoch is a free network from its own starts: centimetres apart
        in datum. Read without the S-transformation, every station would move."""
        raw = compare(stable, moved)
        assert np.max(np.abs(raw.difference)) > 0.002
        analysed = analyse(raw, REFERENCE, confidence=CONFIDENCE)
        stable_values = [d for d in analysed.displacements if d.station_id != "O2"]
        assert max(abs(v) for d in stable_values for v in d.values) < 0.003


# -- criterion 5: a moving reference station ----------------------------------------


@pytest.fixture(scope="module")
def reference_moved(stable):
    """R3, a reference pillar, moved 18 mm."""
    return compare(stable, epoch(2026.0, moves={"R3": (0.015, 0.010)}, seed=3))


class TestCriterion5MovingReference:
    @pytest.fixture
    def comparison(self, reference_moved):
        return reference_moved

    def test_the_block_fails_and_the_station_is_named(self, comparison):
        check = check_reference(comparison, REFERENCE, confidence=CONFIDENCE)
        assert not check.passed
        assert check.implicated == ("R3",)
        assert check.stable == ("R1", "R2", "R4")
        assert check.final.passed
        step = check.steps[0]
        assert max(step.contributions, key=step.contributions.get) == "R3"

    def test_the_analysis_does_not_proceed_on_it(self, comparison):
        with pytest.raises(ValidationError) as caught:
            analyse(comparison, REFERENCE, confidence=CONFIDENCE)
        assert caught.value.code == "validation.monitoring_reference_block_unstable"
        assert caught.value.context["stations"] == ["R3"]
        assert caught.value.context["steps"][0]["removed"] == "R3"

    def test_with_the_block_the_user_accepts_the_motion_is_found(self, comparison):
        analysed = analyse(comparison, ("R1", "R2", "R4"), confidence=CONFIDENCE)
        assert analysed.displacement("R3").decision == SIGNIFICANT
        assert analysed.displacement("R3").role == "object"
        assert analysed.significant == ("R3",)


# -- criterion 6 and 7 -----------------------------------------------------------------


class TestCriterion6Independence:
    def test_without_cross_covariance_it_is_approximate_and_says_which_way(self, stable, moved):
        comparison = compare(stable, moved)
        assert comparison.mode is UncertaintyMode.APPROXIMATE
        assert Strategy.INDEPENDENCE_ASSUMED in comparison.strategies
        assert "understated" in comparison.bias

    def test_with_it_the_result_is_rigorous_and_the_uncertainty_smaller(self, stable, moved):
        independent = compare(stable, moved)
        # A positive correlation between the epochs -- a shared datum, say.
        cross = 0.3 * np.minimum(independent.first_covariance, independent.second_covariance)
        cross = (cross + cross.T) / 2.0
        correlated = compare(stable, moved, cross_covariance=cross)
        assert correlated.mode is UncertaintyMode.RIGOROUS
        assert not correlated.strategies
        assert np.trace(correlated.covariance) < np.trace(independent.covariance)


class TestCriterion7NotSignificantIsNotZero:
    def test_a_small_displacement_keeps_its_value(self, stable):
        comparison = compare(stable, epoch(2026.0, moves={"O5": (0.0006, 0.0)}, seed=2))
        displacement = analyse(comparison, REFERENCE, confidence=CONFIDENCE).displacement("O5")
        assert displacement.decision == NOT_SIGNIFICANT
        assert displacement.values[0] != 0.0
        assert displacement.std_devs[0] > 0.0
        # Its confidence ellipse contains zero: that is what not significant means.
        assert displacement.ellipse is not None


# -- criterion 1 and 2: compatibility ------------------------------------------------


def _geocentric(
    solution_id: str, frame: str, year: float, positions: dict, *, sigma: float = 0.003
) -> Solution:
    stations = []
    labels, blocks = [], []
    for station, xyz in positions.items():
        values = tuple(Quantity.from_std_dev(float(v), sigma, Unit.METRE) for v in xyz)
        stations.append(
            AdjustedStation(
                station_id=station,
                position=Position(
                    values=values,
                    system=CoordinateSystem.CARTESIAN,
                    crs=frame,
                    epoch=Epoch.from_decimal_year(year),
                    height_type=HeightType.ELLIPSOIDAL,
                ),
                covariance=Covariance(
                    matrix=np.eye(3) * sigma**2,
                    labels=tuple(f"{station}.{c}" for c in "xyz"),
                    units=(Unit.METRE,) * 3,
                ),
            )
        )
        labels += [f"{station}.{c}" for c in "xyz"]
        blocks.append(np.eye(3) * sigma**2)
    size = len(labels)
    matrix = np.zeros((size, size))
    for i, block in enumerate(blocks):
        matrix[3 * i : 3 * i + 3, 3 * i : 3 * i + 3] = block
    return Solution(
        id=solution_id,
        network_id="gnss",
        kind=SolutionKind.ADJUSTMENT,
        crs=frame,
        epoch=Epoch.from_decimal_year(year),
        datum_definition=DatumDefinition.FIXED,
        adjusted_stations=tuple(stations),
        parameter_covariance=Covariance(matrix=matrix, labels=tuple(labels), units=(Unit.METRE,) * size),
        statistics=AdjustmentStatistics(degrees_of_freedom=10, variance_factor_aposteriori=1.0),
    )


POSITIONS = {
    "A": np.array([3_763_751.0, -4_364_795.0, -2_724_265.0]),
    "B": np.array([3_764_751.0, -4_363_795.0, -2_723_265.0]),
}


class TestCriterion1Frames:
    def test_two_frames_are_transformed_with_a_record(self):
        """The second epoch in ITRF2014, the first in ITRF2020, the same marks:
        once transformed, nothing moved -- and what was applied is on the result."""
        in_2014 = {
            s: transform_point(xyz, source="ITRF2020", target="ITRF2014", epoch=2026.0).xyz
            for s, xyz in POSITIONS.items()
        }
        first = _geocentric("e1", "ITRF2020", 2026.0, POSITIONS)
        second = _geocentric("e2", "ITRF2014", 2026.0, in_2014)
        comparison = compare(first, second)
        assert comparison.geocentric and comparison.components == ("e", "n", "u")
        assert len(comparison.transformations) == 1
        record = comparison.transformations[0]
        assert (record.source, record.target) == ("ITRF2014", "ITRF2020")
        assert np.max(np.abs(comparison.difference)) < 1e-6

    def test_the_transformation_uncertainty_is_a_common_translation(self):
        in_2014 = {
            s: transform_point(xyz, source="ITRF2020", target="ITRF2014", epoch=2026.0).xyz
            for s, xyz in POSITIONS.items()
        }
        comparison = compare(
            _geocentric("e1", "ITRF2020", 2026.0, POSITIONS), _geocentric("e2", "ITRF2014", 2026.0, in_2014)
        )
        accuracy = comparison.transformations[0].accuracy
        same = compare(
            _geocentric("e1", "ITRF2020", 2026.0, POSITIONS), _geocentric("e2", "ITRF2020", 2026.0, POSITIONS)
        )
        added = comparison.covariance - same.covariance
        # Between A and B as much as on either: it moves them together.
        assert added[0, 3] == pytest.approx(added[0, 0], rel=1e-3)
        assert np.trace(added) == pytest.approx(6 * accuracy**2, rel=1e-3)

    def test_a_frame_related_only_at_another_epoch_is_refused(self):
        with pytest.raises(ValidationError) as caught:
            compare(
                _geocentric("e1", "ITRF2020", 2026.0, POSITIONS),
                _geocentric("e2", "SIRGAS2000", 2026.0, POSITIONS),
            )
        assert caught.value.code == "validation.monitoring_frame_needs_velocity"

    def test_incompatible_datum_definitions_are_refused_by_name(self, stable):
        held = replace(stable, datum_definition=DatumDefinition.FIXED, id="held")
        with pytest.raises(ValidationError) as caught:
            compare(stable, held)
        assert caught.value.code == "validation.monitoring_datum_incompatible"
        assert caught.value.context["received"] == ["inner_constraint", "fixed"]

    def test_two_free_definitions_compare_and_the_finding_says_how(self, stable, moved):
        minimum = replace(moved, datum_definition=DatumDefinition.MINIMUM_CONSTRAINT)
        comparison = compare(stable, minimum)
        assert any("S-transformation" in finding for finding in comparison.findings)

    def test_two_projections_are_refused(self, stable, moved):
        other = replace(moved, crs="EPSG:31983")
        with pytest.raises(ValidationError) as caught:
            compare(stable, other)
        assert caught.value.code == "validation.monitoring_frames_differ"

    def test_two_geoid_models_are_refused(self, stable, moved):
        stations = tuple(
            replace(s, position=replace(s.position, geoid_model="mapgeo2015"))
            for s in moved.adjusted_stations
        )
        with pytest.raises(ValidationError) as caught:
            compare(stable, replace(moved, adjusted_stations=stations))
        assert caught.value.code == "validation.monitoring_geoid_models_differ"


class TestCriterion2Epoch:
    def test_a_solution_without_an_epoch_is_refused(self, stable):
        with pytest.raises(ValidationError) as caught:
            compare(stable, SimpleNamespace(id="undated", epoch=None))
        assert caught.value.code == "validation.monitoring_solution_without_epoch"
        assert caught.value.context["solution"] == "undated"

    def test_nor_can_one_be_read_back_without_it(self, stable):
        document = stable.to_dict()
        document["epoch"] = None
        with pytest.raises(ValidationError):
            Solution.from_dict(document)


# -- criterion 8: three epochs --------------------------------------------------------


#: O1's true velocity in the three-epoch series, metres a year.
VELOCITY = (0.004, -0.003)


@pytest.fixture(scope="module")
def three_epochs():
    """2024, 2025, 2026, O1 moving at VELOCITY; everything else still."""
    epochs = []
    for n, year in enumerate((2024.0, 2025.0, 2026.0)):
        dt = year - 2024.0
        epochs.append(epoch(year, moves={"O1": (VELOCITY[0] * dt, VELOCITY[1] * dt)}, seed=10 + n))
    return {s.station_id: s for s in series(epochs, reference=REFERENCE, confidence=CONFIDENCE)}


class TestCriterion8Series:
    @pytest.fixture
    def result(self, three_epochs):
        return three_epochs

    def test_the_velocity_is_recovered_with_its_uncertainty(self, result):
        o1 = result["O1"]
        for value, truth, sigma in zip(o1.velocity, VELOCITY, o1.velocity_std_devs, strict=True):
            assert abs(value - truth) < 3.0 * sigma
            assert sigma < 0.002
        assert not o1.velocity_test.passed
        assert o1.degrees_of_freedom == 2

    def test_a_stable_station_has_no_significant_velocity(self, result):
        assert all(result[s].velocity_test.passed for s in REFERENCE)

    def test_the_series_is_plottable(self, result):
        rows = result["O1"].to_rows()
        assert len(rows) == 3 * 2
        assert {row["epoch"] for row in rows} == {2024.0, 2025.0, 2026.0}
        first = [row for row in rows if row["epoch"] == 2024.0]
        assert all(row["offset"] == 0.0 and row["std_dev"] > 0.0 for row in first)
        assert result["O1"].strategies == frozenset({Strategy.INDEPENDENCE_ASSUMED})


# -- deformation across the network ---------------------------------------------------


class TestStrain:
    def test_a_homogeneous_extension_is_found_and_measured(self, stable):
        """The structure stretched 40 ppm east-west about its centre."""
        centre = np.mean([LAYOUT[s] for s in OBJECTS], axis=0)
        moves = {s: (40e-6 * (LAYOUT[s][0] - centre[0]), 0.0) for s in OBJECTS}
        later = epoch(2026.0, moves=moves, seed=4)
        analysed = analyse(compare(stable, later), REFERENCE, confidence=CONFIDENCE)
        result = strain(analysed)
        assert result.deforming
        assert abs(result.strain_tensor[0] - 40e-6) < 3.0 * result.std_devs["e_ee"]
        assert abs(result.strain_tensor[1]) < 3.0 * result.std_devs["e_nn"]
        assert result.azimuth == pytest.approx(math.pi / 2, abs=0.2)

    def test_a_block_that_moved_whole_is_not_straining(self, stable):
        moves = dict.fromkeys(OBJECTS, (0.006, 0.004))
        analysed = analyse(
            compare(stable, epoch(2026.0, moves=moves, seed=5)), REFERENCE, confidence=CONFIDENCE
        )
        result = strain(analysed)
        assert not result.deforming
        assert result.rigid_translation[0] == pytest.approx(0.006, abs=0.002)
        assert result.rigid_translation[1] == pytest.approx(0.004, abs=0.002)
        assert set(analysed.significant) == set(OBJECTS)

    def test_too_few_points_are_refused(self, analysis):
        with pytest.raises(ValidationError) as caught:
            strain(analysis, stations=("O1", "O2"))
        assert caught.value.code == "validation.monitoring_strain_configuration"


# -- alerts ------------------------------------------------------------------------------


class TestAlerts:
    def test_the_right_stations_are_flagged(self, analysis):
        thresholds = [
            AlertThreshold(AlertKind.HORIZONTAL, limit=0.005, group="structure", stations=frozenset(OBJECTS)),
            AlertThreshold(AlertKind.SIGNIFICANCE),
        ]
        alerts = evaluate_alerts(thresholds, displacements=analysis.displacements)
        flagged = {(a.threshold.kind, a.station_id) for a in alerts if a.exceeded}
        assert flagged == {(AlertKind.HORIZONTAL, "O2"), (AlertKind.SIGNIFICANCE, "O2")}
        # Checked as well as flagged: every covered station has its alert.
        assert len([a for a in alerts if a.threshold.kind is AlertKind.HORIZONTAL]) == len(OBJECTS)

    def test_large_but_not_significant_motion_still_crosses_the_line(self, analysis):
        """The owner's criterion is not silenced by the survey's."""
        alerts = evaluate_alerts(
            [AlertThreshold(AlertKind.HORIZONTAL, limit=0.0005)], displacements=analysis.displacements
        )
        crossed = [a for a in alerts if a.exceeded and not a.significant]
        assert crossed

    def test_a_threshold_needs_a_limit(self):
        with pytest.raises(ValidationError):
            AlertThreshold(AlertKind.VERTICAL, limit=0.0)


# -- heights alone ------------------------------------------------------------------


def _levelling(year: float, *, sink: dict | None = None, seed: int = 1) -> Solution:
    """Five marks levelled every pair, 0.5 mm a difference, adjusted free."""
    from itertools import combinations

    from geocomp.core.adjustment.least_squares import AdjustmentOptions, adjust, to_solution
    from geocomp.core.adjustment.parameters import Frame
    from geocomp.core.models import Network, Observation, ObservationType, Station

    heights = {"B1": 100.0, "B2": 101.2, "B3": 99.4, "P1": 100.7, "P2": 98.9}
    for mark, change in (sink or {}).items():
        heights[mark] += change
    rng = np.random.default_rng(seed)
    network = Network(id=f"levels-{year}", crs="LOCAL")
    for mark in heights:
        network.add_station(Station(id=mark))
    for a, b in combinations(heights, 2):
        network.add_observation(
            Observation(
                id=f"l-{a}-{b}",
                type=ObservationType.HEIGHT_DIFFERENCE,
                stations=(a, b),
                values=(
                    Quantity.from_std_dev(
                        heights[b] - heights[a] + rng.normal(0, 0.0005), 0.0005, Unit.METRE
                    ),
                ),
            )
        )
    options = AdjustmentOptions(frame=Frame.HEIGHT_1D, datum=DatumDefinition.INNER_CONSTRAINT)
    start = {mark: {"h": 100.0 + rng.uniform(-0.05, 0.05)} for mark in heights}
    run = adjust(network, options, approximate=start)
    return to_solution(
        run,
        network,
        solution_id=network.id,
        crs="LOCAL",
        epoch=Epoch.from_decimal_year(year),
        datum=DatumDefinition.INNER_CONSTRAINT,
        height_type=HeightType.ORTHOMETRIC,
    )


class TestHeights:
    def test_a_sinking_mark_is_found_against_a_shift_datum(self):
        comparison = compare(_levelling(2025.0), _levelling(2026.0, sink={"P2": -0.004}, seed=2))
        assert comparison.components == ("h",)
        analysed = analyse(comparison, ("B1", "B2", "B3"), confidence=CONFIDENCE)
        assert analysed.datum == "translation"
        assert analysed.significant == ("P2",)
        displacement = analysed.displacement("P2")
        assert displacement.values[0] == pytest.approx(-0.004, abs=3 * displacement.std_devs[0])
        assert displacement.horizontal is None and displacement.ellipse is None
        assert displacement.vertical_magnitude == pytest.approx(0.004, abs=0.0015)
