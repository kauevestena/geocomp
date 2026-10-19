# SPDX-License-Identifier: GPL-2.0-or-later
"""Read report labels and prose, and find English retained across languages.

Test-only machinery: no Qt and no probabilistic language detector. Unchanged
technical terms come from the catalogue, survey data from explicit fixture
values. A translated opening must not conceal an English sentence later in a
paragraph. This is a regression guard, not a native speaker's wording review.
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from html.parser import HTMLParser

LABELS = {"title", "h1", "h2", "h3", "h4", "h5", "h6", "th", "legend", "caption"}
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "wbr"}


class Report(HTMLParser):
    """Visible blocks, retaining inline emphasis, links, code and superscripts."""

    def __init__(self, html: str) -> None:
        super().__init__(convert_charrefs=True)
        self.lang: str | None = None
        self.blocks: list[tuple[str, str]] = []
        self._open: list[str] = []
        self._block: tuple[int, str, list[str]] | None = None
        self.feed(html)
        self.close()

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "html":
            self.lang = attributes.get("lang")
        note = tag == "div" and "note" in attributes.get("class", "").split()
        if self._block is None and (tag in LABELS or tag in {"p", "li"} or note):
            self._block = (len(self._open), "label" if tag in LABELS else "prose", [])
        if tag not in VOID:
            self._open.append(tag)
        elif self._block is not None and tag in {"br", "hr"}:
            self._block[2].append(" ")

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag not in self._open:
            return
        while self._open:
            closed = self._open.pop()
            if self._block is not None and len(self._open) == self._block[0]:
                _, kind, pieces = self._block
                self.blocks.append((kind, " ".join("".join(pieces).split())))
                self._block = None
            if closed == tag:
                break

    def handle_data(self, data):
        if self._block is not None and not {"script", "style"}.intersection(self._open):
            self._block[2].append(data)


def retained_english(
    english: Report,
    translated: Report,
    catalogue: dict[str, dict[str, str]],
    *,
    data: tuple[str, ...] = (),
) -> list[str]:
    """Unchanged labels/blocks, or a substantive English fragment in prose.

    Mask exact fixture data, never a whole paragraph containing data. Likewise
    excuse a catalogue's unchanged term, not everything surrounding it. A
    fragment is substantive here when at least two English words survive
    consecutively; whole unchanged labels and prose need only one word.
    """
    assert [kind for kind, _ in english.blocks] == [kind for kind, _ in translated.blocks]
    kept = {source for context in catalogue.values() for source, text in context.items() if source == text}
    # These Latin technical phrases are preserved inside longer catalogue
    # entries (e.g. "Variance factor, a priori"), rather than filed alone.
    for term in ("a priori", "a posteriori"):
        if any(
            term in source and term in text
            for context in catalogue.values()
            for source, text in context.items()
        ):
            kept.add(term)
    exempt = sorted(kept | set(data), key=len, reverse=True)

    def words(text):
        for value in exempt:
            if value:
                text = re.sub(r"(?<!\w)" + re.escape(value) + r"(?!\w)", " ", text)
        # Keep punctuation and numbers as boundaries: deleting them could join
        # unrelated words into an apparent English sentence.
        return re.findall(r"[\w]+|[^\w\s]", text)

    left = []
    for (kind, source), (_, shown) in zip(english.blocks, translated.blocks, strict=True):
        first, second = words(source), words(shown)
        if not any(re.search(r"[A-Za-z]{4,}", word) for word in first):
            continue
        if first == second:
            left.append(source)
        elif kind == "prose":
            for match in SequenceMatcher(a=first, b=second, autojunk=False).get_matching_blocks():
                common = first[match.a : match.a + match.size]
                if sum(bool(re.fullmatch(r"[A-Za-z]+", word)) for word in common) >= 2:
                    left.append(" ".join(common))
    return left
