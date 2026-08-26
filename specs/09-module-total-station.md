# 09 — Module: Total Station

**Status:** Draft
**Requirements covered:** FR-400…FR-412; contributes to FR-204, FR-205.
**Source:** tex §Painel de Configuração Global, item 1 (Estação Total); modificações.md.
**Seed reference:** `topo_test/processing_prototype.ipynb` and `topo_test/raw_data.csv` — the project author's
own prototype of this module, adopted as reference dataset **RD-01**
([`20-testing-and-validation.md`](./20-testing-and-validation.md)).

This is the largest technique module and the first end-to-end vertical slice in the roadmap (phase P3),
because it exercises the whole stack — import, pre-processing with covariance propagation, network
formation, adjustment, statistics, visualisation — **without requiring any external engine**.

---

## 1. Menu structure

Per `tex §Painel de Configuração Global`, item 1, the Total Station submenu offers:

| Menu item | Requirement | §  |
|---|---|---|
| Generalised pre-processing | FR-400…FR-405 | §2 |
| Traverse | FR-406 | §4.1 |
| Resection | FR-407 | §4.2 |
| Forward intersection | FR-408 | §4.3 |
| Classical networks (triangulation, trilateration, triangulateration) | FR-409 | §4.4 |
| Trigonometric levelling (including leap-frog) | FR-410 | §4.5 |
| 3D radiation | FR-411 | §4.6 |

Each is a Processing algorithm (FR-005), so the whole chain can be assembled in the graphical modeller.

---

## 2. Generalised pre-processing (FR-400…FR-405)

The pipeline, each stage a separate algorithm with an inspectable output (the teaching requirement from
[`01-vision-and-scope.md`](./01-vision-and-scope.md) §3, profile P1):

```text
raw readings → face reduction → instrument corrections → atmospheric correction
   → EDM corrections → geometric reductions → observations ready for adjustment
```

Uncertainty is propagated at every stage (FR-412, FR-204, FR-205); no stage produces a bare float.

### 2.1 Face-left / face-right reduction (FR-400)

Combining direct and reverse pointings (PD / PI) cancels collimation error, horizontal-axis tilt and
vertical index error to first order.

**Horizontal.** The two faces differ nominally by 180°. The mean must be computed as a **circular** mean —
the naive arithmetic mean is wrong whenever the pair straddles the 0°/360° discontinuity. Concretely, with
PD = 181° and PI = 1°, an arithmetic mean gives 91°, which after the conventional ±90° adjustment yields 1°
instead of 181°.

> **Prototype note — corrected in phase P3.** `pd_pi_H()` in `processing_prototype.ipynb` uses the
> arithmetic mean with a `mean > 180` branch. This document previously said it was "correct for the RD-01
> data, and wrong for pairs that straddle the wrap". **The first half of that is false**, and it was found
> by implementing the circular form and comparing: the prototype puts the `3,1,2` foresight direction at
> **19.110139°** where the correct reduction gives **199.110139°**, exactly 180° away. Every other value in
> `processed_data.csv` agrees to 1e-12.
>
> Two independent checks settle which is right, and both are tests:
>
> | Check | With the published 19.110139° | With the correct 199.110139° |
> |---|---|---|
> | Sum of the triangle's interior angles | 38.240556° | 180.019167° |
> | 2–3 distance implied by the law of cosines, against 24.349 m measured | 4.427 m | 24.362 m |
>
> The production implementation MUST use the circular form. Both the wrap case and this row MUST be test
> cases.

**Vertical.** V = (V_PD − V_PI + 360°)/2, equivalent to the prototype's `((PD - PI)/2) + 180`, which is
correct.

**Diagnostics — required, not optional.** The face pair carries information the mean throws away:

| Diagnostic | Meaning | Action |
|---|---|---|
| Collimation, c = (H_PD − H_PI ± 180°)/2 | Instrumental, should be stable across a setup | Report per pair and per setup; flag drift |
| Vertical index error, i = (V_PD + V_PI − 360°)/2 | Instrumental, should be stable | Report; compare against the stored constant (FR-061) |
| Distance difference between faces | Should be within the EDM's precision | **Flag as a blunder candidate** |

> **Prototype note, and why this diagnostic matters.** In `topo_test/raw_data.csv`, the pair
> `2,3,1,PD,R … 24.361` / `2,3,1,PI,R … 23.361` differs by exactly 1.000 m on the same line — while every
> other face pair in the file agrees to the millimetre. The prototype averages them silently to 23.861 m,
> and that value propagates into `processed_data.csv`. This is almost certainly a transcription error in the
> raw data. GeoComp MUST flag it rather than average it. Reproducing this detection is an acceptance
> criterion (§7).

The reduction also computes the **mean of repeated sets** with the dispersion of the repetitions, which is
an empirical precision estimate and feeds the stochastic model
([`05-uncertainty-and-covariance.md`](./05-uncertainty-and-covariance.md) §5).

