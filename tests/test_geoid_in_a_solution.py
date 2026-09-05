# SPDX-License-Identifier: GPL-2.0-or-later
"""A geoid model from a file, through an adjustment, into a solution (FR-804).

``specs/17-persistence-and-interoperability.md`` acceptance criterion 8, whole:
*a geoid model imports, is applied, records its identity in the solution, and
contributes its uncertainty.* The clauses are tested separately elsewhere --
:mod:`tests.test_geoid_import` for the reading, :mod:`tests.test_geoid` for the
interpolation and its uncertainty, :mod:`tests.test_levelling` for the
conversion inside a network -- and here they are tested joined up, because a
chain of four correct links can still fail to be a chain.

The scenario is the one FR-802 exists for: a levelling network holding one
benchmark whose height came from GNSS and is therefore ellipsoidal, alongside
benchmarks from the national levelling network, which are orthometric. Without a
model that is refused; with one it adjusts, and the solution says which model
made it possible.
"""

from __future__ import annotations

import math
import struct
from pathlib import Path

import pytest

import tests.reference_levelling as rd
from geocomp.core.adjustment import Frame, approximate_values
from geocomp.core.adjustment.least_squares import (
    AdjustmentOptions,
    adjust,
    to_observation_results,
    to_solution,
)
from geocomp.core.errors import ValidationError
from geocomp.core.models import DatumDefinition, HeightType
from geocomp.core.models.epoch import Epoch
from geocomp.core.techniques.levelling import Benchmark, build_network, reduce_line
from geocomp.core.uncertainty import Quantity
from geocomp.core.units import Unit
from geocomp.io.geoid import read_geoid

METRE = Unit.METRE

#: A gently sloping undulation over southern Brazil, in metres. Not constant:
#: a constant would pass even if the interpolation ignored position entirely.
SOUTH, WEST, STEP = -26.0, -51.0, 1.0
UNDULATION = [
    [3.00, 3.20, 3.40],
    [3.60, 3.80, 4.00],
    [4.20, 4.40, 4.60],
]


def _model_file(tmp_path: Path) -> Path:
    """A GTX file, written from the format's layout rather than by the reader."""
    path = tmp_path / "MAPGEO-TEST.gtx"
    payload = struct.pack(">4d2i", SOUTH, WEST, STEP, STEP, 3, 3)
    for row in UNDULATION:
        payload += struct.pack(">3f", *row)
    path.write_bytes(payload)
    return path


def _benchmarks(*, ellipsoidal: bool, latitude: float, longitude: float):
    """BM1 orthometric and held; BM2 from GNSS, so ellipsoidal, and weighted.

    BM2's ellipsoidal height is its true orthometric height plus the undulation
    at its position, so a correct conversion recovers the orthometric value
    exactly and an incorrect one is out by metres.
    """
    orthometric = 103.75
    if not ellipsoidal:
        return [
            Benchmark("BM1", Quantity.exact(100.0, METRE)),
            Benchmark("BM2", Quantity.from_std_dev(orthometric, 0.015, METRE), fixed=False),
        ]
    undulation = 3.00 + 0.60 * (latitude - math.radians(SOUTH)) / math.radians(STEP)
    undulation += 0.20 * (longitude - math.radians(WEST)) / math.radians(STEP)
    return [
        Benchmark("BM1", Quantity.exact(100.0, METRE)),
        Benchmark(
            "BM2",
            Quantity.from_std_dev(orthometric + undulation, 0.015, METRE),
            height_type=HeightType.ELLIPSOIDAL,
            fixed=False,
            latitude=latitude,
            longitude=longitude,
        ),
    ]


def _solve(result, *, geoid_model: str | None):
    start = approximate_values(result.network, Frame.HEIGHT_1D)
    run = adjust(
        result.network,
        AdjustmentOptions(frame=Frame.HEIGHT_1D, datum=DatumDefinition.CONSTRAINED),
        approximate=start.values,
    )
    return to_solution(
        run,
        result.network,
        solution_id="geoid-case",
        crs="LOCAL",
        epoch=Epoch.from_decimal_year(2026.0),
        datum=DatumDefinition.CONSTRAINED,
        height_type=result.height_type,
        geoid_model=geoid_model,
        observation_results=to_observation_results(run),
    )


