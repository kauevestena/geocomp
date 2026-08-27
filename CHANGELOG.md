# Changelog

Semantic versioning. Breaking changes to the storage schema, algorithm ids or public core interfaces are
major ([`specs/21-packaging-ci-release-licensing.md`](specs/21-packaging-ci-release-licensing.md) §6).

## [Unreleased]

### Phase P3 - Total station (in progress)

The first end-to-end vertical slice: raw field book to adjusted, statistically
validated network, with no external engine anywhere in the path.

#### Added

- **`core/techniques/total_station/`** - face reduction with its diagnostics,
  instrument and EDM corrections, the first-velocity atmospheric correction, the
  basic reductions with the d-z correlation kept, and the geometric reductions
  (FR-400 to FR-405, FR-412). Every stage separately callable and separately
  inspectable, which is the teaching requirement; every stage propagating
  covariance.
- **Survey computations** - traverse in all three forms with both classical
  rules and the misclosure checks (FR-406); resection with danger-circle
  detection (FR-407); forward intersection reporting weak geometry through the
  error ellipse (FR-408); classical networks assembled for the P2 core (FR-409);
  trigonometric levelling including leap-frog (FR-410); 3D radiation with its
  full 3x3 covariance (FR-411).
- **`core/instruments/`** - named instrument and reflector profiles with a
  per-constant uncertainty and the applied-once rule, and the stochastic model
  resolution whose last step refuses rather than inventing a sigma (FR-061,
  FR-064, FR-069).
- **Eight Processing algorithms and the Total Station menu** - import field
  book (FR-160), generalised pre-processing (FR-400), traverse (FR-406),
  resection (FR-407), forward intersection (FR-408), classical network
  (FR-409), trigonometric levelling (FR-410) and 3D radiation (FR-411). Each
  writes an HTML report, a machine-readable document and scalar outputs, and
  each one's document is the next one's input so the chain assembles in the
  graphical modeller (FR-033).
- **A synthetic survey fixture with known coordinates** (`tests/synthetic.py`).
  RD-01 stays the reference for face reduction and free-network adjustment, but
  it has no known point, so it cannot check a traverse, a resection or a
  radiation at all. The fixture generates the readings a total station would
  have recorded standing at coordinates chosen in advance, and every routine is
  asked to recover the geometry it was generated from - so the expected values
  are the survey itself rather than a previous output.
- **A structural check on the tier-3 tests' parameter names.** Those tests only
  run where QGIS does, and Processing *ignores* an unrecognised key rather than
  rejecting it, so a mistyped parameter silently becomes a default and fails
  somewhere else. Every key is now checked against the declaring algorithm by
  parsing, which works without QGIS installed.
- **Styled result layers** (FR-900, FR-904, FR-905). Both adjustments now offer
  the same five map layers: adjusted stations sized by their positional
  uncertainty, error ellipses, observations coloured by what the w-test decided
  about them, the measured network by observation type, and coordinate
  correction vectors. They arrive styled, which is what "visualização imediata"
  asked for -- a user who runs an adjustment sees the result rather than styling
  five layers by hand. None is created unless asked for, so an adjustment run to
  feed another algorithm writes nothing extra.
- **Five QML style files** in `geocomp/resources/styles/`, editable in the layer
  properties dialog and re-saveable over the shipped file. Code applies a style;
  it does not contain one. Uncertainty maps to size and significance to colour
  across every layer, so the plugin reads as one system; the palette is
  Okabe-Ito, which survives every common colour-vision deficiency and greyscale
  printing, because these layers end up in technical reports. Significance is
  three symbols rather than a ramp, because the w-test gives three answers --
  and an observation nothing could be tested about is not a passing one.
- **`core/visualization/`** - ellipse rings, vector tips and the first
  exaggeration factor, with no QGIS in them, so the vertices are checked against
  closed-form values rather than only inside a QGIS runtime.

#### The exaggeration factor, and why it is a required argument

`specs/19` calls an unstated exaggeration the single most important rule in the
document: a 5 mm semi-axis is a micron at 1:5000, so every drawn ellipse is
enlarged, and one that does not say by how much is a misrepresentation rather
than a visualisation.