### 2.2 Instrument corrections (FR-402)

Applied from the instrument profile (FR-061, FR-069): vertical index correction where face reduction was not
possible (single-face observations), collimation where applicable, and horizontal-axis tilt. Each correction
parameter has its own uncertainty, which propagates (FR-204).

### 2.3 Atmospheric correction (FR-401)

The first-velocity correction: the measured distance is scaled by the ratio of the reference refractive index
assumed by the EDM to the actual refractive index computed from temperature, pressure and humidity. The
correction is expressed in ppm and is typically 1 ppm per ≈ 1 °C or ≈ 3.5 hPa.

- The model is selectable in Global Settings (FR-062), with the manufacturer's formula for the configured
  instrument as the default.
- **The uncertainty of the meteorological readings propagates** (FR-204). A ± 2 °C uncertainty is roughly
  ± 2 ppm — 2 mm over a kilometre. On a 20 m sight it is negligible; the propagation makes that visible
  rather than assumed.
- Where meteorological data are absent, the configured defaults are used and the result is marked
  `APPROXIMATE` with the `TYPE_DEFAULT` strategy (FR-202, FR-203).

### 2.4 EDM corrections (FR-403)

Additive constant (instrument plus reflector — a single combined constant from calibration, or the two
separately when known), scale factor from calibration, and cyclic error where the calibration provides it.
All come from the instrument and reflector profiles with their calibration uncertainties, which propagate.

**Rule:** a correction already applied by the instrument is not applied again. The instrument profile records
what the instrument applies internally, and applying a prism constant twice is a silent metre-level error.

### 2.5 Basic reductions (FR-404)

From the corrected slope distance d, zenith angle z, instrument height hi and target height hs:

- horizontal distance d_h = d·sin z
- vertical component d_v = d·cos z
- height difference Δh = d_v + hi − hs

All three propagate covariance, including the d–z correlation from the common pointing
([`05-uncertainty-and-covariance.md`](./05-uncertainty-and-covariance.md) §4.1). This is exactly what the
prototype computes (`DH`, `DV`, `dH`) — the difference is that GeoComp attaches an uncertainty to each.

### 2.6 Geometric and atmospheric-geometric reductions (FR-405)

- **Earth curvature and refraction** in trigonometric heighting: (1 − k)·d²/(2R), with k the refraction
  coefficient (configurable, default ≈ 0.13). k is poorly known and varies through the day; its uncertainty
  propagates, and it is the dominant error source on long sights. GeoComp reports the correction's magnitude
  so the user can see when it stops being negligible.
- **Reduction to the ellipsoid**, using the station heights and the geoid model where orthometric heights are
  involved (FR-165, FR-804).
- **Reduction to the projection plane**, using the point scale factor of the project CRS.

Each carries the uncertainty of the heights and coordinates it used (FR-205) — the reduction of a distance to
the ellipsoid is only as certain as the height it was reduced with.

---

## 3. The stochastic model

Per-observation σ from the instrument profile
([`05-uncertainty-and-covariance.md`](./05-uncertainty-and-covariance.md) §5):