@pytest.fixture
def reductions():
    books, _truth = rd.loop(noise=0.0003)
    return [reduce_line(book.line, rd.profile()) for book in books]


def test_the_mixture_is_refused_without_a_model(reductions) -> None:
    """The state of affairs before this work: correct, and unusable."""
    with pytest.raises(ValidationError) as excinfo:
        build_network(
            reductions,
            _benchmarks(
                ellipsoidal=True,
                latitude=math.radians(-25.4),
                longitude=math.radians(-50.3),
            ),
        )
    assert excinfo.value.code == "validation.mixed_height_types"


def test_the_whole_chain_from_file_to_solution(reductions, tmp_path: Path) -> None:
    """Import, apply, record, propagate -- criterion 8 end to end."""
    latitude, longitude = math.radians(-25.4), math.radians(-50.3)
    geoid = read_geoid(_model_file(tmp_path), sigma=0.04, version="2015")
    assert geoid.id == "MAPGEO-TEST"

    result = build_network(
        reductions,
        _benchmarks(ellipsoidal=True, latitude=latitude, longitude=longitude),
        geoid=geoid,
    )
    solution = _solve(result, geoid_model=result.meta["geoid_model"])

    # Recorded, on the solution's positions, where a report and a multi-epoch
    # comparison will both find it.
    assert result.meta["geoid_model"] == "MAPGEO-TEST"
    assert {station.position.geoid_model for station in solution.adjusted_stations} == {
        "MAPGEO-TEST"
    }
    assert {station.position.height_type for station in solution.adjusted_stations} == {
        HeightType.ORTHOMETRIC
    }


def test_the_converted_network_agrees_with_the_orthometric_one(reductions, tmp_path: Path) -> None:
    """The conversion is right, not merely present.

    The same network is solved twice: once with BM2 given as the orthometric
    height it really has, and once with BM2 given as that height plus the
    undulation, declared ellipsoidal, and converted back through the model. If
    the interpolation, the sign of ``H = h - N`` or the row order were wrong,
    the two solutions would differ by metres.
    """
    latitude, longitude = math.radians(-25.4), math.radians(-50.3)
    geoid = read_geoid(_model_file(tmp_path), sigma=0.04)

    direct = _solve(
        build_network(reductions, _benchmarks(ellipsoidal=False, latitude=0.0, longitude=0.0)),
        geoid_model=None,
    )
    converted = _solve(
        build_network(
            reductions,
            _benchmarks(ellipsoidal=True, latitude=latitude, longitude=longitude),
            geoid=geoid,
        ),
        geoid_model="MAPGEO-TEST",
    )

    for station in direct.adjusted_stations:
        theirs = converted.station(station.station_id).position.height.value
        assert theirs == pytest.approx(station.position.height.value, abs=1.0e-6)


def test_the_geoid_uncertainty_reaches_the_adjusted_heights(reductions, tmp_path: Path) -> None:
    """FR-204: the model's 40 mm is not lost between the benchmark and the answer.

    The converted network's heights must be *less* certain than the directly
    orthometric one's, because a 40 mm model uncertainty entered the weighted
    constraint on BM2. A conversion that dropped it would look better and be
    wrong -- which is the failure mode worth a test.
    """
    latitude, longitude = math.radians(-25.4), math.radians(-50.3)
    geoid = read_geoid(_model_file(tmp_path), sigma=0.04)

    direct = _solve(
        build_network(reductions, _benchmarks(ellipsoidal=False, latitude=0.0, longitude=0.0)),
        geoid_model=None,
    )
    converted = _solve(
        build_network(
            reductions,
            _benchmarks(ellipsoidal=True, latitude=latitude, longitude=longitude),
            geoid=geoid,
        ),
        geoid_model="MAPGEO-TEST",
    )

    looser = 0
    for station in direct.adjusted_stations:
        theirs = converted.station(station.station_id).position.height.std_dev
        assert theirs >= station.position.height.std_dev - 1.0e-12
        if theirs > station.position.height.std_dev + 1.0e-9:
            looser += 1
    assert looser, "the geoid's uncertainty vanished somewhere between the file and the answer"
