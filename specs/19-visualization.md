# 19 — Visualisation and reporting

**Status:** Draft
**Requirements covered:** FR-900…FR-905, FR-930…FR-932.
**Source:** tex §Arquitetura do plugin; §Integração com o DynAdjust; §Justificativa técnica ("Visualização
imediata"); §Comparação multiépoca; §Justificativa aplicada e comercial.

The proposal's technical justification names *immediate visualisation* as one of three gaps GeoComp closes:
results overlaid on orthoimagery and context layers, so they can be interpreted and communicated. That is
the standard this module is held to.

---

## 1. Result layers (FR-900)

| Layer | Geometry | Carries |
|---|---|---|
| Adjusted stations | Point | Coordinates, uncertainties, positional uncertainty, ellipse parameters, constraint status |
| Error ellipses | Polygon | Semi-axes, orientation, confidence level, exaggeration factor |
| Residual vectors | Line | Residual, standardised residual, w-test decision, redundancy number |
| Observations | Line | Type, value, uncertainty, status, residual |
| GNSS baselines | Line | Components, covariance, solution status, quality indicators |
| Displacement vectors | Line | Displacement, covariance, significance decision, epochs compared |
| Reliability | Point / Line | MDB, external reliability, uncheckable flag |
| Planned network (pre-analysis) | Point / Line | Expected ellipses, expected reliability |

All arrive **styled and immediately interpretable** (FR-905). A user who runs an adjustment sees the result;
they do not then style eight layers by hand.

## 2. Styling (FR-904)

Styles ship as **QML files** in `resources/`, applied by the algorithms and editable by users. Code applies a
style; it does not *contain* one — a user preparing a report for a client needs to restyle for their own
template, and a renderer built in Python is not editable in the layer properties dialog.

Conventions across every layer, so the plugin reads as one system:

- **Uncertainty maps to size**; **residual magnitude and significance map to colour.**
- **Rejected and excluded observations are visually distinct** and remain visible — a rejected observation
  that disappears from the map cannot be reconsidered.
- **Significance is categorical, not continuous**: significant / not significant / not testable are three
  distinct symbols, because that is the actual decision structure.
- Colour ramps are colour-vision-deficiency safe and legible in print, since these layers end up in
  technical reports.
- Every layer gets field aliases and value maps in the active language (FR-090), so the attribute table is
  readable.

## 3. Error ellipses (FR-901)

Real error ellipses are invisible at map scale: a 5 mm semi-axis on a 1:5000 map is a micron.

**Requirements:**

1. Ellipses are drawn at a user-selected **confidence level**, and the level is stated.
2. Ellipses are drawn with an explicit **exaggeration factor**, which is stated in the legend and in any
   layout that includes the layer. An unstated exaggeration turns a quality visualisation into a
   misrepresentation — the single most important rule in this document.
3. The default exaggeration is computed from the map extent and the ellipse sizes, so the first view is
   useful; it is then adjustable.
4. **Relative ellipses** between station pairs are available as well as absolute ones. Relative ellipses are
   what answer "how well do I know this baseline", which is usually the real question
   ([`06-adjustment-core.md`](./06-adjustment-core.md) §4.4).
5. 3D solutions offer ellipsoids projected to the map plane, plus a vertical-uncertainty representation —
   the horizontal projection of an ellipsoid hides the vertical component, which in geodetic work is
   typically the worst one.
6. A scale reference — an ellipse of a stated true size — is available for the layout.

Displacement vectors carry the same treatment: an exaggeration factor stated in the legend, and the
displacement's confidence ellipse drawn at the vector tip so the reader can see whether zero lies inside it
([`14-multi-epoch-monitoring.md`](./14-multi-epoch-monitoring.md) §4.1).

## 4. Thematic quality maps (FR-902)

Networks are styled by: positional uncertainty; standardised residual; redundancy number (which shows
immediately where the network is uncheckable); MDB; external reliability; GNSS solution status; observation
type; and epoch or campaign.

The redundancy-number map deserves particular emphasis: a network can pass every statistical test while
containing observations whose blunders are undetectable, and the map is the fastest way to see it.

## 5. Time series (FR-903)

A dockable panel plotting a station's coordinates across monitoring epochs: per component, with uncertainty
bands, alert threshold lines, significance marks, and epoch metadata visible on hover.

- Selecting a station on the map shows its series; selecting a point in the series highlights the station and
  the epoch.
- Multiple stations overlay for comparison.
- Exports as data (CSV) and as an image for reports.

This map-to-plot linkage is the interaction that makes monitoring analysis inside a GIS worthwhile rather
than merely possible.

## 6. Base maps and layout (FR-167)

Results overlay orthophotos and base layers, which is the proposal's stated point. GeoComp offers to add
configured base map services and honours existing QGIS layers and connections; it bundles no imagery and
hard-codes no service.

Print layout templates ship for the standard deliverables — network map with ellipses, displacement map,
quality map — as QGIS layout templates the user can adapt.

---

## 7. Reporting (FR-930…FR-932)

### 7.1 Adjustment report (FR-930)

Sections: identification and provenance; input summary (stations, observations by type, constraints);
parameters and their effective values *with the scope each came from* (FR-068); results (adjusted
coordinates with uncertainties); statistics (variance factors, degrees of freedom, global test with its
critical values and decision); per-observation results (residuals, standardised residuals, redundancy,
w-test, MDB); reliability summary including uncheckable observations; error ellipses; maps; and a software
and version record.

**The report states the uncertainty mode and, if approximate, the strategies used** (FR-203). It states the
engine, its version and its command line. It is intended to be defensible: a reader should be able to see
exactly what was computed, from what, with what assumptions.

### 7.2 Monitoring report (FR-932)

Displacement table with significance decisions; reference block stability test result; deformation summary;
alert exceedances; displacement map; time series plots; and the epoch metadata and transformations applied
for every epoch compared.

### 7.3 Mechanics (FR-931)

- HTML output as the Processing output type, viewable in the results panel and in a browser, printable to
  PDF.
- **Template-driven** from the templates directory configured in Global Settings (FR-066), so an organisation
  can apply its own layout and branding.
- Fully translated (FR-090); numbers formatted per locale (FR-094).
- Data available separately as CSV/`.xlsx` (FR-162) for users who build their own reports.
- Deterministic: the same solution produces the same report (NFR-007).

---

## 8. Acceptance criteria

1. Running an adjustment produces styled layers requiring no manual styling (FR-905).
2. Error ellipses render at the selected confidence with the exaggeration factor stated in the legend; a
   test asserts the legend text is present and correct.
3. Relative ellipses between a station pair match the values computed from the joint covariance.
4. Layer styles are QML files, editable in the layer properties dialog, and surviving a QGIS project save
   and reload.
5. Thematic maps render correctly for each listed attribute, including the redundancy-number map.
6. The time series panel plots a three-epoch series with uncertainty bands and threshold lines, and map-to-
   plot selection works in both directions.
7. Reports render in all three languages with locale-correct numbers, and are byte-identical across two runs
   on the same solution.
8. A report from an `APPROXIMATE` solution names the approximation strategies used.
