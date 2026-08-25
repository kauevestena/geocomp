# 12 — Module: Gravimetry

**Status:** Draft
**Requirements covered:** FR-700…FR-703.
**Source:** tex §Painel de Configuração Global, item 4 (Gravímetro).

---

## 1. Why this module is entirely in-house

DynAdjust has no gravity measurement type ([`07-engine-dynadjust.md`](./07-engine-dynadjust.md) §1.1), and
`rnx2rtkp` is unrelated. **Gravimetry runs wholly on the in-house adjustment core**
([`06-adjustment-core.md`](./06-adjustment-core.md)).

This is the clearest single refutation of the archived roadmap's premise that "all heavy geodetic math is
delegated to DynAdjust and RNX2RTKP" — a menu group required by the proposal has no engine behind it at all.
It is one of the reasons ADR-0002 exists.

---

## 2. Menu structure

Per `tex §Painel de Configuração Global`, item 4:

| Menu item | Requirement |
|---|---|
| Pre-processing (scale, tide, drift) | FR-701 |
| Gravimetric network adjustment | FR-700, FR-702 |

---

## 3. Observation model

Two observation types ([`04-data-model.md`](./04-data-model.md) §4):

- `GRAVITY` — an absolute determination at one station.
- `GRAVITY_DIFFERENCE` — a relative determination between two stations, the output of the overwhelmingly
  common relative gravimeter.

A relative gravimeter reads in **instrument units**, not in gravity units. The conversion is the scale
calibration (§4.1), and the reading is contaminated by tides and by drift. Pre-processing addresses all
three.

Units: SI throughout internally (m·s⁻²); display in mGal and µGal per the user's preference (FR-067), since
that is the working unit of the field. The conversion is display-only, never applied to stored values
([`04-data-model.md`](./04-data-model.md) §6).

---

## 4. Pre-processing (FR-701)

### 4.1 Instrument scale correction

Converts instrument reading to gravity units, using the manufacturer's calibration table (typically a
piecewise-linear table over the instrument's range) plus a calibration factor determined on a calibration
line.

- The calibration table and factor live in the instrument profile (FR-061, FR-069).
- **The calibration factor's uncertainty propagates** (FR-204). It is a multiplicative term, so its effect
  grows with the size of the gravity difference — it is negligible on a short line and dominant on a long
  one, and the propagation makes that visible.

### 4.2 Tidal correction

Removes the solid-Earth tide and, where required, ocean loading. Computed from station position and
observation time, so both must be recorded with the reading — a gravity observation without a timestamp
cannot be tidally corrected, and is rejected at validation.

Model selectable in Global Settings, with the correction's magnitude reported (it reaches a few hundred µGal
and varies over hours — it is never negligible in precise work).

### 4.3 Drift

A relative gravimeter's reading changes with time even at a fixed station.

- **Static drift** — the instrument at rest, approximately linear over hours.
- **Dynamic drift** — additional drift induced by transport, shock and tilting between stations, which is
  the part that is neither linear nor predictable.

**Two treatments, and the distinction matters (FR-702):**

1. **Pre-correction from repeated base readings.** The classic field method: return to a base station,
   observe the drift directly, distribute it linearly in time. Simple, and adequate for many purposes. The
   result is `APPROXIMATE` where the linear assumption is imposed rather than verified.
2. **Joint estimation in the adjustment.** Drift parameters are estimated *simultaneously with* station
   gravity values (FR-702). This is the rigorous treatment, because drift and gravity differences are not
   separable by pre-correction alone — a pre-corrected drift error propagates straight into the gravity
   values with no way to detect it, whereas jointly estimated drift is subject to the adjustment's residual
   analysis and reliability testing like any other parameter.

GeoComp offers both, and the joint estimation is the default whenever the observation scheme (repeated
occupations, closed loops) supports it. Which was used is recorded in the result.

Drift models: linear in time (one parameter per instrument per session), polynomial of user-selected degree,
and per-session parameters where the instrument was transported between sessions.

---

## 5. Network adjustment (FR-700)

Gravity differences form a network in exactly the way height differences do: a 1D network in gravity, with
the same structure and the same theory
([`06-adjustment-core.md`](./06-adjustment-core.md), [`10-module-levelling.md`](./10-module-levelling.md) §4).

- **Parameters:** station gravity values, plus drift parameters (§4.3) and scale factors where these are
  estimated rather than fixed.
- **Datum:** the network is free in gravity until at least one absolute value, or one station of known
  gravity, is introduced. The datum defect is 1 (a constant offset) plus 1 more if scale is estimated.
  GeoComp reports the detected defect and how it was removed, exactly as for other network types.
- **Weighting:** from the instrument's precision and the reading dispersion, plus a term for the elapsed
  time or transport between readings where the drift model does not absorb it.
- **Statistics:** the full treatment — global test, data snooping, internal and external reliability
  (FR-250…FR-253). A gravimetric network is small and often weakly redundant, so reliability analysis is
  proportionally *more* important here than in a large geodetic net: many observations may be uncheckable,
  and the user needs to know which.

**Absolute and relative observations combine** in one adjustment, with absolute values entering as weighted
observations of a station's gravity, not as hard constraints — an absolute determination has an uncertainty
and it should be used.

---

## 6. Configuration

In Global Settings, under a Gravimeter section (FR-060, FR-061): gravimeter profiles with calibration tables
and factors, nominal precision, and drift characteristics; tidal model selection; default weighting;
and display units.

---

## 7. Interaction with other modules

Gravity is not adjusted jointly with coordinates in v1.0 — the coupling (through the vertical gradient and
the geoid) is real but belongs to a physical-geodesy scope this project has not claimed
([`01-vision-and-scope.md`](./01-vision-and-scope.md) §5).

What is supported: gravity values are stored against the same stations as other observations, so they are
available alongside coordinates, are exported together, and are visualised on the same map.

---

## 8. Acceptance criteria

1. Scale, tidal and drift corrections each reproduce a worked example to published precision.
2. A gravimetric network with a synthetic linear drift injected recovers the drift parameter to within its
   estimated uncertainty, and recovers the true station gravity values.
3. Pre-corrected drift and jointly estimated drift give consistent results on data where the linear
   assumption holds, and demonstrably different results where it does not — with the difference reported.
4. The datum defect of a gravity-difference-only network is detected as 1 and reported.
5. Absolute and relative observations combine correctly, with absolute values weighted rather than fixed.
6. Uncheckable observations (redundancy number ≈ 0) are flagged prominently.
7. All values are stored in SI and displayed in the configured unit; a test asserts no unit conversion
   reaches storage.
8. Every output carries an uncertainty and an `uncertainty_mode` (FR-703).
