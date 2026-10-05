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

**A chain of documents is tested against the same chain in memory (P12c-20).** The field techniques reach
their networks through files, because the graphical modeller chains algorithms through files. Each file is a
place where a field can be dropped. P12c-18 found a 3D total-station network that had lost every sight's
instrument and target heights between pre-processing and the network. The in-memory path carried them, and
its tests passed. So for each technique a T3 test reads the field file again in memory, runs it through the
same core functions with the options the algorithms used, and requires the network the algorithms built
through their documents to equal it, observation by observation:

| Technique | Test |
|---|---|
| Total station, 2D, 3D, 1D | `tests/qgis/test_totalstation_algorithms.py::TestAThreeDimensionalNetwork::test_the_network_through_the_files_is_the_one_built_in_memory` |
| Levelling | `tests/qgis/test_levelling_algorithms.py::TestClosuresAndTheNetwork::test_the_network_through_the_files_is_the_one_built_in_memory` |
| Gravimetry | `tests/qgis/test_gravimetry_algorithms.py::TestTheDocumentAndTheMemoryAgree` |

A new document in a chain needs its row here.

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
| Every code raised, and every finding outside a shrinking baseline, has a message template; every template interpolates only context keys its raising site supplies, has one `%n` per key, interpolates no English the core spells out, and names a code something raises or reports | NFR-006, FR-091, [`18-i18n-and-profiles.md`](./18-i18n-and-profiles.md) §2 |
| Every requirement ID in `02-requirements.md` appears in exactly one `ROADMAP.md` phase | [`README.md`](./README.md) |
| Relative links between spec documents resolve | — |
| Locale round trip: every output format written under a comma-decimal locale reads back under a period-decimal one | FR-095 |
| No credential appears in any log, config, provenance record or export | NFR-010 |
| Basic and Advanced modes produce identical numeric results with defaults, for every algorithm | FR-071 |
| Every acceptance criterion of every specification has one row in §10's register, and every test a row cites exists | §9 criterion 8 |
| Every requirement has one row in §11's register, and every test a row cites exists (P12c-13) | FR-302 and FR-304's lesson: a requirement with no criterion of its own was held to nothing |
| Every parameter an algorithm declares is read by the run, and every output it declares is returned (P12c-12) | [`16-processing-provider.md`](./16-processing-provider.md) §4 |
| Every translated string that uses a glossary term uses the glossary's rendering of it (`scripts/check_glossary.py`) | FR-093, [`18-i18n-and-profiles.md`](./18-i18n-and-profiles.md) §3 |
| Coverage of `core/` measured on every run of the QGIS job, and every public function and method of `core/` reached by at least one test (`scripts/check_coverage.py`) | §9 criterion 6 |
| Every module of the plugin has a function the suite runs, measured in the same run (`scripts/check_coverage.py`, P12c-13) | NFR-011 |
| Every package the plugin imports has a recorded decision in [`03`](./03-architecture.md) §3.7 (P12c-13) | NFR-005 |
| Every interface one module imports from another is documented and annotated, against a frozen list that may only shrink (P12c-13) | NFR-012 |
| Every `Observation(...)` the plugin makes passes `provenance=`, or is in a reader that stamps it afterwards with `Network.record_provenance` (`tests/structural/test_observation_provenance.py`, P12c-20) | FR-102, [`04-data-model.md`](./04-data-model.md) §2.5 |

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

**As built (P12c): the comparison export is *Export solution tables*** (`geocomp:project_export`), CSV or
`.xlsx`. A second export of the same numbers would be a second place for them to disagree. Every field of step 3
is in it, and `io/tabular.py`'s `COMPARISON_FIELDS` names where. `tests/test_export.py::TestTheComparisonExport`
asserts each is exported and filled for an adjusted network.

| Step 3 field | Sheet | Columns |
|---|---|---|
| Adjusted coordinates | `adjusted` | `value_1`, `value_2`, `value_3` |
| σ̂₀² | `statistics` | `variance_factor_aposteriori` |
| Degrees of freedom | `statistics` | `degrees_of_freedom` |
| Residuals | `residuals` | `residual`, `standardised_residual` |
| Error ellipses | `adjusted` | `ellipse_semi_major`, `ellipse_semi_minor`, `ellipse_orientation`, `ellipse_confidence` |
| Positional uncertainty | `adjusted` | `positional_uncertainty` |
| Test decisions | `residuals`; `statistics` | `w_test`, `w_statistic`, `w_passed`; `global_test_statistic`, `global_test_passed` |

**Writing that test found the positional uncertainty empty for every in-house solution.** Only DynAdjust's
reader had ever filled it. The in-house adjustment now carries it, as [`06`](./06-adjustment-core.md) §4.5
defines it.

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
| SciPy | Present and absent (asserting the NumPy-only fallback, [`03-architecture.md`](./03-architecture.md) §3.7). Present, the QGIS job runs the whole suite a second time with every adjustment on the sparse path (`pytest --sparse`, NFR-008) |

The **engines-absent** and **SciPy-absent** rows are not optional. FR-306 and the fallback path are
requirements, and an untested fallback is a fallback that does not work.

**As built (P12c-6).** The QGIS tier runs on all three operating systems, in the QGIS a user installs on
each and in that QGIS's own Python: the `qgis/qgis` image on Linux, OSGeo4W on Windows, the official bundle
on macOS. Which releases is decided when the workflow runs, from the images' `stable` and `ltr` tags
(`scripts/qgis_versions.py`); a release below the plugin's `qgisMinimumVersion` is left out with a notice.
On 4 October 2026 that is stable 4.2.3 alone, the `ltr` tag being 3.44. PostGIS is a Linux row only:
service containers exist on Linux runners alone. The `--sparse` second pass is Linux's too. Before P12c-6
the QGIS tier ran in `qgis/qgis:latest` on Linux, which is the nightly build, so no released QGIS was under
test anywhere.

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
   *Met in P12c-6, and measured on every run rather than per release:* 95.6% of `core/`'s lines, and all 685
   public functions and methods reached. The first measurement found 49 that no test reached;
   `tests/test_core_public_functions.py` holds them to what they claim, and the check now admits none.
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

**State at the audit (P12c, 2 October 2026): 90 met, 31 partly met, 12 open, 2 manual, of 135. State now: 123 met, 7 partly met, 4 open, 2 manual, of 136.** The audit
found that several criteria believed met were met in part. A test existed near each one but did not assert
what the criterion says, and nothing compared the two until this table. The rows say which part.

