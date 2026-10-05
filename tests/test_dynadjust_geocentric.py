# SPDX-License-Identifier: GPL-2.0-or-later
"""The geocentric frame against DynAdjust, on a combined survey (specs/13 section 3).

P6 cross-validated the in-house core on GNSS baselines alone, which are linear
in the coordinates -- so the core could hold them in any three orthogonal metres
and the comparison said nothing about how an angle is modelled on a curved
Earth. This one does. ``tests/combined_network.py`` is a six-station survey
over 3 km with GNSS baselines, an ellipsoidal height, and a total station's
direction sets, zenith angles, slope distances, a horizontal angle and an
azimuth. GeoComp's writer turned it into ``combined-{stn,msr}.xml``; DynAdjust's
answer is the committed ``combined.*``; and the in-house core adjusts **the same
two files**, read back with GeoComp's own DynaML reader, in
``Frame.GEOCENTRIC_3D`` with each station's own vertical. The files round
coordinates, baselines and distances to 0.1 mm, so adjusting the survey itself
would compare two slightly different problems.

**What is compared, and what is not.** Two modelling differences are real and
are recorded in ``specs/07`` section 6.3 rather than tolerated here:

* For a **slope distance** DynAdjust carries the target height along the
  instrument's vertical, not the target's own (0.8 mm on a 2.9 km sight with a
  1.7 m reflector); its zenith distances use each end's own, as GeoComp does
  for every type. The survey is therefore built with ``target=0``, where the
  two coincide; the instrument heights stay, and both carry those the same way.
* DynAdjust adjusts a **direction set** as derived angles and weights them with
  their full banded covariance -- the coordinates agree -- but its chi-square
  adds ``v^2 / sigma^2`` over the angles alone, dropping the correlation between
  consecutive ones. Its sigma zero is therefore not ``v^T P v / r`` of its own
  weights. The test below reproduces DynAdjust's figure from the in-house
  residuals by making exactly that omission, which is what shows it is the
  cause and not a difference of solution.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest

from geocomp.core.adjustment.least_squares import (
    AdjustmentOptions,
    adjust,
    to_observation_results,
)
from geocomp.core.adjustment.parameters import Frame
from geocomp.core.errors import DataError
from geocomp.core.models import ClusterKind, ConstraintMode, DatumDefinition, ObservationType
from geocomp.core.units import Unit
from geocomp.engines.dynadjust.engine import (
    ANGULAR_FORMAT,
    MEASUREMENT_FORMAT,
    DynAdjustEngine,
    DynAdjustJob,
)
from geocomp.engines.dynadjust.read_dynaml import read_dynaml
from geocomp.engines.dynadjust.read_output import match_observations, read_measurements
from geocomp.engines.dynadjust.solution import read_solution

from .combined_network import EPOCH, FRAME, SETUPS, TRUTH, survey
from .conftest import requires_dynadjust

OUTPUT = Path(__file__).parent / "data" / "dynadjust" / "output"

#: How far the in-house starting coordinates are moved from the written ones.
#: The same five metres as the P6 cross-validation, for the same reason: so
#: agreement is not an artefact of having started where DynAdjust did.
PERTURBATION = 5.0

#: DynAdjust prints coordinates to 0.1 mm, so half that is the most two equal
#: answers can differ by on the page; the micrometre is for arithmetic. The
#: largest difference on this survey is 0.049 mm, inside the rounding.
PRINTED = 0.5e-4 + 1e-6


def written():
    """The network DynAdjust adjusted, as GeoComp reads its input back."""
    return read_dynaml(OUTPUT / "combined-stn.xml", OUTPUT / "combined-msr.xml").network


def job(network) -> DynAdjustJob:
    return DynAdjustJob(
        network=network,
        name="combined",
        target_frame=FRAME,
        target_epoch=EPOCH,
        iteration_threshold=1e-6,
        maximum_iterations=20,
    )


def _held(network) -> dict[str, np.ndarray]:
    return {
        identifier: np.array([q.value for q in station.constraint.position.values])
        for identifier, station in network.stations.items()
        if station.constraint.mode is ConstraintMode.FIXED
    }


def _coordinates(run, network, station: str) -> np.ndarray:
    """A station's adjusted ECEF position; a held one is where it was held."""
    held = _held(network)
    if station in held:
        return held[station]
    columns = run.layout.station_columns(station)
    return np.array([run.parameters[columns[c]] for c in ("x", "y", "z")])


