# SPDX-License-Identifier: GPL-2.0-or-later
"""A synthetic survey with exactly known coordinates.

RD-01 is the project's reference field book and stays the reference for
pre-processing and for the free-network adjustment. It is also three stations,
with a blunder in it and no known point -- which is the right thing to test a
face reduction and a minimum-constraint adjustment against, and the wrong thing
to test a traverse, a resection or a radiation against, because none of those
can be checked without coordinates that are known in advance.

So this module generates the readings a total station would have recorded
standing at coordinates chosen here, and every algorithm that consumes them can
be asked to recover the geometry it was generated from.

What is generated is **exact plane geometry**: no noise, no atmosphere, no
refraction bending of the line of sight, no projection. That is deliberate --
a test whose expected value is "the number the code produced last time" checks
nothing, whereas one whose expected value is the coordinate the observation was
computed from checks the whole path. Where an algorithm applies a correction
that this geometry does not contain -- curvature and refraction being the one
that matters -- the test states that term in closed form rather than hiding it
in a tolerance.

The observations do carry a stochastic model, because everything downstream
refuses to run without one (``specs/05`` section 5).
"""

from __future__ import annotations

import math

# Easting, northing, orthometric height, metres. A closed four-station traverse
# (A-B-C-D-A) with a resection station inside it, two detail points radiated
# from A, and one instrument station placed so that its two sights are exactly
# balanced.
COORDINATES: dict[str, tuple[float, float, float]] = {
    "A": (1000.000, 1000.000, 100.000),
    "B": (1150.000, 1080.000, 105.500),
    "C": (1230.000, 940.000, 98.250),
    "D": (1060.000, 880.000, 102.750),
    "R": (1120.000, 990.000, 101.000),
    "L": (1030.000, 940.000, 99.000),
    "P1": (1035.000, 1042.000, 100.900),
    "P2": (1078.000, 1013.000, 101.400),
}

#: The stations a traverse or a resection may treat as known.
CONTROL = ("A", "B", "C", "D")

#: The loop, and the station backsighted from its first point.
ROUTE = ("A", "B", "C", "D", "A")
BACKSIGHT = "D"

#: What each setup sighted, in the order it was recorded. Order matters for the
#: leap-frog mode, which reads the first sight as backward and the second as
#: forward.
SETUPS: dict[str, tuple[str, ...]] = {
    "A": ("D", "B", "P1", "P2"),
    "B": ("A", "C"),
    "C": ("B", "D"),
    "D": ("C", "A"),
    "R": ("A", "B", "C"),
    "L": ("A", "D"),
}

#: An arbitrary, distinct circle orientation per setup, radians. Distinct on
#: purpose: an algorithm that quietly assumed the circle was oriented to north
#: would pass with zeros here and fail in the field.
ORIENTATIONS: dict[str, float] = {
    "A": 0.4712389,
    "B": 2.1467550,
    "C": 4.0142573,
    "D": 5.6548668,
    "R": 1.2217305,
    "L": 3.3161256,
}

SIGMA_DIRECTION = 5.0e-6  # 1 arcsecond, radians
SIGMA_ZENITH = 5.0e-6
SIGMA_DISTANCE = 0.002  # metres
INSTRUMENT_HEIGHT = 1.500
TARGET_HEIGHT = 1.500


def azimuth(origin: str, target: str) -> float:
    """Grid azimuth from *origin* to *target*, radians, on [0, 2pi)."""
    east = COORDINATES[target][0] - COORDINATES[origin][0]
    north = COORDINATES[target][1] - COORDINATES[origin][1]
    return math.atan2(east, north) % math.tau


def horizontal_distance(origin: str, target: str) -> float:
    east = COORDINATES[target][0] - COORDINATES[origin][0]
    north = COORDINATES[target][1] - COORDINATES[origin][1]
    return math.hypot(east, north)


def height_difference(origin: str, target: str) -> float:
    return COORDINATES[target][2] - COORDINATES[origin][2]


def slope_distance(origin: str, target: str) -> float:
    return math.hypot(horizontal_distance(origin, target), height_difference(origin, target))


