<!-- SPDX-License-Identifier: GPL-2.0-or-later -->
# RTKLIB sample data

`07590920.05o`, `30400920.05o` and the file gzipped here as `brdc_0759.05n.gz`
are **RTKLIB's own test data, copied unmodified** from `test/data/rinex/` of
[RTKLIB-EX](https://github.com/rtklibexplorer/RTKLIB) at commit `06e8644`
(`rnx2rtkp ver.EX 2.5.1`). RTKLIB is distributed under the **BSD 2-clause**
licence, which permits redistribution with the copyright notice; the
attribution is in [`THIRD_PARTY.md`](../../../THIRD_PARTY.md).

| File | What it is | Why it is here |
|---|---|---|
| `07590920.05o` | Station `0759`, RINEX 2.10, GPS L1/C1/L2/P2 at 30 s, 2 April 2005 | One end of a real baseline. Marker name, receiver `TRIMBLE 5700`, antenna `TRM29659.00`, approximate position and a **zero** antenna delta |
| `30400920.05o` | Station `3040`, same day, same interval, same receiver and antenna model | The other end. The two observe **simultaneously**, which is what makes them a relative-static pair rather than two files |
| `brdc_0759.05n.gz` | The broadcast navigation file for the same day, gzipped here | The navigation input, and the only **gzipped** fixture — so the compression path is exercised on a real file rather than on one this project wrote |

The pair is a genuine 2005 Japanese GSI survey, and `rnx2rtkp -p 3` resolves the
ambiguities on it within four epochs. That makes it a real end-to-end fixture
for session discovery, the runner and the `.pos` parser.

**What it is not.** These stations have no published official coordinates
reachable from this project, so the pair validates the *pipeline* and not the
*accuracy*. The reference dataset that would validate accuracy is **RD-06**, and
[`specs/22-reference-data-sources.md`](../../../specs/22-reference-data-sources.md)
§5 records why it is not here.

**No RINEX 3 observation file is committed, because none could be produced.**
Nothing in the RTKLIB tree is RINEX 3, and `convbin`, the tool that would convert
one, **aborts with a glibc buffer overflow** on RTKLIB's own sample data at this
commit:

```console
$ convbin -r rinex -v 3.04 -o base.rnx 07590920.05o
scanning: 2005/04/02 00:59:00 G
*** buffer overflow detected ***: terminated
```

Reproducible with those flags alone. `convbin` is not a GeoComp deliverable, so
this is recorded rather than worked around. The RINEX 3 header path in
`geocomp/io/rinex.py` is therefore covered by a **transcribed** fixture built
from the published RINEX 3.04 format definition — `rinex3-header.rnx` — and the
tests say so rather than implying a tool wrote it.

## `pos/` — solution files written by a real engine

Four runs of the **same** relative-static solution over the RINEX pair above,
one per output format, produced by `rnx2rtkp ver.EX 2.5.1` built from RTKLIB-EX
commit `06e8644`:

```sh
rnx2rtkp -p 3 -m 15 [FLAGS] -o pos/NAME.pos 07590920.05o 30400920.05o nav.05n
```

| Fixture | Flags | What it is here to exercise |
|---|---|---|
| `llh.pos` | none | The default: latitude, longitude, height, with cross columns labelled `sdne sdeu sdun` |
| `llh-dms.pos` | `-g` | The same solution with latitude and longitude split into degrees, minutes and seconds — **seven** position columns, a seven-number `% ref pos` line, and the mislabelled third cross column (below) |
| `xyz.pos` | `-e` | ECEF, whose cross columns are `sdxy sdyz sdzx` — a different pairing order from either geodetic format |
| `enu.pos` | `-a` | The ENU **baseline**, whose cross columns are `sden sdnu sdue` — a third pairing order |
| `llh-calendar.pos` | `-t` | A calendar date and time where the default writes a GPS week and second-of-week. Both are two whitespace-separated fields, which is what lets one parser take either |

Only the absolute paths on the `% inp file` lines were rewritten to relative
ones, exactly as the DynAdjust fixtures were: they name the machine that
produced them and nothing reads them. Every number is as the engine wrote it.

**Why four.** `llh.pos` and `enu.pos` are one solution in two orderings, so
their covariances must be one matrix under permutation — which is what makes the
per-format column mapping evidence rather than assertion. `llh-dms.pos` is the
same solution again, and proves that ignoring a wrong column label is correct:

> With `-g`, RTKLIB labels the third cross column **`sdue`** while writing the
> same `sqvar(Q[5])` — the **N–U** covariance — that the default format
> correctly calls `sdun`. And `sdue` genuinely means E–U in the ENU format. So
> the same label means two different things across formats, and in one of them
> it is wrong. Confirmed twice: by reading `outsolheads` in `src/solution.c` at
> the pinned commit, and by running the engine both ways and comparing the
> printed values, which are identical.

`specs/08-engine-rtklib.md` §7.1 records the column table this establishes, §7.2 the
signed-square-root encoding, and §7.3 the mislabelled header.
