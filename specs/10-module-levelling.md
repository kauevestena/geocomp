# 10 — Module: Level

**Status:** Implemented (phase P4)
**Requirements covered:** FR-500…FR-505.
**Source:** tex §Painel de Configuração Global, item 2 (Nível); modificações.md.

Geometric (differential) levelling. Small module, high leverage: it reuses the adjustment core wholesale
([`06-adjustment-core.md`](./06-adjustment-core.md)) and delivers a complete second technique cheaply
(roadmap P4).

---

## 1. Menu structure

| Menu item | Requirement |
|---|---|
| Import levelling field book | FR-160 |
| Equal sights | FR-500 |
| Equidistant sights | FR-501 |
| Extreme sights | FR-502 |
| Closures and tolerances | FR-503 |
| Levelling network adjustment | FR-504 |

Six rather than the proposal's four. Import and closures were implicit in the other four and are separate
algorithms because each produces a document the next step reads (ADR-0005: one capability, one algorithm).

**Equal and extreme sights share an implementation and are still two entries.** They answer different
questions and produce different things: equal sights reduces a *line* to one height difference between two
marks, extreme sights reduces a *setup* to several that are correlated with each other — which is the whole
point of that scheme and is invisible in a line reduction.

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

**A line is reduced as a whole, not as a sum of setups**, and this is load-bearing. One instrument levels the
line, so there is one collimation error *c*, carried through a single shared column. Two things follow that a
per-setup treatment gets wrong. The value is corrected by `−c · (accumulated imbalance)`, so imbalances of
opposite sign cancel as they physically do. And the uncertainty contribution is
`(accumulated imbalance)² · var(c)`, which is **zero for a balanced line** — whatever *c* is and whatever its
own uncertainty. That is the mathematical statement of why equal sights is the preferred method: on a
balanced line the collimation need not even be known.

Summing independently reduced setups would instead give `Σ imbalance_i² · var(c)`, never zero unless every
setup was individually balanced. It is the same mistake, in the same shape, as giving the two sights of a
leap-frog pair independent refraction coefficients ([`09`](./09-module-total-station.md) §4.5).

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

**GeoComp ships no national tolerance table.** The permissible misclosure is `k·√L` everywhere, but *k*
differs by country, by class within a country, and by edition of the standard. A transcribed value that is
wrong does not fail loudly: it silently accepts a line that should have been re-run, or rejects one that was
fine, and the surveyor cannot see which. So a levelling class is a record the user fills in from the
specification in front of them, and it carries a `source` field naming that document. **With no *k*
configured there is no verdict** — the misclosure is reported and `passed` is neither true nor false but
absent. A check that reports success when it could not test anything is worse than one that admits it.

**And the distribution comes with a statement of what it cannot do.** Proportional distribution is the
classical correction and many specifications require it, so it is computed — but it *localises nothing*:
every setup receives its share whether or not it is where the error entered, so a blunder is smeared evenly
along the line and made harder to find. What localises an error is the network adjustment with data snooping
([`06`](./06-adjustment-core.md)). So the misclosure is also compared with **its own propagated standard
deviation**, and the result says which situation the user is in: consistent with accumulated random error, in
which case distribute it, or not, in which case spreading it evenly is the one response guaranteed to hide
it.

**The acknowledgement, in the network adjustment (P12a).** Until P12a the rule above was kept by the closures
algorithm, which checks what it is pointed at, and broken by *Levelling network adjustment*, which adjusted
whatever it was given — while `level.adjust_failing_lines`, the setting that was to be the acknowledgement,
was read by nothing. The adjustment now closes, before it adjusts, everything the network itself allows:

- **each line between two benchmarks** of the same height type, against the difference of their heights;
- **each section levelled more than once**, each later run against the first, oriented from the station ids.
  A section is judged on its **one-way** length — the shorter run's where the two differ — because a section
  tolerance is stated per section, and two runs over 2 km judged as a 4 km loop would loosen it by √2.

Loops are not searched for: a network's cycle basis is not unique, each would give different numbers for the
same observations, and the global test and data snooping see every loop at once. A named loop is the closures
algorithm's. With *k* configured (`level.tolerance_coefficient`, the run's *Tolerance coefficient*), a failing
closure **refuses the adjustment** by name unless *Adjust lines that failed their tolerance* is on — the
setting's default, or the run's — and an adjustment that proceeds on it says so in the log, lists the closures
in the report, and records which failed in the provenance. With no *k* nothing is judged, and the report says
that too.