It is therefore not defaulted anywhere. Every function that produces drawn
geometry takes `exaggeration` keyword-only and without a default, so a call site
cannot omit it; the factor travels on the geometry it produced rather than
beside it; and the layer's name -- which is what reaches the legend -- is
composed from the same argument the vertices used, so the two cannot disagree. A
structural check enforces all of that by parsing, and a tier-3 test follows one
factor from the parameter through the ring to the name and the attribute table.

Where no factor is given, one is fitted to the network's own extent, since an
algorithm has no map canvas to measure, and rounded down to a 1-2-5 value: a
legend reading "x500" is read at a glance and "x487.3" is not. It is never below
1. Shrinking an ellipse understates the uncertainty, which is the failure the
rule exists to prevent.

#### Fixed in the phase P2 core

Both found by running direction sets end to end for the first time, and both
producing a diverging adjustment whose only symptom was a convergence failure
that said nothing about the cause.

- **Angular misclosures are wrapped to the short way round the circle.** A
  direction read as 353 degrees against a computed -7 differs by nothing; the
  plain subtraction made it 360, which entered the normal equations as an
  enormous residual. P2's own networks happened to have every angular
  observation near its computed value, so the wrap never arose.
- **A direction set's orientation unknown is derived from the observations and
  started from the data.** It was previously left to the caller to declare and
  initialised at zero. A direction without an orientation unknown is always
  wrong, and zero is essentially never the right starting value, so both are now
  automatic.

#### Fixed while testing the algorithms

- **A closed traverse left without a closing azimuth no longer checks itself
  against north.** The parameter fell through to zero, so an untouched field
  produced an angular misclosure of several hundred degrees that read as a
  catastrophic survey. A loop that backsights the station it returns from
  arrives on the very line its start azimuth refers to, so that case is now
  inferred; anything else says plainly that the angles cannot be checked.
- **An exactly closing traverse no longer reports the worst possible relative
  precision.** The ratio is absent for two opposite reasons - a zero misclosure
  and an open traverse - and one sentinel of `0.0` for both read as 1:0.
- **`ErrorEllipse` no longer documents a `scale_factor` it never had.** The
  exaggeration belongs to a drawing, not to a confidence region: the same
  ellipse on two maps at two scales is one ellipse. It lives on `DrawnEllipse`
  instead, where it is required.
- **The spread of the orientations implied by several known points was
  identically zero for two of them**, which is the commonest case in a detail
  survey. It was the range of the *absolute* deviations, and two estimates
  always sit symmetrically about their own mean. It is now the range of the
  signed deviations, and a spread beyond three times the pointing precision is
  warned about by name: one of the control points is not where it is recorded,
  and every point radiated from that setup carries the error.

#### Notes

- **RD-01 carries two defects, and both are now tests.** The 1.000 m face-pair
  distance discrepancy is flagged as blocking and the pointing is kept out of
  the observations. And the prototype's arithmetic-mean face reduction puts one
  of its six directions exactly 180 degrees out - which `specs/09` had recorded
  as "correct for the RD-01 data". Two independent checks settle it, and
  acceptance criterion 1 is amended, because it could not have been met by a
  correct implementation.
- **RD-01 is a free network.** It contains no azimuth and no known point, so its
  datum defect is two translations and a rotation, and it can only be adjusted
  with inner or minimum constraints. A property of the dataset, now asserted.
- The whole slice runs in the test suite with no QGIS and no engines: reduce,
  assemble, inspect, adjust, test.


### Phase P2 - Adjustment core

The phase the project turns on. Least squares with its full statistical treatment, plus network design -
the engine behind four later modules, and what makes ADR-0002 real: gravimetric adjustment and pre-analysis
have no external engine at all. Still runs with no QGIS and no SciPy.

#### Added

- **`core/adjustment/`** - the parametric model `Lb + v = Ax + L0` end to end. Observation equations with
  analytic Jacobians for twelve types (1D height and gravity, 2D distance, angle, direction with its
  orientation unknown, azimuth, 3D slope distance, zenith angle, GNSS baseline and point), dispatched
  through the observation type registry so a new type stays a registry entry. Normal equations from the
  full weight matrix including correlated clusters; Cholesky with a QR fallback; iteration to convergence
  with **non-convergence reported as a failure, never a silently returned last iterate** (FR-220 to
  FR-227).
