# 06 — Adjustment core

**Status:** Draft
**Requirements covered:** FR-220…FR-227, FR-250…FR-255, FR-270…FR-273.
**Source:** tex §Fundamentos do Ajustamento de Observações; §Análise de Qualidade de Redes Geodésicas;
§Justificativa pedagógica; O1, O4.
**Decision:** [`adr/0002-in-house-lsq-core.md`](./adr/0002-in-house-lsq-core.md).

---

## 1. Scope of this module

GeoComp implements least-squares adjustment itself, *in addition to* driving DynAdjust (FR-220). The reasons
are set out in ADR-0002; in brief: gravimetric networks have no DynAdjust measurement type (FR-700),
pre-analysis needs the design matrix before any observation exists (FR-270), the teaching profile needs every
intermediate quantity visible, CI must run without engine binaries, and having two independent
implementations produce the same answer is the strongest correctness evidence available (roadmap P6).

Division of labour with DynAdjust:

| | In-house core | DynAdjust |
|---|---|---|
| Teaching-scale and project-scale networks | ✔ primary | ✔ cross-check |
| Gravimetric networks | ✔ only option | ✖ unsupported |
| Pre-analysis / design simulation | ✔ only option | ✖ |
| Continental-scale networks (≫ 10⁴ stations) | ✖ (NFR-008) | ✔ primary, with segmentation |
| Reference-frame transformation, geoid application at scale | ✖ | ✔ |

Both produce the same `Solution` ([`04-data-model.md`](./04-data-model.md) §2.8).

---

## 2. The mathematical model

### 2.1 Parametric (observation-equation) model

Following the proposal (`tex §Fundamentos do Ajustamento de Observações`):

$$\mathbf{L}_b + \mathbf{v} = \mathbf{A}\mathbf{x} + \mathbf{L}_0$$

minimising **v**ᵀ**Pv**, giving

$$\mathbf{x} = (\mathbf{A}^{T}\mathbf{P}\mathbf{A})^{-1}\mathbf{A}^{T}\mathbf{P}(\mathbf{L}_b - \mathbf{L}_0)$$

with **P** derived from the observation covariance matrix, **P** = σ₀²·**Σ**_Lb⁻¹.

**The full covariance matrix is used, not just its diagonal** (FR-221). Correlated clusters — GNSS baselines,
direction sets — contribute block-diagonal terms. This is a requirement, not an optimisation: treating a GNSS
baseline's three components as independent misstates every statistic that follows.

### 2.2 Non-linearity and iteration (FR-223)

The observation equations are non-linear in the coordinates, so the solution iterates:

1. Compute **L**₀ and **A** at the current approximate parameters.
2. Solve for **x**.
3. Update the parameters; repeat.

Convergence when max|**x**| falls below a configurable threshold (default: 0.1 mm for coordinates, and the
angular equivalent for orientation parameters) or a maximum iteration count is reached. The iteration count,
the final maximum correction, and whether convergence was achieved are all reported (§2.9 of the data model).
**Non-convergence is a reported failure, never a silently returned last iterate.**

Approximate coordinates matter. GeoComp provides an automatic approximate-coordinate generator (traverse
propagation, resection, intersection — see [`09-module-total-station.md`](./09-module-total-station.md)) and
reports which stations got theirs from where.

### 2.3 Parameters

Beyond station coordinates, the adjustment estimates: direction-set orientation parameters (one per set),
scale and refraction coefficients when the user enables them, gravimeter drift parameters (FR-702), geoid
undulations where orthometric observations meet ellipsoidal heights ([`13`](./13-module-integration.md) §3.2),
and transformation parameters where a solution is being related to another frame.

**A direction's orientation belongs to its setup, and never to nobody** **[V]**. The owner is the direction's
`setup_id`; else an explicit `meta["orientation_owner"]` (two setups sharing one — a pillar occupied twice);
else **its set's cluster**, because a direction set is one setup's by construction and a direction outside a
set cannot be constructed (`observation_requires_cluster`). Until P9a a direction with no setup id was given
no orientation unknown and adjusted as an absolute azimuth — the Krumm reader was fixed for exactly this
([`22`](./22-reference-data-sources.md) §2.2), and P9a found the DynaML reader doing the same, a set read back
38° from its own readings. The rule is now the core's (`parameters.orientation_owner`), not each reader's.

