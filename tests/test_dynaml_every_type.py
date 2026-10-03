# SPDX-License-Identifier: GPL-2.0-or-later
"""Every mapped observation type, written as DynaML, valid and imported cleanly (specs/07 criterion 1).

``specs/07`` §4.2 maps eighteen DynAdjust codes to GeoComp observation types
(``E`` is read as an ellipsoid distance but never written, and ``M`` has no
counterpart). Before P12c-6 the writer had been checked against ``dnaimport``
on three networks that between them used seven codes, and against the schema
never. Here one network uses all eighteen:

* both files it writes validate against DynAdjust's own schema,
  ``tests/data/dynadjust/DynaML.xsd`` (Apache-2.0, ``THIRD_PARTY.md``) --
  wherever ``lxml`` is installed;
* ``dnaimport`` takes in every station and every measurement row, and warns
  about nothing -- tier 4, where DynAdjust is.

The values are plausible rather than consistent: an import checks form, not
geometry, and a network built to adjust would need every type's geometry to
agree.
"""

from __future__ import annotations

import math
import re
import subprocess
from pathlib import Path

import numpy as np
import pytest

from geocomp.core.geodesy.cartesian import cartesian_to_geodetic
from geocomp.core.geodesy.ellipsoid import ellipsoid_by_name
from geocomp.core.models import (
    Cluster,
    ClusterKind,
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
from geocomp.core.models.observation import OBSERVATION_TYPES
from geocomp.core.uncertainty import Covariance, Quantity
from geocomp.core.units import Unit
from geocomp.engines.dynadjust.dynaml import write_measurement_file, write_station_file
from tests.conftest import REPO_ROOT, requires_dynadjust

SCHEMA = REPO_ROOT / "tests" / "data" / "dynadjust" / "DynaML.xsd"
FRAME, EPOCH = "GDA2020", "01.01.2020"

#: Every code a GeoComp observation is written as.
WRITTEN_CODES = {"A", "B", "C", "D", "G", "H", "I", "J", "K", "L", "P", "Q", "R", "S", "V", "X", "Y", "Z"}

TRUTH = {
    "BASE": (-4052051.767, 4212836.215, -2545106.026),
    "PT01": (-4052185.112, 4212742.009, -2545021.587),
    "PT02": (-4051990.336, 4212999.478, -2544897.155),
    "PT03": (-4052260.904, 4212950.233, -2544858.712),
}
SEC = math.radians(1.0 / 3600.0)


def _cartesian(xyz, *, exact: bool = False) -> Position:
    make = (
        (lambda v: Quantity.exact(v, Unit.METRE))
        if exact
        else (lambda v: Quantity.from_std_dev(v, 0.5, Unit.METRE))
    )
    return Position(
        values=tuple(make(v) for v in xyz),
        system=CoordinateSystem.CARTESIAN,
        crs="EPSG:7842",
        height_type=HeightType.ELLIPSOIDAL,
    )


def _geodetic(station: str) -> tuple[float, float, float]:
    return cartesian_to_geodetic(*TRUTH[station], ellipsoid_by_name("GRS80"))


def _angle(value: float, sigma: float = 2.0 * SEC) -> tuple[Quantity, ...]:
    return (Quantity.from_std_dev(value, sigma, Unit.RADIAN),)


def _metres(value: float, sigma: float = 0.003) -> tuple[Quantity, ...]:
    return (Quantity.from_std_dev(value, sigma, Unit.METRE),)


def _gnss_cluster(network, cluster_id, kind, observations):
    for observation in observations:
        network.add_observation(observation)
    size = 3 * len(observations)
    matrix = np.eye(size) * 1.0e-4 + (np.ones((size, size)) - np.eye(size)) * 1.0e-5
    components = OBSERVATION_TYPES[observations[0].type].components
    network.add_cluster(
        Cluster(
            id=cluster_id,
            kind=kind,
            observation_ids=tuple(o.id for o in observations),
            covariance=Covariance(
                matrix=matrix,
                labels=tuple(f"{o.id}.{c}" for o in observations for c in components),
                units=(Unit.METRE,) * size,
            ),
        )
    )


def every_type() -> Network:
    """One network using every DynAdjust code GeoComp writes."""
    network = Network(id="every-type", crs="EPSG:7842")
    network.add_station(
        Station(
            id="BASE",
            approx_position=_cartesian(TRUTH["BASE"]),
            constraint=ConstraintSpec(
                mode=ConstraintMode.FIXED,
                components=frozenset({"x", "y", "z"}),
                position=_cartesian(TRUTH["BASE"], exact=True),
            ),
        )
    )
    for name in ("PT01", "PT02", "PT03"):
        network.add_station(Station(id=name, approx_position=_cartesian(TRUTH[name])))

    def delta(a, b):
        return tuple(Quantity.from_std_dev(TRUTH[b][k] - TRUTH[a][k], 0.01, Unit.METRE) for k in range(3))

    def observation(oid, kind, stations, values, **extra):
        return Observation(id=oid, type=kind, stations=stations, values=values, **extra)

    # X: a cluster of two baselines; G: a cluster of one; Y: a point cluster.
    _gnss_cluster(
        network,
        "cX",
        ClusterKind.GNSS_BASELINE,
        [
            observation(
                "x1", ObservationType.GNSS_BASELINE, ("BASE", "PT01"), delta("BASE", "PT01"), cluster_id="cX"
            ),
            observation(
                "x2", ObservationType.GNSS_BASELINE, ("BASE", "PT02"), delta("BASE", "PT02"), cluster_id="cX"
            ),
        ],
    )
    _gnss_cluster(
        network,
        "cG",
        ClusterKind.GNSS_BASELINE,
        [
            observation(
                "g1", ObservationType.GNSS_BASELINE, ("PT01", "PT02"), delta("PT01", "PT02"), cluster_id="cG"
            )
        ],
    )
    _gnss_cluster(
        network,
        "cY",
        ClusterKind.GNSS_POINT,
        [
            observation(
                "y1",
                ObservationType.GNSS_POINT,
                ("PT03",),
                tuple(Quantity.from_std_dev(v, 0.01, Unit.METRE) for v in TRUTH["PT03"]),
                cluster_id="cY",
            )
        ],
    )

    # D: a direction set of three from PT01.
    directions = [
        observation(
            f"d{n}",
            ObservationType.DIRECTION,
            ("PT01", target),
            _angle(value),
            cluster_id="cD",
            setup_id="PT01-setup",
        )
        for n, (target, value) in enumerate((("BASE", 0.0), ("PT02", 1.1), ("PT03", 2.3)))
    ]
    for item in directions:
        network.add_observation(item)
    network.add_cluster(
        Cluster(
            id="cD",
            kind=ClusterKind.DIRECTION_SET,
            observation_ids=tuple(o.id for o in directions),
            covariance=Covariance(
                matrix=np.eye(3) * (2.0 * SEC) ** 2,
                labels=tuple(f"{o.id}.angle" for o in directions),
                units=(Unit.RADIAN,) * 3,
            ),
        )
    )

    latitude, longitude, height = _geodetic("PT03")
    singles = [
        ("p1", ObservationType.GEODETIC_LATITUDE, ("PT03",), _angle(latitude, 0.01 * SEC)),
        ("q1", ObservationType.GEODETIC_LONGITUDE, ("PT03",), _angle(longitude, 0.01 * SEC)),
        ("r1", ObservationType.ELLIPSOIDAL_HEIGHT, ("PT03",), _metres(height, 0.02)),
        ("h1", ObservationType.ORTHOMETRIC_HEIGHT, ("PT02",), _metres(_geodetic("PT02")[2] - 20.0, 0.02)),
        ("i1", ObservationType.ASTRONOMIC_LATITUDE, ("PT02",), _angle(_geodetic("PT02")[0], 0.5 * SEC)),
        ("j1", ObservationType.ASTRONOMIC_LONGITUDE, ("PT02",), _angle(_geodetic("PT02")[1], 0.5 * SEC)),
        (
            "c1",
            ObservationType.ELLIPSOID_DISTANCE,
            ("BASE", "PT03"),
            _metres(math.dist(TRUTH["BASE"], TRUTH["PT03"])),
        ),
        (
            "s1",
            ObservationType.SLOPE_DISTANCE,
            ("BASE", "PT02"),
            _metres(math.dist(TRUTH["BASE"], TRUTH["PT02"])),
        ),
        ("v1", ObservationType.ZENITH_ANGLE, ("PT01", "PT03"), _angle(math.radians(89.5))),
        ("z1", ObservationType.VERTICAL_ANGLE, ("PT02", "PT03"), _angle(math.radians(0.5))),
        ("a1", ObservationType.HORIZONTAL_ANGLE, ("PT01", "BASE", "PT03"), _angle(math.radians(73.2))),
        ("b1", ObservationType.AZIMUTH, ("BASE", "PT02"), _angle(math.radians(41.7))),
        ("k1", ObservationType.ASTRONOMIC_AZIMUTH, ("PT01", "BASE"), _angle(math.radians(212.4))),
        ("l1", ObservationType.HEIGHT_DIFFERENCE, ("PT01", "PT02"), _metres(4.217, 0.002)),
    ]
    for oid, kind, stations, values in singles:
        network.add_observation(observation(oid, kind, stations, values))
    network.require_valid()
    return network


@pytest.fixture
def written(tmp_path: Path):
    network = every_type()
    station_file, measurement_file = tmp_path / "every-stn.xml", tmp_path / "every-msr.xml"
    write_station_file(network, station_file, frame=FRAME, epoch=EPOCH)
    document = write_measurement_file(network, measurement_file, frame=FRAME, epoch=EPOCH)
    return network, station_file, measurement_file, document


def test_the_network_writes_every_code_and_skips_nothing(written):
    _network, _stations, _measurements, document = written
    assert not document.skipped
    assert set(document.counts) == WRITTEN_CODES


def test_every_file_validates_against_dynadjusts_own_schema(written):
    etree = pytest.importorskip("lxml.etree")
    schema = etree.XMLSchema(etree.parse(str(SCHEMA)))
    _network, station_file, measurement_file, _document = written
    for path in (station_file, measurement_file):
        document = etree.parse(str(path))
        assert schema.validate(document), f"{path.name}: {[str(e) for e in schema.error_log][:5]}"


@requires_dynadjust
def test_dnaimport_takes_in_every_row_and_warns_about_nothing(written, tmp_path):
    from geocomp.engines.dynadjust.engine import imported_counts, printed_rows

    network, station_file, measurement_file, _document = written
    run = subprocess.run(
        ["dnaimport", "-n", "every", station_file.name, measurement_file.name],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    output = run.stdout + run.stderr
    assert run.returncode == 0, output
    counts = imported_counts(run.stdout)
    assert counts["stations"] == len(network.stations)
    assert counts["measurements"] == len(printed_rows(network))
    warnings = [
        line for line in output.splitlines() if re.search(r"\bwarning\b|\berror\b", line, re.IGNORECASE)
    ]
    assert not warnings, "\n".join(warnings)