| Observation | Typical model |
|---|---|
| Direction | Constant σ, optionally decomposed into pointing and reading components; σ scales with 1/√(number of sets) |
| Horizontal angle | From two directions, **correlated** through the shared setup — never independent |
| Zenith angle | Constant σ, plus a refraction term growing with distance |
| Slope distance | σ = a + b·d (the manufacturer's specification, with a user scale factor) |
| Instrument / target height | Constant σ, typically 1–2 mm — routinely the dominant error in short-sight height differences |

Directions from one setup form a `DIRECTION_SET` cluster (FR-104) sharing an orientation unknown.

---

## 4. Survey computations

All are implemented over the in-house adjustment core
([`06-adjustment-core.md`](./06-adjustment-core.md)); each also produces approximate coordinates suitable as
starting values for a rigorous network adjustment.

### 4.1 Traverse (FR-406)

Open, closed (loop) and connected (enquadrada). GeoComp computes the angular misclosure, the linear
misclosure and the relative precision, compares them against the configured tolerances (FR-061), and then
adjusts.

**Two adjustment paths, both offered, clearly distinguished:**

1. **Classical distribution** — the compass (Bowditch) and transit rules. These are what students are taught
   and what many specifications still require; they are *not* least squares and do not produce a rigorous
   covariance. Results are labelled `APPROXIMATE` (FR-203).
2. **Least squares** — the rigorous path, giving residuals, statistics, reliability and error ellipses.

Presenting both on the same data is directly pedagogically valuable: the student sees what the classical
rule approximates.

### 4.2 Resection (FR-407)

Coordinates of the occupied station from directions and/or distances to known points. Both the classical
three-point angular solution and the general least-squares solution over *n* points. The **danger circle** —
the configuration where the occupied station lies on the circle through three known points and the solution
is indeterminate — MUST be detected and reported, not returned as a numerically noisy answer.

### 4.3 Forward intersection (FR-408)

Coordinates of a sighted point from two or more known stations, by directions, distances, or both. With more
than the minimum, by least squares with residuals and an error ellipse. Weak intersection geometry
(near-parallel rays) is reported through the error ellipse's shape rather than left for the user to discover.

### 4.4 Classical networks (FR-409)

Triangulation (angles), trilateration (distances) and triangulateration (both), adjusted by least squares
with the full statistical treatment of [`06-adjustment-core.md`](./06-adjustment-core.md) §4. Free and
constrained solutions are both available (FR-222) — this is precisely the "redes livres e amarradas"
comparison the proposal names as a pedagogical goal.

### 4.5 Trigonometric levelling (FR-410)

Height differences from zenith angles and slope distances, with curvature and refraction (§2.6) and
instrument and target heights.

**Leap-frog** is required explicitly by the proposal: the instrument is placed between two targets and
observes both, so that refraction and instrument-height errors cancel between the two sights. This changes
the error model, not just the arithmetic — the correlation between the two sights is what produces the
cancellation, and it MUST be modelled, not approximated by treating the two as independent.

Output height differences feed the levelling network adjustment
([`10-module-levelling.md`](./10-module-levelling.md)) and combined adjustments
([`13-module-integration.md`](./13-module-integration.md)).

### 4.6 3D radiation (FR-411)

Three-dimensional coordinates of a point from one setup: horizontal angle, zenith angle, slope distance,
instrument and target heights, and the orientation of the setup. The full 3×3 covariance of the resulting
position is produced as a cluster (FR-104) — the three coordinates are strongly correlated through the shared
pointing, and treating them as independent is wrong.

Batch radiation of many detail points from one setup is supported, as this is the routine production case.

---

## 5. Data import

RD-01's `raw_data.csv` layout is the reference case for the field-mapping importer (FR-160):

| Column | Meaning |
|---|---|
| `R`, `E`, `V` | Backsight (ré), occupied (estação), foresight (vante) station identifiers |
| `pos` | `PD` / `PI` — face left / face right |
| `vis` | `R` / `V` — which of the two is being sighted |
| `HG`, `HM`, `HS` | Horizontal angle, degrees / minutes / seconds |
| `VG`, `VM`, `VS` | Zenith angle, degrees / minutes / seconds |
| `D` | Slope distance |
| `hi`, `hs` | Instrument height, target height |

Requirements this exercises: sexagesimal parsing into radians; a locale-independent decimal separator on
import (FR-095); a saved, reusable field mapping (FR-160); per-record error reporting (FR-166).

The importer MUST also accept the common vendor export formats where the format is documented, and MUST
never silently discard a column it does not recognise.

---

## 6. Configuration

From Global Settings ([`15-ui-menu-and-settings.md`](./15-ui-menu-and-settings.md)), all layered per FR-068:
instrument profiles with nominal precisions and calibration constants (FR-061); reflector profiles with
prism constants; default meteorological values and the atmospheric model (FR-062); refraction coefficient;
closure tolerances by traverse class; and default weights per observation type (FR-064).

---

## 7. Acceptance criteria

1. **RD-01 reproduces, except where the prototype is wrong.** The full pipeline over
   `topo_test/raw_data.csv` reproduces `topo_test/processed_data.csv` — `H_corr`, `V_corr`, `DH`, `DV`,
   `dH` — to within 1e-9 **at every value except the `3,1,2` foresight `H_corr`**, where the correct
   reduction gives 199.110139° against the prototype's 19.110139° (§2.1). A test asserts the agreement
   everywhere else *and* the disagreement there, with the triangle-closure and law-of-cosines checks that
   establish which is right. Every value additionally carries an uncertainty.
2. **Both of RD-01's defects are caught.** The `2,3,1` face-pair distance discrepancy of 1.000 m (§2.1) is
   flagged as a blunder candidate, not averaged; and the `3,1,2` direction is reduced correctly rather than
   reproduced.
3. **The wrap case is correct.** Face reduction with PD = 181°, PI = 1° returns 181°, and a test asserts it.
4. Face reduction against a synthetic dataset with known injected collimation and index error recovers both
   to the injected values.
5. Traverse misclosure and both adjustment paths reproduce a published worked example
   ([`20-testing-and-validation.md`](./20-testing-and-validation.md)).
6. Resection on a danger-circle configuration is detected and reported, not solved.
7. A triangulateration network adjusted free and constrained satisfies the consistency check in
   [`06-adjustment-core.md`](./06-adjustment-core.md) §7.2.
8. Every output of every algorithm in this module carries an uncertainty and an `uncertainty_mode`; a test
   asserts it over the module's public API.
9. Running the whole chain from the GeoComp menu on RD-01 produces styled QGIS layers with error ellipses
   without further user action (FR-905).
