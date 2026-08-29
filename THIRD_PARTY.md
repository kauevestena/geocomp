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
| **RTKLIB** / **RTKLIB-EX** — GNSS post-processing (`rnx2rtkp`) | See the upstream `license.txt` | <https://www.rtklib.com/> · <https://github.com/rtklibexplorer/RTKLIB> |

**DynAdjust** is developed by Geoscience Australia. It builds against Boost, Apache Xerces-C++ and
CodeSynthesis XSD; the last is GPL-2.0-licensed, which affects the distribution terms of the DynAdjust binary
itself rather than GeoComp's. It is one more reason GeoComp downloads engine binaries from upstream instead
of redistributing them.

**RTKLIB** was written by T. Takasu; **RTKLIB-EX** (formerly "demo5") is the rtklibexplorer fork, based on
RTKLIB 2.4.3 and optimised for low-cost receivers. The research project names RTKLIB-EX; GeoComp targets
`rnx2rtkp` from both distributions and records which one produced a result.

Where GeoComp downloads an engine, it places that engine's own licence text alongside the binary and shows
it in the About dialog.

### Test data redistributed from DynAdjust

`tests/data/dynadjust/sample-stn.xml`, `sample-msr.xml`, `sample.stn` and `sample.msr` are a **slice of
upstream's own `sampleData/gnss-network` files** — the same network in both DynaML and DNA form —, from the DynAdjust repository, under **Apache-2.0**. Around ten stations and
four measurements — one GNSS baseline cluster, one point cluster and two single baselines — kept because the
parsers must be tested against files DynAdjust itself accepts, rather than against files written to satisfy
the parser.

This is the one place GeoComp redistributes anything of upstream's, and it is data rather than a binary.
Apache-2.0 permits it; the attribution is here and in the test module that reads them.

## Attribution

Beyond licence obligation. GeoComp exists because DynAdjust and RTKLIB exist, and the research project
commits to feeding defects and improvements back upstream (FR-955):

- **DynAdjust** — Geoscience Australia. Fraser, R., Leahy, F. and Collier, P., *DynAdjust User's Guide*.
  Harrison, C., Brown, N., Dawson, J. and Fraser, R. (2024), *Geocentric Datum of Australia 2020*,
  Journal of Spatial Science 69(1).
- **RTKLIB** — Takasu, T., *RTKLIB: An Open Source Program Package for GNSS Positioning*, and the
  RTKLIB-EX contributors.
- **QGIS** — the QGIS Development Team, for the platform and its Processing framework.

## Bundled assets

| Asset | Origin | Licence |
|---|---|---|
| `geocomp/resources/icons/geocomp.svg` | Original work for this project | GPL-2.0-or-later |
| `topo_test/` (reference dataset RD-01) | Collected by the project author | GPL-2.0-or-later, as part of this repository |

## Keeping this file current

Adding a runtime dependency requires a row here and a recorded justification (NFR-005) — a QGIS plugin
cannot assume the user can run `pip`, so each new dependency is a real cost to weigh. A CI check asserts that
every Python source carries an SPDX header; nothing yet checks this table, so it is maintained by review.
