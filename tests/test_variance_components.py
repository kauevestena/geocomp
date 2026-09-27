# SPDX-License-Identifier: GPL-2.0-or-later
"""Variance component estimation (``specs/13`` section 4, criterion 3).

A synthetic survey is the only kind whose truth is known exactly, and for this
criterion the truth is the point: the observations are drawn with one set of
standard deviations and declared with another, and the estimator has to find
the ratio. The survey is a total-station and GNSS network of the size a
project is, adjusted in a local 3D frame.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from geocomp.core.adjustment import Frame
from geocomp.core.adjustment.least_squares import AdjustmentOptions, adjust
from geocomp.core.adjustment.variance_components import (
    estimate_variance_components,
    scale_groups,
)
from geocomp.core.errors import ComputationError, ValidationError
from geocomp.core.models import (
    BaselineFrame,
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
from geocomp.core.models.observation import BASELINE_FRAME_KEY
from geocomp.core.uncertainty import Covariance, Quantity
from geocomp.core.units import Unit

SIGMA_DISTANCE = 0.003
SIGMA_ZENITH = math.radians(3.0 / 3600.0)
#: The GNSS covariance the receivers *really* had, per component.
GNSS_TRUE = np.array([[25e-6, 2e-6, 1e-6], [2e-6, 25e-6, -1e-6], [1e-6, -1e-6, 100e-6]])
FIXED = ("P00", "P03", "P10")


def _truth(seed: int = 7) -> dict[str, tuple[float, float, float]]:
    rng = np.random.default_rng(seed)
    points = {}
    for i in range(4):
        for j in range(3):
            points[f"P{i}{j}"] = (
                i * 600.0 + rng.uniform(-80, 80),
                j * 700.0 + rng.uniform(-80, 80),
                100.0 + rng.uniform(-30, 60),
            )
    return points


def _position(values, *, exact: bool) -> Position:
    make = (
        (lambda v: Quantity.exact(v, Unit.METRE))
        if exact
        else (lambda v: Quantity.from_std_dev(v, 1.0, Unit.METRE))
    )
    return Position(
        values=tuple(make(v) for v in values),
        system=CoordinateSystem.PROJECTED,
        crs="LOCAL",
        height_type=HeightType.ORTHOMETRIC,
    )


def survey(*, gnss_declared_scale: float = 1.0, seed: int = 11) -> Network:
    """A 12-station network: slope distances and zenith angles between
    neighbours, and GNSS baselines on a sparser pattern, each drawn from its
    true covariance and declared with its sigmas multiplied by
    *gnss_declared_scale*."""
    rng = np.random.default_rng(seed)
    truth = _truth()
    network = Network(id="synthetic", crs="LOCAL")
    for name, xyz in truth.items():
        start = tuple(v + rng.uniform(-0.05, 0.05) for v in xyz)
        constraint = (
            ConstraintSpec(
                mode=ConstraintMode.FIXED,
                components=frozenset({"easting", "northing", "up"}),
                position=_position(xyz, exact=True),
            )
            if name in FIXED
            else ConstraintSpec()
        )
        network.add_station(
            Station(id=name, approx_position=_position(start, exact=False), constraint=constraint)
        )
    names = sorted(truth)
    counter = 0
    for a in names:
        for b in names:
            if a >= b:
                continue
            ea, na, ua = truth[a]
            eb, nb, ub = truth[b]
            de, dn, du = eb - ea, nb - na, ub - ua
            distance = math.sqrt(de * de + dn * dn + du * du)
            if distance < 1200.0:
                counter += 1
                network.add_observation(
                    Observation(
                        id=f"s{counter}",
                        type=ObservationType.SLOPE_DISTANCE,
                        stations=(a, b),
                        values=(
                            Quantity.from_std_dev(
                                distance + rng.normal(0, SIGMA_DISTANCE), SIGMA_DISTANCE, Unit.METRE
                            ),
                        ),
                    )
                )
                zenith = math.atan2(math.hypot(de, dn), du)
                network.add_observation(
                    Observation(
                        id=f"z{counter}",
                        type=ObservationType.ZENITH_ANGLE,
                        stations=(a, b),
                        values=(
                            Quantity.from_std_dev(
                                zenith + rng.normal(0, SIGMA_ZENITH), SIGMA_ZENITH, Unit.RADIAN
                            ),
                        ),
                    )
                )
            if distance < 1700.0 and (int(a[1]) + int(b[2])) % 2 == 0:
                counter += 1
                noise = rng.multivariate_normal(np.zeros(3), GNSS_TRUE)
                declared = GNSS_TRUE * gnss_declared_scale**2
                identifier = f"g{counter}"
                network.add_observation(
                    Observation(
                        id=identifier,
                        type=ObservationType.GNSS_BASELINE,
                        stations=(a, b),
                        values=tuple(
                            Quantity(v + n, declared[k, k], Unit.METRE)
                            for k, (v, n) in enumerate(zip((de, dn, du), noise, strict=True))
                        ),
                        cluster_id=f"c{identifier}",
                        meta={BASELINE_FRAME_KEY: BaselineFrame.LOCAL.value},
                    )
                )
                network.add_cluster(
                    Cluster(
                        id=f"c{identifier}",
                        kind=ClusterKind.GNSS_BASELINE,
                        observation_ids=(identifier,),
                        covariance=Covariance(
                            matrix=declared, labels=("m0.x", "m0.y", "m0.z"), units=(Unit.METRE,) * 3
                        ),
                    )
                )
    return network


OPTIONS = AdjustmentOptions(frame=Frame.SPACE_3D, datum=DatumDefinition.FIXED)


class TestTheEstimator:
    def test_one_group_is_the_familiar_variance_factor(self):
        """With a single group LS-VCE reduces to v^T P v / r -- the a posteriori
        variance factor every adjustment already reports."""
        network = survey()
        run = adjust(network, OPTIONS)
        result = estimate_variance_components(network, OPTIONS, group_of=lambda o: "all")
        (component,) = result.components
        assert component.factor == pytest.approx(run.variance_factor_aposteriori, rel=1e-6)
        assert component.redundancy == pytest.approx(run.degrees_of_freedom, rel=1e-9)

    def test_a_mis_scaled_technique_is_recovered(self):
        """Criterion 3. The GNSS sigmas are declared at half their true value,
        so the true factor on its variances is 4; the total station's are
        right, so its factor is 1. Both are recovered within two of their own
        standard deviations."""
        result = estimate_variance_components(survey(gnss_declared_scale=0.5), OPTIONS)
        gnss = result.factor("gnss")
        total_station = result.factor("total_station")
        assert abs(gnss.factor - 4.0) <= 2.0 * gnss.std_dev
        assert abs(total_station.factor - 1.0) <= 2.0 * total_station.std_dev
        assert not gnss.is_consistent_with_one()
        assert gnss.sigma_scale == pytest.approx(math.sqrt(gnss.factor))
        # It says something: the factor is several of its sigmas from one.
        assert gnss.std_dev < 1.0

    def test_a_weighted_constraint_is_a_known_part_not_a_group(self):
        """A control station held weighted is a row with a stated covariance
        and no observation behind it. It belonged to no group, and the
        estimator looked every row up as an observation -- a KeyError on the
        first network with a weighted benchmark or a geoid prior. It is now
        ``Q_0``, the known part, and the factors are recovered around it."""
        network = survey(gnss_declared_scale=0.5)
        rng = np.random.default_rng(5)
        sigma = 0.004
        truth = _truth()["P10"]
        network.stations["P10"] = Station(
            id="P10",
            approx_position=network.stations["P10"].approx_position,
            constraint=ConstraintSpec(
                mode=ConstraintMode.WEIGHTED,
                components=frozenset({"easting", "northing", "up"}),
                position=_position([v + rng.normal(0, sigma) for v in truth], exact=True),
                covariance=Covariance(
                    matrix=np.eye(3) * sigma**2,
                    labels=("easting", "northing", "up"),
                    units=(Unit.METRE,) * 3,
                ),
            ),
        )
        result = estimate_variance_components(network, OPTIONS)
        assert [c.group for c in result.components] == ["total_station", "gnss"]
        gnss, total_station = result.factor("gnss"), result.factor("total_station")
        assert abs(gnss.factor - 4.0) <= 2.0 * gnss.std_dev
        assert abs(total_station.factor - 1.0) <= 2.0 * total_station.std_dev
        # The constraint's rows carry redundancy of their own, which neither
        # group is credited with.
        assert gnss.redundancy + total_station.redundancy < result.run.degrees_of_freedom

    def test_correct_weights_give_factors_consistent_with_one(self):
        result = estimate_variance_components(survey(), OPTIONS)
        for component in result.components:
            assert component.is_consistent_with_one(z=2.5), component

    def test_the_rescaled_network_passes_where_the_original_failed(self):
        """The use a factor has: applied once, the global test that failed for a
        reason nobody could locate is satisfied, and the factor says whose."""
        network = survey(gnss_declared_scale=0.5)
        before = adjust(network, OPTIONS)
        result = estimate_variance_components(network, OPTIONS)
        assert before.variance_factor_aposteriori > 1.5
        assert result.run.variance_factor_aposteriori == pytest.approx(1.0, abs=1e-3)

    def test_the_stated_uncertainty_is_what_the_estimates_scatter_by(self):
        """D(theta) is a claim, and a claim is tested: over repeated surveys
        the factors scatter by what their standard deviation says -- within the
        30 % a sample of 40 can resolve."""
        estimates, stated = [], []
        for seed in range(40):
            result = estimate_variance_components(survey(gnss_declared_scale=0.5, seed=seed), OPTIONS)
            gnss = result.factor("gnss")
            estimates.append(gnss.factor)
            stated.append(gnss.std_dev)
        assert np.std(estimates, ddof=1) == pytest.approx(np.mean(stated), rel=0.3)
        assert np.mean(estimates) == pytest.approx(4.0, abs=3.0 * np.std(estimates) / math.sqrt(40))


class TestWhatItRefuses:
    def test_a_cluster_split_across_groups_is_refused(self):
        """Two distances in one correlated cluster, put in two groups: the
        cluster's covariance cannot be rescaled by two factors at once."""
        network = survey()
        two = Network(id="split", crs="LOCAL")
        for station in network.stations.values():
            two.add_station(station)
        members = [o for o in network.observations.values() if o.type is ObservationType.SLOPE_DISTANCE][:2]
        for observation in members:
            two.add_observation(
                Observation(
                    id=observation.id,
                    type=observation.type,
                    stations=observation.stations,
                    values=observation.values,
                    cluster_id="pair",
                )
            )
        two.add_cluster(
            Cluster(
                id="pair",
                kind=ClusterKind.GENERIC,
                observation_ids=tuple(o.id for o in members),
                covariance=Covariance(
                    matrix=np.diag([SIGMA_DISTANCE**2] * 2),
                    labels=tuple(o.id for o in members),
                    units=(Unit.METRE,) * 2,
                ),
            )
        )
        with pytest.raises(ValidationError) as caught:
            estimate_variance_components(two, OPTIONS, group_of=lambda o: o.id)
        assert caught.value.code == "validation.variance_component_cluster_split"

    def test_a_group_with_no_redundancy_is_refused_by_name(self):
        """GNSS reaches only a pendant station, which nothing else observes: its
        baseline has a redundancy of zero, the residuals say nothing about its
        weight, and a factor from them would be noise with a number attached."""
        network = survey()
        for identifier in [
            o.id for o in network.observations.values() if o.type is ObservationType.GNSS_BASELINE
        ]:
            del network.observations[identifier]
            del network.clusters[f"c{identifier}"]
        network.add_station(Station(id="Q", approx_position=_position((10.0, -400.0, 90.0), exact=False)))
        declared = GNSS_TRUE
        network.add_observation(
            Observation(
                id="gq",
                type=ObservationType.GNSS_BASELINE,
                stations=("P00", "Q"),
                values=tuple(
                    Quantity(v, declared[k, k], Unit.METRE) for k, v in enumerate((10.0, -400.0, -10.0))
                ),
                cluster_id="cq",
                meta={BASELINE_FRAME_KEY: BaselineFrame.LOCAL.value},
            )
        )
        network.add_cluster(
            Cluster(
                id="cq",
                kind=ClusterKind.GNSS_BASELINE,
                observation_ids=("gq",),
                covariance=Covariance(
                    matrix=declared, labels=("m0.x", "m0.y", "m0.z"), units=(Unit.METRE,) * 3
                ),
            )
        )
        with pytest.raises(ComputationError) as caught:
            estimate_variance_components(network, OPTIONS)
        assert caught.value.code == "computation.variance_component_unestimable"
        assert caught.value.context["group"] == "gnss"


def test_scaling_leaves_values_and_correlations_alone():
    network = survey()
    scaled = scale_groups(network, {"gnss": 4.0})
    for identifier, observation in network.observations.items():
        after = scaled.observations[identifier]
        assert [v.value for v in after.values] == [v.value for v in observation.values]
        factor = 4.0 if observation.type is ObservationType.GNSS_BASELINE else 1.0
        assert [v.variance for v in after.values] == pytest.approx(
            [v.variance * factor for v in observation.values]
        )
    for identifier, cluster in network.clusters.items():
        assert np.asarray(scaled.clusters[identifier].covariance.matrix) == pytest.approx(
            np.asarray(cluster.covariance.matrix) * 4.0
        )
