# 11 — Module: GNSS

**Status:** Draft
**Requirements covered:** FR-600…FR-604; module-level use of FR-350…FR-359.
**Source:** tex §Painel de Configuração Global, item 3 (GNSS); §Integração com o rnx2rtkp; §Posicionamento
pelo GNSS; O3.
**Engine contract:** [`08-engine-rtklib.md`](./08-engine-rtklib.md).

This document covers the *module* — the menu, the workflow, and what happens to a GNSS result once it
exists. The engine adapter, product download and `.pos` parsing are specified in `08-`.

---

## 1. Menu structure (FR-600, FR-601)

The proposal specifies two submenus, each with two options:

```text
GNSS
 ├── Absolute
 │    ├── Static        →  static PPP
 │    └── Kinematic     →  kinematic PPP
 └── Relative
      ├── Static        →  static baselines
      └── Kinematic     →  post-processed RTK and kinematic trajectories
```

Plus the supporting operations, which are algorithms in the same group: scan sessions, download products,
process batch, build baselines, compare configurations.

The Absolute branch carries the PPP limitation notice required by FR-604 — see
[`08-engine-rtklib.md`](./08-engine-rtklib.md) §3. The limitation is stated where the user chooses the mode,
not buried in documentation.

---

## 2. Workflow

```text
scan folder → sessions (FR-351)
     ↓
resolve products (FR-352) ── cache ── services
     ↓
configure (profile or explicit parameters, FR-354)
     ↓
process (single or batch, FR-355) ── engine ──►  .pos
     ↓
parse (FR-356) → positions / trajectories + covariance + quality
     ↓
build baselines (FR-602)  →  observations for adjustment
     ↓
adjust (in-house core or DynAdjust)  →  Solution
```

Each arrow is a Processing algorithm, so the whole chain is scriptable and can be assembled in the graphical
modeller (FR-033). Basic mode offers a single algorithm that runs the whole chain with defaults.

---

## 3. Positioning modes

### 3.1 Relative static

The workhorse: a baseline between two simultaneously observing stations, with its 3×3 covariance. This is
what feeds network adjustment, and it is where RTKLIB is strongest.

The module handles: identifying which sessions overlap sufficiently to form a baseline; choosing the base
station (a known station, a CORS, or the user's choice); processing each baseline; and assembling the
results.

**Baseline network topology matters and is reported.** Processing every possible pair of *n* simultaneously
observing stations produces n(n−1)/2 baselines, of which only n−1 are independent. Feeding all of them into
an adjustment as if independent inflates the apparent redundancy and understates the resulting uncertainty —
a classic and well-documented error. GeoComp:

- identifies the independent set and marks the rest as dependent;
- offers the independent set by default;
- allows the full set in Advanced mode, marked, with the consequence stated.

### 3.2 Relative kinematic

Post-processed RTK and kinematic trajectories. Output is a time series of positions with per-epoch
covariance and quality, imported as a point layer or a trajectory (FR-357). Used for detail survey and for
moving-platform work rather than for network adjustment.

### 3.3 Absolute static and kinematic (PPP)

Per the menu requirement. Static PPP produces one position per session with its covariance; kinematic PPP a
time series. Both carry the FR-604 notice and prominent convergence information — a PPP solution reported
without its convergence behaviour is not interpretable.

---

## 4. Baseline construction (FR-602)

The rules are in [`08-engine-rtklib.md`](./08-engine-rtklib.md) §8 and are not repeated. The module-level
requirements are:

1. **Station mapping.** A processed session maps to a GeoComp station via the RINEX marker name, the
   session's declared station, or an explicit user mapping. An ambiguous mapping is presented for resolution
   rather than guessed — a mis-mapped baseline is a confidently wrong observation.
2. **Antenna height reduction** to the mark is applied once, recorded, and never applied twice (a check
   asserts this).
3. **The baseline is a cluster** (FR-104) and reaches the adjustment with its covariance intact.
4. **Provenance** links each baseline back to its sessions, products, configuration and engine run
   (FR-134).

---

## 5. Quality reporting (FR-603)

Per session and, for kinematic, per epoch:

| Indicator | Why it is reported |
|---|---|
| Solution status (fixed / float / single) | A float solution is centimetre-to-decimetre, not millimetre. Presenting it without its status misrepresents the survey |
| Satellite count and constellations used | Multi-constellation availability is what makes a solution possible in obstructed sites (`tex §Posicionamento pelo GNSS`) |
| Ambiguity ratio factor | The evidence for the fixed solution being right |
| DOP values | Geometry quality |
| Percentage of epochs fixed (kinematic) | The single most informative summary of a kinematic run |
| Observation span and interval | Whether the session was long enough for the mode used |
| Cycle slips / rejected epochs | Data quality |

These surface in the results table, in the layer attributes, in the report (FR-930), and as thematic styling
(FR-902) — a map of sessions coloured by solution status is the fastest way to see what a campaign actually
achieved.

---

## 6. Comparative configuration testing (FR-359)

Process the same data under several named configurations and compare. GeoComp presents:

- the solutions side by side, with coordinate differences and their significance given the covariances;
- the quality indicators of §5 per configuration;
- an export of the comparison table (FR-162).

This directly serves both the researcher profile (does this parameter matter for my data?) and teaching (see
what an elevation mask actually does). Configurations are saved as named profiles and are shareable.

---

## 7. Reference station data

Relative positioning needs a base. The module supports: a station of the user's own campaign; a CORS whose
data the user supplies; and a configured reference-station database (FR-063) recording station identifiers,
coordinates, their datum and epoch, and data-source URLs.

**A reference station's coordinates carry a datum and an epoch, and they are used** (FR-105). Processing
against a base whose published coordinates are in a different frame or at a different epoch from the project,
without transformation, is a systematic error affecting every derived point. GeoComp checks and transforms
(FR-832), recording what it did.

---

## 8. Acceptance criteria

1. Scanning a folder of mixed RINEX 2 and RINEX 3 files produces correct sessions, with header/filename
   mismatches reported (see [`08-engine-rtklib.md`](./08-engine-rtklib.md) §10).
2. A static relative session over a published reference dataset reproduces the published coordinates within
   the tolerance in [`20-testing-and-validation.md`](./20-testing-and-validation.md).
3. Baselines built from a multi-station session have their independent subset correctly identified, and the
   dependent ones marked.
4. A baseline reaches a DynAdjust G measurement with its 3×3 covariance intact.
5. Antenna height reduction applied twice is detected and prevented; a test asserts it.
6. Comparative testing of two configurations over one session produces a comparison with correct differences
   and significance.
7. A base station in a different frame or epoch from the project triggers transformation, recorded in
   provenance; processing without it is refused.
8. Selecting an Absolute mode displays the FR-604 limitation notice.
