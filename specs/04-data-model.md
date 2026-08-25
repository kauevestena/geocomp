# 04 — Data model

**Status:** Draft
**Requirements covered:** FR-100…FR-107, FR-130, FR-135, FR-830.
**Source:** tex §Levantamento de requisitos e modelagem conceitual; §Integração com PostGIS; O4, O5, O6.

The physical storage schemas are in
[`17-persistence-and-interoperability.md`](./17-persistence-and-interoperability.md); this document defines
the *logical* model, which is identical in file mode and database mode (FR-132).

---

## 1. Entity overview

```text
Project
 ├── Settings (project scope)                       15-ui-menu-and-settings.md
 ├── Instrument[]           definitions and constants
 ├── Campaign[]             one field effort, bound to one Epoch
 │    ├── Setup[]           one occupation of one station
 │    ├── Observation[]     the measurements
 │    └── GnssSession[]     continuous GNSS observation periods
 ├── Network[]              what gets adjusted: a station set + an observation set
 │    ├── Station[]
 │    └── (references Observation[] and constraints)
 └── Solution[]             the output of one adjustment or processing run
      ├── AdjustedStation[]  coordinates + covariance
      ├── ObservationResult[] residual, standardised residual, redundancy, MDB
      ├── Statistics          global test, variance factor, degrees of freedom
      └── Provenance          inputs, parameters, engine, versions, timestamps
```

A **Campaign** is *what was observed*; a **Network** is *what is adjusted*. They are separate because one
campaign's observations can feed several network definitions (a free network and a constrained network, a
2D and a 3D solution), and one network can draw on several campaigns (FR-100).

---

## 2. Core entities

### 2.1 `Project`

The top-level container. One project is one GeoPackage file or one PostGIS schema.

| Field | Type | Notes |
|---|---|---|
| `id`, `name`, `description` | str | |
| `default_crs` | CRS reference | Authority:code |
| `default_epoch` | Epoch | FR-105 |
| `schema_version` | int | FR-133 |
| `created`, `modified` | timestamp (UTC) | |
| `settings` | mapping | Project-scope setting overrides (FR-068) |

### 2.2 `Epoch` (FR-105, FR-830)

Not a bare float. An epoch is a first-class value because comparing two coordinate sets is only meaningful
when both carry one.

| Field | Type | Notes |
|---|---|---|
| `decimal_year` | float | e.g. `2020.0` |
| `instant` | datetime (UTC) | The precise instant, when known |
| `label` | str | Human-readable, e.g. `"Epoch 3 — Oct 2026"` |

**Rule:** any coordinate set without an epoch is `epoch = None`, and any operation requiring an epoch
(FR-831, FR-832) **rejects** it with a `ValidationError` rather than assuming a default. A silently assumed
epoch is a wrong displacement.

### 2.3 `Station` (FR-101)

| Field | Type | Notes |
|---|---|---|
| `id` | str | Unique within a project |
| `name`, `description` | str | |
| `approx_position` | `Position` | Approximate coordinates; see §3 |
| `constraint` | `ConstraintSpec` | See §2.4 |
| `station_type` | enum | `MARK`, `BENCHMARK`, `GNSS_CORS`, `OBJECT_POINT`, `REFERENCE_POINT`, `PLANNED` |
| `monitoring_role` | enum \| None | `REFERENCE` or `OBJECT` — the stable block vs the structure (FR-835) |
| `meta` | mapping | Free-form: monument type, photo, installation date |

`PLANNED` marks a station that exists only in a pre-analysis design and has no observations yet (FR-270).

### 2.4 `ConstraintSpec` (FR-222)

Constraints are per-component, not per-station, because a station is routinely fixed in height and free in
plan (a benchmark used in a 3D network) or the reverse.

| Field | Type | Notes |
|---|---|---|
| `mode` | enum | `FREE`, `FIXED`, `WEIGHTED` |
| `components` | set | Any of `X`, `Y`, `Z` / `E`, `N`, `U` / `LAT`, `LON`, `H` |
| `position` | `Position` \| None | The constraining coordinates, with their epoch |
| `covariance` | `Covariance` \| None | Required when `mode == WEIGHTED` |

### 2.5 `Observation` (FR-102, FR-103)

