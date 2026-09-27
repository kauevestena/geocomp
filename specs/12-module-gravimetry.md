# 12 — Module: Gravimetry

**Status:** Draft. The computation is implemented (phase P8a, `core/techniques/gravimetry/` and
`core/instruments/gravimeter.py`); the menu, settings and layers are P8b's.
**Requirements covered:** FR-700…FR-703.
**Source:** tex §Painel de Configuração Global, item 4 (Gravímetro).

---

## 1. Why this module is entirely in-house

DynAdjust has no gravity measurement type ([`07-engine-dynadjust.md`](./07-engine-dynadjust.md) §1.1), and
`rnx2rtkp` is unrelated. **Gravimetry runs wholly on the in-house adjustment core**
([`06-adjustment-core.md`](./06-adjustment-core.md)).

**But not because the mathematics is exotic — the opposite.** A gravity difference and a height difference are
the *same observation equation*: an observed difference between two station parameters, partials −1 and +1.
GeoComp implements them as one function, and `tests/test_gravimetry_is_levelling.py` asserts that the two
design matrices are identical element for element and that the two adjustments agree on estimates, residuals,
variance factor and redundancy. A drift-corrected gravimetric network is a 1D difference network under a
relabelling, and DynAdjust adjusts those.

What has no engine behind it is everything *around* the adjustment: the corrections in §4 below, and above all
**drift estimated jointly with the network** — because drift and gravity differences are not separable by
pre-correction alone (§4.3), so pre-correcting is an approximation the in-house core does not have to make.
That is the refutation of the archived roadmap's "all heavy geodetic math is delegated" premise, and one of
the reasons ADR-0002 exists; see its Amendment 1, which corrects the overstated version of this claim.

Three things follow. This module is **much smaller than planned**, since the adjustment is already written and
tested. It **can** be cross-validated against DynAdjust by relabelling, which the original plan assumed
impossible. And it is why a combined gravimetric-and-levelling adjustment
([`13-module-integration.md`](./13-module-integration.md)) is possible at all: the two are the same kind of
unknown observed the same way.

---

## 2. Menu structure

Per `tex §Painel de Configuração Global`, item 4:

| Menu item | Algorithm | Requirement |
|---|---|---|
| Pre-processing (scale, tide, drift) | `geocomp:gravimetry_preprocess` | FR-701 |
| Gravimetric network adjustment | `geocomp:gravimetry_network` | FR-700, FR-702 |

**Built in phase P8b.** *Pre-processing* reads a gravimeter file (§3.1), reduces every reading (§4) and writes
a **reduced readings** document — the readings in SI with the gravimeter profiles they were reduced with, so
the network propagates the calibration the reduction applied and not whatever the library says by then. It
also writes the corrections per reading, and each session's drift as its base readings show it, with whether
the session lets the network estimate it jointly; **nothing is subtracted for drift there**, because a drift
estimated with the station values uses every re-occupation (§4.3). *Gravimetric network adjustment* reads that
document and writes the solution, a report, a CSV and two layers (§5).

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

**A station's gravity is not part of its position** (phase P8a). It was carried in the `up` slot of a
`Position` until then, which enforces metres, so no gravity solution could even be written. A known gravity is
`ConstraintSpec.gravity`, an adjusted one `AdjustedStation.gravity`, both in m·s⁻²; the station's position
says where it is — the tide and the map both need that — and nothing else
([`04-data-model.md`](./04-data-model.md) §2.4).

**Readings, occupations, differences.** A reading is what the instrument recorded: a station, an instant, a
value, an instrument and a *session* — a stretch of the instrument's operation with one drift behaviour.
Consecutive readings at one station within a session are one **occupation**: a CG-5 records a reading a
minute for as long as it stands on a mark, and those are one visit, not sixty. Their weighted mean, at their
weighted mean time, is what differences are formed from; treating the readings of one visit as independent is
recorded as `INDEPENDENCE_ASSUMED`.

