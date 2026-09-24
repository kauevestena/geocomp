<!-- SPDX-License-Identifier: GPL-2.0-or-later -->
# 22 — Reference data sources

**Status:** Draft. §§2 and 4 are implemented (RD-11, RD-12); §5 has RD-06 data and an unmet accuracy check.
**Requirements covered:** FR-161, FR-952; the reference datasets RD-02…RD-08 of
[`20-testing-and-validation.md`](./20-testing-and-validation.md) §3.
**Source:** A search for reference data, prompted by three pieces of work stalling on the same shortage.

---

> **Verification note.** This document follows the convention of
> [`07-engine-dynadjust.md`](./07-engine-dynadjust.md). **[V]** means verified directly — the files were
> obtained and inspected. **[C]** means *claimed*: found through a search index whose summary could not be
> checked against the source, because this project's build environment blocks outbound HTTP to every host
> except a few. A **[C]** here is a lead for a contributor with an ordinary internet connection, not a fact.

## 1. Why this document exists

[`20-testing-and-validation.md`](./20-testing-and-validation.md) §3 lists the reference datasets. Two remain
*to assemble* (RD-07, RD-08); RD-06 now has repository fixtures but no passing accuracy check (§5).
RD-02, RD-03 and RD-04 carry a standing note that their
**validation is complete but their citation is not**: they are reference cases built from the operations
GeoComp performs, not transcriptions of published worked examples, so the project cannot yet say it agrees
with the standard references *by name*.

Three separate pieces of work have now stalled on the same thing:

* ~~**FR-161**, the *Adjust* (Ghilani) format, has been re-planned twice — out of P5 and then out of P6 — for
  want of one example file with a published answer.~~ **Resolved** — §4. It took a third re-planning and a
  public dataset of five networks published in the format.
* **P6's cross-validation** exit criterion asks for three networks and has one, because the other two need
  observation types and coordinate frames that DynAdjust cannot take from GeoComp
  ([`07`](./07-engine-dynadjust.md) §4.4, §4.2).
* **The commercial-comparison protocol** ([`20`](./20-testing-and-validation.md) §5) and the teaching
  material (FR-952) both want agreement with named references.

## 2. GNU Gama and the Krumm examples — 45 networks with published answers **[V]**

