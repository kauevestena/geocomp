<!-- SPDX-License-Identifier: GPL-2.0-or-later -->
# Solution-status fixture and RTKLIB's own dilutions of precision (P12c-35)

| File | What it is |
|---|---|
| `relative-static.pos.stat.gz` | The solution-status file (`out-outstat = residual`) `rnx2rtkp` wrote for RTKLIB's sample baseline -- rover `07590920.05o`, base `30400920.05o`, broadcast `brdc_0759.05n` from [`../`](../PROVENANCE.md) -- under the configuration GeoComp writes for its `relative-static` profile. Gzipped with `gzip -9 -n`; 120 epochs, 1,500 `$SAT` lines. |
| `relative-static.dops.csv` | GDOP, PDOP, HDOP and VDOP of every epoch in that file, computed by **RTKLIB's own `dops()`** (`src/rtkcmn.c`) through [`scripts/rtklib_dops_reference.c`](../../../../scripts/rtklib_dops_reference.c), counting each satellite whose first-frequency line is flagged valid, with a zero cutoff. |

Both from RTKLIB-EX commit `06e8644`, the commit the plugin ships and the `.pos` fixtures were made by:

```console
$ python -c 'from geocomp.engines.rtklib.config import profile, write_config; write_config(profile("relative-static"), "rnx2rtkp.conf")'
$ rnx2rtkp -k rnx2rtkp.conf -o relative-static.pos 07590920.05o 30400920.05o brdc_0759.05n
$ cc -O2 -I$RTKLIB/src -DENAGLO -DENAQZS -DENAGAL -DENACMP -DENAIRN -DNFREQ=4 -DNEXOBS=3 \
     scripts/rtklib_dops_reference.c $RTKLIB/src/rtkcmn.c $RTKLIB/src/trace.c -lm -o dops-reference
$ ./dops-reference relative-static.pos.stat > relative-static.dops.csv
```

**Why RTKLIB's function and not a second computation.** The test compares GeoComp's DOP with the engine's
definition of it, applied by the engine's code, so an error in GeoComp's arithmetic or in its reading of the
`$SAT` layout fails it. A table computed by GeoComp itself would agree with GeoComp whatever it did.

The sample stations have no published coordinates, as [`../PROVENANCE.md`](../PROVENANCE.md) says; that does not
matter here, because DOP depends only on which satellites were used and where they were in the sky.
