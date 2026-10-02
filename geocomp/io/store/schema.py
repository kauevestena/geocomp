# SPDX-License-Identifier: GPL-2.0-or-later
"""The logical schema, as data (FR-130, FR-131, FR-132).

``specs/17-persistence-and-interoperability.md`` section 2 and ADR-0006.

**One schema definition drives both stores.** That is the whole of ADR-0006's
"identical logical schema": the tables below are declared once, and each backend
maps the abstract column kinds onto its own physical types. Switching store is
then a migration of content, not of meaning.

Pure data, and deliberately so. Nothing here opens a file, imports sqlite, or
knows what a GeoPackage is, which buys three things:

* the schema can be *checked* -- foreign keys resolve, every table has a primary
  key, ids are stable -- in the fast test tier;
* the DDL for both backends is generated from one source, so PostGIS cannot
  drift from GeoPackage by an omitted column; and
* ``specs/17`` section 2's table list can be compared against the code
  mechanically rather than by reading.

**Design rules, from the spec, made structural here.**

1. *One observation table with a typed payload*, not one per type. Adding an
   observation type must not require a schema migration
   (``specs/03-architecture.md`` section 4), so the per-type values live in a
   JSON column and the type is a discriminator. Per-type **views** give the
   convenient querying that "observações (por tipo)" needs in practice.
2. *Covariance is stored as a matrix*, as a blob of big-endian float64 -- never
   flattened to standard deviations, and never rounded through text. Reloading
   is bit-identical, which is acceptance criterion 9 and NFR-007.
3. *Every result references its provenance*, and provenance references its
   inputs by id and content digest.
4. *Nothing that produced a result is deleted while the result exists*
   (FR-135). ``superseded_by`` is the mechanism; the foreign keys below are what
   make the refusal structural rather than remembered.
5. *Geometry is a derived convenience.* The numeric columns are the record.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

__all__ = [
    "POSTGRES",
    "SCHEMA",
    "SCHEMA_VERSION",
    "SQLITE",
    "Column",
    "ColumnKind",
    "GeometryKind",
    "Table",
    "ddl",
    "geometry_type",
    "index_ddl",
    "physical_type",
    "quoted",
    "table",
    "table_names",
    "view_ddl",
]

#: The logical schema version (FR-133). Incremented on **every** schema change,
#: with a migration added in :mod:`geocomp.io.store.migrations`. A monitoring
#: project accumulates epochs over years and outlives several plugin releases,
#: so this is load-bearing rather than ceremonial.
#:
#: Schema 4 (phase P11) added ``gc_project.revision``, which is how a save
#: detects that someone else saved first, and ``gc_network_member.ordinal``,
#: which records the order of a network's stations and observations instead of
#: leaving it to SQLite's row order -- an order PostgreSQL does not keep.
#:
#: Schema 5 (phase P12c) added ``gc_provenance.strategies``: which
#: approximations a result rests on, which its provenance had never recorded.
SCHEMA_VERSION = 5


class ColumnKind(Enum):
    """An abstract column type, mapped to a physical type per backend."""

    TEXT = "text"
    INTEGER = "integer"
    REAL = "real"
    BOOLEAN = "boolean"
    #: A JSON document. Text in SQLite, ``jsonb`` in PostgreSQL.
    JSON = "json"
    #: Raw bytes: a covariance matrix, a digest.
    BLOB = "blob"
    #: An ISO-8601 UTC instant. Stored as text in both, deliberately: a
    #: timestamp round-tripped through a database's own type loses its
    #: timezone in one backend and its microseconds in the other, and
    #: provenance that cannot be compared exactly is not provenance.
    TIMESTAMP = "timestamp"


class GeometryKind(Enum):
    """The geometry a table carries, or nothing."""

    POINT = "POINT"
    LINESTRING = "LINESTRING"


@dataclass(frozen=True)
class Column:
    """One column, with the reason it exists where that is not obvious."""

    name: str
    kind: ColumnKind
    primary_key: bool = False
    nullable: bool = True
    #: ``"table.column"``, or ``None``.
    references: str | None = None
    #: Whether deleting the referenced row is refused rather than cascaded.
    #: **True for every reference from a result to its inputs** -- FR-135 in
    #: the one place it can be enforced rather than remembered.
    restrict: bool = True
    #: Whether the reference becomes a foreign key, or is documented only.
    #:
    #: Not every real relationship should be enforced at write time. Raw field
    #: data legitimately precedes the network it will belong to -- a GNSS
    #: session is recorded in the field, and which network it feeds is decided
    #: in the office, sometimes weeks later. A foreign key there would refuse to
    #: store the observation until somebody had defined a network, which is the
    #: storage layer dictating the order of the work.
    enforced: bool = True
    note: str = ""

    def __post_init__(self) -> None:
        if self.primary_key and self.nullable:
            object.__setattr__(self, "nullable", False)
        if self.references is not None and "." not in self.references:
            raise ValueError(f"{self.name}: a reference must be 'table.column'")


@dataclass(frozen=True)
class Table:
    """One table of the logical schema."""

    name: str
    columns: tuple[Column, ...]
    geometry: GeometryKind | None = None
    note: str = ""
    #: Columns to index together, beyond the primary key.
    indexes: tuple[tuple[str, ...], ...] = ()

    def __post_init__(self) -> None:
        if not any(column.primary_key for column in self.columns):
            raise ValueError(f"{self.name}: no primary key")
        names = [column.name for column in self.columns]
        if len(set(names)) != len(names):
            raise ValueError(f"{self.name}: duplicate column")

    @property
    def primary_key(self) -> tuple[str, ...]:
        return tuple(c.name for c in self.columns if c.primary_key)

    def column(self, name: str) -> Column:
        for candidate in self.columns:
            if candidate.name == name:
                return candidate
        raise KeyError(f"{self.name} has no column {name!r}")


def _text(name: str, **kwargs) -> Column:
    return Column(name, ColumnKind.TEXT, **kwargs)


def _json(name: str, **kwargs) -> Column:
    return Column(name, ColumnKind.JSON, **kwargs)


def _real(name: str, **kwargs) -> Column:
    return Column(name, ColumnKind.REAL, **kwargs)


def _int(name: str, **kwargs) -> Column:
    return Column(name, ColumnKind.INTEGER, **kwargs)


def _bool(name: str, **kwargs) -> Column:
    return Column(name, ColumnKind.BOOLEAN, **kwargs)


def _blob(name: str, **kwargs) -> Column:
    return Column(name, ColumnKind.BLOB, **kwargs)


def _stamp(name: str, **kwargs) -> Column:
    return Column(name, ColumnKind.TIMESTAMP, **kwargs)


#: Every table, in the order ``specs/17`` section 2 lists them. Creation order
#: matters -- a referenced table must exist first -- and this order satisfies it.
SCHEMA: tuple[Table, ...] = (
    Table(
        "gc_project",
        (
            _text("id", primary_key=True),
            _text("name"),
            _text("description"),
            _text("default_crs"),
            _json("default_epoch"),
            _int("schema_version", nullable=False),
            _stamp("created"),
            _stamp("modified"),
            _text("geocomp_version"),
            _int(
                "revision",
                note=(
                    "Incremented by every save. A save compares it with the revision "
                    "it read and refuses when they differ, so a concurrent save is "
                    "detected rather than overwritten (specs/17 section 4)"
                ),
            ),
        ),
        note="One row. The schema version lives here and nowhere else (FR-133).",
    ),
    Table(
        "gc_settings",
        (
            _text("key", primary_key=True),
            _json("value", nullable=False),
        ),
        note="Project-scope setting overrides (FR-068).",
    ),
    Table(
        "gc_epoch",
        (
            _text("id", primary_key=True),
            _real("decimal_year", nullable=False),
            _stamp("instant"),
            _text("label"),
        ),
    ),
    Table(
        "gc_instrument",
        (
            _text("id", primary_key=True),
            _text("kind", nullable=False, note="instrument, reflector, level, levelling_class"),
            _json("payload", nullable=False),
        ),
        note=(
            "Profiles as their own documents, one JSON payload per record. The "
            "alternative -- a column per constant -- would need a schema "
            "migration every time an instrument model gains a term, and P4 "
            "added a whole new profile kind without touching this table."
        ),
    ),
    Table(
        "gc_campaign",
        (
            _text("id", primary_key=True),
            _text("name"),
            _text("epoch_id", references="gc_epoch.id"),
            _stamp("start"),
            _stamp("end"),
            _text("crew"),
            _json("meta"),
        ),
    ),
    Table(
        "gc_station",
        (
            _text("id", primary_key=True),
            _text("name"),
            _text("description"),
            _text("station_type", nullable=False),
            _text("monitoring_role"),
            _json("approx_position"),
            _json("constraint_spec", nullable=False),
            _json("meta"),
        ),
        geometry=GeometryKind.POINT,
        note="Geometry derived from approx_position for display; the JSON is the record.",
    ),
    Table(
        "gc_setup",
        (
            _text("id", primary_key=True),
            _text(
                "station_id",
                references="gc_station.id",
                enforced=False,
                note="Documented, not enforced: a setup is field data and may precede the network.",
            ),
            _text("instrument_id", references="gc_instrument.id"),
            _text("campaign_id", references="gc_campaign.id"),
            _json("meta"),
        ),
    ),
    Table(
        "gc_cluster",
        (
            _text("id", primary_key=True),
            _text("kind", nullable=False),
            _json("labels", nullable=False),
            _json("units", nullable=False),
            _text("mode", nullable=False),
            _json("strategies"),
            _int("size", nullable=False),
            _blob("matrix", nullable=False, note="Big-endian float64, row major."),
        ),
        note=(
            "Covariance as a matrix, as a blob of big-endian float64. Not text, "
            "because a matrix round-tripped through decimal is not the matrix "
            "that went in, and not standard deviations, because that discards "
            "the correlations FR-104 exists for."
        ),
    ),
    Table(
        "gc_observation",
        (
            _text("id", primary_key=True),
            _text("type", nullable=False),
            _json("stations", nullable=False),
            _text("station_from", note="First station, for the per-type views and geometry."),
            _text("station_to", note="Last station, where the type relates two."),
            _json("values", nullable=False, note="One Quantity document per component."),
            _json("epoch"),
            _text("setup_id", references="gc_setup.id"),
            _text("instrument_id", references="gc_instrument.id"),
            _text("cluster_id", references="gc_cluster.id"),
            _int("cluster_index", note="Position in the cluster's covariance ordering."),
            _text("status", nullable=False),
            _json("rejection"),
            _json("meta"),
            _json(
                "instrument_height",
                note=(
                    "A Quantity document, or null. Height of the trunnion axis "
                    "above the mark, for a sight measured from the instrument "
                    "rather than from the point (specs/09 section 2.5)."
                ),
            ),
            _json("target_height", note="A Quantity document, or null."),
        ),
        geometry=GeometryKind.LINESTRING,
        indexes=(("type",), ("station_from",), ("cluster_id",)),
        note=(
            "One table, typed payload. Adding an observation type must not "
            "require a migration (specs/03 section 4), so the type is a "
            "discriminator and the values are a document."
        ),
    ),
    Table(
        "gc_gnss_session",
        (
            _text("id", primary_key=True),
            _text(
                "station_id",
                references="gc_station.id",
                enforced=False,
                note=(
                    "Documented, not enforced. A session is recorded in the "
                    "field; which network it feeds is decided in the office, "
                    "sometimes weeks later. A foreign key here would refuse to "
                    "store the observation until somebody had defined a network."
                ),
            ),
            _text("obs_file"),
            _json("nav_files"),
            _stamp("start"),
            _stamp("end"),
            _real("interval"),
            _text("receiver"),
            _text("antenna"),
            _json("antenna_height"),
            _text("antenna_height_method"),
            _json("products"),
            _json("meta"),
        ),
        geometry=GeometryKind.POINT,
    ),
    Table(
        "gc_network",
        (
            _text("id", primary_key=True),
            _text("name"),
            _text("crs"),
            _json("epoch"),
            _json("meta"),
        ),
    ),
    Table(
        "gc_network_member",
        (
            _text("network_id", primary_key=True, references="gc_network.id"),
            _text("member_kind", primary_key=True, note="station, observation or cluster"),
            _text("member_id", primary_key=True),
            _int(
                "ordinal",
                note=(
                    "The member's position in the network. A network's stations and "
                    "observations have an order -- the field book's -- and before "
                    "schema 4 it survived only as SQLite's row order"
                ),
            ),
        ),
        note=(
            "A network is a *selection*, so membership is its own table: one "
            "campaign's observations feed several network definitions, and a "
            "free and a constrained solution of the same data are two networks."
        ),
    ),
    Table(
        "gc_provenance",
        (
            _text("id", primary_key=True),
            _stamp("created", nullable=False),
            _text("source"),
            _text("algorithm_id"),
            _json("parameters"),
            _text("engine"),
            _text("engine_version"),
            _text("command_line"),
            _int("exit_code"),
            _json("input_ids"),
            _json("input_digests"),
            _text("geocomp_version"),
            _text("qgis_version"),
            _text("uncertainty_mode", nullable=False),
            _json("strategies"),
        ),
        note=(
            "FR-134. Never holds a credential, a token, or a URL containing "
            "one (NFR-010) -- checked by a test rather than trusted."
        ),
    ),
    Table(
        "gc_solution",
        (
            _text("id", primary_key=True),
            _text("network_id", references="gc_network.id"),
            _text("kind", nullable=False),
            _text("crs", nullable=False),
            _json("epoch", nullable=False),
            _text("datum_definition", nullable=False),
            _text("uncertainty_mode", nullable=False),
            _text("provenance_id", references="gc_provenance.id"),
            _text("parameter_covariance_id", references="gc_cluster.id"),
            _text("superseded_by", references="gc_solution.id", restrict=False),
        ),
        note=(
            "``superseded_by`` rather than deletion (FR-135), and it is the one "
            "reference here that does not restrict: superseding a solution with "
            "a newer one must not be blocked by the newer one existing."
        ),
    ),
    Table(
        "gc_adjusted_station",
        (
            _text("solution_id", primary_key=True, references="gc_solution.id"),
            _text("station_id", primary_key=True),
            _json("position", nullable=False),
            _text("covariance_id", references="gc_cluster.id"),
            _json("ellipse"),
            _real("positional_uncertainty"),
            _json("correction"),
            # A gravity solution's adjusted value (specs/12 section 5). The
            # position of such a station is where it is, not what was adjusted.
            _json("gravity"),
        ),
        geometry=GeometryKind.POINT,
    ),
    Table(
        "gc_observation_result",
        (
            _text("solution_id", primary_key=True, references="gc_solution.id"),
            _int(
                "row_index",
                primary_key=True,
                note=(
                    "The design-matrix row. **The key, and not the observation "
                    "id**: there is one result per *row*, and a GNSS baseline "
                    "contributes three rows under one observation id. Keying on "
                    "the observation would silently keep the last of the three."
                ),
            ),
            _text(
                "observation_id",
                nullable=False,
                references="gc_observation.id",
                note=(
                    "FR-135 made structural. With this reference in place, "
                    "deleting an observation a stored solution was computed "
                    "from is refused by the database, not by a check somebody "
                    "has to remember to write."
                ),
            ),
            _real("residual"),
            _real("standardised_residual"),
            _real("redundancy"),
            _real("minimal_detectable_bias"),
            _real("external_reliability"),
            _real("adjusted_value"),
            _bool(
                "is_uncheckable",
                note=(
                    "Derived from the redundancy number beside it, and stored "
                    "anyway: 'which observations could not be checked at all' is "
                    "the query a reader most wants to run, and a Python property "
                    "is not available in SQL."
                ),
            ),
            _json("w_test"),
        ),
        indexes=(("observation_id",),),
    ),
    Table(
        "gc_statistics",
        (
            _text("solution_id", primary_key=True, references="gc_solution.id"),
            _real("variance_factor_apriori"),
            _real("variance_factor_aposteriori"),
            _int("degrees_of_freedom"),
            _int("n_observations"),
            _int("n_parameters"),
            _int("n_constraints"),
            _int("iterations"),
            _real("max_correction"),
            _real("condition_number"),
            _bool("converged"),
            _json("global_test"),
        ),
    ),
    Table(
        "gc_run",
        (
            _text("id", primary_key=True),
            _text("provenance_id", references="gc_provenance.id"),
            _text("kind", nullable=False),
            _stamp("started"),
            _stamp("finished"),
            _int("exit_code"),
            _text("log"),
        ),
        note="Engine and algorithm runs (FR-036).",
    ),
    Table(
        "gc_displacement",
        (
            _text("id", primary_key=True),
            _text("station_id", nullable=False),
            _text("from_solution_id", references="gc_solution.id"),
            _text("to_solution_id", references="gc_solution.id"),
            _json("vector", nullable=False),
            _text("covariance_id", references="gc_cluster.id"),
            _real("test_statistic"),
            _real("critical_value"),
            _bool("is_significant"),
        ),
        geometry=GeometryKind.LINESTRING,
        note="Multi-epoch displacements. Filled by phase P10; declared now so the schema is whole.",
    ),
)

_BY_NAME = {entry.name: entry for entry in SCHEMA}


def table(name: str) -> Table:
    return _BY_NAME[name]


def table_names() -> tuple[str, ...]:
    return tuple(entry.name for entry in SCHEMA)


#: Physical types per backend, exercised against a real PostgreSQL with PostGIS
#: since phase P11 (``tests/test_postgis_store.py``). Two choices in the
#: PostgreSQL column are not the obvious ones, and both are about losing
#: nothing:
#:
#: * **Text is collated ``"C"``.** SQLite compares text byte by byte; a
#:   PostgreSQL database compares it by its locale, so ``ORDER BY station_id``
#:   would put ``a2`` and ``A10`` in a different order on the two backends, and
#:   a project would read back in a different order depending on where it was
#:   kept. ``"C"`` is byte order, which is SQLite's.
#: * **JSON is ``text``, not ``jsonb``.** P5 planned ``jsonb``. It cannot hold
#:   ``NaN``, which a zero-redundancy solution's global test stores as its
#:   statistic, so a valid project would be refused; and it rewrites the
#:   document's text, so a round trip would be equal only after parsing.
#:   ``text`` keeps both. A query can still cast a column with ``::jsonb``.
_PHYSICAL: dict[ColumnKind, tuple[str, str]] = {
    ColumnKind.TEXT: ("TEXT", 'text COLLATE "C"'),
    ColumnKind.INTEGER: ("INTEGER", "bigint"),
    ColumnKind.REAL: ("REAL", "double precision"),
    ColumnKind.BOOLEAN: ("INTEGER", "boolean"),
    ColumnKind.JSON: ("TEXT", 'text COLLATE "C"'),
    ColumnKind.BLOB: ("BLOB", "bytea"),
    ColumnKind.TIMESTAMP: ("TEXT", 'text COLLATE "C"'),
}

SQLITE, POSTGRES = "sqlite", "postgres"

_POSTGIS_GEOMETRY = {
    GeometryKind.POINT: "geometry(Point)",
    GeometryKind.LINESTRING: "geometry(LineString)",
}


def geometry_type(kind: GeometryKind, backend: str = SQLITE) -> str:
    """The geometry column's physical type.

    A typed PostGIS column with no SRID: each project's stations carry their
    own network's CRS, and an unconstrained SRID is what lets one table hold
    them. (``geometry(Point)`` accepts any SRID; checked against PostGIS 3.4.)
    """
    if backend == SQLITE:
        return "BLOB"
    if backend == POSTGRES:
        return _POSTGIS_GEOMETRY[kind]
    raise ValueError(f"unknown backend {backend!r}")


def physical_type(kind: ColumnKind, backend: str = SQLITE) -> str:
    sqlite_type, postgres_type = _PHYSICAL[kind]
    if backend == SQLITE:
        return sqlite_type
    if backend == POSTGRES:
        return postgres_type
    raise ValueError(f"unknown backend {backend!r}")


def quoted(name: str) -> str:
    """One identifier, quoted.

    Every generated identifier goes through this, not only the ones that
    obviously need it. ``values`` and ``end`` are reserved words in SQL and are
    also the natural names for an observation's components and a session's end
    -- bending the *schema* to avoid a quoting rule would be the wrong way round,
    and quoting selectively is how the next reserved word gets through.
    Double quotes are standard SQL and correct in both backends.
    """
    if '"' in name:  # pragma: no cover - no such identifier exists
        raise ValueError(f"identifier {name!r} contains a quote")
    return f'"{name}"'


def ddl(entry: Table, backend: str = SQLITE) -> str:
    """``CREATE TABLE`` for one table, in the given backend's dialect."""
    lines: list[str] = []
    for column in entry.columns:
        piece = f"  {quoted(column.name)} {physical_type(column.kind, backend)}"
        if not column.nullable:
            piece += " NOT NULL"
        lines.append(piece)

    if entry.geometry is not None:
        lines.append(f"  {quoted('geom')} {geometry_type(entry.geometry, backend)}")

    keys = ", ".join(quoted(name) for name in entry.primary_key)
    lines.append(f"  PRIMARY KEY ({keys})")

    for column in entry.columns:
        if column.references is None or not column.enforced:
            continue
        target_table, target_column = column.references.split(".", 1)
        action = "RESTRICT" if column.restrict else "SET NULL"
        # Deferrable in PostgreSQL so that copying a store can insert a solution
        # before the solution it was superseded by; immediate unless a
        # transaction asks otherwise, which is SQLite's behaviour too.
        deferrable = " DEFERRABLE INITIALLY IMMEDIATE" if backend == POSTGRES else ""
        lines.append(
            f"  FOREIGN KEY ({quoted(column.name)}) "
            f"REFERENCES {quoted(target_table)}({quoted(target_column)}) "
            f"ON DELETE {action}{deferrable}"
        )

    body = ",\n".join(lines)
    return f"CREATE TABLE {quoted(entry.name)} (\n{body}\n)"


def index_ddl(entry: Table, backend: str = SQLITE) -> list[str]:
    """``CREATE INDEX`` statements for one table."""
    del backend  # identical in both dialects for what is declared here
    statements = []
    for columns in entry.indexes:
        name = f"idx_{entry.name}_{'_'.join(columns)}"
        targets = ", ".join(quoted(column) for column in columns)
        statements.append(
            f"CREATE INDEX {quoted(name)} ON {quoted(entry.name)} ({targets})"
        )
    return statements


#: Per-type observation views. ``specs/17`` section 2 asks for "observações (por
#: tipo)" as convenient querying, and a view gives exactly that without the
#: table-per-type schema that would need a migration for every new type.
def view_ddl(observation_types: list[str], backend: str = SQLITE) -> list[str]:
    """One view per observation type, over the single observation table."""
    del backend
    return [
        f"CREATE VIEW {quoted('gc_observation_' + name.lower())} AS "
        f"SELECT * FROM {quoted('gc_observation')} WHERE {quoted('type')} = '{name}'"
        for name in observation_types
    ]
