# 14 — Multi-epoch comparison and structural monitoring

**Status:** Draft — the computation is implemented (P10a, §8.1); the algorithms, panel, layers and report
are P10b's.
**Requirements covered:** FR-830…FR-838; uses FR-105, FR-207, FR-835, FR-903, FR-932.
**Source:** O6; tex §Comparação multiépoca e monitoramento de estruturas; §Introdução; §Justificativa
aplicada e comercial.

This capability is **entirely absent from the archived roadmap**
([`archive/README.md`](./archive/README.md), item 4) despite being a full objective, a methodology section and
an expected result of the research project. It is also the module with the highest stakes: its outputs
inform decisions about dams, bridges and slopes.

---

## 1. The distinction that organises this module

The proposal makes it explicitly, citing Kuang (1996):

> *"Na literatura é feita uma distinção entre o ajustamento de uma rede em uma única época e a análise de
> deformações, que envolve a comparação de coordenadas obtidas em épocas subsequentes. O ajustamento
> tradicional procura determinar as melhores coordenadas em um instante específico, ao passo que a análise
> de deformações mede a diferença entre soluções e quantifica deslocamentos."* — `tex §Introdução`

**Adjustment** answers *where is this point now, and how well do I know that?* **Deformation analysis**
answers *has it moved, and am I sure?* The second is not the first applied twice — it depends on the
covariance of *both* solutions and on how the two are related to each other.

---

## 2. Metadata contract (FR-830)

Comparison is only meaningful when both solutions carry, and GeoComp checks:

| Metadata | Why | Where |
|---|---|---|
| Reference frame / CRS | Coordinates in different frames differ by the frame difference, which is not motion | [`04-data-model.md`](./04-data-model.md) §3 |
| Reference epoch | Coordinates at different epochs differ by plate motion and deformation between them | §2.2 of the data model |
| Observation date and time | Distinguishes the observation instant from the coordinate epoch | Campaign, Solution |
| Datum definition | A minimum-constraint solution and a constrained solution of the same data are *not* comparable | Solution |
| Geoid model | Heights computed with different models differ by the model difference | FR-804 |
| Engine, version, parameters | Two solutions from different processing are not a displacement | Provenance |

**Hard rule (FR-105).** A solution without an epoch cannot enter a comparison. GeoComp raises
`ValidationError` rather than assuming. An assumed epoch produces a displacement that is wrong by however
much the assumption missed — silently, and with full apparent confidence.

---

## 3. Compatibility and transformation (FR-831, FR-832)

Before differencing anything:

1. **Check.** Frame, epoch, datum definition, height type, geoid model, and station identity. Report every
   discrepancy found.
2. **Transform where possible.** Bring both solutions to a common frame and epoch, with time-dependent
   transformations where the frames require them. **GeoComp's own** (`core/geodesy/frames.py`, built in P9a
   and shared with the combination — [`13`](./13-module-integration.md) §5.1): EPSG's parameters, checked
   against PROJ to a nanometre, because the comparison needs each transformation's Jacobian, velocities
   carried across it and a record, which a PROJ pipeline does not return. Its `TransformationRecord.accuracy`
   is the common-mode term this item's uncertainty rule adds to absolute positions.
   The transformation applied is recorded in the result (FR-832), and **the transformation's own uncertainty
   propagates into the comparison** (FR-207) — a transformation is not exact, and its uncertainty can exceed
   the displacement being sought.
3. **Refuse where not.** Two solutions with incompatible datum definitions are not made comparable by a
   coordinate transformation. GeoComp refuses, and says why.

**Rule:** GeoComp never silently transforms. Every transformation appears in the result, in the report and in
the provenance, because a monitoring series in which some epochs were transformed and others were not is
uninterpretable afterwards.

---

## 4. Displacements (FR-833, FR-834)

For each station present in both epochs:

$$\mathbf{d} = \mathbf{x}_2 - \mathbf{x}_1, \qquad
\boldsymbol{\Sigma}_{d} = \boldsymbol{\Sigma}_{x_2} + \boldsymbol{\Sigma}_{x_1} - \boldsymbol{\Sigma}_{x_1 x_2} - \boldsymbol{\Sigma}_{x_1 x_2}^{T}$$

The cross-covariance term is not decoration. Two epochs sharing reference stations, a common datum
definition, or common GNSS products **are correlated**, and ignoring the correlation overstates the
displacement uncertainty — which makes real motion look insignificant. Where the cross-covariance is
unavailable, GeoComp assumes independence, marks the result `APPROXIMATE` with the `INDEPENDENCE_ASSUMED`
strategy, and states the direction of the resulting bias (FR-202, FR-203).

