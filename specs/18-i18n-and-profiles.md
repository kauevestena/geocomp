# 18 — Internationalisation and usage profiles

**Status:** Draft
**Requirements covered:** FR-070, FR-071, FR-090…FR-095.
**Source:** O7; tex §Internacionalização e interface trilíngue; §Justificativa pedagógica.

---

## 1. Three languages, equally (FR-090)

Portuguese (pt-BR), English (en) and Spanish (es), **complete** in each: menus, dialogs, algorithm names and
descriptions, parameter names and help, messages, warnings, errors, report labels and layer field aliases.

The proposal says *"completamente disponível"*. Partial translation is worse than none: a dialog half in
Spanish and half in English is harder to use than one consistently in either.

**Source locale is English** — see [`README.md`](./README.md) §Language for why. The QGIS translation
toolchain extracts English source strings, and the project's open-development goal depends on international
contributors being able to read the code.

## 2. String discipline from day one (FR-091)

**Every user-facing string passes through the translation layer in the commit that introduces it.**

This is a process requirement, and it is the single cheapest thing in this specification. Wrapping a string
as you write it costs nothing. Finding and wrapping several thousand strings across a finished codebase is
a large, error-prone, low-value task that is invariably deferred — which is what the archived roadmap did by
putting i18n in Phase 9 ([`archive/README.md`](./archive/README.md), item 10). Here it is in **P0**.

Mechanics:

- `self.tr()` in `QObject` subclasses; `QCoreApplication.translate("GeoComp", …)` elsewhere.
- **`core/` contains no user-facing strings at all.** It raises exceptions with structured, machine-readable
  context ([`03-architecture.md`](./03-architecture.md) §3.6); the presentation layer renders them into
  translated messages. This is a direct consequence of NFR-002 — a QGIS-free core cannot call `tr()` — and it
  is a better design regardless, because it separates *what went wrong* from *how it is phrased*.
- Concatenation is forbidden. Placeholders carry the variation: `tr("Station %1 has no approximate
  coordinates")`, never `tr("Station ") + name + tr(" has no…")`, which is untranslatable into languages with
  different word order.
- Plural forms use Qt's plural mechanism, not an `if n == 1` branch.
- Context is supplied where a word is ambiguous — English "level" is the instrument (*nível*) and a
  confidence level (*nível de confiança*), and they translate identically in Portuguese but not everywhere.

**Enforcement:** a CI check scans for user-facing string literals outside a translation call, and for string
concatenation inside one. See [`20-testing-and-validation.md`](./20-testing-and-validation.md).

**A word is looked up under the context it is filed under, or it is not translated at all.** The extractor files
a string under the `TR_CONTEXT` of the class whose body holds it, or under its module's `_CONTEXT`. At run time
`self.tr` looks it up under the `TR_CONTEXT` of the instance, which for a shared base class is a subclass's.
P12c's audit found five places where the two differed. Each catalogue was complete and the word still showed
in English in every language:

- "Requirement" in every algorithm's help;
- every Processing group's name;
- the four GNSS modes' shared parameters and help;
- the PostGIS mode switch's connection and schema;
- the layer outputs every adjustment declares.

**Words that live in shared code use their module's own `_tr`.** A base class does not use `self.tr`.
`tests/qgis/test_language.py` holds the rule from the outside. It installs each catalogue and reads back every
algorithm's words, every help and every menu entry, so a word that does not translate fails, whatever the
reason.

**Every code has its words (P12c-7).** The split above has a second failure mode, besides a template
interpolating a key its raiser never supplies. A code may have **no template at all**. The user then reads
"GeoComp could not complete the operation (data.some_code)", which says none of what NFR-006 requires. When
P12c-7 counted, 457 of the codes GeoComp raises were in that state.

- The 81 codes of the engine package now have templates. These are DynAdjust's and RTKLIB's: what GeoComp
  cannot write for an engine, a run that failed, and an output file that does not read.
- A template for a failed engine run shows the **engine's own message** (FR-305). Each engine failure carries
  that message in its context, and the template must interpolate it.
- The 28 codes of the file readers the algorithms use have templates too: RINEX files and folders, field and
  levelling books and their mappings, geoid grids, and the tables export.
- The 67 codes of the levelling and total-station techniques have templates as well. A user's observations
  reach most of them: a line that does not join up, a setup without a foresight, or a resection with two known
  points.
- The 51 codes of GNSS, gravimetry and integration follow, which completes every technique. They cover
  baselines, loops, comparisons, the reference-station database, gravity readings, drift and tides, and the
  combination.