@pytest.fixture(scope="module")
def network():
    return written()


@pytest.fixture(scope="module")
def in_house(network):
    rng = np.random.default_rng(20260926)
    approximate = {
        identifier: dict(
            zip(
                ("x", "y", "z"),
                (q.value + rng.uniform(-PERTURBATION, PERTURBATION) for q in station.approx_position.values),
                strict=True,
            )
        )
        for identifier, station in network.stations.items()
    }
    return adjust(
        network,
        AdjustmentOptions(frame=Frame.GEOCENTRIC_3D, datum=DatumDefinition.FIXED),
        approximate=approximate,
    )


@pytest.fixture(scope="module")
def dynadjust(network):
    return read_solution(
        OUTPUT / "combined.adj",
        network=network,
        apu_path=OUTPUT / "combined.apu",
        # What ``DynAdjustEngine.parse`` passes, so this reads the file the way
        # a GeoComp-driven run would.
        angular_format=ANGULAR_FORMAT,
        measurement_format=MEASUREMENT_FORMAT,
    )


class TestTheCommittedInput:
    def test_it_is_what_the_writer_makes_of_the_survey(self, tmp_path) -> None:
        """The fixture's input is GeoComp's own DynaML. If the writer changes,
        the output was made from files it no longer writes, and this says so
        before a stale comparison can pass."""
        DynAdjustEngine().prepare(job(survey(target=0.0)), tmp_path)
        for name in ("combined-stn.xml", "combined-msr.xml"):
            assert (tmp_path / name).read_text() == (OUTPUT / name).read_text(), name

    def test_reading_it_back_loses_nothing_the_adjustment_uses(self, network) -> None:
        """Every observation, every set, and the heights the zenith angles and
        slope distances were measured with."""
        original = survey(target=0.0)
        assert len(network.observations) == len(original.observations) == 48
        assert len(network.clusters) == len(original.clusters) == 5
        setups = [
            o
            for o in network.observations.values()
            if o.type in (ObservationType.SLOPE_DISTANCE, ObservationType.ZENITH_ANGLE)
        ]
        assert len(setups) == 28
        assert all(o.instrument_height.value == pytest.approx(1.563) for o in setups)
        assert all(o.target_height.value == 0.0 for o in setups)


