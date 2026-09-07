<!-- SPDX-License-Identifier: GPL-2.0-or-later -->
# DynAdjust output fixtures

Real `dnaadjust` output, kept verbatim except for one thing: the `File name:`
and `Input files:` lines were rewritten to relative paths, because the absolute
ones name the machine that produced them and nothing reads them. Timestamps,
version banners, column spacing and every number are as the engine wrote them.

All were produced by **DynAdjust 1.4.0** built from upstream commit `5cdb897`.

| Fixture | Produced by | What it is here to exercise |
|---|---|---|
| `sample.{adj,apu,cor,xyz}` | the default flags, plus `--output-adj-msr --output-pos-uncertainty --output-all-covariances --output-corrections-file --stn-corrections` | the ordinary layout: `PLHhXYZ` coordinates, station corrections, and an `.apu` with the **full** covariance matrix between every pair of stations |
| `alt-flags.{adj,apu,xyz}` | `--output-tstat-adj-msr --output-apu-vcv-units 1 --stn-coord-types PLH --angular-stn-type 1` | that the layout is read from the file rather than assumed: three coordinate columns instead of seven, no corrections, an extra `T-stat` column, variances in the local `e,n,up` frame, and latitude and longitude in **decimal degrees** rather than HP notation |
| `sample-no-covariances.apu` | the `sample.*` flags **without** `--output-all-covariances` | that a missing full matrix stays missing: the per-station blocks are read and no block-diagonal is assembled from them, which would assert that every pair of stations is uncorrelated |
| `grid.xyz` with `grid-{stn,msr}.xml` | `--stn-coord-types ENz --precision-stn-linear 5` | the **UTM projection**, as an independent check on `core/geodesy/projection.py`. Fifteen stations on exact whole arcseconds -- values HP notation holds without rounding -- all constrained, so the output is a pure coordinate conversion rather than an adjustment, and eastings printed to 0.01 mm. Easting agrees with GeoComp to the printed precision; **northing does not**, by up to 0.25 mm at 45 degrees, and `specs/07` section 4.5 records which implementation the quadrature says is right |
| `grid-precision7.xyz` | `--stn-coord-types ENzPLH --precision-stn-angular 7` on the same `grid-*.xml` | the **column overflow**: a 15-character HP latitude in a 14-character field, so Zone, Latitude and Longitude run together and every field after them is a slice of the wrong text (`specs/07` §5.5) |
| `grid-hp-carry.xyz` | `--stn-coord-types ENzPLH` on the same `grid-*.xml`, default angular precision | **DynAdjust printing 60 minutes**: three stations at latitude -45 degrees, two written `-45.00000000` and one `-44.60000000`, which HP notation cannot hold. No unusual flags are needed for this one |
| `angles.{adj,apu,cor,xyz}` | the default flags on the network in `angles-*.xml` | every angular measurement type — `S`, `V`, `B`, `K`, `A`, `L` — with values in separated degrees/minutes/seconds and corrections and precisions in **seconds of arc**; also a `Failed to converge` solution and a `*** WARNING ***` chi-square verdict, which must not be read as success |

`terrestrial.{stn,msr}` are not an adjustment at all: they are what
`dnaimport --export-dna-files` makes of `terrestrial-{stn,msr}.xml`, which are
ours. They exist because every other DNA pair here is upstream's GNSS sample,
whose measurements are all Cartesian clusters — so the whole terrestrial half of
`engines/dynadjust/read_dna.py` was unreachable from the suite, and four column
defects were sitting in it. This pair carries a direction set, a slope distance
and a zenith angle with instrument and target heights, a horizontal angle with
three stations, a height difference and an orthometric height:

```sh
dnaimport -n terrestrial terrestrial-stn.xml terrestrial-msr.xml --export-dna-files
```

Its coordinates are made up. Every one is valid HP notation, which is less
obvious than it sounds: `-37.4782` looks like a latitude and is not one, because
82 seconds do not exist.

`sample.*` is an adjustment of the slice of upstream's `gnss-network` sample that
`tests/data/dynadjust/sample-{stn,msr}.xml` holds; that data is Apache-2.0 and is
attributed in `THIRD_PARTY.md`. `angles-stn.xml` and `angles-msr.xml` are ours,
written for this purpose, and are kept beside the outputs so the fixture can be
regenerated:

```sh
dnaimport -n angles angles-stn.xml angles-msr.xml
dnaadjust -n angles --output-adj-msr --output-pos-uncertainty \
    --output-corrections-file --stn-corrections
```

Its coordinates and measurements are made up and mutually consistent to within
the residuals shown; it is a parser fixture, not a reference network, and no
result in it means anything geodetically.

`grid-stn.xml` and `grid-msr.xml` are ours too, and exist to make one comparison
clean. Every station carries an `H` measurement because DynAdjust discards a
station no measurement reaches, and every station is constrained so the
adjustment moves nothing:

```sh
dnaimport -n grid grid-stn.xml grid-msr.xml
dnaadjust -n grid --stn-coord-types ENz --precision-stn-linear 5
```

The two `grid-*.xyz` fixtures beside it come from the same inputs with the angular columns added, and differ
from each other only in the requested precision:

```sh
dnaadjust -n grid --stn-coord-types ENzPLH                            # grid-hp-carry.xyz
dnaadjust -n grid --stn-coord-types ENzPLH --precision-stn-angular 7  # grid-precision7.xyz
```

Both are files GeoComp **refuses**, and each is here so that the refusal is the right one and says why.
