<!-- SPDX-License-Identifier: GPL-2.0-or-later -->
# RTKLIB sample baseline — a GNSS session you can run in two minutes

Two receivers that observed at the same time on 2 April 2005, 3.3 km apart, and the broadcast ephemeris for
the day. It is **RTKLIB's own sample data**, copied unmodified from the RTKLIB-EX repository at commit
`06e8644`; RTKLIB is BSD 2-clause licensed and its notice is in `RTKLIB-license.txt` beside this file.

| File | What it is |
|---|---|
| `30400920.05o` | Station `3040`, RINEX 2.10, GPS, 30 s. **The base.** |
| `07590920.05o` | Station `0759`, same day, same receiver and antenna model. **The rover.** |
| `brdc_0759.05n.gz` | The broadcast navigation file for that day. GeoComp reads it gzipped. |

## Run it

1. **Install the dataset** if you have not: toolbox ▸ GeoComp ▸ *Install tutorial dataset*, dataset
   `rtklib-sample`, and a folder you can write to.
2. **GeoComp ▸ GNSS ▸ Relative — Static.**
   - *Folder of RINEX observations*: the folder you just installed.
   - *Base station*: `3040`. *Rover station*: `0759`.
   - Leave the rest. Write the solution and the quality summary somewhere you can find them, and let the
     *Solution epochs* layer load.
3. `rnx2rtkp` runs. **You do not need to install it:** GeoComp carries its own, and the run's log says
   *Using RTKLIB-EX 2.5.1* and where it is.

## What you should see

- **120 epochs** over the first hour (00:00 to 00:59:30), **117 of them with the ambiguities fixed**
  (97.5 %) and three float.
- A log line that the navigation file was *paired by fallback*: its name states no date. That is expected
  here and harmless; there is only one navigation file.
- A log line that base `3040` **is not in the reference-station database**, so it is held at the
  approximate position in its RINEX header, and the results are **in no stated frame**.

## What this does not show

**The pipeline, not the accuracy.** These two stations have no published official coordinates that this
project can reach, so the baseline is held at the approximate position in its header, and nothing here says the
coordinates are right. What it shows is the whole chain running — session discovery, the engine, the
solution reader, the quality figures, the map layer — and the ambiguities resolving. The dataset that would
validate the accuracy is RD-06 (`specs/22-reference-data-sources.md` §5).