class TestTheTwoEnginesAgree:
    def test_they_solve_problems_of_the_same_size(self, in_house, dynadjust) -> None:
        """Degrees of freedom agree; the counts behind them do not, and should
        not. GeoComp models a set of *n* directions as *n* observations and one
        orientation unknown, DynAdjust as *n - 1* derived angles and none: four
        sets, so four more of each here, and the same redundancy."""
        sets = len(SETUPS)
        assert in_house.degrees_of_freedom == dynadjust.statistics.degrees_of_freedom == 38
        assert in_house.system.design.shape[0] == dynadjust.statistics.n_observations + sets
        assert in_house.system.design.shape[1] == dynadjust.statistics.n_parameters + sets

    def test_the_coordinates_agree_to_the_printed_precision(
        self, in_house, network, dynadjust
    ) -> None:
        """The headline: two implementations of angles on the ellipsoid, one
        started 5 m out, placing four free stations as close together as the
        0.1 mm DynAdjust prints can show -- over 3 km, with sights up to 2.9 km
        long."""
        for station in dynadjust.adjusted_stations:
            theirs = np.array([q.value for q in station.position.values])
            difference = np.abs(_coordinates(in_house, network, station.station_id) - theirs)
            assert difference.max() <= PRINTED, (station.station_id, difference)

    def test_the_answer_is_near_the_truth_the_measurements_came_from(
        self, in_house, network
    ) -> None:
        """Not a comparison but a sanity check on the survey: noise of a few
        millimetres and arcseconds cannot move a station decimetres."""
        for station, truth in TRUTH.items():
            assert np.abs(_coordinates(in_house, network, station) - truth).max() < 0.02

    def test_every_residual_dynadjust_reports_agrees(self, in_house, network, dynadjust) -> None:
        """Per observation, to the file's printed precision -- 0.1 mm for the
        linear rows and 0.0001 arcseconds for the angles -- so a sign convention
        or a unit that differed would show at once."""
        ours: dict[str, list[float]] = {}
        for result in to_observation_results(in_house):
            ours.setdefault(result.observation_id, []).append(result.residual)
        theirs: dict[str, list[float]] = {}
        for result in dynadjust.observation_results:
            theirs.setdefault(result.observation_id, []).append(result.residual)
        for identifier, values in theirs.items():
            angular = network.observations[identifier].values[0].unit is Unit.RADIAN
            tolerance = math.radians(0.0002 / 3600.0) if angular else 1e-4
            assert values == pytest.approx(ours[identifier], abs=tolerance), identifier
        # Every row but the derived angles: 9 baseline components, 14 slope
        # distances, 14 zenith angles, an angle, an azimuth and a height.
        assert sum(len(values) for values in theirs.values()) == 40

    def test_dynadjusts_sigma_zero_is_ours_with_the_angle_correlation_dropped(
        self, in_house, network, dynadjust
    ) -> None:
        """The finding, reproduced rather than tolerated.

        From the in-house residuals, each set's derived-angle residuals are the
        differences of consecutive directions'. With their full covariance --
        ``sigma^2`` times the tridiagonal (2, -1) -- their quadratic form is the
        set's share of the in-house ``v^T P v``, and the in-house sigma zero
        follows. With the diagonal alone it is what DynAdjust's chi-square
        sums, and the result matches DynAdjust's printed figure to its last
        digit. The two differ by far more than that digit, so the match says
        which one DynAdjust computed.
        """
        residual = {r.observation_id: r.residual for r in to_observation_results(in_house)}
        full = diagonal = 0.0
        for cluster in network.clusters.values():
            if cluster.kind is not ClusterKind.DIRECTION_SET:
                continue
            members = [network.observations[i] for i in cluster.observation_ids]
            sigma = members[0].values[0].std_dev
            angles = np.diff([residual[m.id] for m in members])
            size = len(angles)
            covariance = sigma**2 * (2.0 * np.eye(size) - np.eye(size, k=1) - np.eye(size, k=-1))
            full += float(angles @ np.linalg.solve(covariance, angles))
            diagonal += float(angles @ angles) / (2.0 * sigma**2)

        dof = in_house.degrees_of_freedom
        quadratic = in_house.variance_factor_aposteriori * dof
        # The full form is the sets' share of v^T P v, so it cannot exceed it.
        assert 0.0 < full < quadratic
        as_dynadjust = (quadratic - full + diagonal) / dof
        printed = dynadjust.statistics.variance_factor_aposteriori
        assert as_dynadjust == pytest.approx(printed, abs=5.5e-4)
        assert abs(in_house.variance_factor_aposteriori - printed) > 0.02


class TestDirectionSetRows:
    def test_they_are_checked_but_produce_no_result(self, network) -> None:
        """A row is the direction as read plus the *derived angle's* correction:
        a difference of two directions' residuals. It is no one direction's."""
        rows = read_measurements(OUTPUT / "combined.adj", angular_format=MEASUREMENT_FORMAT)
        results = match_observations(rows, network)
        directions = {
            identifier
            for identifier, observation in network.observations.items()
            if observation.type is ObservationType.DIRECTION
        }
        assert sum(1 for row in rows if row.code == "D") == 10
        assert directions.isdisjoint(result.observation_id for result in results)
        assert len(results) == len(rows) - 10

    def test_a_set_out_of_order_still_fails(self, network) -> None:
        rows = read_measurements(OUTPUT / "combined.adj", angular_format=MEASUREMENT_FORMAT)
        rows[0], rows[1] = rows[1], rows[0]
        with pytest.raises(DataError) as excinfo:
            match_observations(rows, network)
        assert excinfo.value.code == "data.dynadjust_measurement_station_mismatch"

    def test_the_measurements_are_not_read_in_the_stations_format(self) -> None:
        """What the engine got wrong: one format for both tables. The stations
        are in HP and the measurements in separated fields, so reading the
        latter as HP fails on the first angle."""
        with pytest.raises(DataError) as excinfo:
            read_measurements(OUTPUT / "combined.adj", angular_format=ANGULAR_FORMAT)
        assert excinfo.value.code == "data.dynadjust_output_not_a_number"


