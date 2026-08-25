# 10 — Module: Level

**Status:** Draft
**Requirements covered:** FR-500…FR-505.
**Source:** tex §Painel de Configuração Global, item 2 (Nível); modificações.md.

Geometric (differential) levelling. Small module, high leverage: it reuses the adjustment core wholesale
([`06-adjustment-core.md`](./06-adjustment-core.md)) and delivers a complete second technique cheaply
(roadmap P4).

---

## 1. Menu structure

| Menu item | Requirement |
|---|---|
| Equal sights | FR-500 |
| Equidistant sights | FR-501 |
| Extreme sights | FR-502 |
| Levelling network adjustment | FR-504 |

---

## 2. The three schemes

The proposal names three, each with a different geometry and therefore a different error model. The
distinction is not cosmetic — it changes which systematic errors cancel.

### 2.1 Equal sights (FR-500)

Backsight and foresight distances equal. Named in the proposal as the **preferred method** (*"método
preferencial"*), because equal sight lengths cancel, to first order, the collimation error of the instrument
and the effects of curvature and refraction.

- Height difference per setup: Δh = backsight reading − foresight reading.
- GeoComp checks the sight-length balance per setup and per line against a configurable tolerance, and
  **reports the accumulated imbalance**, which is what actually drives the residual collimation error over a
  line.
- Where the imbalance is significant and a collimation value is known (from a two-peg test, stored per
  instrument, FR-061), the residual correction is applied with its uncertainty propagated.

### 2.2 Equidistant sights (FR-501)

The scheme used to cross obstacles such as rivers, where an equal-sight setup is impossible. The proposal
names this use explicitly. Reciprocal observations from both banks are combined so that the errors that do
not cancel geometrically cancel by symmetry instead.

- Requires the reciprocal pairs to be identified and combined; GeoComp models the pairing explicitly rather
  than treating the observations as an ordinary line.
- Refraction across water varies rapidly and asymmetrically. The uncertainty model for this scheme is
  **deliberately more conservative** than for equal sights, and the reason is stated in the output.

### 2.3 Extreme sights (FR-502)

Multiple foresights from one setup — the routine case for levelling a set of points from one instrument
position. All foresights from one setup share the backsight and therefore share its error: they are
**correlated**, and form a cluster (FR-104). Treating them as independent understates the uncertainty of
every derived height difference between two of the foresighted points.

---

## 3. Closures and tolerances (FR-503)

A levelling result without a closure check is not a result. GeoComp computes, per line and per loop:

- misclosure against the known closing height or around the loop;
- the permissible misclosure from the configured tolerance model — typically k·√L with L in kilometres, with
  k by levelling class (FR-061) — and the comparison;
- the distribution of misclosure across setups, which localises where an error entered.

Failing tolerance is reported as a failure with the numbers, and the user decides; GeoComp does not adjust a
line that failed its tolerance without an explicit acknowledgement.

---

## 4. Network adjustment (FR-504)

Height differences become `HEIGHT_DIFFERENCE` observations
([`04-data-model.md`](./04-data-model.md) §4) and are adjusted by the core as a 1D network.

**Weighting.** σ²_Δh ∝ L (line length) or ∝ n (number of setups), selectable, with the constant of
proportionality from the instrument and scheme (FR-064). The choice matters and is recorded in the result:
length weighting suits long lines with consistent sight lengths; setup weighting suits short, irregular
lines where the per-setup reading error dominates.

Everything from [`06-adjustment-core.md`](./06-adjustment-core.md) applies: free and constrained networks
(a levelling net tied to one or several benchmarks), the global test, data snooping, reliability, and — the
1D analogue of error ellipses — per-benchmark height uncertainties and relative height uncertainties between
pairs.

Height differences from trigonometric levelling
([`09-module-total-station.md`](./09-module-total-station.md) §4.5) enter the same adjustment, with their own
(generally larger) uncertainties. Combining geometric and trigonometric levelling in one network is
supported and is a case where per-technique variance component scaling (FR-805) earns its place.

---

## 5. Height systems

A levelling network produces height *differences*, which become heights only against a datum. GeoComp
records the height system of the benchmarks used (`height_type` in
[`04-data-model.md`](./04-data-model.md) §3) and refuses to mix orthometric and ellipsoidal heights without
a geoid model (FR-804, FR-802).

Orthometric corrections (the non-parallelism of level surfaces) are applied for precise levelling over
significant height ranges, as an option with its magnitude reported so the user can see when it matters.

---

## 6. Data import

Field-book layouts vary widely. The importer (FR-160) handles: one row per setup with backsight and
foresight readings; one row per reading with a setup identifier; and three-wire readings (upper, middle,
lower) from which the sight distance is derived by stadia and the mean reading is formed with its dispersion
as an empirical precision estimate.

Sight distances are imported where recorded, because §2.1's balance check depends on them.

---

## 7. Acceptance criteria

1. All three schemes reproduce published worked examples to the precision printed in the source.
2. Loop misclosure and tolerance comparison reproduce a worked example, including the failing case.
3. Extreme-sight foresights from one setup are represented as a correlated cluster; a test asserts that the
   derived height difference between two of them has a *smaller* uncertainty than the independent treatment
   would give (the correlation is real and it helps here).
4. A levelling network adjusted with length weighting and with setup weighting gives results consistent with
   each other and with the published example for each.
5. Combining geometric and trigonometric height differences in one network produces a solution whose
   variance components reflect the different techniques.
6. Mixing orthometric and ellipsoidal heights without a geoid model raises `ValidationError`.
7. Every output carries an uncertainty and an `uncertainty_mode` (FR-505).
