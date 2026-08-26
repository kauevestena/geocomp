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
| **RD-02** | Worked variance-propagation examples from Ghilani (2010) and Gemael | [`05-uncertainty-and-covariance.md`](./05-uncertainty-and-covariance.md) | To assemble |
| **RD-03** | Worked network adjustments from the same sources — free and constrained, 2D and 3D | [`06-adjustment-core.md`](./06-adjustment-core.md) | To assemble |
| **RD-04** | Levelling networks with published solutions, all three schemes | [`10-module-levelling.md`](./10-module-levelling.md) | To assemble |
| **RD-05** | DynAdjust's own example datasets | [`07-engine-dynadjust.md`](./07-engine-dynadjust.md) | From upstream |
| **RD-06** | GNSS reference data with published official coordinates (IBGE, NGS, Geoscience Australia) | [`08-engine-rtklib.md`](./08-engine-rtklib.md), [`11-module-gnss.md`](./11-module-gnss.md) | To assemble |
| **RD-07** | Gravimetric network with a published solution | [`12-module-gravimetry.md`](./12-module-gravimetry.md) | To assemble |
| **RD-08** | Multi-epoch monitoring series with known displacements — a published deformation example, plus synthetic data with injected motion | [`14-multi-epoch-monitoring.md`](./14-multi-epoch-monitoring.md) | To assemble |
| **RD-09** | Synthetic networks with injected blunders of known size and location | Data snooping, reliability | Generated |
| **RD-10** | Field campaign data collected by students (`tex §Participação dos alunos`) | End-to-end, real-world | Project activity |

**RD-01 is special.** It is the author's own prototype data, it exercises the whole first vertical slice, and
it contains a real transcription blunder (a 1.000 m face-pair distance discrepancy —
[`09-module-total-station.md`](./09-module-total-station.md) §2.1) which becomes a detection test. It ships
with the plugin as a tutorial dataset (FR-952).

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
