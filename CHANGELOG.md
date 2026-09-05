# Changelog

Semantic versioning. Breaking changes to the storage schema, algorithm ids or public core interfaces are
major ([`specs/21-packaging-ci-release-licensing.md`](specs/21-packaging-ci-release-licensing.md) §6).

## [Unreleased]

### Geodetic reductions

#### Added

- **`core/geodesy/`** - the piece three of P6's exit criteria were waiting on.
  Until now GeoComp had no ellipsoid at all: the distance reductions take a mean
  Earth radius and a caller-supplied point scale factor, which is enough to
  shorten a distance and not enough to say where a station is.

  - `ellipsoid.py` stores the two **defining** constants and derives the rest,
    so there is no table of pre-rounded values to disagree with itself in the
    eleventh digit. `e^2` is computed as `2f - f^2`, not `1 - b^2/a^2`: equal on
    paper, and the second form loses four significant figures to cancellation.
  - `cartesian.py` converts geodetic to geocentric and back, with Jacobians, so
    a coordinate that arrives with a covariance leaves with one (FR-201,
    FR-205). The inverse is Bowring's start refined by Newton until the identity
    is exact to floating point.
  - `projection.py` is Transverse Mercator in both directions -- Krüger's series
    in the third flattening, the form EPSG Guidance Note 7-2 gives for method
    9807 -- plus UTM as a parameterisation of it, and the point scale factor
    that `reduce_to_projection` has been taking as a magic argument.

  Validated against an **arbiter**, not against another series: the meridian arc
  integrated by Gauss-Legendre quadrature, NumPy only so it runs where SciPy is
  absent (ADR-0008). GeoComp is within a micrometre of the integral from -84 to
  84 degrees.

#### Found

- **DynAdjust's northing carries a meridian-arc truncation** ([`specs/07`](specs/07-engine-dynadjust.md) §4.5).
  Measured on fifteen stations placed on exact whole arcseconds, all
  constrained, so the engine's output is a pure conversion: **easting agrees to
  the printed 0.01 mm; northing does not**, by 0.085 mm at 36.5 degrees and
  0.253 mm at 45, growing with latitude and independent of longitude. That
  signature is the meridian arc rather than the projection, and the quadrature
  says the truncation is DynAdjust's. Recorded because a cross-validation that
  expects exact northing agreement will keep rediscovering it, and because
  matching it deliberately would mean shipping a worse conversion to agree with
  a better-known one.
- **The `.xyz` parser cannot read a column set containing `E`, `N` and `z`.** It
  refuses rather than mis-slicing, which is the right failure, but it means
  `--stn-coord-types ENz` output is unreadable. Not fixed here; the widths are
  in upstream's `dnaconsts-iostream.hpp` and this is the same work as the rest
  of `columns.py`.

### Grounding - published network adjustments

#### Added

- **`io/krumm.py`** - a reader for the format of Friedhelm Krumm's *Geodetic
  Network Adjustment Examples* (Universität Stuttgart, 2020), 61 worked networks
  transcribed from a dozen textbooks and redistributed with GNU Gama, **45 of
  them with the adjusted coordinates as published**
  ([`specs/22`](specs/22-reference-data-sources.md) §2).

  **33 of them now reproduce**, worst coordinate difference **0.05 mm** - which
  is the rounding of a value printed to four decimals, not a residual
  disagreement. Ghilani, Niemeier, Benning, Wolf, Strang and Borre, Grossmann,
  Höpke, Lother and Strehle, Carosio, Weiss and Blankenbach, by name and page.
  That is the citation RD-02, RD-03 and RD-04 have carried a standing note about
  since P1: they were validated against the operations under test rather than
  against a book, so "GeoComp agrees with itself" was all they established.

  The remaining 18 files are **refused by name**, each for something GeoComp
  cannot represent rather than something it reads badly - a weighted datum, an
  ellipsoidal network, conditions between parameters, an azimuth to a point with
  no coordinates. GNU Gama excludes most of the same files, for the same
  reasons.
- **`tests/data/krumm/`** (RD-11) - all 107 files, copied verbatim from GNU
  Gama at commit `963c309`. Vendoring was the maintainers' call and they made
  it, so the reference tests are now **tier 2**: they run on every commit, on
  every platform, with no network and nothing to opt into.
  `GEOCOMP_KRUMM_DIR` still overrides the path for checking the reader against a
  different revision.

  GNU Gama is GPL-3.0-or-later and GeoComp is GPL-2.0-**or-later**, so the
  combined portion is effectively GPL-3.0; that directory carries a
  GPL-3.0-or-later SPDX header rather than the repository's usual one.
  `PROVENANCE.md` records the chain, Gama's own `README.md` sits beside it
  unedited, and `THIRD_PARTY.md` carries the attribution.

  Two claims hold the position up, and neither is left as a promise:
  `scripts/check_krumm_corpus.py` compares every file against a fresh clone of
  the pinned commit (the `reference` workflow runs it on any change and
  monthly), and `TestTheCorpusIsTestDataOnly` asserts that no corpus file
  reaches the plugin package and no plugin module reads the directory. The ZIP
  is what users actually install, and it is unchanged: 164 entries, byte for
  byte.
- **`tests/test_krumm_corpus.py`** - the corpus run, with the expected outcome
  of every one of the 61 files recorded, so a change that turns a reproduction
  into a refusal fails rather than quietly shrinking the evidence.
- **`VERTICAL_ANGLE` now has an observation equation.** It was in the type
  registry, in the data model and in the DynAdjust type table, and the
  adjustment core had no equation for it at all - a gap the corpus found.
  ``v = pi/2 - z``, checked against complex-step differentiation and against the
  zenith-angle equation on the same geometry, because a numerical Jacobian
  cannot see a sign error in the value it is differentiating.

#### Fixed

Three defects the corpus found, each of which produced a plausible wrong answer
rather than an error:

- **A direction now carries its setup id**, not only its cluster id. The cluster
  is what FR-104 holds the set's correlation on; the *setup* is what the
  adjustment keys the orientation unknown on. Without it every direction is read
  as an absolute azimuth and the network still solves - to coordinates wrong by
  the unmodelled orientation, which reached **2 km** on one of Benning's
  networks.
- **A levelling standard deviation is per kilometre.** The line's own is
  `sigma * sqrt(L/1000)`, so the length column decides the weight; reading the
  stated value as the line's own weights a 1.2 km line and a 0.44 km line alike,
  and put `Niemeier_Height_fix1` **1.9 mm** out.
- **The station names after `free` are the datum stations**, not decoration.
  `LotherStrehle_Direction4` is `LotherStrehle_Direction3` with one station left
  out of the inner constraint, and the two published answers differ by
  **3.6 mm**.

### Phase P6 - DynAdjust

#### Fixed

- **The `engine` workflow had been failing since its second run**, and I had
  reported it green. The cache holds DynAdjust's binaries; the `apt-get install`
  that provides the shared libraries they link against sat *inside* the
  cache-guarded build step, so a cache hit skipped it and `dnaadjust` died with
  `libboost_program_options.so.1.83.0: cannot open shared object file` before a
  single fixture was compared. The job whose whole purpose is to catch fixture
  drift had silently stopped catching it. The install is now unconditional.

#### Added

