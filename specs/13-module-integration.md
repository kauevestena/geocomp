# 13 — Module: Integration

**Status:** Draft — implemented: the computation in P9a (§3.2, §4.1, §5.1, §6.1), the menu, report section,
layers and DynAdjust path in P9b (§6.2).
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

### 3.2 In the combined model (P9a)

The combination is adjusted in `Frame.GEOCENTRIC_3D` ([`06`](./06-adjustment-core.md) §2.3), which
estimates X, Y, Z and so **ellipsoidal** heights. An orthometric observation — a levelled difference whose
`meta["height_type"]` says `ORTHOMETRIC`, or an `ORTHOMETRIC_HEIGHT` — needs the geoid, and gets it as
follows (`core/adjustment/undulations.py`).

**Each undulation is a parameter with the model's value as a weighted prior.** At every station an
orthometric observation touches, *N* is estimated, and the model (`AdjustmentOptions.geoid`) contributes one
observation of it: the interpolated value with the model's stated accuracy. An orthometric observation reads
`h − N` with *N* the parameter. The two shortcuts are both wrong: subtracting the model's *N* as an exact
number discards its uncertainty (item 4), and adding its variance to each observation double-counts it —
every difference at a station shares that station's *N*, so the errors are correlated across observations,
and with a 0.1 m geoid and 2 mm levelling the levelling would become worthless when in fact, between GNSS
stations, it measures the *change* in undulation. As parameters, the geoid's uncertainty propagates through
the normal equations (item 4), and **each prior's residual is the empirical test of the model** (item 5):
`geoid_residuals(run)` gives, per station, the model's value, the adjusted one, their difference, its
redundancy and its w-statistic. A model 20 cm wrong against its stated 5 cm is found at every station with
|w| > 1.96; an exact one leaves residuals under a micrometre.

**The priors are independent between stations**, and the solution says so (`INDEPENDENCE_ASSUMED`). A geoid
model's errors are spatially correlated — its relative accuracy over a few kilometres is far better than its
absolute one — and a model stating only an absolute sigma gives nothing to build the correlation from.
Independence trusts the model *less* for a difference than it deserves, so a height that depends only on the
geoid comes out pessimistic rather than optimistic.

| Situation | Code |
|---|---|
| Orthometric observations and no geoid model | `mixed_height_types`, naming the stations |
| A levelled difference that does not state its height type | `height_difference_type_unstated` — not guessed |
| A station **held** at a geodetic position with an orthometric height | `geocentric_frame_orthometric_constraint` — hold the benchmark as an `ORTHOMETRIC_HEIGHT` observation instead |
| A station held in latitude, longitude or height alone | `geocentric_frame_partial_geodetic_constraint` — no subset of X, Y, Z expresses it |
| A station outside the model's coverage | `geoid_outside_coverage` |

**Item 3's report half was missing.** P5 recorded the model on every adjusted position, and nothing printed
it: the shared report's identification section now names every geoid model on the solution's positions.

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

### 4.1 As implemented (P9a)

`core/adjustment/variance_components.py`: **least-squares variance component estimation** (Teunissen and
Amiri-Simkooei, 2008) — `N θ = l` with `N_kl = ½ tr(M Q_k M Q_l)`, `l_k = ½ (Pv)ᵀ Q_k (Pv)` and
`M = P Q_vv P`, iterated by rescaling each group until every estimate is one. It is exact for correlated
clusters, which `vᵀPv/r` per group is not, and `D(θ) = N⁻¹` is the factors' own covariance. Groups are
techniques by default (`technique_of`: an observation's recorded `meta["technique"]`, else its type's).

Rows that are no group's — a weighted benchmark, a geoid prior — are the **known part** `Q₀`: they keep their
stated covariance and their expected contribution comes off the right-hand side,
`l_k −= ½ tr(M Q_k M Q₀)`. (The first version looked every row up as an observation and would have failed on
the first network with a weighted benchmark.) Refused, by name: a cluster split across groups
(`variance_component_cluster_split`), a group with a redundancy below one (`variance_component_unestimable`),
a negative estimate, a singular system, and no convergence.

