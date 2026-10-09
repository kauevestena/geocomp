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
| The menu of [`11`](./11-module-gnss.md) §1 exists and every entry runs an algorithm | **met** — eight algorithms; *Download products* waits on FR-352 in P10, so its entry does not exist rather than pointing at nothing (it arrived in P10c) |
| The four modes are reachable, and Absolute carries FR-604's notice | **met** — in the help, the short description and a warning at the top of every Absolute run |
| GNSS results import as QGIS layers (FR-357) | **met** — baselines as lines, solution epochs as points, both styled and both carrying their quality |
| Comparative configuration testing (FR-359) | **met as an algorithm**; the side-by-side dialog of [`15`](./15-ui-menu-and-settings.md) §1.2 is **not built** and is named below |
| A reference station's frame and epoch are used, not assumed (FR-063, FR-105) | **met** |
| A base in a different frame triggers transformation (FR-832) | **not met, and refused rather than guessed** — the transformations are P10's; a mismatch raises |
| A batch with one broken session completes and reports it (FR-355) | **met** — a failure is a row, not an absence |
| Precise ephemerides from a directory on disk (FR-358) | **met** — the download half is FR-352's and so P10's (P10c, which also found the directory's files were handed over whatever their day) |

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

**The obvious escape was tried and measured.** Leaving the site for a longer same-antenna pair fails
for a second reason: at 4 km the ionosphere-free combination fixes the horizontal (P281–P282 goes from
−4.4/+4.9 mm to +0.15/+0.50 mm) but resolves **no ambiguities at all** — it has no integer wavelength,
so every run is FLOAT at a ratio near 1 and the height degrades to −14.7 mm. The short baseline is what
makes the comparison possible with this engine, not a convenience.

**Three things this turned up that the product keeps.** A wrong integer fix does **not** enlarge RTKLIB's
formal covariance — a 22 mm error reports a 1.08 mm sigma — so the validation ratio is the only indicator
that moves, and `fixed_fraction` alone is not enough (FR-603). `rnx2rtkp`'s `-te` is inclusive, so disjoint
windows end one interval short. And a same-antenna-type pair longer than 4 km errs by 13 to 47 mm under
this configuration, which is why the 65 m GGAO baseline is the case and not a "more realistic" one.

**One conclusion from that screen has been narrowed.** "GGAO's 65 m is the shortest clean baseline in
the network" was measured with the observation day fixed at 2025 day 001, and the observation day is a
free parameter. Against 2020 day 015 the same screen finds **17** same-antenna pairs within 5 km,
fifteen of them at 22 to 46 m, where 2025 day 001 gives one — the 4 km pair already ruled out. The
claim held for the days processed, not for the network. `scripts/screen_cors_pairs.py` is that screen;
[`22`](./22-reference-data-sources.md) §5.2 carries the table and what it still does not settle.

| P7d exit criterion | State |
|---|---|
| The 7.5 mm is attributed to specific, named causes | **met** — one contaminated hour, and one station's post-epoch antenna change |
| The attribution is a test, not a paragraph | **met** — `tests/test_rd06.py` fails if the counter-case stops showing it |
| A defect of this class cannot recur silently | **met** — the antenna-epoch guard refuses it offline, and an exemption must stay earned |
| A GNSS numerical threshold is derived | **met, and deliberately not adopted** — see below |
| **A static relative session over RD-06 meets its accuracy criterion** | **met** — the criterion is now loop closure and repeatability, not agreement with a published coordinate. The GODN–GODE–GODS triangle closes to **0.245 / 0.787 mm** and the six-hour sub-sessions repeat to **0.613 / 0.318 / 0.992 mm**, against 2 mm per component ([`20`](./20-testing-and-validation.md) §6) |

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
file exists, and that is the next step rather than a claim made here. It is now a narrower question
than it was: the screen above supplies fifteen same-antenna candidate pairs to test membership for,
instead of an open search.

**That step is done, and it answered more than it was asked.** The maintainer supplied `igs20.atx` on
24 September 2026. `AOAD/M_T JPLA` is absent from it too, so GODE's unjudgeability is confirmed against
a second calibration set rather than being an artefact of one file; `TRM41249USCG SCIT` is present, so
the candidate pairs are exactly calibrated and the comparison is finally decidable. Running **all
fourteen** eligible pairs on three days each — `scripts/check_published_coordinates.py`, every result
reported, none selected after solving — **not one reaches 1 mm per component**, the median worst
component being 5.1 mm. Each pair holds its own offset to 0.43 mm across days, pairs differ from each
other by 2.7 to 6.6 mm, and the offsets do not move between a 10° and a 30° elevation mask: not our
noise, not multipath. GGAO was never an outlier — GODN–GODE's 7.8 mm sits near the middle of that
distribution. The two defects P7d attributed are real; they were simply never what kept the criterion
red. What remains is a decision about the threshold, put to the maintainer in
[`20`](./20-testing-and-validation.md) §6, not further measurement.

**The maintainer's answer, on 24 September 2026, was to close the last caveat before deciding.** Those
fourteen results were measured with `igs20.atx`; NGS computes the coordinates they are compared against
with its own `ngs20.atx`, which this environment cannot fetch but engine CI already does. The engine job
now re-runs all fourteen pairs against it and fails if any component moves by more than 1 mm, the size
at which the conclusion would change.

**It has been made, and it changes nothing.** The supplied `ngs20.atx` matches the digest this
repository already pins; NGS calibrates the antenna; its entry differs from the IGS one only in a
SINEX provenance code, every phase-centre number being identical; and re-running all fourteen pairs
moves the largest component by 0.0005 mm. `AOAD/M_T JPLA` is absent there too — NGS publishes no JPLA
radome at all — so GODE's unjudgeability is a fact about the radome, not about the file.

## P7e — the criterion GNSS is actually judged on

**The maintainer's decision of 24 September 2026: stop judging GNSS on somebody else's coordinates.**
A tolerance no clean pair can meet is a statement about NGS, and a green check ought to be a statement
about GeoComp. RD-06 is now met on two criteria, each at 2 mm per component, and both are.

**Loop closure**, delivered as `core/techniques/gnss/baselines.py::loop_closure` and specified in
[`11`](./11-module-gnss.md) §4.1.1. A closed circuit of measured vectors must return where it began,
which needs no external coordinate at all. The GGAO triangle's third leg, GODE–GODS, is now processed
independently rather than differenced from the other two — differencing would close by construction
and check nothing — and the circuit closes to **0.245 mm** on 2025-001 and **0.787 mm** on 2025-002
over a 282 m perimeter. The sum is refused outside ECEF, because east, north and up at one station are
not east, north and up at another, and refused across mixed antenna reduction, because such a loop
closes by the antenna heights.

**Repeatability**, because closure alone is not enough: an error common to every baseline at one
station enters the loop twice with opposite signs and cancels. 2025-001 proves the blind spot — it
carries the contaminated hour P7d attributed and closes to a quarter of a millimetre anyway. The
six-hour sub-sessions repeat to **0.613 / 0.318 / 0.992 mm**, and `tests/test_rd06.py` asserts the
blind spot rather than describing it.

**The published comparison is kept and reported**, never deleted. It still runs on every engine build,
its number still reaches `metrics.json` and the artifact, and a test asserts it stays the size
[`22`](./22-reference-data-sources.md) §5 describes. Evidence does not stop being interesting because
it stopped being a gate.

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

**Split, at the maintainer's decision of 25 September 2026**, as P7 was: **P8a** the computation, **P8b** the
surface, so the correctness work is reviewable apart from the menu wiring. **Ocean loading moves to P12** at
the same decision (below).

### P8a — the computation

**Delivered.**

| Delivered | Where |
|---|---|
| Gravity's own carrier: `ConstraintSpec.gravity`, `AdjustedStation.gravity`, store schema 3 | `core/models/`, `io/store/` |
| Gravimeter profiles: calibration table, factor with uncertainty, nominal precision, applied-once tide (FR-061, FR-069) | `core/instruments/gravimeter.py` |
| The solid-Earth tide, Longman (1959), accuracy measured against ETERNA and a CG-5's firmware (FR-701) | `core/techniques/gravimetry/tides.py` |
| Reduction of a reading: scale, tide, and to the mark (FR-701, FR-204) | `core/techniques/gravimetry/readings.py` |
| Drift jointly estimated as a per-session polynomial, or pre-corrected from a base (FR-701, FR-702) | `core/techniques/gravimetry/drift.py`, `core/adjustment/equations.py` |
| Occupations, differences with their exact covariance, absolute values weighted, the result (FR-700, FR-703) | `core/techniques/gravimetry/network.py` |
| RD-07, assembled | `tests/data/rd07/`, `scripts/check_rd07.py`, `scripts/check_tide_reference.py` |

**The wart P2 recorded was worse than recorded.** A station's gravity travelled in the `up` slot of a
`Position`, which enforces metres; `tests/test_gravimetry_is_levelling.py` asserted it "so the day it is fixed
this fails". What it did not say, because it only ever called `adjust()`, is that **no gravity solution could be
written at all** — `to_solution` handed `Position` an acceleration and `Position` refused it.

| P8a exit criterion (`specs/12` §8) | State |
|---|---|
| Corrections reproduce RD-07 | **Tide: met** — Longman against a CG-5's firmware, 0.60 µGal rms and 1.51 at worst over 2,096 readings printed to 1 µGal. **Drift and adjustment: met** — pyGrav's published solution reproduced on four days, within the rounding of its printed inputs once its datum-free `S Sᵀ` term is accounted for. **Scale table: not met against a published example** — none was reachable ([`22`](./22-reference-data-sources.md) §5.6) |
| A synthetic linear drift is recovered within its uncertainty, with the true station values | **met** — USGS's surveys with published truth: every station within 3σ, the drift within 2σ, calibrations of 3, 5 and 10 % |
| Pre-corrected and joint drift agree where the drift is linear and part where it is not | **met** — under 1 µGal against 3.7, and up to 245 µGal at every station; see the finding below |
| The datum defect of a difference-only network is detected as 1 | **met**, and reported with what removed it |
| Absolute values enter weighted, not fixed | **met** — two conflicting absolute values both move and both carry a residual |
| Uncheckable observations are flagged | **met in the result, by name**; shown prominently in P8b |
| Values stored in SI | **met** — a GeoPackage round trip returns the adjusted gravity bit for bit |
| Every output carries an uncertainty and a mode (FR-703) | **met** |

**Found, and kept.**

- **Pre-correction with its drift estimate's covariance carried in full *is* the joint estimate**, to
  3×10⁻¹⁰ µGal: the base readings' residuals carry no information about the station values. What makes field
  pre-correction worse is discarding that covariance. The two findings are asserted, and `specs/12` §4.3 now
  says which pre-correction criterion 3 is about.
- **There is no scheme where pre-correction works and joint estimation does not** — the base readings a
  pre-correction needs already make the joint design full rank. The "automatic" choice between them was
  removed rather than kept as dead code, and a property test over every visiting order asserts the
  implication.
- **No solution had ever been labelled approximate.** `Solution.uncertainty_mode` was set by nothing, so every
  solution of every technique claimed to be rigorous, including one weighted entirely by a brochure's
  precision — against FR-203. `to_solution` now derives it from the observations; nothing else changed.
- **A station held in height seeded its gravity with a height in metres** — `approximate_values` read any
  constraint's `up` for a gravity network too.
- **MCGravi and pyGrav form a degree-*k* drift as `(Δt)^k`**, right only at degree 1, and pyGrav prints the
  drift's variance under "SD". Neither touches the degree-1 comparison.

**Not built in P8a, named so the ticks above do not imply them.** The two algorithms, the Gravimeter settings
section, profile management and the result layers — P8b. Scale estimated as a parameter
([`12`](./12-module-gravimetry.md) §5). Ocean loading — P12. A zero-tide conversion: the result notes a
mismatch and does not convert.

### P8b — the surface

**Delivers.** The Gravimetry menu of [`12`](./12-module-gravimetry.md) §2 — *Pre-processing (scale, tide,
drift)* and *Gravimetric network adjustment* — as Processing algorithms; a reader for Scintrex CG-5 and CG-6
files, whose header states the location, GMT offset and tide option the reduction needs; the Gravimeter
section of Global Settings (tidal model and factor, drift model and degree, default weighting, display unit);
gravimeter profile management; gravity stations and differences as result layers, uncheckable observations
shown prominently; the report; gravity in the CSV and XLSX exports, which today would drop it.

**Exit.** Both algorithms run from the menu and the toolbox on a CG-5 file and produce the P8a result as
layers and a report. Values display in the configured unit and are stored in SI. Every `gravimeter.*`
setting is read by the computation.

**Delivered.**

| Delivered | Where |
|---|---|
| *Pre-processing (scale, tide, drift)* and *Gravimetric network adjustment*, in the Gravimetry menu (FR-700…FR-702) | `algorithms/gravimetry/` |
| Readers for Scintrex CG-5 and ZLS Burris exports and a plain CSV; a CG-5's clock settled by its own tide column (FR-160, FR-701) | `io/gravimeter_files.py` |
| The Gravimeter settings: tide model and factor, drift treatment and degree, a precision floor as the default weighting, the display unit — all six read | `core/settings_def.py`, [`12`](./12-module-gravimetry.md) §6 |
| Gravity stations and gravity differences as styled layers, uncheckable ones as prominent as blunder candidates (FR-900, FR-904) | `layers/builders.py`, `resources/styles/gravity_*.qml` |
| The report, in the network algorithm and in the shared adjustment report, in the display unit | `algorithms/gravimetry/network_adjust.py`, `reports/adjustment.py` |
| Gravity in the CSV and XLSX exports | `io/tabular.py` |
| Stations held by name: a known gravity without a sigma | `core/techniques/gravimetry/network.py` |

| P8b exit criterion | State |
|---|---|
| Both algorithms run from the menu and the toolbox on a CG-5 file | **met** — registered in the Gravimetry menu in order; tier 3 runs the chain on a CG-5 export built from the format, and the `reference` workflow runs the production reader, the reduction and the network on RD-07's real survey (2,096 readings, four days) |
| …and produce the P8a result as layers and a report | **met** — USGS's Test 2 through both algorithms recovers every station within 3σ of its published truth and the 0.01 mGal/h drift (0.0101 ± 0.0014 from the base, 0.0092 ± 0.0011 joint) |
| Values display in the configured unit and are stored in SI | **met** — every table, CSV, layer and report names its unit; the documents, the solution and the layers' `gravity_si` are m·s⁻² |
| Every `gravimeter.*` setting is read by the computation | **met** — `tests/structural/test_settings_are_honoured.py` finds all six, and a tier-3 test changes two and sees the algorithm's defaults follow |

**Found.**

- **The residual layer drew every passing observation as *not testable*** — in every adjustment since the
  layers were built. The core recorded a w-test only for blunder candidates and uncheckable rows, and the
  layer read "no test recorded" as "uncheckable"; its tier-3 test checked that the decisions were *among*
  the three categories, which a layer of one category satisfies. The core now records every test it ran, and
  the test asserts a passing observation appears ([`19`](./19-visualization.md) §1).
- **The provenance beside an approximate solution still said `RIGOROUS`** — the one place P8a's fix of the
  solution's mode had not reached ([`05`](./05-uncertainty-and-covariance.md) §2).
- **36 of the 61 settings cannot be edited in the Settings window** — every number, path, string and CRS
  shows *(not editable in this version)*. Two of the six gravimeter settings are among them. Not fixed here;
  recorded in [`15`](./15-ui-menu-and-settings.md) §2.3.
- **The message-template check read only `core`**, so the readers' templates in `io` looked stale; and the
  return-type check judged `tuple[X, ...]` by its ellipsis. Both checks were widened rather than worked around.
- A hand-written profile library missing a field ended in a `KeyError` traceback; it now names the field.

**Not built in P8b, named so the ticks above do not imply them.**

- **A CG-6 reader.** No CG-6 export was reachable to write one against; a CG-6 survey reads through the CSV
  ([`12`](./12-module-gravimetry.md) §3.1).
- **A profile editor** — for gravimeters as for every other instrument, profiles are library documents
  (FR-069 import and export are the document itself); an editor is P12's settings work.
- **Real-survey precision.** RD-07's survey through the algorithms' path lands within 6 µGal of pyGrav's
  published stations, but on one linear drift a day against pyGrav's eight hand-split loops, and the global
  test fails on three of the four days: one drift a day is too simple for that instrument. Sessions come from
  the file's dates; splitting them by loop is not offered yet.
- Carried from P8a: the scale table against a published example, scale as a parameter, ocean loading (P12),
  a zero-tide conversion.

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

**Split, at the maintainer's decision of 26 September 2026**, as P7 and P8 were: **P9a** the computation —
combination, variance components, height and frame reconciliation, the published combined example, gravity
routing, per-technique breakdowns — and **P9b** the surface: the four Integration menu presets
([`13`](./13-module-integration.md) §1), the report's per-technique section and the layers. **The frame
transformation is built here, in-house**, at the same decision, and P10 reuses it rather than routing through
PROJ ([`14`](./14-multi-epoch-monitoring.md) §3).

### P9a — the computation

**Delivered.**

| Delivered | Where |
|---|---|
| `Frame.GEOCENTRIC_3D`: every observation at its own station's vertical, exact Jacobians; geodetic holds whole or refused | `core/adjustment/geocentric.py`, `parameters.py`, [`06`](./06-adjustment-core.md) §2.3 |
| Geoid undulations as parameters with the model as prior; the geoid tested by its residuals; the model named in the report (FR-802, FR-804) | `core/adjustment/undulations.py`, `reports/adjustment.py`, [`13`](./13-module-integration.md) §3.2 |
| Least-squares variance component estimation by technique, constraints as the known part (FR-805) | `core/adjustment/variance_components.py`, [`13`](./13-module-integration.md) §4.1 |
| Frame and epoch transformations: eleven EPSG transformations, velocities, covariances, a record; agreeing with PROJ to a nanometre (FR-832) | `core/geodesy/frames.py`, `scripts/check_frames.py`, [`13`](./13-module-integration.md) §5.1 |
| The combination: merge, reconcile, route, adjust, break down by technique (FR-800…FR-803) | `core/techniques/integration/`, [`13`](./13-module-integration.md) §6.1 |
| Krumm's GNSS baselines read; `Caspary` and `Ghilani_GNSS_Baselines` reproduced, coordinates and sigmas | `io/krumm.py`, [`22`](./22-reference-data-sources.md) §2.2 |
| The geocentric frame cross-validated against DynAdjust on a combined survey | `tests/test_dynadjust_geocentric.py`, [`07`](./07-engine-dynadjust.md) §6.3 |

| P9 exit criterion ([`13`](./13-module-integration.md) §7) | State |
|---|---|
| A GNSS + total station network reproduces a published combined example | **met** — `Caspary`, to 0.05 mm and its sigmas to the printed 0.01 mm |
| Mixing height types without a geoid raises; with one, the model is recorded | **met** — on the solution and, new, in the report |
| A mis-scaled technique's variance component is recovered | **met** — within two of its standard deviations, and the stated uncertainty checked over 40 surveys |
| A three-technique combination runs end to end | **met** — GNSS in ITRF2014, control in SIRGAS 2000, total station and levelling, one solution in ITRF2020 |
| Gravity routes to the in-house core with the reason | **met** — and is adjusted beside the geometry, not dropped |
| Per-technique breakdowns in the report | **computed and tested; rendered in P9b** |

**Found.**

- **Every GeoComp-driven DynAdjust run with an angle in it failed to parse** — the engine read the measurement
  table in the stations' angle format. Unnoticed because every engine run until now carried only baselines.
- **DynAdjust's direction-set rows were attributed to single directions**, though each carries a derived
  angle's correction; no adjusted fixture had a direction set.
- **The DynaML writer held stations at their approximate coordinates** — 0.3 m apart gave 0.3 m in the answer
  and σ̂₀² ≈ 900. P6's networks were read *from* DynaML, where the two coincide.
- **A direction with no setup id was an absolute azimuth in the core** — the Krumm reader had been fixed for
  it, the DynaML reader had not. The rule is the core's now ([`06`](./06-adjustment-core.md) §2.3).
- **The report never named the geoid model** P5 recorded on every position.
- In DynAdjust, recorded in [`07`](./07-engine-dynadjust.md) §6.3: its σ̂₀ for a direction set drops the
  derived angles' correlation, and its slope distances carry the target height along the instrument's
  vertical.

**Not built in P9a, named so the ticks above do not imply them.** The Integration menu, the report section and
the layers (P9b). DynAdjust *running* a combination — routing decides, the engine glue is P9b. The
transformation's common-mode accuracy is recorded, not added to covariances; P10 adds it where absolute
positions are compared. No velocity model (VEMOS): a velocity is supplied or the epoch change is refused. Geoid
priors are independent between stations. The deflection of the vertical is not modelled.

### P9b — the surface

**Delivers.** The four Integration menu items of [`13`](./13-module-integration.md) §1 as presets over the
combination, each with its defaults and validation; the per-technique section of the report (residuals,
redundancy shares, variance components, geoid residuals); the result layers; DynAdjust as the engine for a
combination when routing allows it.

**Exit.** Each preset runs from the menu and the toolbox and produces one solution, a report with the
per-technique section, and layers. Criterion 7 is met in the report.

**Delivered.**

| Delivered | Where |
|---|---|
| The four presets: GNSS and total station, Total station and level, GNSS and level, Multiple techniques | `algorithms/integration/`, [`13`](./13-module-integration.md) §6.2 |
| A local combination, adjusted in heights alone or in 3D; projected inputs in a geocentric one through QGIS's CRS | `core/techniques/integration/combine.py`, `adjustment.py` |
| Levelling benchmarks as orthometric height observations in a geocentric frame; stations nothing places refused by name | same, [`13`](./13-module-integration.md) §6.2 |
| DynAdjust running a combination, agreeing with the in-house core to 0.75 mm | `engines/dynadjust/combination.py`, [`07`](./07-engine-dynadjust.md) §6.4 |
| The report's *Techniques* section, read from the solution's provenance | `reports/adjustment.py`, [`19`](./19-visualization.md) §7.1 |
| A geocentric solution drawn in its own frame's UTM grid, ellipses turned by the convergence | `core/visualization/display.py`, [`19`](./19-visualization.md) §1.1 |
| Network documents from *Build baselines* (with its frame) and levelling *Network adjustment* (differences typed) | [`11`](./11-module-gnss.md) §4.4, [`10`](./10-module-levelling.md) §5 |

| P9b exit | State |
|---|---|
| Each preset runs from the toolbox and produces one solution, a report and layers | **met** — `tests/qgis/test_integration_algorithms.py` runs all four; the menu is generated from the same registry entries |
| The per-technique section in the report; criterion 7 | **met** — [`13`](./13-module-integration.md) §7.1 |
| The layers | **met where QGIS ≥ 3.38 runs** — the display conversion is tested without QGIS; the layer test needs the modern field API, as every result-layer test does |

**Found.**

- **A levelling benchmark in a geocentric combination was silently free.** Its hold names `up`, which is none
  of X, Y, Z, so the geocentric frame held nothing — no error, a free station. Now an orthometric height
  observation; one held exactly is refused.
- **Levelled differences never said their height type**, which P9a's geocentric frame refuses to guess; no
  test had used a levelling network *as the levelling algorithm builds it*.
- A levelling network's `LOCAL` CRS was an "irreconcilable frame"; two agreeing holds kept the first input's;
  a benchmark's placeholder zeros shadowed another input's starting position.
- **The combined solution carried no per-observation results**, so its residual layer would have been empty.
- QGIS matches a bare GRS80 UTM string to "SIRGAS 2000 / UTM" — an ITRF solution drawn that way is labelled
  decimetres wrong. The grid is WKT2 naming the frame.

**Not built in P9b.** The per-technique breakdown on the DynAdjust path. Height-only adjustment of a mark only
levelling reaches, inside a 3D combination. A control-point document. Gravity in the combined report (its
solution is written beside it).

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

**Split, at the maintainer's decision of 28 September 2026**, as P7 to P9 were: **P10a** the computation —
compatibility, frame reconciliation with the transformation's uncertainty, displacements with
cross-covariance, significance, reference-block stability, congruency and strain, velocities, time-series
data and alert evaluation — and **P10b** the surface: the monitoring algorithms, the displacement layers and
alert styling, the time-series panel with its map linkage, the monitoring report, and the product download
(FR-352, FR-353, NFR-010) if the archives are reachable by then.

**Split again, at the maintainer's decision of 28 September 2026, before P10b began**: the product download
(FR-352, FR-353, NFR-010) is **P10c**. P10b re-checked the archives and found one reachable — NOAA's CORS
open-data bucket, which serves IGS final orbits and broadcast navigation without credentials — so the
download can be built and tested this phase. But it is about as large as the monitoring surface, and two
reviewable changes were preferred to one.

### P10a — the computation

**Delivered.**

| Delivered | Where |
|---|---|
| Two epochs compared: FR-105 refusal, compatibility refusals by name, frames transformed with their uncertainty as a common translation, cross-covariance or independence marked | `core/monitoring/compare.py`, [`14`](./14-multi-epoch-monitoring.md) §8.1 |
| S-transformation onto the reference block, its congruency, stepwise localisation naming the station, a refusal to proceed on a moved block; displacements tested jointly and by component | `core/monitoring/congruency.py` |
| Rigid-body motion separated from homogeneous strain, the strain F-tested | `core/monitoring/strain.py` |
| Series and velocities over any number of epochs, referred to the block | `core/monitoring/series.py` |
| Alert thresholds evaluated, over the line whether or not significant | `core/monitoring/alerts.py` |
| RD-08's synthetic half: a structure measured and adjusted as a free network at each epoch | `tests/monitoring_network.py`, `tests/test_monitoring.py` |

| P10 exit criterion | State after P10a |
|---|---|
| RD-08 reproduces, with the significance decisions | **open** — the published half is unreachable from here ([`22`](./22-reference-data-sources.md) §5.3); the synthetic half is met |
| Injected displacement recovered, no false positives | **met** |
| A moving reference station caught and named | **met**, and the analysis refuses to proceed on it |
| No epoch refused | **met** |
| Not significant, never zero | **met** |
| Three epochs: velocities and a plottable series with map-to-plot linkage | **velocities and the series met**; the linkage is the panel's (P10b) |

**Found.**

- **`Solution.from_dict` crashed on a document without an epoch** — an `AttributeError` from the epoch reader —
  instead of refusing it as the constructor does (FR-105). A monitoring input read from disk is where it would
  have surfaced.

**Not built in P10a, named so the ticks above do not imply them.** The algorithms, layers, panel and report
(P10b). The product download (P10b, or moved again with the reason if the archives are still refused). A
published deformation example. Velocities assume independent epochs. Strain is two-dimensional and
homogeneous; there is no vertical strain or velocity field between points.

### P10b — the surface

**Delivered.**

| Delivered | Where |
|---|---|
| The results as documents that the report, the layers and the panel all read: a comparison (or its refusal, with the localisation) and a series; stations placed for the map, geocentric ones in their frame's UTM grid | `core/monitoring/document.py`, [`14`](./14-multi-epoch-monitoring.md) §8.2 |
| *Compare two epochs*: roles named or read from the network, the block tested, refusal after the record is written, displacements, strain, alerts | `algorithms/monitoring/compare_epochs.py` |
| *Time series and velocities*: the block tested at every epoch, the series, a CSV, a velocity layer tied to its series | `algorithms/monitoring/time_series.py` |
| *Monitoring report*: from the saved documents, templated, three sections a template cannot drop; map and plots as inline SVG | `algorithms/monitoring/report.py`, `reports/monitoring.py`, `core/visualization/svg.py` |
| Displacement, displacement-ellipse and velocity layers, styled alert / significant / not significant, the exaggeration in the name | `core/visualization/monitoring.py`, `layers/builders.py`, three QML styles |
| The time-series panel: map selection plots, plot picking selects on the map, CSV and image export | `gui/time_series_panel.py`, [`19`](./19-visualization.md) §5 |
| The compatibility dialog before a comparison | `gui/compare_dialog.py`, [`15`](./15-ui-menu-and-settings.md) §3 |
| A message naming the solutions or stations for every monitoring refusal | `algorithms/monitoring/messages.py` |
| The register of validation data still to be found | [`23`](./23-wanted-reference-data.md) |

| P10 exit criterion | State after P10b |
|---|---|
| RD-08 reproduces, with the significance decisions | **open** — the published half; W-01 in [`23`](./23-wanted-reference-data.md) |
| Injected displacement recovered, no false positives | **met** (P10a) |
| A moving reference station caught and named | **met**, in the core and as the algorithms refuse — both the two-epoch comparison and the series |
| No epoch refused | **met** |
| Not significant, never zero | **met** — in the table, the layer and the report |
| Three epochs: velocities and a plottable series with map-to-plot linkage | **met** — the panel, both directions (`tests/qgis/test_time_series_panel.py`) |

**Found.**

- **A velocity alert on a heights-only series could never be raised.** It was judged on the horizontal
  speed, which a levelling series does not have. It is now judged on the vertical rate there
  (`StationSeries.speed`).
- **A comparison's findings were English sentences** in the core, which does not phrase
  ([`18`](./18-i18n-and-profiles.md) §2), and the report has to say them in three languages. They are now
  codes with their values.
- **A series stored its velocity but not the fitted line's offset**, so a plot could only draw a line forced
  through the first epoch, which is not the line that was fitted.
- **The monitoring refusals had no messages.** P10a's core raised them and nothing phrased them, so through
  an algorithm every one would have read "could not complete the operation", without the stations it names.
  Two codes were also raised through a conditional expression, which the template check cannot see; they are
  now literal.

**Not built in P10b, named so the ticks above do not imply them.** The cross-covariance between epochs as an
input: no document GeoComp writes carries it, so every run is approximate, as it says. The product download
(P10c). A published deformation example (W-01). The layer tests need QGIS ≥ 3.38 and run in CI only; the
development environment has 3.34.

### P10c — product download

**Delivers.** FR-352, FR-353, NFR-010: precise and broadcast products resolved from cache, the configured
product directory, then a configured service, through the QGIS network stack; credentials through the QGIS
authentication system and never in a log, provenance or export; availability checked before a batch; every
product used recorded by name, source and checksum ([`08`](./08-engine-rtklib.md) §5).

**What is reachable**, re-checked 28 September 2026 from the development environment:
`noaa-cors-pds.s3.amazonaws.com` (anonymous), which RD-06 already fetches IGS final orbits and broadcast
navigation from. Still 403: `files.igs.org`, `cddis.nasa.gov`, `igs.bkg.bund.de`, `geoftp.ibge.gov.br`,
`igs.ign.fr`, `garner.ucsd.edu` — W-14 in [`23`](./23-wanted-reference-data.md). The credentialed path has
nothing reachable to authenticate to and is tested against a local server.

**Delivered.**

| Delivered | Where |
|---|---|
| Products, requests and the days a session touches; services as URL templates; the cache keyed by kind, latency, centre and day with a record per product; resolution cache → directory → services; availability before anything is fetched; retry with backoff for a network failure only | `core/techniques/gnss/products.py`, [`08`](./08-engine-rtklib.md) §5 |
| One shipped service, NOAA's CORS open-data archive (`noaa-ncn`): IGS final and rapid orbits, GPS and GLONASS broadcast navigation; others in a services file | `products.NOAA`, `gnss.service_definitions` |
| The fetcher on the QGIS network stack, a login applied by its authentication configuration id; not found, refused login and network failure told apart | `services/downloads.py` |
| Four settings, all read: services in priority order, services file, cache, rapid-orbit fallback | [`15`](./15-ui-menu-and-settings.md) §6 |
| *Download products*: fetch or only check, for a folder's days or a range; copy out; a manifest | `algorithms/gnss/download.py` |
| The four modes, batch and the configuration comparison resolve what their sessions need, refuse a missing product before the engine, and record every product in the run's JSON; batch checks every session first | `algorithms/gnss/common.py` |
| A message for every product and service refusal, naming the product, service or URL | `algorithms/gnss/messages.py` |
| A live check of RD-06's products against NOAA, monthly and on change | `scripts/check_products.py`, the `reference` workflow |

| Criterion ([`08`](./08-engine-rtklib.md) §10) | State after P10c |
|---|---|
| 6. Products resolve from cache without a network call on a second run, and provenance names every product used | **met** — counted calls in tier 1, against NOAA in the `reference` workflow; the run JSON's `products` |
| 7. No credential in any log, configuration file, provenance record or export | **met** — asserted end to end through a real QGIS login (`tests/qgis/test_product_download.py`) |
| Availability before a batch, with the lower-latency option recorded (§5, §9) | **met** — batch refuses before starting, naming each session and product; the fallback setting, recorded as a substitution |
| Authentication failure distinguished from network failure (§9) | **met** — three codes, three messages |

**Found.**

- **Batch processing and Compare configurations never passed precise products**, whatever the ephemeris
  setting said; the single-run modes passed every SP3, CLK and ION file in the directory regardless of its day.
  Orbits are now matched to the days the sessions touch — by IGS name, or by the span an SP3 header states,
  so another analysis centre's orbit is still found.
- **A compressed orbit in the product directory would have been loaded by nothing.** RTKLIB's SP3 reader
  selects files by extension and skips `.gz`, with no error. A compressed directory product is now inflated
  into the cache, with its record.
- **The first P10c commit failed a structural test** (three new public functions with no recorded reason for
  a plain return type), found when the whole suite ran; recorded.

**Not built in P10c, named so the ticks above do not imply them.** Clock and ionosphere files are still passed
from the directory whatever their day (they are now recorded). Ultra-rapid orbits are not offered. No archive
but NOAA has a shipped template, because no other is reachable to test (W-14); IGS, CDDIS, BKG and IBGE are a
services file away, untested. The interactive "proceed with rapid orbits?" of §5 is a setting, not a prompt:
Processing has no place to ask, so the refusal names the setting.

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

**Why it could be built now.** P5 could not: no environment it ran in had a PostgreSQL server
([`17`](./17-persistence-and-interoperability.md) §4). The development environment now has PostgreSQL 16, to
which PostGIS 3.4 installed, and CI runs the `postgis/postgis:16-3.4` service container, so every criterion
below is asserted against a real server rather than a stub.

**Delivered.**

| Delivered | Where |
|---|---|
| One store logic for both backends: the rows a project becomes, FR-135's refusals, the revision check | `io/store/base.py` |
| The PostGIS store: one schema per project, PostGIS and schema checks refused by name, `psycopg2` named when absent | `io/store/postgis.py` |
| Schema 4: `gc_project.revision`, `gc_network_member.ordinal`; migrations on both backends; a PostGIS backup as a schema copy | `io/store/schema.py`, `io/store/migrations.py` |
| Concurrent saves refused, on both backends, under each one's write lock | `ProjectStore._writing` |
| Mode switching, table by table, with every table compared after the copy | `io/store/transfer.py` |
| Connections from the QGIS registry, logins from QGIS authentication, never in a message or the store's name | `services/postgis.py` |
| *Save to project store* in database mode; *Export project to PostGIS*; *Import project from PostGIS* | `algorithms/project/store.py`, `algorithms/project/postgis.py` |
| Messages for every store refusal, which showed as codes before | `algorithms/project/messages.py` |
| A PostGIS service in the `test` workflow, for the store tests and the QGIS job, failing on a skip | `.github/workflows/test.yml` |

| P11 exit criterion | State |
|---|---|
| GeoPackage → PostGIS → GeoPackage lossless, table by table | **met** — every table compared, floats by their bytes (`tests/test_postgis_store.py`; through QGIS, `tests/qgis/test_postgis_project.py`) |
| Migration works on both backends | **met** — a schema-3 store migrated on each; the PostGIS one is constructed, since none older than schema 4 was ever written |
| A concurrent modification detected on save rather than overwritten | **met** — on PostGIS and on GeoPackage; a refused save writes nothing |

**Found.**

- **Re-saving a stored solution failed on every GeoPackage.** `INSERT OR REPLACE` deletes the conflicting row
  first, and the restricting foreign keys refused deleting the stored solution's provenance -- reproduced on
  `main` as an integrity error. A replace that got through would have set every `superseded_by` pointing at the
  row to NULL. Both backends now upsert in place.
- **A migration chain's first `ALTER TABLE` committed on its own** (Python's legacy `sqlite3` mode opens no
  transaction for DDL), so a failed later step left a half-migrated store. Migrations now begin explicitly.