| Spec | # | Criterion, abridged | State | Evidence, or what is missing |
|---|---|---|---|---|
| 05 | 1 | Jacobians against numerical derivatives | **met** | `tests/test_adjustment.py::TestJacobians` (central differences: the observation equations are not complex-safe), `tests/test_uncertainty.py::TestJacobianVerification`, `tests/test_geodesy.py::TestJacobians`, `tests/test_differentiation.py` |
| 05 | 2 | Propagation reproduces Ghilani and Gemael | **partly met** | RD-02 is validated three ways, closed form, first order and Monte Carlo (`tests/test_reference_propagation.py`). Published standard deviations are reproduced through RD-11 (`tests/test_krumm_corpus.py::test_the_published_standard_deviations_are_reproduced_too`). No printed *propagation* example is transcribed: Gemael waits on W-04, and the books are not transcribed from memory |
| 05 | 3 | A pre-processing chain preserves the combined propagation | **met** | Since P12c: `tests/test_total_station.py::TestTheChainIsOnePropagation` differentiates the whole total-station chain numerically. Its 16 inputs are the readings, heights, air and calibration constants, and it propagates once through that Jacobian. The stepwise result agrees to 2e-8. The one term the chain leaves out by design, the cyclic error's slope in the distance, shows as 5.5e-5, and the test holds it to that |
| 05 | 4 | No geodetic value without an uncertainty | **met** | `tests/structural/test_no_bare_geodetic_floats.py` |
| 05 | 5 | Approximate results name their strategies in export, report and provenance | **met** | Since P12c: the report (`tests/qgis/test_adjustment_report.py::TestItIsDefensible::test_an_approximate_solution_names_its_strategies`); the provenance, its document and its stored row, schema 5; the export's statistics sheet (`tests/test_approximation_is_named.py`) |
| 05 | 6 | Correlated operands refused by the scalar path | **met** | `tests/test_uncertainty.py::TestCorrelationGuard` |
| 06 | 1 | Ghilani and Gemael network examples reproduced | **partly met** | Ghilani by name through RD-11, coordinates to 0.05 mm (`tests/test_krumm_corpus.py::test_the_published_coordinates_are_reproduced`); the corpus publishes coordinates, so residuals, σ̂₀² and ellipses are not compared against print. Gemael waits on W-04 |
| 06 | 2 | Free and constrained solutions consistent | **met** | `tests/test_adjustment.py::TestFreeNetworkAndDatum` |
| 06 | 3 | A 2 × MDB blunder found on the first pass | **met** | `tests/test_statistics.py::TestDataSnooping::test_a_blunder_at_twice_the_mdb_is_located_on_the_first_pass` |
| 06 | 4 | Rank deficiency diagnosed, never a number | **met** | `tests/test_adjustment.py::TestRankDiagnosis` |
| 06 | 5 | Pre-analysis reproduces the adjusted Σₓ | **met** | `tests/test_statistics.py::TestPreAnalysis` |
| 06 | 6 | In-house core and DynAdjust agree | **met** | Tier 4: `tests/test_dynadjust_crossvalidation.py::TestTheTwoEnginesAgree`, `tests/test_dynadjust_pipeline.py::TestAProjectedNetworkCrossValidates`, `tests/test_dynadjust_pipeline.py::TestATerrestrialNetworkCrossValidates` |
| 06 | 7 | Every statistic with critical value, confidence and decision | **met** | `tests/test_statistics.py::TestGlobalTest::test_the_statistic_carries_both_critical_values`, `tests/test_statistics.py::TestDataSnooping::test_the_distribution_used_is_reported` |
| 06 | 8 | Beyond the dense path, the sparse one agrees with it; without SciPy, a refusal naming it | **met** | Since P12c: `tests/test_sparse_adjustment.py::TestTheTwoPathsAgree`, `tests/test_network_scale.py::TestTheAdjustmentAsks::test_without_scipy_it_refuses_before_allocating`, and the whole suite again on the sparse path in CI (`--sparse`). Measured to 10,000 stations ([`06`](./06-adjustment-core.md) §2.4.1) |
| 07 | 1 | DynaML validates and imports without warnings, every mapped type | **met** | Since P12c-6: one network writes all eighteen codes; both files validate against upstream's `DynaML.xsd` and `dnaimport` reads every row with no warning (`tests/test_dynaml_every_type.py::test_every_file_validates_against_dynadjusts_own_schema`, `tests/test_dynaml_every_type.py::test_dnaimport_takes_in_every_row_and_warns_about_nothing`) |
| 07 | 2 | A baseline cluster round-trips at full precision | **met** | `tests/test_dynaml_writer.py::test_the_covariance_survives_to_full_double_precision`, `tests/test_gnss_to_dynadjust.py::TestTwoBaselinesBecomeAnXCluster` |
| 07 | 3 | The pipeline runs end to end to a Solution | **met** | Tier 4: `tests/test_dynadjust_pipeline.py::TestAgainstARealEngine::test_the_whole_pipeline_reaches_a_solution` |
| 07 | 4 | Parsed results match the printed files | **met** | `tests/test_dynadjust_output.py`, against files a real DynAdjust wrote; tier 4 re-runs them (`tests/test_dynadjust_output.py::TestTheFixtureDriftGuard`) |
| 07 | 5 | Cross-validation passes | **met** | As 06.6 |
| 07 | 6 | Every **[C]** confirmed | **manual** | A documentation audit, not a behaviour; discharged in P6 against upstream at a pinned commit, recorded in [`07`](./07-engine-dynadjust.md)'s header |
| 07 | 7 | Without DynAdjust, everything else works | **met** | `tests/qgis/test_engine_algorithms.py::TestAdjustWithoutTheEngine::test_it_says_how_to_get_dynadjust_rather_than_failing_obscurely`; the whole suite runs without engines in `.github/workflows/test.yml` |
| 08 | 1 | Session discovery over RINEX 2 and 3, compressed, mismatches reported | **met** | `tests/test_gnss_discovery.py`, `tests/test_rinex.py` |
| 08 | 2 | A configuration fed back through `-k` reproduces the run bit for bit | **met** | Since P12c-6: `tests/test_rtklib_engine.py::TestAgainstTheRealEngine::test_the_written_configuration_fed_back_reproduces_the_run_bit_for_bit` |
| 08 | 3 | `.pos` parsing round-trips, every format | **met** | `tests/test_pos_reader.py::TestEveryFormatReads`, `tests/test_pos_reader.py::TestTheFormatsAgree` |
| 08 | 4 | Covariance reaches a G measurement intact | **met** | `tests/test_gnss_to_dynadjust.py::TestOneBaselineBecomesAGMeasurement` |
| 08 | 5 | One broken session does not abort a batch | **met** | `tests/test_gnss_batch.py::TestOneBadSessionDoesNotAbortTheBatch` |
| 08 | 6 | Products from cache on a second run, named in provenance | **met** | `tests/test_gnss_products.py::TestResolution`, `tests/test_gnss_products.py::TestProvenance` |
| 08 | 7 | No credential anywhere GeoComp writes | **met** | `tests/test_gnss_products.py::TestCredentials`, `tests/qgis/test_product_download.py` |
| 08 | 8 | A PPP mode shows the FR-604 notice | **met** | Since P12c: in the Absolute algorithms' help and description, not the Relative ones', and as the first warning of a run (`tests/qgis/test_ppp_notice.py`) |
| 09 | 1 | RD-01 reproduces, except where the prototype is wrong | **met** | `tests/test_reference_total_station.py::TestReproduction`, `tests/test_reference_total_station.py::TestTheOneHundredAndEightyDegreeError` |
| 09 | 2 | Both RD-01 defects caught | **met** | `tests/test_reference_total_station.py::TestTheDistanceBlunder`, `tests/test_reference_total_station.py::TestTheOneHundredAndEightyDegreeError` |
| 09 | 3 | The wrap case | **met** | `tests/test_reference_total_station.py::TestTheWrapCase::test_the_case_the_spec_names` |
| 09 | 4 | Injected collimation and index error recovered | **met** | `tests/test_reference_total_station.py::TestInjectedInstrumentalErrors` |
| 09 | 5 | Traverse against a published worked example | **open** | Waits on W-07. The traverse paths are tested against constructed truth (`tests/test_survey_computations.py::TestTraverse`), not against print |
| 09 | 6 | The danger circle detected, not solved | **met** | `tests/test_survey_computations.py::TestTheDangerCircle` |
| 09 | 7 | A triangulateration free and constrained is consistent | **met** | Since P12c, on RD-03's triangulateration as well as its trilateration (`tests/test_adjustment.py::TestFreeNetworkAndDatum`, parametrised over both) |
| 09 | 8 | Every output carries an uncertainty and a mode | **met** | `tests/structural/test_no_bare_geodetic_floats.py::TestTechniqueModuleReturns` |
| 09 | 9 | RD-01 through the menu gives styled layers with ellipses | **met** | Since P12c: `tests/qgis/test_model_chain.py::TestRd01ArrivesAsStyledLayers`. RD-01 runs as the menu's dialog runs it, as a task on a worker thread. It gives an ellipse for each of its three stations, a layer name that states the exaggeration, and each layer drawn with its shipped style |
| 10 | 1 | Three schemes reproduce published examples | **open** | Waits on W-05. RD-04's field books are generated by inverting the equations under test (`tests/test_levelling.py::TestEqualSights`, `tests/test_levelling.py::TestExtremeSights`, `tests/test_levelling.py::TestReciprocalSights`), which proves correctness but not agreement by name |
| 10 | 2 | Loop misclosure and tolerance against a worked example, failing case included | **partly met** | The failing case is asserted (`tests/test_levelling.py::TestClosures`); agreement with a published example waits on W-05 |
| 10 | 3 | Extreme sights are a correlated cluster that helps | **met** | `tests/test_levelling.py::TestExtremeSights::test_the_correlation_makes_a_derived_difference_better_not_worse` |
| 10 | 4 | Length and setup weighting consistent, and with a published example | **partly met** | Consistent with each other (`tests/test_levelling.py::TestTheNetwork::test_length_and_setup_weighting_agree_on_the_heights`); a network published under both waits on W-06 |
| 10 | 5 | Geometric and trigonometric combined, variance components by technique | **met** | The computation, since P12c: geometric and trigonometric height differences in one network, a factor of 4 recovered on the mis-declared technique and 1 on the other (`tests/test_variance_components.py::TestTwoLevellingTechniques`). From the menu since P12c: *Levelling network* reads the document *Trigonometric levelling* writes and estimates a factor per technique (`tests/qgis/test_levelling_algorithms.py::TestClosuresAndTheNetwork::test_trigonometric_differences_join_the_network_with_their_own_factor`) |
| 10 | 6 | Mixed heights without a geoid refused; with one, converted and named | **met** | `tests/test_levelling.py::TestHeightSystems` |
| 10 | 7 | Every output carries an uncertainty and a mode | **met** | `tests/test_levelling.py::TestEveryOutputCarriesAnUncertainty` |
| 10 | 8 | The tolerance gate and the orthometric correction | **met** | `tests/test_levelling.py::TestTheToleranceGate`, `tests/test_levelling.py::TestOrthometricCorrectionOfLines`, `tests/qgis/test_levelling_algorithms.py` |
| 11 | 1 | Mixed RINEX sessions with mismatches reported | **met** | `tests/test_gnss_discovery.py` |
| 11 | 2 | A static session reproduces a published reference within tolerance | **met** | Tier 4, on the criterion as P7e restated it: loop closure and repeatability ([`20`](./20-testing-and-validation.md) §6), `tests/test_rd06.py::TestTheTriangleCloses`. Agreement with the published coordinate is reported, not judged (`tests/test_rd06.py::test_the_published_coordinate_comparison_is_reported_not_judged`) |
| 11 | 3 | The independent subset identified | **met** | `tests/test_gnss_baselines.py::TestTheIndependentSubset` |
| 11 | 4 | A baseline reaches a G measurement intact | **met** | As 08.4 |
| 11 | 5 | Antenna height reduced twice is prevented | **met** | `tests/test_gnss_baselines.py::TestAntennaHeightIsRemovedOnce` |
| 11 | 6 | Two configurations compared with significance | **met** | `tests/test_gnss_comparison.py` |
| 11 | 7 | A base station in another frame is transformed, with a record | **met** | Since P12c: the core transformation and its refusals (`tests/test_gnss_stations.py::TestABaseInAnotherFrame`). The relative runs fetch the base from the database, hold it in the run's frame at the session's epoch, give RTKLIB the coordinates, and record it (`tests/qgis/test_base_station_frame.py`) |
| 11 | 8 | An Absolute mode shows the FR-604 notice | **met** | As 08.8 |
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
| 15 | 1 | The menu's eight entries in order, with the separator | **met** | Since P12c, on a main window: `tests/qgis/test_plugin_lifecycle.py::TestLoading::test_the_menu_is_on_the_menu_bar_with_its_eight_entries_in_order`; the structure in the registry it is built from, `tests/test_registry.py::TestMenuStructure` |
| 15 | 2 | Menu items and algorithms correspond | **met** | `tests/structural/test_menu_algorithm_parity.py` |
| 15 | 3 | Unload removes everything; reloading duplicates nothing | **met** | Since P12c: `tests/qgis/test_plugin_lifecycle.py`, in a QGIS of its own with a stand-in `iface` |
| 15 | 4 | Global Settings shows the specified sections | **met** | `tests/test_settings_def.py`, `tests/qgis/test_settings_dialog.py` |
| 15 | 5 | An instrument profile created, used, exported, imported, identical | **met** | Since P12c: `tests/test_total_station.py::TestAProfileTravels` |
| 15 | 6 | A project-scope override takes effect and the UI shows its origin | **met** | It takes effect and every contributing scope is recorded (`tests/test_settings_resolution.py`). Since P12c the window shows the override, marks it *this project*, saves it to the project alone and can take it away (`tests/qgis/test_settings_dialog.py::test_marking_a_row_saves_it_in_the_project_alone`, `tests/qgis/test_settings_dialog.py::test_ok_no_longer_makes_a_projects_override_everyones`) |
| 15 | 7 | Basic and Advanced identical, every algorithm | **met** | `tests/qgis/test_basic_advanced_identity.py` |
| 15 | 8 | No string bypasses the translation layer | **met** | `tests/structural/test_i18n_strings.py` |
| 16 | 1 | Provider `geocomp`, algorithms in their groups | **met** | `tests/test_registry.py`, and `tests/qgis/test_basic_advanced_identity.py::test_every_algorithm_is_checked` through the registered provider |
| 16 | 2 | Toolbox, modeller, batch and PyQGIS give identical results | **met** | Since P12c: `tests/qgis/test_model_chain.py::TestEveryWayGivesOneAnswer`. RD-01's chain is run three ways: by PyQGIS; as a `QgsProcessingAlgRunnerTask`, the way the toolbox and batch dialogs run it; and as a saved model. All three give the same solution document, provenance aside. The dialogs' parameter widgets are QGIS's own |
| 16 | 3 | The menu-to-algorithm correspondence | **met** | As 15.2 |
| 16 | 4 | Basic and Advanced identical | **met** | As 15.7 |
| 16 | 5 | A model chaining import, pre-process, adjust, visualise runs headless | **met** | Since P12c: `tests/qgis/test_model_chain.py::TestTheModel`. The test builds the model, saves it as a `.model3`, loads it back and runs it from the field book to the solution and its layers |
| 16 | 6 | Translated help documenting every parameter with units | **met** | Since P12c: every algorithm's help lists its parameters and outputs by their labels, every number's label states its unit or is named dimensionless, and the help's own words translate (`tests/qgis/test_algorithm_help.py`) |
| 16 | 7 | Inputs validated before computing, the failure naming the parameter | **met** | Since P12c-6, over every algorithm and every input: `tests/qgis/test_inputs_are_named.py::test_a_missing_file_or_folder_is_refused_before_the_run_and_named`, `tests/qgis/test_inputs_are_named.py::test_a_mandatory_input_left_out_is_named`, `tests/qgis/test_inputs_are_named.py::test_an_input_of_the_wrong_kind_is_refused_and_named` |
| 16 | 8 | Cancelling leaves no partial output | **met** | Since P12c, held around every algorithm (`geocomp/algorithms/transaction.py`, applied by the base class to all 46: `tests/qgis/test_cancellation.py::test_every_algorithm_runs_inside_the_transaction`). A run cancelled after writing puts back the file it replaced and removes those it made (`tests/qgis/test_cancellation.py::TestCancelledAfterWriting`), and is reported as not finished. Database targets roll back in their own transaction (`tests/test_project_store.py::TestSeveralWritesAsOne`) |
| 17 | 1 | GeoPackage → PostGIS → GeoPackage identical | **met** | `tests/test_postgis_store.py`, `tests/qgis/test_postgis_project.py` |
| 17 | 2 | Newer schemas refused, older migrated after a backup, both backends | **met** | `tests/test_project_store.py::TestVersioning`, `tests/test_postgis_store.py::TestVersioning` |
| 17 | 3 | Deleting what a solution used is refused | **met** | `tests/test_project_store.py::TestNothingThatProducedAResultIsDeleted`, `tests/test_postgis_store.py::TestNothingThatProducedAResultIsDeleted::test_deleting_an_observation_a_solution_used_is_refused` |
| 17 | 4 | RD-01 through a saved mapping, reapplied to a second file | **met** | `tests/test_fieldbook_import.py::TestReadingRd01`, `tests/test_fieldbook_import.py::TestMappingDocument`, `tests/test_fieldbook_import.py::TestLocaleIndependentNumbers` |
| 17 | 5 | Corrupt rows reported by number, the rest imported | **met** | `tests/test_fieldbook_import.py::TestPerRecordErrors` |
| 17 | 6 | Cancelling an import leaves the target unchanged | **met** | Since P12c: a field-book import (`tests/qgis/test_cancellation.py::test_a_cancelled_import_leaves_its_target_unchanged`); a save into a project, GeoPackage and PostGIS (`tests/qgis/test_cancellation.py::test_a_cancelled_save_leaves_the_project_as_it_was`, `tests/qgis/test_postgis_project.py::TestCancelling`); the PostGIS switches, which roll back the rows and drop a schema the run created (`tests/test_postgis_store.py::TestACancelledExport`) |
| 17 | 7 | An *Adjust* file reads, adjusts and writes back equivalently | **met** | Since after P6: `tests/test_adjust.py`, `tests/test_adjust_corpus.py` |
| 17 | 8 | A geoid model imported, applied, recorded, propagated | **met** | `tests/test_geoid_in_a_solution.py::test_the_whole_chain_from_file_to_solution` |
| 17 | 9 | Covariance stored and reloaded bit-identical | **met** | `tests/test_project_store.py::TestTheSolution::test_the_covariance_is_bit_identical`, `tests/test_postgis_store.py::TestARoundTrip::test_the_covariance_is_bit_identical` |
| 18 | 1 | Every string in the catalogues; no unwrapped literal | **met** | `tests/structural/test_translations.py`, `tests/structural/test_i18n_strings.py` |
| 18 | 2 | Portuguese or Spanish translates the whole UI | **met** | Since P12c, in both languages: every algorithm's name, group, description, parameters, outputs and help, and every menu entry (`tests/qgis/test_language.py`). Writing it found five places where a word was filed under one context and looked up under another, and so was never translated |
| 18 | 3 | The override works independently of QGIS's language | **met** | Since P12c: `tests/qgis/test_language.py::test_geocomps_language_overrides_qgiss` |
| 18 | 4 | Terminology checked against the glossary by a script | **met** | Since P12c: `scripts/check_glossary.py`, held by `tests/structural/test_glossary.py::test_every_translation_uses_the_glossary`. Its first run found 128 Portuguese and Spanish strings off the glossary, most of them the levelling strings calling a *setup* a *station* |
| 18 | 5 | Files written under one decimal convention read under the other | **met** | Imports read either separator (`tests/test_fieldbook_import.py::TestLocaleIndependentNumbers`, `tests/test_levelbook_import.py`). Since P12c, RD-01's whole chain, from the field book to the stored project's export, is written under Qt's, GeoComp's and Python's comma locale in pt-BR and es. Every file it writes equals the English run's, and reads back in English (`tests/qgis/test_locale_numbers.py::TestFilesKeepAPoint`) |
| 18 | 6 | Displayed numbers use the locale separator | **met** | Since P12c (`core/number_format.py`). Every number in every table of RD-01's four reports changes its separator and nothing else (`tests/qgis/test_locale_numbers.py::TestReportsUseTheComma`), as do the formatters every report uses (`tests/test_number_format.py`). Thousands grouping and locale dates are not built ([`18`](./18-i18n-and-profiles.md) §5) |
| 18 | 7 | Basic and Advanced identical | **met** | As 15.7 |
| 18 | 8 | No concatenation inside a translation call | **met** | `tests/structural/test_i18n_strings.py::test_no_composed_string_inside_a_translation_call` |
| 19 | 1 | Styled layers with no manual styling | **met** | `tests/qgis/test_result_layers.py::TestTheStylesLoad` |
| 19 | 2 | Ellipses at the confidence, the exaggeration in the legend | **met** | `tests/qgis/test_result_layers.py::TestTheExaggerationReachesTheReader`, `tests/qgis/test_print_layouts.py` |
| 19 | 3 | Relative ellipses match the joint covariance | **met** | The computation (`tests/test_statistics.py::TestEllipses::test_the_relative_ellipse_uses_the_cross_covariance`); every observed pair's ellipse from the joint covariance, a held station's line left out, a geocentric difference turned into the horizon (`tests/test_relative_ellipses.py`); the layer, each feature against the joint covariance and drawn at the stated factor (`tests/qgis/test_result_layers.py::TestTheRelativeEllipses`, P12c-6) |
| 19 | 4 | Styles are QML, editable, surviving a project save | **met** | `tests/structural/test_layer_styles.py`, `tests/qgis/test_thematic_maps.py::TestTheyLast` |
| 19 | 5 | Every thematic map renders | **met** | `tests/qgis/test_thematic_maps.py::TestEachMapDrawsEachFeatureInItsClass` |
| 19 | 6 | The time-series panel, both directions | **met** | `tests/qgis/test_time_series_panel.py` |
| 19 | 7 | Reports in three languages, locale numbers, byte-identical | **met** | Byte-identical (`tests/qgis/test_adjustment_report.py::TestItIsDeterministic`); locale numbers since P12c, in English, Portuguese and Spanish (`tests/qgis/test_locale_numbers.py::TestReportsUseTheComma`) |
| 19 | 8 | An approximate solution's report names its strategies | **met** | `tests/qgis/test_adjustment_report.py::TestItIsDefensible::test_an_approximate_solution_names_its_strategies` |
| 20 | 1 | T1 in under 60 seconds | **manual** | Measured, not enforced: 33 s on the development container for 3,497 tests (P12b); the `core` jobs of `.github/workflows/test.yml` report their duration |
| 20 | 2 | Every structural check in §2 implemented | **met** | In `tests/structural/`, the credential and identity checks in `tests/qgis/test_product_download.py` and `tests/qgis/test_basic_advanced_identity.py`, the help check since P12c in `tests/qgis/test_algorithm_help.py`, and the locale round trip since P12c in `tests/qgis/test_locale_numbers.py` |
| 20 | 3 | Every reference dataset with an expected-results file and a test | **partly met** | §3's table: RD-01 to RD-04, RD-06, RD-07, RD-09, RD-11 and RD-12 have tests; RD-08's published half waits on W-01, RD-05 is not vendored, RD-10 is P13's |
| 20 | 4 | Cross-validation on three networks | **met** | As 06.6 |
| 20 | 5 | The CI matrix, engines-absent and SciPy-absent rows included | **met** | `.github/workflows/test.yml`'s `degraded environments` job |
| 20 | 6 | Coverage measured per release; every public function tested | **met** | Since P12c-6: `scripts/check_coverage.py` in the QGIS job, on every run; the functions it first found unreached, `tests/test_core_public_functions.py` |
| 20 | 7 | A comparison export of §5's step-3 fields, documented | **met** | Since P12c: *Export solution tables*, documented in §5, every field exported and filled (`tests/test_export.py::TestTheComparisonExport`). No comparison has been run (W-12); that is §5's protocol, not this criterion |
| 20 | 8 | Every criterion has a test or a reason | **met** | This table, held by `tests/structural/test_acceptance_register.py` |
| 21 | 1 | The ZIP installs into a clean QGIS and validates | **met** | `.github/workflows/build.yml` installs the built archive into the QGIS image and loads it |
| 21 | 2 | Two builds byte-identical | **met** | `.github/workflows/build.yml`, *The archive must be reproducible* |
| 21 | 3 | Loads with no engine; engine operations explained | **met** | As 07.7 |
| 21 | 4 | The engine manager on every OS, with an override | **partly met** | DynAdjust: the pinned archive downloaded, verified, installed, recorded, run and overridden on Linux, Windows and macOS, and a network adjusted through it agreeing with the fixture (`tests/test_engine_manager_live.py`, the `engine` workflow's `manager` job); the plugin's own path through the QGIS network stack, Global Settings and *Install an engine* (`tests/qgis/test_engine_install.py`, P12c-6). RTKLIB is located, not acquired: upstream publishes Windows executables only, from a release that is not the build the parsers were checked against ([`21`](./21-packaging-ci-release-licensing.md) §4) |
| 21 | 5 | CI on Linux, Windows and macOS, LTR and stable QGIS | **met** | Since P12c-6 the whole suite runs on all three in the QGIS a user installs there, in its own Python: the `qgis/qgis` image on Linux, OSGeo4W on Windows, the official bundle on macOS (`.github/workflows/test.yml`, the three *qgis integration* jobs). The releases are read from the images' `stable` and `ltr` tags at each run and held to ADR-0007's reading of NFR-001: stable 4.2 today, the LTR added when its tag is a 4.x release (`scripts/qgis_versions.py`, `tests/test_qgis_versions.py`). Not covered: the LTR legs have not yet run; PostGIS runs on Linux only; the engine-installation tests skip on Windows ([`21`](./21-packaging-ci-release-licensing.md) §5) |
| 21 | 6 | A tagged release publishes and installs | **open** | P13's: no release has been made |
| 21 | 7 | LICENSE, THIRD_PARTY.md and SPDX headers | **met** | `tests/structural/test_spdx_headers.py` |
| 21 | 8 | The About dialog shows the licences and engine versions | **met** | Since P12c: GeoComp's licence and each engine's, and the version installed or *not installed* (`tests/qgis/test_about_dialog.py`, `tests/test_engine_status.py`) |

## 11. Requirement register (P12c-13)

**The acceptance register above holds every criterion to a test, but not every requirement.** P12c-11 found two
requirements broken with every acceptance row green: no algorithm that runs RTKLIB warned about an untested
version (FR-302), and its time limit could not be configured (FR-304). Neither requirement had a criterion of its
own. This table gives every requirement of [`02`](./02-requirements.md) a row with the same four states and the
same rules: a **met** row cites a test, directly or through "As NN.N" to a met acceptance row, and a row that
is not met says what is missing. `tests/structural/test_requirement_register.py` holds it to the requirements
document. It was written block by block in seven pull requests, the last of which, in P12c-13, left no requirement
without a row.

**Every requirement has a row (P12c-13): the platform block, FR-001 to FR-095; data, persistence and interoperability, FR-100 to FR-167; uncertainty and adjustment, FR-200 to FR-273; engines, FR-300 to FR-359; total station and level, FR-400 to FR-505; GNSS, gravimetry, integration and multi-epoch, FR-600 to FR-838; visualisation, reporting and community, FR-900 to FR-955; and the non-functional requirements, NFR-001 to NFR-012. State now: 162 met, 13 partly met, 1 open, 0 manual, of 176.**

| ID | State | Evidence, or what is missing |
|---|---|---|
| FR-001 | **met** | `.github/workflows/build.yml` installs the built archive into the QGIS image and loads it; `tests/qgis/test_plugin_lifecycle.py` loads it through `classFactory` |
| FR-002 | **met** | As 15.1 |
| FR-003 | **met** | As 15.1 |
| FR-004 | **met** | As 15.2 |
| FR-005 | **met** | As 15.2 |
| FR-006 | **met** | As 15.3 |
| FR-007 | **met** | Since P12c-13: inspect, adjust, save to the project store, run the last algorithm again, the results panel and Global Settings, hidden by `interface.show_toolbar` (`tests/qgis/test_plugin_lifecycle.py::TestTheToolbar`). Until then the toolbar held Global Settings alone. *Open project* is QGIS's own: a store is a GeoPackage or a PostGIS schema, opened as any other |
| FR-008 | **met** | Off the GUI thread as a Processing task (`tests/qgis/test_model_chain.py::TestEveryWayGivesOneAnswer`); cancellation leaves no partial output (`tests/qgis/test_cancellation.py`). 37 of the 41 algorithm modules report progress; the four that do not finish in a moment. Polling for the cancel at every iteration is per algorithm, 14 of 41 ([`16`](./16-processing-provider.md) §7) |
| FR-009 | **met** | Since P12c-13: the `GeoComp` tab and the verbosity `interface.log_level` sets (`tests/qgis/test_log.py`) |
| FR-030 | **met** | `tests/test_registry.py::TestIdentity::test_provider_id_is_the_documented_one` |
| FR-031 | **met** | `tests/test_registry.py::TestReferentialIntegrity::test_every_algorithm_names_a_declared_processing_group` |
| FR-032 | **met** | Since P12c-13 every published id is listed, and one leaving the list fails (`tests/test_registry.py::TestIdentity::test_no_published_id_has_gone`). None has been renamed, so no alias exists yet |
| FR-033 | **met** | As 16.2 |
| FR-034 | **met** | `tests/structural/test_parameters_are_read.py::test_every_declared_output_is_returned`; chained in a model, As 16.5 |
| FR-035 | **met** | As 16.7 |
| FR-036 | **met** | DynAdjust: since P12c-13 each stage's command, exit code, wall time and the ends of stdout and stderr in the solution's provenance (`tests/test_dynadjust_pipeline.py::TestTheProvenance`); until then the command lines and one exit code. RTKLIB: since P12c-13 the run and the engine's version in every GNSS algorithm's JSON output (`tests/qgis/test_engine_runs.py::TestTheVersion`); until then neither |
| FR-060 | **met** | As 15.4 |
| FR-061 | **met** | The closure, face and sight tolerances are settings (`tests/test_settings_def.py`). The instrument constants — vertical index, EDM additive and scale, prism constants, nominal precisions — are named profiles, by [`15`](./15-ui-menu-and-settings.md) §2.2's decision. Since P12c-16 they are managed from Global Settings, whose Total Station, Level and Gravimeter pages open the profiles window (`tests/qgis/test_profiles_dialog.py::TestFromGlobalSettings`). Since P12c-17 each of those pages names the library its technique's runs read when given none (`tests/qgis/test_settings_reach_the_computation.py`, `tests/qgis/test_profiles_dialog.py::TestTheLibraryARunReads`). Until then each run was given the file |
| FR-062 | **met** | The model and the default temperature, pressure and humidity are settings read by *Preprocess* (`tests/test_settings_def.py`, `tests/structural/test_settings_are_honoured.py`) |
| FR-063 | **met** | The thirteen `gnss.*` settings, every one read (`tests/structural/test_settings_are_honoured.py`) |
| FR-064 | **partly met** | The outlier parameters and the confidence level are settings, and the default sigmas of directions, zenith angles and slope distances (`tests/structural/test_settings_are_honoured.py`). No setting gives a default for the other seventeen observation types: their sigma must come from the data or an instrument profile, or the adjustment refuses rather than invent one ([`05`](./05-uncertainty-and-covariance.md) §5) |
| FR-065 | **met** | Preferred CRS, default epoch and geoid model are settings read as the defaults of the parameters they name (`tests/structural/test_settings_are_honoured.py`); the transformation parameters are published parameter sets with provenance in `core/geodesy/frames.py` ([`15`](./15-ui-menu-and-settings.md) §2.1) |
| FR-066 | **partly met** | The DynAdjust and RTKLIB locations are settings (`tests/qgis/test_engine_install.py`). Working directories and report templates are each algorithm's parameters, not settings, by P12c-6's decision ([`15`](./15-ui-menu-and-settings.md) §2.1) |
| FR-067 | **met** | Language (As 18.3), usage mode (`tests/qgis/test_basic_advanced_identity.py`), units and angle format (`tests/test_number_format.py`) |
| FR-068 | **met** | As 15.6 |
| FR-069 | **met** | Since P12c-16 the profiles window adds, edits, duplicates, deletes, imports and exports them, and chooses the default (`tests/qgis/test_profiles_dialog.py`); the operations and the units they are edited in are tested without QGIS (`tests/test_profile_editing.py`). Profiles exported and imported compute identically (As 15.5). Until then a profile was edited as a document |
| FR-070 | **met** | Since P12c-13 Basic hides the advanced parameters and Advanced shows them (`tests/qgis/test_basic_advanced_identity.py::test_basic_mode_shows_the_reduced_set`). Until then both modes showed the same set and the setting changed nothing. Since P12c-21 Advanced takes hand-written configuration files for both engines: a DynAdjust configuration of options per program (FR-325) and an RTKLIB options file on the four processing modes and *Batch processing* (`tests/qgis/test_engine_runs.py::TestAUsersOwnRtklibOptions`, `tests/test_rtklib_engine.py::TestAUsersOwnOptions`; `specs/08` §2.4). Options GeoComp reads the result back by are refused in both |
| FR-071 | **met** | As 15.7 |
| FR-090 | **met** | As 18.2 |
| FR-091 | **met** | As 18.1; every error and finding in words, `tests/structural/test_message_templates.py` |
| FR-092 | **met** | As 18.3 |
| FR-093 | **met** | As 18.4 |
| FR-094 | **met** | As 18.6 |
| FR-095 | **met** | As 18.5 |
| FR-100 | **met** | `tests/test_models.py::TestProjectSerialisation`, `tests/test_models.py::TestGnssSession` |
| FR-101 | **met** | `tests/test_models.py::TestStation` |
| FR-102 | **met** | Type, stations, values with their uncertainty, epoch and instrument (`tests/test_models.py::TestObservation`). Since P12c-19 and P12c-20 an observation also carries its provenance: the reader or reduction, the file and the records, in network documents and in both stores, schema 6 (`tests/test_observation_provenance.py`, `tests/test_project_store.py`). It is recorded by the four file readers, each checked against the line it names; by the total-station, levelling and gravimetry chains, through their files, to the rows or lines of the field file; and by GNSS, design and benchmark observations. For each field technique the network built through the files equals the one built in memory, provenance included (§1) |
| FR-103 | **met** | `tests/test_models.py::TestObservationTypeRegistry` |
| FR-104 | **met** | `tests/test_models.py::TestCluster`; stored and reloaded bit-identical, As 17.9 |
| FR-105 | **met** | `tests/test_models.py::TestEpoch`; refused where needed rather than assumed, e.g. `tests/test_dynadjust_pipeline.py::TestTheJob::test_a_job_without_a_frame_or_epoch_is_refused` |
| FR-106 | **met** | `tests/test_models.py::TestSolution`; the covariance stored whole, As 17.9 |
| FR-107 | **met** | `tests/structural/test_no_qgis_in_core.py` |
| FR-130 | **met** | `tests/test_project_store.py::TestARoundTrip` |
| FR-131 | **met** | `tests/test_postgis_store.py`, in the `postgis store` job. One observation table with per-type views, by [`17`](./17-persistence-and-interoperability.md) §2's first rule. The processing logs since P12c-13 (`tests/test_project_store.py::TestTheProcessingLog`): `gc_run` was declared in P5 and written by nothing until then |
| FR-132 | **met** | As 17.1 |
| FR-133 | **met** | As 17.2 |
| FR-134 | **met** | `tests/test_project_store.py::TestProvenance` |
| FR-135 | **met** | As 17.3 |
| FR-160 | **met** | Since P12c-13, `.xlsx` as well as CSV, for both field books and for stations' coordinates (`tests/test_spreadsheet_import.py`, `tests/qgis/test_totalstation_algorithms.py::TestTheWholeChain`); until then CSV alone. The mapping saved by name and reused, As 17.4 |
| FR-161 | **met** | As 17.7 |
| FR-162 | **met** | `tests/test_export.py::TestCsv`, `tests/test_export.py::TestTheWorkbook` |
| FR-163 | **met** | As 07.1, and the cluster at full precision As 07.2 |
| FR-164 | **met** | `tests/test_rinex.py` |
| FR-165 | **partly met** | Geoid models imported, applied, recorded and propagated (As 17.8). The deflection of the vertical is not estimated: it needs the undulation's horizontal gradient and a case to check it against, and none is available ([`17`](./17-persistence-and-interoperability.md) §5.5) |
| FR-166 | **met** | As 17.5; a cancelled import leaves the target unchanged, As 17.6 |
| FR-167 | **met** | `tests/qgis/test_basemap_offer.py` |
| FR-200 | **met** | As 05.4 |
| FR-201 | **met** | As 05.1 |
| FR-202 | **met** | As 05.5 |
| FR-203 | **met** | As 05.5; in the report, As 19.8 |
| FR-204 | **met** | As 05.3 |
| FR-205 | **met** | Curvature and refraction, the reductions to the ellipsoid and to the projection plane, each carrying the uncertainty of the heights and scale it used (`tests/test_total_station.py::TestGeometricReductions`). Applied by *Classical network* since P12c-14, FR-405's row |
| FR-206 | **met** | A baseline cluster kept whole through a combined adjustment (`tests/test_integration.py::TestCriterion5Clusters::test_the_baseline_cluster_survives_whole`) and through DynaML, As 07.2 |
| FR-207 | **met** | As 14.4; not significant is not zero, As 14.7 |
| FR-208 | **met** | As 05.6 |
| FR-220 | **met** | As 06.2; agreeing with DynAdjust, As 06.6 |
| FR-221 | **met** | A correlated cluster weighted by its whole covariance (`tests/test_integration.py::TestCriterion5Clusters`) |
| FR-222 | **met** | Free and constrained, As 06.2; weighted stations (`tests/test_weighted_constraints.py`) |
| FR-223 | **met** | Convergence threshold and iteration limit are parameters of *Adjust network*, the iteration count an output; non-convergence reported, not returned (`tests/test_adjustment.py::TestFailureModes::test_non_convergence_is_reported_not_returned`) |
| FR-224 | **met** | `tests/test_adjustment.py::TestSolutionAssembly` |
| FR-225 | **met** | Redundancy numbers summing to the degrees of freedom (`tests/test_adjustment.py::TestLevellingAdjustment::test_redundancy_numbers_sum_to_the_degrees_of_freedom`); standardised residuals, As 06.3 |
| FR-226 | **met** | As 06.4 |
| FR-227 | **met** | 1D `tests/test_adjustment.py::TestLevellingAdjustment`, 2D `tests/test_adjustment.py::TestTrilateration`, 3D `tests/test_geocentric_frame.py::TestTheNetworkIsRecovered` |
| FR-250 | **met** | As 06.7 |
| FR-251 | **met** | As 06.3 and 06.7 |
| FR-252 | **met** | Since P12c-13 a stricter α or a higher power is shown to enlarge every MDB by the same factor (`tests/test_statistics.py::TestReliability::test_alpha_and_beta_are_the_users_and_move_every_mdb`); until then only the defaults were exercised |
| FR-253 | **met** | `tests/test_statistics.py::TestReliability::test_external_reliability_is_reported_alongside_internal` |
| FR-254 | **met** | Ellipses and ellipsoids at a chosen confidence (`tests/test_statistics.py::TestEllipses`), relative ones As 19.3, drawn As 19.2 |
| FR-255 | **met** | Recorded and never deleted (`tests/test_models.py::TestObservation`, `tests/test_models.py::TestNetwork`); never automatic, so re-adjusting is always the user's run. Since P12c-13 the report lists each observation set aside with its reason (`tests/qgis/test_adjustment_report.py::TestWhatWasSetAsideIsSaid`); until then it counted the active ones and said nothing of the rest. An observation is set aside or restored by editing its status in the network document: no dialog does it. P12c-21 measured that on the DynAdjust path a set-aside member of a GNSS cluster or a direction set was written as active and used, and a set-aside lone observation made the result refuse to read back; and the core refused a cluster with a member set aside. Since P12c-22 both engines adjust what remains, under the cluster's covariance cut to it, and agree (`tests/test_dynadjust_geocentric.py::TestWhatWasSetAside`, and against DynAdjust 1.4.0 in `TestWhatWasSetAsideAgainstARealEngine`) |
| FR-270 | **met** | As 06.5 |
| FR-271 | **met** | `tests/test_statistics.py::TestPreAnalysis::test_a_design_reports_expected_reliability_not_only_precision` |
| FR-272 | **met** | `tests/qgis/test_preanalysis_dialog.py` |
| FR-273 | **met** | `tests/test_statistics.py::TestInspection` |
| FR-300 | **met** | `tests/test_engines.py::test_a_configured_path_wins`, `tests/test_engines.py::test_a_configured_directory_is_searched_for_the_program`; set in Global Settings, `tests/qgis/test_engine_install.py` |
| FR-301 | **partly met** | As 21.4: DynAdjust is acquired from *Install an engine*; RTKLIB is located, not acquired |
| FR-302 | **met** | Detected and recorded (`tests/test_rtklib_engine.py::TestVersion`, `tests/test_dynadjust_pipeline.py::TestVersionDetection`); warned about, by every algorithm that runs an engine since P12c-11 (`tests/qgis/test_engine_runs.py::TestTheVersion`) |
| FR-303 | **met** | One runner, version record and discovery for both engines (`geocomp/engines/base.py`, `tests/test_engines.py`); the RTKLIB adapter was added in P7 without changing it ([`08`](./08-engine-rtklib.md) §2) |
| FR-304 | **met** | Captured (`tests/test_engines.py`); a timeout told from a failure (`tests/test_engines.py::test_a_timeout_is_distinguished_from_a_failure`) and reported with elapsed time and limit since P12c-11 (`tests/test_engine_timeouts.py`); the limit configurable on every algorithm that runs an engine (`tests/qgis/test_engine_runs.py::TestTheTimeLimit`) |
| FR-305 | **met** | `tests/qgis/test_engine_messages.py`; every engine failure's template shows the engine's own words, `tests/structural/test_message_templates.py::test_an_engine_failure_shows_the_engines_own_message` |
| FR-306 | **met** | As 07.7 and 21.3; `tests/test_rtklib_engine.py::TestGracefulAbsence` |
| FR-320 | **partly met** | From a GeoComp network document (`tests/test_dynadjust_pipeline.py::TestPrepare`), which the field-book imports make from CSV and `.xlsx` and the GNSS and integration algorithms make from their results. Since P12c-24 also straight from a project store, a GeoPackage or a PostgreSQL schema (`tests/qgis/test_engine_runs.py::TestFromTheProjectStore`, `tests/qgis/test_postgis_project.py::TestAdjustingStraightFromTheDatabase`). Not from a QGIS layer of the user's own design: stations as points and observations as table rows would need a field mapping that does not exist (`specs/07` §4) |
| FR-321 | **met** | As 07.3; which stages ran and why, `tests/test_dynadjust_pipeline.py::TestThePlan`. `dnaplot` is not driven: GeoComp draws the result itself (FR-324) |
| FR-322 | **met** | As 07.4 |
| FR-323 | **met** | `tests/test_dynadjust_solution.py`; cross-validated against the in-house Solution, As 06.6 |
| FR-324 | **met** | Since P12c-13, *Adjust network (DynAdjust)* offers the in-house adjustment's result layers, and a GDA2020 solution is drawn under its own frame's name (`tests/qgis/test_engine_runs.py::TestADynAdjustResultOnTheMap`, `tests/test_display.py::TestTheGrid`). Until then it wrote its solution document and no layer, and the display grid refused a frame GeoComp holds no transformation for. Displacements and thematic maps follow from the Solution, as for the in-house one |
| FR-325 | **met** | Since P12c-21 *Adjust network (DynAdjust)* can stop after writing the input, with a manifest holding what reading the result back needs, and *Run a prepared DynAdjust job* runs the folder as it now is, recording which files were edited (`tests/qgis/test_engine_runs.py::TestStopEditAndRunLater`, `tests/test_dynadjust_pipeline.py::TestStopEditAndRunLater`; tier 4, a station constrained by hand reaches the solution: `TestAgainstARealEngine::test_a_prepared_job_runs_the_input_as_the_user_left_it`). A user configuration passes options to each stage, and options GeoComp sets itself are refused (`TestTheUsersConfiguration`). Until then the input was kept only when asked, and no algorithm stopped before execution. Since P12c-22 a measurement, or one direction of a set, flagged `Ignore` by hand is read back set aside, as GeoComp would set it aside itself (`tests/test_dynadjust_geocentric.py::TestIgnoredByHand`; tier 4, the same adjustment to the printed digit). A measurement added or removed is refused before anything runs, because its rows can no longer be matched (`specs/07` §3) |
| FR-350 | **met** | `tests/test_models.py::TestGnssSession`, As 08.1 |
| FR-351 | **met** | As 08.1 |
| FR-352 | **met** | As 08.6 |
| FR-353 | **met** | As 08.7 |
| FR-354 | **met** | `tests/test_rtklib_engine.py::TestConfiguration`; fed back to the engine, As 08.2 |
| FR-355 | **met** | As 08.5; the run's time limit and its record since P12c-11 and P12c-13 (`tests/qgis/test_engine_runs.py`) |
| FR-356 | **met** | As 08.3 and 08.4 |
| FR-357 | **met** | Baselines and trajectories as layers, and the network document for a joint adjustment (`tests/qgis/test_gnss_layers.py`) |
| FR-358 | **met** | Static and kinematic profiles, precise ephemerides and the atmospheric models as configuration (`tests/test_rtklib_engine.py::TestConfiguration`); quality indicators read back, As 08.3; the products, As 08.6 |
| FR-359 | **partly met** | The comparison and its significance test, As 11.6, written as one table with a row per configuration. The side-by-side dialog [`11`](./11-module-gnss.md) §6 describes is not built |
| FR-400 | **met** | As 09.1 |
| FR-401 | **met** | `tests/test_total_station.py::TestAtmosphere` |
| FR-402 | **met** | `tests/test_total_station.py::TestInstrumentCorrections`; injected errors recovered, As 09.4 |
| FR-403 | **met** | `tests/test_total_station.py::TestEdmCorrections` |
| FR-404 | **met** | `tests/test_total_station.py::TestBasicReduction` |
| FR-405 | **met** | Curvature and refraction in trigonometric heighting (`tests/test_total_station.py::TestGeometricReductions`, `tests/test_trigonometric_levelling.py`). Since P12c-14 the reductions to the ellipsoid and to the grid are applied by *Classical network*, in a 2D adjustment on a projected CRS: a network observed on the ground at a UTM zone's edge fails to fit its grid control as measured and fits it to 0.1 mm reduced (`tests/test_grid_reduction.py::TestANetworkAtTheEdgeOfAZone`), through the algorithm with QGIS's scale factor (`tests/qgis/test_grid_reduction.py`). Not in a 3D adjustment, whose frame is not a grid ([`09`](./09-module-total-station.md) §2.6) |
| FR-406 | **met** | Open, closed and connected, with closure against tolerance, against constructed truth (`tests/test_survey_computations.py::TestTraverse`); a published example waits on W-07, row 09.5 |
| FR-407 | **met** | `tests/test_survey_computations.py::TestResection`; the danger circle refused, As 09.6 |
| FR-408 | **met** | `tests/test_survey_computations.py::TestForwardIntersection` |
| FR-409 | **met** | As 09.7; `tests/test_adjustment.py::TestTrilateration`, `tests/test_adjustment.py::TestTriangulateration` |
| FR-410 | **met** | `tests/test_trigonometric_levelling.py::TestRadialHeightDifference`, `tests/test_trigonometric_levelling.py::TestLeapFrog` |
| FR-411 | **met** | `tests/test_survey_computations.py::TestRadiation` |
| FR-412 | **met** | As 09.8; one propagation through the whole chain, As 05.3 |
| FR-500 | **met** | Against field books generated by inverting the equations under test (`tests/test_levelling.py::TestEqualSights`); a published example waits on W-05, row 10.1 |
| FR-501 | **met** | `tests/test_levelling.py::TestReciprocalSights`; a published example waits on W-05 |
| FR-502 | **met** | `tests/test_levelling.py::TestExtremeSights`; the cluster helps, As 10.3 |
| FR-503 | **met** | Line and loop closures against the tolerance `level.tolerance_coefficient` sets (`tests/test_levelling.py::TestClosures`), and a failing line held back from the adjustment, As 10.8 |
| FR-504 | **met** | By length and by setups, consistent (`tests/test_levelling.py::TestWeighting`, `tests/test_levelling.py::TestTheNetwork::test_length_and_setup_weighting_agree_on_the_heights`); a network published under both waits on W-06, row 10.4 |
| FR-505 | **met** | As 10.7 |
| FR-600 | **met** | `geocomp:gnss_absolute_static` and `gnss_absolute_kinematic` under *GNSS > Absolute* (`tests/test_registry.py::TestNesting`) |
| FR-601 | **met** | `geocomp:gnss_relative_static` and `gnss_relative_kinematic` under *GNSS > Relative* (`tests/test_registry.py::TestNesting`) |
| FR-602 | **met** | As 11.4; the cluster reaches an adjustment, `tests/test_gnss_baselines.py::TestTheClusterReachesAnAdjustment` |
| FR-603 | **partly met** | Per session, the fixed fraction, satellite count and ratio (`tests/test_gnss_baselines.py::TestTheEngineBridgeRefusesWhatItCannotUse::test_the_quality_summary_carries_what_the_run_achieved`); per epoch, the trajectory layer's status and quality columns (`tests/qgis/test_gnss_layers.py::TestTheTrajectoryLayer`). Dilution of precision is always absent: `rnx2rtkp` does not write it, and `core/techniques/gnss/quality.py` leaves the field empty rather than put another quantity in it |
| FR-604 | **met** | As 08.8 |
| FR-700 | **met** | `tests/test_gravimetry_network.py::TestTheDatum`; absolute values weighted, not fixed, As 12.5 |
| FR-701 | **met** | Tide (`tests/test_gravimetry_readings.py::TestTheTide`), scale (`tests/test_gravimetry_network.py::TestTheCalibrationUncertaintyReachesTheDifferences`), drift (As 12.2). Agreement with a published scale example waits on W-02, row 12.1 |
| FR-702 | **met** | As 12.3 |
| FR-703 | **met** | As 12.8 |
| FR-800 | **met** | `tests/qgis/test_integration_algorithms.py::TestGnssAndTotalStation`; clusters intact, As 13.5 |
| FR-801 | **met** | `tests/qgis/test_integration_algorithms.py::TestTotalStationAndLevel` |
| FR-802 | **met** | `tests/qgis/test_integration_algorithms.py::TestGnssAndLevel`; no geoid refuses, As 13.2 |
| FR-803 | **met** | As 13.8; `tests/qgis/test_integration_algorithms.py::TestMultiple` |
| FR-804 | **met** | As 13.2 |
| FR-805 | **met** | As 13.3; reported per technique, As 13.7 |
| FR-830 | **met** | A solution without an epoch cannot be built (`tests/test_models.py::TestSolution`); campaigns are bound to an epoch (`tests/test_models.py::TestProjectSerialisation`); refused where missing, As 14.2 |
| FR-831 | **met** | As 14.1 and 14.2 |
| FR-832 | **met** | As 14.1 |
| FR-833 | **met** | As 14.4, with the covariance FR-207 asks for |
| FR-834 | **met** | As 14.4; not significant is not zero, As 14.7 |
| FR-835 | **met** | As 14.5 |
| FR-836 | **met** | `tests/test_monitoring.py::TestStrain` |
| FR-837 | **met** | As 14.9 |
| FR-838 | **met** | As 14.8 |
| FR-900 | **met** | Each drawn with the style it ships with: adjusted stations, residuals and error ellipses (`tests/qgis/test_result_layers.py::TestTheStylesLoad`), GNSS baselines (`tests/qgis/test_gnss_layers.py::TestTheStyleLoads`), displacement vectors and velocities (`tests/qgis/test_monitoring_algorithms.py::TestLayers`). Since P12c-13 the produced layer is compared with its shipped style; until then the adjustment's layers were held only to having a renderer, which an unstyled layer has too, and nothing ran the displacement layers' post-processor |
| FR-901 | **met** | As 19.2 |
| FR-902 | **met** | As 19.5 |
| FR-903 | **met** | As 19.6 |
| FR-904 | **met** | As 19.4 |
| FR-905 | **met** | As 19.1; through a model as well as the toolbox, `tests/qgis/test_model_chain.py::TestRd01ArrivesAsStyledLayers` |
| FR-930 | **met** | `tests/qgis/test_adjustment_report.py::TestItCarriesEverySection`; the parameters' scopes, the inputs by digest and the software versions, `tests/qgis/test_adjustment_report.py::TestItIsDefensible` |
| FR-931 | **met** | One HTML file, printed to PDF by any browser, and print layouts (`tests/qgis/test_print_layouts.py`); an organisation's template used and what it leaves out reported (`tests/qgis/test_adjustment_report.py::TestATemplateCanChangeTheLayout`, `tests/test_report_templates.py`). The template is chosen per run rather than in Global Settings, which is FR-066's row |
| FR-932 | **met** | Displacements, decisions and the map (`tests/qgis/test_monitoring_algorithms.py::TestCompareEpochs::test_the_report_carries_the_decisions_and_the_map`), the time series (`tests/qgis/test_monitoring_algorithms.py::TestTimeSeries::test_the_series_report_plots_every_station`), both drawn from the layers' geometry (`tests/test_monitoring_drawing.py::TestReportMap`, `tests/test_monitoring_drawing.py::TestReportPlot`) |
| FR-950 | **partly met** | Nine of the twelve reference datasets have an expected result and a test; RD-05 is not vendored, RD-08's published half waits on W-01, RD-10 is P13's (row 20 3). Only RD-01 ships with the plugin (`tests/test_tutorial_dataset.py::TestItShips`); the others are in the repository |
| FR-951 | **partly met** | The protocol is written, §5, with how a difference is classified, investigated and published, and GeoComp's half of it, the comparison export, As 20.7. It is a section of a specification rather than documentation a comparison's author is handed, and it has never been run (W-12): P13's |
| FR-952 | **partly met** | RD-01 ships as a tutorial dataset with its walkthrough, and every number the walkthrough states is checked against the files (`tests/test_tutorial_dataset.py::TestTheTutorialTellsTheTruth`, `tests/qgis/test_tutorial.py::TestFollowingIt`). One module, in English; tutorials for every module in three languages and worked QGIS projects are P13's |
| FR-953 | **met** | Public, with CI on every push (`.github/workflows/test.yml`, `.github/workflows/build.yml`), every algorithm's help held to its parameters (`tests/qgis/test_algorithm_help.py`), and the specifications in `specs/`. Teaching material is FR-952's row |
| FR-954 | **open** | No contribution guide. §8 says what it must cover and P13 writes it; how companies and public bodies take part is the maintainer's to decide, not an audit's to draft |
| FR-955 | **partly met** | What a report needs is kept: a DynAdjust failure that names its files leaves them and says where (`tests/qgis/test_engine_runs.py::TestADynAdjustRefusal`), an RTKLIB working directory is kept on request with its configuration (`tests/qgis/test_engine_runs.py::TestTheWorkingDirectory`), and the command and what the engine said are in the result (`tests/qgis/test_engine_runs.py::TestTheVersion`). Nothing packages them into one report for upstream, as §8 describes: P13's |
| NFR-001 | **met** | `metadata.txt` declares 4.0 (`tests/structural/test_version_consistency.py::test_minimum_qgis_is_the_targeted_series`); the releases under test are read from QGIS's own channels and held to this requirement's reading, stable until a 4.x LTR exists (`tests/test_qgis_versions.py`), As 21.5 |
| NFR-002 | **met** | `tests/structural/test_no_qgis_in_core.py` |
| NFR-003 | **met** | As 21.5. How far each engine is installed on each system is FR-301's row |
| NFR-004 | **met** | Processing runs every algorithm off the GUI thread (FR-008's row). Since P12c-15 the panels read solutions, stores and series in a task (`tests/qgis/test_results_panel.py::TestNothingSlowOnTheGuiThread`, `tests/qgis/test_task_service.py::TestRunInBackground`), and their tables fill, filter and sort 5,000 rows each within the bound; since P12c-13 the field-mapping preview reads only the rows it shows (`tests/test_spreadsheet_import.py::TestAPreviewReadsOnlyWhatItShows`). Measured on the GUI thread: 46 ms for a 2,500-station solution; the pre-analysis dialog's evaluation, the one computation left there, 177 ms at 225 stations drawn by hand ([`03`](./03-architecture.md) §3.5) |
| NFR-005 | **met** | Since P12c-13, every package the plugin imports is one [`03`](./03-architecture.md) §3.7 records (`tests/structural/test_dependencies.py`). The first run found two that it did not: `psycopg2`, recorded only in specs/17, and QGIS's `processing` |
| NFR-006 | **partly met** | Every code and finding has words naming what failed, with the values that failed (`tests/structural/test_message_templates.py`), and a core error that leaves an algorithm reaches the user as those words, not as a traceback or a code (`tests/qgis/test_inputs_are_named.py::test_an_input_of_the_wrong_kind_is_refused_and_named`). That each also says what the user can do is not checked: most do, and some say what and why and stop |
| NFR-007 | **met** | As 08.2; the solution identical by every route, provenance aside (`tests/qgis/test_model_chain.py::TestEveryWayGivesOneAnswer`), and its report byte for byte (`tests/qgis/test_adjustment_report.py::TestItIsDeterministic`) |
| NFR-008 | **met** | As 06.8 |
| NFR-009 | **met** | As 21.7; `tests/structural/test_version_consistency.py::test_licence_is_declared_as_gpl` |
| NFR-010 | **met** | As 08.7; a PostGIS login reaches no log, result, copy or setting (`tests/qgis/test_postgis_project.py`) |
| NFR-011 | **met** | Since P12c-13 every module of the plugin has a function the suite runs, checked after the QGIS job (`scripts/check_coverage.py`, `tests/test_coverage_check.py`); the one exemption, `classFactory`, runs in a QGIS of its own. Until then only `core/` was measured. The core runs with no QGIS and no engine in the `core` jobs (`.github/workflows/test.yml`), every public function reached, As 20.6 |
| NFR-012 | **partly met** | Held since P12c-13 by `tests/structural/test_public_interfaces.py`: of the 1,347 classes, functions and methods one module imports from another, 399 have no docstring and 51 are not fully annotated, frozen in lists that may only shrink |
