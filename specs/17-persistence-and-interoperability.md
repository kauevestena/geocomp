# 17 — Persistence and interoperability

**Status:** Draft
**Requirements covered:** FR-130…FR-135, FR-160…FR-167.
**Source:** O5; tex §Integração com PostGIS e bancos de dados espaciais; §Arquitetura do plugin;
§Levantamento de requisitos.
**Decision:** [`adr/0006-storage.md`](./adr/0006-storage.md).

---

## 1. Two modes, one logical schema (FR-132)

> *"O GeoComp deverá permitir ao usuário alternar entre um modo baseado em arquivos e um modo baseado em
> banco de dados, de forma transparente e configurável."* — `tex §Integração com PostGIS`

| | File mode | Database mode |
|---|---|---|
| Store | One GeoPackage file | One PostGIS schema |
| For | Individual work, portability, teaching, field laptops | Shared projects, concurrent users, long monitoring series, large volumes |
| Default | ✔ | |

**The logical schema is identical.** Same tables, same columns, same semantics — only the physical types and
the indexing strategy differ. This is what makes "transparent" achievable: switching mode is a migration of
content, not of meaning, and every consumer above the storage layer is unaware of which is in use.

The motivation for database mode is quoted directly in the proposal from `wander_thesis`: structured
centralised storage of large volumes, concurrent access, advanced spatial and temporal queries, and direct
GIS integration.

## 2. Schema