- **A network's order was an accident of SQLite.** Stations and observations read back in the order written
  only because SQLite returns rows in insertion order. Schema 4 records it.
- **`jsonb`, the mapping P5 planned for JSON, cannot hold `NaN`**, which a zero-redundancy solution's global test
  stores; JSON is `text` in both backends. And text needs `COLLATE "C"`, or ordering follows the database's
  locale.

**Not built in P11, named so the ticks above do not imply them.** A project-level setting that remembers which
store a project lives in: the store is chosen per run -- a GeoPackage, or a QGIS connection and a schema -- so
"configurable" is met by the algorithms rather than by a setting. Merging concurrent saves: the second is
refused, not reconciled. A spatial index on the PostGIS geometry columns (the logical schema declares none; a
backend-specific index is the kind of change ADR-0006 anticipates). `psycopg2` is not bundled: QGIS's
installers carry it, and where one does not the refusal names it. Inserts are row by row; a very large
project's copy time is unmeasured.

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

**Also delivers, moved from P8 at the maintainer's decision of 25 September 2026: ocean loading on gravity**
([`12`](./12-module-gravimetry.md) §4.2). It needs per-station coefficients from the Onsala loading service,
unreachable from the development environment, and nothing reachable could check an implementation; written
and unverified it would be a claim rather than a feature. If the service is still unreachable when P12 runs,
the same rule applies again — it moves, and the move is recorded. **Moved to P13 on 3 October 2026** (P12c-5): the service
still refuses the connection.

**Closes.** FR-902, FR-931

**Exit.** No untranslated string in any language. Every algorithm passes the Basic/Advanced identity check.
Thematic maps render for every listed attribute, including the redundancy-number map. Every acceptance
criterion in every specification document has a passing automated test or a documented reason to be manual.

**Split in three, at the maintainer's decision of 2 October 2026**, one pull request each, because the three
halves share nothing but the phase's name and a single change touching all of them could not be reviewed:

| | Delivers | Exit criteria it owns |
|---|---|---|
| **P12a** | The settings reaching the computation; units and display formatting; the Basic/Advanced identity check across every algorithm; an editor for every setting type | Every algorithm passes the identity check |
| **P12b** | Thematic maps for every listed attribute (FR-902); the results panel; print layout templates (FR-931) | Thematic maps render for every listed attribute, the redundancy-number map included |
| **P12c** | The acceptance-criteria audit across every specification; NFR-008 performance; the records — ocean loading moves again if Onsala is still unreachable, and the native-speaker review | Every acceptance criterion has a passing test or a documented reason to be manual; no untranslated string, reviewed |

### P12a — the settings reach the computation

**Delivered.**

| Delivered | Where |
|---|---|
| A parameter's default is its setting, resolved when the algorithm is instantiated, through run, project and global scope | `algorithms/defaults.py`; every algorithm group |
| 29 settings wired to parameter defaults, 4 to behaviours, 4 to the reports; 4 removed as unconsumable | [`15`](./15-ui-menu-and-settings.md) §2.3 |
| *Levelling network adjustment* closes lines between benchmarks and double-run sections before adjusting, and refuses a failure unless acknowledged | `core/techniques/levelling/network.py` `network_closures`, `closure.py` `section_closure`; [`10`](./10-module-levelling.md) §3 |
| The normal orthometric correction applied in the network adjustment, from a positions layer read through QGIS | `orthometric.py` `correct_lines`; [`10`](./10-module-levelling.md) §5 |
| The base-map offer, on a custom property every result layer now carries | `gui/basemap_offer.py`; [`17`](./17-persistence-and-interoperability.md) §5.6 |
| Display formatting: angles, small angles, coordinates and distances in the reports, the adjustment report included | `core/display_format.py`, `algorithms/display.py`; [`19`](./19-visualization.md) §7.4 |
| An editor for every setting type: numbers, text, paths, directories, the CRS | `gui/settings_dialog.py` |
| The structural check reads code, not comments; `NOT_YET_HONOURED` is empty | `tests/structural/test_settings_are_honoured.py` |

| P12a criterion | State |
|---|---|
| Every declared setting is read by the computation | **met** — the structural check, now blind to comments; and every parameter default asserted to follow its setting (`tests/qgis/test_settings_reach_the_computation.py`) |
| Every algorithm passes the Basic/Advanced identity check | **met** — all 45, by construction ([`16`](./16-processing-provider.md) §4.1, `tests/qgis/test_basic_advanced_identity.py`) |
| Every setting editable in the window | **met** — `tests/qgis/test_settings_dialog.py` |
| No untranslated string | **met** for P12a's strings, pt-BR and es; the native-speaker review is P12c's |

**Found.**

- **Five settings passed the "is it read" check on prose alone** — a comment, a docstring — so the true
  count of unread settings was 41 of 66, not 36. The check now reads string literals in code.
- **The traverse setting's default was least squares**, which the Traverse algorithm cannot compute; the
  angular tolerance setting said 29.9″ where the algorithm used 30″; the face-distance setting mirrored a
  last-resort constant rather than the parameter's *from the instrument*. Each had agreed with nothing, which
  no one could see while nothing read them.
- **The closure check promised an acknowledgement nothing asked for.** Its finding says GeoComp will not
  adjust a failing line without one; the network adjustment adjusted it anyway. The orthometric correction
  had been written in P4 and called by nothing since.
- **Every UTM northing in a report was printed with an exponent**, `7.3951e+06`: the report formatter
  switches at a million, which a southern-hemisphere northing always exceeds.

**Not built in P12a, named so the ticks above do not imply them.** A project-scope override control in the
window — the settings service has the scope; the window writes global only. Number formatting per locale
(FR-094): every report uses a point as the decimal separator. When no default epoch is stated, three network
adjustments still fall back to an epoch of their own (2000.0, or 2026.0 for levelling), which is an assumed
epoch in FR-105's terms; P12c's audit owns it. The levelling reduction reports and the monitoring report keep
their own units (metres to 0.01 mm; millimetres). The offer is tested against a message bar, not inside a
running QGIS window.

### P12b — thematic maps, the results panel, print layouts

**Delivered.**

| Delivered | Where |
|---|---|
| A thematic map for every FR-902 attribute, as a named style on the layer that carries it; fitted classes where the scale is the network's, fixed bands where the value has a meaning of its own | `layers/themes.py`, `core/visualization/{themes,classes}.py`, `resources/styles/themes/`; [`19`](./19-visualization.md) §4 |
| The MDB drawn as a length, and an epoch on every observation feature, so both can be mapped | `layers/builders.py` `mdb_displacement`, `epoch` |
| Every legend label translated, the shipped styles' included | `scripts/translations.py`, `layers/styles.py` `translate_legend` |
| The results panel: run history, statistics, observations sorted and filtered, stations, links to the run's own features and to the time series | `gui/results_panel.py`, `core/visualization/results.py`; [`15`](./15-ui-menu-and-settings.md) §4 |
| Result layers name the solution document they came from | `algorithms/layer_outputs.py` `SOLUTION_PROPERTY` |
| Three print layout templates and *Create print layout*, stating the exaggeration on the page | `resources/layouts/`, `algorithms/project/print_layout.py`; [`19`](./19-visualization.md) §6 |

| P12b criterion | State |
|---|---|
| Thematic maps render for every listed attribute, the redundancy-number map included | **met**, but for the campaign — `tests/qgis/test_thematic_maps.py` draws a feature of each kind in its class under each of the eight maps, and the maps reach a real adjustment's layers (`tests/qgis/test_result_layers.py`). *Epoch or campaign*: an observation records its epoch and no campaign, so the epoch is mapped and there is nothing to draw a campaign from |
| The results panel, each clause of [`15`](./15-ui-menu-and-settings.md) §4 | **met** — `tests/qgis/test_results_panel.py`, and `tests/test_results_view.py` without QGIS |
| Print layout templates for the three deliverables, adaptable | **met** — `tests/qgis/test_print_layouts.py`, the exaggeration in the legend and notes included ([`19`](./19-visualization.md) criterion 2) |
| No untranslated string | **met** for P12b's strings and every legend label, pt-BR and es; the native-speaker review is P12c's |

**Found.**

- **No map legend had ever been translated.** FR-090 asks for value maps in the active language; the 31
  labels of the shipped QML styles reached every legend in English, because the extractor read Python and
  nothing else. It now reads the styles too.
- **The redundancy-number map, as first written, left a gap** between 0.00999999 and 0.01 in which an
  observation was drawn in no class. The test written for the boundary found it; the class expression now
  makes the 0.01 test itself.
- **A map of raw MDBs cannot be read.** A direction's MDB is in radians and a distance's in metres; on one
  scale either every angle or every distance falls in one class. Hence `mdb_displacement`.

**Not built in P12b, named so the ticks above do not imply them.** The results panel opens GeoPackage stores
only, and has no observation-type column (the type is in the network document, which it does not read).
Relative ellipses ([`19`](./19-visualization.md) §3 item 4) are in no layer, and the scale-reference ellipse
(item 6) in no template. The fitted classes are fitted when the layer loads; a layer edited afterwards keeps
them.

### P12c — the audit, and the work it found

**Delivered in several pull requests, not one.** The split table above gives P12c one pull request. The audit
found too much for that: 31 criteria partly met and 12 open, with the work behind them ranging from a missing
test to a feature not yet built. Since 2 October 2026 the maintainer's standing instruction is that a
pull request whose CI is green is merged. P12c is therefore a sequence of pull requests, each one coherent,
each one updating the register:

