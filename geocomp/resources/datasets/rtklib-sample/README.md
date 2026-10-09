<!-- SPDX-License-Identifier: GPL-2.0-or-later -->
# RTKLIB sample baseline — a GNSS session you can run in two minutes

*Em português: README.pt_BR.md. En español: README.es.md.*

Two receivers that observed at the same time on 2 April 2005, 3.3 km apart, and the broadcast ephemeris for
the day. It is **RTKLIB's own sample data**, copied unmodified from the RTKLIB-EX repository at commit
`06e8644`; RTKLIB is BSD 2-clause licensed and its notice is in `RTKLIB-license.txt` beside this file.

| File | What it is |
|---|---|
| `30400920.05o` | Station `3040`, `RINEX 2.10`, GPS, 30 s. **The base.** |
| `07590920.05o` | Station `0759`, same day, same receiver and antenna model. **The rover.** |
| `brdc_0759.05n.gz` | The broadcast navigation file for that day. GeoComp reads it gzipped. |

---

## Walking through it

### 1. Install tutorial dataset — `geocomp:project_tutorial_dataset`

If you are reading this in the folder it was installed into, this step is done. If not, it is in the menu
under *GeoComp ▸ Project*.

- **Dataset**: *rtklib-sample*
- **Destination folder**: a folder you can write to

### 2. Relative — Static — `geocomp:gnss_relative_static`

From the menu, *GeoComp ▸ GNSS ▸ Relative — Static*.

- **Folder of RINEX observations**: the folder step 1 installed
- **Base station**: `3040`
- **Rover station**: `0759`
- **Solution**: somewhere you can find it
- **Quality summary**: somewhere you can find it
- **Solution epochs (layer)**: let it load

Leave the rest. `rnx2rtkp` runs. **You do not need to install it:** GeoComp carries its own, and the log
says *Using RTKLIB-EX* `2.5.1` and where it is.

## What you should see

**120 epochs** over the first hour (00:00 to 00:59:30), **117 of them with the ambiguities fixed** and three
float. The log puts it as:

> 120 epochs, 97.5% with resolved ambiguities

The log says, of each station's observations, that the navigation file's name does not say which day it is
for:

> no navigation file's name states this session's day, so every navigation file in the folder (1) is
> offered to it. Name the navigation files by their day, or keep only this session's in the folder.

That is expected here, and harmless: there is only one navigation file, and it is the right one.

And it says what the base is held at:

> Base 3040 is not in the reference-station database, so RTKLIB holds it at the approximate position in its
> RINEX header, and the results are in no stated frame.

## What this does not show

**The pipeline, not the accuracy.** These two stations have no published official coordinates that this
project can reach, so the baseline is held at the approximate position in its header, and nothing here says the
coordinates are right. What it shows is the whole chain running — session discovery, the engine, the
solution reader, the quality figures, the map layer — and the ambiguities resolving. The dataset that would
validate the accuracy is RD-06 (`specs/22-reference-data-sources.md` §5).