- **Datum handling** - `FIXED`, `WEIGHTED`, `MINIMUM_CONSTRAINT` and `INNER_CONSTRAINT`, the last two via
  the trace-minimum **G** matrix over a chosen station set, which is what deformation analysis needs:
  holding a station that has itself moved spreads its motion across the network. The defect is detected
  from the observation content and recorded on the solution rather than assumed (FR-222).
- **Rank diagnosis (FR-226)** - a singular system produces a sentence naming the stations and components
  in each undetermined direction, not a number and not a crash.
- **`core/statistics/`** - the two-sided global chi-square test (an unexpectedly *small* variance factor is
  information, not a pass); Baarda's w-test with the tau variant when sigma-nought is estimated, reporting
  which was used; redundancy numbers, minimal detectable bias and external reliability, with uncheckable
  observations flagged; absolute and relative error ellipses and 3D ellipsoids, chi-square or F scaled
  (FR-250 to FR-254).
- **Nothing is rejected automatically** (FR-255). Data snooping returns candidates; the decision is the
  user's, and re-adjustment after a rejection is a second explicit run.
- **`core/statistics/distributions.py`** - normal, chi-square, F and t with a SciPy fast path and a
  complete NumPy-only fallback (Acklam plus Newton; the regularised incomplete gamma; Lentz's continued
  fraction for the incomplete beta). Both paths tested against published tables and against each other.
- **`core/preanalysis/`** - design simulation, `Sigma_x = sigma_0^2 (A^T P A)^-1` from geometry and assumed
  precisions with no observations at all, reporting expected ellipses *and* expected reliability (FR-270,
  FR-271); and network inspection on real data - connectivity, isolated stations, insufficient
  observations, duplicates, missing approximate coordinates - returning every finding in one pass rather
  than stopping at the first (FR-273).
- **Three Processing algorithms** - `geocomp:analysis_network_inspect`,
  `geocomp:analysis_network_preanalysis` and `geocomp:analysis_network_adjust`, each with HTML and CSV
  outputs and scalar outputs so they chain in the graphical modeller.
- **The Analysis menu group**, the seventh top-level entry. `specs/15` §1.1 left its placement open; P2
  needed it and settled it, and FR-003 and FR-004 were amended to say seven rather than being contradicted
  by the code.
- **RD-03 and RD-09 reference networks** - 1D levelling, 2D trilateration, 2D triangulateration, free and
  constrained, with a known truth; and the same with a blunder of known size at a known place, which is
  the only way to test detection against ground truth rather than against another computation.
- **Structural check for message templates** - a template that interpolates a context key its raising site
  never supplies renders "(not set)" to the user and raises nothing. Both sides are now read as source and
  cross-checked.

#### Notes

- The tests that carry the weight are the *identities*, because they hold for every network rather than
  one: redundancy numbers sum to the degrees of freedom; a free and a constrained solution agree on
  residuals and on the variance factor; design simulation reproduces the adjustment's covariance to
  machine precision at the adjusted coordinates; every analytic Jacobian matches complex-step
  differentiation.
- **RD-03 and RD-09 are not transcriptions from Ghilani or Gemael.** Those books are unavailable here and
  inventing a citation would be worse than having none. They are validated against closed forms where one
  exists and against the identities above everywhere else; transcribing the published worked examples
  remains outstanding and is recorded in `specs/20`.
- **The sparse solver is not implemented.** The dense NumPy path is correct at every size and comfortable
  to roughly 2,000-3,000 stations. NFR-008 was reworded and the sparse path assigned to P12, where a
  network large enough to measure it will exist
  ([`specs/adr/0008-scipy-and-network-scale.md`](specs/adr/0008-scipy-and-network-scale.md)).
- **FR-272 moved to P3.** P2 ships the pre-analysis mathematics and the Processing algorithm; the
  interactive canvas dialog needs a running QGIS to verify, and shipping interaction code nobody has run
  is how a phase reports done while leaving a defect.
- Ellipses and the a priori variance factor now reach the `Solution` itself, so a DynAdjust result in P6
  fills the same structure on the same terms.


### Phase P1 - Core domain and uncertainty

The types everything else is built from, and the property that defines this project: no geodetic value
without an uncertainty. Still no QGIS dependency anywhere in this layer, and still no external engine.

#### Added

