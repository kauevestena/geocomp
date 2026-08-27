# SPDX-License-Identifier: GPL-2.0-or-later
"""The interactive design loop (FR-272), without a canvas.

``specs/06`` section 8: a design is edited -- stations added, moved and removed,
observations drawn between them -- and re-evaluated after every change. The
canvas is where that happens; this is what happens.

The behaviour that matters most here is what the session does when the design
is **not** evaluable, which is most of the time while one is being built. An
interactive loop that raised on each intermediate state would be unusable, so
"cannot be evaluated" has to arrive in the same shape as "evaluated and poor",
with a message a user can act on.
"""

from __future__ import annotations

import math

import pytest

from geocomp.core.errors import GeoCompError
from geocomp.core.models import DatumDefinition, ObservationType, StationType
from geocomp.core.preanalysis.session import DesignSession, default_sigma_for

DISTANCE = ObservationType.HORIZONTAL_DISTANCE
DIRECTION = ObservationType.DIRECTION


def _quadrilateral() -> DesignSession:
    """Four stations, six distances: redundant, and evaluable."""
    session = DesignSession(crs="EPSG:31982")
    for name, east, north in (
        ("A", 1000.0, 1000.0),
        ("B", 1150.0, 1080.0),
        ("C", 1230.0, 940.0),
        ("D", 1060.0, 880.0),
    ):
        session.add_station(name, east, north)
    for first, second in (
        ("A", "B"),
        ("B", "C"),
        ("C", "D"),
        ("D", "A"),
        ("A", "C"),
        ("B", "D"),
    ):
        session.add_observation(DISTANCE, (first, second))
    return session


class TestADesignBeingBuilt:
    """The states a design passes through before it can be evaluated at all."""

    def test_an_empty_design_says_what_to_do_rather_than_raising(self):
        state = DesignSession().evaluate()
        assert not state.is_evaluable
        assert state.blocking
        assert "add one" in state.findings[0].message

    def test_stations_without_observations_say_what_to_do(self):
        session = DesignSession(crs="EPSG:31982")
        session.add_station("A", 0.0, 0.0)
        session.add_station("B", 100.0, 0.0)
        state = session.evaluate()
        assert not state.is_evaluable
        assert state.findings[0].code == "design_without_observations"
        assert "Connect two stations" in state.findings[0].message

    def test_a_design_that_cannot_be_solved_reports_instead_of_throwing(self):
        """Two stations and one distance leave the geometry undetermined. The
        message has to reach the user, not the log."""
        session = DesignSession(crs="EPSG:31982")
        session.add_station("A", 0.0, 0.0)
        session.add_station("B", 100.0, 0.0)
        session.add_observation(DISTANCE, ("A", "B"))
        state = session.evaluate()
        assert isinstance(state.findings, tuple)
        assert state.blocking or not state.is_evaluable or state.report is not None

    def test_a_complete_design_evaluates(self):
        state = _quadrilateral().evaluate()
        assert state.is_evaluable
        assert state.report.degrees_of_freedom > 0
        assert len(state.report.stations) == 4

    def test_planned_stations_are_marked_planned(self):
        """A design must not produce stations indistinguishable from surveyed
        ones, or a plan can be mistaken for a result."""
        session = _quadrilateral()
        assert all(
            station.station_type is StationType.PLANNED
            for station in session.network.stations.values()
        )


class TestEditingChangesTheAnswer:
    def test_moving_a_station_changes_its_expected_precision(self):
        """The whole loop in one assertion: drag a station, and the design it
        is part of is a different design."""
        session = _quadrilateral()
        before = session.evaluate().report.worst_station().positional_uncertainty
        session.move_station("D", 1059.0, 300.0)
        after = session.evaluate().report.worst_station().positional_uncertainty
        assert after != pytest.approx(before)

    def test_moving_a_station_keeps_its_height(self):
        session = DesignSession(crs="EPSG:31982")
        session.add_station("A", 0.0, 0.0, 123.0)
        session.move_station("A", 50.0, 50.0)
        assert session.network.stations["A"].approx_position.values[2].value == 123.0

    def test_adding_an_observation_adds_redundancy(self):
        session = _quadrilateral()
        before = session.evaluate().report.degrees_of_freedom
        session.add_observation(DIRECTION, ("A", "C"))
        assert session.evaluate().report.degrees_of_freedom > before

    def test_removing_a_station_removes_the_observations_that_touched_it(self):
        """Leaving them behind gives a network referring to a station that does
        not exist, which fails deep in the adjustment with a message about a
        missing parameter rather than about the click that caused it."""
        session = _quadrilateral()
        orphaned = session.remove_station("D")
        assert len(orphaned) == 3
        assert "D" not in session.network.stations
        assert all(
            "D" not in observation.stations
            for observation in session.network.observations.values()
        )
        assert session.evaluate().is_evaluable

    def test_removing_a_station_drops_it_from_the_datum(self):
        """A datum held by a station that no longer exists is a constraint on
        nothing, and the adjustment would refuse for a reason that looks
        unrelated to the deletion."""
        session = _quadrilateral()
        session.set_datum(DatumDefinition.FIXED, ("A", "D"))
        session.remove_station("D")
        assert session.datum_stations == ("A",)