- **`engines/dynadjust/read_output.py`** - the output parsers (FR-322, FR-323).
  `dnaadjust` writes up to four text files - `.adj`, `.xyz`, `.apu` and `.cor` -
  and these read all four into the same `Solution` the in-house core produces,
  which is what keeps everything downstream engine-agnostic and makes P6 a
  cross-validation rather than a second pipeline.

  **No table has a fixed layout**, so none is parsed as though it had. Which
  columns appear depends on the run: `--stn-coord-types` chooses the coordinate
  columns *and their widths*, `--stn-corrections` adds three, `--output-tstat-adj-msr`
  and `--output-database-ids` add more, and `--output-apu-vcv-units` renames
  three. Each file states its own options in its preamble, or shows them in its
  column-header line, so the plan is built per file from the widths in
  DynAdjust's own `dnaconsts-iostream.hpp` and a header that does not match is
  refused rather than guessed at.
- **`engines/dynadjust/columns.py`** - the fixed-width machinery, and the one
  thing about these files that cannot be parsed at all in the general case:
  `std::setw` pads but never truncates, and station names may be 30 characters
  in a 20-character column, so a long name runs into the next field **with no
  separator** (`A STATION WITH SPACESCCC`) - and names may contain spaces, so
  splitting on whitespace is no better than slicing. Resolved against the names
  GeoComp itself wrote, which it always knows; without them the ambiguous case
  raises and says what to pass instead of inventing a split.
- **`engines/dynadjust/solution.py`** - joining the four files into one
  `Solution`, including the full parameter covariance assembled from the
  `.apu`'s per-pair blocks.
- **`scripts/check_dynadjust_fixtures.py`** and the `engine` CI workflow - the
  guard against fixture drift. Every parser test reads committed real output,
  which is what keeps them tier 1; the cost is that a DynAdjust which changed a
  column would keep passing against a fixture written by the old one. This
  regenerates all twelve fixtures with a real engine built from a pinned commit
  and fails on any difference beyond the wall-clock timings. Numbers are
  compared to a part in a million rather than textually: two builds of a
  numerical program disagree in the last digits of an ill-conditioned inverse,
  and everything this guard exists to catch -- a moved column, an angle read in
  the wrong notation, a correction read as an angle rather than seconds -- is
  wrong by a factor. Token *positions* are still compared exactly, so a column
  that moved fails even when every value it holds is unchanged.

- **`engines/dynadjust/engine.py`** - the pipeline (FR-321, FR-325).
  `dnaimport` -> `dnareftran` -> `dnageoid` -> `dnasegment` -> `dnaadjust`, with
  `prepare`, `run` and `parse` separate so Advanced mode can stop after the
  input is written. **Every stage appears in the plan whether it runs or not,
  each with its reason**, because a provenance record that lists only what ran
  cannot distinguish a transformation that was unnecessary from one that was
  forgotten.
- **`engines/dynadjust/crossvalidation.py`** - the P6 exit criterion. Compares
  two `Solution`s on degrees of freedom, counts, variance factor, coordinates
  and residuals. Coordinates are compared only when both are in the same frame,
  and the check is real: differencing a geocentric X against a projected easting
  produces a number, and the number means nothing, so a frame mismatch is
  reported as not attempted rather than silently done.

  **The result, on upstream's `gnss-network` slice:** the in-house core and
  DynAdjust agree on degrees of freedom (3), observations (36) and parameters
  (33) exactly, on the variance factor to the three decimals DynAdjust prints,
  and on all eleven stations' coordinates to **0.047 mm** - with the core
  started from coordinates perturbed by up to five metres, so the agreement is
  not an artefact of the seed. Residuals agree to 0.05 mm.
- **`to_solution` now takes the coordinate system** instead of hard-coding
  `PROJECTED`. `Frame.SPACE_3D` is three orthogonal metres whatever they are
  called, so the core can hold a network in geocentric X, Y and Z; saying so is
  what lets the comparison above compare coordinates rather than refuse to.

- **`geocomp:analysis_dynadjust_adjust`** and **`geocomp:analysis_dynadjust_compare`**
  - the Processing face of both (FR-321, FR-323), under the *Analysis* menu
  beside the in-house adjustment. Which engine ran is an implementation choice
  about one operation, not a different kind of work: a menu organised by engine
  would ask a user to know which one they wanted before they knew what they
  wanted done. When DynAdjust is absent the algorithm still appears, and fails
  with a message saying how to get it rather than an import error (ADR-0003).

#### Fixed

Four unit errors that the files' own numbers do not reveal, each found by
checking one file against another rather than against itself:

- **The `.apu` ellipse orientation is HP notation**, not decimal degrees:
  `79.4724` is 79 deg 47 min 24 sec. `PrintPosUncertainty` writes `RadtoDms(azimuth)` with
  no branch on `--angular-stn-type`, so a file can hold decimal-degree
  coordinates and an HP orientation in the same row. Read as degrees it rotates
  every ellipse by up to a third of a degree - small enough to look right.
- **An angular measurement's correction and precisions are in seconds of arc**,
  while its `Measured` and `Adjusted` are degrees/minutes/seconds. Both branches
  of `PrintAdjMeasurementsAngular` wrap the former in `Seconds(...)` whatever
  format the latter took, so reading them alike is a factor of 3600 on every
  angular residual.
- **Angularity is a property of the component, not the type.** A `Y` cluster
  prints `P`, `L` and `H` under one type letter - two angles and a height - so a
  rule keyed on the type reads a height as an angle.
- **The `.cor` file writes separated fields** (`84 42 21`) where the `.adj`
  writes HP (`84.4221`) for the same kind of quantity. A reader that assumed one
  format for both divides by 100 in one of the two files.

- **`dnaimport` exits 0 on a measurement file it could not parse.** It warns on
  stdout - "some files were not parsed", "there are no measurements to
  process" - and returns success. Trusting the exit code alone carries an empty
  network into `dnaadjust`; worse, when only *part* of a file fails to parse, it
  carries an adjustment of fewer observations than intended, whose variance
  factor looks perfectly healthy. The pipeline now checks the counts
  `dnaimport` reports against what GeoComp wrote, which is exact - both numbers
  are known - rather than matching the warning's wording, which is not.
- **`test_a_half_installed_suite_names_the_missing_program` asserted something
  about the machine it ran on.** It put a lone `dnaimport` in a temporary
  directory and expected `dnaadjust` to be missing; on a machine with DynAdjust
  installed, `locate` finds it on `PATH` and the suite is complete - correct
  behaviour, failing test. It now empties `PATH` for its duration. Invisible
  until the new `engine` job started running the suite with DynAdjust present.

- **The DynaML writer declared `<Type>XYZ</Type>` and then wrote whatever the
  position held.** Correct only for a cartesian position. A geodetic latitude in
  radians went into `XAxis`, and a projected easting of 671 000 m put a UTM 22S
  station **845 km above the Earth's surface** — which DynAdjust accepts without
  complaint. It never showed up because the one network exercised end to end has
  absolute GNSS point observations, so DynAdjust computed its own approximate
  coordinates and discarded the nonsense; the cross-validation result is
  unaffected for the same reason. In a *relative* network — a traverse, a
  levelling line — the approximate coordinates set the datum, and the answer
  would have been wrong in a way that looks healthy. The type now follows the
  position: `XYZ` for cartesian, `LLH` with HP latitude and longitude for
  geodetic (which is what upstream's own files use and what GeoComp's reader
  reads back), and a **refusal** for projected, because DynaML's `UTM` needs a
  zone and hemisphere GeoComp cannot derive.

- **`HORIZONTAL_DISTANCE` had no row in the spec's measurement-type table at
  all** — not mapped, not listed as unmappable, simply absent from a table that
  called itself "the module's contract" and claimed every row confirmed. So the
  writer skipped it, and RD-03's trilateration lost **ten of its eleven
  observations** on the way to DynAdjust. It is genuinely unmappable — a
  horizontal distance is a distance in a plane, and DynAdjust's are ellipsoidal,
  sea-level or slope; converting needs the point scale factor and a height
  reduction, the same missing geodetic reductions as the projected-coordinate
  gap. Now documented with that reasoning, and
  `tests/structural/test_dynadjust_type_table.py` makes the table and the
  registry agree so neither can drift again.
