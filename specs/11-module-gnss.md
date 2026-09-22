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

**Built in phase P7c [V]**, as eight registered algorithms: the four modes under two submenus, plus scan
sessions, build baselines, batch processing and compare configurations. Two notes on what the drawing above
now means in code:

- **The second level is an exception, and it is guarded.** Every other GeoComp menu group is one level deep
  ([`15-ui-menu-and-settings.md`](./15-ui-menu-and-settings.md) §1.1). GNSS nests because its four modes are
  two branches of two and "Static" alone names nothing; a flat menu would read *Absolute static*, *Absolute
  kinematic*, *Relative static*, *Relative kinematic*, four entries distinguished pairwise by their first
  word. `geocomp/registry.py` names the permitted set in `NESTING_MENUS`, refuses a submenu declared under
  any other group at import, and `tests/test_registry.py` holds the set to one — so the exception cannot
  spread by imitation, which is how a one-level menu usually stops being one.
- **Download products is not among the eight.** FR-352 and FR-353 moved to P10 when the egress check found
  every major archive unreachable from CI (`ROADMAP.md`, P7b). The menu entry arrives with the capability;
  listing it now would be a menu item pointing at nothing, which §1.2 of `specs/15` forbids outright.

FR-604's notice reaches the user three ways in the Absolute algorithms — in the short description, in the
help body, and as a warning pushed at the top of every run — because "state the limitation in the UI" is not
satisfied by documentation nobody opens.

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

### 4.1 The independent subset **[V]**

Delivered in phase P7b as `core/techniques/gnss/baselines.py::independent_subset`.

*n* simultaneously observing stations yield *n(n−1)/2* baselines of which only *n−1* carry new information.
The independent set is a **maximum spanning forest** over the station graph, and "maximum" is by quality: a
baseline whose covariance has the smaller trace is preferred, so the chosen set is the best-determined
spanning tree rather than whichever one the input order happened to produce.

*Forest*, not tree, is deliberate — two disconnected pairs of stations give two independent baselines and no
error, because there is no baseline between the groups to be dependent on.

**Nothing is discarded.** Both lists come back with every baseline marked `is_independent`, because §3.1
allows the full set in Advanced mode with the consequence stated, and that needs the dependent ones to still
exist and to know what they are.

### 4.2 Antenna height reduction happens once **[V]**

The reduction is recorded **on the baseline it produced**, not beside it: `Baseline.antenna_reduction` is
`None` until `reduce_to_marks` runs and holds both offsets afterwards, and a second call raises
`antenna_height_already_reduced`. Acceptance criterion 5 below asks for a test that a double reduction is
prevented; a flag that a caller has to remember to check is not that, because any caller that copies the
components out can separate the record from the thing it describes.

The geometry, including why each end is rotated at its *own* horizon, is in
[`08-engine-rtklib.md`](./08-engine-rtklib.md) §8.3.

### 4.3 Result layers (FR-357) **[V]**

Delivered in phase P7c as `layers/builders.py::gnss_baseline_layer` and the optional `OUTPUT_LAYER` of
`geocomp:gnss_build_baselines`, styled by `resources/styles/gnss_baselines.qml`.

A baseline is a geocentric vector and has no position of its own, so what the map draws is the pair of marks
it connects — one line per baseline, from the geodetic latitude and longitude each `Baseline` already carries
for both its ends. That is what makes the layer available the moment processing finishes: no network, no
adjustment and no station list are needed. The horizons are drawn as EPSG:4326, which is wrong by the few
centimetres the ITRF realisations differ by and right to far better than any map draws; the `.pos` file does
not state its realisation, so there is nothing more exact to use.

Three decisions in the attribute table are worth recording, because each is a way the layer could have lied:

1. **The components are `d1/d2/d3`, not `dx/dy/dz`, and a `frame` column names their axes.** §4.1's rotation
   produces a baseline in east, north and up for the in-house core, and a column headed `dx` holding an east
   component is the kind of label that gets read rather than checked.
