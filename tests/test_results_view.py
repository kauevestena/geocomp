# SPDX-License-Identifier: GPL-2.0-or-later
"""What the results panel shows, read from a solution (specs/15 section 4; phase P12b)."""

from __future__ import annotations

import dataclasses

import pytest

from geocomp.core.models.solution import ObservationResult
from geocomp.core.models.solution import TestResult as WTest
from geocomp.core.visualization.results import (
    FILTERS,
    decision,
    matches,
    observation_rows,
    run_summary,
    station_rows,
    statistics_items,
)
from tests.test_project_store import reference  # noqa: F401 -- the fixture


def _w(passed: bool) -> WTest:
    return WTest(name="w-test", statistic=1.0 if passed else 4.2, passed=passed)


#: One observation of each kind the table tells apart.
VARIED = (
    ObservationResult("passes", 0.001, 0.8, 0.5, _w(True), 0.004, 0.002),
    ObservationResult("blunder", 0.012, 4.2, 0.4, _w(False), 0.005, 0.003),
    ObservationResult("blind", 0.0, None, 0.004, None, None, None),
    ObservationResult("engine", 0.002, None, None, None, None, None),
)


@pytest.fixture
def varied(reference):  # noqa: F811 -- the imported fixture
    _project, solution, _network = reference
    return dataclasses.replace(solution, observation_results=VARIED)


class TestTheDecision:
    @pytest.mark.parametrize(
        ("observation", "expected"),
        [("passes", "accepted"), ("blunder", "rejected"), ("blind", "uncheckable"), ("engine", "")],
    )
    def test_the_four_answers(self, observation, expected):
        result = next(r for r in VARIED if r.observation_id == observation)
        assert decision(result) == expected


class TestTheRunHistory:
    def test_a_run_says_what_ran_and_whether_it_passed(self, reference):  # noqa: F811
        _project, solution, _network = reference
        summary = run_summary(solution)
        assert summary.id == "s1"
        assert summary.algorithm == "geocomp:analysis_network_adjust"
        assert summary.global_test is solution.statistics.global_test.passed
        assert summary.degrees_of_freedom == solution.statistics.degrees_of_freedom
        assert summary.created is not None

    def test_it_counts_candidates_and_the_uncheckable(self, varied):
        summary = run_summary(varied)
        assert (summary.candidates, summary.uncheckable) == (1, 1)


class TestTheStatistics:
    def test_every_quantity_in_reading_order(self, reference):  # noqa: F811
        _project, solution, _network = reference
        keys = [key for key, _value in statistics_items(solution)]
        assert keys[:6] == [
            "observations",
            "parameters",
            "constraints",
            "degrees_of_freedom",
            "variance_factor_apriori",
            "variance_factor_aposteriori",
        ]
        values = dict(statistics_items(solution))
        assert values["variance_factor_aposteriori"] == (
            solution.statistics.variance_factor_aposteriori
        )
        assert values["uncertainty_mode"] == solution.uncertainty_mode.value

    def test_what_was_not_computed_is_none_not_absent(self, varied):
        stripped = dataclasses.replace(
            varied, statistics=dataclasses.replace(varied.statistics, global_test=None)
        )
        values = dict(statistics_items(stripped))
        assert "test_statistic" in values and values["test_statistic"] is None


class TestTheObservationTable:
    def test_one_row_per_result_with_its_decision(self, varied):
        rows = observation_rows(varied)
        assert [(row.observation_id, row.decision) for row in rows] == [
            ("passes", "accepted"),
            ("blunder", "rejected"),
            ("blind", "uncheckable"),
            ("engine", ""),
        ]

    @pytest.mark.parametrize(
        ("kind", "expected"),
        [
            ("all", ["passes", "blunder", "blind", "engine"]),
            ("rejected", ["blunder"]),
            ("uncheckable", ["blind"]),
            ("untested", ["engine"]),
        ],
    )
    def test_each_filter(self, varied, kind, expected):
        assert kind in FILTERS
        rows = observation_rows(varied)
        assert [row.observation_id for row in rows if matches(row, kind)] == expected

    def test_the_text_filter_ignores_case(self, varied):
        rows = observation_rows(varied)
        assert [row.observation_id for row in rows if matches(row, "all", "BLU")] == ["blunder"]


class TestTheStationTable:
    def test_one_row_per_adjusted_station(self, reference):  # noqa: F811
        _project, solution, _network = reference
        rows = station_rows(solution)
        assert {row.station_id for row in rows} == {
            station.station_id for station in solution.adjusted_stations
        }
        assert all(len(row.values) == len(row.components) for row in rows)
