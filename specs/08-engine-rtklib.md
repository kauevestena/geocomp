# 08 — Engine: RTKLIB / `rnx2rtkp`

**Status:** Draft
**Requirements covered:** FR-164, FR-300…FR-306, FR-350…FR-359, FR-604, NFR-010.
**Source:** O3; tex §Integração com o rnx2rtkp (RTKLIB); §Posicionamento pelo GNSS.

**Upstream references.** [RTKLIB (Takasu)](https://www.rtklib.com/) ·
[RTKLIB-EX / demo5 (rtklibexplorer)](https://github.com/rtklibexplorer/RTKLIB) ·
RTKLIB manual (2.4.x) · `manual_demo5.pdf` for the fork.

> **Verification note.** Statements marked **[V]** were verified upstream during specification; **[C]** must
> be confirmed against the RTKLIB manual when the module is implemented (roadmap P7).

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
Command-line flags are used only where they have no configuration-file equivalent.

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
components, the corresponding correlation/covariance terms, age of differential, and the ambiguity ratio
factor. The exact column set depends on the selected output format **[C]** and MUST be confirmed against the
RTKLIB manual; the parser MUST read the file's own header rather than assuming a column order.

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
