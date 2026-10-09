# RD-04 loop — a levelling loop that does not close, and why the adjustment cannot say where

**Reference dataset RD-04** (`specs/20-testing-and-validation.md` §3, FR-950, FR-952), the levelling tutorial.
*Em português: README.pt_BR.md. En español: README.es.md.*

Three lines of spirit levelling between three benchmarks — BM1 to BM2, BM2 to BM4 and back to BM1 — ten
setups and twenty staff readings, with sights balanced on every setup. One foresight on the line BM2 to BM4
was written down 12 mm wrong.

**This is constructed data, and it says so.** The readings were generated from heights chosen in advance —
BM1 100.000 m, BM2 103.750 m, BM4 106.480 m — with 0.3 mm of noise from a fixed seed, and then one reading was
spoiled. That is how the answer is known exactly, and how GeoComp's levelling is tested
(`tests/reference_levelling.py`). It is not a survey anyone walked.

The tutorial shows the loop failing to close, an adjustment that hides the error instead of finding it, and the
two known heights that find it.

---

## The files

| File | What it is |
|---|---|
| `loop.csv` | The field book: one row per staff reading — setup, point, `BS` or `FS`, the reading and the sight distance in metres, and the line |
| `mapping.json` | Which column feeds which field (FR-160) |
| `profiles.json` | The level: 0.5 mm on a staff reading, 0.7 mm per root kilometre. Without it GeoComp refuses to import rather than invent a precision |

---

## Walking through it

Each step's output document is the next step's input.

### 1. Import levelling field book — `geocomp:levelling_import`

- **Field book**: `loop.csv`
- **Field mapping**: `mapping.json`
- **Instrument profiles**: `profiles.json`

Ten setups in three lines, no row rejected. The layout is one row per reading, which is what a digital level
exports; GeoComp works that out from the columns the mapping names.

### 2. Equal sights — `geocomp:levelling_equal_sights`

- **Setups**: the document step 1 wrote
- **Instrument profiles**: `profiles.json`

Each line becomes one height difference with its uncertainty. The sights are balanced on every setup, so the
accumulated imbalance is zero and a collimation error cancels; the worst line, BM2 to BM4, carries 1.6 mm.

### 3. Closures and tolerances — `geocomp:levelling_closures`

- **Reduced lines**: the document step 2 wrote
- **Mode**: *Loop*
- **Tolerance coefficient k (m per root km)**: `0.008` — 8 mm √K, a common tolerance for ordinary levelling

The three height differences should sum to zero round the loop. They sum to **−15.7 mm**, against a permissible
**7.0 mm** for the loop's 0.76 km. **The loop fails.**

That is all a loop can say: something in it is wrong. It cannot say what, because every line contributes to the
one sum.

**Try this:** run it again with the tolerance coefficient at `0`. The misclosure is the same, and there is no
verdict, neither passed nor failed: GeoComp does not hold a loop to a tolerance nobody stated.

### 4. Levelling network adjustment — `geocomp:levelling_network`

Hold BM1 alone.

- **Reduced lines**: the document step 2 wrote
- **Benchmarks**: `BM1=100.000`
- **Tolerance coefficient k (m per root km; 0 judges nothing)**: `0.008`
- **Uncertainty per root kilometre (m)**: `0.0007`, the level's own figure

The adjustment runs. Before adjusting, it closes each line that runs between two known heights, and with only
BM1 known there is none; a loop is the closures algorithm's to judge, and the adjustment's own check on it is
the global test (`specs/10` §3). Three height differences, two unknown heights: **one degree of freedom.** The
global test fails, with an a-posteriori variance factor of **662**: the data disagree with their stated
precision by far more than chance allows.

**Now look for the culprit.** Data snooping tests each line's residual, and every one of them scores **1.00**,
below the critical value of 1.96, so **no outlier is named.** It is not that the test missed it. With one
degree of freedom there is one residual's worth of information, and it is shared among the three lines in
proportion to their length: 3.7 mm on BM1 to BM2, 10.3 mm on BM2 to BM4, 1.7 mm on BM4 back to BM1. Any one of
them could hold the blunder and the residuals would look the same.

The heights are wrong as well, and nothing in them says so: BM2 comes out at 103.7525 m, **2.5 mm** from where it
is. The adjustment has hidden the error by spreading it.

### 5. The benchmarks that find it

Run the network adjustment again, giving the **Benchmarks** as `BM1=100.000,BM2=103.750,BM4=106.480` — the
heights a benchmark register would publish for them.

GeoComp refuses:

> 1 closure(s) failed their tolerance: BM2-BM4. GeoComp does not adjust a line that failed its tolerance
> without an explicit acknowledgement. Re-run the line, or turn on 'Adjust lines that failed their tolerance'
> for this run or in Global Settings (Levelling).

With every line now running between known heights, each line closes on its own, and only **BM2 to BM4** fails.
That is the line to level again. The loop said something was wrong; the benchmarks said where.

**Try this:** turn on *Adjust lines that failed their tolerance* and run it once more. GeoComp refuses again,
for a different reason: with all three benchmarks held there is nothing left to estimate.

---

## What to take from it

- **A loop closure detects; it does not locate.** Neither does an adjustment with one degree of freedom, however
  carefully its statistics are computed.
- **An adjustment can make a blunder look like precision.** The heights in step 4 come with uncertainties of a few
  millimetres and are wrong by as much, which only a failed global test warned of.
- **Known heights are what locate an error**, by giving each line something of its own to close against.