| | Delivers |
|---|---|
| **P12c-1** | The register itself — [`20`](./20-testing-and-validation.md) §10, one row per criterion, held by a structural check — and the stale state notes it contradicted |
| **P12c-2** | The gaps that are tests and small code: the FR-604 notice, the plugin's load and unload, a model run headless, help for every algorithm, the language switch, the glossary check, strategies in the export and the provenance, the remaining criteria of 05, 09, 10, 15 and 21 |
| **P12c-3** | The gaps that are features: cancellation that leaves no partial output, the locale's decimal separator (FR-094) and the locale round trip, the settings window showing a project override, the base-station frame transformation, and the assumed epochs P12a left to this audit |
| **P12c-4** | NFR-008: the sparse path, and the refusal without SciPy, measured |
| **P12c-5** | The records: ocean loading, the native-speaker review, and the remaining **[C]** claims; P12's exit |
| **P12c-6** | The register rows P12c-5 found to be work in this repository: 07 1, 08 2, 16 7, 19 3, 20 6, 21 4, 21 5 |

#### P12c-1 — the register

**Delivered.** [`20`](./20-testing-and-validation.md) §10: 135 rows, one per criterion of specifications 05 to
21, each with its state and evidence. `tests/structural/test_acceptance_register.py` fails on a criterion
with no row or two, a **met** row with no test, a row that is not met and gives no reason, a count in the
summary that drifts, and a citation of a test, class or file that does not exist. Every one of the 146
citations resolved once five misremembered class names were corrected, which is what the check is for.

**State at the audit: 90 met, 31 partly met, 12 open, 2 manual.** Seven rows were then closed or narrowed by tests
written against them, leaving **96 met, 27 partly met, 10 open, 2 manual**:

- The FR-604 notice, in help and run, for both criteria that name it (`tests/qgis/test_ppp_notice.py`).
- The plugin loaded on a main window, unloaded without a trace and reloaded without duplicates, in a QGIS of
  its own (`tests/qgis/test_plugin_lifecycle.py`). A deliberately leaked toolbar fails it.
- An instrument profile computing identically after export and re-import.
- The free-and-constrained check on the triangulateration.
- Geometric and trigonometric height differences given a variance component each.

**Found.**

- **Criteria recorded as met that were met in part.** A test existed near each and asserted something
  else. Examples:
  - specs/09's free-and-constrained check ran on a trilateration, where the criterion says triangulateration;
  - the FR-604 notice is written but nothing asserts it;
  - specs/16's help check covers four algorithms of 46;
  - two of specs/20 §2's eleven structural checks were never implemented — every algorithm's help, and the
    locale round trip.
- **Cancellation is not handled.** 13 of 46 algorithms check for it and none writes its outputs atomically,
  so specs/16 criterion 8 and specs/17 criterion 6 are open. Nothing had claimed them met; nothing had
  looked either.
- **An approximate solution does not name its strategies in its provenance**, which records the mode only,
  nor in the export's statistics sheet. The report derives them from the covariance.
- **Two state notes contradicted later phases.** specs/17 called the *Adjust* format blocked, though it was
  met after P6. specs/11 called its criterion 2 red, though it was met since P7e. Both now say so.
- **No glossary check exists**, though specs/18 criterion 4 names one.
- **The document *Trigonometric levelling* writes is read by nothing.** Its height differences cannot
  reach a network adjustment, so specs/10 criterion 5 is met in the computation and not from the menu.
- **specs/15 criterion 1 still said seven entries**, two phases after FR-003 was amended to eight.

**Not done in P12c-1, and not implied by it.** Every row that is not met is listed in §10 with what it
waits on; the four pull requests above work through them.

#### P12c-2 — the gaps that were tests and small code (first pull request)

**Delivered.** Six register rows closed, leaving **102 met, 21 partly met, 10 open, 2 manual**:

| Criterion | Now shown by |
|---|---|
| specs/05 5: approximate results name their strategies everywhere | `tests/test_approximation_is_named.py`, against the provenance, its document, its stored row (schema 5) and the export |
| specs/16 6: help documents every parameter with its unit | `tests/qgis/test_algorithm_help.py`, all 46 algorithms |
| specs/18 2 and 3: the whole UI in either language; GeoComp's language over QGIS's | `tests/qgis/test_language.py`, in both languages |
| specs/20 7: the comparison export, documented | [`20`](./20-testing-and-validation.md) §5; `tests/test_export.py::TestTheComparisonExport` |
| specs/21 8: the About dialog's licences and engine versions | `tests/qgis/test_about_dialog.py`, `tests/test_engine_status.py` |

**Found — every one of them by writing the test the register asked for.**

- **The in-house adjustment never set a station's positional uncertainty.** Only DynAdjust's reader did. Every
  in-house solution's report, tables, results panel, station layer and P12b's *Positional uncertainty* map
  showed it missing, and nothing failed. It is the confidence ellipse's semi-major axis, as
  [`06`](./06-adjustment-core.md) §4.5 now records.
- **Five places never translated, though every catalogue was complete.** Each word was filed under one context
  and looked up under another:
  - "Requirement" in every help;
  - every Processing group's name;
  - the four GNSS modes' shared parameters and help;
  - the PostGIS switch's connection and schema;
  - the adjustments' layer outputs.

  [`18`](./18-i18n-and-profiles.md) §2 now states the rule, and `tests/qgis/test_language.py` holds it from
  outside.
- **The About dialog and the system report both said the engines were still to come**, three phases after
  they arrived. The dialog showed no version, and the report put "not integrated yet" in the document a support
  request attaches. Both now ask the engines (`engines/status.py`). The dialog also gained RTKLIB's licence,
  which it had left out.
- **The provenance recorded an approximate solution's mode and not its strategies.** Store schema 5 adds the
  column. A `Solution` now keeps its provenance's strategies in step with its own uncertainties, whichever
  producer built it.
- **No help documented its parameters**, and one label stated no unit — *Trigonometric levelling*'s imbalance
  tolerance, a fraction of the longer sight.

**Not done here.** Of P12c-2's list, the glossary check (specs/18 criterion 4), a model run headless (specs/16
criteria 2 and 5), the chain-against-single propagation test (specs/05 criterion 3) and RD-01's styled layers
(specs/09 criterion 9) are the next pull request's.

#### P12c-2 — the rest of it (second pull request)

**Delivered.** Five more register rows closed, leaving **107 met, 18 partly met, 8 open, 2 manual**:

| Criterion | Now shown by |
|---|---|
| specs/05 3: the chain is one propagation | `tests/test_total_station.py::TestTheChainIsOnePropagation`. The whole total-station chain is differentiated numerically, through 16 inputs, and agrees with the stepwise propagation to 2e-8 |
| specs/09 9: RD-01 arrives as styled layers with ellipses | `tests/qgis/test_model_chain.py::TestRd01ArrivesAsStyledLayers`, run as the menu's dialog runs it |
| specs/16 2: every way of running gives one answer | `tests/qgis/test_model_chain.py::TestEveryWayGivesOneAnswer`: PyQGIS, the task the toolbox and batch dialogs use, and a saved model |
| specs/16 5: a model runs headless | `tests/qgis/test_model_chain.py::TestTheModel`, saved as `.model3` and loaded back |
| specs/18 4: terminology checked against the glossary | `scripts/check_glossary.py`, held by `tests/structural/test_glossary.py` |

**Found.**