- **A network DynAdjust cannot represent whole is now refused**, rather than
  adjusted in part. The remainder produces a variance factor and residuals that
  look healthy for a network the user does not have, with nothing in the result
  saying what was left out. `DynAdjustJob.allow_partial` accepts it explicitly.
  The writer still reports rather than refuses — exporting part of a network is
  a legitimate request — so the refusal sits at the layer whose promise is
  "adjust this network".

#### Phase P6 is not complete

Three of its seven exit criteria are outstanding, and
[`specs/ROADMAP.md`](specs/ROADMAP.md) records each with what it needs:

- **Cross-validation ran on one network, not three.** The other two are blocked
  on the same missing piece: GeoComp has no geodetic-to-geocentric conversion.
  For a network of GNSS baselines and points the core's local frame and
  DynAdjust's geocentric one coincide, because both observation equations are
  coordinate differences and the frame cancels; for a levelling or terrestrial
  network they do not, and the core's third component would be geocentric *Z*
  where DynAdjust's is ellipsoidal *height*.
- **The engine manager installs nothing**, because no DynAdjust release exists
  that can honestly be pinned. The install path is implemented and tested
  against synthetic archives; what is missing is a real release to point it at.
- **FR-161, the *Adjust* format, moves again** - still no example file with a
  published answer, and a parser written from a guess is not an implementation.

#### Known limits

- **The angular format is not in any preamble.** Only the recorded command line
  names it, and the `.xyz` and `.apu` files record no command line at all. Both
  readings of `-36.552865187` are valid HP, so it cannot be recovered from the
  number: the parsers take a declared format, fall back to the command line, and
  otherwise refuse. HP validation catches a decimal-degree value whose fraction
  is 0.60 or more, which is a useful net and not a guarantee.
- **`--dms-msr-format 1`** (degrees, minutes and seconds with symbols) is
  refused rather than parsed.
- **The engine CI job builds rather than downloads.** ADR-0003 prefers a pinned
  binary, but Geoscience Australia publishes Windows build artefacts and a
  `:latest` Docker Hub tag - neither a versioned, digest-addressable Linux
  binary. Building from an immutable commit is the pinnable option; `PINNED` in
  `engines/manager.py` stays empty until a release that can honestly be pinned
  exists.

### Phase P5 - Persistence, interoperability and reporting

#### Added

- **`io/store/`** - the GeoPackage project store (FR-130, FR-132, FR-134): a
  nineteen-table schema declared as data, written for SQLite and PostgreSQL from
  one declaration; write, read, supersede and delete; the referential protection
  that refuses to delete an observation a stored solution depends on (FR-135);
  and schema versioning with a backed-up migration path. Built on the standard
  library's `sqlite3` rather than GDAL, so it is exercised in eight of the nine
  CI jobs instead of one. Covariance is stored as a big-endian float64 blob and
  reloads bit-identically (NFR-007).
- **`io/tabular.py`** - CSV and `.xlsx` export of stations, observations,
  adjusted values, residuals and statistics (FR-161). The workbook is written
  directly as its OPC/SpreadsheetML zip, with fixed timestamps so the same
  solution produces the same bytes (NFR-007), and is verified by reading it back
  with `openpyxl` - an independent implementation, not this one.
- **`reports/`** - the adjustment report (FR-930, FR-931), template-driven and
  translated, built from a `Solution` and nothing else, so P6's DynAdjust
  solutions render through the same code.
- **`core/geoid.py` and `io/geoid.py`** - geoid models (FR-165, FR-804, FR-204).
  A model carries its identity, version, coverage and stated accuracy; grids are
  read from GTX and ESRI ASCII in pure Python, so a geoid works wherever the
  plugin does rather than only where GDAL is; and extrapolation beyond the stated
  coverage is refused rather than clamped.
- **The bilinear interpolation's own uncertainty is estimated from the grid**,
  by the local curvature over the cell, shaped per axis. For a separable
  quadratic it is not a bound but the error exactly; it goes to zero at a node,
  which a flat "assume a centimetre" figure would not, and it grows where the
  geoid curves sharply, which is where a bilinear interpolant is worst.
- **The height-type conversion P4 had to refuse** (FR-802, FR-804).
  `harmonise_benchmarks` converts a mixed set of benchmarks to orthometric - the
  system the levelled differences already measure - propagates the model's
  uncertainty in, records the model on the station and on the solution, and
  reports each conversion with its undulation and the size of the change.

- **Reference-system settings** (FR-065): preferred CRS, default epoch,
  transformation choice and preferred paths, transformation grid directory,
  default geoid model and its stated accuracy. Every default is empty or "ask",
  which is the design rather than an omission - GeoComp does not assume a CRS
  and refuses operations needing an epoch it was not given, so shipping a
  plausible default for either would make the plugin assume what the rest of it
  refuses. The geoid model's accuracy is a setting because no grid format
  carries it and the reader will not invent it.
- **`core/basemaps.py` and `layers/basemaps.py`** - base map integration
  (FR-167). Services are records with a URL, an attribution and an optional
  authentication reference, catalogued in a file that replaces the defaults
  wholesale. Attribution is required at construction, because a base map added
  without it puts the user in breach of the licence without telling them, and it
  is written into the layer's metadata so it reaches a print layout. **A URL
  carrying an embedded credential is refused** (NFR-010), naming the QGIS
  authentication database as where it belongs: a key in a URL is copied into
  every export and every log the moment a configuration is shared. A base map
  already in the project is reused rather than stacked - matched on its URL,
  since the layer name is the user's to change - and goes to the bottom of the
  tree, because above the results it hides what was just computed.
- **Four Processing algorithms** making the phase's work reachable:
  `geocomp:project_export` (FR-162), `project_report` (FR-930),
  `project_store` (FR-130) and `project_basemap` (FR-167). All three of the
  first take a solution document, so they chain onto any adjustment algorithm -
  and onto DynAdjust's in P6 without changing.
- **An eighth menu entry, Project**, and with it an empty
  `TOOLBOX_ONLY_JUSTIFICATIONS`. Six algorithms had accumulated with no menu
  home - P0's system report and tutorial dataset, and P5's four - and
  `test_the_toolbox_only_list_stays_small` failed when the sixth arrived, which
  is what it was written to do. Six exceptions are not exceptions; they are a
  category, and the honest answer to a category is an entry rather than a longer
  list of reasons it does not need one. They share a real description:
  operations on a project's *results* rather than on one technique's
  observations. FR-003 and FR-004 are amended, as they were in P2 for Analysis.
- **A ninth Global Settings section, Base maps.** An amendment to `specs/15`
  §2.1, which followed the proposal's list of eight; none of them is where a
  user would look for base map configuration, and putting it under Interface
  would make "Interface" mean "everything left over".

#### Fixed

- **`ConstraintMode.WEIGHTED` was declared and then ignored.** Only `FIXED` ever
  reached the adjustment, so a weighted station was estimated as though free and
  its published coordinates were discarded: a network held only by weighted
  constraints was rank-deficient rather than constrained, and one held by a fixed
  benchmark and several weighted ones silently used the first and dropped the
  rest - so the disagreement between benchmarks, the reason a user holds several,
  could never appear in the residuals. A weighted constraint is now an
  observation of the station's own coordinates and enters the system as one, with
  its covariance as a block rather than a diagonal (FR-104), a residual saying how
  far the station moved, and a contribution to the redundancy. Found while
  checking that a geoid-derived height's uncertainty reached the adjusted
  heights - it could not, because the constraint carrying it was not there.
