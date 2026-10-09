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
- **Download products was not among the eight, and is the ninth since P10c.** FR-352 and FR-353 moved to
  P10 when the egress check found every major archive unreachable from CI (`ROADMAP.md`, P7b); P10b found
  NOAA's CORS open-data bucket reachable, and P10c built the capability and its menu entry together, so the
  entry never pointed at nothing (§1.2 of `specs/15`). It sits after *Scan sessions*, since it can read a
  folder's days, and before the modes, since it is what lets them run offline. It fetches — or, with *check
  only*, merely reports — the orbits and navigation for a folder's days or a range of days, copies them out
  if asked, and writes a manifest. The processing algorithms do not depend on it: each resolves its own
  products (§2), and this is for fetching ahead or checking ahead.

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

**Resolving products is both an arrow and a step inside processing (P10c).** *Download products* is the
arrow, for fetching or checking ahead. But the four modes, batch processing and *Compare configurations*
resolve what their own sessions need before the engine starts — an orbit per day when the precise ephemeris
is selected, navigation when the folder has none — and refuse a missing product there, naming it, rather
than leave the engine to fail on something else or to run on broadcast orbits presented as precise ones.
Batch processing resolves every session's products before the first session runs. Every run's JSON names its
products by origin and checksum ([`08`](./08-engine-rtklib.md) §5).

**The process arrow did not reach the baselines arrow until P13-15.** *Relative — Static* and a static batch
wrote latitude, longitude and height, *Build baselines* takes ECEF alone ([`08`](./08-engine-rtklib.md) §8.1),
and an options file may not change an `out-` key, so no solution processed from the menu could become a
baseline. Every test of the chain answered with an ECEF solution from a stand-in engine; the real profile was
never asked. The static profile now writes ECEF. The kinematic one still writes latitude and longitude: a
trajectory is not a baseline, and its layer reads every format.

**A station observed more than once is never guessed between (P13-16).** A campaign observes a mark on
several days, and a folder holds them all. Until P13-16 every processing algorithm kept one session per
station, the last the scan listed, and dropped the others without a word: *Relative — Static* processed that
pair whether or not the two had observed together, and *Batch processing* keyed its rows by station, so a mark
observed on two days was processed twice as the second day. Now:
- **One baseline, one pair.** The relative modes take the base and rover sessions that overlap. One pair is
  processed, and the log names it when either station has other sessions. Several are refused with their
  spans, since choosing one is a guess; none is refused too.
- **One position, one session.** The absolute modes refuse a station with several sessions, naming them.
- **A batch row per session.** Each rover session runs against the base session it overlaps, and is keyed by
  its station and span where the station has more than one. A session the base did not observe with fails
  with that reason, and so does one two base sessions overlap; the rest of the batch runs.
- **Spans are written `2025-01-01 00:00/00:59`**, an ISO 8601 interval, whose separator needs no translation.

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

### 4.1.1 Loop closure **[V]**

Delivered in phase P7e as `core/techniques/gnss/baselines.py::loop_closure`.

The dependent baselines §4.1 marks are exactly the ones that can be *checked*: a closed circuit of
measured vectors must return where it began, so the sum is zero but for the errors in the legs. That
makes closure the one check on a set of baselines needing **no external coordinate at all** — it asks
whether the measurements agree with each other rather than with somebody's published position.
[`20`](./20-testing-and-validation.md) §6 rests RD-06's GNSS criterion on that distinction.

**The sum is taken in ECEF and a local-frame leg is refused.** East, north and up at one station are
not east, north and up at another, so adding local vectors round a circuit adds three different frames
and returns a misclosure that is mostly rotation. Over a 65 m triangle the two horizons differ by about
2e-6 rad and the error hides under a millimetre; over a 50 km loop it does not, and a check that is
silently wrong only at the scale where it matters is worse than no check. Mixing legs reduced to the
marks with legs still at the antenna reference points is refused for the same reason: such a loop
closes by the difference of the antenna heights, which looks exactly like a measurement error.

**The covariance is always approximate**, and says so. Legs of one session share satellites, clocks and
atmosphere, so adding their covariances as though independent understates the truth; that is recorded
as `Strategy.INDEPENDENCE_ASSUMED` rather than left to be inferred, because a misclosure judged against
an over-optimistic sigma looks significant when it is not.

**What closure cannot see.** An error common to every baseline at one station enters the loop twice
with opposite signs and cancels, so a perfect closure does not mean the station is right. RD-06
demonstrates it: 2025-001 carries a contaminated hour and still closes to a quarter of a millimetre.
Closure is therefore necessary and not sufficient, and [`20`](./20-testing-and-validation.md) §6 pairs
it with a repeatability criterion for exactly that reason.