class TestWhatItRefuses:
    def test_two_stations_cannot_share_a_name(self):
        session = _quadrilateral()
        with pytest.raises(GeoCompError):
            session.add_station("A", 0.0, 0.0)

    def test_a_station_needs_a_name(self):
        with pytest.raises(GeoCompError):
            DesignSession().add_station("   ", 0.0, 0.0)

    def test_an_observation_to_a_station_that_does_not_exist_is_refused(self):
        session = _quadrilateral()
        with pytest.raises(GeoCompError):
            session.add_observation(DISTANCE, ("A", "Z"))

    def test_moving_or_removing_an_unknown_station_is_refused(self):
        session = _quadrilateral()
        with pytest.raises(GeoCompError):
            session.move_station("Z", 0.0, 0.0)
        with pytest.raises(GeoCompError):
            session.remove_station("Z")

    def test_a_type_with_no_assumed_precision_refuses_rather_than_guessing(self):
        """``specs/05`` section 5: GeoComp does not invent a sigma. A design
        built on an invented one states a precision nobody chose."""
        with pytest.raises(GeoCompError):
            default_sigma_for(ObservationType.GNSS_BASELINE)

    def test_a_refused_edit_leaves_no_undo_point_behind(self):
        """Otherwise undo would step through edits that never happened."""
        session = _quadrilateral()
        depth = len(session._undo)
        with pytest.raises(GeoCompError):
            session.add_station("A", 0.0, 0.0)
        assert len(session._undo) == depth


class TestUndo:
    """Editing on a canvas without undo is punishing: a misplaced click moves a
    station and there is no way back."""

    def test_an_added_station_can_be_undone(self):
        session = _quadrilateral()
        session.add_station("E", 900.0, 900.0)
        assert session.undo()
        assert "E" not in session.network.stations

    def test_a_removed_station_comes_back_with_its_observations(self):
        session = _quadrilateral()
        before = dict(session.network.observations)
        session.remove_station("D")
        assert session.undo()
        assert "D" in session.network.stations
        assert set(session.network.observations) == set(before)

    def test_a_move_can_be_undone(self):
        session = _quadrilateral()
        original = session.network.stations["D"].approx_position.values[0].value
        session.move_station("D", 1.0, 2.0)
        session.undo()
        assert session.network.stations["D"].approx_position.values[0].value == original

    def test_redo_replays_what_undo_took_back(self):
        session = _quadrilateral()
        session.add_station("E", 900.0, 900.0)
        session.undo()
        assert session.redo()
        assert "E" in session.network.stations

    def test_a_new_edit_discards_the_redo_branch(self):
        """Keeping it would let a user redo their way into a state the current
        one never came from."""
        session = _quadrilateral()
        session.add_station("E", 900.0, 900.0)
        session.undo()
        session.add_station("F", 800.0, 800.0)
        assert not session.can_redo
        assert not session.redo()

    def test_undo_on_an_untouched_session_does_nothing_and_says_so(self):
        session = DesignSession()
        assert not session.can_undo
        assert not session.undo()