- **Saving a network into a project store deleted every solution in it.** The
  store algorithm's "add" mode called `write`, which replaces — so adding this
  epoch's network to a monitoring project silently discarded last year's
  answers, and the GeoPackage on disk still looked healthy. `write` now takes
  `keep_solutions`, and the algorithm rewrites the project only when there is
  something new in it. The defect was found by a tier-3 test of the algorithm,
  which is the wrong place: it is a store defect, and it now has tier-1 tests
  that fail without the fix.
- **Every base map layer was invalid.** `QgsRasterLayer` was constructed with
  the service kind as its **provider key**, and QGIS has no provider called
  `xyz` or `wmts`: all three kinds load through the `wms` provider, with the
  kind carried in the URI as `type=`, which the URI builder already wrote. Only
  the CI QGIS job could catch it - without a runtime the layer is never
  constructed - and it did, on the commit that introduced it.
- **The enum-member check could not survive a lazy package.** It resolved each
  imported name with `getattr` on the module, guarding only the import; a
  package with a lazy `__getattr__` - which `geocomp.reports` became, above -
  resolves on *access*, so asking for a Qt-dependent name raised where nothing
  caught it. A name that cannot be resolved is simply not an enum this check can
  see, and is now skipped.
- **A tier-3 module errored instead of skipping without QGIS.**
  `tests/qgis/test_adjustment_report.py` carried `pytestmark = pytest.mark.qgis`,
  which labels and does not skip. Every other tier-3 module reaches QGIS through
  a fixture that skips, so the label being inert had never mattered; this one's
  fixtures did not need the provider, so nothing skipped and their lazy imports
  raised - twenty-five errors in the seven CI jobs with no QGIS.
  `tests/structural/test_tier3_skips_cleanly.py` now fails when a tier-3 module
  has neither `requires_qgis` in its `pytestmark` nor a skipping fixture reaching
  every test, autouse fixtures included.
- **`geocomp.reports` forced Qt on every importer.** The package re-exported the
  Qt-dependent report renderer eagerly, so importing the pure-Python template
  engine pulled in `qgis`, and the template engine's tier-1 tests failed to
  collect in the seven CI jobs that have no QGIS. The Qt-dependent names are now
  resolved on first access.
- **Two refusals where P4 had one.** Naming a geoid model without supplying its
  grid is refused separately from mixing height types with no model at all: a
  name records *which* model was used and cannot compute an undulation, so
  treating it as permission to mix would leave the heights wrong *and* the record
  asserting they had been corrected.

### Phase P4 - Level

A second technique, cheaply, by reusing P2 - and one written so that P8 inherits
the parts it needs rather than writing them again.

#### Added

- **`core/techniques/levelling/`** - the three sight schemes (FR-500, FR-501,
  FR-502), line and loop closures against a tolerance (FR-503), network
  assembly with two weighting models (FR-504), and the normal orthometric
  correction. Every result carries an uncertainty and an uncertainty mode
  (FR-505).
- **A line is reduced as a whole, not as a sum of setups.** One instrument
  levels the line, so there is one collimation error, carried through a single
  shared column. Per-setup imbalances of opposite sign then cancel as they
  physically do, and the uncertainty contribution is
  `(accumulated imbalance)^2 * var(c)` - *zero* for a balanced line, whatever
  the collimation is and whatever its own uncertainty. That is the mathematical
  statement of why equal sights is the preferred method. Summing independently
  reduced setups would give `sum(imbalance_i^2) * var(c)` instead, never zero
  unless every setup was individually balanced; the same mistake, in the same
  shape, as giving the two sights of a leap-frog pair independent refraction
  coefficients.
- **Extreme sights keep their correlation, and it helps.** The foresights of one
  setup share their backsight, so it cancels exactly between any two of them.
  Treating them as independent adds twice the backsight variance that is not
  there and reports an uncertainty too *large* - the opposite of the usual
  failure, and enough to have a network declared inadequate that is fine. The
  report shows both figures side by side and the percentage an independent
  treatment would have overstated by.
- **`core/adjustment/weighting.py` and `core/adjustment/difference_network.py`**,
  technique-neutral by construction. A gravity difference is the same
  observation equation as a height difference (ADR-0002, Amendment 1), so the
  weighting model (`sigma = k * sqrt(extent)`) and the 1D machinery around it -
  starting values by traversal, connectivity - would otherwise be written twice.
  `ExtentKind.DURATION` is there now for a gravimeter's drift rather than
  promised for later, and `tests/test_gravimetry_is_levelling.py` asserts both
  work unchanged in the gravity frame. An abstraction used once is an assertion;
  used twice, it is a design.
- **`io/levelbook.py`** (FR-160) - both common field-book layouts, with which
  one a file uses worked out from the mapped columns rather than asked for, and
  three-wire readings that give the sight distance by stadia and a half-sum
  check that catches a misread wire.
- **Six Processing algorithms and a populated Level menu** - import (FR-160),
  equal sights (FR-500), equidistant sights (FR-501), extreme sights (FR-502),
  closures (FR-503) and network adjustment (FR-504). Equal and extreme sights
  share an implementation and are still two entries: one reduces a *line* to one
  height difference between two marks, the other a *setup* to several that are
  correlated with each other.
- **The `level` settings section** (FR-061, FR-503, FR-504), and labels for the
  seventeen settings P3 declared - see Fixed.
- **RD-04** (`tests/reference_levelling.py`). Its books are generated from known
  heights by inverting the very equations under test, so a sign error produces a
  line that fails to recover a height it must recover *exactly*. Not a
  transcription from Ghilani or Gemael; that remains outstanding and is recorded
  in `specs/20`.
- **`Strategy.RECORDED_PRECISION`** - a sigma taken from how many digits were
  written: `32.4` lies in `[32.35, 32.45)`, so sigma is `0.05/sqrt(3)`.
  Deliberately narrow, and not a hole in *GeoComp does not invent a sigma*: the
  digits are real information, present in the file. Permitted only for a sight
  distance, whose uncertainty reaches the answer multiplied by a collimation of
  order 1e-4. A staff reading, whose sigma becomes an adjustment weight, still
  refuses.

#### Decided

- **GeoComp ships no national tolerance table.** The permissible misclosure is
  `k*sqrt(L)` everywhere, but *k* differs by country, by class within a country
  and by edition of the standard, and a transcribed value that is wrong does not
  fail loudly - it silently accepts a line that should have been re-run. A
  levelling class is a record the user fills in from the specification in front
  of them, carrying the document it came from. **With no k configured there is no
  verdict**: `passed` is neither true nor false but absent, because a check that
  reports success when it could not test anything is worse than one that admits
  it.
- **The misclosure distribution says what it cannot do.** Proportional
  distribution is the classical correction and many specifications require it,
  so it is computed - but it localises nothing, so a blunder is smeared evenly
  along the line and made harder to find. The misclosure is therefore also
  compared with its own propagated standard deviation, and the report says which
  situation the user is in: consistent with accumulated random error, in which
  case distribute it, or not, in which case the network adjustment with data
  snooping is what will find it.
- **Turning points are not network stations.** A turning point existed for four
  minutes and has no mark; adding it contributes one parameter and one
  observation, so no redundancy, no effect, and a solution cluttered with points
  that cannot be checked.
- **The levelling network algorithm offers no map layers.** A levelling network
  has no planimetry, so every station would be drawn at the same point. Saying
  so beats shipping a layer of coincident markers.
- **Only the *normal* orthometric correction is implemented.** The rigorous one
  needs observed gravity along the line and is not approximated here with an
  assumed field pretending to be a measured one. It arrives with P8, where the
  gravity observations do.