- **`core/units.py`** - SI and radians internally; DMS, gon, feet and mGal converted at the boundary and
  never stored. Sexagesimal parsing for field-book layouts, and a circular mean, which is what makes a
  face-left/face-right reduction correct across the zero of the horizontal circle.
- **`core/uncertainty.py`** - `Quantity` (value, variance, unit, rigorous-or-approximate mode) with
  propagating arithmetic and unit checking, and `Covariance` (labelled, symmetry- and PSD-validated) with
  rigorous propagation `Sigma_out = A Sigma A^T` (FR-200 to FR-208).
- **The correlation guard.** A quantity drawn from a covariance is tagged with it, and combining two
  quantities carrying the same tag through scalar arithmetic raises. This turns the most dangerous silent
  error in the system - treating correlated inputs as independent - into a loud one. `.detached()` is the
  explicit, documented escape hatch.
- **`core/differentiation.py`** - complex-step and central-difference Jacobians. The complex step is exact
  to machine precision and is what every analytic Jacobian is verified against, because a sign error there
  produces a plausible-looking wrong uncertainty rather than an error.
- **`core/models/`** - Epoch, Position, Station, ConstraintSpec, Observation, Cluster, GnssSession, Network,
  Campaign, Project, Solution and Provenance, with the observation type registry and lossless JSON
  round-tripping (FR-100 to FR-107).
- **RD-02 reference cases**, each validated three ways: a hand-derived closed form, the module's first-order
  propagation, and a derivative-free Monte Carlo simulation.
- **Structural check for FR-200**: a new plain-float field on a model class fails the build until someone
  decides whether it is a measurement or a diagnostic.

#### Notes

- Constraints are per component, not per station, so the routine case of a benchmark fixed in height and
  free in plan is expressible.
- Gravity carries no DynAdjust measurement type in the registry, which is the concrete form of ADR-0002:
  a required menu group with no engine behind it.
- NumPy is a hard dependency from this phase (it ships with QGIS); SciPy remains optional, and CI tests the
  SciPy-absent path.


## [0.1.0] — Phase P0, Foundations

The first phase of [`specs/ROADMAP.md`](specs/ROADMAP.md). The plugin installs, loads, shows its menu and
its Processing provider, reads its settings, logs, tests and packages. **Nothing computes yet** — P0's job is
that everything which will compute has somewhere to live and a way to be tested, translated and shipped.

### Added

- **Plugin lifecycle** — `classFactory`, `initGui` / `unload`, the GeoComp menu on the QGIS menu bar with the
  six specified entries, a toolbar, and an About dialog under Plugins (FR-001…FR-007).
- **Processing provider** `geocomp`, with algorithms declared in a single QGIS-free registry that the menu
  and the toolbox both read, so the two cannot drift apart (FR-030…FR-032, ADR-0005).
- **Pure-Python core** — the exception hierarchy with stable machine-readable codes, the cancellation and
  progress protocols, the setting declarations, and layered settings resolution. Imports and runs with no
  QGIS (NFR-002).
- **Layered settings** — `run → project → global → built-in default`, with the origin scope of every
  effective value recoverable and shown in the UI (FR-068).
- **Global Settings window** with a side menu by equipment type, its pages generated from the setting
  declarations so a setting cannot exist without a UI (FR-060, FR-067).
- **Trilingual infrastructure** wired from the first commit rather than retrofitted: `tr()` discipline,
  catalogue extraction with an AST fallback for environments without the Qt tools, and complete pt-BR and es
  catalogues (FR-090…FR-095).
- **`geocomp:project_system_report`** — reports versions, engine availability and every setting with its
  origin scope. Proves the registry → provider → menu path, and answers the first question of any support
  request.
- **Structural CI checks** — no QGIS in the core, i18n string discipline, menu/algorithm parity, requirement
  phase partition, spec link integrity, SPDX headers, version consistency, translation completeness.
- **Reproducible packaging** — `scripts/build.py` produces a byte-identical ZIP for a given commit.

### Notes

- Minimum QGIS is **4.0.0**; the 3.x series is deliberately not supported
  ([`specs/adr/0007-qgis-4-minimum.md`](specs/adr/0007-qgis-4-minimum.md)).
- Marked `experimental=True` in `metadata.txt` until a phase ships geodetic computation.
- DynAdjust and RTKLIB are not integrated yet: they arrive in P6 and P7. The system report says so rather
  than reporting them as missing.
