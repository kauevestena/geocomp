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
agrees with complex-step differentiation to ≤ 1e-9 relative. No public core function can return a geodetic
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
| Cross-validation on **at least three** networks | **one of three** — see below |
| The engine manager installs on all three operating systems | **not met** — see below |
| With DynAdjust absent, everything else still works | **met** — the whole suite passes with no engine, and the algorithm fails with a message naming the remedy |
| Every **[C]** claim confirmed or corrected | **met** |
| FR-161, the *Adjust* format | **moves again** — see below |

**Cross-validation: one network, not three.** The `gnss-network` slice agrees to 0.047 mm
([`07-engine-dynadjust.md`](./07-engine-dynadjust.md) §6.1). The other two are blocked on the same missing
piece: **GeoComp has no geodetic↔geocentric conversion.** The in-house core works in a local metre frame and
DynAdjust in a geocentric one; for a network of GNSS baselines and points those coincide, because both
observation equations are differences of coordinates and the frame cancels. For a levelling network, or any
terrestrial one, they do not — the core's third component would be geocentric *Z* where DynAdjust's is
ellipsoidal *height*, and the two differ by thousands of kilometres. The conversion is a self-contained piece
of work (ellipsoid definitions, the closed-form inverse, its own reference cases) and belongs with the
geodetic-computations work rather than bolted onto the end of this phase.

**The engine manager installs nothing** because there is nothing that can honestly be pinned. ADR-0003 asks
for a downloaded binary verified against a digest; Geoscience Australia publishes Windows build artefacts and
a `:latest` Docker Hub tag under a personal namespace, neither of which is a versioned, digest-addressable
release. `PINNED` in `engines/manager.py` is therefore empty, and the `engine` CI job builds DynAdjust from
an immutable commit instead — which is pinnable and verifiable, and is what the fixtures and this spec were
checked against. The install path itself is implemented and tested against synthetic archives; what is
missing is a real release to point it at.

**Independent validation, from a different direction.** The cross-validation criterion is specifically
*against DynAdjust*, and one network is what it got. The in-house core is nonetheless no longer checked only
against itself: `io/krumm.py` and `tests/test_krumm_corpus.py` (RD-11) reproduce **33 published network
adjustments** — 1D, 2D and 3D, free and constrained — to 0.05 mm, from Ghilani, Niemeier, Benning, Wolf,
Strang and Borre and others by name and page
([`22-reference-data-sources.md`](./22-reference-data-sources.md) §2.2). That closes the citation gap
RD-02, RD-03 and RD-04 have carried since P1, and it reaches the plane and levelling networks DynAdjust
cannot take from GeoComp at all. It does **not** satisfy this criterion, which is about the engine.

**FR-161 moves again**, to the phase that can obtain an *Adjust*-format example file with its published
answer. P6 could not, for the reason P5 recorded: neither a specification of the format nor an example file
is publicly available, and
[`17-persistence-and-interoperability.md`](./17-persistence-and-interoperability.md) §5.2 states what would
unblock it. It is not to be implemented from a guess, and moving it twice with the reason recorded is the
honest outcome rather than a parser nobody can validate.

---

## P7 — GNSS

**Goal.** RINEX in, baselines with covariance out.

**Specs.** [`08-engine-rtklib.md`](./08-engine-rtklib.md) · [`11-module-gnss.md`](./11-module-gnss.md)

**Delivers.** `io/rinex.py` header scanning; session discovery; product resolution with caching, configurable
services and credentials through the QGIS authentication system; the `rnx2rtkp` configuration writer, runner
and `.pos` parser; batch processing; baseline construction with independent-set identification; quality
reporting; comparative configuration testing; the reference station database.

**Closes.** FR-063, FR-164, FR-350, FR-351, FR-352, FR-353, FR-354, FR-355, FR-356, FR-357, FR-358, FR-359,
FR-600, FR-601, FR-602, FR-603, FR-604, NFR-010

**Exit.** A static relative session over RD-06 reproduces the published coordinates within tolerance.
Baselines reach DynAdjust as G measurements with their 3×3 covariance intact. The independent baseline subset
is correctly identified. Antenna height reduction applied twice is prevented. A batch with one broken session
completes and reports it. No credential appears in any log, config, provenance record or export. PPP modes
show the FR-604 notice.

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

**Closes.** FR-830, FR-831, FR-832, FR-833, FR-834, FR-835, FR-836, FR-837, FR-838, FR-903, FR-932

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
