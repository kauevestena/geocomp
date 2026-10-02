# SPDX-License-Identifier: GPL-2.0-or-later
"""What the results panel shows, read from a solution (specs/15 section 4; phase P12b).

*A dockable panel showing the current project's solutions: run history with
status, statistics summaries, per-observation results with sorting and
filtering, and links from a table row to the corresponding map feature.* The
panel is ``gui/results_panel.py``; this is everything it says, worked out
without QGIS so it is tested without QGIS.

**The decision is the one the residual layer draws** (:func:`decision`): the
same three answers the w-test gives, plus *uncheckable*, which is not a pass,
and empty where no test was made -- an engine's result. One function, so the
table row and the map feature it links to cannot disagree about an
observation.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from geocomp.core.models import Solution
from geocomp.core.models.solution import ObservationResult

__all__ = [
    "FILTERS",
    "ObservationRow",
    "RunSummary",
    "StationRow",
    "decision",
    "matches",
    "observation_rows",
    "run_summary",
    "station_rows",
    "statistics_items",
]

#: What the observation table can be narrowed to, in the order it offers them.
FILTERS = ("all", "rejected", "uncheckable", "untested")


def decision(result: ObservationResult) -> str:
    """``"accepted"``, ``"rejected"``, ``"uncheckable"``, or empty where nothing was tested."""
    if result.is_uncheckable:
        return "uncheckable"
    if result.w_test is None:
        return ""
    return "accepted" if result.w_test.passed else "rejected"


@dataclass(frozen=True)
class RunSummary:
    """One row of the run history."""

    id: str
    created: datetime | None
    algorithm: str
    kind: str
    global_test: bool | None
    variance_factor: float | None
    degrees_of_freedom: int
    candidates: int
    uncheckable: int
    approximate: bool
    superseded: bool


def run_summary(solution: Solution) -> RunSummary:
    statistics = solution.statistics
    decisions = [decision(result) for result in solution.observation_results]
    provenance = solution.provenance
    return RunSummary(
        id=solution.id,
        created=provenance.created if provenance else None,
        algorithm=(provenance.algorithm_id or provenance.source) if provenance else "",
        kind=solution.kind.value,
        global_test=statistics.global_test.passed if statistics.global_test else None,
        variance_factor=statistics.variance_factor_aposteriori,
        degrees_of_freedom=statistics.degrees_of_freedom,
        candidates=decisions.count("rejected"),
        uncheckable=decisions.count("uncheckable"),
        approximate=solution.is_approximate,
        superseded=solution.is_superseded,
    )


def statistics_items(solution: Solution) -> list[tuple[str, Any]]:
    """The statistics summary as ``(key, value)`` pairs, in reading order.

    Keys, not labels: the panel phrases each one in the active language. A
    value the solution does not hold is ``None``, shown as a dash rather than
    left out, so a reader can see that it was not computed.
    """
    statistics = solution.statistics
    test = statistics.global_test
    summary = run_summary(solution)
    return [
        ("observations", statistics.n_observations),
        ("parameters", statistics.n_parameters),
        ("constraints", statistics.n_constraints),
        ("degrees_of_freedom", statistics.degrees_of_freedom),
        ("variance_factor_apriori", statistics.variance_factor_apriori),
        ("variance_factor_aposteriori", statistics.variance_factor_aposteriori),
        ("global_test", None if test is None else test.passed),
        ("test_statistic", None if test is None else test.statistic),
        ("critical_low", None if test is None else test.critical_low),
        ("critical_high", None if test is None else test.critical_high),
        ("confidence", None if test is None else test.confidence),
        ("candidates", summary.candidates),
        ("uncheckable", summary.uncheckable),
        ("iterations", statistics.iterations),
        ("converged", statistics.converged),
        ("max_correction", statistics.max_correction),
        ("condition_number", statistics.condition_number),
        ("uncertainty_mode", solution.uncertainty_mode.value),
    ]


@dataclass(frozen=True)
class ObservationRow:
    """One row of the per-observation table, and the key to its map feature."""

    observation_id: str
    residual: float
    standardised: float | None
    redundancy: float | None
    mdb: float | None
    external: float | None
    decision: str


def observation_rows(solution: Solution) -> list[ObservationRow]:
    return [
        ObservationRow(
            observation_id=result.observation_id,
            residual=result.residual,
            standardised=result.standardised_residual,
            redundancy=result.redundancy,
            mdb=result.minimal_detectable_bias,
            external=result.external_reliability,
            decision=decision(result),
        )
        for result in solution.observation_results
    ]


def matches(row: ObservationRow, kind: str, text: str = "") -> bool:
    """Whether *row* passes the table's filter: a decision, and a fragment of its id."""
    if text and text.casefold() not in row.observation_id.casefold():
        return False
    if kind == "rejected":
        return row.decision == "rejected"
    if kind == "uncheckable":
        return row.decision == "uncheckable"
    if kind == "untested":
        return row.decision == ""
    return True


@dataclass(frozen=True)
class StationRow:
    """One adjusted station, and the key to its map feature."""

    station_id: str
    components: tuple[str, ...]
    values: tuple[float, ...]
    std_devs: tuple[float, ...]
    positional_uncertainty: float | None
    semi_major: float | None
    semi_minor: float | None


def station_rows(solution: Solution) -> list[StationRow]:
    rows = []
    for station in solution.adjusted_stations:
        values = station.position.values
        rows.append(
            StationRow(
                station_id=station.station_id,
                components=tuple(station.position.system.component_names),
                values=tuple(quantity.value for quantity in values),
                std_devs=tuple(quantity.std_dev for quantity in values),
                positional_uncertainty=station.positional_uncertainty,
                semi_major=station.ellipse.semi_major if station.ellipse else None,
                semi_minor=station.ellipse.semi_minor if station.ellipse else None,
            )
        )
    return rows
