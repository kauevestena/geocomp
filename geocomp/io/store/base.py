# SPDX-License-Identifier: GPL-2.0-or-later
"""The project store's logic, once, for both backends (FR-130 to FR-135, phase P11).

``specs/17-persistence-and-interoperability.md`` and ADR-0006: GeoPackage is the
default and canonical store, PostGIS a mirror with an identical logical schema.
**This is where "identical" is made true rather than promised.** Everything a
store does with a project -- what a network becomes in rows, what a solution
becomes, what may be deleted (FR-135), how a save detects that someone else
saved first -- is written here once, and a backend supplies only what differs:

* how a statement is executed and a parameter is marked,
* how a row is inserted or replaced,
* how a geometry is encoded (a GeoPackage blob, or PostGIS EWKB),
* how a transaction is opened -- and, for a write, locked.

Before P11 this was the GeoPackage store's own code. Moving it rather than
copying it is the point: a PostGIS store with its own copy of the domain logic
would be a second implementation of the one thing that must not differ.

**A save detects a concurrent save** (``specs/17`` section 4). ``gc_project``
carries a ``revision``; a store remembers the revision it last read or wrote,
and every write -- under the backend's write lock -- compares it with the one
in the store. When they differ, someone else saved in between, and the write is
refused rather than allowed to overwrite what they saved.

**Order is recorded, not inherited.** A network's stations and observations
come back in the order they were written because ``gc_network_member.ordinal``
says so (schema 4); before P11 that order was SQLite's row order, which
PostgreSQL does not keep. Every other collection is read in primary-key order,
the same on both backends.
"""

from __future__ import annotations

import itertools
import json
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from datetime import UTC, datetime
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
from geocomp.core.uncertainty import Covariance, Quantity, Strategy, UncertaintyMode
from geocomp.core.units import Unit
from geocomp.core.version import __version__
from geocomp.io.store.migrations import MigrationReport
from geocomp.io.store.schema import SCHEMA, SCHEMA_VERSION, Table, quoted, table

__all__ = ["SRS_UNDEFINED_CARTESIAN", "ProjectStore", "srs_of"]

#: Undefined cartesian, used for a levelling network that has no CRS. A
#: GeoPackage requires *some* srs_id, and claiming a real one would assert a
#: datum the heights do not belong to. PostGIS has no -1; it stores 0.
SRS_UNDEFINED_CARTESIAN = -1


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _dumps(value: Any) -> str | None:
    """Serialise a document, deterministically (NFR-007)."""
    if value is None:
        return None
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _loads(value: str | None) -> Any:
    return json.loads(value) if value else None


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


def srs_of(crs: str) -> int:
    """The spatial reference id for a CRS string.

    Only ``EPSG:nnnn`` is recognised. Anything else -- including the ``LOCAL``
    a levelling network carries -- maps to undefined cartesian, which is what a
    GeoPackage is for: an honest "no spatial reference" rather than a borrowed
    one that would claim a datum the coordinates do not belong to.
    """
    authority, _, code = crs.partition(":")
    if authority.upper() == "EPSG" and code.isdigit():
        return int(code)
    return SRS_UNDEFINED_CARTESIAN


# -- the store ------------------------------------------------------------


