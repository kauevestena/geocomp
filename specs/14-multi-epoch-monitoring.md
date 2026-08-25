# 14 — Multi-epoch comparison and structural monitoring

**Status:** Draft
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
2. **Transform where possible.** Bring both solutions to a common frame and epoch. GeoComp uses the QGIS/PROJ
   transformation infrastructure, including time-dependent transformations where the frames require them.
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
