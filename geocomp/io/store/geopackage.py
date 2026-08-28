# SPDX-License-Identifier: GPL-2.0-or-later
"""The GeoPackage project store (FR-130, FR-133, FR-134, FR-135).

``specs/17-persistence-and-interoperability.md`` and ADR-0006: GeoPackage is the
default and canonical store, and PostGIS a mirror with an identical logical
schema.

**Written with the standard library's ``sqlite3``, not GDAL.** A GeoPackage *is*
a SQLite database with a documented set of metadata tables, so nothing here needs
a spatial library -- and the consequence is the point: the store is testable in
the fast tier, on every platform, with no QGIS and no GDAL. Eight of CI's nine
jobs have neither. A GDAL-backed store would have been shorter to write and
untestable in all eight, which for the one part of the system whose whole job is
*not losing data* is the wrong trade.

The file is a valid GeoPackage: the ``GPKG`` application id, the required
``gpkg_spatial_ref_sys`` rows, a ``gpkg_contents`` entry per table, and geometry
in the GeoPackage binary encoding. QGIS opens it and draws the network.

**Geometry is derived, and derived late.** ``specs/17`` section 2 rule 5: the
numeric coordinates are the record and the geometry is a view of them. So it is
computed on write from the authoritative JSON and never read back -- a reader
that took coordinates from the geometry column would be reading a rounded copy
of what sits beside it.
"""

from __future__ import annotations

import json
import sqlite3
import struct
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from geocomp.core.errors import DataError, ValidationError
from geocomp.core.models import (
    Campaign,
    Cluster,
    ClusterKind,
    CoordinateSystem,
    Epoch,
    GnssSession,
    Network,
    Observation,
    ObservationType,
    Position,
    Project,
    Solution,
    Station,
)
from geocomp.core.models.solution import (
    AdjustedStation,
    AdjustmentStatistics,
    DatumDefinition,
    ErrorEllipse,
    ObservationResult,
    Provenance,
    SolutionKind,
    TestResult,
)
from geocomp.core.uncertainty import Covariance, Strategy, UncertaintyMode
from geocomp.core.units import Unit
from geocomp.core.version import __version__
from geocomp.io.store.migrations import MigrationReport, check_version, migrate
from geocomp.io.store.schema import (
    SCHEMA,
    SCHEMA_VERSION,
    Table,
    ddl,
    index_ddl,
    quoted,
    view_ddl,
)

__all__ = ["GeoPackageStore", "open_store"]

#: ``GPKG`` as a big-endian integer, the GeoPackage application id.
APPLICATION_ID = 0x47504B47
#: GeoPackage 1.4.0, as the specification's ``user_version`` encoding.
USER_VERSION = 10400

#: Undefined cartesian, used for a levelling network that has no CRS. A
#: GeoPackage requires *some* srs_id, and claiming a real one would assert a
#: datum the heights do not belong to.
SRS_UNDEFINED_CARTESIAN = -1
SRS_UNDEFINED_GEOGRAPHIC = 0


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _dumps(value: Any) -> str | None:
    """Serialise a document, deterministically (NFR-007)."""
    if value is None:
        return None
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _loads(value: str | None) -> Any:
    return json.loads(value) if value else None


# -- geometry -------------------------------------------------------------


def _point_blob(easting: float, northing: float, srs_id: int) -> bytes:
    """A GeoPackage POINT: the standard binary header plus little-endian WKB."""
    header = struct.pack("<2sBBi", b"GP", 0, 0b00000001, srs_id)
    wkb = struct.pack("<BIdd", 1, 1, easting, northing)
    return header + wkb


def _line_blob(points: Sequence[tuple[float, float]], srs_id: int) -> bytes:
    header = struct.pack("<2sBBi", b"GP", 0, 0b00000001, srs_id)
    wkb = struct.pack("<BII", 1, 2, len(points))
    for easting, northing in points:
        wkb += struct.pack("<dd", easting, northing)
    return header + wkb


def _plan_of(position: dict[str, Any] | None) -> tuple[float, float] | None:
    """The first two components of a stored position, or ``None``.

    Deliberately blunt: for a projected position they are easting and northing,
    for a geodetic one longitude and latitude *in radians*, and a geometry drawn
    from radians is wrong. So a geodetic position is converted, and any other
    system draws nothing rather than drawing something misleading.
    """
    if not position:
        return None
    values = position.get("values") or []
    if len(values) < 2:
        return None
    first, second = float(values[0]["value"]), float(values[1]["value"])
    system = position.get("system")
    if system == CoordinateSystem.PROJECTED.name:
        return first, second
    if system == CoordinateSystem.GEODETIC.name:
        return float(np.degrees(second)), float(np.degrees(first))
    return None


# -- the store ------------------------------------------------------------


