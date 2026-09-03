<!-- SPDX-License-Identifier: GPL-2.0-or-later -->
# 22. Reference data sources

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

* **FR-161**, the *Adjust* (Ghilani) format, has been re-planned twice — out of P5 and then out of P6 — for
  want of one example file with a published answer.
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

### 2.2 What this would take, and what it is worth

A reader for the Krumm `.dat` format is a modest piece of work: it is line-oriented with `[Section]`
headers, documented in the README beside the data, and GNU Gama's own `krumm2gama-local` is a working
reference implementation to check against. Against that cost:

* RD-03's citation gap closes **by name and page**, for the book the note names.
* The cross-validation gets its second and third networks — and many more — without needing the geodetic
  reductions GeoComp lacks.
* A plane trilateration and a levelling network finally get adjusted by something other than GeoComp.
* GNU Gama becomes a **third** independent implementation, in the frame the core natively uses.

**Licensing.** The files are distributed inside GNU Gama under GPL-3.0. GeoComp is GPL-2.0-*or-later*, so it
may be combined with GPL-3.0 material; the combined portion is then effectively GPL-3.0, which is worth
stating explicitly rather than discovering at release. Attribution to Krumm and to GNU Gama belongs in
`THIRD_PARTY.md`, on the same terms as the DynAdjust sample data already there. The underlying numbers are
worked examples from textbooks; GNU Gama redistributes them with attribution and a documented changelog of
its edits, which is the model to follow.

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

## 4. FR-161 — a specific lead, not a resolution **[C]**

Krumm's document is reported to ship **input files for Charles Ghilani's `Adjust` program**, with the ASCII
data in companion zip archives, alongside the examples above. If so, that is exactly what FR-161 has twice
been re-planned for want of: an *Adjust*-format file whose published answer is known.

**Not verified.** GNU Gama's copy of the Krumm data contains only `.dat` and `.adj` — no Adjust-format files
— and `www.gis.uni-stuttgart.de` is unreachable from this environment. The document itself is at
`https://www.gis.uni-stuttgart.de/lehre/campus-docs/adjustment_examples.pdf`. Ghilani's `ADJUST` program is
separately distributed from the Wiley student companion site for *Adjustment Computations*.

This changes FR-161's status from *blocked, no known source* to *blocked on one download somebody with a
normal connection can do in a minute*. It should not be implemented until the file is in hand.

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

1. **The Krumm/GNU Gama examples.** Verified, licence-compatible, 45 published answers, and it unblocks both
   the citation gap and the cross-validation count. Nothing else here has that ratio.
2. **Fetch Krumm's document** and settle FR-161 one way or the other, since it is one download.
3. **RD-06 from RBMC**, when P7 needs it.
4. **Borrow the round-robin practice** for §5 rather than inventing a comparison protocol.
5. RD-07 and RD-08 when P8 and the monitoring phase need them.