@pytest.mark.engines
@requires_dynadjust
class TestAgainstARealEngine:
    """Tier 4: the same comparison with DynAdjust run now, through the engine."""

    def test_the_pipeline_reaches_the_same_answer(self, in_house, network, tmp_path) -> None:
        solution = DynAdjustEngine().adjust(job(survey(target=0.0)), tmp_path)
        assert solution.statistics.converged
        assert solution.statistics.degrees_of_freedom == in_house.degrees_of_freedom
        for station in solution.adjusted_stations:
            theirs = np.array([q.value for q in station.position.values])
            ours = _coordinates(in_house, network, station.station_id)
            assert np.abs(ours - theirs).max() <= PRINTED


# -- What was set aside (FR-255, P12c-22) -----------------------------------

#: One of each kind that matters: a baseline from a correlated cluster, a
#: direction from a set (not its reference), and a lone slope distance.
ASIDE = ("X4-1", "D0-1", "S5")


def _set_aside(network, identifiers=ASIDE):
    from dataclasses import replace

    from geocomp.core.models.observation import ObservationStatus

    for identifier in identifiers:
        network.observations[identifier] = replace(
            network.observations[identifier], status=ObservationStatus.EXCLUDED
        )
    return network


def _starting(network) -> dict[str, dict[str, float]]:
    rng = np.random.default_rng(20261005)
    return {
        identifier: dict(
            zip(
                ("x", "y", "z"),
                (q.value + rng.uniform(-PERTURBATION, PERTURBATION) for q in station.approx_position.values),
                strict=True,
            )
        )
        for identifier, station in network.stations.items()
    }


def _ignore(text: str, nth: int, *, direction: int | None = None) -> str:
    """Flag the *nth* measurement ``Ignore``, or one of its directions."""
    parts = text.split("<DnaMeasurement>")
    part = parts[nth + 1]
    if direction is None:
        part = part.replace("<Ignore />", "<Ignore>*</Ignore>", 1)
    else:
        pieces = part.split("<Directions>")
        pieces[direction + 1] = pieces[direction + 1].replace("<Ignore />", "<Ignore>*</Ignore>", 1)
        part = "<Directions>".join(pieces)
    parts[nth + 1] = part
    return "<DnaMeasurement>".join(parts)


