# 21 — Packaging, CI, release and licensing

**Status:** Draft
**Requirements covered:** FR-001, FR-301, FR-953, NFR-001, NFR-003, NFR-005, NFR-009.
**Source:** O11; tex §Justificativa aplicada e comercial ("bastando instalar o QGIS e o plugin, com poucos
cliques"); §Desenvolvimento aberto e colaboração.
**Decisions:** [`adr/0001-licensing.md`](./adr/0001-licensing.md),
[`adr/0003-engine-acquisition.md`](./adr/0003-engine-acquisition.md).

---

## 1. Repository layout

```text
geocomp/                    repository root
  geocomp/                  the installable plugin package — this and only this is zipped
  specs/                    these documents
  tests/                    T1–T5 (see 20-testing-and-validation.md)
  scripts/                  build, translation, release tooling
  docs/                     user documentation and tutorials
  research_project/         the primary source (LaTeX proposal)
  topo_test/                RD-01 reference dataset
```

The plugin package is `geocomp/geocomp/`; everything else is development infrastructure and never ships.

## 2. The plugin package

A QGIS plugin ZIP must contain exactly one top-level directory whose name matches the plugin package and
which contains `metadata.txt`. So `geocomp.zip` contains `geocomp/` with `metadata.txt`, `__init__.py` and
the modules of [`03-architecture.md`](./03-architecture.md) §2.

**`metadata.txt`** declares: name, `qgisMinimumVersion` (`4.0.0` — NFR-001 and
[`adr/0007-qgis-4-minimum.md`](./adr/0007-qgis-4-minimum.md)), description, version,
author, email, repository and tracker URLs, `license=GPL-2.0-or-later` (NFR-009), tags, homepage, category
and changelog.

**In the ZIP:** Python sources, compiled `.qm` translations, icons, QML styles, layout templates, report
templates, and RD-01 as a tutorial dataset.
**Not in the ZIP:** `.ts` sources, tests, specs, development tooling, and **engine binaries** (§4).

## 3. Build

`scripts/build.py` — compile translations (`lrelease`), assemble the package, and produce a reproducible ZIP
(sorted entries, fixed timestamps, so the same source yields the same artefact). The build refuses to
proceed on an untranslated string or a `metadata.txt`/`__init__.py` version mismatch.

## 4. Engine acquisition (FR-301)

The proposal promises installation "com poucos cliques": install QGIS, install the plugin, done. The engines
are separate C++ programs, so this needs a mechanism. Full reasoning in
[`adr/0003-engine-acquisition.md`](./adr/0003-engine-acquisition.md); the requirements are:

1. **DynAdjust is not bundled in the plugin ZIP** (RTKLIB's `rnx2rtkp` is: ADR-0009, below). Platform-specific binaries for three operating systems
   would multiply the package size, break the single-artefact model, and create a licence-redistribution
   obligation GeoComp should not carry.
2. **An engine manager in Global Settings** (FR-066) downloads the pinned release for the user's platform
   from the upstream release page, verifies its checksum, extracts it into the QGIS profile directory, and
   records the version.
   DynAdjust publishes prebuilt binaries for Windows x64, macOS Apple Silicon and Linux, including
   self-contained static builds — which is what makes this workable
   ([`07-engine-dynadjust.md`](./07-engine-dynadjust.md) §2).
3. **An explicitly configured path always wins**, for users with a system installation or a build of their
   own (FR-300).
4. **Absence is graceful** (FR-306): the plugin loads, everything not needing that engine works, and the
   operations that do are disabled with an explanation and an offer to install.
5. **Versions are pinned and recorded** (FR-302, FR-134).

**As built (P12c-6).** Until P12c-6 the manager was a library that nothing in the plugin called: its
download, verification and extraction had been run once, by hand, on Linux (P6); the *Paths and engines*
page of Global Settings held no setting; no engine looked in the folder the manager installs into; and
RTKLIB could be found only on the system path. Now:

- **Where a program comes from**, in rule 3's order: a path in Global Settings (`paths.dynadjust_directory`,
  `paths.rtklib_program`, global scope only, since where a program is installed is a fact about a machine)
  or, for DynAdjust, the algorithm's own parameter for one run; then GeoComp's installation in the QGIS
  profile; then the system path (`services/engines.py`). Every algorithm that runs an engine, the About
  dialog and the system report build it the same way.
- **Installing** is *Project ▸ Install an engine* (`geocomp:project_install_engine`), which the *Paths and
  engines* page opens beside each engine's state. It downloads the pinned release for this machine
  (`current_platform()`) over the QGIS network stack, verifies it, extracts it, **records** version,
  platform, source, digest and directory in `installed.json`, and runs the installed `dnaadjust` to show
  it works here. The record is written last, so it only ever names an installation that verified.
- **Checked on each operating system** by the `engine` workflow's `manager` job, on Linux, Windows and
  Apple-Silicon macOS: the real archive downloaded and verified, every program where the record says,
  `dnaadjust --version` answering the pinned version, a configured directory winning, and a network
  adjusted through the managed installation agreeing with the committed fixture to 0.1 mm.

**RTKLIB's `rnx2rtkp` ships inside the plugin (ADR-0009).** Its upstream (RTKLIB-EX) publishes executables for
Windows only, at a release (`v2.5.1`, `62d4677`) that is not the build GeoComp's parsers were checked against
(`06e8644`), so there was nothing pinnable to download on Linux or macOS, and GeoComp is meant to be
self-contained. The `build` workflow now builds `rnx2rtkp` from `06e8644` on the oldest supported Ubuntu, checks
that it links `libc` and `libm` only and that the committed `.pos` fixtures match *that binary*, and
`scripts/build.py --engine rtklib=linux-x86_64:PATH` stores it, executable, under
`resources/engines/linux-x86_64/rtklib/` with RTKLIB's BSD 2-clause notice beside it; a build that carries the
program without the notice fails. The plugin looks for it after a configured path and a managed installation and
before `PATH`, restores the executable bit a ZIP library drops, and reports the source as `bundled`. The `install`
job unpacks the archive the way QGIS does, with no `rnx2rtkp` on `PATH`, and runs the bundled program.

**Not done:** Windows and macOS builds. Criterion 4 is met for DynAdjust and, on Linux x86-64 only, for RTKLIB.
On the other platforms RTKLIB is still located, not acquired, until a runner builds it and its fixtures check
out; macOS also needs a decision about Gatekeeper.

## 5. Continuous integration (FR-953)

Per [`20-testing-and-validation.md`](./20-testing-and-validation.md) §7:

| Workflow | Trigger | Does |
|---|---|---|
| `test` | Every push and PR | T1–T3, structural checks; T4/T5 where engines are cached |
| `nightly` | Daily | Full matrix including T4/T5 across all OSes |
| `translations` | Every push | Extract strings; fail on untranslated additions |
| `build` | Every push and tag | Build the ZIP; validate it installs into a headless QGIS; on a **published release**, attach the archive and its SHA-256 to it (P12c-28, untested until a release is published) |
| `release` | Tag | Build, sign, attach to the GitHub release, publish to plugins.qgis.org |

A pull request cannot merge with a failing `test` or `translations` workflow.

**As built (P12c-6): the QGIS tier, for criterion 5.** The `test` workflow runs the whole suite three
times more, once per operating system, each time in the Python of the QGIS a user installs there:

| System | QGIS from | Its Python | Not run there |
|---|---|---|---|
| Linux | The `qgis/qgis` image at the release tag | The image's | — |
| Windows | OSGeo4W, unattended: `qgis` (stable) or `qgis-ltr`, with `python3-pytest` and `python3-scipy` | OSGeo4W's, through `python-qgis.bat` | PostGIS; the engine-installation tests, whose stand-in engine is shell scripts |
| macOS | The official bundle, through the Homebrew cask `qgis` or `qgis@ltr` | The bundle's, with `PYTHONPATH` naming its standard library | PostGIS |

PostGIS service containers exist on Linux runners only, and the Linux job runs those tests against a real
server; the `engine` workflow installs and runs DynAdjust's real Windows archive (§4).

**Which QGIS** is decided at each run by `scripts/qgis_versions.py`. It resolves the images' moving `stable`
and `ltr` tags, through Docker Hub's tag listing, to the release tags with the same digest, and leaves out a
release below the plugin's `qgisMinimumVersion` with a notice: ADR-0007 reads NFR-001 as the 4.x series,
its LTR once one exists and its stable until then. On 4 October 2026 that is stable 4.2.3 alone, the `ltr`
tag being 3.44.15; the LTR joins the matrix when its tag is a 4.x release, with no change to the workflow. A
channel that cannot be resolved fails the run rather than shrinking the matrix. Each job then checks that the
QGIS it runs is the release line its name states (`--check`): exactly on Linux, where the image *is* the
release tag; within the release line on Windows and macOS, whose packages can trail the image by a patch
release (Homebrew's cask was 4.2.2 that day).

Until P12c-6 the tier ran in `qgis/qgis:latest` on Linux alone. That tag is the **nightly build**
(4.3.0-Master), so no released QGIS was under test anywhere; `build`'s install check used it too, and now
uses `stable`.

## 6. Versioning and releases

Semantic versioning. Breaking changes to storage schema, algorithm ids or public core interfaces are major.

Every release: a changelog entry in `metadata.txt` and `CHANGELOG.md`; translation completeness per
language; the tested engine version range; the storage schema version and any migration; the reference
datasets that pass; and any known cross-validation discrepancy (§4 of `20-`).

Published to the **official QGIS plugin repository** (plugins.qgis.org) — the proposal's "poucos cliques"
requires it — and to GitHub releases.

---

## 7. Licensing (NFR-009)

### 7.1 The conflict, and its resolution

The proposal states the project will use a **permissive** licence, arguing against tools like Bernese whose
terms restrict commercial use or redistribution (`tex §Justificativa aplicada e comercial`).

The *intent* — no cost, no commercial restriction, free modification and redistribution — is entirely
achievable. The word "permissive" is not, for two reasons:

1. **plugins.qgis.org requires GPLv2-or-later** for listed plugins.
2. **PyQGIS and PyQt are GPL.** A Python plugin importing them is a derivative work in the sense the GPL
   intends.

**Decision: GPL-2.0-or-later** ([`adr/0001-licensing.md`](./adr/0001-licensing.md)).

This satisfies every stated goal: free of charge, freely modifiable, freely redistributable, and usable
commercially without restriction. It is not what "permissive" technically means, but it removes exactly the
barriers the proposal objects to.

> **Recommendation for the research project.** `tex §Justificativa aplicada e comercial` should read *"com
> licença livre"* or *"copyleft"* rather than *"licença permissiva"*, since the current wording promises
> something a QGIS plugin cannot deliver. This is a wording change, not a change of intent.

### 7.2 Third-party components

| Component | Licence | Relationship |
|---|---|---|
| QGIS / PyQGIS | GPL-2.0-or-later | Imported — the reason for the licence choice |
| PyQt | GPL / commercial | Imported via QGIS |
| NumPy | BSD-3-Clause | Imported |
| SciPy (optional) | BSD-3-Clause | Imported when present |
| `openpyxl` (optional) | MIT | Imported when present |
| **DynAdjust** | **Apache-2.0** | **Separate process, invoked via subprocess** |
| **RTKLIB / RTKLIB-EX** | See upstream `license.txt` | **Separate process, invoked via subprocess** |

**The engines are invoked as separate processes, never linked.** GeoComp writes input files, runs a program,
and reads output files. This is arm's-length use, not derivation, and it is one more reason engines are not
bundled (§4).

DynAdjust builds against CodeSynthesis XSD, which is GPL2-licensed; this affects the DynAdjust binary's own
distribution terms, not GeoComp's, and is another reason to download from upstream rather than redistribute.

### 7.3 Obligations

- `LICENSE` at the repository root: the full GPL-2.0-or-later text.
- `NOTICE` or `THIRD_PARTY.md`: every component of §7.2 with its licence and upstream URL, kept current.
- Source-file headers: SPDX identifiers (`SPDX-License-Identifier: GPL-2.0-or-later`).
- Where an engine is downloaded, its own licence text is placed alongside it and shown in the About dialog.
- Attribution to Geoscience Australia (DynAdjust) and to the RTKLIB authors in the About dialog and the
  documentation — beyond obligation, this is due credit to the projects GeoComp is built on, and it supports
  the upstream-feedback goal (FR-955).

---

## 8. Acceptance criteria

1. `scripts/build.py` produces a ZIP that installs into a clean QGIS and passes plugin validation.
2. Two builds of the same commit produce byte-identical ZIPs.
3. The plugin loads with no engine installed; engine-dependent operations are disabled with an explanation
   (FR-306).
4. The engine manager downloads, verifies, installs and detects each engine on each supported OS, and an
   explicitly configured path overrides it.
5. The CI matrix runs on Linux, Windows and macOS, on the current LTR and current stable QGIS.
6. A tagged release builds, publishes to GitHub releases and to plugins.qgis.org, and the published artefact
   installs.
7. `LICENSE`, `THIRD_PARTY.md` and SPDX headers are present and complete; a CI check asserts every source
   file has an SPDX header.
8. The About dialog shows GeoComp's licence, the engine versions in use, and their licences and attributions.