### 3.1 Reading a gravimeter file (phase P8b)

`geocomp/io/gravimeter_files.py` reads three formats, recognised from the content rather than the name, into
readings with every value in SI:

- **Scintrex CG-5** text exports. The header gives the location, the clock's `GMT DIFF.` and whether the
  instrument removed the tide; a reading's precision is `SD / √DUR`, the standard error of the samples it
  averaged (Hector and Hinderer, 2016).
- **ZLS Burris** exports, in the layout USGS's GSadjust reads. They state no precision.
- **A plain CSV** with named columns — `station`, `time` and `reading_mgal`, and optionally `sd_mgal`,
  `instrument`, `session`, `latitude_deg`, `longitude_deg`, `height_m`, `sensor_height_m`, `tide_applied`. A
  time without its UTC offset is refused: the tide depends on the time to the minute.

**What the instrument already did is kept, not repeated.** A CG-5 with *Tide Correction: YES* and a Burris
with a non-zero tide column have removed the tide; *replace* adds it back before GeoComp removes its own. A
Burris tide column of zero says only that the meter applied none — its correction was off, or the file is
synthetic and tide-free — so the gravimeter profile decides (`applies_tide`), and without a profile GeoComp
removes the tide.

**The clock.** Which way a CG-5's GMT difference runs is settled by the file, not assumed: when GeoComp needs
UTC, the instrument's tide column is compared with Longman's under both readings, and the one that agrees to
3 µGal is used — or the file is refused unless the offset is given. A difference of **zero** is taken as UTC
and the notes say so, with how well the instrument's tide agrees under that reading (1.2 µGal on RD-07's
survey). When the instrument's tide is kept, only elapsed time matters and the offset cancels.

**A precision floor** is added in quadrature to each reading's own precision, for what the instrument's
statistic knows nothing of — tilt, temperature, transport. It is a nominal figure, so a precision that
includes one is labelled approximate with `NOMINAL_PRECISION` (FR-203).

**Not built: a CG-6 reader.** The roadmap named one. No CG-6 export was reachable to write it against —
GSadjust's test data has CG-5 and Burris files only — and a reader written from memory of a format is a
reader of a guess. A CG-6 survey can be read today through the CSV.

---

## 4. Pre-processing (FR-701)

### 4.1 Instrument scale correction

Converts instrument reading to gravity units, using the manufacturer's calibration table (typically a
piecewise-linear table over the instrument's range) plus a calibration factor determined on a calibration
line.

- The calibration table and factor live in the instrument profile (FR-061, FR-069):
  `GravimeterProfile`, with a `CalibrationTable` for a counter-reading instrument and none for one that reads
  gravity. A table whose value column disagrees with its own interval factors by more than 0.01 mGal — more
  than its printing explains — is refused, naming the row: one mistyped row converts every reading above it
  wrongly.
- **The calibration factor's uncertainty propagates** (FR-204). It is a multiplicative term, so its effect
  grows with the size of the gravity difference — it is negligible on a short line and dominant on a long
  one, and the propagation makes that visible.
- **Where it propagates to is the design decision.** The factor multiplies every reading of the instrument,
  so its error is perfectly correlated across all of them. On one counter reading — thousands of milligal from
  zero — 10⁻⁴ of it is a few hundred microgal; in a difference nearly all of that cancels. It is therefore put
  on **no reading**: the reduction applies the factor's value and the network builder adds
  `σ_k² (A g)(A g)ᵀ` to the covariance of the differences, where `A g` is what survives of it in each one —
  the difference itself, correlated across every observation of the instrument (§5).
- **Applied-once.** An instrument that removes its own tide (a CG-5 with *Tide Correction: YES*) says so in
  its profile, and a reading can override that per survey. Removing the tide twice is a silent error of
  a few hundred microgal.

### 4.2 Tidal correction