class TestWhatWasSetAside:
    """Until P12c-22 the DynAdjust path adjusted a set-aside cluster member, the
    core refused one, and a set-aside lone observation made DynAdjust's result
    refuse to read back."""

    def test_a_cluster_keeps_the_rest_under_their_part_of_its_covariance(self) -> None:
        network = _set_aside(written())
        whole = network.clusters["X4"].covariance
        kept = network.active_clusters()["X4"]
        assert kept.observation_ids == ("X4-0", "X4-2")
        rows = [0, 1, 2, 6, 7, 8]
        np.testing.assert_array_equal(kept.covariance.matrix, whole.matrix[np.ix_(rows, rows)])
        assert kept.covariance.labels == tuple(whole.labels[i] for i in rows)
        assert network.active_clusters()["D1"] is network.clusters["D1"]

    def test_a_cluster_wholly_set_aside_is_left_out(self) -> None:
        network = _set_aside(written(), ("X4-0", "X4-1", "X4-2"))
        assert "X4" not in network.active_clusters()

    def test_the_core_adjusts_what_remains_as_a_smaller_survey(self) -> None:
        """What setting aside means: the same answer as a survey that never had
        the observation, with the cluster's covariance cut to the rest."""
        aside = _set_aside(written())
        smaller = written()
        for identifier in ASIDE:
            del smaller.observations[identifier]
        smaller.clusters = aside.active_clusters()
        options = AdjustmentOptions(frame=Frame.GEOCENTRIC_3D, datum=DatumDefinition.FIXED)
        one = adjust(aside, options, approximate=_starting(aside))
        other = adjust(smaller, options, approximate=_starting(smaller))
        assert one.degrees_of_freedom == other.degrees_of_freedom == 33
        np.testing.assert_allclose(one.parameters, other.parameters, rtol=0, atol=1e-9)

    def test_the_writer_writes_only_what_is_active(self, tmp_path) -> None:
        prepared = DynAdjustEngine().prepare(job(_set_aside(written())), tmp_path)
        held = [identifier for element in prepared.elements for identifier in element]
        assert not set(ASIDE) & set(held)
        text = prepared.measurement_file.read_text(encoding="utf-8")
        assert text.count("<Ignore>*</Ignore>") == 0
        assert ("X4-0", "X4-2") in prepared.elements
        assert ("D0-0", "D0-2") in prepared.elements

    def test_the_reader_expects_what_the_writer_wrote(self) -> None:
        from geocomp.engines.dynadjust.read_output import printed_rows

        everything = len(printed_rows(written()))
        # A baseline is three rows, a direction one, a distance one.
        assert len(printed_rows(_set_aside(written()))) == everything - 5