**From the menu since P13-14.** Until then nothing in QGIS called the closure: a reader could build three
baselines round a triangle and never learn whether they agreed. *Build baselines* now closes every loop it can.
- **Which loops.** Each dependent baseline joins two stations the independent forest already connects, so
  exactly one path joins them through it. That path and the dependent baseline back are the loop
  (`closing_loops`). One loop per dependent baseline is a basis: every other circuit is a combination of them.
- **Closed whether kept or not.** Keeping a dependent baseline is the adjustment's question; whether it agrees
  with the others is a check, and is made either way.
- **Where it is reported.** The log gives each loop's misclosure in millimetres over its perimeter, and in
  parts per million. The JSON output's `closures` gives the components and their propagated sigma, in the
  form `scripts/check_rd06.py` records (`LoopClosure.to_dict`).
- **The same pair twice is not a loop.** A two-station circuit retraces itself, so a repeated pair is left
  out; comparing two determinations of one vector is repeatability, and nothing in the menu compares them yet.
- **Nothing to close is said.** With no loop to close, the log says what one needs.

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

### 4.4 The network document (P9b)

*Build baselines* writes, on request (`OUTPUT_NETWORK`), the network the Integration menu combines: the kept
baselines as one cluster, each observation at its **session's mid-epoch** (`% obs start`/`% obs end`, or the
first and last epochs), and each mark's **starting position** — the base's from the `% ref pos` header, a
rover's from its last epoch (its antenna's, a metre or two from its mark at most: a start, not a coordinate).
Every mark is free; the datum is the combination's to set.

It needs **the frame of the base coordinates** (`FRAME`), which a `.pos` file does not state and GeoComp does
not assume (FR-105). Asked for the document without it, the algorithm refuses: a vector with no frame cannot
be brought into another's, and a combination would refuse it later with less to say about why.

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

**A float baseline is named where it is built (P13-18).** A static baseline is its run's last epoch
([`08`](./08-engine-rtklib.md) §8.1), so that epoch's status is the baseline's. *Build baselines* warns of every
baseline whose last epoch's ambiguities were not fixed, with its ambiguity ratio, and its JSON output lists them
under `float`. Until P13-18 only the layer's `solution_status` column said so, and the log said nothing.
[`22`](./22-reference-data-sources.md) §5.1 measured a float GODN–GODS baseline 872 mm wrong with a 7.6 mm formal
sigma: a float baseline's covariance does not describe its error. It is named rather than dropped, because
leaving out an observation is the surveyor's decision, and data snooping in the adjustment is there to judge it.

**DOP is computed from the satellite geometry RTKLIB reports, by RTKLIB's definition** (P12c-35). No column
of the `.pos` file carries a dilution of precision, and P7b recorded it as absent rather than derive one from
the position covariance -- that number would depend on the weighting RTKLIB happened to use, a different
quantity under a familiar name. It is still not derived that way. The engine's solution-status file carries
each used satellite's azimuth and elevation per epoch ([`08`](./08-engine-rtklib.md) §7), and the DOP of that
geometry is what RTKLIB's own `dops()` computes: rows `[cos e sin a, cos e cos a, sin e, 1]` for the
satellites above the horizon, at least four of them, and the square roots of the diagonal of the inverse of
the normal matrix. Each epoch carries GDOP, PDOP, HDOP and VDOP, or none where fewer than four satellites were
used; the session carries each one's median and the epoch whose PDOP was worst, because a good median can hide
a stretch where the geometry was not. They reach the JSON summary and the trajectory layer's `pdop`, `hdop`
and `vdop` columns.

These surface in the results table, in the layer attributes, in the report (FR-930), and as thematic styling
(FR-902) — a map of sessions coloured by solution status is the fastest way to see what a campaign actually
achieved.

**Delivered in P7c, on both layers.** The trajectory layer (§4.3.1) is categorised by solution status and
carries the satellite count, the ambiguity ratio, the age of differential and north/east/up sigmas per epoch;
the baseline layer carries the fixed fraction and the status of the epoch its vector came from. The
processing algorithms also write the whole `SessionQuality` as a JSON summary beside the `.pos`.

**Cycle slips and rejected observations are the engine's own detections, read from the same file** (P12c-36).
P7c recorded them as reported in no output format; that was wrong. The `$SAT` lines carry, per satellite and
frequency -- a *signal*, named `G20/1` by the satellite and RTKLIB's frequency number -- a slip flag and an outlier
counter (`outsolstat` in `src/rtkpos.c`), and GeoComp reports what they say rather than detecting anything itself:

- **a cycle slip** is the slip flag's first bit on a signal flagged valid. Valid matters: RTKLIB clears the flag
  each epoch only for satellites both receivers observe, so a satellite the base has lost carries its last flag
  forward on lines that are not valid.