2. **`independent` is text with three states, not a boolean.** It is empty until §4.1's subset has run, and a
   map that rendered that third state as "no" would report an unassessed baseline as one carrying no new
   information. The style gives it its own symbol for the same reason.
3. **The layer draws every baseline that was built, including the dependent ones when they were not kept.**
   §3.1 requires the dependent ones to be marked rather than discarded, and a map that dropped them is
   precisely how nobody notices they were there. The JSON output carries what was kept; the layer carries
   what was processed, and the two are cross-checked in `tests/qgis/test_gnss_layers.py`.

The quality indicators of §5 travel on the same features, so the thematic styling FR-902 asks for — solution
status, fixed fraction — is a change of renderer rather than a second query.

### 4.3.1 The trajectory layer **[V]**

FR-357's other half, and §3.2's: a kinematic run is a time series, not a baseline. `gnss_trajectory_layer`
draws one point per solution epoch, categorised by solution status — which §5 calls the fastest way to see
what a session actually achieved, because a fixed epoch and a float one differ by two orders of magnitude in
accuracy and by nothing at all in appearance.

It is offered by **all four** processing modes rather than only the kinematic pair. A static run's epochs are
its filter converging, which is worth being able to look at, and a parameter present on two of four otherwise
identical algorithms is a difference nobody would remember.

**Every point is in the local horizon, whatever the engine wrote.** `rnx2rtkp` has four output formats and
each needs a different operation to yield a coordinate and a comparable covariance: the two geodetic ones are
already north/east/up, ECEF must be *rotated* at each epoch's own position, and ENU must be *permuted* — the
same three axes in another order. A `sigma_n` column that meant a different thing per file would be
unreadable, so `core/techniques/gnss/trajectory.py` refuses to construct a point whose covariance is in any
other frame.

That the four formats are one solution written four ways is what makes this testable, and
`tests/test_gnss_trajectory.py` uses it: every format must place the last epoch within a millimetre of the
others and give the same three standard deviations. **It caught a real defect** — the first ECEF path passed
`(n, e, u)` to the rotation, whose rows are east, north and up in that order, so it relabelled rather than
permuted and swapped the north and east sigmas. Both numbers stayed the right order of magnitude and the map
still drew.

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

**DOP is not available from `rnx2rtkp`, and is recorded as absent rather than substituted for** (phase P7b).
No column of the `.pos` file in any of its four output formats carries a dilution of precision
([`08-engine-rtklib.md`](./08-engine-rtklib.md) §7.1). It could be computed from the position covariance by
dividing out an assumed a-priori sigma, but that number would be a function of the weighting RTKLIB happened
to use, and presenting it as DOP would be presenting a different quantity under a familiar name.
`SessionQuality.dilution_of_precision` therefore exists and is always `None` today: the field is there so an
engine that *does* report DOP has somewhere to put it, and so the gap is visible rather than silently absent.
**This clause of FR-603 is unmet**, and the requirement is not recorded as fully closed on its account.

These surface in the results table, in the layer attributes, in the report (FR-930), and as thematic styling
(FR-902) — a map of sessions coloured by solution status is the fastest way to see what a campaign actually
achieved.

**Delivered in P7c, on both layers.** The trajectory layer (§4.3.1) is categorised by solution status and
carries the satellite count, the ambiguity ratio, the age of differential and north/east/up sigmas per epoch;
the baseline layer carries the fixed fraction and the status of the epoch its vector came from. The
processing algorithms also write the whole `SessionQuality` as a JSON summary beside the `.pos`. Cycle slips
and rejected epochs remain unavailable: `rnx2rtkp` reports neither in any output format, which is the same
situation as DOP above and is recorded the same way rather than substituted for.

---

## 6. Comparative configuration testing (FR-359)

Process the same data under several named configurations and compare. GeoComp presents:

- the solutions side by side, with coordinate differences and their significance given the covariances;
- the quality indicators of §5 per configuration;
- an export of the comparison table (FR-162).

This directly serves both the researcher profile (does this parameter matter for my data?) and teaching (see
what an elevation mask actually does). Configurations are saved as named profiles and are shareable.