---

## 4. Network adjustment (FR-504)

Height differences become `HEIGHT_DIFFERENCE` observations
([`04-data-model.md`](./04-data-model.md) §4) and are adjusted by the core as a 1D network.

**Weighting.** σ²_Δh ∝ L (line length) or ∝ n (number of setups), selectable, with the constant of
proportionality from the instrument and scheme (FR-064). The choice matters and is recorded in the result:
length weighting suits long lines with consistent sight lengths; setup weighting suits short, irregular
lines where the per-setup reading error dominates.

**Two figures compete, and neither wins silently.** A reduced line arrives carrying an uncertainty
propagated from its staff readings, which is rigorous and usually optimistic — it knows nothing of
refraction, staff calibration or a tripod settling. The `k·√L` and `k·√n` models are fitted to lines that
suffered all three. Both are offered; leaving the coefficients unset keeps the propagated figure, and the
result records which was used.

The weighting model lives in `core/adjustment/weighting.py` rather than in the levelling package, because a
gravity difference is the same observation equation (ADR-0002, Amendment 1) and would otherwise have it
written twice.

**Two ways to build the network, because there are two questions.** Lines become one observation each between
two permanent marks, and turning points do **not** appear: a turning point existed for four minutes, has no
mark, and adding it contributes one parameter and one observation — no redundancy, no effect, and a solution
cluttered with points that cannot be checked. Setups become their own observations when every foresighted
point is wanted, and that is the form in which an extreme-sights cluster reaches the adjustment.

Everything from [`06-adjustment-core.md`](./06-adjustment-core.md) applies: free and constrained networks
(a levelling net tied to one or several benchmarks), the global test, data snooping, reliability, and — the
1D analogue of error ellipses — per-benchmark height uncertainties and relative height uncertainties between
pairs.

Height differences from trigonometric levelling
([`09-module-total-station.md`](./09-module-total-station.md) §4.5) enter the same adjustment, with their own
(generally larger) uncertainties. Combining geometric and trigonometric levelling in one network is
supported and is a case where per-technique variance component scaling (FR-805) earns its place.

**As built (P12c).** Until P12c nothing read the document *Trigonometric levelling* writes, so the
combination worked in the core and not from the menu. *Levelling network* now does it:

- **The input.** It takes that document as *Trigonometric height differences* (optional).
- **The observations.** Each difference joins the lines as a `HEIGHT_DIFFERENCE` recording the technique
  `total_station` (`levelling.add_height_differences`), weighted by its own propagated uncertainty, since it
  has no line length or set-up count to be weighted by.
- **New points.** A point only the trigonometric differences reach is added as a mark.
- **Variance components.** *Estimate a variance component per technique* (advanced) runs P9a's estimation by
  technique. The run lists the factors, the solution's provenance keeps them, and the report has a table of
  them.
- **What is assumed.** The differences take the levelling's height type. Over the distances trigonometric
  levelling spans, the plumb line and the normal differ by far less than the differences' uncertainty.

---

## 5. Height systems

A levelling network produces height *differences*, which become heights only against a datum. GeoComp
records the height system of the benchmarks used (`height_type` in
[`04-data-model.md`](./04-data-model.md) §3) and refuses to mix orthometric and ellipsoidal heights without
a geoid model (FR-804, FR-802).

**With a model, the mixture is resolved rather than tolerated (P5).** `harmonise_benchmarks` converts every
benchmark to orthometric — the system the levelled differences already measure — propagates the model's
uncertainty into the converted height (FR-204), records the model on the station and on the solution
(FR-804), and reports each conversion as a finding carrying the undulation and the size of the change. P4
had to refuse this case for want of a grid; the refusal is now narrower and sharper: naming a model without
supplying its grid is still refused (`geoid_model_named_without_grid`), because a name records *which* model
was used and cannot compute an undulation, and a benchmark needing conversion without a latitude and
longitude is refused too (`benchmark_without_position`), because an undulation is a function of position.
See [`13-module-integration.md`](./13-module-integration.md) §3.1.

A benchmark converted through a geoid model should ordinarily be held **weighted**, not fixed: its height
now carries the model's uncertainty, and holding it exactly throws that away and forces the disagreement
into the observations. That works as of P5 — see [`06-adjustment-core.md`](./06-adjustment-core.md) §3 for
why it did not before.