- **a rejected observation** is the outlier counter changing to a value other than zero. The counter is not itself
  a count: RTKLIB raises it once for each pass over the residuals that rejects the signal -- three in one epoch of
  the test run -- and resets it when it restarts the signal's ambiguity. It misses a rejection only where the
  engine reset the counter and rejected that signal as many times again in the same epoch.

Each epoch carries the signals of either kind; the session carries how many there were and which satellites
they were on -- `None`, not zero, where the engine reported on no epoch. A slip found from the two carriers
together is two signals. The trajectory layer carries `slips` and `rejections` as counts and `slipped` and
`rejected` as the signals. Checked against faults put where the answer is known -- a slip on one satellite, an
outlier on another, in the sample's real observations (`tests/gnss_faults.py`) -- which the engine finds at the
epochs and on the signals they were put on, and nowhere else (`tests/test_cycle_slips.py`).

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

**Side by side is the algorithm's report (P12c-43).** The HTML report has one column per configuration,
with the reference first. Its rows are:
- the elevation mask the configuration ran at, and the baseline's length with its standard deviation;
- the difference from the reference in X, Y, Z, in 3D and in length;
- the test statistic and the decision;
- the quality indicators of §5 from that configuration's own run: epochs, fixed fraction, median ratio,
  satellites, median PDOP, cycle slips and rejected observations.

A note says how to read the independence assumption, and one sentence says what the comparison found. The
comparison's JSON records what each configuration set and how its run went; its CSV is the export (FR-162),
with the data's own header.

A configuration is an elevation mask, swept, or an RTKLIB options file of the user's own (FR-070). Given
two or more files, each is a configuration named by its file and compared at the options it states over
Global Settings. A file is the named, shareable profile this section asks for.

[`15-ui-menu-and-settings.md`](./15-ui-menu-and-settings.md) §1.2 listed a custom dialog for this, and none is
built. What the user needs to see is the result, and the report is where every algorithm presents one, opened
by Processing's results viewer whether the run came from the menu, the toolbox or a model. A dialog that ran
the configurations itself would be a second way to run them ([`adr/0005-menu-algorithm-parity.md`](./adr/0005-menu-algorithm-parity.md)),
and one that only collected parameters would add nothing the Processing dialog lacks.

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
- **Changing frame raises.** An ITRF2020 coordinate read as SIRGAS2000 would be wrong by decimetres and
  internally consistent — `reference_station_frame_mismatch` names the requirement rather than guessing. The
  transformation itself exists since P9a (`core/geodesy/frames.py`,
  [`13`](./13-module-integration.md) §5.1) and the refusal now points to it; **the base-station path does not
  call it yet**, so acceptance criterion 7 below is still half met: the mismatch is detected and processing
  refused, and applying the transformation there with its record is the wiring left.

**Since P12c the base-station path transforms, and records it.** A wider gap came first: no processing run read
the reference-station database at all. A relative run held its base where the RINEX header put it, which is an
approximate position in no stated frame. Now:

- **The run's frame.** The relative algorithms and the batch take *Frame of the results*. The default is the
  project's: the datum of `reference_systems.preferred_crs`, read through its geographic base, so a SIRGAS 2000
  UTM zone names SIRGAS 2000. The other choices are the base's own frame, or one of the frames P9a holds
  transformations for.
- **A base in the database** is brought into that frame at its session's epoch (`stations.to_frame`). P9a's
  Helmert steps run at the published epoch, and a change of epoch moves the base along its published velocity.
  RTKLIB gets the result as explicit `xyz` coordinates.
- **The record.** The run's summary records what was published, where the base was held, and every step with
  its stated accuracy, under `base_coordinates`.
- **What cannot be done is refused** before the engine runs, each case by name:
  - a session with no start time;
  - a station with no epoch;
  - a change of epoch with no velocity, including any move into SIRGAS 2000, which is defined at 2000.4;
  - a frame no transformation is held for, such as WGS 84.
- **A base not in the database** keeps the header position, as before, and the summary says it is in no stated
  frame.

Not done: *Build baselines* still asks for the base's frame as a parameter rather than reading it from the
run's summary.

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
| 7 | **Met in P12c** | The base is transformed into the run's frame at the session's epoch and recorded in the run's summary; what cannot be transformed is refused (§7) |
| 8 | **Met** | The notice is in the help, the short description and a warning pushed at the top of every Absolute run |

Criteria 2 and 7 are the two that are not closed, and neither closes inside P7c: one waits on a threshold to
be *derived* rather than chosen, the other on applying P9a's transformation in the base-station path.

**Since P7e, criterion 2 is met** on the criterion as restated — loop closure and repeatability
([`20`](./20-testing-and-validation.md) §6). Criterion 7 is still half met. The table above is the state
after P7c; the register in [`20`](./20-testing-and-validation.md) §10 holds the current state of every
criterion.