#### The geocentric frame (P9a) [V]

`Frame.GEOCENTRIC_3D` estimates each station's ECEF X, Y, Z and evaluates every observation **in its own
station's horizon** — the ellipsoidal normal at that station (GRS80), with instrument and target heights
along each end's own normal. It is what a combination needs: a flat frame's single "up" is wrong by
`d²/2R` in height, 0.7 m at 3 km, and GNSS vectors are geocentric to begin with. The Jacobians are exact,
the turning of each station's horizon with its position included, and are checked against numerical
derivatives for every type. It holds slope and horizontal distances, zenith and vertical angles,
azimuths, directions, horizontal angles, height differences (ellipsoidal or orthometric, which the
observation must state), ellipsoidal and orthometric heights, GNSS baselines (ECEF, or `LOCAL` in the base's
horizon) and GNSS points; any other type is refused by name (`observation_type_not_geocentric`) — an
ellipsoid distance and the astronomic types among them. The deflection of the vertical is not modelled:
astronomic and geodetic verticals are taken as one.

**Held positions** in this frame are cartesian or geodetic. A geodetic hold is all three of latitude,
longitude and height or nothing: one held in part constrains a combination no subset of X, Y, Z expresses and
is refused, and a weighted one has its covariance carried to X, Y, Z through the conversion's Jacobian. Before
this rule the constraint's names were matched against `x`, `y`, `z`, found nothing, and **left a
geodetically held station free** — caught by a test before the frame shipped. A held height must be
ellipsoidal (§3.2 of [`13`](./13-module-integration.md) says how an orthometric benchmark enters).

It is cross-validated against DynAdjust on a combined GNSS and total-station survey
([`07`](./07-engine-dynadjust.md) §6.3): the same files, coordinates within half the printed 0.1 mm.

### 2.4 Solving

Normal equations are formed and solved by Cholesky factorisation of **A**ᵀ**PA**, exploiting sparsity where
SciPy is available and falling back to dense NumPy otherwise
([`03-architecture.md`](./03-architecture.md) §3.7). For ill-conditioned systems, QR on the weighted design
matrix is available as an alternative with better numerical behaviour.

> **State, as of P2.** The dense NumPy path is implemented — Cholesky, falling back to QR when Cholesky
> fails numerically — and is correct for every network. The **sparse path is not yet implemented**; it
> belongs to P12 with the rest of the work against NFR-008, because it needs a network large enough to show
> that it helps. [`adr/0008-scipy-and-network-scale.md`](./adr/0008-scipy-and-network-scale.md) records the
> decision and what it means for NFR-008. SciPy is used today only for the statistical distributions, and
> there too the NumPy path is the reference implementation.

#### 2.4.1 Network scale, as built (P12c)

**Which path.** `core/adjustment/scale.py` decides before anything the size of the network is allocated.
The dense path holds **A**, **P**, **N**, **Q**ₓₓ and **Q**ᵥᵥ in full, about `8 (6m² + 4mn + 2n²)` bytes for
m rows and n unknowns — the m² terms dominate, since **Q**ᵥᵥ is m × m. `AdjustmentOptions.solver` is
`"auto"` by default:

| Dense footprint | SciPy present | SciPy absent |
|---|---|---|
| ≤ 1 GiB (`SPARSE_ABOVE`, about 1,050 stations of a braced plane grid) | dense | dense |
| above, within half the machine's physical memory | **sparse** | dense |
| above half the machine's memory | **sparse** | refused: `adjustment_needs_scipy`, naming SciPy and, beyond 10,000 stations, DynAdjust's segmentation |

The choice depends on the network and the machine, never on the memory free at the moment, and the
solution's provenance records it (`solver`). `"dense"` and `"sparse"` force a path; forced dense beyond the
machine's half is refused (`adjustment_too_large_for_dense`), as is forced sparse without SciPy. Pre-analysis
(§5) takes the same decision.

