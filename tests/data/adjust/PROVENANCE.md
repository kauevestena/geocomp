<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Provenance of this directory

**These are not GeoComp's networks, and they are not in the format they were
published in.** They are five surveying networks from a public dataset,
converted from the *Adjust* format into GeoComp's own `Network` serialisation.

| | |
|---|---|
| **Source** | <https://data.mendeley.com/datasets/rr8js427vt/1> (`doi:10.17632/rr8js427vt.1`) |
| **Licence** | **CC BY 4.0** |
| **Published as** | ten `.Adat` files — five networks, each with and without observed values |
| **Vendored as** | `Network.to_dict()` JSON, produced by `scripts/convert_adjust_corpus.py` |
| **Accompanies** | a doctoral thesis; the dataset record is the citable artefact |

## Why converted rather than copied

The *data* is CC BY 4.0 and free to redistribute. The **format** is another
matter: it belongs to Charles Ghilani's *Adjust* teaching software, and this
repository does not carry files in it. GeoComp's own serialisation is a
documented format the project already round-trips, so nothing is lost by
carrying the networks in it.

Interoperability with the *Adjust* format is still implemented — that is
FR-161, and `geocomp/io/adjust.py` reads and writes it. It is exercised by
**round trip** (write a network out, read it back, compare) rather than against
a vendored `.Adat`. Anyone holding the original files can point
`GEOCOMP_ADJUST_DIR` at them and `tests/test_adjust_corpus.py` will read those
too, exactly as `GEOCOMP_KRUMM_DIR` works for the Krumm corpus.

## The five networks

The dataset compares three ways of establishing the same 16-point network over
the same four control stations — which is what makes it worth having: the same
ground, surveyed three ways, with the differences visible.

| File | Network | Observations | Notes |
|---|---|---|---|
| `free-stations.json` | 12 free stations (`EL1`…`EL12`) sighting the network points | 51 distances, 52 angles | The method the thesis is about |
| `traverse-ac.json` | traverse A→C | 6 distances, 7 angles | |
| `traverse-ad.json` | traverse A→D | 5 distances, 6 angles | |
| `traverse-bc.json` | traverse B→C | 8 distances, 9 angles | |
| `triangulateration.json` | conventional triangulateration | 40 distances, 69 angles | **Carries a blunder — see below** |
| `triangulateration-corrected.json` | the same, with the blunder undone | 40 distances, 69 angles | |

Control stations `A`…`D` are **weighted**, not held: the format states two
standard deviations per control station (0.010 m here), and holding such a
station exactly would assert a certainty the file does not.

## What GeoComp measures on them

Adjusted as plane networks with the control weighted as published:

| Network | dof | σ̂₀² | worst standardised residual |
|---|---|---|---|
| `free-stations` | 47 | **0.0028** | 0.1 |
| `traverse-ac` | 3 | 845 | 19.7 |
| `traverse-ad` | 3 | 1195 | 15.3 |
| `traverse-bc` | 3 | 482 | 12.1 |
| `triangulateration` | 77 | **8.6 × 10⁶** | 12040 |
| `triangulateration-corrected` | 77 | 61.5 | 8.3 |

**The traverses have no redundancy of their own.** Freed of their control they
adjust with **−2** degrees of freedom: 13 observations against 14 estimable
parameters. All three of their degrees of freedom come from the weighted
control, so their σ̂₀² measures how far each traverse misses its control, not
how well its observations agree among themselves. That is a property of a
traverse, not a defect in the data.

## Two defects in the published files

Both were found by reading the files, and both are recorded here because a
reference dataset whose defects are undocumented is a trap.

### 1. `MMEL dados.Adat` miscounts its own angles

Its header declares `51 51 0 4 32` — 51 distances and 51 angles — and the file
holds 51 distances and **52** angles. Comparing it against its valueless half,
which declares `52 52` and holds them, one distance (`EL10 16`) was removed and
*both* counts were decremented. The rows are the data; the header is a summary,
and this summary is wrong by one.

`read_adjust` refuses the file by default and names both counts, because the
header is the format's own self-check and a file that fails it cannot say which
reading was intended. `accept_count_mismatch=True` reads the rows that are
actually there, which is what the conversion did.

### 2. The round of angles at station 9 of the triangulateration is rotated

Six angles are observed at station 9. **Each carries the value belonging to the
next row in the round.**

| row | value in the file | implied by the file's own coordinates |
|---|---|---|
| `D 9 4` | 71.158° | 32.293° |
| `4 9 8` | 62.061° | 71.158° |
| `8 9 14` | 67.185° | 62.061° |
| `14 9 16` | 34.178° | 67.185° |
| `16 9 C` | 93.302° | 34.167° |
| `C 9 D` | 32.117° | 93.136° |

Each row's value matches the *next* row's computed angle to 0.18°, while the
other 63 angles in the file agree to a median of 0.0001°.

**A closure check cannot see this.** The round still sums to 360.00028°,
because rotating a closed round leaves its sum unchanged. Only the least-squares
residuals find it, and they find it emphatically: σ̂₀² of 8.6 × 10⁶ against 61.5
once the values are rotated back, and a worst standardised residual of 12040
against 8.3.

Both copies are vendored, deliberately:

* `triangulateration.json` is **faithful to the publication** and is the
  reference case for blunder detection — a real blunder, of unknown provenance,
  that the classical field check passes.
* `triangulateration-corrected.json` has the six values rotated back by one
  position, and is for validating the adjustment itself.

Correcting the round does **not** make the network fit its stated
uncertainties: σ̂₀² is 61.5 and the worst residual 8.3σ. Whether that is the
stated sigmas being optimistic or something else in the data, this repository
does not claim to know.

## Test data, and what keeps it so

These files validate the adjustment core and the *Adjust* reader. They live
under `tests/`, never under `geocomp/`, and `scripts/build.py` packages
`geocomp/` alone — so **nothing here reaches an installed plugin**. That is
asserted by `tests/test_adjust_corpus.py`, not merely intended.
