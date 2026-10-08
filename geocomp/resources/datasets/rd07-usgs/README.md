# RD-07 USGS — a gravity network whose answer someone else published, and a meter that reads 3 % high

**Reference dataset RD-07, its USGS half** (`specs/20-testing-and-validation.md` §3,
`specs/22-reference-data-sources.md` §5.6, FR-950, FR-952), the gravimetry tutorial.

Two relative-gravity surveys of five stations, sta1 to sta5, each station visited two or three times in one
afternoon with meter B44, eleven readings a survey. They are **USGS's synthetic test surveys for GSadjust**,
copied unmodified from the GSadjust repository at commit `17bb3ca`. USGS generated them from a truth it
published beside them, so the answer is known and is not GeoComp's own:

| | sta1 | sta2 | sta3 | sta4 | sta5 | Drift | Meter scale |
|---|---|---|---|---|---|---|---|
| **Truth**, mGal | 50.000 | 48.000 | 45.000 | 48.500 | 46.000 | | |
| `Test2.txt` | | | | | | 0.01 mGal per hour | correct |
| `Test3.txt` | | | | | | 0.01 mGal per hour | **reads 3 % high** |

Each reading carries 3 µGal of noise. The files are public domain in the United States and dedicated worldwide
under CC0; `GSadjust-LICENSE.md` beside them says so.

---

## The files

| File | What it is |
|---|---|
| `Test2.txt`, `Test3.txt` | The two surveys, in the Burris export format GeoComp reads |
| `profiles.json` | Meter B44: 3 µGal a reading, tide already removed, **no calibration** — as a meter is before anyone has measured its scale |
| `profiles-calibrated.json` | The same meter with the calibration Test 3 was generated with: a factor of 1/1.03 |
| `GSadjust-LICENSE.md` | USGS's licence for the surveys |

---

## Walking through it

### 1. Pre-processing (scale, tide, drift) — `geocomp:gravimetry_preprocess`

- **Gravimeter file**: `Test2.txt`
- **Gravimeter profiles**: `profiles.json`
- **Precision floor (mGal)**: `0`
- **Reduced readings**: `test2.json`

Eleven readings, eleven occupations, one session. A Burris export states neither a precision nor a time zone,
and the log says what was assumed for each: the profile's 3 µGal, and UTC. It also fits the drift to the three
readings of sta1 alone, the base: **0.01008 ± 0.00142 mGal per hour**.

### 2. Gravimetric network adjustment — `geocomp:gravimetry_network`

- **Reduced readings**: `test2.json`
- **Known gravity (mGal)**: `sta1=50.000`
- **Drift treatment**: *Estimated with the station values*

The adjustment has **5 degrees of freedom**, and the global test passes with a variance factor of **1.17**. The drift is estimated with the stations, from every reading rather than the
base's three: **0.00915 ± 0.00109 mGal per hour**, against the 0.01 USGS put in.

And the stations come back as USGS published them. sta2 is **1.3 µGal** from its truth, sta3 **2.6**, sta4
**0.9** and sta5 **2.0**, each within its own standard deviation of about 3 µGal.

### 3. Pre-processing (scale, tide, drift) — `geocomp:gravimetry_preprocess`

The second survey, with the same profile.

- **Gravimeter file**: `Test3.txt`
- **Gravimeter profiles**: `profiles.json`
- **Precision floor (mGal)**: `0`
- **Reduced readings**: `test3.json`

### 4. Gravimetric network adjustment — `geocomp:gravimetry_network`

This time sta3's gravity is known too, as an absolute meter would give it.

- **Reduced readings**: `test3.json`
- **Known gravity (mGal)**: `sta1=50.000,sta3=45.000`
- **Drift treatment**: *Estimated with the station values*

**The global test fails**, with a variance factor of **525**. The meter's differences do not fit between two
values that are both known.

**Try this:** hold sta1 alone, `sta1=50.000`. The global test passes, with a variance factor of **1.51**,
and sta3 comes out at **44.846 mGal**, **154 µGal** from its truth. Nothing in the adjustment says so. A
meter that reads every difference 3 % high is self-consistent: each difference is wrong in proportion, the
network closes, and the residuals are those of a correct survey. Run it again with
`profiles-calibrated.json` and the variance factor is the same, 1.51, to every digit shown.

### 5. Pre-processing (scale, tide, drift) — `geocomp:gravimetry_preprocess`

The second survey again, with the meter's calibration.

- **Gravimeter file**: `Test3.txt`
- **Gravimeter profiles**: `profiles-calibrated.json`
- **Precision floor (mGal)**: `0`
- **Reduced readings**: `test3-calibrated.json`

### 6. Gravimetric network adjustment — `geocomp:gravimetry_network`

- **Reduced readings**: `test3-calibrated.json`
- **Known gravity (mGal)**: `sta1=50.000,sta3=45.000`
- **Drift treatment**: *Estimated with the station values*

The global test passes, with a variance factor of **1.56**, and the three unknown stations are within
**2.5 µGal** of their truth.

---

## What to take from it

- **A network checks the meter's consistency, not its scale.** A calibration error leaves every statistic as
  it was; only something that knows the size of a difference can find it, such as a second absolute value or
  a calibration line.
- **One known station gives a datum and nothing to check it against.** Two give the scale a test.
- **Drift is estimated more precisely from every reading than from the base's alone** (±0.00109 against
  ±0.00142 mGal per hour here), and GeoComp estimates it with the stations unless told otherwise.