**The sparse path** (`core/adjustment/sparse.py`, imported only when chosen) assembles **A** compressed by
row from the same linearisation as the dense path (`normal_equations.linearise`) and **P** as its diagonal
blocks (`core/adjustment/blocks.py`), and factorises **N** — bordered by **G** for an inner or minimum
constraint — with SuperLU under a minimum-degree ordering of **N**'s own pattern. COLAMD, SuperLU's default,
filled the 10,000-station factor fifty times over and took 83 s where this takes 0.2 s. The inverse is never
formed: one sweep over **Q**ₓₓ's columns keeps each owner's block (a station's components, a setup's
orientation, a session's drift), **Q**ᵥᵥ over **P**'s blocks, and each row's ‖**Q**ₓₓ**A**ᵀ**P**eᵢ‖ for the
external reliability (`(P A C)` row by row over column chunks C, since **Q**ₓₓ² = Σ CCᵀ). Any other entry of
**Q**ₓₓ is solved for when asked. The rank is examined on the first and the final system — densely up to
2,000 unknowns, as the dense path does; beyond, by Lanczos and shift-invert Lanczos on the same factorisation,
reporting up to 12 undetermined directions with the same message.

**What the sparse path does not give.** The full parameter covariance: its solution carries each station's
block and `parameter_covariance` is empty, since a block-diagonal stand-in would assert that every two
stations are uncorrelated. A comparison of epochs then takes each epoch's stations as uncorrelated with one
another and says so (`station_blocks_only`, [`14`](./14-multi-epoch-monitoring.md) §8.1). Variance component
estimation reads all of **Q**ᵥᵥ and is always dense ([`13`](./13-module-integration.md) §4.1).

**Agreement.** `tests/test_sparse_adjustment.py` compares the two paths on held, weighted and free plane
networks, a levelling loop and the geocentric combined survey with its correlated baseline cluster:
coordinates, σ̂₀², every station's covariance and ellipse, **Q**ᵥᵥ within each block of **P**, the
redundancy numbers, the w-tests, the MDBs and the external reliability, to 1e-9 relative or better. And
`pytest --sparse`, run in CI's QGIS job, adjusts every network of the whole suite on the sparse path. On a
1,600-station braced grid the two paths agree to 9e-13 m in the coordinates, 4e-11 relative in **Q**ₓₓ's
diagonal and 1.3e-10 in the external reliability.

**Measured** (P12c, on braced plane grids — every square's sides and both diagonals, two stations held —
with 4 CPUs and 15 GB). Dense: Python's peak allocation by `tracemalloc`; sparse: the process's peak
resident memory, interpreter included, so the two columns are not the same measure and the sparse one errs
high.

| Stations | Rows | Unknowns | Dense | Dense peak | Sparse | Sparse peak |
|---|---|---|---|---|---|---|
| 100 | 342 | 196 | 0.17 s | 7 MiB | — | — |
| 400 | 1,482 | 796 | 2.0 s | 132 MiB | — | — |
| 900 | 3,422 | 1,796 | 13.4 s | 698 MiB | — | — |
| 1,600 | 6,162 | 3,196 | 48 s | (2.6 GB estimated) | 2.5 s | — |
| 2,500 | 9,702 | 4,996 | (6.5 GB estimated) | | 6.1 s | 311 MiB |
| 2,500, free | 9,702 | 5,000 | | | 6.7 s | 335 MiB |
| 10,000 | 39,402 | 19,996 | (77 GB estimated) | | 84 s | 578 MiB |
| 10,000, free | 39,402 | 20,000 | | | 97 s | 593 MiB |

At 10,000 stations the sweep is most of the time: SuperLU's triangular solves for the 20,000 columns, 56 s;
the products with **A**, 11 s; the linearisation, in Python, 7 s over four systems. NFR-008's 10,000
stations are supported; a geocentric network of that size, with three unknowns a station and denser
coupling, has not been measured.

The condition number is computed and reported. A system that is rank-deficient or numerically singular
produces a **diagnosis**, not a crash and not a meaningless answer (FR-226): the null-space vectors are
examined and mapped back to the stations and components that are undetermined, and the message names them —
*"stations 7 and 8 are connected to the network only by observations that do not determine their height"*.

---

## 3. Datum definition (FR-222)

The proposal names free and constrained networks as concepts students must be able to explore visually.
GeoComp supports:

| Mode | What it does | Use |
|---|---|---|
| `FIXED` | One or more stations held exactly | Simple constrained adjustment |
| `WEIGHTED` | Stations constrained with a covariance | Realistic tie to a reference frame with its own uncertainty |
| `MINIMUM_CONSTRAINT` | The minimum number of constraints to remove the datum defect, chosen or user-specified | Testing the network's internal geometry without external distortion |
| `INNER_CONSTRAINT` | Free network with the datum defined by a trace-minimum condition over a chosen station set | Deformation analysis — the standard choice when no station may be assumed stable |

The **datum defect** is computed from the network's dimensionality and observation content (e.g. 4 for a 2D
network with distances and angles only: two translations, one rotation, one scale — 3 if a distance fixes
scale). GeoComp reports the detected defect and how it was removed. Getting this wrong is the classic way to
produce a beautiful adjustment of the wrong thing, so it is stated in the result, not assumed.

