# 23 — Wanted: reference data still to be found

**Status:** Living register, first compiled 28 September 2026 (start of P10b). Every phase that finds a gap adds
to it; every item that is supplied moves to [`22-reference-data-sources.md`](./22-reference-data-sources.md)
with what it reproduced, and is struck through here rather than deleted.

**What this is for.** A list the maintainer can work from when looking for data, one entry per missing
reference, each saying what would close it. [`22`](./22-reference-data-sources.md) is the record of what was
found and what it proved; this is the list of what was *not* found. Nothing here is transcribed from memory:
the leads are places to look, not facts about what those places contain.

**Why most of it is missing.** The development environment's egress policy refuses the general web, journal
hosts and most geodetic archives (403 on CONNECT) — `geoftp.ibge.gov.br`, `cddis.nasa.gov`, `igs.bkg.bund.de`,
`files.igs.org`, `geodesy.noaa.gov`, the Onsala loading service, Zenodo, `www.geodetski-vestnik.com`. `git`
to GitHub and PyPI work. So every item below is something a person with an ordinary network connection, or a
library, can probably find in minutes, and this environment cannot find at all.

**How to hand one over.** A file uploaded to the session is enough, as `ngs20.atx` was for RD-06. Say where it
came from (citation, URL, retrieval date) and on what terms it may be redistributed. If it may not be
committed — as pyGrav's survey may not — it is fetched by pinned digest at test time instead
([`22`](./22-reference-data-sources.md) §5.6), and the test says so when it skips.

---

## 1. Blocking an acceptance criterion

These are the items that keep a criterion open. Each is worth more than everything in §2 and §3 together.

### W-01 — A published deformation analysis worked example (RD-08, published half)

| | |
|---|---|
| **Closes** | [`14`](./14-multi-epoch-monitoring.md) §9 criterion 3 — the only open criterion of the monitoring module; P10's exit criterion "RD-08 reproduces, including the significance decisions" |
| **Minimum that closes it** | One network observed at **two epochs**, with, for each epoch, either the adjusted coordinates **and their full covariance matrix** (or cofactor matrix and σ̂₀² with degrees of freedom), or the observations to re-adjust; which points are **reference** and which are **object**; the confidence level; and the **published decisions** — the global congruency test statistic and its critical value, the localisation steps if the block failed, and which points were declared moved |
| **Better** | Three or more epochs (checks the velocity path too); a published strain result for the object points |
| **Leads, unverified** | *Deformation analysis: the Caspary approach*, Geodetski vestnik 64(1), 2020 — works a 12-point dam network through the Caspary method and compares with the other named methods (host 403 from here). The worked examples in Caspary's monograph *Concepts of Network and Deformation Analysis* (UNSW School of Surveying). The deformation chapter of Niemeier, *Ausgleichungsrechnung*. The FIG ad hoc committee test networks used to compare the Hannover, Karlsruhe, Delft, Fredericton and München methods (Chrzanowski & Chen). JAG3D's documentation, if a worked example with numbers exists outside its repository |
| **Already tried** | Krumm's corpus (RD-11) and GNU Gama's: single-epoch only. JAG3D's repository: congruence code, no example with its numbers |

### W-02 — A gravimeter calibration table with a worked conversion (RD-07)

| | |
|---|---|
| **Closes** | [`12`](./12-module-gravimetry.md) §8 criterion 1, *scale* half — currently checked against a constructed table in a manufacturer's layout and against USGS's surveys with known 3/5/10 % calibration errors, but **not against a published example** |
| **Minimum that closes it** | A manufacturer's (or a textbook's) counter-reading → milligal table for one instrument, **plus** at least one reading converted with it and the printed result — e.g. a LaCoste & Romberg G- or D-meter table with the interval factors and a worked conversion |
| **Leads, unverified** | The instrument manuals (LaCoste & Romberg G/D, Scintrex CG-5/CG-6 calibration sheets); gravimetry textbooks' worked examples (Torge, *Gravimetry*); an IBGE or university field-procedure manual |

### W-03 — A relative network tied to published absolute stations (RD-07)

| | |
|---|---|
| **Closes** | The second gap [`22`](./22-reference-data-sources.md) §5.6 names: a relative survey adjusted onto **absolute** values checked against someone else's answer, not against synthetic truth |
| **Minimum that closes it, option A** | The **Burris sensor height** (or instrument-to-mark height) for meters B44 and B108 in USGS's December 2017 and February 2018 field surveys, already at the pinned GSadjust commit. With it, the Micro-g A-10 absolute values (given at a 100 cm transfer height with their gradient) can be compared. Nothing else is needed |
| **Option B** | A RENEGA (IBGE absolute network) station's published value with a relative tie survey to it |

---

## 2. Citation by name — validated already, but not against the named book