#### Fixed

- **A 1D solution wrote its heights into the *easting* slot**, so every
  levelling result would have reported a height of zero. P2's `to_solution`
  padded the frame's components into the position triple in order, while
  `starting_values` read them back by name - the two halves of one
  correspondence, disagreeing. Nothing caught it because no test had read a 1D
  solution through its `Position`. The correspondence is now stated once, as
  `Frame.position_components`, and both directions go through it.
- **The Global Settings dialog rendered its raw dotted key** for all seventeen
  settings phase P3 declared: a user saw `total_station.atmospheric_model`, in
  every language. The dialog is generated from the declarations but the labels
  are not, and nothing checked the correspondence.
  `tests/structural/test_settings_labels.py` now fails when a setting, a choice
  or a section has no label.
- **A three-wire mean was drafted using the sample spread of the three wires as
  its precision.** The wires read deliberately different heights, so that spread
  is the stadia interval - the draft reported a reading good to half a
  millimetre as good to five centimetres. Caught before it was committed, and
  the test that would have caught it is now in the suite. The empirical figure a
  three-wire set does carry is the half-sum residual, pooled across a line.

1287 tests pass locally against QGIS 3.34 (16 skipped for needing QGIS >= 3.38),
1138 without QGIS. Both translation catalogues complete at 1045/1045.

### Phase P3 - Total station

The first end-to-end vertical slice: raw field book to adjusted, statistically
validated network, with no external engine anywhere in the path.

#### Added

- **`core/techniques/total_station/`** - face reduction with its diagnostics,
  instrument and EDM corrections, the first-velocity atmospheric correction, the
  basic reductions with the d-z correlation kept, and the geometric reductions
  (FR-400 to FR-405, FR-412). Every stage separately callable and separately
  inspectable, which is the teaching requirement; every stage propagating
  covariance.
- **Survey computations** - traverse in all three forms with both classical
  rules and the misclosure checks (FR-406); resection with danger-circle
  detection (FR-407); forward intersection reporting weak geometry through the
  error ellipse (FR-408); classical networks assembled for the P2 core (FR-409);
  trigonometric levelling including leap-frog (FR-410); 3D radiation with its
  full 3x3 covariance (FR-411).
- **`core/instruments/`** - named instrument and reflector profiles with a
  per-constant uncertainty and the applied-once rule, and the stochastic model
  resolution whose last step refuses rather than inventing a sigma (FR-061,
  FR-064, FR-069).
- **Eight Processing algorithms and the Total Station menu** - import field
  book (FR-160), generalised pre-processing (FR-400), traverse (FR-406),
  resection (FR-407), forward intersection (FR-408), classical network
  (FR-409), trigonometric levelling (FR-410) and 3D radiation (FR-411). Each
  writes an HTML report, a machine-readable document and scalar outputs, and
  each one's document is the next one's input so the chain assembles in the
  graphical modeller (FR-033).
- **A synthetic survey fixture with known coordinates** (`tests/synthetic.py`).
  RD-01 stays the reference for face reduction and free-network adjustment, but
  it has no known point, so it cannot check a traverse, a resection or a
  radiation at all. The fixture generates the readings a total station would
  have recorded standing at coordinates chosen in advance, and every routine is
  asked to recover the geometry it was generated from - so the expected values
  are the survey itself rather than a previous output.
- **A structural check on the tier-3 tests' parameter names.** Those tests only
  run where QGIS does, and Processing *ignores* an unrecognised key rather than
  rejecting it, so a mistyped parameter silently becomes a default and fails
  somewhere else. Every key is now checked against the declaring algorithm by
  parsing, which works without QGIS installed.
- **Styled result layers** (FR-900, FR-904, FR-905). Both adjustments now offer
  the same five map layers: adjusted stations sized by their positional
  uncertainty, error ellipses, observations coloured by what the w-test decided
  about them, the measured network by observation type, and coordinate
  correction vectors. They arrive styled, which is what "visualização imediata"
  asked for -- a user who runs an adjustment sees the result rather than styling
  five layers by hand. None is created unless asked for, so an adjustment run to
  feed another algorithm writes nothing extra.
- **Five QML style files** in `geocomp/resources/styles/`, editable in the layer
  properties dialog and re-saveable over the shipped file. Code applies a style;
  it does not contain one. Uncertainty maps to size and significance to colour
  across every layer, so the plugin reads as one system; the palette is
  Okabe-Ito, which survives every common colour-vision deficiency and greyscale
  printing, because these layers end up in technical reports. Significance is
  three symbols rather than a ramp, because the w-test gives three answers --
  and an observation nothing could be tested about is not a passing one.
- **`core/visualization/`** - ellipse rings, vector tips and the first
  exaggeration factor, with no QGIS in them, so the vertices are checked against
  closed-form values rather than only inside a QGIS runtime.
- **RD-01 ships as a tutorial dataset** (FR-950, FR-952), with
  `geocomp:project_tutorial_dataset` to copy it somewhere writable -- a plugin
  directory usually is not, and a tutorial that starts "first find your own
  data" is not a tutorial. The dataset carries its field book, a saved field
  mapping, an instrument profile library, approximate coordinates, and a
  tutorial that walks the whole chain.

  **Both of its defects are the lesson rather than a caveat.** The 1.000 m
  face-pair discrepancy is a transcription blunder that pre-processing blocks
  instead of averaging away, and the global test fails correctly because the
  distances disagree between the two ends by far more than the instrument's
  stated precision. Software catching two genuine errors in genuine data teaches
  more than a clean run. The tutorial also explains why a network with no known
  point and no azimuth can only be adjusted with inner constraints.

  Every number the prose states is checked against the constants the reference
  tests use, and the whole chain is run on the shipped files -- with the shipped
  mapping and profiles, as a reader would -- so the tutorial cannot drift from
  the software it describes.
- **The field-mapping dialog** (FR-160), the second of the enumerated custom
  dialogs in `specs/15` §3. Mapping columns onto fields is impossible without
  seeing the data in them: a combo box offering `HS` and `hs` tells a user
  nothing, and a preview showing `48` under one and `1.500` under the other
  tells them everything -- and in RD-01 those two columns are the seconds of a
  horizontal angle and a target height.

  The dialog is a **view**. Every decision it makes -- which fields are still
  unmapped, which column got assigned twice, whether the result can be used --
  is made by `io/mapping_editor.py`, which has no Qt in it and is tested without
  QGIS. It reports every problem at once rather than one at a time, blocks on a
  missing required field or a column assigned twice, and mentions an unmapped
  column without blocking. Assigning a column already in use does not silently
  steal it from the other field: which one the user meant is not something the
  editor can know, so it says so.

  A saved mapping is the feature rather than a convenience on it: an
  organisation defines its instrument's export layout once and distributes the
  file. Saving is allowed while the mapping is still incomplete, because half a
  mapping of a forty-column export is worth keeping.