Criterion 3 is met on a 12-station synthetic survey: GNSS declared at half its true sigma is recovered as a
factor of 4 within two of its standard deviations, the total station as 1, and over 40 repeated surveys the
estimates scatter by what `D(θ)` says, within the 30 % a sample of 40 resolves.

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

### 5.1 As implemented (P9a)

**The transformations are GeoComp's own arithmetic on EPSG's parameters** (`core/geodesy/frames.py`), at the
maintainer's decision of 26 September 2026, and P10 reuses them. PROJ holds the same parameters, but the
combination needs each transformation's Jacobian for the covariances, needs velocities carried across it,
and needs a record provenance can hold — none of which a PROJ pipeline returns.

Held: every non-deprecated EPSG (v11.004) transformation between ITRF2000, 2005, 2008, 2014 and 2020 — a
direct one for every pair (9991–9994, 7790, 8078, 8079, 6300, 6302, 6389), so none is ever a composition —
and ITRF2000 to SIRGAS 2000 (9052). The ITRF ones are 14-parameter, time-dependent (method 1053, position
vector convention: `X' = T + (1 + D)(I + R) X`, every parameter at the coordinates' epoch); the inverse is
solved exactly, not by flipping signs. SIRGAS 2000 is ITRF2000 at 2000.4 (method 1065, time-specific): valid
only there, so reaching it from another epoch moves the point along its velocity, and **without a velocity
the move is refused** (`epoch_change_without_velocity`) — zero is a decimetre a decade in most of Brazil. A
velocity crosses each transformation with its rates (`V' = M V + Ṫ + Ṁ X`: the scale rate alone changes a
Brazilian velocity by 0.3 mm/year). The covariance goes through each step's Jacobian, and a change of epoch
adds the velocity's covariance times the interval squared.

**The transformation's own accuracy is recorded, not added** to each station's covariance. It is common to
every point transformed — a shift of the network, not scatter between its stations — so adding it per
station would falsify every relative position. `TransformationRecord.accuracy` carries it, and a comparison of
absolute positions ([`14`](./14-multi-epoch-monitoring.md) §3) is where it belongs.

**Validation.** `scripts/check_frames.py` transforms 303 point, epoch and frame-pair cases with pyproj and
compares: GeoComp agrees with PROJ 9.4 **to under a nanometre** in every one, and PROJ used the same EPSG
operation in each. The PROJ answers are committed (`tests/data/frames/proj_reference.json`) so the tier-1
test compares against them everywhere; the `reference` workflow regenerates them with a pinned pyproj and
fails if either side moves. **SIRGAS 2000 is the exception PROJ makes**: PROJ lists EPSG:9052 as unavailable
(method 1065 is not implemented) and substitutes a no-op, which agrees only because 9052 is the identity —
so those cases check consistency, and the SIRGAS behaviour that matters (the epoch refusal, the velocity
path) is tested in tier 1 against the definitions.

WGS 84 is refused (`frame_unknown`): its realisations differ by decimetres and the name does not say which.
Frame names are canonical over one datum's CRSs only (ITRF2020 is EPSG:9988, 9989 and 9990), never across
datums. No velocity *model* (VEMOS) is held; a station's velocity is supplied or the move is refused.

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

### 6.1 As implemented (P9a)

`core/techniques/integration/`:

* **`combine(inputs, frame=, epoch=, velocities=)`** merges the networks each technique produced. Station ids
  are never renamed — the same id in two inputs *is* the same mark, which is how the techniques tie together.
  An observation, cluster or **setup** id that collides with an earlier input's is prefixed with its input's
  id and recorded (`Combination.renamed`); a shared setup id would otherwise give two instrument setups one
  orientation unknown. Every observation is tagged with its technique. Every cluster survives whole, its
  covariance carried through the transformation (criterion 5).
* **Only frame-dependent content is transformed.** A held coordinate and a GNSS point take the full
  transformation and move to the target epoch along their station's velocity; a GNSS vector takes scale and
  rotation only (the translation cancels) and changes epoch by the difference of its ends' velocities; a GNSS
  ellipsoidal height moves by the vertical component of its station's displacement. Distances, angles,
  levelled differences and gravity belong to no frame and are untouched; terrestrial work is taken as made at
  the target epoch, which holds for a project's weeks and not for years in a deforming region. Approximate
  coordinates are carried across a frame change so they stay close, never along a velocity, and not recorded.
  Every transformation applied is recorded with its input and subject, and the solution's provenance carries
  them all (criterion 4).
* **Refused, naming the input:** a frame GeoComp cannot transform from (`combination_frame_irreconcilable`);
  a position — held, or GNSS — in an input with no frame (`combination_input_without_frame`) or no epoch
  (`combination_input_without_epoch`: never taken to be the combination's, FR-105, even where the frames
  already agree); a position that must change epoch with no velocity (`combination_epoch_without_velocity`);
  one station held by two inputs more than a millimetre apart (`combination_station_held_differently`).
* **`route(network, requested)`**: a combination with gravity goes to the in-house core whatever was asked,
  and the reason says why (criterion 6). So does one with any type DynAdjust has no letter for — a
  horizontal distance, say ([`07`](./07-engine-dynadjust.md) §4.2) — because sending the rest would adjust a
  different network. **Gravity is adjusted beside the geometry, not inside it**: nothing
  in the combination relates gravity to position, so the normal equations are block-diagonal and adjusting
  together gives exactly what adjusting apart does. `adjust_combination(gravity=)` takes the gravity network
  with its drift model and adjusts it in-house next to the geometric solution; gravity merged into the
  geometry as bare observations is refused (`combination_gravity_without_its_network`), because without its
  drift unknowns it would be adjusted as drift-free.
* **`technique_breakdown(run, network)`**: per technique, rows, redundancy and its share of the degrees of
  freedom, the technique's part of `vᵀPv`, `vᵀPv/r`, the largest |w| and the uncheckable observations — with
  weighted constraints and geoid priors as their own groups, so the parts add up to the whole exactly.
* **`adjust_combination(combination, geoid=, estimate_components=)`** runs the combination in the geocentric
  frame and returns the solution, the routing, the breakdown, the geoid residuals and, when asked, the
  variance components.

The combined frame was cross-validated against DynAdjust on a six-station GNSS and total-station survey:
coordinates within half the printed 0.1 mm and residuals within 0.05 mm and 0.0001″, with two modelling
differences in DynAdjust recorded in [`07`](./07-engine-dynadjust.md) §6.3.

---

### 6.2 As implemented (P9b)

**The four menu items** (`algorithms/integration/`) are presets over one algorithm. Each takes the network
documents the technique algorithms write — *Build baselines* ([`11`](./11-module-gnss.md) §4.4), *Classical
network*, levelling *Network adjustment* ([`10`](./10-module-levelling.md) §5) — and produces one solution, the
report with its *Techniques* section ([`19`](./19-visualization.md) §7.1), the result layers
([`19`](./19-visualization.md) §1.1) and, on request, the combined network.

| Preset | Inputs | Combines | Particular to it |
|---|---|---|---|
| GNSS and total station (FR-800) | GNSS, total station | geocentric | the total station may be in UTM |
| Total station and level (FR-801) | total station, levelling | in the total station's own CRS | heights alone when that is all there is |
| GNSS and level (FR-802) | GNSS, levelling | geocentric | the geoid model is required |
| Multiple techniques (FR-803) | any three of GNSS, total station, levelling, gravimetry | geocentric with GNSS, local without | gravity beside the geometry; fewer than three refused |

Shared: the frame and epoch (the epoch defaulting to the GNSS input's, else refused), station velocities as
CSV, the geoid model and its uncertainty, *fixed stations* held where the first input that places them says
they are (for GNSS, the base's coordinates from the processing), the datum, the engine, variance components by
technique, the confidence level.

**What the combination learned to do for them:**

* **A local combination** (`combine(frame=None)`): the inputs merged as they stand, in their one CRS —
  different ones refused naming each (`combination_frames_differ`), a GNSS position refused
  (`combination_gnss_in_local_frame`). Adjusted in `HEIGHT_1D` when every observation is a height or a height
  difference, in `SPACE_3D` otherwise. Every combination needs an epoch, local ones included
  (`combination_epoch_required`): a solution is at one or it is not a solution (FR-105).
* **A projected input in a geocentric combination** is read through a `GridFrame` — its Transverse Mercator
  parameters and the frame beneath — which the algorithm derives from QGIS's own CRS, the core carrying no
  projection database ([`07`](./07-engine-dynadjust.md) §4.4). Only starting positions use it, their heights
  lifted by the median ellipsoid-minus-grid difference at the stations another input places. A point held in
  grid coordinates is refused (`combination_projected_hold`): its height is not the ellipsoidal one.
* **A levelling benchmark** holds a height on a placeholder planimetry. In a local combination the hold is
  kept. In a geocentric one it becomes an **orthometric height observation** with its uncertainty, tested
  against the geoid like any other; one held exactly is refused (`combination_benchmark_held_exactly`), since
  it would make the geoid exact there, and the same benchmark in two networks is one observation, not two.
  Before this, a geocentric combination would have left such a station **silently free** — a height-only hold
  names none of X, Y, Z.
* **A station nothing places horizontally** — reached only through heights, not held horizontally — is refused
  by name in either three-dimensional frame (`combination_station_without_horizontal`), rather than left for a
  singular matrix to report.
* **Two agreeing holds of one station** — a benchmark's height and a control point's full position — merge into
  the fuller one; before, the first input's won, and the second input's starting position was shadowed by the
  benchmark's placeholder zeros.
* **Routing** keeps a local combination in-house (DynAdjust adjusts on the ellipsoid of a named frame) and one
  with orthometric observations (the in-house core estimates each undulation with the model's uncertainty,
  where DynAdjust would take separations as exact). When it allows DynAdjust, `adjust_with_dynadjust` runs it
  ([`07`](./07-engine-dynadjust.md) §6.4); the two engines agree to 0.75 mm on the combined survey.
* **The solution is complete**: the global test, data snooping and reliability per observation, as every
  single-technique algorithm's is, and in its provenance the per-technique breakdown, the geoid residuals and
  the variance components — so the report reads them from the saved document.

**Not done, named so the ticks below do not imply them.** The per-technique breakdown on the DynAdjust path (its
output carries no redundancy numbers; the report says so). A mark reached only by levelling in a
three-dimensional combination is refused rather than adjusted in height alone — a per-station component set
the core does not have. No `CONTROL` document: control is held through an input's own positions. A gravity
solution is written beside the geometric one, and the report covers the geometry.

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

### 7.1 State after P9a, and P9b

| Criterion | State |
|---|---|
| 1. A published combined example | **met** — Krumm's `Caspary` (GNSS baselines, slope distances, a zenith angle) reproduces its coordinates to 0.05 mm and its a-posteriori standard deviations to the printed 0.01 mm ([`22`](./22-reference-data-sources.md) §2.2) |
| 2. No geoid refuses; with one, the model is in the solution and the report | **met** — §3.2 |
| 3. A mis-scaled technique's factor recovered | **met** — §4.1 |
| 4. Two frames transform with a record; irreconcilable refused by input | **met** — §5.1, §6.1: GNSS in ITRF2014 and control in SIRGAS 2000 (2000.4, with velocities) combined in ITRF2020 at 2020.0 return the held marks to their truth to a micrometre; WGS 84 is refused naming the input |
| 5. Clusters survive intact | **met** — a 12 × 12 baseline covariance through a frame change, four direction sets |
| 6. Gravity routed in-house with the reason | **met** — including when DynAdjust was asked for, and the gravity network is adjusted, not dropped |
| 7. Per-technique breakdowns in the report | **met in P9b** — the report's *Techniques* section, from the solution's provenance, checked against the breakdown and through a saved document (`tests/qgis/test_adjustment_report.py`) |
| 8. Three techniques end to end, one solution | **met** — GNSS, total station and levelling with a geoid, in `tests/test_integration.py`; every station within 2 cm of the truth, the geoid residuals and variance components by technique on the same run |
