<!-- SPDX-License-Identifier: GPL-2.0-or-later -->
# GGAO triangle — three GNSS receivers, two hours, and a loop that says which hour to trust

*Em português: README.pt_BR.md. En español: README.es.md.*

Three permanent GNSS stations at NASA's Goddard Geophysical and Astronomical Observatory, in Greenbelt,
Maryland: **GODN**, **GODE** and **GODS**, a short walk apart, observing together on 1 January 2025. Two hours
of that day, each in its own folder:

| Folder | Hour (GPS time) | What it holds |
|---|---|---|
| `hour-00` | 00:00 to 00:59:30 | An ordinary hour |
| `hour-11` | 11:00 to 11:59:30 | The hour GeoComp's own validation found failing (`specs/22-reference-data-sources.md` §5.1) |

Each folder has the three stations' observations, `godn0010.25o`, `gode0010.25o` and `gods0010.25o`, and the
day's broadcast navigation file, `brdc0010.25n.gz`.

**The data is NOAA's.** It comes from the NOAA CORS Network, operated by the National Geodetic Survey; NASA
Goddard supplied the observations. Each observation file is NOAA's published file for the day, cut to the hour
and reduced to GPS and the eight observables a dual-frequency GPS solution reads. No value is changed, and
`scripts/make_ggao_triangle.py` rebuilds the files from NOAA's. `NOTICE.md` beside this file gives the
attribution and the terms.

The tutorial is about one check, the **loop closure**: three baselines round a triangle should add up to
nothing. It needs no published coordinate, and it says when a set of baselines disagrees with itself.

---

## Walking through it

### 1. Install tutorial dataset — `geocomp:project_tutorial_dataset`

If you are reading this in the folder it was installed into, this step is done. If not, it is in the menu
under *GeoComp ▸ Project*.

- **Dataset**: *ggao-triangle*
- **Destination folder**: a folder you can write to

### 2. Relative — Static — `geocomp:gnss_relative_static`

From the menu, *GeoComp ▸ GNSS ▸ Relative — Static*. The first side of the midnight triangle.

- **Folder of RINEX observations**: `hour-00`
- **Base station**: `GODN`
- **Rover station**: `GODE`
- **Solution**: `solutions-00/godn-gode.pos`, in a new folder beside `hour-00`

Leave the rest. The log says how it went:

> 120 epochs, 96.7% with resolved ambiguities

All but the first four epochs, while the solution settled, have their ambiguities fixed. The log also says what
the base is held at:

> Base GODN is not in the reference-station database, so RTKLIB holds it at the approximate position in its
> RINEX header, and the results are in no stated frame.

That is enough here: a closure needs the vectors between the stations, not where the stations are.

### 3. Relative — Static — `geocomp:gnss_relative_static`

The second side.

- **Folder of RINEX observations**: `hour-00`
- **Base station**: `GODN`
- **Rover station**: `GODS`
- **Solution**: `solutions-00/godn-gods.pos`

### 4. Relative — Static — `geocomp:gnss_relative_static`

The third side, the one that closes the triangle.

- **Folder of RINEX observations**: `hour-00`
- **Base station**: `GODE`
- **Rover station**: `GODS`
- **Solution**: `solutions-00/gode-gods.pos`

Each of the three fixes the same share of its epochs, 96.7%.

### 5. Build baselines — `geocomp:gnss_build_baselines`

From the menu, *GeoComp ▸ GNSS ▸ Build baselines*.

- **Folder of .pos solutions**: `solutions-00`
- **Baselines**: somewhere you can find it

> 3 baseline(s): 2 independent, 1 dependent

Two of the three baselines are enough to place the three stations; the third is *dependent*, and that is what
makes it a check. Going round the triangle on all three:

> Loop GODN → GODE → GODS → GODN closes to 0.37 mm over 282.2 m of baselines (1.33 ppm).

**The triangle closes to 0.37 mm.** Three vectors measured independently, each by its own run, agree with each
other to less than half a millimetre.

---

## The eleven o'clock hour

Now the same three runs on the other folder.

### 6. Relative — Static — `geocomp:gnss_relative_static`

- **Folder of RINEX observations**: `hour-11`
- **Base station**: `GODN`
- **Rover station**: `GODE`
- **Solution**: `solutions-11/godn-gode.pos`, in a new folder beside `hour-11`

> 120 epochs, 48.3% with resolved ambiguities

Half the epochs fixed, not 96.7%. The log says what the engine saw:

> Cycle slips detected by the engine: 6, on G21.

### 7. Relative — Static — `geocomp:gnss_relative_static`

- **Folder of RINEX observations**: `hour-11`
- **Base station**: `GODN`
- **Rover station**: `GODS`
- **Solution**: `solutions-11/godn-gods.pos`

> 120 epochs, 47.5% with resolved ambiguities

### 8. Relative — Static — `geocomp:gnss_relative_static`

- **Folder of RINEX observations**: `hour-11`
- **Base station**: `GODE`
- **Rover station**: `GODS`
- **Solution**: `solutions-11/gode-gods.pos`

> 120 epochs, 97.5% with resolved ambiguities

The side without GODN fixes as well as any side at midnight.

### 9. Build baselines — `geocomp:gnss_build_baselines`

- **Folder of .pos solutions**: `solutions-11`
- **Baselines**: somewhere you can find it

Before it closes the loop, it says what two of the baselines are made of:

> GODN-GODE is taken from an epoch whose ambiguities were not fixed (ambiguity ratio 1.0). A float baseline can be
> wrong by far more than its covariance says: process the session again, over a longer span, or leave it out.

And the same of GODN-GODS. Then:

> Loop GODN → GODE → GODS → GODN closes to 7.62 mm over 282.3 m of baselines (26.98 ppm).

**The triangle misses by 7.62 mm**, twenty times the midnight loop over the same ground. The hour's baselines
disagree with each other.

---

## What to take from it

- **A loop closure detects; it does not locate.** The loop says one of the three sides is wrong, not which.
  Here the runs themselves point: GODN's two sides fixed half their epochs, and a baseline is taken from the
  last epoch, which on both is not fixed, as *Build baselines* says. Process those two again — a longer span,
  another hour — before using them.
- **A loop that closes does not mean the stations are right.** An error common to both of a station's sides
  enters the loop twice, with opposite signs, and cancels. With GeoComp's default settings these runs apply no
  antenna calibration at all, and the midnight loop still closes to 0.37 mm, because each antenna's error is on
  two sides. When GeoComp's
  validation compared baselines like these with NGS's published coordinates, they disagreed by millimetres
  while the loops closed to a fraction of one (`specs/22-reference-data-sources.md` §5).
- **A fixed share is part of the answer.** The hour that did not close is the hour that did not fix. Read the
  quality figures before reading the coordinates.