- The 61 codes of the adjustment and what surrounds it have templates too: weighting, variance components,
  the geocentric frame's constraints, ellipsoids, frames and projections, the statistics, the drawing of
  ellipses, and the pre-analysis design.
- The 44 codes of the instrument profiles, the report templates and the settings service follow. They
  cover gravimeters and their calibration tables, levels and levelling classes, unknown or duplicate
  profiles, and an observation with no standard deviation from anywhere.
- The 46 codes of the data model follow: stations and their constraints, observations and clusters,
  positions and heights, epochs, solutions, GNSS sessions, and the project document.
- The last 79 complete it. They are the 48 of the core's own modules (uncertainty and covariance matrices,
  geoid models, base maps and display formats) and the 31 of the readers of the reference corpora
  (`krumm.py`, `adjust.py`). Only the tests and `scripts/` reach those readers, but whoever runs them reads
  the refusal.

The codes without words were frozen, while P12c-7 worked through them, in a list that could only shrink. It is
empty and has been removed, and **there is no exemption**. `tests/structural/test_message_templates.py`
reads all of `geocomp/` and enforces two rules:

- a code raised without a template fails;
- a code whose every raise site carries an engine's diagnostic fails unless its template shows it.

A template is only reached through `message_for`. A refusal shown with `str(error)` gives the developer's
diagnostic, which is the code and its context, so no window, panel or algorithm should show one that way. A handler
that catches GeoComp's refusals together with Python's own (`OSError`, `ValueError`) says the reason with
`reason_for`, which words the first and passes the second through. Until P12c-7 these showed `str(error)`:
*Add base map*, the results panel, the time-series panel, the pre-analysis dialog, the total-station field
mapping and readings, and the levelling field mapping and lines.

**Every finding has its words too (P12c-8).** A finding is returned rather than raised (FR-166), but the
reader meets it in the same places: a report, the Processing log, a dialog. Until P12c-8 it carried only an
English sentence, and everything showed that sentence whatever the language. That broke the rule above that
the core never phrases a sentence. A finding is now worded as an error is:

- It carries a `context`: the ids and values its sentence needs. A number in the context is already written
  for the reader, rounded and in the display locale's separator (FR-094), because the template only places
  it. `finding_text` does not localise, so a station named `1.1` is not rewritten as a number.
- Its template is `finding.<code>`. The English `message` stays, for logs and tests only.
- A finding that reports a refusal carries it as `error`, and its template says it through `reason`. A
  refusal reported per row, setup or line keeps the refusal's code, which filters and tests use, and names
  the frame it is worded by with `wording`: "Row %1: %2". The levelling-book import showed such a refusal's
  developer diagnostic (`f"setup {id}: {error}"`) until P12c-8; it now shows its words.
- A file keeps the English: a findings CSV is the same in every language, as FR-095 requires of anything a
  person does not read on the screen.

The structural test reads findings as it reads errors. Every `Finding(...)` must name its template and
context keys where the test can read them: a literal code or `wording`, and a dict literal for `context`. Its
template must interpolate only those keys. The findings still without words are frozen in
`tests/structural/unworded_findings.py`, which may only shrink. They are the techniques' own: levelling and
the total station.

## 3. Terminology (FR-093)

[`00-glossary.md`](./00-glossary.md) is **normative** for translators: its PT-BR and ES columns are the
required renderings. Geodetic terminology is precise and regionally variable, and a translator without domain
knowledge will reasonably but wrongly render *"resíduo"* as *"remainder"* or *"pontaria direta"* as *"direct
aim"*.

The glossary also fixes what is *not* translated: `data snooping`, `leap-frog`, `RINEX`, `PPP`, `SINEX`,
`DynaML`, engine names, file extensions and command names.

**As built (P12c).** `scripts/check_glossary.py` reads the glossary's tables and every translated string, and
reports each string whose English uses a term, plurals included, but whose translation uses none of the
term's renderings. A structural test runs it for both languages. It matches leniently, since the languages
inflect: each word of the rendering must start a word of the translation, accents and case aside, with its
last two letters free. It checks terminology, not grammar, and does not replace the review by native speakers
that P12's exit asks for ([`ROADMAP.md`](./ROADMAP.md), P12c-5). Five English words are also ordinary words
— *run*, *direction*, *static*, *engine*, *level* — and no pattern tells the term from the word. The script
names them, each with its reason, and does not check them.

