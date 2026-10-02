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
| Gravity stations | Point | Gravity and its sigma in the display unit and in SI, how it was determined (held, absolute, relative), the w-test's decision on its absolute value |
| Gravity differences | Line | Difference, sigma, residual, standardised residual, redundancy, MDB, w-test decision; uncheckable drawn as prominently as a blunder candidate |
| Displacement vectors | Line | Displacement by component, its standard deviations, the joint, horizontal and vertical decisions, the alerts crossed, the epochs compared |
| Displacement ellipses | Polygon | The displacement's horizontal confidence ellipse at the arrow's tip, with its confidence and the decision |
| Velocities | Line | A year's motion: velocity by component, its standard deviations, the speed an alert is judged on, the test, the epochs |
| Reliability | Point / Line | MDB, external reliability, uncheckable flag |
| Planned network (pre-analysis) | Point / Line | Expected ellipses, expected reliability |

All arrive **styled and immediately interpretable** (FR-905). A user who runs an adjustment sees the result;
they do not then style eight layers by hand.

**A passing observation carries its w-test (phase P8b).** Until then the adjustment recorded a w-test only for
blunder candidates and uncheckable rows, so a row that passed looked exactly like one never tested — and the
residual layer drew **every passing observation as *not testable***. The categories the style promised were
there; the one most observations belong to never appeared. The core now records the test for every row it
tested, and a result that records none — an engine's, which GeoComp did not test — says so with an empty
decision rather than claiming a redundancy nobody computed.

### 1.1 A geocentric solution on the map (P9b)

A combined solution is in geocentric X, Y, Z, and no map draws those — a layer in them would put every station
inside the Earth. The result layers re-express it **for display** (`core/visualization/display.py`) in the UTM
zone of its centroid: easting, northing and ellipsoidal height, the covariance turned into each station's
horizon. The solution itself is untouched.

* **The grid names the solution's own frame.** SIRGAS 2000 by its EPSG code (31971–31976 north, 31977–31985
  south); an ITRF by a WKT2 Transverse Mercator on *that* frame, so the layer reads "ITRF2020 / UTM zone 22S".
  A bare GRS80 UTM string is what QGIS matches to "SIRGAS 2000 / UTM" — for an ITRF2020 solution at 2026, a
  label decimetres of plate motion wrong.
* **Ellipses and correction vectors turn by the grid convergence.** The solution states an ellipse's
  orientation from geodetic north; UTM's north differs by the meridian convergence, over a degree at a zone's
  edge, and every ellipse drawn without the turn would lean by that much.
* **Held marks are placed from the network**, which is re-expressed too; their constraint mode still chooses
  their symbol.

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

**As built (P10b).** The arrow, the ellipse at its tip and a velocity's year of motion are computed without
QGIS (`core/visualization/monitoring.py`). The factor is fitted so the largest arrow spans a seventh of the
network, unless one is given, and it is stated in both layers' names. A geocentric comparison is drawn in the
UTM grid of its frame, and each station's arrow and ellipse turn by the grid convergence, as §1.1's do. The
three monitoring styles draw one category per station, strongest first: **alert** (a threshold crossed,
whether or not the motion is significant), **significant**, **not significant**. Not significant is drawn,
thinner and grey, never hidden.

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

**As built (P10b)** — `gui/time_series_panel.py`. The panel is docked and hidden at start. A layer written by
*Time series and velocities* carries its series document's path as a custom property; when such a layer is
added to the project, the panel attaches to it and shows itself. Selecting stations on the map overlays their
series. Clicking a point selects that station on the map and shows the epoch's solution, value and band.
Hovering shows the same. The band is the confidence level's two-sided normal quantile times each epoch's
standard deviation. The fitted line is the one fitted, with its own offset, not one forced through zero. The
dashed limits are the station's vertical limit on the up or height plot, and its horizontal or magnitude
limits on east and north. The panel exports the plotted stations' rows as CSV and the plot as a PNG. It is
also reachable from Plugins ▸ GeoComp ▸ *Time series panel*. The curves come from
`series_curves`, which the report's plots use too.

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
coordinates with uncertainties — or, for a gravity solution, adjusted gravity in the display unit, with its
residuals, MDB and external effect in that unit too, since six decimals of m·s⁻² print them all as zero);
statistics (variance factors, degrees of freedom, global test with its
critical values and decision); per-observation results (residuals, standardised residuals, redundancy,
w-test, MDB); reliability summary including uncheckable observations; error ellipses; maps; and a software
and version record.

