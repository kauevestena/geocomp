# ADR-0006 — GeoPackage canonical, PostGIS mirror, identical logical schema

**Status:** Accepted
**Date:** 2026-08
**Requirements:** FR-130, FR-131, FR-132, FR-133

## Context

The proposal requires both file-based and database-based operation, switchable *"de forma transparente e
configurável"* (`tex §Integração com PostGIS`), and cites `wander_thesis` for why a spatial database matters:
structured centralised storage, concurrent access, advanced spatial and temporal queries, and direct GIS
integration.

Two stores raise the question of which is authoritative and how they relate.

## Options

**A. PostGIS primary, file mode as an export.** Best for the multi-user monitoring case. Rejected: it makes a
PostgreSQL server a prerequisite for a student on a laptop or a surveyor in the field, which contradicts the
adoption goal.

**B. GeoPackage primary, PostGIS as an optional mirror with the same logical schema.** Chosen.

**C. An abstraction layer over both, with neither primary.** Cleanest in principle. Rejected as
over-engineering: it means a third schema definition to maintain, and neither store gets to use what it is
good at.

## Decision

**Option B.** GeoPackage is the default and canonical store. PostGIS is a fully supported alternative with an
**identical logical schema** — same tables, same columns, same semantics — differing only in physical types
and indexing.

Schema in [`../17-persistence-and-interoperability.md`](../17-persistence-and-interoperability.md) §2.

## Rationale

- **GeoPackage matches the default user.** A single file, no server, portable, versionable, emailable,
  natively supported by QGIS and OGR. A student, a teacher and a field laptop all need this.
- **An identical logical schema is what makes "transparent" true.** Switching stores becomes a content
  migration, not a semantic one; every consumer above the storage layer is unaware of which is in use; and
  there is one schema to design, document, version and test.
- **PostGIS earns its place where the proposal says it does** — concurrent access, long monitoring series,
  large volumes — and users who need it are already running it.

## Consequences

- One schema definition drives both stores, with a physical type mapping per backend.
- Round-trip fidelity is a hard requirement and a test: GeoPackage → PostGIS → GeoPackage must be lossless,
  table by table.
- `schema_version` is stored and enforced in both (FR-133), with forward-only migrations tested against
  fixture stores of every released version — important because monitoring projects outlive plugin releases.
- Some PostGIS capabilities (partitioning, advanced indexing, materialised views) are not exploited, because
  doing so would break schema identity. If a real performance need appears, it is a new ADR — likely adding
  backend-specific *indexes*, which do not change the logical schema, before anything that does.
- GeoPackage's concurrency limits are accepted; the documented answer for concurrent multi-user work is
  PostGIS.

## Implementation note (phase P11)

The decision stands as written; building the mirror changed three things beneath it, each recorded in
[`../17-persistence-and-interoperability.md`](../17-persistence-and-interoperability.md) §4.

- **"One schema definition drives both stores" became "one store logic drives both".** The declarations were
  already shared; the code that turns a project into rows now is too (`io/store/base.py`), so the two backends
  can differ only in what PostgreSQL and SQLite do differently.
- **JSON is `text` in PostgreSQL, not `jsonb`.** `jsonb` cannot hold `NaN`, which a valid solution stores, and
  it rewrites a document's text. A physical-type choice, as this ADR allows; queries can still cast to `jsonb`.
- **Order and concurrency are in the logical schema** (schema 4): a network's member order, which SQLite had
  kept by accident and PostgreSQL would not, and a revision every save checks.

