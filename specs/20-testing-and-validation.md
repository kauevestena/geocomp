# 20 — Testing and validation

**Status:** Draft
**Requirements covered:** FR-950…FR-955, NFR-002, NFR-007, NFR-011; the acceptance criteria of every other
document.
**Source:** O9, O10, O11; tex §Comparação com softwares comerciais; §Estudos de caso e avaliação.

---

## 1. Test tiers

| Tier | Needs | Runs | Purpose |
|---|---|---|---|
| **T1 — Core unit** | Python + NumPy only | Every commit, seconds | The mathematics. No QGIS, no engines (NFR-002, NFR-011) |
| **T2 — Reference** | T1 | Every commit | Reproduce published results (§3), RD-11 among them |
| **T3 — QGIS integration** | QGIS runtime | Every commit, containerised | Algorithms, layers, provider, menu, i18n |
| **T4 — Engine integration** | Pinned engine binaries | Every commit where available; nightly in full | Real input generation, real runs, real parsing |
| **T5 — Cross-validation** | T1 + T4 | Nightly and pre-release | In-house core vs DynAdjust (§4) |
| **T6 — Commercial comparison** | Third-party licences | Per release, manual | The proposal's O9 protocol (§5) |

**T1 is the tier that must be fast and comprehensive.** It is where a wrong Jacobian or a sign error is
caught, and it is why `core/` is QGIS-free.

## 2. Structural checks in CI

Beyond tests, checks that enforce the specifications' structural rules:

| Check | Enforces |
|---|---|
| No `import qgis` / `PyQt` under `core/` | NFR-002, [`03-architecture.md`](./03-architecture.md) §1 |
| No user-facing string literal outside a translation call; no concatenation inside one | FR-091, [`18-i18n-and-profiles.md`](./18-i18n-and-profiles.md) §2 |
| String extraction produces no new untranslated strings without `.ts` updates | FR-090 |
| Every menu item maps to a registered algorithm and vice versa | FR-005 |
| Every algorithm has a translated `shortHelpString()` documenting every parameter with units | FR-090, [`16-processing-provider.md`](./16-processing-provider.md) §8 |
| Every public core function returning a geodetic value returns a `Quantity`-bearing type | FR-200 |
| Every message template interpolates only context keys its raising site supplies, has one `%n` per key, and names a code something raises | NFR-006, [`18-i18n-and-profiles.md`](./18-i18n-and-profiles.md) §2 |
| Every requirement ID in `02-requirements.md` appears in exactly one `ROADMAP.md` phase | [`README.md`](./README.md) |
| Relative links between spec documents resolve | — |
| Locale round trip: every output format written under a comma-decimal locale reads back under a period-decimal one | FR-095 |
| No credential appears in any log, config, provenance record or export | NFR-010 |
| Basic and Advanced modes produce identical numeric results with defaults, for every algorithm | FR-071 |
| Every acceptance criterion of every specification has one row in §10's register, and every test a row cites exists | §9 criterion 8 |

## 3. Reference datasets (FR-950)

Datasets with an independently known correct answer. Each has an id, a documented provenance, a licence
permitting redistribution, and an expected-results file. What is still missing — here and in every module's
criteria — is registered in [`23-wanted-reference-data.md`](./23-wanted-reference-data.md).

| Id | Dataset | Validates | Status |
|---|---|---|---|
| **RD-01** | `topo_test/` — the project author's total-station triangle (3 stations, PD/PI, distances, zenith angles) | Face reduction, corrections, basic reductions, small-network adjustment, the field-mapping importer | **In repository** |
| **RD-02** | Covariance-propagation reference cases, each validated three ways: a hand-derived closed form, the module's first-order propagation, and a derivative-free Monte Carlo simulation | [`05-uncertainty-and-covariance.md`](./05-uncertainty-and-covariance.md) | **Implemented** (P1). See the note below |
| **RD-03** | Network adjustments with a known truth — 1D levelling, 2D trilateration, 2D triangulateration, free and constrained | [`06-adjustment-core.md`](./06-adjustment-core.md) | **Implemented** (P2), in `tests/networks.py`. Same citation note as RD-02 |
| **RD-04** | Levelling field books generated from known heights, all three schemes, plus a loop with an injected blunder | [`10-module-levelling.md`](./10-module-levelling.md) | **Implemented** (P4), in `tests/reference_levelling.py`. Same citation note as RD-02 and RD-03 |
| **RD-05** | DynAdjust's own example datasets | [`07-engine-dynadjust.md`](./07-engine-dynadjust.md) | From upstream |
| **RD-06** | GNSS reference data with published official coordinates (IBGE, NGS, Geoscience Australia) | [`08-engine-rtklib.md`](./08-engine-rtklib.md), [`11-module-gnss.md`](./11-module-gnss.md) | **In repository**, `tests/data/rd06/` and `tests/test_rd06.py`: NGS GODN–GODS, two days; **accuracy criterion unmet**, enforced by engine CI — [`22`](./22-reference-data-sources.md) §5 |
| **RD-07** | Gravimetric network with a published solution | [`12-module-gravimetry.md`](./12-module-gravimetry.md) | **Assembled (P8a)** — a CG-5 survey's firmware tides, pyGrav's published solution reproduced, ETERNA, and USGS's synthetic surveys with published truth; [`22`](./22-reference-data-sources.md) §5.6. No published calibration-table example |
| **RD-08** | Multi-epoch monitoring series with known displacements — a published deformation example, plus synthetic data with injected motion | [`14-multi-epoch-monitoring.md`](./14-multi-epoch-monitoring.md) | **Synthetic half in repository (P10a)**, `tests/monitoring_network.py` and `tests/test_monitoring.py`; the published half is not reachable here — [`22`](./22-reference-data-sources.md) §5.3 |
| **RD-09** | The RD-03 networks with a blunder of known size injected at a known place | Data snooping, reliability | **Implemented** (P2), in `tests/networks.py` |
| **RD-10** | Field campaign data collected by students (`tex §Participação dos alunos`) | End-to-end, real-world | Project activity |
| **RD-11** | Krumm's *Geodetic Network Adjustment Examples* — 61 networks from a dozen textbooks, 45 with the adjusted coordinates as published | [`06-adjustment-core.md`](./06-adjustment-core.md), and the citation RD-02/03/04 lacked | **Implemented** (T2), in `tests/data/krumm/` and `tests/test_krumm_corpus.py`. **36 reproduced to 0.05 mm**, two of them combined GNSS networks (P9a). Vendored from GNU Gama at a pinned commit, on the terms in [`22`](./22-reference-data-sources.md) §2.3 |
| **RD-12** | Five surveying networks over one set of control — twelve free stations, three traverses and a triangulateration — published in the *Adjust* format, CC BY 4.0 | FR-161's reader and writer, the weighted-constraint path (FR-232), and blunder detection | **Implemented** (T2), in `tests/data/adjust/` and `tests/test_adjust_corpus.py`. Converted from `.Adat` into GeoComp's own serialisation on the terms in [`22`](./22-reference-data-sources.md) §4; **two defects in the publication are recorded rather than repaired**, and one is vendored twice |

