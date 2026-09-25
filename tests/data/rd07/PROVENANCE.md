<!-- SPDX-License-Identifier: GPL-2.0-or-later -->
# Provenance of RD-07

RD-07 is the gravimetric reference case of [`specs/22`](../../../specs/22-reference-data-sources.md)
§5.6. It has four parts, and only two of them live in this directory.

## `eterna_hw95.json` — GeoComp's own output of ETERNA

Rigid-Earth tidal gravity at three latitudes and two epochs, 30 days hourly,
computed by **ETERNA PREDICT 3.4** with the **Hartmann and Wenzel (1995)**
catalogue through **pygtide 0.9.1** (MPL-2.0), pole and length-of-day tides off,
one wave group of amplitude 1. It is the output of someone else's program run
by GeoComp, and `scripts/check_tide_reference.py` regenerates it and fails if it
has changed. The generator settings are recorded inside the file.

pygtide is a test-time reference, never a runtime dependency: it is compiled
Fortran, not shipped with QGIS.

## `gsadjust/` — USGS's synthetic test surveys, verbatim

| | |
|---|---|
| **Upstream** | <https://github.com/jkennedy-usgs/sgp-gsadjust>, branch `2.0.0` |
| **Path** | `test_data/synthetic/` |
| **Commit** | `17bb3ca09f0ea23b6a74c1c44ae0a2c77c64b440` |
| **Copied** | `GSadjust_TestData.xlsx` and `Test1.txt` … `Test5.txt` |
| **Modified** | Nothing. `scripts/check_rd07.py` proves it against the upstream commit |

GSadjust is a product of the USGS Southwest Gravity Program; its `LICENSE.md`
places it in the public domain in the United States and dedicates it worldwide
under CC0 1.0. These files are USGS's own work — synthetic surveys generated
from a stated truth, drift and calibration — so that dedication covers them.

The workbook states the truth each survey was generated from, and that is what
makes it a reference rather than a fixture: a result that recovers it is not
recovering GeoComp's own assumptions. `tests/test_gravimetry_network.py`
transcribes the truth and checks the transcription against the workbook.

SHA-256:

```
3a1d29df5540be8d9420126801e3dbea91b27d3e3d36e54031bf793318beb9b9  GSadjust_TestData.xlsx
dd1e6468dd10fc526f0900e42825a4152c27d16b254bd1c26aab721cccbbd6e5  Test1.txt
05cd8ccdbb4b685c28e27fa2a0e199bcb56838729df59570ab44d55e04fe2c0b  Test2.txt
910640b46e5d5a423e4bbb51bcfaaa42a0895bfaeeeee6ae4b09acd95514d201  Test3.txt
2f0c964e5497f0c73c0fd164387e898d412fe83c76a50f0d8d736c205dd594ac  Test4.txt
574140376776b411d3f8be9a03d793040275004e009d18b09a53612c004d7798  Test5.txt
```

## Not here: the CG-5 survey and pyGrav's published solution

| | Upstream | Commit | Path |
|---|---|---|---|
| CG-5 survey | GSadjust | `17bb3ca…` | `test_data/field/CG-5/CG-5_TestData.txt` |
| Published solution | <https://github.com/basileh/pyGrav> | `fc39609b6393dd935a8a0417698217bec1879e78` | `test_case/input_data/preprocessed/*/LSresults_tot_20150812_1637.dat` |

A Scintrex CG-5 survey at Djougou, Benin, in September 2013, and pyGrav's
least-squares solution for four of its days, from the test case of

> B. Hector and J. Hinderer, *pyGrav, a Python-based program for handling and
> processing relative gravity data*, Computers & Geosciences, 2016,
> doi:10.1016/j.cageo.2016.03.010.

**pyGrav states no licence.** The CG-5 file GSadjust re-hosts came from pyGrav —
GSadjust's own readme says so — and GSadjust cannot have waived rights it never
held. So neither is committed. `scripts/check_rd07.py --fetch DIR` clones both at
the commits above and refuses any file whose SHA-256 differs from the one pinned
in the script, the way engine CI treats the ANTEX file; the `reference` workflow
does exactly that, and `tests/test_rd07.py` skips with that reason everywhere
the files have not been fetched.