class TestIgnoredByHand:
    """FR-325 (P12c-22): ``Ignore`` set in a prepared job's measurement file."""

    @staticmethod
    def _prepared(tmp_path):
        prepared = DynAdjustEngine().prepare(job(written()), tmp_path)
        return prepared, prepared.measurement_file.read_text(encoding="utf-8")

    def test_a_measurement_flagged_sets_aside_everything_it_holds(self, tmp_path) -> None:
        from geocomp.engines.dynadjust.engine import load_prepared

        prepared, text = self._prepared(tmp_path)
        nth = prepared.elements.index(("X4-0", "X4-1", "X4-2"))
        prepared.measurement_file.write_text(_ignore(text, nth), encoding="utf-8")
        again = load_prepared(tmp_path)
        assert again.ignored == ("X4-0", "X4-1", "X4-2")
        adjusted = again.adjusted_network.observations
        assert not any(adjusted[i].is_active for i in again.ignored)
        assert adjusted["X4-0"].rejection.by == "user"
        assert all(again.job.network.observations[i].is_active for i in again.ignored)

    def test_a_direction_flagged_sets_aside_that_direction(self, tmp_path) -> None:
        from geocomp.engines.dynadjust.engine import load_prepared

        prepared, text = self._prepared(tmp_path)
        nth = prepared.elements.index(("D1-0", "D1-1", "D1-2", "D1-3", "D1-4"))
        prepared.measurement_file.write_text(_ignore(text, nth, direction=1), encoding="utf-8")
        assert load_prepared(tmp_path).ignored == ("D1-2",)

    def test_a_measurement_added_or_removed_is_refused(self, tmp_path) -> None:
        from geocomp.engines.dynadjust.engine import load_prepared

        prepared, text = self._prepared(tmp_path)
        first = text.index("<DnaMeasurement>")
        second = text.index("<DnaMeasurement>", first + 1)
        prepared.measurement_file.write_text(text[:first] + text[second:], encoding="utf-8")
        with pytest.raises(DataError) as refused:
            load_prepared(tmp_path)
        assert refused.value.code == "data.dynadjust_prepared_measurements_changed"
        assert refused.value.context["written"] == len(prepared.elements)

    def test_a_direction_added_or_removed_is_refused_naming_the_set(self, tmp_path) -> None:
        from geocomp.engines.dynadjust.engine import load_prepared

        prepared, text = self._prepared(tmp_path)
        nth = prepared.elements.index(("D1-0", "D1-1", "D1-2", "D1-3", "D1-4"))
        parts = text.split("<DnaMeasurement>")
        start = parts[nth + 1].index("<Directions>")
        end = parts[nth + 1].index("</Directions>") + len("</Directions>")
        parts[nth + 1] = parts[nth + 1][:start] + parts[nth + 1][end:]
        prepared.measurement_file.write_text("<DnaMeasurement>".join(parts), encoding="utf-8")
        with pytest.raises(DataError) as refused:
            load_prepared(tmp_path)
        assert refused.value.code == "data.dynadjust_prepared_directions_changed"
        assert refused.value.context["observation"] == "D1-0"
        assert (refused.value.context["written"], refused.value.context["found"]) == (4, 3)

    def test_a_file_that_is_not_xml_is_left_to_dnaimport(self, tmp_path) -> None:
        from geocomp.engines.dynadjust.engine import load_prepared

        prepared, text = self._prepared(tmp_path)
        prepared.measurement_file.write_text(text[: len(text) // 2], encoding="utf-8")
        assert load_prepared(tmp_path).ignored == ()

    def test_the_provenance_names_what_was_ignored(self, tmp_path) -> None:
        from geocomp.engines.dynadjust.engine import load_prepared, provenance

        prepared, text = self._prepared(tmp_path)
        nth = prepared.elements.index(("X4-0", "X4-1", "X4-2"))
        prepared.measurement_file.write_text(_ignore(text, nth), encoding="utf-8")
        recorded = provenance([], load_prepared(tmp_path)).parameters
        assert recorded["ignored_in_input"] == ["X4-0", "X4-1", "X4-2"]


@pytest.mark.engines
@requires_dynadjust
class TestWhatWasSetAsideAgainstARealEngine:
    """Tier 4. Measured with DynAdjust 1.4.0 when P12c-22 was written."""

    def test_dynadjust_and_the_core_agree_on_what_remains(self, tmp_path) -> None:
        network = _set_aside(written())
        ours = adjust(
            network,
            AdjustmentOptions(frame=Frame.GEOCENTRIC_3D, datum=DatumDefinition.FIXED),
            approximate=_starting(network),
        )
        theirs = DynAdjustEngine().adjust(job(network), tmp_path)
        assert ours.degrees_of_freedom == theirs.statistics.degrees_of_freedom == 33
        for station in theirs.adjusted_stations:
            position = np.array([q.value for q in station.position.values])
            assert np.abs(_coordinates(ours, network, station.station_id) - position).max() <= PRINTED
        assert not {r.observation_id for r in theirs.observation_results} & set(ASIDE)

    def test_ignored_by_hand_is_the_same_as_set_aside_in_geocomp(self, tmp_path) -> None:
        """A baseline cluster and one direction flagged by hand read back as the
        adjustment GeoComp makes when it sets the same observations aside."""
        from geocomp.engines.dynadjust.engine import load_prepared

        engine = DynAdjustEngine()
        prepared = engine.prepare(job(written()), tmp_path / "by-hand")
        text = prepared.measurement_file.read_text(encoding="utf-8")
        text = _ignore(text, prepared.elements.index(("X4-0", "X4-1", "X4-2")))
        text = _ignore(text, prepared.elements.index(("D1-0", "D1-1", "D1-2", "D1-3", "D1-4")), direction=1)
        prepared.measurement_file.write_text(text, encoding="utf-8")
        again = load_prepared(tmp_path / "by-hand")
        by_hand = engine.parse(engine.run(again, timeout=120), again)

        aside = _set_aside(written(), ("X4-0", "X4-1", "X4-2", "D1-2"))
        in_geocomp = engine.adjust(job(aside), tmp_path / "in-geocomp")

        assert by_hand.statistics.degrees_of_freedom == in_geocomp.statistics.degrees_of_freedom == 28
        ours = {s.station_id: [q.value for q in s.position.values] for s in by_hand.adjusted_stations}
        theirs = {s.station_id: [q.value for q in s.position.values] for s in in_geocomp.adjusted_stations}
        assert ours.keys() == theirs.keys()
        for station, position in ours.items():
            np.testing.assert_allclose(position, theirs[station], rtol=0, atol=1e-6)
        # In file order: the direction sets come before the baseline cluster.
        assert by_hand.provenance.parameters["ignored_in_input"] == ["D1-2", "X4-0", "X4-1", "X4-2"]
