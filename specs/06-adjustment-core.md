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
scale and refraction coefficients when the user enables them, gravimeter drift parameters (FR-702), and
transformation parameters where a solution is being related to another frame.

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
