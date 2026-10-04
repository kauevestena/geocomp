# SPDX-License-Identifier: GPL-2.0-or-later
"""Measured distances carried to the grid (FR-405, specs/09 section 2.6).

Until P12c-14 nothing applied the reduction: a network on a projected CRS was
adjusted with ground distances taken as grid distances, 400 to 1000 ppm wrong on
UTM. The last class here is the point of the rest: a network observed on the
ground at the edge of a UTM zone, held to two grid control points, fails its
global test as measured and fits its truth to a tenth of a millimetre once
reduced.

The scale factor is GeoComp's own, from :mod:`geocomp.core.geodesy.projection`;
``tests/qgis/test_grid_reduction.py`` checks that the one QGIS supplies to the
algorithm is the same number.
"""

from __future__ import annotations

import math
from typing import ClassVar

import numpy as np
import pytest

from geocomp.core.adjustment import Frame
from geocomp.core.adjustment.least_squares import AdjustmentOptions, adjust
from geocomp.core.errors import ValidationError
from geocomp.core.geodesy import inverse_transverse_mercator, point_scale_factor, utm_parameters
from geocomp.core.models import (
    Cluster,
    ClusterKind,
    ConstraintMode,
    ConstraintSpec,
    CoordinateSystem,
    DatumDefinition,
    HeightType,
    Network,
    Observation,
    ObservationType,
    Position,
    Station,
)
from geocomp.core.techniques.total_station.grid import GRID_REDUCTION, reduce_distances_to_grid
from geocomp.core.techniques.total_station.reductions import DEFAULT_EARTH_RADIUS
from geocomp.core.uncertainty import Covariance, Quantity
from geocomp.core.units import Unit

R = DEFAULT_EARTH_RADIUS
ZERO = Quantity.exact(0.0, Unit.METRE)
UTM_22S = utm_parameters(22, southern_hemisphere=True)


def utm_k(easting: float, northing: float) -> float:
    """GeoComp's own point scale factor for SIRGAS 2000 / UTM zone 22S."""
    latitude, longitude = inverse_transverse_mercator(easting, northing, UTM_22S)
    return point_scale_factor(latitude, longitude, UTM_22S)


def _position(easting, northing, height, *, kind=HeightType.ORTHOMETRIC, sigma=0.0):
    def quantity(value):
        return Quantity.exact(value, Unit.METRE) if sigma == 0.0 else Quantity.from_std_dev(
            value, sigma, Unit.METRE
        )

    return Position(
        values=(quantity(easting), quantity(northing), quantity(height)),
        system=CoordinateSystem.PROJECTED,
        crs="EPSG:31982",
        height_type=kind,
    )


def _two_stations(*, kind=HeightType.ORTHOMETRIC, distance_type=ObservationType.HORIZONTAL_DISTANCE):
    network = Network(id="pair", crs="EPSG:31982")
    network.add_station(Station(id="A", approx_position=_position(200_000.0, 7_400_000.0, 800.0, kind=kind)))
    network.add_station(Station(id="B", approx_position=_position(201_000.0, 7_400_000.0, 820.0, kind=kind)))
    network.add_observation(
        Observation(
            id="d",
            type=distance_type,
            stations=("A", "B"),
            values=(Quantity.from_std_dev(1000.0, 0.002, Unit.METRE),),
        )
    )
    return network


def constant(k):
    return lambda _easting, _northing: k


class TestOneDistance:
    def test_a_ground_distance_goes_to_the_ellipsoid_then_to_the_grid(self):
        network = _two_stations()
        reduced, (record,) = reduce_distances_to_grid(
            network, scale_factor=constant(0.9996), undulation=Quantity.exact(-10.0, Unit.METRE)
        )
        h = 810.0 - 10.0  # the mean orthometric height plus N
        expected = 1000.0 * R / (R + h) * 0.9996
        (value,) = reduced.observations["d"].values
        assert value.value == pytest.approx(expected, abs=1e-9)
        assert record.factor == pytest.approx(R / (R + h) * 0.9996, rel=1e-12)
        assert record.parts_per_million == pytest.approx((R / (R + h) * 0.9996 - 1.0) * 1e6)
        assert record.height.value == pytest.approx(h)

    def test_an_ellipsoid_distance_is_only_scaled(self):
        network = _two_stations(distance_type=ObservationType.ELLIPSOID_DISTANCE)
        reduced, (record,) = reduce_distances_to_grid(network, scale_factor=constant(1.0004))
        assert reduced.observations["d"].values[0].value == pytest.approx(1000.4, abs=1e-9)
        assert record.height is None

    def test_an_ellipsoidal_height_needs_no_undulation(self):
        network = _two_stations(kind=HeightType.ELLIPSOIDAL)
        _, (record,) = reduce_distances_to_grid(network, scale_factor=constant(1.0))
        assert record.height.value == pytest.approx(810.0)

    def test_the_uncertainty_is_the_measurements_scaled_and_the_heights_added(self):
        """FR-205: only as certain as the height it was reduced with."""
        network = Network(id="pair", crs="EPSG:31982")
        for name, easting in (("A", 200_000.0), ("B", 201_000.0)):
            network.add_station(
                Station(id=name, approx_position=_position(easting, 7_400_000.0, 800.0, sigma=5.0))
            )
        network.add_observation(
            Observation(
                id="d",
                type=ObservationType.HORIZONTAL_DISTANCE,
                stations=("A", "B"),
                values=(Quantity.from_std_dev(1000.0, 0.002, Unit.METRE),),
            )
        )
        _, (record,) = reduce_distances_to_grid(
            network, scale_factor=constant(0.9996), undulation=Quantity.exact(0.0, Unit.METRE)
        )
        h_sigma = 5.0 / math.sqrt(2.0)  # the mean of two independent heights
        factor = R / (R + 800.0)
        d_dh = -1000.0 * R / (R + 800.0) ** 2
        expected = 0.9996**2 * ((factor * 0.002) ** 2 + (d_dh * h_sigma) ** 2)
        assert record.grid.variance == pytest.approx(expected, rel=1e-9)

    def test_the_record_travels_with_the_observation(self):
        network = _two_stations()
        reduced, (record,) = reduce_distances_to_grid(
            network, scale_factor=constant(0.9996), undulation=Quantity.exact(0.0, Unit.METRE)
        )
        meta = reduced.observations["d"].meta[GRID_REDUCTION]
        assert meta["measured"]["value"] == 1000.0
        assert meta["factor"] == pytest.approx(record.factor)
        assert meta["scale_factor"] == 0.9996
        # A document written and read back keeps it.
        again = Observation.from_dict(reduced.observations["d"].to_dict())
        assert again.meta[GRID_REDUCTION]["factor"] == pytest.approx(record.factor)


