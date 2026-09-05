<!-- SPDX-License-Identifier: GPL-3.0-or-later -->
# Provenance of this directory

**These files are not GeoComp's.** They are copied verbatim from GNU Gama, and
`README.md` beside this file is GNU Gama's own — left exactly as it arrived,
including its changelog of the edits Gama made to Krumm's originals.

| | |
|---|---|
| **Upstream** | <https://github.com/Geo-Linux-Calculations/gnu-gama> |
| **Path** | `tests/krumm/input/` |
| **Commit** | `963c3099054594922716786f92119732f12d714e` (GNU Gama 2.24) |
| **Copied** | 61 `.dat` inputs, 45 `.adj` published answers, and `README.md` |
| **Modified** | Nothing. `scripts/check_krumm_corpus.py` proves it |

## Where the numbers come from

> Friedhelm Krumm, *Geodetic Network Adjustment Examples*, Geodätisches
> Institut, Universität Stuttgart, Rev. 3.5, 20 January 2020.

Krumm's document transcribes worked examples from a dozen textbooks — Ghilani,
Niemeier, Benning, Wolf, Leick, Strang and Borre, Grossmann, Caspary, Höpke,
Baumann, Mittermayer, Lother and Strehle among them. Each `.dat` names its own
source, by edition and page, in its `[Source]` or `[Quelle]` section. The `.adj`
files hold **Krumm's published adjusted coordinates**, not GNU Gama's output —
Gama's README is explicit about this, and it is the property that makes them
worth having: a check against one's own previous output proves nothing.

## Licence, and the honest statement of it

GNU Gama is **GPL-3.0-or-later**. GeoComp is GPL-2.0-**or-later**, which may be
combined with GPL-3.0 material; the combined portion is then effectively
GPL-3.0. That is why this directory carries a GPL-3.0-or-later SPDX header
rather than the repository's usual GPL-2.0-or-later one.

The underlying numbers are transcriptions from copyrighted textbooks. GNU Gama
redistributes them publicly with attribution and a documented changelog of its
edits, and this directory does the same, unchanged, from a named commit. That
is the basis on which they are here; it is the same basis Gama relies on.

## Testing only, and what enforces it

These files exist to validate the adjustment core against published answers
(RD-11, `specs/20-testing-and-validation.md` §3). They are **development data,
not plugin content**:

* they live under `tests/`, never under `geocomp/`;
* `scripts/build.py` packages `geocomp/` alone, so nothing here reaches an
  installed plugin — asserted by `tests/test_krumm_corpus.py`, not merely
  intended;
* no GeoComp runtime code reads this directory. Only the tests do.

If that ever stops being true, the licensing question changes shape, because
the plugin ZIP is what gets distributed to users.
