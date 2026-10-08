# Contributing to GeoComp

GeoComp is developed in the open, and is meant to be worked on by students, surveyors, researchers and
anyone else who adjusts geodetic networks for a living or for a degree. This guide says how to take part and
what "done" means before you open a pull request ([`specs/20`](specs/20-testing-and-validation.md) §8,
FR-954).

## Ways to take part

**Report a problem.** Open an issue on the [tracker](https://github.com/kauevestena/geocomp/issues). Say what
you ran, on what data, what you expected and what happened. *Project › GeoComp system report* writes the
versions, the engines GeoComp found and every setting with where it came from, which answers the first
questions anyone will ask. Attach it.

**Report an engine's problem to its developers.** When DynAdjust or RTKLIB fails, GeoComp keeps the folder the
engine ran in and names it. *Project › Package an engine problem* puts that folder in one zip, with a README
for the engine's developers saying what ran and where to report it. Look inside before you send it: the files
are your survey's data.

**Contribute reference data.** Validation is only as good as the examples it is checked against.
[`specs/23-wanted-reference-data.md`](specs/23-wanted-reference-data.md) lists the published worked examples
and field data GeoComp still needs (the `W-` items), each with what it would let us check. A dataset you can
share, with a licence that allows it, is one of the most useful contributions there is.

**Review a translation.** GeoComp speaks English, Portuguese (Brazil) and Spanish, equally
([`specs/18`](specs/18-i18n-and-profiles.md)). The catalogues are complete but have not yet had a
native speaker's review; §3.1 of that specification says how they were prepared for one.

**Write code or specifications.** Read on.

## Specifications come first

[`specs/`](specs/) is authoritative: code is written from it, not the other way round.
[`specs/README.md`](specs/README.md) explains how requirements, phases and decisions relate, and
[`specs/ROADMAP.md`](specs/ROADMAP.md) says which phase is current.

- **To change behaviour**, find the requirement (`FR-###` or `NFR-###` in
  [`specs/02-requirements.md`](specs/02-requirements.md)) and the specification that governs it, and amend the
  specification in the same pull request as the code.
- **To add a feature**, add the requirement first, with its source, place it in a phase, and add its row to
  [`specs/traceability.md`](specs/traceability.md).
- **To change a recorded decision**, add an ADR in [`specs/adr/`](specs/adr/) that supersedes it, rather than
  editing the old one.
- **Every requirement and every acceptance criterion has a row** in the registers of
  [`specs/20`](specs/20-testing-and-validation.md) §10 and §11, saying whether it is met and citing the test
  that shows it. A change that meets a requirement, or finds that one is not met after all, updates its row.

## What "done" means

### The tests

Four tiers run locally ([`specs/20`](specs/20-testing-and-validation.md) §1); the README says how to set each
up.

| Tier | Needs | Command |
|---|---|---|
| Core and reference | Python and NumPy | `ruff check . && python3 -m pytest -q` |
| QGIS | QGIS 4 with its Python | `QT_QPA_PLATFORM=offscreen python3 -m pytest -q tests/qgis tests/structural` |
| Engines | DynAdjust and RTKLIB on the path | the first command, with them on `PATH` |
| Sparse path | SciPy | `python3 -m pytest -q --sparse` |

**A test that needs something absent skips and says why**, so a green local run does not mean CI is green.
Four workflows check a change. `test` (every operating system, the QGIS tier, the translations) and `build`
(the plugin package) run on every push and pull request. `reference` (the reference datasets) and `engine` (the
real engines) run when a change touches what they cover, and can be started by hand from the Actions tab. Look
at all four before calling a change finished.

**Test against what is known, not against what the code happens to produce.** A reference dataset with a
published or independently computed answer, a constructed case whose answer follows from the construction, or
a second method that must agree. A test that asserts whatever the code returned today catches nothing
tomorrow.

### The structural checks

`tests/structural/` holds the rules the specifications make of every module, run with the QGIS tier
([`specs/20`](specs/20-testing-and-validation.md) §2 lists them all). The ones a new contributor meets first:

- **`core/` imports no QGIS and no Qt.** The mathematics is tested in seconds, anywhere.
- **Every string a user reads goes through a translation call**, with `%1`-style placeholders and no
  concatenation, and has a Portuguese and a Spanish translation in the same pull request. Run
  `python3 scripts/update_translations.py` to extract them, translate the new entries in
  `geocomp/i18n/*.ts`, then `python3 scripts/check_glossary.py`: the glossary in
  [`specs/00-glossary.md`](specs/00-glossary.md) is the terminology every translation uses.
- **Every refusal says what to do.** An error raised in `core/` carries a code and its context; the plugin
  words it from a message template that names the input at fault and the remedy (NFR-006). A new code needs
  its template.
- **Every parameter an algorithm declares is read, and every output it declares is returned**, and an
  algorithm id once published never changes (FR-032).
- **Every setting in Global Settings is read by something.** A control that changes nothing is refused.
- **No credential appears in a log, a provenance record or an export** (NFR-010). Credentials go through
  QGIS's authentication system.

### Uncertainty is not optional

Every geodetic value carries its uncertainty, propagated rigorously
([`specs/05`](specs/05-uncertainty-and-covariance.md)). GeoComp does not invent a standard deviation: where
the data, the instrument profile and the stated defaults give none, it refuses. A contribution that weights
an observation by a number nobody stated will be asked to refuse instead.

## Pull requests and commits

- **Name the requirements** the change implements or amends.
- **Say what changed, and what it cost.** If the change found a defect, name it, including one in your own
  first attempt. State what is *not* done, rather than letting a green tick imply that it is.
- **Keep a pull request to one coherent piece of work**, with its specification, tests and translations in it.
- Commit messages follow the same standard as the pull request description.

## Licence

GeoComp is GPL-2.0-or-later ([`LICENSE`](LICENSE)), and contributions are accepted under the same licence.
Data from third parties is listed with its terms in [`THIRD_PARTY.md`](THIRD_PARTY.md). Test data stays
under `tests/`, outside the plugin package. A tutorial dataset ships in the package only where its terms
allow that, with its notice beside it, as RTKLIB's sample does. Data whose terms do not allow
redistribution is not committed at all: a test that needs it fetches it, and skips without it.

## Companies and public bodies

How organisations take part, through sponsored work, contracted features, institutional datasets or a seat in
the project's decisions, is for the project's maintainer to set out, and this section will say so when they
have. Until then, open an issue describing what you have in mind.