class TestWhatIsLeftAlone:
    def test_the_input_network_is_not_changed(self):
        network = _two_stations()
        reduce_distances_to_grid(network, scale_factor=constant(0.9996), undulation=ZERO)
        assert network.observations["d"].values[0].value == 1000.0
        assert GRID_REDUCTION not in network.observations["d"].meta

    def test_reducing_twice_reduces_once(self):
        network = _two_stations()
        once, _ = reduce_distances_to_grid(
            network, scale_factor=constant(0.9996), undulation=Quantity.exact(0.0, Unit.METRE)
        )
        twice, records = reduce_distances_to_grid(
            once, scale_factor=constant(0.9996), undulation=Quantity.exact(0.0, Unit.METRE)
        )
        assert records == ()
        assert twice.observations["d"] == once.observations["d"]

    def test_other_observations_are_the_same_objects(self):
        network = _two_stations()
        azimuth = Observation(
            id="az",
            type=ObservationType.AZIMUTH,
            stations=("A", "B"),
            values=(Quantity.from_std_dev(1.5, 1e-5, Unit.RADIAN),),
        )
        network.add_observation(azimuth)
        reduced, _ = reduce_distances_to_grid(
            network, scale_factor=constant(0.9996), undulation=Quantity.exact(0.0, Unit.METRE)
        )
        assert reduced.observations["az"] is azimuth


class TestWhatIsRefused:
    def test_an_orthometric_height_without_an_undulation(self):
        with pytest.raises(ValidationError) as refused:
            reduce_distances_to_grid(_two_stations(), scale_factor=constant(1.0))
        assert refused.value.code == "validation.grid_reduction_without_undulation"
        assert refused.value.context["received"] == ["A", "B"]

    def test_a_height_of_no_stated_kind(self):
        with pytest.raises(ValidationError) as refused:
            reduce_distances_to_grid(_two_stations(kind=HeightType.NONE), scale_factor=constant(1.0))
        assert refused.value.code == "validation.grid_reduction_without_height"

    def test_a_station_with_no_position(self):
        network = _two_stations()
        network.stations["B"] = Station(id="B")
        with pytest.raises(ValidationError) as refused:
            reduce_distances_to_grid(network, scale_factor=constant(1.0), undulation=ZERO)
        assert refused.value.code == "validation.grid_reduction_without_position"
        assert refused.value.context["received"] == ["B"]

    def test_a_distance_in_a_correlated_cluster(self):
        network = _two_stations()
        network.observations["d"] = Observation(
            id="d",
            type=ObservationType.HORIZONTAL_DISTANCE,
            stations=("A", "B"),
            values=(Quantity.from_std_dev(1000.0, 0.002, Unit.METRE),),
            cluster_id="c",
        )
        network.add_cluster(
            Cluster(
                id="c",
                kind=ClusterKind.DIRECTION_SET,
                observation_ids=("d",),
                covariance=Covariance(
                    matrix=np.array([[0.002**2]]), labels=("d",), units=(Unit.METRE,)
                ),
            )
        )
        with pytest.raises(ValidationError) as refused:
            reduce_distances_to_grid(network, scale_factor=constant(1.0), undulation=ZERO)
        assert refused.value.code == "validation.grid_reduction_of_clustered_distance"