**A combination adds a *Techniques* section (P9b, [`13`](./13-module-integration.md) criterion 7):** the
inputs, the engine and why, every frame transformation applied, each technique's observations, redundancy
and share of it, part of `vᵀPv` and `vᵀPv/r`, largest |w| and uncheckable count — the constraint and geoid
rows as their own groups, so the shares add up — the variance components when estimated, and the geoid
residuals with the model named. All of it is read from the solution's provenance, where the combined
adjustment recorded it, so a report rendered later from the saved document says the same. A solution that is
not a combination has no such section.

**The report states the uncertainty mode and, if approximate, the strategies used** (FR-203). It states the
engine, its version and its command line. It is intended to be defensible: a reader should be able to see
exactly what was computed, from what, with what assumptions.

### 7.2 Monitoring report (FR-932)

Displacement table with significance decisions; reference block stability test result; deformation summary;
alert exceedances; displacement map; time series plots; and the epoch metadata and transformations applied
for every epoch compared.

**As built (P10b)** — `reports/monitoring.py`, template `monitoring.html`. Rendered from the monitoring
documents alone, by the two analysis algorithms and by `geocomp:monitoring_report`. The map and the plots
are **inline SVG**: a report travels as one file, and an SVG drawn from the same geometry as the layers
cannot show something the map does not. The map states its exaggeration in the picture, because a report
is read away from any legend. Three sections are placed even by a template that leaves them out: the
uncertainty notice, the compatibility findings and transformations, and the reference block's test. A
refused analysis has a report too, carrying the localisation steps and the proposed stable subset, marked as
proposed and not adopted. Values are in millimetres; the documents keep metres.

### 7.3 Mechanics (FR-931)

- HTML output as the Processing output type, viewable in the results panel and in a browser, printable to
  PDF.
- **Template-driven** from the templates directory configured in Global Settings (FR-066), so an organisation
  can apply its own layout and branding.
- Fully translated (FR-090); numbers formatted per locale (FR-094).
- Data available separately as CSV/`.xlsx` (FR-162) for users who build their own reports.
- Deterministic: the same solution produces the same report (NFR-007).


### 7.4 How a number is written (FR-067; P12a)

Four interface settings describe it — `interface.angle_format`, `angle_decimals`, `coordinate_decimals`,
`distance_unit` — and until P12a no report read them: a user who chose gon saw decimal degrees, and every UTM
northing printed as `7.3951e+06`, because the report's number formatter switches to an exponent at a million.
`core/display_format.py` formats, QGIS-free; `algorithms/display.py` resolves the settings when a report is
written, and the adjustment report receives the result in its context, so rendering stays a function of its
inputs (NFR-007).

| Quantity | Written as |
|---|---|
| An absolute angle — a direction, an orientation, an ellipse's azimuth, a latitude | the chosen format: DMS, decimal degrees, gon or radians; *places* count on the smallest customary unit (seconds for DMS), so one setting resolves about the same angle in every format |
| A small angle — a misclosure, a residual, a collimation or index error, an orientation spread | the format's small unit: arc-seconds for DMS and decimal degrees, centesimal seconds (cc) for gon, microradians for radians; the column heading names it |
| A coordinate | to the chosen places, **never with an exponent**, in its CRS's units — the distance unit does not apply, because a metric grid in feet describes a coordinate system that does not exist |
| A distance or height difference that was measured or derived | in the chosen unit — metre, international foot or US survey foot — to the coordinate places |

Uncertainties, residuals in length and misclosures in millimetres stay in SI: they are precision figures with
their own conventional units. **Only what a person reads changes**: every file — JSON, CSV, the project
store — stays SI at full precision (FR-095). Not addressed: the locale's decimal separator (FR-094), and the
monitoring report's displacement tables, which are in millimetres by design.
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