### 4.1 Significance testing (FR-834)

A displacement is not a result until it is tested against its uncertainty.

- **Per station:** the quadratic form **d**ᵀ **Σ**_d⁻¹ **d**, tested against the appropriate distribution for
  the dimensionality, at a user-selected confidence level. Reported: the statistic, the critical value, the
  confidence level, and the decision.
- **Confidence region:** the displacement's own error ellipse, plotted at the displacement's tip, so the user
  can *see* whether zero lies inside it (FR-901).
- **Component-wise** results as well as the joint test, since horizontal and vertical motion often have very
  different significance.

**A displacement below its detection threshold is reported as "not significant", never as zero and never
suppressed.** "We could not detect motion" and "there is no motion" are different statements, and in
structural monitoring the difference matters.

---

## 5. Reference block and datum (FR-835)

The hardest part of deformation analysis, and the one most often got wrong.

If the datum for both epochs is defined by holding stations that have themselves moved, that motion is
redistributed across the network and appears as everything *else* moving. GeoComp therefore:

1. Supports declaring a **reference (stable) block** and **object points**
   ([`04-data-model.md`](./04-data-model.md) §2.3, `monitoring_role`).
2. Supports **inner-constraint** free-network solutions over the reference block
   ([`06-adjustment-core.md`](./06-adjustment-core.md) §3), so the datum is defined by the block as a whole
   rather than by any single station.
3. Provides a **stability test on the reference block itself** — a congruency test over the reference
   stations, testing the null hypothesis that they have not moved relative to one another. If the block fails,
   the analysis says so and the user is told which stations are implicated, rather than the analysis
   proceeding on a false premise.
4. Supports iteratively identifying the stable subset, with each step recorded — never as a silent automatic
   procedure, because "find the subset that makes the answer come out stable" is a real methodological
   hazard.

---

## 6. Deformation across the network (FR-836)

Beyond per-station displacements:

- **Global congruency test** across all common stations: has the network as a whole changed?
- **Strain parameters** over the object points where the configuration supports it, giving deformation as a
  field rather than a set of independent point motions.
- **Movement patterns**: rigid-body translation and rotation separated from actual deformation — a structure
  that has tilted as a block is a different finding from one that is straining.
- **Velocities** across three or more epochs, with their uncertainties.

---

## 7. Alerts and time series (FR-837, FR-838)

**Alert thresholds** (FR-837): configurable per station or per station group, by displacement magnitude,
by component, by velocity, or by significance. Exceedances are flagged in the results, in the map styling
(FR-900) and in the report (FR-932). Thresholds live in the project so a monitoring project carries its own
alarm criteria.

GeoComp flags; it does not notify. Automatic external notification (email, webhook) is a service concern
outside v1.0 scope ([`01-vision-and-scope.md`](./01-vision-and-scope.md) §5).

**Time series** (FR-838): per station, per component, across all epochs, with uncertainty bands, threshold
lines, and epoch metadata visible. Plotted in a dockable panel (FR-903), exportable as data and as an image.
Selecting a station on the map shows its series — the interaction that makes monitoring analysis in a GIS
worth doing.

---

## 8. Workflow

```text
Epoch 1 solution ─┐
Epoch 2 solution ─┼─► compatibility check (FR-831)
                  │         │ fail → report, refuse
                  │         ▼
                  └──► transform to common frame/epoch (FR-832)
                            ▼
                    reference block stability test (FR-835)
                            ▼
                    displacements + covariance (FR-833)
                            ▼
                    significance tests (FR-834)
                            ▼
              deformation analysis (FR-836) · alerts (FR-837)
                            ▼
        displacement layer · time series (FR-838) · report (FR-932)
```

Each step is a Processing algorithm (FR-005), so a monitoring campaign can be re-run identically at every
epoch — which is exactly what a monitoring programme needs.

### 8.1 As implemented (P10a)

`core/monitoring/`, the pipeline above as functions; the Processing algorithms over them are P10b's.

* **`compare(first, second, cross_covariance=)`** (§2–§4). Refuses a solution without an epoch
  (`monitoring_solution_without_epoch`, FR-105), heights of different types or geoid models, datum definitions
  no transformation bridges (`monitoring_datum_incompatible`: free against free compares, held against held,
  free against held does not), two projected systems, and a frame pair related only at another epoch
  (`monitoring_frame_needs_velocity`: moving a position between epochs is the motion being measured).
  Geocentric solutions in different frames are transformed with GeoComp's own transformations (§3), the
  second into the first's frame at its own epoch; the transformation's stated accuracy enters as a **common
  translation** of every station, so it cancels in anything measured against the reference block and stays in
  an absolute displacement. Differences in engine or version, and stations one epoch lacks, are findings, not
  refusals. Without a cross-covariance the result is `APPROXIMATE` with `INDEPENDENCE_ASSUMED` and states its
  bias (§4). Tests use each epoch's cofactors with the **pooled** a-posteriori variance factor over their joint
  degrees of freedom: F under the null hypothesis, chi-square when neither epoch had redundancy.
  A geocentric difference is turned into each station's east, north and up.
