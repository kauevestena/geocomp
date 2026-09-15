# Third-party components

GeoComp is licensed **GPL-2.0-or-later** (see [`LICENSE`](LICENSE) and
[`specs/adr/0001-licensing.md`](specs/adr/0001-licensing.md)). This file records every third-party component
it depends on, as required by `specs/21-packaging-ci-release-licensing.md` §7.3.

## Two kinds of dependency, and why the distinction matters

**Imported libraries** are loaded into the same Python process as GeoComp, so their licences interact with
GeoComp's. This is the reason GeoComp is GPL: PyQGIS and PyQt are GPL, and a plugin that imports them is a
derivative work in the sense the GPL intends.

**Processing engines** are different. GeoComp writes input files, runs a separate program, and reads its
output files. It never links against them, never loads them into its process, and never redistributes them —
they are downloaded from upstream at the user's request
([`specs/adr/0003-engine-acquisition.md`](specs/adr/0003-engine-acquisition.md)). This is arm's-length use,
not derivation, and their licences do not combine with GeoComp's.

---

## Imported libraries

| Component | Licence | Relationship | Notes |
|---|---|---|---|
| [QGIS / PyQGIS](https://qgis.org) | GPL-2.0-or-later | Imported | The host application. Its licence determines GeoComp's |
| [PyQt](https://riverbankcomputing.com/software/pyqt) | GPL-3.0 or commercial | Imported via `qgis.PyQt` | GeoComp imports Qt through the QGIS shim rather than directly |
| [NumPy](https://numpy.org) | BSD-3-Clause | Imported | Ships with QGIS. Used from phase P1 |
| [SciPy](https://scipy.org) | BSD-3-Clause | Imported when present | Optional: sparse factorisation and distribution quantiles. A NumPy-only fallback is required and tested ([`specs/03-architecture.md`](specs/03-architecture.md) §3.7) |
| [openpyxl](https://openpyxl.readthedocs.io) | MIT | Imported when present | Optional: `.xlsx` import and export (FR-160). Degrades to CSV when absent |

## Processing engines (separate programs, not bundled)

| Component | Licence | Upstream |
|---|---|---|
| **DynAdjust** — least-squares network adjustment | Apache-2.0 | <https://github.com/GeoscienceAustralia/DynAdjust> |
| **RTKLIB** / **RTKLIB-EX** — GNSS post-processing (`rnx2rtkp`) | BSD-2-Clause | <https://www.rtklib.com/> · <https://github.com/rtklibexplorer/RTKLIB> |

**DynAdjust** is developed by Geoscience Australia. It builds against Boost, Apache Xerces-C++ and
CodeSynthesis XSD; the last is GPL-2.0-licensed, which affects the distribution terms of the DynAdjust binary
itself rather than GeoComp's. It is one more reason GeoComp downloads engine binaries from upstream instead
of redistributing them.

**RTKLIB** was written by T. Takasu; **RTKLIB-EX** (formerly "demo5") is the rtklibexplorer fork, based on
RTKLIB 2.4.3 and optimised for low-cost receivers. The research project names RTKLIB-EX; GeoComp targets
`rnx2rtkp` from both distributions and records which one produced a result. The licence is **BSD 2-clause**
(`license.txt`, "Copyright (c) 2007-2020, T. Takasu, All rights reserved"), confirmed at the pinned commit in
phase P7 — the previous entry here said only "see the upstream `license.txt`", which is not an answer.

Where GeoComp downloads an engine, it places that engine's own licence text alongside the binary and shows
it in the About dialog.

### Test data redistributed from DynAdjust

`tests/data/dynadjust/sample-stn.xml`, `sample-msr.xml`, `sample.stn` and `sample.msr` are a **slice of
upstream's own `sampleData/gnss-network` files** — the same network in both DynaML and DNA form —, from the DynAdjust repository, under **Apache-2.0**. Around ten stations and
four measurements — one GNSS baseline cluster, one point cluster and two single baselines — kept because the
parsers must be tested against files DynAdjust itself accepts, rather than against files written to satisfy
the parser.

Apache-2.0 permits it; the attribution is here and in the test module that reads them. It is data rather
than a binary, and like the Krumm corpus below it is test data that never enters the plugin package.

### Test data redistributed from RTKLIB

`tests/data/rtklib/07590920.05o`, `30400920.05o` and `brdc_0759.05n.gz` are
**RTKLIB's own sample data**, copied unmodified from `test/data/rinex/` of
[RTKLIB-EX](https://github.com/rtklibexplorer/RTKLIB) at commit `06e8644`
(`rnx2rtkp ver.EX 2.5.1`); the navigation file is gzipped here and otherwise
byte-identical. They are a real 2005 GSI Japan survey: two marks observing the
same hour at 30 s, which is a genuine relative-static baseline rather than a
pair of unrelated files.

**BSD 2-clause** permits the redistribution with the copyright notice, which is
this entry. Like the other corpora below, it is test data and never enters the
plugin package.

The RINEX 3 fixture beside them, `rinex3-header.rnx`, is **not** RTKLIB's — it
is transcribed from the published RINEX 3.04 format definition, because nothing
in the RTKLIB tree is RINEX 3 and `convbin` aborts with a buffer overflow when
asked to convert one. `tests/data/rtklib/PROVENANCE.md` records both facts, and
the tests say which fixture is which.

### Test data redistributed from GNU Gama — the Krumm examples

`tests/data/krumm/` is **107 files copied verbatim** from
[GNU Gama](https://www.gnu.org/software/gama/)'s `tests/krumm/input/`, at commit
`963c3099054594922716786f92119732f12d714e` (GNU Gama 2.24): 61 network
definitions, 45 published answers, and Gama's own `README.md`. They are the
example networks of

> Friedhelm Krumm, *Geodetic Network Adjustment Examples*, Geodätisches Institut,
> Universität Stuttgart, Rev. 3.5, 2020,

which transcribe worked examples from a dozen textbooks — Ghilani, Niemeier,
Benning, Wolf, Leick, Strang and Borre among them — each `.dat` naming its own
source by edition and page. GeoComp reproduces 33 of them to 0.05 mm (RD-11).

**Licence.** GNU Gama is **GPL-3.0-or-later**. GeoComp is GPL-2.0-*or-later*, so
it may be combined with GPL-3.0 material; the combined work is then effectively
GPL-3.0, and `tests/data/krumm/` carries a GPL-3.0-or-later SPDX header rather
than the repository's usual one. The underlying numbers are transcriptions from
copyrighted textbooks; GNU Gama redistributes them publicly with attribution and
a documented changelog of its edits, and this repository does the same, unedited,
from a named commit. That is the basis, and it is the same basis Gama relies on.

**Test data, and what keeps it so.** These files exist to validate the
adjustment core. They live under `tests/`, never under `geocomp/`, and
`scripts/build.py` packages `geocomp/` alone — so **nothing here reaches an
installed plugin**. That is asserted by
`tests/test_krumm_corpus.py::TestTheCorpusIsTestDataOnly`, not merely intended,
because the plugin ZIP is the artefact actually distributed to users and putting
this data in it would be a different question from the one answered above.

`scripts/check_krumm_corpus.py` compares every vendored file against a fresh
clone of the pinned commit and fails on any difference; the `reference` workflow
runs it. An attribution to a source you have quietly edited is not an
attribution, so the "verbatim" claim is checked rather than asserted.
`tests/data/krumm/PROVENANCE.md` records the whole chain.

### Test data redistributed from a public dataset — the *Adjust*-format networks

`tests/data/adjust/` holds **five surveying networks** — twelve free stations, three traverses and a
triangulateration over one set of four control points — from

> the dataset at <https://data.mendeley.com/datasets/rr8js427vt/1>, `doi:10.17632/rr8js427vt.1`,
> accompanying a doctoral thesis on network establishment methods,

under **CC BY 4.0**. They are RD-12 ([`specs/22`](specs/22-reference-data-sources.md) §4), and they are what
closed FR-161 after it had been re-planned out of three phases for want of one example file in the format.

**Converted, not copied.** The dataset is published as `.Adat` files — the format of Charles Ghilani's
*Adjust* teaching software. The *data* is CC BY 4.0 and free to redistribute; the *format* is not this
repository's to carry, so the networks are vendored as `Network.to_dict()` JSON instead, produced by
`scripts/convert_adjust_corpus.py`. GeoComp's own serialisation is a documented format the project already
round-trips, so nothing is lost.

Interoperability with the format is still implemented — that *is* FR-161, and `geocomp/io/adjust.py` reads
and writes it. It is exercised by round trip, and against the original files for anyone who sets
`GEOCOMP_ADJUST_DIR`.

**Attribution** is the licence's one obligation, and it is met here, in
`tests/data/adjust/PROVENANCE.md`, and in the test module that reads them. Two defects in the publication are
documented in both rather than quietly repaired; the file carrying the more interesting one is vendored twice,
faithfully and corrected, and PROVENANCE.md says which is which.

**Test data, and what keeps it so.** These files live under `tests/`, never under `geocomp/`, and
`scripts/build.py` packages `geocomp/` alone — so nothing here reaches an installed plugin. That is asserted
by `tests/test_adjust_corpus.py::TestTheCorpusIsTestDataOnly`, not merely intended.

## Attribution

Beyond licence obligation. GeoComp exists because DynAdjust and RTKLIB exist, and the research project
commits to feeding defects and improvements back upstream (FR-955):

- **DynAdjust** — Geoscience Australia. Fraser, R., Leahy, F. and Collier, P., *DynAdjust User's Guide*.
  Harrison, C., Brown, N., Dawson, J. and Fraser, R. (2024), *Geocentric Datum of Australia 2020*,
  Journal of Spatial Science 69(1).
- **RTKLIB** — Takasu, T., *RTKLIB: An Open Source Program Package for GNSS Positioning*, and the
  RTKLIB-EX contributors.
- **QGIS** — the QGIS Development Team, for the platform and its Processing framework.
- **GNU Gama** — Aleš Čepek and contributors, for the adjustment package, for `krumm2gama-local` (the
  reference implementation this project's Krumm reader was written against), and for assembling and
  maintaining the example corpus. **Friedhelm Krumm**, Universität Stuttgart, for the examples themselves.

## Bundled assets

| Asset | Origin | Licence |
|---|---|---|
| `geocomp/resources/icons/geocomp.svg` | Original work for this project | GPL-2.0-or-later |
| `topo_test/` (reference dataset RD-01) | Collected by the project author | GPL-2.0-or-later, as part of this repository |

Development data, in the repository but **not** in the plugin package:

| Asset | Origin | Licence |
|---|---|---|
| `tests/data/krumm/` (RD-11) | GNU Gama `tests/krumm/input` at `963c309`; examples by F. Krumm | GPL-3.0-or-later |
| `tests/data/dynadjust/sample*` | DynAdjust `sampleData/gnss-network` | Apache-2.0 |

## Keeping this file current

Adding a runtime dependency requires a row here and a recorded justification (NFR-005) — a QGIS plugin
cannot assume the user can run `pip`, so each new dependency is a real cost to weigh. A CI check asserts that
every Python source carries an SPDX header; nothing yet checks this table, so it is maintained by review.