- **The interactive pre-analysis dialog** (FR-272), re-planned out of P2 into
  the phase with a QGIS job that can verify it. A design is placed on the canvas
  -- stations clicked in, observations drawn between them, dragged, removed --
  and re-evaluated after every change, with the expected ellipses drawn over
  whatever basemap is loaded. That loop is the reason pre-analysis belongs in a
  GIS: a spreadsheet can compute Σx, but it cannot let a surveyor watch the
  ellipses shrink as they drag a station onto ground the orthophoto tells them
  is accessible.

  **Evaluation never raises.** A design under construction spends most of its
  life un-evaluable -- one station, no observations, three stations and a rank
  defect -- and a loop that threw on each of those would be unusable. A design
  that cannot be evaluated reports why, as findings, in the same shape as one
  that can be evaluated but is poor, so the panel renders one thing rather than
  branching on which kind of answer arrived. The messages are actionable:
  "connect two stations to begin", not "singular normal matrix".

  Removing a station takes its observations with it, because leaving them gives
  a network referring to a station that does not exist, which fails deep in the
  adjustment with a message about a missing parameter rather than about the
  click that caused it. Planned directions from one setup form one cluster, as
  the model requires -- splitting them would drop the orientation unknown and
  evaluate a network nobody could observe. Every edit is undoable: editing on a
  canvas without undo is punishing, and a design network is small enough that
  snapshotting it costs nothing.

  As with field mapping, the dialog is a view: `core/preanalysis/session.py`
  holds every rule and is tested without QGIS, and the dialog hands its design
  to `geocomp:analysis_network_preanalysis` for the report, so an interactive
  design and a loaded one are evaluated by identical code.
- **`registry.CUSTOM_DIALOGS`** enumerates which algorithms open a custom dialog
  before the standard Processing one, and why. The custom dialog never replaces
  the algorithm (ADR-0005): it fills in parameters and hands them to the same
  dialog every other menu item opens, so one implementation is reachable
  identically from the menu, the toolbox and the modeller. A structural check
  holds the declarations and the handlers equal, requires each reason to cite a
  requirement, and fails if the set grows past the six the specification
  enumerates -- a growing list means the generated UI is being abandoned one
  dialog at a time.

#### The exaggeration factor, and why it is a required argument

`specs/19` calls an unstated exaggeration the single most important rule in the
document: a 5 mm semi-axis is a micron at 1:5000, so every drawn ellipse is
enlarged, and one that does not say by how much is a misrepresentation rather
than a visualisation.

It is therefore not defaulted anywhere. Every function that produces drawn
geometry takes `exaggeration` keyword-only and without a default, so a call site
cannot omit it; the factor travels on the geometry it produced rather than
beside it; and the layer's name -- which is what reaches the legend -- is
composed from the same argument the vertices used, so the two cannot disagree. A
structural check enforces all of that by parsing, and a tier-3 test follows one
factor from the parameter through the ring to the name and the attribute table.

Where no factor is given, one is fitted to the network's own extent, since an
algorithm has no map canvas to measure, and rounded down to a 1-2-5 value: a
legend reading "x500" is read at a glance and "x487.3" is not. It is never below
1. Shrinking an ellipse understates the uncertainty, which is the failure the
rule exists to prevent.

#### Fixed in the phase P2 core

Both found by running direction sets end to end for the first time, and both
producing a diverging adjustment whose only symptom was a convergence failure
that said nothing about the cause.

- **Angular misclosures are wrapped to the short way round the circle.** A
  direction read as 353 degrees against a computed -7 differs by nothing; the
  plain subtraction made it 360, which entered the normal equations as an
  enormous residual. P2's own networks happened to have every angular
  observation near its computed value, so the wrap never arose.
- **A direction set's orientation unknown is derived from the observations and
  started from the data.** It was previously left to the caller to declare and
  initialised at zero. A direction without an orientation unknown is always
  wrong, and zero is essentially never the right starting value, so both are now
  automatic.

#### Fixed while testing the algorithms

- **A closed traverse left without a closing azimuth no longer checks itself
  against north.** The parameter fell through to zero, so an untouched field
  produced an angular misclosure of several hundred degrees that read as a
  catastrophic survey. A loop that backsights the station it returns from
  arrives on the very line its start azimuth refers to, so that case is now
  inferred; anything else says plainly that the angles cannot be checked.
- **An exactly closing traverse no longer reports the worst possible relative
  precision.** The ratio is absent for two opposite reasons - a zero misclosure
  and an open traverse - and one sentinel of `0.0` for both read as 1:0.
- **`ErrorEllipse` no longer documents a `scale_factor` it never had.** The
  exaggeration belongs to a drawing, not to a confidence region: the same
  ellipse on two maps at two scales is one ellipse. It lives on `DrawnEllipse`
  instead, where it is required.
- **The spread of the orientations implied by several known points was
  identically zero for two of them**, which is the commonest case in a detail
  survey. It was the range of the *absolute* deviations, and two estimates
  always sit symmetrically about their own mean. It is now the range of the
  signed deviations, and a spread beyond three times the pointing precision is
  warned about by name: one of the control points is not where it is recorded,
  and every point radiated from that setup carries the error.

#### The QGIS job had been red since P2, and nobody looked

Ten consecutive CI runs failed and were reported here as "CI-pending" rather than
checked. Every other job was green; the `qgis integration` job was not. The tier-3
suite was being written against an environment nobody had run it in.

Running QGIS locally — `apt-get install qgis python3-qgis`, which takes a
minute — found **six real defects** that no amount of tier-1 testing could have
reached. They are listed below because the class of each matters more than the
instance.

- **`np.bool_` is not a `bool`.** The w-test's `passed` came from comparing two
  NumPy scalars, and `np.bool_` does not subclass `bool`, so the JSON encoder
  refused it. *Every adjustment that wrote a solution* failed at the last step
  with a `TypeError` naming neither the field nor the test. Coerced now in
  `TestResult` and `ObservationResult`, floats included: `np.float64` *does*
  subclass `float` and serialises silently, and it was the silent half that let
  the loud half through unnoticed.
- **`ErrorEllipse.azimuth` does not exist** — the field is `orientation`. Five
  call sites, in the report and CSV paths of four algorithms, dating from P2.
  This is what had been failing CI since P2.
- **`AngleFormat.SEXAGESIMAL_STRING` does not exist** — it is `SEXAGESIMAL_TEXT`.
  In the field-mapping dialog's label table, so the dialog raised on
  construction. Shipped in the commit that introduced it.
- **The result-layer sinks were built even when nobody asked for one.** All five
  are optional, so the common case is that most are absent; building their field
  lists anyway meant a layer concern could take down an adjustment that requested
  no layers. It did.
- **The Classical network algorithm declared its CRS optional and then required
  it**, failing deep in `Position` with "GeoComp does not infer one" rather than
  at the empty field. Now required, and refused early by name.
- **The pre-analysis dialog did not give the canvas back** when the canvas had no
  tool before it: `setMapTool(None)` does not clear the current tool. The user
  would be left clicking stations into a design no longer on screen.

Two of these were also design faults rather than slips, and are fixed as such:
the traverse's closing easting, northing and azimuth had a numeric default of
`0.0`, which is not a closing azimuth but *north*, and which broke FR-071's
promise that Basic and Advanced compute the same thing — "left blank" was
inferred while "at its default" was due north. They are optional with no default
now. And the tutorial's step 2 needed the profile library a second time without
saying so, which is now both documented and refused by name.

**Guards added, so the classes cannot recur silently:**

- A tier-1 test that a real adjustment's `Solution` serialises, round-trips, and
  contains no NumPy scalar at all. The bug reached the algorithms only because
  no tier-1 test had ever asked a solution to serialise — they checked the
  numbers and stopped.
- A structural check that every `Enum.MEMBER` written anywhere in the plugin is a
  member that exists, by parsing rather than importing, so it covers the Qt-only
  modules that tier 1 cannot import. Verified against the exact typo that shipped.
- `README.md` now documents how to run tier 3 locally, and says to do it before
  believing a change works.
- Tier-3 tests needing a QGIS newer than the one installed now **skip with the
  reason stated** rather than failing, so a red local run is a real one. Sixteen
  do: `QgsField(name, QMetaType.Type)` needs QGIS ≥ 3.38, and Ubuntu ships 3.34.

Local result after the fixes: **132 tier-3 tests pass, 16 skip, none fail.**