* **`analyse(comparison, reference, objects=)`** (§4.1, §5). The difference is S-transformed onto the datum
  the reference block defines — translations; a rotation about the vertical for a terrestrial network; a scale
  on request — so two free epochs, each with its own realisation of the datum, are not mistaken for motion.
  The block's congruency is tested; if it fails, `check_reference` localises it step by step (the station whose
  removal reduces Ω most, every step and every station's contribution kept) and `analyse` **refuses**, naming
  the implicated stations (`monitoring_reference_block_unstable`). The stable subset is proposed, never adopted.
  Every station's displacement is then reported with its covariance, horizontal confidence ellipse and joint,
  horizontal and vertical tests — *significant* or *not significant*, the value kept either way — and the
  global congruency test over all stations.
* **`strain(analysis)`** (§6). Rigid-body translation and rotation fitted to the object points, then a
  homogeneous strain; the drop in weighted squares over the three strain parameters F-tested, so a block that
  moved whole is distinguished from one that is deforming. Dilatation, maximum shear, principal strains and
  their azimuth, with standard deviations. Three points in an area at least, or refused.
* **`series(solutions, reference=)`** (§6, §7). Each station's offsets from the first epoch with that epoch's
  own covariance, referred to the reference block as the two-epoch analysis is, as plottable rows; a velocity
  per station by weighted least squares with its covariance, its test and the line's own redundancy. Epochs are
  independent (`INDEPENDENCE_ASSUMED`).
* **`evaluate_alerts(thresholds, displacements=, series=)`** (§7). Magnitude, horizontal, vertical, velocity or
  significance, per station or group; one alert per station covered, so a result says what was checked as well
  as what crossed. A displacement over its limit is flagged **whether or not it is significant**: the owner's
  criterion is not silenced by the survey's.

---

## 9. Acceptance criteria

1. Comparing two solutions with different frames or epochs triggers transformation with a provenance record;
   comparing solutions with incompatible datum definitions is refused with a message naming the problem.
2. A solution lacking an epoch is refused (FR-105), asserted by a test.
3. Displacements and their covariance reproduce a published deformation-analysis worked example, including
   the significance decisions.
4. Synthetic data with a known displacement injected at one station: the displacement is recovered, found
   significant, and no other station is falsely flagged.
5. Synthetic data with a *moving reference station*: the reference-block stability test detects it and names
   the station, and the analysis does not proceed on the false premise.
6. Ignoring cross-covariance is marked `APPROXIMATE` with the bias direction stated.
7. Displacements below the detection threshold are reported as "not significant", never as zero.
8. A three-epoch series produces correct velocities with uncertainties and a plottable time series.
9. Alert thresholds flag the correct stations, in the results, the map styling and the report.

### 9.1 State after P10a

Against `tests/monitoring_network.py`: four reference pillars and five points on a structure, 36 distances an
epoch, each epoch adjusted by the core as a free network from its own starting coordinates.

| Criterion | State |
|---|---|
| 1. Frames transform with a record; incompatible datums refused by name | **met** — ITRF2014 against ITRF2020 with the record and the common-mode uncertainty; free against held, two projections, two geoid models, and SIRGAS 2000 at another epoch refused |
| 2. No epoch refused | **met** — by `compare`, and by `Solution.from_dict`, which crashed on it before (see ROADMAP P10a) |
| 3. A published worked example reproduced | **open** — no published example is reachable from the development environment ([`22`](./22-reference-data-sources.md) §5.3); it waits on one being supplied |
| 4. Injected displacement recovered, no false positives | **met** — 10 mm at one point found at 99 %, every other station's statistic under half its critical value |
| 5. A moving reference station caught and named | **met** — 18 mm on a pillar: the block fails, the localisation names it at the first step, the analysis refuses; with the block the user accepts, its motion is found |
| 6. Independence marked approximate with its bias | **met** |
| 7. Not significant is not zero | **met** — the value, its σ and its ellipse are kept |
| 8. Three epochs give velocities and a plottable series | **met in the core** — velocities within their uncertainty, a series as rows; the panel and its map linkage are P10b's |
| 9. Alerts flag the right stations | **met in the results**; the map styling and the report are P10b's |