**RD-01 is special, and carries two known defects.** It is the author's own prototype data and it exercises
the whole first vertical slice. It contains a real transcription blunder — a 1.000 m face-pair distance
discrepancy ([`09-module-total-station.md`](./09-module-total-station.md) §2.1) — which becomes a detection
test. And its `processed_data.csv`, produced by the prototype notebook, carries a **180° error** in one
reduced direction, caused by the arithmetic-mean face reduction the same section documents. Both are
assets rather than problems: a reference dataset whose expected output is known to be wrong in two specific,
independently verifiable places tests more than a clean one would.

The 180° error is established two ways, not asserted: the published value gives a triangle whose interior
angles sum to 38.24°, and implies a 2–3 distance of 4.43 m against 24.35 m measured. Both checks are in
`tests/test_reference_total_station.py`.

RD-01 ships with the plugin as a tutorial dataset (FR-952), with both defects documented — a tutorial in
which the software catches two real errors in real data teaches more than one in which nothing is wrong.

**RD-02, RD-03 and RD-04 note — validation complete, citation now made by RD-11.** The cases implemented in
`tests/test_reference_propagation.py`, `tests/networks.py` and `tests/reference_levelling.py` are *not*
transcriptions from Ghilani or Gemael; they are reference cases built from the geodetic operations GeoComp performs, with a known truth.

RD-02 agrees with a hand-derived closed form *and* with a Monte Carlo simulation that uses no derivative at
all. That triangle is stronger evidence than matching a printed answer — a transcription error in a book's
input value would be invisible, whereas the Monte Carlo check catches a sign error the closed form and the
implementation could share.

RD-03 has no closed form for most of its quantities, so it is validated against the **identities of least
squares**, which hold for every network rather than for one: redundancy numbers sum to the degrees of
freedom; a free and a constrained solution of the same data agree on residuals and on σ̂₀²; design simulation
reproduces the adjustment's covariance to machine precision when both are evaluated at the same coordinates;
every analytic Jacobian matches a numerical derivative — complex-step, or central differences where the
function is not complex-safe ([`05-uncertainty-and-covariance.md`](./05-uncertainty-and-covariance.md)
§2.2). Several of these would catch errors that
matching a printed answer would not.

What remains for both is *citation*: transcribing the published worked examples so the project can state
agreement with the standard references by name, which matters for the commercial-comparison protocol (§5)
and for the teaching material (FR-952).

**The citation is now made — see RD-11.** GNU Gama redistributes the 61 example networks of Krumm's
*Geodetic Network Adjustment Examples* (Universität Stuttgart, 2020), **45 of them with the adjusted
coordinates as published**, each citing the textbook it came from by edition and page.
`geocomp/io/krumm.py` reads them and **36 reproduce to 0.05 mm** — Ghilani, Niemeier, Benning, Wolf, Strang
and Borre, Grossmann, Höpke, Lother and Strehle, Carosio, Weiss and Blankenbach among them. The full result
and the reasons for every refusal are in
[`22-reference-data-sources.md`](./22-reference-data-sources.md) §2.2.

RD-04 goes one step further than either. Its field books are **generated from known heights by inverting
the very equations under test**: a staff reading is `r = Z - H + c·d`, so a line that fails to recover the
height it was built from has a sign error, exactly locatable, in the noiseless case. That is stronger than
matching a printed answer, where a transcription error in the book's input is invisible. What it cannot do
is confirm agreement with the standard references *by name*, which is what the citation is for.

Synthetic datasets (RD-09) matter as much as published ones: only with synthetic data is the true answer
known *exactly*, so blunder detection, reliability and deformation analysis can be tested against ground
truth rather than against another computation.

## 4. Cross-validation (T5)

The same network adjusted by the in-house core and by DynAdjust, compared field by field.

| Quantity | Tolerance |
|---|---|
| Adjusted coordinates | 0.1 mm |
| Residuals | 0.1 mm, or 0.01″ for angles |
| σ̂₀² | 1e-6 relative |
| Degrees of freedom | Exact |
| Error ellipse semi-axes | 0.1 mm |
| Ellipse orientation | 0.01° |

These are tight deliberately. Two correct implementations of least squares on identical inputs agree to
near machine precision; a disagreement at millimetre level is a real difference in method or a real defect,
and either way it must be understood, not tolerated.

**Every discrepancy above tolerance is investigated and documented before release.** Where it stems from a
genuine methodological difference — a different refraction model, a different datum convention — that
difference is documented in the specification, not tuned away.

## 5. Comparison with commercial software (FR-951)

