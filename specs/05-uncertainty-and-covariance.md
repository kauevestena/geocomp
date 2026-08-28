# 05 — Uncertainty and covariance propagation

**Status:** Draft
**Requirements covered:** FR-200…FR-208, FR-412, FR-505, FR-703.
**Source:** modificações.md; tex §Propagação de variâncias e covariâncias; §Aplicação da propagação de
covariâncias no GeoComp.

---

## 1. Why this document exists

The project author's change notes state the central idea plainly:

> *"deixando claro que uma das idéias centrais é que para todas as medidas e variáveis seja possível realizar
> estimativa de seus níveis de incerteza, tanto por abordagens aproximadas/heurísticas como por abordagens
> rigorosas"* — `research_project/modificações.md`

This is not a feature of one module. It is a property the whole system must have: **no measured or derived
geodetic quantity exists in GeoComp without an uncertainty attached** (FR-200). That is why this
specification sits above the technique modules, and why the type that carries it is the most-used type in
`core/`.

The mathematics is standard. What matters here is that it is applied *everywhere*, that the approximate path
is available where the rigorous one cannot run, and that the two are never confused.

---

## 2. The mathematics

### 2.1 Rigorous propagation (FR-201)

Given **L**_a = f(**L**_b), the covariance of the derived quantities follows from the covariance of the
inputs:

$$\boldsymbol{\Sigma}_{L_a} = \mathbf{A}\,\boldsymbol{\Sigma}_{L_b}\,\mathbf{A}^{T}$$

with **A** = ∂f/∂**L**_b evaluated at the input values. For non-linear f this is a first-order
approximation; GeoComp records that fact rather than implying exactness (§6).

Two properties matter operationally:

- **Correlations are carried, not discarded** (FR-208). If **Σ**_Lb has off-diagonal terms, they affect
  **Σ**_La. Reducing inputs to independent standard deviations is a *different* computation, and GeoComp
  only does it when the user explicitly asks.
- **Composition works.** Propagating through g∘f equals propagating through f and then through g, up to
  linearisation error. This is what allows each pre-processing step to be an independent algorithm
  (FR-005) without losing rigour across the chain.

### 2.2 Jacobians

Three ways to obtain **A**, in order of preference:

1. **Analytic.** Hand-derived and unit-tested for every standard geodetic transformation. This is the
   default and covers the great majority of cases.
2. **Complex-step differentiation.** For real-analytic functions, ∂f/∂x ≈ Im(f(x + ih))/h with h ≈ 10⁻²⁰,
   which has no subtractive cancellation and is accurate to machine precision. Used for verifying analytic
   Jacobians in tests.
3. **Central finite differences.** Fallback for functions that are not complex-safe, with a step chosen from
   the variable's scale. Flagged in the result, because the derivative is approximate.

**Every analytic Jacobian MUST have a test comparing it against the complex-step or finite-difference
value.** A sign error in a Jacobian produces a plausible-looking, wrong uncertainty — the failure mode this
whole document exists to prevent.

### 2.3 The approximate path (FR-202)

The proposal explicitly requires approximate or heuristic estimation "úteis em situações onde não se dispõe
de informação completa sobre as incertezas das variáveis de entrada ou onde a simplificação é aceitável para
fins práticos". GeoComp provides these strategies, each named and recorded:

| Strategy | What it does | When it applies |
|---|---|---|
| `NOMINAL_PRECISION` | Uses the instrument's manufacturer specification (e.g. ± (2 mm + 2 ppm), ± 5″) as the input σ | Input data has no stated uncertainty but the instrument is known |
| `TYPE_DEFAULT` | Uses the configured default per observation type (FR-064) | Instrument unknown |
| `INDEPENDENCE_ASSUMED` | Ignores unknown correlations, treating inputs as independent | Correlation information unavailable |
| `DOMINANT_TERM` | Propagates only the dominant contributions, dropping negligible ones | Deliberate simplification, with the dropped terms listed |
| `EMPIRICAL_SCALING` | Scales an a priori model by an empirically determined factor | Residual analysis shows the a priori model is optimistic |
| `NUMERIC_DERIVATIVE` | Obtains a derivative by finite differences rather than analytically | No closed-form Jacobian is available |
| `RECORDED_PRECISION` | Takes σ from how many digits were written: a value recorded as `32.4` lies in `[32.35, 32.45)`, so σ = `0.05 / √3` | Nothing better exists **and** the quantity is not load-bearing |