Its first run found 128 strings off the glossary, 61 Portuguese and 67 Spanish. Most were levelling strings that rendered *setup* as
*estação*/*estación*. The glossary keeps that word for *station*, so one levelling dialog gave a mark and an
instrument position the same name, while the total-station strings had always said *estacionamento*. The rest:

* *minimal detectable bias*, *datum defect* and *covariance matrix* had been worded freely;
* in Portuguese, *resection* and *forward intersection* were *inversa*/*direta*, not *à ré*/*à vante*;
* in Spanish, the *target height* had been called the *prism's*;
* the gravity help translated *data snooping*, which the glossary keeps in English.

Reading the levelling strings also showed European Portuguese in the pt_BR catalogue. The vocabulary was
replaced (*ficheiro*, *registo*, *folha de cálculo*, *partilhar*, *detetável*). Constructions such as *pelo
que* and *tem de*, about twenty strings, were left for that review, and P12c-5 converted the ones that are
European and not merely formal (§3.1).

### 3.1 The native-speaker review (P12c-5)

**Not yet held.** It needs people who speak the languages natively and know the subject, and none has been
available to this project's development. P12's exit asks for it ([`ROADMAP.md`](./ROADMAP.md), P12c-5), and
it moves to P13, where a release in three languages needs it anyway.

**What was done to prepare it**, so that the review reads the language rather than chasing what a script
can find:

* The catalogues are complete — 2,212 strings in each — and every one passes the glossary check above.
* In pt_BR, 23 strings had their European markers converted: the conclusive *pelo que* to *de modo que*;
  *estar a* + infinitive to the gerund; *registar*, *registado* to *registrar*, *registrado*; *quilómetro*
  to *quilômetro*; *rede de monitorização* to *rede de monitoramento*; *partes desligadas* to *partes
  desconexas*. In es, the one *fichero* among 71 *archivo*.
* Kept on purpose: *ter de*, standard in formal Brazilian writing too; *pelo que* as a relative ("*pelo
  que esse valor ignora*"), valid in both variants; *injunção* and *injuncionar*, Brazilian geodesy's own
  terms for a constraint.

**What the reviewers should look at first**, because no pattern decides it:

* pt_BR: enclitic pronouns (*introduzem-se*, *compara-o*, *exigem-na*, *cancela-se*) — correct, and stiffer
  than Brazilian technical prose usually is; the register of the long help texts.
* es: *pulsar* (Peninsular, beside *hacer clic*), and whether the catalogue reads as neutral Latin American
  Spanish throughout, which is the audience FR-090 names first.
* Both: whether the glossary's renderings are the ones the profession in each country actually uses.

**The record.** A review is entered here when it happens, one row per language, against the catalogue's
commit, so a later change to a string shows as unreviewed:

| Language | Reviewer | Date | Catalogue at | Scope | Findings |
|---|---|---|---|---|---|
| pt_BR | — | — | — | — | not yet held |
| es | — | — | — | — | not yet held |

## 4. Workflow

| Step | Tool | When |
|---|---|---|
| Extract source strings to `.ts` | `pylupdate5` / `lupdate` over a `.pro` listing every source file | Automatically in CI on every change |
| Translate | Qt Linguist, or any `.ts` editor | Continuously |
| Compile to `.qm` | `lrelease` | In the release build |
| Load | `QTranslator` in `plugin.py`, honouring FR-092 | At plugin start |

- `.ts` files are committed; `.qm` files are build artefacts, generated at packaging
  ([`21-packaging-ci-release-licensing.md`](./21-packaging-ci-release-licensing.md)).
- **CI fails the build if extraction produces new untranslated strings without the `.ts` files being
  updated.** Untranslated strings are caught at the commit that adds them, not at release.
- A release reports translation completeness per language.

## 5. Locale behaviour (FR-092, FR-094, FR-095)

**Language selection:** follow the QGIS UI language, with an explicit override in Global Settings
(FR-067, FR-092). Changing it takes effect immediately where Qt allows, and otherwise prompts for a reload —
it never requires the user to find the setting in QGIS's own preferences.

**Display formatting (FR-094):**

- Decimal separator from the locale — a comma in pt-BR and es. Never hard-coded.
- Thousands separator, date and time formats from the locale.
- Angles in the configured format (DMS or decimal degrees) with locale-correct separators.
- Units are displayed with their symbol; the symbol is not translated (`m` is `m`).

**File formatting (FR-095):** every file GeoComp writes — CSV, engine input, JSON, GeoPackage content — uses
a locale-independent representation regardless of UI language. A project produced by a Brazilian user must
open unchanged for a colleague running an English QGIS, and an engine input file with comma decimals is
simply invalid. This is the single most common i18n bug in scientific software and it is asserted by a test
that writes every output format under a comma-decimal locale and reads it back under a period-decimal one.

**As built (P12c).** `core/number_format.py` holds the separator. It is the language GeoComp's own words are
in, which the plugin sets when it installs the catalogue, so a report never mixes Portuguese words with English
numbers. Each Processing run reads it once, at its start, and holds it in a context variable for the whole run.
The formatters for people — the reports' `format_number`, P12a's `DisplayFormat`, the dialogs, the chart and
legend labels — turn the point of a number they have just formatted into the separator. A setting's value
recorded as text is turned only if it is a number. The formatters for machines (`exact`, the engines' writers)
do not call it.

`tests/qgis/test_locale_numbers.py` is the round trip asked for above. It runs RD-01's chain, field book to
export, in English, then in pt-BR and in es with Qt's, GeoComp's and Python's locale all set to the language.
Every file must equal the English run's and read back, and every number in every report table must change
its separator and nothing else. Writing it found two tables that printed a value with `str()`: the settings
and the provenance parameters. Both used a point in every language.

**Not built:** thousands grouping (a coordinate prints as `7395123,4567`) and locale dates (reports write ISO
8601).

---

## 6. Basic and Advanced profiles (FR-070, FR-071)

The proposal frames these as two audiences:

> **Modo padrão/comercial** — *"opções reduzidas e voltadas a fluxos de processamento mais comuns, com
> parâmetros padrão pré-configurados"*
> **Modo avançado/pesquisa** — *"exposição de parâmetros adicionais e opções de configuração refinadas,
> permitindo experimentação com diferentes estratégias de processamento e ajuste"*

### 6.1 The invariant (FR-071)

**Switching mode changes what is shown, never what is computed.** A parameter hidden in Basic mode takes
exactly the value it would take as the Advanced default.

This is what makes Basic mode professionally usable. If Basic were a cheaper approximation, a professional
could not defend a Basic-mode result to a client, and the "modo comercial" framing would be self-defeating.
Asserted by a test that runs every algorithm in both modes with defaults and compares numeric output
(FR-071).

*As built (P12a):* asserted by construction rather than by running — every algorithm's parameters and
defaults are identical in both modes and no run reads the mode; see
[`16-processing-provider.md`](./16-processing-provider.md) §4.1.

### 6.2 What differs

| | Basic | Advanced |
|---|---|---|
| Parameters | Reduced set with defaults | Full set |
| Engine configuration | Generated | Generated, inspectable, editable, or user-supplied (FR-325) |
| Pipeline stages | Automatic (§3 of [`07-engine-dynadjust.md`](./07-engine-dynadjust.md)) | Individually controllable |
| Uncertainty strategy | Automatic, labelled (FR-203) | Selectable per operation |
| Automatic outlier rejection | Not offered | Offered, with an explicit warning |
| Intermediate outputs | Final results | Every intermediate available |
| Diagnostics | Summary | Full, including condition numbers and iteration history |

### 6.3 Mechanism

Implemented through the Processing advanced-parameter flag plus dynamic parameter construction where that is
insufficient ([`16-processing-provider.md`](./16-processing-provider.md) §4.1). Mode is a Global Setting,
switchable without restart, and applies to menu dialogs and Processing dialogs alike.

**A third audience is served by neither mode and needs no switch:** the student. Basic mode is the right
default for learning, and what students additionally need — visible intermediate results and visible
statistics — is available in both modes because it is a property of the algorithms
([`15-ui-menu-and-settings.md`](./15-ui-menu-and-settings.md) §4), not a mode.

---

## 7. Acceptance criteria

1. Every user-facing string appears in the `.ts` files; the CI extraction check finds no unwrapped literal.
2. Switching QGIS to Portuguese or Spanish translates the entire GeoComp UI, with no English remaining in
   menus, dialogs, algorithm names, parameters, help or messages.
3. The language override in Global Settings works independently of the QGIS UI language.
4. Terminology in the translations matches [`00-glossary.md`](./00-glossary.md); checked by a script
   comparing translated strings against the glossary for the listed terms.
5. Under a comma-decimal locale, every file GeoComp writes reads back correctly under a period-decimal
   locale, and vice versa (FR-095).
6. Displayed numbers use the locale separator (FR-094).
7. Every algorithm produces identical numeric results in Basic and Advanced modes with defaults (FR-071).
8. No string concatenation occurs inside a translation call; asserted by the CI check.
