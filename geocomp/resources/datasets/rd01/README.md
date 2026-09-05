# RD-01 — a total-station triangle, with two real errors in it

**Reference dataset RD-01** (`specs/20-testing-and-validation.md` §3, FR-950, FR-952).

Three stations, six pointings, each observed on both faces of the instrument. It is
the smallest complete total-station survey there is, and it exercises the whole of
GeoComp's first vertical slice: field-book import, face reduction, the basic
reductions, network assembly, statistical testing and adjustment.

It is also **real data with two real errors in it**, and that is why it is the
tutorial. A tutorial in which nothing is wrong teaches you which buttons to press.
This one teaches you what the software is for.

---

## The files

| File | What it is |
|---|---|
| `raw_data.csv` | The field book as recorded: station, backsight, foresight, face, sexagesimal angles, slope distance, instrument and target heights |
| `mapping.json` | Which column feeds which field (FR-160). Defined once, reusable for every export from the same instrument |
| `profiles.json` | The instrument's nominal precisions. Without one, GeoComp refuses to import rather than inventing a sigma |
| `approximate.json` | Starting coordinates for the adjustment, in a local frame with station 1 at the origin |

The coordinates are local, not projected. RD-01 has no known point and no measured
azimuth, so nothing ties it to a datum — see *The network is free* below.

---

## Walking through it

Each step's output document is the next step's input, so the whole tutorial also
assembles as one model in the graphical modeller.

### 1. Import field book — `geocomp:totalstation_import_fieldbook`

- **Source**: `raw_data.csv`
- **Field mapping**: `mapping.json`
- **Instrument profiles**: `profiles.json`

Twelve records, three setups, none rejected. Every reading comes out with an
uncertainty attached, taken from the instrument profile: uncertainties are attached
at the boundary, because a value that enters the system without one can never
honestly acquire one later.

**Try this:** run it again without the profiles. It refuses, and says what it needs.
GeoComp will not invent a standard deviation, because a made-up sigma propagates
through every later number and turns an unknown quality into a stated one.

### 2. Generalised pre-processing — `geocomp:totalstation_preprocess`

- **Readings**: the document step 1 wrote
- **Instrument profiles**: `profiles.json` again

The profiles are needed a second time, and that is not an oversight: the readings
record *which* instrument took them, and reducing a face pair needs that
instrument's collimation, vertical index and EDM constants. GeoComp will not
substitute another instrument's — it refuses and names the one it was looking
for, because a silent substitution would make every number after it wrong in a
way nothing could detect.

Six pointings reduced from twelve face readings. **Five are usable and one is
blocked**, and the blocked one is the first real error:

> the two faces of the pointing from station 3 to station 2 disagree in distance by
> 1.000 m

A face pair measures the same line twice. The angles agree to seconds; the distances
differ by a round metre. That is not noise, it is a transcription error — a digit
written down wrong in the field book. Averaging the two would bury a half-metre
error in the mean and produce a plausible, wrong distance. GeoComp blocks the
pointing and says why, and the remaining five carry on.

**Look at the report.** The collimation and vertical-index errors are estimated from
the face pairs themselves and reported per setup, which is what the second face is
for: observing both faces cancels them, and their size tells you whether the
instrument needs adjusting.

### 3. Classical network — `geocomp:totalstation_network`

- **Reduced observations**: the document step 2 wrote
- **Approximate coordinates**: `approximate.json`
- **Dimension**: 2D
- **Datum definition**: inner constraint
- **CRS**: `EPSG:31982` (UTM 22S), or the projected CRS of your own area

RD-01's coordinates are local, but a CRS is still required and GeoComp will not
invent one: adjusted coordinates are meaningless without knowing what they are
coordinates *in*, and a guess would be recorded on the solution as though someone
had chosen it.

The adjustment converges and **the global test fails**. That is the correct answer,
and the second thing this dataset teaches.

The distances between stations disagree by about 15 mm depending on which end they
were measured from, against the 2 mm precision the instrument profile claims. The
global test compares the residuals against the stochastic model, and the model says
the data should be better than it is. Something is wrong: either the instrument is
less precise than stated, or the centring was worse than assumed, or there is a
smaller blunder still in there. A test that passed here would not be testing
anything.

**Look at the residuals layer.** The observations are coloured by what the w-test
decided about each, and no observation was removed — GeoComp reports candidates and
leaves the decision to you (FR-255). Rejecting a measurement is a judgement about
the survey, not an arithmetic step.

### 4. The map

Ask step 3 for the result layers. They arrive styled: stations sized by their
positional uncertainty, error ellipses, residuals by significance, the network by
observation type, and the correction vectors.

**The ellipse layer's name states its exaggeration factor.** A 2 mm semi-axis is
invisible at any map scale, so drawn ellipses are always enlarged, and an
exaggeration that is not stated turns a quality visualisation into a
misrepresentation. Change the factor and watch the name change with it.

---

## The network is free

RD-01 contains no known point, no measured azimuth and no fixed height. Its datum
defect is therefore **three**: two translations and a rotation. Distances fix the
scale; nothing fixes where the triangle is or which way it faces.

A free network can only be adjusted with inner or minimum constraints. That is not a
limitation of the software, it is a property of the data: the survey genuinely does
not know where it is. Try the adjustment with *Fixed stations* naming station 1 and
compare — the residuals and the variance factor are identical, and only the
coordinates move. Which is the lesson: the constraint chooses a frame, it does not
add information.

---

## The third error, which is not in the data

`processed_data.csv` in the repository's `topo_test/` folder is the output of the
prototype notebook this dataset came from, and **one of its six reduced directions
is 180° out**. The prototype averaged the two faces arithmetically. Directions are
circular: the two faces of a pointing differ by about 180°, so their arithmetic mean
lands halfway between them rather than on either, and for one pointing here that
lands exactly half a turn from the truth.

It is established two ways, not asserted. The published value gives a triangle whose
interior angles sum to 38.24° instead of 180°, and implies a 2–3 distance of 4.43 m
against the 24.35 m that was measured. Both checks are in
`tests/test_reference_total_station.py`.

GeoComp reduces faces circularly and gets 199.110°, where the prototype published
19.110°. If you are comparing GeoComp's numbers against that file, this is the one
line that will not match, and GeoComp is right.