class GeoPackageStore:
    """A GeoComp project in one GeoPackage file.

    Used as a context manager. Writes happen in a transaction, so a failed save
    leaves the previous content intact rather than half of each.
    """

    def __init__(self, path: str | Path, connection: sqlite3.Connection) -> None:
        self.path = Path(path)
        self._connection = connection
        #: Set when opening migrated the store, so the caller can report what
        #: changed and where the backup went.
        self.migration: MigrationReport | None = None

    # -- lifecycle -------------------------------------------------------

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> GeoPackageStore:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    @property
    def connection(self) -> sqlite3.Connection:
        return self._connection

    # -- schema ----------------------------------------------------------

    @property
    def schema_version(self) -> int:
        row = self._connection.execute(
            'SELECT schema_version FROM "gc_project" LIMIT 1'
        ).fetchone()
        if row is None:
            raise DataError(
                "project_store_empty",
                path=str(self.path),
                expected="a store holding a project row",
            )
        return int(row[0])

    def tables(self) -> list[str]:
        rows = self._connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
        ).fetchall()
        return [row[0] for row in rows]

    # -- writing ---------------------------------------------------------

    def write(self, project: Project) -> None:
        """Write a whole project, replacing what is there.

        One transaction. A partially written project is worse than an unwritten
        one -- it looks like data.
        """
        with self._connection:
            for entry in reversed(SCHEMA):
                self._connection.execute(f"DELETE FROM {quoted(entry.name)}")
            self._write_project(project)
            self._write_settings(project.settings)
            for campaign in project.campaigns.values():
                self._write_campaign(campaign)
            for network in project.networks.values():
                self._write_network(network)
            for session in project.gnss_sessions.values():
                self._write_gnss_session(session)

    def write_solution(self, solution: Solution) -> None:
        """Add or replace one solution, with its provenance and results."""
        with self._connection:
            self._write_solution(solution)

    def _insert(self, name: str, values: dict[str, Any]) -> None:
        columns = ", ".join(quoted(key) for key in values)
        marks = ", ".join("?" for _ in values)
        self._connection.execute(
            f"INSERT OR REPLACE INTO {quoted(name)} ({columns}) VALUES ({marks})",
            tuple(values.values()),
        )

    def _write_project(self, project: Project) -> None:
        self._insert(
            "gc_project",
            {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "default_crs": project.default_crs,
                "default_epoch": _dumps(
                    project.default_epoch.to_dict() if project.default_epoch else None
                ),
                "schema_version": SCHEMA_VERSION,
                "created": project.created.astimezone(UTC).isoformat()
                if project.created
                else _now(),
                "modified": _now(),
                "geocomp_version": __version__,
            },
        )

    def _write_settings(self, settings: dict[str, Any]) -> None:
        for key, value in settings.items():
            self._insert("gc_settings", {"key": key, "value": _dumps(value)})

    def _write_epoch(self, epoch: Epoch | None) -> str | None:
        """Store an epoch and return its id, or ``None``.

        The id is derived from the content so the same epoch stored twice is one
        row, which keeps a round trip stable (NFR-007).
        """
        if epoch is None:
            return None
        identifier = f"epoch-{epoch.decimal_year:.6f}"
        self._insert(
            "gc_epoch",
            {
                "id": identifier,
                "decimal_year": epoch.decimal_year,
                "instant": epoch.instant.astimezone(UTC).isoformat()
                if epoch.instant
                else None,
                "label": epoch.label,
            },
        )
        return identifier

    def _write_campaign(self, campaign: Campaign) -> None:
        self._insert(
            "gc_campaign",
            {
                "id": campaign.id,
                "name": campaign.name,
                "epoch_id": self._write_epoch(campaign.epoch),
                "start": campaign.start.astimezone(UTC).isoformat()
                if campaign.start
                else None,
                "end": campaign.end.astimezone(UTC).isoformat() if campaign.end else None,
                "crew": campaign.crew,
                "meta": _dumps(dict(campaign.meta)) if campaign.meta else None,
            },
        )

    def _write_gnss_session(self, session: GnssSession) -> None:
        self._insert(
            "gc_gnss_session",
            {
                "id": session.id,
                "station_id": session.station_id,
                "obs_file": session.obs_file,
                "nav_files": _dumps(list(session.nav_files)) if session.nav_files else None,
                "start": session.start.astimezone(UTC).isoformat() if session.start else None,
                "end": session.end.astimezone(UTC).isoformat() if session.end else None,
                "interval": session.interval,
                "receiver": session.receiver,
                "antenna": session.antenna,
                "antenna_height": _dumps(
                    session.antenna_height.to_dict() if session.antenna_height else None
                ),
                "antenna_height_method": session.antenna_height_method,
                "products": _dumps(list(session.products)) if session.products else None,
                "meta": _dumps(dict(session.meta)) if session.meta else None,
            },
        )

    def _write_covariance(self, identifier: str, covariance: Covariance, kind: str) -> str:
        """Store a covariance as a matrix blob, exactly."""
        matrix = np.ascontiguousarray(covariance.matrix, dtype=">f8")
        self._insert(
            "gc_cluster",
            {
                "id": identifier,
                "kind": kind,
                "labels": _dumps(list(covariance.labels)),
                "units": _dumps([unit.name for unit in covariance.units]),
                "mode": covariance.mode.name,
                "strategies": _dumps(
                    sorted(strategy.name for strategy in covariance.strategies)
                )
                if covariance.strategies
                else None,
                "size": covariance.size,
                "matrix": matrix.tobytes(),
            },
        )
        return identifier

    def _write_network(self, network: Network) -> None:
        self._insert(
            "gc_network",
            {
                "id": network.id,
                "name": network.name,
                "crs": network.crs,
                "epoch": _dumps(network.epoch.to_dict() if network.epoch else None),
                "meta": _dumps(dict(network.meta)) if network.meta else None,
            },
        )
        srs_id = _srs_of(network.crs)

        for station in network.stations.values():
            self._write_station(station, srs_id)
            self._insert(
                "gc_network_member",
                {
                    "network_id": network.id,
                    "member_kind": "station",
                    "member_id": station.id,
                },
            )

        for cluster in network.clusters.values():
            self._write_covariance(cluster.id, cluster.covariance, cluster.kind.name)
            self._insert(
                "gc_network_member",
                {
                    "network_id": network.id,
                    "member_kind": "cluster",
                    "member_id": cluster.id,
                },
            )

        order = {
            observation_id: (cluster.id, index)
            for cluster in network.clusters.values()
            for index, observation_id in enumerate(cluster.observation_ids)
        }
        positions = {
            station.id: _plan_of(station.approx_position.to_dict())
            if station.approx_position
            else None
            for station in network.stations.values()
        }
        for observation in network.observations.values():
            self._write_observation(observation, order, positions, srs_id)
            self._insert(
                "gc_network_member",
                {
                    "network_id": network.id,
                    "member_kind": "observation",
                    "member_id": observation.id,
                },
            )

    def _write_station(self, station: Station, srs_id: int) -> None:
        position = station.approx_position.to_dict() if station.approx_position else None
        plan = _plan_of(position)
        self._insert(
            "gc_station",
            {
                "id": station.id,
                "name": station.name,
                "description": station.description,
                "station_type": station.station_type.name,
                "monitoring_role": station.monitoring_role.name
                if station.monitoring_role
                else None,
                "approx_position": _dumps(position),
                "constraint_spec": _dumps(station.constraint.to_dict()),
                "meta": _dumps(dict(station.meta)) if station.meta else None,
                "geom": _point_blob(plan[0], plan[1], srs_id) if plan else None,
            },
        )

    def _write_observation(
        self,
        observation: Observation,
        order: dict[str, tuple[str, int]],
        positions: dict[str, tuple[float, float] | None],
        srs_id: int,
    ) -> None:
        cluster_id, cluster_index = order.get(observation.id, (observation.cluster_id, None))
        drawn = [positions.get(name) for name in observation.stations]
        geometry = (
            _line_blob([point for point in drawn if point is not None], srs_id)
            if len([point for point in drawn if point is not None]) >= 2
            else None
        )
        self._insert(
            "gc_observation",
            {
                "id": observation.id,
                "type": observation.type.name,
                "stations": _dumps(list(observation.stations)),
                "station_from": observation.stations[0],
                "station_to": observation.stations[-1]
                if len(observation.stations) > 1
                else None,
                "values": _dumps([q.to_dict() for q in observation.values]),
                "epoch": _dumps(observation.epoch.to_dict() if observation.epoch else None),
                "setup_id": None,
                "instrument_id": None,
                "cluster_id": cluster_id,
                "cluster_index": cluster_index,
                "status": observation.status.name,
                "rejection": _dumps(
                    observation.rejection.to_dict() if observation.rejection else None
                ),
                "meta": _dumps(
                    {
                        **dict(observation.meta),
                        **(
                            {"setup_id": observation.setup_id}
                            if observation.setup_id
                            else {}
                        ),
                        **(
                            {"instrument_id": observation.instrument_id}
                            if observation.instrument_id
                            else {}
                        ),
                    }
                )
                if (observation.meta or observation.setup_id or observation.instrument_id)
                else None,
                "geom": geometry,
            },
        )

    def _write_provenance(self, provenance: Provenance | None, solution_id: str) -> str | None:
        if provenance is None:
            return None
        identifier = f"prov-{solution_id}"
        payload = provenance.to_dict()
        self._insert(
            "gc_provenance",
            {
                "id": identifier,
                "created": payload["created"],
                "source": payload.get("source", ""),
                "algorithm_id": payload.get("algorithm_id", ""),
                "parameters": _dumps(payload.get("parameters")),
                "engine": payload.get("engine", ""),
                "engine_version": payload.get("engine_version", ""),
                "command_line": payload.get("command_line", ""),
                "exit_code": payload.get("exit_code"),
                "input_ids": _dumps(payload.get("input_ids")),
                "input_digests": _dumps(payload.get("input_digests")),
                "geocomp_version": payload.get("geocomp_version", ""),
                "qgis_version": payload.get("qgis_version", ""),
                "uncertainty_mode": payload["uncertainty_mode"],
            },
        )
        return identifier

    def _write_solution(self, solution: Solution) -> None:
        provenance_id = self._write_provenance(solution.provenance, solution.id)
        covariance_id = None
        if solution.parameter_covariance is not None:
            covariance_id = self._write_covariance(
                f"cov-{solution.id}", solution.parameter_covariance, "SOLUTION"
            )

        self._insert(
            "gc_solution",
            {
                "id": solution.id,
                "network_id": solution.network_id,
                "kind": solution.kind.name,
                "crs": solution.crs,
                "epoch": _dumps(solution.epoch.to_dict()),
                "datum_definition": solution.datum_definition.name,
                "uncertainty_mode": solution.uncertainty_mode.name,
                "provenance_id": provenance_id,
                "parameter_covariance_id": covariance_id,
                "superseded_by": solution.superseded_by,
            },
        )

        srs_id = _srs_of(solution.crs)
        for station in solution.adjusted_stations:
            station_covariance = None
            if station.covariance is not None:
                station_covariance = self._write_covariance(
                    f"cov-{solution.id}-{station.station_id}",
                    station.covariance,
                    "ADJUSTED_STATION",
                )
            position = station.position.to_dict()
            plan = _plan_of(position)
            self._insert(
                "gc_adjusted_station",
                {
                    "solution_id": solution.id,
                    "station_id": station.station_id,
                    "position": _dumps(position),
                    "covariance_id": station_covariance,
                    "ellipse": _dumps(station.ellipse.to_dict() if station.ellipse else None),
                    "positional_uncertainty": station.positional_uncertainty,
                    "correction": _dumps(
                        list(station.correction) if station.correction else None
                    ),
                    "geom": _point_blob(plan[0], plan[1], srs_id) if plan else None,
                },
            )

        for row_index, result in enumerate(solution.observation_results):
            self._insert(
                "gc_observation_result",
                {
                    "solution_id": solution.id,
                    "row_index": row_index,
                    "observation_id": result.observation_id,
                    "residual": result.residual,
                    "standardised_residual": result.standardised_residual,
                    "redundancy": result.redundancy,
                    "minimal_detectable_bias": result.minimal_detectable_bias,
                    "external_reliability": result.external_reliability,
                    "adjusted_value": result.adjusted_value,
                    # Derived, and stored anyway: "which observations could not
                    # be checked at all" is the query a reader most wants to run
                    # against a stored solution, and recomputing a property in
                    # SQL is not possible. The authority is still the redundancy
                    # number beside it.
                    "is_uncheckable": int(result.is_uncheckable),
                    "w_test": _dumps(result.w_test.to_dict() if result.w_test else None),
                },
            )

        statistics = solution.statistics
        self._insert(
            "gc_statistics",
            {
                "solution_id": solution.id,
                "variance_factor_apriori": statistics.variance_factor_apriori,
                "variance_factor_aposteriori": statistics.variance_factor_aposteriori,
                "degrees_of_freedom": statistics.degrees_of_freedom,
                "n_observations": statistics.n_observations,
                "n_parameters": statistics.n_parameters,
                "n_constraints": statistics.n_constraints,
                "iterations": statistics.iterations,
                "max_correction": statistics.max_correction,
                "condition_number": statistics.condition_number,
                "converged": int(statistics.converged),
                "global_test": _dumps(
                    statistics.global_test.to_dict() if statistics.global_test else None
                ),
            },
        )

    # -- deletion and superseding (FR-135) --------------------------------

    def delete_observation(self, observation_id: str) -> None:
        """Delete one observation, unless a stored solution used it.

        The refusal comes from the database -- ``gc_observation_result`` holds a
        restricting reference to ``gc_observation`` -- and this method turns it
        into a message that names the solutions rather than an integrity error
        with a column name in it (NFR-006).
        """
        users = self.solutions_using(observation_id)
        if users:
            raise ValidationError(
                "observation_has_results",
                observation=observation_id,
                received=users,
                expected=(
                    "an observation no stored solution was computed from. "
                    "Supersede those solutions first, or keep the observation: "
                    "GeoComp does not delete what a result depends on (FR-135)"
                ),
            )
        with self._connection:
            self._connection.execute(
                'DELETE FROM "gc_network_member" WHERE member_kind = ? AND member_id = ?',
                ("observation", observation_id),
            )
            self._connection.execute(
                'DELETE FROM "gc_observation" WHERE id = ?', (observation_id,)
            )

    def solutions_using(self, observation_id: str) -> list[str]:
        """Which stored solutions were computed from this observation."""
        rows = self._connection.execute(
            'SELECT DISTINCT solution_id FROM "gc_observation_result" '
            "WHERE observation_id = ? ORDER BY solution_id",
            (observation_id,),
        ).fetchall()
        return [row[0] for row in rows]

    def supersede_solution(self, old_id: str, new_id: str) -> None:
        """Mark one solution as replaced by another.

        The mechanism FR-135 names. Superseding **keeps** the old solution and
        everything it was computed from: a superseded solution is still the
        record of what was believed at the time, which is exactly what a
        monitoring series is made of.
        """
        for identifier in (old_id, new_id):
            if not self._rows("gc_solution", "id = ?", (identifier,)):
                raise ValidationError(
                    "unknown_solution",
                    solution=identifier,
                    expected="a solution stored in this project",
                )
        if old_id == new_id:
            raise ValidationError(
                "solution_supersedes_itself",
                solution=old_id,
                expected="two different solutions",
            )
        with self._connection:
            self._connection.execute(
                'UPDATE "gc_solution" SET superseded_by = ? WHERE id = ?', (new_id, old_id)
            )

    def delete_solution(self, solution_id: str) -> None:
        """Delete a solution and its results -- and nothing it was computed from.

        The observations, stations and networks stay. That is the whole of
        FR-135: a solution is a conclusion, and deleting a conclusion must not
        delete the evidence.
        """
        if not self._rows("gc_solution", "id = ?", (solution_id,)):
            raise ValidationError(
                "unknown_solution",
                solution=solution_id,
                expected="a solution stored in this project",
            )
        with self._connection:
            for name in (
                "gc_observation_result",
                "gc_adjusted_station",
                "gc_statistics",
            ):
                self._connection.execute(
                    f"DELETE FROM {quoted(name)} WHERE solution_id = ?", (solution_id,)
                )
            self._connection.execute(
                'UPDATE "gc_solution" SET superseded_by = NULL WHERE superseded_by = ?',
                (solution_id,),
            )
            self._connection.execute(
                'DELETE FROM "gc_solution" WHERE id = ?', (solution_id,)
            )

    # -- reading ---------------------------------------------------------

    def read(self) -> Project:
        """Read the whole project back."""
        row = self._row("gc_project")
        if row is None:
            raise DataError(
                "project_store_empty",
                path=str(self.path),
                expected="a store holding a project row",
            )

        project = Project(
            id=row["id"],
            name=row["name"] or "",
            description=row["description"] or "",
            default_crs=row["default_crs"] or "",
            default_epoch=Epoch.from_dict(_loads(row["default_epoch"]))
            if row["default_epoch"]
            else None,
            schema_version=int(row["schema_version"]),
            created=datetime.fromisoformat(row["created"]) if row["created"] else None,
            modified=datetime.fromisoformat(row["modified"]) if row["modified"] else None,
            settings={
                entry["key"]: _loads(entry["value"])
                for entry in self._rows("gc_settings")
            },
        )

        for entry in self._rows("gc_campaign"):
            project.add_campaign(self._read_campaign(entry))
        for entry in self._rows("gc_network"):
            project.add_network(self._read_network(entry))
        for entry in self._rows("gc_gnss_session"):
            project.add_gnss_session(self._read_gnss_session(entry))
        return project

    def read_solutions(self) -> list[Solution]:
        return [self._read_solution(row) for row in self._rows("gc_solution")]

    def _row(self, name: str) -> sqlite3.Row | None:
        return self._connection.execute(f"SELECT * FROM {quoted(name)} LIMIT 1").fetchone()

    def _rows(self, name: str, where: str = "", parameters: Sequence[Any] = ()) -> list:
        clause = f" WHERE {where}" if where else ""
        return list(
            self._connection.execute(
                f"SELECT * FROM {quoted(name)}{clause}", tuple(parameters)
            ).fetchall()
        )

    def _read_campaign(self, row) -> Campaign:
        epoch = None
        if row["epoch_id"]:
            found = self._rows("gc_epoch", "id = ?", (row["epoch_id"],))
            if found:
                epoch = Epoch(
                    decimal_year=float(found[0]["decimal_year"]),
                    instant=datetime.fromisoformat(found[0]["instant"])
                    if found[0]["instant"]
                    else None,
                    label=found[0]["label"] or "",
                )
        return Campaign(
            id=row["id"],
            name=row["name"] or "",
            epoch=epoch,
            start=datetime.fromisoformat(row["start"]) if row["start"] else None,
            end=datetime.fromisoformat(row["end"]) if row["end"] else None,
            crew=row["crew"] or "",
            meta=_loads(row["meta"]) or {},
        )

    def _read_gnss_session(self, row) -> GnssSession:
        from geocomp.core.uncertainty import Quantity

        height = _loads(row["antenna_height"])
        return GnssSession(
            id=row["id"],
            station_id=row["station_id"] or "",
            obs_file=row["obs_file"] or "",
            nav_files=tuple(_loads(row["nav_files"]) or ()),
            start=datetime.fromisoformat(row["start"]) if row["start"] else None,
            end=datetime.fromisoformat(row["end"]) if row["end"] else None,
            interval=row["interval"],
            receiver=row["receiver"] or "",
            antenna=row["antenna"] or "",
            antenna_height=Quantity.from_dict(height) if height else None,
            antenna_height_method=row["antenna_height_method"] or "",
            products=tuple(_loads(row["products"]) or ()),
            meta=_loads(row["meta"]) or {},
        )

    def _read_covariance(self, identifier: str | None) -> Covariance | None:
        if not identifier:
            return None
        found = self._rows("gc_cluster", "id = ?", (identifier,))
        if not found:
            return None
        row = found[0]
        size = int(row["size"])
        matrix = np.frombuffer(row["matrix"], dtype=">f8").reshape(size, size)
        strategies = _loads(row["strategies"]) or []
        return Covariance(
            matrix=np.array(matrix, dtype=float),
            labels=tuple(_loads(row["labels"])),
            units=tuple(Unit[name] for name in _loads(row["units"])),
            mode=UncertaintyMode[row["mode"]],
            strategies=frozenset(Strategy[name] for name in strategies),
        )

    def _read_network(self, row) -> Network:
        network = Network(
            id=row["id"],
            name=row["name"] or "",
            crs=row["crs"] or "",
            epoch=Epoch.from_dict(_loads(row["epoch"])) if row["epoch"] else None,
            meta=_loads(row["meta"]) or {},
        )
        members = self._rows("gc_network_member", "network_id = ?", (row["id"],))
        wanted = {
            kind: {entry["member_id"] for entry in members if entry["member_kind"] == kind}
            for kind in ("station", "cluster", "observation")
        }

        for entry in self._rows("gc_station"):
            if entry["id"] in wanted["station"]:
                network.add_station(self._read_station(entry))

        for entry in self._rows("gc_cluster"):
            if entry["id"] not in wanted["cluster"]:
                continue
            covariance = self._read_covariance(entry["id"])
            member_rows = self._rows(
                "gc_observation",
                "cluster_id = ? ORDER BY cluster_index",
                (entry["id"],),
            )
            network.add_cluster(
                Cluster(
                    id=entry["id"],
                    kind=ClusterKind[entry["kind"]],
                    observation_ids=tuple(member["id"] for member in member_rows),
                    covariance=covariance,
                )
            )

        for entry in self._rows("gc_observation"):
            if entry["id"] in wanted["observation"]:
                network.add_observation(self._read_observation(entry))
        return network

    def _read_station(self, row) -> Station:
        from geocomp.core.models import ConstraintSpec, MonitoringRole, StationType

        position = _loads(row["approx_position"])
        return Station(
            id=row["id"],
            name=row["name"] or "",
            description=row["description"] or "",
            approx_position=Position.from_dict(position) if position else None,
            constraint=ConstraintSpec.from_dict(_loads(row["constraint_spec"])),
            station_type=StationType[row["station_type"]],
            monitoring_role=MonitoringRole[row["monitoring_role"]]
            if row["monitoring_role"]
            else None,
            meta=_loads(row["meta"]) or {},
        )

    def _read_observation(self, row) -> Observation:
        from geocomp.core.models.observation import ObservationStatus, RejectionRecord
        from geocomp.core.uncertainty import Quantity

        meta = _loads(row["meta"]) or {}
        setup_id = meta.pop("setup_id", None)
        instrument_id = meta.pop("instrument_id", None)
        rejection = _loads(row["rejection"])
        return Observation(
            id=row["id"],
            type=ObservationType[row["type"]],
            stations=tuple(_loads(row["stations"])),
            values=tuple(Quantity.from_dict(value) for value in _loads(row["values"])),
            epoch=Epoch.from_dict(_loads(row["epoch"])) if row["epoch"] else None,
            setup_id=setup_id,
            instrument_id=instrument_id,
            cluster_id=row["cluster_id"],
            status=ObservationStatus[row["status"]],
            rejection=RejectionRecord.from_dict(rejection) if rejection else None,
            meta=meta,
        )

    def _read_solution(self, row) -> Solution:
        provenance = None
        if row["provenance_id"]:
            found = self._rows("gc_provenance", "id = ?", (row["provenance_id"],))
            if found:
                entry = found[0]
                provenance = Provenance.from_dict(
                    {
                        "created": entry["created"],
                        "source": entry["source"] or "",
                        "algorithm_id": entry["algorithm_id"] or "",
                        "parameters": _loads(entry["parameters"]) or {},
                        "engine": entry["engine"] or "",
                        "engine_version": entry["engine_version"] or "",
                        "command_line": entry["command_line"] or "",
                        "exit_code": entry["exit_code"],
                        "input_ids": _loads(entry["input_ids"]) or [],
                        "input_digests": _loads(entry["input_digests"]) or {},
                        "geocomp_version": entry["geocomp_version"] or "",
                        "qgis_version": entry["qgis_version"] or "",
                        "uncertainty_mode": entry["uncertainty_mode"],
                    }
                )

        stations = tuple(
            AdjustedStation(
                station_id=entry["station_id"],
                position=Position.from_dict(_loads(entry["position"])),
                covariance=self._read_covariance(entry["covariance_id"]),
                ellipse=ErrorEllipse.from_dict(_loads(entry["ellipse"]))
                if entry["ellipse"]
                else None,
                positional_uncertainty=entry["positional_uncertainty"],
                correction=tuple(_loads(entry["correction"]))
                if entry["correction"]
                else None,
            )
            for entry in self._rows(
                "gc_adjusted_station", "solution_id = ? ORDER BY station_id", (row["id"],)
            )
        )

        results = tuple(
            ObservationResult(
                observation_id=entry["observation_id"],
                residual=entry["residual"],
                standardised_residual=entry["standardised_residual"],
                redundancy=entry["redundancy"],
                w_test=TestResult.from_dict(_loads(entry["w_test"]))
                if entry["w_test"]
                else None,
                minimal_detectable_bias=entry["minimal_detectable_bias"],
                external_reliability=entry["external_reliability"],
                adjusted_value=entry["adjusted_value"],
            )
            for entry in self._rows(
                "gc_observation_result",
                "solution_id = ? ORDER BY row_index",
                (row["id"],),
            )
        )

        statistics = AdjustmentStatistics()
        found = self._rows("gc_statistics", "solution_id = ?", (row["id"],))
        if found:
            entry = found[0]
            global_test = _loads(entry["global_test"])
            statistics = AdjustmentStatistics(
                variance_factor_apriori=entry["variance_factor_apriori"],
                variance_factor_aposteriori=entry["variance_factor_aposteriori"],
                degrees_of_freedom=entry["degrees_of_freedom"],
                n_observations=entry["n_observations"],
                n_parameters=entry["n_parameters"],
                n_constraints=entry["n_constraints"],
                iterations=entry["iterations"],
                max_correction=entry["max_correction"],
                condition_number=entry["condition_number"],
                converged=bool(entry["converged"]),
                global_test=TestResult.from_dict(global_test) if global_test else None,
            )

        return Solution(
            id=row["id"],
            network_id=row["network_id"] or "",
            kind=SolutionKind[row["kind"]],
            crs=row["crs"],
            epoch=Epoch.from_dict(_loads(row["epoch"])),
            datum_definition=DatumDefinition[row["datum_definition"]],
            adjusted_stations=stations,
            parameter_covariance=self._read_covariance(row["parameter_covariance_id"]),
            observation_results=results,
            statistics=statistics,
            uncertainty_mode=UncertaintyMode[row["uncertainty_mode"]],
            provenance=provenance,
            superseded_by=row["superseded_by"],
        )