The proposal makes this a student activity with four stated aims: validating results, identifying and
explaining discrepancies, documenting equivalence, and comparative learning
(`tex §Comparação com softwares comerciais`).

**Protocol:**

1. **Fix the dataset.** A documented dataset, with its own id, unchanged between systems.
2. **Record the configuration of both systems** completely — models, tolerances, datum, constraints,
   stochastic model. Most apparent discrepancies are configuration differences.
3. **Compare a fixed field list**: adjusted coordinates, σ̂₀², degrees of freedom, residuals, error ellipses,
   positional uncertainty, and test decisions.
4. **Classify each discrepancy** as: within numerical tolerance · a documented methodological difference ·
   a configuration difference · **an unexplained difference**.
5. **Investigate every unexplained difference** until it is reclassified. An unexplained difference is a
   defect somewhere, and it is not acceptable to leave it unexplained in a published comparison.
6. **Publish the result** — dataset, configurations, comparison table, and the explanation of every
   difference — as a technical report or paper (`tex §Comparação com softwares comerciais`).

Collaboration routes the proposal names: partner companies, other institutions, vendor academic licences,
and published official reference data from IBGE, NGS/NOAA and Geoscience Australia.

**GeoComp's job is to make this cheap**: a comparison export producing exactly the fields of step 3, in a
form that lines up against a commercial package's output.

## 6. Numerical tolerance policy

| Comparison | Tolerance |
|---|---|
| Against an analytic result | 1e-12 relative |
| Against complex-step differentiation (Jacobians) | 1e-9 relative |
| Against central differences (Jacobians of functions that are not complex-safe) | 1e-7 relative |
| Against a published worked example | The precision printed in the source |
| Between the two engines (§4) | The table in §4 |
| Against commercial software | Documented per comparison; unexplained differences are defects |
| Reproducibility of a run | **Bit-identical** (NFR-007) |

Bit-identical reproducibility requires: deterministic iteration order, explicit and stable observation
ordering, no reliance on set or dictionary ordering for numeric outcomes, and pinned engine versions
recorded in provenance.

**RD-06's known discrepancy stays visible.** The frozen official sources, the coordinate transcription,
the antenna-epoch guard and the sheets' own phase-centre self-consistency are checked offline on every
commit. With `rnx2rtkp` and the test-only Hatanaka decompressor available, `tests/test_rd06.py` runs the
current development code against every configuration and checks full-day coverage and byte
reproducibility. The single primary accuracy assertion is a strict, exception-specific expected failure
locally; engine CI uses `--runxfail` and **fails while the criterion remains unmet**. Processing errors
are not expected failures. The standalone `scripts/check_rd06.py` also returns failure for the accuracy
mismatch and retains evidence.

