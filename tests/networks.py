# SPDX-License-Identifier: GPL-2.0-or-later
"""Reference networks RD-03 and RD-09 (specs/20 section 3).

**What these are, stated plainly.** As with RD-02 in phase P1, these are *not*
transcriptions from Ghilani or Gemael -- those books are not available to the
author of this module, and inventing a citation would be worse than having none.
They are networks built from the geodetic configurations GeoComp must handle,
with a **known truth**, validated against closed-form results where one exists
and against the fundamental identities of least squares everywhere else.

That is a real standard, not a weaker substitute. Several of the checks these
datasets support -- that redundancy numbers sum to the degrees of freedom, that
a free and a constrained solution differ only by a datum transformation, that
design simulation reproduces the adjustment's covariance -- would catch errors
that matching a printed answer would not, because they hold for *every* network
rather than one.

Transcribing the published worked examples remains outstanding and is recorded
in ``specs/20-testing-and-validation.md``.

* **RD-03** -- networks with a known truth: 1D levelling, 2D trilateration,
  2D triangulateration, 3D.
* **RD-09** -- the same networks with a blunder of known size injected at a
  known place, which is the only way to test detection against ground truth
  rather than against another computation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from geocomp.core.models import (
    ConstraintMode,
    ConstraintSpec,
    CoordinateSystem,
    HeightType,
    Network,
    Observation,
    ObservationType,
    Position,
    Station,
)
from geocomp.core.uncertainty import Quantity
from geocomp.core.units import Unit

METRE, RADIAN = Unit.METRE, Unit.RADIAN

#: Fixed so every reference network is reproducible (NFR-007).
SEED = 20260826


@dataclass
class ReferenceNetwork:
    """A network with a known truth, and the blunder injected into it if any."""

    network: Network
    truth: dict[str, dict[str, float]]
    sigma: dict[str, float] = field(default_factory=dict)
    blunder_observation: str | None = None
    blunder_size: float = 0.0

    def error_at(self, station_id: str, component: str, parameters, layout) -> float:
        """Signed error of an adjusted parameter against the truth."""
        column = layout.station_columns(station_id)[component]
        return float(parameters[column]) - self.truth[station_id][component]

    def max_coordinate_error(self, parameters, layout) -> float:
        errors = [
            abs(self.error_at(station_id, component, parameters, layout))
            for station_id in layout.station_ids()
            for component in layout.station_columns(station_id)
        ]
        return max(errors) if errors else 0.0


def _position(values: tuple[float, ...], *, exact: bool = False, sigma: float = 0.5) -> Position:
    padded = tuple(values) + (0.0,) * (3 - len(values))
    quantities = tuple(
        Quantity.exact(v, METRE) if exact else Quantity.from_std_dev(v, sigma, METRE)
        for v in padded
    )
    return Position(
        values=quantities,  # type: ignore[arg-type]
        system=CoordinateSystem.PROJECTED,
        crs="EPSG:31982",
        height_type=HeightType.ORTHOMETRIC,
    )


def _fixed(values: tuple[float, ...], components: set[str]) -> ConstraintSpec:
    return ConstraintSpec(
        mode=ConstraintMode.FIXED,
        components=frozenset(components),
        position=_position(values, exact=True),
    )


# -- RD-03.1: 1D levelling loop ------------------------------------------


def levelling_loop(*, blunder: float = 0.0, blunder_on: str | None = None) -> ReferenceNetwork:
    """Four benchmarks, one fixed, six height differences.

    The simplest network with real redundancy, and the one whose answer can be
    checked entirely by hand: with equal weights a loop misclosure distributes
    equally around the loop.
    """
    truth = {"A": 10.000, "B": 12.500, "C": 15.000, "D": 11.250}
    sigma = 0.002
    rng = np.random.default_rng(SEED)

    network = Network(id="rd03-levelling", crs="EPSG:31982")
    network.add_station(
        Station(
            id="A",
            approx_position=_position((0.0, 0.0, truth["A"])),
            constraint=_fixed((0.0, 0.0, truth["A"]), {"up"}),
        )
    )
    for station_id in ("B", "C", "D"):
        network.add_station(
            Station(id=station_id, approx_position=_position((0.0, 0.0, truth[station_id] + 0.05)))
        )

    lines = [("A", "B"), ("B", "C"), ("C", "D"), ("D", "A"), ("A", "C"), ("B", "D")]
    for index, (origin, target) in enumerate(lines):
        value = truth[target] - truth[origin] + float(rng.normal(0.0, sigma))
        observation_id = f"L{index}"
        if observation_id == blunder_on:
            value += blunder
        network.add_observation(
            Observation(
                id=observation_id,
                type=ObservationType.HEIGHT_DIFFERENCE,
                stations=(origin, target),
                values=(Quantity.from_std_dev(value, sigma, METRE),),
            )
        )

    return ReferenceNetwork(
        network=network,
        truth={k: {"h": v} for k, v in truth.items()},
        sigma={"height_difference": sigma},
        blunder_observation=blunder_on,
        blunder_size=blunder,
    )


# -- RD-03.2: 2D trilateration -------------------------------------------


def trilateration(*, blunder: float = 0.0, blunder_on: str | None = None) -> ReferenceNetwork:
    """Five stations, ten distances, one azimuth for orientation.

    Distances fix scale but not orientation, so the azimuth is what removes the
    remaining rotation. It is deliberately the *only* observation that does, so
    the network contains an uncheckable observation -- which is itself worth
    testing, because a network can pass every statistical test while containing
    one.
    """
    truth = {
        "A": (0.0, 0.0),
        "B": (1200.0, 0.0),
        "C": (1200.0, 900.0),
        "D": (0.0, 900.0),
        "E": (600.0, 450.0),
    }
    sigma = 0.004
    sigma_azimuth = 1.0e-5
    rng = np.random.default_rng(SEED)

    network = Network(id="rd03-trilateration", crs="EPSG:31982")
    network.add_station(
        Station(
            id="A",
            approx_position=_position(truth["A"]),
            constraint=_fixed(truth["A"], {"easting", "northing"}),
        )
    )
    for station_id in ("B", "C", "D", "E"):
        easting, northing = truth[station_id]
        network.add_station(
            Station(id=station_id, approx_position=_position((easting + 0.3, northing - 0.2)))
        )

    pairs = [
        ("A", "B"), ("B", "C"), ("C", "D"), ("D", "A"), ("A", "C"),
        ("B", "D"), ("A", "E"), ("B", "E"), ("C", "E"), ("D", "E"),
    ]
    for index, (origin, target) in enumerate(pairs):
        value = math.dist(truth[origin], truth[target]) + float(rng.normal(0.0, sigma))
        observation_id = f"d{index}"
        if observation_id == blunder_on:
            value += blunder
        network.add_observation(
            Observation(
                id=observation_id,
                type=ObservationType.HORIZONTAL_DISTANCE,
                stations=(origin, target),
                values=(Quantity.from_std_dev(value, sigma, METRE),),
            )
        )

    azimuth = math.atan2(truth["B"][0] - truth["A"][0], truth["B"][1] - truth["A"][1])
    network.add_observation(
        Observation(
            id="az",
            type=ObservationType.AZIMUTH,
            stations=("A", "B"),
            values=(
                Quantity.from_std_dev(
                    azimuth + float(rng.normal(0.0, sigma_azimuth)), sigma_azimuth, RADIAN
                ),
            ),
        )
    )

    return ReferenceNetwork(
        network=network,
        truth={k: {"e": v[0], "n": v[1]} for k, v in truth.items()},
        sigma={"horizontal_distance": sigma, "azimuth": sigma_azimuth},
        blunder_observation=blunder_on,
        blunder_size=blunder,
    )


# -- RD-03.3: 2D triangulateration ---------------------------------------


def triangulateration(*, blunder: float = 0.0, blunder_on: str | None = None) -> ReferenceNetwork:
    """Angles and distances together -- the mixed case the proposal names.

    Exercises two things the pure-distance network does not: an observation type
    with three stations, and a weight matrix mixing radians and metres, where a
    unit error would be immediately visible in the variance factor.
    """
    truth = {"A": (0.0, 0.0), "B": (800.0, 0.0), "C": (400.0, 700.0), "D": (1200.0, 700.0)}
    sigma_distance = 0.005
    sigma_angle = 2.0e-5
    rng = np.random.default_rng(SEED + 1)

    network = Network(id="rd03-triangulateration", crs="EPSG:31982")
    network.add_station(
        Station(
            id="A",
            approx_position=_position(truth["A"]),
            constraint=_fixed(truth["A"], {"easting", "northing"}),
        )
    )
    for station_id in ("B", "C", "D"):
        easting, northing = truth[station_id]
        network.add_station(
            Station(id=station_id, approx_position=_position((easting - 0.25, northing + 0.35)))
        )

    for index, (origin, target) in enumerate([("A", "B"), ("B", "C"), ("C", "A"), ("B", "D"), ("C", "D")]):
        value = math.dist(truth[origin], truth[target]) + float(rng.normal(0.0, sigma_distance))
        observation_id = f"s{index}"
        if observation_id == blunder_on:
            value += blunder
        network.add_observation(
            Observation(
                id=observation_id,
                type=ObservationType.HORIZONTAL_DISTANCE,
                stations=(origin, target),
                values=(Quantity.from_std_dev(value, sigma_distance, METRE),),
            )
        )

    def bearing(origin: str, target: str) -> float:
        return math.atan2(
            truth[target][0] - truth[origin][0], truth[target][1] - truth[origin][1]
        )

    angles = [("A", "B", "C"), ("B", "C", "A"), ("C", "A", "B"), ("B", "A", "D"), ("C", "B", "D")]
    for index, (at, backsight, foresight) in enumerate(angles):
        value = bearing(at, foresight) - bearing(at, backsight)
        value = (value + math.pi) % (2 * math.pi) - math.pi
        value += float(rng.normal(0.0, sigma_angle))
        observation_id = f"a{index}"
        if observation_id == blunder_on:
            value += blunder
        network.add_observation(
            Observation(
                id=observation_id,
                type=ObservationType.HORIZONTAL_ANGLE,
                stations=(at, backsight, foresight),
                values=(Quantity.from_std_dev(value, sigma_angle, RADIAN),),
            )
        )

    azimuth = bearing("A", "B")
    network.add_observation(
        Observation(
            id="az",
            type=ObservationType.AZIMUTH,
            stations=("A", "B"),
            values=(
                Quantity.from_std_dev(
                    azimuth + float(rng.normal(0.0, sigma_angle)), sigma_angle, RADIAN
                ),
            ),
        )
    )

    return ReferenceNetwork(
        network=network,
        truth={k: {"e": v[0], "n": v[1]} for k, v in truth.items()},
        sigma={"horizontal_distance": sigma_distance, "angle": sigma_angle},
        blunder_observation=blunder_on,
        blunder_size=blunder,
    )


# -- RD-03.4: free network for datum testing -----------------------------


def free_trilateration() -> ReferenceNetwork:
    """The trilateration network with **no** station fixed.

    Used to test inner constraints, and to check that a free and a constrained
    solution of the same data agree on everything a datum choice cannot change:
    residuals, the variance factor, and the relative geometry.
    """
    reference = trilateration()
    network = Network(
        id="rd03-free",
        crs="EPSG:31982",
        stations={
            station_id: Station(id=station_id, approx_position=station.approx_position)
            for station_id, station in reference.network.stations.items()
        },
        observations=dict(reference.network.observations),
        clusters=dict(reference.network.clusters),
    )
    return ReferenceNetwork(
        network=network, truth=reference.truth, sigma=reference.sigma
    )
