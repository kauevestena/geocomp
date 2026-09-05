# 13 — Module: Integration

**Status:** Draft
**Requirements covered:** FR-800…FR-805; uses FR-165, FR-804.
**Source:** tex §Painel de Configuração Global, item 5 (Integração); O4.

The point of the whole project, arguably: one environment in which observations from different techniques
are adjusted together rather than in separate programs with manual handoffs.

---

## 1. Menu structure

Per `tex §Painel de Configuração Global`, item 5:

| Menu item | Requirement |
|---|---|
| GNSS and Total Station | FR-800 |
| Total Station and Level | FR-801 |
| GNSS and Level | FR-802 |
| Multiple (three or more techniques) | FR-803 |

Each is a preset over one general combined-adjustment capability; the presets exist because they carry
different defaults, different validation, and different explanatory material.

---

## 2. What makes combination hard

Combining techniques is not concatenating observation lists. Four things must be right, and each has a
requirement:

| Problem | Consequence if wrong | Handled by |
|---|---|---|
| The techniques' stochastic models are on inconsistent scales | One technique dominates the solution and the other's information is wasted; σ̂₀² fails the global test for a reason nobody can locate | FR-805, §4 |
| Heights are of different types | GNSS gives ellipsoidal, levelling gives orthometric; differencing them silently is a metre-scale error in Brazil | FR-804, §3 |
| The observations are in different reference frames or at different epochs | A systematic shift absorbed as apparent network distortion | FR-832, §5 |
| Correlations within a technique are lost | Redundancy overstated, uncertainties understated | FR-104 |

---

## 3. Height systems (FR-802, FR-804)

The GNSS-and-levelling case is the sharpest.

- GNSS determines **ellipsoidal** height h.
- Geometric levelling determines **orthometric** height differences ΔH.
- They are related by the geoid: h = H + N.

**Requirements:**

1. Every height carries its `height_type` ([`04-data-model.md`](./04-data-model.md) §3).
2. Combining heights of different types **without** a geoid model raises `ValidationError`. Not a warning —
   the resulting numbers would be wrong by the geoid undulation, tens of metres in much of Brazil.
3. When a geoid model is supplied (FR-165), it is applied, and **which model** is recorded in the solution
   and in every report (FR-804). Two solutions computed with different geoid models are not comparable, and
   the record is what makes that visible.
4. The geoid model's own uncertainty propagates (FR-204). A geoid model is not exact, and in a combined
   adjustment its uncertainty is often the limiting factor on the height solution.
5. The residuals of the geoid-related observations are reported separately, because they are the empirical
   test of the geoid model over the project area — genuinely useful information the user would otherwise
   have to compute by hand.

### 3.1 As implemented (P5)

Items 1–4 are in place; item 5 waits on the combined adjustment itself (this module is still Draft).

`geocomp.core.geoid` holds the model — identity, version, coverage, stated accuracy, bilinear interpolation
with its own uncertainty — and `geocomp.io.geoid` reads one from GTX or ESRI ASCII
([`17-persistence-and-interoperability.md`](./17-persistence-and-interoperability.md) §5.5). The height-type
conversion runs where a mixture first arises, which in P5 is a levelling network holding a benchmark whose
height came from GNSS: `harmonise_benchmarks` converts to **orthometric**, and not arbitrarily — the
observations are levelled height differences, which are differences of orthometric height, so converting the
outliers into the system the observations are already in leaves the observations untouched. `to_solution`
records the model on every adjusted position (FR-804).

Three refusals rather than two, because "a geoid model was supplied" turned out to have three meanings:

| Situation | Code |
|---|---|
| Mixed height types, no model at all | `mixed_height_types` |
| A model **named** but its grid not supplied | `geoid_model_named_without_grid` |
| A benchmark needing conversion with no latitude and longitude | `benchmark_without_position` |

The middle one matters: a name records *which* model was used and cannot compute an undulation. Accepting
the name as permission to mix would be the worst of both — heights wrong by the undulation, and a record
asserting they had been corrected.

**A defect this uncovered.** Checking that the geoid's uncertainty reached the adjusted heights showed that
it could not: `ConstraintMode.WEIGHTED` was declared, validated, and then ignored by the adjustment, which
read only `FIXED`. A geoid-derived height is exactly the kind that should be held weighted rather than
fixed, so item 4 of §3 was unreachable. See [`06-adjustment-core.md`](./06-adjustment-core.md) §3.

---

## 4. Variance component estimation (FR-805)

When techniques with different a priori stochastic models are combined, the relative weighting between them
is an assumption, and usually a wrong one. GeoComp:

- allows a scale factor per technique group (or per observation-type group), either fixed by the user or
  **estimated** from the adjustment;
- reports the estimated factors with their uncertainties;
- states the interpretation plainly: a factor of 2 for a technique means its a priori precisions were
  optimistic by a factor of 2 — which is information about the survey, not a number to be tuned away.

Without this, the classic failure is silent: the global test fails, the user has no way to see which
technique caused it, and the usual response is to inflate everything until the test passes.

---

## 5. Frames and epochs (FR-832)

Observations from different techniques frequently arrive in different frames and at different epochs — GNSS
in a global frame at the observation epoch, terrestrial work in a national frame at its official epoch.

Before combination, GeoComp checks frame and epoch compatibility, transforms where needed, and records the
transformation applied. Same machinery as multi-epoch comparison
([`14-multi-epoch-monitoring.md`](./14-multi-epoch-monitoring.md) §3) — the problem is identical, so the
implementation is shared.

A combination whose frames GeoComp cannot reconcile is **refused**, with a message naming the incompatible
inputs. The alternative — proceeding and absorbing a datum shift into the residuals — produces a plausible
adjustment of the wrong thing.

---

## 6. The combined adjustment

Mechanically, once §3–§5 are satisfied, this is the core's ordinary business
([`06-adjustment-core.md`](./06-adjustment-core.md)): assemble **A** and **P** across all observation types,
solve, test, report. Each observation type contributes its rows through the type registry
([`04-data-model.md`](./04-data-model.md) §4), which is why adding a type does not require touching the
adjustment.

Engine choice: the in-house core for project-scale networks, DynAdjust for large ones or where the user
prefers it (FR-321) — with the exception that gravity observations cannot go to DynAdjust
([`12-module-gravimetry.md`](./12-module-gravimetry.md) §1), so a combination including gravity uses the
in-house core and GeoComp says so rather than silently dropping the gravity observations.

**Reporting is per technique as well as overall:** residual summaries, variance components, reliability and
redundancy contributions broken down by technique. "The adjustment passed" is much less useful than "the
adjustment passed, and the levelling is carrying almost none of the redundancy."

---

## 7. Acceptance criteria

1. A GNSS + total station network reproduces a published combined-adjustment example within tolerance.
2. Combining ellipsoidal and orthometric heights without a geoid model raises `ValidationError`; with one,
   the model used appears in the solution and in the report.
3. Variance component estimation on data with a deliberately mis-scaled technique recovers the injected
   scale factor within its uncertainty.
4. A combination of observations in two different frames triggers transformation with a provenance record;
   an irreconcilable combination is refused with a message naming the inputs.
5. Correlated clusters survive combination intact into the adjustment.
6. A combination including gravity observations is routed to the in-house core, with the reason reported.
7. Per-technique residual and redundancy breakdowns appear in the report.
8. A three-technique combination (FR-803) runs end to end and produces a single solution.
