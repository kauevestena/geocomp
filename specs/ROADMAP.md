# GeoComp — Implementation roadmap

**Status:** Draft
**Supersedes:** [`archive/2025-plugin-roadmap-v2.md`](./archive/2025-plugin-roadmap-v2.md) — see
[`archive/README.md`](./archive/README.md) for what was carried forward and what was rejected.

This document says **when**. The specification documents say **what**. Implement from both: open the phase,
read the specs it lists, satisfy the requirement IDs it closes, meet the exit criteria.

---

## How this roadmap differs from the archived one

Four deliberate changes, each a consequence of reading the research project rather than the previous plan:

1. **A complete, demoable product exists by P3, with no external binary.** The archived roadmap made
   DynAdjust a prerequisite for anything to compute, so nothing worked — and nothing could be tested in CI —
   until phase 4 of 10. Here the in-house core (ADR-0002) carries a full vertical slice early.
2. **i18n and settings land in P0.** The archived roadmap deferred i18n to phase 9. Wrapping a string as you
   write it is free; retrofitting several thousand is not, and is invariably deferred again.
3. **DynAdjust arrives as a *second* engine (P6), not the first.** This turns integration into
   cross-validation: the same network adjusted two ways must agree, which is far stronger evidence than
   either alone.
4. **The missing half of the project is planned.** Covariance propagation (P1), statistical validation and
   pre-analysis (P2), gravimetry (P8) and multi-epoch monitoring (P10) are absent from the archived roadmap
   and are between them a large fraction of the work.

## Sequencing principles

- **Every phase ends with something a user can run.** No phase delivers only scaffolding.
- **Nothing is scaffolded ahead of use.** Files are created by the phase that fills them — the archived
  roadmap's "create these files even if initially empty" is rejected.
- **Pure computation before integration.** `core/` is testable in milliseconds; engines are not.
- **Each phase closes its requirements.** A phase is not done while an ID it claims is unmet.
- **NFRs are standing.** Each is listed in the phase that first enforces it, and is re-verified in every
  phase thereafter by the CI checks of [`20-testing-and-validation.md`](./20-testing-and-validation.md) §2.

---

## P0 — Foundations

**Goal.** The plugin installs, loads, shows its menu and its provider, reads its settings, logs, tests and
packages. Nothing computes yet — everything that *will* compute has somewhere to live and a way to be
tested, translated, and shipped.

**Specs.** [`03-architecture.md`](./03-architecture.md) · [`15-ui-menu-and-settings.md`](./15-ui-menu-and-settings.md) ·
[`16-processing-provider.md`](./16-processing-provider.md) · [`18-i18n-and-profiles.md`](./18-i18n-and-profiles.md) ·
[`20-testing-and-validation.md`](./20-testing-and-validation.md) · [`21-packaging-ci-release-licensing.md`](./21-packaging-ci-release-licensing.md)

**Delivers.** `metadata.txt`, `__init__.py`, `plugin.py`, `provider.py`; the GeoComp menu with its six groups
and the Global Settings window shell; layered settings resolution; `QgsTask` infrastructure; the exception
hierarchy and logging; the i18n toolchain end to end (extraction → `.ts` → `.qm` → load) with pt-BR and es
files in place; one trivial algorithm proving the menu-to-algorithm path; the test harness; CI with the
structural checks; the build script and a ZIP that installs.

**Closes.** FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-030, FR-031, FR-032,
FR-060, FR-067, FR-068, FR-090, FR-091, FR-092, FR-093, FR-094, FR-095, FR-953, NFR-001, NFR-003, NFR-004,
NFR-005, NFR-006, NFR-009, NFR-011, NFR-012

**Exit.** Installs into a clean QGIS. "GeoComp" appears on the menu bar with six entries; the provider appears
in the toolbox. Switching QGIS to Portuguese translates everything present. `pytest` is green in CI on all
three operating systems, with every structural check active. `scripts/build.py` produces an installable ZIP,
byte-identical across two runs.

---

## P1 — Core domain and uncertainty

**Goal.** The types everything else is built from, and the property that defines this project: no geodetic
value without an uncertainty.

**Specs.** [`04-data-model.md`](./04-data-model.md) · [`05-uncertainty-and-covariance.md`](./05-uncertainty-and-covariance.md)

**Delivers.** `core/units.py`, `core/uncertainty.py`, `core/models/`. `Quantity`, `Covariance`, the
observation type registry, the entity model, JSON round-tripping, rigorous propagation with analytic
Jacobians, the approximate strategies, and the `RIGOROUS`/`APPROXIMATE` labelling that travels with a value.

**Closes.** FR-100, FR-101, FR-102, FR-103, FR-104, FR-105, FR-106, FR-107, FR-200, FR-201, FR-202, FR-203,
FR-204, FR-205, FR-206, FR-207, FR-208, NFR-002, NFR-007

**Exit.** Reproduces the worked propagation examples of RD-02 to published precision. Every analytic Jacobian
agrees with a numerical derivative — complex-step to ≤ 1e-9 relative, or central differences to ≤ 1e-7 where
the function takes no complex argument
([`05-uncertainty-and-covariance.md`](./05-uncertainty-and-covariance.md) §2.2; the split was recorded in the
pre-P7 review, which found this criterion stated in a form the observation equations could not meet). No public core function can return a geodetic
value without an uncertainty — asserted by a test. Combining two quantities from one `Covariance` through the
scalar path raises. All of it runs with no QGIS and no engines.

---

## P2 — Adjustment core

**Goal.** Least squares with the full statistical treatment, plus network design. The engine behind four
later modules.

**Specs.** [`06-adjustment-core.md`](./06-adjustment-core.md)

**Delivers.** `core/adjustment/`, `core/statistics/`, `core/preanalysis/`. Parametric LSQ with a full weight
matrix; iteration to convergence; free (minimum- and inner-constraint) and constrained datum handling; rank
diagnosis; 1D/2D/3D; global χ² test; data snooping; internal and external reliability; absolute and relative
error ellipses; design simulation; network inspection. Three Processing algorithms exposing them —
`geocomp:analysis_network_inspect`, `geocomp:analysis_network_preanalysis`,
`geocomp:analysis_network_adjust` — and with them the **Analysis** menu group, which settles what
[`15-ui-menu-and-settings.md`](./15-ui-menu-and-settings.md) §1.1 left open and amends FR-003 and FR-004 to
seven entries.