class TestTheLinesScaleFactor:
    """Simpson's rule against the mean of *k* along the line, integrated finely.

    Agreement to 0.001 ppm, which is the resolution of the scale factor itself:
    :func:`point_scale_factor` differentiates the projection numerically, and its
    own noise is of that order.
    """

    @pytest.mark.parametrize("easting", [500_000.0, 330_000.0, 170_000.0])
    def test_a_ten_kilometre_line_anywhere_in_the_zone(self, easting):
        start, end = (easting, 7_400_000.0), (easting + 8_000.0, 7_406_000.0)
        steps = 2000
        mean = (
            sum(
                utm_k(
                    start[0] + (end[0] - start[0]) * (i + 0.5) / steps,
                    start[1] + (end[1] - start[1]) * (i + 0.5) / steps,
                )
                for i in range(steps)
            )
            / steps
        )

        network = Network(id="line", crs="EPSG:31982")
        for name, (e, n) in (("A", start), ("B", end)):
            network.add_station(
                Station(id=name, approx_position=_position(e, n, 0.0, kind=HeightType.ELLIPSOIDAL))
            )
        network.add_observation(
            Observation(
                id="d",
                type=ObservationType.ELLIPSOID_DISTANCE,
                stations=("A", "B"),
                values=(Quantity.from_std_dev(10_000.0, 0.005, Unit.METRE),),
            )
        )
        _, (record,) = reduce_distances_to_grid(network, scale_factor=utm_k)
        assert record.scale_factor == pytest.approx(mean, abs=1e-9)


class TestANetworkAtTheEdgeOfAZone:
    """Five stations 300 km west of the central meridian, 800 m up, observed on the
    ground and held to two grid control points.

    The combined factor there is about +580 ppm: k is 1.0007 and the height takes
    125 ppm off it. As measured, the distances do not fit the control; reduced,
    they fit it as well as the noise allows.
    """

    TRUTH: ClassVar[dict[str, tuple[float, float]]] = {
        "A": (200_000.0, 7_400_000.0),
        "B": (203_000.0, 7_400_000.0),
        "C": (203_000.0, 7_402_000.0),
        "D": (200_000.0, 7_402_000.0),
        "E": (201_500.0, 7_401_000.0),
    }
    HEIGHT = 800.0
    N = -5.0
    SIGMA = 0.002
    PAIRS = (
        ("A", "B"), ("B", "C"), ("C", "D"), ("D", "A"), ("A", "C"),
        ("B", "D"), ("A", "E"), ("B", "E"), ("C", "E"), ("D", "E"),
    )

    @classmethod
    def network(cls) -> Network:
        network = Network(id="edge", crs="EPSG:31982")
        for name, (easting, northing) in cls.TRUTH.items():
            held = name in ("A", "C")
            network.add_station(
                Station(
                    id=name,
                    approx_position=_position(
                        easting + (0.0 if held else 0.4),
                        northing - (0.0 if held else 0.3),
                        cls.HEIGHT,
                        sigma=1.0,
                    ),
                    constraint=ConstraintSpec(
                        mode=ConstraintMode.FIXED,
                        components=frozenset({"easting", "northing"}),
                        position=_position(easting, northing, cls.HEIGHT),
                    )
                    if held
                    else ConstraintSpec(),
                )
            )
        h = cls.HEIGHT + cls.N
        for index, (origin, target) in enumerate(cls.PAIRS):
            (e1, n1), (e2, n2) = cls.TRUTH[origin], cls.TRUTH[target]
            k = (utm_k(e1, n1) + 4 * utm_k((e1 + e2) / 2, (n1 + n2) / 2) + utm_k(e2, n2)) / 6
            ground = math.dist((e1, n1), (e2, n2)) / k / (R / (R + h))
            network.add_observation(
                Observation(
                    id=f"d{index}",
                    type=ObservationType.HORIZONTAL_DISTANCE,
                    stations=(origin, target),
                    values=(Quantity.from_std_dev(ground, cls.SIGMA, Unit.METRE),),
                )
            )
        return network

    @staticmethod
    def _adjust(network):
        return adjust(network, AdjustmentOptions(frame=Frame.PLANE_2D, datum=DatumDefinition.CONSTRAINED))

    def _worst(self, run) -> float:
        worst = 0.0
        for name, (easting, northing) in self.TRUTH.items():
            if name in ("A", "C"):
                continue
            columns = run.layout.station_columns(name)
            worst = max(
                worst,
                abs(float(run.parameters[columns["e"]]) - easting),
                abs(float(run.parameters[columns["n"]]) - northing),
            )
        return worst

    def test_as_measured_the_distances_do_not_fit_the_grid(self):
        """Noise-free, so all of the misfit is the missing reduction."""
        run = self._adjust(self.network())
        assert run.variance_factor_aposteriori > 1000.0
        assert self._worst(run) > 0.1

    def test_reduced_they_fit_it_exactly(self):
        reduced, records = reduce_distances_to_grid(
            self.network(), scale_factor=utm_k, undulation=Quantity.exact(self.N, Unit.METRE)
        )
        assert len(records) == len(self.PAIRS)
        assert all(560.0 < record.parts_per_million < 600.0 for record in records)
        run = self._adjust(reduced)
        assert run.variance_factor_aposteriori < 1e-4
        assert self._worst(run) < 1e-4
