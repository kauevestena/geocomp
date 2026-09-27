# SPDX-License-Identifier: GPL-2.0-or-later
"""Geoid undulations as parameters of a combined adjustment (FR-802, FR-804).

``specs/13`` section 3. The geocentric frame estimates ellipsoidal heights; a
levelled height difference or a published benchmark is orthometric, and the two
are related by the geoid, ``h = H + N``. Items 2 to 5 of that section decide how.

**Each undulation is a parameter, with the geoid model's value as a weighted
prior.** At every station an orthometric observation touches, ``N`` is
estimated, and the model contributes one observation of it: its interpolated
value, with the model's stated accuracy. The alternatives are both wrong in a
way that matters:

* Subtracting the model's ``N`` as an exact number discards its uncertainty
  (item 4), and a height solution is often limited by exactly that.
* Subtracting it and adding its variance to each observation's double-counts
  it: every height difference at a station shares that station's ``N``, so the
  added errors are correlated across observations, not independent. With a
  0.1 m geoid and 2 mm levelling it also makes the levelling worthless, which
  it is not -- levelling between two GNSS stations measures the *change* in
  undulation, and the parameters let it.

As parameters, the geoid's uncertainty propagates through the normal equations
like any other (item 4), and the prior's residual at each station -- adjusted
``N`` less the model's -- is the empirical test of the model over the project
(item 5), which is what :func:`geoid_residuals` reports.

**The priors are independent between stations**, and that is an approximation,
recorded as ``INDEPENDENCE_ASSUMED`` on the solution. A geoid model's errors are
spatially correlated -- its relative accuracy over a few kilometres is far
better than its absolute one -- and a model that states only an absolute
``sigma`` gives nothing to build that correlation from. Treating them as
independent trusts the model *less* for a height difference than it deserves,
so heights that depend only on the geoid come out with honest-to-pessimistic
uncertainties rather than optimistic ones.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from geocomp.core.adjustment.geocentric import ELLIPSOID, UNDULATION, height_type_of
from geocomp.core.adjustment.normal_equations import CONSTRAINT_ROW_PREFIX
from geocomp.core.adjustment.parameters import (
    ParameterLayout,
    WeightedConstraint,
    geocentric_component,
)
from geocomp.core.errors import ValidationError
from geocomp.core.geodesy.cartesian import cartesian_to_geodetic
from geocomp.core.geoid import GeoidModel
from geocomp.core.models import HeightType, Network, Observation, ObservationType
from geocomp.core.uncertainty import Quantity, Strategy

__all__ = [
    "GEOID_OWNER_PREFIX",
    "UNDULATION",
    "GeoidResidual",
    "geoid_residuals",
    "model_undulations",
    "orthometric_stations",
    "undulation_priors",
]

#: Prefix of a prior's row label after :data:`CONSTRAINT_ROW_PREFIX`, so a
#: report can tell the geoid's rows from a weighted benchmark's.
GEOID_OWNER_PREFIX = "geoid:"

_HEIGHT_TYPES = (
    ObservationType.HEIGHT_DIFFERENCE,
    ObservationType.ORTHOMETRIC_HEIGHT,
    ObservationType.ELLIPSOIDAL_HEIGHT,
)


def orthometric_stations(observations: list[Observation]) -> list[str]:
    """Every station an orthometric observation touches, in first-met order."""
    stations: list[str] = []
    for observation in observations:
        if observation.type not in _HEIGHT_TYPES:
            continue
        if height_type_of(observation) is not HeightType.ORTHOMETRIC:
            continue
        for station in observation.stations:
            if station not in stations:
                stations.append(station)
    return stations


def model_undulations(
    network: Network, stations: list[str], geoid: GeoidModel
) -> dict[str, Quantity]:
    """The model's undulation at each station, with its uncertainty.

    Looked up at the station's approximate position, or its held one: a metre
    of error in where the lookup happens is nothing to a geoid. The strategy
    set records both approximations -- the model's accuracy is a summary figure
    (``DOMINANT_TERM``, from :meth:`GeoidModel.undulation`) and the priors are
    independent between stations (``INDEPENDENCE_ASSUMED``).

    Raises:
        ValidationError: ``undulation_without_position`` for a station with no
            position to look the undulation up at, and whatever the model
            raises for a point outside its coverage.
    """
    undulations: dict[str, Quantity] = {}
    for station_id in stations:
        station = network.stations.get(station_id)
        position = None
        if station is not None:
            position = station.approx_position or station.constraint.position
        if position is None:
            raise ValidationError(
                "undulation_without_position",
                station=station_id,
                expected=(
                    "an approximate position, so the geoid undulation relating its "
                    "orthometric height to the ellipsoidal one can be looked up"
                ),
            )
        cartesian = [geocentric_component(position, c, station_id) for c in ("x", "y", "z")]
        latitude, longitude, _height = cartesian_to_geodetic(*cartesian, ELLIPSOID)
        undulation = geoid.undulation(latitude, longitude)
        strategies = set(undulation.strategies)
        if len(stations) > 1:
            strategies.add(Strategy.INDEPENDENCE_ASSUMED)
        undulations[station_id] = Quantity(
            value=undulation.value,
            variance=undulation.variance,
            unit=undulation.unit,
            mode=undulation.mode,
            strategies=frozenset(strategies),
        )
    return undulations


def undulation_priors(
    layout: ParameterLayout, undulations: dict[str, Quantity]
) -> list[WeightedConstraint]:
    """One weighted observation of each undulation parameter: the model's value."""
    priors: list[WeightedConstraint] = []
    for station_id, undulation in undulations.items():
        column = layout.column(station_id, UNDULATION)
        if column is None:
            continue
        priors.append(
            WeightedConstraint(
                station_id=f"{GEOID_OWNER_PREFIX}{station_id}",
                components=(UNDULATION,),
                columns=(column,),
                values=(undulation.value,),
                covariance=np.array([[undulation.variance]]),
            )
        )
    return priors


