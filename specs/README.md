# GeoComp specifications

This folder is the authoritative description of what the GeoComp QGIS plugin is and how it must behave.
Code in [`../geocomp/`](../geocomp/) is written *from* these documents, not the other way round.

**Primary source.** Every requirement here derives from the research project in
[`../research_project/projeto_geocomp_abnt.tex`](../research_project/projeto_geocomp_abnt.tex) (with the
author's change notes in `../research_project/modificações.md` and the design figures in
`../research_project/fig/`). Where a specification adds detail the proposal does not contain, it says so.
Where a specification contradicts the proposal, that is a defect in the specification — raise it.

---

## How to use this folder

**Implementing a phase.** Open [`ROADMAP.md`](./ROADMAP.md), find the phase, read the specification documents
it lists, then write code that satisfies the requirement IDs it closes. Do not implement from the roadmap
alone — the roadmap says *when*, the specifications say *what*.

**Adding a feature.** Add or amend a requirement in [`02-requirements.md`](./02-requirements.md) first, give it
an ID, cite its source, place it in a phase in [`ROADMAP.md`](./ROADMAP.md), and add the row to
[`traceability.md`](./traceability.md). Then write the code.

**Disagreeing with a decision.** Significant, hard-to-reverse choices are recorded as ADRs in
[`adr/`](./adr/). To change one, add a new ADR that supersedes it rather than editing the old one.

**Reviewing.** A pull request that changes behaviour should name the requirement IDs it implements or changes.
A pull request that changes behaviour with no corresponding requirement is a specification gap — fix the
specification in the same PR.

---

## Document map

### Foundations

| # | Document | What it settles |
|---|---|---|
| — | [`00-glossary.md`](./00-glossary.md) | Terms, in EN / PT-BR / ES. Also the terminology contract for translators |
| — | [`01-vision-and-scope.md`](./01-vision-and-scope.md) | Who this is for, what is in scope, what is explicitly not |
| — | [`02-requirements.md`](./02-requirements.md) | Every `FR-###` and `NFR-###`, each traced to its source |
| — | [`03-architecture.md`](./03-architecture.md) | Layers, dependency rules, engine abstraction, threading, errors |

### Computation

| # | Document | What it settles |
|---|---|---|
| 04 | [`04-data-model.md`](./04-data-model.md) | Project / Campaign / Epoch / Network / Station / Observation / Solution |
| 05 | [`05-uncertainty-and-covariance.md`](./05-uncertainty-and-covariance.md) | How every quantity carries its uncertainty |
| 06 | [`06-adjustment-core.md`](./06-adjustment-core.md) | In-house least squares, statistics, reliability, pre-analysis |

### External engines

| # | Document | What it settles |
|---|---|---|
| 07 | [`07-engine-dynadjust.md`](./07-engine-dynadjust.md) | The DynAdjust pipeline, file formats, and its limits |
| 08 | [`08-engine-rtklib.md`](./08-engine-rtklib.md) | `rnx2rtkp`, products download, `.pos` parsing, baselines |

### Technique modules (one per GeoComp menu group)

| # | Document | Menu group |
|---|---|---|
| 09 | [`09-module-total-station.md`](./09-module-total-station.md) | Total Station |
| 10 | [`10-module-levelling.md`](./10-module-levelling.md) | Level |
| 11 | [`11-module-gnss.md`](./11-module-gnss.md) | GNSS |
| 12 | [`12-module-gravimetry.md`](./12-module-gravimetry.md) | Gravimetry |
| 13 | [`13-module-integration.md`](./13-module-integration.md) | Integration |
| 14 | [`14-multi-epoch-monitoring.md`](./14-multi-epoch-monitoring.md) | (cross-cutting — monitoring and deformation) |

### Platform

| # | Document | What it settles |
|---|---|---|
| 15 | [`15-ui-menu-and-settings.md`](./15-ui-menu-and-settings.md) | The GeoComp menu and the Global Settings window |
| 16 | [`16-processing-provider.md`](./16-processing-provider.md) | Algorithm naming, parameters, chainability |
| 17 | [`17-persistence-and-interoperability.md`](./17-persistence-and-interoperability.md) | GeoPackage, PostGIS, and every import/export format |
| 18 | [`18-i18n-and-profiles.md`](./18-i18n-and-profiles.md) | Trilingual UI; Basic vs Advanced profiles |
| 19 | [`19-visualization.md`](./19-visualization.md) | Styled layers, ellipses, vectors, plots, reports |
| 20 | [`20-testing-and-validation.md`](./20-testing-and-validation.md) | Test tiers, reference datasets, numerical tolerances |
| 21 | [`21-packaging-ci-release-licensing.md`](./21-packaging-ci-release-licensing.md) | ZIP layout, CI, releases, licence, third-party notices |

### Planning and provenance

| Document | Purpose |
|---|---|
| [`ROADMAP.md`](./ROADMAP.md) | Phases P0–P13: goal, specs, requirement IDs closed, exit criteria |
| [`traceability.md`](./traceability.md) | Objectives O1–O12 and menu items × requirements × phase |
| [`adr/`](./adr/) | Architecture decision records |
| [`archive/`](./archive/) | Superseded planning documents, with the reasons they were superseded |

---

## Conventions

### Requirement identifiers

- `FR-###` — functional requirement: something the plugin does.
- `NFR-###` — non-functional requirement: how well, how fast, how safely it does it.
- `RD-##` — reference dataset used for validation (see [`20-testing-and-validation.md`](./20-testing-and-validation.md)).
- `ADR-####` — architecture decision record.

IDs are **permanent**. A withdrawn requirement is marked `Withdrawn` in place; its number is never reused.
Numbers are assigned in blocks by area, with gaps left for growth — do not renumber to close a gap.

### Requirement wording

The key words **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT** and **MAY** are used as in
[RFC 2119](https://www.rfc-editor.org/rfc/rfc2119). A requirement written with SHOULD is still a requirement;
deviating from it needs a recorded reason, not silence.

### Source citations

Each requirement carries a `Source:` field:

- `O1`…`O12` — a numbered specific objective from the proposal (`projeto_geocomp_abnt.tex`, §Objetivos específicos).
- `tex §<section name>` — a section of the proposal.
- `modificações.md` — the author's change notes.
- `fig/<name>.png` — a design figure.
- `derived` — an engineering consequence of another requirement, not stated in the proposal. Every `derived`
  requirement names what it derives from.

### Document status

Each document opens with a status line:

- **Draft** — written, not yet reviewed by the project coordinator.
- **Accepted** — reviewed; changes now require the amendment process above.
- **Superseded** — replaced; the header names the replacement.

All documents are currently **Draft**, pending first review.

### Language

Specifications, code, identifiers, comments and *source* UI strings are in **English**. This is a
practical constraint, not a preference: the QGIS translation toolchain extracts English source strings, and
the project's open-development goal (`tex §Desenvolvimento aberto e colaboração`) depends on international
contributors being able to read the codebase. Portuguese and Spanish reach users through `.qm` translation
files — see [`18-i18n-and-profiles.md`](./18-i18n-and-profiles.md). The
[glossary](./00-glossary.md) fixes the PT-BR and ES rendering of each technical term so translations stay
consistent.
