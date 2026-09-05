# SPDX-License-Identifier: GPL-2.0-or-later
"""A planned network being edited, and what it would achieve (FR-272).

``specs/06-adjustment-core.md`` section 8 and ``specs/19`` section 1: a design
is edited on the canvas -- stations added, moved and removed, observations drawn
between them -- and re-evaluated after every change. Doing that inside a GIS,
against orthoimagery and existing control, is the reason pre-analysis belongs in
QGIS rather than in a spreadsheet.

This module is that loop with no Qt in it. The dialog in
:mod:`geocomp.gui.preanalysis_dialog` renders a session and calls its methods;
every rule about what an edit means lives here.

**Evaluation never raises.** A design under construction spends most of its life
un-evaluable: one station, no observations, three stations and a rank defect.
An interactive loop that threw on each of those would be unusable, and a caller
forced to guess which exceptions to swallow would swallow the wrong ones. So a
design that cannot be evaluated reports *why*, as findings, in the same shape as
a design that can be evaluated but is poor.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field, replace

import numpy as np

from geocomp.core.adjustment.parameters import Frame
from geocomp.core.errors import GeoCompError
from geocomp.core.findings import Finding, Severity
from geocomp.core.models import (
    Cluster,
    ClusterKind,
    CoordinateSystem,
    DatumDefinition,
    HeightType,
    Network,
    Observation,
    ObservationType,
    Position,
    Station,
    StationType,
)
from geocomp.core.preanalysis.design import DesignReport, simulate
from geocomp.core.preanalysis.inspection import inspect
from geocomp.core.uncertainty import Covariance, Quantity
from geocomp.core.units import Unit

__all__ = ["DesignSession", "SessionState", "default_sigma_for"]

#: Assumed precision per observation type, used when the caller states none.
#: A design is a statement about an instrument as much as about a geometry, so
#: these are a starting point to be overridden, never a silent answer -- the
#: report carries the sigmas it used.
DEFAULT_SIGMAS: dict[ObservationType, float] = {
    ObservationType.HORIZONTAL_DISTANCE: 0.003,
    ObservationType.SLOPE_DISTANCE: 0.003,
    ObservationType.DIRECTION: 5.0e-6,
    ObservationType.HORIZONTAL_ANGLE: 7.0e-6,
    ObservationType.AZIMUTH: 5.0e-6,
    ObservationType.ZENITH_ANGLE: 5.0e-6,
    ObservationType.HEIGHT_DIFFERENCE: 0.002,
}


def default_sigma_for(observation_type: ObservationType) -> float:
    """The assumed precision for a planned observation of this type."""
    try:
        return DEFAULT_SIGMAS[observation_type]
    except KeyError as exc:
        raise GeoCompError(
            "no_default_sigma",
            observation_type=observation_type.name,
            expected="a stated precision; GeoComp does not invent one (specs/05 section 5)",
        ) from exc


@dataclass(frozen=True)
class SessionState:
    """One evaluated state of the design.

    ``report`` is ``None`` when the design could not be evaluated, and
    ``findings`` then says why. Both are always present, so a caller renders one
    shape rather than branching on which kind of answer arrived.
    """

    report: DesignReport | None
    findings: tuple[Finding, ...] = ()

    @property
    def is_evaluable(self) -> bool:
        return self.report is not None

    @property
    def blocking(self) -> tuple[Finding, ...]:
        return tuple(finding for finding in self.findings if finding.is_blocking)


@dataclass
class _Snapshot:
    stations: dict[str, Station]
    observations: dict[str, Observation]
    clusters: dict[str, object]


@dataclass
class DesignSession:
    """A planned network under interactive edit.

    Every mutation records an undo point first. Editing a design on a canvas
    without undo is punishing -- a misplaced click moves a station and there is
    no way back -- and a design network is small enough that snapshotting it
    costs nothing.
    """

    crs: str = ""
    frame: Frame = Frame.PLANE_2D
    datum: DatumDefinition = DatumDefinition.INNER_CONSTRAINT
    datum_stations: tuple[str, ...] = ()
    confidence: float = 0.95
    tolerance: float | None = None
    network: Network = field(default_factory=lambda: Network(id="design", name="Design"))
    _undo: list[_Snapshot] = field(default_factory=list, repr=False)
    _redo: list[_Snapshot] = field(default_factory=list, repr=False)
    _counter: itertools.count = field(default_factory=lambda: itertools.count(1), repr=False)

    def __post_init__(self) -> None:
        if self.crs and not self.network.crs:
            self.network.crs = self.crs

    # -- editing ---------------------------------------------------------

    def add_station(
        self, station_id: str, easting: float, northing: float, height: float = 0.0
    ) -> None:
        """Add a planned station at a canvas position.

        :attr:`StationType.PLANNED` rather than ``MARK``: it does not exist yet,
        and a design that produced stations indistinguishable from surveyed ones
        would let a plan be mistaken for a result.
        """
        if not station_id.strip():
            raise GeoCompError("station_without_id", expected="a station name")
        if station_id in self.network.stations:
            raise GeoCompError(
                "duplicate_station",
                station=station_id,
                expected="a name no other planned station is using",
            )
        self._checkpoint()
        self.network.add_station(
            Station(
                id=station_id,
                approx_position=self._position(easting, northing, height),
                station_type=StationType.PLANNED,
            )
        )

    def move_station(self, station_id: str, easting: float, northing: float) -> None:
        """Move a planned station, keeping its height.

        The whole point of the loop: drag a station and watch the ellipses
        change. The observations that touch it are untouched -- what they
        connect has not changed, only where it is.
        """
        station = self._station(station_id)
        height = station.approx_position.values[2].value if station.approx_position else 0.0
        self._checkpoint()
        self.network.stations[station_id] = replace(
            station, approx_position=self._position(easting, northing, height)
        )

    def remove_station(self, station_id: str) -> tuple[str, ...]:
        """Remove a station **and every observation that touches it**.

        Leaving them would produce a network referring to a station that does
        not exist, which fails deep inside the adjustment with a message about
        a missing parameter rather than about the click that caused it.

        Returns the observation ids that went with it, so the caller can say so.
        """
        self._station(station_id)
        orphaned = tuple(
            sorted(
                observation.id
                for observation in self.network.observations.values()
                if station_id in observation.stations
            )
        )
        self._checkpoint()
        del self.network.stations[station_id]
        touched = {
            self.network.observations[observation_id].cluster_id
            for observation_id in orphaned
            if self.network.observations[observation_id].cluster_id is not None
        }
        for observation_id in orphaned:
            del self.network.observations[observation_id]
        for cluster_id in touched:
            self._rebuild_cluster(cluster_id)
        self.datum_stations = tuple(s for s in self.datum_stations if s != station_id)
        return orphaned

    def add_observation(
        self,
        observation_type: ObservationType,
        stations: tuple[str, ...],
        *,
        sigma: float | None = None,
        observation_id: str = "",
    ) -> str:
        """Plan an observation between existing stations.

        Its *value* is irrelevant and is stored as zero: a design uses the
        geometry and the assumed precision, never the measurement, which is what
        lets a network be judged before anyone goes to the field.
        """
        for name in stations:
            self._station(name)
        if not stations:
            raise GeoCompError(
                "observation_without_stations",
                expected="the stations the planned observation connects",
            )
        precision = sigma if sigma is not None else default_sigma_for(observation_type)
        unit = _unit_for(observation_type)
        identifier = observation_id or self._next_id(observation_type)
        cluster_id = self._cluster_id(observation_type, stations)

        self._checkpoint()
        self.network.add_observation(
            Observation(
                id=identifier,
                type=observation_type,
                stations=tuple(stations),
                values=(Quantity.from_std_dev(0.0, precision, unit),),
                cluster_id=cluster_id,
                meta={"planned": True},
            )
        )
        if cluster_id is not None:
            self._rebuild_cluster(cluster_id)
        return identifier

    def remove_observation(self, observation_id: str) -> None:
        observation = self.network.observations.get(observation_id)
        if observation is None:
            raise GeoCompError(
                "unknown_observation",
                observation=observation_id,
                expected="an observation this design contains",
            )
        self._checkpoint()
        del self.network.observations[observation_id]
        if observation.cluster_id is not None:
            self._rebuild_cluster(observation.cluster_id)

    def set_datum(self, datum: DatumDefinition, stations: tuple[str, ...] = ()) -> None:
        self._checkpoint()
        self.datum = datum
        self.datum_stations = tuple(stations)

    # -- undo ------------------------------------------------------------

    @property
    def can_undo(self) -> bool:
        return bool(self._undo)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo)

    def undo(self) -> bool:
        if not self._undo:
            return False
        self._redo.append(self._capture())
        self._restore(self._undo.pop())
        return True

    def redo(self) -> bool:
        if not self._redo:
            return False
        self._undo.append(self._capture())
        self._restore(self._redo.pop())
        return True

    def _checkpoint(self) -> None:
        self._undo.append(self._capture())
        # A new edit invalidates the redo branch. Keeping it would let a user
        # redo their way into a state the current one never came from.
        self._redo.clear()

    def _capture(self) -> _Snapshot:
        return _Snapshot(
            stations=dict(self.network.stations),
            observations=dict(self.network.observations),
            clusters=dict(self.network.clusters),
        )

    def _restore(self, snapshot: _Snapshot) -> None:
        self.network.stations = dict(snapshot.stations)
        self.network.observations = dict(snapshot.observations)
        self.network.clusters = dict(snapshot.clusters)

    # -- evaluation ------------------------------------------------------

    def evaluate(self) -> SessionState:
        """What the design as it stands would achieve, or why it cannot be told.

        Never raises. A design mid-edit is usually not evaluable, and an
        interactive loop that threw on every intermediate state would be
        unusable.
        """
        findings = list(self._structural_findings())
        if any(finding.is_blocking for finding in findings):
            return SessionState(report=None, findings=tuple(findings))

        try:
            report = simulate(
                self.network,
                frame=self.frame,
                datum=self.datum,
                datum_stations=list(self.datum_stations) or None,
                confidence=self.confidence,
            )
        except GeoCompError as exc:
            findings.append(
                Finding(
                    code=exc.code if hasattr(exc, "code") else "design_not_evaluable",
                    severity=Severity.BLOCKING,
                    message=str(exc),
                )
            )
            return SessionState(report=None, findings=tuple(findings))

        findings.extend(self._quality_findings(report))
        return SessionState(report=report, findings=tuple(findings))

    def _structural_findings(self) -> list[Finding]:
        """What is wrong with the design as a *network*, before any arithmetic.

        These are the messages that make the loop usable: "add an observation"
        is actionable, and "singular normal matrix" is not.
        """
        found: list[Finding] = []
        if not self.network.stations:
            found.append(
                Finding(
                    code="design_without_stations",
                    severity=Severity.BLOCKING,
                    message="the design has no stations yet; add one to begin",
                )
            )
            return found
        if not self.network.observations:
            found.append(
                Finding(
                    code="design_without_observations",
                    severity=Severity.BLOCKING,
                    message=(
                        "the design has stations but no planned observations, so there is "
                        "nothing to evaluate. Connect two stations to begin"
                    ),
                )
            )
            return found

        found.extend(inspect(self.network, frame=self.frame).findings)
        return found

    def _quality_findings(self, report: DesignReport) -> list[Finding]:
        """What is wrong with an evaluable design -- the design question itself."""
        found: list[Finding] = []
        if report.degrees_of_freedom <= 0:
            found.append(
                Finding(
                    code="design_without_redundancy",
                    severity=Severity.WARNING,
                    message=(
                        "the design has no redundancy, so nothing in it can be checked. "
                        "A blunder anywhere would be invisible and would pass into the "
                        "coordinates unaltered"
                    ),
                    value=float(report.degrees_of_freedom),
                )
            )
        if self.tolerance is not None and not report.meets(self.tolerance):
            worst = report.worst_station()
            found.append(
                Finding(
                    code="design_misses_tolerance",
                    severity=Severity.WARNING,
                    message=(
                        f"station {worst.station_id} is expected to reach "
                        f"{worst.positional_uncertainty * 1000:.1f} mm against a required "
                        f"{self.tolerance * 1000:.1f} mm"
                    ),
                    stations=(worst.station_id,),
                    value=worst.positional_uncertainty,
                    threshold=self.tolerance,
                )
            )
        for result in report.reliability.uncheckable:
            found.append(
                Finding(
                    code="planned_observation_uncheckable",
                    severity=Severity.WARNING,
                    message=(
                        f"planned observation {result.observation_id} would be "
                        "uncheckable: no blunder in it could be detected at all"
                    ),
                    observations=(result.observation_id,),
                    value=result.redundancy,
                )
            )
        return found

    # -- helpers ---------------------------------------------------------

    def _cluster_id(
        self, observation_type: ObservationType, stations: tuple[str, ...]
    ) -> str | None:
        """The cluster a planned observation of this type belongs to.

        Directions from one setup share an unknown orientation, so they are one
        set and the model refuses to hold them otherwise (FR-104). The occupied
        station names the set, which is exactly what a direction set is: every
        direction turned from one instrument station.
        """
        if observation_type is not ObservationType.DIRECTION:
            return None
        return f"directions-{stations[0]}"

    def _rebuild_cluster(self, cluster_id: str) -> None:
        """Rebuild a cluster from its current members, or drop it when empty.

        Rebuilt rather than patched because the covariance ordering *is* the
        member order: adding a direction to a set changes the matrix, and a
        stale one would be applied to the wrong observations. The units come
        from the members themselves rather than from the caller, so this cannot
        be told the wrong ones.
        """
        members = sorted(
            observation.id
            for observation in self.network.observations.values()
            if observation.cluster_id == cluster_id
        )
        if not members:
            self.network.clusters.pop(cluster_id, None)
            return
        quantities = [self.network.observations[name].values[0] for name in members]
        self.network.clusters[cluster_id] = Cluster(
            id=cluster_id,
            kind=ClusterKind.DIRECTION_SET,
            observation_ids=tuple(members),
            covariance=Covariance(
                matrix=np.diag([quantity.variance for quantity in quantities]),
                labels=tuple(members),
                units=tuple(quantity.unit for quantity in quantities),
            ),
        )

    def _station(self, station_id: str) -> Station:
        try:
            return self.network.stations[station_id]
        except KeyError as exc:
            raise GeoCompError(
                "unknown_station",
                station=station_id,
                expected="a station this design contains",
            ) from exc

    def _position(self, easting: float, northing: float, height: float) -> Position:
        return Position(
            values=(
                Quantity.exact(easting, Unit.METRE),
                Quantity.exact(northing, Unit.METRE),
                Quantity.exact(height, Unit.METRE),
            ),
            system=CoordinateSystem.PROJECTED,
            crs=self.crs or self.network.crs or "EPSG:4326",
            height_type=HeightType.ORTHOMETRIC,
        )

    def _next_id(self, observation_type: ObservationType) -> str:
        prefix = observation_type.name.lower()
        while True:
            candidate = f"{prefix}-{next(self._counter)}"
            if candidate not in self.network.observations:
                return candidate


def _unit_for(observation_type: ObservationType) -> Unit:
    angular = {
        ObservationType.DIRECTION,
        ObservationType.HORIZONTAL_ANGLE,
        ObservationType.AZIMUTH,
        ObservationType.ZENITH_ANGLE,
    }
    return Unit.RADIAN if observation_type in angular else Unit.METRE