Inner constraints matter specifically for monitoring (FR-835): if the datum is defined by holding a station
that has in fact moved, its motion is redistributed across the whole network and appears as everyone else
moving.

**How `WEIGHTED` is implemented, and a defect it hid until P5.** A weighted constraint is an *observation of
the station's own coordinates*, and enters the system as one: a row per constrained component, weight
**Σ⁻¹** over the constraint's covariance block, so the station moves under the adjustment, carries a
residual saying how far, and adds to the redundancy. Taken as a block rather than a diagonal, because a
constraint from a GNSS solution has correlated components and reducing it to variances would discard the
correlation that makes it what it is (FR-104). The rows are labelled `constraint:<station>` so a report can
tell them from observations while the statistics treat them identically — which is the point of holding a
benchmark weighted rather than fixed.

Until phase P5 none of that happened. `WEIGHTED` was declared here, implemented in the model layer
(`ConstraintSpec` refuses one without a covariance), and then **silently dropped by the adjustment**, which
read only `FIXED`. A network held solely by weighted constraints was rank-deficient rather than constrained
and refused to adjust; a network with one fixed and several weighted benchmarks used the first and discarded
the rest, so the disagreement between benchmarks — the reason a user holds several — could never appear in
the residuals. It was found while checking that a geoid-derived height's uncertainty reached the adjusted
heights ([`13-module-integration.md`](./13-module-integration.md) §3.1): it could not, because the
constraint carrying it was not in the system. The lesson is recorded rather than quietly fixed, because the
shape of it — a mode that validates, stores and displays correctly while doing nothing — is one that a test
of the model layer alone will never catch.

### 3.1 Dimensionality (FR-227)

1D (heights only), 2D (planimetric) and 3D adjustment are each supported, in geodetic, cartesian or
projected coordinates. The observation type registry declares which dimensionalities each type can
contribute to; a mismatch is rejected at validation rather than silently ignored.

---

## 4. Statistical validation

The proposal requires rigorous statistical validation so that results "possuam integridade e possam ser
utilizados com segurança em aplicações como obras de engenharia e cadastro".

### 4.1 Global test (FR-250)

Compares the a posteriori variance factor σ̂₀² = **v**ᵀ**Pv**/(n − u) with the a priori σ₀².

Reported: the statistic, both critical values (the test is two-sided — an unexpectedly *small* σ̂₀² means the
a priori precisions were pessimistic, which is also information), degrees of freedom, confidence level, and
the decision. Rejection is *not* automatically attributed to blunders; the report states the three
possibilities — blunders, an incorrect stochastic model, or an incorrect functional model — because
students and practitioners routinely assume the first.

### 4.2 Data snooping (FR-251)

Baarda's w-test on standardised residuals:

$$w_i = \frac{|v_i|}{\sigma_{v_i}}, \qquad \sigma_{v_i} = \sigma_0\sqrt{q_{v_i}}$$