Orthometric corrections (the non-parallelism of level surfaces) are applied for precise levelling over
significant height ranges, as an option with its magnitude reported so the user can see when it matters.

**What is implemented is the *normal* orthometric correction**, from the ellipsoid's gravity field:
`OC = −β · sin(2φ_m) · H_m · Δφ`, needing only latitude and height. At mean latitude 30°, mean height 1000 m,
over one degree of latitude it is 81 mm; at 100 m of height, 8 mm; over one minute of latitude at that
height, 0.12 mm. It matters for precise levelling that climbs, over long north–south lines, and is negligible
on a construction site — and the result says which.

**Applied by the network adjustment (P12a).** The function existed from P4 and nothing called it, while
`level.apply_orthometric_correction` was read by nothing. *Levelling network adjustment* now applies it to
every line before adjusting when the option is on, and reports each line's correction with the mean latitude
and height it came from. Latitudes come from a **point layer of station positions** and the field holding
each station's id, read through QGIS in the geographic CRS of the layer's own datum — an inverse projection,
never a datum transformation. Approximate heights are the benchmarks' carried along the lines. Three things
are refused rather than assumed: a station a line ends at with no position (all of them named), a positions
layer with no valid CRS, and a free network, whose heights hang from an arbitrary zero. The correction's
uncertainty, a tenth of the correction tagged as a dominant-term stand-in, reaches the corrected difference.

The **rigorous** orthometric correction needs observed gravity along the line, and is deliberately *not*
approximated here with an assumed field pretending to be a measured one. It arrives with the gravimetry
module (P8), which is where the gravity observations do.

**Every difference says what it is a difference of (P9b).** Both network builders tag each height difference
with its height type (`meta["height_type"]`, the benchmarks' — orthometric unless the levelling was reduced
otherwise). A single-technique adjustment never needed it; a geocentric combination does, because there a
levelled difference and an ellipsoidal one differ by the change in undulation, and the core refuses one that
does not say (`height_difference_type_unstated`). *Network adjustment* writes the network as built
(`OUTPUT_NETWORK`) for the Integration menu, benchmarks held in `up` alone as the lines held them. What a
geocentric combination makes of such a benchmark is in [`13`](./13-module-integration.md) §6.2.

---

## 6. Data import

Field-book layouts vary widely. The importer (FR-160) handles: one row per setup with backsight and
foresight readings; one row per reading with a setup identifier; and three-wire readings (upper, middle,
lower) from which the sight distance is derived by stadia and the mean reading is formed with its dispersion
as an empirical precision estimate.

Sight distances are imported where recorded, because §2.1's balance check depends on them.

**Which layout a file is in is worked out from the mapped columns, not asked for**: a mapping that declares
one layout while naming the other's columns produces wrong data quietly, so naming both is refused by name.

**The three-wire mean is propagated, not sampled.** The three wires read deliberately *different* heights, so
their sample spread is the stadia interval — centimetres — and using it as a precision would report a reading
good to half a millimetre as good to five. The empirical evidence in a three-wire set is the half-sum residual
`(u + l)/2 − m`, and one set carries a single degree of freedom; pooled over a line it becomes the only
precision figure in the module that can contradict the instrument profile.

**A sight distance may take its σ from the digits it was written to** — `32.4` lies in `[32.35, 32.45)`, so
σ = `0.05/√3` — recorded as `Strategy.RECORDED_PRECISION` ([`05`](./05-uncertainty-and-covariance.md) §2.3).
This is not a hole in *GeoComp does not invent a σ*: the digits are real information, present in the file. It
is permitted here because a sight distance's uncertainty reaches the answer only multiplied by a collimation
of order 10⁻⁴. **A staff reading, whose σ becomes an adjustment weight, still refuses.**

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
6. Mixing orthometric and ellipsoidal heights without a geoid model raises `ValidationError`; **with** one,
   the benchmarks are converted, the model's uncertainty reaches the adjusted heights, and the solution
   names the model.
7. Every output carries an uncertainty and an `uncertainty_mode` (FR-505).
8. *(P12a)* The network adjustment refuses a line between two benchmarks, or a double-run section, that failed
   its tolerance, unless the failure is acknowledged, and then records it; with positions it applies the normal
   orthometric correction and reports it, refusing a station without one
   (`tests/test_levelling.py`, `tests/qgis/test_levelling_algorithms.py`).