def _srs_of(crs: str) -> int:
    """The GeoPackage srs_id for a CRS string.

    Only ``EPSG:nnnn`` is recognised. Anything else -- including the ``LOCAL``
    a levelling network carries -- maps to undefined cartesian, which is what a
    GeoPackage is for: an honest "no spatial reference" rather than a borrowed
    one that would claim a datum the coordinates do not belong to.
    """
    authority, _, code = crs.partition(":")
    if authority.upper() == "EPSG" and code.isdigit():
        return int(code)
    return SRS_UNDEFINED_CARTESIAN


def _initialise(connection: sqlite3.Connection) -> None:
    """Make an empty SQLite file into a valid, empty GeoPackage."""
    connection.execute(f"PRAGMA application_id = {APPLICATION_ID}")
    connection.execute(f"PRAGMA user_version = {USER_VERSION}")
    connection.execute("PRAGMA foreign_keys = ON")

    connection.execute(
        """
        CREATE TABLE gpkg_spatial_ref_sys (
            srs_name TEXT NOT NULL,
            srs_id INTEGER NOT NULL PRIMARY KEY,
            organization TEXT NOT NULL,
            organization_coordsys_id INTEGER NOT NULL,
            definition TEXT NOT NULL,
            description TEXT
        )
        """
    )
    connection.executemany(
        "INSERT INTO gpkg_spatial_ref_sys VALUES (?, ?, ?, ?, ?, ?)",
        [
            ("Undefined cartesian SRS", -1, "NONE", -1, "undefined", None),
            ("Undefined geographic SRS", 0, "NONE", 0, "undefined", None),
            (
                "WGS 84 geodetic",
                4326,
                "EPSG",
                4326,
                'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],'
                'PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]]',
                None,
            ),
        ],
    )
    connection.execute(
        """
        CREATE TABLE gpkg_contents (
            table_name TEXT NOT NULL PRIMARY KEY,
            data_type TEXT NOT NULL,
            identifier TEXT UNIQUE,
            description TEXT DEFAULT '',
            last_change TEXT NOT NULL,
            min_x DOUBLE, min_y DOUBLE, max_x DOUBLE, max_y DOUBLE,
            srs_id INTEGER,
            CONSTRAINT fk_gc_r_srs_id FOREIGN KEY (srs_id)
                REFERENCES gpkg_spatial_ref_sys(srs_id)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE gpkg_geometry_columns (
            table_name TEXT NOT NULL,
            column_name TEXT NOT NULL,
            geometry_type_name TEXT NOT NULL,
            srs_id INTEGER NOT NULL,
            z TINYINT NOT NULL,
            m TINYINT NOT NULL,
            CONSTRAINT pk_geom_cols PRIMARY KEY (table_name, column_name)
        )
        """
    )

    for entry in SCHEMA:
        connection.execute(ddl(entry))
        for statement in index_ddl(entry):
            connection.execute(statement)
        _register(connection, entry)

    for statement in view_ddl([kind.name for kind in ObservationType]):
        connection.execute(statement)


