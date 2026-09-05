# SPDX-License-Identifier: GPL-2.0-or-later
"""Network design simulation -- pre-analysis proper (FR-270, FR-271).

``specs/06-adjustment-core.md`` section 5.1.

**Pre-analysis is network design, not data checking.** The archived roadmap
conflated the two ([`specs/archive/README.md`](../../../specs/archive/README.md)
item 6); both capabilities exist and they answer different questions. Checking
real data for connectivity and duplicates is
:mod:`geocomp.core.preanalysis.inspection`.

Here, no observation has been made yet:

    Sigma_x = sigma_0^2 (A^T P A)^-1

**A** depends only on the geometry of the planned network and **P** only on the
assumed precisions, so the expected precision of a network can be computed
before anyone goes to the field. That is the whole value: a network that cannot
meet its specification is much cheaper to discover now.

The planned observations carry no values -- only types, stations and assumed
sigmas -- so this module fabricates a value of zero for each, purely to reuse
the same equation code. The values never affect **A** or **P**, which is why the
simulation is exact rather than approximate.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from geocomp.core.adjustment.datum import constraint_matrix, detect_defect
from geocomp.core.adjustment.least_squares import AdjustmentOptions, starting_values
from geocomp.core.adjustment.normal_equations import assemble, solve
from geocomp.core.adjustment.parameters import Frame, ParameterLayout
from geocomp.core.errors import ComputationError
from geocomp.core.models import DatumDefinition, ErrorEllipse, Network
from geocomp.core.statistics.ellipses import error_ellipse, positional_uncertainty
from geocomp.core.statistics.reliability import (
    DEFAULT_ALPHA,
    DEFAULT_BETA,
    ReliabilityReport,
    reliability,
)

__all__ = ["DesignReport", "StationDesign", "simulate"]


@dataclass(frozen=True)
class StationDesign:
    """The precision a planned network is expected to give one station."""

    station_id: str
    ellipse: ErrorEllipse
    positional_uncertainty: float
    std_devs: tuple[float, ...]


@dataclass(frozen=True)
class DesignReport:
    """What a planned network would achieve, before observing it.

    Attributes:
        stations: Expected precision per station.
        reliability: Expected internal and external reliability. The second half
            of the answer: a design can be precise and still unable to detect a
            blunder anywhere.
        degrees_of_freedom: Redundancy of the design.
        defect: The datum defect of the planned observation set.
    """

    stations: tuple[StationDesign, ...]
    reliability: ReliabilityReport
    degrees_of_freedom: int
    observation_count: int
    parameter_count: int
    defect_description: str

    def worst_station(self) -> StationDesign | None:
        """The station the design serves least well -- usually the design question."""
        if not self.stations:
            return None
        return max(self.stations, key=lambda station: station.positional_uncertainty)

    def meets(self, tolerance: float) -> bool:
        """Whether every station's positional uncertainty is within *tolerance*."""
        return all(station.positional_uncertainty <= tolerance for station in self.stations)


def simulate(
    network: Network,
    *,
    frame: Frame = Frame.PLANE_2D,
    datum: DatumDefinition = DatumDefinition.INNER_CONSTRAINT,
    datum_stations: list[str] | None = None,
    confidence: float = 0.95,
    variance_factor: float = 1.0,
    alpha: float = DEFAULT_ALPHA,
    beta: float = DEFAULT_BETA,
) -> DesignReport:
    """Compute the expected precision and reliability of a *planned* network.

    The network's observations supply types, stations and assumed sigmas; their
    values are ignored. Stations may be :attr:`StationType.PLANNED` and need only
    approximate coordinates -- which for a design is all anyone has.

    Args:
        datum: How the datum defect is removed. Inner constraints by default,
            because a design should not be judged through the distortion a
            particular fixed station imposes.
    """
    observations = list(network.observations.values())
    if not observations:
        raise ComputationError(
            "no_planned_observations",
            network=network.id,
            expected="at least one planned observation to evaluate the design",
        )

    layout = ParameterLayout.build(network, frame)
    options = AdjustmentOptions(frame=frame, datum=datum, datum_stations=datum_stations)
    values = starting_values(network, layout, options, None)
    x = np.array([values[slot.owner][slot.component] for slot in layout.slots])

    system = assemble(observations, network.clusters, layout, x)

    defect = detect_defect(observations, frame)
    constraints = None
    if datum in (DatumDefinition.INNER_CONSTRAINT, DatumDefinition.MINIMUM_CONSTRAINT) and defect.size:
        constraints = constraint_matrix(layout, values, defect, station_ids=datum_stations)

    result = solve(system, layout, constraints=constraints)
    covariance = variance_factor * result.cofactor
    degrees_of_freedom = system.observation_count - layout.size + (
        defect.size if constraints is not None else 0
    )

    q_ll = np.linalg.inv(system.weight)
    cofactor_residuals = q_ll - system.design @ result.cofactor @ system.design.T

    stations: list[StationDesign] = []
    for station_id in layout.station_ids():
        columns = layout.station_columns(station_id)
        if not columns:
            continue
        indices = [columns[c] for c in frame.components if c in columns]
        block = covariance[np.ix_(indices, indices)]
        if block.shape[0] < 2:
            # A 1D design has no ellipse; report the standard deviation as both
            # axes so the structure stays uniform rather than optional.
            sigma = float(np.sqrt(max(block[0, 0], 0.0)))
            ellipse = ErrorEllipse(sigma, sigma, 0.0, confidence)
            uncertainty = sigma
        else:
            ellipse = error_ellipse(
                block[:2, :2], confidence=confidence, degrees_of_freedom=degrees_of_freedom
            )
            uncertainty = positional_uncertainty(
                block[:2, :2], confidence=confidence, degrees_of_freedom=degrees_of_freedom
            )
        stations.append(
            StationDesign(
                station_id=station_id,
                ellipse=ellipse,
                positional_uncertainty=uncertainty,
                std_devs=tuple(float(np.sqrt(max(block[i, i], 0.0))) for i in range(block.shape[0])),
            )
        )

    return DesignReport(
        stations=tuple(stations),
        reliability=reliability(
            cofactor_residuals,
            system.weight,
            system.design,
            result.cofactor,
            system.row_labels,
            alpha=alpha,
            beta=beta,
        ),
        degrees_of_freedom=degrees_of_freedom,
        observation_count=system.observation_count,
        parameter_count=layout.size,
        defect_description=defect.describe(),
    )
