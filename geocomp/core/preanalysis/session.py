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
from geocomp.core.errors import DataError, GeoCompError
from geocomp.core.findings import Finding, Severity
from geocomp.core.models import (
    Cluster,
    ClusterKind,
    CoordinateSystem,
    DatumDefinition,
    HeightType,
    Network,
    Observation,
    ObservationSource,
    ObservationType,
    Position,
    Station,
    StationType,
)
from geocomp.core.number_format import localised
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
                provenance=ObservationSource("design"),
            )
        )
        if cluster_id is not None:
            self._rebuild_cluster(cluster_id)
        return identifier

    def remove_observation(self, observation_id: str) -> None:
        """Take an observation out of the design, as an edit that can be undone.

        Its cluster, if it had one, is rebuilt from the members left, or dropped when none are.

        Raises:     GeoCompError: ``unknown_observation`` when the design has no such observation.
        """
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

    def set_observation_sigma(self, observation_id: str, sigma: float) -> None:
        """Change the assumed standard deviation of a planned observation, as an edit that can be undone."""
        observation = self.network.observations.get(observation_id)
        if observation is None:
            raise GeoCompError(
                "unknown_observation",
                observation=observation_id,
                expected="an observation this design contains",
            )
        if sigma <= 0.0:
            raise DataError(
                "observation_without_uncertainty",
                observation=observation_id,
                expected=(
                    "a positive variance; GeoComp does not invent a weight, "
                    "because a fabricated one silently corrupts every statistic"
                ),
            )
        quantity = observation.values[0]
        self._checkpoint()
        self.network.observations[observation_id] = replace(
            observation,
            values=(Quantity.from_std_dev(quantity.value, sigma, quantity.unit),),
        )
        if observation.cluster_id is not None:
            self._rebuild_cluster(observation.cluster_id)

    def required_observation_sigmas(
        self, report: DesignReport | None = None
    ) -> dict[str, float]:
        """The standard deviation each planned observation needs.

        In the observation's own SI unit, so every station reaches :attr:`tolerance`.
        """
        if self.tolerance is None or self.tolerance <= 0.0:
            return {}
        current = report if report is not None else self.evaluate().report
        if current is None:
            return {}
        return current.required_observation_sigmas(self.network, self.tolerance)

    def apply_required_precisions(self) -> dict[str, float]:
        """Scale every planned observation's standard deviation to reach :attr:`tolerance`.

        So the worst station reaches it, as an edit that can be undone.
        """
        required = self.required_observation_sigmas()
        if not required:
            return {}
        self._checkpoint()
        touched: set[str] = set()
        for observation_id, sigma in required.items():
            observation = self.network.observations[observation_id]
            quantity = observation.values[0]
            self.network.observations[observation_id] = replace(
                observation,
                values=(Quantity.from_std_dev(quantity.value, sigma, quantity.unit),),
            )
            if observation.cluster_id is not None:
                touched.add(observation.cluster_id)
        for cluster_id in touched:
            self._rebuild_cluster(cluster_id)
        return required

    def set_datum(self, datum: DatumDefinition, stations: tuple[str, ...] = ()) -> None:
        """Change the datum, and the stations it names, as an edit that can be undone."""
        self._checkpoint()
        self.datum = datum
        self.datum_stations = tuple(stations)

    def load_network(
        self, network: Network, *, tolerance: float | None = None
    ) -> None:
        """Replace the current design with *network*, as an edit that can be undone."""
        self._checkpoint()
        self.network.id = network.id or "design"
        self.network.name = network.name or "Design"
        if network.crs:
            self.network.crs = network.crs
            self.crs = network.crs
        self.network.stations = dict(network.stations)
        self.network.observations = dict(network.observations)
        self.network.clusters = dict(network.clusters)
        if tolerance is not None:
            self.tolerance = tolerance if tolerance > 0.0 else None

    def to_feature_records(self) -> list[dict[str, object]]:
        """Every station (Point) and planned observation (LineString) as flat attribute records."""
        state = self.evaluate()
        report = state.report
        if report is None and self.network.observations:
            connected_ids = {
                station_id
                for observation in self.network.observations.values()
                for station_id in observation.stations
                if station_id in self.network.stations
            }
            if connected_ids and len(connected_ids) < len(self.network.stations):
                sub_network = Network(
                    id=self.network.id, name=self.network.name, crs=self.network.crs
                )
                sub_network.stations = {
                    sid: self.network.stations[sid] for sid in connected_ids
                }
                sub_network.observations = dict(self.network.observations)
                sub_network.clusters = dict(self.network.clusters)
                try:
                    report = simulate(
                        sub_network,
                        frame=self.frame,
                        datum=self.datum,
                        datum_stations=[
                            s for s in self.datum_stations if s in connected_ids
                        ]
                        or None,
                        confidence=self.confidence,
                    )
                except GeoCompError:
                    report = None
        station_designs = (
            {station.station_id: station for station in report.stations}
            if report is not None
            else {}
        )
        reliability_by_id = report.reliability.by_observation() if report is not None else {}
        required_by_id = self.required_observation_sigmas(report) if report is not None else {}

        crs = self.network.crs or self.crs
        tolerance = float(self.tolerance) if self.tolerance is not None else 0.0
        records: list[dict[str, object]] = []

        for station in self.network.stations.values():
            fe, fn, fh = _station_coords(station)
            fd = station_designs.get(station.id)
            uncertainty = float(fd.positional_uncertainty) if fd is not None else None
            semi_major = float(fd.ellipse.semi_major) if fd is not None else None
            semi_minor = float(fd.ellipse.semi_minor) if fd is not None else None
            orientation = float(fd.ellipse.orientation) if fd is not None else None
            records.append(
                {
                    "record_kind": "station",
                    "geometry_type": "Point",
                    "network_id": self.network.id,
                    "crs": crs,
                    "frame": self.frame.name,
                    "datum": self.datum.name,
                    "tolerance": tolerance,
                    "confidence": float(self.confidence),
                    "station_id": station.id,
                    "station_type": station.station_type.name,
                    "easting": fe,
                    "northing": fn,
                    "height": fh,
                    "uncertainty": uncertainty,
                    "semi_major": semi_major,
                    "semi_minor": semi_minor,
                    "orientation": orientation,
                    "observation_id": "",
                    "observation_type": "",
                    "from_station": station.id,
                    "from_type": station.station_type.name,
                    "from_easting": fe,
                    "from_northing": fn,
                    "from_height": fh,
                    "from_uncertainty": uncertainty,
                    "from_semi_major": semi_major,
                    "from_semi_minor": semi_minor,
                    "from_orientation": orientation,
                    "to_station": "",
                    "to_type": "",
                    "to_easting": None,
                    "to_northing": None,
                    "to_height": None,
                    "to_uncertainty": None,
                    "to_semi_major": None,
                    "to_semi_minor": None,
                    "to_orientation": None,
                    "unit": "",
                    "value": None,
                    "sigma": None,
                    "required_sigma": None,
                    "redundancy": None,
                    "mdb": None,
                    "external_effect": None,
                    "cluster_id": "",
                }
            )

        for observation in self.network.observations.values():
            from_id = observation.stations[0]
            to_id = (
                observation.stations[1]
                if len(observation.stations) > 1
                else observation.stations[0]
            )
            from_st = self.network.stations.get(from_id)
            to_st = self.network.stations.get(to_id)
            fe, fn, fh = _station_coords(from_st)
            te, tn, th = _station_coords(to_st)
            fd = station_designs.get(from_id)
            td = station_designs.get(to_id)
            rel = reliability_by_id.get(observation.id)
            req_sigma = required_by_id.get(observation.id)
            quantity = observation.values[0]

            records.append(
                {
                    "record_kind": "observation",
                    "geometry_type": "LineString",
                    "network_id": self.network.id,
                    "crs": crs,
                    "frame": self.frame.name,
                    "datum": self.datum.name,
                    "tolerance": tolerance,
                    "confidence": float(self.confidence),
                    "station_id": "",
                    "station_type": "",
                    "easting": None,
                    "northing": None,
                    "height": None,
                    "uncertainty": None,
                    "semi_major": None,
                    "semi_minor": None,
                    "orientation": None,
                    "observation_id": observation.id,
                    "observation_type": observation.type.name,
                    "from_station": from_id,
                    "from_type": (
                        from_st.station_type.name if from_st is not None else StationType.PLANNED.name
                    ),
                    "from_easting": fe,
                    "from_northing": fn,
                    "from_height": fh,
                    "from_uncertainty": float(fd.positional_uncertainty) if fd is not None else None,
                    "from_semi_major": float(fd.ellipse.semi_major) if fd is not None else None,
                    "from_semi_minor": float(fd.ellipse.semi_minor) if fd is not None else None,
                    "from_orientation": float(fd.ellipse.orientation) if fd is not None else None,
                    "to_station": to_id,
                    "to_type": (
                        to_st.station_type.name if to_st is not None else StationType.PLANNED.name
                    ),
                    "to_easting": te,
                    "to_northing": tn,
                    "to_height": th,
                    "to_uncertainty": float(td.positional_uncertainty) if td is not None else None,
                    "to_semi_major": float(td.ellipse.semi_major) if td is not None else None,
                    "to_semi_minor": float(td.ellipse.semi_minor) if td is not None else None,
                    "to_orientation": float(td.ellipse.orientation) if td is not None else None,
                    "unit": quantity.unit.value,
                    "value": float(quantity.value),
                    "sigma": float(quantity.std_dev),
                    "required_sigma": float(req_sigma) if req_sigma is not None else None,
                    "redundancy": float(rel.redundancy) if rel is not None else None,
                    "mdb": (
                        float(rel.minimal_detectable_bias)
                        if rel is not None and rel.minimal_detectable_bias is not None
                        else None
                    ),
                    "external_effect": (
                        float(rel.external_effect)
                        if rel is not None and rel.external_effect is not None
                        else None
                    ),
                    "cluster_id": observation.cluster_id or "",
                }
            )

        return records

    def to_geojson_dict(self) -> dict[str, object]:
        """Serialize the planned network as a single GeoJSON ``FeatureCollection`` containing both
        station ``Point`` features and observation ``LineString`` features."""
        crs = self.network.crs or self.crs or "EPSG:4326"
        features: list[dict[str, object]] = []
        for record in self.to_feature_records():
            props = {k: v for k, v in record.items() if k != "geometry_type"}
            if record.get("record_kind") == "station":
                east = _opt_float(record.get("easting"))
                if east is None:
                    east = _opt_float(record.get("from_easting")) or 0.0
                north = _opt_float(record.get("northing"))
                if north is None:
                    north = _opt_float(record.get("from_northing")) or 0.0
                geometry: dict[str, object] = {
                    "type": "Point",
                    "coordinates": [east, north],
                }
            else:
                fe = _opt_float(record.get("from_easting")) or 0.0
                fn = _opt_float(record.get("from_northing")) or 0.0
                te = _opt_float(record.get("to_easting"))
                if te is None:
                    te = fe
                tn = _opt_float(record.get("to_northing"))
                if tn is None:
                    tn = fn
                geometry = {
                    "type": "LineString",
                    "coordinates": [[fe, fn], [te, tn]],
                }
            features.append(
                {
                    "type": "Feature",
                    "geometry": geometry,
                    "properties": props,
                }
            )

        payload: dict[str, object] = {
            "type": "FeatureCollection",
            "name": self.network.name or self.network.id or "planned_network",
            "features": features,
        }
        if crs:
            payload["crs"] = {"type": "name", "properties": {"name": crs}}
        return payload

    @classmethod
    def from_geojson_dict(
        cls, payload: dict[str, object], *, default_crs: str = ""
    ) -> DesignSession:
        """Reconstruct a :class:`DesignSession` from a GeoJSON ``FeatureCollection``."""
        crs = default_crs
        crs_obj = payload.get("crs")
        if isinstance(crs_obj, dict):
            props = crs_obj.get("properties")
            if isinstance(props, dict) and props.get("name"):
                crs = str(props["name"])
        raw_features = payload.get("features")
        records: list[dict[str, object]] = []
        if isinstance(raw_features, list):
            for feature in raw_features:
                if not isinstance(feature, dict):
                    continue
                properties = feature.get("properties")
                record: dict[str, object] = (
                    dict(properties) if isinstance(properties, dict) else {}
                )
                geometry = feature.get("geometry")
                if isinstance(geometry, dict):
                    gtype = geometry.get("type")
                    coords = geometry.get("coordinates")
                    if (
                        gtype == "Point"
                        and isinstance(coords, (list, tuple))
                        and len(coords) >= 2
                    ):
                        x = _opt_float(coords[0])
                        y = _opt_float(coords[1])
                        if x is not None and y is not None:
                            record.setdefault("record_kind", "station")
                            record["easting"] = x
                            record["northing"] = y
                            record["from_easting"] = x
                            record["from_northing"] = y
                    elif (
                        gtype == "LineString"
                        and isinstance(coords, (list, tuple))
                        and len(coords) >= 2
                    ):
                        first_pt = coords[0]
                        last_pt = coords[-1]
                        if (
                            isinstance(first_pt, (list, tuple))
                            and len(first_pt) >= 2
                            and isinstance(last_pt, (list, tuple))
                            and len(last_pt) >= 2
                        ):
                            x1, y1 = _opt_float(first_pt[0]), _opt_float(first_pt[1])
                            x2, y2 = _opt_float(last_pt[0]), _opt_float(last_pt[1])
                            if x1 is not None and y1 is not None:
                                record["from_easting"] = x1
                                record["from_northing"] = y1
                            if x2 is not None and y2 is not None:
                                record["to_easting"] = x2
                                record["to_northing"] = y2
                records.append(record)
        return cls.from_feature_records(records, default_crs=crs)

    @classmethod
    def from_feature_records(
        cls, records: list[dict[str, object]], *, default_crs: str = ""
    ) -> DesignSession:
        """Reconstruct a :class:`DesignSession` from exported feature attribute records."""
        first = next(
            (r for r in records if r.get("crs") or r.get("frame") or r.get("network_id")),
            records[0] if records else {},
        )
        crs = str(first.get("crs") or default_crs or "")
        frame_name = str(first.get("frame") or "")
        frame = Frame[frame_name] if frame_name in Frame.__members__ else Frame.PLANE_2D
        datum_name = str(first.get("datum") or "")
        datum = (
            DatumDefinition[datum_name]
            if datum_name in DatumDefinition.__members__
            else DatumDefinition.INNER_CONSTRAINT
        )
        raw_tol = _opt_float(first.get("tolerance"))
        tolerance = raw_tol if raw_tol is not None and raw_tol > 0.0 else None
        raw_conf = _opt_float(first.get("confidence"))
        confidence = raw_conf if raw_conf is not None and 0.0 < raw_conf < 1.0 else 0.95

        session = cls(
            crs=crs,
            frame=frame,
            datum=datum,
            confidence=confidence,
            tolerance=tolerance,
        )
        network_id = str(first.get("network_id") or "")
        if network_id:
            session.network.id = network_id

        for record in records:
            kind = str(record.get("record_kind") or "")
            obs_type_name = str(record.get("observation_type") or "").strip()
            names_a_station = record.get("station_id") or record.get("from_station")
            if kind == "station" or (not obs_type_name and names_a_station):
                station_id = str(
                    record.get("station_id") or record.get("from_station") or ""
                ).strip()
                if not station_id:
                    continue
                easting = _opt_float(record.get("easting"))
                if easting is None:
                    easting = _opt_float(record.get("from_easting")) or 0.0
                northing = _opt_float(record.get("northing"))
                if northing is None:
                    northing = _opt_float(record.get("from_northing")) or 0.0
                height = _opt_float(record.get("height"))
                if height is None:
                    height = _opt_float(record.get("from_height")) or 0.0
                type_name = str(record.get("station_type") or record.get("from_type") or "")
                station_type = (
                    StationType[type_name]
                    if type_name in StationType.__members__
                    else StationType.PLANNED
                )
                session.network.stations[station_id] = Station(
                    id=station_id,
                    approx_position=session._position(easting, northing, height),
                    station_type=station_type,
                )

        for record in records:
            kind = str(record.get("record_kind") or "")
            if kind == "station":
                continue
            for prefix in ("from", "to"):
                station_id = str(record.get(f"{prefix}_station") or "").strip()
                if not station_id or station_id in session.network.stations:
                    continue
                easting = _opt_float(record.get(f"{prefix}_easting")) or 0.0
                northing = _opt_float(record.get(f"{prefix}_northing")) or 0.0
                height = _opt_float(record.get(f"{prefix}_height")) or 0.0
                type_name = str(record.get(f"{prefix}_type") or "")
                station_type = (
                    StationType[type_name]
                    if type_name in StationType.__members__
                    else StationType.PLANNED
                )
                session.network.add_station(
                    Station(
                        id=station_id,
                        approx_position=session._position(easting, northing, height),
                        station_type=station_type,
                    )
                )

        for record in records:
            kind = str(record.get("record_kind") or "observation")
            obs_type_name = str(record.get("observation_type") or "").strip()
            if kind == "station" or not obs_type_name:
                continue
            if obs_type_name not in ObservationType.__members__:
                continue
            from_id = str(record.get("from_station") or "").strip()
            to_id = str(record.get("to_station") or "").strip()
            if not from_id or not to_id or from_id == to_id:
                continue
            obs_type = ObservationType[obs_type_name]
            raw_sigma = _opt_float(record.get("sigma"))
            sigma = (
                raw_sigma
                if raw_sigma is not None and raw_sigma > 0.0
                else default_sigma_for(obs_type)
            )
            obs_id = str(record.get("observation_id") or "").strip()
            session.add_observation(
                obs_type,
                (from_id, to_id),
                sigma=sigma,
                observation_id=obs_id if obs_id not in session.network.observations else "",
            )

        session._undo.clear()
        session._redo.clear()
        return session

    # -- undo ------------------------------------------------------------

    @property
    def can_undo(self) -> bool:
        """Whether there is an edit to undo."""
        return bool(self._undo)

    @property
    def can_redo(self) -> bool:
        """Whether an undone edit can be made again."""
        return bool(self._redo)

    def undo(self) -> bool:
        """Undo the last edit.

        Returns whether there was one to undo.
        """
        if not self._undo:
            return False
        self._redo.append(self._capture())
        self._restore(self._undo.pop())
        return True

    def redo(self) -> bool:
        """Make the last undone edit again.

        Returns whether there was one to make.
        """
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
                    error=exc,
                    wording="design_not_evaluable",
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
                    context={
                        "station": worst.station_id,
                        "expected": localised(f"{worst.positional_uncertainty * 1000:.1f}"),
                        "required": localised(f"{self.tolerance * 1000:.1f}"),
                    },
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
                    context={"observation": result.observation_id},
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


def _station_coords(station: Station | None) -> tuple[float, float, float]:
    if station is None or station.approx_position is None:
        return 0.0, 0.0, 0.0
    east, north, up = station.approx_position.values
    return float(east.value), float(north.value), float(up.value)


def _opt_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        result = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return result if np.isfinite(result) else None