def _register(connection: sqlite3.Connection, entry: Table) -> None:
    """Announce a table in the GeoPackage metadata."""
    data_type = "features" if entry.geometry is not None else "attributes"
    connection.execute(
        "INSERT INTO gpkg_contents "
        "(table_name, data_type, identifier, description, last_change, srs_id) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (
            entry.name,
            data_type,
            entry.name,
            entry.note.split(".")[0] if entry.note else "",
            _now(),
            SRS_UNDEFINED_CARTESIAN if entry.geometry is not None else None,
        ),
    )
    if entry.geometry is not None:
        connection.execute(
            "INSERT INTO gpkg_geometry_columns VALUES (?, ?, ?, ?, ?, ?)",
            (entry.name, "geom", entry.geometry.value, SRS_UNDEFINED_CARTESIAN, 0, 0),
        )


def open_store(
    path: str | Path, *, create: bool = False, migrate_older: bool = False
) -> GeoPackageStore:
    """Open a GeoComp GeoPackage, optionally creating or migrating it.

    Args:
        path: The file.
        create: Create it when it does not exist. Never overwrites: opening an
            existing file always opens it.
        migrate_older: Bring an older schema forward, after a backup. Off by
            default because migrating is a decision the user makes, and a
            library that silently rewrote the file it was asked to read would be
            taking it for them.

    Raises:
        DataError: ``project_store_not_found`` when the file is absent and
            *create* is false; ``project_store_not_geocomp`` when the file is a
            database but not one of ours; ``store_schema_too_new`` when it was
            written by a newer GeoComp; ``store_schema_older`` when it needs a
            migration that was not asked for.
    """
    target = Path(path)
    exists = target.is_file()
    if not exists and not create:
        raise DataError(
            "project_store_not_found",
            path=str(target),
            expected="an existing GeoComp GeoPackage, or create=True",
        )

    connection = sqlite3.connect(target)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    if not exists:
        with connection:
            _initialise(connection)
        return GeoPackageStore(target, connection)

    names = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    missing = sorted({entry.name for entry in SCHEMA} - names)
    if missing:
        connection.close()
        raise DataError(
            "project_store_not_geocomp",
            path=str(target),
            received=sorted(names)[:10],
            expected=f"a GeoComp store; these tables are missing: {', '.join(missing[:5])}",
        )

    store = GeoPackageStore(target, connection)
    found = store.schema_version
    try:
        check_version(found, path=target)
    except DataError:
        connection.close()
        raise

    if found < SCHEMA_VERSION:
        if not migrate_older:
            connection.close()
            raise DataError(
                "store_schema_older",
                path=str(target),
                received=found,
                supported=SCHEMA_VERSION,
                expected=(
                    "an up-to-date store, or migrate_older=True to bring it forward. "
                    "A backup is taken first and the caller is told what changed"
                ),
            )
        store.migration = migrate(connection, target, found)
    return store
