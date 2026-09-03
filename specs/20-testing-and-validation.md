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
| **T2 — Reference** | T1 | Every commit | Reproduce published results (§3) |
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

## 3. Reference datasets (FR-950)

Datasets with an independently known correct answer. Each has an id, a documented provenance, a licence
permitting redistribution, and an expected-results file.

| Id | Dataset | Validates | Status |
|---|---|---|---|
| **RD-01** | `topo_test/` — the project author's total-station triangle (3 stations, PD/PI, distances, zenith angles) | Face reduction, corrections, basic reductions, small-network adjustment, the field-mapping importer | **In repository** |
| **RD-02** | Covariance-propagation reference cases, each validated three ways: a hand-derived closed form, the module's first-order propagation, and a derivative-free Monte Carlo simulation | [`05-uncertainty-and-covariance.md`](./05-uncertainty-and-covariance.md) | **Implemented** (P1). See the note below |
| **RD-03** | Network adjustments with a known truth — 1D levelling, 2D trilateration, 2D triangulateration, free and constrained | [`06-adjustment-core.md`](./06-adjustment-core.md) | **Implemented** (P2), in `tests/networks.py`. Same citation note as RD-02 |
| **RD-04** | Levelling field books generated from known heights, all three schemes, plus a loop with an injected blunder | [`10-module-levelling.md`](./10-module-levelling.md) | **Implemented** (P4), in `tests/reference_levelling.py`. Same citation note as RD-02 and RD-03 |
| **RD-05** | DynAdjust's own example datasets | [`07-engine-dynadjust.md`](./07-engine-dynadjust.md) | From upstream |
| **RD-06** | GNSS reference data with published official coordinates (IBGE, NGS, Geoscience Australia) | [`08-engine-rtklib.md`](./08-engine-rtklib.md), [`11-module-gnss.md`](./11-module-gnss.md) | To assemble — candidates in [`22`](./22-reference-data-sources.md) §5 |
| **RD-07** | Gravimetric network with a published solution | [`12-module-gravimetry.md`](./12-module-gravimetry.md) | To assemble — candidates in [`22`](./22-reference-data-sources.md) §5 |
| **RD-08** | Multi-epoch monitoring series with known displacements — a published deformation example, plus synthetic data with injected motion | [`14-multi-epoch-monitoring.md`](./14-multi-epoch-monitoring.md) | To assemble — candidates in [`22`](./22-reference-data-sources.md) §5 |
| **RD-09** | The RD-03 networks with a blunder of known size injected at a known place | Data snooping, reliability | **Implemented** (P2), in `tests/networks.py` |
| **RD-10** | Field campaign data collected by students (`tex §Participação dos alunos`) | End-to-end, real-world | Project activity |

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

**RD-02, RD-03 and RD-04 note — validation complete, citation outstanding.** The cases implemented in
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
every analytic Jacobian matches complex-step differentiation. Several of these would catch errors that
matching a printed answer would not.

What remains for both is *citation*: transcribing the published worked examples so the project can state
agreement with the standard references by name, which matters for the commercial-comparison protocol (§5)
and for the teaching material (FR-952).

**A source for this has been found** and is described in
[`22-reference-data-sources.md`](./22-reference-data-sources.md) §2: GNU Gama redistributes the 61 example
networks of Krumm's *Geodetic Network Adjustment Examples* (Universität Stuttgart, 2020), **45 of them with
the adjusted coordinates as published**, each citing the textbook it came from by edition and page — Ghilani
and Niemeier among them. It no longer needs a contributor who owns the books, only a reader for one
line-oriented text format.

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
| Against a published worked example | The precision printed in the source |
| Between the two engines (§4) | The table in §4 |
| Against commercial software | Documented per comparison; unexplained differences are defects |
| Reproducibility of a run | **Bit-identical** (NFR-007) |

Bit-identical reproducibility requires: deterministic iteration order, explicit and stable observation
ordering, no reliance on set or dictionary ordering for numeric outcomes, and pinned engine versions
recorded in provenance.

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
   documented reason why it must be manual.