**`RECORDED_PRECISION` is deliberately narrow** (added in phase P4). It is not an exception to *GeoComp does
not invent a sigma*: the information is genuinely in the file, in the number of digits the observer chose to
write. But it is weak information, so it is permitted only where the quantity does not carry the result — a
levelling sight distance, whose uncertainty reaches the answer only multiplied by a collimation error of
order 10⁻⁴, qualifies; **a staff reading, whose σ becomes an adjustment weight, does not, and the importer
still refuses there.**

A computation using any of these is `APPROXIMATE`. There is no partial credit: one approximate input makes
the result approximate.

### 2.4 Labelling (FR-203)

`uncertainty_mode ∈ {RIGOROUS, APPROXIMATE}` propagates with the value and appears:

- on the `Quantity` itself, with the specific strategies used;
- on the `Solution` (see [`04-data-model.md`](./04-data-model.md) §2.8);
- in the UI wherever an uncertainty is displayed;
- in every export and every report (FR-930), naming the strategies;
- in provenance (FR-134).

The reason is not pedantry. A professional deliverable that presents a heuristic figure as a rigorously
propagated one misrepresents the quality of the survey — and monitoring decisions are made on exactly these
numbers.

---

## 3. The `Quantity` type

The workhorse of `core/`. Conceptually:

```python
@dataclass(frozen=True)
class Quantity:
    value: float
    variance: float                  # σ², in (unit)²
    unit: Unit                       # metre, radian, m/s², dimensionless
    mode: UncertaintyMode            # RIGOROUS | APPROXIMATE
    strategies: frozenset[Strategy]  # empty when RIGOROUS
```

Design rules:

- **Immutable.** Operations return new values; nothing is modified in place.
- **Variance, not σ.** Variance is what composes linearly; storing σ invites squaring errors.
- **Units are carried and checked.** Adding a metre to a radian raises. Angles are radians internally;
  degrees-minutes-seconds is display only.
- **Arithmetic propagates.** `+`, `-`, `*`, `/`, and the elementary functions have propagation built in for
  the *uncorrelated* case, and raise if used where correlation matters (§3.2).
- **Mode is contagious.** `RIGOROUS op APPROXIMATE → APPROXIMATE`, with the union of strategies.

### 3.1 `Covariance`

For correlated sets:

```python
class Covariance:
    matrix: np.ndarray          # n x n, symmetric positive semi-definite
    labels: tuple[str, ...]     # names the ordering — never implicit
    unit: tuple[Unit, ...]      # per component
    mode: UncertaintyMode
```

- Symmetry and positive semi-definiteness are validated on construction, with a tolerance, and a violation
  is a `DataError` naming the offending block — a non-PSD input covariance is a data problem that will
  otherwise surface as a nonsensical adjustment.
- `labels` is mandatory. Silent reordering of a covariance matrix relative to its observations is a
  catastrophic and near-invisible bug.
- Provides `sub(labels)`, `block(labels)`, `to_correlation()`, `std_devs()`, and
  `transform(jacobian, out_labels)`.

### 3.2 The scalar/vector boundary

Scalar `Quantity` arithmetic assumes independence. When a computation involves quantities that *are*
correlated, the vector path (`Covariance` + an explicit Jacobian) is mandatory. To keep this from being a
matter of memory:

- Quantities that came out of a `Covariance` carry a provenance tag identifying the covariance they belong
  to;
- combining two quantities tagged to the same covariance raises unless done through the vector path.

This turns the most dangerous silent error in the system into a loud one.

---

## 4. Where propagation is applied

The proposal names five stages (`tex §Aplicação da propagação de covariâncias`). Each is a requirement, and
each is realised in a specific module:

| Stage | Requirement | Realised in |
|---|---|---|
| Observation pre-processing — atmospheric, instrument and EDM corrections carry the uncertainty of their parameters | FR-204 | [`09-module-total-station.md`](./09-module-total-station.md), [`12-module-gravimetry.md`](./12-module-gravimetry.md) |
| Geometric reductions — to the ellipsoid, to the projection plane, between heights — carry the uncertainty of the heights and coordinates used | FR-205 | [`09-module-total-station.md`](./09-module-total-station.md) §reductions |
| GNSS processing — solution covariance preserved and used in combined adjustment | FR-206 | [`08-engine-rtklib.md`](./08-engine-rtklib.md), [`11-module-gnss.md`](./11-module-gnss.md) |
| Network adjustment — least squares yields **Σ**ₓ, from which ellipses and precision indicators follow | FR-224, FR-254 | [`06-adjustment-core.md`](./06-adjustment-core.md) |
| Deformation analysis — propagated coordinate uncertainty gives the significance of a detected displacement | FR-207, FR-834 | [`14-multi-epoch-monitoring.md`](./14-multi-epoch-monitoring.md) |

### 4.1 Worked illustration — one reduction

To make the requirement concrete: reducing a slope distance to horizontal,
d_h = d · sin(z), with correlated (d, z):

**A** = [∂d_h/∂d, ∂d_h/∂z] = [sin z, d·cos z]

σ²_dh = **A** **Σ** **A**ᵀ = sin²z·σ²_d + d²cos²z·σ²_z + 2·d·sin z·cos z·σ_dz

The third term vanishes only if d and z are uncorrelated — which, measured by one total station in one
pointing, they generally are not. GeoComp keeps it. Dropping it is the `INDEPENDENCE_ASSUMED` strategy and
must be recorded as such.

---

## 5. Stochastic models

Where the input σ comes from, in order of precedence:

1. **Stated in the data.** An imported per-observation σ is used as given.
2. **Instrument model.** From the instrument profile (FR-061, FR-069). Typically σ_d = a + b·d for EDM and a
   constant angular σ with a pointing/reading decomposition. Nominal specifications are usually optimistic;
   the model supports a user scale factor, and residual analysis (FR-250) tells the user whether their
   assumption held.
3. **Type default.** From Global Settings (FR-064).
4. **Refuse.** If none of the above yields a value, the operation fails with a `ValidationError`. GeoComp
   does not invent a σ, because a fabricated weight silently corrupts every downstream statistic.

Correlation sources modelled explicitly: within a direction set (shared orientation), within a GNSS baseline
(3×3 from the processor), between the components of a repeated observation, and between reductions sharing
an input height.

---

## 6. Documented limits

Stated in the specification, in the API documentation and in reports — because a limit that is only known to
the implementer is not a limit, it is a trap.

1. **First-order only.** Propagation linearises. For strongly non-linear functions over large input
   uncertainties, the result understates the true dispersion. GeoComp flags a computation where the
   second-order term is estimated to be significant relative to the first.
2. **Gaussian assumption.** Covariance describes the second moment. Confidence regions derived from it
   assume approximate normality; that assumption is stated wherever a confidence level is reported.
3. **Input quality bounds output quality.** A rigorously propagated result from an invented input σ is
   precise nonsense. This is why §5 ends in refusal rather than a default.
4. **Positive semi-definiteness can be lost numerically** through long chains. GeoComp validates at each
   construction (§3.1) and reports where it first fails, rather than allowing a silently indefinite matrix
   to reach the adjustment.

---

## 7. Acceptance criteria

Implementation of this specification is complete when:

1. Every analytic Jacobian has a test agreeing with complex-step differentiation to ≤ 1e-9 relative.
2. Rigorous propagation reproduces the worked examples in the reference textbooks (Ghilani; Gemael) to the
   precision printed there — see [`20-testing-and-validation.md`](./20-testing-and-validation.md).
3. A round trip through a full pre-processing chain preserves the covariance that a single combined
   propagation would produce, to within linearisation error.
4. No code path in `core/` can produce a geodetic value without an attached uncertainty; a test asserts this
   over the public API surface.
5. Every `APPROXIMATE` result names its strategies in its export, in its report and in its provenance.
6. Combining two quantities from the same `Covariance` through the scalar path raises.
