# RD-08 dam — two epochs of a monitored structure, and the one point that moved

**Reference dataset RD-08, its synthetic half** (`specs/20-testing-and-validation.md` §3, FR-950, FR-952), the
monitoring tutorial.

Four reference pillars on stable ground around a structure, R1 to R4, on a site 1200 m by 900 m, and five
targets on the structure itself, O1 to O5. Every pair of the nine is measured by distance, 36 distances at each
epoch, each to 1 mm. The network was measured in 2025 and again in 2026. In between, **O2 moved 8 mm east and
6 mm south.**

**This is constructed data, and it says so.** The distances were generated from positions chosen in advance,
with 1 mm of noise from a fixed seed at each epoch, and the motion was put into the second epoch's positions.
That is how the answer is known exactly, and how GeoComp's monitoring is tested (`tests/monitoring_network.py`).
It is not a structure anyone surveyed.

The tutorial adjusts each epoch, compares the two, finds O2, and then shows what happens when the stations
held as stable are not.

---

## The files

| File | What it is |
|---|---|
| `epoch-2025.json` | The first epoch, as measured: each station's approximate position and the 36 distances (a GeoComp network document) |
| `epoch-2026.json` | The second epoch, the same way |
| `thresholds.csv` | An alert threshold: 5 mm of motion on any of the five targets |

---

## Walking through it

### 1. Adjust network — `geocomp:analysis_network_adjust`

The first epoch, held on the four pillars.

- **Network document**: `epoch-2025.json`
- **Coordinate frame**: *2D — planimetric (easting, northing)*
- **Datum definition**: *Minimum constraint — over chosen stations*
- **Datum stations (comma-separated; empty = all)**: `R1,R2,R3,R4`
- **Solution**: `solution-2025.json`

Thirty-six distances and nine stations: **21 degrees of freedom.** The global test passes, with an
a-posteriori variance factor of **1.14**: the distances agree with each other as well as their 1 mm says they
should.

Data snooping lists **3** observations whose w-test exceeds the critical value of 1.94, the largest
**2.37**. They are noise. At 95 % confidence one good observation in twenty exceeds the critical value by
chance, and 36 of them give about two. GeoComp rejects none of them, and in monitoring that matters: an
observation removed because it disagrees with the others may be the motion you came to measure.

### 2. Adjust network — `geocomp:analysis_network_adjust`

The second epoch, the same way.

- **Network document**: `epoch-2026.json`
- **Coordinate frame**: *2D — planimetric (easting, northing)*
- **Datum definition**: *Minimum constraint — over chosen stations*
- **Datum stations (comma-separated; empty = all)**: `R1,R2,R3,R4`
- **Solution**: `solution-2026.json`

The global test passes again, with a variance factor of **1.18**. Nothing in either adjustment says that
anything moved. A single epoch cannot: the motion is between them.

### 3. Compare two epochs — `geocomp:monitoring_compare_epochs`

- **First epoch (solution)**: `solution-2025.json`
- **Second epoch (solution)**: `solution-2026.json`
- **Reference stations (comma-separated)**: `R1,R2,R3,R4`
- **Alert thresholds (CSV)**: `thresholds.csv`
- **Analysis document**: `comparison.json`
- **Monitoring report**: somewhere you can open it

From the menu, *GeoComp ▸ Analysis ▸ Compare two epochs* first shows whether the two solutions can be
compared at all: the same frame, stated epochs, the same stations. These can.

**The reference block is tested first**, because every displacement is measured against it. Its congruency test
gives **0.59** against a critical value of **2.44**: the pillars have not moved relative to each other. The
whole network's gives **16.07** against **1.91**: something else has.

**Significant motion at one station: O2**, by **10.8 mm**, 8.7 mm east and 6.5 mm south. Its test gives
**77.1** against **3.22**. It was moved by 10.0 mm; the other 0.8 mm is the noise of two epochs' measurement,
well inside its 95 % ellipse of **3.0 by 2.1 mm**. Of the other targets, the largest displacement is O3's
**2.0 mm**, and none is significant.

The alert threshold is crossed at O2 alone. It is a separate question from significance. A significant motion
smaller than the threshold is real but tolerable; a motion larger than the threshold that is not significant
cannot be told from noise, and the report says which is which.

**Try this:** adjust both epochs again with *Datum definition* at *Inner constraint — free network, trace
minimum*, which holds no station in particular, and compare them. The displacements come out the same, to the
tenth of a micrometre. The comparison transforms both epochs onto the reference block before it measures
anything, so the datum each epoch was adjusted in does not matter. **Which stations are the reference does.**

### 4. A reference block that has moved

Compare again, giving the **Reference stations (comma-separated)** as `R1,R2,R3,R4,O2`: as if O2 were a
pillar. GeoComp refuses:

> The reference block has moved: its congruency test gives 28.8678 against a critical value of 2.2371, and the
> localisation implicates O2. The analysis does not proceed on a block that has itself moved, because that
> motion would be spread over every other station. The stations that remain stable are R1, R2, R3, R4. Check
> the implicated pillars, then analyse again with them among the object points.

and says where it wrote the localisation. Held as stable, O2's 10.8 mm would have been shared among the other
four pillars and shown up, smaller and in the wrong direction, at every target on the structure.

---

## What to take from it

- **Motion is between epochs.** Each adjustment on its own passes, and has nothing to say about it.
- **The reference block is tested before anything is measured against it.** A pillar that moved and is held
  as stable moves everything else.
- **The datum of each epoch does not matter; the choice of reference stations does.**
- **Significant and alarming are different questions.** Significance is measured against the displacement's
  own uncertainty; a threshold is an engineer's limit.
- **Data snooping at 95 % flags good observations by chance.** GeoComp lists them and rejects none.