def zenith(origin: str, target: str) -> float:
    """Zenith angle of the straight line, radians.

    Measured between the instrument and the target *marks*: the instrument and
    target heights are equal throughout this survey, so they cancel and the
    line between the marks is the line between the points.
    """
    return math.atan2(horizontal_distance(origin, target), height_difference(origin, target))


def interior_angle(occupied: str, backsight: str, foresight: str) -> float:
    """The angle turned from *backsight* to *foresight*, radians on [0, 2pi)."""
    return (azimuth(occupied, foresight) - azimuth(occupied, backsight)) % math.tau


def start_azimuth() -> float:
    """The azimuth the traverse's first backsight direction refers to.

    ``adjust_traverse`` starts from the azimuth of the line *arriving* at the
    first station, then adds 180 degrees and the turned angle to get the first
    forward azimuth.
    """
    return azimuth(BACKSIGHT, ROUTE[0])


def perimeter() -> float:
    return sum(horizontal_distance(ROUTE[i], ROUTE[i + 1]) for i in range(len(ROUTE) - 1))


def _quantity(value: float, sigma: float, unit: str) -> dict:
    return {"value": value, "variance": sigma * sigma, "unit": unit, "mode": "RIGOROUS"}


def reductions_document(
    setups: dict[str, tuple[str, ...]] | None = None,
    *,
    sigma_direction: float = SIGMA_DIRECTION,
    sigma_zenith: float = SIGMA_ZENITH,
    sigma_distance: float = SIGMA_DISTANCE,
) -> dict:
    """The document the pre-processing algorithm writes, built from geometry.

    Every consumer in ``geocomp.algorithms.totalstation`` reads this shape, so
    generating it directly is what lets each algorithm be tested on its own
    rather than only at the end of the chain.
    """
    chosen = SETUPS if setups is None else setups
    document = {"kind": "geocomp.reductions", "version": 1, "setups": []}

    for station, targets in chosen.items():
        orientation = ORIENTATIONS[station]
        pointings = []
        for target in targets:
            distance = slope_distance(station, target)
            # The circle reading is the azimuth less the setup's orientation:
            # what the instrument displays, not where north is.
            reading = (azimuth(station, target) - orientation) % math.tau
            pointings.append(
                {
                    "target": target,
                    "horizontal": _quantity(reading, sigma_direction, "RADIAN"),
                    "zenith": _quantity(zenith(station, target), sigma_zenith, "RADIAN"),
                    "distance": _quantity(distance, sigma_distance, "METRE"),
                    "horizontal_distance": _quantity(
                        horizontal_distance(station, target), sigma_distance, "METRE"
                    ),
                    "height_difference": _quantity(
                        height_difference(station, target), sigma_distance, "METRE"
                    ),
                    "usable": True,
                }
            )
        document["setups"].append({"station": station, "pointings": pointings})

    return document


def known_points(names: tuple[str, ...] = CONTROL) -> dict[str, list[float]]:
    """The shape the resection, intersection and radiation inputs take."""
    return {name: list(COORDINATES[name]) for name in names}


def sightings_document(
    target: str, from_stations: tuple[str, ...], *, sigma_degrees: float = 5.0 / 3600.0
) -> dict:
    """Azimuths to an inaccessible point, for a forward intersection."""
    return {
        station: {
            "position": list(COORDINATES[station][:2]),
            "azimuth": math.degrees(azimuth(station, target)),
            "sigma": sigma_degrees,
        }
        for station in from_stations
    }


def curvature_and_refraction(distance: float, coefficient: float = 0.13) -> float:
    """``(1 - k) d^2 / 2R``, metres -- stated here so a test can name it.

    The synthetic sights are straight lines between marks. A trigonometric
    height computed from them and then corrected for curvature and refraction
    is high by exactly this, and a test that expects the true height difference
    plus this term is checking the correction rather than tolerating it.
    """
    earth_radius = 6371000.0
    return (1.0 - coefficient) * distance * distance / (2.0 * earth_radius)
