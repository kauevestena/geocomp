# Combined survey, Curitiba — GNSS and a total station adjusted together, and the one that overstated its precision

The integration tutorial (`specs/13-module-integration.md`, FR-952).

Six stations over about 3 km near Curitiba. GNSS baselines tie two control marks, CTB1 and CTB2, to the other
four, processed in ITRF2014 at 2020.0. A total station occupies four of the stations and measures directions,
zenith angles and slope distances to every station it can see, with one more angle and one azimuth: 44
observations, in no frame at all, as a total station has none.

The total station states its precision as 2 mm on a distance, 1.5″ on a direction and 3″ on a zenith angle.
**It measured three times worse than that.**

**This is constructed data, and it says so.** Every measurement was computed from positions chosen in advance
and perturbed with a fixed seed; the total station's with three times its stated standard deviations. It is
the survey GeoComp's integration is cross-validated on against DynAdjust (`tests/combined_network.py`,
`specs/07` §6.3), with that one change. Nobody walked it.

---

## The files

| File | What it is |
|---|---|
| `gnss.json` | The GNSS baselines and an ellipsoidal height, in ITRF2014 at 2020.0, with CTB1 and CTB2 at their known positions (a GeoComp network document) |
| `total-station.json` | The total station's observations, with no frame (a network document) |

---

## Walking through it

### 1. GNSS and total station — `geocomp:integration_gnss_total_station`

- **GNSS network (from Build baselines)**: `gnss.json`
- **Total station network (from Classical network)**: `total-station.json`
- **Frame to combine in**: *ITRF2020*
- **Fixed stations (comma-separated)**: `CTB1,CTB2`
- **Estimate a variance component per technique**: off

The two inputs are combined in ITRF2020: the GNSS baselines carried from ITRF2014, the total station's
observations given each station's own vertical. The log says so: *Combined 2 inputs (gnss, total_station) in
ITRF2020; 7 transformation(s) applied.*

**41 degrees of freedom, and the global test fails**, with a variance factor of **5.80**. Something in the
combined survey disagrees with its stated precision. The global test cannot say what. The log breaks it down
by technique, though:

> GNSS: 5 observation(s), 20.6% of the redundancy, vᵀPv/r 1.375. Total station: 44 observation(s), 79.4% of
> the redundancy, vᵀPv/r 6.950.

Each technique's weighted squared residuals over its share of the redundancy: **6.950 for the total
station**, against 1.375 for the GNSS. It is a quick reading of how a technique's weights fit, and the report
says so; it is not yet a variance component, which the next step estimates.

### 2. GNSS and total station — `geocomp:integration_gnss_total_station`

The same, letting the data weigh each technique.

- **GNSS network (from Build baselines)**: `gnss.json`
- **Total station network (from Classical network)**: `total-station.json`
- **Frame to combine in**: *ITRF2020*
- **Fixed stations (comma-separated)**: `CTB1,CTB2`
- **Estimate a variance component per technique**: on

The report's *Techniques* section, under *Variance components*, gives the total station a component of **7.19 ± 1.76** and the
GNSS **0.56 ± 0.46**. A component is the factor a technique's stated variances are multiplied by: the total
station's standard deviations were understated by about **2.7** times, where the survey was made with 3, and
the GNSS's are about right, the 1 in its component being inside its uncertainty.

The global test now passes, and that tells you nothing: the components were estimated so that it would. What
is information is the components themselves, and that the total station's weight in the solution is now the
one it earned. Its share of the redundancy goes from 79.4 % to **88.5 %**.

---

## What to take from it

- **A combined adjustment's global test says that something disagrees, not which technique.** The breakdown
  by technique says which.
- **Variance components weigh each technique by what it measured, not by what it claimed.** They are an
  estimate with their own uncertainty, and they need redundancy within each technique to be estimable.
- **After variance components, a passing global test is not evidence.** The components are.