class TestTheDesignQuestions:
    def test_a_design_with_no_redundancy_is_warned_about(self):
        """A triangle of three distances determines itself exactly. It can be
        computed and nothing in it can be checked."""
        session = DesignSession(crs="EPSG:31982")
        for name, east, north in (("A", 0.0, 0.0), ("B", 100.0, 0.0), ("C", 50.0, 90.0)):
            session.add_station(name, east, north)
        for first, second in (("A", "B"), ("B", "C"), ("C", "A")):
            session.add_observation(DISTANCE, (first, second))
        state = session.evaluate()
        assert state.is_evaluable
        assert state.report.degrees_of_freedom == 0
        codes = {finding.code for finding in state.findings}
        assert "design_without_redundancy" in codes
        assert "planned_observation_uncheckable" in codes

    def test_a_tolerance_is_judged_rather_than_reported(self):
        """The design question is 'will this do', and answering it with a
        number leaves the user to do the comparison."""
        session = _quadrilateral()
        reachable = session.evaluate().report.worst_station().positional_uncertainty

        session.tolerance = reachable * 2.0
        assert not any(
            finding.code == "design_misses_tolerance" for finding in session.evaluate().findings
        )

        session.tolerance = reachable / 2.0
        finding = next(
            f for f in session.evaluate().findings if f.code == "design_misses_tolerance"
        )
        assert finding.value == pytest.approx(reachable)
        assert finding.threshold == pytest.approx(reachable / 2.0)

    def test_a_better_geometry_gives_a_better_expected_precision(self):
        """Non-vacuousness for the whole simulation: the numbers have to move
        the way geometry says they should."""
        session = _quadrilateral()
        spread = session.evaluate().report.worst_station().positional_uncertainty
        session.move_station("C", 1155.0, 1081.0)
        crowded = session.evaluate().report.worst_station().positional_uncertainty
        assert crowded > spread

    def test_the_assumed_precisions_are_the_ones_it_used(self):
        session = _quadrilateral()
        observation = next(iter(session.network.observations.values()))
        assert observation.values[0].std_dev == pytest.approx(default_sigma_for(DISTANCE))

    def test_a_planned_observation_carries_no_value(self):
        """A design uses geometry and assumed precision, never a measurement --
        which is what lets a network be judged before anyone goes to the
        field."""
        session = _quadrilateral()
        assert all(
            observation.values[0].value == 0.0
            for observation in session.network.observations.values()
        )

    def test_angular_observations_are_planned_in_radians(self):
        session = _quadrilateral()
        identifier = session.add_observation(DIRECTION, ("A", "B"))
        from geocomp.core.units import Unit

        assert session.network.observations[identifier].values[0].unit is Unit.RADIAN
        assert math.isfinite(session.network.observations[identifier].values[0].std_dev)


class TestPlannedDirectionSets:
    """Directions from one setup share an unknown orientation, so they are one
    cluster and the model refuses to hold them otherwise (FR-104). A design
    that split them would omit the orientation unknown and evaluate a network
    nobody could observe."""

    @pytest.fixture
    def session(self) -> DesignSession:
        session = _quadrilateral()
        session.add_observation(DIRECTION, ("A", "B"))
        session.add_observation(DIRECTION, ("A", "C"))
        session.add_observation(DIRECTION, ("B", "A"))
        return session

    def test_directions_from_one_station_are_one_set(self, session):
        assert set(session.network.clusters) == {"directions-A", "directions-B"}
        assert len(session.network.clusters["directions-A"].observation_ids) == 2

    def test_the_cluster_covariance_matches_its_members(self, session):
        cluster = session.network.clusters["directions-A"]
        assert cluster.covariance.size == len(cluster.observation_ids)
        assert cluster.covariance.labels == cluster.observation_ids

    def test_removing_a_direction_rebuilds_the_set(self, session):
        """The covariance ordering *is* the member order, so a stale matrix
        would be applied to the wrong observations."""
        removed = session.network.clusters["directions-A"].observation_ids[0]
        session.remove_observation(removed)
        cluster = session.network.clusters["directions-A"]
        assert removed not in cluster.observation_ids
        assert cluster.covariance.size == 1

    def test_removing_the_last_direction_drops_the_set(self, session):
        for identifier in list(session.network.clusters["directions-B"].observation_ids):
            session.remove_observation(identifier)
        assert "directions-B" not in session.network.clusters

    def test_removing_a_station_cleans_up_the_sets_it_was_in(self, session):
        session.remove_station("A")
        assert "directions-A" not in session.network.clusters
        assert all(
            observation.cluster_id in session.network.clusters
            for observation in session.network.observations.values()
            if observation.cluster_id is not None
        )
        assert session.network.validate() == []

    def test_undo_restores_the_clusters_too(self, session):
        """Restoring observations without their clusters would leave the model
        holding directions whose cluster id points at nothing."""
        before = {
            name: cluster.observation_ids for name, cluster in session.network.clusters.items()
        }
        session.remove_station("A")
        session.undo()
        assert {
            name: cluster.observation_ids for name, cluster in session.network.clusters.items()
        } == before

    def test_a_design_with_directions_still_evaluates(self, session):
        state = session.evaluate()
        assert state.is_evaluable
        assert state.report.degrees_of_freedom > 0