Reported per observation: residual, its standard deviation, w, the critical value, the decision, and the
redundancy number r_i. Where σ₀² is estimated rather than known, the τ (tau) variant is used and the report
says which was applied.

**Rules that prevent misuse:**

- The test locates *one* outlier at a time. Multiple simultaneous blunders can mask each other, and the
  report says so when several observations exceed the critical value.
- An observation with r_i ≈ 0 is **uncheckable** — no blunder in it is detectable at all. These are flagged
  prominently; a network full of uncheckable observations can pass every test and still be wrong.
- Rejection is never automatic and never silent (FR-255). GeoComp presents candidates; the user decides;
  the decision is recorded with its reason and is reversible. Automatic iterative rejection is offered only
  in Advanced mode, with an explicit warning: in a monitoring network, the displacement being measured is
  exactly what an automatic outlier remover will delete.

  *As built (P12c-13).* Automatic rejection is offered in neither mode. A user sets an observation aside by
  giving it the status `REJECTED` or `EXCLUDED`, with a `RejectionRecord`, in the network document, and
  restores it the same way. The adjustment report lists every observation set aside, with its status,
  reason, test and statistic. Until P12c-13 the report counted only the active observations, so a rejection
  was recorded in the document and silent in the report (`tests/qgis/test_adjustment_report.py`).

### 4.3 Reliability (FR-252, FR-253)

**Internal** — the minimal detectable bias per observation, for configurable α (Type I) and β (Type II),
default α = 0.001, β = 0.20 (power 0.80):

$$\text{MDB}_i = \frac{\delta_0\,\sigma_i}{\sqrt{r_i}}$$

with δ₀ the non-centrality parameter for the chosen α and β. This answers the question the user actually
has: *how large a blunder could be hiding in this observation without me noticing?*

**External** — the effect on the adjusted coordinates of an undetected blunder at exactly the MDB. This
answers the consequential question: *and would it matter?* An observation with a large MDB but negligible
external effect is not a problem; one with a modest MDB and a large external effect is.

Both are reported per observation and summarised per station, and both are visualised (FR-902).

### 4.4 Error ellipses (FR-254)

From the eigen-decomposition of the 2×2 (or 3×3) covariance block of each adjusted station:

- semi-major and semi-minor axes, and orientation;
- scaled to a user-selected confidence level, stating whether the standard ellipse or the F-distribution
  confidence ellipse is used;
- **relative** ellipses between station pairs, from the joint covariance — these, not the absolute ellipses,
  are what tell you whether a *baseline* is well determined;
- 3D ellipsoids for 3D adjustments.

Display exaggeration is explicit and stated in the legend (FR-901).

### 4.5 Positional uncertainty

A single scalar per station at a stated confidence, comparable with the values DynAdjust reports in its
`.apu` output — so that the two engines' results can be compared directly (roadmap P6 exit criterion).

**As built.** The semi-major axis of the station's confidence ellipse at the solution's confidence
(`core/statistics/ellipses.py`, `positional_uncertainty`) — the radius of the circle the ellipse fits in,
which is never smaller than the true circular radius. DynAdjust's reader takes the engine's own `Hz PosU`.
**Until P12c the in-house adjustment set nothing here.** Its reports, tables, layers and the P12b thematic
map all showed it as missing for every in-house solution, and no test failed. The comparison export's test
([`20`](./20-testing-and-validation.md) §5) found it.

---

## 5. Pre-analysis (FR-270…FR-273)

**Pre-analysis is network design, not data checking.** This document restates that because the archived
roadmap conflated the two ([`archive/README.md`](./archive/README.md), item 6). Both capabilities exist; they
are different.

### 5.1 Design simulation (FR-270, FR-271, FR-272)

Given a *planned* network — station positions and intended observations, with assumed precisions but no
measured values — form **A** and **P**, and compute:

$$\boldsymbol{\Sigma}_{x} = \sigma_0^2 (\mathbf{A}^{T}\mathbf{P}\mathbf{A})^{-1}$$

