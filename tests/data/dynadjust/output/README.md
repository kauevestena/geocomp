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
| `angles.{adj,apu,cor,xyz}` | the default flags on the network in `angles-*.xml` | every angular measurement type — `S`, `V`, `B`, `K`, `A`, `L` — with values in separated degrees/minutes/seconds and corrections and precisions in **seconds of arc**; also a `Failed to converge` solution and a `*** WARNING ***` chi-square verdict, which must not be read as success |

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