Removes the solid-Earth tide and, where required, ocean loading. Computed from station position and
observation time, so both must be recorded with the reading — a gravity observation without a timestamp
cannot be tidally corrected, and is rejected at validation.

Model selectable in Global Settings, with the correction's magnitude reported (it reaches a few hundred µGal
and varies over hours — it is never negligible in precise work).

**The model is Longman (1959)** — the closed form relative gravimeters' own firmware uses, needing no
catalogue and no download. Its accuracy is measured, not asserted **[V]**:

| Against | Measured |
|---|---|
| A Scintrex CG-5's own firmware, 2,096 readings of a real survey that record the correction applied, printed to 1 µGal | **0.60 µGal rms, 1.51 µGal worst**, mean −0.04 µGal |
| ETERNA PREDICT 3.4 with the Hartmann–Wenzel (1995) catalogue, rigid Earth on both sides, three latitudes, two epochs | **0.76–1.21 µGal rms, 2.0–4.2 µGal worst**, slightly worse in 2026 than in 2013 |

The first checks the transcription; the second is the formula's own accuracy, and the stated model
uncertainty — **1.5 µGal**, `MODEL_UNCERTAINTY` — is derived from it (worst rms × 1.16, rounded up), with a
test that fails if the two part. The firmware matches at an amplification factor of **1.16**, the default;
at Longman's own 1.2 it misses by 1 µGal in the mean and 7 at worst.

Two limits, recorded rather than hidden: one factor for every frequency, where an elastic Earth's differ
slightly between diurnal, semidiurnal and long-period tides; and the *whole* tide removed, permanent part
included, so values are **tide-free**. An absolute value published zero-tide (IAG Resolution 16, 1983)
differs by a latitude-dependent few µGal; the result notes the mismatch rather than converting silently.

**Ocean loading is deferred to P12** ([`ROADMAP.md`](./ROADMAP.md)). It needs per-station loading
coefficients from the Onsala service, which is unreachable from the development environment, and nothing
reachable could check an implementation. Written and unverified would be a claim, not a feature — the same
reasoning that moved FR-352.

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

**The formulation (phase P8a).** Drift is a polynomial per session in `τ = t / T`, `t` seconds since the
session's first occupation and `T` a declared scale — one hour by default — so each coefficient is an
acceleration with a stated meaning. A difference between occupations at `t_from` and `t_to` sees
`Σ c_k (τ_to^k − τ_from^k)`: the drift at both. MCGravi and pyGrav use `(τ_to − τ_from)^k`, which agrees at
degree 1 and above it makes a quadratic drift depend on how far apart a pair was, not when.

**Estimability.** A session's drift is determined by its own occupations when the design over one column per
station and one per degree has full rank — something re-occupied, at enough distinct times. A session that
visits each station once is refused, naming it, rather than reported later as a singular system with the
wrong stations blamed. The check is local and so conservative.

**Two findings that change how treatment 1 should be read [V].**

1. **Pre-correction with its drift estimate's covariance carried in full is not an approximation: it is the
   joint estimate**, to 3×10⁻¹⁰ µGal on USGS's test surveys. The base readings' residuals carry no information
   about the station values, so a two-step estimate propagated exactly reproduces the one-step one. What
   makes field pre-correction worse is **discarding that covariance** — treating the corrected differences as
   independent. That is the version criterion 3 distinguishes: on a linear drift it agrees with joint
   estimation to under 1 µGal against a precision of 3.7 µGal; on USGS's non-linear Test 5 it differs by up to
   245 µGal at every station, and both treatments flag the model as wrong (§8).
2. **There is no scheme where pre-correction works and joint estimation does not.** Pre-correction needs the
   base read at `degree + 1` distinct times, and those readings alone make the joint design full rank. So there
   is nothing for an "automatic" choice to choose between: joint estimation is the default, and pre-correction
   is offered for the classical workflow and for comparison. A pre-correction whose base fit had no redundancy
   is labelled `MODEL_ASSUMED`, and one whose base residuals fail their χ² test says so.

