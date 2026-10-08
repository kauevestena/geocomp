# SPDX-License-Identifier: GPL-2.0-or-later
"""RD-08's synthetic half: a monitored structure, measured at several epochs.

``specs/20`` names RD-08 as *a published deformation example, plus synthetic
data with injected motion*, and ``specs/22`` §5.3 is right that the synthetic
half is the only source of exact truth. This is it, built the way a survey is:

* four **reference** pillars around a structure and five **object** points on
  it, in UTM 22S;
* every epoch measured anew -- all 36 distances, 1 mm each, drawn from their
  stated precision -- and **adjusted by the core as a free network** (inner
  constraints), each epoch from its own starting coordinates, so the two
  epochs' datums differ by the few centimetres of their approximations. That
  is exactly the situation the S-transformation onto the reference block
  exists for, and a test that fed the analysis two identical datums would not
  exercise it;
* motion **injected into the truth** of the epoch it belongs to, at a known
  station, by a known vector.
"""

from __future__ import annotations

from collections.abc import Mapping
from itertools import combinations

import numpy as np

from geocomp.core.adjustment.least_squares import AdjustmentOptions, adjust, to_solution
from geocomp.core.adjustment.parameters import Frame
from geocomp.core.models import (
    CoordinateSystem,
    DatumDefinition,
    Epoch,
    HeightType,
    Network,
    Observation,
    ObservationType,
    Position,
    Solution,
    Station,
)
from geocomp.core.uncertainty import Quantity
from geocomp.core.units import Unit

CRS = "EPSG:31982"
ORIGIN = np.array([675_000.0, 7_185_000.0])
REFERENCE = ("R1", "R2", "R3", "R4")
OBJECTS = ("O1", "O2", "O3", "O4", "O5")
#: Local metres from ORIGIN: pillars at the corners, points on the structure.
LAYOUT = {
    "R1": (0.0, 0.0),
    "R2": (1200.0, 0.0),
    "R3": (1200.0, 900.0),
    "R4": (0.0, 900.0),
    "O1": (500.0, 350.0),
    "O2": (700.0, 350.0),
    "O3": (500.0, 550.0),
    "O4": (700.0, 550.0),
    "O5": (600.0, 450.0),
}
SIGMA = 0.001


def truth(moves: Mapping[str, tuple[float, float]] | None = None) -> dict[str, np.ndarray]:
    """Every station's true easting and northing, with *moves* added."""
    moves = moves or {}
    return {s: ORIGIN + np.array(xy) + np.array(moves.get(s, (0.0, 0.0))) for s, xy in LAYOUT.items()}


def _position(e: float, n: float, sigma: float) -> Position:
    return Position(
        values=(
            Quantity.from_std_dev(e, sigma, Unit.METRE),
            Quantity.from_std_dev(n, sigma, Unit.METRE),
            Quantity.exact(0.0, Unit.METRE),
        ),
        system=CoordinateSystem.PROJECTED,
        crs=CRS,
        height_type=HeightType.NONE,
    )


def epoch_network(
    year: float,
    *,
    moves: Mapping[str, tuple[float, float]] | None = None,
    seed: int = 1,
    start_error: float = 0.03,
) -> Network:
    """One epoch as measured, before adjustment: approximate positions and the 36 distances.

    The network states its epoch, so a solution adjusted from it carries that
    epoch rather than an assumed one -- which the comparison would refuse.
    """
    rng = np.random.default_rng(seed)
    points = truth(moves)
    network = Network(id=f"dam-{year}", crs=CRS, epoch=Epoch.from_decimal_year(year))
    for station, xy in points.items():
        start = xy + rng.uniform(-start_error, start_error, 2)
        network.add_station(Station(id=station, approx_position=_position(*start, sigma=1.0)))
    for a, b in combinations(LAYOUT, 2):
        distance = float(np.linalg.norm(points[b] - points[a]))
        network.add_observation(
            Observation(
                id=f"d-{a}-{b}",
                type=ObservationType.HORIZONTAL_DISTANCE,
                stations=(a, b),
                values=(Quantity.from_std_dev(distance + rng.normal(0.0, SIGMA), SIGMA, Unit.METRE),),
            )
        )
    return network


def epoch(
    year: float,
    *,
    moves: Mapping[str, tuple[float, float]] | None = None,
    seed: int = 1,
    start_error: float = 0.03,
) -> Solution:
    """One epoch: measured, adjusted as a free network, as a Solution."""
    network = epoch_network(year, moves=moves, seed=seed, start_error=start_error)
    options = AdjustmentOptions(frame=Frame.PLANE_2D, datum=DatumDefinition.INNER_CONSTRAINT)
    run = adjust(network, options)
    return to_solution(
        run,
        network,
        solution_id=network.id,
        crs=CRS,
        epoch=Epoch.from_decimal_year(year),
        datum=DatumDefinition.INNER_CONSTRAINT,
    )


#: The shipped monitoring tutorial (P13-3): two epochs, the second after O2
#: moved 8 mm east and 6 mm south. The same seeds and motion the tier-3 tests use.
TUTORIAL_MOTION = {"O2": (0.008, -0.006)}
TUTORIAL_EPOCHS: dict[str, dict] = {
    "epoch-2025.json": {"year": 2025.0, "seed": 1},
    "epoch-2026.json": {"year": 2026.0, "seed": 2, "moves": TUTORIAL_MOTION},
}
#: The alert threshold the tutorial ships, in metres, on the object points.
TUTORIAL_THRESHOLD = 0.005


def tutorial_networks() -> dict[str, Network]:
    """The tutorial's two network documents, by file name, as measured and not yet adjusted."""
    return {
        name: epoch_network(spec["year"], moves=spec.get("moves"), seed=spec["seed"])
        for name, spec in TUTORIAL_EPOCHS.items()
    }


def tutorial_thresholds() -> str:
    """The tutorial's ``thresholds.csv``: one magnitude limit on the five object points."""
    limit = f"{TUTORIAL_THRESHOLD:g}"
    return f"kind,limit,stations,group\nmagnitude,{limit},{' '.join(OBJECTS)},structure\n"