**The GNSS criterion is loop closure and repeatability, not agreement with a published coordinate**
(maintainer's decision, 24 September 2026). RD-06 is met when both of these hold, each at **2 mm per
component**:

| Criterion | What it is | Measured |
|---|---|---|
| **Loop closure** | The GODN–GODE–GODS triangle, every leg processed independently, summed round the circuit | **0.245 mm** on 2025-001 and **0.787 mm** on 2025-002 over a 282 m perimeter; worst single component 0.6 mm |
| **Repeatability** | Robust scatter of the six-hour sub-sessions of the judged baseline | **0.613 / 0.318 / 0.992 mm** in east, north and up |

**Why the published comparison stopped being a criterion.** It was never measuring this software.
Fourteen independent same-antenna CORS pairs of 22 to 46 m, every one resolving its own antenna *and*
radome exactly, miss their published ITRF2020 coordinates by a median worst component of 5.1 mm and
**none reaches 1 mm**, while the same estimator repeats to well under a millimetre. The disagreement is
fixed per pair across days, differs between pairs, and does not move with the elevation mask, so it
belongs to the reference or the site rather than to the processing — [`22`](./22-reference-data-sources.md)
§5.4 has the measurement and its limits. A tolerance that no clean pair can meet is a statement about
NGS, and a green check ought to be a statement about GeoComp. The comparison is still **run and
reported** on every engine build, and a test asserts the discrepancy stays the size §5 describes, so
the evidence does not quietly disappear; it simply no longer decides anything.

**Why both, and not closure alone.** An error common to every baseline at one station enters a loop
twice with opposite signs and cancels, so a triangle can close perfectly while the whole site is
displaced. 2025-001 demonstrates it: that day carries the contaminated hour §5.1 attributes and still
closes to a quarter of a millimetre. Repeated independent sub-sessions do see what closure cannot, so
the criterion requires both and `tests/test_rd06.py` asserts the blind spot rather than describing it.

**Why these numbers.** 2 mm is about three times the worst component either measurement produces,
which leaves room for a different site or receiver without leaving room for a defect. The closure
limit is per component rather than on the magnitude, because a magnitude hides one bad axis behind two
good ones and the axis is what a reader needs in order to act. Repeatability is judged on the
**six-hour** spans because that is the shortest length with enough solutions per day for the statistic
to mean anything and enough time for the ambiguities to resolve, and on the **robust** scatter because
a criterion a single known-bad hour can fail is measuring that hour rather than the estimator.

## 7. CI matrix

| Axis | Values |
|---|---|
| OS | Linux (primary), Windows, macOS (NFR-003) |
| QGIS | The 4.x series: current 4.x LTR once one exists, current stable until then (NFR-001, [`adr/0007-qgis-4-minimum.md`](./adr/0007-qgis-4-minimum.md)) |
| Python | As shipped by the targeted QGIS versions |
| Engines | Present (T4, T5) and absent (asserting graceful degradation, FR-306) |
| SciPy | Present and absent (asserting the NumPy-only fallback, [`03-architecture.md`](./03-architecture.md) §3.7) |

The **engines-absent** and **SciPy-absent** rows are not optional. FR-306 and the fallback path are
requirements, and an untested fallback is a fallback that does not work.

## 8. Documentation and community (FR-952…FR-955)

- **Tutorials** for each module, each built on a reference dataset, in all three languages, published as
  project documentation.
- **Worked examples** shipped as QGIS projects a student can open and run.
- **Contribution guide** covering the specification process ([`README.md`](./README.md)), the tiers above,
  and the structural checks — so a contributor knows what "done" means before opening a pull request
  (FR-954).
- **Upstream defect reporting** (FR-955): where a failure is in DynAdjust or RTKLIB, GeoComp packages the
  exact inputs, configuration, command line and output that reproduce it, so the report is actionable. The
  proposal names this feedback loop as an expected result of the project.

## 9. Acceptance criteria

1. T1 runs in under 60 seconds with no QGIS and no engines installed.
2. Every structural check in §2 is implemented and failing them fails the build.
3. Every reference dataset in §3 has an expected-results file and a passing test.
4. Cross-validation (§4) passes on at least three networks of differing type and size.
5. The CI matrix (§7) runs, including the engines-absent and SciPy-absent rows.
6. Coverage of `core/` is measured and reported per release; every public function has at least one test.
7. A comparison export producing the §5 step-3 fields exists and is documented.
8. Every acceptance criterion in every other specification document has a corresponding automated test, or a
   documented reason why it must be manual. *(The register, §10, since P12c.)*

## 10. Acceptance register (P12c)

**Every acceptance criterion in specifications 05 to 21 has exactly one row here**, saying whether it is met
and what shows it — criterion 8 above, made checkable. `tests/structural/test_acceptance_register.py` reads
each document's acceptance section and this table, and fails when a criterion has no row or two, when a row
names a criterion that does not exist, when a **met** row cites no test, when a row that is not met says
nothing about why, or when a cited test, file or class does not exist. It cannot tell whether a test proves
what its row claims; that is what review is for, and a row is changed in the same commit as the test it cites.

| State | Means |
|---|---|
| **met** | A test that runs in CI asserts the criterion as written. Tier 4 tests run in the `engine` workflow, and tests needing QGIS ≥ 3.38 run only on the CI image |
| **partly met** | Part of the criterion is asserted; the row names the part that is not |
| **open** | Not met; the row says what is missing and where it waits — often a `W-` item of [`23`](./23-wanted-reference-data.md) |
| **manual** | Cannot be automated; the row says why and how it is checked instead |

**State at the audit (P12c, 2 October 2026): 90 met, 31 partly met, 12 open, 2 manual, of 135.** The audit
found that several criteria believed met were met in part. A test existed near each one but did not assert
what the criterion says, and nothing compared the two until this table. The rows say which part.

| Spec | # | Criterion, abridged | State | Evidence, or what is missing |
|---|---|---|---|---|
| 05 | 1 | Jacobians against numerical derivatives | **met** | `tests/test_adjustment.py::TestJacobians` (central differences: the observation equations are not complex-safe), `tests/test_uncertainty.py::TestJacobianVerification`, `tests/test_geodesy.py::TestJacobians`, `tests/test_differentiation.py` |
| 05 | 2 | Propagation reproduces Ghilani and Gemael | **partly met** | RD-02 is validated three ways, closed form, first order and Monte Carlo (`tests/test_reference_propagation.py`). Published standard deviations are reproduced through RD-11 (`tests/test_krumm_corpus.py::test_the_published_standard_deviations_are_reproduced_too`). No printed *propagation* example is transcribed: Gemael waits on W-04, and the books are not transcribed from memory |
| 05 | 3 | A pre-processing chain preserves the combined propagation | **partly met** | The identity holds in general (`tests/test_uncertainty.py::TestRigorousPropagation::test_propagation_composes`). No test runs the real total-station chain against a single propagation through it |
| 05 | 4 | No geodetic value without an uncertainty | **met** | `tests/structural/test_no_bare_geodetic_floats.py` |
| 05 | 5 | Approximate results name their strategies in export, report and provenance | **partly met** | The report does (`tests/qgis/test_adjustment_report.py::TestItIsDefensible::test_an_approximate_solution_names_its_strategies`). The export names them per observation but not for the solution, and `Provenance` records the mode without the strategies |
| 05 | 6 | Correlated operands refused by the scalar path | **met** | `tests/test_uncertainty.py::TestCorrelationGuard` |
| 06 | 1 | Ghilani and Gemael network examples reproduced | **partly met** | Ghilani by name through RD-11, coordinates to 0.05 mm (`tests/test_krumm_corpus.py::test_the_published_coordinates_are_reproduced`); the corpus publishes coordinates, so residuals, σ̂₀² and ellipses are not compared against print. Gemael waits on W-04 |
| 06 | 2 | Free and constrained solutions consistent | **met** | `tests/test_adjustment.py::TestFreeNetworkAndDatum` |
| 06 | 3 | A 2 × MDB blunder found on the first pass | **met** | `tests/test_statistics.py::TestDataSnooping::test_a_blunder_at_twice_the_mdb_is_located_on_the_first_pass` |
| 06 | 4 | Rank deficiency diagnosed, never a number | **met** | `tests/test_adjustment.py::TestRankDiagnosis` |
| 06 | 5 | Pre-analysis reproduces the adjusted Σₓ | **met** | `tests/test_statistics.py::TestPreAnalysis` |
| 06 | 6 | In-house core and DynAdjust agree | **met** | Tier 4: `tests/test_dynadjust_crossvalidation.py::TestTheTwoEnginesAgree`, `tests/test_dynadjust_pipeline.py::TestAProjectedNetworkCrossValidates`, `tests/test_dynadjust_pipeline.py::TestATerrestrialNetworkCrossValidates` |
| 06 | 7 | Every statistic with critical value, confidence and decision | **met** | `tests/test_statistics.py::TestGlobalTest::test_the_statistic_carries_both_critical_values`, `tests/test_statistics.py::TestDataSnooping::test_the_distribution_used_is_reported` |
| 07 | 1 | DynaML validates and imports without warnings, every mapped type | **partly met** | Imports are checked against `dnaimport`'s own counts on three networks: GNSS, levelling, and directions, zenith angles and slope distances (`tests/test_dynadjust_pipeline.py::TestAgainstARealEngine::test_an_unparsed_measurement_file_is_caught_despite_a_zero_exit`, `tests/test_dynadjust_pipeline.py::TestATerrestrialNetworkCrossValidates`). Not every type of §4.2 passes through `dnaimport`, and nothing validates against the schema |
| 07 | 2 | A baseline cluster round-trips at full precision | **met** | `tests/test_dynaml_writer.py::test_the_covariance_survives_to_full_double_precision`, `tests/test_gnss_to_dynadjust.py::TestTwoBaselinesBecomeAnXCluster` |
| 07 | 3 | The pipeline runs end to end to a Solution | **met** | Tier 4: `tests/test_dynadjust_pipeline.py::TestAgainstARealEngine::test_the_whole_pipeline_reaches_a_solution` |
| 07 | 4 | Parsed results match the printed files | **met** | `tests/test_dynadjust_output.py`, against files a real DynAdjust wrote; tier 4 re-runs them (`tests/test_dynadjust_output.py::TestTheFixtureDriftGuard`) |
| 07 | 5 | Cross-validation passes | **met** | As 06.6 |
| 07 | 6 | Every **[C]** confirmed | **manual** | A documentation audit, not a behaviour; discharged in P6 against upstream at a pinned commit, recorded in [`07`](./07-engine-dynadjust.md)'s header |
| 07 | 7 | Without DynAdjust, everything else works | **met** | `tests/qgis/test_engine_algorithms.py::TestAdjustWithoutTheEngine::test_it_says_how_to_get_dynadjust_rather_than_failing_obscurely`; the whole suite runs without engines in `.github/workflows/test.yml` |
| 08 | 1 | Session discovery over RINEX 2 and 3, compressed, mismatches reported | **met** | `tests/test_gnss_discovery.py`, `tests/test_rinex.py` |
| 08 | 2 | A configuration fed back through `-k` reproduces the run bit for bit | **partly met** | The file written is the one the engine read (`tests/test_rtklib_engine.py::TestAgainstTheRealEngine::test_the_written_configuration_is_what_the_engine_read`); no test re-runs it and compares the output |
| 08 | 3 | `.pos` parsing round-trips, every format | **met** | `tests/test_pos_reader.py::TestEveryFormatReads`, `tests/test_pos_reader.py::TestTheFormatsAgree` |
| 08 | 4 | Covariance reaches a G measurement intact | **met** | `tests/test_gnss_to_dynadjust.py::TestOneBaselineBecomesAGMeasurement` |
| 08 | 5 | One broken session does not abort a batch | **met** | `tests/test_gnss_batch.py::TestOneBadSessionDoesNotAbortTheBatch` |
| 08 | 6 | Products from cache on a second run, named in provenance | **met** | `tests/test_gnss_products.py::TestResolution`, `tests/test_gnss_products.py::TestProvenance` |
| 08 | 7 | No credential anywhere GeoComp writes | **met** | `tests/test_gnss_products.py::TestCredentials`, `tests/qgis/test_product_download.py` |
| 08 | 8 | A PPP mode shows the FR-604 notice | **partly met** | The notice is written into the Absolute algorithms' help and pushed at the start of their runs (`algorithms/gnss/process.py`); no test asserts it |
| 09 | 1 | RD-01 reproduces, except where the prototype is wrong | **met** | `tests/test_reference_total_station.py::TestReproduction`, `tests/test_reference_total_station.py::TestTheOneHundredAndEightyDegreeError` |
| 09 | 2 | Both RD-01 defects caught | **met** | `tests/test_reference_total_station.py::TestTheDistanceBlunder`, `tests/test_reference_total_station.py::TestTheOneHundredAndEightyDegreeError` |
| 09 | 3 | The wrap case | **met** | `tests/test_reference_total_station.py::TestTheWrapCase::test_the_case_the_spec_names` |
| 09 | 4 | Injected collimation and index error recovered | **met** | `tests/test_reference_total_station.py::TestInjectedInstrumentalErrors` |
| 09 | 5 | Traverse against a published worked example | **open** | Waits on W-07. The traverse paths are tested against constructed truth (`tests/test_survey_computations.py::TestTraverse`), not against print |
| 09 | 6 | The danger circle detected, not solved | **met** | `tests/test_survey_computations.py::TestTheDangerCircle` |
| 09 | 7 | A triangulateration free and constrained is consistent | **partly met** | The consistency check runs on RD-03's trilateration (`tests/test_adjustment.py::TestFreeNetworkAndDatum`), not on its triangulateration |
| 09 | 8 | Every output carries an uncertainty and a mode | **met** | `tests/structural/test_no_bare_geodetic_floats.py::TestTechniqueModuleReturns` |
| 09 | 9 | RD-01 through the menu gives styled layers with ellipses | **partly met** | RD-01 runs the chain through Processing to a solution with ellipses (`tests/qgis/test_totalstation_algorithms.py::TestTheWholeChain`); styled layers are asserted for the analysis adjustment (`tests/qgis/test_result_layers.py::TestTheStylesLoad`), not for RD-01's |
| 10 | 1 | Three schemes reproduce published examples | **open** | Waits on W-05. RD-04's field books are generated by inverting the equations under test (`tests/test_levelling.py::TestEqualSights`, `tests/test_levelling.py::TestExtremeSights`, `tests/test_levelling.py::TestReciprocalSights`), which proves correctness but not agreement by name |
| 10 | 2 | Loop misclosure and tolerance against a worked example, failing case included | **partly met** | The failing case is asserted (`tests/test_levelling.py::TestClosures`); agreement with a published example waits on W-05 |
| 10 | 3 | Extreme sights are a correlated cluster that helps | **met** | `tests/test_levelling.py::TestExtremeSights::test_the_correlation_makes_a_derived_difference_better_not_worse` |
| 10 | 4 | Length and setup weighting consistent, and with a published example | **partly met** | Consistent with each other (`tests/test_levelling.py::TestTheNetwork::test_length_and_setup_weighting_agree_on_the_heights`); a network published under both waits on W-06 |
| 10 | 5 | Geometric and trigonometric combined, variance components by technique | **open** | Variance components by group are tested on GNSS and total station (`tests/test_variance_components.py::TestTheEstimator`); no test combines the two levelling techniques |
| 10 | 6 | Mixed heights without a geoid refused; with one, converted and named | **met** | `tests/test_levelling.py::TestHeightSystems` |
| 10 | 7 | Every output carries an uncertainty and a mode | **met** | `tests/test_levelling.py::TestEveryOutputCarriesAnUncertainty` |
| 10 | 8 | The tolerance gate and the orthometric correction | **met** | `tests/test_levelling.py::TestTheToleranceGate`, `tests/test_levelling.py::TestOrthometricCorrectionOfLines`, `tests/qgis/test_levelling_algorithms.py` |
| 11 | 1 | Mixed RINEX sessions with mismatches reported | **met** | `tests/test_gnss_discovery.py` |
| 11 | 2 | A static session reproduces a published reference within tolerance | **met** | Tier 4, on the criterion as P7e restated it: loop closure and repeatability ([`20`](./20-testing-and-validation.md) §6), `tests/test_rd06.py::TestTheTriangleCloses`. Agreement with the published coordinate is reported, not judged (`tests/test_rd06.py::test_the_published_coordinate_comparison_is_reported_not_judged`) |
| 11 | 3 | The independent subset identified | **met** | `tests/test_gnss_baselines.py::TestTheIndependentSubset` |
| 11 | 4 | A baseline reaches a G measurement intact | **met** | As 08.4 |
| 11 | 5 | Antenna height reduced twice is prevented | **met** | `tests/test_gnss_baselines.py::TestAntennaHeightIsRemovedOnce` |
| 11 | 6 | Two configurations compared with significance | **met** | `tests/test_gnss_comparison.py` |
| 11 | 7 | A base station in another frame is transformed, with a record | **partly met** | The mismatch is refused (`tests/test_gnss_stations.py`); the P9a transformation is not applied in the base-station path |
| 11 | 8 | An Absolute mode shows the FR-604 notice | **partly met** | As 08.8: written, not asserted |
| 12 | 1 | Scale, tide and drift against worked examples | **partly met** | Tide against the CG-5 firmware (`tests/test_gravimetry_readings.py::TestTheTide`) and ETERNA (`tests/test_gravimetry_tides.py::TestAgainstEterna`); drift against pyGrav (`tests/test_rd07.py::TestGeoCompIsThePublishedModel`). Scale has no published example: W-02 |
| 12 | 2 | Injected drift recovered with the truth | **met** | `tests/test_gravimetry_network.py::TestTheTruthIsRecovered` |
| 12 | 3 | Pre-corrected and joint drift, consistent and different where they should be | **met** | `tests/test_gravimetry_network.py::TestPreCorrectionAgainstJointEstimation` |
| 12 | 4 | A datum defect of one, reported | **met** | `tests/test_gravimetry_network.py::TestTheDatum` |
| 12 | 5 | Absolute values weighted, not fixed | **met** | `tests/test_gravimetry_network.py::TestTheDatum::test_absolute_values_are_weighted_not_fixed` |
| 12 | 6 | Uncheckable observations flagged prominently | **met** | `tests/test_gravimetry_network.py::TestUncheckableObservationsAreNamed`, `tests/qgis/test_gravimetry_algorithms.py` |
| 12 | 7 | SI in storage, the configured unit on display | **met** | `tests/test_gravimetry_network.py::TestEveryOutputCarriesItsUncertainty::test_values_are_stored_in_si`, `tests/qgis/test_gravimetry_algorithms.py` |
| 12 | 8 | Every output carries an uncertainty and a mode | **met** | `tests/test_gravimetry_network.py::TestEveryOutputCarriesItsUncertainty` |
| 13 | 1 | A published combined example within tolerance | **met** | Caspary through RD-11 (`tests/test_krumm_corpus.py::test_the_published_standard_deviations_are_reproduced_too`) |
| 13 | 2 | No geoid refuses; with one, it is named | **met** | `tests/test_geocentric_frame.py::TestHeightSystems`, `tests/qgis/test_adjustment_report.py::TestTheGeoidModelIsNamed` |
| 13 | 3 | A mis-scaled technique's factor recovered | **met** | `tests/test_variance_components.py::TestTheEstimator::test_a_mis_scaled_technique_is_recovered` |
| 13 | 4 | Two frames transformed with a record; irreconcilable refused | **met** | `tests/test_integration.py::TestCriterion4Frames` |
| 13 | 5 | Clusters survive intact | **met** | `tests/test_integration.py::TestCriterion5Clusters` |
| 13 | 6 | Gravity routed in-house, with the reason | **met** | `tests/test_integration.py::TestCriterion6Routing` |
| 13 | 7 | Per-technique breakdowns in the report | **met** | `tests/test_integration.py::TestCriterion7Breakdown`, `tests/qgis/test_adjustment_report.py::TestTheTechniquesSection` |
| 13 | 8 | Three techniques, one solution | **met** | `tests/test_integration.py::TestCriterion8ThreeTechniques` |
| 14 | 1 | Frames transformed with a record; incompatible datums refused | **met** | `tests/test_monitoring.py::TestCriterion1Frames` |
| 14 | 2 | A solution without an epoch refused | **met** | `tests/test_monitoring.py::TestCriterion2Epoch` |
| 14 | 3 | A published deformation example reproduced | **open** | Waits on W-01: no published example is reachable ([`22`](./22-reference-data-sources.md) §5.3) |
| 14 | 4 | An injected displacement found, no false positive | **met** | `tests/test_monitoring.py::TestCriterion4InjectedDisplacement` |
| 14 | 5 | A moving reference station caught and named | **met** | `tests/test_monitoring.py::TestCriterion5MovingReference` |
| 14 | 6 | Independence marked approximate with its bias | **met** | `tests/test_monitoring.py::TestCriterion6Independence` |
| 14 | 7 | Not significant is not zero | **met** | `tests/test_monitoring.py::TestCriterion7NotSignificantIsNotZero` |
| 14 | 8 | Three epochs give velocities and a plottable series | **met** | `tests/test_monitoring.py::TestCriterion8Series`, `tests/qgis/test_time_series_panel.py` |
| 14 | 9 | Alerts flag the right stations, in results, styling and report | **met** | `tests/test_monitoring.py::TestAlerts`, `tests/qgis/test_monitoring_algorithms.py` |
| 15 | 1 | The menu's seven entries in order, with the separator | **partly met** | The structure is asserted in the registry the menu is built from (`tests/test_registry.py::TestMenuStructure`); no test builds the menu on a QGIS main window |
| 15 | 2 | Menu items and algorithms correspond | **met** | `tests/structural/test_menu_algorithm_parity.py` |
| 15 | 3 | Unload removes everything; reloading duplicates nothing | **open** | No test loads and unloads the plugin |
| 15 | 4 | Global Settings shows the specified sections | **met** | `tests/test_settings_def.py`, `tests/qgis/test_settings_dialog.py` |
| 15 | 5 | An instrument profile created, used, exported, imported, identical | **partly met** | A profile round-trips through a document (`tests/test_total_station.py::TestProfiles::test_a_profile_round_trips_through_a_document`); no test computes with it before and after |
| 15 | 6 | A project-scope override takes effect and the UI shows its origin | **partly met** | It takes effect and every contributing scope is recorded (`tests/test_settings_resolution.py`); the window shows neither the override nor its origin |
| 15 | 7 | Basic and Advanced identical, every algorithm | **met** | `tests/qgis/test_basic_advanced_identity.py` |
| 15 | 8 | No string bypasses the translation layer | **met** | `tests/structural/test_i18n_strings.py` |
| 16 | 1 | Provider `geocomp`, algorithms in their groups | **met** | `tests/test_registry.py`, and `tests/qgis/test_basic_advanced_identity.py::test_every_algorithm_is_checked` through the registered provider |
| 16 | 2 | Toolbox, modeller, batch and PyQGIS give identical results | **partly met** | Every QGIS-tier test runs algorithms as PyQGIS does; the toolbox and batch dialogs are QGIS's own and run the same `processAlgorithm`. No test runs one through a model and compares |
| 16 | 3 | The menu-to-algorithm correspondence | **met** | As 15.2 |
| 16 | 4 | Basic and Advanced identical | **met** | As 15.7 |
| 16 | 5 | A model chaining import, pre-process, adjust, visualise runs headless | **open** | Chaining is tested step to step (`tests/qgis/test_totalstation_algorithms.py::TestTheWholeChain::test_the_network_document_feeds_the_analysis_algorithms`); no test builds a model |
| 16 | 6 | Translated help documenting every parameter with units | **partly met** | Every algorithm has help through the base class, and the engine algorithms are checked (`tests/qgis/test_engine_algorithms.py::TestRegistration::test_every_parameter_is_described`); nothing checks every algorithm, or the units |
| 16 | 7 | Inputs validated before computing, the failure naming the parameter | **partly met** | Refusals name what is wrong algorithm by algorithm (`tests/qgis/test_analysis_algorithms.py::TestInspect::test_a_disconnected_network_is_blocked_and_named`, `tests/qgis/test_project_algorithms.py::test_an_unknown_service_names_the_ones_that_exist`); no test covers every algorithm |
| 16 | 8 | Cancelling leaves no partial output | **open** | 13 of 46 algorithms check for cancellation, and none writes its outputs atomically. The task service's cancellation is tested (`tests/qgis/test_task_service.py::TestCancellation`), but it is not the path Processing runs |
| 17 | 1 | GeoPackage → PostGIS → GeoPackage identical | **met** | `tests/test_postgis_store.py`, `tests/qgis/test_postgis_project.py` |
| 17 | 2 | Newer schemas refused, older migrated after a backup, both backends | **met** | `tests/test_project_store.py::TestVersioning`, `tests/test_postgis_store.py::TestVersioning` |
| 17 | 3 | Deleting what a solution used is refused | **met** | `tests/test_project_store.py::TestNothingThatProducedAResultIsDeleted`, `tests/test_postgis_store.py::TestNothingThatProducedAResultIsDeleted::test_deleting_an_observation_a_solution_used_is_refused` |
| 17 | 4 | RD-01 through a saved mapping, reapplied to a second file | **met** | `tests/test_fieldbook_import.py::TestReadingRd01`, `tests/test_fieldbook_import.py::TestMappingDocument`, `tests/test_fieldbook_import.py::TestLocaleIndependentNumbers` |
| 17 | 5 | Corrupt rows reported by number, the rest imported | **met** | `tests/test_fieldbook_import.py::TestPerRecordErrors` |
| 17 | 6 | Cancelling an import leaves the target unchanged | **open** | As 16.8: neither import checks for cancellation, and neither writes atomically |
| 17 | 7 | An *Adjust* file reads, adjusts and writes back equivalently | **met** | Since after P6: `tests/test_adjust.py`, `tests/test_adjust_corpus.py` |
| 17 | 8 | A geoid model imported, applied, recorded, propagated | **met** | `tests/test_geoid_in_a_solution.py::test_the_whole_chain_from_file_to_solution` |
| 17 | 9 | Covariance stored and reloaded bit-identical | **met** | `tests/test_project_store.py::TestTheSolution::test_the_covariance_is_bit_identical`, `tests/test_postgis_store.py::TestARoundTrip::test_the_covariance_is_bit_identical` |
| 18 | 1 | Every string in the catalogues; no unwrapped literal | **met** | `tests/structural/test_translations.py`, `tests/structural/test_i18n_strings.py` |
| 18 | 2 | Portuguese or Spanish translates the whole UI | **partly met** | Both catalogues are complete (`tests/structural/test_translations.py::test_every_source_string_is_translated`), and the legends since P12b (`tests/qgis/test_thematic_maps.py::TestTheLegendSpeaksTheLanguage`); no test switches the language and reads the menus, dialogs and messages back |
| 18 | 3 | The override works independently of QGIS's language | **partly met** | The setting is global (`tests/test_settings_def.py::TestScopes::test_language_is_global_only`); no test installs it against a different QGIS locale |
| 18 | 4 | Terminology checked against the glossary by a script | **open** | No such script exists |
| 18 | 5 | Files written under one decimal convention read under the other | **partly met** | Imports read either separator (`tests/test_fieldbook_import.py::TestLocaleIndependentNumbers`, `tests/test_levelbook_import.py`); no test writes under a comma locale and reads back |
| 18 | 6 | Displayed numbers use the locale separator | **open** | Not built (FR-094): every report and table uses a point, recorded in P12a |
| 18 | 7 | Basic and Advanced identical | **met** | As 15.7 |
| 18 | 8 | No concatenation inside a translation call | **met** | `tests/structural/test_i18n_strings.py::test_no_composed_string_inside_a_translation_call` |
| 19 | 1 | Styled layers with no manual styling | **met** | `tests/qgis/test_result_layers.py::TestTheStylesLoad` |
| 19 | 2 | Ellipses at the confidence, the exaggeration in the legend | **met** | `tests/qgis/test_result_layers.py::TestTheExaggerationReachesTheReader`, `tests/qgis/test_print_layouts.py` |
| 19 | 3 | Relative ellipses match the joint covariance | **partly met** | The computation (`tests/test_statistics.py::TestEllipses::test_the_relative_ellipse_uses_the_cross_covariance`); no layer draws one |
| 19 | 4 | Styles are QML, editable, surviving a project save | **met** | `tests/structural/test_layer_styles.py`, `tests/qgis/test_thematic_maps.py::TestTheyLast` |
| 19 | 5 | Every thematic map renders | **met** | `tests/qgis/test_thematic_maps.py::TestEachMapDrawsEachFeatureInItsClass` |
| 19 | 6 | The time-series panel, both directions | **met** | `tests/qgis/test_time_series_panel.py` |
| 19 | 7 | Reports in three languages, locale numbers, byte-identical | **partly met** | Byte-identical (`tests/qgis/test_adjustment_report.py::TestItIsDeterministic`); locale numbers are 18.6 |
| 19 | 8 | An approximate solution's report names its strategies | **met** | `tests/qgis/test_adjustment_report.py::TestItIsDefensible::test_an_approximate_solution_names_its_strategies` |
| 20 | 1 | T1 in under 60 seconds | **manual** | Measured, not enforced: 33 s on the development container for 3,497 tests (P12b); the `core` jobs of `.github/workflows/test.yml` report their duration |
| 20 | 2 | Every structural check in §2 implemented | **partly met** | All but two, in `tests/structural/`, with the credential and identity checks in `tests/qgis/test_product_download.py` and `tests/qgis/test_basic_advanced_identity.py`. The help check covers the engine algorithms only (16.6), and the locale round trip is not implemented (18.5) |
| 20 | 3 | Every reference dataset with an expected-results file and a test | **partly met** | §3's table: RD-01 to RD-04, RD-06, RD-07, RD-09, RD-11 and RD-12 have tests; RD-08's published half waits on W-01, RD-05 is not vendored, RD-10 is P13's |
| 20 | 4 | Cross-validation on three networks | **met** | As 06.6 |
| 20 | 5 | The CI matrix, engines-absent and SciPy-absent rows included | **met** | `.github/workflows/test.yml`'s `degraded environments` job |
| 20 | 6 | Coverage measured per release; every public function tested | **open** | Coverage is not measured in CI |
| 20 | 7 | A comparison export of §5's step-3 fields, documented | **partly met** | *Export solution tables* carries every step-3 field (`tests/test_export.py`); it is not documented as the comparison export, and no comparison has been run (W-12) |
| 20 | 8 | Every criterion has a test or a reason | **met** | This table, held by `tests/structural/test_acceptance_register.py` |
| 21 | 1 | The ZIP installs into a clean QGIS and validates | **met** | `.github/workflows/build.yml` installs the built archive into the QGIS image and loads it |
| 21 | 2 | Two builds byte-identical | **met** | `.github/workflows/build.yml`, *The archive must be reproducible* |
| 21 | 3 | Loads with no engine; engine operations explained | **met** | As 07.7 |
| 21 | 4 | The engine manager on every OS, with an override | **partly met** | Verified on Linux (P6); Windows and macOS are pinned and untested (`tests/test_engines.py`) |
| 21 | 5 | CI on Linux, Windows and macOS, LTR and stable QGIS | **partly met** | The QGIS-free tier runs on all three (`.github/workflows/test.yml`); the QGIS tier runs on Linux against one QGIS image |
| 21 | 6 | A tagged release publishes and installs | **open** | P13's: no release has been made |
| 21 | 7 | LICENSE, THIRD_PARTY.md and SPDX headers | **met** | `tests/structural/test_spdx_headers.py` |
| 21 | 8 | The About dialog shows the licences and engine versions | **partly met** | Built (`gui/about_dialog.py`); no test opens it |