### 4.4 Reduction to the mark

*Added in phase P8a; not in the original specification.* The sensor sits some tens of centimetres above the
mark and gravity falls by about 3 µGal per centimetre of height. A network whose sensor heights all match
loses nothing without this; one that combines relative readings with an absolute value quoted at the mark
does not, and the error is tens of microgal and looks like nothing. A reading may carry its sensor height; it
is reduced with the normal free-air gradient (−0.3086 mGal/m) or a station's measured one, both terms'
uncertainties propagated. A reading without a sensor height is taken to refer to the mark, and the result says
so in words.

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

**The covariance of the differences is exact (phase P8a).** Every observation of one instrument is a linear
function of its occupations, `z = A y`, so `C_z = A Σ_y Aᵀ + σ_k² (A g)(A g)ᵀ`: the first term is why
successive differences are correlated — each inner occupation appears in two, with opposite signs — and why
differences from a base share the fitted base value; the second is the calibration factor (§4.1). Both go into
one correlated cluster per instrument (FR-104). `DriftOptions(correlated=False)` drops the correlation, as
MCGravi and pyGrav do, and records `INDEPENDENCE_ASSUMED`; it exists so their published solutions can be
reproduced (RD-07), not because it is better.

**What the result states.** The defect of the relative observations (1) and what removed it — a fixed station,
weighted absolute values by name, or an inner constraint that leaves every value relative to their mean; each
session's treatment and drift with its covariance; every uncheckable observation by name — a pendant station
and a lone absolute value are the common cases; and a solution `uncertainty_mode` that is approximate whenever
any input was. That last one was set by nothing before phase P8: every solution of every technique claimed to
be rigorous, including one weighted entirely by a brochure's precision (FR-203). `to_solution` now derives it.

**Known gravity, as the network algorithm takes it (phase P8b).** `station=value` in mGal: with `±sigma` it is
an absolute determination and enters weighted, as above; without one the station is **held**, which makes it
the datum and every uncertainty relative to it — a choice, not a measurement, and the report says which. With
neither, the network is adjusted with an inner constraint and every value is relative to the stations' mean.

**The result as layers (phase P8b).** *Gravity stations* — every station, held ones included, with its value
and sigma in the display unit and in SI, how it was determined, and the w-test's decision on its absolute
value if it has one; *Gravity differences* — one line per difference with its residual, redundancy, MDB and
decision. An uncheckable difference is drawn as prominently as a blunder candidate, in a colour of its own,
and a lone absolute value gets the same colour as an outline: in a weakly redundant network it is the more
common warning and the easier one to miss. The report lists them by name before anything else.

**Not built in P8a: scale estimated as a parameter.** A calibration factor enters known, with its uncertainty
propagated. Estimating it needs at least two absolute values far enough apart in gravity to define a scale,
adds one to the defect, and makes the model bilinear; it is named here so the parameter list above does not
imply it.

---

## 6. Configuration

In Global Settings, under a Gravimeter section (FR-060, FR-061): gravimeter profiles with calibration tables
and factors, nominal precision, and drift characteristics; tidal model selection; default weighting;
and display units.

**What phase P8b declared — six settings, every one read by the computation:**

| Setting | Default | Read by |
|---|---|---|
| `gravimeter.tide_model` — Longman (1959) or none | Longman | *Pre-processing*: the tide model |
| `gravimeter.tide_amplification` — the gravimetric factor | 1.16 | *Pre-processing*: the tide's amplification |
| `gravimeter.drift_mode` — joint or pre-corrected | joint | *Network adjustment*: the drift treatment |
| `gravimeter.drift_degree` | 1 | both: the preview, and the network's polynomial |
| `gravimeter.precision_floor` — the default weighting, m·s⁻² | 0 | *Pre-processing*: added in quadrature to each reading |
| `gravimeter.display_unit` — mGal or µGal | mGal | every table, CSV, layer and report that shows gravity |

