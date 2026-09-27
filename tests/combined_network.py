# SPDX-License-Identifier: GPL-2.0-or-later
"""A combined GNSS and total-station survey near Curitiba, for cross-validation.

Six stations over about 3 km: three correlated GNSS baselines tie two control
marks to three other stations, and one of the rest has an ellipsoidal height; a
total station occupies four stations and observes a direction set, zenith
angles and slope distances (with instrument and target heights) to every
station it can see; one horizontal angle and one geodetic azimuth complete the
terrestrial types. Every measurement is computed
from a known truth in the geocentric model and perturbed by its own standard
deviation, with a fixed seed.

Every type has a DynAdjust counterpart (``specs/07`` section 4.2), and with
``target=0`` the two engines model every one of them identically (section 6.3),
so the in-house geocentric frame and DynAdjust solve the same problem and any
difference between them is arithmetic, not modelling.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime

import numpy as np

from geocomp.core.adjustment.geocentric import ELLIPSOID
from geocomp.core.geodesy.cartesian import cartesian_to_geodetic, enu_rotation, geodetic_to_cartesian
from geocomp.core.models import (
    BaselineFrame,
    Cluster,
    ClusterKind,
    ConstraintMode,
    ConstraintSpec,
    CoordinateSystem,
    Epoch,
    HeightType,
    Network,
    Observation,
    ObservationType,
    Position,
    Station,
)
from geocomp.core.models.observation import BASELINE_FRAME_KEY
from geocomp.core.uncertainty import Covariance, Quantity
from geocomp.core.units import Unit

LATITUDE, LONGITUDE = math.radians(-25.43), math.radians(-49.27)
#: East, north, ellipsoidal height, metres.
OFFSETS = {
    "CTB1": (0.0, 0.0, 912.0),
    "CTB2": (2900.0, 350.0, 938.0),
    "M03": (1450.0, 1650.0, 921.0),
    "M04": (650.0, 2600.0, 905.0),
    "M05": (2300.0, 2450.0, 944.0),
    "M06": (1200.0, -700.0, 918.0),
}
HELD = ("CTB1", "CTB2")
EPOCH = Epoch.from_datetime(datetime(2020, 1, 1, tzinfo=UTC), label="01.01.2020")
FRAME = "ITRF2014"

SIGMA_DISTANCE = 0.002
SIGMA_ANGLE = math.radians(1.5 / 3600.0)
SIGMA_ZENITH = math.radians(3.0 / 3600.0)
INSTRUMENT, TARGET = 1.563, 1.700
GNSS_COVARIANCE = np.array([[16e-6, 3e-6, -2e-6], [3e-6, 12e-6, 1e-6], [-2e-6, 1e-6, 36e-6]])


def _ecef(east: float, north: float, height: float) -> np.ndarray:
    radius = 6_378_137.0
    return np.array(
        geodetic_to_cartesian(
            LATITUDE + north / radius,
            LONGITUDE + east / (radius * math.cos(LATITUDE)),
            height,
            ELLIPSOID,
        )
    )


TRUTH = {name: _ecef(*offset) for name, offset in OFFSETS.items()}


def _local(origin: str, target: str, instrument: float = 0.0, target_height: float = 0.0) -> np.ndarray:
    lat_o, lon_o, _ = cartesian_to_geodetic(*TRUTH[origin], ELLIPSOID)
    lat_t, lon_t, _ = cartesian_to_geodetic(*TRUTH[target], ELLIPSOID)
    rotation = enu_rotation(lat_o, lon_o)
    delta = (TRUTH[target] + target_height * enu_rotation(lat_t, lon_t)[2]) - (
        TRUTH[origin] + instrument * rotation[2]
    )
    return rotation @ delta


def _cartesian(values, *, sigma: float | None = None) -> Position:
    make = (
        (lambda v: Quantity.exact(float(v), Unit.METRE))
        if sigma is None
        else (lambda v: Quantity.from_std_dev(float(v), sigma, Unit.METRE))
    )
    return Position(
        values=tuple(make(v) for v in values),
        system=CoordinateSystem.CARTESIAN,
        crs=FRAME,
        epoch=EPOCH,
        height_type=HeightType.ELLIPSOIDAL,
    )


#: Which stations the total station occupies, and what it sees from each.
SETUPS = {
    "CTB1": ("M06", "M03", "M04"),
    "M03": ("CTB1", "M04", "M05", "CTB2", "M06"),
    "M05": ("M03", "M04", "CTB2"),
    "M06": ("CTB2", "M03", "CTB1"),
}


def correlated_normal(rng: np.random.Generator, covariance: np.ndarray) -> np.ndarray:
    """One draw from N(0, *covariance*), the same on every platform.

    Not ``rng.multivariate_normal``: it factors the covariance by SVD, whose
    signs and ordering depend on the LAPACK underneath, so macOS's Accelerate
    and Linux's OpenBLAS draw different noise from one seed -- and a fixture
    written from the survey on one no longer matches it on the other. The
    Cholesky factor is unique, so this is the same draw everywhere.
    """
    return np.linalg.cholesky(covariance) @ rng.standard_normal(len(covariance))


def survey(*, seed: int = 20260926, perturb: float = 0.5, target: float = TARGET) -> Network:
    """The network, its measurements drawn once from their stated precision.

    *target* is the reflector's height above each station. For a slope
    distance DynAdjust carries it along the **instrument's** vertical rather
    than the target's own (``specs/07`` section 6.3), which moves a 2.9 km
    sight's end by ``t d / R``: 0.8 mm at 1.7 m. The cross-validation therefore
    uses ``target=0``, where the two models coincide; the default keeps a
    realistic reflector for every other test.
    """
    rng = np.random.default_rng(seed)
    network = Network(id="curitiba-combined", crs=FRAME, epoch=EPOCH)
    for name, truth in TRUTH.items():
        constraint = (
            ConstraintSpec(
                mode=ConstraintMode.FIXED,
                components=frozenset({"x", "y", "z"}),
                position=_cartesian(truth),
            )
            if name in HELD
            else ConstraintSpec()
        )
        start = truth + rng.uniform(-perturb, perturb, 3)
        network.add_station(
            Station(id=name, approx_position=_cartesian(start, sigma=1.0), constraint=constraint)
        )

    def add(identifier, kind, stations, values, sigma, unit, **extra):
        network.add_observation(
            Observation(
                id=identifier,
                type=kind,
                stations=stations,
                values=tuple(
                    Quantity.from_std_dev(float(v) + rng.normal(0.0, sigma), sigma, unit) for v in values
                ),
                **extra,
            )
        )

    heights = {
        "instrument_height": Quantity.exact(INSTRUMENT, Unit.METRE),
        "target_height": Quantity.exact(target, Unit.METRE),
    }
    reflector = target
    for setup, targets in SETUPS.items():
        members = []
        for target in targets:
            sight = _local(setup, target, INSTRUMENT, reflector)
            add(f"s-{setup}-{target}", ObservationType.SLOPE_DISTANCE, (setup, target),
                [np.linalg.norm(sight)], SIGMA_DISTANCE, Unit.METRE, **heights)
            add(f"z-{setup}-{target}", ObservationType.ZENITH_ANGLE, (setup, target),
                [math.atan2(math.hypot(sight[0], sight[1]), sight[2])], SIGMA_ZENITH, Unit.RADIAN,
                **heights)
            plain = _local(setup, target)
            identifier = f"d-{setup}-{target}"
            # The circle's zero is arbitrary; 0.7 rad off north here.
            add(identifier, ObservationType.DIRECTION, (setup, target),
                [math.remainder(math.atan2(plain[0], plain[1]) - 0.7, math.tau) % math.tau],
                SIGMA_ANGLE, Unit.RADIAN, setup_id=f"set-{setup}", cluster_id=f"set-{setup}")
            members.append(network.observations[identifier])
        network.add_cluster(
            Cluster(
                id=f"set-{setup}",
                kind=ClusterKind.DIRECTION_SET,
                observation_ids=tuple(m.id for m in members),
                covariance=Covariance(
                    matrix=np.diag([SIGMA_ANGLE**2] * len(members)),
                    labels=tuple(m.id for m in members),
                    units=(Unit.RADIAN,) * len(members),
                ),
            )
        )

    back, fore = _local("M04", "M03"), _local("M04", "M05")
    add("a-M04", ObservationType.HORIZONTAL_ANGLE, ("M04", "M03", "M05"),
        [(math.atan2(fore[0], fore[1]) - math.atan2(back[0], back[1])) % math.tau],
        SIGMA_ANGLE, Unit.RADIAN)
    sight = _local("M05", "M04")
    add("b-M05-M04", ObservationType.AZIMUTH, ("M05", "M04"),
        [math.atan2(sight[0], sight[1]) % math.tau], math.radians(5.0 / 3600.0), Unit.RADIAN)

    baselines = []
    for base, rover in (("CTB1", "M05"), ("CTB2", "M04"), ("CTB1", "M06")):
        noise = correlated_normal(rng, GNSS_COVARIANCE)
        identifier = f"g-{base}-{rover}"
        network.add_observation(
            Observation(
                id=identifier,
                type=ObservationType.GNSS_BASELINE,
                stations=(base, rover),
                values=tuple(
                    Quantity(float(v + n), float(GNSS_COVARIANCE[k, k]), Unit.METRE)
                    for k, (v, n) in enumerate(zip(TRUTH[rover] - TRUTH[base], noise, strict=True))
                ),
                cluster_id="gnss",
                meta={BASELINE_FRAME_KEY: BaselineFrame.ECEF.value},
            )
        )
        baselines.append(identifier)
    size = 3 * len(baselines)
    matrix = np.zeros((size, size))
    for index in range(len(baselines)):
        matrix[3 * index : 3 * index + 3, 3 * index : 3 * index + 3] = GNSS_COVARIANCE
    network.add_cluster(
        Cluster(
            id="gnss",
            kind=ClusterKind.GNSS_BASELINE,
            observation_ids=tuple(baselines),
            covariance=Covariance(
                matrix=matrix,
                labels=tuple(f"m{i}.{c}" for i in range(len(baselines)) for c in ("x", "y", "z")),
                units=(Unit.METRE,) * size,
            ),
        )
    )
    height = cartesian_to_geodetic(*TRUTH["M03"], ELLIPSOID)[2]
    add("r-M03", ObservationType.ELLIPSOIDAL_HEIGHT, ("M03",), [height], 0.015, Unit.METRE)
    return network