The operations below are validated against synthetic truth, least-squares identities, Monte Carlo and, for
most adjustments, 36 published networks (RD-11). What is missing is agreement with the **specific references
the specifications name**, which the commercial-comparison protocol ([`20`](./20-testing-and-validation.md)
§5) and the teaching material (FR-952) rely on.

| ID | Wanted | Names it | What is there instead |
|---|---|---|---|
| **W-04** | **Gemael's worked examples** — *Introdução ao ajustamento de observações: aplicações geodésicas* (Gemael, Machado & Wandresen). Covariance propagation and network adjustment examples with inputs and printed answers | [`05`](./05-uncertainty-and-covariance.md) §7 criterion 2, [`06`](./06-adjustment-core.md) §7 criterion 1 | Ghilani by name through Krumm's corpus (4 examples); Gemael by none. The Brazilian reference a Brazilian student will check against |
| **W-05** | **Levelling field books, one per scheme**, printed with their reductions — equal sights, equidistant sights, extreme sights ([`10`](./10-module-levelling.md) §2) — and a **loop misclosure with its tolerance, including a failing loop** | [`10`](./10-module-levelling.md) §7 criteria 1 and 2 | RD-04: field books generated by inverting the equations under test, which is stronger for correctness and says nothing about agreement by name |
| **W-06** | **A levelling network published under both length weighting and setup weighting**, with both answers | [`10`](./10-module-levelling.md) §7 criterion 4 | Krumm's 1D networks (5 reproduced), one weighting each |
| **W-07** | **A traverse with its misclosure and both adjustment paths** (a classical rule — Bowditch/compass or transit — and least squares), printed | [`09`](./09-module-total-station.md) §7 criterion 5 | RD-12 has three traverses but **no published answers** ([`22`](./22-reference-data-sources.md) §4.3) |
| **W-08** | **The published adjusted results for RD-12's five networks**, if their author has them | [`22`](./22-reference-data-sources.md) §4.3 | The reader and writer are validated by round trip; the adjustment of those networks is compared with nothing |

---

## 3. Real data that would widen a check

Nothing is blocked on these; each would make an existing check about something real rather than constructed.

| ID | Wanted | Why | State now |
|---|---|---|---|
| **W-09** | **An RBMC pair** (IBGE): RINEX for two stations with official SIRGAS 2000 coordinates, one day, ideally a short baseline with the **same antenna and radome** at both ends, both in `ngs20.atx` or `igs20.atx` | A Brazilian reference case in the national frame; RD-06 is NGS stations in ITRF2020 | RD-06 is met on closure and repeatability; the published-coordinate comparison is reported, not judged ([`22`](./22-reference-data-sources.md) §5.4) |
| **W-10** | **A real MAPGEO2015 grid** (IBGE) **and a handful of points with the undulation IBGE's own program prints** | The geoid readers are tested against the formats' published layouts with grids GeoComp wrote itself; a real file read and interpolated to IBGE's answer is independent | `tests/test_geoid_import.py` uses synthetic grids |
| **W-11** | **Ocean-loading coefficients** (Onsala service, BLQ format) for a few gravity stations, **and a published gravity series or example with the loading correction applied** | Ocean loading on gravity is P12's; it is not written until something can check it ([`12`](./12-module-gravimetry.md) §4.2) | Deferred, by the rule that an unverified feature is a claim |
| **W-12** | **A commercial package's full output for one fixed dataset** — adjusted coordinates, σ̂₀², degrees of freedom, residuals, ellipses, test decisions — with **its complete configuration** (Trimble Business Center, Leica Infinity, Topcon Magnet, Star\*Net, or similar) | FR-951's comparison protocol ([`20`](./20-testing-and-validation.md) §5) needs the other side | Protocol and export exist in the specification; no comparison has been run |
| **W-13** | **Student field campaigns** (RD-10) — total station, levelling and GNSS over one site, raw files as the instruments wrote them | End-to-end on real field data; planned for P13 | Project activity, not yet collected |

---

## 4. Access rather than data

Not examples, but they block a capability the same way.

| ID | Wanted | Blocks |
|---|---|---|
| **W-14** | **Reachable GNSS product archives** — any one of IGS (`files.igs.org`), CDDIS (`cddis.nasa.gov`, needs an Earthdata login), BKG (`igs.bkg.bund.de`), IBGE (`geoftp.ibge.gov.br`) — from CI or from the development environment; or a CI job allowed to fetch from one of them | FR-352/353 product download and NFR-010 credentials ([`ROADMAP.md`](./ROADMAP.md) P10b). Code that downloads from an archive nobody can reach would be untested |

---

## 5. How an item leaves this list

1. It is supplied, with its source and terms.
2. The test that uses it is written and passes — or fails, and the failure is attributed, as RD-06's was.
3. [`22`](./22-reference-data-sources.md) records it as found, with what it reproduced; the criterion it closes
   is updated in its own specification and in [`ROADMAP.md`](./ROADMAP.md).
4. The row here is struck through with the date and a pointer, not deleted, so the list also records what
   was once missing.