| Field | Type | Notes |
|---|---|---|
| `id` | str | |
| `type` | `ObservationType` | See §4 |
| `stations` | tuple[str, …] | Ordered; arity depends on type (see §4) |
| `value` | `Quantity` or vector of `Quantity` | Always carries uncertainty (FR-200) |
| `epoch` | `Epoch` | When it was observed |
| `setup_id` | str \| None | The occupation it belongs to |
| `instrument_id` | str \| None | Which instrument, for constants and nominal precision |
| `cluster_id` | str \| None | Membership of a correlated group (FR-104) |
| `status` | enum | `ACTIVE`, `REJECTED`, `EXCLUDED` |
| `rejection` | `RejectionRecord` \| None | Why, by which test, when, by whom (FR-255) |
| `provenance` | `Provenance` | Where this observation came from |
| `meta` | mapping | Weather, target type, notes |

`REJECTED` means a statistical test rejected it (FR-251); `EXCLUDED` means a human removed it. Both are
reversible and neither deletes the record (FR-255, FR-135).

### 2.6 `Cluster` (FR-104)

A group of observations sharing one covariance matrix. GNSS baselines (3 correlated components), GNSS point
clusters, and sets of directions from one setup are clusters. **A cluster is the atomic unit passed to an
adjustment** — decomposing it into independent scalars discards correlation and falsifies the result, so the
model does not permit it silently.

| Field | Type | Notes |
|---|---|---|
| `id`, `kind` | str, enum | `GNSS_BASELINE`, `GNSS_POINT`, `DIRECTION_SET`, `GENERIC` |
| `observation_ids` | list[str] | Ordered — the order defines the covariance matrix ordering |
| `covariance` | `Covariance` | Full *n*×*n* matrix over the ordered members |

### 2.7 `GnssSession` (FR-350)

| Field | Type | Notes |
|---|---|---|
| `id`, `station_id` | str | |
| `obs_file`, `nav_files` | path, list[path] | RINEX |
| `start`, `end` | datetime (UTC) | From the RINEX header where available (FR-351) |
| `interval` | float | Sampling interval, seconds |
| `receiver`, `antenna` | descriptors | Type, serial, firmware |
| `antenna_height` | `Quantity` | With its method (vertical / slant) and reference point |
| `products` | list[path] | Resolved ephemeris, clock and ANTEX files (FR-352) |
| `meta` | mapping | |

### 2.8 `Solution` (FR-106, FR-323)

**One `Solution` type for every producer** — the in-house adjustment, DynAdjust, and `rnx2rtkp` all fill it.
This is what makes everything downstream engine-agnostic (see [`03-architecture.md`](./03-architecture.md) §3.2).

| Field | Type | Notes |
|---|---|---|
| `id`, `network_id` | str | |
| `kind` | enum | `ADJUSTMENT`, `GNSS_PROCESSING`, `PREANALYSIS`, `TRANSFORMATION` |
| `crs`, `epoch` | CRS, `Epoch` | Mandatory (FR-105) |
| `datum_definition` | enum + detail | `MINIMUM_CONSTRAINT`, `INNER_CONSTRAINT`, `CONSTRAINED`, `FIXED` |
| `adjusted_stations` | list[`AdjustedStation`] | Coordinates + covariance block |
| `parameter_covariance` | `Covariance` | The full **Σ**ₓ (FR-224) |
| `observation_results` | list[`ObservationResult`] | Per observation |
| `statistics` | `AdjustmentStatistics` | See §2.9 |
| `uncertainty_mode` | enum | `RIGOROUS` or `APPROXIMATE` (FR-203) |
| `provenance` | `Provenance` | See §2.10 |
| `superseded_by` | str \| None | Solutions are never overwritten (FR-135) |

`AdjustedStation`: station id, `Position`, its covariance block, error ellipse/ellipsoid parameters,
positional uncertainty, and the correction applied to the approximate coordinates.

`ObservationResult`: observation id, adjusted value, residual, standardised residual, redundancy number,
w-test statistic and decision, MDB, external reliability contribution (FR-225, FR-251, FR-252, FR-253).

### 2.9 `AdjustmentStatistics`

| Field | Notes |
|---|---|
| `n_observations`, `n_parameters`, `n_constraints`, `degrees_of_freedom` | |
| `variance_factor_apriori`, `variance_factor_aposteriori` | |
| `global_test` | statistic, lower and upper critical values, confidence level, decision (FR-250) |
| `iterations`, `converged`, `max_correction` | FR-223 |
| `condition_number` | Diagnostic for FR-226 |

### 2.10 `Provenance` (FR-134, NFR-007)

Recorded for every observation, solution and run.

| Field | Notes |
|---|---|
| `created` | UTC timestamp |
| `source` | Import file, engine run, or algorithm id |
| `algorithm_id`, `parameters` | The exact effective parameters, with the scope each came from (FR-068) |
| `engine` | Name, version, executable path, command line, exit code (FR-036) |
| `input_ids`, `input_digests` | Referenced entities plus content hashes of input files |
| `geocomp_version`, `qgis_version` | |
| `uncertainty_mode` | FR-203 |

