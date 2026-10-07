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

## `slip-and-outlier.pos.stat.gz` -- a run with faults put in (P12c-36)

The same baseline, configuration and commit, with the rover file changed first by
[`tests/gnss_faults.py`](../../../gnss_faults.py)'s `SLIP_AND_OUTLIER`: five cycles added to G20's L1 phase and three
to its L2 from the file's 60th epoch (00:30:00) to its end -- a cycle slip, with no loss-of-lock flag set -- and
500 m added to both of G19's pseudoranges at the 90th (00:45:00) alone -- an outlier. The sample has neither of
its own, so this is the only way to know where the engine *should* find them. Gzipped with `gzip -9 -n`; 120
epochs, 1,500 `$SAT` lines.

```console
$ python -c 'from tests.gnss_faults import SLIP_AND_OUTLIER, with_faults; import pathlib; \
    rover = pathlib.Path("tests/data/rtklib/07590920.05o").read_text(); \
    pathlib.Path("07590920.05o").write_text(with_faults(rover, SLIP_AND_OUTLIER))'
$ rnx2rtkp -k rnx2rtkp.conf -o slip-and-outlier.pos 07590920.05o 30400920.05o brdc_0759.05n
```

The engine flags the slip on both of G20's carriers at 00:30:00 and nowhere else, and rejects both of G19's
signals at 00:45:00 and nowhere else -- its rejection counter reads 3 there, one for each pass it made over the
residuals that epoch. `tests/test_cycle_slips.py` reads this file and requires exactly that; its tier-4 class
puts the same faults in and runs the engine live.