- **128 translated strings did not use the glossary's terms**, 61 Portuguese and 67 Spanish. Nothing had
  checked them against it. Most were the levelling strings, which called an instrument *setup* a *station*
  (*estação*/*estación*). That is the glossary's word for a mark, so a levelling dialog named the two the
  same, while the total-station strings had always said *estacionamento*. The others had worded *minimal
  detectable bias*, *datum defect*, *covariance matrix* and *cluster* freely. In Portuguese, *resection* and
  *forward intersection* were not *à ré* and *à vante*; in Spanish, the target height was the prism's.
  [`18`](./18-i18n-and-profiles.md) §3 lists them.
- **European Portuguese in the pt_BR catalogue.** Its vocabulary is replaced. About twenty constructions such as
  *pelo que* and *tem de* are left for the native speakers' review in P12c-5.
- **The chain loses nothing, measurably.** Stage by stage it is the single propagation to the precision of the
  difference quotient. The one term it leaves out by design, the cyclic error's slope in the distance,
  moves the reduced pointing's covariance by at most 5.5e-5 on a 400 m sight.

**Not done here.** specs/16 criterion 7, validation naming the parameter in every algorithm, stays partly met;
a test across all 46 algorithms is bigger than this pull request.

#### P12c-3 — the feature gaps (first pull request)

**Delivered.** Seven register rows closed, leaving **114 met, 14 partly met, 5 open, 2 manual**:

| Criterion | Now shown by |
|---|---|
| specs/16 8 and 17 6: a cancelled run leaves no partial output; an import leaves its target unchanged | `geocomp/algorithms/transaction.py` around all 46 algorithms; `ProjectStore.atomic`; a cancellable `copy_store`; `tests/qgis/test_cancellation.py`, `tests/qgis/test_postgis_project.py::TestCancelling` |
| specs/18 5 and 20 2: the locale round trip | `tests/qgis/test_locale_numbers.py::TestFilesKeepAPoint`, RD-01's chain under pt-BR and es |
| specs/18 6 and 19 7: displayed numbers in the language's separator | `core/number_format.py`; `tests/qgis/test_locale_numbers.py::TestReportsUseTheComma` |
| specs/15 6: the window shows and sets a project's override | `tests/qgis/test_settings_dialog.py` |

**Found.**

- **Cancelling reported success and kept what was written.** 13 algorithms looked at the cancel button, each
  returned an empty result from wherever it noticed, and Processing called the run complete. The rule now sits
  around every algorithm, so a new one cannot leave it out. A run cancelled after writing puts back the files
  it replaced, removes the ones it made, and raises.
- **A first version undid outputs on any failure, and the monitoring tests caught it.** An analysis that refuses
  writes the refusal document and report before raising, and those are what the user reads. A failure is now
  left as it failed.
- **A save into a project was three transactions**: the project, its network, the solution. Cancelled between
  them, it left the first stored. They now commit together or not at all.
- **Two report tables printed a value with `str()`**, the settings with their scopes and the provenance
  parameters, so a point appeared in every language. The locale test found them.
- **The settings window made one project's override every project's.** It loaded the override as the row's
  value and wrote every row globally on OK.

**Not done here.** Thousands grouping and locale dates (FR-094's other half), recorded in
[`18`](./18-i18n-and-profiles.md) §5. Of P12c-3's list, the base-station frame transformation (specs/11
criterion 7), the assumed epochs P12a left and the trigonometric-levelling document read by nothing are the
next pull request's.

#### P12c-3 — the rest of it (second pull request)

**Delivered.** Two register rows closed, leaving **116 met, 12 partly met, 5 open, 2 manual**, and P12a's
assumed epochs settled:

| Gap | Now |
|---|---|
| specs/11 7: a base in another frame transformed, with a record | `stations.to_frame`. Relative runs fetch the base from the reference-station database and hold it in the run's frame at the session's epoch. RTKLIB gets explicit `xyz`, and the run's summary keeps the record. `tests/qgis/test_base_station_frame.py` |
| specs/10 5: geometric and trigonometric combined from the menu | *Levelling network* reads *Trigonometric levelling*'s document and estimates a variance component per technique. `tests/qgis/test_levelling_algorithms.py` |
| FR-105: the epochs P12a left assumed | An unstated epoch is the network's own, or the old default marked *assumed*, which the report shows and a comparison refuses. `tests/qgis/test_assumed_epoch.py` |

**Found.**

- **No processing run read the reference-station database.** A relative run held its base where the RINEX
  header put it: an approximate position in no stated frame. The frame check guarded a path nothing took.
- **QGIS's geographic CRS for a projected one has no authority code.** `toGeographicCrs()` returns the base with
  its axes normalised for display. The project's frame is therefore read from the WKT2 base CRS's name.
- **The solution model requires an epoch, by design**, so that every solution can enter a comparison. The
  assumed default therefore stays for a network that states none, and is marked rather than removed.

**Not done here.** *Build baselines* still takes the base's frame as a parameter rather than reading the run's
summary.

#### P12c-4 — network scale (NFR-008)

**Delivered.** The sparse adjustment path, the solver choice and the refusal without SciPy, measured to
10,000 stations; [`06`](./06-adjustment-core.md) §2.4.1 has the design and the table, and ADR-0008 what it
means. A criterion was added to make it checkable — specs/06 8 — and is met, so the register stands at
**117 met, 12 partly met, 5 open, 2 manual, of 136**.

| | |
|---|---|
| The choice | `core/adjustment/scale.py`, before anything is allocated: dense to a 1 GiB footprint, then sparse with SciPy; without it dense to half the machine's memory, then `adjustment_needs_scipy` |
| The sparse path | `core/adjustment/sparse.py`: SuperLU under a minimum-degree ordering, one sweep for each station's covariance, **Q**ᵥᵥ over **P**'s blocks and the external reliability; the rank examined by Lanczos beyond 2,000 unknowns |
| Measured | 10,000 stations in 84 s and 578 MiB (97 s free); 1,600 stations in 2.5 s against the dense path's 48 s, agreeing to 1e-10 |
| Tested | `tests/test_sparse_adjustment.py` (seven networks, every statistic), `tests/test_network_scale.py` (the choice and the refusal, where SciPy is absent too), and the whole suite again with `pytest --sparse` in CI's QGIS job, which now installs SciPy if its image lacks it |

**Found.**

- **The dense path's reach was overestimated by half.** P2 put it at 2,000–3,000 stations without measuring.
  The residual cofactor matrix is m × m in the observation rows, and 900 stations already peaked at 698 MiB.
- **The redundancy numbers cost O(m³) where O(m²) does.** `diag(Qvv P)` was formed as the full product. Both
  paths now take the diagonal alone (`blocks.product_diagonal`).
- **The gravimetry report read its strategies from the full covariance**, which a solution need not carry:
  found by the `--sparse` run, and read from the solution's stations now.
- **A comparison of epochs fell back silently** to each station's own block when a solution lacked the full
  covariance, as a DynAdjust run without `--output-all-covariances` does. It now says so
  (`station_blocks_only`).
- **A free network's reported condition number is noise**, on both paths: it is that of **N**, which is
  singular by construction, so it reports its largest eigenvalue over a rounding error (about 1e16). Recorded,
  not fixed: the meaningful figure is over **N**'s range, and no criterion asks for it.

**Not done here.** A geocentric network of 10,000 stations has not been measured. The sparse path's solution
carries no full covariance, by design. Variance component estimation stays dense.

#### P12c-5 — the records, and P12's exit assessed

**Delivered.**

| | |
|---|---|
| Ocean loading | The Onsala service still refuses the connection (403 on CONNECT, re-checked 3 October 2026), so it moves again, to P13, on the same condition: written when something can check it (W-11). [`12`](./12-module-gravimetry.md) §4.2 |
| The native-speaker review | **Not held**: it needs people, and moves to P13. Prepared: 23 pt_BR strings had their European markers converted and one Spanish *fichero* became *archivo*; what is left for the reviewers, and the table that will record the review, are in [`18`](./18-i18n-and-profiles.md) §3.1 |
| The **[C]** claims | 07's and 08's were discharged in P6 and P7. 22 §3 (JAG3D) is now checked against JAG3D's README at a pinned commit, and **corrected**: TraCIM verified its form-fitting module, not its network adjustment. The PTB report and the Zenodo datasets it cites stay unreachable and are marked so. 22 §5's published RD-08 stays a lead (W-01), its host still refusing the connection. Every **[C]** is now discharged, corrected or recorded as unresolvable from here, with the item that would resolve it |

**P12's exit, assessed.**

| Exit criterion | State |
|---|---|
| No untranslated string | **met**: 2,212 of 2,212 in pt_BR and in es |
| …reviewed by native speakers | **not met**: needs people; P13 |
| Every algorithm passes the Basic/Advanced identity check | **met** (P12a) |
| Thematic maps render for every listed attribute, the redundancy-number map included | **met** (P12b) |
| Every acceptance criterion has a passing test or a documented reason to be manual | **not met**: 17 of 136 rows, 12 partly met and 5 open |

The 17 rows divide three ways:

* **Nine wait on reference data this environment cannot reach** — 05 2, 06 1, 09 5, 10 1, 10 2, 10 4, 12 1,
  14 3 and 20 3, each with its W- item in [`23`](./23-wanted-reference-data.md). They cannot be closed from
  here at all, and P13's own exit — every reference dataset with a passing test — inherits them.
* **One is P13's by definition**: 21 6, a tagged release.
* **Seven are work in this repository**: 07 1 (the remaining DynaML types against the engine), 08 2 (a
  configuration re-run and compared), 16 7 (inputs validated before computing, across the algorithms), 19 3
  (a layer that draws relative ellipses), 20 6 (coverage measured), 21 4 (the engine manager on Windows and
  macOS) and 21 5 (the QGIS tier beyond one image). They are **P12c-6**.

**P12 does not exit with this pull request**, and saying so is the point of the assessment: a phase marked
finished with seventeen rows behind it would be the kind of claim the register exists to prevent.

**Not done here.** The review itself. Ocean loading, again.

#### P12c-6 — the in-repo rows (first pull request)

**Delivered.** Four of the seven rows P12c-5 named, leaving **121 met, 9 partly met, 4 open, 2 manual, of
136**:

| Row | Now |
|---|---|
| 07 1: every mapped type, schema and `dnaimport` | One network writes all eighteen codes; both files validate against upstream's `DynaML.xsd`, vendored, and `dnaimport` reads all 28 rows with no warning. `tests/test_dynaml_every_type.py`, in the `engine` workflow with `lxml` installed so it cannot skip |
| 08 2: `-k` reproduces the run | The written configuration, given to `rnx2rtkp -k` by hand, writes the same `.pos` byte for byte |
| 16 7: inputs checked first, refusals naming them | `algorithms/inputs.py`, inherited by every algorithm; `tests/qgis/test_inputs_are_named.py` walks every algorithm and every input three ways |
| 20 6: coverage, every public function reached | `scripts/check_coverage.py` after the QGIS job's full run: 95.6% of `core/`, all 685 public functions reached |

**Found.**

- **No refusal of a missing input file named the input.** Of 38, most gave the path alone; four gave a
  traceback (*Gravimetry pre-processing*), an internal code with its context (*Export* and *Report*, which
  showed `str(error)`), or "could not complete the operation" (*Compare two epochs*, *Import field book*:
  their codes had no template). The project documents' codes clashed with the network document's template
  of the same name, which interpolated a key they never supplied; they have their own now.
- **QGIS names a bad value by the parameter's internal name**, which no dialog shows.
- **A PyQGIS run never calls `checkParameterValues()`**, so a check placed only there misses scripts and
  models; the wrapper around `processAlgorithm()` asks again.
- **49 public functions of `core/` were reached by no test**, among them `RejectionRecord`'s serialisation:
  the record of why an observation was rejected had never been written and read back.
- **The message-template check read only `core/`, `io/` and `services/`** for raise sites, so codes raised in
  `algorithms/` could never be checked against their templates.

**Not done here.** 19 3 (a layer of relative ellipses), and 21 4 and 21 5 (the engine manager and the QGIS tier
on Windows and macOS) — the next pull requests.

#### P12c-6 — the in-repo rows (second pull request)

**Delivered.** Row 19 3, leaving **122 met, 8 partly met, 4 open, 2 manual, of 136**. Every adjustment offers a
sixth layer, *Relative ellipses between observed stations*: one ellipse for each pair of estimated stations an
observation joins, from their joint covariance, drawn at the middle of the line at the absolute ellipses'
factor and confidence, which its name states (`core/visualization/relative.py`; [`19`](./19-visualization.md)
§3, as built). The computation is checked against `relative_ellipse` to 1e-12, and the layer feature by
feature against the solution's covariance on the CI image.

A line to a fixed station is not drawn: the solution does not estimate that station, and the line's ellipse
would be the free station's own, already on the ellipse layer. The layout template did not need changing: its
notes state the factor of any layer with an `exaggeration` field, so this layer's reaches the page as the
others' do.

**Found.** No defect. One result looked like one and is not: three of the trilateration's relative ellipses
equal three of its absolute ones, but not the pair's own. The network is a square A B C D around E with A fixed,
so B→C is the vector A→D moved and has D's ellipse, and B→D is A→C and has C's.

**Not done here.** A solution that carries each station's own covariance only — the sparse path, or a
DynAdjust `.apu` written without `--output-all-covariances` — draws no relative ellipses, and the run says so;
computing the cross blocks for the observed pairs alone on the sparse path is possible and not built. 21 4 and
21 5 — the next pull request.


#### P12c-6 — the in-repo rows (third pull request): the engine manager the user can reach

**Delivered.** Row 21 4's DynAdjust half, and the plugin around it; the row stays **partly met** (RTKLIB,
below), so the state is unchanged at **122 met, 8 partly met, 4 open, 2 manual, of 136**.

- *Paths and engines* in Global Settings holds the DynAdjust directory and the RTKLIB program (global scope
  only), shows each engine's state, and opens *Project ▸ Install an engine*.
- *Install an engine* downloads the pinned release over the QGIS network stack, verifies it, installs it in
  the profile, **records** what it installed (`installed.json`), and runs it.
- Every algorithm that runs an engine, the About dialog and the system report find it the same way: the
  configured path, then GeoComp's installation, then the system path (`services/engines.py`).
- The `engine` workflow's `manager` job runs the real pinned archive on Linux, Windows and Apple-Silicon macOS:
  downloaded, verified, every program found, run, overridden by a configured directory, and used to adjust a
  network that agrees with the committed fixture to 0.1 mm.

**Found.**

- **Nothing in the plugin called the engine manager.** P6 recorded it as installing on Linux; it did, from a
  Python prompt. No algorithm, setting or dialog reached it, and its docstring named a module
  (`services/engine_downloads`) that never existed.
- **No engine looked in the folder the manager installs into.** An installation that had downloaded and
  verified would have been reported absent and never run.
- **RTKLIB had no configurable path anywhere**, against FR-066 and FR-300: it was found on the system path
  or not at all, and the three GNSS algorithms built it with no arguments.
- **The *Paths and engines* page was empty**, and told whoever opened it that its settings were "added by
  the development phase that implements this equipment type" — five phases after the engines arrived.
- **An absent RTKLIB reached the user as a code**: "could not complete the operation
  (computation.engine_not_available)". The error's own hint sent them to install it from that empty page,
  which offers no RTKLIB download at all. A configured DynAdjust directory that did not exist was likewise a
  code. Neither had a template; the engine package's other 80-odd codes still have none.
- **QGIS's blocking request does not resolve a relative redirect.** GitHub's is absolute, so release
  downloads work; a mirror answering with a relative `Location` would fail as a download error.

**Not done here.**

- **RTKLIB is not acquired.** Its upstream publishes executables for Windows only, from tag `v2.5.1`
  (`62d4677`), which is not the build the parsers were checked against (`06e8644`). Pinning it means
  checking that release's output first; Linux and macOS have nothing upstream to download, which needs
  either upstream binaries or a decision to amend criterion 21 4.
- **The engine package's error codes** — DynAdjust's stages and parsers, RTKLIB's — have no templates, and
  `tests/structural/test_message_templates.py` reads only `engines/manager.py` and `engines/base.py`.
- **Row 21 5**, the QGIS tier on Windows and macOS — the next pull request.

#### P12c-6 — the in-repo rows (fourth pull request): the QGIS tier on every system

**Delivered.** Row 21 5, leaving **123 met, 7 partly met, 4 open, 2 manual, of 136**
([`21`](./21-packaging-ci-release-licensing.md) §5, as built).

- **Released QGIS, not nightly.** The QGIS tier ran in `qgis/qgis:latest`, which is the nightly build
  (4.3.0-Master): no released QGIS was under test. It now runs on the releases the images' `stable` and `ltr`
  tags name, resolved when the workflow runs (`scripts/qgis_versions.py`). Today that is 4.2.3 alone: the `ltr`
  tag is 3.44.15, which ADR-0007 excludes, and a 4.x LTR joins the matrix with no change.
- **Windows and macOS**, each in the QGIS a user installs there and that QGIS's own Python: OSGeo4W's 4.2.3
  (Python 3.12.15, Qt 6.11.0) and the official bundle through Homebrew, 4.2.2 (Python 3.12.11, Qt 6.11.1).
  The whole suite runs, not tier 3 alone: tier 1 had run on these systems since P0, but on python.org's Python
  and PyPI's NumPy. First green run: 4,705 passed on Windows and 4,719 on macOS, none failed; the skips are
  reference data, tier 4 and PostGIS, and on Windows the engine-installation tests.
- **How was found by asking the runners.** Every installer's host is unreachable from the development
  environment, so three probe rounds ran there first: OSGeo4W installs unattended in under three minutes and
  carries pytest and SciPy as packages; its launcher replaces `PATH`; the macOS bundle keeps its standard
  library in `Contents/Resources/python3.12`, which only `PYTHONPATH` can name.

**Found.**

- ***Save to project store* showed a code.** Given a file that is not JSON, it raised `str(error)` where its
  siblings raise the template, so the user read `data.json_document_unreadable (expected=…, path=…)`. On Linux
  the path inside that matched the input's, the input's label was put in front, and
  `tests/qgis/test_inputs_are_named.py` passed. On Windows `repr()` doubles a path's backslashes, nothing
  matched, and the test failed — the first run there. Fixed both ways, and the test now refuses a code where a
  sentence belongs, which fails on Linux too against the old algorithm.
- **No released QGIS was under test** (above), in the `test` workflow or in `build`'s install check.

**Not done here.**

- **The LTR legs have not run.** OSGeo4W's `qgis-ltr` and the `qgis@ltr` cask are named in the workflow and
  will first run when the `ltr` tag is a 4.x release; until then the row is met on ADR-0007's reading of
  NFR-001, stable alone.
- **PostGIS runs on Linux only**: service containers exist on Linux runners alone.
- **On Windows the engine-installation tests skip**: their stand-in engine is shell scripts, and DynAdjust's
  Windows programs would need a stand-in `.exe`. The `engine` workflow's `manager` job installs and runs the
  real Windows archive; the QGIS fetcher and *Install an engine* on Windows are unexercised.
- *Add base map* and *Adjust network (DynAdjust)* still raise `str(error)`: their codes have no templates, so the
  template path would say less, not more. The templates are the engine-code follow-up named above.

With this, P12c-6's rows are done except 21 4's RTKLIB half, which needs upstream binaries or a decision on
the criterion. The 11 rows not met are those nine waiting on reference data, 21 6 (P13's) and 21 4.

#### P12c-7 — every error in words (first pull request): the engines

NFR-006 is standing: an error says what failed, why, and what the user can do. Two P12c-6 records named the
engine package's 80-odd codes as having no template. Counting all of `geocomp/` found **457** in that state,
read by the user as "GeoComp could not complete the operation (data.some_code)". This is P12's own goal,
"everything present, coherent, and finished", and it is work in this repository, so it is P12c-7.

**Delivered.**

- **The 81 codes of the engine package have templates**, with pt-BR and es. They cover:
  - what GeoComp cannot write for DynAdjust;
  - a stage that failed;
  - DynAdjust's output, DynaML and DNA files that do not read;
  - RTKLIB's job checks, its run failures and `.pos` files that do not read;
  - the engine manager's malformed digest.
- ***Adjust network (DynAdjust)*** uses them; it showed `str(error)`, the code and its context.
- ***Batch GNSS processing*** phrases each failed session with its template. The batch's result now keeps the
  error itself.
- **A ratchet** (`tests/structural/test_message_templates.py`, specs/18 §2):
  - it reads all of `geocomp/` where it read five places;
  - a code raised without a template fails unless it is in a baseline list of the codes still without words;
  - that list may only shrink. The eighth pull request emptied it and removed it.

**Found.**

- ***GNSS processing* dropped RTKLIB's message** (FR-305; specs/08 §9). The engine adapter extracts
  `rnx2rtkp`'s last word and puts it on the error. The algorithm rendered that error through a template that
  did not exist, so a failed run read "could not complete the operation (engine.rtklib_run_failed)". A
  structural rule now holds it: a code whose every raise site carries an engine's diagnostic must have a
  template that shows it. `tests/qgis/test_engine_messages.py` reads it back for all five such codes.
- **The template check scanned five places**, and every place it skipped held codes no template covered.
  That was how 457 accumulated without a test failing.

**Not done here.** The other 376 codes, by area:

| Area | Codes |
|---|---|
| `io/` | 58 |
| `core/` | 49 |
| `core/models/` | 45 |
| `core/instruments/` | 39 |
| `core/techniques/levelling/` | 38 |
| `core/techniques/gnss/` | 32 |
| `core/adjustment/` | 30 |
| `core/techniques/total_station/` | 30 |
| `core/techniques/gravimetry/` | 14 |
| `core/geodesy/` | 13 |
| `core/statistics/` | 7 |
| `core/preanalysis/` | 6 |
| `core/visualization/` | 6 |
| `core/techniques/integration/` | 4 |
| `reports/` | 3 |
| `services/` | 2 |

Some are guards no user input reaches, such as a matrix of the wrong shape passed between two functions.
They still need words, because a defect is exactly when they surface. The readers in `io/` come first:
there a malformed file is the user's, and the message is all they have to find it.

#### P12c-7 — every error in words (second pull request): the file readers

**Delivered.** Templates, with pt-BR and es, for the 28 codes of the readers the algorithms use. That leaves
**348** in the baseline:

- RINEX files and the folder they are scanned from, shown by the GNSS algorithms;
- the field book and its mapping, shown by *Import field book* and the mapping dialog;
- the levelling book and its mapping, shown by *Import levelling field book*;
- geoid grids, shown by the integration algorithms;
- the tables export.

The 31 codes left in `io/` are all in `krumm.py` and `adjust.py`. These read the RD-11 and ADJUST
reference corpora for the tests and scripts, and no algorithm reaches them; the baseline says so.

A tier-3 test reads every registered template back through the real translation layer, each given exactly
its own keys (`tests/qgis/test_engine_messages.py`).

**Found.** **The field-mapping dialog showed a traceback for a mapping file it refused.** `FieldMapping`
refuses an unknown field or a missing name with a `ValidationError`, which is not a `ValueError`. The
dialog caught only `OSError`, `ValueError` and `KeyError`, so the refusal escaped the slot and reached the
user as QGIS's Python error window. It now says why the file was refused, in a warning
(`tests/qgis/test_mapping_dialog.py`).

**Not done here.** The 317 codes raised in `core/`, `reports/` and `services/`. They are next, technique by
technique, starting with the levelling and total-station codes a user's observations reach.

#### P12c-7 — every error in words (third pull request): levelling and total station

**Delivered.** Templates, with pt-BR and es, for the 67 codes the levelling and total-station techniques
raise. That leaves **281** in the baseline.

- **Levelling (37).** The readings and setups of a book; lines that break or loops that do not close;
  double-run sections and reciprocal crossings whose runs disagree; benchmarks no line reaches, or that
  carry no height type; and a geoid model named without its grid. They reach the user through the levelling
  algorithms.
- **Total station (30).** Readings and face pairs; atmospheric and geometric reductions; and traverses,
  resections and intersections that cannot be determined or do not converge. They reach the user through
  the total-station algorithms.

They follow the catalogue's existing words for survey terms. In pt-BR these are *referência de nível*,
*circuito*, *travessia recíproca*, *interseção à ré* and *interseção à vante*, with PD/PI for the faces; es
uses its existing equivalents.

**Found.** No defect. This was writing words for codes whose checks already worked.

**Not done here.** 281 codes. In `core/` the largest groups are the top level (49), the models (45), the
instruments (39), GNSS (32) and adjustment (30). The 31 in `io/` are the reference-corpus readers.

#### P12c-7 — every error in words (fourth pull request): GNSS, gravimetry and integration

**Delivered.** Templates, with pt-BR and es, for the 51 codes the three remaining techniques raise, which
completes the techniques. That leaves **230** in the baseline.

- **GNSS (32):** baselines and their antenna-height reductions, GNSS loops, comparisons of processing
  configurations, the reference-station database, and trajectory points.
- **Gravimetry (15):** readings, the drift model, the solid-Earth tide, and the gravity network.
- **Integration (4):** the combination's routing and its stations.

The setting a refusal sends the user to is named as the settings window shows it. For the reference-station
database that is *Global Settings, under GNSS*.

**Found.** No defect.

**Not done here.** 230 codes, none of them a technique's:

| Area | Codes |
|---|---|
| `core/` (top level) | 49 |
| `core/models/` | 45 |
| `core/instruments/` | 39 |
| `core/adjustment/` | 29 |
| `core/geodesy/` | 13 |
| `core/statistics/` | 7 |
| `core/preanalysis/` | 6 |
| `core/visualization/` | 6 |
| `reports/` | 3 |
| `services/` | 2 |

The 31 in `io/` are the reference-corpus readers.

#### P12c-7 — every error in words (fifth pull request): the adjustment and what surrounds it

**Delivered.** Templates, with pt-BR and es, for 61 codes. That leaves **169** in the baseline.

- **Adjustment (29):** directions without a setup, and a GNSS baseline in the wrong frame; drift terms
  without their times; constraints the geocentric frame cannot hold; weighted constraints that are singular
  or incomplete; extent weighting; and variance components that are negative, cannot be estimated,
  cannot be told apart or do not settle.
- **Geodesy (13):** unknown ellipsoids and frames, transformations GeoComp does not hold or that hold at one
  epoch only, and projections outside their domain.
- **Statistics (7) and the drawing of ellipses (6):** probabilities, degrees of freedom, confidence, ellipse
  blocks, and exaggeration factors.
- **Pre-analysis (6):** the design session's stations and observations.

**Found.** No defect. One path was checked and is safe: the pre-analysis dialog calls its session from
canvas slots, with no handler. A planned observation of a type with no assumed precision would raise there.
Every type the dialog offers has one, so no user can reach that error.

**Not done here.** 169 codes. They are in the core's top level (49), the models (45) and the instruments
(39), in `reports/` (3) and `services/` (2), and the 31 reference-corpus codes in `io/`.

#### P12c-7 — every error in words (sixth pull request): instruments, report templates and the settings service

**Delivered.** Templates, with pt-BR and es, for 44 codes. That leaves **125** in the baseline.

- **Gravimeters (11):** a profile without an id, a counter gravimeter without its calibration table (and a
  gravity-reading one with a table), calibration factors, standard deviations, reading units, and
  calibration tables that are too short, do not increase, carry a factor that is not positive or are
  inconsistent.
- **Levels and levelling classes (8):** a profile or class without an id, stadia constants, standard
  deviations, a level without its reading precision, a class's negative limits, and negative line lengths
  and setup counts.
- **Instrument profiles and the stochastic model (20):** no profile that applies, unknown and duplicate
  profiles and classes, a parameter in the wrong unit, negative EDM specifications and standard deviations,
  a cyclic error without its wavelength, set counts, unknown observation kinds, and an observation with no
  standard deviation from anywhere.
- **Report templates (3):** a template name with a path in it, a template that does not exist, and one that
  asks for a section GeoComp does not fill.
- **Settings service (2):** a project setting with no project open, and a setting at a scope it does not
  allow.

A refusal about the stochastic model sends the user to *Global Settings, under Stochastic model*, as the
settings window names that page.

**Found.** No defect.

**Not done here.** 125 codes:

| Area | Codes |
|---|---|
| `core/` (top level) | 49 |
| `core/models/` | 45 |
| `io/` (reference-corpus readers) | 31 |

#### P12c-7 — every error in words (seventh pull request): the data model

**Delivered.** Templates, with pt-BR and es, for 46 codes: the 45 of `core/models/`, plus the refusal to
combine heights of different types, which the models and the geoid module share. That leaves **79** in the
baseline.

- **Stations and their constraints (14):** a station without an id, duplicate stations, observations and
  clusters, and constraints that are free but carry detail, hold nothing, name components the position does
  not have, or are weighted without an uncertainty. Gravity constraints are covered the same way.
- **Observations and clusters (13):** the wrong number of stations or values for the type, a value without
  its uncertainty or in the wrong unit, a correlated type outside a cluster, an active observation carrying a
  rejection record, a setup height not in metres or one the type would silently ignore, a multi-component
  observation read as one value, an unknown baseline frame, and clusters that are empty, list a member twice
  or carry a covariance of the wrong size.
- **Positions and heights (6):** the component count, uncertainty and unit, a position without a CRS, an
  unknown component, and heights of two types without a geoid model.
- **Epochs and solutions (6):** an epoch that is not finite or has no time zone, an operation that needs an
  epoch it was not given, the adjusted gravity's unit, a solution without a CRS, and a station the solution
  does not hold.
- **GNSS sessions and the project document (7):** a session without an id or that ends before it starts, an
  antenna height not in metres, duplicate sessions, networks and campaigns, and a project written by a newer
  GeoComp.

A refusal never lists a solution's stations: a network of 10,000 would put all of them in one message.

**Found.** No defect. `Project.require_schema_version` has no caller. The store refuses a newer schema
itself (`store_schema_too_new`, which already has words), so its template is for a check nothing makes yet.

**Not done here.** 79 codes:

| Area | Codes |
|---|---|
| `core/` (top level) | 48 |
| `io/` (reference-corpus readers) | 31 |

#### P12c-7 — every error in words (eighth pull request): the last 79, and no exemption

**Delivered.** Templates, with pt-BR and es, for the last 79 codes. That leaves **none**. The baseline list
of codes without words is removed, and the structural test now fails on **any** code raised without a
template (specs/18 §2). The register row in specs/20 says so.

- **Uncertainty and covariance matrices (28):** matrices that are not square, not symmetric or not positive
  semi-definite; labels and units that do not match the size; units that cannot be combined; values outside
  a function's domain; and the guards of propagation. Several are internal errors, and their words say so and
  ask for a report.
- **Geoid models and heights (8):** a grid too small or with no-data nodes, no stated accuracy, a point outside
  the coverage, bounds out of order, and a conversion a geoid cannot make.
- **Base maps (9) and the display settings (3):** each sends the user to the settings page that fixes it,
  *Global Settings, under Base maps* or *under Interface*.
- **The reference-corpus readers (31):** the ADJUST files and Krumm's examples. Only the tests and `scripts/`
  read them, but whoever runs them reads the refusal.

No refusal lists a covariance matrix's labels: one over a network's stations would put every station in a
single message.

**Found.**

- **A base-map key could reach the Processing log** (NFR-010). The tile tokens were checked before the
  credential, and that refusal carried the URL. A keyed XYZ URL without `{z}`, `{x}` and `{y}` was refused for
  the tokens, and *Add base map* showed the refusal with `str(error)`, key and all. Now the credential is
  checked first and no refusal carries the URL, because the check is shallow and may miss a key under an
  unfamiliar name (specs/17 §5.6). Tests hold both.
- **Eight places showed `str(error)`**, the developer's diagnostic, instead of the refusal's words. They
  were *Add base map*, the results panel, the time-series panel, the pre-analysis dialog, the
  total-station field mapping and readings, and the levelling field mapping and lines. All now word it.
  Where a handler also catches Python's own errors, it goes through the new `reason_for`, which words a
  refusal and passes anything else through. For the pre-analysis dialog, the session's state now keeps the
  refusal, because the finding it made carries only the diagnostic.

**Not done here.** The core's inspection *findings* are a separate set from errors, and they are not
covered: what *Inspect network*, the field-book import and the pre-analysis dialog report as warnings. Each
carries a code and an English sentence, and the presentation layer shows the sentence untranslated. That
gap is outside NFR-006's error messages and is FR-091's to close. It needs a template per finding code, as
errors have, and is recorded here rather than widened into this pull request. One refusal still reaches the
user as a diagnostic through that gap. The levelling-book import makes a refused setup or line into a
finding whose text is `f"setup {id}: {error}"`, so the code and context reach the import report. It goes
with the findings, as P12c-8.

#### P12c-8 — every finding in words (first pull request): the mechanism, the importers and inspection

FR-091 and specs/18 §2: the core never phrases a sentence. A *finding* broke that rule. It is what an import,
an inspection or a reduction reports rather than raises (FR-166), and it carried only an English sentence. A
report, the Processing log, the field-mapping dialog and the pre-analysis dialog showed that sentence in
every language. The P12c-7 records named this gap.

**Delivered.**

- **The mechanism.**
  - `Finding` gains `context` (the values its sentence needs), `error` (the refusal it reports) and
    `wording` (the frame a per-row, per-setup or per-line refusal is worded by).
  - `services.messages.finding_text` words a finding from `finding.<wording or code>`, falling back to the
    English only for a code still in the baseline.
  - Every display site uses it: the levelling and total-station finding tables and log lines, *Inspect
    network*, *Traverse*, *Intersection*, *Trigonometric levelling*, the total-station network's refusal,
    and both dialogs. A findings CSV keeps the English, because the locale test requires such a file to be
    the same in every language (FR-095).
- **The ratchet.** `tests/structural/test_message_templates.py` reads every `Finding(...)` beside every
  `*Error(...)`.
  - A finding's template must exist, unless its code is in a baseline list that may only shrink, and
    must interpolate only the keys its `context` literal supplies.
  - A construction whose template or keys cannot be read from the source fails.
  - The specs/20 register row says so.
- **Worded, with pt-BR and es: 31 findings and the 12 refusals of a field book's rows.**
  - The field-mapping editor (4).
  - The field book (3) and the levelling book (1).
  - The frames of a refused row, setup or line (4).
  - Network inspection (12), with the referential problems now structured as `Network.integrity_problems()`.
  - The pre-analysis design (6).
  - A pointing rejected in pre-processing (1).
  - The book readers' per-row refusals are now `DataError`s, worded as any refusal is (12).

**Found.**

- **The levelling-book import still showed a refusal's developer diagnostic.** P12c-7 recorded it: a refused
  setup or line became a finding whose text was `f"setup {id}: {error}"`. It now reads "Setup 3: …" followed
  by the refusal's words.
- **The pre-analysis refusal had two mechanisms.** P12c-7 added `SessionState.error` to word a refused
  design. The finding now carries the refusal itself, and that field is gone.

**Not done here.** 42 findings, all the techniques' own, are frozen in the baseline: levelling (25)
and the total station (17). They are the misclosures, balances, collimation and index checks, the
orthometric correction and the resection's geometry. Their sentences hold numbers the core formats in place,
so each needs its values moved into a context.

#### P12c-8 — every finding in words (second pull request): the techniques

**Delivered.** The last 42 findings get context and templates, with pt-BR and es. The baseline is empty and
removed, and the structural test now fails on **any** finding without a template, as on any error (specs/18
§2).

- **Levelling (25).**
  - Closures: out of tolerance; not judged, with three sentences for its three reasons and one code; beyond
    or within their own precision.
  - Lines: length unknown, accumulated imbalance, exactly balanced, very short.
  - Setups and sights: no distances, too long, out of balance, imbalance with no level profile.
  - Reciprocal crossings: variance inflated or not; banks that disagree.
  - The network: side shots, the weighting, a free network, trigonometric differences joined, a benchmark
    converted through the geoid, setups clustered.
  - The orthometric correction, applied or negligible; and the three-wire half-sum.
- **The total station (17).**
  - Face pairs: collimation and vertical index beyond tolerance or drifting, distance discrepancy, single
    face.
  - The near-vertical sight, and the instrument applying the EDM or prism constant itself.
  - Leap-frog imbalance and missing atmospheric data.
  - Traverses: angular misclosure, relative precision, open traverse.
  - Resection and intersection geometry: collinear points, the danger circle, weak geometry.

Every number in a finding's sentence is now in its context, written for the reader with the display
locale's separator (FR-094). Until now the core formatted these numbers with a point inside its English.

A word the core cannot translate is no longer interpolated. A closure's "line", "loop" or "section" and the
type a geoid conversion went to are now said in the sentence. Where they vary, a separate wording carries
them. The structural test's placeholders went from `%6` to `%9`, because the geoid conversion's sentence
needs seven.

**Found.** No defect beyond the English itself. The `three_wire_half_sum` label was English assembled by the
caller (`"{station} in setup {id}"`); `check()` now takes the station and the setup apart.

**Not done here.** Nothing of P12c-8 remains. Two smaller English remnants, recorded rather than widened in:

- the `problems` of `network_integrity` (an error), interpolated into its translated sentence;
- the `expected` text some errors carry from the core.

#### P12c-9 — no English inside a translated sentence

The two English remnants P12c-8 recorded both came from the same pattern. A template is translated, but the
values it interpolates are not. 29 templates interpolated a key that a raise site filled with an English
sentence, so a Portuguese message carried an English clause:

- `expected="a whole number from 0 to 6"`;
- `expected="a line starting or ending at B"`;
- the gravimeter formats GeoComp reads, spelled out in English;
- `network_integrity`'s list of problem sentences.

**Delivered.**

- **The 29 templates say their own sentence**, with pt-BR and es. The raise sites pass the data the sentence
  needs under keys of their own, such as `maximum`, `at`, `start`, `station`, `previous`, `low`, `high`,
  `south`… `east`, `needed`, `missing`, `available` and `format`. Their `expected` stays, for the developer's
  diagnostic and the provenance record, but no template reads it.
- **Codes that cover several situations keep one code**, and their sentence covers every case. Strain names
  all it needs; a gravimeter line names its format, CG-5, Burris or CSV.
- **`network_integrity` says the number of problems**, and *Inspect network* words each one.
- **The rule.** `test_no_template_interpolates_english_from_the_core` fails on a template that interpolates a
  key some raise site, or a finding's context, fills with a phrase of three words or more. Run against the
  templates as they were, it flags four in `project/messages.py` alone. The specs/20 register row says so.

**Found.** No defect beyond the English itself. One template quoted a JSON key (`'stations'`) inside its
sentence. The glossary check caught it, because the key was read as the word it spells, and the template now
says "its list of stations".

**Not done here.** The rule reads values written at the raise site. A value computed elsewhere and passed in
cannot be judged from the source, as `network_integrity`'s list was. Each of those is found by reading, and
none is known to remain.

#### P12c-10 — a session that solved nothing says when it observed

specs/08 §9's failure table requires a session with no solution to be reported with the engine's own message
*and the session's data span*. P12c-7 gave `rtklib_produced_no_solution` the engine's message, but not the span.
The P12c-7 records named the gap.

**Delivered.**

- The refusal carries `spans`, one per session (the rover's, and the base's for a relative mode), as `id
  start/end`. That is an ISO 8601 interval, the same in every language, and an end the session does not state
  is `?`.
- The template shows the spans beside RTKLIB's own word, and *Batch GNSS processing* reports them per failed
  session.
- The refusal is built in `_no_solution`, so a QGIS-free test checks it without `rnx2rtkp`. The tier-4 test
  still forces the case through a live run.

**Found.** No defect. Sessions that share no epoch at all are already refused before the run
(`rtklib_sessions_do_not_overlap`). A run that solves nothing therefore had overlapping sessions, and the spans
show by how little. Products that do not cover the overlap are the next cause to look for, and the sentence
names them.

**Not done here.** The products' own span is not in the refusal. A run receives product file paths, and their
coverage is resolved when they are fetched (P10c), not carried to the engine.

#### P12c-11 — an engine that runs out of time says so

The rest of the specs/07 §7 and specs/08 §9 failure tables, read against the code. Every integration code
they name is raised, but four rows were not what they say.

**Delivered.**

- **Timeouts.** Both adapters now check `EngineRun.timed_out` before the exit code. `rtklib_timed_out` and
  `dynadjust_stage_timed_out` give the elapsed time, the limit and the working directory, and say how to raise
  the limit. Until now both were reported as a failure with exit code -9, which sends a user looking at their
  data when what ran out was the time.
- **A configurable RTKLIB limit (FR-304).** The six algorithms that run `rnx2rtkp` have an advanced *Timeout
  per run (s)*, 600 s by default. Until now the limit was the adapter's fixed ten minutes.
- **The RTKLIB version (FR-302).** The same six warn when the version is outside the tested range, log which
  one they use, and record it under `engine` in their JSON output. DynAdjust's adjustment already warned;
  nothing that runs RTKLIB did.
- **The working directory is kept when a refusal points at it.** *Adjust network (DynAdjust)* ran in a
  `TemporaryDirectory`, which deleted the files as the refusal propagated. It now keeps the directory whenever
  the refusal names it and removes it otherwise. `dynadjust_stage_failed` now carries the command line and the
  working directory, which the "non-zero exit with no message" row requires.

**Found.**

- *Keep the engine's working directory*, on the four GNSS modes, was read by nothing. Unchecking it changed
  nothing. It now removes the directory after a successful run, and the run says where a kept one is.
- A GNSS run with no solution file to save put its working directory in QGIS's own current directory. It now
  uses a temporary one.

**Not done here.** specs/08's "solution quality below a configured threshold — flagged" has no threshold to
apply. The one configured threshold is the ambiguity ratio, which RTKLIB applies per epoch. A threshold that
flags a whole session (a fixed fraction, or a precision) is the maintainer's decision, as specs/11 §8
criterion 2 records for the GNSS acceptance threshold. specs/08 §9 records the gap rather than inventing a
default.

#### P12c-12 — every parameter an algorithm declares is read

P12c-11 found *Keep the engine's working directory* on the GNSS modes. It had been offered since P7 and was
read by nothing. That is the defect the pre-P7 review found in 36 settings, one level down, and the settings
have had a structural check since P12a. The parameters had none.

**Delivered.** `tests/structural/test_parameters_are_read.py`, which reads the sources without QGIS:

- every parameter an `initAlgorithm` declares is read by the run;
- every output it adds is returned;
- every parameter name is upper snake case.

The test checks itself in two ways. It must find more than 150 declared parameters, and a planted module
with a key that is declared, logged and never read must fail it. Run against `main` before P12c-11, it fails
on `gnss.process` alone.

**Found.** No other unread parameter, and no unreturned output: KEEP_WORK_DIR was the only one. specs/16 §4
said parameter names are `snake_case`. None of the 162 is: every one is upper snake case, like QGIS's own. The
spec was corrected to the code rather than the reverse, because a renamed key breaks every saved model that
names it.

**Not done here.** The check proves a run asks for a parameter's value, not that it uses the value correctly.
A parameter whose constant does not follow `NAME = "NAME"` would escape it. None does today, and the name rule
would not catch one that broke the pattern by its value.

#### P12c-13 — every requirement held to a test (first pull request): the platform

The acceptance register holds every criterion to a test, but not every requirement. FR-302 and FR-304 were
broken with every criterion green, because neither had a criterion of its own. specs/20 §11 now gives each
requirement of specs/02 a row, by the acceptance register's rules, and
`tests/structural/test_requirement_register.py` holds it to the document. It is written block by block; the
test's list of blocks not yet audited may only shrink.

**Delivered.** The register, and the platform block, FR-001 to FR-095: 29 met and 5 partly met, of 34.

**Found and fixed.**

- **The usage mode did nothing (FR-070).** Every advanced parameter was flagged advanced in both modes, and QGIS
  draws a flagged parameter, collapsed, whatever GeoComp's mode says. `is_advanced_mode()` read the setting,
  so the settings check passed, and nothing called it. Basic now hides the advanced parameters and Advanced
  shows them, and a change of mode refreshes the provider. The parameter set and every default stay identical
  in both modes (FR-071).
- **The toolbar (FR-007, specs/15 §1.3)** held Global Settings alone. It now has *Inspect network*, *Adjust
  network*, *Save to project store*, *Run again* and the results panel.
- **An engine's run was not in its output (FR-036).** DynAdjust's provenance kept the command lines and one exit
  code; it now keeps each stage's run, with the ends of stdout and stderr. The GNSS algorithms kept none of it;
  their JSON now carries the run.
- **Published algorithm ids were not pinned (FR-032).** Every one is now listed, and one leaving the list fails.
- **The log tab and its verbosity (FR-009)** had no test; `tests/qgis/test_log.py`.

**Not done here — the five partly met.**

- FR-061 and FR-069: instrument constants live in profile documents, and no window adds, edits, duplicates or
  deletes a profile.
- FR-064: Global Settings give a default sigma for three of the twenty observation types.
- FR-066: working directories and report templates are algorithm parameters, by P12c-6's decision.
- FR-070: a user-supplied engine configuration in Advanced mode is FR-325's, audited with the engines block.

The other nine blocks are still to be audited.

#### P12c-13 — every requirement held to a test (second pull request): data, persistence, interoperability

FR-100 to FR-167: 20 met and 2 partly met, of 22.

**Found and fixed.**

- **`.xlsx` was never read (FR-160).** The requirement names CSV and `.xlsx`, and every import read CSV alone.
  `io/tabular.py` now reads a workbook's first sheet with the standard library, beside the writer that has
  been there since P5. Both book imports and the mapping dialog's preview go through it.
- **Stations could not come from a table (FR-160).** *Total station network* took approximate coordinates only
  as a JSON document. It now also reads a CSV or `.xlsx` table, a station and three coordinates a row.
- **The processing-log table was empty (FR-131).** `gc_run` was declared in P5 and written by nothing. It now
  gets one row per engine run a stored solution's provenance carries.
- **specs/17 §5.1 contradicted specs/03.** It still said `.xlsx` export needs `openpyxl` and falls back to CSV;
  P5 had built the writer in.

**Not done here — the two partly met.**

- FR-102: an observation has no `provenance`. specs/04 §2.5 lists it, but the model and the store have none,
  and adding it needs a schema migration.
- FR-165: the deflection of the vertical is not estimated, as specs/17 §5.5 has recorded since P5.

Eight blocks remain.

#### P12c-13 — every requirement held to a test (third pull request): uncertainty and adjustment

FR-200 to FR-273: all 27 met, most through the acceptance rows of specs/05, 06, 14 and 19.

**Found and fixed.**

- **A rejection was silent in the report (FR-255).** An observation set aside in the network document left
  the adjustment, and the report counted the active observations and said nothing of it. The report now
  lists each one, with its status, reason, test and statistic, and says how it comes back.
- **α and β were configurable and never exercised (FR-252).** Every test used the defaults. A test now
  shows that a stricter α or a higher power enlarges every MDB by the same factor.
- **specs/06 §4.2** said automatic rejection is offered in Advanced mode. It is offered in neither, and the
  section now says so.

**Not done here.** The reductions to the ellipsoid and to the projection plane propagate their uncertainty,
and FR-205 holds, but no algorithm calls them. Whether a user can apply them is FR-405's question, in the
total-station block. Seven blocks remain.

#### P12c-13 — every requirement held to a test (fourth pull request): the engines

FR-300 to FR-359: 19 met and 4 partly met, of 23.

**Found and fixed.**

- **A DynAdjust result never reached the map (FR-324).** *Adjust network (DynAdjust)* wrote its solution
  document and offered no layer, though the in-house adjustment did. It now offers the same result layers.
  Writing the test found the second half: the display grid refused any frame outside GeoComp's transformation
  table, so a DynAdjust solution in GDA2020 could not be drawn even through a path that tried. Drawing
  transforms nothing, and the grid now names any frame the solution states.

**Not done here — the four partly met.**

- FR-301: RTKLIB is located, not acquired (21 4, the maintainer's decision).
- FR-320: DynAdjust's input is a network document, not a QGIS layer or the project store directly.
- FR-325: no algorithm stops before execution for the generated input to be edited, and none takes a
  user-supplied DynAdjust configuration.
- FR-359: the configuration comparison is one table, not the side-by-side dialog specs/11 §6 describes.

Six blocks remain.

#### P12c-13 — every requirement held to a test (fifth pull request): total station and level

FR-400 to FR-505: 18 met and 1 partly met, of 19. The computations are tested against constructed truth;
the three rows that wait on published examples (09 5, 10 1, 10 4) are the acceptance register's, and are not
counted again here.

**Found, not fixed: the grid reduction (FR-405).** The reductions to the ellipsoid and to the projection
plane propagate their uncertainty, but no algorithm applies them. *Classical network* adjusts measured
distances in the plane of the approximate coordinates with no scale factor, so a network on a projected CRS
takes ground distances as grid distances: 400 to 1000 ppm on UTM, plus the height term. That is design work, not an audit fix, and
specs/09 §2 now records it. It is the most consequential gap the audit has found so far.

Four blocks remain.

#### P12c-13 — every requirement held to a test (sixth pull request): GNSS, gravimetry, integration and multi-epoch

FR-600 to FR-838: 23 met and 1 partly met, of 24. Most rows borrow the acceptance register's evidence
(specs/08, 12, 13 and 14 have a criterion for nearly every requirement); the rest cite the test directly.
Nothing was found broken.

**Not done here — the one partly met.**

- FR-603: dilution of precision is never reported. `rnx2rtkp` does not write it, and the quality summary
  leaves the field empty rather than put another quantity in it; specs/08 §7.3 now says so. Computing it
  from the satellite geometry needs the navigation data the engine already reads, and is not an audit fix.

Two blocks remain: visualisation, reporting and community (FR-900 to FR-955) and the non-functional
ones (NFR-001 to NFR-012).

#### P12c-13 — every requirement held to a test (seventh pull request): visualisation, reporting and community

FR-900 to FR-955: 10 met, 4 partly met and 1 open, of 15.

**Found and fixed: a test of styling that could not fail (FR-900, FR-905).** The check that the adjustment's
result layers "are not left with the default renderer" asserted that each had a renderer, and every vector
layer has one, so an unstyled layer passed it. Nothing ran the displacement and velocity layers'
post-processor at all, so a style that never reached them would have passed too. Each produced layer is now
post-processed as Processing does it and its renderer compared with the one its shipped QML gives: the six
adjustment layers, the displacements, their ellipses and the velocities. The code was right; the tests are now
able to show it.

**Not done here.**

- FR-950: three reference datasets have no test (row 20 3), and only RD-01 ships with the plugin.
- FR-951: the comparison protocol is written in §5 of specs/20 and its export exists, but it is a specification
  section, not documentation, and has never been run (W-12).
- FR-952: one tutorial, for one module, in English.
- FR-954, open: no contribution guide. How companies and public bodies take part is the maintainer's decision.
- FR-955: the files an upstream report needs are kept, but nothing packages them into one.

All four partly met and the open one are P13's deliverables, as its plan already states. One block remains: the
non-functional requirements (NFR-001 to NFR-012).

#### P12c-13 — every requirement held to a test (eighth pull request): the non-functional requirements

NFR-001 to NFR-012: 9 met and 3 partly met, of 12. **Every requirement now has a row**: 155 met, 20 partly
met and 1 open, of 176. The list of blocks still to audit is gone, and the register test now asks for a row
for every requirement in specs/02.

**Found and fixed.**

- **The field-mapping dialog stalled on a large workbook (NFR-004).** Its preview read the whole `.xlsx` on
  the GUI thread to show twelve rows: 0.1 s at 1,000 rows, 0.4 s at 5,000, 2 s at 20,000. The defect came in
  with P12c-13's own `.xlsx` reader. The sheet is now streamed, and the reader stops after the rows asked for;
  the string table is read only as far as those rows reach. A preview takes 3 to 5 ms at any size.
- **Two runtime dependencies had no recorded decision (NFR-005).** `psycopg2` was justified only in specs/17,
  and QGIS's `processing` nowhere. Both are now in specs/03 §3.7. `tests/structural/test_dependencies.py`
  holds every package the plugin imports to that table.
- **Nothing measured whether a module outside `core/` was tested at all (NFR-011).** CI's coverage run now
  measures the whole plugin, and `scripts/check_coverage.py` fails if a module defines functions and the suite
  runs none of them. Locally the only modules it names are the two PostGIS ones, which need the server the QGIS
  job provides. `classFactory` is exempt, with its reason: it runs in a QGIS of its own.
- **Nothing held public interfaces to being documented and annotated (NFR-012).** Of the 1,347 classes,
  functions and methods one module imports from another, 399 have no docstring and 51 are not fully annotated.
  `tests/structural/test_public_interfaces.py` freezes both lists and lets them only shrink, as P12c-7 did for
  unworded error codes.

**Not done here — the three partly met.**

- NFR-004: the results panel and the time-series panel read their documents on the GUI thread. A 625-station
  solution with full covariance (37 MB) takes 0.85 s, so those reads need to move into a task. Nothing
  measures the 200 ms bound.
- NFR-006: every error has words and none reaches the user as a traceback, but nothing checks that each
  message says what the user can do.
- NFR-012: the 399 and the 51 above.

#### P12c-14 — measured distances reduced to the grid (FR-405)

P12c-13's register left the audit with work in this repository behind twenty rows. FR-405 was the most
consequential: *Classical network* adjusted ground distances as grid distances. On UTM that is a scale error
from −400 ppm at the central meridian to about +1000 ppm at a zone's edge, plus 157 ppm for each kilometre
of height. Against grid control it surfaces in the residuals and the variance factor, and nothing says why.

**Delivered.**

| | |
|---|---|
| The reduction, as a network operation | `core/techniques/total_station/grid.py`: horizontal distances to the ellipsoid at the mean of their ends' *H + N*, then to the grid by Simpson's mean of *k* over the line; ellipsoid distances scaled only. The height's uncertainty is carried, the measured value and the factors recorded on each observation, and a second reduction reduces nothing |
| *Classical network* applies it | In a 2D adjustment on a projected, conformal CRS, with *k* from QGIS. *Reduce measured distances to the grid* is on by default, and *Geoid undulation N (m)* is an advanced parameter. Coordinates outside the CRS's area of use are read as a local plane and left alone, which keeps RD-01 and the tutorial as they were. The summary, the report and the provenance all say whether the reduction was applied, the range in ppm if it was, and why not if it was not |
| Evidence | A network observed on the ground 300 km from a UTM central meridian, held to two grid control points: as measured, a variance factor above 1000; reduced, its truth to 0.1 mm (`tests/test_grid_reduction.py`). QGIS's *k* agrees with GeoComp's Krüger series to 0.01 ppm, and RD-01 moved into the zone adjusts to the same triangle scaled by exactly *k* (`tests/qgis/test_grid_reduction.py`) |

**Not done.** A 3D adjustment's slope distances are not reduced: its frame treats E, N, U as Cartesian, and a
grid is not, which is a larger question than a scale factor. *Adjust network* takes a document's distances as
given. *N* is one value for the network, not read from a geoid model per station. GeoComp's own point scale
factor differentiates numerically and is good to 0.005 ppm; QGIS's is used.

#### P12c-15 — nothing slow on the GUI thread (NFR-004)

P12c-13 measured it: opening a 625-station solution in the results panel held QGIS for 1.3 s, a second of it
reading the 37 MB document and a quarter of a second filling the observation table.

**Delivered.**

| | |
|---|---|
| Reads in tasks | A solution, a project store or a series document is read off the GUI thread when the panel's buttons open it or a layer that arrives names it. This uses `task_service.run_in_background`, the task service's first caller since it was written before P7, and the result is listed when the read is done. The synchronous `add_solution_file`, `open_store` and `load` stay for scripts and tests |
| Tables that hold their rows | The observation and station tables are one row-backed model, so filling is a reset, filtering and sorting are list operations, and Qt asks only for the cells it draws. 625 stations now cost 19 ms on the GUI thread, 2,500 cost 46 ms, and a 5,000-row table fills, filters and sorts within 200 ms, held by a test |
| Found on the way | The station table sorted its numbers as text, so 10.5 came before 9.2. Each column now sorts by its value, with a missing one last in both directions |

**Not done.** The pre-analysis dialog still evaluates the design on the GUI thread at each click: 177 ms at
225 stations, which a design drawn by hand does not reach.

#### P12c-16 — instrument profiles in a window (FR-069, FR-061)

Until P12c-16 a total station, reflector, level, levelling class or gravimeter profile was edited as a JSON
document. The library could add a profile and refuse a duplicate id, and no window did either.

**Delivered** ([`15`](./15-ui-menu-and-settings.md) §2.2, *As built*).

| | |
|---|---|
| The window | `gui/profiles_dialog.py`. It has one tab per kind and opens, saves and saves-as the same library file an algorithm's *Instrument profiles* input reads. It adds, edits, duplicates, deletes, imports and exports profiles, and chooses the default. Import adds only new ids and keeps this library's profile where an id is taken. Unsaved changes are asked about before they are discarded. The Total Station, Level and Gravimeter pages of Global Settings each open it on their own tab |
| Units a surveyor reads | Angles are shown in the interface's small-angle unit (″, cc or µrad), constants in mm, EDM proportional terms in ppm, a level's σ in mm/√km and a gravimeter's in µGal. The file keeps radians, metres and ratios. `core/instruments/editing.py` holds the fields, the conversions and the operations, tested without QGIS |
| Refusals in the profile's words | An edit is read back through the profile's own `from_dict`, so a negative σ is refused with the message a file would get, and the library is left as it was |

**Not done.** No setting names the library a run reads, so FR-061 stays partly met. Each run is still given
the file. Making a library every run's default needs a rule for a library that lacks the technique's kind,
and that rule is the next step. The window does not edit a gravimeter's counter-to-milligal table: the table
is kept as imported.

#### P12c-17 — the library a run reads (FR-061)

After P12c-16, profiles were edited in a window reached from Global Settings, but Global Settings did not
remember which library to use. Every run had to be given the file again.

**Delivered** ([`15`](./15-ui-menu-and-settings.md) §2.2, *As built (P12c-17)*).

| | |
|---|---|
| A library per technique | `total_station.profile_library`, `level.profile_library` and `gravimeter.profile_library` are each the default of their technique's *Instrument profiles* inputs, six in all. A run that names its own library still reads that one. Empty leaves every run as it was. There is one setting per technique, not one for all, so a library holding only total stations never becomes what a levelling run reads |
| The window opens it | The page's *Instrument profiles…* opens the library the page names. A file named but not yet written is started there. A library saved while the page names none is entered on the page, for OK to keep |
| Found on the way | In P12c-16, before it merged: the window's *Add* did not make the first profile of a kind its default, as the library's own `add_instrument` does. So a library built in the window failed every run that named no instrument. The first test of a run reading such a library found it |

FR-061 is now **met**: 159 met, 16 partly met, 1 open, of 176.

#### P12c-18 — a 3D network's sights keep their heights

Found while tracing, for FR-102, where a total-station observation comes from. The reductions document
dropped each pointing's instrument and target heights, so *Classical network* in 3D adjusted every zenith
angle and slope distance from mark to mark. On RD-01 that put the heights out by up to 12 mm and multiplied
the variance factor by seventeen. 2D and 1D networks were unaffected, because pre-processing applies the
heights to what they take.

**Delivered** ([`09`](./09-module-total-station.md) §2.5, *Found in P12c-18*). The document is now version 2
and carries both heights. A 3D network refuses a version 1 document and says to pre-process again. The
3D heights on RD-01 now agree with the levelled network's to 0.4 mm, and the test requires 1 mm.

**Not done.** Documents written before P12c-18 are not upgraded. They are refused for 3D, and pre-processing
again is all that a 3D network needs.

#### P12c-19 — where an observation came from (FR-102, first part)

P12c-13's audit found that an observation recorded none of its origin, except a levelling reading's row in
`meta`. Specs/04 §2.5 listed a `provenance` field that did not exist.

**Delivered** ([`04`](./04-data-model.md) §2.5, *As built (P12c-19)*).

| | |
|---|---|
| The record | `ObservationSource`: the reader or reduction that made the observation, the file, and the records in it. It is carried in network documents and in `gc_observation.provenance`, schema 6, with its migration on both backends. It is `None`, never invented, for anything written before |
| The file readers | DNA, DynaML, Krumm and Adjust record the line or record of each observation, assigned in one pass after reading. The test checks every one against the file: the line it names holds the observation's first station |
| The total station, through the files | Each field-book row reaches the observation: reading, pointing, readings document, reductions document, network. A face pair names both of its rows. Checked in memory against RD-01's rows and in QGIS through the three algorithms |
| GNSS, design, benchmarks | A baseline names the engine's solution file and its two sessions. A pre-analysis observation is `design`. A benchmark height the combination makes from a constraint is `integration` |

**Not done.** Levelling and gravimetry observations carry no provenance yet. Their documents do not carry
their source, so FR-102 stays partly met until P12c-20.

#### P12c-20 — levelling and gravimetry provenance; the files against memory (FR-102)

**Delivered** ([`04`](./04-data-model.md) §2.5; [`20`](./20-testing-and-validation.md) §1).

| | |
|---|---|
| Levelling | A reading's row reaches the setup reduction, and a line names its rows as runs. The setups, reductions and trigonometric height-difference documents carry the book's name, and each line or difference its rows |
| Gravimetry | A difference names the file and the lines of every reading in its two visits |
| The files against memory | For the total station in 2D, 3D and 1D, for levelling and for gravimetry, the network built through the algorithms' documents equals the one built in memory from the same field file, observation by observation and cluster by cluster. All are equal, and P12c-18's lost heights were the only loss. The rule, and the table of tests a new document joins, are in specs/20 §1 |

FR-102 is now **met**: 160 met, 15 partly met, 1 open, of 176.

**Not done.** The gravity network algorithm writes no network document, so a gravity observation's provenance
is in the network the adjustment builds and not in a file a user can open. The integration algorithms copy
observations with their provenance, and the combined network's own benchmark heights name the benchmark.

#### P12c-21 — hand-written engine configuration; stop, edit and run DynAdjust later (FR-070, FR-325)

**Delivered** ([`07`](./07-engine-dynadjust.md) §3; [`08`](./08-engine-rtklib.md) §2.4).

| | |
|---|---|
| Stop after writing the input | *Adjust network (DynAdjust)* writes the input, the plan and a manifest to its working-files folder and stops. It runs nothing, so it needs no DynAdjust |
| Run it later | *Run a prepared DynAdjust job*, a new algorithm, runs the folder as it now is and reads the result into the same Solution. Files changed since GeoComp wrote them are found by digest, warned about and recorded in the provenance |
| DynAdjust configuration | A JSON file of options per program, passed to each stage after GeoComp's own. A program GeoComp does not run, and any option GeoComp sets itself, are refused |
| RTKLIB configuration | The four processing modes and *Batch processing* take an `rnx2rtkp` options file. Options GeoComp models set their fields, so a precise ephemeris in the file fetches precise products; any other is written after GeoComp's. The mode, the base position and every `out-` option are refused. The summary and the batch report record the file and its options |

FR-070 is now **met**.

**Defects found.**

- **A refused run told the user about the network before the engine** — introduced while building this, and
  caught by `tests/qgis/test_engine_install.py` before it left the branch: building the job first meant a
  machine without DynAdjust heard about a missing frame before being told to install it. A run that will use
  DynAdjust looks for it first again; only a stopped one does not.
- **The test of an edited file edited nothing.** It replaced `<Ignore/>`, which GeoComp writes as `<Ignore />`,
  and passed only because it also appended a newline. It now scales a variance and checks the edit happened.
- **DynAdjust ignores what GeoComp set aside only some of the time** — older than this phase, found by running
  a hand-ignored measurement through the real engine. A set-aside member of a GNSS cluster or a direction set is
  written as active, and DynAdjust uses it: with a baseline set aside the sample still solved with 3 degrees of
  freedom. A set-aside lone observation is left out of the file while the reader expects its rows, so the
  result refuses to read back. FR-255 goes back to **partly met** until P12c-22 fixes it.

FR-325 stays **partly met**: a measurement added, removed or ignored by hand in a prepared job is refused when
the result is read back, for the same reason as the defect above. 160 met, 15 partly met, 1 open, of 176.

**Not done.** An individual DynAdjust stage cannot be switched on or off: each runs when its condition holds,
and a configuration can give it options but not override that. *Compare configurations* takes no RTKLIB
options file.

#### P12c-22 — what was set aside stays aside, on both engines; Ignore by hand (FR-255, FR-325)

**Delivered** ([`04`](./04-data-model.md) §2.6; [`06`](./06-adjustment-core.md) §4.2; [`07`](./07-engine-dynadjust.md) §3).

| | |
|---|---|
| One rule for clusters | `Network.active_clusters()`: a cluster cut to its active members, under their part of its covariance. The core, the DynaML writer and the reader of DynAdjust's output all use it |
| The core | Adjusts a cluster with a member set aside, as a survey that never had it. It refused before |
| DynAdjust | GeoComp writes only active observations, and the reader expects exactly the rows written. Against DynAdjust 1.4.0 the two engines agree on the combined survey with a baseline, a direction and a distance set aside |
| Ignore by hand | In a prepared job, `Ignore` on a measurement or on one direction of a set is read back set aside, with a record by the user, and gives the adjustment GeoComp makes when it sets the same observations aside. Adding or removing a measurement is refused before anything runs |

FR-255 and FR-325 are now **met**: 162 met, 13 partly met, 1 open, of 176.

**Defects found.**

- **The fix's first draft duplicated half of `dynaml.py`**: a slice that removed the wrong span. The diff
  showed two `_write_cluster` definitions before any test ran, and the file was restored and edited again.
- **The core refused what P12c-21 found DynAdjust adjusting.** Setting aside one baseline of a correlated
  cluster raised `data.cluster_rows_mismatch` in the core, a message about matrix shapes that did not say
  an observation had been set aside. The two engines now agree instead of failing in two different ways.

**Found, not fixed.** An in-house adjustment with no redundancy (0 degrees of freedom) has an undefined
a-posteriori variance factor; it is `NaN`, and the station covariances built from it make `to_solution` fail
with numpy's `Eigenvalues did not converge` instead of a refusal in words. Setting aside one observation from
the three-dof GNSS sample is enough to reach it. Which variance factor a zero-redundancy solution should carry
is a decision for `specs/06`, not a fix to make in passing.

**Not done.** Directions never reach a DynAdjust solution's observation results (§5.6), so a set-aside
direction is visible only in the degrees of freedom and the provenance.

#### P12c-23 — a network with no redundancy adjusts, and says nothing was checked

**Delivered** ([`06`](./06-adjustment-core.md) §4.1).

P12c-22 found that setting aside one observation of the three-dof GNSS sample made the in-house adjustment
fail inside numpy. The cause was any network with as many observations as unknowns, and an **open levelling
line** is one: a benchmark and three marks, levelled one after another and never closed. The a-posteriori
variance factor is 0/0. It was used to scale every covariance anyway, every covariance came out NaN, and
building the solution failed with `Eigenvalues did not converge`. Every adjusting algorithm reached it.

| | |
|---|---|
| The covariances | Scaled by the a priori factor when there is no redundancy (`AdjustmentRun.variance_factor`). On the open line the heights carry 2, 2.8 and 3.5 mm: 2 mm per line, propagated |
| The solution | Carries no a-posteriori factor rather than NaN, and a test not made has no statistic; both write as JSON a strict reader accepts |
| The global test | `TestResult.tested = False`, reported as **not tested** with the reason. The analysis, levelling, total-station, gravimetry and integration adjustments, the shared report, the results panel and the CSV and spreadsheet exports all say so; `GLOBAL_TEST_PASSED` is empty |

**Defects found.**

- **An adjustment that checked nothing was reported as having passed.** The global test already returned
  "nothing to test" for no redundancy, as `passed=True` with a note. Every report read `passed`, and the
  note was English text that only one report printed. Unseen until now, because the crash came first.
- **The core's English note sat under a translated verdict** in the total-station report. Where the test was
  not made, the report now prints the translated reason instead.

**Not done.** The levelling and total-station adjustments are exercised at zero redundancy only through the
shared code; `tests/qgis/test_zero_redundancy.py` drives *Adjust network* end to end.

#### P12c-24 — DynAdjust input straight from the project store (FR-320)

**Delivered** ([`07`](./07-engine-dynadjust.md) §4).

*Adjust network (DynAdjust)* takes its network from a project store, a GeoPackage or a PostgreSQL schema
through a saved QGIS connection, as an alternative to a network document. An empty network id takes the
store's only network. A store with several, an id it does not hold, and a store with no network are each
refused, naming what the store holds. Exactly one source is given. The store is read as it is, never created
or migrated, and a test checks the file is byte-for-byte unchanged. Tested on a GeoPackage, and on PostGIS
through the saved-connection fixture the P11 tests use.

FR-320 stays **partly met**, narrower: a QGIS layer of the user's own design is not read, because no field
mapping exists.

**Not done.** The other adjusting algorithms still take documents only; the store route is FR-320's, which
names DynAdjust.

#### P12c-27 — `rnx2rtkp` ships with the plugin (ADR-0009)

On the maintainer's instruction that the plugin is meant to be self-contained, ADR-0003's "do not bundle" is
amended for RTKLIB's `rnx2rtkp` alone ([`adr/0009`](./adr/0009-bundle-rnx2rtkp.md)); DynAdjust stays a
download. The `build` workflow builds it from the pinned commit on Ubuntu 22.04, links `libc` and `libm` only,
checks the committed `.pos` fixtures against that binary, and `scripts/build.py --engine` stores it executable
under `resources/engines/linux-x86_64/rtklib/` with RTKLIB's BSD 2-clause notice, without which the build
fails. The plugin searches a configured path, the managed installation, the bundled copy, then `PATH`; restores
the executable bit a ZIP library drops; and reports the source as `bundled`. The `install` job unpacks the
archive as QGIS does, with nothing on `PATH`, and runs the bundled program.

It also ships a second tutorial dataset, `rtklib-sample` (RTKLIB's own base-and-rover pair, BSD 2-clause notice
beside it), so a GNSS run can be shown from *Install tutorial dataset* to the map; the build now ships dataset
folders whole, because RINEX is `.05o`. A real run of it through the bundled program gave 120 epochs, 117
fixed, and the README states exactly that. A static landing page is in `docs/`, with the logo.

**Decisions taken while building it.** Dynamic against glibc rather than static, to avoid LGPL relinking
obligations; `libgfortran` left out because only the IERS tide model, off in this build, uses it.

**Found while running it.** The result-layer step of the GNSS run could not be exercised on the QGIS in this
container, which is older than the plugin's declared minimum of 4.0 (`QgsField` with a `QMetaType`); the
engine, the solution file and the summary were. The layer is covered by the QGIS tier in CI.

**Not done.** Windows and macOS builds (a runner each, fixtures run against the result, and a Gatekeeper
decision for macOS); the one-button DynAdjust install with a licence acknowledgement the maintainer asked for.

#### P12c-28 — publishing a release attaches the plugin ZIP

The landing page sends a visitor to the Releases page for `geocomp.zip`, and nothing put it there. The `build`
workflow's `attach` job, on a published release only and with the write-scoped token in that job alone,
attaches the archive the same run built and checked, with its SHA-256 (`specs/21` §5). **Not verified** until
a release is published.

#### P12c-29 — a licence acknowledgement on installing DynAdjust

On the maintainer's instruction that DynAdjust, which cannot be bundled, be a single button press with a tick
box saying the person understands the licensing. *Install an engine* already was one run; it now has a
required, unticked-by-default box, and an install without it is refused before any download, naming the box,
the program's owner and its licence. The log records the confirmation. The help and the refusal point to
DynAdjust's own repository for the licence text. Tested against the local release server the install tests
already use: refused with nothing downloaded or written, accepted with the confirmation logged before the
download starts. pt_BR and es are complete.

**Not done.** The acknowledgement is **not recorded in `installed.json`**, only in the run's log, so a later
reader of the installation cannot tell it was given. A script or model that installed DynAdjust unattended must
now pass the input. DynAdjust's licence text is **not** placed beside the installed program (the manager extracts only the
programs). `THIRD_PARTY.md` said it was; that was wrong and is corrected, not worked around.

#### P12c-30 — `docs/` published to GitHub Pages

The landing page was merged and Pages switched on with the "GitHub Actions" source, which with no workflow is
a 404. `.github/workflows/pages.yml` publishes `docs/` on a push to `main` that touches it, and on demand; its
first run, on the merge, succeeded.

#### P12c-31 — public interfaces documented: the models, the adjustment, the instruments, the techniques (NFR-012)

185 of the 399 undocumented interfaces in `tests/structural/test_public_interfaces.py`'s frozen list now
have docstrings: every one in `core.models` (69), `core.adjustment` (32), `core.instruments` (34) and
`core.techniques` (50). Of 1,409 interfaces one module imports from another, 214 remain undocumented and 51
not fully annotated. Each docstring says what is specific to the function: what a document omits, what a
reader refuses, what a default reads as.

**Defects found.** None in the code. Writing them turned up two wrong drafts, corrected before commit: a
zenith precision's distance term is refraction, not centring; and a constraint's components are named in
the constraining position's own system, not as ``east``/``north``/``up``.

**Not done.** 214 docstrings and 51 annotations: the engines, the store, the GUI, the provider and the
smaller core packages. NFR-012 stays **partly met**.

#### P12c-32 — every public interface documented (NFR-012)

The other 214: `core.monitoring`, the store, the engines, the remaining core packages, `io`, the
algorithms, the GUI, the plugin and the provider. The frozen docstring list is empty, so
`tests/structural/test_public_interfaces.py` drops it and states the rule plainly: every interface one
module imports from another has a docstring. The QGIS overrides (`displayName`, `initAlgorithm`, `tr` and
the like) say what Processing asks of them, in a line; the rest say what is particular to them, such as
what a reader returns for an absent path, what a fetcher counts as missing rather than failed, and what a
stored form leaves out.

**Defects found.** None in the code. Checking each draft against the source completed three that had
left out what a caller needs: a level mapping's `parse_number` converts to SI as well as parsing; a unit's
symbol is empty for a dimensionless quantity; `MessageTemplate.render` shows a missing value as "(not
set)".

**Not done.** The 51 interfaces not fully annotated. NFR-012 stays **partly met**.

#### P12c-33 — every public interface annotated; NFR-012 met

The last 51 interfaces between modules that did not annotate every parameter and their return now do, and the
frozen list is gone: `tests/structural/test_public_interfaces.py` requires a docstring and full annotation of
every one. **NFR-012 is met**: 163 met, 12 partly met, 1 open, of 176.

Most of the 51 were arguments that are QGIS objects (a feedback, a context, a canvas, a layer) or the core's own
types passed across a boundary that would otherwise make an import cycle. The latter are imported for type
checking only, except in `core/techniques`, where `tests/structural/test_no_bare_geodetic_floats.py` evaluates
the hints at run time, so `adjust_combination`'s gravity network and `add_height_differences`'s differences are
real imports, checked to load fresh without a cycle.

**Found while doing it.** Two builders in `layers/builders.py` said they were "typed loosely" so that `layers`
would not import the GNSS technique package; a type-checking-only import keeps that true, and the docstrings now
say so. `read_document` was first annotated as taking a dictionary reader; the readers it is given take any
payload and check it themselves, and the annotation says that.

**Not done.** Nothing checks the annotations are *right* -- no type checker runs in CI. They are read against the
callers here, not verified by a tool.

#### P12c-34 — `rnx2rtkp` for Windows and macOS; FR-301 met

P12c-27 shipped `rnx2rtkp` for Linux only. The `build` workflow's `rtklib` job is now a matrix over three
runners: Linux as before; Windows with MinGW-w64, linked statically and failed if it needs a MinGW runtime DLL;
and macOS as one universal program, failed if it links beyond `libSystem`. Each checks the committed `.pos`
fixtures against its own binary -- the macOS one's Intel half under Rosetta, through a wrapper -- and runs it as
the plugin will, planted unexecutable under its platform name and found as the bundled copy
(`tests/test_bundled_engine.py::TestARealBuildOnThisSystem`, which skips unless a workflow names a binary). The
package carries all four platform folders, the macOS program twice. **FR-301 and acceptance row 21.4 are met**:
164 met, 11 partly met, 1 open, of 176; 124 of 136.

`scripts/check_rtklib_fixtures.py` shelled out to `gunzip` and normalised only `/` paths; it now uses Python's
`gzip` and accepts a Windows path, so the same check runs on all three.

**Found by the first CI run.** RTKLIB selects its Windows code with `WIN32`, which MinGW does not define, so the
Windows build failed asking for `sys/select.h`; it is now built with `-DWIN32`, and imports only `KERNEL32` and
`msvcrt` -- the check is now an allow-list of those two. The macOS linkage check read the second architecture's
header line of `otool -L` as a library and failed a program that links only `libSystem`. The Windows program,
cross-compiled and run under Wine to reproduce both locally, matches the fixtures in every column but one: at two
epochs its ambiguity ratio prints 629.3 and 654.6 where Linux prints 629.4 and 654.7. Both C libraries print the
same float the same way, so the difference is arithmetic at the float's last bits, turned into a whole unit by a
rounding boundary, and a relative tolerance of a part in a million cannot absorb that. The fixture check now also
accepts one unit in the last printed decimal place; integers -- week, status, satellite count -- stay exact
(`tests/test_rtklib_engine.py::TestTheFixtureDriftGuard`). The sample RINEX, in the tests and in the plugin's
own copy, is now kept byte for byte (`-text`) so a Windows checkout does not hand the engine CRLF input; marking
only the tests' copy failed the test that requires the two copies to be the same bytes, on Windows alone.

**Not done.** Gatekeeper on a user's Mac is expected not to apply, because QGIS's `zipfile` extraction does not
carry the quarantine attribute, but no runner can show it, and the program is not notarised (ADR-0009,
*Platforms*). Any platform beyond the three -- Linux on ARM, say -- still needs a configured path.

#### P12c-35 — dilution of precision from the satellite geometry; FR-603 met

P7b recorded DOP as unavailable from `rnx2rtkp`, and that was true of its solution file only. Every
configuration GeoComp writes now sets `out-outstat = residual`; the engine reads the `$SAT` lines of the status
file that produces -- each used satellite's azimuth and elevation per epoch, in the layout `outsolstat` writes
at the pinned commit -- then removes the file, which at this level runs to hundreds of megabytes for a day at
1 Hz. GDOP, PDOP, HDOP and VDOP follow RTKLIB's own `dops()`; each epoch carries them, the session carries each
one's median and the epoch whose PDOP was worst, and the trajectory layer gains three columns. **FR-603 is
met**: 165 met, 10 partly met, 1 open, of 176.

The evidence is RTKLIB's, not GeoComp's: `scripts/rtklib_dops_reference.c` links RTKLIB's `rtkcmn.c` and
applies its `dops()` to the same status file, and every one of the 120 epochs of the sample run agrees to the
six decimals it prints; a live run's worst epoch, PDOP 37.551224 with five satellites, is the reference's. A
hand-worked geometry -- a satellite at the zenith and four at 30 degrees -- gives HDOP sqrt(4/3), VDOP sqrt(5),
PDOP sqrt(19/3) and GDOP sqrt(25/3).

**Found while doing it.** A combined solution writes every epoch's status twice, forward pass then backward,
and the reader as first written appended both: every epoch's satellites doubled and its DOP was too small by
the square root of two -- found by running the engine both ways, before any of it was pushed. Each epoch's
first block, opened by its `$POS` line, is now the one read; keying on the `$POS` line matters because the
backward pass begins on the epoch the forward pass ended on. A live test runs both solution types and requires
the same geometry (`tests/test_rtklib_engine.py::TestABaselineFromALiveRun`).

specs/11 §5 also said cycle slips and rejections are reported in no output format.
The same `$SAT` lines carry a slip flag and slip and rejection counters; the statement is corrected and reading
them is recorded as not done. The `SessionQuality.dilution_of_precision` justification in
`test_no_bare_geodetic_floats.py` said "always None today" and is replaced by reasons for the four new values.

**Not done.** Cycle slips and rejections, from the same lines. A `.pos` read on its own, without the run that
produced it, has no geometry and so no DOP.

#### P12c-36 — cycle slips and rejected observations, as the engine reports them

specs/11 §5 lists cycle slips and rejected epochs among the quality indicators; P12c-35 found that the status
file it reads carries both and recorded reading them as not done. They are read now, in the same pass: a slip
is the slip flag's first bit on a signal flagged valid, a rejection the outlier counter changing to a value
other than zero (specs/11 §5 says why each rule is what it is). Each epoch carries the signals, the session the
counts and the satellites, the JSON summary all four, and the trajectory layer `slips`, `slipped`,
`rejections` and `rejected`.

**Where the evidence comes from.** RTKLIB's sample is clean -- no slip and no outlier in 120 epochs -- so a
reader tested on it would pass reading nothing. `tests/gnss_faults.py` puts faults into the sample's real
rover file where the answer is known: five and three cycles on G20's carriers from 00:30 with no loss-of-lock
flag, and 500 m on G19's pseudoranges at 00:45. The engine flags the slip on both of G20's carriers at 00:30
and rejects both of G19's signals at 00:45, and nothing else; the committed status file of that run is read in
tier 1, and the same faults are put in and the engine run live in tier 4 (`tests/test_cycle_slips.py`).

**Found while doing it.** RTKLIB's rejection counter read 3 at the outlier's epoch: the engine passes over the
residuals up to three times an epoch and counts each rejection, so summing the counter would have reported
three outliers for one. It is read as changes, one per signal per epoch. The sample's rover file holds a RINEX
event record (a splice, flag 4) that a fault-insertion helper written for flag 0 alone refused; the helper
passes event records over.

**Not done.** Which band a frequency number is depends on the constellation and on RTKLIB's code priorities, so
a signal is named `G20/1` and not `G20 L1`. A `.pos` read on its own, as the baseline algorithm reads one,
has no status file beside it and reports neither -- `None`, not zero. GNSS processing writes no HTML report;
the counts are in the JSON summary (single and batch runs alike), the layer and the log.

#### P12c-37 — every refusal says what the user can do (NFR-006), the ratchet and its first batch

NFR-006 is partly met because nothing checked its third part, what the user can do about an error. When
counted, 322 of the 641 refusal templates said what failed and why and stopped. The structural test now reads
a remedy as a clause that begins with an imperative, from a fixed list of verbs, and froze those 322 in
`tests/structural/nfr006_without_a_remedy.txt`; the list may only shrink, and a code that gains a remedy must
leave it. This pull request gives one to 91: all 37 in the settings service and the monitoring,
integration and project algorithms, and all 54 of gravimetry and levelling -- "Give a limit greater than
zero.", "Save to it with the Save to project store algorithm, which takes a backup and then migrates it.",
"Swap its near and far readings." -- each in Portuguese and Spanish too, keeping the reviewed translation and
adding the remedy's. Six more already had remedies the first verb list missed. 225 remain: 146 in the
analysis algorithms, 44 in GNSS and 35 in engines.

**Not done.** NFR-006 stays partly met until the list is empty. The test checks that a remedy is there, not
that it is right; the review still reads each one.

#### P12c-38 — remedies for the engine and GNSS refusals (NFR-006)

The 35 refusals of the DynAdjust and RTKLIB adapters and the 44 of GNSS gain what the user can do: give the
output of the run prepared from this network, run the adjustment again to write a damaged file afresh, use the
DynAdjust release the *Install an engine* algorithm installs, process the session again with ECEF output. Two
are reachable only from GeoComp's own code -- a trajectory point built over a covariance that is not local --
and say so: an internal error, to report. Four rewordings put an existing remedy where a clause starts, so the
test can see it ("set a measurement's Ignore to * to leave it out"); four already had remedies with verbs the
list lacked. 145 remain, all in the analysis algorithms.

**Not done.** The analysis algorithms' 145; NFR-006 stays partly met until they are done.

#### P12c-39 — the last 145 refusal templates; no exemption

The 145 refusals of the analysis algorithms gain what the user can do, in three languages, and the frozen list
is empty and removed: every one of the 641 refusal templates says what failed, why and what to do, and a new
one must. They include the readers of the Adjust and Krumm corpora, whose refusals end with the offending line
and now say what to correct before it ("…; correct it on the line: %4"), and fourteen checks of the core that
only GeoComp's own code can reach -- thirteen of arithmetic, units and shapes (the incomplete beta function's
domain, a square root at zero, a covariance block of the wrong shape) and an observation without its
provenance -- which now say they are an internal error to report.
"build", "map" and "complete" join the verb list; two templates already used them.

**Found while doing it.** The rule reads templates, and an algorithm can refuse without one: a sentence of its
own, raised as a `QgsProcessingException`. Of the 134 such sentences, 94 say what failed and stop -- "No RINEX
observation sessions were found in %1", "The file '%1' does not exist." NFR-006 stays partly met for them.

**Not done.** Those 94; the structural test does not read them yet.

#### P12c-40 — the sentences an algorithm words itself, and the GUI's failures (NFR-006)

The structural test now reads the refusals an algorithm raises in words of its own, with no template: the
literal text of each `QgsProcessingException`'s `tr` calls, and the sentences `input_problem` and
`missing_products_message` return for a caller to raise. Of 127, 86 said what failed and stopped, and each
now says what to do, in three languages, placed before the detail it ends with: choose the folder that holds
the observation files, check the path or create the folder, correct the problems the log lists as blocking,
choose the document *Import levelling field book* wrote. A second rule covers what a window, a panel or a
layer says failed. These sentences have no single sink, so the rule is read off their wording "could not",
and all eight lacked a remedy; among them is the fallback for a code with no template, which now says it is an
internal error to report. A log warning the rule cannot see, a style file that is missing, was given one too.

**Found while doing it.** P12c-39's count of 94 of 134 was wrong. It counted `tr` calls, not raises. And the
extractor treated a raise that called `reason_for`, `_describe` or `about_input` as already worded. The first
two give Python's own text for an `OSError` or a `KeyError`, and the third only puts the input's label in
front. So nine sentences were never checked, and seven of them said nothing about what to do: two of GNSS,
whose words are all their own, and five readers whose detail can be Python's. They are among the 86. Only the
helpers that always give a template's words now excuse a raise.

The GNSS folder scan's warnings carry their reasons as the reader's English or as an error's code and expected
value, and the algorithms interpolate them into translated sentences: "Could not read %1: %2". That breaks
FR-091 as well as NFR-006, and the P12c-9 rule does not see it because the text arrives in a data structure,
not in a call.

**Not done.** The scan's warnings, so NFR-006 stays partly met; they are P12c-41. A GUI failure worded other
than "could not" is not seen by the rule. And the test checks that a remedy is there, not that it is right.

#### P12c-41 — GNSS says files and products in words; the core's English held to a list (FR-091, NFR-006)

The GNSS folder scan reported what it skipped or doubted as `(file, reason)` pairs in its own English, and four
algorithms put the reason into a translated sentence. It now reports findings, with six codes: a file it
could not read (worded with the refusal's own template), a RINEX file that is neither observation nor
navigation, a name that claims another station or another day, navigation paired by fallback, and a session
whose span cannot be known. Each template says what to do. One helper, `report_scan`, says them for the four
algorithms; batch processing now warns of the doubts as single-session processing does.

A product was named by `ProductRequest.describe()` in eight sentences, and why it could not be had by the bare
"not found" or "no download service". It is now named in words, "final orbit for 2025-01-02", and each reason
is a sentence with what to do. The two reasons are constants in the core, `NOT_FOUND` and
`NO_DOWNLOAD_SERVICE`, so the algorithms compare against a name, not a copied string. A batch row the engine
solved nothing for said the batch's English `detail`; it now says what to check in the log.

**Found while doing it.** The same mistake is made outside GNSS. A sentence an algorithm makes takes a value
the core wrote in English for its own logs: the datum defect and how it was removed, the global test's note,
the integration's routing reason, the techniques and variance-component groups, the DynAdjust stages' reasons.
P12c-9's rule reads templates and cannot see it. FR-091 was recorded as met, and is partly met. The structural
test now reads every value put into a translated sentence outside the core: a `describe()`, or an attribute
the core fills with English. The ten sites left are frozen in a list that may only shrink.

**Register.** NFR-006 is met: every refusal template, every sentence an algorithm raises itself, every failure
a window reports in the words "could not", and the scan's warnings say what to do, each held by a test.
FR-091 is partly met, for the ten. The totals are unchanged.

**Not done.** The ten sites, which are P12c-42. Core English under a name the list does not hold is not seen.

#### P12c-42 — the core's enums and English in words, wherever a reader is shown them (FR-091 met)

P12c-41's rule read the values put into a translated sentence. Widened to every place a value reaches a reader
-- a report cell or note, the log, a widget -- it found 25 sites beside its ten. They were report cells showing
an enum's value as it stood (a Portuguese report's datum read `minimum_constraint`, its frame `plane_2d`, an
observation `slope_distance`) and report notes showing the global test's English note. All 35 are worded now.

- `geocomp/algorithms/labels.py` says the core's values in words. `in_words` covers the twelve enums a reader
  is shown, and a test holds every member to having words. Beside it are the technique, closure-kind,
  test-name, solver and engine tokens, and the datum defect with its components. The report's own technique
  labels moved there.
- The global test's failure is said by `global_test_failed`, which tells a variance factor too large (look for
  blunders, then the precisions and the model) from one too small (the precisions are pessimistic).
- The DynAdjust stages and the integration's routing carry a code and its values beside their English reason,
  which stays in the provenance and the prepared job's manifest. The algorithms word them. A job an older
  release prepared has no code, and its skipped stage is said without the why rather than in English.
- The gravity datum report says which definition held it and at which stations. The pre-analysis design keeps
  its `DatumDefect`.

**Found while doing it.** Two values the rule reads as the core's were the plugin's own translated words:
the grid reduction's `note` and the time-series plot's `describe`. They were renamed rather than excused.
The adjustment log said "removed by: cholesky" -- the solver, not the datum -- and now says "Solved by
Cholesky factorisation".

**Register.** FR-091 is met: 166 met, 9 partly met, 1 open.

**Not done.** Core English under a name the rule does not hold, or reaching a reader by a path it does not
read, is not seen. The English in the provenance and in JSON documents is data, and stays.

#### P12c-43 — configurations compared side by side (FR-359 met)

FR-359 was partly met: the comparison and its significance test existed, written as one table with a row per
configuration, and the side-by-side presentation specs/11 §6 asks for did not. `geocomp:gnss_compare_configurations`
now writes an HTML report, one column per configuration with the reference first. It shows the elevation mask
each ran at, the baseline's length and its standard deviation, the difference from the reference in X, Y, Z, 3D
and length, the test statistic and the decision. Below them are the quality indicators of specs/11 §5 from each
configuration's own run: epochs, fixed fraction, median ratio, satellites, median PDOP, cycle slips and
rejected observations. A note says how to read the independence assumption, and a sentence says what the
comparison found.

A configuration was only an elevation mask. It can now be an RTKLIB options file of the user's own (FR-070): give
two or more, and each is a configuration named by its file and compared at the options it states. A file is
the named, shareable profile specs/11 §6 describes. The comparison's JSON records what each configuration set
and its quality indicators.

**Decided.** No custom dialog. specs/15 §1.2 listed one; what the user needs to see is the result, and the report
is where every algorithm presents one, opened by Processing's results viewer from the menu, the toolbox or a
model alike. A dialog that ran the configurations would be a second way to run them (ADR-0005), and one that
only collected parameters would add nothing the Processing dialog lacks. The time series took the same turn in
P10b, as a dock panel.

**Found while doing it.** The log printed the export's rows as they stood: an English header -- "configuration,
dX mm, ..., significant" -- and "yes" or "no", in every language, through an f-string the P12c-42 rule cannot
read. Each configuration is now one sentence in words. The CSV keeps the data's own header: it is an export for
another program, as the JSON's keys are.

**Register.** FR-359 met: 167 met, 8 partly met, 1 open.

**Found while doing it, too.** A live comparison of two masks over RTKLIB's sample, added as a tier 4 test
(`tests/test_gnss_comparison.py::TestTwoMasksOverRealData`), could not run: at 30° one epoch's printed covariance
is marginally indefinite, within what its four decimals explain, and the `.pos` reader refused the whole file
over it. The default sweep, 10° to 35°, lost two of its six configurations to this. Only the baseline's last
epoch went through `covariance_from_printed`; every epoch does now, conditioned within its own printing and
marked when moved, and a matrix indefinite beyond that is still refused (specs/08 §8.2).

**Not done.** The report is tested end to end against a stand-in for `rnx2rtkp` that answers every configuration
with one solution, so its differences are zero. Two real runs are compared in tier 4, through the core, not
through the algorithm and its report.

#### P12c-44 — field books and stations from the project's own layers (FR-320, FR-160)

FR-320 was partly met because a QGIS layer of the user's own design was not read: stations as points and
observations as table rows "would need a field mapping that does not exist" (P12c-24). The field books' own
mapping was that mapping. *Import total station field book* and *Import levelling book* now take the book as a
table layer instead of a file -- the field names its header, each feature a row, each value the text a CSV of it
would hold -- and write the same document from it as from the file, with the numeric fields typed as numbers or
not. *Classical network* takes its approximate coordinates from a point layer: a field names each station, a
second field or the point's Z gives its height, and a layer in another CRS is carried into the network's,
horizontally. RD-01, moved into the area EPSG:31982 is defined for, adjusts to the same answer from a point
layer in that CRS, exactly, and from one in
EPSG:4326 to a few nanometres. Exactly one of a file and a layer is given; both and neither are refused,
naming the two inputs, and a station the layer cannot place is refused by name
(`geocomp/algorithms/layer_sources.py`, `tests/qgis/test_layer_sources.py`).

**Found while doing it.** The end-to-end test was to carry RD-01 from its layers into DynAdjust's input, and it
cannot be carried there from its files either. *Adjust with DynAdjust* refuses a network in a projected CRS:
the job has a `projection` field the writer needs, and the algorithm never sets it, although the combination
algorithms derive one from the CRS through QGIS. It gives no geoid undulation for a projected network's
orthometric heights either, and a 2D network's horizontal distances have no DynAdjust measurement type. specs/07
§4 and the register said the field-book imports' networks reached DynAdjust; a total-station network does not,
and both now say so. That is P12c-45.

**Register.** FR-320 stays partly met, for a different reason: the layers are read, and a total-station network
does not reach DynAdjust. FR-160's row records the layer. 167 met, 8 partly met, 1 open.

**Not done.** Only *Classical network* takes stations from a layer. A levelling network's known heights, a
traverse's known stations and a gravity network's stations still come from files. A layer's geometry is not read
as a field book's: where the book was observed from is the network's business.

#### P12c-45 — a total-station network reaches DynAdjust (FR-320 met)

P12c-44 found that *Adjust with DynAdjust* refused every network in a projected CRS, so no total-station
network reached DynAdjust from files or from layers. Three things stood in the way, and the core had answered
each already. RD-01 goes through DynAdjust in tier 4 with the projection stated, the undulations given and,
until now, `allow_partial` set; the algorithm did none of the three.

- **The projection.** The algorithm now asks QGIS which projection the network's CRS is and states it to the
  writer. That is UTM or Transverse Mercator on GRS80, read by the parser the combination has used since P9b,
  now `geocomp/algorithms/projection.py`. Anything else is refused by station, as before, in a message that no
  longer says GeoComp "cannot tell which projection" a CRS is.
- **The heights.** A *Classical network*'s heights are orthometric on grid coordinates, which the writer turns
  into DynaML's *h* only with an undulation, and a geoid grid cannot give one there. The algorithm takes one,
  *Geoid undulation N*, for the whole network; a grid as well is refused.
- **The lone direction.** RD-01's station 3 sights one target, and a direction set of one has no DynAdjust
  form. It was reported as skipped and made the network partial, which no algorithm accepts. Leaving it out
  changes nothing, which a tier-4 test asserts. It is still reported, and no longer counts as
  partial; one that does still refuses the network (`tests/test_dynadjust_pipeline.py::TestAPartialNetwork`).

RD-01 now goes from its files to DynAdjust's input in three dimensions, and from a table layer and a point layer
to the same input, file for file: latitude and longitude, *h* = *H* + *N* (`tests/qgis/test_layer_sources.py::
TestDynAdjustInputFromLayers`). The tier-4 cross-validation of RD-01 runs without `allow_partial`.

**Found while doing it.** The log line that lists the skipped observations joined (id, reason) pairs as text and
raised `TypeError`. No skip had reached it before, because every one was refused first. It lists the ids.
specs/07 cited "§5 rule 6" for the partial-network rule, which is §4.3's.

**Register.** FR-320 met: 168 met, 7 partly met, 1 open.

**Not done.** A 2D network is still refused, for its horizontal distances: DynAdjust has no measurement type for
one, and writing a grid distance as an ellipsoid arc needs reductions GeoComp does not make (specs/07 §4.2).
One undulation serves the whole network; a geoid model read per station is not. The input is checked as
written, not adjusted: the end-to-end test stops before running, so it needs no DynAdjust. The core's tier-4
test is what adjusts RD-01.

#### P12c-46 — the engines' working directory and the report templates are settings (FR-066 met)

FR-066 lists four paths for Global Settings, and P12c-6 made two of them settings, the engines' locations. It
decided the other two, working directories and report templates, were each algorithm's parameters. That
answered how a run names them, not where an organisation sets them once, and specs/19 §7.3 had said all along
that reports take their template from "the templates directory configured in Global Settings". No setting named
one. The core could already read a user's templates folder (`load_template(name, directory=...)`), and no
algorithm gave it one unless the run named a template.

Both are settings now, under *Paths and engines*, global as the engines are. Each is the default a run falls
back to; a folder or template the run names still wins.
- The working directory holds every engine run's working folder (`working_directory()` in
  `geocomp/algorithms/defaults.py`). An unwritable one is refused by name, saying where it is set. Empty, the
  system's temporary directory.
- The templates folder serves every template-driven report: adjustment, combination, monitoring, comparison and
  time series (`report_template()`). A folder without the template a report needs falls back to the shipped one.

**Register.** FR-066 met; FR-931's row records the folder. 169 met, 6 partly met, 1 open.

**Not done.** A kept working folder is still named by the run: the setting is where it goes when the run names
none. RTKLIB's single run with its solution saved keeps its working folder beside the solution, as before.

#### P12c-47 — a staff reading's default standard deviation is a setting (FR-064 met)

FR-064 asks for default weights per observation type, and the register held it partly met for the seventeen
types without one. Which types a default can serve is decided by specs/05 §5: a type default is step 3 of the
precedence an importer follows when it weights a reading at the boundary, after the data and the instrument
profile. The readers ask it for seven kinds of reading. Directions, zenith angles and distances had settings
since P3. Instrument and target heights never reach step 3, because every instrument profile states them,
the generic one included. That leaves the staff reading. *Import levelling book* asks for it when the level
profile states no reading precision, and until now only the run's own parameter could give one.
`stochastic.default_sigma_staff_reading` is that parameter's default now, as the total station's are theirs.

Every other observation type reaches GeoComp with its σ, from RTKLIB's covariance, a gravimeter's reading, a
network document or a DynAdjust file, or is derived from readings that carry one. A default for any of them
would be a control that changes nothing, which `tests/structural/test_settings_are_honoured.py` exists to
refuse. FR-064 is met on that reading of it; specs/05 §5 now says so.

**Register.** FR-064 met: 170 met, 5 partly met, 1 open.

**Not done.** No setting serves a sight distance, whose precision falls back to the digits the observer wrote
(specs/05 §2.3), or a height difference, which levelling weights by line length or setups.

#### P12c-48 — an engine's failure, packaged for its developers (FR-955 met)

FR-955 asks that a defect in DynAdjust or RTKLIB be straightforward to report upstream, with the inputs that
triggered it. specs/20 §8 says how: GeoComp packages the inputs, configuration, command line and output that
reproduce it. Half of that was there already. A failed run's working directory was kept and named, with the
inputs and the configuration in it. The other half was not. The command and what the engine said travelled on
the refusal and in the solution's provenance, cut to their first and last forty lines, and nothing put them
together.

- **The record.** Every run of every engine program now leaves its record in its working directory: each
  stream whole, and a line of `geocomp-runs.jsonl` with the command, the exit code, the time and the version
  (`keep_record` in `geocomp/engines/base.py`). The environment is not recorded (NFR-010).
- **The package.** *Package an engine problem* (Project menu) zips the directory with an English README for
  the engine's developers: engine and version, each program, its command and how it ended, and where that
  project takes reports. It removes nothing, and says to look before sending.
- **The pointer.** A failed DynAdjust stage's refusal and RTKLIB's both name the algorithm.

A real DynAdjust failure is packaged in tier 4: the real `dnaimport` refuses a broken station file, and the zip
holds the station and measurement files, the plan, `dnaimport`'s output and its exit code.

**Found while doing it.** `EngineRun.to_dict` said "the retained work_dir holds the full logs", and nothing
wrote them. It is true now. And as first written the record was kept by every run, the version probes too:
DynAdjust's probe runs in QGIS's own working directory and RTKLIB's beside the program, which may be the copy the
plugin ships, so each detection left three files there. A local test run left them in the repository, and they
went into the first commit of this change. A probe keeps no record now (`run_process(..., record=False)`), and
a test detects both engines from a folder that must stay empty
(`tests/test_engine_problem_report.py::TestEveryRunLeavesItsRecord::test_detecting_either_engine_writes_nowhere`).

**Register.** FR-955 met: 171 met, 4 partly met, 1 open.

**Not done.** Nothing is filed for the user: the package is a file to attach, and where the project takes it is
a link. A folder kept before P12c-48 holds no record and is refused, which says to run it again. The RTKLIB
side is tested with stand-ins, not with a real `rnx2rtkp` failure.

---

## P13 — Validation, documentation and release

**Goal.** Evidence that it is right, material that teaches it, and v1.0 on plugins.qgis.org.

**Specs.** [`20-testing-and-validation.md`](./20-testing-and-validation.md) ·
[`21-packaging-ci-release-licensing.md`](./21-packaging-ci-release-licensing.md)

**Delivers.** The remaining reference datasets assembled; field campaign data collected with students
(RD-10); case studies comparing the integrated workflow against traditional CLI-and-script workflows; the
commercial software comparison protocol executed and published; tutorials in three languages; the
contribution guide; the upstream defect reporting path; v1.0 released.

**Also delivers, moved from P12 on 3 October 2026 (P12c-5):** the native-speaker review of both
catalogues ([`18`](./18-i18n-and-profiles.md) §3.1), and ocean loading on gravity
([`12`](./12-module-gravimetry.md) §4.2) on the condition it has carried since P8 — written when W-11 can
check it, and moved again, with the move recorded, if it cannot.

**Closes.** FR-951, FR-952, FR-954, FR-955

**Exit.** Every reference dataset has a passing test. At least one published commercial comparison with every
discrepancy classified and no unexplained differences remaining. Tutorials cover every module in all three
languages. v1.0 is on plugins.qgis.org and installs cleanly. At least one external contribution merged.

**Begun in P12c.** FR-955, which this phase closes, was met in P12c-48: the upstream defect reporting path is
*Package an engine problem*.

#### P13-1 — the contribution guide (FR-954 partly met)

[`CONTRIBUTING.md`](../CONTRIBUTING.md) is the guide specs/20 §8 describes. It covers:
- the ways to take part: reporting a problem with the system report attached, reporting an engine's problem with
  the package, contributing reference data against specs/23's wanted list, reviewing a translation, writing code;
- that specifications come first, and how a change amends them and their registers;
- what "done" means: the tiers with their commands, the four workflows and when each runs, the structural checks
  a newcomer meets first, and why GeoComp refuses rather than invent a standard deviation;
- the standard a pull request and a commit are held to, and the licence.

The README's *Contributing* section points to it.

**Register.** FR-954 partly met, from open: 171 met, 5 partly met, 0 open.

**Not done.** How companies and public bodies take part -- sponsored work, contracted features, institutional
data, a voice in decisions -- is the maintainer's to set out, as the register has said since P12c-13. The guide
has the section, and the section says that.

#### P13-2 — the levelling tutorial (FR-952, FR-950 stay partly met)

*Install tutorial dataset* offers a third dataset, **`rd04-loop`**
(`geocomp/resources/datasets/rd04-loop/`): RD-04's loop, three lines and ten setups between BM1, BM2 and BM4,
with one foresight on BM2-BM4 written down 12 mm wrong. Its field book is what
`tests/reference_levelling.py::tutorial_rows` generates from the module's seed. Its README is a walkthrough in five
steps, and it is about what a loop cannot do. The closure fails: −15.7 mm against 7.0 mm, which says
something is wrong but not what. The adjustment holding BM1 has one degree of freedom. Its global test fails, every w-test scores
1.00, so no outlier is named, and BM2 comes out 2.5 mm from its true height. Holding all three benchmarks gives
every line its own closure, and the failing-line gate names BM2-BM4.

Tests. `tests/test_tutorial_dataset.py::TestTheLevellingLoop` checks that the shipped files are exactly the
generator's and that the build ships them. `tests/qgis/test_levelling_tutorial.py` installs the dataset and
follows the README through the four algorithms. It reads every number the README quotes, out of the README, and
compares each with what the algorithm returned. It also checks that each step's title and every input the README
fills are the toolbox's own.

**Defects found.**
- *The dataset order was the folders' names sorted*, and the enum's index is what a saved model keeps.
  `rd04-loop` sorts before `rtklib-sample`, so adding it would have turned a model's GNSS sample into the
  levelling loop. The test that should have caught it asserted the sorted order itself. The order is now
  `geocomp.resources.DATASET_ORDER`, which is append-only, and the test holds it and the folders to each other
  both ways.
- *The walkthrough as first written named dialogs by names they do not have.* It said "Reductions" for
  *Reduced lines*, "Import levelling book" for *Import levelling field book*, and "Network adjustment" for
  *Levelling network adjustment*, and it gave the tolerance and uncertainty inputs without their units. It also
  quoted the gate's refusal without its last sentence, which is the remedy. The test now reads them all from
  the toolbox.
- *Install tutorial dataset*'s help described RD-01 alone, while its enum offered two datasets. It now names
  all three.

**Register.** Unchanged: 171 met, 5 partly met, 0 open. FR-952 now has two modules of six, and FR-950's row
names the second shipped reference dataset.

**Not done.** Tutorials for GNSS, gravimetry, integration and monitoring. The Portuguese and Spanish versions of
both walkthroughs. Worked examples as QGIS projects.

#### P13-3 — the monitoring tutorial (FR-952, FR-950 stay partly met)

*Install tutorial dataset* offers a fourth dataset, **`rd08-dam`** (`geocomp/resources/datasets/rd08-dam/`). It
holds two epochs of RD-08's synthetic network, as measured and not yet adjusted, and an alert threshold. The
networks are what `tests/monitoring_network.py::tutorial_networks` makes from the seeds and the motion the
monitoring tests already use. That function is `epoch()` split in two, with the network now stating its epoch.
The README has four steps:
1. Adjust 2025 on the four pillars, with minimum constraints. It passes with a variance factor of 1.14, and data
   snooping flags three good observations at 95 %. GeoComp rejects none, and the README says why that matters in
   monitoring.
2. Adjust 2026 the same way. It passes too: no single epoch can show motion.
3. Compare the epochs. The reference block is congruent (0.59 against 2.44), and the whole network is not. O2's
   10.8 mm is significant (77.1 against 3.22), within its ellipse of the 10.0 mm it was moved, and no other
   target's motion is. The alert is at O2 alone. The "Try this" adjusts both epochs as free networks instead, and
   the displacements agree to a tenth of a micrometre.
4. With O2 among the reference stations, the comparison is refused, and the refusal names O2.

Tests. `tests/qgis/test_monitoring_tutorial.py` follows the README, as P13-2's does. The helpers both use
are now one module, `tests/qgis/walkthrough.py`. It also checks every choice a step makes from a list, such as
*Minimum constraint — over chosen stations*, against the dialog's options. `tests/test_tutorial_dataset.py::TestTheMonitoredDam`
checks the shipped networks against the generator, to a nanometre and not byte for byte, because the
distances are computed floats.

**Defects found.**
- *My first draft sent the reader to GeoComp ▸ Monitoring*, a menu that does not exist. Comparison is under
  *Analysis*, where specs/15 §1.1 puts it. The test now builds the path from the registry.
- *A check I first wrote for "nothing is rejected" was vacuous.* It read observation statuses from a solution
  document, which holds none, so it could not fail. It now checks that all 36 observations were adjusted and
  the degrees of freedom are 21.
- *`THIRD_PARTY.md`'s table of bundled assets named none of the shipped datasets.* That included
  `rtklib-sample`, which is under RTKLIB's own licence and has been in every plugin ZIP since P12c-27. P13-1's
  contribution guide made it worse: it said third-party data "is never part of the plugin package". Each
  dataset now has a row, a test requires one, and the guide says what is true.
- *The walkthrough's numbers held on the dense path only, and CI's `--sparse` pass found it.* On the sparse path
  the epochs carry no covariance between stations, so the comparison's statistics differ: 1.07 for the block
  where the README says 0.59, and 66.5 for O2 where it says 77.1. A nine-station network always takes the
  dense path as shipped, so the tests that quote numbers are `dense_only`. A new test asserts what the
  numbers conclude on either path: the block holds, O2 alone moved, and O2 held as a pillar is refused.
  I had run neither walkthrough's QGIS tier with `--sparse`; both pass it now.

**Register.** Unchanged: 171 met, 5 partly met, 0 open. FR-952 now has three modules of six.

**Not done.** Tutorials for GNSS (`rtklib-sample` shows a run but says nothing about accuracy), gravimetry and
integration. The time series of three or more epochs. The Portuguese and Spanish walkthroughs. Worked QGIS
projects.

#### P13-4 — the gravimetry tutorial (FR-952, FR-950 stay partly met)

*Install tutorial dataset* offers a fifth dataset, **`rd07-usgs`** (`geocomp/resources/datasets/rd07-usgs/`).
It holds two of USGS's synthetic surveys for GSadjust, byte for byte the copies RD-07 vendored in P8a, with
GSadjust's CC0 licence beside them, and two profiles of meter B44: one uncalibrated and one with Test 3's
stated calibration. It is the first tutorial whose answer is someone else's. The README walks six steps in
three pairs:
1. Test 2: pre-processing fits the drift to the base, 0.01008 ± 0.00142 mGal per hour. The network, holding
   sta1, passes (1.17) and estimates the drift with the stations at 0.00915 ± 0.00109, against the 0.01 USGS
   put in. The four unknown stations come back within 2.6 µGal of USGS's truth, each within its own
   standard deviation.
2. Test 3, uncalibrated, with sta3 known as well: the global test fails (525). With sta1 alone it passes
   (1.51) and sta3 is 154 µGal wrong. The variance factor is the same to every digit as with the calibration,
   so the network cannot see the scale.
3. Test 3, calibrated, both stations known: it passes (1.56), and every station is within 2.5 µGal.

The truth USGS published moved from `tests/test_gravimetry_network.py` to `tests/usgs_gravity.py`, which
both that test and the tutorial's use. `tests/qgis/walkthrough.py` gained `run_logged`, because the drift
the README quotes is in the run's log and not in any output.

**Defect found, by CI.** The shipped `Test2.txt` and `Test3.txt` failed their byte-for-byte check on Windows.
Git checked them out with CRLF, because only the vendored copies were marked `-text` in `.gitattributes`.
The plugin's copies are now marked the same way, as RTKLIB's sample has been since P12c-27. Every other
check of the shipped files parses them, so line endings cannot move it.

**Register.** Unchanged: 171 met, 5 partly met, 0 open. FR-952 now has four modules of six.

**Not done.** Tutorials for GNSS and integration. GNSS's needs RD-06's accuracy criterion met, or another
dataset with published coordinates that may be redistributed. The Portuguese and Spanish walkthroughs.
Worked QGIS projects.

#### P13-5 — the integration tutorial (FR-952 stays partly met)

*Install tutorial dataset* offers a sixth dataset, **`combined-curitiba`**
(`geocomp/resources/datasets/combined-curitiba/`). It is the survey integration is cross-validated on, with one
change: the total station measured three times worse than it states. That change is a new `noise` scale in
`tests/combined_network.py::survey`; at 1 it draws exactly what the survey drew before. The inputs are the
generator's (`tests/test_integration.py::tutorial_inputs`): the GNSS baselines in ITRF2014 at 2020.0 with the
control marks at their known positions, and the total station's observations with no frame. The README has
two runs of *GNSS and total station*, holding CTB1 and CTB2:
1. Without variance components the global test fails (5.80). The log's breakdown by technique points at the
   total station: vᵀPv/r 6.950 against the GNSS's 1.375. The README says, as the report does, that this is a
   quick reading of fit and not a variance component.
2. With variance components the total station gets 7.19 ± 1.76, within its uncertainty of the 9 it was made
   with, and the GNSS 0.56 ± 0.46. The global test passes, and the README says that this is by construction
   and not evidence.

`tests/qgis/test_integration_tutorial.py` follows it and holds the components to the misweighting the survey
was built with. The GNSS input that the presets' tier-3 test built in place moved to
`tests/test_integration.py::gnss_input_held_at_truth`, so tier 1 can check the shipped file.

**Defects found.**
- *The generator's GNSS noise shadowed the new parameter.* A local variable called `noise` held each
  baseline's error vector, so the terrestrial draws after the baselines saw an array and failed. The local is
  now `error`.
- *My first draft called vᵀPv/r "its own variance factor in effect".* The report says plainly that it is not a
  variance component. The README now agrees with the report, and the test holds both to it.
- *My first draft named a report section, "Variance components by technique", that the integration report
  does not have.* It is *Techniques*, under *Variance components*, and the test reads it from the report.

**Register.** Unchanged: 171 met, 5 partly met, 0 open. FR-952 now has five modules of six.

**Not done.** A GNSS tutorial. The Portuguese and Spanish walkthroughs. Worked QGIS projects.

#### P13-6 — the levelling walkthrough in Portuguese and Spanish (FR-952 stays partly met)

`rd04-loop` now ships `README.pt_BR.md` and `README.es.md` beside its `README.md`, and the English one points to
them. In the translations, the prose uses the decimal comma. Values the reader types stay as typed, and the
translations explain why: the *Benchmarks* field separates its entries with commas, so a height in it takes a
decimal point.

Two checks hold a translation, and both apply to every walkthrough translated later:
- `tests/test_tutorial_translations.py` holds it to its English original, without QGIS. It must have the same
  steps naming the same algorithms in the same order, and the same values in backticks. It must have the same
  numbers outside them, with the decimal comma and no decimal point left in the prose. Every input it fills,
  and every choice from a list, must be named as the catalogue translates the English label. Changing a
  number, a label and a choice in the Portuguese file each made it fail.
- `tests/qgis/test_levelling_tutorial.py::TestInEachLanguage` installs each catalogue, as
  `tests/qgis/test_language.py` does. It checks the translated walkthrough's names against the translated
  dialogs, and its quoted refusal against the refusal GeoComp gives in that language.

**Defect found.** Translating the refusal turned up a Portuguese inconsistency. The levelling network's
dialog and its refusal called the failing-line switch 'Ajustar linhas que falharam na tolerância'. Global
Settings, where the refusal also sends the reader, labels it 'Ajustar linhas que não cumpriram a tolerância'.
English and Spanish use one label in both places, so nothing in English could show the problem. The
Portuguese label, the refusal, the network's help and two related messages now use the Global Settings
wording. `tests/structural/test_translations.py::test_a_label_a_message_quotes_is_the_label_shown` checks
every catalogue: whenever an English string quotes a capitalised label, the label must have one translation
across every context, and the translated string must quote it. It covers ten quotations. It failed on the
old catalogue and passes on the new one. As first written it paired possessive apostrophes as quotation marks
and missed the help text; it now searches for each label directly.

**Register.** Unchanged: 171 met, 5 partly met, 0 open.

**Not done.** The other walkthroughs in Portuguese and Spanish: RD-01's, the monitoring one, the gravimetry one,
the integration one and the GNSS sample's. *Install tutorial dataset* still says "Start with README.md" in
every language, which becomes right per language once every dataset has its translations. A native speaker's
review of these texts belongs with the catalogues' (specs/18 §3.1).

#### P13-7 — the monitoring, gravimetry and integration walkthroughs in Portuguese and Spanish (FR-952 stays partly met)

`rd08-dam`, `rd07-usgs` and `combined-curitiba` now ship `README.pt_BR.md` and `README.es.md`, and each English
README points to them. All three are held by P13-6's tier-1 checks, so `TRANSLATED` in
`tests/test_tutorial_translations.py` now names four walkthroughs. Each tier-3 test gains its checks in each
language:
- **Monitoring.** It checks every dialog, input and choice name, the menu path, the labels and the datum
  choice named in the prose, under the installed catalogue. The quoted refusal must be the one GeoComp gives in
  that language. Like the English one, that check runs on the dense path only.
- **Gravimetry.** It checks every name, and the known-gravity label named in the prose.
- **Integration.** It checks every name, and that the two runs differ only in the components switch. GeoComp
  is run in each language: the log line, the per-technique breakdown and the report's two section headings
  the translation quotes must be what GeoComp writes. Changing a number in the breakdown, a word in the log
  line, a label or a heading in the Spanish file each made it fail.

A block quote is GeoComp's own words, which write a statistic with a decimal point in every language, so the
tier-1 check for a decimal point left in the prose skips block quotes; tier 3 holds those to GeoComp. That
check also skips section numbers (`specs/22 §5.6`). A choice the catalogue does not translate, such as the
frame *ITRF2020*, is expected unchanged; tier 3 holds it to the translated dialog's options.

**Register.** Unchanged: 171 met, 5 partly met, 0 open.

**Not done.** RD-01's walkthrough has never been held to the dialogs as the later four are. It should be,
and translated after that. The GNSS sample's walkthrough is untranslated. *Install tutorial dataset* still
says "Start with README.md" in every language. A native speaker's review of these texts belongs with the
catalogues' (specs/18 §3.1).

#### P13-8 — one English string, one translation (FR-093)

Translating the integration walkthrough (P13-7) turned up *Estimate a variance component per technique* worded
two ways in each language. The integration dialog said *um componente* and the levelling one *uma
componente*, *un* and *una* in Spanish. A reader who learns a label in one dialog looks for the same words in
the next.

`tests/structural/test_translations.py::test_one_english_string_reads_the_same_in_every_dialog` makes it a
rule. An English string that appears in several contexts, 278 of them in each catalogue, reads one way in
all of them, unless `TRANSLATED_BY_CONTEXT` lists it with what it means in each place. Seven strings are
listed:
- *(none)*, whose gender is the quantity's;
- levelling's *Differences*, which are height differences;
- the two broadcast-navigation product kinds, which are also written into the middle of a sentence;
- *Layout*, both a level book's column layout and a print layout;
- *To*, both a line's end and a transformation's target frame;
- *Uncheckable*, both a column of counts and one observation's decision.

`test_every_string_translated_by_context_still_differs` removes an exception no catalogue needs any more. On
the old catalogues the rule failed with ten strings, every one named (specs/18 §3), and each was unified:
- *componente* is masculine, the general noun in both languages, and two messages about variance components
  changed their agreement with it;
- the rest took the wording most of their dialogs already used;
- in the profiles window, *Largest imbalance along a line (m)* changed with the label beside it.

No English string changed, and no walkthrough named a changed label.

**Register.** Unchanged: 171 met, 5 partly met, 0 open. Row 18.4 cites the new test.

**Not done.** The rule checks that a string reads one way. It cannot check that two different English strings
for one idea read alike, nor whether the wording chosen is the best one. Both are the native speakers'
review's (specs/18 §3.1).

#### P13-9 — RD-01's walkthrough held to the dialogs, and the datum removed once (FR-952 stays partly met)

RD-01's walkthrough was written before `tests/qgis/walkthrough.py` existed, and had never been checked
against the dialogs. Checking it found four names that were not the dialog's:
- *Source*, where the dialog says *Field book*;
- *CRS*, where the dialog says *CRS authority code, e.g. EPSG:31982*;
- *2D* and *inner constraint* written as words, not chosen from the lists.

Its *Try this* asked the reader to name station 1 in *Fixed stations* and promised the same residuals.
GeoComp refused it under *Inner constraint*. Under *Minimum constraint* it ran, with a variance factor of
15,388 instead of 141.

That turned up two defects in the core and one in *Classical network*:
- **The datum removed twice.** The defect is counted from the observations, so inner and minimum
  constraints remove all of it even when held stations have removed part. The adjustment now refuses held
  stations under either, with `datum_removed_twice`, naming them (specs/06 §3). No existing caller relied on
  the combination: every tier passed with the refusal in place.
- **Nowhere to choose the minimum constraint's stations.** *Classical network* offered *Minimum constraint
  — over chosen stations* but had no input to choose them in, so it took the fixed stations and held them
  too. It now has **Datum stations (comma-separated; empty = all)**, as *Adjust network* has, not hidden in
  Basic mode (specs/09 §4.4). Its help and both translations say which datum reads which input.
- **A zero variance refused.** Minimum constraints over RD-01's stations 1 and 2, the second due north of
  the first, fix both eastings exactly. Computed, one variance came out −2 × 10⁻²⁴ m², and the solution was
  refused as having a negative variance. Over 2 and 3 the rounding fell the other way. The dense and sparse
  constrained solvers now zero a variance that rounding took below zero, with its row and column, within
  `Covariance`'s tolerance for computed matrices.

The walkthrough now names what the dialogs show. Its *Try this* defines the datum over stations 1 and 2, and
says why holding station 1 as well is refused, and why station 1 alone cannot be the datum. The tier-3 test
checks every name and runs every claim:
- step 3's 4 degrees of freedom and variance factor of 140.67;
- the same residuals, degrees of freedom and variance factor over stations 1 and 2, with different
  coordinates;
- both refusals.

It also stopped turning the atmospheric correction off in step 2, which the walkthrough never asks a reader
to do; the counts are the same either way. At tier 1, `TestTheDatumIsRemovedOnce` and `TestRoundedVariances`
hold the core.

**Register.** Unchanged: 171 met, 5 partly met, 0 open. FR-222's and FR-952's rows cite the new tests.

**Not done.** RD-01's walkthrough in Portuguese and Spanish, now that it is held to the dialogs. The GNSS
sample's walkthrough has never been held to them either. Holding some stations and constraining the rest of
the defect is refused rather than supported.

#### P13-10 — the total-station walkthrough in Portuguese and Spanish (FR-952 stays partly met)

`rd01` ships `README.pt_BR.md` and `README.es.md`, and its English README points to them. With it, every
tutorial walkthrough is in all three languages.

The translation is held like the others:
- **Tier 1.** `TRANSLATED` names all five walkthroughs.
- **Tier 3.** `tests/qgis/test_tutorial.py::TestInEachLanguage` checks every dialog, input and choice name in
  each language, and the labels and datum choices the *Try this* names. It runs step 2 in that language, and
  the translation's quoted log line must be what GeoComp writes.

**Defects found.**
- **A quote that was not GeoComp's.** RD-01's walkthrough block-quoted "the two faces of the pointing from
  station 3 to station 2 disagree in distance by 1.000 m". That is a paraphrase of an older core message, not
  what step 2 logs. Every later walkthrough quotes GeoComp's words and has its tests check them. The English
  now quotes the log line, and a tier-3 test holds it there. The prose keeps naming the pointing and the round
  metre, which tier 1 checks, and that check now ignores line breaks.
- **A Spanish agreement error.** The message for that finding said *Los dos círculos …* and then *La media de
  las dos*. It now says *de los dos*. The tier-3 test found it, holding the Spanish quote to the log.

The Portuguese message calls the faces *as duas posições*, where the glossary's term is *pontaria* (PD/PI).
It was left alone: all six Portuguese strings about faces say *posições*, so changing one would make them
disagree. Whether to change all six is the native speakers' review's.

**Register.** Unchanged: 171 met, 5 partly met, 0 open. FR-952's row now says all five walkthroughs are
translated; what keeps it partly met is a GNSS tutorial and worked QGIS projects.

**Not done.** *Install tutorial dataset* still says "Start with README.md" in every language. The GNSS
sample's README is untranslated, and has never been held to the dialogs.

#### P13-11 — the GNSS sample held to the dialogs, in three languages, and the installer pointing to each

`rtklib-sample`'s README was the last walkthrough no test held to the dialogs. It was a numbered list rather
than steps that name their algorithms. It is now in the walkthrough form, and
`tests/qgis/test_gnss_sample.py` follows it through *Relative — Static*. `rnx2rtkp` is tier 4, so the engine
is the stand-in `tests/qgis/test_engine_runs.py` uses, answering with the solution RTKLIB-EX 2.5.1 gave for this
pair (`tests/data/rtklib/pos/xyz.pos`). The algorithm, its log and its outputs are GeoComp's own. The test checks:
- every dialog, input and choice name, and where each step is in the menu;
- the three log lines the README quotes, against the log;
- the 120 epochs and 117 fixed it states, from the log's summary line;
- the engine line, *Using RTKLIB-EX* `2.5.1`.

**Defects found.**
- **A retired log line.** The README said the log reports the navigation file *paired by fallback*. P12c-41
  replaced that wording with a sentence, and `tests/qgis/test_gnss_words.py` asserts the old words are gone. The
  README had kept them, quoted as GeoComp's.
- **The wrong place for the installer.** The README said *toolbox ▸ GeoComp ▸ Install tutorial dataset*. In
  the toolbox it is under *Project and data*, and in the menu under *GeoComp ▸ Project*.

Then the translations, `README.pt_BR.md` and `README.es.md`, held as every other walkthrough is, at tier 1 and
under each catalogue at tier 3. Two refinements to the tier-1 check came with them:
- The log's summary line, *120 epochs, 97.5% with resolved ambiguities*, is quoted as a block quote, like
  GeoComp's other words. A percentage with a decimal point in italics would read as untranslated prose.
- The decimal-point check skips comments. The licence header, `GPL-2.0-or-later`, is a name.

Every dataset now ships its README in all three languages, so *Install tutorial dataset* ends by naming the one
in the reader's language: *Comece pelo README.pt_BR.md*, *Empiece por el README.es.md*.
`tests/test_tutorial_translations.py::test_the_installer_sends_each_language_to_its_own_walkthrough` checks
that each translation names its own file, and that every dataset ships it.

**Register.** Unchanged: 171 met, 5 partly met, 0 open.

**Not done.** A GNSS tutorial: it needs RD-06's accuracy criterion met, or another redistributable dataset
with published coordinates. Worked QGIS projects. A native speaker's review of the walkthroughs.

#### P13-12 — worked examples as QGIS projects (FR-952 stays partly met)

`specs/20` §8 asks for *worked examples shipped as QGIS projects a student can open and run*. *Install
tutorial dataset* now writes one beside the files: `<dataset>.qgz`, holding the walkthrough as one
Processing model. Opened in QGIS, the model is in the toolbox under *Project models*. Its inputs default to
the installed files, its files go to `results/`, and its layers load when it finishes.

**How.**
- **Embedding.** The model is embedded the way QGIS's own project provider embeds one
  (`processing/modeler/ProjectProvider.py`): a `projectModels` element under `qgis`, holding the model's
  variant. `worked_examples.write_project` writes the element, and `read_models` reads it back the same way.
- **Written at install time.** The project is written when the dataset is installed, not shipped, because a
  model's inputs are absolute paths and only the installer knows where the files went.
- **Declared chains.** Each chain is declared as data (`Step`): the algorithm, the files it reads, the
  earlier outputs it takes and the values the walkthrough gives. Choices are indices from GeoComp's own
  order constants, so a model built in Portuguese chooses what one built in English does. Its labels are in
  the language of the installer's run.
- **Left out.** A step the README leaves to the reader is not in the model: the levelling loop's three
  benchmarks, which GeoComp refuses, and the dam's moved pillar.
- **Main thread.** The installer now runs on the main thread, where a `QgsProject` is built, as *Add print
  layout* already did. `_no_threading` gained a docstring now that two modules use it.
- **Declared outputs.** The installer declares its outputs: `OUTPUT_DIRECTORY`, `FILE_COUNT`, and the new
  `OUTPUT_PROJECT`. It had returned the first two without declaring them, so a model could not use them.

**Tests.** `tests/qgis/test_worked_examples.py` installs each of the six datasets and reads its project back
as QGIS does. For each, it checks:
- the project holds one model, whose steps are the README's, less installing the dataset;
- the model's inputs are the installed files;
- run with nothing changed, it writes its files to `results/` and gives the numbers the README states;
- the GNSS sample runs with the stand-in engine of P13-11.

`test_rd01s_model_draws_its_map` runs RD-01's model with temporary layers, as its dialog would, and finds the
five layers. It needs a QGIS whose field API is current, so it runs in CI and not on a 3.34 machine. The
listing of each tutorial's installed folder now includes the project and `results/`
(`tests/qgis/walkthrough.installed`).

**Register.** Unchanged: 171 met, 5 partly met, 0 open. FR-952's row now names the worked projects; a GNSS
tutorial is what keeps it partly met.

**Not done.**
- A GNSS tutorial.
- The project opens with no map: its layers appear when the model runs. A project with the inputs already on
  the map, and a print layout of the results, would teach more, and is not built.
- The model's labels are in the language of the installer's run. Changing QGIS's language afterwards leaves
  them as they were.

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