**Then CI was still red, and the local pass was not the proof it looked like.**
This container has QGIS 3.34 with PyQt5 and NumPy 1.26; CI has QGIS 4.3 with
PyQt6 and NumPy 2.2. Five more defects lived only in that gap, and each needed
the version CI runs:

- **A feature sink's `type` is a `ProcessingSourceType`, not a WKB geometry.**
  Passing the wrong enum raises inside a C++ virtual — printed under PyQt5,
  **fatal under PyQt6** — so the provider aborted with exit 134 in
  `loadAlgorithms`, all 148 tier-3 tests died at once, and the traceback named
  the provider rather than the algorithm. That abort, not any test failure, is
  what the job had been reporting for ten runs. `scripts/diagnose_provider.py`
  now walks the registry one algorithm at a time so the last line before an
  abort names the culprit; it found this on its first run.
- **A sink's CRS is a `QgsCoordinateReferenceSystem` in QGIS 4**, not the string
  QGIS 3 took.
- **`repr()` of a NumPy scalar is `"np.float64(1.93e-06)"` under NumPy 2.** The
  CSV writers used `repr` to get full round-trip precision, so on NumPy 2 every
  table an adjustment wrote became unparseable — and the same code produced two
  different files depending on a version nobody had pinned. One helper,
  `reporting.exact()`, converts to a built-in float first.
- **A held station is not in `adjusted_stations`**, so locating stations from the
  solution alone left every observation touching one without a line: five of
  eleven on the trilateration network, and precisely the ones tying it to its
  datum. Positions now fall back to the network's approximate and constraint
  coordinates.
- **The exaggeration factor reached the layer name only via the post-processor**,
  which Processing runs when loading a layer into the project and not for a
  model or script run. FR-901 requires the factor to reach the reader; on one of
  three paths is not that. Layers are named during the run as well.

Two more were mine in the tests rather than the product: `QMouseEvent` from a
`QPoint`, an overload Qt6 dropped; and a residual-count assertion that was right
about the number and wrong about which number.

**CI is green** — all nine jobs, for the first time since P1.

#### Gravimetric adjustment is levelling adjustment

*Raised in review.* ADR-0002 justified the in-house core partly on "gravimetry
has no alternative", and the engine table said DynAdjust could not adjust a
gravimetric network. The observation equation of a gravity difference **is** the
observation equation of a height difference — GeoComp already implements them as
one function, `_difference_1d`, called with the component `"g"` or `"h"` — so a
drift-corrected gravimetric network is a 1D difference network under a
relabelling, and DynAdjust adjusts those.

What DynAdjust genuinely cannot do is the gravimetric corrections and **drift
estimated jointly with the network**, which matters because drift and gravity
differences are not separable by pre-correction alone.

The decision stands on its other three rationales; the reasoning is corrected in
**ADR-0002, Amendment 1**. `tests/test_gravimetry_is_levelling.py` makes the
identity executable: the two design matrices are identical element for element,
and the two adjustments agree on estimates, residuals, variance factor and
redundancy. Three consequences, all gains: **P8 is much smaller** than planned,
**P6 gains a gravimetric cross-validation case** it was assumed not to have, and
it is the reason **P9's combined adjustment** is possible at all. The roadmap's
P4 and P8 entries now say so.

It also surfaced a smaller thing worth recording rather than fixing now: a
gravity parameter's *value* is carried in the `up` component of a `Position`,
which enforces metres, so a milligal arrives through a field that describes it
wrongly. The arithmetic is unaffected — the frame never mixes the two — and
giving gravity its own parameter carrier is P8's work. A test asserts the present
state so that the day it is fixed, it fails and points at itself.

#### Where phase P3 stands

Against the exit criteria in [`specs/ROADMAP.md`](specs/ROADMAP.md), verified in
this environment with **no QGIS, no SciPy and no external engine** — 865 tests:

- RD-01's 1.000 m face-pair discrepancy is flagged as a blunder candidate and
  the pointing is kept out of the observations, never averaged. ✔
- The PD = 181° / PI = 1° wrap case returns 181°, and the arithmetic mean it is
  contrasted with is asserted alongside it so the test says what it is for. ✔
- RD-01 reproduces `topo_test/processed_data.csv` **except for the one direction
  the published file has 180° wrong**, established two independent ways. Every
  value carries an uncertainty. ✔ with the documented exception.
- A planned station added on the canvas re-evaluates the design without leaving
  the map — the loop itself is tested here; the canvas is CI's. ✔
- Basic and Advanced defaults give identical numbers, for the Analysis group and
  the Total Station group. ✔ *(runs in CI)*

**Tier 3 runs in both places now.** Locally, against QGIS 3.34 from the
distribution: 1114 pass and 16 skip for needing QGIS ≥ 3.38. In CI, against QGIS
4.3: **1130 pass, none fail.** The claim that all 148 were "CI-pending" was made
while CI had been failing for ten runs; see above. Neither environment alone was
sufficient — the local one found six defects the QGIS-free tiers could not
reach, and CI found five more that only QGIS 4, PyQt6 and NumPy 2 expose.

#### Notes

- **RD-01 carries two defects, and both are now tests.** The 1.000 m face-pair
  distance discrepancy is flagged as blocking and the pointing is kept out of
  the observations. And the prototype's arithmetic-mean face reduction puts one
  of its six directions exactly 180 degrees out - which `specs/09` had recorded
  as "correct for the RD-01 data". Two independent checks settle it, and
  acceptance criterion 1 is amended, because it could not have been met by a
  correct implementation.
- **RD-01 is a free network.** It contains no azimuth and no known point, so its
  datum defect is two translations and a rotation, and it can only be adjusted
  with inner or minimum constraints. A property of the dataset, now asserted.
- The whole slice runs in the test suite with no QGIS and no engines: reduce,
  assemble, inspect, adjust, test.


### Phase P2 - Adjustment core

The phase the project turns on. Least squares with its full statistical treatment, plus network design -
the engine behind four later modules, and what makes ADR-0002 real: gravimetric adjustment and pre-analysis
have no external engine at all. Still runs with no QGIS and no SciPy.

#### Added

- **`core/adjustment/`** - the parametric model `Lb + v = Ax + L0` end to end. Observation equations with
  analytic Jacobians for twelve types (1D height and gravity, 2D distance, angle, direction with its
  orientation unknown, azimuth, 3D slope distance, zenith angle, GNSS baseline and point), dispatched
  through the observation type registry so a new type stays a registry entry. Normal equations from the
  full weight matrix including correlated clusters; Cholesky with a QR fallback; iteration to convergence
  with **non-convergence reported as a failure, never a silently returned last iterate** (FR-220 to
  FR-227).
- **Datum handling** - `FIXED`, `WEIGHTED`, `MINIMUM_CONSTRAINT` and `INNER_CONSTRAINT`, the last two via
  the trace-minimum **G** matrix over a chosen station set, which is what deformation analysis needs:
  holding a station that has itself moved spreads its motion across the network. The defect is detected
  from the observation content and recorded on the solution rather than assumed (FR-222).
- **Rank diagnosis (FR-226)** - a singular system produces a sentence naming the stations and components
  in each undetermined direction, not a number and not a crash.
- **`core/statistics/`** - the two-sided global chi-square test (an unexpectedly *small* variance factor is
  information, not a pass); Baarda's w-test with the tau variant when sigma-nought is estimated, reporting
  which was used; redundancy numbers, minimal detectable bias and external reliability, with uncheckable
  observations flagged; absolute and relative error ellipses and 3D ellipsoids, chi-square or F scaled
  (FR-250 to FR-254).
