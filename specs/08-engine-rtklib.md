# 08 — Engine: RTKLIB / `rnx2rtkp`

**Status:** Draft
**Requirements covered:** FR-164, FR-300…FR-306, FR-350…FR-359, FR-604, NFR-010.
**Source:** O3; tex §Integração com o rnx2rtkp (RTKLIB); §Posicionamento pelo GNSS.

**Upstream references.** [RTKLIB (Takasu)](https://www.rtklib.com/) ·
[RTKLIB-EX / demo5 (rtklibexplorer)](https://github.com/rtklibexplorer/RTKLIB) ·
RTKLIB manual (2.4.x) · `manual_demo5.pdf` for the fork.

> **Verification note.** Statements marked **[V]** were verified upstream during specification; **[C]** must
> be confirmed against the RTKLIB manual when the module is implemented (roadmap P7).
>
> **Discharged in P7.** The one **[C]** in this document — §7's column set — has been confirmed, and against
> something better than the manual: `src/solution.c` at commit `06e8644` (`rnx2rtkp ver.EX 2.5.1`), the code
> that writes the file, cross-checked by running the engine in every output format and comparing what came
> out. It is now **[V]**, with the table in §7. Two things that confirmation found are recorded there and in
> §2 because neither is in any manual: the cross-covariance columns are *signed square roots*, and one of the
> column headers is **wrong upstream**.

---

## 1. Which RTKLIB

The proposal names the **`rnx2rtkp` utility from the RTKLIB-EX distribution** (`00-dados.tex`, abstract).

RTKLIB-EX (formerly "RTKLIB demo5") is a fork of Takasu's RTKLIB, based on RTKLIB 2.4.3, optimised for
low-cost GNSS receivers and maintained at `github.com/rtklibexplorer/RTKLIB` **[V]**.

> **Source-document note.** `research_project/referencias.bib:119` cites the `rtklib_explorer` entry with the
> URL `https://github.com/tomojitakasu/RTKLIB` — that is Takasu's *original* repository, not the
> rtklibexplorer fork the text names. This is a citation defect in the research project, not a design
> question; it should be corrected there. It is recorded here so the discrepancy is not mistaken for a
> deliberate choice.

**GeoComp targets `rnx2rtkp` from both distributions.** The command-line interface and the output formats are
compatible, so the adapter is one adapter with a distribution and version identifier attached (FR-302). Where
behaviour diverges, the version record is what makes the divergence explicable.

---

## 2. Command-line interface

Verified option set **[V]**:

| Flag | Meaning |
|---|---|
| `-k <file>` | Read options from a configuration file |
| `-o <file>` | Output file |
| `-ts`, `-te`, `-ti` | Start time, end time, time interval |
| `-p <mode>` | Positioning mode: `0` single, `1` dgps, `2` kinematic, `3` static, `4` moving-base, `5` fixed, `6` ppp-kinematic, `7` ppp-static |
| `-m <deg>` | Elevation mask |
| `-f <n>` | Number of frequencies (relative mode) |
| `-v <thres>` | Ambiguity resolution validation threshold |
| `-b`, `-c` | Backward solutions; forward/backward combined |
| `-i`, `-h` | Instantaneous ambiguity resolution; fix-and-hold |
| `-e`, `-a` | Output ECEF x/y/z; output ENU baseline |
| `-n`, `-g`, `-t`, `-u`, `-d`, `-s` | NMEA GGA output; lat/lon in d m s; time format; UTC; time decimals; field separator |
| `-r`, `-l` | Reference receiver position (ECEF; lat/lon/height) |
| `-y <level>` | Solution status output: `0` off, `1` states, `2` residuals |
| `-x <level>` | Debug trace level |

Mapping to the GNSS menu (FR-600, FR-601):

| Menu item | Mode |
|---|---|
| Absolute → Static | `-p 7` (ppp-static) |
| Absolute → Kinematic | `-p 6` (ppp-kinematic) |
| Relative → Static | `-p 3` (static) |
| Relative → Kinematic | `-p 2` (kinematic), with `-p 4` (moving-base) available in Advanced mode |

**GeoComp invokes with `-k <config>` as the primary mechanism** (FR-354), because a configuration file is
reproducible, storable in provenance, attachable to a bug report, and editable by the user in Advanced mode.
Command-line flags are used only where they have no configuration-file equivalent — in practice the inputs,
the output path and the time window.

### 2.1 A configuration file is not the same run as the equivalent flags [V]

**`rnx2rtkp -k <config>` and `rnx2rtkp -p 3` are not equivalent, and the difference is silent.** Loading a
configuration file rebuilds the whole processing option set from the option table, whose default base-station
position is `ant2-postype = llh` with `ant2-pos1/2/3 = 0` — latitude 0, longitude 0, height 0. The
command-line path instead leaves the base position to be taken from the base receiver's RINEX header.

So a generated configuration that does not state `ant2-postype` puts the base station in the Gulf of Guinea.
Measured on the sample pair in `tests/data/rtklib/`: with `ant2-postype = rinexhead`, 120 epochs and 117 of
them ambiguity-fixed; without it, **no solution at all**.

Two things make this worth a section rather than a code comment:

- The whole reason §2 prefers `-k` is that it is *reproducible*. Omitting this option would have made it
  reproducibly **wrong**, which is worse than a flag nobody recorded.
- It failed loudly here only because the default is 9 000 km away. A base station wrong by ten metres — an
  outdated published coordinate, a transcription slip — produces a solution that succeeds, looks ordinary,
  and is wrong by ten metres.

**Therefore: every configuration GeoComp writes states the base-station position type explicitly**, and
explicit base coordinates given with a position type that would ignore them are refused rather than accepted
and dropped.

### 2.2 `convbin` is broken at this commit [V]

Not a GeoComp deliverable, recorded so the next reader does not spend the afternoon on it. Converting
RINEX 2 to RINEX 3 — the obvious way to produce a RINEX 3 test file — aborts:

```console
$ convbin -r rinex -v 3.04 -o base.rnx 07590920.05o
scanning: 2005/04/02 00:59:00 G
*** buffer overflow detected ***: terminated
```

Reproducible with those flags alone, on RTKLIB's own sample data. GeoComp's RINEX 3 header support is
therefore tested against a fixture transcribed from the published format definition, and
`tests/data/rtklib/PROVENANCE.md` says so rather than letting a transcript pass for a tool's output.

### 2.3 The time window is the one option with no configuration key [V]

`RtklibJob.window` writes `-ts` and `-te`. It is a flag because RTKLIB's option table has no equivalent
key, which means a window is recorded in provenance **only** through the command line — so the command
line is stored whole rather than summarised. It is what lets a session be solved in parts: the RD-06
repeatability measurement in [`22`](./22-reference-data-sources.md) §5.1 splits two full days into hours
and takes the scatter of the results.

Two traps, both silent:

- **The date separator is a slash.** `rnx2rtkp` reads the bound with `sscanf("%lf/%lf/%lf")`, so an ISO
  `2025-01-01` parses as the year alone and the window becomes "2025, from January the first" — every
  epoch selected, no error, no warning.
- **Both bounds are GPST calendar labels, not UTC.** The engine compares them against observation times,
  which are GPST; so is `TIME OF FIRST OBS` in a GPS RINEX header and so are the labels the `.pos` reader
  returns. All four carry `tzinfo=UTC` for arithmetic and none of them is UTC. Converting one moves it by
  the leap seconds and selects a different interval, with nothing in the output to say so.

**Both bounds are inclusive.** `-te` selects the epoch that lands on it, so 06:00:00 to 07:00:00 at a
30 s interval returns 121 epochs, not 120, and two consecutive windows written from the same instant
share one. Measured, not read: the manual says nothing about it. A caller splitting a session into
disjoint parts ends each window one interval short.

A window that selects nothing is **refused rather than run**, because the engine's report of it is
indistinguishable from unusable observations: exit zero, a header, no records. So is a bound without
`tzinfo`, which would otherwise fail as a `TypeError` from comparing it against the session's own
times — an error that says nothing about which of the caller's two numbers is wrong.

---

## 3. Risk: PPP capability (FR-604)

The menu requires Absolute → Static and Absolute → Kinematic, that is PPP (`tex §Painel de Configuração
Global`, item 3). RTKLIB's PPP implementation is widely reported as substantially weaker than its relative
positioning, particularly in convergence behaviour and in the completeness of its correction models.

This is a real gap between what the menu promises and what the chosen engine delivers well. The proposal
anticipates exactly this situation:

> *"a arquitetura modular do GeoComp permitirá a incorporação futura de outros motores de processamento GNSS,
> conforme a demanda dos usuários e a evolução do projeto"* — `tex §Integração com o rnx2rtkp`

**How GeoComp handles it, in order:**

1. **Implement PPP through `rnx2rtkp` (`-p 6` / `-p 7`)** — it is the specified engine and it works for many
   purposes.
2. **State the limitation in the UI where PPP is selected** (FR-604), with the convergence time and expected
   quality, so no result is presented as better than it is. A silently degraded PPP solution used for a
   monitoring baseline is a real harm.
3. **Report solution quality prominently** (FR-603) so the user can judge the result rather than trust it.
4. **Keep the engine abstraction ready for an alternative** (FR-303). Candidates for a later phase include an
   adapter to an online PPP service or another open engine. This is *not* v1.0 scope
   ([`01-vision-and-scope.md`](./01-vision-and-scope.md) §5) and would need its own ADR.

**Rejected:** silently substituting relative processing for a PPP request, or shipping PPP without stating
its limitations.

---

## 4. Session discovery (FR-351, FR-164)

Scanning a folder produces `GnssSession` objects ([`04-data-model.md`](./04-data-model.md) §2.7).

**Read the header, do not trust the file name.** RINEX headers carry the marker name, receiver and antenna
type and serial, antenna height, observation interval and the first and last observation epochs. File-naming
conventions (both the short `ssssdddf.yyo` form and the long RINEX 3 form) are used only as a **fallback**
and as a cross-check — a mismatch between header and file name is surfaced as a warning, not silently
resolved, because a mis-attributed session produces a confidently wrong baseline.

Discovery also: pairs observation files with navigation files, groups sessions by day and by simultaneity
(which sessions can form a baseline at all), detects Hatanaka-compressed and archive-compressed files and
decompresses them into the working area, and reports files it could not interpret without aborting the scan
(FR-166).

**Antenna height is a first-class field, not metadata.** Its measurement method — vertical or slant, to which
antenna reference point — must be recorded, because an unrecorded slant height is one of the most common
sources of a systematic height error in GNSS work.

---

## 5. Products (FR-352, FR-353)

Precise ephemerides, clock products, ANTEX antenna models, DCB and ionosphere products as required by the
selected mode.

**Caller-supplied files in P7.** `RtklibJob.products` supplies positional orbit/clock inputs. ANTEX must
instead be named by `file-rcvantfile` and `file-satantfile` in `RtklibConfig.extra`; the pinned engine's
`src/postpos.c` loads antenna calibration through these configuration options, not the positional product
list. RD-06 exercises this path with explicit antenna types and offsets consistent with ARP truth
(`tests/test_rd06.py`, [`22`](./22-reference-data-sources.md) §5). Automatic resolution remains deferred.

**Resolution order** for each session: the local cache → the configured product directory (FR-063) → download
from a configured service. Cached products are keyed by product type, GNSS week/day, analysis centre and
latency class (ultra-rapid / rapid / final), so that a later re-run with final products is a deliberate,
visible change rather than an accidental one.

**Services** are configurable (FR-063) — IGS data centres, CDDIS, BKG, IBGE and others. The following are
requirements, not implementation notes:

- **Credentials go through the QGIS authentication system** (FR-353). Several major archives require login.
  Credentials are never written to a configuration file, a log, a provenance record or an exported file
  (NFR-010).
- **Downloads use the QGIS network stack**, so the user's proxy configuration is honoured
  ([`03-architecture.md`](./03-architecture.md) §3.7).
- **Availability is checked before a batch starts.** Products for a recent session may not exist yet; the
  user is told which sessions lack which products *before* a long batch begins, with the option to proceed
  with a lower-latency product class, recorded in provenance.
- **Every product used is recorded in provenance** by name, source and checksum (FR-134, NFR-007). A GNSS
  solution is not reproducible without knowing which orbit file produced it.

---

## 6. Execution (FR-355)

Single-session and batch. Batch requirements:

- One session's failure does not abort the batch; it is recorded and reported in a summary at the end.
- Progress is determinate — sessions completed of sessions total (FR-008).
- Cancellation terminates the running process and leaves completed sessions intact.
- Sessions run sequentially by default, with optional bounded parallelism in Advanced mode.
- Every run's configuration file, command line, stdout, stderr, exit code and product set are retained
  (FR-036, FR-304).

### 6.1 Comparative configuration testing (FR-359)

The proposal asks for the ability to evaluate the effect of processing choices — atmospheric models,
solution type, filtering strategy — on the same data. GeoComp implements this as: run the same session under
*n* named configurations, then present the solutions side by side with their differences and quality
indicators, and export the comparison.

This is a first-class feature, not a scripting exercise: it is one of the clearest pedagogical tools in the
plugin, and it is how a researcher answers "does this setting matter for my data?"

---

## 7. Output parsing (FR-356, FR-206)

The `.pos` solution file carries, per epoch: time, position (in the configured representation — ECEF,
geodetic, or ENU baseline), the quality flag Q, satellite count, the standard deviations of the position
components, the corresponding covariance terms, age of differential, and the ambiguity ratio factor.

### 7.1 The column set, confirmed [V]

Established from `src/solution.c` at commit `06e8644` — `outecef`, `outpos`, `outenu` and `outsolheads` —
and confirmed by running the engine in each format over one dataset and comparing the output.
`tests/data/rtklib/pos/` holds one fixture per row below, and `scripts/check_rtklib_fixtures.py` re-derives
them from a live engine so this table cannot quietly go stale.

Every format is **fourteen columns** of the same shape — two of time, three of position, Q, satellite count,
three standard deviations, three cross terms, age, ratio — with two exceptions: `-g` splits the latitude and
longitude into degrees, minutes and seconds (seven position columns), and the velocity option appends nine.

| Format | Flag | Position | Deviations | Cross terms, **as written** | Header labels |
|---|---|---|---|---|---|
| Geodetic | default | lat, lon, h | n, e, u | N–E, E–U, N–U | `sdne sdeu sdun` ✔ |
| Geodetic, sexagesimal | `-g` | lat, lon as d/m/s | n, e, u | N–E, E–U, N–U | `sdne sdeu` **`sdue`** ✘ |
| ECEF | `-e` | x, y, z | x, y, z | X–Y, Y–Z, Z–X | `sdxy sdyz sdzx` ✔ |
| ENU baseline | `-a` | e, n, u | e, n, u | E–N, N–U, E–U | `sden sdnu sdue` ✔ |

**The deviation triple and the cross triple do not run in the same order as each other in any format**, and
the cross triple's order differs between formats. The pairing is positional, not nominal.

### 7.2 The cross columns are signed square roots [V]

`sqvar(covar)` is `covar < 0 ? -sqrt(-covar) : sqrt(covar)` (`solution.c:132`). A printed `-0.6097` is
therefore neither a covariance nor a correlation: **the covariance is `-0.6097²`, with the sign restored**.

This is the whole of FR-206 for this engine, and nothing in the file says it. Getting it wrong has two
distinct failure modes, both silent:

- **Squaring without restoring the sign** turns every negative covariance positive. The north–up and east–up
  terms are routinely negative in a levelled solution, so the resulting error ellipse leans the wrong way.
- **Using the printed value as a covariance** is wrong by a square — at these magnitudes, by three orders.

### 7.3 Reading the header is necessary and not sufficient [V]

The parser MUST read the file's own header rather than assuming a column order — and MUST NOT trust the
labels it finds there, because **one of them is wrong upstream**. With `-g`, RTKLIB labels the third cross
column `sdue` while writing the same `sqvar(Q[5])` — the **N–U** covariance — that the default format
correctly calls `sdun`. And `sdue` genuinely denotes E–U in the ENU format. The same label therefore means
two different things across formats, and in one of them it is wrong.

So: **the header decides the format, the format decides each column's meaning**, and the labels are compared
against what the format says they should be and *reported* rather than obeyed. `llh.pos` and `llh-dms.pos`
in the fixtures are the same solution written both ways, and their parsed covariances are identical to the
bit — which is the evidence that ignoring the wrong label is right.

**Covariance is preserved, not reduced** (FR-206). The per-epoch standard deviations *and* their
cross-component terms are read and assembled into a `Covariance`
([`05-uncertainty-and-covariance.md`](./05-uncertainty-and-covariance.md) §3.1). Discarding the
cross-component terms and keeping three standard deviations is a loss that silently misstates every
downstream statistic, and is forbidden.

Parsed into:

| Output | GeoComp type |
|---|---|
| Static session solution | `Solution` of kind `GNSS_PROCESSING`, one `AdjustedStation` with covariance |
| Kinematic trajectory | Time-ordered positions with per-epoch covariance and quality |
| Quality indicators | Q flag (fixed / float / single), satellite count, DOP, ratio, age (FR-603) |

**Solution quality is never silently discarded.** A float solution presented without its Q flag is a
misrepresentation; Q travels with the result into every layer, report and adjustment.

### 7.4 Two traps below the header, found in P7c **[V]**

Both were latent in the parser from P7 and were found when the trajectory layer needed a real coordinate out
of every format rather than only out of the ECEF one.

1. **`-g` writes seven position columns, and the last three are not a position.** §7.3's format table gives
   `llh_dms` seven columns — degrees, minutes and seconds of latitude, the same of longitude, then the
   height — and `PosEpoch.position` keeps all seven, because that is what the file says. Its *last three* are
   therefore the longitude's minutes, its seconds and the height: a plausible-looking triple that is not a
   coordinate. `_reference_position` already handled this for the `% ref pos` header and said so in its own
   docstring; below the header nothing did. `PosEpoch.decimal_position` is the accessor a caller that wants a
   coordinate uses, and it collapses the seven to three.
2. **A geodetic epoch pairs degrees with metres.** `PosEpoch.quantities()` put each component beside its own
   standard deviation in one `Quantity`. For the two geodetic formats the components are **degrees** of
   latitude and longitude while the deviations beside them are **metres** on the ground, so the result read
   as *35.16 degrees plus or minus 1.5 metres* — a value and an uncertainty in different quantities under one
   unit, which nothing downstream could have noticed. It now raises `pos_quantities_are_geodetic` and names
   `decimal_position` and `covariance` as the two things to use instead. The ECEF and ENU formats, whose
   components are metres like their deviations, are unaffected — and ECEF is what a baseline wants anyway.

Neither had reached a result: the only production caller is §8.1's baseline, which is ECEF-only by
construction and refuses any other format. They are recorded because "not reached yet" is a property of
today's callers, not of the code.

---

### 7.5 A missing antenna calibration is silent **[V]**

With `pos1-posopt2 = on`, `rnx2rtkp` looks each configured antenna up in the ANTEX. On a miss it
**clears the antenna name and carries on with no calibration for that receiver** — `postpos.c`:

```c
if (!(pcv=searchpcv(0,popt->anttype[i],time,pcvr))) {
    trace(2,"no receiver antenna pcv: %s\n",popt->anttype[i]);
    *popt->anttype[i]='\0';
    continue;
}
strcpy(popt->anttype[i],pcv->type);
```

The warning goes to `trace`, which writes nothing unless `-x` enabled a trace file. So the run exits
zero, the solution has the usual epoch count and ambiguity fixing, the formal covariance is unchanged,
and the answer is wrong by that antenna's phase-centre offset — centimetres for some antennas, and about
7 mm of height for the RD-06 pair.

Two further points the code above makes:

- **The lookup is not exact.** `searchpcv` requires every whitespace-separated token of the configured
  name to appear in the entry, then retries with the radome dropped. `AOAD/M_T        JPLA` therefore
  matches `AOAD/M_T        NONE` when the JPLA variant is absent — a real calibration, but a different
  one.
- **The header reports what was matched, not what was asked for**, because the matched entry's name is
  copied over the configured one. That makes `% antenna1` / `% antenna2` the only evidence available
  from an ordinary run.

**Therefore `PosSolution.antennas` reads those lines back**, by position (1 is the rover), keeping the
radome — splitting the name on whitespace would erase the distinction the line exists to show. An empty
name means no calibration was applied. RD-06 refuses a calibrated case whose antennas did not resolve
to the ones configured, as a *processing* error rather than an accuracy one: a calibrated case whose
calibration was skipped is not a calibrated case, and judging accuracy on it judges a mislabelled run.

---

## 8. Baseline construction (FR-602)

Turning GNSS solutions into observations the adjustment can use
([`11-module-gnss.md`](./11-module-gnss.md) covers the module-level behaviour; this section fixes the
engine-side contract).

1. **Prefer the engine's own baseline output.** A relative-mode run *is* a baseline determination; its ΔX, ΔY,
   ΔZ and their 3×3 covariance are what the adjustment wants. Extract these directly.
2. **Differencing two independently computed positions is a different and weaker thing** — it discards the
   correlation between them and overstates the baseline uncertainty. GeoComp offers it where no relative
   solution exists, marks the result `APPROXIMATE` with the `INDEPENDENCE_ASSUMED` strategy (FR-202, FR-203),
   and says so in the UI.
3. **The resulting baseline is a cluster** (FR-104) and reaches DynAdjust as a G or X measurement with its
   covariance intact ([`07-engine-dynadjust.md`](./07-engine-dynadjust.md) §4.3).
4. **Antenna height reduction to the mark** is applied explicitly, with its own uncertainty propagated
   (FR-204), and is recorded so it can never be applied twice.
5. **Correlations between baselines from a common session** are not invented. Where the engine does not
   provide them, they are absent and the result says so, rather than a fabricated correlation being
   supplied.

### 8.1 How the vector comes out of a `.pos` **[V]**

Confirmed in phase P7b by running the engine and comparing its own two output formats against each other.

**Use the ECEF format, and subtract.** `rnx2rtkp -e` writes the rover's absolute geocentric position per
epoch and the base in the `% ref pos` header; the base is held in relative mode, so the rover's covariance
*is* the baseline's and the vector is one subtraction:

```text
d = last_epoch_position - reference_position
```

Measured on the committed fixtures: `[2022.7707, −468.6291, 2610.2891]`, length **3335.3896 m**, against
**3335.3895 m** for the length of the independently computed ENU baseline in `enu.pos` — the same run in a
different format. **They agree to 0.05 mm.** No rotation, no projection, and nothing to undo.

The other formats are refused rather than converted (`pos_not_geocentric`): deriving a baseline from the LLH
or ENU output means inverting a projection or a rotation the engine has already applied, losing precision to
no purpose.

**The last epoch is the answer.** A static run writes the filter's state at every epoch, so the earlier ones
are a converging filter's guesses — `xyz.pos`'s first epoch is a float solution two metres out.

### 8.2 The printed covariance is worth about one significant figure **[V]**

Every deviation and cross column is written `%8.4f`, so 0.1 mm. At the sub-centimetre magnitudes a fixed
static solution reaches, that is one or two significant figures and the covariance built from them is
uncertain by several per cent. `covariance_from_printed` (`core/uncertainty.py`) exists for exactly this —
**but the half-width it is given is not the printing's half-width**, and that distinction is the whole of
this section.

The file prints `v = sqvar(c) = sign(c)·√|c|` (§7.2), so `c = sign(v)·v²` and `dc/dv = 2|v|`. A printed value
uncertain by `0.5e-4` therefore gives a covariance uncertain by `2·|v|·0.5e-4`:

| Quantity | Value |
|---|---|
| Printed half-width | `0.5e-4` |
| Largest `|v|` in a fixed static epoch | ≈ `0.0025` |
| Covariance half-width | **`2.5e-7`** |

Passing `0.5e-4` through unchanged would be **two hundred times too loose**, and would condition away
matrices that are indefinite for a real reason instead of only those rounding explains.

**No approximation strategy is asserted** on a baseline covariance read this way, and that is a decision
rather than an omission. `RECORDED_PRECISION` would be the wrong label: the sigma is the engine's own, not
one invented from how many digits were written, and its own definition forbids it "for an observation whose
sigma becomes an adjustment weight" — which is what this becomes. `covariance_from_printed` adds
`ROUNDING_CONDITIONED` itself, and only if it had to move the matrix.

### 8.3 Antenna reduction needs both horizons **[V]**

Rule 4 above, made exact. An engine determines the vector between two *antenna reference points*; the
adjustment wants the vector between two *marks*:

```text
d_mark = d_ARP − R(rover)ᵀ·o_rover + R(base)ᵀ·o_base
```

**The two rotations are different rotations.** Over a 3 km baseline the local vertical turns by about 0.03°,
which is 0.8 mm across a 1.5 m antenna offset — larger than the millimetre everything else here is careful
about. Using one horizon for both ends makes two equal vertical offsets cancel exactly, which looks tidier
and is wrong; `tests/test_gnss_baselines.py` asserts the residue is there.

A **slant** height is refused rather than assumed vertical (`antenna_height_is_slant`): it is measured to the
antenna rim and needs the antenna's dimensions to be converted, which is FR-063's antenna database and does
not exist yet. Assuming vertical is wrong by centimetres in height, quietly.

---

## 9. Failure handling

| Situation | Behaviour |
|---|---|
| Engine absent | GNSS processing disabled with an explanation and an offer to install (FR-306, FR-301) |
| Product unavailable | Reported before the batch starts, with the option to use a lower-latency class, recorded |
| Download failure | Retried with backoff, then reported per session; the batch continues |
| Authentication failure | Distinguished from a network failure and reported as such, pointing to the credential configuration |
| No solution for a session | Reported with the engine's own message and the session's data span; the batch continues |
| Solution quality below a configured threshold | Flagged in results, not silently accepted |
| Timeout | Process terminated, working directory retained, elapsed and limit reported |

---

## 10. Acceptance criteria

1. Session discovery on a folder of RINEX 2 and RINEX 3 files (short and long names, compressed and
   Hatanaka-compressed) produces correct sessions, with header/filename mismatches reported.
2. A generated configuration file, fed back through `-k`, reproduces a run bit-identically (NFR-007).
3. `.pos` parsing round-trips a known file: every field read matches the file, verified against fixtures for
   each supported output format.
4. Covariance from a static relative solution reaches a DynAdjust G measurement with its 3×3 matrix intact.
5. A batch with one deliberately broken session completes, processes the rest, and reports the failure.
6. Products resolve from cache without a network call on a second run, and provenance names every product
   used.
7. No credential appears in any log, configuration file, provenance record or export (NFR-010) — asserted by
   a test.
8. Selecting a PPP mode displays the limitation notice required by FR-604.