**Closes.** FR-220, FR-221, FR-222, FR-223, FR-224, FR-225, FR-226, FR-227, FR-250, FR-251, FR-252, FR-253,
FR-254, FR-255, FR-270, FR-271, FR-273, NFR-008

**Amends.** FR-003 and FR-004 (a seventh menu entry) and NFR-008 (SciPy for scale — ADR-0008). Both stay
owned by the phase that closed them; an amendment is not a transfer of ownership.

**Re-planned out of this phase.** **FR-272** — editing a design on the QGIS canvas and re-evaluating it in a
loop — moves to **P3**. P2 delivers the pre-analysis mathematics and the non-interactive route, both fully
testable without QGIS; the canvas dialog needs a running QGIS to verify, and shipping interaction code
nobody has run is how a phase reports done while leaving a defect. P3 is where the first custom dialog
(field mapping, FR-160) and the first QGIS-job exit criteria arrive, so it is where FR-272 can be proved
rather than asserted.

**Exit.** Reproduces RD-03 — coordinates, residuals, σ̂₀², ellipses — to published precision. A 2 × MDB blunder
injected into RD-09 is located on the first pass. A rank-deficient network produces a diagnosis naming the
affected stations, never a number. Pre-analysis of a network matches the **Σ**ₓ from adjusting simulated
observations of it.

---

## P3 — Total station: the first vertical slice

**Goal.** A user opens QGIS, picks Total Station from the GeoComp menu, imports field data, and gets an
adjusted, statistically validated, styled network on the map — **with no external engine installed**.

**Specs.** [`09-module-total-station.md`](./09-module-total-station.md) ·
[`19-visualization.md`](./19-visualization.md) · [`17-persistence-and-interoperability.md`](./17-persistence-and-interoperability.md) §5.1

**Delivers.** `core/techniques/total_station/` complete: face reduction with its diagnostics, instrument,
atmospheric and EDM corrections, basic and geometric reductions, traverse (classical and least-squares),
resection, forward intersection, classical networks, trigonometric levelling with leap-frog, 3D radiation.
The CSV/XLSX importer with saved field mappings. Instrument and reflector profiles. Basic/Advanced gating.
Result layers with QML styles and error ellipses. RD-01 shipped as a tutorial dataset. **The interactive
pre-analysis dialog (FR-272)**, re-planned out of P2: it belongs with the phase's other canvas and dialog
work, and with its QGIS job, which is what lets it be verified rather than asserted.

**Closes.** FR-033, FR-034, FR-035, FR-061, FR-062, FR-064, FR-069, FR-070, FR-071, FR-160, FR-166, FR-272,
FR-400, FR-401, FR-402, FR-403, FR-404, FR-405, FR-406, FR-407, FR-408, FR-409, FR-410, FR-411, FR-412,
FR-900, FR-901, FR-904, FR-905, FR-950

**Exit.** RD-01 reproduces `topo_test/processed_data.csv` to 1e-9 **and attaches an uncertainty to every
value**. RD-01's 1.000 m face-pair distance discrepancy is flagged as a blunder candidate, not averaged. The
PD = 181° / PI = 1° wrap case returns 181°. The whole chain runs from the menu and from a model-builder model.
Basic and Advanced modes give identical numbers with defaults. A planned station added on the canvas
re-evaluates the design without leaving the map.

*This is the milestone worth demonstrating.* It is a complete, useful, teachable product.

---

## P4 — Level

**Goal.** A second technique, cheaply, by reusing P2.

**Specs.** [`10-module-levelling.md`](./10-module-levelling.md)

**Delivers.** `core/techniques/levelling/`: the three sight schemes, closure computation against tolerances,
levelling network adjustment with length or setup weighting, three-wire import, orthometric corrections.
Also `io/levelbook.py` (both common field-book layouts), the `level` settings section, six Processing
algorithms under a populated Level menu, and `core/adjustment/{weighting,difference_network}.py` — see the
note below.

**Note for P8.** The height-difference observation equation *is* the gravity-difference equation — one
function in the P2 core, verified in `tests/test_gravimetry_is_levelling.py` (ADR-0002, Amendment 1). The
weighting work here, and the datum handling for a difference-only network, are therefore P8's as well; build
them so that gravimetry inherits them rather than reimplementing them.