Tables, following `tex §Integração com PostGIS` ("tabelas para estações geodésicas, observações (por tipo),
campanhas e projetos… tabelas para armazenar resultados de ajustes, estatísticas e logs de processamento…
chaves e relacionamentos necessários para rastreabilidade e reprocessamento"), and the entities of
[`04-data-model.md`](./04-data-model.md):

| Table | Holds | Geometry |
|---|---|---|
| `gc_project` | One row: identity, default CRS and epoch, schema version | — |
| `gc_settings` | Project-scope setting overrides (FR-068) | — |
| `gc_instrument` | Instrument and reflector profiles with constants and calibration (FR-069) | — |
| `gc_campaign` | Field efforts, bound to an epoch | — |
| `gc_epoch` | Reference epochs | — |
| `gc_station` | Stations with approximate coordinates and constraint status | Point |
| `gc_setup` | Instrument occupations | — |
| `gc_observation` | Observations, common columns; type-specific values in a typed payload | Line, where a station pair makes one meaningful |
| `gc_cluster` | Correlated groups and their covariance (FR-104) | — |
| `gc_gnss_session` | GNSS sessions and their file and product references | Point |
| `gc_network` / `gc_network_member` | Network definitions | — |
| `gc_solution` | Solutions with CRS, epoch, datum definition, uncertainty mode | — |
| `gc_adjusted_station` | Adjusted coordinates with covariance and ellipse parameters | Point |
| `gc_observation_result` | Residuals, standardised residuals, redundancy, w-test, MDB | — |
| `gc_statistics` | Global statistics per solution | — |
| `gc_run` | Engine and algorithm runs: command line, exit code, timings, versions (FR-036) | — |
| `gc_provenance` | Provenance records with input digests (FR-134) | — |
| `gc_displacement` | Multi-epoch displacements with covariance and significance | Line |

**Design rules:**

1. **One observation table with a typed payload**, not one table per type. Adding an observation type must
   not require a schema migration ([`03-architecture.md`](./03-architecture.md) §4). Per-type views are
   provided for convenient querying, which is what "observações (por tipo)" needs in practice.
2. **Covariance is stored as a matrix**, referenced from the cluster, never flattened to standard deviations
   ([`05-uncertainty-and-covariance.md`](./05-uncertainty-and-covariance.md) §3.1).
3. **Every result references its provenance**, and provenance references its inputs by id and content digest
   (FR-134).
4. **Nothing that produced a result is deleted while the result exists** (FR-135). Superseding, via
   `superseded_by`, is the mechanism.
5. **Geometry is a derived convenience**, computed from the authoritative numeric coordinates for map
   display. The numbers are the record; the geometry is a view of them at a moment.

**Implemented in phase P5, with two departures from the list above, both recorded here rather than left to be
discovered in the code.**

*No `gc_cluster_member` table.* An earlier draft of this section paired one with `gc_cluster`. A cluster's
membership is already carried by `gc_observation.cluster_id`, and its **ordering** — which is the part that
matters, because the ordering defines the covariance's ordering — by `gc_observation.cluster_index`. A
separate membership table would be a second place for the same fact, and two places for one fact is how they
come to disagree. `tests/structural/test_spec_consistency.py` compares this table list against the code, with
this one absence declared.

*Not every documented relationship is a foreign key.* `gc_setup.station_id` and `gc_gnss_session.station_id`
are documented and **not enforced**. Raw field data legitimately precedes the network it will belong to: a
GNSS session is recorded in the field and which network it feeds is decided in the office, sometimes weeks
later. A foreign key there would refuse to store the observation until somebody had defined a network, which
is the storage layer dictating the order of the work. Every reference *from a result to its inputs* is
enforced and restricting — that is FR-135, and it is the set where enforcement belongs.

## 3. Versioning and migration (FR-133)

`gc_project.schema_version` is an integer, incremented on every schema change.

- Opening a store with a **newer** version: refuse, with a message naming the versions and directing the user
  to update the plugin. Reading a schema you do not understand silently corrupts it.
- Opening an **older** version: offer migration, take a backup first, migrate in a transaction, report what
  changed.
- Migrations are forward-only, tested against fixture stores of every released version, and never lossy
  without an explicit confirmation.

This matters more than usual: a monitoring project accumulates epochs over years and will outlive several
plugin releases.

## 4. Mode switching (FR-132)

Two operations: export a GeoPackage project to a PostGIS schema, and import a PostGIS schema to a GeoPackage.
Both are complete round trips — a round trip must be lossless, asserted by a test comparing every table.

The user configures the store per project. Reading a PostGIS store uses the QGIS connection registry, so
GeoComp inherits the user's existing connections and credentials handling rather than asking again
(NFR-010).

Concurrency is PostGIS's business, with GeoComp taking the appropriate transaction scope for a write and
detecting a concurrent modification on save rather than overwriting it.

**Status after phase P5: the PostGIS backend is not built.** There is no PostgreSQL server in this project's
development or CI environments, so acceptance criterion 1 — the lossless round trip — cannot be demonstrated,
and shipping an untested storage backend for the one part of the system whose whole job is *not losing data*
would be worse than shipping none. What P5 does deliver for it is the half that can be verified without a
server: the schema is declared once, as data, and generates the DDL for **both** dialects, so the two cannot
drift apart before the backend arrives. `tests/test_project_store.py` asserts the PostgreSQL dialect is
generated; it does not assert that anything executes it.

---

## 5. Interoperability

### 5.1 CSV and spreadsheets (FR-160, FR-162)

The proposal names `.xlsx` and CSV explicitly.

**Built with the standard library's `sqlite3`, not GDAL** (P5). A GeoPackage *is* a SQLite database with a
documented set of metadata tables, so nothing in the store needs a spatial library — and the consequence is
the point: the store is testable in the fast tier, on every platform, with no QGIS and no GDAL. Eight of CI's
nine jobs have neither. A GDAL-backed store would have been shorter to write and untestable in all eight.

**Field mapping is a first-class, reusable object.** Import shows a preview of the source, the user maps
columns to GeoComp fields, and the mapping is **saved by name and reused** — because the same organisation
imports the same instrument export layout every week, and re-mapping by hand every time is exactly the
"inconsistências decorrentes da manipulação manual" the proposal set out to eliminate.

Mapping handles: column-to-field assignment; unit selection per column; angle format (decimal degrees,
DMS in one column, DMS across three columns as in RD-01); decimal separator; date and time formats;
constant values applied to all rows; and rows to skip.

Import reports per-record errors without aborting (FR-166), presents them in a table with row numbers, and
leaves the target unchanged if the user cancels.

Export to CSV and `.xlsx` covers stations, observations, adjusted results, residuals and statistics.
`.xlsx` requires `openpyxl`; where it is unavailable, the feature degrades to CSV with a clear message
([`03-architecture.md`](./03-architecture.md) §3.7).

### 5.2 The *Adjust* format (FR-161)

The proposal requires interoperability with the format of the *Adjust* software accompanying Ghilani (2010) —
a widely used teaching tool, which makes this directly valuable for the pedagogical goal: a class's existing
worked examples can be opened in GeoComp and compared.

Read and write. The format's own conventions (its observation type codes, units and station referencing) are
documented in the implementation and validated against published example files.

### 5.3 DynAdjust formats (FR-163)

DynaML (write and read) and DNA `.stn`/`.msr` (read, with write as a secondary path). Specified in
[`07-engine-dynadjust.md`](./07-engine-dynadjust.md) §4.

Reading these formats is valuable beyond driving the engine: a user with an existing DynAdjust project can
open it in GeoComp, visualise it, and inspect it without converting anything by hand.

### 5.4 RINEX (FR-164)

Header parsing for session discovery: marker name and number, receiver and antenna type and serial, antenna
delta, observation interval, first and last observation times, and observation types present. RINEX 2 and 3,
short and long file names, plain, Hatanaka-compressed and archive-compressed. See
[`08-engine-rtklib.md`](./08-engine-rtklib.md) §4.

GeoComp does not implement full RINEX observation decoding — that is the GNSS engine's work.

### 5.5 Geoid and height models (FR-165)

Import of geoid models for reductions, for relating ellipsoidal and orthometric heights (FR-804), and for
approximate estimation of derived quantities such as the deflection of the vertical — the proposal cites
Franca (2021) for this application.

Supported: the grid formats QGIS/PROJ already handles, plus the model formats published by the relevant
national agencies. Each imported model records its identity, its version and its coverage, so that a solution
can record *which* model produced it (FR-804) and two solutions computed with different models are never
silently compared ([`14-multi-epoch-monitoring.md`](./14-multi-epoch-monitoring.md) §2).

Interpolation is bilinear by default, with the interpolation's own uncertainty contributing to the
propagated result (FR-204).

#### As implemented (P5)

**Two formats, read without GDAL.** **GTX** — the vertical-shift grid PROJ uses, so the format a model
QGIS already handles arrives in — and **ESRI ASCII grid**, the text form nearly every GIS exports and the
one the national agencies' models are most often redistributed as. Both are read in pure Python, the same
choice §3 made for the store and for the same reason: GDAL is present in a QGIS install and absent from
seven of the nine environments the suite runs in, so a reader that needs it is exercised once and assumed
eight times. Anything else is refused with a message naming both formats and how to convert.

**The caller states the model's accuracy.** No grid format carries it, and `GeoidModel` will not be built
without one (FR-204). So `sigma` is a required argument to the reader rather than a default: the geoid's
uncertainty is very often what limits a combined height solution, and this is not the layer to invent it.

**The interpolation's uncertainty comes from the grid.** Estimated from the local curvature by central
second differences, taking the largest over the cell, and shaped per axis by `t(1−t)`:

> σ_interp = ½ · ( h_lat² · |N_φφ| · t_φ(1−t_φ) + h_lon² · |N_λλ| · t_λ(1−t_λ) )

There is no cross-derivative term because a bilinear interpolant reproduces the `xy` term of a surface
exactly. For a separable quadratic this is not a bound but the error itself; for a general surface it is an
estimate that can fall a few tenths of a percent short where the curvature varies within a cell, and it
converges as the grid refines. It is a standard deviation and is combined in quadrature with the model's
stated accuracy. It goes to **zero at a node**, which a flat "assume a centimetre" figure would not.

**Extrapolation is refused, not clamped.** A geoid model quoted beyond its stated coverage is the most
confident wrong number in geodesy. Coverage is stored rather than derived from the grid, so a padded grid
still refuses outside the area the publisher vouched for.

**Deflection of the vertical is not implemented.** The proposal cites it as an application of an imported
model; it needs the horizontal gradient of the undulation and its own validation, and no reference case for
it exists yet. It stays open under FR-165.

### 5.6 Base maps and orthophotos (FR-167)

Cartographic context for processed and planned networks: the plugin offers to add configured base map
services, and honours the user's existing QGIS layers and connections. No bundled imagery, no hard-coded
service — a configurable list with sensible defaults.

---

## 6. Acceptance criteria

1. A complete project — networks, observations, sessions, settings, solutions, provenance — round-trips
   GeoPackage → PostGIS → GeoPackage with every table identical (FR-132).
2. Opening a newer schema version is refused with a clear message; opening an older one migrates after a
   backup, tested against fixture stores of every released version.
3. Deleting observations that a stored solution depends on is refused (FR-135).
4. RD-01's `raw_data.csv` imports through a saved field mapping, including three-column DMS and a
   locale-independent decimal separator; reapplying the saved mapping to a second file works unchanged.
5. An import with deliberately corrupt rows reports each one with its row number and imports the rest.
6. Cancelling an import leaves the target unchanged.
7. An *Adjust*-format example file reads, adjusts, and writes back to the same format equivalently.
8. A geoid model imports, is applied, records its identity in the solution, and contributes its uncertainty.
9. Covariance stored and reloaded is bit-identical (NFR-007).
