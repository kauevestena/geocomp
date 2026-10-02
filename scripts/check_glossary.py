#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Check the translations against the glossary (specs/18 criterion 4; FR-093).

``specs/00-glossary.md`` is normative: its PT-BR and ES columns are the required
renderings of each term. This reads every translated string whose English
source uses a glossary term and reports those whose translation does not use
the glossary's rendering::

    python3 scripts/check_glossary.py            # both languages
    python3 scripts/check_glossary.py pt_BR      # one

**It matches leniently, because the languages inflect.** A term matches when
every word of the required rendering appears in the translation as the start of
a word, accents and case aside, with its last two letters free -- so *Estação*
matches *Estações* and *Elipse de erro* matches *Elipses de erro*. That is a
check of terminology, not of grammar; a native speaker's review is still the
review (``specs/18`` §3).

**What it cannot judge is listed, with why**, in :data:`NOT_CHECKED` -- a word
English uses as more than the term, which no pattern tells apart. A term is
added there only with its reason, and the list is short on purpose.
"""

from __future__ import annotations

import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GLOSSARY = REPO_ROOT / "specs" / "00-glossary.md"
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from translations import catalogue_path, read_catalogue  # noqa: E402

LANGUAGES = ("pt_BR", "es")

#: English words that are glossary terms in one sense and ordinary words in
#: another, which no pattern can tell apart. Each says why.
NOT_CHECKED = {
    "Run": "also the verb, as in 'run the adjustment', which is executar/ejecutar",
    "Direction": "also the sense of a line or a displacement, not only the observation",
    "Static": "also 'static' in its ordinary sense; the GNSS modes are checked by name",
    "Engine": "the processing engine, but also part of names such as DynAdjust's own messages",
    "Level": "also 'confidence level' and 'decimetre-level', which are nível/nivel anyway",
}

#: Rows whose English and translations pair term by term across a slash, which
#: a split on the slash alone would mismatch.
PAIRED = {
    "Fixed / float solution": (
        ("fixed solution", "Solução fixa", "Solución fija"),
        ("float solution", "Solução flutuante", "Solución flotante"),
    ),
    "Face left / Face right": (
        ("face left", "PD", "Círculo directo"),
        ("face right", "PI", "Círculo inverso"),
    ),
    "Backsight / Foresight": (
        ("backsight", "Ré", "Espalda"),
        ("foresight", "Vante", "Frente"),
    ),
}


@dataclass(frozen=True)
class Term:
    """One English term and the renderings any of which satisfies it."""

    english: str
    renderings: dict[str, tuple[str, ...]]


@dataclass(frozen=True)
class Departure:
    """A translation that does not use the glossary's rendering of a term."""

    locale: str
    context: str
    term: str
    required: tuple[str, ...]
    source: str
    translation: str


def _alternatives(text: str) -> tuple[str, ...]:
    """'Altitude geométrica / elipsoidal' and 'MDB (erro ...)' -> each acceptable form."""
    found: list[str] = []
    for part in text.replace("`", "").split(" / "):
        part = part.strip()
        bracketed = re.match(r"^(.*?)\s*\((.*)\)$", part)
        if bracketed:
            found += [bracketed.group(1).strip(), bracketed.group(2).strip()]
        elif part:
            found.append(part)
    return tuple(f for f in found if f)


def terms() -> list[Term]:
    """Every term of the glossary's tables, compound rows paired."""
    result: list[Term] = []
    for line in GLOSSARY.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| ") or line.startswith("|---"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 3 or cells[0].startswith("EN"):
            continue
        english, portuguese, spanish = cells[:3]
        if english in PAIRED:
            for en, pt, es in PAIRED[english]:
                result.append(Term(en, {"pt_BR": (pt,), "es": (es,)}))
            continue
        renderings = {"pt_BR": _alternatives(portuguese), "es": _alternatives(spanish)}
        for alternative in _alternatives(english):
            if alternative in NOT_CHECKED:
                continue
            result.append(Term(alternative, renderings))
    return result


def _plain(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in decomposed if unicodedata.category(c) != "Mn")


def _stems(rendering: str) -> list[str]:
    return [w[: len(w) - 2] if len(w) > 4 else w for w in re.findall(r"\w+", _plain(rendering))]


def uses(rendering: str, translation: str) -> bool:
    """Whether *translation* uses *rendering*, inflection aside."""
    words = re.findall(r"\w+", _plain(translation))
    return all(any(word.startswith(stem) for word in words) for stem in _stems(rendering))


def departures(locale: str) -> list[Departure]:
    """Every translated string of *locale* that does not use a term's rendering."""
    catalogue = read_catalogue(catalogue_path(locale))
    found: list[Departure] = []
    for term in terms():
        # Whole words, plurals included, and not part of a hyphenated compound.
        pattern = re.compile(r"(?<![\w-])" + re.escape(term.english) + r"(?:s|es)?(?![\w-])", re.I)
        required = term.renderings[locale]
        for context, messages in catalogue.items():
            for source, translation in messages.items():
                if not translation or not pattern.search(_strip_markup(source)):
                    continue
                if not any(uses(r, _strip_markup(translation)) for r in required):
                    found.append(Departure(locale, context, term.english, required, source, translation))
    return found


def _strip_markup(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text)


def main(argv: list[str]) -> int:
    locales = argv or list(LANGUAGES)
    total = 0
    for locale in locales:
        found = departures(locale)
        total += len(found)
        print(f"{locale}: {len(found)} translation(s) departing from the glossary")
        for item in found:
            print(f"  [{item.context}] {item.term!r} should be {' or '.join(item.required)!r}")
            print(f"      {item.source[:100]!r}")
            print(f"      {item.translation[:100]!r}")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
