# SPDX-License-Identifier: GPL-2.0-or-later
"""Networks, campaigns, GNSS sessions and the project container (FR-100).

``specs/04-data-model.md`` sections 1, 2.1 and 2.7.

A **campaign** is what was observed; a **network** is what is adjusted. They are
separate because one campaign's observations can feed several network
definitions -- a free and a constrained solution, a 2D and a 3D one -- and one
network can draw on several campaigns.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from geocomp.core.errors import DataError, ValidationError
from geocomp.core.models.epoch import Epoch
from geocomp.core.models.observation import Cluster, Observation
from geocomp.core.models.station import Station
from geocomp.core.uncertainty import Quantity
from geocomp.core.units import Unit

__all__ = ["Campaign", "GnssSession", "Network", "Project"]


@dataclass(frozen=True)
class GnssSession:
    """One continuous observation period by one receiver at one station (FR-350).

    ``antenna_height`` is a first-class field rather than metadata, and carries
    its measurement method: an unrecorded slant height is one of the most common
    sources of a systematic height error in GNSS work.
    """

    id: str
    station_id: str
    obs_file: str = ""
    nav_files: tuple[str, ...] = ()
    start: datetime | None = None
    end: datetime | None = None
    interval: float | None = None
    receiver: str = ""
    antenna: str = ""
    antenna_height: Quantity | None = None
    antenna_height_method: str = ""
    products: tuple[str, ...] = ()
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            raise DataError("gnss_session_without_id")
        if self.start and self.end and self.end < self.start:
            raise DataError(
                "gnss_session_ends_before_it_starts",
                session=self.id,
                start=self.start.isoformat(),
                end=self.end.isoformat(),
            )
        if self.antenna_height is not None and self.antenna_height.unit is not Unit.METRE:
            raise DataError(
                "antenna_height_unit",
                session=self.id,
                received=self.antenna_height.unit.name,
                expected="METRE",
            )

    @property
    def duration_seconds(self) -> float | None:
        if self.start is None or self.end is None:
            return None
        return (self.end - self.start).total_seconds()

    def overlaps(self, other: GnssSession) -> bool:
        """Whether two sessions observed simultaneously, and so could form a baseline."""
        if None in (self.start, self.end, other.start, other.end):
            return False
        return self.start < other.end and other.start < self.end  # type: ignore[operator]

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"id": self.id, "station_id": self.station_id}
        for key, value in (
            ("obs_file", self.obs_file),
            ("nav_files", list(self.nav_files) if self.nav_files else None),
            ("start", self.start.astimezone(UTC).isoformat() if self.start else None),
            ("end", self.end.astimezone(UTC).isoformat() if self.end else None),
            ("interval", self.interval),
            ("receiver", self.receiver),
            ("antenna", self.antenna),
            ("antenna_height", self.antenna_height.to_dict() if self.antenna_height else None),
            ("antenna_height_method", self.antenna_height_method),
            ("products", list(self.products) if self.products else None),
            ("meta", dict(self.meta) if self.meta else None),
        ):
            if value:
                payload[key] = value
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> GnssSession:
        height = payload.get("antenna_height")
        return cls(
            id=payload["id"],
            station_id=payload["station_id"],
            obs_file=payload.get("obs_file", ""),
            nav_files=tuple(payload.get("nav_files", ())),
            start=datetime.fromisoformat(payload["start"]) if payload.get("start") else None,
            end=datetime.fromisoformat(payload["end"]) if payload.get("end") else None,
            interval=payload.get("interval"),
            receiver=payload.get("receiver", ""),
            antenna=payload.get("antenna", ""),
            antenna_height=Quantity.from_dict(height) if height else None,
            antenna_height_method=payload.get("antenna_height_method", ""),
            products=tuple(payload.get("products", ())),
            meta=dict(payload.get("meta", {})),
        )


@dataclass(frozen=True)
class Campaign:
    """A field effort, bounded in time and by crew and instrument.

    Belongs to exactly one epoch, which is what makes a monitoring series
    comparable epoch by epoch.
    """

    id: str
    name: str = ""
    epoch: Epoch | None = None
    start: datetime | None = None
    end: datetime | None = None
    crew: str = ""
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"id": self.id}
        for key, value in (
            ("name", self.name),
            ("epoch", self.epoch.to_dict() if self.epoch else None),
            ("start", self.start.astimezone(UTC).isoformat() if self.start else None),
            ("end", self.end.astimezone(UTC).isoformat() if self.end else None),
            ("crew", self.crew),
            ("meta", dict(self.meta) if self.meta else None),
        ):
            if value:
                payload[key] = value
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> Campaign:
        epoch = payload.get("epoch")
        return cls(
            id=payload["id"],
            name=payload.get("name", ""),
            epoch=Epoch.from_dict(epoch) if epoch else None,
            start=datetime.fromisoformat(payload["start"]) if payload.get("start") else None,
            end=datetime.fromisoformat(payload["end"]) if payload.get("end") else None,
            crew=payload.get("crew", ""),
            meta=dict(payload.get("meta", {})),
        )


@dataclass
class Network:
    """A set of stations connected by observations, adjusted as one unit.

    Mutable, unlike most of the model: a network is assembled incrementally, and
    pre-analysis edits one interactively on the canvas (FR-272).

    Referential integrity is checked by :meth:`validate` rather than on every
    mutation, so a network can be built in any order.
    """

    id: str
    name: str = ""
    stations: dict[str, Station] = field(default_factory=dict)
    observations: dict[str, Observation] = field(default_factory=dict)
    clusters: dict[str, Cluster] = field(default_factory=dict)
    crs: str = ""
    epoch: Epoch | None = None
    meta: dict[str, Any] = field(default_factory=dict)

    # -- assembly --------------------------------------------------------

    def add_station(self, station: Station) -> None:
        if station.id in self.stations:
            raise DataError("duplicate_station", station=station.id, network=self.id)
        self.stations[station.id] = station

    def add_observation(self, observation: Observation) -> None:
        if observation.id in self.observations:
            raise DataError("duplicate_observation", observation=observation.id, network=self.id)
        self.observations[observation.id] = observation

    def add_cluster(self, cluster: Cluster) -> None:
        if cluster.id in self.clusters:
            raise DataError("duplicate_cluster", cluster=cluster.id, network=self.id)
        self.clusters[cluster.id] = cluster

    # -- queries ---------------------------------------------------------

    @property
    def active_observations(self) -> list[Observation]:
        return [o for o in self.observations.values() if o.is_active]

    def observations_at(self, station_id: str) -> list[Observation]:
        return [o for o in self.observations.values() if station_id in o.stations]

    def station_ids(self) -> set[str]:
        return set(self.stations)

    def constrained_stations(self) -> list[Station]:
        return [s for s in self.stations.values() if not s.constraint.is_free]

    # -- integrity -------------------------------------------------------

    def validate(self) -> list[str]:
        """Return referential problems, one message per problem.

        Returns a list rather than raising, because an importer must report
        every bad record rather than stopping at the first (FR-166). Callers
        that want a hard failure check the list.
        """
        problems: list[str] = []

        for observation in self.observations.values():
            for station_id in observation.stations:
                if station_id not in self.stations:
                    problems.append(
                        f"observation {observation.id} references unknown station {station_id}"
                    )
            if observation.cluster_id and observation.cluster_id not in self.clusters:
                problems.append(
                    f"observation {observation.id} references unknown cluster {observation.cluster_id}"
                )

        for cluster in self.clusters.values():
            for observation_id in cluster.observation_ids:
                if observation_id not in self.observations:
                    problems.append(
                        f"cluster {cluster.id} references unknown observation {observation_id}"
                    )

        return problems

    def require_valid(self) -> None:
        """Raise if :meth:`validate` found anything."""
        problems = self.validate()
        if problems:
            raise DataError("network_integrity", network=self.id, problems=problems)

    # -- serialisation ---------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": self.id,
            "stations": [s.to_dict() for s in self.stations.values()],
            "observations": [o.to_dict() for o in self.observations.values()],
            "clusters": [c.to_dict() for c in self.clusters.values()],
        }
        for key, value in (
            ("name", self.name),
            ("crs", self.crs),
            ("epoch", self.epoch.to_dict() if self.epoch else None),
            ("meta", dict(self.meta) if self.meta else None),
        ):
            if value:
                payload[key] = value
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> Network:
        epoch = payload.get("epoch")
        return cls(
            id=payload["id"],
            name=payload.get("name", ""),
            stations={s["id"]: Station.from_dict(s) for s in payload.get("stations", ())},
            observations={
                o["id"]: Observation.from_dict(o) for o in payload.get("observations", ())
            },
            clusters={c["id"]: Cluster.from_dict(c) for c in payload.get("clusters", ())},
            crs=payload.get("crs", ""),
            epoch=Epoch.from_dict(epoch) if epoch else None,
            meta=dict(payload.get("meta", {})),
        )


@dataclass
class Project:
    """The top-level container: one GeoPackage file or one PostGIS schema.

    ``schema_version`` exists because a monitoring project accumulates epochs
    over years and outlives several plugin releases (FR-133).
    """

    id: str
    name: str = ""
    description: str = ""
    default_crs: str = ""
    default_epoch: Epoch | None = None
    schema_version: int = 1
    created: datetime | None = None
    modified: datetime | None = None
    campaigns: dict[str, Campaign] = field(default_factory=dict)
    networks: dict[str, Network] = field(default_factory=dict)
    gnss_sessions: dict[str, GnssSession] = field(default_factory=dict)
    settings: dict[str, Any] = field(default_factory=dict)

    def add_network(self, network: Network) -> None:
        if network.id in self.networks:
            raise DataError("duplicate_network", network=network.id, project=self.id)
        self.networks[network.id] = network

    def add_campaign(self, campaign: Campaign) -> None:
        if campaign.id in self.campaigns:
            raise DataError("duplicate_campaign", campaign=campaign.id, project=self.id)
        self.campaigns[campaign.id] = campaign

    def add_gnss_session(self, session: GnssSession) -> None:
        if session.id in self.gnss_sessions:
            raise DataError("duplicate_gnss_session", session=session.id, project=self.id)
        self.gnss_sessions[session.id] = session

    def require_schema_version(self, supported: int) -> None:
        """Refuse a store written by a newer GeoComp (FR-133).

        Reading a schema you do not understand silently corrupts it, so a newer
        version is a hard refusal rather than a best-effort read.
        """
        if self.schema_version > supported:
            raise ValidationError(
                "schema_version_too_new",
                project=self.id,
                received=self.schema_version,
                supported=supported,
                expected="a project written by this version of GeoComp or older",
            )

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": self.id,
            "schema_version": self.schema_version,
            "campaigns": [c.to_dict() for c in self.campaigns.values()],
            "networks": [n.to_dict() for n in self.networks.values()],
            "gnss_sessions": [s.to_dict() for s in self.gnss_sessions.values()],
        }
        for key, value in (
            ("name", self.name),
            ("description", self.description),
            ("default_crs", self.default_crs),
            ("default_epoch", self.default_epoch.to_dict() if self.default_epoch else None),
            ("created", self.created.astimezone(UTC).isoformat() if self.created else None),
            ("modified", self.modified.astimezone(UTC).isoformat() if self.modified else None),
            ("settings", dict(self.settings) if self.settings else None),
        ):
            if value:
                payload[key] = value
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> Project:
        epoch = payload.get("default_epoch")
        return cls(
            id=payload["id"],
            name=payload.get("name", ""),
            description=payload.get("description", ""),
            default_crs=payload.get("default_crs", ""),
            default_epoch=Epoch.from_dict(epoch) if epoch else None,
            schema_version=int(payload.get("schema_version", 1)),
            created=datetime.fromisoformat(payload["created"]) if payload.get("created") else None,
            modified=datetime.fromisoformat(payload["modified"]) if payload.get("modified") else None,
            campaigns={c["id"]: Campaign.from_dict(c) for c in payload.get("campaigns", ())},
            networks={n["id"]: Network.from_dict(n) for n in payload.get("networks", ())},
            gnss_sessions={
                s["id"]: GnssSession.from_dict(s) for s in payload.get("gnss_sessions", ())
            },
            settings=dict(payload.get("settings", {})),
        )
