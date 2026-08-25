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

## 3. Terminology (FR-093)

[`00-glossary.md`](./00-glossary.md) is **normative** for translators: its PT-BR and ES columns are the
required renderings. Geodetic terminology is precise and regionally variable, and a translator without domain
knowledge will reasonably but wrongly render *"resíduo"* as *"remainder"* or *"pontaria direta"* as *"direct
aim"*.

The glossary also fixes what is *not* translated: `data snooping`, `leap-frog`, `RINEX`, `PPP`, `SINEX`,
`DynaML`, engine names, file extensions and command names.

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