- **Nothing is rejected automatically** (FR-255). Data snooping returns candidates; the decision is the
  user's, and re-adjustment after a rejection is a second explicit run.
- **`core/statistics/distributions.py`** - normal, chi-square, F and t with a SciPy fast path and a
  complete NumPy-only fallback (Acklam plus Newton; the regularised incomplete gamma; Lentz's continued
  fraction for the incomplete beta). Both paths tested against published tables and against each other.
- **`core/preanalysis/`** - design simulation, `Sigma_x = sigma_0^2 (A^T P A)^-1` from geometry and assumed
  precisions with no observations at all, reporting expected ellipses *and* expected reliability (FR-270,
  FR-271); and network inspection on real data - connectivity, isolated stations, insufficient
  observations, duplicates, missing approximate coordinates - returning every finding in one pass rather
  than stopping at the first (FR-273).
- **Three Processing algorithms** - `geocomp:analysis_network_inspect`,
  `geocomp:analysis_network_preanalysis` and `geocomp:analysis_network_adjust`, each with HTML and CSV
  outputs and scalar outputs so they chain in the graphical modeller.
- **The Analysis menu group**, the seventh top-level entry. `specs/15` §1.1 left its placement open; P2
  needed it and settled it, and FR-003 and FR-004 were amended to say seven rather than being contradicted
  by the code.
- **RD-03 and RD-09 reference networks** - 1D levelling, 2D trilateration, 2D triangulateration, free and
  constrained, with a known truth; and the same with a blunder of known size at a known place, which is
  the only way to test detection against ground truth rather than against another computation.
- **Structural check for message templates** - a template that interpolates a context key its raising site
  never supplies renders "(not set)" to the user and raises nothing. Both sides are now read as source and
  cross-checked.

#### Notes

- The tests that carry the weight are the *identities*, because they hold for every network rather than
  one: redundancy numbers sum to the degrees of freedom; a free and a constrained solution agree on
  residuals and on the variance factor; design simulation reproduces the adjustment's covariance to
  machine precision at the adjusted coordinates; every analytic Jacobian matches complex-step
  differentiation.
- **RD-03 and RD-09 are not transcriptions from Ghilani or Gemael.** Those books are unavailable here and
  inventing a citation would be worse than having none. They are validated against closed forms where one
  exists and against the identities above everywhere else; transcribing the published worked examples
  remains outstanding and is recorded in `specs/20`.
- **The sparse solver is not implemented.** The dense NumPy path is correct at every size and comfortable
  to roughly 2,000-3,000 stations. NFR-008 was reworded and the sparse path assigned to P12, where a
  network large enough to measure it will exist
  ([`specs/adr/0008-scipy-and-network-scale.md`](specs/adr/0008-scipy-and-network-scale.md)).
- **FR-272 moved to P3.** P2 ships the pre-analysis mathematics and the Processing algorithm; the
  interactive canvas dialog needs a running QGIS to verify, and shipping interaction code nobody has run
  is how a phase reports done while leaving a defect.
- Ellipses and the a priori variance factor now reach the `Solution` itself, so a DynAdjust result in P6
  fills the same structure on the same terms.


### Phase P1 - Core domain and uncertainty

The types everything else is built from, and the property that defines this project: no geodetic value
without an uncertainty. Still no QGIS dependency anywhere in this layer, and still no external engine.

#### Added

- **`core/units.py`** - SI and radians internally; DMS, gon, feet and mGal converted at the boundary and
  never stored. Sexagesimal parsing for field-book layouts, and a circular mean, which is what makes a
  face-left/face-right reduction correct across the zero of the horizontal circle.
- **`core/uncertainty.py`** - `Quantity` (value, variance, unit, rigorous-or-approximate mode) with
  propagating arithmetic and unit checking, and `Covariance` (labelled, symmetry- and PSD-validated) with
  rigorous propagation `Sigma_out = A Sigma A^T` (FR-200 to FR-208).
- **The correlation guard.** A quantity drawn from a covariance is tagged with it, and combining two
  quantities carrying the same tag through scalar arithmetic raises. This turns the most dangerous silent
  error in the system - treating correlated inputs as independent - into a loud one. `.detached()` is the
  explicit, documented escape hatch.
- **`core/differentiation.py`** - complex-step and central-difference Jacobians. The complex step is exact
  to machine precision and is what every analytic Jacobian is verified against, because a sign error there
  produces a plausible-looking wrong uncertainty rather than an error.
- **`core/models/`** - Epoch, Position, Station, ConstraintSpec, Observation, Cluster, GnssSession, Network,
  Campaign, Project, Solution and Provenance, with the observation type registry and lossless JSON
  round-tripping (FR-100 to FR-107).
- **RD-02 reference cases**, each validated three ways: a hand-derived closed form, the module's first-order
  propagation, and a derivative-free Monte Carlo simulation.
- **Structural check for FR-200**: a new plain-float field on a model class fails the build until someone
  decides whether it is a measurement or a diagnostic.

#### Notes

- Constraints are per component, not per station, so the routine case of a benchmark fixed in height and
  free in plan is expressible.
- Gravity carries no DynAdjust measurement type in the registry, which is the concrete form of ADR-0002:
  a required menu group with no engine behind it.
- NumPy is a hard dependency from this phase (it ships with QGIS); SciPy remains optional, and CI tests the
  SciPy-absent path.


## [0.1.0] — Phase P0, Foundations

The first phase of [`specs/ROADMAP.md`](specs/ROADMAP.md). The plugin installs, loads, shows its menu and
its Processing provider, reads its settings, logs, tests and packages. **Nothing computes yet** — P0's job is
that everything which will compute has somewhere to live and a way to be tested, translated and shipped.

### Added

- **Plugin lifecycle** — `classFactory`, `initGui` / `unload`, the GeoComp menu on the QGIS menu bar with the
  six specified entries, a toolbar, and an About dialog under Plugins (FR-001…FR-007).
- **Processing provider** `geocomp`, with algorithms declared in a single QGIS-free registry that the menu
  and the toolbox both read, so the two cannot drift apart (FR-030…FR-032, ADR-0005).
- **Pure-Python core** — the exception hierarchy with stable machine-readable codes, the cancellation and
  progress protocols, the setting declarations, and layered settings resolution. Imports and runs with no
  QGIS (NFR-002).
- **Layered settings** — `run → project → global → built-in default`, with the origin scope of every
  effective value recoverable and shown in the UI (FR-068).
- **Global Settings window** with a side menu by equipment type, its pages generated from the setting
  declarations so a setting cannot exist without a UI (FR-060, FR-067).
- **Trilingual infrastructure** wired from the first commit rather than retrofitted: `tr()` discipline,
  catalogue extraction with an AST fallback for environments without the Qt tools, and complete pt-BR and es
  catalogues (FR-090…FR-095).
- **`geocomp:project_system_report`** — reports versions, engine availability and every setting with its
  origin scope. Proves the registry → provider → menu path, and answers the first question of any support
  request.
- **Structural CI checks** — no QGIS in the core, i18n string discipline, menu/algorithm parity, requirement
  phase partition, spec link integrity, SPDX headers, version consistency, translation completeness.
- **Reproducible packaging** — `scripts/build.py` produces a byte-identical ZIP for a given commit.

### Notes

- Minimum QGIS is **4.0.0**; the 3.x series is deliberately not supported
  ([`specs/adr/0007-qgis-4-minimum.md`](specs/adr/0007-qgis-4-minimum.md)).
- Marked `experimental=True` in `metadata.txt` until a phase ships geodetic computation.
- DynAdjust and RTKLIB are not integrated yet: they arrive in P6 and P7. The system report says so rather
  than reporting them as missing.