class ProjectStore:
    """A GeoComp project in a store: what both backends share.

    Used as a context manager. Writes happen in a transaction, so a failed save
    leaves the previous content intact rather than half of each.

    Subclasses implement the hooks in the first section below; nothing else.
    """

    #: ``"sqlite"`` or ``"postgres"``, as :mod:`geocomp.io.store.schema` names them.
    backend = ""

    def __init__(self, location: str) -> None:
        #: How the store is named in messages: a file path, or a connection and schema.
        self.location = location
        #: Set when opening migrated the store, so the caller can report what
        #: changed and where the backup went.
        self.migration: MigrationReport | None = None
        #: The revision this store object last read or wrote (schema 4).
        self._revision = 0
        self._next_revision = 0
        self._depth = 0

    # -- what a backend supplies -------------------------------------------

    def close(self) -> None:
        raise NotImplementedError

    def tables(self) -> list[str]:
        raise NotImplementedError

    def _execute(self, sql: str, parameters: Sequence[Any] = ()) -> Any:
        """Run one statement; ``?`` marks a parameter in every backend's SQL."""
        raise NotImplementedError

    def _begin(self, write: bool) -> None:
        """Open a transaction; a write one takes the backend's write lock."""
        raise NotImplementedError

    def _commit(self) -> None:
        raise NotImplementedError

    def _rollback(self) -> None:
        raise NotImplementedError

    def _marker(self, column: str) -> str:
        """The parameter marker for *column*: ``?``, or ``?`` with a cast."""
        return "?"

    def _upsert_sql(self, entry: Table, columns: Sequence[str]) -> str:
        """Insert a row, or update the one with its key **in place**.

        One statement for both backends -- SQLite has had ``ON CONFLICT ... DO
        UPDATE`` since 3.24. **Not** SQLite's ``INSERT OR REPLACE``, which the
        store used before P11: it *deletes* the conflicting row and inserts a
        new one, and deleting a row that a stored result references is exactly
        what the restricting foreign keys refuse (FR-135). So re-saving a
        solution that was already stored failed on its own provenance, and a
        replace that did succeed set to NULL every ``superseded_by`` pointing at
        the replaced row. Every non-key column is set, so a column not given
        becomes NULL, as it would in a fresh row.
        """
        names = ", ".join(quoted(column) for column in columns)
        marks = ", ".join(self._marker(column) for column in columns)
        keys = ", ".join(quoted(key) for key in entry.primary_key)
        others = [column.name for column in entry.columns if not column.primary_key]
        if entry.geometry is not None:
            others.append("geom")
        action = (
            "DO UPDATE SET "
            + ", ".join(f"{quoted(name)} = excluded.{quoted(name)}" for name in others)
            if others
            else "DO NOTHING"
        )
        return (
            f"INSERT INTO {quoted(entry.name)} ({names}) VALUES ({marks}) "
            f"ON CONFLICT ({keys}) {action}"
        )

    def _adapt(self, entry: Table, column: str, value: Any) -> Any:
        """A Python value as this backend stores it in *column*."""
        return value

    def _point(self, easting: float, northing: float, srs_id: int) -> Any:
        raise NotImplementedError

    def _line(self, points: Sequence[tuple[float, float]], srs_id: int) -> Any:
        raise NotImplementedError

    # -- lifecycle -------------------------------------------------------

    def __enter__(self) -> ProjectStore:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # -- transactions and the revision -----------------------------------

    @contextmanager
    def _transaction(self, *, write: bool) -> Iterator[None]:
        """One transaction, however deeply the store's own methods nest."""
        if self._depth:
            self._depth += 1
            try:
                yield
            finally:
                self._depth -= 1
            return
        self._begin(write)
        self._depth = 1
        try:
            yield
        except BaseException:
            self._depth = 0
            self._rollback()
            raise
        self._depth = 0
        self._commit()

    @contextmanager
    def atomic(self) -> Iterator[None]:
        """Several writes as one: all of them commit, or none does.

        Each save is a transaction already. This is for a caller making several
        -- a project, its network and a solution -- which a cancelled or failed
        run must not leave half made (``specs/17`` criterion 6). An exception
        inside, :class:`~geocomp.core.cancellation.Cancelled` included, rolls
        every one of them back.
        """
        with self._writing():
            yield

    @contextmanager
    def _writing(self) -> Iterator[None]:
        """A write, refused if someone else saved since this store last looked.

        The backend's write lock is taken first, so between the comparison and
        the commit no other save can land; the revision is then advanced, so the
        next save by anyone else sees that this one happened.
        """
        if self._depth:
            with self._transaction(write=True):
                yield
            return
        with self._transaction(write=True):
            current = self._stored_revision()
            if current != self._revision:
                raise DataError(
                    "store_modified_concurrently",
                    path=self.location,
                    received=current,
                    seen=self._revision,
                    expected=(
                        f"revision {self._revision}, which this store read; someone else "
                        "saved since. Open the project again and redo the change, so "
                        "their save is not overwritten"
                    ),
                )
            self._next_revision = current + 1
            yield
            self._execute(
                'UPDATE "gc_project" SET "revision" = ?, "modified" = ?',
                (self._next_revision, _now()),
            )
        self._revision = self._next_revision

    def _stored_revision(self) -> int:
        row = self._execute('SELECT "revision" FROM "gc_project" LIMIT 1').fetchone()
        return int(row[0]) if row is not None and row[0] is not None else 0

    @property
    def revision(self) -> int:
        """The revision this store object last read or wrote."""
        return self._revision

    def refresh(self) -> None:
        """Accept the store's current revision as seen, without reading the project.

        For a caller that has just opened the store. Anything that read the
        project earlier and means to write it back must not call this: the
        refusal it would silence is the one that protects someone else's save.
        """
        with self._transaction(write=False):
            self._revision = self._stored_revision()

    # -- schema ----------------------------------------------------------

    @property
    def schema_version(self) -> int:
        row = self._execute('SELECT schema_version FROM "gc_project" LIMIT 1').fetchone()
        if row is None:
            raise DataError(
                "project_store_empty",
                path=self.location,
                expected="a store holding a project row",
            )
        return int(row[0])

    def schema_version_or_none(self) -> int | None:
        """The schema version, or ``None`` for a store with no project yet."""
        row = self._execute('SELECT schema_version FROM "gc_project" LIMIT 1').fetchone()
        return int(row[0]) if row is not None else None

    def _insert(self, name: str, values: dict[str, Any]) -> None:
        entry = table(name)
        columns = list(values)
        self._execute(
            self._upsert_sql(entry, columns),
            tuple(self._adapt(entry, column, values[column]) for column in columns),
        )

    # -- writing ---------------------------------------------------------

    def write(self, project: Project, *, keep_solutions: bool = False) -> None:
        """Write a whole project, replacing what is there.

        One transaction. A partially written project is worse than an unwritten
        one -- it looks like data.

        Args:
            keep_solutions: Re-write the stored solutions afterwards, so adding
                a network to a project does not discard its results.

                **Why this is a flag and not the default.** ``write`` means
                *replace*, and callers rely on that: it is how a project is
                overwritten wholesale. But a caller that means "add this network
                to what is already here" wants the results kept, and getting
                that wrong is the failure FR-135 exists to prevent -- results
                vanishing without anyone being told. Before this existed, saving
                a second epoch's network into a monitoring project silently
                deleted every solution in it, because the algorithm's "add"
                mode called ``write``. The GeoPackage on disk still looked
                healthy; it had simply lost a year of answers.

                Re-writing rather than not deleting, because the solutions are
                read back through the same code that reads them for anything
                else: a second deletion path would be a second place for the
                foreign keys between a solution, its provenance and its results
                to go wrong.
        """
        with self._writing():
            # Inside the write lock: read before it, and another save could land
            # between reading the solutions and deleting them.
            preserved = self.read_solutions() if keep_solutions else []
            for entry in reversed(SCHEMA):
                self._execute(f"DELETE FROM {quoted(entry.name)}")
            self._write_project(project)
            self._write_settings(project.settings)
            for campaign in project.campaigns.values():
                self._write_campaign(campaign)
            for network in project.networks.values():
                self._write_network(network)
            for session in project.gnss_sessions.values():
                self._write_gnss_session(session)
            for solution in preserved:
                self._write_solution(solution)

    def write_solution(self, solution: Solution) -> None:
        """Add or replace one solution, with its provenance and results."""
        with self._writing():
            self._write_solution(solution)

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
                "revision": self._next_revision,
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
        srs_id = srs_of(network.crs)
        # The network's order, written down (schema 4): stations, then clusters,
        # then observations, each in the order the network holds them.
        ordinal = itertools.count()

        for station in network.stations.values():
            self._write_station(station, srs_id)
            self._insert(
                "gc_network_member",
                {
                    "network_id": network.id,
                    "member_kind": "station",
                    "member_id": station.id,
                    "ordinal": next(ordinal),
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
                    "ordinal": next(ordinal),
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
                    "ordinal": next(ordinal),
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
                "geom": self._point(plan[0], plan[1], srs_id) if plan else None,
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
            self._line([point for point in drawn if point is not None], srs_id)
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
                "instrument_height": _dumps(
                    observation.instrument_height.to_dict()
                    if observation.instrument_height
                    else None
                ),
                "target_height": _dumps(
                    observation.target_height.to_dict() if observation.target_height else None
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
                "strategies": _dumps(payload.get("strategies")),
            },
        )
        # FR-131's processing logs: one row per engine run the provenance
        # carries (FR-036). The table was declared in P5 and written by nothing
        # until P12c-13, so the store held no log however the result was made.
        self._execute('DELETE FROM "gc_run" WHERE provenance_id = ?', (identifier,))
        for index, run in enumerate((payload.get("parameters") or {}).get("runs") or ()):
            self._insert(
                "gc_run",
                {
                    "id": f"{identifier}-run-{index + 1}",
                    "provenance_id": identifier,
                    "kind": str(run.get("program") or payload.get("engine") or "engine"),
                    "exit_code": run.get("exit_code"),
                    "log": _dumps(run),
                },
            )
        return identifier

    def _write_solution(self, solution: Solution) -> None:
        # Replacing a stored solution replaces its results: a re-saved solution
        # with one station fewer must not keep the old row for it.
        for name in ("gc_observation_result", "gc_adjusted_station", "gc_statistics"):
            self._execute(f"DELETE FROM {quoted(name)} WHERE solution_id = ?", (solution.id,))
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

        srs_id = srs_of(solution.crs)
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
                    "gravity": _dumps(station.gravity.to_dict() if station.gravity else None),
                    "geom": self._point(plan[0], plan[1], srs_id) if plan else None,
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
        with self._writing():
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
            self._execute(
                'DELETE FROM "gc_network_member" WHERE member_kind = ? AND member_id = ?',
                ("observation", observation_id),
            )
            self._execute(
                'DELETE FROM "gc_observation" WHERE id = ?', (observation_id,)
            )

    def solutions_using(self, observation_id: str) -> list[str]:
        """Which stored solutions were computed from this observation."""
        rows = self._execute(
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
        with self._writing():
            self._execute(
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
        with self._writing():
            for name in (
                "gc_observation_result",
                "gc_adjusted_station",
                "gc_statistics",
            ):
                self._execute(
                    f"DELETE FROM {quoted(name)} WHERE solution_id = ?", (solution_id,)
                )
            self._execute(
                'UPDATE "gc_solution" SET superseded_by = NULL WHERE superseded_by = ?',
                (solution_id,),
            )
            self._execute(
                'DELETE FROM "gc_solution" WHERE id = ?', (solution_id,)
            )

    # -- reading ---------------------------------------------------------

    def read(self) -> Project:
        """Read the whole project back, as one consistent snapshot.

        Reading also records the revision read: whoever writes this project
        back is writing what they saw, and the next save compares against it.
        """
        with self._transaction(write=False):
            project = self._read_project()
            self._revision = self._stored_revision()
        return project

    def _read_project(self) -> Project:
        row = self._row("gc_project")
        if row is None:
            raise DataError(
                "project_store_empty",
                path=self.location,
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
        with self._transaction(write=False):
            return [self._read_solution(row) for row in self._rows("gc_solution")]

    def _row(self, name: str) -> Any:
        return self._execute(f"SELECT * FROM {quoted(name)} LIMIT 1").fetchone()

    def _rows(self, name: str, where: str = "", parameters: Sequence[Any] = ()) -> list:
        """Rows of *name*, in an order both backends agree on.

        A query that states no order gets the primary key's: without one,
        SQLite returns row order and PostgreSQL physical order, and a project
        would read back differently depending on where it was kept.
        """
        clause = f" WHERE {where}" if where else ""
        if "ORDER BY" not in clause.upper():
            clause += " ORDER BY " + ", ".join(quoted(key) for key in table(name).primary_key)
        return list(
            self._execute(
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
        members = self._rows(
            "gc_network_member",
            "network_id = ? ORDER BY ordinal, member_kind, member_id",
            (row["id"],),
        )
        ordered = {
            kind: [entry["member_id"] for entry in members if entry["member_kind"] == kind]
            for kind in ("station", "cluster", "observation")
        }

        stations = {entry["id"]: entry for entry in self._rows("gc_station")}
        for identifier in ordered["station"]:
            if identifier in stations:
                network.add_station(self._read_station(stations[identifier]))

        clusters = {entry["id"]: entry for entry in self._rows("gc_cluster")}
        for identifier in ordered["cluster"]:
            if identifier not in clusters:
                continue
            entry = clusters[identifier]
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

        observations = {entry["id"]: entry for entry in self._rows("gc_observation")}
        for identifier in ordered["observation"]:
            if identifier in observations:
                network.add_observation(self._read_observation(observations[identifier]))
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
        instrument_height = _loads(row["instrument_height"])
        target_height = _loads(row["target_height"])
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
            instrument_height=(
                Quantity.from_dict(instrument_height) if instrument_height else None
            ),
            target_height=Quantity.from_dict(target_height) if target_height else None,
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
                        "strategies": _loads(entry["strategies"]) or [],
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
                gravity=Quantity.from_dict(_loads(entry["gravity"]))
                if entry["gravity"]
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