No observations are needed: **A** depends only on geometry, **P** only on assumed precisions. From **Σ**ₓ
come the expected error ellipses (FR-271) and, from the redundancy numbers, the expected internal and
external reliability. The user learns before going to the field whether the planned network can meet its
specification.

This runs on the QGIS canvas (FR-272): draw planned stations, draw intended observations, evaluate, see the
expected ellipses, move a station, re-evaluate. This interactive loop is the reason pre-analysis belongs in a
GIS at all, and it is a direct answer to the proposal's pedagogical justification.

> **Phasing.** The mathematics above and the Processing algorithm that exposes it
> (`geocomp:analysis_network_preanalysis`) shipped in **P2**; the canvas dialog (FR-272) shipped in **P3**,
> where a running QGIS can verify it. [`ROADMAP.md`](./ROADMAP.md) records the re-planning. The split is
> along a real seam: the algorithm is the whole computation, and the dialog is a way to drive it, so a model
> or a script needs nothing from P3.
>
> The seam held in the implementation. The dialog builds the design and then hands it to the same algorithm
> for the report, so an interactive design and one loaded from a file are evaluated by identical code
> (ADR-0005). What an edit *means* — a removed station taking its observations with it, planned directions
> from one setup forming one set — lives in `core/preanalysis/session.py`, which imports no Qt and is tested
> without QGIS; the dialog contributes the map tool, the rubber bands and the panel.
>
> **Evaluation there never raises.** A design under construction spends most of its life un-evaluable — one
> station, no observations, three stations and a rank defect — and an interactive loop that threw on each of
> those would be unusable. A design that cannot be evaluated reports *why*, as findings, in the same shape as
> one that can be evaluated but is poor, so the panel renders one thing rather than branching on which kind
> of answer arrived.

Supported design questions: *is this network strong enough?* · *where should I add an observation to improve
it most?* · *what happens if I lose station X?* · *can I detect a 5 mm blunder anywhere in this network?*

### 5.2 Network inspection (FR-273)

On *real* data, before adjusting: connectivity and disconnected components, isolated stations, stations with
insufficient observations, duplicate or contradictory observations, missing approximate coordinates, gross
misclosures, and observations referencing unknown stations.

This is fast, needs no adjustment, and catches the errors that otherwise surface as a confusing singular
normal matrix.

---

## 6. Sequencing and reproducibility

A standard adjustment run:

```text
validate → inspect (FR-273) → approximate coordinates → assemble A, P
   → iterate to convergence → statistics → global test → data snooping
   → reliability → ellipses → assemble Solution + provenance
```

Every stage is inspectable and each produces a recorded intermediate (the teaching requirement). The same
inputs, parameters and version produce bit-identical output (NFR-007): iteration order is deterministic,
observation ordering is stable and explicit, and no set iteration or dictionary ordering is allowed to
influence a numeric result.

---

## 7. Acceptance criteria

1. Reproduces the worked network adjustment examples in Ghilani (2010) and Gemael — coordinates, residuals,
   σ̂₀², and error ellipses — to the precision printed in the source.
2. Free-network and constrained solutions of the same network are consistent: residuals and σ̂₀² match, and
   coordinate differences lie within the datum transformation between them.
3. A network with a deliberately injected blunder of 2 × MDB is detected by data snooping in the correct
   observation, on the first pass.
4. Rank-deficient input produces a diagnosis naming the affected stations and components, never a numeric
   result.
5. Pre-analysis of a network reproduces, to within linearisation error, the **Σ**ₓ obtained by adjusting
   simulated observations of that same network.
6. The same network adjusted by the in-house core and by DynAdjust agrees within the tolerances in
   [`20-testing-and-validation.md`](./20-testing-and-validation.md).
7. Every reported statistic is accompanied by its critical value, its confidence level and its decision —
   never a bare pass/fail.
8. A network the dense path cannot hold is adjusted on the sparse path when SciPy is present, and agrees with
   the dense path wherever both run — coordinates, σ̂₀², each station's covariance, redundancy numbers,
   w-tests, MDBs and external reliability; without SciPy it is refused by a message naming SciPy (NFR-008,
   §2.4.1).
