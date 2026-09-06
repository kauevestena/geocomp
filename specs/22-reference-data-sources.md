<!-- SPDX-License-Identifier: GPL-2.0-or-later -->
# 22 — Reference data sources

**Status:** Draft. §2 is implemented (RD-11); §§3-5 remain leads.
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

[`20-testing-and-validation.md`](./20-testing-and-validation.md) §3 lists nine reference datasets. Three are
still marked *to assemble* (RD-06, RD-07, RD-08), and RD-02, RD-03 and RD-04 carry a standing note that their
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

## 5. RD-06, RD-07, RD-08 — the three still to assemble **[C]**

**RD-06, GNSS with published official coordinates.** [IBGE's RBMC](https://www.ibge.gov.br/geociencias/informacoes-sobre-posicionamento-geodesico/rede-geodesica/16258-rede-brasileira-de-monitoramento-continuo-dos-sistemas-gnss-rbmc.html)
(*Rede Brasileira de Monitoramento Contínuo*) publishes RINEX for every station together with official
SIRGAS2000 coordinates; station reports come from the Banco de Dados Geodésicos at `bdg.ibge.gov.br`. RINEX 3
at 1 s has been available since 2020. This is the natural choice for a Brazilian project: the coordinates are
official, the frame is the national one, and the data is public. NGS/CORS and Geoscience Australia are the
equivalents elsewhere. Licence terms were not checked.

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

## 6. Recommended order

1. ~~**The Krumm/GNU Gama examples.**~~ **Done** — see §2.2. 34 networks reproduced to 0.05 mm.
2. ~~**Fetch Krumm's document** and settle FR-161.~~ **Settled another way** — see §4. A public dataset of
   five networks published in the *Adjust* format did what the document was wanted for, and did it under a
   licence that permits redistribution. Krumm's document is still the shortest route to *published answers*
   in that format, which §4.3 records this corpus as not having.
3. **RD-06 from RBMC**, when P7 needs it.
4. **Borrow the round-robin practice** for §5 rather than inventing a comparison protocol.
5. RD-07 and RD-08 when P8 and the monitoring phase need them.
