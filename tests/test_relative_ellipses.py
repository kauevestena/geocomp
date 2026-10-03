# SPDX-License-Identifier: GPL-2.0-or-later
"""Relative ellipses from the joint covariance (specs/19 criterion 3; P12c-6).

The core half: :func:`~geocomp.core.visualization.relative.relative_ellipses`
gives, for every pair an observation joins, the ellipse
:func:`~geocomp.core.statistics.ellipses.relative_ellipse` computes from the
two stations' joint covariance -- with a held station contributing nothing, and
a geocentric difference turned into the horizon. The layer that draws them is
``tests/qgis/test_result_layers.py`` (``TestTheRelativeEllipses``).
"""

from __future__ import annotations

import numpy as np
import pytest

from geocomp.core.adjustment import Frame
from geocomp.core.adjustment.least_squares import AdjustmentOptions, adjust, to_solution
from geocomp.core.models import DatumDefinition, Epoch
from geocomp.core.statistics.ellipses import error_ellipse, relative_ellipse
from geocomp.core.visualization.relative import observed_pairs, relative_ellipses
from tests.networks import trilateration


def _solution(network, frame=Frame.PLANE_2D, datum=DatumDefinition.CONSTRAINED, crs="LOCAL"):
    run = adjust(network, AdjustmentOptions(frame=frame, datum=datum))
    return to_solution(
        run, network, solution_id="s", crs=crs, epoch=Epoch.from_decimal_year(2026.0), datum=datum
    )


def test_the_pairs_are_those_the_observations_join():
    network = trilateration().network
    pairs = observed_pairs(network)
    joined = {frozenset(o.stations) for o in network.observations.values()}
    assert {frozenset(p) for p in pairs} == joined
    assert len(pairs) == len(joined), "each pair once"


@pytest.mark.dense_only
def test_each_ellipse_is_the_joint_covariances():
    network = trilateration().network
    solution = _solution(network)
    covariance = solution.parameter_covariance
    where = {label: i for i, label in enumerate(covariance.labels)}
    dof = solution.statistics.degrees_of_freedom
    found = relative_ellipses(solution, observed_pairs(network))
    assert found
    checked = 0
    for item in found:
        first = [where.get(f"{item.first}.{c}") for c in ("e", "n")]
        second = [where.get(f"{item.second}.{c}") for c in ("e", "n")]
        if None in first or None in second:
            continue  # a held station; below
        expected = relative_ellipse(covariance.matrix, first, second, confidence=0.95, degrees_of_freedom=dof)
        assert item.ellipse.semi_major == pytest.approx(expected.semi_major, rel=1e-12)
        assert item.ellipse.semi_minor == pytest.approx(expected.semi_minor, rel=1e-12)
        assert item.ellipse.orientation == pytest.approx(expected.orientation, abs=1e-12)
        checked += 1
    assert checked >= 3


@pytest.mark.dense_only
def test_a_line_to_a_held_station_is_not_drawn():
    """A held station is not an estimated one: it is in no solution's stations,
    has nowhere to be drawn from, and the line's ellipse would be the free
    station's own, which the ellipse layer draws already."""
    network = trilateration().network
    solution = _solution(network)
    estimated = {s.station_id for s in solution.adjusted_stations}
    held = set(network.stations) - estimated
    assert held, "the reference network holds a station"
    drawn = {
        frozenset((item.first, item.second)) for item in relative_ellipses(solution, observed_pairs(network))
    }
    assert drawn
    assert not any(pair & held for pair in drawn)


@pytest.mark.dense_only
def test_the_line_between_two_correlated_stations_is_better_known_than_either():
    """The reason relative ellipses exist: shared observations correlate two
    stations, and their separation is known better than either's position."""
    network = trilateration().network
    solution = _solution(network)
    by_id = {s.station_id: s for s in solution.adjusted_stations}
    smaller = [
        item
        for item in relative_ellipses(solution, observed_pairs(network))
        if item.ellipse.semi_major
        < max(by_id[item.first].ellipse.semi_major, by_id[item.second].ellipse.semi_major)
    ]
    assert smaller


def test_without_the_covariance_between_stations_there_is_nothing_to_draw():
    from dataclasses import replace

    network = trilateration().network
    solution = replace(_solution(network), parameter_covariance=None)
    assert relative_ellipses(solution, observed_pairs(network)) == []


@pytest.mark.dense_only
def test_a_geocentric_line_is_turned_into_its_horizon():
    """X, Y, Z differences, turned at the line's middle: the horizontal ellipse
    of the rotated 3x3, the same arithmetic as each station's own."""
    from geocomp.core.adjustment.geocentric import ELLIPSOID
    from geocomp.core.geodesy.cartesian import cartesian_to_geodetic, enu_rotation
    from tests.combined_network import survey

    network = survey()
    solution = _solution(network, frame=Frame.GEOCENTRIC_3D, datum=DatumDefinition.FIXED, crs="EPSG:7912")
    covariance = solution.parameter_covariance
    where = {label: i for i, label in enumerate(covariance.labels)}
    by_id = {s.station_id: s for s in solution.adjusted_stations}
    found = [
        item
        for item in relative_ellipses(solution, observed_pairs(network))
        if all(f"{s}.x" in where for s in (item.first, item.second))
    ]
    assert found
    item = found[0]
    first = [where[f"{item.first}.{c}"] for c in "xyz"]
    second = [where[f"{item.second}.{c}"] for c in "xyz"]
    m = np.asarray(covariance.matrix)
    difference = (
        m[np.ix_(first, first)]
        + m[np.ix_(second, second)]
        - m[np.ix_(first, second)]
        - m[np.ix_(second, first)]
    )
    middle = 0.5 * (
        np.array([q.value for q in by_id[item.first].position.values])
        + np.array([q.value for q in by_id[item.second].position.values])
    )
    latitude, longitude, _ = cartesian_to_geodetic(*middle, ELLIPSOID)
    rotation = enu_rotation(latitude, longitude)
    expected = error_ellipse(
        (rotation @ difference @ rotation.T)[:2, :2],
        confidence=0.95,
        degrees_of_freedom=solution.statistics.degrees_of_freedom,
    )
    assert item.ellipse.semi_major == pytest.approx(expected.semi_major, rel=1e-12)
    assert item.ellipse.semi_minor == pytest.approx(expected.semi_minor, rel=1e-12)