**Rule (NFR-010):** provenance never records credentials, tokens or URLs containing them.

---

## 3. `Position` and coordinate handling (FR-105)

A `Position` is never a bare triple.

| Field | Type | Notes |
|---|---|---|
| `values` | 3 × `Quantity` | With uncertainty |
| `system` | enum | `GEODETIC` (φ, λ, h), `CARTESIAN` (X, Y, Z), `PROJECTED` (E, N, U) |
| `crs` | CRS reference | Authority:code |
| `epoch` | `Epoch` \| None | |
| `height_type` | enum | `ELLIPSOIDAL`, `ORTHOMETRIC`, `NORMAL`, `NONE` |
| `geoid_model` | str \| None | Which model related h and H (FR-804) |

`height_type` is explicit because mixing ellipsoidal and orthometric heights is one of the most common and
most damaging errors in combined GNSS/levelling work (FR-802). Any operation combining heights of different
types without a geoid model raises `ValidationError`.

---

## 4. Observation types (FR-103)

| Type | Stations | Value | Notes |
|---|---|---|---|
| `DIRECTION` | 2 (from, to) | angle | Belongs to a direction set with an unknown orientation |
| `HORIZONTAL_ANGLE` | 3 (at, from, to) | angle | Derived from two directions or measured directly |
| `AZIMUTH` | 2 | angle | Geodetic azimuth |
| `ASTRONOMIC_AZIMUTH` | 2 | angle | |
| `ZENITH_ANGLE` | 2 | angle | |
| `VERTICAL_ANGLE` | 2 | angle | 90° − zenith |
| `SLOPE_DISTANCE` | 2 | length | Includes instrument and target heights |
| `HORIZONTAL_DISTANCE` | 2 | length | Reduced |
| `ELLIPSOID_DISTANCE` | 2 | length | Reduced to the ellipsoid |
| `HEIGHT_DIFFERENCE` | 2 | length | Levelling; carries line length and setup count |
| `ORTHOMETRIC_HEIGHT` | 1 | length | Height as an observation |
| `ELLIPSOIDAL_HEIGHT` | 1 | length | |
| `GEODETIC_LATITUDE` / `GEODETIC_LONGITUDE` | 1 | angle | Coordinate as an observation |
| `ASTRONOMIC_LATITUDE` / `ASTRONOMIC_LONGITUDE` | 1 | angle | For deflection of the vertical (FR-165) |
| `GNSS_BASELINE` | 2 | ΔX, ΔY, ΔZ | Always a cluster (3×3 covariance) |
| `GNSS_POINT` | 1 | X, Y, Z | Always a cluster |
| `GRAVITY` | 1 | acceleration | Absolute gravity |
| `GRAVITY_DIFFERENCE` | 2 | acceleration | Relative gravity |

Each type declares: its arity, its value schema and units, its covariance shape, its contribution to the
design matrix, its serialisation, and its mapping to DynAdjust measurement codes where one exists (see
[`07-engine-dynadjust.md`](./07-engine-dynadjust.md) §4). Gravity types have **no** DynAdjust equivalent —
see [`12-module-gravimetry.md`](./12-module-gravimetry.md).

Adding a type means adding a registry entry, not editing the adjustment code
([`03-architecture.md`](./03-architecture.md) §4).

---

## 5. Identity and referential rules

1. **Station identifiers are stable and human-meaningful.** They come from the field book. GeoComp adds a
   surrogate key internally but never renames a user's station.
2. **Identifiers are unique within a project**, not globally. Two projects may both have a station `1`.
3. **Nothing that produced a result is deleted** while the result exists (FR-135). Superseding is the
   mechanism, via `superseded_by`.
4. **Observations reference stations by id.** An observation naming an unknown station is a `DataError` at
   import, reported per record without aborting the import (FR-166).
5. **A cluster's members are never adjusted individually.**

---

## 6. Serialisation

Every entity round-trips through JSON without loss (`to_dict` / `from_dict`), which is the basis of the
persistence layer, of provenance records, and of the model unit tests.

Rules, all consequences of NFR-007 and FR-095:

- Floating-point values serialise at full precision (`repr`-equivalent), never at display precision.
- Angles serialise in radians; DMS is a *display* format only (see [`00-glossary.md`](./00-glossary.md)).
- Timestamps are ISO 8601 UTC with an explicit offset.
- Covariance matrices serialise as the full matrix or as an upper-triangular packed form with the storage
  form declared — never as a bare standard deviation when correlations exist.
- Enumerations serialise by name, never by ordinal.
- Numeric formatting is locale-independent in files regardless of UI language (FR-095).