Each is the default of the algorithm parameter of the same meaning, so a run can override it (FR-068).
**Stored in SI, shown in the display unit** (§3): the reduced readings document, the solution and the layers'
`gravity_si` column are m·s⁻²; what a person reads is converted and names its unit.

**Gravimeter profiles are not settings**, for the reason level profiles are not
([`15-ui-menu-and-settings.md`](./15-ui-menu-and-settings.md) §2.1): they are named records with their own
uncertainties, and they travel as a profile library document, which *Pre-processing* takes. A library that
lacks an instrument the file names is refused rather than completed silently. **With no library**, each
instrument's own scale is used with a calibration factor of one labelled `MODEL_ASSUMED`: its uncertainty
cannot be stated, so none is propagated, and the label carries through to the solution, which then does not
call itself rigorous.

*Drift characteristics* per profile are not modelled: drift is estimated per session from the data (§4.3),
which is what FR-702 asks for, and a profile's typical rate would inform nothing the adjustment uses.

---

## 7. Interaction with other modules

Gravity is not adjusted jointly with coordinates in v1.0 — the coupling (through the vertical gradient and
the geoid) is real but belongs to a physical-geodesy scope this project has not claimed
([`01-vision-and-scope.md`](./01-vision-and-scope.md) §5).

What is supported: gravity values are stored against the same stations as other observations, so they are
available alongside coordinates, are exported together, and are visualised on the same map.

---

## 8. Acceptance criteria

Status after phase P8b, with the evidence for each in [`ROADMAP.md`](./ROADMAP.md) P8a and P8b:

1. Scale, tidal and drift corrections each reproduce a worked example to published precision. — **Tide and
   drift: met** (the CG-5 firmware to its printed microgal; pyGrav's published solution). **Scale: not met
   against a published example** — none was reachable; a constructed table in a manufacturer's layout checks
   the arithmetic, and USGS's surveys with 3, 5 and 10 % calibration errors check the factor end to end.
2. A gravimetric network with a synthetic linear drift injected recovers the drift parameter to within its
   estimated uncertainty, and recovers the true station gravity values. — **Met** on USGS's synthetic
   surveys, whose truth, drift and calibration are published beside them: every station within 3σ, the
   0.01 mGal/h drift within 2σ.
3. Pre-corrected drift and jointly estimated drift give consistent results on data where the linear
   assumption holds, and demonstrably different results where it does not — with the difference reported.
   — **Met, for classical pre-correction** (§4.3): under 1 µGal on a linear drift, up to 245 µGal and
   significant at every station on a non-linear one. Pre-correction with its covariance carried in full is
   identical to joint estimation, and that is asserted too.
4. The datum defect of a gravity-difference-only network is detected as 1 and reported. — **Met**, and
   reported with what removed it.
5. Absolute and relative observations combine correctly, with absolute values weighted rather than fixed.
   — **Met**: two absolute values in conflict both move and both carry a residual.
6. Uncheckable observations (redundancy number ≈ 0) are flagged prominently. — **Met**: by name in the
   result; first in the report, before the adjusted values; in the log as warnings; and on the map in a colour
   of their own, as prominent as a blunder candidate (§5).
7. All values are stored in SI and displayed in the configured unit; a test asserts no unit conversion
   reaches storage. — **Storage met** (a GeoPackage round trip returns the adjusted gravity bit for bit, in
   m·s⁻²). **Display met** (P8b): `gravimeter.display_unit` chooses mGal or µGal for every table, CSV, layer
   and report, each naming its unit, and a tier-3 test runs the chain in both.
8. Every output carries an uncertainty and an `uncertainty_mode` (FR-703). — **Met**, including the
   solution's own mode, which no solution carried correctly before (§5).