@dataclass(frozen=True)
class GeoidResidual:
    """The geoid model tested at one station (``specs/13`` section 3, item 5).

    Attributes:
        station_id: Where.
        model: The model's undulation there, metres.
        model_std_dev: The model's stated accuracy there, metres.
        adjusted: The undulation the adjustment settled on.
        residual: ``adjusted - model``. Consistently one sign across a project
            is a bias in the model or in the height datum; a trend is a tilt.
        redundancy: How much the rest of the network checks this station's
            undulation. Near zero means nothing does -- only the model says what
            it is -- and the residual is then zero by construction, not by
            agreement.
        standardised: ``residual`` over its own standard deviation, or
            ``None`` where the redundancy is too small for one to mean anything.
    """

    station_id: str
    model: float
    model_std_dev: float
    adjusted: float
    residual: float
    redundancy: float
    standardised: float | None


def geoid_residuals(run) -> tuple[GeoidResidual, ...]:
    """How the adjustment moved each undulation from the model's value."""
    prefix = f"{CONSTRAINT_ROW_PREFIX}{GEOID_OWNER_PREFIX}"
    sigma0_squared = run.variance_factor_apriori
    results: list[GeoidResidual] = []
    for row, (label, component) in enumerate(run.system.row_labels):
        if not label.startswith(prefix) or component != UNDULATION:
            continue
        station_id = label[len(prefix) :]
        column = run.layout.column(station_id, UNDULATION)
        residual = float(run.residuals[row])
        redundancy = float(run.redundancy[row])
        variance = sigma0_squared * float(run.cofactor_residuals[row, row])
        standardised = residual / math.sqrt(variance) if redundancy > 1e-6 and variance > 0 else None
        adjusted = float(run.parameters[column])
        results.append(
            GeoidResidual(
                station_id=station_id,
                model=adjusted - residual,
                model_std_dev=float(math.sqrt(1.0 / run.system.weight[row, row])),
                adjusted=adjusted,
                residual=residual,
                redundancy=redundancy,
                standardised=standardised,
            )
        )
    return tuple(results)