**Delivered in P7c as `geocomp:gnss_compare_configurations`, judged by significance rather than by size.**
`core/techniques/gnss/comparison.py` forms `d^T (Sigma_a + Sigma_b)^-1 d` against chi-square on 3 degrees of
freedom, because a 3 mm difference is large against 0.5 mm sigmas and nothing against 5 mm ones — a table of
differences alone invites the reader to supply the judgement, and they have nothing to supply it with. Two
runs over the same observations are **not** independent, so summing the covariances is conservative and is
recorded as `Strategy.INDEPENDENCE_ASSUMED` rather than quietly enjoyed.

**The custom dialog [`15-ui-menu-and-settings.md`](./15-ui-menu-and-settings.md) §1.2 lists is not built.**
The algorithm ships first and alone, per [`adr/0005-menu-algorithm-parity.md`](./adr/0005-menu-algorithm-parity.md):
the algorithm is what makes the capability real, scriptable and testable, and the dialog hands it the same
parameters. It is named in `ROADMAP.md` rather than implied to be present.

---

## 7. Reference station data

Relative positioning needs a base. The module supports: a station of the user's own campaign; a CORS whose
data the user supplies; and a configured reference-station database (FR-063) recording station identifiers,
coordinates, their datum and epoch, and data-source URLs.

**A reference station's coordinates carry a datum and an epoch, and they are used** (FR-105). Processing
against a base whose published coordinates are in a different frame or at a different epoch from the project,
without transformation, is a systematic error affecting every derived point. GeoComp checks and transforms
(FR-832), recording what it did.

**Delivered in P7c as `core/techniques/gnss/stations.py` [V]**, with the epoch half done and the frame half
deferred:

- A station is a position *in a frame, at an epoch*, with an optional velocity. Where an epoch is required
  and absent, the operation is refused rather than assumed current (FR-105) — a coordinate silently read as
  "today" is wrong by the plate motion since it was published, which in Brazil is about 15 mm a year.
- Propagating to another epoch is a multiplication by the velocity and the elapsed years, exact, and recorded
  on the result.
- **Changing frame raises.** FR-832's transformations belong to P10, and until they exist an ITRF2020
  coordinate read as SIRGAS2000 would be wrong by decimetres and internally consistent —
  `reference_station_frame_mismatch` names the requirement and the phase rather than guessing. So acceptance
  criterion 7 below is half met: the mismatch is detected and processing refused; the transformation is P10's.

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

### 8.1 Where they stand after P7c

| # | State | Evidence, or what is missing |
|---|---|---|
| 1 | **Met** | `tests/test_gnss_discovery.py`; mixed RINEX 2 and 3, with header/filename mismatches reported as warnings rather than as failures |
| 2 | **Red by design** | RD-06 reproduces NGS's published coordinates to 7.5 mm against a 1 mm criterion. P7b attributed the residual — a low-elevation error and a stable ~6.9 mm that survives full antenna calibration, IGS20 orbits, two days and a base/rover reversal ([`22-reference-data-sources.md`](./22-reference-data-sources.md) §5) — and deriving a GNSS threshold to replace the borrowed printed-precision one is the maintainer's decision, not this phase's |
| 3 | **Met** | `tests/test_gnss_baselines.py`; the subset is a maximum spanning forest by covariance trace, and the dependent ones come back marked |
| 4 | **Met** | `tests/test_gnss_to_dynadjust.py`; the cluster reaches `<GPSBaseline>` with its 3×3 intact |
| 5 | **Met** | `tests/test_gnss_baselines.py`; the record lives on the reduced baseline, so a second call raises rather than relying on a caller to check a flag |
| 6 | **Met** | `tests/test_gnss_comparison.py`; two configurations over one session, with the difference judged against the summed covariances |
| 7 | **Half met** | The mismatch is detected and refused (§7). The transformation is FR-832's and belongs to P10; until it exists, refusing is the honest half |
| 8 | **Met** | The notice is in the help, the short description and a warning pushed at the top of every Absolute run |

Criteria 2 and 7 are the two that are not closed, and neither closes inside P7c: one waits on a threshold to
be *derived* rather than chosen, the other on P10's transformations.