**This is the find that matters.** [GNU Gama](https://www.gnu.org/software/gama/) is the GNU project's
geodetic network adjustment package, GPL-3.0, mature and maintained. Its source tree carries, in
`tests/krumm/input/`, the example networks of:

> Friedhelm Krumm, *Geodetic Network Adjustment Examples*, Geodätisches Institut, Universität Stuttgart,
> Rev. 3.5, 20 January 2020.

Verified by cloning `Geo-Linux-Calculations/gnu-gama` at `963c309` (v2.24) and reading the files:

| | inputs (`.dat`) | **with published adjusted coordinates** (`.adj`) |
|---|---|---|
| 1D | 14 | 6 |
| 2D | 39 | 32 |
| 3D | 8 | 7 |
| **total** | **61** | **45** |

The `.adj` files are not GNU Gama's own output. Its README states they hold *"adjusted coordinates, as
published by Friedhelm Krumm"*, and its test harness (`tests/krumm/cmp_xml_file.cpp`) adjusts each network
and compares the result against them. That is an **independent** reference, which is the property that makes
it worth having — a self-check against one's own previous output proves nothing.

**The observation types are the ones GeoComp implements**, counted across the 61 files: `Distances` (24),
`Directions` (16), `LevelledHeightDifferences` (14), `SpatialDistances` (7), `TrigonometricHeightDifferences`
(6), `HorizontalDistances` (4), `Angles` (4), `ZenithAngles` (2), `VerticalAngles` (2), plus
`ApproximateOrientation`, `ApproximateScale` and `Restrictions`.

Note `HorizontalDistances`. That is GeoComp's `HORIZONTAL_DISTANCE`, the type that has **no DynAdjust
equivalent** ([`07`](./07-engine-dynadjust.md) §4.2) and therefore cannot be cross-validated against it at
all. GNU Gama adjusts it natively, in the same local plane frame GeoComp's core works in — so it needs none
of the geodetic reductions that block the DynAdjust route.

### 2.1 The sources these examples come from **[V]**

Each `.dat` carries a `[Source]` section citing the textbook it is taken from, by edition and page:

| Source | examples | notes |
|---|---|---|
| Lother & Strehle (2007) | 13 | |
| Benning (2011) | 5 | *Statistik in Geodäsie, Geoinformation und Bauwesen* |
| **Ghilani (2010)** | **4** | *Adjustment Computations*, 5th ed. — **the reference RD-02/03/04 want to cite** |
| Wolf (1979) | 6 | |
| Leick (1995) | 4 | *GPS Satellite Surveying* |
| Niemeier (2008) | 3 | *Ausgleichungsrechnung* |
| Strang & Borre (1997) | 2 | *Linear Algebra, Geodesy, and GPS* |
| Mittermayer (1971), Höpke (1980), Baumann (1995) | 2 each | |
| Caspary (2013), Carosio (1983), Grossmann (1969), Jäger et al. (2005), Weiss et al. (2010), Blankenbach & Willert (2009) | 1 each | |

The Ghilani files are named by chapter and example — `Ghilani12_6_Height_fix`, `Ghilani14_5_Distance_fix`,
`Ghilani15_4_Angle_fix`, `Ghilani15_5_Angle_fix` — and cite pages. `Ghilani14_5` is a fixed trilateration
network, which is the same *kind* of network as RD-03's, from the book RD-03's note names.

### 2.2 The reader, and what it reproduces **[V]**

`geocomp/io/krumm.py` reads the format; `tests/test_krumm_corpus.py` runs every one of the 61 files.
**34 networks reproduce their published coordinates**, the largest disagreement over all of them being
**0.05 mm** — which is the rounding of a value printed to four decimals, not a residual difference.

| | files | reproduced | refused, by name | read, no comparable answer |
|---|---|---|---|---|
| 1D | 14 | 5 | 3 | 6 |
| 2D | 39 | 24 | 11 | 4 |
| 3D | 8 | 5 | 3 | 0 |
| **total** | **61** | **34** | **17** | **10** |

Of the 45 files carrying a published answer: **34** are reproduced, 9 belong to files GeoComp refuses, and 2
cannot be compared — `Hoepke_Distance_fix.adj` is gama-local XML rather than the printed table, and
`Ghilani21_1_DistanceAngle_fix.adj` has its station names truncated in the corpus (`102`, `103`, `201`,
`202`, `203` printed as `10`, `01`, `20`, `02`, `03`).

Every refusal is stated by error code, and every one is a thing GeoComp cannot yet represent rather than a
thing it reads badly: a **dynamic (weighted) datum** (5 files), an **azimuth to a point with no
coordinates** combined with an angle turned from it (3 — GNU Gama excludes the same three, for the same
reason), an **ellipsoidal network** (4), **conditions between parameters** (2), a **GNSS baseline** with a
covariance this format states differently (2), **correlated distances** (1), and **position angles** (1 — GNU
Gama's converter leaves them out too).

`Baumann23_3_4_fix` used to be a tenth refusal: a **slope distance measured instrument-to-reflector**, whose
two setup heights belonged in the observation equation and had nowhere to live on `Observation`. They live
there now ([`09`](./09-module-total-station.md) §2.5) and it reproduces to **0.03 mm** — which is a fifth of
the published rounding, so the heights are being applied the way Baumann applied them and not merely applied.

Four defects were found by running the corpus, each of which produced a plausible wrong answer rather than
an error:

1. **A direction with no setup id** is read as an absolute azimuth. Three direction networks were out by up
   to 2 km before the reader started setting `Observation.setup_id`.
2. **A levelling sigma is per kilometre.** Reading the stated value as the line's own standard deviation
   weights a 1.2 km line and a 0.44 km line alike; `Niemeier_Height_fix1` was out by 1.9 mm.
3. **The names after `free` are the datum stations.** `LotherStrehle_Direction4` is `Direction3` with one
   station left out of the inner constraint, and the published answers differ by 3.6 mm.
4. **`VERTICAL_ANGLE` had no observation equation** in the adjustment core at all — an unrelated gap the
   corpus surfaced, now closed and covered by `specs/06` §7 criterion 1.
5. **Setup heights had nowhere to live**, so a sight measured from the instrument could not be adjusted at
   all. The refusal was correct — applying the reduction in the reader is wrong by however wrong the
   approximate coordinates are — but the fix belonged in the observation equation, and that is where it went.

What this buys:

* RD-03's citation gap closes **by name and page**, for the book the note names.
* The cross-validation gets its second and third networks — and thirty more — without needing the geodetic
  reductions GeoComp lacks.
* A plane trilateration and a levelling network are finally adjusted by something other than GeoComp.
* GNU Gama becomes a **third** independent implementation, in the frame the core natively uses.

### 2.3 The corpus is vendored, and on what terms

`tests/data/krumm/` holds all 107 files, copied verbatim from GNU Gama at commit
`963c3099054594922716786f92119732f12d714e`. The reference tests are therefore part of the ordinary suite —
they run on every commit, on every platform, with no network and nothing to opt into. `GEOCOMP_KRUMM_DIR`
still overrides the path, which is what you want when checking the reader against a different revision of
the corpus.

**Licensing.** The files are distributed inside GNU Gama under GPL-3.0. GeoComp is GPL-2.0-*or-later*, so it
may be combined with GPL-3.0 material; the combined portion is then effectively GPL-3.0, which is worth
stating explicitly rather than discovering at release. Attribution to Krumm and to GNU Gama is in
`THIRD_PARTY.md`, on the same terms as the DynAdjust sample data already there. The underlying numbers are
worked examples from textbooks; GNU Gama redistributes them with attribution and a documented changelog of
its edits, which is the model followed here.

Three things hold that position up, and each is checked rather than promised:

* **The copy is verbatim.** `scripts/check_krumm_corpus.py` compares every file against a fresh clone of the
  pinned commit; the `reference` workflow runs it on any change to the directory and monthly. An attribution
  to a source you have quietly edited is not an attribution.
* **It is test data.** It lives under `tests/`, and `scripts/build.py` packages `geocomp/` alone, so nothing
  here reaches an installed plugin. `tests/test_krumm_corpus.py::TestTheCorpusIsTestDataOnly` asserts both
  halves — no corpus file in the package, no plugin module reading the directory. The ZIP is the artefact
  users actually receive, and putting this data in it would be a different question from the one settled
  here.
* **The chain is written down.** `tests/data/krumm/PROVENANCE.md` names the upstream, the commit, the
  document, and the textbooks behind it; GNU Gama's own `README.md` sits beside it unchanged, including its
  changelog of the edits Gama made to Krumm's originals.

## 3. JAG3D, and how adjustment software gets certified **[C]**

[JAG3D](https://github.com/applied-geodesy/jag3d) (*Java·Applied·Geodesy·3D*, GPL-3.0) combines levelling,
directions, distances, vertical angles **and GNSS baselines** in one rigorous model — which is GeoComp's own
shape, and a closer match than DynAdjust for a mixed terrestrial network.

More interesting than the software is its **quality-assurance practice**, which is a direct answer to the
question this project keeps running into — *how do you validate an adjustment implementation?*

* Its `JUniForm` module passed **TraCIM** verification. TraCIM (*Traceability for Computationally-Intensive
  Metrology*) is a PTB service certifying metrological adjustment algorithms under ISO 10360-6: synthetic
  datasets with modelled random and systematic deviations are supplied, the results returned, and a test
  report issued. Reported maximum deviations were < 0.1 µm and < 0.1 µrad.
* Round-robin comparisons are published with raw data and results at `comet.esgt.cnam.fr/comparisons`.
* Lösler et al. (2023), *Operator-software impact in local tie networks*,
  [doi:10.1007/s12518-022-00477-5](https://doi.org/10.1007/s12518-022-00477-5) — measures how much the
  **operator and the software** change the answer for one dataset. Directly relevant to
  [`20`](./20-testing-and-validation.md) §5's commercial-comparison protocol.
* Lösler (2023), compatibility-evaluation dataset,
  [doi:10.5281/zenodo.7468733](https://doi.org/10.5281/zenodo.7468733).
* Heißelmann & Franke (2023), TraCIM verification,
  [doi:10.5281/zenodo.8217114](https://doi.org/10.5281/zenodo.8217114).

The round-robin idea is worth borrowing whatever else is done: *the same data, several implementations, the
spread reported.* It is a stronger statement than "matches the book" and it is what §5 is reaching for.

## 4. RD-12 — the *Adjust*-format corpus that closed FR-161 **[V]**

FR-161 was re-planned out of three phases for want of one thing: an example file in the *Adjust* format. It
is met now, and what met it was a public dataset rather than the lead §4 used to record.

| | |
|---|---|
| **Source** | <https://data.mendeley.com/datasets/rr8js427vt/1> (`doi:10.17632/rr8js427vt.1`) |
| **Licence** | **CC BY 4.0** |
| **Content** | ten `.Adat` files — five networks, each published with and without its observed values |
| **Accompanies** | a doctoral thesis on network establishment methods |

The dataset is the **same ground surveyed three ways** over one set of four control stations: twelve free
stations, three traverses, and a conventional triangulateration. That is what makes it worth having — the
comparison is the data, not any single network.

`tests/data/adjust/PROVENANCE.md` records the chain and the numbers; this section records what the corpus
established.

### 4.1 The grammar, and how far it can be trusted

There is no published specification, so the reader is written against the examples. Two properties bound
that inference, and both are checkable:

* **The format declares its own observation counts.** A misparse produces a count that disagrees rather than
  a network that looks fine, and `read_adjust` refuses on the disagreement by default.
* **The two conventions that can be silently wrong were settled numerically.** Reading the coordinate pair
  as *x = easting, y = northing* and each angle as *clockwise from backsight to foresight*, the angles the
  files state agree with those their own approximate coordinates imply to a **median of 0.000°** over 143
  angles. Neither convention has a plausible alternative at that level of agreement.

[`17-persistence-and-interoperability.md`](./17-persistence-and-interoperability.md) §5.2 has the layout and
the four rules the reader follows.

### 4.2 Two defects in the publication, both recorded rather than repaired

A reference dataset whose defects are undocumented is a trap, so both are pinned by tests.

**`MMEL dados.Adat` miscounts its own angles.** The header declares 51 distances and 51 angles; the file
holds 51 and **52**. Against its valueless half, which declares 52 of each and holds them, one distance
(`EL10 16`) was removed and *both* counts were decremented. The rows are the data and the header is a
summary; the summary is wrong by one.

**The round of six angles at station 9 of the triangulateration is cyclically rotated.** Each row carries the
value belonging to the *next* row in the round:

| row | value in the file | implied by the file's own coordinates |
|---|---|---|
| `D 9 4` | 71.158° | 32.293° |
| `4 9 8` | 62.061° | 71.158° |
| `8 9 14` | 67.185° | 62.061° |
| `14 9 16` | 34.178° | 67.185° |
| `16 9 C` | 93.302° | 34.167° |
| `C 9 D` | 32.117° | 93.136° |

Each matches the next row's computed angle to 0.18°, while the other 63 angles in the file agree to a median
of 0.0001°. **A closure check cannot see it**: the round still sums to 360.00028°, because rotating a closed
round leaves its sum unchanged. Only the least-squares residuals find it — σ̂₀² of 8.6 × 10⁶ against 61.5
once the values are rotated back.

The file is vendored **twice**: faithfully, as the reference case for blunder detection, and corrected, for
validating the adjustment. The faithful copy teaches something a synthetic blunder cannot — least squares
**smears** a blunder this large, and the largest residual in the network belongs to an observation that is
not one of the six wrong ones. Ranking by residual would accuse the innocent.

### 4.3 What GeoComp measures, and what it does not claim

Adjusted as plane networks with the control weighted as published:

| Network | dof | σ̂₀² | worst standardised residual |
|---|---|---|---|
| free stations (12) | 47 | **0.0028** | 0.09 |
| traverse A→C | 3 | 845 | 19.7 |
| traverse A→D | 3 | 1195 | 15.3 |
| traverse B→C | 3 | 482 | 12.1 |
| triangulateration, as published | 77 | **8.6 × 10⁶** | 12040 |
| triangulateration, corrected | 77 | 61.5 | 8.3 |

**The traverses have no redundancy of their own.** Freed of their control they adjust with *negative* degrees
of freedom — thirteen observations against fourteen estimable parameters. All three of their degrees of
freedom come from the weighted control, so their σ̂₀² measures how far each traverse misses that control, not
how well its own observations agree. Reading 845 as "these angles disagree with each other" is the obvious
mistake and it is wrong.

**No published answer accompanies the data.** These five networks validate the reader, the writer and the
weighted-constraint path; they are not a check of GeoComp's adjustment against an independent one, which is
what RD-11 provides. Correcting the rotated round does not make the triangulateration fit its stated sigmas
either — σ̂₀² is 61.5 — and whether that is optimistic sigmas or something else in the data, this repository
does not claim to know.

### 4.4 What the repository carries

The **data** is CC BY 4.0 and redistributable. The **format** is Ghilani's, and this repository does not
carry files in it: the five networks are vendored as `Network.to_dict()` JSON, produced by
`scripts/convert_adjust_corpus.py`. Interoperability is still implemented and still tested — by round trip,
and against the originals for anyone who sets `GEOCOMP_ADJUST_DIR`.

## 5. RD-06 — data obtained, accuracy unmet **[V]**; RD-07 and RD-08 still to assemble **[C]**

**RD-06 update, 17 September 2026.** The earlier archive-access blocker does not recur in the validation
environment. The reproducible evidence bundle, integrated into `tests/data/rd06/`, contains two complete
days (2025-001 and 2025-002) for the NASA Goddard stations **GODN, GODE and GODS**, from the
[official NOAA archive](https://geodesy.noaa.gov/CORS/data.shtml). The independent expected results come
from the **ITRF2020, epoch 2020.0, ARP** blocks of NGS's coordinate sheets for
[GODN](https://noaa-cors-pds.s3.amazonaws.com/coord/coord_20/godn_20.coord.txt),
[GODE](https://noaa-cors-pds.s3.amazonaws.com/coord/coord_20/gode_20.coord.txt) and
[GODS](https://noaa-cors-pds.s3.amazonaws.com/coord/coord_20/gods_20.coord.txt), not from RINEX
approximate positions or an earlier RTKLIB result. All three stations carry **identical published
velocities**, so the five-year propagation to the observation epoch contributes exactly nothing to either
baseline and cannot be a source of error in it.

The frozen data records the sources, redistribution terms, hashes, complete observations, navigation,
station logs, NGS IGS20 antenna calibration and IGS final orbit. `scripts/check_rd06.py` and
`tests/test_rd06.py` process the **current working tree**, retaining configurations, outputs and metrics.
[`PROVENANCE.md`](../tests/data/rd06/PROVENANCE.md) documents the complete reproduction and reuse terms.
Everything except `ngs20.atx` is served by `noaa-cors-pds.s3.amazonaws.com`, which is reachable from the
development environment and serves bytes identical to `geodesy.noaa.gov`'s, checked by hash.

### 5.1 The discrepancy, attributed [V]

**Superseded reading.** Until 23 September 2026 this section attributed the discrepancy to two things: "a
low-elevation error of up to 11 mm in east" and "a stable ~6.9 mm underneath it". The elevation-mask sweep
that produced that reading is sound and its numbers stand, but **the first half of the conclusion drawn
from it was wrong**, and the second half was attributed to the reference without naming a mechanism. Both
are corrected below. The sweep could not distinguish "raising the mask removes low-elevation multipath"
from "raising the mask removes the one satellite that caused a bad ambiguity fix in one hour"; splitting
the days into sub-sessions can, and does.

#### The east term is one bad hour, not a gradient

`scripts/check_rd06.py --repeatability` solves each day whole and in halves, quarters and hours — 62
solutions per baseline. It exists because **GPS geometry repeats every sidereal day**, so two consecutive
days see nearly the same sky and any geometry-driven error repeats with them: their agreement bounds the
day-to-day *change* in that error, not the error. Sub-daily solutions break the repetition.

They show that on 2025-001 a single hour, **11:00–12:00 GPST**, fails ambiguity resolution outright, and
that the 24-hour static filter carries its wrong fix to the end of the day:

| Solution (GODN–GODS, mask 15°, uncalibrated) | E mm | N mm | U mm | ratio | status |
|---|---|---|---|---|---|
| 2025-001, 11:00–12:00 (1 h) | +871.8 | +452.7 | −569.2 | **1.0** | FLOAT |
| 2025-001, 06:00–12:00 (6 h) | +88.6 | +12.5 | −16.2 | **1.6** | FLOAT |
| 2025-001, 00:00–12:00 (12 h) | +22.1 | −1.5 | +0.1 | **2.1** | FLOAT |
| 2025-001, 12:00–24:00 (12 h) | +1.6 | −6.4 | +3.2 | 102.8 | FIXED |
| 2025-001, whole day | **+6.3** | −4.3 | +1.5 | 11.6 | FIXED |
| 2025-002, whole day | +0.8 | −6.5 | +2.5 | 120.1 | FIXED |

Excluding that hour, day 001 gives **E +1.58 (00:00–11:00) and +1.55 (12:00–24:00)** — the same answer as
day 002 and as the ≥25° mask sweep. **The "11.4 mm spread in east" is that hour, and the high mask removed
it by dropping the satellite that caused it.** Raising the mask is therefore not the fix; detecting the
interval is.

**The engine's own covariance does not see any of this.** The 22 mm solution reports a **1.08 mm** formal
3D standard deviation, and the 872 mm one reports 7.6 mm. A wrong integer fix is not a large residual — it
is a different answer, held confidently. The **ambiguity validation ratio is the only indicator that
moves**, and this is why `Baseline` carries it (FR-603) and why `PosSolution.fixed_fraction` alone is not
enough: the 89 mm solution has a fixed fraction of 0.936, which looks ordinary.

#### The north term is the reference, and the mechanism is an antenna change

Of the 62 GODN–GODS solutions, the **56 that are ambiguity-fixed with a validation ratio ≥ 20** give:

| | E mm | N mm | U mm |
|---|---|---|---|
| mean error | +1.35 | **−6.37** | +1.87 |
| standard deviation | 0.38 | 0.54 | 1.47 |

The scatter barely improves with session length — the robust scaling exponent is ≈ 0 where averaging white
noise would give 0.5 — so **a one-hour baseline over 76 m is as repeatable as a twenty-four-hour one**, and
the −6.4 mm north is a floor, not noise. It is 12σ. No processing choice removes it: not the mask from 25°
to 35°, not two independent days, not the NGS absolute calibration of both antennas, not IGS20 final orbits
and clocks, not reversing base and rover.

**GODS's antenna changed on 2020-09-03** — eight months *after* the 2020.0 epoch of the coordinate it is
compared against, and inside the data span (through GPS week 2295) the coordinate was computed from. NGS's
own [MYCS3 page](https://geodesy.noaa.gov/CORS/news/mycs3/mycs3.shtml) states that *"antenna changes cause
noticeable jumps in the coordinate time series creating discontinuities ranging from a few mm to several
centimeters."* So the published position describes an instrument these observations are not of.

Two further facts from the published sheets alone, with nothing assumed:

- **GODS's sheet contradicts itself by 1.97 mm in east.** Each sheet publishes the same monument twice, at
  the ARP and at the L1 phase centre. An L1 offset is vertical by construction: two verticals 76 m apart
  diverge by 1.2e-5 radians, so 85 mm of offset projects to under a micrometre sideways. GODN's two
  positions differ horizontally by **0.21 mm**; GODS's by **1.99 mm**. It is a *lower* bound — an error
  common to both of a station's coordinates cancels in this difference — and it is the only bound on the
  reference's uncertainty available, because the sheets print no covariance at all.
- **It is not the reference point convention.** Comparing the solution against the published L1PC baseline
  instead of the ARP one is worse, 6.8 mm against 1.8 mm on the best day. ARP is right.

#### The controlled experiment

The reading above is testable rather than arguable, and `tests/test_rd06.py` tests it. **One base, two
rovers, one day, one configuration.** GODE sits 65.163 m from GODN; its antenna was installed 2013-01-30
and has never been removed, so its published coordinate and these observations describe the same
instrument. GODS sits 76.018 m away and changed antenna after its coordinate's epoch. Only one of them
should be several millimetres out in north:

| Day (mask 15°, uncalibrated) | GODN→GODE N mm | GODN→GODS N mm | GODE 3D mm | GODS 3D mm |
|---|---|---|---|---|
| 2025-001 | +2.48 | −4.28 | 5.76 | 7.75 |
| 2025-002 | **+0.65** | **−6.53** | **2.02** | 7.04 |
| 2025-003 | +3.09 | −4.08 | 6.91 | 7.75 |
| 2025-004 | +1.09 | −6.67 | 2.20 | 7.14 |

GODS is 4 to 6.7 mm out in north on **every** day; GODE never is. Days 001 and 003 are the days whose
validation ratios are low (7.9 and 20.2 against 97.2 and 1.7/FLOAT), consistent with the contaminated
interval above. **The station whose reference describes a different antenna is the station that misses its
published baseline.**

`scripts/check_rd06.py` now **refuses** a comparison against a station whose current antenna postdates its
coordinate epoch, checked offline on every commit from the vendored site log. GODS is retained and
explicitly exempted as the counter-case, and the guard verifies that the exemption is still earned, so it
cannot outlive the defect it was written for.

### 5.2 The accuracy criterion, and why a threshold was not derived [V]

**The criterion remains unmet, and as of 23 September 2026 the judged case is also *unjudgeable*.**
Engine CI produced a calibrated GODN–GODE result and the check added alongside it reported why the
number cannot be used: **`ngs20.atx` has no entry for GODE's `AOAD/M_T JPLA`**, so `searchpcv` matched
`AOAD/M_T        NONE` — the same antenna under a different dome. NGS states its calibrations are keyed
by *antenna code plus radome code* and are used in all its products, including the solution this
comparison is against, so the substitution is a confound rather than a formality.

**The numbers it produced are therefore withdrawn as evidence of accuracy**, and recorded only as what
they are — a run whose rover carried another dome's pattern:

| GODN→GODE, day 002, `AOAD/M_T NONE` substituted | E mm | N mm | U mm |
|---|---|---|---|
| calibrated (substituted dome) | +0.68 | +0.09 | **−6.47** |
| uncalibrated | −0.17 | +0.65 | −1.91 |

The horizontal is sub-millimetre either way, which is what makes the vertical worth chasing rather than
accepting: the substitution *moved* it by 4.6 mm, which is the size of a dome. **Whether GODE's true
calibration would leave a vertical residual at all is unknown**, and the specification says so rather
than reporting −6.47 mm as the answer.

**What this does not touch.** The counter-case resolved **exactly** in the same run
(`JAVRINGANT_DM   SCIS` and `TPSCR.G3        SCIS`), so every GODS number section 5.1 rests on is a
genuinely calibrated number, and the attribution there stands. A dome substitution is vertical; the
term it attributes is north.

**Two independent defects, one site.** GODS's published coordinate describes an antenna it no longer
carries; GODE's antenna carries a dome nobody publishes a calibration for. Neither is a clean accuracy
case and they fail for unrelated reasons — which is why the pair remains the right controlled
experiment and neither is the right *reference*.

**And the obvious escape does not work.** The natural objection is to leave the site for a longer
same-antenna pair, and section 5.2 already recorded that every such pair beyond 4 km errs by 13 to
47 mm. That measurement used the broadcast ionosphere model, which is the wrong choice over kilometres,
so the ionosphere-free combination was tried on P281–P282 (4.014 km, `TRM29659.00 SCIT` at both ends,
both installed in 2004):

| 2025-002, P281→P282 | E mm | N mm | U mm | fixed | ratio |
|---|---|---|---|---|---|
| broadcast ionosphere | −4.39 | +4.94 | −11.76 | 0.999 | 34.3 |
| ionosphere-free L1/L2 | **+0.15** | **+0.50** | **−14.67** | **0.000** | **1.0** |

It fixes the horizontal, as expected — the horizontal error at 4 km *was* the ionosphere. But the
ionosphere-free combination has no integer wavelength, so `rnx2rtkp` resolves no ambiguities in this
mode at all: every run comes back FLOAT at a ratio of about 1, and the height degrades with it. A
kilometres-long baseline would need wide-lane/narrow-lane resolution, which this engine does not do
here. **The short baseline is not a convenience; it is what makes the comparison possible with this
engine**, and that is why the answer is a better pair of stations at a short baseline rather than a
longer one. Closing the criterion needs a station whose antenna
**and radome** are both in the calibration set, and the site-log screen of section 5.2 cannot test that
from the development environment: `geodesy.noaa.gov`, which serves `ngs20.atx`, answers 403 to CONNECT,
as do `files.igs.org`, `igs.bkg.bund.de`, `cddis.nasa.gov` and `geoftp.ibge.gov.br`, all re-checked on
23 September 2026. The membership test belongs in engine CI, where the file exists.

**Correction: "the shortest clean baseline in the network" was a property of the day, not the
network.** That screen fixed the observation day at 2025 day 001 and asked which stations had carried
one antenna since the 2020.0 coordinate epoch. The observation day is a free parameter, and nobody had
varied it. Re-run against a day beside the epoch, the same screen gives a different answer:

| Day screened | Stations with data | One antenna spanning 2020.0 → that day | Same-antenna pairs within 5 km |
|---|---|---|---|
| 2025-01-01 | 1723 | 794 | **1** — P281–P282 at 4.014 km, the pair already ruled out above |
| 2020-01-15 | 1698 | 1685 | **17**, of which 15 are shorter than 46 m |

The fifteen short ones are `TRM41249USCG SCIT` at both ends, 22 to 46 m apart — the same geometry that
makes GGAO workable, with the same antenna on both monuments instead of two different ones. So the
earlier conclusion held for the days that were processed and did not hold for the network. Reading a
station against a day adjacent to its coordinate epoch is also the weaker claim in its own right: it
extrapolates the published velocity by weeks rather than by five years.

`scripts/screen_cors_pairs.py` is that screen, so the table above is reproducible rather than
remembered, and `antennas_spanning` in `scripts/check_rd06.py` is the query under it — tested offline
against the three vendored logs, including the boundary that GODS's antenna came off on 2020-09-02 and
its replacement went on the 3rd. GODS is unjudgeable **against a 2025 day**; against 2020-06-01 the
instrument its published coordinate describes was still on the monument.

**This does not by itself close the criterion, and two things are still unknown.** Whether
`TRM41249USCG SCIT` is in the pinned `ngs20.atx` cannot be tested here — the file is 403 from the
development environment, and the ANTEX used for the table above could not be authenticated, so its
membership column is excluded from the claim. And a pair that is *judgeable* may still miss by more
than a millimetre; making the comparison decidable and passing it are different results.

**A GNSS numerical threshold was derived and then deliberately not adopted**, at the maintainer's
decision of 23 September 2026. The derivation is recorded because its outcome is the point: the
estimator's measured repeatability is 0.38 / 0.54 / 1.47 mm per component, so a threshold derived from
*this side* of the comparison is about 1 mm horizontally — **the number already in use**. The borrowed
printed-precision rule was the right order of magnitude for the wrong reason, and tightening or
loosening it settles nothing, because the quantities that would decide the comparison are the
reference's own uncertainty, which the sheets do not publish, and a calibration that matches the
station, which this pair does not have. [`20`](./20-testing-and-validation.md) §6 therefore still
defines no GNSS threshold, and the accuracy check stays red.

### 5.3 What the check enforces [V]

Only the primary accuracy assertion is a strict, exception-specific expected failure during local
development. CI runs it with `--runxfail`, so **the engine accuracy check stays red** while this criterion
is unmet. Source integrity, the antenna-epoch guard, the phase-centre self-consistency measurement,
processing, complete-day coverage and reproducibility must pass normally; missing engine or decompression
prerequisites fail in CI. The standalone checker exits 1 on the discrepancy.

**Repository delivery.** Coordinate sheets, station logs, policy snapshots and a losslessly compressed
primary output are vendored. Larger processing inputs are obtained explicitly with
`python3 scripts/check_rd06.py --fetch-inputs --verify-inputs`; original source hashes are enforced before
use. Engine CI performs this acquisition before testing, while ordinary offline checks need no download.
Changed upstream files are refused.

The following records the original source search and environmental blocker, retained as history.

**RD-06, GNSS with published official coordinates.** [IBGE's RBMC](https://www.ibge.gov.br/geociencias/informacoes-sobre-posicionamento-geodesico/rede-geodesica/16258-rede-brasileira-de-monitoramento-continuo-dos-sistemas-gnss-rbmc.html)
(*Rede Brasileira de Monitoramento Contínuo*) publishes RINEX for every station together with official
SIRGAS2000 coordinates; station reports come from the Banco de Dados Geodésicos at `bdg.ibge.gov.br`. RINEX 3
at 1 s has been available since 2020. This is the natural choice for a Brazilian project: the coordinates are
official, the frame is the national one, and the data is public. NGS/CORS and Geoscience Australia are the
equivalents elsewhere. Licence terms were not checked.

> **P7 could not obtain it, and the reason is not upstream's.** Every candidate archive is **denied by the
> egress policy of the environment GeoComp is developed in** — `geoftp.ibge.gov.br`, `cddis.nasa.gov`,
> `igs.bkg.bund.de` and `files.igs.org` all answer 403 to CONNECT. That is an organisation policy, not a
> service outage and not a missing dataset: the data is public and reachable from an ordinary network.
>
> So RD-06 is **blocked rather than absent**, and P7's exit criterion that a static relative session
> reproduces published coordinates is recorded **unmet** rather than quietly reinterpreted. What would
> unblock it, in order of preference:
>
> 1. **A maintainer-supplied dataset** — RINEX for a station whose official coordinates are published, the
>    way the *Adjust* corpus unblocked FR-161. One station over one day is enough.
> 2. Egress for one of the four hosts above.
> 3. A CI job that runs where those hosts are reachable, fetching at test time rather than vendoring.
>
> **What P7 validated instead, and what that is worth.** RTKLIB's own sample pair — two Japanese GSI marks
> observing the same hour of 2 April 2005 — runs the whole chain and resolves its ambiguities
> (`tests/data/rtklib/`). That shows the pipeline works: RINEX read, sessions paired, configuration written,
> engine run, covariance recovered. It shows **nothing about accuracy**, because those stations have no
> published coordinates reachable here. The distinction is the same one §2.2 draws for RD-11 against RD-03:
> a reference case built from the operations a program performs is not a transcription of a published answer,
> and only the second can settle whether the program is right.

**RD-07, a gravimetric network with a published solution.**
[IBGE's Rede Gravimétrica](https://www.ibge.gov.br/geociencias/informacoes-sobre-posicionamento-geodesico/rede-geodesica/16286-rede-gravimetrica.html),
and **RENEGA**, the national absolute-gravity network (stations at Brasília, Valinhos, Curitiba, Lages, Santa
Maria, Monte Carmelo). Absolute stations are the useful ones: their values are published with uncertainties
and are the fixed points a relative network is adjusted onto. Note that ADR-0002 makes gravimetry the case
with *no* external engine, so a published solution is the only independent check available.

**RD-08, multi-epoch monitoring with known displacements.** No single canonical benchmark surfaced. The
literature instead converges on a set of named methods against which an implementation is compared —
Pelzer/Hannover, Karlsruhe, Delft, Fredericton, München, and robust variants — with the global congruency
test of Pelzer (1971), Niemeier (1981) and Caspary (2000) as the common core. A useful entry point is *Deformation
analysis: the Caspary approach*, Geodetski vestnik 64(1), 2020, which works one dam network of 12 points
through the Caspary method and reports agreement with the other named methods; JAG3D implements one of them.
Synthetic data with injected motion (already RD-08's second half) remains the only source of exact truth.

### 5.4 What a clean pair does — the criterion is unreachable against this reference [V]

**The maintainer supplied `igs20.atx` on 24 September 2026**, which is the one thing this environment
could not fetch, and it settles the question §5.2 left open. Two facts came out of it at once:
`AOAD/M_T JPLA` is **absent from `igs20.atx` as well**, so GODE's radome is uncalibrated in both
calibration sets and its unjudgeability is confirmed rather than an artefact of one file; and
`TRM41249USCG SCIT` **is** present, so the fifteen candidate pairs of §5.2 are exactly calibrated and
the comparison finally becomes decidable.

`scripts/check_published_coordinates.py` then asks the question the other way round — not *"is this
pair clean?"* but *"what does a clean pair do?"*. Every eligible pair is processed and every result
reported; nothing is selected after solving. KEN5/KEN6 drops out because KEN6 publishes no ITRF2020
sheet, leaving **fourteen** pairs of 22 to 46 m, each solved on three consecutive days under RD-06's
own configuration.

**Not one of the fourteen reaches 1 mm per component.** The median worst component is 5.1 mm, the best
pair is 1.9 mm and the worst 18.0 mm; in 3D the errors run from 2.8 to 22.2 mm. Every run resolved
both antennas exactly, fixed its ambiguities, and covered a near-complete day.

The miss belongs to the reference, not to the estimator, and three independent discriminators say so:

| Discriminator | Measured | What it rules out |
|---|---|---|
| Same pair, three days | scatter **0.43 / 0.43 / 0.25 mm** E/N/U | random solution error |
| Between pairs | spread **2.66 / 6.64 / 6.44 mm** E/N/U | a common bias in our processing |
| Elevation mask 10° → 30° | AIS5–AIS6 is +21.33 mm north at 10° and +21.08 at 30°, spread 0.25 mm | low-elevation multipath |

An error that is fixed per pair to a few tenths of a millimetre across days, differs between pairs by
millimetres, and does not move when two thirds of the sky is discarded is a property of the site or of
its published coordinate — not of the software being tested. Which of the two it is, this cannot say:
a wrong published value and a wrong monument eccentricity or antenna orientation look identical from
here. For the criterion it does not matter, because neither is something GeoComp can fix.

**So GGAO was never an outlier.** GODN–GODE's `[3.852, 7.799, −2.808] mm` sits inside this
distribution, close to its median. The two defects §5.1 and §5.2 attribute are real and worth having
found, but they were never what kept the criterion red: **a pair with no defects at all misses by the
same order.** The estimator's own repeatability is 0.500 / 0.297 / 0.080 mm, so the comparison has
been measuring the reference's uncertainty all along, and that uncertainty is now measured rather than
merely described as unpublished: about 5 mm typical, up to 20 mm, on baselines short enough that the
atmosphere cannot account for it.

**What this does not establish.** The calibration used is IGS's type mean; if NGS's own `ngs20.atx`
carries an individual calibration for one of these antennas the two differ, though by well under a
millimetre and not by 20. `geodesy.noaa.gov` was re-checked on 24 September 2026 and still answers 403
to CONNECT, so that comparison cannot be made *here* — but it is now made in engine CI, which fetches
`ngs20.atx` for RD-06 anyway. That step re-runs all fourteen pairs against NGS's own calibration and
fails if any component moves by more than 1 mm, which is the size at which this section's conclusion
would change. It was the maintainer's condition, on 24 September 2026, for deciding the threshold at
all: [`20`](./20-testing-and-validation.md) §6 records that decision and stays empty until the
confirmation has run. And the fourteen pairs are all the same antenna type at
one kind of site, which is what makes them comparable with each other and also what limits how far the
number generalises.

**The consequence for the threshold is a decision, not a finding**, and it is recorded in
[`20`](./20-testing-and-validation.md) §6 rather than taken here.

## 6. Recommended order

1. ~~**The Krumm/GNU Gama examples.**~~ **Done** — see §2.2. 34 networks reproduced to 0.05 mm.
2. ~~**Fetch Krumm's document** and settle FR-161.~~ **Settled another way** — see §4. A public dataset of
   five networks published in the *Adjust* format did what the document was wanted for, and did it under a
   licence that permits redistribution. Krumm's document is still the shortest route to *published answers*
   in that format, which §4.3 records this corpus as not having.
3. **Resolve RD-06's measured discrepancy** against the frozen NGS data (§5); RBMC remains another candidate.
4. **Borrow the round-robin practice** for §5 rather than inventing a comparison protocol.
5. RD-07 and RD-08 when P8 and the monitoring phase need them.