**Done, and how.** The shared parts are `core/adjustment/weighting.py` (σ = k·√extent, with
`ExtentKind.DURATION` present for a gravimeter's drift rather than promised) and
`core/adjustment/difference_network.py` (starting values by traversal, connectivity — for a network of one
unknown per station connected by differences, whichever kind). `tests/test_gravimetry_is_levelling.py`
asserts both work unchanged in the gravity frame, as the second caller arriving early.

**Closes.** FR-500, FR-501, FR-502, FR-503, FR-504, FR-505

**Exit.** All three schemes reproduce RD-04. Loop misclosure and tolerance comparison match, including a
failing case. Extreme-sight foresights are a correlated cluster, demonstrably reducing the uncertainty of
derived differences between them. Mixing height types without a geoid model raises.

**Two defects P4 found in earlier work**, both recorded here because they say something about where to look
next. A 1D solution wrote its heights into the *easting* slot of its `Position` — so every levelling result
would have reported a height of zero — because P2's `to_solution` padded frame components in order while
`starting_values` read them by name. The correspondence is now stated once, as `Frame.position_components`.
And the Global Settings dialog rendered its raw dotted key for all seventeen settings P3 declared, because
the dialog is generated from the declarations but the *labels* are not; `tests/structural/test_settings_labels.py`
now fails when a setting has none.

---

## P5 — Persistence, interoperability and reporting

**Goal.** Work survives being closed, and moves in and out of other tools.

**Specs.** [`17-persistence-and-interoperability.md`](./17-persistence-and-interoperability.md) ·
[`19-visualization.md`](./19-visualization.md) §7

**Delivers.** The GeoPackage project store with its full schema, versioning and migration; provenance
recording; the *Adjust* (Ghilani) reader/writer; CSV and XLSX export; geoid and height model import; base map
integration; the adjustment report.

**Closes.** FR-065, FR-130, FR-132, FR-133, FR-134, FR-135, FR-162, FR-165, FR-167, FR-930

**Exit.** A complete project round-trips through GeoPackage losslessly. A newer schema is refused; an older
one migrates after a backup. Deleting observations a solution depends on is refused. An *Adjust* example file
reads, adjusts and writes back equivalently. A geoid model imports, applies, records its identity and
contributes its uncertainty. Reports render in all three languages, byte-identical across runs.

**Delivered.** The store with its versioning and referential protections, CSV and `.xlsx` export, the
adjustment report, geoid and height models, reference-system settings and base maps, and the four Processing
algorithms that make them reachable — with an eighth menu entry, **Project**, to put them somewhere a user
will look. FR-161 is the one exception, re-planned into P6 below.

**Re-planned: the *Adjust* format (FR-161).** Blocked, not skipped. No specification of the format and no
example file could be obtained — the book is not in this repository, the publisher's and Penn State's
distribution pages are outside this environment's network policy, and no public description of the layout
exists beyond "similar to a StarNet file". A guessed parser would fail the phase's own exit criterion, which
requires round-tripping an example file, and would fail it invisibly: a misread worked example produces an
adjustment of the wrong network, and matching the book's numbers is the entire point of the requirement. One
example file with its published answer unblocks it. See
[`17-persistence-and-interoperability.md`](./17-persistence-and-interoperability.md) §5.2, which also
records the trap that NGS ADJUST — open source, well documented, and what a search returns — is a different
program.

**Exit met**, with FR-161 re-planned into P6 and CI green on all nine jobs.

**Four defects, and what each one says about where the tests were.** Two were of one shape — a feature
declared, validated, displayed, and inert. Two were of another — a defect only one of the nine CI
environments could see.

*Inert features.*
`ConstraintMode.WEIGHTED` reached the model layer and stopped there; the adjustment read only `FIXED`, so a
weighted station was estimated as free and its published height thrown away. Every test of the model layer
passed, because the model layer was right. It surfaced only when something downstream *depended* on the
constraint doing work — checking that a geoid-derived height's uncertainty reached the adjusted heights, which
it could not. And `geocomp.reports` re-exported its Qt-dependent renderer eagerly, so importing the pure-Python
template engine pulled in `qgis` and its tier-1 tests could not even collect in the seven CI jobs without
QGIS; CI run 26 was red on that commit and had not been checked before the phase moved on. Both are recorded
in the CHANGELOG under Fixed, and the second is the reason the phase's own exit now says *confirm CI green*
rather than *push*.

*Environment-specific defects.* Every base map layer was invalid, because `QgsRasterLayer` was given the
service kind as its provider key and QGIS has no provider called `xyz` — all three kinds load through `wms`,
with the kind in the URI. And the store algorithm's "add" mode called `write`, which replaces, so saving a
network into a monitoring project deleted every solution in it while leaving a GeoPackage that looked
perfectly healthy. Both were caught by the QGIS job, on the commit that introduced them, which is the
arrangement working.

The second, though, is a **store** defect and the store is tier 1: it was found in the wrong place, and its
regression tests now live in `tests/test_project_store.py` where eight of the nine jobs run them. The lesson
generalises — when a tier-3 test fails, ask whether the defect it found is really tier-3's to catch, and if
it is not, move the test down rather than leaving it where it happened to surface.

A third of the same family: a tier-3 module carried `pytest.mark.qgis`, which labels and does not skip, so
twenty-five tests *errored* rather than skipping in the seven jobs without QGIS.
`tests/structural/test_tier3_skips_cleanly.py` now fails when a tier-3 module has neither `requires_qgis` in
its `pytestmark` nor a skipping fixture reaching every test — a check that is structural precisely because
neither environment anyone looks at can see the difference.

---

## P6 — DynAdjust

**Goal.** The second engine — and with it, cross-validation of the first.

**Specs.** [`07-engine-dynadjust.md`](./07-engine-dynadjust.md) ·
[`adr/0003-engine-acquisition.md`](./adr/0003-engine-acquisition.md) ·
[`adr/0004-dynadjust-interchange-format.md`](./adr/0004-dynadjust-interchange-format.md)

**Delivers.** `engines/base.py` and `engines/manager.py` — the engine abstraction, download, checksum
verification, installation, version detection, graceful absence. `engines/dynadjust/`: the DynaML writer, the
DNA reader, the pipeline driver, the output parsers, and the mapping into `Solution`.

**Closes.** FR-036, FR-066, FR-161, FR-163, FR-300, FR-301, FR-302, FR-303, FR-304, FR-305, FR-306, FR-320,
FR-321, FR-322, FR-323, FR-324, FR-325

**Re-planned into this phase.** **FR-161** — the *Adjust* (Ghilani) format — moves from **P5**, which could
obtain neither a specification of it nor an example file. It lands here rather than later because P6 is
already the interchange-format phase: the DynaML writer, the DNA reader and an *Adjust* reader are the same
kind of work over the same `Network` and `Solution` types, and one example file with its published answer is
all that is missing. See
[`17-persistence-and-interoperability.md`](./17-persistence-and-interoperability.md) §5.2 for what was
searched and what would unblock it. If P6 cannot obtain the file either, it moves again and says so — it is
not to be implemented from a guess.

**Exit.** DynaML written by GeoComp validates against the schema and imports without warnings for every
mapped observation type. A GNSS baseline cluster round-trips with its covariance intact. **The same network
adjusted by the in-house core and by DynAdjust agrees within the tolerances of
[`20-testing-and-validation.md`](./20-testing-and-validation.md) §4, on at least three networks.** The engine
manager installs on all three operating systems. With DynAdjust absent, everything else still works. Every
**[C]** claim in [`07-engine-dynadjust.md`](./07-engine-dynadjust.md) has been confirmed or corrected. An
*Adjust*-format example file reads, adjusts and writes back equivalently — or FR-161 moves again with the
reason recorded, since a parser written from a guess is not an implementation of it.

### Exit status

| Criterion | State |
|---|---|
| DynaML imports without warnings for every mapped type | **met** |
| A GNSS baseline cluster round-trips with its covariance intact | **met** |
| Cross-validation on **at least three** networks | **met** — three networks, see below |
| The engine manager installs on all three operating systems | **met on Linux, untested on Windows and macOS** — see below |
| With DynAdjust absent, everything else still works | **met** — the whole suite passes with no engine, and the algorithm fails with a message naming the remedy |
| Every **[C]** claim confirmed or corrected | **met** |
| FR-161, the *Adjust* format | **met, after P6 closed** — see below |

**Cross-validation: three networks, one per family of observation.** The `gnss-network` slice agrees to
0.047 mm ([`07-engine-dynadjust.md`](./07-engine-dynadjust.md) §6.1). A **projected levelling network**
agrees to 0.2 mm, which it could not before `core/geodesy/` supplied the inverse projection this entry used
to say was missing. **RD-01**, the terrestrial case — directions, zenith angles and slope distances together,
measured instrument-to-reflector, on the author's own field data — agrees to **0.12 mm in the sides and
0.03 mm in the heights**. `tests/test_dynadjust_pipeline.py` holds all three.

RD-01 cost four defects, none of which raised anything: the 3D pipeline dropped the setup heights
([`09`](./09-module-total-station.md) §2.5); `detect_defect` did not know a zenith angle fixes tilt, so the
inner-constraint solution forced the network flat; a direction set was mapped a row per direction rather than
*N−1* ([`07`](./07-engine-dynadjust.md) §5.6); and a constraint on a projected station was written on the
perpendicular axis (§5.7). `dimension=3` had never been exercised anywhere, which is how all four survived.

**RD-03 is still not one of them, and it is worth naming precisely why.** Its trilateration reaches
DynAdjust's station file, but only one of its eleven observations imports: a **horizontal distance has no
DynAdjust equivalent at all** ([`07`](./07-engine-dynadjust.md) §4.2). That is not a conversion gap and no
amount of geodesy fixes it — DynAdjust's distances are ellipsoidal, sea-level or slope, and a grid distance
is none of those. The third network has to be one whose observation types DynAdjust carries.

**The engine manager now installs, and the previous note here was wrong.** It said there was "nothing that
can honestly be pinned" because upstream published no versioned release. Upstream publishes five: DynAdjust
v1.4.0 carries binary archives for Linux, macOS and Windows ([`07`](./07-engine-dynadjust.md) §2). `PINNED`
holds all five, each digest computed from an archive actually downloaded and hashed by
`scripts/pin_engine_release.py`. The criterion was never blocked by upstream — it was blocked by a note
nobody rechecked.

**Verified end to end on Linux only.** The pinned Linux archive downloads, matches its digest, extracts,
is discovered by every pipeline program and reports `Version: 1.4.0` to GeoComp's own parser. Windows and
macOS are pinned and **untested** — this container can hash their archives but cannot run them — so the
criterion is recorded as met on one platform of three rather than met.

Installing it for real found two defects that synthetic archives could not, both of the same shape — an
install that verifies perfectly and is then invisible:

- **The archives nest.** Programs land under `dynadjust-linux-static/`, and `discover` looks for a direct
  child. `install` now returns the directory the programs are actually in.
- **Windows renames the programs.** It ships `adjust.exe`, not `dnaadjust.exe`, so every lookup would have
  failed on the one platform this criterion is most about.

The `engine` CI job still builds from an immutable commit rather than installing the pinned release: the
build is what the fixtures were produced with, and a job that tests the pin instead would stop testing the
parsers against the exact binary they were written for.

**Independent validation, from a different direction.** The cross-validation criterion is specifically
*against DynAdjust*, and one network is what it got. The in-house core is nonetheless no longer checked only
against itself: `io/krumm.py` and `tests/test_krumm_corpus.py` (RD-11) reproduce **34 published network
adjustments** — 1D, 2D and 3D, free and constrained — to 0.05 mm, from Ghilani, Niemeier, Benning, Wolf,
Strang and Borre and others by name and page
([`22-reference-data-sources.md`](./22-reference-data-sources.md) §2.2). That closes the citation gap
RD-02, RD-03 and RD-04 have carried since P1, and it reaches the plane and levelling networks DynAdjust
cannot take from GeoComp at all. It does **not** satisfy this criterion, which is about the engine.

**FR-161 is met, and it took a fourth attempt.** It had moved out of P5, P6 and P7 for one reason: neither a
specification of the *Adjust* format nor an example file was publicly reachable, and
[`17-persistence-and-interoperability.md`](./17-persistence-and-interoperability.md) §5.2 recorded that it
was not to be implemented from a guess. What unblocked it was **a public dataset of five networks published
in the format** ([`22-reference-data-sources.md`](./22-reference-data-sources.md) §4, CC BY 4.0), supplied by
the maintainer.

The reader and writer are in `geocomp/io/adjust.py`, and the grammar is still **inferred rather than
specified** — bounded by the fact that the format declares its own observation counts, so a misparse fails
loudly on every file, and by two conventions settled to a median of 0.000° against the files' own
coordinates. Three phases of refusing to guess bought a reader whose assumptions are each measured.

---

## P7 — GNSS

**Goal.** RINEX in, baselines with covariance out.

**Specs.** [`08-engine-rtklib.md`](./08-engine-rtklib.md) · [`11-module-gnss.md`](./11-module-gnss.md)

**Delivers.** `io/rinex.py` header scanning; session discovery; product resolution with caching, configurable
services and credentials through the QGIS authentication system; the `rnx2rtkp` configuration writer, runner
and `.pos` parser; batch processing; baseline construction with independent-set identification; quality
reporting; comparative configuration testing; the reference station database.

**Closes.** FR-063, FR-164, FR-350, FR-351, FR-354, FR-355, FR-356, FR-357, FR-358, FR-359, FR-600, FR-601,
FR-602, FR-603, FR-604

**Re-planned out of this phase: FR-352, FR-353 and NFR-010** — product download, credentials through the QGIS
authentication system, and the rule that no credential reaches a log or an export. They move to **P10**; see
the P7b section below for the re-check that settled it and the P10 section for why there.

**Exit.** A static relative session over RD-06 reproduces the published coordinates within tolerance.
Baselines reach DynAdjust as G measurements with their 3×3 covariance intact. The independent baseline subset
is correctly identified. Antenna height reduction applied twice is prevented. A batch with one broken session
completes and reports it. No credential appears in any log, config, provenance record or export. PPP modes
show the FR-604 notice.

**Status: one criterion open.** Everything above is met except the first, and P7d attributes what it is
failing on rather than leaving it unexplained — see the P7d table below. The remaining gap is in the
reference, not the pipeline.

### P7a — the foundation: RINEX in, a real baseline out

**Delivered.** The phase was split after its first slice, at the maintainer's decision: P7 closes seventeen
requirements, roughly twice P6, and stopping at a working engine lets the rest be planned against something
that runs rather than against a specification.

| Delivered | Where |
|---|---|
| RINEX 2 and 3 header scanning (FR-164) | `io/rinex.py` |
| Session discovery and simultaneity grouping (FR-350, FR-351) | `io/gnss_discovery.py` |
| The configuration writer, runner, version detection and graceful absence (FR-354, FR-355, FR-302, FR-304, FR-306, FR-036) | `engines/rtklib/` |
| `.pos` parsing with the covariance whole (FR-356, FR-206) | `engines/rtklib/read_pos.py` |

**Every `[C]` in [`08-engine-rtklib.md`](./08-engine-rtklib.md) is discharged**, against the source that
writes the file rather than against the manual — and the confirmation turned up two things no manual states:
the cross-covariance columns are *signed square roots*, and one column header is **wrong upstream** (§7.1–7.3).
A third came from running the engine: `-k <config>` and the equivalent flags are **not the same run**, because
loading a configuration file silently relocates the base station to latitude 0, longitude 0 (§2.1).

**Exit status of this slice**

| Criterion | State |
|---|---|
| RINEX 2 and 3 headers read, mismatches reported | **met** |
| Sessions discovered and grouped by simultaneity | **met** |
| A configuration fed back through `-k` reproduces the run | **met** |
| `.pos` parsed in every output format, covariance intact | **met** — five fixtures, one per format, re-derived from a live engine by `scripts/check_rtklib_fixtures.py` |
| With RTKLIB absent, everything else still works | **met** — the suite passes with no engine and the adapter reports what is missing |
| **A static relative session over RD-06 reproduces published coordinates** | **not met** — see below |

**RD-06 was blocked during P7a.** All four candidate archives — `geoftp.ibge.gov.br`,
`cddis.nasa.gov`, `igs.bkg.bund.de`, `files.igs.org` — are denied by the egress policy of the development
environment ([`22-reference-data-sources.md`](./22-reference-data-sources.md) §5). The chain is validated
end to end on RTKLIB's own sample pair, which resolves its ambiguities and yields a full covariance; that
demonstrates the **pipeline**, not the **accuracy**, and the criterion stays open rather than being
reinterpreted into one the available data can satisfy.

**Validation update, 17 September 2026.** Official NOAA RINEX and independent NGS ITRF2020 coordinates have
now been obtained for GODN–GODS and integrated into `tests/data/rd06/`. The evidence at the reviewed
commit with the pinned engine shows the calibrated full-day result differs by **7.512 mm in 3D**, and fails the
conservative 1 mm XYZ comparison derived from the source's printed precision. A second day, reciprocal
processing and precise orbits do not close that gap. RD-06 acquisition is unblocked; **this exit criterion
is still not met**. See [`22-reference-data-sources.md`](./22-reference-data-sources.md) §5. No tolerance
has been changed, and this evidence does not close P7c or the deferred product/credential requirements.
`tests/test_rd06.py` now exercises the current development code; the engine workflow enforces its accuracy
assertion with `--runxfail` and retains the resulting evidence. That CI check remains red until the
criterion is met. Local development labels only this known discrepancy as a strict expected failure.

**Deferred out of this slice: products and credentials.** FR-352 (automatic product download), FR-353
(credentials through the QGIS authentication system), NFR-010 and the GNSS half of FR-063 are **not** in P7a,
at the maintainer's decision and for the same reason RD-06 is blocked: the archives they would download from
are unreachable from this environment, so the code could be written but not exercised, and an untested
download path is a claim rather than a feature. There are no credentials to leak until there is something to
authenticate to.

They remain **P7's** — they are P7b's, not another phase's — and that is deliberate: the blocker is an egress
policy, not a technical obstacle, and it could be lifted before P7b runs. **If it has not been, P7b moves
them again and records the move**, the way FR-161 was moved out of P5, P6 and P7 rather than implemented from
a guess. The pipeline works against products supplied on disk in the meantime, which is what
`RtklibJob.products` is for.

### P7b — baselines into an adjustment

**Delivered.** The phase was split a second time, at the maintainer's decision: the *computation* lands here
and the *surface* becomes P7c, so the correctness work arrives reviewable on its own rather than in the same
diff as menu wiring.

| Delivered | Where |
|---|---|
| Baseline construction from a `.pos`, with the covariance conditioned by what the file can carry (FR-602) | `engines/rtklib/baseline.py` |
| Antenna height reduction, applied once and recorded on what it produced (FR-602, FR-204) | `core/techniques/gnss/baselines.py` |
| The independent subset, by quality, with the dependent ones marked rather than dropped (FR-602, FR-104) | `core/techniques/gnss/baselines.py` |
| The baseline cluster reaching DynAdjust as a `G` or `X` (FR-104) | round-tripped in `tests/test_gnss_to_dynadjust.py` |
| Session and per-epoch quality indicators (FR-603) | `core/techniques/gnss/quality.py` |
| ECEF↔ENU rotation of a vector and its covariance | `core/geodesy/cartesian.py` |

**What planning it turned up.** A `GNSS_BASELINE` observation had **no declared frame**, and P7b is the first
code that had to construct one rather than read one. The finding is smaller than it first looked and worth
stating precisely, because the first reading of it was wrong: the in-house core's equation is
`target[c] − origin[c]`, which is correct in *any* orthogonal cartesian 3-frame, so a geocentric network
adjusted with geocentric baselines is right — as P6's cross-validation already relied on. The real hazard is
**mixing** an ECEF baseline with projected station coordinates, which is wrong by a rotation and silent. So
`Network.cartesian_frame` records what the coordinates are, the observation records what the baseline is, and
the equation refuses only a genuine disagreement ([`04-data-model.md`](./04-data-model.md) §2.5.1). The
DynaML writer's guard is absolute rather than conditional, because `<GPSBaseline>` *is* geocentric by
definition.

**Two numbers make the rotation evidence rather than assertion.** `xyz.pos` and `enu.pos` are one run written
twice, so rotating the first must reproduce the second: it does, to **0.006 / 0.047 / 0.024 mm** on the
components and to **every printed digit** on the standard deviations. Nothing else in the suite would catch a
transposed row of the rotation.

**Exit status of this slice**

| Criterion | State |
|---|---|
| A baseline is built from a real run with its covariance intact | **met** — tier 4, live engine |
| It reaches DynAdjust as a `G` measurement and comes back the same matrix | **met** — `specs/11` criterion 4 |
| Antenna height reduction applied twice is detected and prevented | **met** — `specs/11` criterion 5 |
| The independent subset is identified and the dependent ones marked | **met** — `specs/11` criterion 3 |
| Quality indicators per session and per epoch | **met, except DOP** — see below |
| **DOP reported per session** | **not met** — `rnx2rtkp` writes none in any format ([`11`](./11-module-gnss.md) §5) |
| **A static relative session over RD-06 reproduces published coordinates** | **not met** — unchanged from P7a |

### P7c — the surface

**Delivered.** The GNSS menu and its eight algorithms, the two result layers, comparative configurations,
the reference station database, batch execution, and nine `gnss.*` settings that are all read.

| P7c exit criterion | State |
|---|---|
| The menu of [`11`](./11-module-gnss.md) §1 exists and every entry runs an algorithm | **met** — eight algorithms; *Download products* waits on FR-352 in P10, so its entry does not exist rather than pointing at nothing |
| The four modes are reachable, and Absolute carries FR-604's notice | **met** — in the help, the short description and a warning at the top of every Absolute run |
| GNSS results import as QGIS layers (FR-357) | **met** — baselines as lines, solution epochs as points, both styled and both carrying their quality |
| Comparative configuration testing (FR-359) | **met as an algorithm**; the side-by-side dialog of [`15`](./15-ui-menu-and-settings.md) §1.2 is **not built** and is named below |
| A reference station's frame and epoch are used, not assumed (FR-063, FR-105) | **met** |
| A base in a different frame triggers transformation (FR-832) | **not met, and refused rather than guessed** — the transformations are P10's; a mismatch raises |
| A batch with one broken session completes and reports it (FR-355) | **met** — a failure is a row, not an absence |
| Precise ephemerides from a directory on disk (FR-358) | **met** — the download half is FR-352's and so P10's |

**Not built in P7c, named so the ticks above do not imply them.** The FR-359 comparison dialog: ADR-0005
makes the algorithm the capability, and it ships first and alone. FR-832's transformations, which are P10's
along with FR-352, FR-353 and NFR-010. DOP, which `rnx2rtkp` writes in no format. And RD-06's accuracy
criterion, which stays red by design — P7b attributed the 7.5 mm and left *deriving* a GNSS threshold, rather
than choosing one, to the maintainer.

**Found while building the surface, and recorded rather than quietly fixed.** Two latent traps in the `.pos`
parser, both in code P7 wrote and neither reached by any caller at the time: `-g`'s seven position columns,
whose last three are a longitude's minutes, its seconds and the height rather than a coordinate; and
`PosEpoch.quantities()` pairing degrees of latitude with metres of standard deviation for the geodetic
formats. Both are in [`08`](./08-engine-rtklib.md) §7.4. A third was mine, caught by the four-format identity
in `tests/test_gnss_trajectory.py`: rotating an ECEF covariance with `(n, e, u)` labels relabels rather than
permutes, and swaps the north and east sigmas while leaving every number plausible.

**FR-352, FR-353 and NFR-010 move to P10.** P7a deferred them and committed that P7b would move them if the
egress policy still held. It does: `igs.bkg.bund.de` and `geoftp.ibge.gov.br` were re-checked in the P7b
session and both still return 403 on CONNECT. The move and its reasoning are recorded in P7's `Closes` line
and in P10 below.

### P7d — RD-06, attributed

**Delivered.** The sub-session capability the attribution needed, the attribution itself, and the rebuilt
reference case. `specs/08` §2 had declared `-ts`/`-te` verified since P7a and the adapter never had them;
`RtklibJob.window` closes that gap, and with it a session can be solved in parts.

| Delivered | Where |
|---|---|
| A processing time window, with the GPST and `sscanf` traps recorded ([`08`](./08-engine-rtklib.md) §2.3) | `engines/rtklib/engine.py` |
| Sub-session repeatability: 62 solutions per baseline, 24 h down to 1 h | `scripts/check_rd06.py --repeatability` |
| The antenna-epoch guard, offline on every commit | `scripts/check_rd06.py`, `tests/test_rd06.py` |
| RD-06 rebuilt on GODN–GODE, with GODN–GODS kept as the counter-case | `tests/data/rd06/` |

**The previous attribution was half wrong, and the correction is in
[`22`](./22-reference-data-sources.md) §5.1.** The "low-elevation error of up to 11 mm in east" is not a
gradient — it is **one hour**, 11:00–12:00 on 2025-001, whose unvalidated ambiguity fix the 24-hour static
filter carries to the end of the day. The ≥25° mask removed it by dropping the satellite that caused it,
which is why the mask sweep could not tell the two readings apart. Excluding that hour, day 001 agrees with
day 002 to 0.1 mm in east.

**The −6.4 mm north is GODS's reference, and the mechanism is now named.** GODS changed antenna on
2020-09-03, after the 2020.0 epoch of the coordinate it is compared against; NGS states such a change moves
a coordinate by a few mm to several cm; GODS's own sheet contradicts itself by 1.97 mm in east where GODN's
agrees with itself to 0.21 mm. GODE, whose antenna predates the epoch, misses its published baseline by
**0.65 mm in north on the clean day where GODS misses by 6.53 mm** — one base, two rovers, one day, one
configuration, four days tried.

**Three things this turned up that the product keeps.** A wrong integer fix does **not** enlarge RTKLIB's
formal covariance — a 22 mm error reports a 1.08 mm sigma — so the validation ratio is the only indicator
that moves, and `fixed_fraction` alone is not enough (FR-603). `rnx2rtkp`'s `-te` is inclusive, so disjoint
windows end one interval short. And a same-antenna-type pair longer than 4 km errs by 13 to 47 mm under
this configuration, which is why the 65 m GGAO baseline is the case and not a "more realistic" one.

| P7d exit criterion | State |
|---|---|
| The 7.5 mm is attributed to specific, named causes | **met** — one contaminated hour, and one station's post-epoch antenna change |
| The attribution is a test, not a paragraph | **met** — `tests/test_rd06.py` fails if the counter-case stops showing it |
| A defect of this class cannot recur silently | **met** — the antenna-epoch guard refuses it offline, and an exemption must stay earned |
| A GNSS numerical threshold is derived | **met, and deliberately not adopted** — see below |
| **A static relative session over RD-06 reproduces published coordinates** | **not met, and the judged case is unjudgeable** — `ngs20.atx` has no entry for GODE's `AOAD/M_T JPLA`, so the run carries another dome's calibration ([`22`](./22-reference-data-sources.md) §5.2) |

**The threshold was derived and the maintainer chose not to adopt it.** The estimator's measured
repeatability is 0.38 / 0.54 / 1.47 mm per component, so a threshold derived from this side of the
comparison is ~1 mm horizontally — the number already in use. Nothing on GeoComp's side decides the
criterion; the reference's unpublished uncertainty does. [`20`](./20-testing-and-validation.md) §6 records
the decision and [`22`](./22-reference-data-sources.md) §5.2 the derivation.

**The check found a defect in this slice's own reference case, and that is recorded rather than tidied
away.** Engine CI reported that `ngs20.atx` has no entry for GODE's `AOAD/M_T JPLA`, so `searchpcv`
matched `AOAD/M_T        NONE` — the same antenna under a different dome, which NGS keys and uses
separately. The calibrated GODE numbers are therefore withdrawn as evidence of accuracy;
[`22`](./22-reference-data-sources.md) §5.2 keeps them labelled as what they are. The counter-case
resolved exactly in the same run, so the attribution in §5.1 is untouched — a dome substitution is
vertical and the term it attributes is north.

**So the site now has two independent defects and no clean reference.** GODS's published coordinate
describes an antenna it no longer carries; GODE's dome has no published calibration. Closing the
criterion needs a station whose antenna **and radome** are both in the calibration set, and that
membership cannot be tested from the development environment — `geodesy.noaa.gov`, which serves
`ngs20.atx`, is 403, as are `files.igs.org`, `igs.bkg.bund.de`, `cddis.nasa.gov` and
`geoftp.ibge.gov.br`, all re-checked on 23 September 2026. The test belongs in engine CI, where the
file exists, and that is the next step rather than a claim made here.

---

## P8 — Gravimetry

**Goal.** The menu group whose *corrections* have no engine behind them.

**Specs.** [`12-module-gravimetry.md`](./12-module-gravimetry.md)

**Delivers.** `core/techniques/gravimetry/`: scale, tidal and drift corrections; gravimetric network
adjustment on the in-house core with jointly estimated drift; gravimeter profiles.

**Smaller than it looks.** The network adjustment is already written: a gravity difference and a height
difference are the same observation equation, so P2's core and P4's 1D weighting and datum work both carry
over unchanged (ADR-0002, Amendment 1). What is genuinely new here is the corrections, drift as a nuisance
parameter — which is the one piece no external 1D engine can supply, since drift and gravity differences are
not separable by pre-correction alone — and the datum of a difference-only network. It also means the P6
cross-validation *can* cover gravimetry, by relabelling the differences as level differences, which the
original plan assumed impossible.

**Closes.** FR-700, FR-701, FR-702, FR-703

**Exit.** Corrections reproduce RD-07. A synthetic linear drift is recovered within its uncertainty, along
with the true station gravity values. The datum defect of a difference-only network is detected as 1.
Uncheckable observations are flagged. Absolute values enter weighted, not fixed.

---

## P9 — Integration

**Goal.** The point of the project: techniques adjusted together.

**Specs.** [`13-module-integration.md`](./13-module-integration.md)

**Delivers.** `core/techniques/integration/`: combined adjustment across techniques, height system handling
with geoid application and recording, variance component estimation, frame and epoch reconciliation,
per-technique reporting.

**Closes.** FR-800, FR-801, FR-802, FR-803, FR-804, FR-805

**Exit.** A GNSS + total station network reproduces a published combined example. Mixing height types without
a geoid raises; with one, the model is recorded. A deliberately mis-scaled technique's variance component is
recovered. A three-technique combination runs end to end. A combination including gravity routes to the
in-house core with the reason reported.

---

## P10 — Multi-epoch and monitoring

**Goal.** The capability with the highest stakes and the largest gap in the archived plan.

**Specs.** [`14-multi-epoch-monitoring.md`](./14-multi-epoch-monitoring.md)

**Delivers.** `core/monitoring/`: metadata compatibility checking, frame and epoch transformation with
propagated uncertainty, displacement computation with cross-covariance, significance testing, reference block
stability testing, congruency and strain analysis, alert thresholds, the time series panel, the monitoring
report.

**Closes.** FR-352, FR-353, FR-830, FR-831, FR-832, FR-833, FR-834, FR-835, FR-836, FR-837, FR-838, FR-903,
FR-932, NFR-010

**Re-planned into this phase: product download and credentials (FR-352, FR-353, NFR-010).** They were P7's,
and moved after P7b re-checked the egress policy and found it unchanged. **P10 rather than a consolidation
phase because P10 is the first phase that genuinely needs an archive**: a multi-epoch series over published
reference stations is not something a user assembles by hand, so the download path gets built where it is
load-bearing rather than parked somewhere it would be written and never exercised. If the archives are still
unreachable when P10 runs, the same rule applies again — it moves and the move is recorded, as FR-161 did
three times before it landed.

**Exit.** RD-08 reproduces, including the significance decisions. A synthetic injected displacement is
recovered and found significant, with no false positives elsewhere. A *moving reference station* is caught by
the stability test and named. A solution without an epoch is refused. Displacements below threshold are
reported as "not significant", never as zero. A three-epoch series yields correct velocities and a plottable
time series with map-to-plot linkage.

---

## P11 — PostGIS

**Goal.** Database mode, for shared projects and long monitoring series.

**Specs.** [`17-persistence-and-interoperability.md`](./17-persistence-and-interoperability.md) §1–§4 ·
[`adr/0006-storage.md`](./adr/0006-storage.md)

**Delivers.** `io/postgis.py`: the identical logical schema on PostGIS, mode switching in both directions,
schema versioning and migration, concurrent-modification detection, connections through the QGIS registry.

**Closes.** FR-131

**Exit.** GeoPackage → PostGIS → GeoPackage is lossless, table by table. Migration works on both backends. A
concurrent modification is detected on save rather than overwritten.

---

## P12 — Consolidation

**Goal.** Everything present, coherent, and finished — the part that separates a working prototype from a
product.

**Specs.** [`19-visualization.md`](./19-visualization.md) · [`18-i18n-and-profiles.md`](./18-i18n-and-profiles.md) ·
[`15-ui-menu-and-settings.md`](./15-ui-menu-and-settings.md)

**Delivers.** Thematic quality maps across every metric; template-driven reports and print layout templates;
the results panel completed; Basic/Advanced review across every algorithm now that all exist; pt-BR and es
translations completed and reviewed by native speakers against the glossary; performance work against
NFR-008; documentation of every **[C]** claim resolved.

**Also delivers, added by the pre-P7 review: the settings actually reaching the computation.** 36 of the 47
declared settings are read by nothing — the Global Settings window presents controls that resolve correctly
and change no result, because every algorithm declares hard-coded Processing parameter defaults instead
([`15-ui-menu-and-settings.md`](./15-ui-menu-and-settings.md) §2.3). `interface.angle_format` and the three
display settings beside it need `core/units.py`'s formatting half, which until the review had no caller
anywhere and two defects in it. `tests/structural/test_settings_are_honoured.py` holds the list and fails
on any new setting added without a consumer.

**Closes.** FR-902, FR-931

**Exit.** No untranslated string in any language. Every algorithm passes the Basic/Advanced identity check.
Thematic maps render for every listed attribute, including the redundancy-number map. Every acceptance
criterion in every specification document has a passing automated test or a documented reason to be manual.

---

## P13 — Validation, documentation and release

**Goal.** Evidence that it is right, material that teaches it, and v1.0 on plugins.qgis.org.

**Specs.** [`20-testing-and-validation.md`](./20-testing-and-validation.md) ·
[`21-packaging-ci-release-licensing.md`](./21-packaging-ci-release-licensing.md)

**Delivers.** The remaining reference datasets assembled; field campaign data collected with students
(RD-10); case studies comparing the integrated workflow against traditional CLI-and-script workflows; the
commercial software comparison protocol executed and published; tutorials in three languages; the
contribution guide; the upstream defect reporting path; v1.0 released.

**Closes.** FR-951, FR-952, FR-954, FR-955

**Exit.** Every reference dataset has a passing test. At least one published commercial comparison with every
discrepancy classified and no unexplained differences remaining. Tutorials cover every module in all three
languages. v1.0 is on plugins.qgis.org and installs cleanly. At least one external contribution merged.

---

## Mapping to the research project's 24-month schedule

`tex §Cronograma de atividades` proposes six periods. The correspondence:

| Months | Proposal | Phases |
|---|---|---|
| 1–3 | Requirements, bibliography, conceptual modelling | **This specification set**, P0, P1 |
| 4–8 | Plugin core as Processing Provider; first DynAdjust integration | P0–P3, start P6 |
| 9–12 | `rnx2rtkp` integration, product downloads, start multi-epoch | P6, P7, start P10 |
| 13–16 | PostGIS, trilingual interface, UI refinement, monitoring and time series | P10, P11, P12 |
| 17–20 | Field campaigns, test data, case studies with students | P13 (RD-10, case studies) |
| 21–24 | Consolidation, first fully functional version, documentation, publications | P12, P13 |

**Two deliberate deviations, both stated so they are choices rather than drift:**

1. **The trilingual interface is built in P0**, not at months 13–16. The proposal's schedule places
   *completion and refinement* there, which P12 still does; but the string discipline that makes completion
   cheap has to exist from the first commit ([`18-i18n-and-profiles.md`](./18-i18n-and-profiles.md) §2).
2. **The multi-epoch module is P10**, once solutions with rigorous covariance exist to compare. The proposal
   lists it in both months 9–12 and months 21–24; the reconciliation is that design and metadata schema
   belong early (P1 makes epoch a first-class field), and the analysis itself needs P2, P6 and P7 finished.

**Two phases carry the schedule risk.** P3 is the largest single body of new computation, and P7 depends on
external services and on field data. Both should be planned with slack.

---

## Requirement coverage

Every `FR-###` and `NFR-###` in [`02-requirements.md`](./02-requirements.md) appears in exactly one phase
above. This is checked in CI ([`20-testing-and-validation.md`](./20-testing-and-validation.md) §2); a new
requirement without a phase, or a requirement in two phases, fails the build.

The full cross-reference — objectives O1–O12 and menu items against requirements and phases — is in
[`traceability.md`](./traceability.md).
